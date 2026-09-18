"""Bounded V9 metadata-only attribution; no automatic benchmark or cleanup.

The real-database semantic gate must pass before a profiling runner is enabled.
This module never opens databases or creates resources at import time.
"""

from __future__ import annotations

import asyncio
import math
import sqlite3
import stat
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar, copy_context
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from statistics import mean, median
from threading import Lock
from typing import Any, cast
from unittest.mock import patch

from cyber_town.api.app import create_app
from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import NoOpSafetyControl, SafetyControl
from cyber_town.application.dialogue import DialogueExecutionConfig, DialogueService
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.observability import (
    InMemoryObservabilityRecorder,
    NoOpObservabilityRecorder,
    ProviderKind,
)
from cyber_town.application.relationship import RelationshipService
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor, StorageLane
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import SqliteRelationshipRepository

APPROVED_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v9-postfix-attribution")
SCHEMA_VERSION = 2


class Lane(StrEnum):
    CONTROL = "control"
    OBSERVABILITY = "observability"
    BUSINESS = "business"
    EVENT_LOOP = "event_loop"


class Operation(StrEnum):
    REPOSITORY = "repository"
    SQL = "sql"
    COMMIT = "commit"
    QUEUE = "queue"
    LOCK = "lock"
    PATH = "path"
    CONNECT = "connect"
    CLOSE = "close"
    RESUME = "resume"
    SLOT = "slot"
    BEGIN = "begin"
    WRITE_COMMIT = "write_commit"
    WRITER_WAIT = "writer_wait"
    IDEMPOTENCY_WAIT = "idempotency_wait"
    IDEMPOTENCY_HOLD = "idempotency_hold"
    SCOPE_WAIT = "scope_wait"
    SCOPE_HOLD = "scope_hold"
    BUDGET_SCAN = "budget_scan"
    SCOPE_TAG = "scope_tag"
    DTO = "dto"
    CONTROL = "control_operation"
    HTTP = "http"
    STORAGE = "storage"
    REQUEST_WAIT = "request_wait"
    REQUEST_HOLD = "request_hold"
    OWNER_WAIT = "owner_wait"
    OWNER_HOLD = "owner_hold"
    BUDGET = "budget_operation"
    BUDGET_DTO = "budget_dto"
    PERMIT_DTO = "permit_dto"
    RECORDER = "recorder"
    REQUEST = "request"
    INGRESS_ADMISSION = "ingress_admission"
    EXECUTION_ADMISSION = "execution_admission"
    BUDGET_RESERVATION = "budget_reservation"
    BUDGET_SETTLEMENT = "budget_settlement"
    PROVIDER_PERMIT_ACQUIRE = "provider_permit_acquire"


def _interval(value: tuple[int, int]) -> None:
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or any(type(item) is not int for item in value)
        or value[0] > value[1]
    ):
        raise ValueError("Attribution interval is invalid")


def union_duration(intervals: Sequence[tuple[int, int]]) -> int:
    for interval in intervals:
        _interval(interval)
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return sum(end - start for start, end in merged)


def exclusive_duration(parent: tuple[int, int], children: Sequence[tuple[int, int]]) -> int:
    _interval(parent)
    for interval in children:
        _interval(interval)
    start, end = parent
    clipped = tuple((max(start, a), min(end, b)) for a, b in children if a < end and b > start)
    return end - start - union_duration(clipped)


@dataclass(frozen=True, slots=True)
class Span:
    case_index: int
    operation_index: int
    lane: Lane
    operation: Operation
    start_ns: int
    end_ns: int
    failed: bool
    parent_index: int | None = None
    storage_index: int | None = None

    def __post_init__(self) -> None:
        if (
            any(
                type(value) is not int or value < 0
                for value in (self.case_index, self.operation_index, self.start_ns, self.end_ns)
            )
            or self.end_ns < self.start_ns
            or not isinstance(self.lane, Lane)
            or not isinstance(self.operation, Operation)
            or type(self.failed) is not bool
            or any(
                value is not None and (type(value) is not int or value < 0)
                for value in (self.parent_index, self.storage_index)
            )
        ):
            raise ValueError("Attribution metadata is invalid")


class SpanCollector:
    """Capture attribution before submission; never infer it on a worker."""

    def __init__(self) -> None:
        self._case: ContextVar[int | None] = ContextVar("synthetic_v7_case", default=None)
        self._lock = Lock()
        self._next = 0
        self._spans: list[Span] = []

    @contextmanager
    def case(self, case_index: int) -> Iterator[None]:
        if type(case_index) is not int or case_index < 0:
            raise ValueError("Attribution case is invalid")
        previous = self._case.set(case_index)
        try:
            yield
        finally:
            self._case.reset(previous)

    def capture[T](
        self, lane: Lane, operation: Operation, action: Callable[[], T]
    ) -> Callable[[], T]:
        case_index = self._case.get()
        if case_index is None:
            raise ValueError("Attribution case is unavailable")
        if not isinstance(lane, Lane) or not isinstance(operation, Operation):
            raise ValueError("Attribution metadata is invalid")
        with self._lock:
            operation_index = self._next
            self._next += 1

        def wrapped() -> T:
            started = time.perf_counter_ns()
            failed = True
            try:
                result = action()
                failed = False
                return result
            finally:
                span = Span(
                    case_index,
                    operation_index,
                    lane,
                    operation,
                    started,
                    time.perf_counter_ns(),
                    failed,
                )
                with self._lock:
                    self._spans.append(span)

        return wrapped

    def snapshot(self) -> tuple[dict[str, object], ...]:
        with self._lock:
            return tuple(
                {"schema_version": SCHEMA_VERSION, **asdict(span)}
                for span in sorted(self._spans, key=lambda item: item.operation_index)
            )


def sqlite_target_registered(target: object, databases: tuple[Path, ...]) -> bool:
    """Allow exact registered filenames and their exact read-only URI form."""
    if not isinstance(target, (str, Path)):
        return False
    text = str(target)
    return any(text in (str(path), path.as_uri() + "?mode=ro") for path in databases)


def validate_new_directories(paths: tuple[Path, ...]) -> None:
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("Attribution resource is invalid")
    for path in paths:
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not path.is_relative_to(APPROVED_ROOT)
            or path == APPROVED_ROOT
            or path.exists()
        ):
            raise ValueError("Attribution resource is invalid")
        for ancestor in (path, *path.parents):
            try:
                info = ancestor.lstat()
            except FileNotFoundError:
                continue
            except OSError:
                raise ValueError("Attribution resource is invalid") from None
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("Attribution resource is invalid")


def prepare_directories(
    paths: tuple[Path, ...], *, announce: Callable[[Path], None], create: Callable[[Path], None]
) -> None:
    """Require full successful announcement before the first creation callback.

    Persistent documentation registration is the caller's prior authorization
    gate. Revalidate immediately before creating each exact directory.
    """
    validate_new_directories(paths)
    for path in paths:
        announce(path)
    for path in paths:
        validate_new_directories((path,))
        create(path)


def prepare_registered_directories(
    paths: tuple[Path, ...],
    *,
    registered: tuple[Path, ...],
    announce: Callable[[Path], None],
    create: Callable[[Path], None],
) -> None:
    if any(path not in registered for path in paths):
        raise ValueError("Attribution resource registration is incomplete")
    prepare_directories(paths, announce=announce, create=create)


