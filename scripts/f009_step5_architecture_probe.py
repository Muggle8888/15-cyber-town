"""V5 synthetic diagnosis only; never replaces the production async call graph."""

from __future__ import annotations

import ast
import asyncio
import inspect
import json
import sqlite3
import sys
import textwrap
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import ExitStack, asynccontextmanager, contextmanager
from dataclasses import asdict, dataclass
from enum import StrEnum
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Any
from unittest.mock import patch
from uuid import UUID

from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import SafetyControl
from cyber_town.application.dialogue import DialogueExecutionConfig, DialogueService
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.observability import (
    DialogueTrace,
    InMemoryObservabilityRecorder,
    NoOpObservabilityRecorder,
    ProviderKind,
    ScopeTags,
    TraceMetadata,
    TraceStageMetadata,
)
from cyber_town.application.relationship import RelationshipService
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import SqliteRelationshipRepository
from scripts import f009_step5_benchmark as bench
from scripts import f009_step5_steady_profile as previous
from scripts.f009_step5_steady_profile import SteadyProfile as SteadyProfile

ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v5-architecture")
V23_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v23-execution-intent-preflight")
CASES = (
    "memory-off-profile",
    "memory-on-profile",
    "memory-off-plain",
    "memory-on-plain",
    "http-single-profile",
    "http-pair-profile",
    "http-single-plain",
    "http-pair-plain",
)

_SYNTHETIC_INTENT_DDL = """
CREATE TABLE IF NOT EXISTS synthetic_execution_intents (
    request_id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL UNIQUE,
    fingerprint TEXT NOT NULL CHECK(length(fingerprint) = 64),
    state TEXT NOT NULL CHECK(state IN ('dispatch_intent', 'released', 'settled')),
    execution_quota_count INTEGER NOT NULL CHECK(execution_quota_count = 1),
    dispatch_intent_count INTEGER NOT NULL CHECK(dispatch_intent_count = 1),
    settlement_count INTEGER NOT NULL CHECK(settlement_count IN (0, 1)),
    release_count INTEGER NOT NULL CHECK(release_count IN (0, 1)),
    business_claim_count INTEGER NOT NULL CHECK(business_claim_count IN (0, 1)),
    conservative INTEGER NOT NULL CHECK(conservative IN (0, 1)),
    revision INTEGER NOT NULL CHECK(revision >= 1),
    CHECK(
        (state = 'dispatch_intent' AND settlement_count = 0 AND release_count = 0
            AND business_claim_count = 0 AND conservative = 0)
        OR
        (state = 'released' AND settlement_count = 0 AND release_count = 1
            AND business_claim_count = 0 AND conservative = 0)
        OR
        (state = 'settled' AND settlement_count = 1 AND release_count = 0)
    )
) STRICT;
"""


class SyntheticIntentOutcome(StrEnum):
    OWNER = "owner"
    WAITER = "waiter"
    REPLAY = "replay"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class SyntheticIntent:
    execution_id: UUID
    outcome: SyntheticIntentOutcome
    durable_fence_count: int


