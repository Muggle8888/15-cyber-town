"""Run the approved local-only F-009 Step 5 performance gate."""

from __future__ import annotations

import argparse
import asyncio
import gc
import hashlib
import json
import math
import os
import socket
import sqlite3
import stat
import statistics
import tempfile
import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager, closing, contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from threading import Lock as ThreadLock
from typing import Any, cast
from uuid import UUID, uuid4

import httpx
import uvicorn

from cyber_town.api.app import create_app
from cyber_town.application.budget import BudgetRejectedError, PricingPolicy
from cyber_town.application.control import (
    CircuitOpenError,
    NoOpSafetyControl,
    RateLimitExceededError,
    SafetyControl,
)
from cyber_town.application.control_performance import (
    CONTROL_ON_P95_FAILURE_DELTA_MS,
    PerformanceRun,
    PerformanceScenario,
    evaluate_performance_gate,
    evaluate_performance_warnings,
    evaluate_three_sqlite_diagnostic,
    summarize_performance_runs,
)
from cyber_town.application.dialogue import DialogueExecutionConfig, DialogueService
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.observability import (
    OBSERVABILITY_SCHEMA_VERSION,
    AttemptKind,
    IdempotencyOutcome,
    InMemoryObservabilityRecorder,
    LongTermOutcome,
    NoOpObservabilityRecorder,
    ObservabilityRecorder,
    ProviderKind,
    RecordStatus,
    RelationshipOutcome,
    ScopeTags,
    ShortTermOutcome,
    StageOutcome,
    TerminalOutcome,
    TraceErrorCode,
    TraceMetadata,
    TraceReasonCode,
    TraceStage,
    TraceStageMetadata,
)
from cyber_town.application.provider import ProviderCompletion, ProviderRequest, ProviderUsage
from cyber_town.application.relationship import RelationshipService
from cyber_town.application.retry import BreakerFailureReason
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control import sqlite_control as control_module
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import (
    SqliteRelationshipRepository,
)

SYNTHETIC_KEY = b"f009-step5-synthetic-performance-key-v1"
RUN_COUNT = 5
MEMORY_TRACE_COUNT = 1_000
SQLITE_TRACE_COUNT = 100
RUN_DETAILS: dict[str, object] = {}
_INDEPENDENT_CLIENT = False
V11_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v11-runtime-boundary")
CORE_REVALIDATION_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v29-memory-gate-revision"
)
V21_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v21-control-durable-boundary")
V24_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v24-execution-intent-product")
V24_TCP_DIRECTORY = "tcp-1plus5-retry-01"
V26_PRODUCT_SPACE_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v26-control-space-product-gate2"
)
V13_E_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v13-storage-ab\e-usb")
V13_C_ROOT = Path(r"C:\Users\24696\AppData\Local\Temp\cyber-town-f009-v13-storage-ab\c-nvme")
V13_COMPARISON = V13_E_ROOT.parent / "storage-ab-comparison.json"
V13_REQUEST_ID_SEED = 13_000
V15_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v15-protocol-attribution")
MEMORY_PROTOCOL_VERSION = "f-009-memory-control-protocol-v2"
MEMORY_PROTOCOL_PAIR = ("no_recorder_control", "in_memory_control")
MEMORY_PROTOCOL_WARMUP_PAIRS = 1
MEMORY_STAGE_ALLOWLIST = (
    "ingress_admission",
    "provider_dispatch_admission",
    "provider_completion",
    "provider_success_finalization",
    "observability_stage_records",
    "observability_terminal_record",
)
MEMORY_PROTOCOL_RUNTIME_RUNS: list[dict[str, object]] = []


