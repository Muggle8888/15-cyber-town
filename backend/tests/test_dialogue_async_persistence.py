"""Synthetic real-repository checks of the async application boundary."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import threading
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from cyber_town.application.budget import BudgetReservation, PricingPolicy
from cyber_town.application.control import SafetyControl
from cyber_town.application.dialogue import (
    DialogueExecutionConfig,
    DialogueService,
    DialogueUseCaseError,
)
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.memory import ConversationScope
from cyber_town.application.observability import (
    DialogueTrace,
    InMemoryObservabilityRecorder,
    ProviderKind,
    TraceMetadata,
    TraceStage,
    TraceStageMetadata,
)
from cyber_town.application.provider import ProviderCompletion, ProviderRequest
from cyber_town.application.relationship import RelationshipService
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.domain.long_term_memory import LongTermMemoryScope
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.observability.sqlite_observability import (
    ObservabilityQuery,
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import SqliteRelationshipRepository

KEY = b"synthetic-v6-async-local-key"


def _historical_case_root(environment_name: str, label: str) -> Path:
    raw_root = os.environ.get(environment_name)
    if raw_root is None:
        pytest.skip("Historical diagnostic root is not configured")
    parent = Path(raw_root)
    if not parent.is_absolute() or not parent.is_dir():
        pytest.fail(
            "Historical diagnostic root is not a registered absolute directory", pytrace=False
        )
    if parent.is_symlink() or (hasattr(os.path, "isjunction") and os.path.isjunction(parent)):
        pytest.fail("Historical diagnostic root cannot be a reparse point", pytrace=False)
    root = parent / label
    if root.exists():
        pytest.fail("Historical diagnostic case root must be fresh", pytrace=False)
    root.mkdir()
    return root


def test_missing_v8_historical_root_skips_without_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("F009_V8_BATCH", raising=False)
    sentinel = "SYNTHETIC-ENV-VALUE-MUST-NOT-APPEAR"
    monkeypatch.setenv("F009_UNRELATED_SENTINEL", sentinel)
    with pytest.raises(pytest.skip.Exception) as captured:
        _historical_case_root("F009_V8_BATCH", "idempotency_resolution")
    assert sentinel not in str(captured.value)


@pytest.mark.parametrize("blocked_stage", ["idempotency_resolution", "state_commit"])
def test_unrelated_scope_progresses_during_persistence_boundary(
    blocked_stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pause one real-disk stage acknowledgement, not the shared SQLite worker."""
    root = _historical_case_root("F009_V8_BATCH", blocked_stage)

    async def scenario() -> None:
        service, provider, recorder, control = build(root)
        first_request = command()
        paused, release = asyncio.Event(), asyncio.Event()
        original = DialogueTrace.astage

        async def boundary(trace: DialogueTrace, stage: TraceStage, *args: Any, **kw: Any) -> None:
            await original(trace, stage, *args, **kw)
            if trace.request_id == first_request.request_id and stage.value == blocked_stage:
                paused.set()
                await release.wait()

        monkeypatch.setattr(DialogueTrace, "astage", boundary)
        first = asyncio.create_task(service.execute(first_request, trace_id=uuid4()))
        second: asyncio.Task[Any] | None = None
        try:
            await asyncio.wait_for(paused.wait(), 5)
            second = asyncio.create_task(
                service.execute(command("signal_archivist"), trace_id=uuid4())
            )
            done, _ = await asyncio.wait({second}, timeout=2)
            assert second in done, "unrelated scope blocked by global persistence critical section"
            assert second.result().status.value == "completed"
        finally:
            release.set()
            await asyncio.gather(first, *(() if second is None else (second,)))
            await service.aclose()
            recorder.close()
            control.close()
        assert provider.call_count == 2

    asyncio.run(scenario())