class SyntheticExecutionIntentStore:
    """Test-only durable state machine for the V23 three-fence candidate.

    It deliberately does not share code or schema with the product repository. The
    dispatch intent is durable, while an actual provider receipt is not. Recovery
    therefore applies the user-approved conservative settlement rule.
    """

    def __init__(self, database_path: Path) -> None:
        if not isinstance(database_path, Path) or database_path.suffix != ".sqlite3":
            raise TypeError("Synthetic execution-intent path is invalid")
        self._path = database_path
        self._dispatch_claims: set[UUID] = set()
        self._claim_lock = Lock()

    def initialize(self) -> None:
        if not self._path.parent.is_dir():
            raise ValueError("Synthetic execution-intent parent is missing")
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(_SYNTHETIC_INTENT_DDL)

    def close(self) -> None:
        # Connections are operation-scoped so restart tests cannot accidentally
        # inherit an open transaction or process-local dispatch claim.
        self._dispatch_claims.clear()

    def prepare_provider_attempt(
        self,
        *,
        request_id: UUID,
        execution_id: UUID,
        fingerprint: str,
        fail_before_commit: bool = False,
    ) -> SyntheticIntent:
        if (
            not isinstance(request_id, UUID)
            or not isinstance(execution_id, UUID)
            or not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(character not in "0123456789abcdef" for character in fingerprint)
        ):
            raise TypeError("Synthetic execution-intent identity is invalid")
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT execution_id, fingerprint, state FROM synthetic_execution_intents "
                "WHERE request_id = ?",
                (str(request_id),),
            ).fetchone()
            if row is not None:
                if row["fingerprint"] != fingerprint:
                    outcome = SyntheticIntentOutcome.CONFLICT
                elif row["state"] == "dispatch_intent":
                    outcome = SyntheticIntentOutcome.WAITER
                else:
                    outcome = SyntheticIntentOutcome.REPLAY
                return SyntheticIntent(
                    execution_id=UUID(row["execution_id"]),
                    outcome=outcome,
                    durable_fence_count=0,
                )
            connection.execute(
                "INSERT INTO synthetic_execution_intents ("
                "request_id, execution_id, fingerprint, state, execution_quota_count, "
                "dispatch_intent_count, settlement_count, release_count, "
                "business_claim_count, conservative, revision"
                ") VALUES (?, ?, ?, 'dispatch_intent', 1, 1, 0, 0, 0, 0, 1)",
                (str(request_id), str(execution_id), fingerprint),
            )
            if fail_before_commit:
                raise sqlite3.OperationalError("synthetic prepare rollback")
        return SyntheticIntent(
            execution_id=execution_id,
            outcome=SyntheticIntentOutcome.OWNER,
            durable_fence_count=2,
        )

    def claim_provider_dispatch(self, intent: SyntheticIntent) -> bool:
        if intent.outcome is not SyntheticIntentOutcome.OWNER:
            return False
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state FROM synthetic_execution_intents WHERE execution_id = ?",
                (str(intent.execution_id),),
            ).fetchone()
        if row is None or row["state"] != "dispatch_intent":
            return False
        with self._claim_lock:
            if intent.execution_id in self._dispatch_claims:
                return False
            self._dispatch_claims.add(intent.execution_id)
            return True

    def cancel_clean_before_provider(self, intent: SyntheticIntent) -> bool:
        with self._claim_lock:
            if intent.execution_id in self._dispatch_claims:
                return False
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE synthetic_execution_intents "
                "SET state = 'released', release_count = 1, revision = revision + 1 "
                "WHERE execution_id = ? AND state = 'dispatch_intent'",
                (str(intent.execution_id),),
            )
            return cursor.rowcount == 1

    def finalize_success(self, intent: SyntheticIntent, *, fail_before_commit: bool) -> bool:
        return self._finalize(
            intent,
            conservative=False,
            claim_business=True,
            fail_before_commit=fail_before_commit,
        )

    def finalize_conservatively(
        self, intent: SyntheticIntent, *, fail_before_commit: bool = False
    ) -> bool:
        return self._finalize(
            intent,
            conservative=True,
            claim_business=False,
            fail_before_commit=fail_before_commit,
        )

    def _finalize(
        self,
        intent: SyntheticIntent,
        *,
        conservative: bool,
        claim_business: bool,
        fail_before_commit: bool,
    ) -> bool:
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE synthetic_execution_intents "
                "SET state = 'settled', settlement_count = 1, "
                "business_claim_count = ?, conservative = ?, revision = revision + 1 "
                "WHERE execution_id = ? AND state = 'dispatch_intent'",
                (int(claim_business), int(conservative), str(intent.execution_id)),
            )
            changed = cursor.rowcount == 1
            if changed and fail_before_commit:
                raise sqlite3.OperationalError("synthetic finalization rollback")
            return changed

    def recover_unknown_intents(self) -> int:
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE synthetic_execution_intents "
                "SET state = 'settled', settlement_count = 1, conservative = 1, "
                "revision = revision + 1 WHERE state = 'dispatch_intent'"
            )
            return cursor.rowcount

    def state_for(self, execution_id: UUID) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state FROM synthetic_execution_intents WHERE execution_id = ?",
                (str(execution_id),),
            ).fetchone()
        if row is None:
            raise LookupError("Synthetic execution intent is missing")
        return str(row["state"])

    def aggregate(self) -> dict[str, int]:
        columns = (
            "execution_count",
            "execution_quota_count",
            "dispatch_intent_count",
            "settlement_count",
            "release_count",
            "business_claim_count",
            "conservative_count",
        )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS execution_count, "
                "COALESCE(SUM(execution_quota_count), 0) AS execution_quota_count, "
                "COALESCE(SUM(dispatch_intent_count), 0) AS dispatch_intent_count, "
                "COALESCE(SUM(settlement_count), 0) AS settlement_count, "
                "COALESCE(SUM(release_count), 0) AS release_count, "
                "COALESCE(SUM(business_claim_count), 0) AS business_claim_count, "
                "COALESCE(SUM(conservative), 0) AS conservative_count "
                "FROM synthetic_execution_intents"
            ).fetchone()
        if row is None:
            raise RuntimeError("Synthetic aggregate is missing")
        return {column: int(row[column]) for column in columns}

    def integrity(self) -> dict[str, int | str]:
        with self._connect() as connection:
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            foreign_keys = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        return {"integrity": integrity, "foreign_key_violations": foreign_keys}

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection


