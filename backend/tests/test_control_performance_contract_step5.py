from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from scripts import f009_step5_benchmark as benchmark

from cyber_town.application import control_performance as performance_contract
from cyber_town.application.control import SafetyControl
from cyber_town.application.control_performance import (
    COMBINED_DB_GROWTH_LIMIT_BYTES,
    CONTROL_DB_GROWTH_LIMIT_BYTES,
    CONTROL_ON_P95_FAILURE_DELTA_MS,
    CONTROL_ON_P95_WARNING_DELTA_MS,
    OBSERVABILITY_DB_GROWTH_LIMIT_BYTES,
    PerformanceRun,
    PerformanceScenario,
    evaluate_performance_gate,
    evaluate_performance_warnings,
    summarize_performance_runs,
)
from cyber_town.application.observability import (
    InMemoryObservabilityRecorder,
    NoOpObservabilityRecorder,
)


def _run(
    *samples: float,
    throughput: float,
    growth: int = 0,
    dispatches: int = 0,
) -> PerformanceRun:
    return PerformanceRun(
        samples_ms=samples,
        throughput_per_second=float(throughput),
        database_growth_bytes=growth,
        provider_dispatch_count=dispatches,
    )


def _memory_summaries(
    *,
    baseline_p95_ms: float,
    recorded_p95_ms: float,
    recorded_p99_ms: float = 4.0,
    baseline_throughput: float = 100.0,
    recorded_throughput: float = 100.0,
) -> dict[PerformanceScenario, performance_contract.PerformanceSummary]:
    return {
        PerformanceScenario.NO_RECORDER_CONTROL: summarize_performance_runs(
            PerformanceScenario.NO_RECORDER_CONTROL,
            tuple(_run(baseline_p95_ms, throughput=baseline_throughput) for _ in range(5)),
        ),
        PerformanceScenario.IN_MEMORY_CONTROL: summarize_performance_runs(
            PerformanceScenario.IN_MEMORY_CONTROL,
            tuple(
                _run(
                    *(recorded_p95_ms for _ in range(98)),
                    recorded_p99_ms,
                    recorded_p99_ms,
                    throughput=recorded_throughput,
                )
                for _ in range(5)
            ),
        ),
    }


def test_v29_in_memory_threshold_constants_are_fixed() -> None:
    assert performance_contract.IN_MEMORY_P95_WARNING_MS == 3.0
    assert performance_contract.IN_MEMORY_P95_FAILURE_MS == 3.5
    assert performance_contract.IN_MEMORY_PAIRED_P95_WARNING_DELTA_MS == 0.5
    assert performance_contract.IN_MEMORY_PAIRED_P95_FAILURE_DELTA_MS == 0.75


def test_v29_in_memory_absolute_p95_warning_and_failure_boundaries() -> None:
    at_warning = _memory_summaries(baseline_p95_ms=3.0, recorded_p95_ms=3.0)
    above_warning = _memory_summaries(baseline_p95_ms=3.001, recorded_p95_ms=3.001)
    at_failure = _memory_summaries(baseline_p95_ms=3.5, recorded_p95_ms=3.5)
    above_failure = _memory_summaries(baseline_p95_ms=3.501, recorded_p95_ms=3.501)

    assert evaluate_performance_warnings(at_warning) == ()
    assert "in_memory_p95_exceeded" not in evaluate_performance_gate(at_warning)
    assert evaluate_performance_warnings(above_warning) == ("in_memory_p95_warning",)
    assert "in_memory_p95_exceeded" not in evaluate_performance_gate(above_warning)
    assert evaluate_performance_warnings(at_failure) == ("in_memory_p95_warning",)
    assert "in_memory_p95_exceeded" not in evaluate_performance_gate(at_failure)
    assert evaluate_performance_warnings(above_failure) == ("in_memory_p95_warning",)
    assert "in_memory_p95_exceeded" in evaluate_performance_gate(above_failure)


def test_v29_in_memory_paired_p95_delta_warning_and_failure_boundaries() -> None:
    at_warning = _memory_summaries(baseline_p95_ms=2.5, recorded_p95_ms=3.0)
    above_warning = _memory_summaries(baseline_p95_ms=2.499, recorded_p95_ms=3.0)
    at_failure = _memory_summaries(baseline_p95_ms=2.25, recorded_p95_ms=3.0)
    above_failure = _memory_summaries(baseline_p95_ms=2.249, recorded_p95_ms=3.0)

    assert evaluate_performance_warnings(at_warning) == ()
    assert "in_memory_p95_regression" not in evaluate_performance_gate(at_warning)
    assert evaluate_performance_warnings(above_warning) == ("in_memory_p95_regression_warning",)
    assert "in_memory_p95_regression" not in evaluate_performance_gate(above_warning)
    assert evaluate_performance_warnings(at_failure) == ("in_memory_p95_regression_warning",)
    assert "in_memory_p95_regression" not in evaluate_performance_gate(at_failure)
    assert evaluate_performance_warnings(above_failure) == ("in_memory_p95_regression_warning",)
    assert "in_memory_p95_regression" in evaluate_performance_gate(above_failure)


