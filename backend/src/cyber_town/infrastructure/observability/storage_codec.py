"""Versioned, reversible metadata storage codes; no payload or secret material."""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from uuid import UUID

CODEC_VERSION = "f009-observability-storage-v1"

# Explicit codes, independent of application Enum declaration order. Never reuse
# a code for another value; any future changes require a new storage migration.
WORD_CODES: Mapping[str, int] = MappingProxyType(
    {
        "none": 1,
        "completed": 2,
        "degraded_content_filter": 3,
        "degraded_no_history": 4,
        "local_memory_command": 5,
        "cache_replay": 6,
        "shared_execution": 7,
        "cancelled": 8,
        "orphaned": 9,
        "restart_recovery": 10,
        "not_reached": 11,
        "http_received": 12,
        "request_validation": 13,
        "persona_resolution": 14,
        "idempotency_resolution": 15,
        "scope_lock": 16,
        "short_term_selection": 17,
        "long_term_retrieval": 18,
        "context_budget_selection": 19,
        "provider_queue": 20,
        "provider_completion": 21,
        "relationship_evaluation": 22,
        "state_commit": 23,
        "response_mapping": 24,
        "terminal": 25,
        "started": 26,
        "skipped": 27,
        "failed": 28,
        "validation_error": 29,
        "npc_not_found": 30,
        "conflict": 31,
        "provider_timeout": 32,
        "provider_unavailable": 33,
        "provider_invalid_response": 34,
        "unsafe_content": 35,
        "internal_error": 36,
        "observability_unavailable": 37,
        "active": 38,
        "expired": 39,
        "dispatch_owner": 40,
        "shared_waiter": 41,
        "local_execution": 42,
        "reservation": 43,
        "dispatch": 44,
        "settlement": 45,
        "release": 46,
        "rejection": 47,
        "f-009-budget-policy-v1": 48,
        "fake": 49,
        "deepseek": 50,
        "local-fallback": 51,
        "disabled": 52,
        "unknown": 53,
        "reserved": 54,
        "settled": 55,
        "rejected": 56,
        "breaker_check": 57,
        "retry_scheduled": 58,
        "attempt": 59,
        "breaker_result": 60,
        "probe_release": 61,
        "f-009-retry-breaker-v1": 62,
        "not_eligible": 63,
        "scheduled": 64,
        "attempted": 65,
        "exhausted": 66,
        "closed": 67,
        "open": 68,
        "half_open": 69,
        "allowed": 70,
        "probe_allowed": 71,
        "transitioned": 72,
    }
)


def _domain(words: str) -> Mapping[str, int]:
    return MappingProxyType({word: WORD_CODES[word] for word in words.split()})


ENUM_FIELDS: Mapping[tuple[str, str], Mapping[str, int]] = MappingProxyType(
    {
        ("trace_stage_events", "stage"): _domain(
            "http_received request_validation persona_resolution idempotency_resolution "
            "scope_lock short_term_selection long_term_retrieval context_budget_selection "
            "provider_queue provider_completion relationship_evaluation state_commit "
            "response_mapping terminal"
        ),
        ("trace_stage_events", "outcome"): _domain(
            "started completed skipped failed cancelled not_reached"
        ),
        ("trace_stage_events", "reason_code"): _domain(
            "none completed degraded_content_filter degraded_no_history local_memory_command "
            "cache_replay shared_execution cancelled orphaned restart_recovery not_reached"
        ),
        ("trace_stage_events", "error_code"): _domain(
            "none validation_error npc_not_found conflict provider_timeout provider_unavailable "
            "provider_invalid_response unsafe_content internal_error observability_unavailable"
        ),
        ("trace_stage_events", "retention_status"): _domain("active expired"),
        ("execution_links", "link_kind"): _domain("dispatch_owner shared_waiter local_execution"),
        ("execution_links", "retention_status"): _domain("active expired"),
        ("safety_cost_events", "event_kind"): _domain(
            "reservation dispatch settlement release rejection"
        ),
        ("safety_cost_events", "policy_version"): _domain("f-009-budget-policy-v1"),
        ("safety_cost_events", "provider_kind"): _domain(
            "fake deepseek local-fallback disabled unknown"
        ),
        ("safety_cost_events", "outcome"): _domain("not_reached reserved settled rejected failed"),
        ("retry_breaker_events", "event_kind"): _domain(
            "breaker_check retry_scheduled attempt breaker_result probe_release"
        ),
        ("retry_breaker_events", "policy_version"): _domain("f-009-retry-breaker-v1"),
        ("retry_breaker_events", "retry_outcome"): _domain(
            "not_reached not_eligible scheduled attempted exhausted cancelled"
        ),
        ("retry_breaker_events", "breaker_state"): _domain("closed open half_open"),
        ("retry_breaker_events", "breaker_outcome"): _domain(
            "not_reached allowed rejected probe_allowed transitioned failed"
        ),
        ("retry_breaker_events", "failure_reason"): _domain(
            "provider_timeout provider_unavailable provider_invalid_response"
        ),
    }
)
UUID_FIELDS = frozenset(
    (table, "execution_id")
    for table in ("execution_links", "safety_cost_events", "retry_breaker_events")
)
TAG_FIELDS = frozenset(
    ("safety_cost_events", column)
    for column in ("player_scope_tag", "npc_scope_tag", "player_npc_scope_tag")
)
ENCODED_FIELDS = frozenset(ENUM_FIELDS) | UUID_FIELDS | TAG_FIELDS
_NULLABLE = ("retry_breaker_events", "failure_reason")
_TAG = re.compile(r"[0-9a-f]{64}\Z")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


def encode_value(table: str, column: str, value: object) -> int | bytes | None:
    field = (table, column)
    if field == _NULLABLE and value is None:
        return None
    if type(value) is str:
        mapping = ENUM_FIELDS.get(field)
        if mapping is not None and value in mapping:
            return mapping[value]
        if field in UUID_FIELDS and _UUID.fullmatch(value):
            return UUID(value).bytes
        if field in TAG_FIELDS and _TAG.fullmatch(value):
            return bytes.fromhex(value)
    raise ValueError("Invalid observability storage value")


def decode_value(table: str, column: str, value: object) -> str | None:
    field = (table, column)
    if field == _NULLABLE and value is None:
        return None
    mapping = ENUM_FIELDS.get(field)
    if mapping is not None and type(value) is int:
        for word, code in mapping.items():
            if value == code:
                return word
    if type(value) is bytes:
        if field in UUID_FIELDS and len(value) == 16:
            return str(UUID(bytes=value))
        if field in TAG_FIELDS and len(value) == 32:
            return value.hex()
    raise ValueError("Invalid observability storage value")