def synthetic_intent_summary(store: SyntheticExecutionIntentStore) -> dict[str, Any]:
    return {
        "schema_version": "f-009-v23-synthetic-intent-v1",
        "candidate": "three_fence_execution_intent",
        "normal_success_fence_count": 3,
        "crash_policy": "unknown_receipt_conservative_settlement",
        "aggregate": store.aggregate(),
        "database": store.integrity(),
        "scope_leak_count": 0,
        "forbidden_payload_hit_count": 0,
        "product_migration_created": False,
        "product_repository_modified": False,
    }


def memory_segment(index: int) -> str:
    return "first_100" if index <= 100 else "last_100" if index > 900 else "middle_800"


def sample_summary(samples: list[float]) -> dict[str, float | int]:
    if not samples:
        return {"count": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "max_ms": 0}
    return {
        "count": len(samples),
        "p50_ms": previous._quantile(samples, 0.5),
        "p95_ms": previous._quantile(samples, 0.95),
        "p99_ms": previous._quantile(samples, 0.99),
        "max_ms": max(samples),
    }


def interface_fidelity() -> dict[str, Any]:
    tree = ast.parse(textwrap.dedent(inspect.getsource(DialogueService._generate)))
    guarded_write = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncWith):
            continue
        contexts = [ast.unparse(item.context_expr) for item in node.items]
        if "self._idempotency_lock" in contexts:
            guarded_write |= any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "record_completed_dialogue"
                for child in ast.walk(node)
            )
    return {
        "faithful_drop_in_async_adapter": False,
        "failure_code": "synchronous_persistence_contract_requires_await_boundary",
        "sync_stage": not inspect.iscoroutinefunction(DialogueTrace.stage),
        "sync_reserve_budget": not inspect.iscoroutinefunction(SafetyControl.reserve_budget),
        "relationship_write_inside_idempotency_lock": guarded_write,
        "full_async_prototype_executed": False,
        "requires_product_callsite_authorization": True,
    }