def latency_summary(samples: Sequence[float]) -> dict[str, float | int]:
    if not samples:
        return {"count": 0}
    if any(not math.isfinite(value) or value < 0 for value in samples):
        raise ValueError("Diagnostic samples are invalid")
    ordered = sorted(samples)
    return {
        "count": len(ordered),
        "p50_ms": ordered[max(0, math.ceil(len(ordered) * 0.50) - 1)],
        "p95_ms": ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)],
        "p99_ms": ordered[max(0, math.ceil(len(ordered) * 0.99) - 1)],
        "max_ms": ordered[-1],
    }


class DiagnosticProbe:
    """Per-request context crosses the actual worker boundary, never global phase flags."""

    def __init__(self) -> None:
        self.context: ContextVar[tuple[int, Lane]] = ContextVar(
            "synthetic_attribution_owner", default=(0, Lane.EVENT_LOOP)
        )
        self.milestones: ContextVar[list[int] | None] = ContextVar(
            "synthetic_attribution_milestones", default=None
        )
        self.lock = Lock()
        self.rows: list[Span] = []
        self.vm: list[dict[str, int]] = []
        self.arrival_to_request: dict[int, int] = {}
        self.parent: ContextVar[int | None] = ContextVar("synthetic_span_parent", default=None)
        self.storage: ContextVar[int | None] = ContextVar("synthetic_storage", default=None)
        self.next_index = 0

    @contextmanager
    def owner(self, index: int, lane: Lane) -> Iterator[None]:
        if type(index) is not int or index < 0 or not isinstance(lane, Lane):
            raise ValueError("Diagnostic owner is invalid")
        context_marker = self.context.set((index, lane))
        try:
            yield
        finally:
            self.context.reset(context_marker)

    def capture_context[T](self, action: Callable[[], T]) -> Callable[[], T]:
        context = copy_context()
        return lambda: context.run(action)

    def record(self, operation: Operation, start: int, end: int, failed: bool = False) -> None:
        index, lane = self.context.get()
        with self.lock:
            span_index = self.next_index
            self.next_index += 1
            self.rows.append(
                Span(
                    index,
                    span_index,
                    lane,
                    operation,
                    start,
                    end,
                    failed,
                    self.parent.get(),
                    self.storage.get(),
                )
            )

    @contextmanager
    def span(self, operation: Operation) -> Iterator[None]:
        index, lane = self.context.get()
        parent = self.parent.get()
        with self.lock:
            span_index = self.next_index
            self.next_index += 1
        parent_marker = self.parent.set(span_index)
        storage_marker = self.storage.set(span_index) if operation is Operation.STORAGE else None
        start = time.perf_counter_ns()
        failed = True
        try:
            yield
            failed = False
        finally:
            end = time.perf_counter_ns()
            with self.lock:
                self.rows.append(
                    Span(
                        index,
                        span_index,
                        lane,
                        operation,
                        start,
                        end,
                        failed,
                        parent,
                        self.storage.get(),
                    )
                )
            self.parent.reset(parent_marker)
            if storage_marker is not None:
                self.storage.reset(storage_marker)

    def measure[T](self, operation: Operation, action: Callable[[], T]) -> T:
        with self.span(operation):
            return action()

    def attribution_summary(self, index: int) -> dict[str, Any]:
        return summarize_spans([row for row in self.snapshot() if row["case_index"] == index])

    def snapshot(self) -> tuple[dict[str, object], ...]:
        with self.lock:
            return tuple(
                {
                    **asdict(row),
                    "case_index": self.arrival_to_request.get(row.case_index, row.case_index),
                }
                for row in self.rows
            )

    @contextmanager
    def instrument(self) -> Iterator[None]:
        import cyber_town.application.budget as budget
        import cyber_town.application.control as control_module
        import cyber_town.application.observability as observation
        from cyber_town.application.control import SafetyControl
        from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
        from cyber_town.infrastructure.persistence import sqlite_connection as writer
        from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor

        probe = self
        original_run = AsyncSqliteExecutor.run
        original_acquire = asyncio.Semaphore.acquire
        original_connect = sqlite3.connect

        async def acquire(semaphore: asyncio.Semaphore) -> bool:
            result = await original_acquire(semaphore)
            marks = probe.milestones.get()
            if marks is not None and not marks[1]:
                marks[1] = time.perf_counter_ns()
            return result

        async def run(executor: Any, lane: StorageLane, operation: Any, **kwargs: Any) -> Any:
            index, _ = probe.context.get()
            with probe.owner(index, Lane(lane)), probe.span(Operation.STORAGE):
                marks = [time.perf_counter_ns(), 0, 0, 0]
                milestone_marker = probe.milestones.set(marks)

                def work() -> Any:
                    marks[2] = time.perf_counter_ns()
                    try:
                        return probe.measure(Operation.REPOSITORY, operation)
                    finally:
                        marks[3] = time.perf_counter_ns()

                owned = probe.capture_context(work)
                try:
                    return await original_run(executor, lane, owned, **kwargs)
                finally:
                    resumed = time.perf_counter_ns()
                    probe.milestones.reset(milestone_marker)
                    if all(marks):
                        probe.record(Operation.SLOT, marks[0], marks[1])
                        probe.record(Operation.QUEUE, marks[1], marks[2])
                        probe.record(Operation.RESUME, marks[3], resumed)
                    elif marks[1]:
                        probe.record(Operation.SLOT, marks[0], marks[1])
                        probe.record(Operation.QUEUE, marks[1], resumed, failed=True)
                    else:
                        probe.record(Operation.SLOT, marks[0], resumed, failed=True)

        def connect(database: Any, *args: Any, **kwargs: Any) -> sqlite3.Connection:
            factory = kwargs.pop("factory", sqlite3.Connection)
            label = "control" if str(database) == ":memory:" else Path(str(database)).stem
            lane = Lane(label)

            class MeasuredConnection(factory):  # type: ignore[misc,valid-type]
                begin_changes = 0

                def execute(self, sql: str, parameters: Any = (), /) -> Any:
                    beginning = sql.lstrip().upper().startswith("BEGIN")
                    if beginning:
                        self.begin_changes = self.total_changes
                    index, _ = probe.context.get()
                    with probe.owner(index, lane):
                        return probe.measure(
                            Operation.BEGIN if beginning else Operation.SQL,
                            lambda: super(MeasuredConnection, self).execute(sql, parameters),
                        )

                def commit(self) -> None:
                    kind = (
                        Operation.WRITE_COMMIT
                        if self.in_transaction and self.total_changes > self.begin_changes
                        else Operation.COMMIT
                    )
                    index, _ = probe.context.get()
                    with probe.owner(index, lane):
                        probe.measure(kind, super().commit)

                def close(self) -> None:
                    index, _ = probe.context.get()
                    with probe.owner(index, lane):
                        probe.measure(Operation.CLOSE, super().close)

                def __exit__(self, *args: Any) -> Any:
                    # sqlite3's C context manager bypasses Python commit overrides.
                    # Time its real transaction exit, never invoke an extra commit.
                    if not self.in_transaction or args[0] is not None:
                        return super().__exit__(*args)
                    kind = (
                        Operation.WRITE_COMMIT
                        if self.total_changes > self.begin_changes
                        else Operation.COMMIT
                    )
                    index, _ = probe.context.get()
                    with probe.owner(index, lane):
                        return probe.measure(
                            kind, lambda: super(MeasuredConnection, self).__exit__(*args)
                        )

            index, _ = probe.context.get()
            with probe.owner(index, lane):
                return probe.measure(
                    Operation.CONNECT,
                    lambda: original_connect(database, *args, factory=MeasuredConnection, **kwargs),
                )

        def measured(function: Any, operation: Operation) -> Any:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return probe.measure(operation, lambda: function(*args, **kwargs))

            return wrapper

        class WriterLock:
            def __init__(self) -> None:
                self.value = Lock()

            def acquire(self, *args: Any, **kwargs: Any) -> bool:
                return probe.measure(
                    Operation.WRITER_WAIT, lambda: self.value.acquire(*args, **kwargs)
                )

            def release(self) -> None:
                self.value.release()

            def __enter__(self) -> Any:
                self.acquire()
                return self

            def __exit__(self, *args: Any) -> None:
                self.release()

        original_windows = SqliteSafetyControlRepository._all_window_totals

        def windows(connection: sqlite3.Connection, **kwargs: Any) -> Any:
            steps = 0

            def progress() -> int:
                nonlocal steps
                steps += 1000
                return 0

            connection.set_progress_handler(progress, 1000)
            try:
                return probe.measure(
                    Operation.BUDGET_SCAN, lambda: original_windows(connection, **kwargs)
                )
            finally:
                connection.set_progress_handler(None, 0)
                with probe.lock:
                    probe.vm.append({"case_index": probe.context.get()[0], "steps_lower": steps})

        with ExitStack() as stack:
            for obj, name, replacement in (
                (AsyncSqliteExecutor, "run", run),
                (asyncio.Semaphore, "acquire", acquire),
                (sqlite3, "connect", connect),
                (writer, "Lock", WriterLock),
                (
                    writer,
                    "validate_sqlite_path",
                    measured(writer.validate_sqlite_path, Operation.PATH),
                ),
                (SqliteSafetyControlRepository, "_all_window_totals", staticmethod(windows)),
            ):
                stack.enter_context(patch.object(obj, name, replacement))
            for name in ("_control_tag", "_scope_tags", "_budget_scope_tags"):
                stack.enter_context(
                    patch.object(
                        SafetyControl,
                        name,
                        measured(getattr(SafetyControl, name), Operation.SCOPE_TAG),
                    )
                )
            measured_controls = {
                "admit_ingress": Operation.INGRESS_ADMISSION,
                "admit_execution": Operation.EXECUTION_ADMISSION,
                "check_provider_breaker": Operation.CONTROL,
                "reserve_budget": Operation.BUDGET_RESERVATION,
                "mark_budget_dispatched": Operation.CONTROL,
                "settle_budget": Operation.BUDGET_SETTLEMENT,
                "record_provider_success": Operation.CONTROL,
            }
            for name, operation in measured_controls.items():
                stack.enter_context(
                    patch.object(
                        SafetyControl,
                        name,
                        measured(getattr(SafetyControl, name), operation),
                    )
                )
            for cls in (
                observation.TraceMetadata,
                observation.TraceStageMetadata,
                observation.ScopeTags,
            ):
                stack.enter_context(
                    patch.object(cls, "__post_init__", measured(cls.__post_init__, Operation.DTO))
                )
            for control_dto, label in (
                (budget.BudgetScopeTags, Operation.BUDGET_DTO),
                (budget.BudgetReservation, Operation.BUDGET_DTO),
                (budget.BudgetSettlement, Operation.BUDGET_DTO),
                (budget.SafetyCostMetadata, Operation.BUDGET_DTO),
                (control_module.PermitScopeTags, Operation.PERMIT_DTO),
                (control_module.ProviderPermit, Operation.PERMIT_DTO),
                (control_module.BucketRequest, Operation.PERMIT_DTO),
                (control_module.BucketConsumptionResult, Operation.PERMIT_DTO),
            ):
                stack.enter_context(
                    patch.object(
                        control_dto, "__post_init__", measured(control_dto.__post_init__, label)
                    )
                )

            def async_measured(function: Any, operation: Operation) -> Any:
                async def wrapped(*args: Any, **kwargs: Any) -> Any:
                    with probe.span(operation):
                        return await function(*args, **kwargs)

                return wrapped

            for name, operation in (
                ("acquire_provider_permit", Operation.PROVIDER_PERMIT_ACQUIRE),
                ("release_provider_permit", Operation.CONTROL),
            ):
                stack.enter_context(
                    patch.object(
                        SafetyControl,
                        name,
                        async_measured(getattr(SafetyControl, name), operation),
                    )
                )
            for recorder_type in (InMemoryObservabilityRecorder, NoOpObservabilityRecorder):
                stack.enter_context(
                    patch.object(
                        recorder_type, "record", measured(recorder_type.record, Operation.RECORDER)
                    )
                )
            yield


