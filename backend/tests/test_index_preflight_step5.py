"""Pure, resource-free contracts for the approved index-only experiment."""

from scripts.f009_step5_index_preflight import (
    CONTROL_INDEXES,
    OBSERVABILITY_INDEXES,
    growth_failures,
    occupied_growth,
)


def test_fixed_candidate_index_counts_and_no_unique_owner() -> None:
    assert len(CONTROL_INDEXES) == 4
    assert len(OBSERVABILITY_INDEXES) == 6
    assert "idx_execution_links_one_dispatch_owner" not in OBSERVABILITY_INDEXES


def test_frozen_growth_limits_are_inclusive_and_combined_excludes_business() -> None:
    assert growth_failures(control=262_144, observability=524_288) == ()
    assert growth_failures(control=262_145, observability=524_288) == (
        "control_growth_exceeded",
        "combined_growth_exceeded",
    )
    assert growth_failures(control=262_144, observability=524_289) == (
        "observability_growth_exceeded",
        "combined_growth_exceeded",
    )


def test_baseline_free_pages_cannot_hide_occupied_growth() -> None:
    assert occupied_growth(40, 4, 100, 0, 4096) == 64 * 4096
    assert occupied_growth(40, 0, 100, 0, 4096) == 60 * 4096
