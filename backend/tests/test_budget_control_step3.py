from __future__ import annotations

import asyncio
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from time import perf_counter_ns
from typing import Never
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from cyber_town.api.app import create_app
from cyber_town.application.budget import (
    ATTEMPT_WINDOW_SPECS,
    BUDGET_POLICY_VERSION,
    COST_WINDOW_SPECS,
    SYNTHETIC_PRICING_POLICY,
    BudgetEventKind,
    BudgetLimitClass,
    BudgetRejectedError,
    BudgetReservation,
    BudgetScopeTags,
    InMemorySafetyCostRecorder,
    PricingPolicy,
    SafetyCostRecorder,
    calculate_cost_micro_usd,
)
from cyber_town.application.control import ControlUnavailableError, SafetyControl
from cyber_town.application.dialogue import (
    DialogueExecutionConfig,
    DialogueFailureKind,
    DialogueService,
    DialogueUseCaseError,
)
from cyber_town.application.memory import ConversationScope, ShortTermSessionStore
from cyber_town.application.observability import (
    InMemoryObservabilityRecorder,
    ObservabilityRecorder,
    ProviderKind,
)
from cyber_town.application.provider import (
    ProviderCompletion,
    ProviderInvalidResponseError,
    ProviderProtocol,
    ProviderRequest,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderUsage,
)
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import (
    SafetyControlStorageError,
    SqliteSafetyControlRepository,
)
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.observability.storage_codec import decode_value, encode_value

KEY = b"synthetic-f009-budget-key-v1"
BASE_NS = 1_800_000_000_000_000_000
ZERO_COST_POLICY = PricingPolicy.zero_cost(
    provider_kind=ProviderKind.FAKE,
    model="fake-model",
)

# Historical v4 scan retained only as an equivalence oracle for V7/V10 tests.
# Product admission must use the v5 projection instead.
_LEGACY_BUDGET_WINDOW_SQL = (
    "SELECT "
    + ", ".join(
        "COALESCE(" + expression + (f" FILTER (WHERE {condition})" if condition else "") + ", 0)"
        for condition in (
            "o.player_npc_scope_tag = :player_npc",
            "o.player_scope_tag = :player",
            "o.npc_scope_tag = :npc",
            "",
        )
        for expression in (
            "SUM(r.reserved_at_ns > :hour)",
            "COUNT(*)",
            "SUM(CASE WHEN r.status = 'settled' THEN s.actual_cost_micro_usd "
            "ELSE r.reserved_micro_usd END)",
        )
    )
    + " FROM budget_reservations r JOIN budget_execution_owners o USING (execution_id) "
    "LEFT JOIN budget_settlements s USING (execution_id, attempt_number) "
    "WHERE r.reserved_at_ns > :day AND r.status <> 'released'"
)
_BUDGET_WINDOW_SCOPES_FOR_TEST = ("player_npc", "player", "npc", "global")