def test_v29_keeps_in_memory_p99_and_throughput_gates() -> None:
    at_boundaries = _memory_summaries(
        baseline_p95_ms=2.5,
        recorded_p95_ms=2.5,
        recorded_p99_ms=5.0,
        baseline_throughput=100.0,
        recorded_throughput=80.0,
    )
    above_p99 = _memory_summaries(
        baseline_p95_ms=2.5,
        recorded_p95_ms=2.5,
        recorded_p99_ms=5.001,
    )
    below_throughput = _memory_summaries(
        baseline_p95_ms=2.5,
        recorded_p95_ms=2.5,
        baseline_throughput=100.0,
        recorded_throughput=79.999,
    )

    assert "in_memory_p99_exceeded" not in evaluate_performance_gate(at_boundaries)
    assert "in_memory_throughput_regression" not in evaluate_performance_gate(at_boundaries)
    assert "in_memory_p99_exceeded" in evaluate_performance_gate(above_p99)
    assert "in_memory_throughput_regression" in evaluate_performance_gate(below_throughput)


def test_v29_accepts_v28_memory_result_without_warning() -> None:
    summaries = _memory_summaries(
        baseline_p95_ms=2.7237,
        recorded_p95_ms=2.8436,
        recorded_p99_ms=3.6704,
        baseline_throughput=586.833831,
        recorded_throughput=612.242624,
    )

    assert evaluate_performance_warnings(summaries) == ()
    assert not {
        "in_memory_p95_exceeded",
        "in_memory_p95_regression",
        "in_memory_p99_exceeded",
        "in_memory_throughput_regression",
    }.intersection(evaluate_performance_gate(summaries))


def test_v29_warning_codes_are_sorted_and_missing_pair_does_not_invent_delta() -> None:
    summaries = _memory_summaries(baseline_p95_ms=2.0, recorded_p95_ms=3.1)
    summaries[PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF] = summarize_performance_runs(
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF,
        tuple(_run(50.0, throughput=10.0) for _ in range(5)),
    )
    summaries[PerformanceScenario.FULL_LOOPBACK_CONTROL_ON] = summarize_performance_runs(
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON,
        tuple(_run(176.0, throughput=10.0) for _ in range(5)),
    )
    warnings = evaluate_performance_warnings(summaries)
    missing_pair = {
        PerformanceScenario.IN_MEMORY_CONTROL: summaries[PerformanceScenario.IN_MEMORY_CONTROL]
    }

    assert warnings == tuple(sorted(warnings))
    assert warnings == (
        "control_on_relative_p95_warning",
        "in_memory_p95_regression_warning",
        "in_memory_p95_warning",
    )
    assert evaluate_performance_warnings(missing_pair) == ("in_memory_p95_warning",)
    assert "in_memory_p95_regression" not in evaluate_performance_gate(missing_pair)


def test_v29_core_revalidation_root_is_new_and_registered() -> None:
    assert (
        Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v29-memory-gate-revision")
        == benchmark.CORE_REVALIDATION_ROOT
    )


def test_performance_growth_contract_is_fixed() -> None:
    assert OBSERVABILITY_DB_GROWTH_LIMIT_BYTES == 512 * 1024
    assert CONTROL_DB_GROWTH_LIMIT_BYTES == 256 * 1024
    assert COMBINED_DB_GROWTH_LIMIT_BYTES == 768 * 1024


def test_v26_product_space_manifest_is_exact_and_fresh_pair_bounded() -> None:
    root = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v26-control-space-product-gate2")
    directories, files = benchmark.v26_product_space_manifest(root)

    assert root == benchmark.V26_PRODUCT_SPACE_ROOT
    assert directories[:6] == (
        root,
        root / "tmp",
        root / "pytest-red-01",
        root / "pytest-green-01",
        root / "pytest-regression-01",
        root / "space-gate-01",
    )
    for pair in range(1, 6):
        pair_root = root / f"space-pair-{pair:02d}"
        assert pair_root in directories
        assert pair_root / "baseline-v6" in directories
        assert pair_root / "product-v7" in directories
        for variant in ("baseline-v6", "product-v7"):
            database = pair_root / variant / "control.sqlite3"
            assert database in files
            assert Path(str(database) + "-wal") in files
            assert Path(str(database) + "-shm") in files
    assert root / "summary.json" in files
    assert len(directories) == 21
    assert len(files) == 31