def v26_product_space_manifest(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    directories = [
        root,
        root / "tmp",
        root / "pytest-red-01",
        root / "pytest-green-01",
        root / "pytest-regression-01",
        root / "space-gate-01",
    ]
    files: list[Path] = [root / "summary.json"]
    for pair in range(1, RUN_COUNT + 1):
        pair_root = root / f"space-pair-{pair:02d}"
        directories.append(pair_root)
        for variant in ("baseline-v6", "product-v7"):
            directory = pair_root / variant
            database = directory / "control.sqlite3"
            directories.append(directory)
            files.extend((database, Path(str(database) + "-wal"), Path(str(database) + "-shm")))
    return tuple(directories), tuple(files)


def _v26_product_space_pair_failures(
    *,
    baseline_growth_bytes: int,
    product_growth_bytes: int,
    product_candidate_index_pages: int,
    baseline_digest: str,
    product_digest: str,
) -> tuple[str, ...]:
    failures: list[str] = []
    if product_growth_bytes > 256 * 1024:
        failures.append("product_control_growth_exceeded")
    if product_candidate_index_pages != 0:
        failures.append("product_index_still_present")
    if baseline_digest != product_digest:
        failures.append("product_logical_digest_mismatch")
    if baseline_growth_bytes - product_growth_bytes < 2 * 4096:
        failures.append("product_space_saving_below_8192")
    return tuple(failures)


def memory_protocol_config() -> dict[str, object]:
    """Return the single protocol shared by preflight and the core matrix."""

    return {
        "protocol_version": MEMORY_PROTOCOL_VERSION,
        "warmup_pair_count": MEMORY_PROTOCOL_WARMUP_PAIRS,
        "measured_pair_count": RUN_COUNT,
        "pair_order": list(MEMORY_PROTOCOL_PAIR),
        "execution_per_run": MEMORY_TRACE_COUNT,
        "percentile_aggregation": "median_of_five_run_level_percentiles",
        "stage_attribution_blocks_gate": False,
    }


@dataclass(frozen=True, slots=True)
class MemoryProtocolResult:
    baseline_runs: tuple[PerformanceRun, ...]
    recorded_runs: tuple[PerformanceRun, ...]
    runtime_runs: tuple[dict[str, object], ...]


class _MemoryStageProbe:
    def __init__(self) -> None:
        self._samples: dict[str, list[float]] = {stage: [] for stage in MEMORY_STAGE_ALLOWLIST}

    def run(self, stage: str, operation: Callable[[], Any]) -> Any:
        if stage not in self._samples:
            raise ValueError("Memory stage is not allowlisted")
        started = time.perf_counter_ns()
        try:
            return operation()
        finally:
            self._samples[stage].append((time.perf_counter_ns() - started) / 1_000_000)

    async def run_async(self, stage: str, operation: Callable[[], Awaitable[Any]]) -> Any:
        if stage not in self._samples:
            raise ValueError("Memory stage is not allowlisted")
        started = time.perf_counter_ns()
        try:
            return await operation()
        finally:
            self._samples[stage].append((time.perf_counter_ns() - started) / 1_000_000)

    def summary(self) -> dict[str, dict[str, int | float]]:
        return {stage: _percentile_summary(samples) for stage, samples in self._samples.items()}


def storage_ab_manifest(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Return the exact registered V13 surface without creating it."""

    directories = [root, root / "tmp"]
    files: list[Path] = []
    for mode in ("off", "on"):
        for index in range(RUN_COUNT + 1):
            run_root = root / f"loopback-{mode}-{index}"
            directories.append(run_root)
            for database in ("business", "control"):
                database_path = run_root / f"{database}.sqlite3"
                files.extend(
                    (
                        database_path,
                        Path(f"{database_path}-wal"),
                        Path(f"{database_path}-shm"),
                    )
                )
    files.append(root / "performance-summary.json")
    return tuple(directories), tuple(files)


def _storage_ab_config() -> dict[str, object]:
    return {
        "concurrency": 2,
        "executions_per_run": SQLITE_TRACE_COUNT,
        "fake_provider": True,
        "observability_mode": "noop",
        "request_id_seed": V13_REQUEST_ID_SEED,
        "run_count": RUN_COUNT,
        "scenario_order": ["control_off", "control_on"],
        "schema_version": 1,
        "synchronous": "full",
        "transport": "tcp_independent_client_process",
        "wal": True,
        "warmup_runs": 1,
    }


def _storage_ab_config_digest() -> str:
    payload = json.dumps(_storage_ab_config(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_reparse_point(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _validate_storage_ab_root(root: Path, approved: Path) -> None:
    try:
        resolved = root.resolve(strict=True)
        approved_resolved = approved.resolve(strict=True)
    except OSError:
        raise ValueError("Storage A/B root is not approved") from None
    if resolved != approved_resolved or root != resolved:
        raise ValueError("Storage A/B root is not approved")
    for current in (resolved, *resolved.parents):
        if _is_reparse_point(current):
            raise ValueError("Storage A/B root crosses a reparse boundary")
    directories, files = storage_ab_manifest(resolved)
    if not (resolved / "tmp").is_dir():
        raise ValueError("Storage A/B root is not fresh")
    allowed_children = {resolved / "tmp"}
    if set(resolved.iterdir()) != allowed_children:
        raise ValueError("Storage A/B root is not fresh")
    if any(path.exists() for path in directories[2:]) or any(path.exists() for path in files):
        raise ValueError("Storage A/B root is not fresh")


def _percentile_summary(samples: list[float]) -> dict[str, int | float]:
    if not samples:
        return {
            "count": 0,
            "total_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
        }
    ordered = sorted(samples)

    def value(fraction: float) -> float:
        return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]

    return {
        "count": len(ordered),
        "total_ms": round(sum(ordered), 6),
        "p50_ms": round(value(0.50), 6),
        "p95_ms": round(value(0.95), 6),
        "p99_ms": round(value(0.99), 6),
        "max_ms": round(ordered[-1], 6),
    }


class _StorageTimingProbe:
    """Aggregate storage timings without recording SQL, paths, or identifiers."""

    def __init__(self) -> None:
        self._lock = ThreadLock()
        self._samples: dict[str, list[float]] = {
            key: []
            for key in ("writer_wait", "path_check", "connect", "write_commit", "empty_commit")
        }

    def _measure[T](self, key: str, action: Callable[[], T]) -> T:
        started = time.perf_counter()
        try:
            return action()
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            with self._lock:
                self._samples[key].append(elapsed)

    def summary(self) -> dict[str, dict[str, int | float]]:
        with self._lock:
            return {key: _percentile_summary(list(values)) for key, values in self._samples.items()}

    @contextmanager
    def instrument(self) -> Iterator[None]:
        from cyber_town.infrastructure.persistence import sqlite_connection as writer

        probe = self
        lock_attribute = "Lock"
        connect_attribute = "connect"
        original_lock = getattr(writer, lock_attribute)
        original_validate = writer.validate_sqlite_path
        original_connect = sqlite3.connect

        class MeasuredLock:
            def __init__(self) -> None:
                self._value = ThreadLock()

            def acquire(self, *args: Any, **kwargs: Any) -> bool:
                return probe._measure("writer_wait", lambda: self._value.acquire(*args, **kwargs))

            def release(self) -> None:
                self._value.release()

            def __enter__(self) -> MeasuredLock:
                self.acquire()
                return self

            def __exit__(self, *args: Any) -> None:
                self.release()

        def measured_validate(path: Path, allowed_root: Path) -> Any:
            return probe._measure("path_check", lambda: original_validate(path, allowed_root))

        def measured_connect(database: Any, *args: Any, **kwargs: Any) -> sqlite3.Connection:
            factory = kwargs.pop("factory", sqlite3.Connection)

            class MeasuredConnection(factory):  # type: ignore[misc,valid-type]
                begin_changes = 0

                def execute(self, sql: str, parameters: Any = (), /) -> Any:
                    if sql.lstrip().upper().startswith("BEGIN"):
                        self.begin_changes = self.total_changes
                    return super().execute(sql, parameters)

                def commit(self) -> None:
                    key = (
                        "write_commit"
                        if self.in_transaction and self.total_changes > self.begin_changes
                        else "empty_commit"
                    )
                    probe._measure(key, super().commit)

                def __exit__(self, *args: Any) -> Any:
                    if not self.in_transaction or args[0] is not None:
                        return super().__exit__(*args)
                    key = (
                        "write_commit"
                        if self.total_changes > self.begin_changes
                        else "empty_commit"
                    )
                    return probe._measure(
                        key, lambda: super(MeasuredConnection, self).__exit__(*args)
                    )

            return probe._measure(
                "connect",
                lambda: original_connect(database, *args, factory=MeasuredConnection, **kwargs),
            )

        setattr(writer, lock_attribute, MeasuredLock)
        writer.validate_sqlite_path = measured_validate
        setattr(sqlite3, connect_attribute, measured_connect)
        try:
            yield
        finally:
            setattr(sqlite3, connect_attribute, original_connect)
            writer.validate_sqlite_path = original_validate
            setattr(writer, lock_attribute, original_lock)


def runtime_boundary_manifest(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Return the exact V11 resource boundary without creating it."""

    case_root = root / "runtime-default-01"
    return (
        (root, root / "tmp", case_root),
        (
            case_root / "business.sqlite3",
            case_root / "business.sqlite3-wal",
            case_root / "business.sqlite3-shm",
            case_root / "control.sqlite3",
            case_root / "control.sqlite3-wal",
            case_root / "control.sqlite3-shm",
            case_root / "performance-summary.json",
        ),
    )


def gate_boundary_matrix_manifest(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Return the exact registered warm-up plus five-run resource boundary."""

    matrix_root = root / "full-matrix-01"
    directories = [matrix_root]
    files = [matrix_root / "performance-summary.json"]

    def add_database_group(label: str, databases: tuple[str, ...]) -> None:
        for index in range(RUN_COUNT + 1):
            run_root = matrix_root / f"{label}-{index}"
            directories.append(run_root)
            for database in databases:
                database_path = run_root / f"{database}.sqlite3"
                files.extend(
                    (
                        database_path,
                        Path(f"{database_path}-wal"),
                        Path(f"{database_path}-shm"),
                    )
                )

    add_database_group("sqlite-observability", ("observability",))
    for kind in ("rate", "budget", "breaker"):
        add_database_group(f"sqlite-reject-{kind}", ("control",))
    add_database_group("loopback-off", ("business", "control"))
    add_database_group("loopback-on", ("business", "control"))
    add_database_group(
        "loopback-three-sqlite",
        ("business", "control", "observability"),
    )
    return tuple(directories), tuple(files)


def memory_protocol_manifest(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    protocol_root = root / "protocol-01"
    return (
        (root, root / "tmp", protocol_root),
        (protocol_root / "summary-protocol-01.json",),
    )


class SyntheticClock:
    def __init__(self) -> None:
        self.now_ns = 2_000_000_000_000_000_000

    def time_ns(self) -> int:
        return self.now_ns

    def monotonic(self) -> float:
        return self.now_ns / 1_000_000_000

    def advance(self, seconds: float) -> None:
        self.now_ns += round(seconds * 1_000_000_000)


def _trace() -> TraceMetadata:
    started = datetime(2026, 8, 27, tzinfo=UTC)
    return TraceMetadata(
        schema_version=OBSERVABILITY_SCHEMA_VERSION,
        trace_id=uuid4(),
        request_id=uuid4(),
        execution_id=uuid4(),
        attempt_kind=AttemptKind.INITIAL,
        scope_tags=ScopeTags.from_identifiers(
            key=SYNTHETIC_KEY,
            player_id="synthetic_player",
            npc_id="neon_guide",
            conversation_id="00000000-0000-4000-8000-000000000001",
        ),
        persona_version="nia-v1",
        provider_kind=ProviderKind.FAKE,
        record_status=RecordStatus.COMPLETE,
        terminal_outcome=TerminalOutcome.COMPLETED,
        error_code=TraceErrorCode.NONE,
        reason_code=TraceReasonCode.COMPLETED,
        idempotency_outcome=IdempotencyOutcome.NEW,
        short_term_outcome=ShortTermOutcome.COMMITTED,
        long_term_outcome=LongTermOutcome.EMPTY,
        relationship_outcome=RelationshipOutcome.INERT,
        retryable=False,
        from_cache=False,
        provider_dispatch_count=1,
        started_at_utc=started,
        finished_at_utc=started + timedelta(milliseconds=1),
        total_latency_ms=1,
        provider_wait_ms=0,
        provider_latency_ms=0,
        context_budget_units=1,
        selected_short_term_turns=0,
        selected_long_term_facts=0,
        input_chars=1,
        output_chars=1,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        cost_micro_usd=0,
    )


def _stages(trace: TraceMetadata) -> tuple[TraceStageMetadata, ...]:
    assert trace.finished_at_utc is not None
    return tuple(
        TraceStageMetadata(
            schema_version=OBSERVABILITY_SCHEMA_VERSION,
            trace_id=trace.trace_id,
            stage=stage,
            sequence=sequence,
            outcome=StageOutcome.COMPLETED,
            reason_code=TraceReasonCode.COMPLETED,
            error_code=TraceErrorCode.NONE,
            started_at_utc=trace.started_at_utc,
            finished_at_utc=trace.finished_at_utc,
            latency_ms=0,
            item_count=0,
        )
        for sequence, stage in enumerate(TraceStage, start=1)
    )


def _measure_calls(action: Callable[[], None], count: int) -> PerformanceRun:
    samples: list[float] = []
    started = time.perf_counter()
    for _ in range(count):
        item_started = time.perf_counter()
        action()
        samples.append((time.perf_counter() - item_started) * 1_000)
    elapsed = time.perf_counter() - started
    return PerformanceRun(tuple(samples), float(count / elapsed))


def _database_size(root: Path) -> int:
    return sum(
        path.stat().st_size
        for path in root.rglob("*")
        if path.is_file() and ("sqlite3" in path.name or path.suffix in {".wal", ".shm"})
    )


def _snapshot(path: Path) -> dict[str, int]:
    # Only newly created, owned benchmark databases. No historical evidence reads.
    with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)) as connection:
        page_size = connection.execute("PRAGMA page_size").fetchone()[0]
        pages = connection.execute("PRAGMA page_count").fetchone()[0]
        free = connection.execute("PRAGMA freelist_count").fetchone()[0]
    return {
        "main_bytes": pages * page_size,
        "occupied_bytes": (pages - free) * page_size,
        "page_size": page_size,
        "pages": pages,
        "freelist": free,
        "file_bytes": path.stat().st_size,
        "wal_bytes": _surface_size(Path(str(path) + "-wal")),
        "shm_bytes": _surface_size(Path(str(path) + "-shm")),
    }


def _surface_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def _growth(before: dict[str, int], after: dict[str, int]) -> int:
    return max(
        0,
        after["main_bytes"] - before["main_bytes"],
        after["occupied_bytes"] - before["occupied_bytes"],
    )


def _combined_growth(before: dict[str, dict[str, int]], after: dict[str, dict[str, int]]) -> int:
    return sum(_growth(before[name], after[name]) for name in ("control", "observability"))


async def _timed_call(action: Callable[[], Awaitable[None]]) -> float:
    if _INDEPENDENT_CLIENT:
        from scripts.f009_step5_steady_profile import REMOTE_LATENCY

        latency_marker = REMOTE_LATENCY.set(None)
        started = time.perf_counter()
        try:
            await action()
            remote = REMOTE_LATENCY.get()
            return remote if remote is not None else (time.perf_counter() - started) * 1000
        finally:
            REMOTE_LATENCY.reset(latency_marker)
    started = time.perf_counter()
    await action()
    return (time.perf_counter() - started) * 1000


@asynccontextmanager
async def _http_client(
    service: DialogueService, recorder: ObservabilityRecorder | None
) -> AsyncIterator[Any]:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)
    listener.setblocking(False)
    port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(service, observability_recorder=recorder),
            host="127.0.0.1",
            port=port,
            access_log=False,
            log_config=None,
            log_level="critical",
            lifespan="off",
        )
    )
    task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        async with asyncio.timeout(10):
            while not server.started:
                if task.done():
                    raise RuntimeError("Synthetic loopback startup failed")
                await asyncio.sleep(0.01)
        url = f"http://127.0.0.1:{port}"
        if _INDEPENDENT_CLIENT:
            from scripts.f009_step5_steady_profile import _remote_client

            print(json.dumps({"endpoint": url, "client": "independent_process"}), flush=True)
            async with _remote_client(url) as remote:
                yield remote
        else:
            async with httpx.AsyncClient(base_url=url, trust_env=False, timeout=30) as client:
                yield client
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, 10)
        listener.close()


class _MemoryConnection(sqlite3.Connection):
    def close(self) -> None:
        if self.in_transaction:
            self.rollback()
        self.row_factory = None


class _MemoryControl(SqliteSafetyControlRepository):
    """Synthetic paired diagnostic only, never wired into product composition."""

    def __init__(self, root: Path) -> None:
        super().__init__(
            database_path=root / "not-created-memory-control.sqlite3", allowed_root=root
        )
        self.connection = sqlite3.connect(
            ":memory:", isolation_level=None, factory=_MemoryConnection
        )
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA trusted_schema=OFF")

    def _connect(self) -> sqlite3.Connection:
        composed = getattr(self._composed, "connection", None)
        if composed is not None:
            return cast(sqlite3.Connection, composed)
        return self.connection

    @contextmanager
    def _composed_transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            raw = self.connection
            raw.execute("BEGIN IMMEDIATE")
            self._composed.connection = control_module._ComposedTransactionConnection(raw)
            try:
                yield raw
            except BaseException:
                if raw.in_transaction:
                    raw.rollback()
                raise
            finally:
                del self._composed.connection
        except control_module.SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise control_module.SafetyControlStorageError from error

    def close(self) -> None:
        sqlite3.Connection.close(self.connection)


async def _memory_control_run(
    root: Path,
    recorder_factory: Callable[[], ObservabilityRecorder],
    *,
    stage_probe: _MemoryStageProbe | None = None,
) -> PerformanceRun:
    repository = _MemoryControl(root)
    repository.initialize()
    clock = SyntheticClock()
    control = SafetyControl(
        repository=repository,
        scope_key=SYNTHETIC_KEY,
        clock_ns=clock.time_ns,
        monotonic_clock=clock.monotonic,
        pricing_policy=PricingPolicy.zero_cost(provider_kind=ProviderKind.FAKE, model="fake-model"),
    )
    recorder = recorder_factory()
    provider = FakeProvider(_completion() for _ in range(MEMORY_TRACE_COUNT))
    traces = tuple(_trace() for _ in range(MEMORY_TRACE_COUNT))
    samples = []
    started = time.perf_counter()
    try:
        for index, trace in enumerate(traces):
            request = DialogueRequestV1(
                request_id=UUID(int=1000 + index),
                player_id=f"bench_player_{index:04d}",
                npc_id=("neon_guide", "signal_archivist", "night_courier")[index % 3],
                conversation_id=UUID(int=index + 1),
                message="Synthetic local benchmark.",
            )

            async def action(
                request: DialogueRequestV1 = request, trace: TraceMetadata = trace
            ) -> None:
                execution_id = trace.execution_id
                assert execution_id is not None
                provider_request = ProviderRequest(
                    system_prompt="Synthetic local diagnostic persona.",
                    user_message=request.message,
                    model="fake-model",
                    temperature=0.6,
                    max_tokens=256,
                    timeout_seconds=12,
                )
                if stage_probe is None:
                    control.admit_ingress(peer_host="127.0.0.1")
                    admission = await control.admit_provider_dispatch(
                        request=request, execution_id=execution_id, attempt_number=1
                    )
                    completion = await provider.complete(provider_request)
                    await control.finalize_provider_success(admission, usage=completion.usage)
                    for stage in _stages(trace):
                        recorder.record(stage)
                    recorder.record(trace)
                    return

                stage_probe.run(
                    "ingress_admission",
                    lambda: control.admit_ingress(peer_host="127.0.0.1"),
                )
                admission = await stage_probe.run_async(
                    "provider_dispatch_admission",
                    lambda: control.admit_provider_dispatch(
                        request=request, execution_id=execution_id, attempt_number=1
                    ),
                )
                completion = await stage_probe.run_async(
                    "provider_completion", lambda: provider.complete(provider_request)
                )
                await stage_probe.run_async(
                    "provider_success_finalization",
                    lambda: control.finalize_provider_success(
                        admission,
                        usage=completion.usage,
                    ),
                )

                def record_stages() -> None:
                    for stage in _stages(trace):
                        recorder.record(stage)

                stage_probe.run("observability_stage_records", record_stages)
                stage_probe.run("observability_terminal_record", lambda: recorder.record(trace))

            samples.append(await _timed_call(action))
            clock.advance(60)
        elapsed = time.perf_counter() - started
        assert repository.budget_settlement_count() == MEMORY_TRACE_COUNT
        return PerformanceRun(
            tuple(samples), float(MEMORY_TRACE_COUNT / elapsed), 0, provider.call_count
        )
    finally:
        repository.close()


def _single_memory_run_summary(run: PerformanceRun) -> dict[str, int | float]:
    return {
        **_percentile_summary(list(run.samples_ms)),
        "throughput_per_second": round(run.throughput_per_second, 6),
        "provider_dispatch_count": run.provider_dispatch_count,
    }


def _memory_protocol_run(
    root: Path,
    *,
    pair_index: int,
    order_position: int,
    scenario: str,
    recorder_factory: Callable[[], ObservabilityRecorder],
    warmup: bool,
    stage_attribution: bool,
) -> tuple[PerformanceRun, dict[str, object]]:
    before_counts = gc.get_count()
    before_stats = tuple(int(item["collections"]) for item in gc.get_stats())
    before_threads = threading.active_count()
    cpu_started = time.process_time_ns()
    wall_started = time.perf_counter_ns()
    probe = _MemoryStageProbe() if stage_attribution else None
    run = asyncio.run(_memory_control_run(root, recorder_factory, stage_probe=probe))
    wall_elapsed = time.perf_counter_ns() - wall_started
    cpu_elapsed = time.process_time_ns() - cpu_started
    after_stats = tuple(int(item["collections"]) for item in gc.get_stats())
    metadata: dict[str, object] = {
        "protocol_version": MEMORY_PROTOCOL_VERSION,
        "pair_index": pair_index,
        "order_position": order_position,
        "scenario": scenario,
        "warmup": warmup,
        "gating": not stage_attribution,
        "summary": _single_memory_run_summary(run),
        "runtime": {
            "gc_enabled": gc.isenabled(),
            "gc_count_before": list(before_counts),
            "gc_count_after": list(gc.get_count()),
            "gc_collection_delta": [
                after - before for before, after in zip(before_stats, after_stats, strict=True)
            ],
            "process_cpu_ms": round(cpu_elapsed / 1_000_000, 6),
            "wall_ms": round(wall_elapsed / 1_000_000, 6),
            "thread_count_before": before_threads,
            "thread_count_after": threading.active_count(),
        },
        "stage_attribution": None if probe is None else probe.summary(),
    }
    return run, metadata


def _paired_memory_protocol(root: Path, *, stage_attribution: bool) -> MemoryProtocolResult:
    baseline: list[PerformanceRun] = []
    recorded: list[PerformanceRun] = []
    runtime_runs: list[dict[str, object]] = []
    factories: tuple[tuple[str, Callable[[], ObservabilityRecorder]], ...] = (
        ("no_recorder_control", NoOpObservabilityRecorder),
        ("in_memory_control", InMemoryObservabilityRecorder),
    )
    for pair_index in range(MEMORY_PROTOCOL_WARMUP_PAIRS + RUN_COUNT):
        warmup = pair_index < MEMORY_PROTOCOL_WARMUP_PAIRS
        for order_position, (scenario, recorder_factory) in enumerate(factories, start=1):
            run, metadata = _memory_protocol_run(
                root,
                pair_index=pair_index,
                order_position=order_position,
                scenario=scenario,
                recorder_factory=recorder_factory,
                warmup=warmup,
                stage_attribution=stage_attribution,
            )
            runtime_runs.append(metadata)
            if warmup:
                continue
            (baseline if scenario == "no_recorder_control" else recorded).append(run)
    return MemoryProtocolResult(tuple(baseline), tuple(recorded), tuple(runtime_runs))


def _paired_memory_runs(
    root: Path,
) -> tuple[tuple[PerformanceRun, ...], tuple[PerformanceRun, ...]]:
    result = _paired_memory_protocol(root, stage_attribution=False)
    MEMORY_PROTOCOL_RUNTIME_RUNS[:] = result.runtime_runs
    return result.baseline_runs, result.recorded_runs


def _memory_runs(
    recorder_factory: Callable[[], ObservabilityRecorder],
) -> tuple[PerformanceRun, ...]:
    warmup = recorder_factory()
    trace = _trace()
    _measure_calls(partial(warmup.record, trace), MEMORY_TRACE_COUNT)
    runs: list[PerformanceRun] = []
    for _ in range(RUN_COUNT):
        recorder = recorder_factory()
        runs.append(
            _measure_calls(
                partial(recorder.record, trace),
                MEMORY_TRACE_COUNT,
            )
        )
    return tuple(runs)


def _sqlite_observability_runs(root: Path) -> tuple[PerformanceRun, ...]:
    runs: list[PerformanceRun] = []
    for index in range(RUN_COUNT + 1):
        run_root = root / f"sqlite-observability-{index}"
        run_root.mkdir()
        repository = SqliteObservabilityRepository(
            database_path=run_root / "observability.sqlite3",
            allowed_root=run_root,
        )
        repository.initialize()
        before = _snapshot(repository.database_path)
        samples: list[float] = []
        started = time.perf_counter()
        for _ in range(SQLITE_TRACE_COUNT):
            trace = _trace()
            item_started = time.perf_counter()
            pending = replace(
                trace, record_status=RecordStatus.OPEN, terminal_outcome=None, finished_at_utc=None
            )
            repository.start_trace(pending)
            for stage in _stages(trace)[:13]:
                repository.record_progress(pending, stage)
            repository.finish_trace(trace, _stages(trace))
            samples.append((time.perf_counter() - item_started) * 1_000)
        elapsed = time.perf_counter() - started
        repository.close()
        after = _snapshot(repository.database_path)
        RUN_DETAILS[run_root.name] = {
            "before": before,
            "after": after,
            "durable_stage_count": SQLITE_TRACE_COUNT * 14,
        }
        run = PerformanceRun(
            tuple(samples),
            float(SQLITE_TRACE_COUNT / elapsed),
            _growth(before, after),
            SQLITE_TRACE_COUNT,
        )
        if index:
            runs.append(run)
        print(json.dumps({"group": run_root.name, "samples": SQLITE_TRACE_COUNT}), flush=True)
    return tuple(runs)


def _open_breaker(control: SafetyControl) -> None:
    for _ in range(5):
        execution_id = uuid4()
        control.check_provider_breaker(execution_id=execution_id)
        control.record_provider_failure(
            execution_id=execution_id,
            reason=BreakerFailureReason.TIMEOUT,
        )


def _reject_runs(root: Path, *, kind: str = "breaker") -> tuple[PerformanceRun, ...]:
    runs: list[PerformanceRun] = []
    for index in range(RUN_COUNT + 1):
        run_root = root / f"sqlite-reject-{kind}-{index}"
        run_root.mkdir()
        clock = SyntheticClock()
        repository = SqliteSafetyControlRepository(
            database_path=run_root / "control.sqlite3",
            allowed_root=run_root,
        )
        repository.initialize()
        control = SafetyControl(
            repository=repository,
            scope_key=SYNTHETIC_KEY,
            clock_ns=clock.time_ns,
            monotonic_clock=clock.monotonic,
            pricing_policy=PricingPolicy.zero_cost(
                provider_kind=ProviderKind.FAKE,
                model="fake-model",
            ),
        )
        item = DialogueRequestV1(
            request_id=UUID(int=100),
            player_id="budget_player",
            npc_id="neon_guide",
            conversation_id=UUID(int=200),
            message="Synthetic budget diagnostic.",
        )
        reject_execution_id = UUID(int=9999)
        if kind == "breaker":
            _open_breaker(control)
        elif kind == "rate":
            for _ in range(15):
                control.admit_ingress(peer_host="127.0.0.1")
        elif kind == "budget":
            for count in range(15):
                admitted = item.model_copy(update={"request_id": UUID(int=count + 1)})
                execution = UUID(int=count + 1000)
                control.admit_execution(request=admitted, execution_id=execution)
                reservation = control.reserve_budget(
                    request=admitted, execution_id=execution, attempt_number=1
                )
                control.mark_budget_dispatched(reservation)
                control.settle_budget(reservation, usage=ProviderUsage(0, 0))
                clock.advance(60)
            control.admit_execution(request=item, execution_id=reject_execution_id)
        else:
            raise ValueError("Synthetic rejection kind is invalid")
        before = _snapshot(repository.database_path)

        def reject(
            control: SafetyControl = control,
            item: DialogueRequestV1 = item,
            reject_execution_id: UUID = reject_execution_id,
        ) -> None:
            try:
                if kind == "breaker":
                    control.check_provider_breaker(execution_id=uuid4())
                elif kind == "rate":
                    control.admit_ingress(peer_host="127.0.0.1")
                else:
                    control.reserve_budget(
                        request=item, execution_id=reject_execution_id, attempt_number=1
                    )
            except (CircuitOpenError, RateLimitExceededError, BudgetRejectedError):
                return
            raise RuntimeError("Synthetic pre-dispatch rejection did not occur")

        measured = _measure_calls(reject, SQLITE_TRACE_COUNT)
        repository.close()
        after = _snapshot(repository.database_path)
        RUN_DETAILS[run_root.name] = {"before": before, "after": after}
        run = PerformanceRun(
            measured.samples_ms,
            measured.throughput_per_second,
            _growth(before, after),
            0,
        )
        if index:
            runs.append(run)
    return tuple(runs)


def _completion() -> ProviderCompletion:
    return ProviderCompletion(
        content="Synthetic local benchmark reply.",
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="fake",
        model="fake-model",
        usage=ProviderUsage(prompt_tokens=0, completion_tokens=0),
    )


async def _loopback_run(
    run_root: Path,
    *,
    control_on: bool,
    sqlite_observability: bool = True,
    request_id_seed: int | None = None,
    storage_probe: _StorageTimingProbe | None = None,
) -> PerformanceRun:
    if storage_probe is None:
        return await _loopback_run_body(
            run_root,
            control_on=control_on,
            sqlite_observability=sqlite_observability,
            request_id_seed=request_id_seed,
        )
    with storage_probe.instrument():
        return await _loopback_run_body(
            run_root,
            control_on=control_on,
            sqlite_observability=sqlite_observability,
            request_id_seed=request_id_seed,
        )


async def _loopback_run_body(
    run_root: Path,
    *,
    control_on: bool,
    sqlite_observability: bool = True,
    request_id_seed: int | None = None,
) -> PerformanceRun:
    business_path = run_root / "business.sqlite3"
    memory = SqliteLongTermMemoryRepository(
        database_path=business_path,
        allowed_root=run_root,
    )
    memory.initialize()
    relationship = SqliteRelationshipRepository(
        database_path=business_path,
        allowed_root=run_root,
    )
    relationship.initialize()
    control_repository = SqliteSafetyControlRepository(
        database_path=run_root / "control.sqlite3",
        allowed_root=run_root,
    )
    control_repository.initialize()
    observability = None
    if sqlite_observability:
        observability = SqliteObservabilityRepository(
            database_path=run_root / "observability.sqlite3",
            allowed_root=run_root,
        )
        observability.initialize()
    database_names = (
        ("business", "control", "observability")
        if observability
        else (
            "business",
            "control",
        )
    )
    paths = {name: run_root / f"{name}.sqlite3" for name in database_names}
    before = {name: _snapshot(path) for name, path in paths.items()}
    clock = SyntheticClock()
    provider = FakeProvider(_completion() for _ in range(SQLITE_TRACE_COUNT))
    safety_control = (
        SafetyControl(
            repository=control_repository,
            scope_key=SYNTHETIC_KEY,
            clock_ns=clock.time_ns,
            monotonic_clock=clock.monotonic,
            pricing_policy=PricingPolicy.zero_cost(
                provider_kind=ProviderKind.FAKE,
                model="fake-model",
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
            timeout_seconds=12.0,
            max_concurrency=2,
            idempotency_ttl_seconds=600.0,
            idempotency_max_entries=256,
        ),
        clock=clock.monotonic,
        long_term_memory=LongTermMemoryService(repository=memory),
        long_term_retriever=LongTermMemoryRetriever(repository=memory),
        relationship_service=RelationshipService(repository=relationship),
        safety_control=safety_control,
        observability_recorder=observability,
        observability_scope_key=SYNTHETIC_KEY,
        observability_provider_kind=ProviderKind.FAKE,
        safety_cost_recorder=observability,
        retry_breaker_recorder=observability,
    )
    requests = tuple(
        DialogueRequestV1(
            request_id=(
                uuid4() if request_id_seed is None else UUID(int=request_id_seed + index + 1)
            ),
            player_id=f"bench_player_{index:03d}",
            npc_id=("neon_guide", "signal_archivist", "night_courier")[index % 3],
            conversation_id=UUID(int=index + 1),
            message="My favorite food is synthetic noodles.",
        )
        for index in range(SQLITE_TRACE_COUNT)
    )
    samples: list[float] = []
    peaks = {name: {"wal_bytes": 0, "shm_bytes": 0} for name in paths}
    try:
        async with _http_client(service, observability) as client:
            started = time.perf_counter()
            for offset in range(0, SQLITE_TRACE_COUNT, 2):

                async def send(item: DialogueRequestV1) -> None:
                    response = await client.post(
                        "/api/v1/dialogue",
                        content=item.model_dump_json(),
                        headers={"Content-Type": "application/json"},
                    )
                    if response.status_code != 200 or response.json().get("status") != "completed":
                        raise RuntimeError("Synthetic HTTP completion failed")

                samples.extend(
                    await asyncio.gather(
                        *(
                            _timed_call(partial(send, item))
                            for item in requests[offset : offset + 2]
                        )
                    )
                )
                clock.advance(2.0)
                for name, path in paths.items():
                    for suffix in ("wal", "shm"):
                        key = f"{suffix}_bytes"
                        peaks[name][key] = max(
                            peaks[name][key], _surface_size(Path(str(path) + f"-{suffix}"))
                        )
            elapsed = time.perf_counter() - started
    finally:
        await service.aclose()
        if observability is not None:
            observability.close()
        control_repository.close()
    after = {name: _snapshot(path) for name, path in paths.items()}
    RUN_DETAILS[run_root.name] = {
        "before": before,
        "after": after,
        "pair_boundary_surface_peaks": peaks,
        "business_growth_bytes": _growth(before["business"], after["business"]),
        "transport": "tcp_http_individual_request",
        "independent_client": _INDEPENDENT_CLIENT,
        "observability_mode": "sqlite" if observability is not None else "noop",
    }
    return PerformanceRun(
        tuple(samples),
        float(SQLITE_TRACE_COUNT / elapsed),
        (
            _combined_growth(before, after)
            if observability is not None
            else _growth(before["control"], after["control"])
        ),
        provider.call_count,
    )


async def _runtime_default_loopback_run(run_root: Path) -> PerformanceRun:
    """Measure the actual default-off observability runtime boundary."""

    return await _loopback_run(
        run_root,
        control_on=True,
        sqlite_observability=False,
    )


def _runtime_percentile(samples: tuple[float, ...], fraction: float) -> float:
    ordered = sorted(samples)
    return round(ordered[max(0, math.ceil(len(ordered) * fraction) - 1)], 6)


def _runtime_boundary_summary(run: PerformanceRun) -> dict[str, int | float | str]:
    return {
        "scenario": "full_http_control_on_noop_observability",
        "sample_count": len(run.samples_ms),
        "pair_concurrency": 2,
        "p50_ms": _runtime_percentile(run.samples_ms, 0.50),
        "p95_ms": _runtime_percentile(run.samples_ms, 0.95),
        "p99_ms": _runtime_percentile(run.samples_ms, 0.99),
        "throughput_per_second": round(run.throughput_per_second, 6),
        "control_database_growth_bytes": run.database_growth_bytes,
        "provider_dispatch_count": run.provider_dispatch_count,
    }


def _runtime_boundary_failure_codes(run: PerformanceRun) -> tuple[str, ...]:
    failures = []
    if run.provider_dispatch_count != SQLITE_TRACE_COUNT:
        failures.append("runtime_default_dispatch_ownership_failed")
    if _runtime_percentile(run.samples_ms, 0.95) > 250.0:
        failures.append("runtime_default_p95_exceeded")
    if _runtime_percentile(run.samples_ms, 0.99) > 400.0:
        failures.append("runtime_default_p99_exceeded")
    if run.throughput_per_second < 4.0:
        failures.append("runtime_default_throughput_below_minimum")
    return tuple(failures)


def _runtime_boundary_database_audit(run_root: Path) -> dict[str, object]:
    business_path = run_root / "business.sqlite3"
    control_path = run_root / "control.sqlite3"
    with closing(sqlite3.connect(f"{business_path.as_uri()}?mode=ro", uri=True)) as business:
        business_integrity = business.execute("PRAGMA integrity_check").fetchone()[0]
        business_fk_errors = len(business.execute("PRAGMA foreign_key_check").fetchall())
        relationship_states = business.execute(
            "SELECT COUNT(*) FROM relationship_states"
        ).fetchone()[0]
        relationship_events = business.execute(
            "SELECT COUNT(*) FROM relationship_events"
        ).fetchone()[0]
        relationship_requests = business.execute(
            "SELECT COUNT(DISTINCT request_id) FROM relationship_events"
        ).fetchone()[0]
        long_term_memories = business.execute("SELECT COUNT(*) FROM long_term_memories").fetchone()[
            0
        ]
        memory_operations = business.execute("SELECT COUNT(*) FROM memory_operations").fetchone()[0]
        business_journal_mode = business.execute("PRAGMA journal_mode").fetchone()[0]
        business_synchronous = business.execute("PRAGMA synchronous").fetchone()[0]
    with closing(sqlite3.connect(f"{control_path.as_uri()}?mode=ro", uri=True)) as control:
        control_integrity = control.execute("PRAGMA integrity_check").fetchone()[0]
        control_fk_errors = len(control.execute("PRAGMA foreign_key_check").fetchall())
        admissions = control.execute("SELECT COUNT(*) FROM execution_admissions").fetchone()[0]
        permits = control.execute("SELECT COUNT(*) FROM provider_permits").fetchone()[0]
        completed_permits = control.execute(
            "SELECT COUNT(*) FROM provider_permits "
            "WHERE released_at_ns IS NOT NULL AND release_reason = 'completed'"
        ).fetchone()[0]
        owners = control.execute("SELECT COUNT(*) FROM budget_execution_owners").fetchone()[0]
        reservations = control.execute("SELECT COUNT(*) FROM budget_reservations").fetchone()[0]
        settled_reservations = control.execute(
            "SELECT COUNT(*) FROM budget_reservations WHERE status = 'settled'"
        ).fetchone()[0]
        settlements = control.execute("SELECT COUNT(*) FROM budget_settlements").fetchone()[0]
        actual_cost_micro_usd = control.execute(
            "SELECT COALESCE(SUM(actual_cost_micro_usd), 0) FROM budget_settlements"
        ).fetchone()[0]
        joined_executions = control.execute(
            "SELECT COUNT(*) FROM execution_admissions AS admission "
            "JOIN provider_permits AS permit USING (execution_id) "
            "JOIN budget_execution_owners AS owner USING (execution_id) "
            "JOIN budget_reservations AS reservation USING (execution_id) "
            "JOIN budget_settlements AS settlement "
            "ON settlement.execution_id = reservation.execution_id "
            "AND settlement.attempt_number = reservation.attempt_number "
            "WHERE reservation.attempt_number = 1"
        ).fetchone()[0]
        control_journal_mode = control.execute("PRAGMA journal_mode").fetchone()[0]
        control_synchronous = control.execute("PRAGMA synchronous").fetchone()[0]
    observability_surfaces = tuple(
        path.name for path in sorted(run_root.glob("observability.sqlite3*"))
    )
    return {
        "business": {
            "integrity": business_integrity,
            "foreign_key_errors": business_fk_errors,
            "journal_mode": business_journal_mode,
            "synchronous": business_synchronous,
            "relationship_states": relationship_states,
            "relationship_events": relationship_events,
            "distinct_relationship_requests": relationship_requests,
            "long_term_memories": long_term_memories,
            "memory_operations": memory_operations,
        },
        "control": {
            "integrity": control_integrity,
            "foreign_key_errors": control_fk_errors,
            "journal_mode": control_journal_mode,
            "synchronous": control_synchronous,
            "execution_admissions": admissions,
            "provider_permits": permits,
            "completed_provider_permits": completed_permits,
            "budget_execution_owners": owners,
            "budget_reservations": reservations,
            "settled_budget_reservations": settled_reservations,
            "budget_settlements": settlements,
            "joined_execution_owners": joined_executions,
            "actual_cost_micro_usd": actual_cost_micro_usd,
        },
        "observability": {
            "mode": "noop",
            "sqlite_surfaces": observability_surfaces,
        },
    }


def _runtime_boundary_audit_failure_codes(audit: dict[str, object]) -> tuple[str, ...]:
    business = audit["business"]
    control = audit["control"]
    observability = audit["observability"]
    assert isinstance(business, dict)
    assert isinstance(control, dict)
    assert isinstance(observability, dict)
    failures = []
    if (
        business.get("integrity") != "ok"
        or business.get("foreign_key_errors") != 0
        or business.get("journal_mode") != "wal"
        or business.get("synchronous") != 2
        or business.get("relationship_states") != SQLITE_TRACE_COUNT
        or business.get("relationship_events") != SQLITE_TRACE_COUNT
        or business.get("distinct_relationship_requests") != SQLITE_TRACE_COUNT
        or business.get("long_term_memories") != 0
        or business.get("memory_operations") != 0
    ):
        failures.append("runtime_default_business_ownership_failed")
    if (
        control.get("integrity") != "ok"
        or control.get("foreign_key_errors") != 0
        or control.get("journal_mode") != "wal"
        or control.get("synchronous") != 2
        or any(
            control.get(key) != SQLITE_TRACE_COUNT
            for key in (
                "execution_admissions",
                "provider_permits",
                "completed_provider_permits",
                "budget_execution_owners",
                "budget_reservations",
                "settled_budget_reservations",
                "budget_settlements",
                "joined_execution_owners",
            )
        )
        or control.get("actual_cost_micro_usd") != 0
    ):
        failures.append("runtime_default_control_ownership_failed")
    if observability.get("mode") != "noop" or observability.get("sqlite_surfaces") != ():
        failures.append("runtime_default_observability_database_created")
    return tuple(failures)


def _loopback_runs(
    root: Path,
    *,
    control_on: bool,
    sqlite_observability: bool = True,
    label: str | None = None,
    request_id_seed: int | None = None,
) -> tuple[PerformanceRun, ...]:
    runs: list[PerformanceRun] = []
    resolved_label = label or ("on" if control_on else "off")
    for index in range(RUN_COUNT + 1):
        run_root = root / f"loopback-{resolved_label}-{index}"
        run_root.mkdir()
        storage_probe = _StorageTimingProbe() if request_id_seed is not None else None
        run = asyncio.run(
            _loopback_run(
                run_root,
                control_on=control_on,
                sqlite_observability=sqlite_observability,
                request_id_seed=request_id_seed,
                storage_probe=storage_probe,
            )
        )
        if storage_probe is not None:
            details = RUN_DETAILS[run_root.name]
            assert isinstance(details, dict)
            details["storage_timing"] = storage_probe.summary()
        if index:
            runs.append(run)
    return tuple(runs)


def _gate_boundary_loopback_runs(
    root: Path,
) -> dict[PerformanceScenario, tuple[PerformanceRun, ...]]:
    return {
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: _loopback_runs(
            root,
            control_on=False,
            sqlite_observability=False,
            label="off",
        ),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: _loopback_runs(
            root,
            control_on=True,
            sqlite_observability=False,
            label="on",
        ),
        PerformanceScenario.FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC: _loopback_runs(
            root,
            control_on=True,
            sqlite_observability=True,
            label="three-sqlite",
        ),
    }


def _storage_ab_runs(
    root: Path,
) -> dict[PerformanceScenario, tuple[PerformanceRun, ...]]:
    RUN_DETAILS.clear()
    return {
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: _loopback_runs(
            root,
            control_on=False,
            sqlite_observability=False,
            label="off",
            request_id_seed=V13_REQUEST_ID_SEED,
        ),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: _loopback_runs(
            root,
            control_on=True,
            sqlite_observability=False,
            label="on",
            request_id_seed=V13_REQUEST_ID_SEED,
        ),
    }


def _validate_storage_ab_pair(
    left: dict[PerformanceScenario, tuple[PerformanceRun, ...]],
    right: dict[PerformanceScenario, tuple[PerformanceRun, ...]],
) -> None:
    expected = {
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF,
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON,
    }
    if set(left) != expected or set(right) != expected:
        raise ValueError("Storage A/B workload mismatch")
    for scenario in expected:
        for collection in (left[scenario], right[scenario]):
            if (
                len(collection) != RUN_COUNT
                or any(len(run.samples_ms) != SQLITE_TRACE_COUNT for run in collection)
                or any(run.provider_dispatch_count != SQLITE_TRACE_COUNT for run in collection)
            ):
                raise ValueError("Storage A/B workload mismatch")


def _storage_ab_failure_codes(
    summaries: dict[PerformanceScenario, Any],
) -> tuple[str, ...]:
    off = summaries.get(PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF)
    on = summaries.get(PerformanceScenario.FULL_LOOPBACK_CONTROL_ON)
    if off is None or on is None:
        return ("storage_ab_missing_http_scenario",)
    failures: list[str] = []
    if on.p95_ms > 250.0:
        failures.append("full_loopback_p95_exceeded")
    if on.p99_ms > 400.0:
        failures.append("full_loopback_p99_exceeded")
    if on.throughput_per_second < 4.0:
        failures.append("full_loopback_throughput_below_minimum")
    if on.database_growth_bytes > 256 * 1024:
        failures.append("runtime_default_control_database_growth_exceeded")
    if (
        off.provider_dispatch_count != SQLITE_TRACE_COUNT
        or on.provider_dispatch_count != SQLITE_TRACE_COUNT
    ):
        failures.append("storage_ab_dispatch_ownership_failed")
    if on.p95_ms - off.p95_ms > CONTROL_ON_P95_FAILURE_DELTA_MS:
        failures.append("control_on_relative_p95_regression")
    return tuple(sorted(failures))


def _storage_ab_warning_codes(
    summaries: dict[PerformanceScenario, Any],
) -> tuple[str, ...]:
    return evaluate_performance_warnings(summaries)


def _storage_ab_result_boundary() -> tuple[str, ...]:
    return (
        "diagnostic_only",
        "in_memory_blocker_open",
        "step_5_open",
        "step_6_not_authorized",
    )


def _storage_ab_conclusion(
    e_failures: tuple[str, ...],
    c_failures: tuple[str, ...],
    *,
    e_p95_runs: tuple[float, ...] = (),
    c_p95_runs: tuple[float, ...] = (),
) -> str:
    if not e_failures and not c_failures:
        return "environment_variance_requires_control"
    if e_failures and not c_failures and e_p95_runs and c_p95_runs:
        e_median = float(statistics.median(e_p95_runs))
        c_median = float(statistics.median(c_p95_runs))
        variation = max(max(e_p95_runs) - min(e_p95_runs), max(c_p95_runs) - min(c_p95_runs), 10.0)
        if e_median - c_median > variation:
            return "runtime_data_root_candidate_supported"
    return "storage_media_route_not_supported"


def _storage_ab_audit_failure_codes(
    audit: dict[str, object], *, control_on: bool
) -> tuple[str, ...]:
    business = audit["business"]
    control = audit["control"]
    observability = audit["observability"]
    assert isinstance(business, dict)
    assert isinstance(control, dict)
    assert isinstance(observability, dict)
    failures: list[str] = []
    if (
        business.get("integrity") != "ok"
        or business.get("foreign_key_errors") != 0
        or business.get("journal_mode") != "wal"
        or business.get("synchronous") != 2
        or business.get("relationship_states") != SQLITE_TRACE_COUNT
        or business.get("relationship_events") != SQLITE_TRACE_COUNT
        or business.get("distinct_relationship_requests") != SQLITE_TRACE_COUNT
        or business.get("long_term_memories") != 0
        or business.get("memory_operations") != 0
    ):
        failures.append("storage_ab_business_ownership_failed")
    expected = SQLITE_TRACE_COUNT if control_on else 0
    if (
        control.get("integrity") != "ok"
        or control.get("foreign_key_errors") != 0
        or control.get("journal_mode") != "wal"
        or control.get("synchronous") != 2
        or any(
            control.get(name) != expected
            for name in (
                "execution_admissions",
                "provider_permits",
                "completed_provider_permits",
                "budget_execution_owners",
                "budget_reservations",
                "settled_budget_reservations",
                "budget_settlements",
                "joined_execution_owners",
            )
        )
        or control.get("actual_cost_micro_usd") != 0
    ):
        failures.append("storage_ab_control_ownership_failed")
    if observability.get("mode") != "noop" or observability.get("sqlite_surfaces") != ():
        failures.append("storage_ab_observability_database_created")
    return tuple(failures)


def _storage_ab_surface_state(root: Path) -> tuple[tuple[str, int, int], ...]:
    return tuple(
        (str(path.relative_to(root)), path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


@contextmanager
def _storage_ab_temp_root(root: Path) -> Iterator[None]:
    tmp_root = root / "tmp"
    previous_temp = os.environ.get("TEMP")
    previous_tmp = os.environ.get("TMP")
    previous_tempdir = tempfile.tempdir
    os.environ["TEMP"] = str(tmp_root)
    os.environ["TMP"] = str(tmp_root)
    tempfile.tempdir = str(tmp_root)
    try:
        yield
    finally:
        tempfile.tempdir = previous_tempdir
        if previous_temp is None:
            os.environ.pop("TEMP", None)
        else:
            os.environ["TEMP"] = previous_temp
        if previous_tmp is None:
            os.environ.pop("TMP", None)
        else:
            os.environ["TMP"] = previous_tmp


def _storage_ab_media_result(
    root: Path, media: str
) -> tuple[dict[str, object], dict[PerformanceScenario, tuple[PerformanceRun, ...]]]:
    runs = _storage_ab_runs(root)
    summaries = {
        scenario: summarize_performance_runs(scenario, values) for scenario, values in runs.items()
    }
    audits: dict[str, object] = {}
    audit_failures: list[str] = []
    for mode, control_on in (("off", False), ("on", True)):
        for index in range(RUN_COUNT + 1):
            label = f"loopback-{mode}-{index}"
            audit = _runtime_boundary_database_audit(root / label)
            audits[label] = audit
            audit_failures.extend(_storage_ab_audit_failure_codes(audit, control_on=control_on))
    result = {
        "schema_version": 1,
        "media": media,
        "config": _storage_ab_config(),
        "config_digest": _storage_ab_config_digest(),
        "summaries": {scenario.value: summary.as_dict() for scenario, summary in summaries.items()},
        "runs": {
            scenario.value: [asdict(run) for run in values] for scenario, values in runs.items()
        },
        "performance_failure_codes": list(_storage_ab_failure_codes(summaries)),
        "performance_warning_codes": list(_storage_ab_warning_codes(summaries)),
        "audit_failure_codes": sorted(set(audit_failures)),
        "database_details": dict(RUN_DETAILS),
        "database_audits": audits,
        "resource_boundary": {
            "directories": [str(path) for path in storage_ab_manifest(root)[0]],
            "files": [str(path) for path in storage_ab_manifest(root)[1]],
        },
        "boundary": list(_storage_ab_result_boundary()),
    }
    output = root / "performance-summary.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result, runs


def _run_storage_ab(e_root: Path, c_root: Path) -> int:
    global _INDEPENDENT_CLIENT
    approved_e = V13_E_ROOT.resolve(strict=True)
    approved_c = V13_C_ROOT.resolve(strict=True)
    _validate_storage_ab_root(e_root, approved_e)
    _validate_storage_ab_root(c_root, approved_c)
    if e_root == c_root or V13_COMPARISON.exists():
        raise ValueError("Storage A/B roots are invalid")
    c_before = _storage_ab_surface_state(c_root)
    _INDEPENDENT_CLIENT = True
    with _storage_ab_temp_root(e_root):
        e_result, e_runs = _storage_ab_media_result(e_root, "e_usb")
    if _storage_ab_surface_state(c_root) != c_before:
        raise ValueError("Storage A/B cross-root write detected")
    e_before_c = _storage_ab_surface_state(e_root)
    with _storage_ab_temp_root(c_root):
        c_result, c_runs = _storage_ab_media_result(c_root, "c_nvme")
    if _storage_ab_surface_state(e_root) != e_before_c:
        raise ValueError("Storage A/B cross-root write detected")
    _validate_storage_ab_pair(e_runs, c_runs)
    e_on = e_runs[PerformanceScenario.FULL_LOOPBACK_CONTROL_ON]
    c_on = c_runs[PerformanceScenario.FULL_LOOPBACK_CONTROL_ON]
    e_failures = tuple(
        str(item) for item in cast(list[object], e_result["performance_failure_codes"])
    )
    c_failures = tuple(
        str(item) for item in cast(list[object], c_result["performance_failure_codes"])
    )
    e_warnings = tuple(
        str(item) for item in cast(list[object], e_result["performance_warning_codes"])
    )
    c_warnings = tuple(
        str(item) for item in cast(list[object], c_result["performance_warning_codes"])
    )
    comparison = {
        "schema_version": 1,
        "config_digest": _storage_ab_config_digest(),
        "e_summary": e_result["summaries"],
        "c_summary": c_result["summaries"],
        "e_failure_codes": list(e_failures),
        "c_failure_codes": list(c_failures),
        "e_warning_codes": list(e_warnings),
        "c_warning_codes": list(c_warnings),
        "conclusion": _storage_ab_conclusion(
            e_failures,
            c_failures,
            e_p95_runs=tuple(_runtime_percentile(run.samples_ms, 0.95) for run in e_on),
            c_p95_runs=tuple(_runtime_percentile(run.samples_ms, 0.95) for run in c_on),
        ),
        "boundary": list(_storage_ab_result_boundary()),
    }
    with V13_COMPARISON.open("x", encoding="utf-8") as stream:
        json.dump(comparison, stream, sort_keys=True, indent=2)
    print(json.dumps(comparison, sort_keys=True))
    audit_failures = tuple(cast(list[object], e_result["audit_failure_codes"])) + tuple(
        cast(list[object], c_result["audit_failure_codes"])
    )
    return 1 if audit_failures else 0


def _v26_product_schema_audit(database: Path) -> dict[str, object]:
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as connection:
        return {
            "user_version": int(connection.execute("PRAGMA user_version").fetchone()[0]),
            "migration_versions": [
                int(row[0])
                for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            ],
            "candidate_index_present": any(
                str(row[1]) == "idx_budget_owners_npc"
                for row in connection.execute("PRAGMA index_list('budget_execution_owners')")
            ),
            "integrity": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            "foreign_key_errors": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        }


def _v26_product_database_failures(
    audit: dict[str, object],
    *,
    expected_version: int,
    candidate_index_present: bool,
) -> tuple[str, ...]:
    failures: list[str] = []
    if audit["user_version"] != expected_version or audit["migration_versions"] != list(
        range(1, expected_version + 1)
    ):
        failures.append("product_migration_version_mismatch")
    if audit["candidate_index_present"] is not candidate_index_present:
        failures.append("product_index_presence_mismatch")
    if audit["integrity"] != "ok" or audit["foreign_key_errors"] != 0:
        failures.append("product_database_integrity_failed")
    return tuple(failures)


async def _run_v26_product_space_gate(root: Path) -> int:
    from scripts.f009_step5_control_space_preflight import (
        _audit_failures,
        _populate_full_control,
        _space_pair_snapshot,
        _space_result_for_json,
    )

    resolved = root.resolve(strict=True)
    if resolved != V26_PRODUCT_SPACE_ROOT or root.is_symlink() or root.is_junction():
        raise ValueError("V26 product space root is outside the registered boundary")
    for current in (root, *root.parents):
        if _is_reparse_point(current):
            raise ValueError("V26 product space root crosses a reparse boundary")
        if current == Path(root.anchor):
            break
    directories, files = v26_product_space_manifest(root)
    required_existing = set(directories[:5])
    if any(not path.is_dir() for path in required_existing):
        raise ValueError("V26 product space pytest/TEMP surface is incomplete")
    if files[0].exists() or any(path.exists() for path in directories[5:]):
        raise ValueError("V26 product space scenario is not fresh")

    (root / "space-gate-01").mkdir()
    pairs: list[dict[str, object]] = []
    all_failures: list[str] = []
    product_migrations = control_module.CONTROL_MIGRATIONS
    if product_migrations[-1] != (7, "0007_drop_redundant_budget_owner_npc_index.sql"):
        raise ValueError("V26 product migration 7 is not registered")
    for pair in range(1, RUN_COUNT + 1):
        pair_root = root / f"space-pair-{pair:02d}"
        pair_root.mkdir()
        try:
            control_module.CONTROL_MIGRATIONS = cast(Any, product_migrations[:6])
            baseline = await _populate_full_control(
                pair_root / "baseline-v6",
                candidate=False,
            )
        finally:
            control_module.CONTROL_MIGRATIONS = product_migrations
        product = await _populate_full_control(
            pair_root / "product-v7",
            candidate=False,
        )
        baseline_snapshot = _space_pair_snapshot(baseline)
        product_snapshot = _space_pair_snapshot(product)
        baseline_audit = _v26_product_schema_audit(cast(Path, baseline["database"]))
        product_audit = _v26_product_schema_audit(cast(Path, product["database"]))
        failures = list(
            _v26_product_space_pair_failures(
                baseline_growth_bytes=baseline_snapshot.occupied_growth_bytes,
                product_growth_bytes=product_snapshot.occupied_growth_bytes,
                product_candidate_index_pages=product_snapshot.candidate_index_pages,
                baseline_digest=cast(str, baseline["logical_digest"]),
                product_digest=cast(str, product["logical_digest"]),
            )
        )
        failures.extend(_audit_failures(cast(dict[str, object], baseline["audit"])))
        failures.extend(_audit_failures(cast(dict[str, object], product["audit"])))
        failures.extend(
            _v26_product_database_failures(
                baseline_audit,
                expected_version=6,
                candidate_index_present=True,
            )
        )
        failures.extend(
            _v26_product_database_failures(
                product_audit,
                expected_version=7,
                candidate_index_present=False,
            )
        )
        all_failures.extend(failures)
        pairs.append(
            {
                "pair": pair,
                "baseline": _space_result_for_json(baseline),
                "product": _space_result_for_json(product),
                "baseline_schema": baseline_audit,
                "product_schema": product_audit,
                "occupied_saving_bytes": (
                    baseline_snapshot.occupied_growth_bytes - product_snapshot.occupied_growth_bytes
                ),
                "failures": failures,
            }
        )
    summary = {
        "schema_version": "f-009-v26-product-space-gate-v1",
        "status": "product_space_gate_passed" if not all_failures else "failed",
        "candidate_index": "idx_budget_owners_npc",
        "control_growth_limit_bytes": 256 * 1024,
        "required_saving_bytes": 2 * 4096,
        "pairs": pairs,
        "failures": sorted(set(all_failures)),
    }
    serialized = json.dumps(summary, indent=2, sort_keys=True)
    for forbidden in (
        "bench_player_",
        "Synthetic local benchmark",
        "api-key-synthetic-secret",
    ):
        if forbidden in serialized:
            raise ValueError("V26 product space summary contains forbidden payload")
    files[0].write_text(serialized + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": summary["status"],
                "failure_codes": summary["failures"],
                "pair_count": len(pairs),
            },
            sort_keys=True,
        )
    )
    return 0 if not all_failures else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--runtime-boundary", action="store_true")
    parser.add_argument("--gate-boundary-matrix", action="store_true")
    parser.add_argument("--memory-protocol-attribution", action="store_true")
    parser.add_argument("--storage-ab", action="store_true")
    parser.add_argument("--control-boundary-matrix", action="store_true")
    parser.add_argument("--execution-intent-matrix", action="store_true")
    parser.add_argument("--v26-product-space-gate", action="store_true")
    parser.add_argument("--c-output-root", type=Path)
    return parser.parse_args()


def _validate_memory_protocol_root(root: Path) -> Path:
    approved = V15_ROOT.resolve(strict=True)
    if root != approved or root.is_symlink() or root.is_junction():
        raise ValueError("Memory protocol root is not approved")
    for current in (root, *root.parents):
        if _is_reparse_point(current):
            raise ValueError("Memory protocol root crosses a reparse boundary")
        if current == Path(root.anchor):
            break
    directories, files = memory_protocol_manifest(root)
    allowed_existing = {
        root / "tmp",
        root / "pytest-red-01",
        root / "pytest-green-01",
        root / "pytest-green-02",
    }
    if not (root / "tmp").is_dir() or not set(root.iterdir()) <= allowed_existing:
        raise ValueError("Memory protocol root is not fresh")
    if any(path.exists() for path in directories[2:]) or any(path.exists() for path in files):
        raise ValueError("Memory protocol root is not fresh")
    return root


def _run_memory_protocol_attribution(root: Path) -> int:
    resolved = _validate_memory_protocol_root(root)
    protocol_root = resolved / "protocol-01"
    protocol_root.mkdir()
    plain = _paired_memory_protocol(protocol_root, stage_attribution=False)
    attributed = _paired_memory_protocol(protocol_root, stage_attribution=True)
    plain_baseline = summarize_performance_runs(
        PerformanceScenario.NO_RECORDER_CONTROL, plain.baseline_runs
    )
    plain_recorded = summarize_performance_runs(
        PerformanceScenario.IN_MEMORY_CONTROL, plain.recorded_runs
    )
    attributed_baseline = summarize_performance_runs(
        PerformanceScenario.NO_RECORDER_CONTROL, attributed.baseline_runs
    )
    attributed_recorded = summarize_performance_runs(
        PerformanceScenario.IN_MEMORY_CONTROL, attributed.recorded_runs
    )
    result = {
        "schema_version": 1,
        "status": "completed",
        "protocol": memory_protocol_config(),
        "plain": {
            "gating": True,
            "baseline": plain_baseline.as_dict(),
            "recorded": plain_recorded.as_dict(),
            "paired_throughput_ratio": round(
                plain_recorded.throughput_per_second / plain_baseline.throughput_per_second,
                6,
            ),
            "runtime_runs": list(plain.runtime_runs),
        },
        "stage_companion": {
            "gating": False,
            "baseline": attributed_baseline.as_dict(),
            "recorded": attributed_recorded.as_dict(),
            "runtime_runs": list(attributed.runtime_runs),
        },
    }
    output = protocol_root / "summary-protocol-01.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    print(json.dumps({"status": "completed", "protocol": memory_protocol_config()}))
    return 0


def _run_runtime_boundary(root: Path) -> int:
    global _INDEPENDENT_CLIENT
    approved = V11_ROOT.resolve(strict=True)
    if root != approved or root.is_symlink() or root.is_junction():
        raise ValueError("Runtime boundary output root is not approved")
    directories, files = runtime_boundary_manifest(root)
    if directories[:2] != (root, root / "tmp") or not (root / "tmp").is_dir():
        raise ValueError("Runtime boundary TEMP root is not registered")
    case_root = root / "runtime-default-01"
    if case_root.exists() or any(path.exists() for path in files):
        raise ValueError("Runtime boundary case is not fresh")
    case_root.mkdir()
    _INDEPENDENT_CLIENT = True
    run = asyncio.run(_runtime_default_loopback_run(case_root))
    audit = _runtime_boundary_database_audit(case_root)
    failures = _runtime_boundary_failure_codes(run) + _runtime_boundary_audit_failure_codes(audit)
    result = {
        "schema_version": 1,
        "scenario": "full_http_control_on_noop_observability",
        "production_sla": False,
        "formal_runtime_default": True,
        "warmup_runs": 0,
        "run_count": 1,
        "summary": _runtime_boundary_summary(run),
        "run": asdict(run),
        "failure_codes": list(failures),
        "database_details": RUN_DETAILS[case_root.name],
        "database_audit": audit,
        "resource_boundary": {
            "directories": [str(path) for path in directories],
            "files": [str(path) for path in files],
        },
    }
    output = case_root / "performance-summary.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    print(json.dumps(result["summary"], sort_keys=True))
    print(json.dumps({"failure_codes": list(failures)}, sort_keys=True))
    return 1 if failures else 0


def _run_gate_boundary_matrix(root: Path) -> int:
    global _INDEPENDENT_CLIENT
    approved = CORE_REVALIDATION_ROOT.resolve(strict=True)
    if root != approved or root.is_symlink() or root.is_junction():
        raise ValueError("Gate boundary output root is not approved")
    directories, files = gate_boundary_matrix_manifest(root)
    if not (root / "tmp").is_dir():
        raise ValueError("Gate boundary TEMP root is not registered")
    benchmark_root = root / "full-matrix-01"
    if benchmark_root.exists() or any(path.exists() for path in files):
        raise ValueError("Gate boundary matrix is not fresh")
    benchmark_root.mkdir()
    _INDEPENDENT_CLIENT = True
    memory_off, memory_on = _paired_memory_runs(benchmark_root)
    plain_memory_runtime = tuple(MEMORY_PROTOCOL_RUNTIME_RUNS)
    stage_companion = _paired_memory_protocol(benchmark_root, stage_attribution=True)
    rejection_runs = {
        kind: _reject_runs(benchmark_root, kind=kind) for kind in ("rate", "budget", "breaker")
    }
    all_runs = {
        PerformanceScenario.NO_RECORDER: _memory_runs(NoOpObservabilityRecorder),
        PerformanceScenario.NO_RECORDER_CONTROL: memory_off,
        PerformanceScenario.IN_MEMORY_CONTROL: memory_on,
        PerformanceScenario.SQLITE_OBSERVABILITY: _sqlite_observability_runs(benchmark_root),
        PerformanceScenario.SQLITE_PRE_DISPATCH_REJECT: rejection_runs["breaker"],
        **_gate_boundary_loopback_runs(benchmark_root),
    }
    summaries = {
        scenario: summarize_performance_runs(scenario, runs) for scenario, runs in all_runs.items()
    }
    failures = evaluate_performance_gate(summaries)
    warnings = evaluate_performance_warnings(summaries)
    for kind, runs in rejection_runs.items():
        summary = summarize_performance_runs(
            PerformanceScenario.SQLITE_PRE_DISPATCH_REJECT,
            runs,
        )
        if (
            summary.p95_ms > 50
            or summary.provider_dispatch_count
            or summary.database_growth_bytes > 256 * 1024
        ):
            failures += (f"{kind}_pre_dispatch_gate_failed",)
    failures = tuple(sorted(set(failures)))
    diagnostic = summaries[PerformanceScenario.FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC]
    diagnostic_codes = evaluate_three_sqlite_diagnostic(diagnostic)
    result = {
        "schema_version": 1,
        "run_count": RUN_COUNT,
        "warmup_runs": 1,
        "production_sla": False,
        "gate_boundary": {
            "http_blocking_runtime": "control_on_noop_observability",
            "sqlite_observability_independent_gate": True,
            "three_sqlite_non_blocking_diagnostic": True,
        },
        "memory_protocol": {
            "config": memory_protocol_config(),
            "plain_runtime_runs": list(plain_memory_runtime),
            "stage_companion_gating": False,
            "stage_companion_runtime_runs": list(stage_companion.runtime_runs),
        },
        "summaries": {scenario.value: summary.as_dict() for scenario, summary in summaries.items()},
        "runs": {
            scenario.value: [asdict(run) for run in runs] for scenario, runs in all_runs.items()
        },
        "failure_codes": list(failures),
        "warning_codes": list(warnings),
        "diagnostic_codes": list(diagnostic_codes),
        "database_details": RUN_DETAILS,
        "rejection_runs": {
            kind: [asdict(run) for run in runs] for kind, runs in rejection_runs.items()
        },
        "resource_boundary": {
            "directories": [str(path) for path in directories],
            "files": [str(path) for path in files],
        },
        "remaining_scenarios_require_core_gate_pass": [
            "single_scope_serial",
            "waiter",
            "replay",
            "retry",
            "restart",
            "long_term_write",
        ],
    }
    output = benchmark_root / "performance-summary.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    print(json.dumps(result["summaries"], sort_keys=True))
    print(json.dumps({"failure_codes": list(failures)}, sort_keys=True))
    print(json.dumps({"warning_codes": list(warnings)}, sort_keys=True))
    print(json.dumps({"diagnostic_codes": list(diagnostic_codes)}, sort_keys=True))
    return 1 if failures else 0


def _run_control_boundary_matrix(
    root: Path,
) -> int:
    approved = V21_ROOT.resolve(strict=True)
    if root != approved or root.is_symlink() or root.is_junction():
        raise ValueError("Control boundary output root is not approved")
    if not (root / "tmp").is_dir() or not (root / "performance-02").is_dir():
        raise ValueError("Control boundary roots are not registered")
    performance_root = root / "performance-02"
    if any(performance_root.iterdir()):
        raise ValueError("Control boundary matrix is not fresh")
    return _run_http_control_pair(performance_root, gate_boundary="v21_control_boundary")


def _run_execution_intent_matrix(root: Path) -> int:
    approved = V24_ROOT.resolve(strict=True)
    if root != approved or root.is_symlink() or root.is_junction():
        raise ValueError("Execution intent output root is not approved")
    if not (root / "tmp").is_dir() or not (root / V24_TCP_DIRECTORY).is_dir():
        raise ValueError("Execution intent roots are not registered")
    performance_root = root / V24_TCP_DIRECTORY
    if any(performance_root.iterdir()):
        raise ValueError("Execution intent matrix is not fresh")
    return _run_http_control_pair(
        performance_root,
        gate_boundary="v24_execution_intent_real_tcp",
    )


def _run_http_control_pair(performance_root: Path, *, gate_boundary: str) -> int:
    global _INDEPENDENT_CLIENT
    _INDEPENDENT_CLIENT = True
    RUN_DETAILS.clear()
    all_runs = {
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: _loopback_runs(
            performance_root,
            control_on=False,
            sqlite_observability=False,
            label="off",
            request_id_seed=V13_REQUEST_ID_SEED,
        ),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: _loopback_runs(
            performance_root,
            control_on=True,
            sqlite_observability=False,
            label="on",
            request_id_seed=V13_REQUEST_ID_SEED,
        ),
    }
    summaries = {
        scenario: summarize_performance_runs(scenario, runs) for scenario, runs in all_runs.items()
    }
    failures = _storage_ab_failure_codes(summaries)
    warnings = _storage_ab_warning_codes(summaries)
    audits = {
        name: _runtime_boundary_database_audit(performance_root / name) for name in RUN_DETAILS
    }
    audit_failures = tuple(
        sorted(
            {
                code
                for name, audit in audits.items()
                for code in _storage_ab_audit_failure_codes(
                    audit,
                    control_on=name.startswith("loopback-on-"),
                )
            }
        )
    )
    result = {
        "schema_version": 1,
        "status": "passed" if not failures and not audit_failures else "failed",
        "gate_boundary": gate_boundary,
        "run_count": RUN_COUNT,
        "warmup_runs": 1,
        "summaries": {scenario.value: summary.as_dict() for scenario, summary in summaries.items()},
        "runs": {
            scenario.value: [asdict(run) for run in runs] for scenario, runs in all_runs.items()
        },
        "failure_codes": list(failures),
        "warning_codes": list(warnings),
        "audit_failure_codes": list(audit_failures),
        "database_details": RUN_DETAILS,
        "database_audits": audits,
    }
    output = performance_root / "performance-summary.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    print(json.dumps(result["summaries"], sort_keys=True))
    print(json.dumps({"failure_codes": list(failures)}, sort_keys=True))
    print(json.dumps({"warning_codes": list(warnings)}, sort_keys=True))
    print(json.dumps({"audit_failure_codes": list(audit_failures)}, sort_keys=True))
    return 1 if failures or audit_failures else 0


def main() -> int:
    global _INDEPENDENT_CLIENT
    args = _parse_args()
    root = args.output_root.resolve(strict=True)
    if args.v26_product_space_gate:
        return asyncio.run(_run_v26_product_space_gate(root))
    if args.storage_ab:
        if args.c_output_root is None:
            raise ValueError("Storage A/B C root is required")
        return _run_storage_ab(root, args.c_output_root.resolve(strict=True))
    if args.runtime_boundary:
        return _run_runtime_boundary(root)
    if args.memory_protocol_attribution:
        return _run_memory_protocol_attribution(root)
    if args.gate_boundary_matrix:
        return _run_gate_boundary_matrix(root)
    if args.control_boundary_matrix:
        return _run_control_boundary_matrix(root)
    if args.execution_intent_matrix:
        return _run_execution_intent_matrix(root)
    approved = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v8-minimal-fix").resolve(
        strict=True
    )
    if root != approved or root.is_symlink() or root.is_junction():
        raise ValueError("Benchmark output root is not approved")
    benchmark_root = root / "matrix-01"
    benchmark_root.mkdir()
    _INDEPENDENT_CLIENT = True
    memory_off, memory_on = _paired_memory_runs(benchmark_root)
    rejection_runs = {
        kind: _reject_runs(benchmark_root, kind=kind) for kind in ("rate", "budget", "breaker")
    }
    all_runs = {
        PerformanceScenario.NO_RECORDER: _memory_runs(NoOpObservabilityRecorder),
        PerformanceScenario.NO_RECORDER_CONTROL: memory_off,
        PerformanceScenario.IN_MEMORY_CONTROL: memory_on,
        PerformanceScenario.SQLITE_OBSERVABILITY: _sqlite_observability_runs(benchmark_root),
        PerformanceScenario.SQLITE_PRE_DISPATCH_REJECT: rejection_runs["breaker"],
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: _loopback_runs(
            benchmark_root, control_on=False
        ),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: _loopback_runs(
            benchmark_root, control_on=True
        ),
    }
    summaries = {
        scenario: summarize_performance_runs(scenario, runs) for scenario, runs in all_runs.items()
    }
    failures = evaluate_performance_gate(summaries)
    warnings = evaluate_performance_warnings(summaries)
    for kind, runs in rejection_runs.items():
        summary = summarize_performance_runs(PerformanceScenario.SQLITE_PRE_DISPATCH_REJECT, runs)
        if (
            summary.p95_ms > 50
            or summary.provider_dispatch_count
            or summary.database_growth_bytes > 256 * 1024
        ):
            failures += (f"{kind}_pre_dispatch_gate_failed",)
    result = {
        "schema_version": 1,
        "run_count": RUN_COUNT,
        "warmup_runs": 1,
        "production_sla": False,
        "summaries": {scenario.value: summary.as_dict() for scenario, summary in summaries.items()},
        "runs": {
            scenario.value: [asdict(run) for run in runs] for scenario, runs in all_runs.items()
        },
        "failure_codes": list(failures),
        "warning_codes": list(warnings),
        "database_details": RUN_DETAILS,
        "rejection_runs": {
            kind: [asdict(run) for run in runs] for kind, runs in rejection_runs.items()
        },
        "remaining_scenarios_require_core_gate_pass": [
            "single_scope_serial",
            "waiter",
            "replay",
            "retry",
            "restart",
            "long_term_write",
        ],
    }
    output = benchmark_root / "performance-summary.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    print(json.dumps(result["summaries"], sort_keys=True))
    print(json.dumps({"failure_codes": list(failures)}, sort_keys=True))
    print(json.dumps({"warning_codes": list(warnings)}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