def test_window_aggregate_reduces_vm_steps_without_changing_totals() -> None:
    # Frozen V7 query is the semantic/cost comparison, never a product fallback.
    reference = (
        "WITH windows AS (SELECT o.player_npc_scope_tag, o.player_scope_tag, o.npc_scope_tag, "
        "CASE WHEN r.status <> 'released' AND r.reserved_at_ns > :hour "
        "THEN 1 ELSE 0 END AS hourly, "
        "CASE WHEN r.status <> 'released' THEN 1 ELSE 0 END AS daily, "
        "CASE WHEN r.status = 'settled' THEN s.actual_cost_micro_usd "
        "WHEN r.status IN ('reserved', 'dispatched') THEN r.reserved_micro_usd ELSE 0 END AS cost "
        "FROM budget_reservations r JOIN budget_execution_owners o USING (execution_id) "
        "LEFT JOIN budget_settlements s USING (execution_id, attempt_number) "
        "WHERE r.reserved_at_ns > :day) SELECT "
        + ", ".join(
            f"COALESCE(SUM(CASE WHEN {condition} THEN {metric} ELSE 0 END), 0)"
            for condition in (
                "player_npc_scope_tag = :player_npc",
                "player_scope_tag = :player",
                "npc_scope_tag = :npc",
                "1 = 1",
            )
            for metric in ("hourly", "daily", "cost")
        )
        + " FROM windows"
    )
    params = {
        "player_npc": "pair0",
        "player": "player",
        "npc": "npc0",
        "hour": BASE_NS - 3600_000_000_000,
        "day": BASE_NS - 86400_000_000_000,
    }
    with closing(sqlite3.connect(":memory:")) as c:
        c.executescript(
            "CREATE TABLE budget_execution_owners(execution_id TEXT PRIMARY KEY, "
            "player_npc_scope_tag TEXT, player_scope_tag TEXT, npc_scope_tag TEXT);"
            "CREATE TABLE budget_reservations(execution_id TEXT, attempt_number INTEGER, "
            "status TEXT, reserved_at_ns INTEGER, reserved_micro_usd INTEGER, "
            "PRIMARY KEY(execution_id,attempt_number));"
            "CREATE TABLE budget_settlements(execution_id TEXT, attempt_number INTEGER, "
            "actual_cost_micro_usd INTEGER, PRIMARY KEY(execution_id,attempt_number));"
        )
        for index in range(1000):
            identity = str(index)
            c.execute(
                "INSERT INTO budget_execution_owners VALUES (?,?,?,?)",
                (identity, f"pair{index % 3}", "player", f"npc{index % 3}"),
            )
            status = ("reserved", "dispatched", "settled", "released")[index % 4]
            c.execute(
                "INSERT INTO budget_reservations VALUES (?,1,?,?,2000)",
                (identity, status, BASE_NS - index * 60_000_000_000),
            )
            if status == "settled":
                c.execute("INSERT INTO budget_settlements VALUES (?,1,7)", (identity,))
        counts: list[int] = []
        rows: list[tuple[object, ...]] = []
        timings: list[int] = []
        for sql in (reference, _LEGACY_BUDGET_WINDOW_SQL):
            steps = 0

            def progress() -> int:
                nonlocal steps
                steps += 1
                return 0

            c.set_progress_handler(progress, 1)
            rows.append(c.execute(sql, params).fetchone())
            c.set_progress_handler(None, 0)
            counts.append(steps)
            start = perf_counter_ns()
            for _ in range(100):
                assert c.execute(sql, params).fetchone() == rows[0]
            timings.append((perf_counter_ns() - start) // 100)
        print({"vm_steps": counts, "late_1000_rows_mean_ns": timings})
        assert rows[0] == rows[1]
        # Ignore a few statement setup opcodes; require a per-row work reduction.
        assert counts[1] <= counts[0] - 1000, "budget query repeats V7 scope/status/window work"


def test_product_budget_projection_is_versioned_and_replaces_ledger_window_scan(
    tmp_path: Path,
) -> None:
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    repository.initialize()

    with closing(repository._connect()) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        migrations = connection.execute(
            "SELECT version,name FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert connection.execute("PRAGMA user_version").fetchone() == (9,)
        assert migrations[-1] == (9, "0009_provider_permit_scope_storage.sql")
        assert {
            "budget_window_projection_state",
            "budget_window_totals",
        } <= tables

    repository.close()


def test_product_budget_projection_lookup_is_bounded_by_requested_scopes_not_ledger_size(
    tmp_path: Path,
) -> None:
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    repository.initialize()
    requested = BudgetScopeTags(
        player_scope_tag=f"{1:064x}",
        npc_scope_tag=f"{2:064x}",
        player_npc_scope_tag=f"{3:064x}",
    )

    def insert_rows(connection: sqlite3.Connection, start: int, stop: int) -> None:
        for index in range(start, stop):
            identity = str(UUID(int=10_000 + index))
            player = f"{index + 1:064x}"
            npc = f"{(index % 3) + 1:064x}"
            pair = f"{20_000 + index:064x}"
            connection.execute(
                "INSERT INTO execution_admissions VALUES (?,?,?,?,?,?,?)",
                (
                    identity,
                    identity,
                    "f-009-safety-control-v1",
                    player,
                    pair,
                    f"{30_000 + index:064x}",
                    BASE_NS,
                ),
            )
            connection.execute(
                "INSERT INTO budget_execution_owners VALUES (?,?,?,?,?,?)",
                (identity, BUDGET_POLICY_VERSION, player, npc, pair, BASE_NS),
            )
            connection.execute(
                "INSERT INTO budget_reservations "
                "(execution_id,attempt_number,policy_version,pricing_version,provider_kind,"
                "provider_model,reserved_micro_usd,soft_warning,status,reserved_at_ns) "
                "VALUES (?,1,?,'synthetic-bounded-v1','fake','fake-model',0,0,'reserved',?)",
                (identity, BUDGET_POLICY_VERSION, BASE_NS - index * 1_000_000),
            )

    def lookup_steps(connection: sqlite3.Connection) -> tuple[int, int]:
        steps = 0

        def progress() -> int:
            nonlocal steps
            steps += 1
            return 0

        connection.set_progress_handler(progress, 1)
        try:
            totals = repository._all_window_totals(
                connection,
                scope_tags=requested,
                now_ns=BASE_NS,
            )
        finally:
            connection.set_progress_handler(None, 0)
        return steps, totals["global"][1]

    try:
        with closing(repository._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            insert_rows(connection, 0, 100)
            repository._rebuild_budget_projection(connection, now_ns=BASE_NS)
            connection.commit()
            small_steps, small_total = lookup_steps(connection)

            connection.execute("BEGIN IMMEDIATE")
            insert_rows(connection, 100, 1_000)
            repository._rebuild_budget_projection(connection, now_ns=BASE_NS)
            connection.commit()
            large_steps, large_total = lookup_steps(connection)

        assert small_total == 100
        assert large_total == 1_000
        print(
            {
                "ledger_rows": (100, 1_000),
                "projection_lookup_vm_steps": (small_steps, large_steps),
            }
        )
        assert large_steps <= small_steps + 40
    finally:
        repository.close()


class FakeClock:
    def __init__(self, now_ns: int = BASE_NS) -> None:
        self.now_ns = now_ns

    def __call__(self) -> int:
        return self.now_ns

    def advance(self, seconds: int) -> None:
        self.now_ns += seconds * 1_000_000_000


class BlockingProvider:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.call_count = 0

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        del request
        self.call_count += 1
        self.started.set()
        await self.release.wait()
        return completion()


class CancellingProvider:
    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        del request
        raise asyncio.CancelledError


class FailingCostRecorder:
    def record_safety_cost(self, record: object) -> None:
        del record
        raise RuntimeError("synthetic recorder failure")


def request(
    *,
    player_id: str = "synthetic_player",
    npc_id: str = "neon_guide",
    request_id: UUID | None = None,
    conversation_id: UUID | None = None,
) -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=request_id or uuid4(),
        player_id=player_id,
        npc_id=npc_id,
        conversation_id=conversation_id or uuid4(),
        message="Synthetic budget test.",
    )


def completion(
    *,
    prompt_tokens: int = 1_000,
    completion_tokens: int = 250,
) -> ProviderCompletion:
    return ProviderCompletion(
        content="Synthetic response.",
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="fake",
        model="fake-model",
        usage=ProviderUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        ),
    )


def make_control(
    tmp_path: Path,
    clock: FakeClock,
    *,
    pricing_policy: PricingPolicy = SYNTHETIC_PRICING_POLICY,
) -> tuple[SafetyControl, SqliteSafetyControlRepository]:
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    repository.initialize()
    control = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock,
        pricing_policy=pricing_policy,
    )
    return control, repository


def make_service(
    provider: ProviderProtocol,
    control: SafetyControl,
    *,
    sessions: ShortTermSessionStore | None = None,
    observability: ObservabilityRecorder | None = None,
    cost_recorder: SafetyCostRecorder | None = None,
) -> DialogueService:
    return DialogueService(
        personas=load_bundled_personas(),
        provider=provider,
        config=DialogueExecutionConfig(
            model="fake-model",
            temperature=0.6,
            max_tokens=256,
            timeout_seconds=1.0,
            max_concurrency=2,
            idempotency_ttl_seconds=600.0,
            idempotency_max_entries=256,
        ),
        safety_control=control,
        session_store=sessions,
        observability_recorder=observability,
        observability_scope_key=KEY if observability is not None else None,
        observability_provider_kind=ProviderKind.FAKE,
        safety_cost_recorder=cost_recorder,
    )


def admit_and_reserve(
    control: SafetyControl,
    item: DialogueRequestV1,
    execution_id: UUID,
    *,
    attempt_number: int = 1,
) -> BudgetReservation:
    control.admit_execution(request=item, execution_id=execution_id)
    return control.reserve_budget(
        request=item,
        execution_id=execution_id,
        attempt_number=attempt_number,
    )