def test_v26_product_space_gate_requires_limit_saving_and_removed_index() -> None:
    assert (
        benchmark._v26_product_space_pair_failures(
            baseline_growth_bytes=266_240,
            product_growth_bytes=258_048,
            product_candidate_index_pages=0,
            baseline_digest="same",
            product_digest="same",
        )
        == ()
    )
    assert benchmark._v26_product_space_pair_failures(
        baseline_growth_bytes=266_240,
        product_growth_bytes=262_145,
        product_candidate_index_pages=1,
        baseline_digest="before",
        product_digest="after",
    ) == (
        "product_control_growth_exceeded",
        "product_index_still_present",
        "product_logical_digest_mismatch",
        "product_space_saving_below_8192",
    )


def test_paired_memory_diagnostic_executes_real_control_methods(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(benchmark, "MEMORY_TRACE_COUNT", 2)
    run = asyncio.run(benchmark._memory_control_run(tmp_path, InMemoryObservabilityRecorder))
    assert len(run.samples_ms) == 2
    assert run.provider_dispatch_count == 2
    assert list(tmp_path.iterdir()) == []


def test_memory_diagnostic_uses_current_composed_provider_fences(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(benchmark, "MEMORY_TRACE_COUNT", 2)
    calls = {
        "legacy_execution_admission": 0,
        "provider_dispatch_admission": 0,
        "provider_success_finalization": 0,
    }
    original_legacy = cast(Callable[..., object], SafetyControl.admit_execution)
    original_admit = cast(Callable[..., Awaitable[object]], SafetyControl.admit_provider_dispatch)
    original_finalize = cast(
        Callable[..., Awaitable[object]], SafetyControl.finalize_provider_success
    )

    def legacy_spy(*args: object, **kwargs: object) -> object:
        calls["legacy_execution_admission"] += 1
        return original_legacy(*args, **kwargs)

    async def admit_spy(*args: object, **kwargs: object) -> object:
        calls["provider_dispatch_admission"] += 1
        return await original_admit(*args, **kwargs)

    async def finalize_spy(*args: object, **kwargs: object) -> object:
        calls["provider_success_finalization"] += 1
        return await original_finalize(*args, **kwargs)

    monkeypatch.setattr(SafetyControl, "admit_execution", legacy_spy)
    monkeypatch.setattr(SafetyControl, "admit_provider_dispatch", admit_spy)
    monkeypatch.setattr(SafetyControl, "finalize_provider_success", finalize_spy)

    run = asyncio.run(benchmark._memory_control_run(tmp_path, NoOpObservabilityRecorder))

    assert run.provider_dispatch_count == 2
    assert calls == {
        "legacy_execution_admission": 0,
        "provider_dispatch_admission": 2,
        "provider_success_finalization": 2,
    }


def test_memory_control_uses_one_connection_for_schema_transactions_and_close(
    tmp_path: Path,
) -> None:
    for _ in range(2):
        repository = benchmark._MemoryControl(tmp_path)
        repository.initialize()
        assert repository._connect() is repository.connection
        assert repository.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='control_execution_intents'"
        ).fetchone() == (1,)
        repository.connection.execute("CREATE TEMP TABLE runner_tx_probe(value INTEGER)")

        with (
            pytest.raises(RuntimeError, match="rollback sentinel"),
            repository._composed_transaction() as connection,
        ):
            assert connection is repository.connection
            nested = repository._connect()
            assert nested is not repository.connection
            nested.execute("BEGIN IMMEDIATE")
            nested.commit()
            connection.execute("INSERT INTO runner_tx_probe VALUES (1)")
            raise RuntimeError("rollback sentinel")

        assert repository.connection.execute("SELECT COUNT(*) FROM runner_tx_probe").fetchone() == (
            0,
        )
        repository.close()
        with pytest.raises(sqlite3.ProgrammingError):
            repository.connection.execute("SELECT 1")
        assert list(tmp_path.rglob("*.sqlite3*")) == []


def test_memory_protocol_is_the_single_warmup_plus_five_fixed_pair_contract() -> None:
    assert benchmark.memory_protocol_config() == {
        "execution_per_run": 1_000,
        "measured_pair_count": 5,
        "pair_order": ["no_recorder_control", "in_memory_control"],
        "percentile_aggregation": "median_of_five_run_level_percentiles",
        "protocol_version": "f-009-memory-control-protocol-v2",
        "stage_attribution_blocks_gate": False,
        "warmup_pair_count": 1,
    }


def test_plain_and_stage_memory_protocols_share_order_without_probe_contamination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(benchmark, "MEMORY_TRACE_COUNT", 2)

    plain = benchmark._paired_memory_protocol(tmp_path, stage_attribution=False)
    attributed = benchmark._paired_memory_protocol(tmp_path, stage_attribution=True)

    for result in (plain, attributed):
        assert len(result.baseline_runs) == 5
        assert len(result.recorded_runs) == 5
        assert len(result.runtime_runs) == 12
        assert [(item["warmup"], item["scenario"]) for item in result.runtime_runs] == [
            (pair_index == 0, scenario)
            for pair_index in range(6)
            for scenario in ("no_recorder_control", "in_memory_control")
        ]
        assert all(
            {
                "gc_collection_delta",
                "process_cpu_ms",
                "thread_count_after",
                "thread_count_before",
                "wall_ms",
            }
            <= set(cast(dict[str, object], item["runtime"]))
            for item in result.runtime_runs
        )

    assert all(item["stage_attribution"] is None for item in plain.runtime_runs)
    assert all(item["gating"] is True for item in plain.runtime_runs)
    assert all(item["gating"] is False for item in attributed.runtime_runs)
    assert all(
        set(cast(dict[str, object], item["stage_attribution"]))
        == set(benchmark.MEMORY_STAGE_ALLOWLIST)
        for item in attributed.runtime_runs
    )
    assert all(
        stage["count"] == 2
        for item in attributed.runtime_runs
        for stage in cast(dict[str, dict[str, int | float]], item["stage_attribution"]).values()
    )
    serialized = json.dumps(attributed.runtime_runs, sort_keys=True)
    assert "Synthetic local benchmark" not in serialized
    assert "bench_player" not in serialized
    assert "scope_tag" not in serialized
    assert NoOpObservabilityRecorder.__name__ not in serialized


def test_combined_growth_excludes_business_and_initial_freelist_reuse() -> None:
    before = {
        "control": {"main_bytes": 40960, "occupied_bytes": 32768},
        "observability": {"main_bytes": 81920, "occupied_bytes": 65536},
        "business": {"main_bytes": 4096, "occupied_bytes": 4096},
    }
    after = {
        "control": {"main_bytes": 45056, "occupied_bytes": 45056},
        "observability": {"main_bytes": 86016, "occupied_bytes": 86016},
        "business": {"main_bytes": 1048576, "occupied_bytes": 1048576},
    }
    assert benchmark._combined_growth(before, after) == 32768


def test_individual_async_latency_is_not_pair_duration_divided_by_two() -> None:
    async def scenario() -> tuple[float, float]:
        async def action() -> None:
            await asyncio.sleep(0.02)

        first, second = await asyncio.gather(
            benchmark._timed_call(action), benchmark._timed_call(action)
        )
        return first, second

    first, second = asyncio.run(scenario())
    assert first >= 18 and second >= 18


def test_memory_throughput_uses_explicit_paired_control_workload() -> None:
    base = summarize_performance_runs(
        PerformanceScenario.NO_RECORDER, tuple(_run(0.01, throughput=1000000) for _ in range(5))
    )
    summaries = {
        PerformanceScenario.NO_RECORDER: base,
        PerformanceScenario.NO_RECORDER_CONTROL: replace(
            base, scenario=PerformanceScenario.NO_RECORDER_CONTROL, throughput_per_second=1000
        ),
        PerformanceScenario.IN_MEMORY_CONTROL: replace(
            base, scenario=PerformanceScenario.IN_MEMORY_CONTROL, throughput_per_second=850
        ),
    }
    assert "in_memory_throughput_regression" not in evaluate_performance_gate(summaries)


def test_five_run_summary_uses_median_run_statistics() -> None:
    runs = tuple(
        _run(0.001, 0.002, 0.003, throughput=250_000 + index, growth=index) for index in range(5)
    )

    summary = summarize_performance_runs(PerformanceScenario.NO_RECORDER, runs)

    assert summary.run_count == 5
    assert summary.sample_count == 15
    assert summary.p50_ms == 0.002
    assert summary.p95_ms == 0.003
    assert summary.p99_ms == 0.003
    assert summary.throughput_per_second == 250_002
    assert summary.database_growth_bytes == 2


def test_gate_accepts_all_frozen_absolute_and_relative_thresholds() -> None:
    summaries = {
        PerformanceScenario.NO_RECORDER_CONTROL: summarize_performance_runs(
            PerformanceScenario.NO_RECORDER_CONTROL,
            tuple(_run(0.5, 1.0, throughput=100_000) for _ in range(5)),
        ),
        PerformanceScenario.NO_RECORDER: summarize_performance_runs(
            PerformanceScenario.NO_RECORDER,
            tuple(_run(0.01, 0.02, throughput=100_000) for _ in range(5)),
        ),
        PerformanceScenario.IN_MEMORY_CONTROL: summarize_performance_runs(
            PerformanceScenario.IN_MEMORY_CONTROL,
            tuple(_run(0.5, 1.0, throughput=85_000) for _ in range(5)),
        ),
        PerformanceScenario.SQLITE_OBSERVABILITY: summarize_performance_runs(
            PerformanceScenario.SQLITE_OBSERVABILITY,
            tuple(_run(90.0, 120.0, throughput=9.0, growth=200_000) for _ in range(5)),
        ),
        PerformanceScenario.SQLITE_PRE_DISPATCH_REJECT: summarize_performance_runs(
            PerformanceScenario.SQLITE_PRE_DISPATCH_REJECT,
            tuple(_run(10.0, 20.0, throughput=20.0, dispatches=0) for _ in range(5)),
        ),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: summarize_performance_runs(
            PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF,
            tuple(_run(100.0, 150.0, throughput=6.0, growth=400_000) for _ in range(5)),
        ),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: summarize_performance_runs(
            PerformanceScenario.FULL_LOOPBACK_CONTROL_ON,
            tuple(
                _run(
                    *(110.0 for _ in range(99)),
                    170.0,
                    throughput=5.0,
                    growth=200_000,
                    dispatches=100,
                )
                for _ in range(5)
            ),
        ),
    }

    assert evaluate_performance_gate(summaries) == ()


def test_control_overhead_warning_and_failure_boundaries_are_fixed() -> None:
    assert CONTROL_ON_P95_WARNING_DELTA_MS == 125.0
    assert CONTROL_ON_P95_FAILURE_DELTA_MS == 140.0

    def summaries(delta_ms: float) -> dict[PerformanceScenario, object]:
        return {
            PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: summarize_performance_runs(
                PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF,
                tuple(_run(100.0, throughput=10.0, dispatches=100) for _ in range(5)),
            ),
            PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: summarize_performance_runs(
                PerformanceScenario.FULL_LOOPBACK_CONTROL_ON,
                tuple(_run(100.0 + delta_ms, throughput=8.0, dispatches=100) for _ in range(5)),
            ),
        }

    at_warning = cast(
        dict[PerformanceScenario, performance_contract.PerformanceSummary],
        summaries(CONTROL_ON_P95_WARNING_DELTA_MS),
    )
    above_warning = cast(
        dict[PerformanceScenario, performance_contract.PerformanceSummary],
        summaries(CONTROL_ON_P95_WARNING_DELTA_MS + 0.001),
    )
    at_failure = cast(
        dict[PerformanceScenario, performance_contract.PerformanceSummary],
        summaries(CONTROL_ON_P95_FAILURE_DELTA_MS),
    )
    above_failure = cast(
        dict[PerformanceScenario, performance_contract.PerformanceSummary],
        summaries(CONTROL_ON_P95_FAILURE_DELTA_MS + 0.001),
    )

    assert evaluate_performance_warnings(at_warning) == ()
    assert "control_on_relative_p95_regression" not in evaluate_performance_gate(at_warning)
    assert evaluate_performance_warnings(above_warning) == ("control_on_relative_p95_warning",)
    assert "control_on_relative_p95_regression" not in evaluate_performance_gate(above_warning)
    assert evaluate_performance_warnings(at_failure) == ("control_on_relative_p95_warning",)
    assert "control_on_relative_p95_regression" not in evaluate_performance_gate(at_failure)
    assert evaluate_performance_warnings(above_failure) == ("control_on_relative_p95_warning",)
    assert "control_on_relative_p95_regression" in evaluate_performance_gate(above_failure)


def test_storage_ab_uses_the_same_control_overhead_warning_and_failure_contract() -> None:
    def summary(
        scenario: PerformanceScenario, p95_ms: float
    ) -> performance_contract.PerformanceSummary:
        return summarize_performance_runs(
            scenario,
            tuple(_run(p95_ms, throughput=8.0, dispatches=100) for _ in range(5)),
        )

    warning = {
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: summary(
            PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF, 100.0
        ),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: summary(
            PerformanceScenario.FULL_LOOPBACK_CONTROL_ON, 225.001
        ),
    }
    failure = dict(warning)
    failure[PerformanceScenario.FULL_LOOPBACK_CONTROL_ON] = summary(
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON, 240.001
    )

    assert benchmark._storage_ab_warning_codes(warning) == ("control_on_relative_p95_warning",)
    assert benchmark._storage_ab_failure_codes(warning) == ()
    assert benchmark._storage_ab_warning_codes(failure) == ("control_on_relative_p95_warning",)
    assert benchmark._storage_ab_failure_codes(failure) == ("control_on_relative_p95_regression",)


def test_gate_emits_stable_failure_codes_without_timing_payloads() -> None:
    summaries = {
        PerformanceScenario.NO_RECORDER: summarize_performance_runs(
            PerformanceScenario.NO_RECORDER,
            tuple(_run(0.2, throughput=10) for _ in range(5)),
        )
    }

    assert evaluate_performance_gate(summaries) == (
        "missing_full_loopback_control_off",
        "missing_full_loopback_control_on",
        "missing_in_memory_control",
        "missing_no_recorder_control",
        "missing_sqlite_observability",
        "missing_sqlite_pre_dispatch_reject",
        "no_recorder_p95_exceeded",
        "no_recorder_p99_exceeded",
    )


def test_runtime_default_boundary_uses_noop_observability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, bool, bool]] = []
    expected = _run(100.0, throughput=5.0, dispatches=1)

    async def fake_loopback(
        run_root: Path, *, control_on: bool, sqlite_observability: bool = True
    ) -> PerformanceRun:
        calls.append((run_root, control_on, sqlite_observability))
        return expected

    monkeypatch.setattr(benchmark, "_loopback_run", fake_loopback)

    actual = asyncio.run(benchmark._runtime_default_loopback_run(Path("synthetic-runtime")))

    assert actual is expected
    assert calls == [(Path("synthetic-runtime"), True, False)]