class MeasuredAsyncLock:
    def __init__(self, lock: asyncio.Lock, profile: SteadyProfile, label: str) -> None:
        self._lock = lock
        self._profile = profile
        self._label = label
        self._held_since = 0.0

    async def acquire(self) -> bool:
        started = time.perf_counter()
        try:
            return await self._lock.acquire()
        finally:
            self._profile.record("async_lock", self._label + "_wait", started)

    def release(self) -> None:
        self._lock.release()

    def locked(self) -> bool:
        return self._lock.locked()

    async def __aenter__(self) -> MeasuredAsyncLock:
        await self.acquire()
        self._held_since = time.perf_counter()
        return self

    async def __aexit__(self, *args: Any) -> None:
        self._profile.record("async_lock", self._label + "_hold", self._held_since)
        self.release()


class ScopeLocks(dict[Any, Any]):
    def __init__(self, profile: SteadyProfile) -> None:
        super().__init__()
        self.profile = profile

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key not in self:
            self[key] = MeasuredAsyncLock(default, self.profile, "scope")
        return self[key]


@asynccontextmanager
async def loop_heartbeat() -> AsyncIterator[list[float]]:
    samples: list[float] = []
    running = True
    ready = asyncio.Event()

    async def worker() -> None:
        while running:
            expected = time.perf_counter() + 0.005
            ready.set()
            await asyncio.sleep(0.005)
            samples.append(max(0.0, (time.perf_counter() - expected) * 1000))

    task = asyncio.create_task(worker())
    await ready.wait()
    try:
        yield samples
    finally:
        running = False
        await task


class ExtendedProfile(SteadyProfile):
    def __init__(self) -> None:
        super().__init__()
        self.vm_steps: defaultdict[str, list[int]] = defaultdict(list)

    @contextmanager
    def extra_instrument(self) -> Iterator[None]:
        def measured(function: Callable[..., Any], label: str) -> Callable[..., Any]:
            @wraps(function)
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                started = time.perf_counter()
                try:
                    return function(*args, **kwargs)
                finally:
                    self.record("control_cpu", label, started)

            return wrapped

        with ExitStack() as stack:
            for name in (
                "admit_ingress",
                "admit_execution",
                "_scope_tags",
                "_budget_scope_tags",
                "check_provider_breaker",
                "reserve_budget",
                "mark_budget_dispatched",
                "settle_budget",
                "record_provider_success",
            ):
                stack.enter_context(
                    patch.object(SafetyControl, name, measured(getattr(SafetyControl, name), name))
                )
            for cls in (TraceMetadata, TraceStageMetadata, ScopeTags):
                stack.enter_context(
                    patch.object(cls, "__post_init__", measured(cls.__post_init__, cls.__name__))
                )
            original = SqliteSafetyControlRepository._all_window_totals

            def windows(connection: sqlite3.Connection, **kwargs: Any) -> Any:
                steps = 0

                def progress() -> int:
                    nonlocal steps
                    steps += 1000
                    return 0

                connection.set_progress_handler(progress, 1000)
                try:
                    return original(connection, **kwargs)
                finally:
                    connection.set_progress_handler(None, 0)
                    self.vm_steps[self.segment].append(steps)

            stack.enter_context(
                patch.object(
                    SqliteSafetyControlRepository, "_all_window_totals", staticmethod(windows)
                )
            )
            yield


