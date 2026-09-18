"""V7 synthetic attribution foundations and real-database cancellation gates."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest

from cyber_town.application.observability import (
    AttemptKind,
    IdempotencyOutcome,
    RecordStatus,
    TerminalOutcome,
    TraceMetadata,
    TraceReasonCode,
)


def replay_metadata() -> TraceMetadata:
    from test_observability import metadata

    return metadata(
        attempt_kind=AttemptKind.CACHE_REPLAY,
        execution_id=None,
        idempotency_outcome=IdempotencyOutcome.CACHE_REPLAY,
        from_cache=True,
        provider_dispatch_count=0,
        terminal_outcome=TerminalOutcome.REPLAYED,
        reason_code=TraceReasonCode.CACHE_REPLAY,
    )


@pytest.mark.parametrize("terminal", [TerminalOutcome.REPLAYED, TerminalOutcome.CANCELLED])
def test_replay_dto_accepts_exact_terminal_contract(
    terminal: TerminalOutcome, caplog: pytest.LogCaptureFixture
) -> None:
    from test_observability import SYNTHETIC_HMAC_KEY

    trace = replace(
        replay_metadata(),
        terminal_outcome=terminal,
        reason_code=(
            TraceReasonCode.CANCELLED
            if terminal is TerminalOutcome.CANCELLED
            else TraceReasonCode.CACHE_REPLAY
        ),
    )
    assert trace.attempt_kind is AttemptKind.CACHE_REPLAY
    assert trace.idempotency_outcome is IdempotencyOutcome.CACHE_REPLAY
    assert trace.from_cache is True and trace.execution_id is None
    assert trace.provider_dispatch_count == trace.cost_micro_usd == 0
    assert trace.record_status is RecordStatus.COMPLETE
    assert trace.request_id is not None and trace.scope_tags is not None
    surfaces = json.dumps(trace.as_dict()) + repr(trace) + caplog.text
    for sentinel in (
        "synthetic_player",
        "neon_guide",
        "66666666-6666-4666-8666-666666666666",
        SYNTHETIC_HMAC_KEY.decode(),
    ):
        assert sentinel not in surfaces


@pytest.mark.parametrize("terminal", [TerminalOutcome.REPLAYED, TerminalOutcome.CANCELLED])
@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"from_cache": False}, id="from-cache-false"),
        pytest.param({"from_cache": 1}, id="from-cache-type"),
        pytest.param({"execution_id": uuid4()}, id="execution-id"),
        pytest.param({"provider_dispatch_count": 1}, id="dispatch"),
        pytest.param({"provider_dispatch_count": True}, id="dispatch-type"),
        pytest.param({"cost_micro_usd": 1}, id="cost"),
        pytest.param({"idempotency_outcome": IdempotencyOutcome.NEW}, id="new"),
        pytest.param({"idempotency_outcome": IdempotencyOutcome.INFLIGHT_SHARED}, id="shared"),
        pytest.param({"scope_tags": None}, id="missing-scope"),
        pytest.param({"request_id": None}, id="missing-request"),
        pytest.param({"record_status": RecordStatus.OPEN}, id="open"),
        pytest.param({"attempt_kind": AttemptKind.INITIAL}, id="wrong-attempt"),
    ],
)
def test_replay_dto_rejects_other_invalid_combinations(
    terminal: TerminalOutcome, changes: dict[str, Any]
) -> None:
    with pytest.raises((ValueError, TypeError)):
        replace(replay_metadata(), terminal_outcome=terminal, **changes)


@pytest.mark.parametrize(
    "terminal",
    [
        value
        for value in TerminalOutcome
        if value not in {TerminalOutcome.REPLAYED, TerminalOutcome.CANCELLED}
    ],
)
def test_replay_dto_rejects_other_terminal_outcomes(terminal: TerminalOutcome) -> None:
    with pytest.raises(ValueError, match="Cache replay invariants"):
        replace(replay_metadata(), terminal_outcome=terminal)


@pytest.mark.parametrize(
    "field",
    [
        "scope_tags",
        "request_id",
        "execution_id",
        "terminal_outcome",
        "idempotency_outcome",
        "from_cache",
        "provider_dispatch_count",
        "cost_micro_usd",
    ],
)
def test_replay_dto_rejects_raw_payload_without_echo(
    field: str, caplog: pytest.LogCaptureFixture
) -> None:
    sentinel = "SYNTHETIC-RAW-SCOPE-MESSAGE-SYSTEM-MEMORY-SUGGESTION-PROVIDER-SECRET"
    changes: dict[str, Any] = {"terminal_outcome": TerminalOutcome.CANCELLED, field: sentinel}
    with pytest.raises((ValueError, TypeError)) as captured:
        replace(replay_metadata(), **changes)
    assert sentinel not in str(captured.value) + repr(captured.value) + caplog.text


def module() -> Any:
    from scripts import f009_step5_attribution

    return f009_step5_attribution


def test_v9_registration_failure_blocks_every_create() -> None:
    tool = module()
    paths = (tool.APPROVED_ROOT / "unit-a", tool.APPROVED_ROOT / "unit-b")
    events: list[Path] = []
    with pytest.raises(ValueError, match="registration"):
        tool.prepare_registered_directories(
            paths, registered=paths[:1], announce=events.append, create=events.append
        )
    assert not events


def test_v9_nested_thread_spans_have_parent_and_storage_identity() -> None:
    tool = module()
    probe = tool.DiagnosticProbe()

    async def scenario() -> None:
        from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor

        executor = AsyncSqliteExecutor()
        with probe.instrument(), probe.owner(11, tool.Lane.EVENT_LOOP):
            assert (
                await executor.run(
                    "business", lambda: probe.measure(tool.Operation.SQL, lambda: 123)
                )
                == 123
            )
            await executor.aclose()

    asyncio.run(scenario())
    rows = probe.snapshot()
    storage = next(row for row in rows if row["operation"] == "storage")
    repository = next(row for row in rows if row["operation"] == "repository")
    sql = next(row for row in rows if row["operation"] == "sql")
    assert repository["parent_index"] == storage["operation_index"]
    assert sql["parent_index"] == repository["operation_index"]
    assert {row["storage_index"] for row in rows} == {storage["operation_index"]}
    assert {row["case_index"] for row in rows} == {11}
    assert len({row["operation_index"] for row in rows}) == len(rows)
    summary = probe.attribution_summary(11)
    assert summary["span_union_ns"] == storage["end_ns"] - storage["start_ns"]
    assert 0 <= summary["exclusive_ns"]["repository"] < summary["union_ns"]["repository"]


@pytest.mark.parametrize("kind", ["request", "owner"])
def test_v9_guard_preserves_reference_counts_waiters_and_cancel(kind: str) -> None:
    from uuid import UUID

    from cyber_town.application.dialogue import DialogueService
    from cyber_town.domain.long_term_memory import LongTermMemoryScope

    tool = module()
    probe = tool.DiagnosticProbe()
    service = object.__new__(DialogueService)
    service._ownership_locks = tool.MeasuredOwnershipLocks(probe)
    service._pending_admissions = set()
    key = (
        UUID(int=17)
        if kind == "request"
        else LongTermMemoryScope(player_id="synthetic_private_owner", npc_id="neon_guide")
    )

    async def scenario() -> None:
        entered, release = asyncio.Event(), asyncio.Event()

        async def holder() -> None:
            with probe.owner(1, tool.Lane.EVENT_LOOP):
                async with service._ownership_guard(key):
                    entered.set()
                    await release.wait()

        async def waiter() -> None:
            with probe.owner(2, tool.Lane.EVENT_LOOP):
                async with service._ownership_guard(key):
                    raise AssertionError("Cancelled waiter must not acquire")

        first = asyncio.create_task(holder())
        await entered.wait()
        guard = service._ownership_locks[key]
        second = asyncio.create_task(waiter())
        await asyncio.sleep(0)
        assert service._ownership_locks[key] is guard and guard.users == 2
        second.cancel()
        second.cancel()
        with pytest.raises(asyncio.CancelledError):
            await second
        assert guard.users == 1 and guard.lock.locked()
        release.set()
        await first
        assert not service._ownership_locks

    asyncio.run(scenario())
    rows = probe.snapshot()
    assert sum(row["operation"] == kind + "_wait" for row in rows) == 2
    assert sum(row["operation"] == kind + "_hold" for row in rows) == 1
    assert any(row["case_index"] == 2 and row["failed"] for row in rows)
    assert "synthetic_private_owner" not in json.dumps(rows)
    assert "neon_guide" not in json.dumps(rows)


@pytest.mark.parametrize("profiled", [False, True])
@pytest.mark.parametrize("finish_on_cancel", [False, True])
@pytest.mark.parametrize("timing", ["queued", "running", "error", "closed"])
def test_v9_executor_probe_transparent_cancellation_and_close(
    profiled: bool, finish_on_cancel: bool, timing: str
) -> None:
    from contextlib import nullcontext

    from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor

    tool = module()
    probe = tool.DiagnosticProbe()

    async def scenario() -> None:
        executor = AsyncSqliteExecutor()
        started, release = threading.Event(), threading.Event()
        calls: list[int] = []

        def operation() -> int:
            calls.append(1)
            started.set()
            assert release.wait(5)
            if timing == "error":
                raise LookupError("SYNTHETIC-PRIVATE-ERROR")
            return 42

        async def wait_started() -> None:
            async with asyncio.timeout(5):
                while not started.is_set():
                    await asyncio.sleep(0)

        with probe.instrument() if profiled else nullcontext(), probe.owner(3, tool.Lane.CONTROL):
            blocker = None
            try:
                if timing == "closed":
                    await executor.aclose()
                    with pytest.raises(RuntimeError):
                        await executor.run("control", operation)
                    assert calls == []
                    return
                if timing == "queued":
                    blocker = asyncio.create_task(executor.run("control", operation))
                    await wait_started()
                task = asyncio.create_task(
                    executor.run("control", operation, finish_on_cancel=finish_on_cancel)
                )
                if timing != "queued":
                    await wait_started()
                else:
                    await asyncio.sleep(0)
                if timing != "error":
                    task.cancel()
                    await asyncio.sleep(0)
                    task.cancel()
                    await asyncio.sleep(0)
                closing = asyncio.create_task(executor.aclose())
                release.set()
                if timing == "error":
                    with pytest.raises(LookupError):
                        await task
                elif finish_on_cancel and timing == "running":
                    assert await task == 42
                else:
                    with pytest.raises(asyncio.CancelledError):
                        await task
                if blocker is not None:
                    assert await blocker == 42
                await closing
                await executor.aclose()
                assert calls == [1]
            finally:
                release.set()
                await executor.aclose()

    asyncio.run(scenario())
    assert "SYNTHETIC-PRIVATE-ERROR" not in json.dumps(probe.snapshot())
    if profiled:
        assert all(row["case_index"] == 3 for row in probe.snapshot())
        assert any(row["operation"] == "storage" for row in probe.snapshot())


def test_v9_budget_and_permit_dto_probes_are_metadata_only() -> None:
    from cyber_town.application.budget import BudgetScopeTags
    from cyber_town.application.control import PermitScopeTags

    tool = module()
    probe = tool.DiagnosticProbe()
    tag = "a" * 64
    with probe.instrument(), probe.owner(4, tool.Lane.CONTROL):
        assert BudgetScopeTags(tag, tag, tag).player_scope_tag == tag
        assert PermitScopeTags(tag, tag, tag).player_scope_tag == tag
    rows = probe.snapshot()
    assert {row["operation"] for row in rows} == {"budget_dto", "permit_dto"}
    assert tag not in json.dumps(rows)


def test_v9_runner_bounds_and_manifest_are_exact() -> None:
    tool = module()
    directories, files = tool.v9_manifest()
    assert len(set(directories)) == len(directories)
    assert len(set(files)) == len(files)
    assert sum(path.suffix == ".json" for path in files) == 12
    assert sum(path.suffix == ".sqlite3" for path in files) == 24
    assert all(path.is_relative_to(tool.APPROVED_ROOT) for path in (*directories, *files))
    assert tool.V9_BATCHES == ("profile-01", "plain-01")
    assert len(tool.CASE_LABELS) == 6


def test_v9_client_bootstrap_only_changes_temp_initialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    tool = module()
    captured: list[Any] = []

    async def create(*args: Any, **kwargs: Any) -> int:
        captured.append((args, kwargs))
        return 42

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)

    async def scenario() -> None:
        with tool.fixed_client_temp():
            result: Any = await asyncio.create_subprocess_exec(
                sys.executable,
                "-B",
                "-m",
                "scripts.f009_step5_steady_profile",
                "--client-url",
                "http://127.0.0.1:1234",
                env={"TEMP": "synthetic"},
            )
            assert result == 42
            with pytest.raises(ValueError):
                await asyncio.create_subprocess_exec("unapproved")

    asyncio.run(scenario())
    assert len(captured) == 1
    args, kwargs = captured[0]
    assert args[:3] == (sys.executable, "-B", "-c")
    assert "tempfile.tempdir=os.environ['TEMP']" in args[3]
    assert args[4:] == ("--client-url", "http://127.0.0.1:1234")
    assert kwargs == {"env": {"TEMP": "synthetic"}}


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


def test_missing_attribution_historical_roots_skip_without_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("F009_V7_CANCEL_ROOT", raising=False)
    monkeypatch.delenv("F009_V9_SEMANTIC_ROOT", raising=False)
    sentinel = "SYNTHETIC-ENV-VALUE-MUST-NOT-APPEAR"
    monkeypatch.setenv("F009_UNRELATED_SENTINEL", sentinel)
    for variable in ("F009_V7_CANCEL_ROOT", "F009_V9_SEMANTIC_ROOT"):
        with pytest.raises(pytest.skip.Exception) as captured:
            _historical_case_root(variable, "synthetic-case")
        assert sentinel not in str(captured.value)


@pytest.mark.parametrize(
    "case",
    [
        "abandoned",
        "recorder-fault",
        "transaction-rollback",
        "old-forget",
        "old-replace",
        "storage-fault",
        "orphan",
        "late",
        "shared-waiter",
        "close",
        "long-term",
    ],
)
def test_remaining_disk_semantics(
    case: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Run existing real-repository scenarios in separately registered fresh databases."""
    import test_dialogue_async_persistence as existing

    root = _historical_case_root("F009_V9_SEMANTIC_ROOT", case)
    if case == "abandoned":
        existing.test_async_durable_open_restart_abandoned_is_idempotent(root)
    elif case == "recorder-fault":
        existing.test_async_recorder_failure_does_not_change_business_result(
            root, monkeypatch, caplog
        )
    elif case == "transaction-rollback":
        existing.test_full_transaction_rollback_and_every_lease_path_check(root, monkeypatch)
    elif case in {"old-forget", "old-replace"}:
        management = "Forget: game_alias" if case == "old-forget" else "Remember: game_alias=NEW-V6"
        existing.test_old_generation_cannot_commit_after_memory_revision(root, management)
    elif case == "storage-fault":
        existing.test_storage_failure_rejects_without_business_writes(root, monkeypatch)
    elif case in {"orphan", "late"}:
        existing.test_orphan_and_late_provider_do_not_commit_history(root, case == "late")
    elif case == "shared-waiter":
        existing.test_cancelled_owner_does_not_cancel_shared_waiter(root)
    elif case == "close":
        existing.test_close_drains_request_and_rejects_new_request(root)
    elif case == "long-term":
        existing.test_long_term_write_restart_and_scope_ownership(root)
    for database in sorted(root.glob("*.sqlite3")):
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)
            assert connection.execute("PRAGMA synchronous").fetchone() == (2,)