def test_runtime_default_boundary_gate_uses_frozen_http_thresholds() -> None:
    passing = _run(
        *(100.0 for _ in range(94)),
        *(250.0 for _ in range(6)),
        throughput=4.0,
        dispatches=100,
    )
    assert benchmark._runtime_boundary_failure_codes(passing) == ()

    failing = _run(
        *(100.0 for _ in range(94)),
        *(251.0 for _ in range(4)),
        *(401.0 for _ in range(2)),
        throughput=3.9,
        dispatches=99,
    )
    assert benchmark._runtime_boundary_failure_codes(failing) == (
        "runtime_default_dispatch_ownership_failed",
        "runtime_default_p95_exceeded",
        "runtime_default_p99_exceeded",
        "runtime_default_throughput_below_minimum",
    )


def test_runtime_boundary_manifest_excludes_observability_sqlite() -> None:
    directories, files = benchmark.runtime_boundary_manifest(benchmark.V11_ROOT)

    assert directories == (
        benchmark.V11_ROOT,
        benchmark.V11_ROOT / "tmp",
        benchmark.V11_ROOT / "runtime-default-01",
    )
    assert files == (
        benchmark.V11_ROOT / "runtime-default-01" / "business.sqlite3",
        benchmark.V11_ROOT / "runtime-default-01" / "business.sqlite3-wal",
        benchmark.V11_ROOT / "runtime-default-01" / "business.sqlite3-shm",
        benchmark.V11_ROOT / "runtime-default-01" / "control.sqlite3",
        benchmark.V11_ROOT / "runtime-default-01" / "control.sqlite3-wal",
        benchmark.V11_ROOT / "runtime-default-01" / "control.sqlite3-shm",
        benchmark.V11_ROOT / "runtime-default-01" / "performance-summary.json",
    )
    assert all("observability" not in path.name for path in files)


