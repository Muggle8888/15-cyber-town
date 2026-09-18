"""Stable local performance summaries and frozen F-009 gate thresholds."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from enum import StrEnum

OBSERVABILITY_DB_GROWTH_LIMIT_BYTES = 512 * 1024
CONTROL_DB_GROWTH_LIMIT_BYTES = 256 * 1024
COMBINED_DB_GROWTH_LIMIT_BYTES = 768 * 1024
IN_MEMORY_P95_WARNING_MS = 3.0
IN_MEMORY_P95_FAILURE_MS = 3.5
IN_MEMORY_PAIRED_P95_WARNING_DELTA_MS = 0.5
IN_MEMORY_PAIRED_P95_FAILURE_DELTA_MS = 0.75
CONTROL_ON_P95_WARNING_DELTA_MS = 125.0
CONTROL_ON_P95_FAILURE_DELTA_MS = 140.0


class PerformanceScenario(StrEnum):
    NO_RECORDER = "no_recorder"
    NO_RECORDER_CONTROL = "no_recorder_control"
    IN_MEMORY_CONTROL = "in_memory_control"
    SQLITE_OBSERVABILITY = "sqlite_observability"
    SQLITE_PRE_DISPATCH_REJECT = "sqlite_pre_dispatch_reject"
    FULL_LOOPBACK_CONTROL_OFF = "full_loopback_control_off"
    FULL_LOOPBACK_CONTROL_ON = "full_loopback_control_on"
    FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC = "full_loopback_three_sqlite_diagnostic"


BLOCKING_PERFORMANCE_SCENARIOS = frozenset(
    scenario
    for scenario in PerformanceScenario
    if scenario is not PerformanceScenario.FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC
)


@dataclass(frozen=True, slots=True)
class PerformanceRun:
    samples_ms: tuple[float, ...]
    throughput_per_second: float
    database_growth_bytes: int = 0
    provider_dispatch_count: int = 0

    def __post_init__(self) -> None:
        if not self.samples_ms or any(
            not isinstance(sample, float) or not math.isfinite(sample) or sample < 0
            for sample in self.samples_ms
        ):
            raise ValueError("Performance samples are invalid")
        if (
            not isinstance(self.throughput_per_second, float)
            or not math.isfinite(self.throughput_per_second)
            or self.throughput_per_second <= 0
        ):
            raise ValueError("Performance throughput is invalid")
        for value, label in (
            (self.database_growth_bytes, "database growth"),
            (self.provider_dispatch_count, "provider dispatch count"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"Performance {label} is invalid")


@dataclass(frozen=True, slots=True)
class PerformanceSummary:
    scenario: PerformanceScenario
    run_count: int
    sample_count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    throughput_per_second: float
    database_growth_bytes: int
    provider_dispatch_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario.value,
            "run_count": self.run_count,
            "sample_count": self.sample_count,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "throughput_per_second": self.throughput_per_second,
            "database_growth_bytes": self.database_growth_bytes,
            "provider_dispatch_count": self.provider_dispatch_count,
        }


def _percentile(samples: tuple[float, ...], quantile: float) -> float:
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def _rounded(value: float) -> float:
    return round(value, 6)


def summarize_performance_runs(
    scenario: PerformanceScenario,
    runs: tuple[PerformanceRun, ...],
) -> PerformanceSummary:
    """Return medians of five independent run-level statistics."""

    if not isinstance(scenario, PerformanceScenario):
        raise TypeError("Performance scenario is invalid")
    if (
        not isinstance(runs, tuple)
        or len(runs) != 5
        or any(not isinstance(run, PerformanceRun) for run in runs)
    ):
        raise ValueError("Exactly five performance runs are required")
    p50_values = tuple(_percentile(run.samples_ms, 0.50) for run in runs)
    p95_values = tuple(_percentile(run.samples_ms, 0.95) for run in runs)
    p99_values = tuple(_percentile(run.samples_ms, 0.99) for run in runs)
    return PerformanceSummary(
        scenario=scenario,
        run_count=len(runs),
        sample_count=sum(len(run.samples_ms) for run in runs),
        p50_ms=_rounded(statistics.median(p50_values)),
        p95_ms=_rounded(statistics.median(p95_values)),
        p99_ms=_rounded(statistics.median(p99_values)),
        throughput_per_second=_rounded(
            statistics.median(run.throughput_per_second for run in runs)
        ),
        database_growth_bytes=round(statistics.median(run.database_growth_bytes for run in runs)),
        provider_dispatch_count=round(
            statistics.median(run.provider_dispatch_count for run in runs)
        ),
    )


def evaluate_performance_gate(
    summaries: dict[PerformanceScenario, PerformanceSummary],
) -> tuple[str, ...]:
    """Evaluate fixed absolute and relative thresholds using stable failure codes."""

    if not isinstance(summaries, dict) or any(
        not isinstance(key, PerformanceScenario) or not isinstance(value, PerformanceSummary)
        for key, value in summaries.items()
    ):
        raise TypeError("Performance summary mapping is invalid")
    failures: list[str] = []
    for scenario in BLOCKING_PERFORMANCE_SCENARIOS:
        if scenario not in summaries:
            failures.append(f"missing_{scenario.value}")

    no_recorder = summaries.get(PerformanceScenario.NO_RECORDER)
    if no_recorder is not None:
        if no_recorder.p95_ms > 0.050:
            failures.append("no_recorder_p95_exceeded")
        if no_recorder.p99_ms > 0.100:
            failures.append("no_recorder_p99_exceeded")

    in_memory = summaries.get(PerformanceScenario.IN_MEMORY_CONTROL)
    paired_no_recorder = summaries.get(PerformanceScenario.NO_RECORDER_CONTROL)
    if in_memory is not None:
        if in_memory.p95_ms > IN_MEMORY_P95_FAILURE_MS:
            failures.append("in_memory_p95_exceeded")
        if in_memory.p99_ms > 5.0:
            failures.append("in_memory_p99_exceeded")
        if (
            paired_no_recorder is not None
            and in_memory.p95_ms - paired_no_recorder.p95_ms > IN_MEMORY_PAIRED_P95_FAILURE_DELTA_MS
        ):
            failures.append("in_memory_p95_regression")
        if (
            paired_no_recorder is not None
            and in_memory.throughput_per_second < paired_no_recorder.throughput_per_second * 0.80
        ):
            failures.append("in_memory_throughput_regression")

    sqlite_observability = summaries.get(PerformanceScenario.SQLITE_OBSERVABILITY)
    if sqlite_observability is not None:
        if sqlite_observability.p95_ms > 150.0:
            failures.append("sqlite_observability_p95_exceeded")
        if sqlite_observability.p99_ms > 200.0:
            failures.append("sqlite_observability_p99_exceeded")
        if sqlite_observability.throughput_per_second < 8.0:
            failures.append("sqlite_observability_throughput_below_minimum")
        if sqlite_observability.database_growth_bytes > OBSERVABILITY_DB_GROWTH_LIMIT_BYTES:
            failures.append("observability_database_growth_exceeded")

    reject = summaries.get(PerformanceScenario.SQLITE_PRE_DISPATCH_REJECT)
    if reject is not None:
        if reject.p95_ms > 50.0:
            failures.append("pre_dispatch_reject_p95_exceeded")
        if reject.provider_dispatch_count != 0:
            failures.append("pre_dispatch_reject_dispatched")
        if reject.database_growth_bytes > CONTROL_DB_GROWTH_LIMIT_BYTES:
            failures.append("control_database_growth_exceeded")

    control_off = summaries.get(PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF)
    control_on = summaries.get(PerformanceScenario.FULL_LOOPBACK_CONTROL_ON)
    if control_on is not None:
        if control_on.p95_ms > 250.0:
            failures.append("full_loopback_p95_exceeded")
        if control_on.p99_ms > 400.0:
            failures.append("full_loopback_p99_exceeded")
        if control_on.throughput_per_second < 4.0:
            failures.append("full_loopback_throughput_below_minimum")
        if control_on.database_growth_bytes > CONTROL_DB_GROWTH_LIMIT_BYTES:
            failures.append("runtime_default_control_database_growth_exceeded")
        median_samples_per_run = control_on.sample_count // control_on.run_count
        if control_on.provider_dispatch_count > median_samples_per_run * 2:
            failures.append("full_loopback_retry_amplification")
    if (
        control_off is not None
        and control_on is not None
        and control_on.p95_ms - control_off.p95_ms > CONTROL_ON_P95_FAILURE_DELTA_MS
    ):
        failures.append("control_on_relative_p95_regression")
    return tuple(sorted(failures))


def evaluate_performance_warnings(
    summaries: dict[PerformanceScenario, PerformanceSummary],
) -> tuple[str, ...]:
    """Return non-blocking warnings for the frozen local performance profile."""

    if not isinstance(summaries, dict) or any(
        not isinstance(key, PerformanceScenario) or not isinstance(value, PerformanceSummary)
        for key, value in summaries.items()
    ):
        raise TypeError("Performance summary mapping is invalid")
    warnings: list[str] = []
    in_memory = summaries.get(PerformanceScenario.IN_MEMORY_CONTROL)
    paired_no_recorder = summaries.get(PerformanceScenario.NO_RECORDER_CONTROL)
    if in_memory is not None:
        if in_memory.p95_ms > IN_MEMORY_P95_WARNING_MS:
            warnings.append("in_memory_p95_warning")
        if (
            paired_no_recorder is not None
            and in_memory.p95_ms - paired_no_recorder.p95_ms > IN_MEMORY_PAIRED_P95_WARNING_DELTA_MS
        ):
            warnings.append("in_memory_p95_regression_warning")
    control_off = summaries.get(PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF)
    control_on = summaries.get(PerformanceScenario.FULL_LOOPBACK_CONTROL_ON)
    if (
        control_off is not None
        and control_on is not None
        and control_on.p95_ms - control_off.p95_ms > CONTROL_ON_P95_WARNING_DELTA_MS
    ):
        warnings.append("control_on_relative_p95_warning")
    return tuple(sorted(warnings))


def evaluate_three_sqlite_diagnostic(summary: PerformanceSummary) -> tuple[str, ...]:
    """Report frozen three-SQLite trends without blocking the default runtime gate."""

    if (
        not isinstance(summary, PerformanceSummary)
        or summary.scenario is not PerformanceScenario.FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC
    ):
        raise TypeError("Three-SQLite diagnostic summary is invalid")
    failures = []
    if summary.p95_ms > 250.0:
        failures.append("three_sqlite_p95_exceeded")
    if summary.p99_ms > 400.0:
        failures.append("three_sqlite_p99_exceeded")
    if summary.throughput_per_second < 4.0:
        failures.append("three_sqlite_throughput_below_minimum")
    if summary.database_growth_bytes > COMBINED_DB_GROWTH_LIMIT_BYTES:
        failures.append("three_sqlite_combined_growth_exceeded")
    median_samples_per_run = summary.sample_count // summary.run_count
    if summary.provider_dispatch_count != median_samples_per_run:
        failures.append("three_sqlite_dispatch_ownership_failed")
    return tuple(sorted(failures))