@pytest.mark.anyio
async def test_execution_intent_admission_is_idempotent_and_clean_release_is_terminal(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    item = request()
    execution_id = uuid4()

    first = await control.admit_provider_dispatch(
        request=item,
        execution_id=execution_id,
        attempt_number=1,
    )
    replay = await control.admit_provider_dispatch(
        request=item,
        execution_id=execution_id,
        attempt_number=1,
    )

    assert replay.reservation == first.reservation
    assert repository.admission_count() == 1
    assert repository.budget_attempt_count() == 1
    assert repository.active_permit_count() == 1
    assert len(repository.execution_intent_snapshot()) == 1

    control.release_budget(first.reservation, reason="cancelled_before_dispatch")
    await control.release_provider_permit(first.permit, reason="cancelled")
    control.release_breaker_probe(execution_id=execution_id)

    intent = repository.execution_intent_snapshot()[0]
    assert intent["state"] == "released"
    assert intent["terminal_reason"] == "cancelled_before_dispatch"
    assert repository.budget_attempt_snapshot()[0]["status"] == "released"
    assert repository.budget_settlement_count() == 0
    assert repository.active_permit_count() == 0


@pytest.mark.anyio
async def test_execution_intent_restart_conservatively_settles_unknown_receipt_once(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    admission = await control.admit_provider_dispatch(
        request=request(),
        execution_id=uuid4(),
        attempt_number=1,
    )
    assert admission.reservation is not None
    assert repository.execution_intent_snapshot()[0]["state"] == "dispatch_intent"
    assert repository.budget_attempt_snapshot()[0]["status"] == "reserved"
    repository.close()

    _, rebuilt = make_control(tmp_path, clock)
    intent = rebuilt.execution_intent_snapshot()[0]
    attempt = rebuilt.budget_attempt_snapshot()[0]
    assert intent["state"] == "settled"
    assert intent["conservative"] == 1
    assert intent["terminal_reason"] == "abandoned_after_restart"
    assert attempt["status"] == "settled"
    assert attempt["conservative"] == 1
    assert rebuilt.budget_settlement_count() == 1
    assert rebuilt.active_permit_count() == 0

    rebuilt.close()
    _, repeated = make_control(tmp_path, clock)
    assert repeated.budget_settlement_count() == 1
    assert repeated.execution_intent_snapshot()[0]["revision"] == intent["revision"]


def test_budget_and_pricing_contract_is_fixed_and_uses_ceiling() -> None:
    assert BUDGET_POLICY_VERSION == "f-009-budget-policy-v1"
    assert SYNTHETIC_PRICING_POLICY.version == "f-009-synthetic-pricing-v1"
    assert (
        calculate_cost_micro_usd(
            policy=PricingPolicy(
                version="synthetic-rounding-v1",
                provider_kind=ProviderKind.DEEPSEEK,
                model="synthetic-model",
                input_micro_usd_per_million_tokens=1,
                output_micro_usd_per_million_tokens=1,
                max_reservation_micro_usd=2_000,
            ),
            usage=ProviderUsage(prompt_tokens=1, completion_tokens=0),
        )
        == 1
    )
    assert (
        calculate_cost_micro_usd(
            policy=SYNTHETIC_PRICING_POLICY,
            usage=ProviderUsage(prompt_tokens=0, completion_tokens=0),
        )
        == 0
    )
    assert tuple(
        (spec.limit_class, spec.window_seconds, spec.hard_limit, spec.warning_threshold)
        for spec in ATTEMPT_WINDOW_SPECS
    ) == (
        (BudgetLimitClass.PLAYER_NPC_ATTEMPTS_1H, 3_600, 15, 12),
        (BudgetLimitClass.PLAYER_NPC_ATTEMPTS_24H, 86_400, 50, 40),
        (BudgetLimitClass.PLAYER_ATTEMPTS_1H, 3_600, 30, 24),
        (BudgetLimitClass.PLAYER_ATTEMPTS_24H, 86_400, 100, 80),
        (BudgetLimitClass.NPC_ATTEMPTS_1H, 3_600, 120, 96),
        (BudgetLimitClass.NPC_ATTEMPTS_24H, 86_400, 500, 400),
        (BudgetLimitClass.GLOBAL_ATTEMPTS_1H, 3_600, 300, 240),
        (BudgetLimitClass.GLOBAL_ATTEMPTS_24H, 86_400, 1_000, 800),
    )
    assert tuple(
        (spec.limit_class, spec.hard_limit, spec.warning_threshold) for spec in COST_WINDOW_SPECS
    ) == (
        (BudgetLimitClass.PLAYER_NPC_COST_24H, 25_000, 20_000),
        (BudgetLimitClass.PLAYER_COST_24H, 50_000, 40_000),
        (BudgetLimitClass.NPC_COST_24H, 250_000, 200_000),
        (BudgetLimitClass.GLOBAL_COST_24H, 500_000, 400_000),
    )


@pytest.mark.parametrize(
    "provider_kind",
    (ProviderKind.FAKE, ProviderKind.LOCAL_FALLBACK, ProviderKind.DISABLED),
)
def test_non_billable_provider_cost_is_always_zero(provider_kind: ProviderKind) -> None:
    policy = PricingPolicy.zero_cost(provider_kind=provider_kind, model="synthetic-model")
    assert (
        calculate_cost_micro_usd(
            policy=policy,
            usage=ProviderUsage(prompt_tokens=32_768, completion_tokens=256),
        )
        == 0
    )


def test_reservation_is_idempotent_and_settlement_releases_difference(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    item = request()
    execution_id = uuid4()

    first = admit_and_reserve(control, item, execution_id)
    repeated = control.reserve_budget(
        request=item,
        execution_id=execution_id,
        attempt_number=1,
    )
    control.mark_budget_dispatched(first)
    settled = control.settle_budget(first, usage=ProviderUsage(1_000, 250))
    replayed = control.settle_budget(first, usage=ProviderUsage(1_000, 250))

    assert repeated == first
    assert settled == replayed
    assert settled.actual_cost_micro_usd == 2
    assert settled.released_micro_usd == first.reserved_micro_usd - 2
    assert repository.budget_attempt_count() == 1
    assert repository.budget_settlement_count() == 1
    with closing(repository._connect()) as connection:
        assert repository._all_window_totals(
            connection,
            scope_tags=first.scope_tags,
            now_ns=clock(),
        ) == {scope: (1, 1, 2) for scope in ("player_npc", "player", "npc", "global")}


def test_dispatch_before_cancel_releases_reservation(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    item = request()
    reservation = admit_and_reserve(control, item, uuid4())

    control.release_budget(reservation, reason="cancelled_before_dispatch")
    control.release_budget(reservation, reason="cancelled_before_dispatch")

    snapshot = repository.budget_attempt_snapshot()
    assert snapshot[0]["status"] == "released"
    assert snapshot[0]["actual_cost_micro_usd"] == 0
    with closing(repository._connect()) as connection:
        assert repository._all_window_totals(
            connection,
            scope_tags=reservation.scope_tags,
            now_ns=clock(),
        ) == {scope: (0, 0, 0) for scope in ("player_npc", "player", "npc", "global")}


def test_dispatch_failure_conservatively_consumes_full_reservation(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    reservation = admit_and_reserve(control, request(), uuid4())

    control.mark_budget_dispatched(reservation)
    result = control.settle_budget_conservatively(
        reservation,
        reason="provider_unavailable",
    )

    assert result.actual_cost_micro_usd == reservation.reserved_micro_usd
    assert result.conservative is True
    assert repository.budget_attempt_snapshot()[0]["status"] == "settled"


def test_restart_releases_undispatched_and_conservatively_settles_dispatched(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    undispatched = admit_and_reserve(control, request(), uuid4())
    dispatched = admit_and_reserve(
        control,
        request(player_id="other_synthetic_player"),
        uuid4(),
    )
    control.mark_budget_dispatched(dispatched)
    clock.advance(1)

    rebuilt_repository = SqliteSafetyControlRepository(
        database_path=repository.database_path,
        allowed_root=tmp_path,
    )
    rebuilt_repository.initialize()
    SafetyControl(
        repository=rebuilt_repository,
        scope_key=KEY,
        clock_ns=clock,
        pricing_policy=SYNTHETIC_PRICING_POLICY,
    )

    rows = {row["execution_id"]: row for row in rebuilt_repository.budget_attempt_snapshot()}
    assert rows[str(undispatched.execution_id)]["status"] == "released"
    assert rows[str(dispatched.execution_id)]["status"] == "settled"
    assert rows[str(dispatched.execution_id)]["conservative"] == 1
    assert rebuilt_repository.recover_open_budget_attempts(now_ns=clock()) == (0, 0)
    with closing(rebuilt_repository._connect()) as connection:
        assert rebuilt_repository._all_window_totals(
            connection,
            scope_tags=dispatched.scope_tags,
            now_ns=clock(),
        ) == {
            scope: (1, 1, dispatched.reserved_micro_usd)
            for scope in ("player_npc", "player", "npc", "global")
        }


def test_attempt_quota_boundaries_warning_and_hard_reject(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock, pricing_policy=ZERO_COST_POLICY)
    warning_seen = False
    for index in range(15):
        item = request(request_id=UUID(int=index + 1), conversation_id=UUID(int=index + 101))
        reservation = admit_and_reserve(control, item, UUID(int=index + 1001))
        warning_seen = warning_seen or reservation.soft_warning
        control.mark_budget_dispatched(reservation)
        control.settle_budget(reservation, usage=ProviderUsage(0, 0))
        clock.advance(6)

    rejected_item = request(request_id=UUID(int=99), conversation_id=UUID(int=199))
    control.admit_execution(request=rejected_item, execution_id=UUID(int=1999))
    with pytest.raises(BudgetRejectedError) as captured:
        control.reserve_budget(
            request=rejected_item,
            execution_id=UUID(int=1999),
            attempt_number=1,
        )

    assert warning_seen is True
    assert captured.value.limit_class is BudgetLimitClass.PLAYER_NPC_ATTEMPTS_1H
    assert "synthetic_player" not in repr(captured.value)


def test_rolling_window_expiry_and_scope_isolation(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock, pricing_policy=ZERO_COST_POLICY)
    for index in range(15):
        item = request(request_id=UUID(int=index + 1), conversation_id=UUID(int=index + 101))
        reservation = admit_and_reserve(control, item, UUID(int=index + 1001))
        control.mark_budget_dispatched(reservation)
        control.settle_budget(reservation, usage=ProviderUsage(0, 0))
        clock.advance(6)

    other = request(
        player_id="other_synthetic_player",
        request_id=UUID(int=80),
        conversation_id=UUID(int=180),
    )
    assert admit_and_reserve(control, other, UUID(int=1800)).attempt_number == 1
    clock.advance(3_601)
    expired = request(request_id=UUID(int=81), conversation_id=UUID(int=181))
    assert admit_and_reserve(control, expired, UUID(int=1801)).attempt_number == 1
    assert repository.budget_attempt_count() == 17


def test_player_npc_cost_cap_warns_then_rejects_before_dispatch(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    warning_seen = False
    for index in range(12):
        item = request(request_id=UUID(int=index + 1), conversation_id=UUID(int=index + 101))
        reservation = admit_and_reserve(control, item, UUID(int=index + 1001))
        warning_seen = warning_seen or reservation.soft_warning
        control.mark_budget_dispatched(reservation)
        control.settle_budget_conservatively(
            reservation,
            reason="provider_unavailable",
        )
        clock.advance(6)

    rejected = request(request_id=UUID(int=99), conversation_id=UUID(int=199))
    control.admit_execution(request=rejected, execution_id=UUID(int=1999))
    with pytest.raises(BudgetRejectedError) as captured:
        control.reserve_budget(request=rejected, execution_id=UUID(int=1999), attempt_number=1)

    assert warning_seen is True
    assert captured.value.limit_class is BudgetLimitClass.PLAYER_NPC_COST_24H


def test_concurrent_reservation_enforces_atomic_player_npc_limit(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock, pricing_policy=ZERO_COST_POLICY)
    barrier = threading.Barrier(16)
    entries: list[tuple[DialogueRequestV1, UUID]] = []
    for index in range(16):
        item = request(request_id=UUID(int=index + 1), conversation_id=UUID(int=index + 101))
        execution_id = UUID(int=index + 1001)
        control.admit_execution(request=item, execution_id=execution_id)
        entries.append((item, execution_id))
        clock.advance(6)

    def reserve(index: int) -> bool:
        item, execution_id = entries[index]
        barrier.wait()
        try:
            control.reserve_budget(request=item, execution_id=execution_id, attempt_number=1)
        except BudgetRejectedError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = tuple(executor.map(reserve, range(16)))

    assert results.count(True) == 15
    assert results.count(False) == 1
    assert repository.budget_attempt_count() == 15


@pytest.mark.anyio
async def test_dialogue_success_reserves_settles_and_commits_once(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, sessions=sessions)
    item = request()

    await service.execute(item, trace_id=uuid4())
    await service.execute(item, trace_id=uuid4())

    assert provider.call_count == 1
    assert repository.budget_attempt_count() == 1
    assert repository.budget_settlement_count() == 1
    assert (
        len(sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)))
        == 1
    )


@pytest.mark.anyio
async def test_safety_cost_recorder_links_one_execution_without_payload(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    observability = InMemoryObservabilityRecorder()
    cost_recorder = InMemorySafetyCostRecorder()
    service = make_service(
        provider,
        control,
        observability=observability,
        cost_recorder=cost_recorder,
    )
    item = request()

    await service.execute(item, trace_id=uuid4())
    records = tuple(cost_recorder.snapshot())

    assert tuple(record.event_kind for record in records) == (
        BudgetEventKind.RESERVATION,
        BudgetEventKind.DISPATCH,
        BudgetEventKind.SETTLEMENT,
    )
    assert len({record.execution_id for record in records}) == 1
    assert records[-1].actual_cost_micro_usd == 2
    serialized = repr(records)
    for forbidden in (item.player_id, item.npc_id, item.message, "provider body sentinel"):
        assert forbidden not in serialized


@pytest.mark.anyio
async def test_sqlite_observability_0002_records_successful_budget_lifecycle(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    observability = SqliteObservabilityRepository(
        database_path=tmp_path / "observability.sqlite3",
        allowed_root=tmp_path,
    )
    observability.initialize()
    service = make_service(
        FakeProvider([completion()]),
        control,
        observability=observability,
        cost_recorder=observability,
    )
    item = request()

    await service.execute(item, trace_id=uuid4())

    with sqlite3.connect(observability.database_path) as connection:
        rows = connection.execute(
            "SELECT event_kind, outcome, actual_cost_micro_usd "
            "FROM safety_cost_events ORDER BY recorded_at_ms, event_kind"
        ).fetchall()
    assert {decode_value("safety_cost_events", "event_kind", row[0]) for row in rows} == {
        "reservation",
        "dispatch",
        "settlement",
    }
    assert (
        next(
            row[2]
            for row in rows
            if decode_value("safety_cost_events", "event_kind", row[0]) == "settlement"
        )
        == 2
    )
    database_bytes = observability.database_path.read_bytes()
    for forbidden in (item.player_id, item.npc_id, item.message, "provider body sentinel"):
        assert forbidden.encode() not in database_bytes


def test_reservation_uses_one_window_aggregate_query(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    item, execution_id = request(), uuid4()
    control.admit_execution(request=item, execution_id=execution_id)
    queries: list[str] = []
    with closing(repository._connect()) as connection:
        connection.set_trace_callback(queries.append)
    try:
        control.reserve_budget(request=item, execution_id=execution_id, attempt_number=1)
    finally:
        with closing(repository._connect()) as connection:
            connection.set_trace_callback(None)
        repository.close()
    projection_reads = sum(
        "WITH requested(scope_class,scope_tag,ordinal)" in sql for sql in queries
    )
    ledger_aggregates = sum(
        "FROM budget_reservations r JOIN budget_execution_owners" in sql
        and ("COUNT(" in sql or "SUM(" in sql)
        for sql in queries
    )
    assert projection_reads == 1
    assert ledger_aggregates == 0


@pytest.mark.parametrize("first_failure", range(12))
def test_single_snapshot_preserves_first_limit_rejection_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    first_failure: int,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    item, execution_id = request(), uuid4()
    control.admit_execution(request=item, execution_id=execution_id)
    specs = ATTEMPT_WINDOW_SPECS + COST_WINDOW_SPECS
    windows = {scope: [0, 0, 0] for scope in ("player_npc", "player", "npc", "global")}
    for index, spec in enumerate(specs):
        scope = spec.limit_class.value.rsplit("_cost_" if spec.cost_window else "_attempts_", 1)[0]
        column = 2 if spec.cost_window else (0 if spec.window_seconds == 3600 else 1)
        windows[scope][column] = spec.hard_limit if index >= first_failure else 0
    monkeypatch.setattr(repository, "_all_window_totals", lambda *a, **k: windows)
    with pytest.raises(BudgetRejectedError) as captured:
        control.reserve_budget(request=item, execution_id=execution_id, attempt_number=1)
    assert captured.value.limit_class is specs[first_failure].limit_class
    with closing(repository._connect()) as c:
        assert c.execute("SELECT COUNT(*) FROM budget_execution_owners").fetchone() == (0,)
    assert repository.budget_attempt_count() == 0
    repository.close()


@pytest.mark.parametrize("fault", ["null", "duplicate", "bad_status", "bad_type"])
def test_aggregate_inputs_keep_strict_constraints_and_rollback(tmp_path: Path, fault: str) -> None:
    control, repository = make_control(tmp_path, FakeClock())
    reservation = admit_and_reserve(control, request(), uuid4())
    with closing(repository._connect()) as c:
        before = c.execute("SELECT * FROM budget_reservations").fetchall()
        c.execute("BEGIN IMMEDIATE")
        statements = {
            "null": "UPDATE budget_reservations SET reserved_micro_usd=NULL",
            "duplicate": "INSERT INTO budget_reservations SELECT * FROM budget_reservations",
            "bad_status": "UPDATE budget_reservations SET status='invalid'",
            "bad_type": "UPDATE budget_reservations SET reserved_micro_usd='invalid'",
        }
        with pytest.raises(sqlite3.IntegrityError):
            c.execute(statements[fault])
        c.rollback()
        assert c.execute("SELECT * FROM budget_reservations").fetchall() == before
        totals = repository._all_window_totals(c, scope_tags=reservation.scope_tags, now_ns=BASE_NS)
        assert totals == {
            scope: (1, 1, 2000) for scope in ("player_npc", "player", "npc", "global")
        }
    repository.close()


def test_single_aggregate_fault_rolls_back_owner_and_retry_can_reserve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    control, repository = make_control(tmp_path, FakeClock())
    item, execution_id = request(), uuid4()
    control.admit_execution(request=item, execution_id=execution_id)
    original = repository._all_window_totals

    def fail(*args: object, **kwargs: object) -> Never:
        raise sqlite3.OperationalError("synthetic private error")

    monkeypatch.setattr(repository, "_all_window_totals", fail)
    with pytest.raises(ControlUnavailableError) as captured:
        control.reserve_budget(request=item, execution_id=execution_id, attempt_number=1)
    assert "private" not in repr(captured.value)
    with closing(repository._connect()) as c:
        assert not c.in_transaction
        assert c.execute("SELECT COUNT(*) FROM budget_execution_owners").fetchone() == (0,)
    monkeypatch.setattr(repository, "_all_window_totals", original)
    first = control.reserve_budget(request=item, execution_id=execution_id, attempt_number=1)
    monkeypatch.setattr(repository, "_all_window_totals", fail)
    assert (
        control.reserve_budget(request=item, execution_id=execution_id, attempt_number=1) == first
    )
    repository.close()


@pytest.mark.parametrize("scope", ["player_npc", "player", "npc", "global"])
@pytest.mark.parametrize("window_seconds", [3600, 86400])
@pytest.mark.parametrize("boundary_delta_ns", [-1, 0, 1])
def test_combined_windows_equal_independent_row_oracle(
    scope: str,
    window_seconds: int,
    boundary_delta_ns: int,
) -> None:
    tags = BudgetScopeTags("a" * 64, "b" * 64, "c" * 64)
    now = BASE_NS + 100_000 * 1_000_000_000
    cutoff = now - window_seconds * 1_000_000_000
    # Pure aggregation test. Product constraints/atomicity are exercised separately.
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.executescript(
            "CREATE TABLE budget_execution_owners(execution_id TEXT, player_scope_tag TEXT, "
            "npc_scope_tag TEXT, player_npc_scope_tag TEXT);"
            "CREATE TABLE budget_reservations(execution_id TEXT, attempt_number INTEGER, "
            "status TEXT, reserved_at_ns INTEGER, reserved_micro_usd INTEGER);"
            "CREATE TABLE budget_settlements(execution_id TEXT, attempt_number INTEGER, "
            "actual_cost_micro_usd INTEGER);"
        )
        expected = [0, 0, 0]
        for index, status in enumerate(("reserved", "dispatched", "settled", "released")):
            for owner in range(4):
                identity = f"{index}-{owner}"
                player = tags.player_scope_tag if owner in (0, 1) else "d" * 64
                npc = tags.npc_scope_tag if owner in (0, 2) else "e" * 64
                pair = tags.player_npc_scope_tag if owner == 0 else "f" * 64
                reserved_at = cutoff + boundary_delta_ns
                connection.execute(
                    "INSERT INTO budget_execution_owners VALUES (?,?,?,?)",
                    (identity, player, npc, pair),
                )
                connection.execute(
                    "INSERT INTO budget_reservations VALUES (?,1,?,?,2000)",
                    (identity, status, reserved_at),
                )
                if status == "settled":
                    connection.execute(
                        "INSERT INTO budget_settlements VALUES (?,1,7)",
                        (identity,),
                    )
                matches = {
                    "player_npc": owner == 0,
                    "player": owner in (0, 1),
                    "npc": owner in (0, 2),
                    "global": True,
                }[scope]
                if matches and reserved_at > now - 86400 * 1_000_000_000:
                    if status != "released":
                        expected[1] += 1
                        if reserved_at > now - 3600 * 1_000_000_000:
                            expected[0] += 1
                    expected[2] += (
                        7
                        if status == "settled"
                        else (2000 if status in ("reserved", "dispatched") else 0)
                    )
            params = {
                "hour": now - 3600 * 1_000_000_000,
                "day": now - 86400 * 1_000_000_000,
                "player_npc": tags.player_npc_scope_tag,
                "player": tags.player_scope_tag,
                "npc": tags.npc_scope_tag,
            }
            row = connection.execute(_LEGACY_BUDGET_WINDOW_SQL, params).fetchone()
            index = _BUDGET_WINDOW_SCOPES_FOR_TEST.index(scope) * 3
            actual = tuple(int(value) for value in row[index : index + 3])
        assert actual == tuple(expected)


@pytest.mark.anyio
async def test_safety_cost_recorder_failure_is_fail_open(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    observability = InMemoryObservabilityRecorder()
    provider = FakeProvider([completion()])
    service = make_service(
        provider,
        control,
        observability=observability,
        cost_recorder=FailingCostRecorder(),
    )

    response = await service.execute(request(), trace_id=uuid4())

    assert response.status.value == "completed"
    assert provider.call_count == 1
    assert repository.budget_settlement_count() == 1


@pytest.mark.anyio
async def test_sqlite_observability_0002_preserves_budget_rejection_metadata(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    observability = SqliteObservabilityRepository(
        database_path=tmp_path / "observability.sqlite3",
        allowed_root=tmp_path,
    )
    observability.initialize()
    provider = FakeProvider([])
    service = make_service(
        provider,
        control,
        observability=observability,
        cost_recorder=observability,
    )
    for index in range(12):
        item = request(
            request_id=UUID(int=index + 1),
            conversation_id=UUID(int=index + 101),
        )
        execution_id = UUID(int=index + 1_001)
        control.admit_execution(request=item, execution_id=execution_id)
        reservation = control.reserve_budget(
            request=item,
            execution_id=execution_id,
            attempt_number=1,
        )
        control.mark_budget_dispatched(reservation)
        control.settle_budget_conservatively(
            reservation,
            reason="provider_unavailable",
        )
        clock.advance(6)

    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(
            request(request_id=UUID(int=99), conversation_id=UUID(int=199)),
            trace_id=uuid4(),
        )

    assert captured.value.kind is DialogueFailureKind.BUDGET_EXHAUSTED
    assert provider.call_count == 0
    with sqlite3.connect(observability.database_path) as connection:
        rejected = connection.execute(
            "SELECT outcome, reserved_micro_usd, actual_cost_micro_usd "
            "FROM safety_cost_events WHERE event_kind = ?",
            (encode_value("safety_cost_events", "event_kind", "rejection"),),
        ).fetchall()
        open_traces = connection.execute(
            "SELECT COUNT(*) FROM trace_runs WHERE record_status = 'open'"
        ).fetchone()[0]
    assert [
        (decode_value("safety_cost_events", "outcome", row[0]), *row[1:]) for row in rejected
    ] == [("rejected", 2_000, 0)]
    assert open_traces == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    "failure",
    (
        ProviderUnavailableError("synthetic provider unavailable"),
        ProviderInvalidResponseError("synthetic invalid response"),
    ),
)
async def test_provider_failure_is_conservatively_settled_without_business_write(
    tmp_path: Path,
    failure: Exception,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([failure])
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, sessions=sessions)
    item = request()

    with pytest.raises(DialogueUseCaseError):
        await service.execute(item, trace_id=uuid4())

    expected_attempts = 2 if isinstance(failure, ProviderUnavailableError) else 1
    assert provider.call_count == expected_attempts
    rows = repository.budget_attempt_snapshot()
    assert len(rows) == expected_attempts
    assert all(row["status"] == "settled" for row in rows)
    assert all(row["conservative"] == 1 for row in rows)
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


@pytest.mark.anyio
async def test_timeout_is_conservatively_settled(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    service = make_service(
        FakeProvider(
            [
                ProviderTimeoutError("synthetic timeout"),
                ProviderTimeoutError("synthetic timeout"),
            ]
        ),
        control,
    )

    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(request(), trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.PROVIDER_TIMEOUT
    rows = repository.budget_attempt_snapshot()
    assert len(rows) == 2
    assert all(row["status"] == "settled" for row in rows)
    assert all(row["conservative"] == 1 for row in rows)


@pytest.mark.anyio
async def test_cancel_while_waiting_for_permit_creates_no_execution_attempt(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = BlockingProvider()
    service = make_service(provider, control)
    owner = asyncio.create_task(service.execute(request(), trace_id=uuid4()))
    await asyncio.wait_for(provider.started.wait(), timeout=1)
    waiting = asyncio.create_task(service.execute(request(), trace_id=uuid4()))
    await asyncio.sleep(0.05)

    waiting.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiting
    provider.release.set()
    await owner

    statuses = tuple(row["status"] for row in repository.budget_attempt_snapshot())
    assert statuses.count("settled") == 1
    assert len(statuses) == 1
    assert repository.admission_count() == 1
    assert len(repository.execution_intent_snapshot()) == 1
    assert provider.call_count == 1


@pytest.mark.anyio
async def test_cancel_after_intent_before_provider_releases_all_control_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = BlockingProvider()
    service = make_service(provider, control)

    async def no_active_waiter(_request_id: UUID) -> bool:
        return False

    monkeypatch.setattr(service, "_execution_has_active_waiter", no_active_waiter)
    with pytest.raises(asyncio.CancelledError):
        await service.execute(request(), trace_id=uuid4())

    intent = repository.execution_intent_snapshot()[0]
    assert provider.call_count == 0
    assert intent["state"] == "released"
    assert intent["terminal_reason"] == "cancelled_before_dispatch"
    assert repository.budget_attempt_snapshot()[0]["status"] == "released"
    assert repository.active_permit_count() == 0


@pytest.mark.anyio
async def test_cancel_after_dispatch_is_conservatively_settled(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = CancellingProvider()
    service = make_service(provider, control)

    with pytest.raises(asyncio.CancelledError):
        await service.execute(request(), trace_id=uuid4())

    row = repository.budget_attempt_snapshot()[0]
    assert row["status"] == "settled"
    assert row["conservative"] == 1


@pytest.mark.anyio
async def test_budget_rejection_is_nonretryable_and_has_zero_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    service = make_service(provider, control)

    def reject(**_values: object) -> Never:
        raise BudgetRejectedError(BudgetLimitClass.PLAYER_NPC_COST_24H)

    monkeypatch.setattr(repository, "reserve_budget", reject)
    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(request(), trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.BUDGET_EXHAUSTED
    assert captured.value.retryable is False
    assert captured.value.retry_after_seconds is None
    assert provider.call_count == 0


@pytest.mark.anyio
async def test_budget_rejection_http_429_has_no_retry_after_or_budget_detail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    application = create_app(dialogue_service=make_service(provider, control))

    def reject(**_values: object) -> Never:
        raise BudgetRejectedError(BudgetLimitClass.PLAYER_NPC_COST_24H)

    monkeypatch.setattr(repository, "reserve_budget", reject)
    item = request()
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/dialogue",
            json={
                "request_id": str(item.request_id),
                "player_id": item.player_id,
                "npc_id": item.npc_id,
                "conversation_id": str(item.conversation_id),
                "message": item.message,
            },
        )

    assert response.status_code == 429
    assert response.json() == {
        "code": "budget_exhausted",
        "message": "The dialogue budget is exhausted.",
        "retryable": False,
        "trace_id": response.json()["trace_id"],
    }
    assert "retry-after" not in response.headers
    assert provider.call_count == 0


@pytest.mark.anyio
async def test_settlement_failure_aborts_business_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, sessions=sessions)
    item = request()

    def fail_settlement(**_values: object) -> Never:
        raise SafetyControlStorageError

    monkeypatch.setattr(repository, "settle_budget", fail_settlement)
    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(item, trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.CONTROL_UNAVAILABLE
    assert provider.call_count == 1
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


def test_control_sqlite_0002_and_payload_sentinel(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    item = request()
    reservation = admit_and_reserve(control, item, uuid4())
    control.mark_budget_dispatched(reservation)
    control.settle_budget(reservation, usage=ProviderUsage(1, 1))

    with sqlite3.connect(repository.database_path) as connection:
        migrations = connection.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
    assert migrations == [
        (1, "0001_safety_cost_control.sql"),
        (2, "0002_budget_cost_control.sql"),
        (3, "0003_retry_circuit_breaker.sql"),
        (4, "0004_leaf_table_storage_layout.sql"),
        (5, "0005_budget_window_projection.sql"),
        (6, "0006_control_execution_intent.sql"),
        (7, "0007_drop_redundant_budget_owner_npc_index.sql"),
        (8, "0008_budget_projection_integrity.sql"),
        (9, "0009_provider_permit_scope_storage.sql"),
    ]
    database_bytes = repository.database_path.read_bytes()
    for forbidden in (
        item.player_id,
        item.npc_id,
        str(item.conversation_id),
        item.message,
        "system prompt sentinel",
        "provider body sentinel",
        "secret sentinel",
    ):
        assert forbidden.encode() not in database_bytes


# V10 uses only real-migration control databases; never a production SQL replacement.
def test_missing_v10_historical_root_skips_without_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("F009_V10_SEMANTIC_ROOT", raising=False)
    sentinel = "SYNTHETIC-ENV-VALUE-MUST-NOT-APPEAR"
    monkeypatch.setenv("F009_UNRELATED_SENTINEL", sentinel)
    with pytest.raises(pytest.skip.Exception) as captured:
        _v10_root_case("matrix")
    assert sentinel not in str(captured.value)


def _v10_root_case(label: str) -> Path:
    import os

    raw_root = os.environ.get("F009_V10_SEMANTIC_ROOT")
    if raw_root is None:
        pytest.skip("Historical diagnostic root is not configured")
    from scripts.f009_step5_attribution import V10_SEMANTIC_LABELS

    if label not in V10_SEMANTIC_LABELS:
        pytest.fail("Historical diagnostic case is not registered", pytrace=False)
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


def test_v10_matrix_oracle_mutants_and_streaming_plan() -> None:
    from scripts.f009_step5_attribution import (
        V10_CANDIDATE_SQL,
        require_budget_equivalence,
        require_streaming_plan,
        synthetic_budget_totals,
    )

    root = _v10_root_case("matrix")
    repository = SqliteSafetyControlRepository(
        database_path=root / "control.sqlite3", allowed_root=root
    )
    repository.initialize()
    actors = tuple(
        BudgetScopeTags(
            player_scope_tag=f"{player:064x}",
            npc_scope_tag=f"{npc:064x}",
            player_npc_scope_tag=f"{pair:064x}",
        )
        for player, npc, pair in ((1, 2, 3), (1, 4, 5), (6, 2, 7), (8, 9, 10))
    )
    rows: list[tuple[BudgetScopeTags, str, int, int, int | None]] = []
    try:
        with closing(repository._connect()) as c:
            c.execute("BEGIN IMMEDIATE")
            assert c.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 6
            times = tuple(
                BASE_NS - window * 1_000_000_000 + delta
                for window in (3600, 86400)
                for delta in (-1, 0, 1)
            )
            for actor in actors:
                for at in times:
                    for status in ("reserved", "dispatched", "settled", "released"):
                        for reserved in (0, 2000):
                            identity = str(UUID(int=len(rows) + 1))
                            actual = reserved // 4 if status == "settled" else None
                            # One legal FK graph with a missing settlement exercises LEFT JOIN NULL.
                            missing = len(rows) == 5
                            if missing:
                                actual = None
                            rows.append((actor, status, at, reserved, actual))
                            c.execute(
                                "INSERT INTO execution_admissions VALUES (?,?,?,?,?,?,?)",
                                (
                                    identity,
                                    identity,
                                    "f-009-safety-control-v1",
                                    actor.player_scope_tag,
                                    actor.player_npc_scope_tag,
                                    f"{11:064x}",
                                    at,
                                ),
                            )
                            c.execute(
                                "INSERT INTO budget_execution_owners VALUES (?,?,?,?,?,?)",
                                (
                                    identity,
                                    BUDGET_POLICY_VERSION,
                                    actor.player_scope_tag,
                                    actor.npc_scope_tag,
                                    actor.player_npc_scope_tag,
                                    at,
                                ),
                            )
                            c.execute(
                                "INSERT INTO budget_reservations "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (
                                    identity,
                                    1,
                                    BUDGET_POLICY_VERSION,
                                    "synthetic-v10",
                                    "fake",
                                    "fake-model",
                                    reserved,
                                    0,
                                    status,
                                    at,
                                    at if status in ("dispatched", "settled") else None,
                                    at if status == "settled" else None,
                                    at if status == "released" else None,
                                    "cancelled_before_dispatch" if status == "released" else None,
                                ),
                            )
                            if status == "settled" and not missing:
                                c.execute(
                                    "INSERT INTO budget_settlements "
                                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                    (
                                        identity,
                                        1,
                                        BUDGET_POLICY_VERSION,
                                        "synthetic-v10",
                                        reserved,
                                        actual,
                                        reserved - int(actual or 0),
                                        0,
                                        0,
                                        0,
                                        "trusted_usage",
                                        at,
                                    ),
                                )
            c.commit()
            c.execute("BEGIN IMMEDIATE")
            scopes = ("player_npc", "player", "npc", "global")
            for actor in actors:
                expected: dict[str, tuple[int, int, int]] = {}
                for scope in scopes:
                    selected = [
                        row
                        for row in rows
                        if row[1] != "released"
                        and row[2] > BASE_NS - 86400_000_000_000
                        and (
                            scope == "global"
                            or getattr(row[0], scope + "_scope_tag")
                            == getattr(actor, scope + "_scope_tag")
                        )
                    ]
                    expected[scope] = (
                        sum(row[2] > BASE_NS - 3600_000_000_000 for row in selected),
                        len(selected),
                        sum((row[4] or 0) if row[1] == "settled" else row[3] for row in selected),
                    )
                current = repository._all_window_totals(c, scope_tags=actor, now_ns=BASE_NS)
                candidate = synthetic_budget_totals(c, scope_tags=actor, now_ns=BASE_NS)
                require_budget_equivalence(expected, current)
                require_budget_equivalence(expected, candidate)
            params = {
                "hour": BASE_NS - 3600_000_000_000,
                "day": BASE_NS - 86400_000_000_000,
                "player": actors[0].player_scope_tag,
                "npc": actors[0].npc_scope_tag,
                "player_npc": actors[0].player_npc_scope_tag,
            }
            plan = tuple(row[1] for row in c.execute("EXPLAIN " + V10_CANDIDATE_SQL, params))
            require_streaming_plan(plan)
            current_row = tuple(c.execute(_LEGACY_BUDGET_WINDOW_SQL, params).fetchone())
            mutants = (
                V10_CANDIDATE_SQL.replace("> :hour", ">= :hour"),
                V10_CANDIDATE_SQL.replace("> :day", ">= :day"),
                V10_CANDIDATE_SQL.replace("r.status <> 'released'", "1=1"),
                V10_CANDIDATE_SQL.replace(
                    "THEN s.actual_cost_micro_usd", "THEN r.reserved_micro_usd"
                ),
            )
            for sql in mutants:
                changed_row = tuple(c.execute(sql, params).fetchone())
                with pytest.raises(ValueError, match="Synthetic budget equivalence"):
                    require_budget_equivalence(
                        {scope: current_row[i * 3 : i * 3 + 3] for i, scope in enumerate(scopes)},
                        {scope: changed_row[i * 3 : i * 3 + 3] for i, scope in enumerate(scopes)},
                    )
            # FK remains active: missing owner cannot enter the real schema.
            with pytest.raises(sqlite3.IntegrityError):
                c.execute(
                    "INSERT INTO budget_execution_owners VALUES (?,?,?,?,?,?)",
                    (
                        str(UUID(int=9999)),
                        BUDGET_POLICY_VERSION,
                        f"{1:064x}",
                        f"{2:064x}",
                        f"{3:064x}",
                        BASE_NS,
                    ),
                )
            c.rollback()
            assert c.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert not c.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        repository.close()
    print({"synthetic_rows": len(rows), "oracle_comparisons": 8, "wrong_sql_detected": 4})


_V10_SCENARIOS = (
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


@pytest.mark.parametrize("variant", ["current", "candidate"])
@pytest.mark.parametrize("scenario", _V10_SCENARIOS)
def test_v10_real_repository_regression(
    variant: str, scenario: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    from scripts.f009_step5_attribution import synthetic_budget_totals

    root = _v10_root_case(variant + "-" + scenario)
    original = SqliteSafetyControlRepository
    opened: list[SqliteSafetyControlRepository] = []

    class SyntheticCandidateRepository(SqliteSafetyControlRepository):
        _all_window_totals = staticmethod(
            synthetic_budget_totals if variant == "candidate" else original._all_window_totals
        )

        def __init__(self, *, database_path: Path, allowed_root: Path) -> None:
            super().__init__(database_path=database_path, allowed_root=allowed_root)
            opened.append(self)

    # Test-local factory only; product globals and real request composition are unchanged.
    monkeypatch.setattr(
        sys.modules[__name__], "SqliteSafetyControlRepository", SyntheticCandidateRepository
    )
    scenarios = {
        "replay": test_reservation_is_idempotent_and_settlement_releases_difference,
        "release": test_dispatch_before_cancel_releases_reservation,
        "conservative": test_dispatch_failure_conservatively_consumes_full_reservation,
        "restart": test_restart_releases_undispatched_and_conservatively_settles_dispatched,
        "attempt-warning": test_attempt_quota_boundaries_warning_and_hard_reject,
        "expiry": test_rolling_window_expiry_and_scope_isolation,
        "cost-warning": test_player_npc_cost_cap_warns_then_rejects_before_dispatch,
        "concurrency": test_concurrent_reservation_enforces_atomic_player_npc_limit,
        "one-query": test_reservation_uses_one_window_aggregate_query,
    }
    try:
        if scenario.startswith("order-"):
            test_single_snapshot_preserves_first_limit_rejection_order(
                root, monkeypatch, int(scenario.removeprefix("order-"))
            )
        elif scenario.startswith("constraint-"):
            test_aggregate_inputs_keep_strict_constraints_and_rollback(
                root, scenario.removeprefix("constraint-")
            )
        elif scenario == "repository-fault":
            test_single_aggregate_fault_rolls_back_owner_and_retry_can_reserve(root, monkeypatch)
        else:
            scenarios[scenario](root)
    finally:
        for repository in opened:
            repository.close()
