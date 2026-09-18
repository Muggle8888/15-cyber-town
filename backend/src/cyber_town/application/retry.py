"""Deterministic metadata-only retry and circuit-breaker contracts for F-009."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable
from uuid import UUID

from cyber_town.application.safety import (
    BreakerOutcome,
    BreakerState,
    RetryOutcome,
)

BREAKER_POLICY_VERSION = "f-009-retry-breaker-v1"
PROVIDER_MAX_ATTEMPTS = 2
PROVIDER_ATTEMPT_TIMEOUT_SECONDS = 5.0
PROVIDER_EXECUTION_DEADLINE_SECONDS = 12.0
PROVIDER_RETRY_BACKOFF_SECONDS = 0.2
PROVIDER_RETRY_MAX_JITTER_SECONDS = 0.2
BREAKER_FAILURE_WINDOW_SECONDS = 60
BREAKER_FAILURE_THRESHOLD = 5
BREAKER_OPEN_SECONDS = 30
BREAKER_PROBE_SUCCESSES = 2


class BreakerFailureReason(StrEnum):
    TIMEOUT = "provider_timeout"
    UNAVAILABLE = "provider_unavailable"
    INVALID_RESPONSE = "provider_invalid_response"


class RetryBreakerEventKind(StrEnum):
    BREAKER_CHECK = "breaker_check"
    RETRY_SCHEDULED = "retry_scheduled"
    ATTEMPT = "attempt"
    BREAKER_RESULT = "breaker_result"
    PROBE_RELEASE = "probe_release"


@dataclass(frozen=True, slots=True)
class ProviderRetryPolicy:
    max_attempts: int = PROVIDER_MAX_ATTEMPTS
    attempt_timeout_seconds: float = PROVIDER_ATTEMPT_TIMEOUT_SECONDS
    execution_deadline_seconds: float = PROVIDER_EXECUTION_DEADLINE_SECONDS
    backoff_seconds: float = PROVIDER_RETRY_BACKOFF_SECONDS
    max_jitter_seconds: float = PROVIDER_RETRY_MAX_JITTER_SECONDS

    def __post_init__(self) -> None:
        if (
            self.max_attempts != PROVIDER_MAX_ATTEMPTS
            or self.attempt_timeout_seconds != PROVIDER_ATTEMPT_TIMEOUT_SECONDS
            or self.execution_deadline_seconds != PROVIDER_EXECUTION_DEADLINE_SECONDS
            or self.backoff_seconds != PROVIDER_RETRY_BACKOFF_SECONDS
            or self.max_jitter_seconds != PROVIDER_RETRY_MAX_JITTER_SECONDS
        ):
            raise ValueError("Provider retry policy must use the approved fixed values")

    def delay_seconds(self, jitter_seconds: float) -> float:
        if not isinstance(jitter_seconds, (int, float)) or isinstance(jitter_seconds, bool):
            raise TypeError("Provider retry jitter is invalid")
        jitter = float(jitter_seconds)
        if not math.isfinite(jitter) or not 0 <= jitter <= self.max_jitter_seconds:
            raise ValueError("Provider retry jitter is invalid")
        return self.backoff_seconds + jitter


@dataclass(frozen=True, slots=True, repr=False)
class BreakerDecision:
    state: BreakerState
    outcome: BreakerOutcome
    retry_after_seconds: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, BreakerState):
            raise TypeError("Circuit-breaker state is invalid")
        if not isinstance(self.outcome, BreakerOutcome):
            raise TypeError("Circuit-breaker outcome is invalid")
        if self.outcome is BreakerOutcome.REJECTED:
            if (
                type(self.retry_after_seconds) is not int
                or not 1 <= self.retry_after_seconds <= BREAKER_OPEN_SECONDS
            ):
                raise ValueError("Circuit-breaker retry delay is invalid")
        elif self.retry_after_seconds is not None:
            raise ValueError("Allowed circuit-breaker decision cannot carry a retry delay")


@dataclass(frozen=True, slots=True, repr=False)
class RetryBreakerMetadata:
    trace_id: UUID
    execution_id: UUID
    attempt_number: int
    event_kind: RetryBreakerEventKind
    retry_outcome: RetryOutcome
    breaker_state: BreakerState
    breaker_outcome: BreakerOutcome
    failure_reason: BreakerFailureReason | None
    backoff_ms: int
    jitter_ms: int
    deadline_remaining_ms: int
    recorded_at_utc: datetime
    policy_version: str = BREAKER_POLICY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.trace_id, UUID) or not isinstance(self.execution_id, UUID):
            raise TypeError("Retry metadata linkage is invalid")
        if type(self.attempt_number) is not int or not 0 <= self.attempt_number <= 2:
            raise ValueError("Retry metadata attempt is invalid")
        if not isinstance(self.event_kind, RetryBreakerEventKind):
            raise TypeError("Retry metadata event is invalid")
        if not isinstance(self.retry_outcome, RetryOutcome):
            raise TypeError("Retry metadata outcome is invalid")
        if not isinstance(self.breaker_state, BreakerState):
            raise TypeError("Retry metadata breaker state is invalid")
        if not isinstance(self.breaker_outcome, BreakerOutcome):
            raise TypeError("Retry metadata breaker outcome is invalid")
        if self.failure_reason is not None and not isinstance(
            self.failure_reason, BreakerFailureReason
        ):
            raise TypeError("Retry metadata failure reason is invalid")
        for value in (self.backoff_ms, self.jitter_ms, self.deadline_remaining_ms):
            if type(value) is not int or value < 0:
                raise ValueError("Retry metadata timing is invalid")
        if self.backoff_ms > 400 or self.jitter_ms > 200 or self.deadline_remaining_ms > 12_000:
            raise ValueError("Retry metadata timing is outside the approved range")
        if self.recorded_at_utc.tzinfo is None or self.recorded_at_utc.utcoffset() is None:
            raise ValueError("Retry metadata timestamp must be timezone-aware")
        if self.policy_version != BREAKER_POLICY_VERSION:
            raise ValueError("Retry metadata policy version is invalid")


@runtime_checkable
class RetryBreakerRecorder(Protocol):
    def record_retry_breaker(self, record: RetryBreakerMetadata) -> None: ...


class NoOpRetryBreakerRecorder:
    def record_retry_breaker(self, record: RetryBreakerMetadata) -> None:
        if not isinstance(record, RetryBreakerMetadata):
            raise TypeError("Retry metadata record is invalid")

    def __repr__(self) -> str:
        return "NoOpRetryBreakerRecorder()"


class InMemoryRetryBreakerRecorder:
    def __init__(self) -> None:
        self._records: list[RetryBreakerMetadata] = []

    def record_retry_breaker(self, record: RetryBreakerMetadata) -> None:
        if not isinstance(record, RetryBreakerMetadata):
            raise TypeError("Retry metadata record is invalid")
        self._records.append(record)

    def snapshot(self) -> tuple[RetryBreakerMetadata, ...]:
        return tuple(self._records)

    def __repr__(self) -> str:
        return "InMemoryRetryBreakerRecorder()"