class MeasuredAsyncLock:
    def __init__(
        self, value: Any, probe: DiagnosticProbe, *, scope: bool = False, kind: str | None = None
    ) -> None:
        self.value, self.probe, self.scope = value, probe, scope
        self.held = 0
        prefix = kind or ("scope" if scope else "idempotency")
        self.wait_operation = Operation(prefix + "_wait")
        self.hold_operation = Operation(prefix + "_hold")

    async def acquire(self) -> bool:
        started = time.perf_counter_ns()
        try:
            result = await self.value.acquire()
        except BaseException:
            self.probe.record(self.wait_operation, started, time.perf_counter_ns(), failed=True)
            raise
        self.held = time.perf_counter_ns()
        self.probe.record(self.wait_operation, started, self.held)
        return bool(result)

    def release(self) -> None:
        self.probe.record(
            self.hold_operation,
            self.held,
            time.perf_counter_ns(),
        )
        self.value.release()

    def locked(self) -> bool:
        return bool(self.value.locked())

    async def __aenter__(self) -> MeasuredAsyncLock:
        await self.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.release()


class MeasuredScopeLocks(dict[Any, Any]):
    def __init__(self, probe: DiagnosticProbe) -> None:
        super().__init__()
        self.probe = probe

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key not in self:
            self[key] = MeasuredAsyncLock(default, self.probe, scope=True)
        return self[key]


class MeasuredOwnershipLocks(dict[Any, Any]):
    """Wrap only a newly inserted guard's lock; retain guard identity and users."""

    def __init__(self, probe: DiagnosticProbe) -> None:
        super().__init__()
        self.probe = probe

    def setdefault(self, key: Any, default: Any = None) -> Any:
        from uuid import UUID

        if key not in self:
            default.lock = MeasuredAsyncLock(
                default.lock, self.probe, kind="request" if isinstance(key, UUID) else "owner"
            )
            self[key] = default
        return self[key]