def test_runtime_default_control_growth_uses_the_frozen_control_limit() -> None:
    summary = summarize_performance_runs(
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON,
        tuple(
            _run(
                100.0,
                throughput=5.0,
                growth=CONTROL_DB_GROWTH_LIMIT_BYTES + 1,
                dispatches=1,
            )
            for _ in range(5)
        ),
    )

    assert "runtime_default_control_database_growth_exceeded" in evaluate_performance_gate(
        {PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: summary}
    )


def test_three_sqlite_diagnostic_is_reported_but_never_blocks_the_core_gate() -> None:
    runs = tuple(
        _run(
            *(100.0 for _ in range(94)),
            *(300.0 for _ in range(4)),
            *(500.0 for _ in range(2)),
            throughput=3.0,
            growth=800_000,
            dispatches=101,
        )
        for _ in range(5)
    )
    summary = summarize_performance_runs(
        PerformanceScenario.FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC,
        runs,
    )

    assert performance_contract.evaluate_three_sqlite_diagnostic(summary) == (
        "three_sqlite_combined_growth_exceeded",
        "three_sqlite_dispatch_ownership_failed",
        "three_sqlite_p95_exceeded",
        "three_sqlite_p99_exceeded",
        "three_sqlite_throughput_below_minimum",
    )
    blocking_failures = evaluate_performance_gate(
        {PerformanceScenario.FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC: summary}
    )
    assert all("three_sqlite" not in failure for failure in blocking_failures)
    assert "missing_full_loopback_three_sqlite_diagnostic" not in blocking_failures


