from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from cyber_town.application.control_evaluation import (
    CONTROL_EVALUATOR_VERSION,
    ControlEvaluationDimension,
    ControlEvaluationFailureCode,
    ControlEvaluationObservation,
    build_control_baseline_observations,
    evaluate_control_fixture,
    load_control_evaluation_fixture,
)
from cyber_town.domain.persona import load_bundled_personas

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "f009_control_evaluation_v1.json"
SYNTHETIC_KEY = b"f009-step5-synthetic-evaluation-key"

EXPECTED_DIMENSIONS = set(ControlEvaluationDimension)
REPORT_KEYS = {
    "evaluator_version",
    "fixture_version",
    "schema_version",
    "case_count",
    "passed_count",
    "failed_count",
    "unauthorized_provider_dispatch_count",
    "scope_leak_count",
    "forbidden_content_hit_count",
    "duplicate_charge_count",
    "duplicate_business_write_count",
    "rate_limit_bypass_count",
    "retry_amplification_count",
    "breaker_transition_consistency_ppm",
    "budget_attribution_consistency_ppm",
    "nonzero_cost_case_count",
    "verdicts",
    "canonical_digest",
}


def test_fixture_is_strict_versioned_and_covers_all_step5_dimensions() -> None:
    fixture = load_control_evaluation_fixture(FIXTURE_PATH)

    assert fixture.schema_version == 1
    assert fixture.fixture_version == "f-009-control-evaluation-fixture-v1"
    assert len(fixture.cases) == 25
    assert {case.dimension for case in fixture.cases} == EXPECTED_DIMENSIONS
    assert len({case.case_id for case in fixture.cases}) == len(fixture.cases)


def test_fixture_locks_three_personas_without_system_prompt_text() -> None:
    fixture = load_control_evaluation_fixture(FIXTURE_PATH)
    personas = load_bundled_personas()

    assert {(item.npc_id, item.version) for item in fixture.personas} == {
        ("neon_guide", "nia-v1"),
        ("signal_archivist", "ivo-v1"),
        ("night_courier", "rhea-v1"),
    }
    raw_fixture = FIXTURE_PATH.read_text(encoding="utf-8")
    for contract in fixture.personas:
        persona = personas[contract.npc_id]
        assert contract.version == persona.version
        assert contract.content_sha256 == persona.content_sha256
        assert persona.system_prompt not in raw_fixture


def test_baseline_report_meets_all_step5_control_thresholds() -> None:
    fixture = load_control_evaluation_fixture(FIXTURE_PATH)
    report = evaluate_control_fixture(
        fixture,
        build_control_baseline_observations(fixture),
        SYNTHETIC_KEY,
    )
    payload = report.as_dict()

    assert set(payload) == REPORT_KEYS
    assert payload["evaluator_version"] == CONTROL_EVALUATOR_VERSION
    assert payload["case_count"] == 25
    assert payload["passed_count"] == 25
    assert payload["failed_count"] == 0
    for key in (
        "unauthorized_provider_dispatch_count",
        "scope_leak_count",
        "forbidden_content_hit_count",
        "duplicate_charge_count",
        "duplicate_business_write_count",
        "rate_limit_bypass_count",
        "retry_amplification_count",
        "nonzero_cost_case_count",
    ):
        assert payload[key] == 0
    assert payload["breaker_transition_consistency_ppm"] == 1_000_000
    assert payload["budget_attribution_consistency_ppm"] == 1_000_000
    verdicts = cast(list[dict[str, object]], payload["verdicts"])
    assert len(verdicts) == 25
    assert all(verdict["passed"] is True for verdict in verdicts)
    assert len(report.canonical_digest) == 64


