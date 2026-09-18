"""Failure-first contract for the V14 synthetic budget projection candidate."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest
from scripts import f009_step5_benchmark as benchmark
from scripts import f009_step5_budget_projection_preflight as projection
from scripts.f009_step5_budget_projection_preflight import (
    GLOBAL_SCOPE_TAG,
    P95_ATTRIBUTION_ORDER,
    PROJECTION_VERSION,
    STABILITY_SEGMENT_RANGES,
    STAGE_ATTRIBUTION_ROOT,
    UNIFIED_VALIDATION_ROOT,
    V18_REVISED_PERFORMANCE_ROOT,
    V18_REVISED_SEMANTIC_ROOT,
    V18_SET_BASED_ROOT,
    V19_SINGLE_WRITE_ROOT,
    CandidateMemoryControl,
    CandidateStageProbe,
    SetBasedCandidateMemoryControl,
    SingleWriteCandidateMemoryControl,
    _candidate_stage_protocol_result,
    _p95_attribution_verdict,
    _performance_gate,
    _set_based_gate_verdict,
    _summarize_stability_runs,
    _validate_revised_performance_root,
    _validate_revised_semantic_root,
    _validate_set_based_root,
    _validate_single_write_root,
    _validate_stage_attribution_root,
    assert_projection_matches_ledger,
    projection_snapshot,
)

from cyber_town.application.budget import BudgetScopeTags, PricingPolicy
from cyber_town.application.control import SafetyControl
from cyber_town.application.observability import ProviderKind
from cyber_town.application.provider import ProviderUsage
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.infrastructure.control.sqlite_control import SafetyControlStorageError

pytestmark = pytest.mark.skipif(
    os.environ.get("F009_V14_V19_DIAGNOSTIC_BATCH") != "enabled",
    reason="Historical projection diagnostic batch is not configured",
)

ROOT = (
    Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection-validation-v2")
    / "validation-01"
)
BASE_NS = 1_800_000_000_000_000_000
KEY = b"f009-v14-synthetic-scope-key-32bytes"


class Clock:
    def __init__(self) -> None:
        self.value = BASE_NS

    def __call__(self) -> int:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += seconds * 1_000_000_000


def request(index: int = 1, *, player: str = "projection_player") -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=UUID(int=index),
        player_id=player,
        npc_id=("neon_guide", "signal_archivist", "night_courier")[(index - 1) % 3],
        conversation_id=UUID(int=10_000 + index),
        message="Synthetic projection preflight.",
    )


def make_control(clock: Clock) -> tuple[SafetyControl, CandidateMemoryControl]:
    repository = CandidateMemoryControl(ROOT / "semantic")
    repository.initialize()
    control = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )
    return control, repository


def test_candidate_schema_is_strict_and_replaces_only_three_owner_indexes() -> None:
    repository = CandidateMemoryControl(ROOT / "semantic")
    repository.initialize()
    try:
        indexes = {
            row[0]
            for row in repository.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
        }
        assert "idx_budget_attempt_quota_time" in indexes
        assert (
            not {
                "idx_budget_owners_player",
                "idx_budget_owners_npc",
                "idx_budget_owners_player_npc",
            }
            & indexes
        )
        tables = {
            row[0]: row[1]
            for row in repository.connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table'"
            )
        }
        assert "STRICT" in tables["budget_window_projection_state"]
        assert "WITHOUT ROWID" in tables["budget_window_totals"]
        assert PROJECTION_VERSION in tables["budget_window_projection_state"]
        assert GLOBAL_SCOPE_TAG == "0" * 64
    finally:
        repository.close()


def test_candidate_schema_repeat_initialize_keeps_v5_boundary() -> None:
    repository = CandidateMemoryControl(ROOT / "semantic")
    repository.initialize()
    repository.initialize()
    try:
        assert repository.connection.execute("PRAGMA user_version").fetchone() == (5,)
        assert repository.connection.execute(
            "SELECT COUNT(*) FROM schema_migrations"
        ).fetchone() == (4,)
    finally:
        repository.close()


def test_reserve_replay_settlement_and_release_keep_projection_exact() -> None:
    clock = Clock()
    control, repository = make_control(clock)
    try:
        first = request(1)
        execution = UUID(int=101)
        control.admit_execution(request=first, execution_id=execution)
        reservation = control.reserve_budget(
            request=first,
            execution_id=execution,
            attempt_number=1,
        )
        assert (
            control.reserve_budget(
                request=first,
                execution_id=execution,
                attempt_number=1,
            )
            == reservation
        )
        assert_projection_matches_ledger(repository.connection, clock())

        control.mark_budget_dispatched(reservation)
        control.settle_budget(reservation, usage=ProviderUsage(0, 0))
        assert_projection_matches_ledger(repository.connection, clock())

        second = request(2)
        second_execution = UUID(int=102)
        control.admit_execution(request=second, execution_id=second_execution)
        released = control.reserve_budget(
            request=second,
            execution_id=second_execution,
            attempt_number=1,
        )
        control.release_budget(released, reason="cancelled_before_dispatch")
        assert_projection_matches_ledger(repository.connection, clock())
        assert repository.budget_attempt_count() == 2
        assert repository.budget_settlement_count() == 1
    finally:
        repository.close()


@pytest.mark.parametrize("seconds", [3_600, 86_400])
@pytest.mark.parametrize("delta_ns", [-1, 0, 1])
def test_projection_preserves_strict_cutoff_boundaries(seconds: int, delta_ns: int) -> None:
    clock = Clock()
    control, repository = make_control(clock)
    try:
        item = request(1)
        execution = UUID(int=201)
        control.admit_execution(request=item, execution_id=execution)
        reservation = control.reserve_budget(
            request=item,
            execution_id=execution,
            attempt_number=1,
        )
        control.mark_budget_dispatched(reservation)
        control.settle_budget(reservation, usage=ProviderUsage(0, 0))
        clock.value = BASE_NS + seconds * 1_000_000_000 + delta_ns
        repository.advance_projection(now_ns=clock())
        assert_projection_matches_ledger(repository.connection, clock())
    finally:
        repository.close()


def test_clock_rollback_and_corrupt_totals_rebuild_from_authoritative_ledger() -> None:
    clock = Clock()
    control, repository = make_control(clock)
    try:
        item = request(1)
        execution = UUID(int=301)
        control.admit_execution(request=item, execution_id=execution)
        control.reserve_budget(request=item, execution_id=execution, attempt_number=1)
        clock.advance(10)
        repository.advance_projection(now_ns=clock())
        repository.connection.execute(
            "UPDATE budget_window_totals SET attempts_24h = attempts_24h + 7"
        )
        repository.connection.commit()
        clock.value -= 5 * 1_000_000_000
        repository.advance_projection(now_ns=clock())
        assert_projection_matches_ledger(repository.connection, clock())
    finally:
        repository.close()


def test_projection_snapshot_is_metadata_only() -> None:
    clock = Clock()
    control, repository = make_control(clock)
    try:
        item = request(1, player="private_projection_player")
        execution = UUID(int=401)
        control.admit_execution(request=item, execution_id=execution)
        control.reserve_budget(request=item, execution_id=execution, attempt_number=1)
        snapshot = projection_snapshot(repository.connection)
        serialized = repr(snapshot)
        assert "private_projection_player" not in serialized
        assert "Synthetic projection preflight" not in serialized
        assert set(snapshot) == {"state", "totals"}
    finally:
        repository.close()


def test_projection_constraints_fail_closed() -> None:
    repository = CandidateMemoryControl(ROOT / "semantic")
    repository.initialize()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            repository.connection.execute(
                "INSERT INTO budget_window_totals VALUES ('global', ?, -1, 0, 0, 1, 1)",
                (GLOBAL_SCOPE_TAG,),
            )
    finally:
        repository.close()


def test_stability_segments_compare_equal_steady_state_work() -> None:
    assert STABILITY_SEGMENT_RANGES == {
        "early_steady_100": (100, 200),
        "middle_steady_100": (500, 600),
        "late_steady_100": (900, 1_000),
    }
    runs = tuple(tuple(0.2 for _ in range(1_000)) for _ in range(5))
    summary = _summarize_stability_runs(runs)
    assert summary["workload_signature"] == {
        "new_scope_rows": 2,
        "hour_expired_rows": 1,
        "day_expired_rows": 0,
        "total_adjustment_groups": 8,
    }
    assert summary["compared_execution_ranges"] == {
        "early_steady_100": [101, 200],
        "middle_steady_100": [501, 600],
        "late_steady_100": [901, 1_000],
    }
    assert summary["stable_tail"] is True


def test_stability_summary_uses_all_five_runs_not_only_the_last() -> None:
    stable = tuple(0.2 for _ in range(1_000))
    regressed = list(stable)
    regressed[900:] = [0.4] * 100
    summary = _summarize_stability_runs((stable, stable, stable, stable, tuple(regressed)))
    per_run = cast(list[dict[str, Any]], summary["per_run_segments"])
    aggregate = cast(dict[str, dict[str, float]], summary["aggregate_segments"])
    assert summary["run_count"] == 5
    assert len(per_run) == 5
    assert per_run[-1]["stable_tail"] is False
    assert aggregate["late_steady_100"]["median_ms"] == 0.2


def test_p95_attribution_uses_the_core_matrix_protocol_without_extra_pairs() -> None:
    assert P95_ATTRIBUTION_ORDER == (
        ("no_recorder_control", "in_memory_control"),
        ("no_recorder_control", "in_memory_control"),
        ("no_recorder_control", "in_memory_control"),
        ("no_recorder_control", "in_memory_control"),
        ("no_recorder_control", "in_memory_control"),
    )
    assert benchmark.memory_protocol_config()["warmup_pair_count"] == 1
    assert benchmark.memory_protocol_config()["measured_pair_count"] == 5


def test_v16_unified_candidate_uses_the_registered_root() -> None:
    assert (
        Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v16-budget-projection-unified")
        == UNIFIED_VALIDATION_ROOT
    )


def test_candidate_performance_gate_exports_unified_runtime_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(benchmark, "MEMORY_TRACE_COUNT", 2)
    monkeypatch.setattr(
        projection,
        "_summarize_stability_runs",
        lambda _runs: {"stable_tail": True},
    )
    (tmp_path / "performance").mkdir()
    result = _performance_gate(tmp_path)
    assert result["protocol"] == benchmark.memory_protocol_config()
    runtime = cast(list[dict[str, object]], result["runtime_runs"])
    assert len(runtime) == 12
    assert [item["warmup"] for item in runtime].count(True) == 2
    assert all(item["protocol_version"] == "f-009-memory-control-protocol-v2" for item in runtime)
    assert all(item["gating"] is True for item in runtime)


def test_v17_stage_attribution_uses_registered_non_gating_protocol(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    assert (
        Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v17-projection-stage-attribution")
        == STAGE_ATTRIBUTION_ROOT
    )
    monkeypatch.setattr(benchmark, "MEMORY_TRACE_COUNT", 2)
    original = benchmark._MemoryControl
    benchmark.__dict__["_MemoryControl"] = CandidateMemoryControl
    try:
        protocol = benchmark._paired_memory_protocol(tmp_path, stage_attribution=True)
    finally:
        benchmark.__dict__["_MemoryControl"] = original
    result = _candidate_stage_protocol_result(protocol)
    assert result["attribution_completeness_percent"] == 100.0
    runtime = cast(list[dict[str, object]], result["runtime_runs"])
    assert len(runtime) == 12
    assert all(item["gating"] is False for item in runtime)
    assert all(item["stage_attribution"] is not None for item in runtime)
    assert result["stage_topology"] == "flat_non_overlapping_siblings"
    serialized = json.dumps(result, sort_keys=True)
    for forbidden in (
        "bench_player_0000",
        "Synthetic local benchmark.",
        "Synthetic local diagnostic persona.",
        "f009-synthetic-scope-key-32bytes!!",
    ):
        assert forbidden not in serialized


def test_v17_stage_root_and_stage_order_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manifest is invalid"):
        _validate_stage_attribution_root(STAGE_ATTRIBUTION_ROOT)
    with pytest.raises(ValueError, match="not approved"):
        _validate_stage_attribution_root(tmp_path)
    probe = CandidateStageProbe()
    with pytest.raises(RuntimeError, match="ownership is incomplete"):
        probe.run("budget_reservation", lambda: None)


def test_stage_probe_preserves_return_exception_and_cancellation() -> None:
    probe = benchmark._MemoryStageProbe()
    sentinel = object()
    assert probe.run("budget_reservation", lambda: sentinel) is sentinel

    expected = RuntimeError("synthetic-stage-error")
    with pytest.raises(RuntimeError) as caught:
        probe.run("budget_reservation", lambda: (_ for _ in ()).throw(expected))
    assert caught.value is expected

    async def cancel() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(probe.run_async("provider_completion", cancel))


def test_p95_attribution_verdict_marks_only_stable_common_exceedance() -> None:
    blocked = _p95_attribution_verdict(
        baseline_p95=(2.1, 2.2, 2.3, 2.4, 1.9),
        recorded_p95=(2.2, 2.3, 2.4, 2.5, 1.8),
        recorded_aggregate_p95=2.3,
        recorded_aggregate_p99=4.0,
        throughput_ratio=0.95,
        stable_tail=True,
    )
    assert blocked["common_p95_exceed_count"] == 4
    assert blocked["common_foundation_blocker"] is True
    assert blocked["passed"] is False

    inconclusive = _p95_attribution_verdict(
        baseline_p95=(2.1, 2.2, 2.3, 1.8, 1.9),
        recorded_p95=(2.2, 2.3, 2.4, 1.7, 1.8),
        recorded_aggregate_p95=1.9,
        recorded_aggregate_p99=4.0,
        throughput_ratio=0.95,
        stable_tail=True,
    )
    assert inconclusive["common_p95_exceed_count"] == 3
    assert inconclusive["common_foundation_blocker"] is False
    assert inconclusive["passed"] is True


def test_v18_set_based_root_and_manifest_are_fail_closed(tmp_path: Path) -> None:
    assert (
        Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based")
        == V18_SET_BASED_ROOT
    )
    with pytest.raises(ValueError, match="not fresh"):
        _validate_set_based_root(V18_SET_BASED_ROOT)
    with pytest.raises(ValueError, match="not approved"):
        _validate_set_based_root(tmp_path)


def test_v18_set_based_reserve_settlement_and_release_use_fixed_batches() -> None:
    clock = Clock()
    repository = SetBasedCandidateMemoryControl(V18_SET_BASED_ROOT / "preflight-01" / "semantic")
    repository.initialize()
    control = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )
    try:
        item = request(801, player="set_based_private_player")
        execution = UUID(int=801)
        control.admit_execution(request=item, execution_id=execution)
        reservation = control.reserve_budget(
            request=item,
            execution_id=execution,
            attempt_number=1,
        )
        after_reserve = repository.set_based_operation_snapshot()
        assert after_reserve["window_total_read_batches"] == 1
        assert after_reserve["scope_delta_apply_batches"] == 1
        assert after_reserve["scope_delta_rows"] == 4
        assert after_reserve["scope_delta_sql_statements"] == 2

        control.mark_budget_dispatched(reservation)
        control.settle_budget(reservation, usage=ProviderUsage(0, 0))
        after_settlement = repository.set_based_operation_snapshot()
        assert after_settlement["scope_delta_apply_batches"] == 2
        assert after_settlement["scope_delta_rows"] == 8
        assert_projection_matches_ledger(repository.connection, clock())

        serialized = json.dumps(after_settlement, sort_keys=True)
        assert "set_based_private_player" not in serialized
        assert "Synthetic projection preflight" not in serialized
    finally:
        repository.close()


def test_v18_set_based_delta_failure_rolls_back_without_negative_totals() -> None:
    repository = SetBasedCandidateMemoryControl(V18_SET_BASED_ROOT / "preflight-01" / "semantic")
    repository.initialize()
    try:
        repository.connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.IntegrityError):
            repository._apply_scope_deltas(
                repository.connection,
                deltas=tuple(
                    (scope_class, scope_tag, -1, -1, 0)
                    for scope_class, scope_tag in projection._scope_pairs(
                        BudgetScopeTags(
                            player_scope_tag="1" * 64,
                            npc_scope_tag="2" * 64,
                            player_npc_scope_tag="3" * 64,
                        )
                    )
                ),
                revision=1,
                now_ns=BASE_NS,
            )
        repository.connection.rollback()
        assert repository.connection.execute(
            "SELECT COUNT(*) FROM budget_window_totals"
        ).fetchone() == (0,)
    finally:
        repository.close()


def test_v18_gate_requires_all_relative_absolute_space_and_semantic_thresholds() -> None:
    passed = _set_based_gate_verdict(
        reservation_p95_ms=0.6,
        settlement_p95_ms=0.35,
        recorded_p95_ms=1.9,
        recorded_p99_ms=4.9,
        throughput_ratio=0.8,
        stable_tail=True,
        control_growth_bytes=256 * 1024,
        semantic_passed=True,
        privacy_hits=0,
    )
    assert passed["passed"] is True
    assert cast(float, passed["reservation_reduction_percent"]) >= 35.0
    assert cast(float, passed["settlement_reduction_percent"]) >= 20.0

    failed = _set_based_gate_verdict(
        reservation_p95_ms=0.7,
        settlement_p95_ms=0.35,
        recorded_p95_ms=1.9,
        recorded_p99_ms=4.9,
        throughput_ratio=0.8,
        stable_tail=True,
        control_growth_bytes=256 * 1024,
        semantic_passed=True,
        privacy_hits=0,
    )
    assert failed["passed"] is False
    assert "reservation_reduction" in cast(list[str], failed["failed_gates"])


def test_v18_revised_semantic_root_is_fresh_and_separate(tmp_path: Path) -> None:
    assert (
        Path(
            r"E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based-revised-semantic"
        )
        == V18_REVISED_SEMANTIC_ROOT
    )
    with pytest.raises(ValueError, match="manifest is invalid"):
        _validate_revised_semantic_root(V18_REVISED_SEMANTIC_ROOT)
    assert V18_REVISED_SEMANTIC_ROOT != V18_SET_BASED_ROOT
    with pytest.raises(ValueError, match="not approved"):
        _validate_revised_semantic_root(tmp_path)


def test_v18_revised_delta_uses_zero_seed_then_set_based_update() -> None:
    assert "INSERT OR IGNORE INTO budget_window_totals" in projection.SET_BASED_ZERO_SEED_SQL
    assert "UPDATE budget_window_totals" in projection.SET_BASED_UPDATE_SQL
    assert "attempts_1h+d.attempts_1h" in projection.SET_BASED_UPDATE_SQL
    assert "ON CONFLICT" not in projection.SET_BASED_UPDATE_SQL


def test_v18_revised_performance_root_is_fresh_and_separate(tmp_path: Path) -> None:
    assert (
        Path(
            r"E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based-revised-performance"
        )
        == V18_REVISED_PERFORMANCE_ROOT
    )
    with pytest.raises(ValueError, match="manifest is invalid"):
        _validate_revised_performance_root(V18_REVISED_PERFORMANCE_ROOT)
    assert V18_REVISED_PERFORMANCE_ROOT not in {
        V18_SET_BASED_ROOT,
        V18_REVISED_SEMANTIC_ROOT,
    }
    with pytest.raises(ValueError, match="not approved"):
        _validate_revised_performance_root(tmp_path)


def test_v19_root_manifest_is_fresh_and_separate(tmp_path: Path) -> None:
    assert (
        Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v19-projection-single-write")
        == V19_SINGLE_WRITE_ROOT
    )
    with pytest.raises(ValueError, match="not fresh"):
        _validate_single_write_root(V19_SINGLE_WRITE_ROOT)
    assert V19_SINGLE_WRITE_ROOT not in {
        V18_SET_BASED_ROOT,
        V18_REVISED_SEMANTIC_ROOT,
        V18_REVISED_PERFORMANCE_ROOT,
    }
    with pytest.raises(ValueError, match="not approved"):
        _validate_single_write_root(tmp_path)


def test_v19_lifecycle_delta_uses_exactly_one_write_statement() -> None:
    clock = Clock()
    repository = SingleWriteCandidateMemoryControl(
        V19_SINGLE_WRITE_ROOT / "validation-01" / "semantic"
    )
    repository.initialize()
    control = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )
    try:
        item = request(1901, player="single_write_private_player")
        execution = UUID(int=1901)
        control.admit_execution(request=item, execution_id=execution)
        reservation = control.reserve_budget(
            request=item,
            execution_id=execution,
            attempt_number=1,
        )
        after_reserve = repository.set_based_operation_snapshot()
        assert after_reserve["scope_delta_apply_batches"] == 1
        assert after_reserve["scope_delta_sql_statements"] == 1
        assert after_reserve["scope_delta_upsert_statements"] == 1
        assert after_reserve["scope_delta_update_statements"] == 0

        control.mark_budget_dispatched(reservation)
        control.settle_budget(reservation, usage=ProviderUsage(0, 0))
        after_settlement = repository.set_based_operation_snapshot()
        assert after_settlement["scope_delta_apply_batches"] == 2
        assert after_settlement["scope_delta_sql_statements"] == 2
        assert after_settlement["scope_delta_update_statements"] == 1
        assert_projection_matches_ledger(repository.connection, clock())
    finally:
        repository.close()


def test_v19_no_expiration_rows_skip_totals_write() -> None:
    clock = Clock()
    repository = SingleWriteCandidateMemoryControl(
        V19_SINGLE_WRITE_ROOT / "validation-01" / "semantic"
    )
    repository.initialize()
    control = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )
    try:
        item = request(1902)
        execution = UUID(int=1902)
        control.admit_execution(request=item, execution_id=execution)
        control.reserve_budget(request=item, execution_id=execution, attempt_number=1)
        before = repository.set_based_operation_snapshot()
        repository.advance_projection(now_ns=clock() + 60 * 1_000_000_000)
        after = repository.set_based_operation_snapshot()
        assert after["expiration_probe_statements"] == before["expiration_probe_statements"] + 1
        assert after["expiration_update_statements"] == before["expiration_update_statements"]
        assert after["expiration_skipped_write_batches"] == (
            before["expiration_skipped_write_batches"] + 1
        )
        assert_projection_matches_ledger(repository.connection, clock() + 60 * 1_000_000_000)
    finally:
        repository.close()


def test_v19_expiration_updates_once_and_missing_scope_rolls_back() -> None:
    clock = Clock()
    repository = SingleWriteCandidateMemoryControl(
        V19_SINGLE_WRITE_ROOT / "validation-01" / "semantic"
    )
    repository.initialize()
    control = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )
    try:
        item = request(1903)
        execution = UUID(int=1903)
        control.admit_execution(request=item, execution_id=execution)
        control.reserve_budget(request=item, execution_id=execution, attempt_number=1)
        repository.advance_projection(now_ns=clock() + 3_600 * 1_000_000_000)
        after_expiration = repository.set_based_operation_snapshot()
        assert after_expiration["expiration_probe_statements"] == 1
        assert after_expiration["expiration_update_statements"] == 1
        assert after_expiration["expiration_sql_statements"] == 2
        assert_projection_matches_ledger(
            repository.connection,
            clock() + 3_600 * 1_000_000_000,
        )

        other = request(1904)
        other_execution = UUID(int=1904)
        clock.advance(3_601)
        control.admit_execution(request=other, execution_id=other_execution)
        control.reserve_budget(
            request=other,
            execution_id=other_execution,
            attempt_number=1,
        )
        repository.connection.execute("DELETE FROM budget_window_totals WHERE scope_class='global'")
        repository.connection.commit()
        before = tuple(
            repository.connection.execute(
                "SELECT scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd "
                "FROM budget_window_totals ORDER BY scope_class,scope_tag"
            ).fetchall()
        )
        with pytest.raises(SafetyControlStorageError):
            repository.advance_projection(now_ns=clock() + 3_600 * 1_000_000_000)
        after = tuple(
            repository.connection.execute(
                "SELECT scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd "
                "FROM budget_window_totals ORDER BY scope_class,scope_tag"
            ).fetchall()
        )
        assert after == before
    finally:
        repository.close()


def test_v19_single_write_sql_shapes_are_fixed_and_parameterized() -> None:
    assert "ON CONFLICT(scope_class,scope_tag) DO UPDATE" in projection.SINGLE_WRITE_UPSERT_SQL
    assert "UPDATE budget_window_totals AS t" in projection.SINGLE_WRITE_UPDATE_SQL
    assert "RETURNING scope_class,scope_tag" in projection.SINGLE_WRITE_UPDATE_SQL
    assert "LIMIT 1" in projection.SINGLE_WRITE_EXPIRATION_PROBE_SQL
    assert "UPDATE budget_window_totals AS t" in projection.SINGLE_WRITE_EXPIRATION_UPDATE_SQL
    assert "NOT EXISTS" in projection.SINGLE_WRITE_EXPIRATION_UPDATE_SQL