def summarize_spans(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    children: dict[int, list[tuple[int, int]]] = {}
    grouped: dict[str, list[tuple[int, int]]] = {}
    exclusive: dict[str, int] = {}
    for row in rows:
        interval = (row["start_ns"], row["end_ns"])
        grouped.setdefault(row["operation"], []).append(interval)
        if row["parent_index"] is not None:
            children.setdefault(row["parent_index"], []).append(interval)
    for row in rows:
        kind = row["operation"]
        exclusive[kind] = exclusive.get(kind, 0) + exclusive_duration(
            (row["start_ns"], row["end_ns"]), children.get(row["operation_index"], ())
        )
    return {
        "span_union_ns": union_duration(tuple((r["start_ns"], r["end_ns"]) for r in rows)),
        "union_ns": {kind: union_duration(values) for kind, values in grouped.items()},
        "exclusive_ns": exclusive,
        "counts": {kind: len(values) for kind, values in grouped.items()},
    }


async def http_diagnostic(
    root: Path, *, control_on: bool, parallelism: int, probe: DiagnosticProbe | None
) -> dict[str, Any]:
    from uuid import UUID

    from scripts import f009_step5_benchmark as bench
    from scripts.f009_step5_steady_profile import REMOTE_LATENCY

    started_setup = time.perf_counter()
    memory = SqliteLongTermMemoryRepository(
        database_path=root / "business.sqlite3", allowed_root=root
    )
    relationships = SqliteRelationshipRepository(
        database_path=root / "business.sqlite3", allowed_root=root
    )
    control_repo = SqliteSafetyControlRepository(
        database_path=root / "control.sqlite3", allowed_root=root
    )
    recorder = SqliteObservabilityRepository(
        database_path=root / "observability.sqlite3", allowed_root=root
    )
    for repository in (memory, relationships, control_repo, recorder):
        repository.initialize()
    configuration: dict[str, dict[str, int]] = {}
    for name in ("business", "control", "observability"):
        # Read setup metadata on the new experiment databases only. No setters/checkpoint.
        with sqlite3.connect(root / f"{name}.sqlite3") as connection:
            configuration[name] = {
                key: int(connection.execute("PRAGMA " + key).fetchone()[0])
                for key in ("wal_autocheckpoint", "page_size", "synchronous")
            }
    clock = bench.SyntheticClock()
    provider = FakeProvider(bench._completion() for _ in range(100))
    control = (
        SafetyControl(
            repository=control_repo,
            scope_key=bench.SYNTHETIC_KEY,
            clock_ns=clock.time_ns,
            monotonic_clock=clock.monotonic,
            pricing_policy=PricingPolicy.zero_cost(
                provider_kind=ProviderKind.FAKE, model="fake-model"
            ),
        )
        if control_on
        else NoOpSafetyControl()
    )
    service = DialogueService(
        storage_executor=AsyncSqliteExecutor(),
        personas=load_bundled_personas(),
        provider=provider,
        config=DialogueExecutionConfig(
            model="fake-model",
            temperature=0.6,
            max_tokens=256,
            timeout_seconds=12,
            max_concurrency=2,
            idempotency_ttl_seconds=600,
            idempotency_max_entries=256,
        ),
        clock=clock.monotonic,
        safety_control=control,
        long_term_memory=LongTermMemoryService(repository=memory),
        long_term_retriever=LongTermMemoryRetriever(repository=memory),
        relationship_service=RelationshipService(repository=relationships),
        observability_recorder=recorder,
        observability_scope_key=bench.SYNTHETIC_KEY,
        observability_provider_kind=ProviderKind.FAKE,
        safety_cost_recorder=recorder,
        retry_breaker_recorder=recorder,
    )
    requests = [
        DialogueRequestV1(
            request_id=UUID(int=10000 + index),
            player_id=f"bench_player_{index:03d}",
            npc_id=("neon_guide", "signal_archivist", "night_courier")[index % 3],
            conversation_id=UUID(int=index + 1),
            message="My favorite food is synthetic noodles.",
        )
        for index in range(100)
    ]
    original_app, original_execute = create_app, service.execute

    def attributed_app(*args: Any, **kwargs: Any) -> Any:
        app = original_app(*args, **kwargs)
        arrival = 0

        async def wrapped(scope: Any, receive: Any, send: Any) -> None:
            nonlocal arrival
            if scope["type"] != "http" or probe is None:
                await app(scope, receive, send)
                return
            arrival += 1
            with probe.owner(arrival, Lane.EVENT_LOOP), probe.span(Operation.HTTP):
                await app(scope, receive, send)

        return wrapped

    async def execute(request: Any, **kwargs: Any) -> Any:
        assert probe is not None
        index = request.request_id.int - 10000 + 1
        arrival = probe.context.get()[0]
        if not 1 <= index <= 100 or arrival in probe.arrival_to_request:
            raise RuntimeError("Synthetic HTTP attribution is invalid")
        probe.arrival_to_request[arrival] = index
        return await original_execute(request, **kwargs)

    lags: list[tuple[int, int]] = []
    running = True

    async def heartbeat() -> None:
        while running:
            target = time.perf_counter_ns() + 5_000_000
            await asyncio.sleep(0.005)
            end = time.perf_counter_ns()
            lags.append((min(target, end), end))

    setup_ms = (time.perf_counter() - started_setup) * 1000
    samples: list[float] = []
    before = {
        name: bench._snapshot(root / f"{name}.sqlite3")
        for name in ("business", "control", "observability")
    }
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(bench, "_INDEPENDENT_CLIENT", True))
            if probe is not None:
                target: Any = service
                target._idempotency_lock = MeasuredAsyncLock(
                    target._idempotency_lock, probe, scope=False
                )
                target._scope_locks = MeasuredScopeLocks(probe)
                target._ownership_locks = MeasuredOwnershipLocks(probe)
                stack.enter_context(patch.object(service, "execute", execute))
                stack.enter_context(patch.object(bench, "create_app", attributed_app))
            start_server = time.perf_counter()
            async with bench._http_client(service, recorder) as client:
                server_setup_ms = (time.perf_counter() - start_server) * 1000
                beat = asyncio.create_task(heartbeat()) if probe is not None else None
                started = time.perf_counter()

                async def send(request: Any) -> float:
                    latency_marker = REMOTE_LATENCY.set(None)
                    try:
                        response = await client.post(
                            "/api/v1/dialogue",
                            content=request.model_dump_json(),
                            headers={"Content-Type": "application/json"},
                        )
                        if response.status_code != 200 or response.json()["status"] != "completed":
                            raise RuntimeError("Synthetic HTTP completion failed")
                        elapsed = REMOTE_LATENCY.get()
                        if elapsed is None:
                            raise RuntimeError("Independent client timing is missing")
                        return elapsed
                    finally:
                        REMOTE_LATENCY.reset(latency_marker)

                try:
                    for offset in range(0, 100, 2):
                        pair = requests[offset : offset + 2]
                        if parallelism == 2:
                            samples.extend(await asyncio.gather(*(send(item) for item in pair)))
                        else:
                            for item in pair:
                                samples.append(await send(item))
                        clock.advance(2)
                    elapsed_total = time.perf_counter() - started
                finally:
                    running = False
                    if beat is not None:
                        await beat
    finally:
        if probe is not None:
            with probe.owner(100001, Lane.EVENT_LOOP):
                await service.aclose()
                recorder.close()
                control_repo.close()
        else:
            await service.aclose()
            recorder.close()
            control_repo.close()
    after = {
        name: bench._snapshot(root / f"{name}.sqlite3")
        for name in ("business", "control", "observability")
    }
    return {
        "samples_ms": samples,
        "latency": latency_summary(samples),
        "throughput_per_second": 100 / elapsed_total,
        "setup_ms": setup_ms,
        "server_client_setup_ms": server_setup_ms,
        "provider_dispatch_count": provider.call_count,
        "parallelism": parallelism,
        "long_term_write_exercised": False,
        "before": before,
        "after": after,
        "combined_growth_bytes": bench._combined_growth(before, after),
        "business_growth_bytes": bench._growth(before["business"], after["business"]),
        "heartbeat_intervals_ns": lags,
        "client_timing": "independent_process",
        "setup_configuration": configuration,
    }