def test_gate_boundary_loopbacks_use_noop_for_default_and_sqlite_only_for_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, bool, bool, str]] = []

    def fake_loopbacks(
        root: Path,
        *,
        control_on: bool,
        sqlite_observability: bool = True,
        label: str | None = None,
    ) -> tuple[PerformanceRun, ...]:
        calls.append((root, control_on, sqlite_observability, label or ""))
        return tuple(_run(1.0, throughput=10.0) for _ in range(5))

    monkeypatch.setattr(benchmark, "_loopback_runs", fake_loopbacks)

    runs = benchmark._gate_boundary_loopback_runs(Path("synthetic-matrix"))

    assert calls == [
        (Path("synthetic-matrix"), False, False, "off"),
        (Path("synthetic-matrix"), True, False, "on"),
        (Path("synthetic-matrix"), True, True, "three-sqlite"),
    ]
    assert tuple(runs) == (
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF,
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON,
        PerformanceScenario.FULL_LOOPBACK_THREE_SQLITE_DIAGNOSTIC,
    )


def test_execution_intent_gate_uses_registered_v24_surface_and_noop_observability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "performance-v24-execution-intent-product"
    (root / "tmp").mkdir(parents=True)
    (root / benchmark.V24_TCP_DIRECTORY).mkdir()
    calls: list[tuple[Path, bool, bool, str]] = []

    def fake_loopbacks(
        run_root: Path,
        *,
        control_on: bool,
        sqlite_observability: bool = True,
        label: str | None = None,
        request_id_seed: int | None = None,
    ) -> tuple[PerformanceRun, ...]:
        del request_id_seed
        calls.append((run_root, control_on, sqlite_observability, label or ""))
        return tuple(
            _run(*(1.0 for _ in range(100)), throughput=100.0, dispatches=100) for _ in range(5)
        )

    monkeypatch.setattr(benchmark, "V24_ROOT", root)
    monkeypatch.setattr(benchmark, "_loopback_runs", fake_loopbacks)
    monkeypatch.setattr(benchmark, "_runtime_boundary_database_audit", lambda _path: {})
    monkeypatch.setattr(benchmark, "_storage_ab_audit_failure_codes", lambda *_args, **_kwargs: ())

    assert benchmark._run_execution_intent_matrix(root.resolve()) == 0
    assert calls == [
        (root / benchmark.V24_TCP_DIRECTORY, False, False, "off"),
        (root / benchmark.V24_TCP_DIRECTORY, True, False, "on"),
    ]
    result = json.loads(
        (root / benchmark.V24_TCP_DIRECTORY / "performance-summary.json").read_text()
    )
    assert result["run_count"] == 5
    assert result["warmup_runs"] == 1
    assert result["gate_boundary"] == "v24_execution_intent_real_tcp"
    assert not any("observability.sqlite3" in str(path) for path in root.rglob("*"))