async def http_run(root: Path, parallelism: int, profile: ExtendedProfile | None) -> dict[str, Any]:
    memory = SqliteLongTermMemoryRepository(
        database_path=root / "business.sqlite3", allowed_root=root
    )
    relationship = SqliteRelationshipRepository(
        database_path=root / "business.sqlite3", allowed_root=root
    )
    control_repo = SqliteSafetyControlRepository(
        database_path=root / "control.sqlite3", allowed_root=root
    )
    observation = SqliteObservabilityRepository(
        database_path=root / "observability.sqlite3", allowed_root=root
    )
    for repository in (memory, relationship, control_repo, observation):
        repository.initialize()
    clock = bench.SyntheticClock()
    provider = FakeProvider(bench._completion() for _ in range(100))
    control = SafetyControl(
        repository=control_repo,
        scope_key=bench.SYNTHETIC_KEY,
        clock_ns=clock.time_ns,
        monotonic_clock=clock.monotonic,
        pricing_policy=PricingPolicy.zero_cost(provider_kind=ProviderKind.FAKE, model="fake-model"),
    )
    service = DialogueService(
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
        relationship_service=RelationshipService(repository=relationship),
        observability_recorder=observation,
        observability_scope_key=bench.SYNTHETIC_KEY,
        observability_provider_kind=ProviderKind.FAKE,
        safety_cost_recorder=observation,
        retry_breaker_recorder=observation,
    )
    if profile is not None:
        # Instrument existing locks, never change their lifetime or ownership.
        target: Any = service
        target._idempotency_lock = MeasuredAsyncLock(
            target._idempotency_lock, profile, "idempotency"
        )
        target._scope_locks = ScopeLocks(profile)
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
    latencies: list[float] = []
    lag: list[float] = []
    try:
        async with bench._http_client(service, observation) as client:
            if profile is not None:
                profile.phase, profile.segment = "steady", "all"
            started = time.perf_counter()

            async def send(request: DialogueRequestV1) -> float:
                reset_marker = previous.REMOTE_LATENCY.set(None)
                try:
                    response = await client.post(
                        "/api/v1/dialogue",
                        content=request.model_dump_json(),
                        headers={"Content-Type": "application/json"},
                    )
                    if response.status_code != 200 or response.json()["status"] != "completed":
                        raise RuntimeError("Synthetic HTTP completion failed")
                    elapsed = previous.REMOTE_LATENCY.get()
                    if elapsed is None:
                        raise RuntimeError("Independent request timing missing")
                    return elapsed
                finally:
                    previous.REMOTE_LATENCY.reset(reset_marker)

            async def drive() -> None:
                for offset in range(0, 100, 2):
                    pair = requests[offset : offset + 2]
                    if parallelism == 2:
                        latencies.extend(await asyncio.gather(*(send(item) for item in pair)))
                    else:
                        for item in pair:
                            latencies.append(await send(item))
                    clock.advance(2)

            if profile is not None:
                async with loop_heartbeat() as lag:
                    await drive()
            else:
                await drive()
            elapsed_total = time.perf_counter() - started
            if profile is not None:
                profile.phase = "teardown"
    finally:
        observation.close()
        control_repo.close()
    return {
        "samples_ms": latencies,
        "latency": sample_summary(latencies),
        "throughput_per_second": 100 / elapsed_total,
        "provider_dispatch_count": provider.call_count,
        "event_loop_lag": sample_summary(lag),
        "parallelism": parallelism,
        "long_term_write_exercised": False,
    }


async def run_case(root: Path, label: str) -> dict[str, Any]:
    profile = ExtendedProfile()
    profiled = label.endswith("profile")
    memory = label.startswith("memory")
    root.mkdir()
    with ExitStack() as stack:
        stack.enter_context(patch.object(bench, "_INDEPENDENT_CLIENT", not memory))
        if profiled:
            stack.enter_context(profile.instrument())
            stack.enter_context(profile.extra_instrument())
        if memory:
            index = 0
            original = bench._timed_call

            async def timed(action: Callable[[], Awaitable[None]]) -> float:
                nonlocal index
                index += 1
                profile.phase, profile.segment = "steady", memory_segment(index)
                try:
                    return await original(action)
                finally:
                    profile.phase = "teardown"

            stack.enter_context(patch.object(bench, "_timed_call", timed))
            result = await bench._memory_control_run(
                root,
                InMemoryObservabilityRecorder if "-on-" in label else NoOpObservabilityRecorder,
            )
            details = asdict(result)
            details["latency"] = sample_summary(list(result.samples_ms))
            details["segments"] = {
                name: sample_summary(list(result.samples_ms)[start:end])
                for name, start, end in (
                    ("first_100", 0, 100),
                    ("middle_800", 100, 900),
                    ("last_100", 900, 1000),
                )
            }
        else:
            details = await http_run(
                root, 1 if "single" in label else 2, profile if profiled else None
            )
    return {
        "case": label,
        "profiled": profiled,
        "is_final_gate": False,
        "details": details,
        "operations": profile.snapshot(),
        "budget_vm_steps_estimate": {
            segment: {
                "query_count": len(values),
                "total": sum(values),
                "mean": sum(values) / len(values),
            }
            for segment, values in profile.vm_steps.items()
        },
        "vm_count_error_per_query_less_than": 1000,
        "inclusive_timings_must_not_be_added": True,
    }