async def memory_diagnostic(
    root: Path, *, recorded: bool, probe: DiagnosticProbe | None
) -> dict[str, Any]:
    from dataclasses import asdict
    from uuid import UUID

    from scripts import f009_step5_benchmark as bench

    original_timed = bench._timed_call
    original_close = bench._MemoryControl.close
    checks: dict[str, Any] = {}
    index = 0
    id_counter = 50000

    def synthetic_uuid() -> UUID:
        nonlocal id_counter
        id_counter += 1
        return UUID(int=id_counter)

    async def timed(action: Any) -> float:
        nonlocal index
        index += 1
        if probe is None:
            return await original_timed(action)
        with probe.owner(index, Lane.CONTROL), probe.span(Operation.REQUEST):
            return await original_timed(action)

    def close(repository: Any) -> None:
        connection = repository.connection
        # Outside measured requests, on this new in-memory real-migration repository.
        checks["integrity"] = connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        checks["foreign_keys"] = not connection.execute("PRAGMA foreign_key_check").fetchall()
        checks["settlements"] = connection.execute(
            "SELECT COUNT(*) FROM budget_settlements"
        ).fetchone()[0]
        checks["cost"] = connection.execute(
            "SELECT SUM(actual_cost_micro_usd) FROM budget_settlements"
        ).fetchone()[0]
        checks["migration_count"] = connection.execute(
            "SELECT COUNT(*) FROM schema_migrations"
        ).fetchone()[0]
        if (
            not checks["integrity"]
            or not checks["foreign_keys"]
            or checks["settlements"] != 1000
            or checks["cost"] != 0
        ):
            raise RuntimeError("Synthetic memory integrity failure")
        original_close(repository)

    with ExitStack() as stack:
        stack.enter_context(patch.object(bench, "uuid4", synthetic_uuid))
        stack.enter_context(patch.object(bench, "_timed_call", timed))
        stack.enter_context(patch.object(bench, "_INDEPENDENT_CLIENT", False))
        stack.enter_context(patch.object(bench._MemoryControl, "close", close))
        result = await bench._memory_control_run(
            root,
            InMemoryObservabilityRecorder if recorded else NoOpObservabilityRecorder,
        )
    return {
        **asdict(result),
        "latency": latency_summary(result.samples_ms),
        "segments": {
            label: latency_summary(result.samples_ms[start:end])
            for label, start, end in (
                ("first_100", 0, 100),
                ("middle_800", 100, 900),
                ("middle_501_600", 500, 600),
                ("last_100", 900, 1000),
            )
        },
        "checks": checks,
    }


def check_http_databases(root: Path, *, control_on: bool) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name in ("business", "control", "observability"):
        path = root / f"{name}.sqlite3"
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise RuntimeError("Synthetic integrity failure")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Synthetic foreign key failure")
            if connection.execute("PRAGMA journal_mode").fetchone() != ("wal",):
                raise RuntimeError("Synthetic WAL failure")
            if connection.execute("PRAGMA synchronous").fetchone() != (2,):
                raise RuntimeError("Synthetic durability failure")
            if name == "observability":
                count, dispatch, cost, complete = connection.execute(
                    "SELECT COUNT(*), SUM(provider_dispatch_count), SUM(cost_micro_usd), "
                    "SUM(record_status='complete' AND terminal_outcome='completed') FROM trace_runs"
                ).fetchone()
                stages = connection.execute("SELECT COUNT(*) FROM trace_stage_events").fetchone()[0]
                if (count, dispatch, cost, complete, stages) != (100, 100, 0, 100, 1400):
                    raise RuntimeError("Synthetic trace completeness failure")
                counts.update(traces=count, stages=stages, dispatch=dispatch, cost=cost)
            elif name == "business":
                counts["relationship_events"] = connection.execute(
                    "SELECT COUNT(*) FROM relationship_events"
                ).fetchone()[0]
                counts["long_term_memories"] = connection.execute(
                    "SELECT COUNT(*) FROM long_term_memories"
                ).fetchone()[0]
                if counts["relationship_events"] != 100:
                    raise RuntimeError("Synthetic business write failure")
            else:
                counts["settlements"] = connection.execute(
                    "SELECT COUNT(*) FROM budget_settlements"
                ).fetchone()[0]
                if counts["settlements"] != (100 if control_on else 0):
                    raise RuntimeError("Synthetic settlement ownership failure")
    return counts


CASE_LABELS = (
    "http-off-single",
    "http-on-single",
    "http-off-pair",
    "http-on-pair",
    "memory-off",
    "memory-on",
)

V9_BATCHES = ("profile-01", "plain-01")


def v9_manifest() -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    directories = [
        APPROVED_ROOT,
        APPROVED_ROOT / "tmp",
        APPROVED_ROOT / "pytest-red-01",
        APPROVED_ROOT / "pytest-green-01",
    ]
    files = []
    for batch in V9_BATCHES:
        directories.append(APPROVED_ROOT / batch)
        for label in CASE_LABELS:
            root = APPROVED_ROOT / batch / label
            directories.append(root)
            files.append(root.with_suffix(".json"))
            if label.startswith("http"):
                files.extend(
                    root / (name + ".sqlite3" + suffix)
                    for name in ("business", "control", "observability")
                    for suffix in ("", "-wal", "-shm")
                )
    return tuple(directories), tuple(files)


@contextmanager
def fixed_client_temp() -> Iterator[None]:
    """Run the unchanged independent client with explicit tempfile initialization."""
    import sys

    original = asyncio.create_subprocess_exec

    async def create(*args: Any, **kwargs: Any) -> Any:
        expected = (sys.executable, "-B", "-m", "scripts.f009_step5_steady_profile", "--client-url")
        if args[:5] != expected or len(args) != 6:
            raise ValueError("V9 client command is invalid")
        bootstrap = (
            "import os,sys,tempfile,runpy;"
            "tempfile.tempdir=os.environ['TEMP'];"
            "sys.argv=['scripts.f009_step5_steady_profile',*sys.argv[1:]];"
            "runpy.run_module('scripts.f009_step5_steady_profile',run_name='__main__')"
        )
        return await original(sys.executable, "-B", "-c", bootstrap, *args[4:], **kwargs)

    with patch.object(asyncio, "create_subprocess_exec", create):
        yield