def test_interval_union_never_adds_nested_inclusive_time() -> None:
    tool = module()
    assert tool.union_duration(((0, 100), (20, 80), (50, 120), (200, 210))) == 130
    assert tool.exclusive_duration((0, 100), ((20, 80), (40, 90))) == 30
    assert tool.exclusive_duration((0, 100), ((-20, 20), (80, 150))) == 60
    assert tool.union_duration(()) == 0


def test_diagnostic_probe_propagates_owner_and_records_failed_work_without_payload() -> None:
    tool = module()
    probe = tool.DiagnosticProbe()
    sentinel = "SYNTHETIC-NOT-IN-DIAGNOSTICS"
    with probe.owner(7, tool.Lane.CONTROL):
        action = probe.capture_context(lambda: probe.measure(tool.Operation.SQL, lambda: 42))
    with ThreadPoolExecutor(max_workers=1) as pool:
        assert pool.submit(action).result() == 42
    with probe.owner(8, tool.Lane.BUSINESS), pytest.raises(ValueError):
        probe.measure(tool.Operation.COMMIT, lambda: (_ for _ in ()).throw(ValueError(sentinel)))
    rows = probe.snapshot()
    assert [row["case_index"] for row in rows] == [7, 8]
    assert [row["lane"] for row in rows] == ["control", "business"]
    assert rows[-1]["failed"] is True
    assert sentinel not in json.dumps(rows)


