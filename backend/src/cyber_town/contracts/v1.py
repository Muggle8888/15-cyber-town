"""Strict version-one dialogue contracts shared by future adapters."""

from __future__ import annotations

import unicodedata
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    WithJsonSchema,
    field_validator,
)

CANONICAL_UUID_PATTERN = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}$"
)
DIALOGUE_MESSAGE_SCHEMA_PATTERN = r"^(?:\S|\S[\s\S]{0,998}\S)$"
CanonicalUUID = Annotated[
    UUID,
    WithJsonSchema(
        {
            "format": "uuid",
            "maxLength": 36,
            "minLength": 36,
            "pattern": CANONICAL_UUID_PATTERN,
            "type": "string",
        },
        mode="validation",
    ),
]


def _require_raw_string_length(value: object, maximum: int) -> object:
    if isinstance(value, str) and len(value) > maximum:
        raise ValueError(f"String must have at most {maximum} characters before trimming")
    return value


def _require_canonical_uuid(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        parsed = UUID(value)
    except ValueError:
        return value
    if value != str(parsed):
        raise ValueError("UUID must use canonical 8-4-4-4-12 representation")
    return value


def _require_safe_dialogue_message(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value != value.strip():
        raise ValueError("Dialogue message cannot contain surrounding whitespace")
    if len(value.encode("utf-8")) > 4_000:
        raise ValueError("Dialogue message exceeds the UTF-8 byte budget")
    for character in value:
        category = unicodedata.category(character)
        if character in {"\n", "\t"}:
            continue
        if character == "\r" or category in {"Cc", "Cf", "Cs"}:
            raise ValueError("Dialogue message contains an unsafe control character")
    return value


ScopedIdentifier = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=r"\S",
    ),
]
PlayerIdentifier = Annotated[
    str,
    StringConstraints(
        strict=True,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
    ),
]
RequestNpcIdentifier = Annotated[
    str,
    StringConstraints(
        strict=True,
        min_length=1,
        max_length=64,
        pattern=r"^(?:neon_guide|signal_archivist|night_courier)$",
    ),
]
DialogueMessage = Annotated[
    str,
    StringConstraints(
        strict=True,
        min_length=1,
        max_length=1_000,
        pattern=r"\S",
    ),
    WithJsonSchema(
        {
            "maxLength": 1_000,
            "minLength": 1,
            "pattern": DIALOGUE_MESSAGE_SCHEMA_PATTERN,
            "type": "string",
        },
        mode="validation",
    ),
]
DialogueReply = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        min_length=1,
        max_length=4_000,
        pattern=r"\S",
    ),
]
ProviderIdentifier = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=r"\S",
    ),
]
PublicErrorMessage = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        min_length=1,
        max_length=500,
        pattern=r"\S",
    ),
]


class StrictContract(BaseModel):
    """Reject coercion and unknown fields at external boundaries."""

    model_config = ConfigDict(extra="forbid", strict=True)


class DialogueStatus(StrEnum):
    """Stable outcome states visible to clients."""

    COMPLETED = "completed"
    DEGRADED = "degraded"


class ApiErrorCode(StrEnum):
    """Stable public errors; internal exception details are never exposed."""

    VALIDATION_ERROR = "validation_error"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    NPC_NOT_FOUND = "npc_not_found"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    BUDGET_EXHAUSTED = "budget_exhausted"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_INVALID_RESPONSE = "provider_invalid_response"
    CIRCUIT_OPEN = "circuit_open"
    CONTROL_UNAVAILABLE = "control_unavailable"
    UNSAFE_CONTENT = "unsafe_content"
    INTERNAL_ERROR = "internal_error"


class DialogueRequestV1(StrictContract):
    """A single idempotent player-to-NPC dialogue command."""

    request_id: CanonicalUUID
    player_id: PlayerIdentifier
    npc_id: RequestNpcIdentifier
    conversation_id: CanonicalUUID
    message: DialogueMessage

    @field_validator("request_id", "conversation_id", mode="before")
    @classmethod
    def require_canonical_uuids(cls, value: object) -> object:
        return _require_canonical_uuid(value)

    @field_validator("player_id", "npc_id", mode="before")
    @classmethod
    def require_raw_identifier_budget(cls, value: object) -> object:
        return _require_raw_string_length(value, 64)

    @field_validator("npc_id", mode="before")
    @classmethod
    def reject_normalizing_npc_id(cls, value: object) -> object:
        if isinstance(value, str) and value != value.strip():
            raise ValueError("NPC identifier cannot contain surrounding whitespace")
        return value

    @field_validator("message", mode="before")
    @classmethod
    def require_raw_message_budget(cls, value: object) -> object:
        return _require_safe_dialogue_message(_require_raw_string_length(value, 1_000))


class DialogueResponseV1(StrictContract):
    """A validated dialogue result without internal provider details."""

    request_id: CanonicalUUID
    trace_id: CanonicalUUID
    npc_id: ScopedIdentifier
    conversation_id: CanonicalUUID
    reply: DialogueReply
    status: DialogueStatus
    provider: ProviderIdentifier

    @field_validator("request_id", "trace_id", "conversation_id", mode="before")
    @classmethod
    def require_canonical_uuids(cls, value: object) -> object:
        return _require_canonical_uuid(value)

    @field_validator("npc_id", "provider", mode="before")
    @classmethod
    def require_raw_identifier_budget(cls, value: object) -> object:
        return _require_raw_string_length(value, 64)

    @field_validator("reply", mode="before")
    @classmethod
    def require_raw_reply_budget(cls, value: object) -> object:
        return _require_raw_string_length(value, 4_000)


class ApiErrorV1(StrictContract):
    """A safe public failure payload correlated by trace identifier."""

    trace_id: CanonicalUUID
    code: ApiErrorCode
    message: PublicErrorMessage
    retryable: bool

    @field_validator("trace_id", mode="before")
    @classmethod
    def require_canonical_uuid(cls, value: object) -> object:
        return _require_canonical_uuid(value)

    @field_validator("message", mode="before")
    @classmethod
    def require_raw_message_budget(cls, value: object) -> object:
        return _require_raw_string_length(value, 500)