@pytest.mark.parametrize(
    ("changes", "failure_code"),
    [
        ({"persona_version": "wrong-v9"}, ControlEvaluationFailureCode.PERSONA_MISMATCH),
        ({"outcome_code": "wrong"}, ControlEvaluationFailureCode.METADATA_MISMATCH),
        ({"provider_dispatch_count": 2}, ControlEvaluationFailureCode.UNAUTHORIZED_DISPATCH),
        ({"scope_leak_count": 1}, ControlEvaluationFailureCode.SCOPE_LEAK),
        ({"forbidden_content_hit_count": 1}, ControlEvaluationFailureCode.FORBIDDEN_CONTENT),
        ({"charge_count": 2}, ControlEvaluationFailureCode.DUPLICATE_CHARGE),
        ({"business_write_count": 2}, ControlEvaluationFailureCode.DUPLICATE_WRITE),
        ({"rate_limit_bypass_count": 1}, ControlEvaluationFailureCode.RATE_LIMIT_BYPASS),
        ({"retry_amplification_count": 1}, ControlEvaluationFailureCode.RETRY_AMPLIFICATION),
        ({"breaker_transition_count": 1}, ControlEvaluationFailureCode.BREAKER_INCONSISTENT),
        (
            {"budget_attribution_error_count": 1},
            ControlEvaluationFailureCode.BUDGET_ATTRIBUTION,
        ),
        ({"cost_micro_usd": 1}, ControlEvaluationFailureCode.COST_NONZERO),
        (
            {"business_semantics_changed": True},
            ControlEvaluationFailureCode.BUSINESS_SEMANTICS_CHANGED,
        ),
    ],
)
def test_evaluator_emits_stable_failure_codes(
    changes: dict[str, Any],
    failure_code: ControlEvaluationFailureCode,
) -> None:
    fixture = load_control_evaluation_fixture(FIXTURE_PATH)
    observations = list(build_control_baseline_observations(fixture))
    observations[0] = replace(observations[0], **changes)

    report = evaluate_control_fixture(fixture, observations, SYNTHETIC_KEY)

    assert report.failed_count == 1
    assert report.verdicts[0].failure_code is failure_code


def test_report_repr_and_json_never_include_forbidden_payload_sentinels() -> None:
    fixture = load_control_evaluation_fixture(FIXTURE_PATH)
    observation = build_control_baseline_observations(fixture)[0]
    report = evaluate_control_fixture(
        fixture,
        build_control_baseline_observations(fixture),
        SYNTHETIC_KEY,
    )
    surfaces = (repr(observation), repr(report), json.dumps(report.as_dict(), sort_keys=True))
    for sentinel in (
        "raw-player-secret",
        "raw-npc-secret",
        "raw-conversation-secret",
        "message-sentinel",
        "reply-sentinel",
        "system-prompt-sentinel",
        "memory-body-sentinel",
        "relationship-suggestion-sentinel",
        "provider-body-sentinel",
        "api-key-sentinel",
    ):
        assert all(sentinel not in surface for surface in surfaces)


def test_observation_does_not_accept_payload_fields() -> None:
    with pytest.raises(TypeError):
        ControlEvaluationObservation(  # type: ignore[call-arg]
            case_id="payload-field",
            message="must-not-be-accepted",
        )


def test_same_fixture_and_key_match_in_three_fresh_python_processes() -> None:
    script = """
import json
import sys
from pathlib import Path
from cyber_town.application.control_evaluation import (
    build_control_baseline_observations,
    evaluate_control_fixture,
    load_control_evaluation_fixture,
)
fixture = load_control_evaluation_fixture(Path(sys.argv[1]))
report = evaluate_control_fixture(
    fixture,
    build_control_baseline_observations(fixture),
    b"f009-step5-synthetic-evaluation-key",
)
print(json.dumps(report.as_dict(), sort_keys=True, separators=(",", ":")))
"""
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    outputs = [
        subprocess.run(
            [sys.executable, "-c", script, str(FIXTURE_PATH)],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        ).stdout.strip()
        for _ in range(3)
    ]

    assert outputs[0] == outputs[1] == outputs[2]
    reports = [json.loads(output) for output in outputs]
    assert len({report["canonical_digest"] for report in reports}) == 1