def test_diagnostic_summary_preserves_slow_samples_and_fixed_quantiles() -> None:
    result = module().latency_summary([1.0] * 99 + [1000.0])
    assert result["count"] == 100 and result["max_ms"] == 1000.0
    assert result["p95_ms"] == result["p99_ms"] == 1.0


def test_diagnostic_actual_executor_keeps_lane_and_phase_order() -> None:
    from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor

    tool = module()
    probe = tool.DiagnosticProbe()

    async def scenario() -> None:
        executor = AsyncSqliteExecutor()
        with probe.instrument(), probe.owner(9, tool.Lane.EVENT_LOOP):
            assert await executor.run("business", lambda: 42) == 42
            await executor.aclose()

    asyncio.run(scenario())
    rows = probe.snapshot()
    assert {row["case_index"] for row in rows} == {9}
    assert {row["lane"] for row in rows} == {"business"}
    assert {row["operation"] for row in rows} == {
        "slot",
        "queue",
        "repository",
        "resume",
        "storage",
    }
    assert tool.union_duration(tuple((row["start_ns"], row["end_ns"]) for row in rows)) > 0


@pytest.mark.parametrize("interval", [(3, 2), (True, 2), (0, 2.5), (0, float("nan"))])
def test_invalid_intervals_fail_safely(interval: Any) -> None:
    with pytest.raises(ValueError, match="Attribution interval is invalid"):
        module().union_duration((interval,))