async def diagnostic_case(root: Path, label: str, *, profiled: bool) -> dict[str, Any]:
    if label not in CASE_LABELS or not root.is_dir() or tuple(root.iterdir()):
        raise ValueError("Diagnostic case directory is invalid")
    probe = DiagnosticProbe() if profiled else None
    with ExitStack() as stack:
        stack.enter_context(fixed_client_temp())
        if probe is not None:
            stack.enter_context(probe.instrument())
        if label.startswith("memory"):
            result = await memory_diagnostic(root, recorded=label.endswith("on"), probe=probe)
        else:
            result = await http_diagnostic(
                root,
                control_on="-on-" in label,
                parallelism=1 if label.endswith("single") else 2,
                probe=probe,
            )
    checks = (
        {} if label.startswith("memory") else check_http_databases(root, control_on="-on-" in label)
    )
    rows = () if probe is None else probe.snapshot()
    if (
        probe is not None
        and label.startswith("http")
        and set(probe.arrival_to_request.values()) != set(range(1, 101))
    ):
        raise RuntimeError("Synthetic request association is incomplete")
    summaries: dict[int, dict[str, Any]] = {}
    if probe is not None:
        expected = 1000 if label.startswith("memory") else 100
        grouped: dict[int, list[dict[str, Any]]] = {}
        by_id = {row["operation_index"]: row for row in rows}
        for row in rows:
            index = cast(int, row["case_index"])
            if not (0 <= index <= expected or index == 100001):
                raise RuntimeError("Synthetic request association is incomplete")
            grouped.setdefault(index, []).append(row)
            parent = row["parent_index"]
            if parent is not None and (parent not in by_id or by_id[parent]["case_index"] != index):
                raise RuntimeError("Synthetic parent association is incomplete")
            storage = row["storage_index"]
            if storage is not None and (
                storage not in by_id
                or by_id[storage]["operation"] != "storage"
                or by_id[storage]["case_index"] != index
            ):
                raise RuntimeError("Synthetic storage association is incomplete")
        if not set(range(1, expected + 1)).issubset(grouped):
            raise RuntimeError("Synthetic request association is incomplete")
        summaries = {index: summarize_spans(values) for index, values in grouped.items()}
        if label.startswith("memory") and (
            len(probe.vm) != 1000 or {row["case_index"] for row in probe.vm} != set(range(1, 1001))
        ):
            raise RuntimeError("Synthetic budget association is incomplete")
    return {
        "schema_version": SCHEMA_VERSION,
        "case": label,
        "profiled": profiled,
        "is_final_gate": False,
        "result": result,
        "checks": checks,
        "spans": rows,
        "per_request_attribution": summaries,
        "request_association_complete": probe is not None,
        "vm_steps": [] if probe is None else probe.vm,
        "vm_error_per_query_less_than": 1000,
        "timing_note": "nested spans require interval union; setup=0 teardown=100001",
    }


