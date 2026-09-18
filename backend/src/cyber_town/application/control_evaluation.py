"""Deterministic metadata-only evaluation for F-009 control invariants."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from cyber_town.domain.persona import load_bundled_personas

CONTROL_EVALUATOR_VERSION = "f-009-control-evaluator-v1"
CONTROL_FIXTURE_VERSION = "f-009-control-evaluation-fixture-v1"
CONTROL_EVALUATION_SCHEMA_VERSION = 1

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:[a-z0-9_-]*[a-z0-9])?$")
_VERSION_PATTERN = re.compile(r"^[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?$")
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_METADATA_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class ControlEvaluationDimension(StrEnum):
    PERSONA_IDENTITY = "persona_identity"
    INPUT_BOUNDARY = "input_boundary"
    PROMPT_INJECTION = "prompt_injection"
    PERSISTENT_SAFETY = "persistent_safety"
    PROVIDER_FIREWALL = "provider_firewall"
    RATE_LIMIT_CONCURRENCY = "rate_limit_concurrency"
    BUDGET_COST = "budget_cost"
    RETRY_IDEMPOTENCY = "retry_idempotency"
    BREAKER_RECOVERY = "breaker_recovery"
    CANCELLATION_SCOPE = "cancellation_scope"
    COMPONENT_FAILURE = "component_failure"


class ControlEvaluationFailureCode(StrEnum):
    NONE = "none"
    PERSONA_MISMATCH = "persona_mismatch"
    METADATA_MISMATCH = "metadata_mismatch"
    UNAUTHORIZED_DISPATCH = "unauthorized_dispatch"
    SCOPE_LEAK = "scope_leak"
    FORBIDDEN_CONTENT = "forbidden_content"
    DUPLICATE_CHARGE = "duplicate_charge"
    DUPLICATE_WRITE = "duplicate_write"
    RATE_LIMIT_BYPASS = "rate_limit_bypass"
    RETRY_AMPLIFICATION = "retry_amplification"
    BREAKER_INCONSISTENT = "breaker_inconsistent"
    BUDGET_ATTRIBUTION = "budget_attribution"
    COST_NONZERO = "cost_nonzero"
    BUSINESS_SEMANTICS_CHANGED = "business_semantics_changed"


def _nonnegative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid {label}")
    return value


def _exact_keys(payload: Mapping[str, object], expected: set[str], label: str) -> None:
    if set(payload) != expected:
        raise ValueError(f"Invalid {label} members")


@dataclass(frozen=True, slots=True)
class ControlPersonaContract:
    npc_id: str
    version: str
    content_sha256: str

    def __post_init__(self) -> None:
        if _IDENTIFIER_PATTERN.fullmatch(self.npc_id) is None:
            raise ValueError("Invalid persona identifier")
        if _VERSION_PATTERN.fullmatch(self.version) is None:
            raise ValueError("Invalid persona version")
        if _DIGEST_PATTERN.fullmatch(self.content_sha256) is None:
            raise ValueError("Invalid persona digest")


@dataclass(frozen=True, slots=True)
class ControlEvaluationObservation:
    case_id: str
    persona_version: str | None
    outcome_code: str
    provider_dispatch_count: int
    charge_count: int
    business_write_count: int
    breaker_transition_count: int
    scope_leak_count: int
    forbidden_content_hit_count: int
    rate_limit_bypass_count: int
    retry_amplification_count: int
    budget_attribution_error_count: int
    cost_micro_usd: int
    business_semantics_changed: bool
    metadata_counts: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if _IDENTIFIER_PATTERN.fullmatch(self.case_id) is None or len(self.case_id) > 64:
            raise ValueError("Invalid control evaluation case identifier")
        if self.persona_version is not None and (
            _VERSION_PATTERN.fullmatch(self.persona_version) is None
            or len(self.persona_version) > 64
        ):
            raise ValueError("Invalid control evaluation persona version")
        if _IDENTIFIER_PATTERN.fullmatch(self.outcome_code) is None:
            raise ValueError("Invalid control evaluation outcome")
        for field_name in (
            "provider_dispatch_count",
            "charge_count",
            "business_write_count",
            "breaker_transition_count",
            "scope_leak_count",
            "forbidden_content_hit_count",
            "rate_limit_bypass_count",
            "retry_amplification_count",
            "budget_attribution_error_count",
            "cost_micro_usd",
        ):
            _nonnegative_integer(getattr(self, field_name), field_name)
        if not isinstance(self.business_semantics_changed, bool):
            raise TypeError("Invalid business semantics flag")
        keys: set[str] = set()
        for key, value in self.metadata_counts:
            if _METADATA_KEY_PATTERN.fullmatch(key) is None or key in keys:
                raise ValueError("Invalid metadata count key")
            keys.add(key)
            _nonnegative_integer(value, "metadata count")
        if tuple(sorted(self.metadata_counts)) != self.metadata_counts:
            raise ValueError("Metadata counts must use canonical order")


@dataclass(frozen=True, slots=True)
class ControlEvaluationCase:
    case_id: str
    dimension: ControlEvaluationDimension
    expected: ControlEvaluationObservation

    def __post_init__(self) -> None:
        if self.case_id != self.expected.case_id:
            raise ValueError("Control evaluation case identity mismatch")


@dataclass(frozen=True, slots=True)
class ControlEvaluationFixture:
    schema_version: int
    fixture_version: str
    personas: tuple[ControlPersonaContract, ...]
    cases: tuple[ControlEvaluationCase, ...]


@dataclass(frozen=True, slots=True)
class ControlCaseVerdict:
    case_id: str
    dimension: ControlEvaluationDimension
    passed: bool
    failure_code: ControlEvaluationFailureCode

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "dimension": self.dimension.value,
            "passed": self.passed,
            "failure_code": self.failure_code.value,
        }


@dataclass(frozen=True, slots=True)
class ControlEvaluationReport:
    evaluator_version: str
    fixture_version: str
    schema_version: int
    case_count: int
    passed_count: int
    failed_count: int
    unauthorized_provider_dispatch_count: int
    scope_leak_count: int
    forbidden_content_hit_count: int
    duplicate_charge_count: int
    duplicate_business_write_count: int
    rate_limit_bypass_count: int
    retry_amplification_count: int
    breaker_transition_consistency_ppm: int
    budget_attribution_consistency_ppm: int
    nonzero_cost_case_count: int
    verdicts: tuple[ControlCaseVerdict, ...]
    canonical_digest: str

    def as_dict(self) -> dict[str, object]:
        return {
            "evaluator_version": self.evaluator_version,
            "fixture_version": self.fixture_version,
            "schema_version": self.schema_version,
            "case_count": self.case_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "unauthorized_provider_dispatch_count": self.unauthorized_provider_dispatch_count,
            "scope_leak_count": self.scope_leak_count,
            "forbidden_content_hit_count": self.forbidden_content_hit_count,
            "duplicate_charge_count": self.duplicate_charge_count,
            "duplicate_business_write_count": self.duplicate_business_write_count,
            "rate_limit_bypass_count": self.rate_limit_bypass_count,
            "retry_amplification_count": self.retry_amplification_count,
            "breaker_transition_consistency_ppm": self.breaker_transition_consistency_ppm,
            "budget_attribution_consistency_ppm": self.budget_attribution_consistency_ppm,
            "nonzero_cost_case_count": self.nonzero_cost_case_count,
            "verdicts": [verdict.as_dict() for verdict in self.verdicts],
            "canonical_digest": self.canonical_digest,
        }


_TOP_LEVEL_KEYS = {"schema_version", "fixture_version", "personas", "cases"}
_PERSONA_KEYS = {"npc_id", "version", "content_sha256"}
_CASE_KEYS = {
    "case_id",
    "dimension",
    "persona_version",
    "outcome_code",
    "provider_dispatch_count",
    "charge_count",
    "business_write_count",
    "breaker_transition_count",
    "scope_leak_count",
    "forbidden_content_hit_count",
    "rate_limit_bypass_count",
    "retry_amplification_count",
    "budget_attribution_error_count",
    "cost_micro_usd",
    "business_semantics_changed",
    "metadata_counts",
}


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate control fixture member")
        result[key] = value
    return result


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"Invalid {label}")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, list):
        raise ValueError(f"Invalid {label}")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Invalid {label}")
    return value


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Invalid {label}")
    return value


def _metadata_counts(value: object) -> tuple[tuple[str, int], ...]:
    payload = _mapping(value, "metadata counts")
    return tuple(
        sorted(
            (
                _text(key, "metadata count key"),
                _nonnegative_integer(count, "metadata count"),
            )
            for key, count in payload.items()
        )
    )


def _persona(value: object) -> ControlPersonaContract:
    payload = _mapping(value, "persona contract")
    _exact_keys(payload, _PERSONA_KEYS, "persona contract")
    return ControlPersonaContract(
        npc_id=_text(payload["npc_id"], "persona identifier"),
        version=_text(payload["version"], "persona version"),
        content_sha256=_text(payload["content_sha256"], "persona digest"),
    )


def _case(value: object) -> ControlEvaluationCase:
    payload = _mapping(value, "control evaluation case")
    _exact_keys(payload, _CASE_KEYS, "control evaluation case")
    case_id = _text(payload["case_id"], "case identifier")
    try:
        dimension = ControlEvaluationDimension(_text(payload["dimension"], "dimension"))
    except ValueError as error:
        raise ValueError("Invalid control evaluation dimension") from error
    persona_version = payload["persona_version"]
    if persona_version is not None and not isinstance(persona_version, str):
        raise ValueError("Invalid expected persona version")
    observation = ControlEvaluationObservation(
        case_id=case_id,
        persona_version=persona_version,
        outcome_code=_text(payload["outcome_code"], "outcome code"),
        provider_dispatch_count=_nonnegative_integer(
            payload["provider_dispatch_count"], "provider dispatch count"
        ),
        charge_count=_nonnegative_integer(payload["charge_count"], "charge count"),
        business_write_count=_nonnegative_integer(
            payload["business_write_count"], "business write count"
        ),
        breaker_transition_count=_nonnegative_integer(
            payload["breaker_transition_count"], "breaker transition count"
        ),
        scope_leak_count=_nonnegative_integer(payload["scope_leak_count"], "scope leak count"),
        forbidden_content_hit_count=_nonnegative_integer(
            payload["forbidden_content_hit_count"], "forbidden content hit count"
        ),
        rate_limit_bypass_count=_nonnegative_integer(
            payload["rate_limit_bypass_count"], "rate-limit bypass count"
        ),
        retry_amplification_count=_nonnegative_integer(
            payload["retry_amplification_count"], "retry amplification count"
        ),
        budget_attribution_error_count=_nonnegative_integer(
            payload["budget_attribution_error_count"], "budget attribution error count"
        ),
        cost_micro_usd=_nonnegative_integer(payload["cost_micro_usd"], "cost micro USD"),
        business_semantics_changed=_boolean(
            payload["business_semantics_changed"], "business semantics flag"
        ),
        metadata_counts=_metadata_counts(payload["metadata_counts"]),
    )
    return ControlEvaluationCase(case_id=case_id, dimension=dimension, expected=observation)


def load_control_evaluation_fixture(path: Path) -> ControlEvaluationFixture:
    """Load the strict checked-in F-009 metadata fixture."""

    if not isinstance(path, Path):
        raise TypeError("Control fixture path type is invalid")
    root = _mapping(
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates),
        "control evaluation fixture",
    )
    _exact_keys(root, _TOP_LEVEL_KEYS, "control evaluation fixture")
    schema_version = _nonnegative_integer(root["schema_version"], "schema version")
    if schema_version != CONTROL_EVALUATION_SCHEMA_VERSION:
        raise ValueError("Unsupported control evaluation schema version")
    fixture_version = _text(root["fixture_version"], "fixture version")
    if fixture_version != CONTROL_FIXTURE_VERSION:
        raise ValueError("Unsupported control evaluation fixture version")
    personas = tuple(_persona(item) for item in _sequence(root["personas"], "personas"))
    cases = tuple(_case(item) for item in _sequence(root["cases"], "cases"))
    if not personas or len({persona.npc_id for persona in personas}) != len(personas):
        raise ValueError("Invalid control persona contract set")
    if not cases or len({case.case_id for case in cases}) != len(cases):
        raise ValueError("Invalid control evaluation case set")
    if {case.dimension for case in cases} != set(ControlEvaluationDimension):
        raise ValueError("Incomplete control evaluation dimension set")
    bundled = load_bundled_personas()
    expected_personas = {
        (persona.npc_id, persona.version, persona.content_sha256) for persona in personas
    }
    actual_personas = {
        (persona.npc_id, persona.version, persona.content_sha256) for persona in bundled.values()
    }
    if expected_personas != actual_personas:
        raise ValueError("Control persona contract does not match the bundled registry")
    return ControlEvaluationFixture(
        schema_version=schema_version,
        fixture_version=fixture_version,
        personas=personas,
        cases=cases,
    )


def build_control_baseline_observations(
    fixture: ControlEvaluationFixture,
) -> tuple[ControlEvaluationObservation, ...]:
    """Return immutable metadata-only baseline observations."""

    if not isinstance(fixture, ControlEvaluationFixture):
        raise TypeError("Control evaluation fixture type is invalid")
    return tuple(case.expected for case in fixture.cases)


def _failure_for(
    case: ControlEvaluationCase,
    observation: ControlEvaluationObservation,
) -> ControlEvaluationFailureCode:
    expected = case.expected
    if observation.persona_version != expected.persona_version:
        return ControlEvaluationFailureCode.PERSONA_MISMATCH
    if observation.outcome_code != expected.outcome_code:
        return ControlEvaluationFailureCode.METADATA_MISMATCH
    if observation.provider_dispatch_count > expected.provider_dispatch_count:
        return ControlEvaluationFailureCode.UNAUTHORIZED_DISPATCH
    if observation.provider_dispatch_count < expected.provider_dispatch_count:
        return ControlEvaluationFailureCode.METADATA_MISMATCH
    if observation.scope_leak_count:
        return ControlEvaluationFailureCode.SCOPE_LEAK
    if observation.forbidden_content_hit_count:
        return ControlEvaluationFailureCode.FORBIDDEN_CONTENT
    if observation.charge_count > expected.charge_count:
        return ControlEvaluationFailureCode.DUPLICATE_CHARGE
    if observation.charge_count < expected.charge_count:
        return ControlEvaluationFailureCode.BUDGET_ATTRIBUTION
    if observation.business_write_count > expected.business_write_count:
        return ControlEvaluationFailureCode.DUPLICATE_WRITE
    if observation.business_write_count < expected.business_write_count:
        return ControlEvaluationFailureCode.BUSINESS_SEMANTICS_CHANGED
    if observation.rate_limit_bypass_count:
        return ControlEvaluationFailureCode.RATE_LIMIT_BYPASS
    if observation.retry_amplification_count:
        return ControlEvaluationFailureCode.RETRY_AMPLIFICATION
    if observation.breaker_transition_count != expected.breaker_transition_count:
        return ControlEvaluationFailureCode.BREAKER_INCONSISTENT
    if observation.budget_attribution_error_count:
        return ControlEvaluationFailureCode.BUDGET_ATTRIBUTION
    if observation.cost_micro_usd:
        return ControlEvaluationFailureCode.COST_NONZERO
    if observation.business_semantics_changed:
        return ControlEvaluationFailureCode.BUSINESS_SEMANTICS_CHANGED
    if observation.metadata_counts != expected.metadata_counts:
        return ControlEvaluationFailureCode.METADATA_MISMATCH
    return ControlEvaluationFailureCode.NONE


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def evaluate_control_fixture(
    fixture: ControlEvaluationFixture,
    observations: Sequence[ControlEvaluationObservation],
    scope_key: bytes,
) -> ControlEvaluationReport:
    """Evaluate allowlisted control metadata and return a stable digest."""

    if not isinstance(fixture, ControlEvaluationFixture):
        raise TypeError("Control evaluation fixture type is invalid")
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise TypeError("Control evaluation observations type is invalid")
    if not isinstance(scope_key, bytes) or len(scope_key) < 16:
        raise ValueError("Control evaluation scope key is invalid")
    observed: dict[str, ControlEvaluationObservation] = {}
    for observation in observations:
        if not isinstance(observation, ControlEvaluationObservation):
            raise TypeError("Control evaluation observation type is invalid")
        if observation.case_id in observed:
            raise ValueError("Duplicate control evaluation observation")
        observed[observation.case_id] = observation
    if set(observed) != {case.case_id for case in fixture.cases}:
        raise ValueError("Control evaluation observation set mismatch")

    verdicts = tuple(
        ControlCaseVerdict(
            case_id=case.case_id,
            dimension=case.dimension,
            passed=(failure := _failure_for(case, observed[case.case_id]))
            is ControlEvaluationFailureCode.NONE,
            failure_code=failure,
        )
        for case in fixture.cases
    )
    unauthorized_dispatches = sum(
        max(
            0,
            observed[case.case_id].provider_dispatch_count - case.expected.provider_dispatch_count,
        )
        for case in fixture.cases
    )
    duplicate_charges = sum(
        max(0, observed[case.case_id].charge_count - case.expected.charge_count)
        for case in fixture.cases
    )
    duplicate_writes = sum(
        max(0, observed[case.case_id].business_write_count - case.expected.business_write_count)
        for case in fixture.cases
    )
    breaker_consistent = sum(
        observed[case.case_id].breaker_transition_count == case.expected.breaker_transition_count
        for case in fixture.cases
    )
    budget_consistent = sum(
        observed[case.case_id].charge_count == case.expected.charge_count
        and observed[case.case_id].budget_attribution_error_count == 0
        for case in fixture.cases
    )
    passed_count = sum(verdict.passed for verdict in verdicts)
    report_without_digest: dict[str, object] = {
        "evaluator_version": CONTROL_EVALUATOR_VERSION,
        "fixture_version": fixture.fixture_version,
        "schema_version": fixture.schema_version,
        "case_count": len(fixture.cases),
        "passed_count": passed_count,
        "failed_count": len(fixture.cases) - passed_count,
        "unauthorized_provider_dispatch_count": unauthorized_dispatches,
        "scope_leak_count": sum(item.scope_leak_count for item in observed.values()),
        "forbidden_content_hit_count": sum(
            item.forbidden_content_hit_count for item in observed.values()
        ),
        "duplicate_charge_count": duplicate_charges,
        "duplicate_business_write_count": duplicate_writes,
        "rate_limit_bypass_count": sum(item.rate_limit_bypass_count for item in observed.values()),
        "retry_amplification_count": sum(
            item.retry_amplification_count for item in observed.values()
        ),
        "breaker_transition_consistency_ppm": breaker_consistent * 1_000_000 // len(fixture.cases),
        "budget_attribution_consistency_ppm": budget_consistent * 1_000_000 // len(fixture.cases),
        "nonzero_cost_case_count": sum(item.cost_micro_usd != 0 for item in observed.values()),
        "verdicts": [verdict.as_dict() for verdict in verdicts],
    }
    tag_digest = hashlib.sha256(
        "".join(
            hmac.new(
                scope_key,
                b"cyber-town:f009:control-evaluation:v1\0" + case.case_id.encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
            for case in fixture.cases
        ).encode("ascii")
    ).hexdigest()
    canonical_digest = hashlib.sha256(
        _canonical_json({"report": report_without_digest, "synthetic_tag_set": tag_digest})
    ).hexdigest()
    return ControlEvaluationReport(
        evaluator_version=CONTROL_EVALUATOR_VERSION,
        fixture_version=fixture.fixture_version,
        schema_version=fixture.schema_version,
        case_count=len(fixture.cases),
        passed_count=passed_count,
        failed_count=len(fixture.cases) - passed_count,
        unauthorized_provider_dispatch_count=unauthorized_dispatches,
        scope_leak_count=sum(item.scope_leak_count for item in observed.values()),
        forbidden_content_hit_count=sum(
            item.forbidden_content_hit_count for item in observed.values()
        ),
        duplicate_charge_count=duplicate_charges,
        duplicate_business_write_count=duplicate_writes,
        rate_limit_bypass_count=sum(item.rate_limit_bypass_count for item in observed.values()),
        retry_amplification_count=sum(item.retry_amplification_count for item in observed.values()),
        breaker_transition_consistency_ppm=breaker_consistent * 1_000_000 // len(fixture.cases),
        budget_attribution_consistency_ppm=budget_consistent * 1_000_000 // len(fixture.cases),
        nonzero_cost_case_count=sum(item.cost_micro_usd != 0 for item in observed.values()),
        verdicts=verdicts,
        canonical_digest=canonical_digest,
    )