def test_capture_keeps_case_ownership_across_worker_threads() -> None:
    tool = module()
    collector = tool.SpanCollector()
    jobs = []
    for case in range(128):
        with collector.case(case):
            jobs.append(collector.capture(tool.Lane.CONTROL, tool.Operation.REPOSITORY, lambda: 7))
    with ThreadPoolExecutor(max_workers=4) as workers:
        assert list(workers.map(lambda job: job(), jobs)) == [7] * 128
    rows = collector.snapshot()
    assert len(rows) == 128
    assert {row["case_index"] for row in rows} == set(range(128))
    assert len({row["operation_index"] for row in rows}) == 128
    assert all(row["end_ns"] >= row["start_ns"] for row in rows)


def test_capture_requires_explicit_case_and_does_not_emit_exception_payload() -> None:
    tool = module()
    collector = tool.SpanCollector()
    with pytest.raises(ValueError, match="Attribution case is unavailable"):
        collector.capture(tool.Lane.CONTROL, tool.Operation.SQL, lambda: None)
    sentinel = "SYNTHETIC-V7-PRIVATE-PAYLOAD"

    def failed() -> None:
        raise RuntimeError(sentinel)

    with collector.case(1):
        captured = collector.capture(tool.Lane.OBSERVABILITY, tool.Operation.COMMIT, failed)
    with pytest.raises(RuntimeError):
        captured()
    assert sentinel not in json.dumps(collector.snapshot())
    assert collector.snapshot()[0]["failed"] is True


@pytest.mark.parametrize("field", ["lane", "operation", "case_index"])
def test_span_dto_rejects_untrusted_identity_or_label(field: str) -> None:
    tool = module()
    values = {
        "case_index": 0,
        "operation_index": 1,
        "lane": tool.Lane.CONTROL,
        "operation": tool.Operation.SQL,
        "start_ns": 2,
        "end_ns": 3,
        "failed": False,
    }
    values[field] = "SYNTHETIC-V7-RAW-SCOPE-OR-SECRET"
    with pytest.raises(ValueError) as error:
        tool.Span(**values)
    assert "SYNTHETIC-V7" not in str(error.value)


def test_resource_print_failure_prevents_all_creation() -> None:
    tool = module()
    created: list[Path] = []
    printed: list[Path] = []
    paths = (tool.APPROVED_ROOT / "unit-a", tool.APPROVED_ROOT / "unit-b")

    def fail_print(path: Path) -> None:
        printed.append(path)
        raise OSError("Synthetic output unavailable")

    with pytest.raises(OSError):
        tool.prepare_directories(paths, announce=fail_print, create=created.append)
    assert len(printed) == 1
    assert not created


def test_resource_list_is_fully_printed_before_any_creation() -> None:
    tool = module()
    events: list[tuple[str, Path]] = []
    paths = (tool.APPROVED_ROOT / "unit-a", tool.APPROVED_ROOT / "unit-b")
    tool.prepare_directories(
        paths,
        announce=lambda path: events.append(("print", path)),
        create=lambda path: events.append(("create", path)),
    )
    assert events == [(action, path) for action in ("print", "create") for path in paths]


@pytest.mark.parametrize("path_kind", ["parent", "traversal", "duplicate", "existing", "relative"])
def test_resource_boundary_rejects_before_print_or_creation(path_kind: str) -> None:
    tool = module()
    paths = {
        "parent": (tool.APPROVED_ROOT.parent,),
        "traversal": (tool.APPROVED_ROOT / ".." / "other",),
        "duplicate": (tool.APPROVED_ROOT / "same", tool.APPROVED_ROOT / "same"),
        "existing": (tool.APPROVED_ROOT,),
        "relative": (Path("relative"),),
    }[path_kind]
    events: list[Path] = []
    with pytest.raises(ValueError, match="Attribution resource is invalid"):
        tool.prepare_directories(paths, announce=events.append, create=events.append)
    assert events == []


@pytest.mark.parametrize("representation", ["path", "string", "readonly_uri"])
def test_sqlite_audit_accepts_only_registered_targets(representation: str) -> None:
    tool = module()
    database = tool.APPROVED_ROOT / "unit-a" / "observability.sqlite3"
    target = {
        "path": database,
        "string": str(database),
        "readonly_uri": database.as_uri() + "?mode=ro",
    }[representation]
    assert tool.sqlite_target_registered(target, (database,))


@pytest.mark.parametrize("variant", ["write_uri", "extra_query", "other", "relative", "object"])
def test_sqlite_audit_rejects_unregistered_or_changed_uri(variant: str) -> None:
    tool = module()
    database = tool.APPROVED_ROOT / "unit-a" / "observability.sqlite3"
    target = {
        "write_uri": database.as_uri() + "?mode=rwc",
        "extra_query": database.as_uri() + "?mode=ro&immutable=1",
        "other": database.with_name("other.sqlite3").as_uri() + "?mode=ro",
        "relative": "observability.sqlite3",
        "object": object(),
    }[variant]
    assert not tool.sqlite_target_registered(target, (database,))