def test_gate_boundary_matrix_manifest_matches_the_registered_resource_set() -> None:
    directories, files = benchmark.gate_boundary_matrix_manifest(benchmark.CORE_REVALIDATION_ROOT)

    assert len(directories) == 43
    assert len(files) == 199
    assert benchmark.CORE_REVALIDATION_ROOT != benchmark.V11_ROOT
    assert directories[0] == benchmark.CORE_REVALIDATION_ROOT / "full-matrix-01"
    assert files[0] == directories[0] / "performance-summary.json"
    assert not any(
        "observability.sqlite3" in path.name
        for path in files
        if "loopback-off-" in str(path) or "loopback-on-" in str(path)
    )


def test_storage_ab_manifest_is_exact_and_excludes_observability() -> None:
    directories, files = benchmark.storage_ab_manifest(benchmark.V13_E_ROOT)

    assert len(directories) == 14
    assert len(files) == 73
    assert directories[:2] == (
        benchmark.V13_E_ROOT,
        benchmark.V13_E_ROOT / "tmp",
    )
    assert directories[2:] == tuple(
        benchmark.V13_E_ROOT / f"loopback-{mode}-{index}"
        for mode in ("off", "on")
        for index in range(benchmark.RUN_COUNT + 1)
    )
    assert files[-1] == benchmark.V13_E_ROOT / "performance-summary.json"
    assert not any("observability" in path.name for path in files)


def test_storage_ab_config_digest_excludes_only_the_data_root() -> None:
    config = benchmark._storage_ab_config()

    assert config == {
        "concurrency": 2,
        "executions_per_run": 100,
        "fake_provider": True,
        "observability_mode": "noop",
        "request_id_seed": 13_000,
        "run_count": 5,
        "scenario_order": ["control_off", "control_on"],
        "schema_version": 1,
        "synchronous": "full",
        "transport": "tcp_independent_client_process",
        "wal": True,
        "warmup_runs": 1,
    }
    assert "root" not in json.dumps(config, sort_keys=True)
    assert benchmark._storage_ab_config_digest() == benchmark._storage_ab_config_digest()
    assert len(benchmark._storage_ab_config_digest()) == 64