async def run_v9_batch(batch: str, *, registered: tuple[Path, ...]) -> None:
    """Exactly six fresh cases; exclusive output creation prevents repeat batches."""
    import json

    if batch not in V9_BATCHES:
        raise ValueError("V9 batch is invalid")
    directories, files = v9_manifest()
    required = tuple(
        path for path in (*directories, *files) if path.is_relative_to(APPROVED_ROOT / batch)
    )
    if any(path not in registered for path in required):
        raise ValueError("V9 resource registration is incomplete")
    for label in CASE_LABELS:
        root = APPROVED_ROOT / batch / label
        if not root.is_dir() or tuple(root.iterdir()) or root.with_suffix(".json").exists():
            raise ValueError("V9 batch is not fresh")
    for label in CASE_LABELS:
        root = APPROVED_ROOT / batch / label
        report = await diagnostic_case(root, label, profiled=batch == "profile-01")
        with root.with_suffix(".json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, sort_keys=True, separators=(",", ":"))
        print(
            json.dumps(
                {
                    "batch": batch,
                    "case": label,
                    "latency": report["result"]["latency"],
                    "checks": report["checks"],
                }
            ),
            flush=True,
        )


# V10 candidate A is diagnostic-only: no product constant or composition is changed.
V10_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v10-budget-equivalence")
V10_CASES = ("current-off", "current-on", "candidate-off", "candidate-on")
V10_SEMANTIC_LABELS = (
    "matrix",
    *(
        f"{variant}-{scenario}"
        for variant in ("current", "candidate")
        for scenario in (
            "replay",
            "release",
            "conservative",
            "restart",
            "attempt-warning",
            "expiry",
            "cost-warning",
            "concurrency",
            "one-query",
            "repository-fault",
            "constraint-null",
            "constraint-duplicate",
            "constraint-bad_status",
            "constraint-bad_type",
            *(f"order-{index}" for index in range(12)),
        )
    ),
)
V10_CANDIDATE_SQL = (
    "SELECT "
    + ", ".join(
        "COALESCE(" + expression + (f" FILTER (WHERE {condition})" if condition else "") + ", 0)"
        for condition in ("match_player_npc", "match_player", "match_npc", "")
        for expression in ("SUM(hour_hit)", "COUNT(*)", "SUM(row_cost)")
    )
    + " FROM (SELECT "
    "o.player_npc_scope_tag = :player_npc AS match_player_npc, "
    "o.player_scope_tag = :player AS match_player, "
    "o.npc_scope_tag = :npc AS match_npc, "
    "r.reserved_at_ns > :hour AS hour_hit, "
    "CASE WHEN r.status = 'settled' THEN s.actual_cost_micro_usd "
    "ELSE r.reserved_micro_usd END AS row_cost "
    "FROM budget_reservations r JOIN budget_execution_owners o USING (execution_id) "
    "LEFT JOIN budget_settlements s USING (execution_id, attempt_number) "
    "WHERE r.reserved_at_ns > :day AND r.status <> 'released' LIMIT -1 OFFSET 0)"
)


def synthetic_budget_totals(
    connection: sqlite3.Connection, *, scope_tags: Any, now_ns: int
) -> dict[str, tuple[int, int, int]]:
    """Only explicit synthetic factories may select this coroutine candidate."""
    row = connection.execute(
        V10_CANDIDATE_SQL,
        {
            "hour": now_ns - 3_600_000_000_000,
            "day": now_ns - 86_400_000_000_000,
            "player_npc": scope_tags.player_npc_scope_tag,
            "player": scope_tags.player_scope_tag,
            "npc": scope_tags.npc_scope_tag,
        },
    ).fetchone()
    return {
        scope: (int(row[index * 3]), int(row[index * 3 + 1]), int(row[index * 3 + 2]))
        for index, scope in enumerate(("player_npc", "player", "npc", "global"))
    }


def require_budget_equivalence(reference: Any, candidate: Any) -> None:
    expected = {"player_npc", "player", "npc", "global"}
    if (
        not all(
            type(value) is dict
            and set(value) == expected
            and all(
                type(row) is tuple and len(row) == 3 and all(type(item) is int for item in row)
                for row in value.values()
            )
            for value in (reference, candidate)
        )
        or reference != candidate
    ):
        raise ValueError("Synthetic budget equivalence failure")


def require_streaming_plan(opcodes: Sequence[str]) -> None:
    if not {"InitCoroutine", "Yield"}.issubset(opcodes) or {
        "OpenEphemeral",
        "SorterOpen",
        "OpenAutoindex",
        "VOpen",
        "VUpdate",
    }.intersection(opcodes):
        raise ValueError("Synthetic budget plan is not streaming")


def v10_manifest() -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    directories = [V10_ROOT, V10_ROOT / "tmp"]
    files: list[Path] = []
    for batch in ("red-01", "green-01"):
        directories.extend((V10_ROOT / ("pytest-" + batch), V10_ROOT / ("semantics-" + batch)))
        for label in V10_SEMANTIC_LABELS:
            root = V10_ROOT / ("semantics-" + batch) / label
            directories.append(root)
            files.extend(root / ("control.sqlite3" + suffix) for suffix in ("", "-wal", "-shm"))
    for batch in V9_BATCHES:
        directories.append(V10_ROOT / batch)
        for label in V10_CASES:
            root = V10_ROOT / batch / label
            directories.append(root)
            files.append(root.with_suffix(".json"))
    return tuple(directories), tuple(files)


def v10_case_spec(batch: str, label: str) -> tuple[bool, bool, bool, int]:
    if batch not in V9_BATCHES or label not in V10_CASES:
        raise ValueError("Synthetic V10 case is invalid")
    return label.startswith("candidate"), label.endswith("on"), batch == "profile-01", 1000


def prepare_v10_batch(batch: str, *, registered: tuple[Path, ...]) -> None:
    """Validate before caller creates anything; never creates paths itself."""
    if batch not in V9_BATCHES:
        raise ValueError("Synthetic V10 batch is invalid")
    directories, files = v10_manifest()
    required = tuple(
        path for path in (*directories, *files) if path.is_relative_to(V10_ROOT / batch)
    )
    if any(path not in registered for path in required):
        raise ValueError("Synthetic V10 registration is incomplete")
    for label in V10_CASES:
        root = V10_ROOT / batch / label
        if not root.is_dir() or tuple(root.iterdir()) or root.with_suffix(".json").exists():
            raise ValueError("Synthetic V10 batch is not fresh")


async def run_v10_batch(batch: str, *, registered: tuple[Path, ...]) -> None:
    """One bounded group; probes only in profile, unchanged complete memory workload."""
    import json

    from scripts import f009_step5_benchmark as bench

    prepare_v10_batch(batch, registered=registered)
    original = SqliteSafetyControlRepository._all_window_totals
    for label in V10_CASES:
        candidate, recorded, profiled, count = v10_case_spec(batch, label)
        probe = DiagnosticProbe() if profiled else None
        selected = synthetic_budget_totals if candidate else original

        def measured(
            connection: sqlite3.Connection,
            active_probe: DiagnosticProbe | None = probe,
            query: Any = selected,
            **kwargs: Any,
        ) -> Any:
            assert active_probe is not None
            steps = 0

            def progress() -> int:
                nonlocal steps
                steps += 1000
                return 0

            connection.set_progress_handler(progress, 1000)
            try:
                return active_probe.measure(
                    Operation.BUDGET_SCAN, lambda: query(connection, **kwargs)
                )
            finally:
                connection.set_progress_handler(None, 0)
                active_probe.vm.append(
                    {"case_index": active_probe.context.get()[0], "steps_lower": steps}
                )

        with ExitStack() as stack:
            if probe is not None:
                stack.enter_context(probe.instrument())
            # Explicit isolated benchmark subclass; never the product repository default.
            stack.enter_context(
                patch.object(
                    bench._MemoryControl,
                    "_all_window_totals",
                    staticmethod(measured if probe is not None else selected),
                )
            )
            result = await memory_diagnostic(
                V10_ROOT / batch / label, recorded=recorded, probe=probe
            )
        rows = () if probe is None else probe.snapshot()
        if probe is not None and (
            len(probe.vm) != count
            or {row["case_index"] for row in probe.vm} != set(range(1, count + 1))
        ):
            raise RuntimeError("Synthetic V10 budget association failure")
        report = {
            "schema_version": SCHEMA_VERSION,
            "candidate_version": "v10-coroutine-a-v1",
            "batch": batch,
            "case": label,
            "profiled": profiled,
            "is_final_gate": False,
            "result": result,
            "spans": rows,
            "vm_steps": [] if probe is None else probe.vm,
            "vm_error_per_query_less_than": 1000,
            "timing_note": "plain only per-execution timing; nested profile intervals not additive",
        }
        with (V10_ROOT / batch / label).with_suffix(".json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, sort_keys=True, separators=(",", ":"))
        print(
            json.dumps(
                {
                    "batch": batch,
                    "case": label,
                    "latency": result["latency"],
                    "checks": result["checks"],
                }
            ),
            flush=True,
        )


V20_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v20-control-fixed-cost-attribution"
)
V20_HOTSPOTS = (
    Operation.INGRESS_ADMISSION.value,
    Operation.EXECUTION_ADMISSION.value,
    Operation.BUDGET_RESERVATION.value,
    Operation.BUDGET_SETTLEMENT.value,
    Operation.PROVIDER_PERMIT_ACQUIRE.value,
)
V20_CATEGORY_OPERATIONS = {
    "transaction_framework_ms": frozenset(
        {
            Operation.BEGIN.value,
            Operation.COMMIT.value,
            Operation.WRITE_COMMIT.value,
            Operation.CLOSE.value,
        }
    ),
    "sql_ms": frozenset({Operation.SQL.value}),
    "hmac_dto_ms": frozenset(
        {
            Operation.SCOPE_TAG.value,
            Operation.BUDGET_DTO.value,
            Operation.PERMIT_DTO.value,
        }
    ),
}


def v20_manifest() -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    return (
        (
            V20_ROOT,
            V20_ROOT / "tmp",
            V20_ROOT / "pytest-red-01",
            V20_ROOT / "pytest-green-01",
            V20_ROOT / "attribution-01",
            V20_ROOT / "attribution-02",
        ),
        (
            V20_ROOT / "attribution-01" / "baseline.json",
            V20_ROOT / "attribution-01" / "recorded.json",
            V20_ROOT / "attribution-02" / "baseline.json",
            V20_ROOT / "attribution-02" / "recorded.json",
            V20_ROOT / "summary-02.json",
        ),
    )


def _span_interval(row: dict[str, object]) -> tuple[int, int]:
    start, end = row.get("start_ns"), row.get("end_ns")
    if type(start) is not int or type(end) is not int or start > end:
        raise ValueError("V20 attribution interval is invalid")
    return start, end


def partition_v20_fixed_costs(
    rows: Sequence[dict[str, object]],
    *,
    required_hotspots: Sequence[str] = V20_HOTSPOTS,
) -> dict[int, dict[str, dict[str, float]]]:
    """Partition five hotspot intervals without adding nested inclusive durations."""
    if not rows or not required_hotspots or len(set(required_hotspots)) != len(required_hotspots):
        raise ValueError("V20 hotspot ownership is invalid")
    by_index: dict[int, dict[str, object]] = {}
    for row in rows:
        operation_index = row.get("operation_index")
        case_index = row.get("case_index")
        if (
            type(operation_index) is not int
            or operation_index in by_index
            or type(case_index) is not int
            or case_index < 0
            or not isinstance(row.get("operation"), str)
        ):
            raise ValueError("V20 attribution metadata is invalid")
        _span_interval(row)
        by_index[operation_index] = row
    for row in rows:
        parent = row.get("parent_index")
        if parent is None or parent not in by_index:
            continue
        if by_index[parent]["case_index"] != row["case_index"]:
            raise ValueError("V20 parent ownership is invalid")

    cases: list[int] = sorted(
        {cast(int, row["case_index"]) for row in rows if row["operation"] in required_hotspots}
    )
    if not cases:
        raise ValueError("V20 hotspot ownership is invalid")
    result: dict[int, dict[str, dict[str, float]]] = {}
    for case_index in cases:
        case_rows = [row for row in rows if row["case_index"] == case_index]
        case_result: dict[str, dict[str, float]] = {}
        for hotspot in required_hotspots:
            roots = [row for row in case_rows if row["operation"] == hotspot]
            if len(roots) != 1:
                raise ValueError("V20 hotspot ownership is invalid")
            root = roots[0]
            root_index = cast(int, root["operation_index"])
            root_start, root_end = _span_interval(root)

            def belongs_to_root(
                row: dict[str, object],
                *,
                active_root: int = root_index,
                active_case: int = cast(int, case_index),
            ) -> bool:
                parent = row.get("parent_index")
                visited: set[int] = set()
                while type(parent) is int and parent not in visited:
                    if parent == active_root:
                        return True
                    visited.add(parent)
                    owner = by_index.get(parent)
                    if owner is None or owner["case_index"] != active_case:
                        return False
                    parent = owner.get("parent_index")
                return False

            descendants = [row for row in case_rows if belongs_to_root(row)]
            category_intervals: dict[str, list[tuple[int, int]]] = {
                name: [] for name in V20_CATEGORY_OPERATIONS
            }
            for row in descendants:
                for name, operations in V20_CATEGORY_OPERATIONS.items():
                    if row["operation"] in operations:
                        category_intervals[name].append(_span_interval(row))
            categorized = [
                interval for intervals in category_intervals.values() for interval in intervals
            ]
            total_ns = root_end - root_start
            covered_ns = union_duration(categorized)
            if covered_ns > total_ns:
                raise ValueError("V20 attribution intervals overlap the hotspot boundary")
            metrics = {
                "total_ms": round(total_ns / 1_000_000, 9),
                **{
                    name: round(union_duration(intervals) / 1_000_000, 9)
                    for name, intervals in category_intervals.items()
                },
                "python_orchestration_ms": round((total_ns - covered_ns) / 1_000_000, 9),
            }
            case_result[hotspot] = metrics
        result[case_index] = case_result
    return result


def _summarize_v20_partition(
    partition: dict[int, dict[str, dict[str, float]]],
) -> dict[str, object]:
    if set(partition) != set(range(1, 1001)):
        raise ValueError("V20 request ownership is incomplete")
    summary: dict[str, object] = {}
    for hotspot in V20_HOTSPOTS:
        metrics: dict[str, object] = {}
        for metric in (
            "total_ms",
            "transaction_framework_ms",
            "sql_ms",
            "hmac_dto_ms",
            "python_orchestration_ms",
        ):
            samples = [partition[index][hotspot][metric] for index in range(1, 1001)]
            metrics[metric] = {**latency_summary(samples), "mean_ms": mean(samples)}
        summary[hotspot] = metrics
    return summary


def _aggregate_v20_runs(runs: Sequence[dict[str, object]]) -> dict[str, object]:
    if len(runs) != 5:
        raise ValueError("V20 measured run count is invalid")
    result: dict[str, object] = {}
    for hotspot in V20_HOTSPOTS:
        hotspot_result: dict[str, object] = {}
        for metric in (
            "total_ms",
            "transaction_framework_ms",
            "sql_ms",
            "hmac_dto_ms",
            "python_orchestration_ms",
        ):
            rows = [
                cast(dict[str, Any], cast(dict[str, Any], run[hotspot])[metric]) for run in runs
            ]
            hotspot_result[metric] = {
                key: median(float(row[key]) for row in rows)
                for key in ("mean_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms")
            }
        result[hotspot] = hotspot_result
    return result


def _validate_v20_paths() -> None:
    directories, files = v20_manifest()
    if not V20_ROOT.is_dir() or not (V20_ROOT / "tmp").is_dir():
        raise ValueError("V20 root is unavailable")
    for path in (*directories, *files):
        if not path.is_absolute() or not path.is_relative_to(V20_ROOT):
            raise ValueError("V20 resource boundary is invalid")
        for ancestor in (path, *path.parents):
            if not ancestor.exists():
                continue
            info = ancestor.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("V20 resource boundary is invalid")
    if not (V20_ROOT / "attribution-01").is_dir() or tuple((V20_ROOT / "attribution-01").iterdir()):
        raise ValueError("V20 aborted attribution evidence is invalid")
    if (V20_ROOT / "attribution-02").exists() or (V20_ROOT / "summary-02.json").exists():
        raise ValueError("V20 attribution output is not fresh")


async def run_v20_fixed_cost_attribution() -> dict[str, object]:
    """Run one bounded non-gating attribution group on the V19 synthetic candidate."""
    import json

    from scripts import f009_step5_benchmark as bench
    from scripts.f009_step5_budget_projection_preflight import (
        SingleWriteCandidateMemoryControl,
    )

    _validate_v20_paths()
    directories, files = v20_manifest()
    for path in (*directories, *files):
        print(str(path.resolve(strict=False)), flush=True)
    output_root = V20_ROOT / "attribution-02"
    output_root.mkdir()
    reports: dict[str, list[dict[str, object]]] = {"baseline": [], "recorded": []}
    warmup: dict[str, dict[str, object]] = {}
    for pair_index in range(6):
        for scenario, recorded in (("baseline", False), ("recorded", True)):
            probe = DiagnosticProbe()
            with ExitStack() as stack:
                stack.enter_context(probe.instrument())
                stack.enter_context(
                    patch.object(bench, "_MemoryControl", SingleWriteCandidateMemoryControl)
                )
                workload = await memory_diagnostic(output_root, recorded=recorded, probe=probe)
            partition = partition_v20_fixed_costs(probe.snapshot())
            summary = _summarize_v20_partition(partition)
            report = {
                "pair_index": pair_index,
                "scenario": scenario,
                "warmup": pair_index == 0,
                "request_count": 1000,
                "provider_dispatch_count": workload["provider_dispatch_count"],
                "checks": workload["checks"],
                "latency": workload["latency"],
                "hotspots": summary,
            }
            if pair_index == 0:
                warmup[scenario] = report
            else:
                reports[scenario].append(report)
    output: dict[str, object] = {
        "schema_version": 1,
        "status": "attribution_complete",
        "is_final_gate": False,
        "candidate": "v19-single-write-rolling-projection",
        "protocol": {
            "warmup_pairs": 1,
            "measured_pairs": 5,
            "pair_order": ["baseline", "recorded"],
            "execution_per_scenario": 1000,
        },
        "warmup": warmup,
        "measured": reports,
        "aggregates": {
            scenario: _aggregate_v20_runs(
                [cast(dict[str, object], report["hotspots"]) for report in scenario_reports]
            )
            for scenario, scenario_reports in reports.items()
        },
        "privacy_forbidden_hits": 0,
        "product_0005_created": False,
    }
    privacy = json.dumps(output, sort_keys=True)
    forbidden = (
        "bench_player_0000",
        "Synthetic local benchmark.",
        "Synthetic local diagnostic persona.",
        "f009-synthetic-scope-key-32bytes!!",
    )
    hits = sum(privacy.count(value) for value in forbidden)
    output["privacy_forbidden_hits"] = hits
    if hits:
        raise RuntimeError("V20 sensitive metadata boundary failed")
    for scenario in ("baseline", "recorded"):
        with (output_root / f"{scenario}.json").open("x", encoding="utf-8") as stream:
            json.dump(
                {"scenario": scenario, "runs": reports[scenario]},
                stream,
                sort_keys=True,
                separators=(",", ":"),
            )
    with (V20_ROOT / "summary-02.json").open("x", encoding="utf-8") as stream:
        json.dump(output, stream, sort_keys=True, indent=2)
    return output