def test_disk_positive_long_term_write_replay_and_restart() -> None:
    import test_dialogue_async_persistence as existing

    root = _historical_case_root("F009_V7_CANCEL_ROOT", "positive-long-term-restart")
    existing.test_long_term_write_restart_and_scope_ownership(root)
    assert database_check(root)["long_term_memories"] == 1


def database_check(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    tables = {
        "business": ("relationship_events", "long_term_memories"),
        "control": ("budget_reservations", "budget_settlements"),
        "observability": ("trace_stage_events", "execution_links"),
    }
    for name, names in tables.items():
        with sqlite3.connect(root / f"{name}.sqlite3") as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)
            assert connection.execute("PRAGMA synchronous").fetchone() == (2,)
            for table in names:
                counts[table] = int(
                    connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                )
    return counts


@pytest.mark.parametrize("known", [True, False], ids=["known", "missing"])
@pytest.mark.parametrize("queued", [True, False], ids=["queued", "running"])
@pytest.mark.parametrize("cancel_count", [1, 2], ids=["once", "twice"])
def test_disk_persona_cancel(
    known: bool, queued: bool, cancel_count: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    import test_dialogue_async_persistence as existing
    from cyber_town.application.observability import TraceStage
    from cyber_town.infrastructure.observability.sqlite_observability import (
        ObservabilityQuery,
        SqliteObservabilityRepository,
    )

    identity = "known" if known else "missing"
    timing = "queued" if queued else "running"
    case = f"persona-{identity}-{timing}-{cancel_count}"
    root = _historical_case_root("F009_V7_CANCEL_ROOT", case)

    async def scenario() -> None:
        service, provider, recorder, control = existing.build(root)
        if not known:
            service._personas = {}
        executor = service.storage_executor
        assert executor is not None
        entered, release = threading.Event(), threading.Event()
        busy, busy_release = threading.Event(), threading.Event()
        submitted = asyncio.Event()
        original_progress, original_run = recorder.record_progress, executor.run
        finish_count = 0
        original_finish = recorder.finish_trace

        def finish(*args: Any) -> None:
            nonlocal finish_count
            original_finish(*args)
            finish_count += 1

        def progress(trace: Any, stage: Any) -> None:
            target = TraceStage.REQUEST_VALIDATION if queued else TraceStage.PERSONA_RESOLUTION
            if stage.stage is target:
                entered.set()
                assert release.wait(10)
            original_progress(trace, stage)

        def busy_operation() -> None:
            busy.set()
            assert busy_release.wait(10)

        async def run(lane: Any, operation: Any, **kwargs: Any) -> Any:
            if (
                isinstance(operation, partial)
                and operation.func == recorder.record_progress
                and operation.args[1].stage is TraceStage.PERSONA_RESOLUTION
            ):
                submitted.set()
            return await original_run(lane, operation, **kwargs)

        monkeypatch.setattr(recorder, "record_progress", progress)
        monkeypatch.setattr(recorder, "finish_trace", finish)
        monkeypatch.setattr(executor, "run", run)
        request = existing.command()
        task = asyncio.create_task(service.execute(request, trace_id=uuid4()))
        blocker = None
        try:
            await existing.thread_started(entered)
            if queued:
                blocker = asyncio.create_task(executor.run("observability", busy_operation))
                await asyncio.sleep(0)
                release.set()
                await existing.thread_started(busy)
                await asyncio.wait_for(submitted.wait(), 3)
            for _ in range(cancel_count):
                task.cancel()
                await asyncio.sleep(0)
            release.set()
            busy_release.set()
            if blocker is not None:
                await blocker
            with pytest.raises(asyncio.CancelledError):
                await task
            await service.aclose()
            traces = recorder.query_traces(ObservabilityQuery(limit=10))
            assert len(traces) == 1
            trace = traces[0]
            assert trace["record_status"] == "complete"
            assert trace["terminal_outcome"] == "cancelled"
            assert trace["provider_dispatch_count"] == provider.call_count == 0
            assert trace["cost_micro_usd"] == 0
            assert finish_count == 1
            counts = database_check(root)
            assert counts == {
                "relationship_events": 0,
                "long_term_memories": 0,
                "budget_reservations": 0,
                "budget_settlements": 0,
                "trace_stage_events": 14,
                "execution_links": 0,
            }
            for sentinel in (
                request.player_id,
                request.npc_id,
                str(request.conversation_id),
                request.message,
                existing.KEY.decode(),
            ):
                assert sentinel not in json.dumps(traces)
            recorder.close()
            restarted = SqliteObservabilityRepository(
                database_path=root / "observability.sqlite3", allowed_root=root
            )
            try:
                restarted.initialize()
                assert restarted.recover_open_traces(now_utc=datetime.now(UTC)) == 0
                assert restarted.recover_open_traces(now_utc=datetime.now(UTC)) == 0
                assert restarted.query_traces(ObservabilityQuery(limit=10)) == traces
            finally:
                restarted.close()
        finally:
            release.set()
            busy_release.set()
            if blocker is not None:
                await blocker
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_disk_response_mapping_queued_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    import test_dialogue_async_persistence as existing
    from cyber_town.application.observability import TraceStage
    from cyber_town.infrastructure.observability.sqlite_observability import ObservabilityQuery

    root = _historical_case_root("F009_V7_CANCEL_ROOT", "response-mapping-queued-1")

    async def scenario() -> None:
        service, provider, recorder, control = existing.build(root)
        executor = service.storage_executor
        assert executor is not None
        committed, release = threading.Event(), threading.Event()
        busy, busy_release = threading.Event(), threading.Event()
        submitted = asyncio.Event()
        original_progress, original_run = recorder.record_progress, executor.run
        finish_count = 0
        original_finish = recorder.finish_trace

        def finish(*args: Any) -> None:
            nonlocal finish_count
            original_finish(*args)
            finish_count += 1

        def progress(trace: Any, stage: Any) -> None:
            original_progress(trace, stage)
            if stage.stage is TraceStage.STATE_COMMIT:
                committed.set()
                assert release.wait(10)

        def busy_operation() -> None:
            busy.set()
            assert busy_release.wait(10)

        async def run(lane: Any, operation: Any, **kwargs: Any) -> Any:
            if (
                isinstance(operation, partial)
                and operation.func == recorder.record_progress
                and operation.args[1].stage is TraceStage.RESPONSE_MAPPING
            ):
                submitted.set()
            return await original_run(lane, operation, **kwargs)

        monkeypatch.setattr(recorder, "record_progress", progress)
        monkeypatch.setattr(recorder, "finish_trace", finish)
        monkeypatch.setattr(executor, "run", run)
        task = asyncio.create_task(service.execute(existing.command(), trace_id=uuid4()))
        blocker = None
        try:
            await existing.thread_started(committed)
            blocker = asyncio.create_task(executor.run("observability", busy_operation))
            await asyncio.sleep(0)
            release.set()
            await existing.thread_started(busy)
            await asyncio.wait_for(submitted.wait(), 3)
            task.cancel()
            await asyncio.sleep(0)
            busy_release.set()
            await blocker
            with pytest.raises(asyncio.CancelledError):
                await task
            await service.aclose()
            traces = recorder.query_traces(ObservabilityQuery(limit=10))
            counts = database_check(root)
            metadata = {
                "case_id": "response_mapping_queued_cancel",
                "trace_count": len(traces),
                "record_status": traces[0]["record_status"],
                "terminal_outcome": traces[0]["terminal_outcome"],
                "provider_calls": provider.call_count,
                "finish_calls": finish_count,
                **counts,
            }
            print(json.dumps(metadata, sort_keys=True), flush=True)
            assert provider.call_count == 1
            assert counts["relationship_events"] == 1
            assert counts["budget_settlements"] == 1
            assert traces[0]["record_status"] == "complete", "V7_CANCEL_RESPONSE_MAPPING_OPEN"
            assert finish_count == 1
            assert counts["trace_stage_events"] == 14
        finally:
            release.set()
            busy_release.set()
            if blocker is not None:
                await blocker
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["fresh", "replay", "waiter", "owner_with_waiter"])
@pytest.mark.parametrize("timing", ["queued", "running", "committed"])
@pytest.mark.parametrize("cancel_count", [1, 2])
def test_disk_response_mapping_cancel_ownership(
    mode: str, timing: str, cancel_count: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    import test_dialogue_async_persistence as existing
    from cyber_town.application.observability import TraceStage
    from cyber_town.infrastructure.observability.sqlite_observability import ObservabilityQuery

    root = _historical_case_root("F009_V7_CANCEL_ROOT", f"mapping-{mode}-{timing}-{cancel_count}")

    async def scenario() -> None:
        service, provider, recorder, control = existing.build(root)
        executor = service.storage_executor
        assert executor is not None
        npc = {"queued": "neon_guide", "running": "signal_archivist", "committed": "night_courier"}
        request = existing.command(npc=npc[timing])
        target_id, peer_id = uuid4(), uuid4()
        entered, release = threading.Event(), threading.Event()
        provider_entered, provider_release = asyncio.Event(), asyncio.Event()
        queued_submitted = asyncio.Event()
        finishes: dict[str, int] = {}
        original_progress, original_run = recorder.record_progress, executor.run
        original_finish, original_complete = recorder.finish_trace, provider.complete
        busy_task = None
        peer = None
        closing = None
        target = None

        def progress(trace: Any, stage: Any) -> None:
            selected = trace.trace_id == target_id and stage.stage is TraceStage.RESPONSE_MAPPING
            if selected and timing == "running":
                entered.set()
                assert release.wait(10)
            original_progress(trace, stage)
            if selected and timing == "committed":
                entered.set()
                assert release.wait(10)

        def finish(trace: Any, stages: Any) -> None:
            original_finish(trace, stages)
            key = str(trace.trace_id)
            finishes[key] = finishes.get(key, 0) + 1

        def occupy_writer() -> None:
            entered.set()
            assert release.wait(10)

        async def run(lane: Any, operation: Any, **kwargs: Any) -> Any:
            nonlocal busy_task
            if (
                timing == "queued"
                and isinstance(operation, partial)
                and operation.func == recorder.record_progress
                and operation.args[0].trace_id == target_id
                and operation.args[1].stage is TraceStage.RESPONSE_MAPPING
            ):
                busy_task = asyncio.create_task(original_run("observability", occupy_writer))
                await existing.thread_started(entered)
                queued_submitted.set()
            return await original_run(lane, operation, **kwargs)

        async def complete(provider_request: Any) -> Any:
            provider_entered.set()
            await provider_release.wait()
            return await original_complete(provider_request)

        monkeypatch.setattr(recorder, "record_progress", progress)
        monkeypatch.setattr(recorder, "finish_trace", finish)
        monkeypatch.setattr(executor, "run", run)
        try:
            if mode == "replay":
                await service.execute(request, trace_id=peer_id)
            if mode in {"waiter", "owner_with_waiter"}:
                monkeypatch.setattr(provider, "complete", complete)
                owner_id = peer_id if mode == "waiter" else target_id
                owner = asyncio.create_task(service.execute(request, trace_id=owner_id))
                await asyncio.wait_for(provider_entered.wait(), 3)
                other_id = target_id if mode == "waiter" else peer_id
                other = asyncio.create_task(service.execute(request, trace_id=other_id))
                target, peer = (other, owner) if mode == "waiter" else (owner, other)
                async with asyncio.timeout(3):
                    while service._idempotency[request.request_id].waiters != 2:
                        await asyncio.sleep(0)
                provider_release.set()
            else:
                target = asyncio.create_task(service.execute(request, trace_id=target_id))
            await existing.thread_started(entered)
            if timing == "queued":
                await asyncio.wait_for(queued_submitted.wait(), 3)
            for _ in range(cancel_count):
                target.cancel()
                await asyncio.sleep(0)
            shutdown_pending = mode == "fresh" and timing == "committed" and cancel_count == 2
            if shutdown_pending:
                closing = asyncio.create_task(service.aclose())
                await asyncio.sleep(0)
                assert not closing.done()
            release.set()
            if busy_task is not None:
                await busy_task
            with pytest.raises(asyncio.CancelledError):
                await target
            if peer is not None:
                assert (await peer).status.value == "completed"
            cached = service._idempotency[request.request_id].result
            assert cached is not None
            if not shutdown_pending:
                replay = await service.execute(request, trace_id=uuid4())
                assert replay.reply == cached.reply and replay.status.value == "completed"
            if closing is not None:
                await closing
            await service.aclose()
            await service.aclose()
            traces = recorder.query_traces(ObservabilityQuery(limit=100))
            selected = next(item for item in traces if item["trace_id"] == str(target_id))
            assert selected["record_status"] == "complete"
            assert selected["terminal_outcome"] == "cancelled"
            expected_kind = {"replay": "cache_replay", "waiter": "concurrent_waiter"}.get(
                mode, "initial"
            )
            assert selected["attempt_kind"] == expected_kind
            assert all(row["record_status"] == "complete" for row in traces)
            assert all(row["cost_micro_usd"] == 0 for row in traces)
            assert all(finishes[str(row["trace_id"])] == 1 for row in traces)
            assert (
                provider.call_count
                == sum(cast(int, row["provider_dispatch_count"]) for row in traces)
                == 1
            )
            dispatch_owner = next(row for row in traces if row["provider_dispatch_count"] == 1)
            if mode == "replay":
                assert selected["execution_id"] is None
                assert selected["provider_dispatch_count"] == 0
                with sqlite3.connect(root / "observability.sqlite3") as connection:
                    assert connection.execute(
                        "SELECT from_cache,idempotency_outcome FROM trace_runs WHERE trace_id=?",
                        (str(target_id),),
                    ).fetchone() == (1, "cache_replay")
            else:
                assert selected["execution_id"] == dispatch_owner["execution_id"]
            assert selected["request_id"] == str(request.request_id)
            assert all(
                selected[field] is not None
                for field in ("player_scope_tag", "npc_scope_tag", "conversation_scope_tag")
            )
            assert all(
                row["terminal_outcome"] == "replayed"
                for row in traces
                if row["attempt_kind"] == "cache_replay" and row != selected
            )
            counts = database_check(root)
            assert counts["relationship_events"] == counts["budget_reservations"] == 1
            assert counts["budget_settlements"] == 1
            assert counts["trace_stage_events"] == 14 * len(traces)
            with sqlite3.connect(root / "control.sqlite3") as connection:
                rows = connection.execute(
                    "SELECT r.execution_id, r.attempt_number, r.status, s.actual_cost_micro_usd "
                    "FROM budget_reservations r JOIN budget_settlements s "
                    "ON r.execution_id=s.execution_id AND r.attempt_number=s.attempt_number"
                ).fetchall()
                assert rows == [(dispatch_owner["execution_id"], 1, "settled", 0)]
                assert connection.execute(
                    "SELECT COUNT(*) FROM budget_execution_owners"
                ).fetchone() == (1,)
            with sqlite3.connect(root / "business.sqlite3") as connection:
                assert connection.execute(
                    "SELECT player_id,npc_id,request_id FROM relationship_events"
                ).fetchall() == [(request.player_id, request.npc_id, str(request.request_id))]
            for sentinel in (
                request.player_id,
                request.npc_id,
                str(request.conversation_id),
                request.message,
                existing.KEY.decode(),
            ):
                assert sentinel not in json.dumps(traces)
            recorder.close()
            control.close()
            restored, restored_provider, restored_recorder, restored_control = existing.build(root)
            try:
                assert restored_recorder.recover_open_traces(now_utc=datetime.now(UTC)) == 0
                assert restored_recorder.recover_open_traces(now_utc=datetime.now(UTC)) == 0
                assert restored_recorder.query_traces(ObservabilityQuery(limit=100)) == traces
                assert database_check(root) == counts
                assert restored_provider.call_count == 0
            finally:
                await restored.aclose()
                restored_recorder.close()
                restored_control.close()
        finally:
            release.set()
            provider_release.set()
            pending = [task for task in (target, peer, busy_task, closing) if task is not None]
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())