def test_storage_ab_root_validation_rejects_unregistered_or_existing_surface(
    tmp_path: Path,
) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    (approved / "tmp").mkdir()

    benchmark._validate_storage_ab_root(approved, approved)

    with pytest.raises(ValueError, match="not approved"):
        benchmark._validate_storage_ab_root(approved, tmp_path / "different")

    (approved / "business.sqlite3").touch()
    with pytest.raises(ValueError, match="not fresh"):
        benchmark._validate_storage_ab_root(approved, approved)


def test_storage_ab_root_validation_rejects_reparse_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    (approved / "tmp").mkdir()
    monkeypatch.setattr(
        benchmark,
        "_is_reparse_point",
        lambda path: path == approved,
    )

    with pytest.raises(ValueError, match="reparse"):
        benchmark._validate_storage_ab_root(approved, approved)


def test_storage_ab_temp_root_is_media_local_and_restores_process_state(
    tmp_path: Path,
) -> None:
    media_root = tmp_path / "media"
    (media_root / "tmp").mkdir(parents=True)
    old_temp = os.environ.get("TEMP")
    old_tmp = os.environ.get("TMP")
    old_tempdir = tempfile.tempdir

    with benchmark._storage_ab_temp_root(media_root):
        assert os.environ["TEMP"] == str(media_root / "tmp")
        assert os.environ["TMP"] == str(media_root / "tmp")
        assert tempfile.gettempdir() == str(media_root / "tmp")

    assert os.environ.get("TEMP") == old_temp
    assert os.environ.get("TMP") == old_tmp
    assert tempfile.tempdir == old_tempdir


def test_storage_ab_runs_fix_workload_order_ids_and_noop_observability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, bool, bool, str, int | None]] = []
    runs = tuple(_run(1.0, throughput=10.0, dispatches=100) for _ in range(5))

    def fake_loopbacks(
        root: Path,
        *,
        control_on: bool,
        sqlite_observability: bool = True,
        label: str | None = None,
        request_id_seed: int | None = None,
    ) -> tuple[PerformanceRun, ...]:
        calls.append((root, control_on, sqlite_observability, label or "", request_id_seed))
        return runs

    monkeypatch.setattr(benchmark, "_loopback_runs", fake_loopbacks)

    actual = benchmark._storage_ab_runs(Path("synthetic-media"))

    assert actual == {
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: runs,
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: runs,
    }
    assert calls == [
        (Path("synthetic-media"), False, False, "off", 13_000),
        (Path("synthetic-media"), True, False, "on", 13_000),
    ]


def test_storage_ab_pair_validation_rejects_workload_or_sample_mismatch() -> None:
    valid_run = _run(*(1.0 for _ in range(100)), throughput=10.0, dispatches=100)
    valid = {
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: tuple(valid_run for _ in range(5)),
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: tuple(valid_run for _ in range(5)),
    }
    benchmark._validate_storage_ab_pair(valid, valid)

    short_run = _run(*(1.0 for _ in range(99)), throughput=10.0, dispatches=99)
    mismatched = dict(valid)
    mismatched[PerformanceScenario.FULL_LOOPBACK_CONTROL_ON] = tuple(short_run for _ in range(5))
    with pytest.raises(ValueError, match="workload mismatch"):
        benchmark._validate_storage_ab_pair(valid, mismatched)


def test_storage_ab_gate_and_conclusion_keep_in_memory_blocker_open() -> None:
    passing_off = summarize_performance_runs(
        PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF,
        tuple(_run(100.0, throughput=10.0, dispatches=100) for _ in range(5)),
    )
    passing_on = summarize_performance_runs(
        PerformanceScenario.FULL_LOOPBACK_CONTROL_ON,
        tuple(_run(120.0, throughput=8.0, growth=200_000, dispatches=100) for _ in range(5)),
    )
    assert (
        benchmark._storage_ab_failure_codes(
            {
                PerformanceScenario.FULL_LOOPBACK_CONTROL_OFF: passing_off,
                PerformanceScenario.FULL_LOOPBACK_CONTROL_ON: passing_on,
            }
        )
        == ()
    )
    assert benchmark._storage_ab_conclusion((), ("full_loopback_p95_exceeded",)) == (
        "storage_media_route_not_supported"
    )
    assert (
        benchmark._storage_ab_conclusion(
            ("full_loopback_p95_exceeded",),
            (),
            e_p95_runs=(300.0, 301.0, 302.0, 303.0, 304.0),
            c_p95_runs=(120.0, 121.0, 122.0, 123.0, 124.0),
        )
        == "runtime_data_root_candidate_supported"
    )
    assert benchmark._storage_ab_conclusion((), ()) == "environment_variance_requires_control"
    assert "in_memory_blocker_open" in benchmark._storage_ab_result_boundary()