def test_pending_admission_preserves_capacity_single_execution_and_conflict(
    database_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        service._config = replace(service._config, idempotency_max_entries=1)
        request = command()
        entered, release = asyncio.Event(), asyncio.Event()
        original = DialogueTrace.astage

        async def boundary(trace: DialogueTrace, stage: TraceStage, *args: Any, **kw: Any) -> None:
            await original(trace, stage, *args, **kw)
            if (
                trace.request_id == request.request_id
                and stage is TraceStage.IDEMPOTENCY_RESOLUTION
            ):
                entered.set()
                await release.wait()

        monkeypatch.setattr(DialogueTrace, "astage", boundary)
        owner = asyncio.create_task(service.execute(request, trace_id=uuid4()))
        peer: asyncio.Task[Any] | None = None
        conflict: asyncio.Task[Any] | None = None
        try:
            await asyncio.wait_for(entered.wait(), 5)
            assert service._pending_admissions == {request.request_id}
            with pytest.raises(DialogueUseCaseError) as error:
                await asyncio.wait_for(
                    service.execute(command("night_courier"), trace_id=uuid4()), 3
                )
            assert error.value.code.value == "provider_unavailable"
            peer = asyncio.create_task(service.execute(request, trace_id=uuid4()))
            changed = request.model_copy(update={"npc_id": "signal_archivist"})
            conflict = asyncio.create_task(service.execute(changed, trace_id=uuid4()))
            release.set()
            assert (await owner).reply == (await peer).reply
            with pytest.raises(DialogueUseCaseError) as collision:
                await conflict
            assert collision.value.code.value == "conflict"
            assert provider.call_count == control.budget_settlement_count() == 1
            assert not service._pending_admissions and not service._ownership_locks
        finally:
            release.set()
            await asyncio.gather(
                owner,
                *[task for task in (peer, conflict) if task is not None],
                return_exceptions=True,
            )
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


class MemoryBoundaryRecorder(InMemoryObservabilityRecorder):
    """Durable-protocol fake; no claim of disk persistence or crash recovery."""

    def __init__(self) -> None:
        super().__init__()
        self.current: TraceMetadata | None = None
        self.stages: tuple[TraceStageMetadata, ...] = ()
        self.finish_calls = 0
        self.progress_hook: Callable[[TraceStageMetadata], None] = lambda stage: None

    def start_trace(self, trace: TraceMetadata) -> None:
        self.current = trace

    def record_progress(self, trace: TraceMetadata, stage: TraceStageMetadata) -> None:
        self.current = trace
        self.progress_hook(stage)

    def finish_trace(self, trace: TraceMetadata, stages: Sequence[TraceStageMetadata]) -> None:
        self.current = trace
        self.stages = tuple(stages)
        self.finish_calls += 1


def memory_boundary_service(
    *, known_persona: bool
) -> tuple[DialogueService, FakeProvider, MemoryBoundaryRecorder, AsyncSqliteExecutor]:
    recorder = MemoryBoundaryRecorder()
    executor = AsyncSqliteExecutor()
    provider = FakeProvider([])
    service = DialogueService(
        personas=load_bundled_personas() if known_persona else {},
        provider=provider,
        config=DialogueExecutionConfig(
            model="deepseek-flash",
            temperature=0.6,
            max_tokens=256,
            timeout_seconds=12.0,
            max_concurrency=2,
            idempotency_ttl_seconds=600.0,
            idempotency_max_entries=256,
        ),
        observability_recorder=recorder,
        observability_scope_key=KEY,
        observability_provider_kind=ProviderKind.FAKE,
        storage_executor=executor,
    )
    return service, provider, recorder, executor


def test_persona_rejection_without_cancel_keeps_contract_in_memory() -> None:
    async def scenario() -> None:
        service, provider, recorder, _ = memory_boundary_service(known_persona=False)
        try:
            with pytest.raises(DialogueUseCaseError) as failure:
                await service.execute(command(), trace_id=uuid4())
            assert failure.value.code.value == "npc_not_found"
            assert not failure.value.retryable
            assert recorder.current is not None
            assert recorder.current.record_status.value == "complete"
            assert recorder.current.terminal_outcome is not None
            assert recorder.current.terminal_outcome.value == "rejected"
            assert recorder.current.error_code.value == "npc_not_found"
            assert recorder.current.reason_code.value == "not_reached"
            assert recorder.finish_calls == 1 and len(recorder.stages) == 14
            assert recorder.current.provider_dispatch_count == provider.call_count == 0
        finally:
            await service.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("known_persona", [True, False], ids=["known", "missing"])
@pytest.mark.parametrize("queued", [True, False], ids=["queued", "running"])
@pytest.mark.parametrize("cancel_count", [1, 2], ids=["once", "twice"])
def test_persona_cancel_closes_trace_in_memory(
    known_persona: bool,
    queued: bool,
    cancel_count: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        service, provider, recorder, executor = memory_boundary_service(known_persona=known_persona)
        entered, release = threading.Event(), threading.Event()
        busy, busy_release = threading.Event(), threading.Event()
        persona_submitted = asyncio.Event()
        original_run = executor.run

        def progress(stage: TraceStageMetadata) -> None:
            blocked = TraceStage.REQUEST_VALIDATION if queued else TraceStage.PERSONA_RESOLUTION
            if stage.stage is blocked:
                entered.set()
                assert release.wait(3)

        def block_lane() -> None:
            busy.set()
            assert busy_release.wait(3)

        async def observed_run(lane: Any, operation: Any, **kwargs: Any) -> Any:
            if (
                isinstance(operation, partial)
                and operation.func == recorder.record_progress
                and operation.args[1].stage is TraceStage.PERSONA_RESOLUTION
            ):
                persona_submitted.set()
            return await original_run(lane, operation, **kwargs)

        monkeypatch.setattr(executor, "run", observed_run)
        recorder.progress_hook = progress
        request = command()
        task = asyncio.create_task(service.execute(request, trace_id=uuid4()))
        blocker: asyncio.Task[None] | None = None
        try:
            await thread_started(entered)
            if queued:
                blocker = asyncio.create_task(executor.run("observability", block_lane))
                await asyncio.sleep(0)
                release.set()
                await thread_started(busy)
                await asyncio.wait_for(persona_submitted.wait(), 3)
            for _ in range(cancel_count):
                task.cancel()
                await asyncio.sleep(0)
            release.set()
            busy_release.set()
            if blocker is not None:
                await blocker
            with pytest.raises(asyncio.CancelledError):
                await task
            assert recorder.current is not None
            assert recorder.current.record_status.value == "complete"
            assert recorder.current.terminal_outcome is not None
            assert recorder.current.terminal_outcome.value == "cancelled"
            assert recorder.finish_calls == 1
            assert len(recorder.stages) == 14
            assert [stage.sequence for stage in recorder.stages] == list(range(1, 15))
            assert recorder.current.execution_id is None
            assert recorder.current.provider_dispatch_count == provider.call_count == 0
            assert recorder.current.cost_micro_usd == 0
            assert not service._idempotency
            surface = json.dumps(recorder.current.as_dict()) + json.dumps(
                [stage.as_dict() for stage in recorder.stages]
            )
            for value in (
                request.player_id,
                request.npc_id,
                str(request.conversation_id),
                request.message,
                KEY.decode(),
            ):
                assert value not in surface
        finally:
            release.set()
            busy_release.set()
            if blocker is not None:
                await blocker
            await service.aclose()

    asyncio.run(scenario())


@pytest.fixture
def database_root(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Path:
    if os.environ.get("F009_V8_TESTROOT") is not None:
        name = hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:16]
        return _historical_case_root("F009_V8_TESTROOT", name)
    root = Path(tmp_path_factory.getbasetemp()) / re.sub(
        r"[^a-zA-Z0-9_-]", "_", str(request.node.name)
    )
    print(str(root), flush=True)
    for name in ("business.sqlite3", "control.sqlite3", "observability.sqlite3"):
        for suffix in ("", "-wal", "-shm"):
            print(str(root / (name + suffix)), flush=True)
    root.mkdir()
    return root


def command(
    npc: str = "neon_guide", message: str = "Synthetic offline hello."
) -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=uuid4(),
        player_id="synthetic_player",
        npc_id=npc,
        conversation_id=uuid4(),
        message=message,
    )


def build(
    root: Path,
    provider_override: FakeProvider | None = None,
) -> tuple[
    DialogueService, FakeProvider, SqliteObservabilityRepository, SqliteSafetyControlRepository
]:
    memory = SqliteLongTermMemoryRepository(
        database_path=root / "business.sqlite3", allowed_root=root
    )
    memory.initialize()
    relationships = SqliteRelationshipRepository(
        database_path=memory.database_path, allowed_root=root
    )
    relationships.initialize()
    control = SqliteSafetyControlRepository(
        database_path=root / "control.sqlite3", allowed_root=root
    )
    control.initialize()
    recorder = SqliteObservabilityRepository(
        database_path=root / "observability.sqlite3", allowed_root=root
    )
    recorder.initialize()
    provider = FakeProvider(
        [
            ProviderCompletion(
                content="Synthetic offline reply.",
                finish_reason="stop",
                choice_count=1,
                tool_calls_present=False,
                reasoning_content_present=False,
                provider="fake",
                model="deepseek-flash",
            )
            for _ in range(12)
        ]
    )
    provider = provider_override or provider
    service = DialogueService(
        personas=load_bundled_personas(),
        provider=provider,
        config=DialogueExecutionConfig(
            model="deepseek-flash",
            temperature=0.6,
            max_tokens=256,
            timeout_seconds=12.0,
            max_concurrency=2,
            idempotency_ttl_seconds=600.0,
            idempotency_max_entries=256,
        ),
        safety_control=SafetyControl(
            repository=control,
            scope_key=KEY,
            pricing_policy=PricingPolicy.zero_cost(
                provider_kind=ProviderKind.FAKE, model="deepseek-flash"
            ),
        ),
        long_term_memory=LongTermMemoryService(repository=memory),
        long_term_retriever=LongTermMemoryRetriever(repository=memory),
        relationship_service=RelationshipService(repository=relationships),
        observability_recorder=recorder,
        observability_scope_key=KEY,
        observability_provider_kind=ProviderKind.FAKE,
        storage_executor=AsyncSqliteExecutor(),
    )
    return service, provider, recorder, control


def test_real_three_database_completion_replay_and_metadata(database_root: Path) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        try:
            for npc in ("neon_guide", "signal_archivist", "night_courier"):
                request = command(npc)
                first = await service.execute(request, trace_id=uuid4())
                second = await service.execute(request, trace_id=uuid4())
                assert first.reply == second.reply and first.trace_id != second.trace_id
            assert provider.call_count == 3
            traces = recorder.query_traces(ObservabilityQuery(limit=100))
            with sqlite3.connect(recorder.database_path) as connection:
                assert connection.execute("SELECT COUNT(*) FROM trace_stage_events").fetchone() == (
                    84,
                )
            assert len(traces) == 6
            assert sum(record["provider_dispatch_count"] == 1 for record in traces) == 3
            assert all(record["cost_micro_usd"] == 0 for record in traces)
            with sqlite3.connect(control.database_path) as connection:
                assert connection.execute(
                    "SELECT COUNT(*) FROM execution_admissions"
                ).fetchone() == (3,)
                assert connection.execute(
                    "SELECT COUNT(*) FROM control_execution_intents "
                    "WHERE state='settled' AND terminal_reason='trusted_usage'"
                ).fetchone() == (3,)
                assert connection.execute("SELECT COUNT(*) FROM budget_settlements").fetchone() == (
                    3,
                )
                assert connection.execute(
                    "SELECT COUNT(*) FROM provider_permits WHERE released_at_ns IS NOT NULL"
                ).fetchone() == (3,)
            with sqlite3.connect(database_root / "business.sqlite3") as connection:
                assert connection.execute(
                    "SELECT COUNT(*) FROM relationship_events"
                ).fetchone() == (3,)
            rendered = repr(traces)
            for sentinel in (
                KEY.decode(),
                "synthetic_player",
                "Synthetic offline reply.",
                "Synthetic offline hello.",
            ):
                assert sentinel not in rendered
        finally:
            await service.aclose()
            recorder.close()
            control.close()
        for name in ("business.sqlite3", "control.sqlite3", "observability.sqlite3"):
            with sqlite3.connect(database_root / name) as connection:
                assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
                assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    asyncio.run(scenario())


class PausedProvider(FakeProvider):
    def __init__(self, *, ignore_cancel: bool = False) -> None:
        super().__init__(
            [
                ProviderCompletion(
                    content="Synthetic paused reply.",
                    finish_reason="stop",
                    choice_count=1,
                    tool_calls_present=False,
                    reasoning_content_present=False,
                    provider="fake",
                    model="deepseek-flash",
                )
                for _ in range(5)
            ]
        )
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.ignore_cancel = ignore_cancel

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        result = await super().complete(request)
        self.started.set()
        try:
            await self.release.wait()
        except asyncio.CancelledError:
            if not self.ignore_cancel:
                raise
            await self.release.wait()
        return result


async def thread_started(event: threading.Event) -> None:
    async with asyncio.timeout(3):
        while not event.is_set():
            await asyncio.sleep(0.001)


def test_cancel_during_reservation_reconciles_without_dispatch(
    database_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        started, release = threading.Event(), threading.Event()
        original = control.reserve_budget

        def reserve(**kwargs: Any) -> BudgetReservation:
            started.set()
            assert release.wait(3)
            return original(**kwargs)

        monkeypatch.setattr(control, "reserve_budget", reserve)
        task = asyncio.create_task(service.execute(command(), trace_id=uuid4()))
        try:
            await thread_started(started)
            task.cancel()
            # Let the detached HTTP waiter mark the execution as orphaned.
            with pytest.raises(asyncio.CancelledError):
                await task
            await asyncio.sleep(0.01)
            release.set()
            await service.aclose()
            assert provider.call_count == 0
            with sqlite3.connect(control.database_path) as connection:
                assert connection.execute("SELECT status FROM budget_reservations").fetchall() == [
                    ("released",)
                ]
                assert connection.execute("SELECT COUNT(*) FROM budget_settlements").fetchone() == (
                    0,
                )
        finally:
            release.set()
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_cancelled_close_drains_request_without_leaving_worker(
    database_root: Path,
) -> None:
    async def scenario() -> None:
        provider = PausedProvider()
        service, _, recorder, control = build(database_root, provider)
        request = asyncio.create_task(service.execute(command(), trace_id=uuid4()))
        await asyncio.wait_for(provider.started.wait(), 3)
        closing = asyncio.create_task(service.aclose())
        try:
            await asyncio.sleep(0)
            closing.cancel()
            await asyncio.sleep(0)
            assert not closing.done()
            provider.release.set()
            assert (await request).status.value == "completed"
            await closing
            assert isinstance(service.storage_executor, AsyncSqliteExecutor)
            with pytest.raises(RuntimeError):
                await service.storage_executor.run("control", lambda: None)
        finally:
            provider.release.set()
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_async_durable_open_restart_abandoned_is_idempotent(database_root: Path) -> None:
    async def scenario() -> None:
        service, _, recorder, control = build(database_root)
        request = command()
        trace = await service.observability.start_validated_async(
            trace_id=uuid4(),
            request_id=request.request_id,
            player_id=request.player_id,
            npc_id=request.npc_id,
            conversation_id=request.conversation_id,
            input_chars=len(request.message),
        )
        assert trace is not None
        assert recorder.query_traces(ObservabilityQuery(limit=10))[0]["record_status"] == "open"
        await service.aclose()
        recorder.close()
        control.close()
        restarted = SqliteObservabilityRepository(
            database_path=database_root / "observability.sqlite3",
            allowed_root=database_root,
        )
        try:
            restarted.initialize()
            assert restarted.recover_open_traces(now_utc=datetime.now(UTC)) == 1
            summary = restarted.query_traces(ObservabilityQuery(limit=10))
            assert summary[0]["terminal_outcome"] == "abandoned_after_restart"
            assert restarted.recover_open_traces(now_utc=datetime.now(UTC)) == 0
            assert restarted.query_traces(ObservabilityQuery(limit=10)) == summary
        finally:
            restarted.close()

    asyncio.run(scenario())


def test_async_recorder_failure_does_not_change_business_result(
    database_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        sentinel = "synthetic-recorder-detail-must-not-leak"

        def fail(*args: Any, **kwargs: Any) -> None:
            del args, kwargs
            raise RuntimeError(sentinel)

        for name in (
            "start_trace",
            "record_progress",
            "finish_trace",
            "record_safety_cost",
            "record_retry_breaker",
        ):
            monkeypatch.setattr(recorder, name, fail)
        try:
            request = command()
            assert (await service.execute(request, trace_id=uuid4())).status.value == "completed"
            assert (await service.execute(request, trace_id=uuid4())).status.value == "completed"
            assert provider.call_count == 1
            assert sentinel not in caplog.text
            with sqlite3.connect(database_root / "business.sqlite3") as connection:
                assert connection.execute(
                    "SELECT COUNT(*) FROM relationship_events"
                ).fetchone() == (1,)
        finally:
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_full_transaction_rollback_and_every_lease_path_check(
    database_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from contextlib import closing

    import cyber_town.infrastructure.persistence.sqlite_connection as connection_module
    from cyber_town.infrastructure.persistence.sqlite_connection import BoundedSqliteWriter

    async def scenario() -> None:
        executor = AsyncSqliteExecutor()
        writer = BoundedSqliteWriter(database_root / "business.sqlite3", allowed_root=database_root)
        calls = 0
        original = connection_module.validate_sqlite_path

        def validate(path: Path, allowed: Path) -> Any:
            nonlocal calls
            calls += 1
            return original(path, allowed)

        monkeypatch.setattr(connection_module, "validate_sqlite_path", validate)

        def create() -> None:
            with closing(writer.borrow(timeout_ms=1000)) as connection:
                assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)
                assert connection.execute("PRAGMA synchronous").fetchone() == (2,)
                connection.execute("CREATE TABLE synthetic (id INTEGER PRIMARY KEY)")

        def fail_after_write() -> None:
            with closing(writer.borrow(timeout_ms=1000)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("INSERT INTO synthetic VALUES (1)")
                raise ValueError("Synthetic transaction failure")

        def check() -> int:
            with closing(writer.borrow(timeout_ms=1000)) as connection:
                return int(connection.execute("SELECT COUNT(*) FROM synthetic").fetchone()[0])

        try:
            await executor.run("business", create)
            before = calls
            with pytest.raises(ValueError, match="Synthetic transaction failure"):
                await executor.run("business", fail_after_write)
            assert calls > before
            before = calls
            assert await executor.run("business", check) == 0
            assert calls > before
        finally:
            await executor.run("business", writer.close)
            await executor.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "management", ["Forget: game_alias", "Remember: game_alias=NEW-V6"], ids=["forget", "replace"]
)
def test_old_generation_cannot_commit_after_memory_revision(
    database_root: Path,
    management: str,
) -> None:
    async def scenario() -> None:
        provider = PausedProvider()
        service, _, recorder, control = build(database_root, provider)
        try:
            await service.execute(command(message="Remember: game_alias=OLD-V6"), trace_id=uuid4())
            old = command(message="What is my game_alias?")
            task = asyncio.create_task(service.execute(old, trace_id=uuid4()))
            await asyncio.wait_for(provider.started.wait(), 3)
            await service.execute(command(message=management), trace_id=uuid4())
            provider.release.set()
            with pytest.raises(DialogueUseCaseError):
                await task
            scope = ConversationScope(old.player_id, old.npc_id, old.conversation_id)
            assert service._session_store.begin(scope) == ()
            service._session_store.abort(scope)
        finally:
            provider.release.set()
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_cancel_queued_initial_stage_closes_durable_open_trace(
    database_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        opened, open_release = threading.Event(), threading.Event()
        busy, busy_release = threading.Event(), threading.Event()
        original = recorder.start_trace

        def open_trace(trace: Any) -> None:
            original(trace)
            opened.set()
            assert open_release.wait(3)

        def block_lane() -> None:
            busy.set()
            assert busy_release.wait(3)

        monkeypatch.setattr(recorder, "start_trace", open_trace)
        task = asyncio.create_task(service.execute(command(), trace_id=uuid4()))
        assert isinstance(service.storage_executor, AsyncSqliteExecutor)
        try:
            await thread_started(opened)
            blocker = asyncio.create_task(service.storage_executor.run("observability", block_lane))
            await asyncio.sleep(0)
            open_release.set()
            await thread_started(busy)
            # The request's first progress write is queued behind block_lane.
            async with asyncio.timeout(3):
                while len(service.storage_executor._pending) < 2:
                    await asyncio.sleep(0.001)
            await asyncio.sleep(0.02)
            task.cancel()
            await asyncio.sleep(0)
            busy_release.set()
            await blocker
            with pytest.raises(asyncio.CancelledError):
                await task
            traces = recorder.query_traces(ObservabilityQuery(limit=10))
            assert len(traces) == 1
            assert traces[0]["record_status"] == "complete"
            assert traces[0]["terminal_outcome"] == "cancelled"
            assert provider.call_count == 0
        finally:
            open_release.set()
            busy_release.set()
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_storage_failure_rejects_without_business_writes(
    database_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        from cyber_town.infrastructure.control.sqlite_control import SafetyControlStorageError

        original = control.reserve_budget

        def fail(**kwargs: Any) -> BudgetReservation:
            del kwargs
            raise SafetyControlStorageError()

        monkeypatch.setattr(control, "reserve_budget", fail)
        try:
            with pytest.raises(DialogueUseCaseError):
                await service.execute(command(), trace_id=uuid4())
            assert provider.call_count == 0
            monkeypatch.setattr(control, "reserve_budget", original)
            assert (
                await service.execute(command("signal_archivist"), trace_id=uuid4())
            ).status.value == "completed"
            assert provider.call_count == 1
        finally:
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("ignore_cancel", [False, True])
def test_orphan_and_late_provider_do_not_commit_history(
    database_root: Path,
    ignore_cancel: bool,
) -> None:
    async def scenario() -> None:
        provider = PausedProvider(ignore_cancel=ignore_cancel)
        service, _, recorder, control = build(database_root, provider)
        request = command()
        task = asyncio.create_task(service.execute(request, trace_id=uuid4()))
        try:
            await asyncio.wait_for(provider.started.wait(), 3)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            await asyncio.sleep(0.01)
            provider.release.set()
            await service.aclose()
            scope = ConversationScope(request.player_id, request.npc_id, request.conversation_id)
            assert service._session_store.begin(scope) == ()
            service._session_store.abort(scope)
            with sqlite3.connect(database_root / "business.sqlite3") as connection:
                assert connection.execute(
                    "SELECT COUNT(*) FROM relationship_events"
                ).fetchone() == (0,)
            with sqlite3.connect(control.database_path) as connection:
                assert connection.execute("SELECT status FROM budget_reservations").fetchall() == [
                    ("settled",)
                ]
                assert connection.execute("SELECT COUNT(*) FROM budget_settlements").fetchone() == (
                    1,
                )
        finally:
            provider.release.set()
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_cancelled_owner_does_not_cancel_shared_waiter(database_root: Path) -> None:
    async def scenario() -> None:
        provider = PausedProvider()
        service, _, recorder, control = build(database_root, provider)
        request = command()
        owner = asyncio.create_task(service.execute(request, trace_id=uuid4()))
        try:
            await asyncio.wait_for(provider.started.wait(), 3)
            waiter = asyncio.create_task(service.execute(request, trace_id=uuid4()))
            async with asyncio.timeout(3):
                while service._idempotency[request.request_id].waiters != 2:
                    await asyncio.sleep(0.001)
            owner.cancel()
            with pytest.raises(asyncio.CancelledError):
                await owner
            provider.release.set()
            response = await waiter
            assert response.status.value == "completed" and provider.call_count == 1
            replay = await service.execute(request, trace_id=uuid4())
            assert replay.reply == response.reply and provider.call_count == 1
        finally:
            provider.release.set()
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_long_term_write_restart_and_scope_ownership(database_root: Path) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        request = command(message="Remember: game_alias=SYNTHETIC-V6")
        try:
            response = await service.execute(request, trace_id=uuid4())
            assert response.provider == "local-memory" and provider.call_count == 0
            replay = await service.execute(request, trace_id=uuid4())
            assert replay.reply == response.reply
            before = recorder.query_traces(ObservabilityQuery(limit=100))
        finally:
            await service.aclose()
            recorder.close()
            control.close()
        restarted, restarted_provider, new_recorder, new_control = build(database_root)
        try:
            assert new_recorder.query_traces(ObservabilityQuery(limit=100)) == before
            retriever = restarted._long_term_retriever
            assert retriever is not None
            assert retriever.retrieve(
                LongTermMemoryScope("synthetic_player", "neon_guide"), "What is my game alias?"
            )
            assert (
                retriever.retrieve(
                    LongTermMemoryScope("synthetic_player", "signal_archivist"),
                    "What is my game alias?",
                )
                == ()
            )
            assert (
                retriever.retrieve(
                    LongTermMemoryScope("other_player", "neon_guide"), "What is my game alias?"
                )
                == ()
            )
            scope = ConversationScope(request.player_id, request.npc_id, request.conversation_id)
            assert restarted._session_store.begin(scope) == ()
            restarted._session_store.abort(scope)
            assert restarted_provider.call_count == 0
            assert new_recorder.recover_open_traces(now_utc=datetime.now(UTC)) == 0
        finally:
            await restarted.aclose()
            new_recorder.close()
            new_control.close()

    asyncio.run(scenario())


def test_close_drains_request_and_rejects_new_request(database_root: Path) -> None:
    async def scenario() -> None:
        provider = PausedProvider()
        service, _, recorder, control = build(database_root, provider)
        task = asyncio.create_task(service.execute(command(), trace_id=uuid4()))
        try:
            await asyncio.wait_for(provider.started.wait(), 3)
            closing = asyncio.create_task(service.aclose())
            await asyncio.sleep(0)
            assert not closing.done()
            with pytest.raises(DialogueUseCaseError):
                await service.execute(command(), trace_id=uuid4())
            provider.release.set()
            assert (await task).status.value == "completed"
            await closing
        finally:
            provider.release.set()
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())