def test_v10_tool_equivalence_rejects_false_or_partial_match() -> None:
    from scripts.f009_step5_attribution import require_budget_equivalence

    reference = {scope: (1, 2, 3) for scope in ("player_npc", "player", "npc", "global")}
    require_budget_equivalence(reference, dict(reference))
    for index in range(12):
        altered = dict(reference)
        scope = tuple(reference)[index // 3]
        values = list(altered[scope])
        values[index % 3] += 1
        altered[scope] = (values[0], values[1], values[2])
        with pytest.raises(ValueError, match="Synthetic budget equivalence failure"):
            require_budget_equivalence(reference, altered)
    with pytest.raises(ValueError):
        require_budget_equivalence(reference, {"global": (1, 2, 3)})


@pytest.mark.parametrize("opcode", ["OpenEphemeral", "SorterOpen", "OpenAutoindex"])
def test_v10_tool_rejects_temporary_plan(opcode: str) -> None:
    from scripts.f009_step5_attribution import require_streaming_plan

    with pytest.raises(ValueError, match="Synthetic budget plan"):
        require_streaming_plan(("InitCoroutine", opcode, "Yield"))
    require_streaming_plan(("InitCoroutine", "Yield", "EndCoroutine", "AggStep"))


def test_v10_tool_manifest_precedes_creations() -> None:
    from scripts.f009_step5_attribution import V10_ROOT, prepare_v10_batch, v10_manifest

    directories, files = v10_manifest()
    assert len(directories) == len(set(directories)) == 122
    assert len(files) == len(set(files)) == 326
    assert all(path.is_relative_to(V10_ROOT) for path in (*directories, *files))
    assert all("observability.sqlite3" not in str(path) for path in files)
    assert all("business.sqlite3" not in str(path) for path in files)
    # Missing registration must fail before any path inspection/creation callback.
    with pytest.raises(ValueError, match="registration"):
        prepare_v10_batch("profile-01", registered=())


def test_v10_tool_plain_has_no_probe_and_fixed_workload() -> None:
    from scripts.f009_step5_attribution import v10_case_spec

    assert v10_case_spec("plain-01", "candidate-on") == (True, True, False, 1000)
    assert v10_case_spec("profile-01", "current-off") == (False, False, True, 1000)
    for batch, label in (("plain-02", "candidate-on"), ("plain-01", "http-on")):
        with pytest.raises(ValueError):
            v10_case_spec(batch, label)


def test_v10_tool_error_does_not_echo_input(caplog: pytest.LogCaptureFixture) -> None:
    from scripts.f009_step5_attribution import require_budget_equivalence

    sentinel = "synthetic-private-payload-key-message"
    with pytest.raises(ValueError) as caught:
        require_budget_equivalence({sentinel: (1, 2, 3)}, {})
    assert sentinel not in str(caught.value) + repr(caught.value) + caplog.text


def test_v20_manifest_is_exact_and_metadata_only() -> None:
    from scripts.f009_step5_attribution import V20_ROOT, v20_manifest

    directories, files = v20_manifest()
    assert directories == (
        V20_ROOT,
        V20_ROOT / "tmp",
        V20_ROOT / "pytest-red-01",
        V20_ROOT / "pytest-green-01",
        V20_ROOT / "attribution-01",
        V20_ROOT / "attribution-02",
    )
    assert files == (
        V20_ROOT / "attribution-01" / "baseline.json",
        V20_ROOT / "attribution-01" / "recorded.json",
        V20_ROOT / "attribution-02" / "baseline.json",
        V20_ROOT / "attribution-02" / "recorded.json",
        V20_ROOT / "summary-02.json",
    )
    assert all(path.is_relative_to(V20_ROOT) for path in (*directories, *files))
    assert all(path.suffix != ".sqlite3" for path in files)


def test_v20_cost_partition_uses_interval_union_and_rejects_missing_hotspots() -> None:
    from scripts.f009_step5_attribution import partition_v20_fixed_costs

    rows = (
        {
            "case_index": 1,
            "operation_index": 1,
            "operation": "budget_reservation",
            "start_ns": 0,
            "end_ns": 1_000_000,
            "parent_index": 0,
        },
        {
            "case_index": 1,
            "operation_index": 2,
            "operation": "scope_tag",
            "start_ns": 100_000,
            "end_ns": 300_000,
            "parent_index": 1,
        },
        {
            "case_index": 1,
            "operation_index": 3,
            "operation": "budget_dto",
            "start_ns": 150_000,
            "end_ns": 250_000,
            "parent_index": 2,
        },
        {
            "case_index": 1,
            "operation_index": 4,
            "operation": "begin",
            "start_ns": 350_000,
            "end_ns": 400_000,
            "parent_index": 1,
        },
        {
            "case_index": 1,
            "operation_index": 5,
            "operation": "sql",
            "start_ns": 450_000,
            "end_ns": 700_000,
            "parent_index": 1,
        },
        {
            "case_index": 1,
            "operation_index": 6,
            "operation": "write_commit",
            "start_ns": 750_000,
            "end_ns": 850_000,
            "parent_index": 1,
        },
    )
    result = partition_v20_fixed_costs(rows, required_hotspots=("budget_reservation",))
    budget = result[1]["budget_reservation"]
    assert budget == {
        "total_ms": 1.0,
        "transaction_framework_ms": 0.15,
        "sql_ms": 0.25,
        "hmac_dto_ms": 0.2,
        "python_orchestration_ms": 0.4,
    }
    with pytest.raises(ValueError, match="hotspot ownership"):
        partition_v20_fixed_costs(rows, required_hotspots=("ingress_admission",))


def test_v20_cost_partition_rejects_cross_request_parent_and_sensitive_output() -> None:
    from scripts.f009_step5_attribution import partition_v20_fixed_costs

    rows = (
        {
            "case_index": 1,
            "operation_index": 1,
            "operation": "ingress_admission",
            "start_ns": 0,
            "end_ns": 10,
            "parent_index": 0,
        },
        {
            "case_index": 2,
            "operation_index": 2,
            "operation": "sql",
            "start_ns": 1,
            "end_ns": 2,
            "parent_index": 1,
        },
    )
    with pytest.raises(ValueError, match="parent ownership") as caught:
        partition_v20_fixed_costs(rows, required_hotspots=("ingress_admission",))
    assert "synthetic-private-player" not in str(caught.value)


def test_v20_five_run_aggregation_uses_each_run_value() -> None:
    from scripts.f009_step5_attribution import V20_HOTSPOTS, _aggregate_v20_runs

    runs: list[dict[str, object]] = []
    for run_index in range(5):
        runs.append(
            {
                hotspot: {
                    metric: {
                        "mean_ms": run_index + 1.0,
                        "p50_ms": run_index + 2.0,
                        "p95_ms": run_index + 3.0,
                        "p99_ms": run_index + 4.0,
                        "max_ms": run_index + 5.0,
                    }
                    for metric in (
                        "total_ms",
                        "transaction_framework_ms",
                        "sql_ms",
                        "hmac_dto_ms",
                        "python_orchestration_ms",
                    )
                }
                for hotspot in V20_HOTSPOTS
            }
        )
    aggregate = cast(dict[str, dict[str, dict[str, float]]], _aggregate_v20_runs(runs))
    assert aggregate["budget_reservation"]["sql_ms"] == {
        "mean_ms": 3.0,
        "p50_ms": 4.0,
        "p95_ms": 5.0,
        "p99_ms": 6.0,
        "max_ms": 7.0,
    }
