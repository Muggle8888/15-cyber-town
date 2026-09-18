from __future__ import annotations

from pathlib import Path

import pytest
from scripts.f009_step5_control_space_preflight import (
    CANDIDATE_INDEX,
    DROP_CANDIDATE_SQL,
    QUERY_PLAN_FIX_ROOT,
    SPACE_LIMIT_BYTES,
    SpaceSnapshot,
    evaluate_query_plan_probe,
    evaluate_space_pair,
    manifest,
    query_plan_fix_manifest,
    sanitize_query_plan,
    validate_candidate_sql,
)


def test_manifest_is_exact_and_bounded() -> None:
    root = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v26-control-space-index")
    directories, files = manifest(root)

    assert directories[:3] == (
        root,
        root / "pytest-red-01",
        root / "pytest-green-01",
    )
    assert root / "pytest-green-02" in directories
    assert root / "pytest-green-03" in directories
    assert root / "pytest-green-04" in directories
    assert root / "query-plan-01" in directories
    assert root / "history-10000-candidate" in directories
    assert root / "space-pair-05" / "candidate" in directories
    assert files == (root / "summary.json",)
    assert len(directories) == 29


def test_candidate_sql_is_exact_and_rejects_scope_expansion() -> None:
    assert CANDIDATE_INDEX == "idx_budget_owners_npc"
    assert DROP_CANDIDATE_SQL == "DROP INDEX idx_budget_owners_npc"
    validate_candidate_sql(DROP_CANDIDATE_SQL)

    for invalid in (
        "DROP INDEX idx_budget_owners_player",
        "DROP INDEX idx_budget_owners_npc; DROP INDEX idx_budget_owners_player",
        "DROP TABLE budget_execution_owners",
    ):
        with pytest.raises(ValueError, match="candidate SQL"):
            validate_candidate_sql(invalid)


def test_space_gate_requires_absolute_limit_and_two_page_saving() -> None:
    baseline = SpaceSnapshot(
        initial_occupied_bytes=100_000,
        final_occupied_bytes=370_336,
        initial_freelist_pages=3,
        final_freelist_pages=0,
        candidate_index_pages=2,
    )
    passing = SpaceSnapshot(
        initial_occupied_bytes=100_000,
        final_occupied_bytes=362_144,
        initial_freelist_pages=5,
        final_freelist_pages=0,
        candidate_index_pages=0,
    )

    assert SPACE_LIMIT_BYTES == 262_144
    assert evaluate_space_pair(baseline, passing) == ()

    insufficient_saving = SpaceSnapshot(
        initial_occupied_bytes=100_000,
        final_occupied_bytes=366_240,
        initial_freelist_pages=5,
        final_freelist_pages=0,
        candidate_index_pages=0,
    )
    assert evaluate_space_pair(baseline, insufficient_saving) == (
        "candidate_occupied_growth_exceeded",
        "candidate_occupied_saving_below_8192",
    )


def test_space_gate_does_not_use_main_file_or_freelist_as_passing_signal() -> None:
    baseline = SpaceSnapshot(0, 270_336, 100, 0, 2)
    candidate = SpaceSnapshot(0, 270_336, 0, 100, 0)

    assert evaluate_space_pair(baseline, candidate) == (
        "candidate_occupied_growth_exceeded",
        "candidate_occupied_saving_below_8192",
    )


def test_query_plan_sanitizer_rejects_scope_and_payload_values() -> None:
    assert sanitize_query_plan(("SEARCH o USING INDEX idx_budget_owners_npc",)) == (
        "SEARCH o USING INDEX idx_budget_owners_npc",
    )

    for sentinel in (
        "bench_player_001",
        "Synthetic local benchmark",
        "a" * 64,
        "api-key-synthetic-secret",
    ):
        with pytest.raises(ValueError, match="query plan metadata"):
            sanitize_query_plan((sentinel,))


def test_query_plan_fix_manifest_is_exact_and_separate_from_old_v26_root() -> None:
    root = Path(
        r"E:\Agent\cyber-town-f009-step5-tests\performance-v26-control-space-query-plan-fix"
    )
    directories, files = query_plan_fix_manifest(root)

    assert root == QUERY_PLAN_FIX_ROOT
    assert directories == (
        root,
        root / "tmp",
        root / "pytest-red-01",
        root / "pytest-green-01",
        root / "query-plan-01",
        root / "query-plan-01" / "baseline",
        root / "query-plan-01" / "candidate",
    )
    assert files == (root / "summary.json",)
    assert all("performance-v26-control-space-index" not in str(path) for path in directories)


def test_query_plan_gate_requires_committed_drop_visible_from_fresh_connection() -> None:
    baseline = {
        "sqlite_master_has_candidate": True,
        "index_list_has_candidate": True,
        "candidate_index_pages": 2,
        "normal": {"owner_by_execution": ("SEARCH owner USING PRIMARY KEY",)},
        "active_npc": ("SEARCH owner USING INDEX idx_budget_owners_npc",),
    }
    candidate = {
        "sqlite_master_has_candidate": False,
        "index_list_has_candidate": False,
        "candidate_index_pages": 0,
        "normal": {"owner_by_execution": ("SEARCH owner USING PRIMARY KEY",)},
        "active_npc": ("SCAN owner",),
    }

    assert evaluate_query_plan_probe(baseline, candidate) == ()

    stale = {**candidate, "active_npc": ("SEARCH owner USING INDEX idx_budget_owners_npc",)}
    assert evaluate_query_plan_probe(baseline, stale) == (
        "candidate_query_plan_retained_dropped_index",
    )


@pytest.mark.parametrize(
    ("field", "value", "failure"),
    (
        ("sqlite_master_has_candidate", True, "candidate_sqlite_master_retained_index"),
        ("index_list_has_candidate", True, "candidate_index_list_retained_index"),
        ("candidate_index_pages", 1, "candidate_dbstat_retained_index_pages"),
    ),
)
def test_query_plan_gate_rejects_each_persisted_index_surface(
    field: str,
    value: object,
    failure: str,
) -> None:
    baseline = {
        "sqlite_master_has_candidate": True,
        "index_list_has_candidate": True,
        "candidate_index_pages": 2,
        "normal": {"projection_totals": ("SEARCH totals USING PRIMARY KEY",)},
        "active_npc": ("SEARCH owner USING INDEX idx_budget_owners_npc",),
    }
    candidate = {
        "sqlite_master_has_candidate": False,
        "index_list_has_candidate": False,
        "candidate_index_pages": 0,
        "normal": {"projection_totals": ("SEARCH totals USING PRIMARY KEY",)},
        "active_npc": ("SCAN owner",),
    }
    candidate[field] = value

    assert evaluate_query_plan_probe(baseline, candidate) == (failure,)


def test_query_plan_gate_rejects_normal_plan_regression() -> None:
    baseline = {
        "sqlite_master_has_candidate": True,
        "index_list_has_candidate": True,
        "candidate_index_pages": 2,
        "normal": {"expiration_join": ("SEARCH reservation USING quota index",)},
        "active_npc": ("SEARCH owner USING INDEX idx_budget_owners_npc",),
    }
    candidate = {
        "sqlite_master_has_candidate": False,
        "index_list_has_candidate": False,
        "candidate_index_pages": 0,
        "normal": {"expiration_join": ("SCAN reservation",)},
        "active_npc": ("SCAN owner",),
    }

    assert evaluate_query_plan_probe(baseline, candidate) == (
        "candidate_normal_query_plan_regressed",
    )