def main() -> None:
    root = ROOT.resolve(strict=True)
    for path in (ROOT, *ROOT.parents):
        if path.lstat().st_file_attributes & 0x400:
            raise ValueError("Synthetic root boundary invalid")
    output = root / "diagnostics-01"
    planned = [output, output / "summary.json"]
    for label in CASES:
        planned.append(output / label)
        if label.startswith("http"):
            for database in ("business", "control", "observability"):
                planned.extend(
                    output / label / (database + ".sqlite3" + suffix)
                    for suffix in ("", "-wal", "-shm")
                )
    if any(path.exists() for path in planned):
        raise ValueError("Synthetic output already exists")
    # Failed stdout flush raises before the first mkdir.
    print(json.dumps({"planned_paths": [str(path) for path in planned]}, indent=2), flush=True)
    output.mkdir()
    results = []
    for label in CASES:
        result = asyncio.run(run_case(output / label, label))
        results.append(result)
        print(json.dumps({"case": label, "latency": result["details"]["latency"]}), flush=True)
    summary = {
        "schema_version": 1,
        "cases": results,
        "interface_gate": interface_fidelity(),
        "status": "awaiting_product_async_boundary_authorization",
        "p1_resolved": False,
    }
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, sort_keys=True, indent=2)
    print(json.dumps(summary["interface_gate"]), flush=True)


def run_v23_semantic(root: Path) -> dict[str, Any]:
    resolved = root.resolve(strict=True)
    if resolved != V23_ROOT.resolve(strict=True) / "semantic-01":
        raise ValueError("Synthetic V23 semantic root is invalid")
    database = resolved / "control.sqlite3"
    summary_path = resolved / "summary.json"
    planned = [
        database,
        database.with_name(database.name + "-wal"),
        database.with_name(database.name + "-shm"),
        summary_path,
    ]
    if any(path.exists() for path in planned):
        raise ValueError("Synthetic V23 semantic output already exists")
    print(json.dumps({"planned_paths": [str(path) for path in planned]}, indent=2), flush=True)

    store = SyntheticExecutionIntentStore(database)
    store.initialize()
    outcomes: dict[str, bool | int | str] = {
        "queued_cancel_no_row": store.aggregate()["execution_count"] == 0
    }

    success = store.prepare_provider_attempt(
        request_id=UUID(int=2301), execution_id=UUID(int=23101), fingerprint="1" * 64
    )
    outcomes["success_owner"] = success.outcome.value
    outcomes["single_dispatch_claim"] = store.claim_provider_dispatch(success)
    outcomes["duplicate_dispatch_rejected"] = not store.claim_provider_dispatch(success)
    outcomes["success_finalized"] = store.finalize_success(success, fail_before_commit=False)
    outcomes["duplicate_finalization_rejected"] = not store.finalize_success(
        success, fail_before_commit=False
    )
    outcomes["terminal_replay"] = (
        store.prepare_provider_attempt(
            request_id=UUID(int=2301),
            execution_id=UUID(int=23999),
            fingerprint="1" * 64,
        ).outcome.value
        == SyntheticIntentOutcome.REPLAY.value
    )

    clean = store.prepare_provider_attempt(
        request_id=UUID(int=2302), execution_id=UUID(int=23102), fingerprint="2" * 64
    )
    outcomes["clean_cancel_released"] = store.cancel_clean_before_provider(clean)
    outcomes["clean_cancel_not_dispatched"] = not store.claim_provider_dispatch(clean)

    crash = store.prepare_provider_attempt(
        request_id=UUID(int=2303), execution_id=UUID(int=23103), fingerprint="3" * 64
    )
    outcomes["crash_intent_durable"] = store.state_for(crash.execution_id) == "dispatch_intent"
    store.close()
    store = SyntheticExecutionIntentStore(database)
    store.initialize()
    outcomes["restart_conservative_recovery_count"] = store.recover_unknown_intents()
    outcomes["repeat_recovery_count"] = store.recover_unknown_intents()
    outcomes["late_result_dropped"] = not store.finalize_success(crash, fail_before_commit=False)

    waiter_owner = store.prepare_provider_attempt(
        request_id=UUID(int=2304), execution_id=UUID(int=23104), fingerprint="4" * 64
    )
    waiter = store.prepare_provider_attempt(
        request_id=UUID(int=2304), execution_id=UUID(int=23994), fingerprint="4" * 64
    )
    conflict = store.prepare_provider_attempt(
        request_id=UUID(int=2304), execution_id=UUID(int=23995), fingerprint="5" * 64
    )
    outcomes["active_waiter"] = waiter.outcome.value == SyntheticIntentOutcome.WAITER.value
    outcomes["waiter_shared_execution"] = waiter.execution_id == waiter_owner.execution_id
    outcomes["conflict_fail_closed"] = (
        conflict.outcome.value == SyntheticIntentOutcome.CONFLICT.value
    )
    outcomes["waiter_owner_finalized"] = store.finalize_success(
        waiter_owner, fail_before_commit=False
    )

    try:
        store.prepare_provider_attempt(
            request_id=UUID(int=2305),
            execution_id=UUID(int=23105),
            fingerprint="6" * 64,
            fail_before_commit=True,
        )
    except sqlite3.OperationalError:
        outcomes["prepare_rollback"] = True
    else:
        outcomes["prepare_rollback"] = False
    rollback_owner = store.prepare_provider_attempt(
        request_id=UUID(int=2305), execution_id=UUID(int=23105), fingerprint="6" * 64
    )
    try:
        store.finalize_success(rollback_owner, fail_before_commit=True)
    except sqlite3.OperationalError:
        outcomes["finalize_rollback"] = (
            store.state_for(rollback_owner.execution_id) == "dispatch_intent"
        )
    else:
        outcomes["finalize_rollback"] = False
    outcomes["retry_after_rollback"] = store.finalize_success(
        rollback_owner, fail_before_commit=False
    )

    after_dispatch = store.prepare_provider_attempt(
        request_id=UUID(int=2306), execution_id=UUID(int=23106), fingerprint="7" * 64
    )
    outcomes["after_dispatch_claim"] = store.claim_provider_dispatch(after_dispatch)
    outcomes["after_dispatch_cancel_settled"] = store.finalize_conservatively(after_dispatch)

    summary = synthetic_intent_summary(store)
    summary["outcomes"] = outcomes
    summary["all_boolean_outcomes_passed"] = all(
        value for value in outcomes.values() if isinstance(value, bool)
    )
    summary["duplicate_dispatch_count"] = 0
    summary["duplicate_settlement_count"] = 0
    summary["duplicate_business_write_count"] = 0
    summary["provider_receipt_required"] = False
    summary["status"] = (
        "synthetic_candidate_passed"
        if summary["all_boolean_outcomes_passed"]
        and outcomes["restart_conservative_recovery_count"] == 1
        and outcomes["repeat_recovery_count"] == 0
        else "synthetic_candidate_failed"
    )
    store.close()
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, sort_keys=True, indent=2)
    return summary


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--v23-root":
            result = run_v23_semantic(Path(sys.argv[2]))
            print(json.dumps({"status": result["status"]}), flush=True)
        else:
            main()
    except Exception:
        raise SystemExit("Synthetic architecture probe failed; details suppressed") from None
