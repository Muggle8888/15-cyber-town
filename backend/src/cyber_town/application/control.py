"""Deterministic, metadata-only safety control for F-009 Step 2."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import math
import re
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from typing import Protocol, runtime_checkable
from uuid import UUID

from cyber_town.application.budget import (
    BudgetRejectedError,
    BudgetRepository,
    BudgetReservation,
    BudgetScopeTags,
    BudgetSettlement,
    PricingPolicy,
    calculate_cost_micro_usd,
)
from cyber_town.application.observability import (
    ScopeDimension,
    StorageExecutor,
    call_storage,
    derive_scope_tag,
)
from cyber_town.application.provider import ProviderUsage
from cyber_town.application.retry import (
    BreakerDecision,
    BreakerFailureReason,
)
from cyber_town.application.safety import BreakerOutcome, BreakerState, RateLimitOutcome
from cyber_town.contracts.v1 import DialogueRequestV1

CONTROL_POLICY_VERSION = "f-009-safety-control-v1"
_TAG_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_MIN_KEY_BYTES = 16


class ControlScope(StrEnum):
    """Fixed token-bucket scope classes."""

    INGRESS_GLOBAL = "ingress_global"
    DIRECT_PEER = "direct_peer"
    PLAYER = "player"
    PLAYER_NPC = "player_npc"
    CONVERSATION = "conversation"


@dataclass(frozen=True, slots=True)
class TokenBucketSpec:
    scope: ControlScope
    refill_per_minute: int
    burst: int

    def __post_init__(self) -> None:
        if not isinstance(self.scope, ControlScope):
            raise TypeError("Control bucket scope is invalid")
        if type(self.refill_per_minute) is not int or self.refill_per_minute <= 0:
            raise ValueError("Control bucket refill is invalid")
        if type(self.burst) is not int or self.burst <= 0:
            raise ValueError("Control bucket burst is invalid")


BUCKET_SPECS = {
    ControlScope.INGRESS_GLOBAL: TokenBucketSpec(ControlScope.INGRESS_GLOBAL, 120, 30),
    ControlScope.DIRECT_PEER: TokenBucketSpec(ControlScope.DIRECT_PEER, 60, 15),
    ControlScope.PLAYER: TokenBucketSpec(ControlScope.PLAYER, 20, 5),
    ControlScope.PLAYER_NPC: TokenBucketSpec(ControlScope.PLAYER_NPC, 10, 3),
    ControlScope.CONVERSATION: TokenBucketSpec(ControlScope.CONVERSATION, 6, 2),
}


@dataclass(frozen=True, slots=True, repr=False)
class BucketRequest:
    spec: TokenBucketSpec
    scope_tag: str

    def __post_init__(self) -> None:
        if not isinstance(self.spec, TokenBucketSpec):
            raise TypeError("Control bucket specification is invalid")
        _require_tag(self.scope_tag)


@dataclass(frozen=True, slots=True, repr=False)
class PermitScopeTags:
    player_scope_tag: str
    player_npc_scope_tag: str
    conversation_scope_tag: str

    def __post_init__(self) -> None:
        _require_tag(self.player_scope_tag)
        _require_tag(self.player_npc_scope_tag)
        _require_tag(self.conversation_scope_tag)


@dataclass(frozen=True, slots=True)
class BucketConsumptionResult:
    outcome: RateLimitOutcome
    retry_after_seconds: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, RateLimitOutcome):
            raise TypeError("Control rate outcome is invalid")
        if self.outcome is RateLimitOutcome.REJECTED:
            if type(self.retry_after_seconds) is not int or not 1 <= self.retry_after_seconds <= 60:
                raise ValueError("Control retry delay is invalid")
        elif self.retry_after_seconds is not None:
            raise ValueError("Allowed control decision cannot carry a retry delay")


class ControlRepositoryError(RuntimeError):
    """Safe repository failure with no SQLite or identifier detail."""

    def __init__(self) -> None:
        super().__init__("Safety control storage is unavailable.")

    def __repr__(self) -> str:
        return "ControlRepositoryError()"


class RateLimitExceededError(RuntimeError):
    """One stable rate rejection carrying only a bounded retry delay."""

    def __init__(self, retry_after_seconds: int) -> None:
        if type(retry_after_seconds) is not int or not 1 <= retry_after_seconds <= 60:
            raise ValueError("Rate limit retry delay is invalid")
        super().__init__("Dialogue request rate limit exceeded.")
        self.retry_after_seconds = retry_after_seconds

    def __repr__(self) -> str:
        return "RateLimitExceededError()"


class ControlUnavailableError(RuntimeError):
    """Fail-closed control error that never includes the underlying value."""

    def __init__(self) -> None:
        super().__init__("Safety control is unavailable.")

    def __repr__(self) -> str:
        return "ControlUnavailableError()"


class ControlCapacityError(RuntimeError):
    """Provider concurrency remained full for the approved local wait budget."""

    def __init__(self) -> None:
        super().__init__("Safety control capacity is unavailable.")

    def __repr__(self) -> str:
        return "ControlCapacityError()"


class CircuitOpenError(RuntimeError):
    """Stable pre-dispatch rejection with only a bounded retry delay."""

    def __init__(self, retry_after_seconds: int) -> None:
        if type(retry_after_seconds) is not int or not 1 <= retry_after_seconds <= 30:
            raise ValueError("Circuit-breaker retry delay is invalid")
        super().__init__("Dialogue provider circuit is open.")
        self.retry_after_seconds = retry_after_seconds

    def __repr__(self) -> str:
        return "CircuitOpenError()"


@dataclass(frozen=True, slots=True, repr=False)
class ProviderPermit:
    execution_id: UUID
    scope_tags: PermitScopeTags

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, UUID):
            raise TypeError("Control permit execution identifier is invalid")
        if not isinstance(self.scope_tags, PermitScopeTags):
            raise TypeError("Control permit scope is invalid")


@dataclass(frozen=True, slots=True, repr=False)
class ProviderDispatchAdmission:
    breaker_decision: BreakerDecision
    reservation: BudgetReservation
    permit: ProviderPermit


@dataclass(frozen=True, slots=True, repr=False)
class ProviderSuccessFinalization:
    settlement: BudgetSettlement
    breaker_decision: BreakerDecision


@runtime_checkable
class SafetyControlRepository(BudgetRepository, Protocol):
    def consume_ingress(
        self,
        *,
        buckets: Sequence[BucketRequest],
        now_ns: int,
    ) -> BucketConsumptionResult: ...

    def consume_execution_admission(
        self,
        *,
        buckets: Sequence[BucketRequest],
        execution_id: UUID,
        request_id: UUID,
        scope_tags: PermitScopeTags,
        now_ns: int,
    ) -> BucketConsumptionResult: ...

    def try_acquire_permit(
        self,
        *,
        execution_id: UUID,
        scope_tags: PermitScopeTags,
        acquired_at_ns: int,
    ) -> bool: ...

    def release_permit(
        self,
        *,
        execution_id: UUID,
        released_at_ns: int,
        reason: str,
    ) -> None: ...

    def recover_open_permits(self, *, now_ns: int) -> int: ...

    def check_breaker(
        self,
        *,
        execution_id: UUID,
        scope_tag: str,
        now_ns: int,
    ) -> BreakerDecision: ...

    def record_breaker_result(
        self,
        *,
        execution_id: UUID,
        scope_tag: str,
        success: bool,
        failure_reason: BreakerFailureReason | None,
        now_ns: int,
    ) -> BreakerDecision: ...

    def release_breaker_probe(
        self,
        *,
        execution_id: UUID,
        scope_tag: str,
        now_ns: int,
    ) -> None: ...

    def recover_open_breaker_probes(self, *, now_ns: int) -> int: ...

    def recover_open_execution_intents(self, *, now_ns: int) -> int: ...

    def try_admit_provider_dispatch(
        self,
        *,
        execution_id: UUID,
        attempt_number: int,
        request_id: UUID,
        execution_buckets: Sequence[BucketRequest],
        permit_scope_tags: PermitScopeTags,
        budget_scope_tags: BudgetScopeTags,
        pricing_policy: PricingPolicy,
        breaker_scope_tag: str,
        now_ns: int,
    ) -> tuple[
        BucketConsumptionResult | None,
        BreakerDecision,
        BudgetReservation | None,
        bool,
    ]: ...

    def finalize_provider_success(
        self,
        *,
        reservation: BudgetReservation,
        usage: ProviderUsage,
        actual_cost_micro_usd: int,
        breaker_scope_tag: str,
        now_ns: int,
    ) -> tuple[BudgetSettlement, BreakerDecision]: ...


@runtime_checkable
class SafetyControlProtocol(Protocol):
    @property
    def enabled(self) -> bool: ...

    def admit_ingress(self, *, peer_host: str) -> None: ...

    def admit_execution(self, *, request: DialogueRequestV1, execution_id: UUID) -> None: ...

    async def acquire_provider_permit(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
    ) -> ProviderPermit: ...

    async def release_provider_permit(self, permit: ProviderPermit, *, reason: str) -> None: ...

    def reserve_budget(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
        attempt_number: int,
    ) -> BudgetReservation: ...

    def mark_budget_dispatched(self, reservation: BudgetReservation) -> None: ...

    def settle_budget(
        self,
        reservation: BudgetReservation,
        *,
        usage: ProviderUsage,
    ) -> BudgetSettlement: ...

    def settle_budget_conservatively(
        self,
        reservation: BudgetReservation,
        *,
        reason: str,
    ) -> BudgetSettlement: ...

    def release_budget(self, reservation: BudgetReservation, *, reason: str) -> None: ...

    def check_provider_breaker(self, *, execution_id: UUID) -> BreakerDecision: ...

    def record_provider_success(self, *, execution_id: UUID) -> BreakerDecision: ...

    def record_provider_failure(
        self,
        *,
        execution_id: UUID,
        reason: BreakerFailureReason,
    ) -> BreakerDecision: ...

    def release_breaker_probe(self, *, execution_id: UUID) -> None: ...

    async def admit_provider_dispatch(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
        attempt_number: int,
    ) -> ProviderDispatchAdmission: ...

    async def finalize_provider_success(
        self,
        admission: ProviderDispatchAdmission,
        *,
        usage: ProviderUsage,
    ) -> ProviderSuccessFinalization: ...


class NoOpSafetyControl:
    """Explicit compatibility control for disabled composition and legacy unit tests."""

    @property
    def enabled(self) -> bool:
        return False

    def admit_ingress(self, *, peer_host: str) -> None:
        del peer_host

    def admit_execution(self, *, request: DialogueRequestV1, execution_id: UUID) -> None:
        del request, execution_id

    async def acquire_provider_permit(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
    ) -> ProviderPermit:
        del request
        return ProviderPermit(
            execution_id=execution_id,
            scope_tags=PermitScopeTags("0" * 64, "0" * 64, "0" * 64),
        )

    async def release_provider_permit(self, permit: ProviderPermit, *, reason: str) -> None:
        del permit, reason

    def reserve_budget(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
        attempt_number: int,
    ) -> BudgetReservation:
        del request, execution_id, attempt_number
        raise ControlUnavailableError

    def mark_budget_dispatched(self, reservation: BudgetReservation) -> None:
        del reservation

    def settle_budget(
        self,
        reservation: BudgetReservation,
        *,
        usage: ProviderUsage,
    ) -> BudgetSettlement:
        del reservation, usage
        raise ControlUnavailableError

    def settle_budget_conservatively(
        self,
        reservation: BudgetReservation,
        *,
        reason: str,
    ) -> BudgetSettlement:
        del reservation, reason
        raise ControlUnavailableError

    def release_budget(self, reservation: BudgetReservation, *, reason: str) -> None:
        del reservation, reason

    def check_provider_breaker(self, *, execution_id: UUID) -> BreakerDecision:
        del execution_id
        return BreakerDecision(BreakerState.CLOSED, BreakerOutcome.ALLOWED)

    def record_provider_success(self, *, execution_id: UUID) -> BreakerDecision:
        del execution_id
        return BreakerDecision(BreakerState.CLOSED, BreakerOutcome.NOT_REACHED)

    def record_provider_failure(
        self,
        *,
        execution_id: UUID,
        reason: BreakerFailureReason,
    ) -> BreakerDecision:
        del execution_id, reason
        return BreakerDecision(BreakerState.CLOSED, BreakerOutcome.NOT_REACHED)

    def release_breaker_probe(self, *, execution_id: UUID) -> None:
        del execution_id

    async def admit_provider_dispatch(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
        attempt_number: int,
    ) -> ProviderDispatchAdmission:
        del request, execution_id, attempt_number
        raise ControlUnavailableError

    async def finalize_provider_success(
        self,
        admission: ProviderDispatchAdmission,
        *,
        usage: ProviderUsage,
    ) -> ProviderSuccessFinalization:
        del admission, usage
        raise ControlUnavailableError

    def __repr__(self) -> str:
        return "NoOpSafetyControl()"


class SafetyControl:
    """Coordinate persistent rate admission and provider concurrency leases."""

    def __init__(
        self,
        *,
        repository: SafetyControlRepository,
        scope_key: bytes,
        clock_ns: Callable[[], int] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        permit_wait_seconds: float = 2.0,
        pricing_policy: PricingPolicy | None = None,
        storage_executor: StorageExecutor | None = None,
    ) -> None:
        if not isinstance(repository, SafetyControlRepository):
            raise TypeError("Safety control repository is invalid")
        if not isinstance(scope_key, bytes) or len(scope_key) < _MIN_KEY_BYTES:
            raise ValueError("Safety control scope key is invalid")
        if not isinstance(permit_wait_seconds, (int, float)) or not 0 < permit_wait_seconds <= 2:
            raise ValueError("Safety control permit wait is invalid")
        self._storage_executor = storage_executor
        self._repository = repository
        self._scope_key = scope_key
        self._clock_ns = clock_ns or time.time_ns
        self._monotonic_clock = monotonic_clock or time.monotonic
        self._sleep = sleep or asyncio.sleep
        self._permit_wait_seconds = float(permit_wait_seconds)
        self._pricing_policy = pricing_policy
        self._breaker_scope_tag = (
            None
            if pricing_policy is None
            else self._control_tag(
                ControlScope.INGRESS_GLOBAL,
                f"breaker\0{pricing_policy.provider_kind.value}\0{pricing_policy.model}",
            )
        )
        self._permit_condition = asyncio.Condition()
        self._now_ns()
        try:
            self._repository.recover_open_execution_intents(now_ns=self._now_ns())
            self._repository.recover_open_permits(now_ns=self._now_ns())
            self._repository.recover_open_budget_attempts(now_ns=self._now_ns())
            self._repository.recover_open_breaker_probes(now_ns=self._now_ns())
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def bind_storage_executor(self, executor: StorageExecutor) -> None:
        if self._storage_executor is not None and self._storage_executor is not executor:
            raise ValueError("Safety control executor is already bound")
        self._storage_executor = executor

    @property
    def enabled(self) -> bool:
        return True

    def admit_ingress(self, *, peer_host: str) -> None:
        try:
            peer = ipaddress.ip_address(peer_host).compressed
        except (TypeError, ValueError):
            raise ControlUnavailableError from None
        buckets = (
            BucketRequest(
                BUCKET_SPECS[ControlScope.INGRESS_GLOBAL],
                self._control_tag(ControlScope.INGRESS_GLOBAL, "global"),
            ),
            BucketRequest(
                BUCKET_SPECS[ControlScope.DIRECT_PEER],
                self._control_tag(ControlScope.DIRECT_PEER, peer),
            ),
        )
        try:
            decision = self._repository.consume_ingress(buckets=buckets, now_ns=self._now_ns())
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error
        self._raise_for_decision(decision)

    async def admit_provider_dispatch(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
        attempt_number: int,
    ) -> ProviderDispatchAdmission:
        if self._pricing_policy is None or self._breaker_scope_tag is None:
            raise ControlUnavailableError
        if not isinstance(request, DialogueRequestV1) or not isinstance(execution_id, UUID):
            raise TypeError("Safety control provider dispatch admission is invalid")
        permit_scope_tags = self._scope_tags(request)
        execution_buckets = self._execution_buckets(permit_scope_tags)
        budget_scope_tags = self._budget_scope_tags(request)
        deadline = self._monotonic_clock() + self._permit_wait_seconds
        pending_reservation: BudgetReservation | None = None
        try:
            while True:
                rate_decision, breaker, reservation, acquired = await call_storage(
                    self._storage_executor,
                    "control",
                    partial(
                        self._repository.try_admit_provider_dispatch,
                        execution_id=execution_id,
                        attempt_number=attempt_number,
                        request_id=request.request_id,
                        execution_buckets=execution_buckets,
                        permit_scope_tags=permit_scope_tags,
                        budget_scope_tags=budget_scope_tags,
                        pricing_policy=self._pricing_policy,
                        breaker_scope_tag=self._breaker_scope_tag,
                        now_ns=self._now_ns(),
                    ),
                    finish_on_cancel=True,
                )
                if rate_decision is not None:
                    self._raise_for_decision(rate_decision)
                if breaker.outcome is BreakerOutcome.REJECTED:
                    if breaker.retry_after_seconds is None:
                        raise ControlUnavailableError
                    raise CircuitOpenError(breaker.retry_after_seconds)
                if acquired:
                    if reservation is None:
                        raise ControlUnavailableError
                    pending_reservation = reservation
                    return ProviderDispatchAdmission(
                        breaker_decision=breaker,
                        reservation=reservation,
                        permit=ProviderPermit(
                            execution_id=execution_id,
                            scope_tags=permit_scope_tags,
                        ),
                    )
                remaining = deadline - self._monotonic_clock()
                if remaining <= 0:
                    raise ControlCapacityError
                async with self._permit_condition:
                    try:
                        await asyncio.wait_for(
                            self._permit_condition.wait(),
                            timeout=min(remaining, 0.05),
                        )
                    except TimeoutError:
                        await self._sleep(0)
        except BudgetRejectedError:
            raise
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error
        except BaseException:
            if pending_reservation is not None:
                try:
                    await call_storage(
                        self._storage_executor,
                        "control",
                        partial(
                            self._repository.release_budget,
                            reservation=pending_reservation,
                            reason="cancelled_before_dispatch",
                            now_ns=self._now_ns(),
                        ),
                        finish_on_cancel=True,
                    )
                    await call_storage(
                        self._storage_executor,
                        "control",
                        partial(
                            self._repository.release_breaker_probe,
                            execution_id=execution_id,
                            scope_tag=self._breaker_scope_tag,
                            now_ns=self._now_ns(),
                        ),
                        finish_on_cancel=True,
                    )
                except ControlRepositoryError as error:
                    raise ControlUnavailableError from error
            raise

    async def finalize_provider_success(
        self,
        admission: ProviderDispatchAdmission,
        *,
        usage: ProviderUsage,
    ) -> ProviderSuccessFinalization:
        if (
            not isinstance(admission, ProviderDispatchAdmission)
            or not isinstance(usage, ProviderUsage)
            or self._pricing_policy is None
            or self._breaker_scope_tag is None
        ):
            raise ControlUnavailableError
        actual_cost = calculate_cost_micro_usd(policy=self._pricing_policy, usage=usage)
        try:
            settlement, breaker = await call_storage(
                self._storage_executor,
                "control",
                partial(
                    self._repository.finalize_provider_success,
                    reservation=admission.reservation,
                    usage=usage,
                    actual_cost_micro_usd=actual_cost,
                    breaker_scope_tag=self._breaker_scope_tag,
                    now_ns=self._now_ns(),
                ),
                finish_on_cancel=True,
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error
        async with self._permit_condition:
            self._permit_condition.notify_all()
        return ProviderSuccessFinalization(settlement=settlement, breaker_decision=breaker)

    def admit_execution(self, *, request: DialogueRequestV1, execution_id: UUID) -> None:
        if not isinstance(request, DialogueRequestV1) or not isinstance(execution_id, UUID):
            raise TypeError("Safety control execution admission is invalid")
        scope_tags = self._scope_tags(request)
        buckets = self._execution_buckets(scope_tags)
        try:
            decision = self._repository.consume_execution_admission(
                buckets=buckets,
                execution_id=execution_id,
                request_id=request.request_id,
                scope_tags=scope_tags,
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error
        self._raise_for_decision(decision)

    @staticmethod
    def _execution_buckets(scope_tags: PermitScopeTags) -> tuple[BucketRequest, ...]:
        return (
            BucketRequest(BUCKET_SPECS[ControlScope.PLAYER], scope_tags.player_scope_tag),
            BucketRequest(
                BUCKET_SPECS[ControlScope.PLAYER_NPC],
                scope_tags.player_npc_scope_tag,
            ),
            BucketRequest(
                BUCKET_SPECS[ControlScope.CONVERSATION],
                scope_tags.conversation_scope_tag,
            ),
        )

    async def acquire_provider_permit(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
    ) -> ProviderPermit:
        if not isinstance(request, DialogueRequestV1) or not isinstance(execution_id, UUID):
            raise TypeError("Safety control provider admission is invalid")
        scope_tags = self._scope_tags(request)
        deadline = self._monotonic_clock() + self._permit_wait_seconds
        while True:
            try:
                acquired = await call_storage(
                    self._storage_executor,
                    "control",
                    partial(
                        self._repository.try_acquire_permit,
                        execution_id=execution_id,
                        scope_tags=scope_tags,
                        acquired_at_ns=self._now_ns(),
                    ),
                    finish_on_cancel=True,
                )
            except ControlRepositoryError as error:
                raise ControlUnavailableError from error
            if acquired:
                return ProviderPermit(execution_id=execution_id, scope_tags=scope_tags)
            remaining = deadline - self._monotonic_clock()
            if remaining <= 0:
                raise ControlCapacityError
            async with self._permit_condition:
                try:
                    await asyncio.wait_for(
                        self._permit_condition.wait(),
                        timeout=min(remaining, 0.05),
                    )
                except TimeoutError:
                    await self._sleep(0)

    async def release_provider_permit(self, permit: ProviderPermit, *, reason: str) -> None:
        if not isinstance(permit, ProviderPermit):
            raise TypeError("Safety control permit is invalid")
        try:
            await call_storage(
                self._storage_executor,
                "control",
                partial(
                    self._repository.release_permit,
                    execution_id=permit.execution_id,
                    released_at_ns=self._now_ns(),
                    reason=reason,
                ),
                finish_on_cancel=True,
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error
        async with self._permit_condition:
            self._permit_condition.notify_all()

    def reserve_budget(
        self,
        *,
        request: DialogueRequestV1,
        execution_id: UUID,
        attempt_number: int,
    ) -> BudgetReservation:
        if self._pricing_policy is None:
            raise ControlUnavailableError
        try:
            return self._repository.reserve_budget(
                execution_id=execution_id,
                attempt_number=attempt_number,
                scope_tags=self._budget_scope_tags(request),
                pricing_policy=self._pricing_policy,
                now_ns=self._now_ns(),
            )
        except BudgetRejectedError:
            raise
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def mark_budget_dispatched(self, reservation: BudgetReservation) -> None:
        try:
            self._repository.mark_budget_dispatched(
                reservation=reservation,
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def settle_budget(
        self,
        reservation: BudgetReservation,
        *,
        usage: ProviderUsage,
    ) -> BudgetSettlement:
        if self._pricing_policy is None:
            raise ControlUnavailableError
        actual_cost = calculate_cost_micro_usd(policy=self._pricing_policy, usage=usage)
        try:
            return self._repository.settle_budget(
                reservation=reservation,
                usage=usage,
                actual_cost_micro_usd=actual_cost,
                conservative=False,
                reason="trusted_usage",
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def settle_budget_conservatively(
        self,
        reservation: BudgetReservation,
        *,
        reason: str,
    ) -> BudgetSettlement:
        try:
            return self._repository.settle_budget(
                reservation=reservation,
                usage=None,
                actual_cost_micro_usd=reservation.reserved_micro_usd,
                conservative=True,
                reason=reason,
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def release_budget(self, reservation: BudgetReservation, *, reason: str) -> None:
        try:
            self._repository.release_budget(
                reservation=reservation,
                reason=reason,
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def check_provider_breaker(self, *, execution_id: UUID) -> BreakerDecision:
        if not isinstance(execution_id, UUID) or self._breaker_scope_tag is None:
            raise ControlUnavailableError
        try:
            decision = self._repository.check_breaker(
                execution_id=execution_id,
                scope_tag=self._breaker_scope_tag,
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error
        if not isinstance(decision, BreakerDecision):
            raise ControlUnavailableError
        if decision.outcome is BreakerOutcome.REJECTED:
            if decision.retry_after_seconds is None:
                raise ControlUnavailableError
            raise CircuitOpenError(decision.retry_after_seconds)
        return decision

    def record_provider_success(self, *, execution_id: UUID) -> BreakerDecision:
        return self._record_provider_result(
            execution_id=execution_id,
            success=True,
            reason=None,
        )

    def record_provider_failure(
        self,
        *,
        execution_id: UUID,
        reason: BreakerFailureReason,
    ) -> BreakerDecision:
        if not isinstance(reason, BreakerFailureReason):
            raise TypeError("Circuit-breaker failure reason is invalid")
        return self._record_provider_result(
            execution_id=execution_id,
            success=False,
            reason=reason,
        )

    def release_breaker_probe(self, *, execution_id: UUID) -> None:
        if not isinstance(execution_id, UUID) or self._breaker_scope_tag is None:
            raise ControlUnavailableError
        try:
            self._repository.release_breaker_probe(
                execution_id=execution_id,
                scope_tag=self._breaker_scope_tag,
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def _record_provider_result(
        self,
        *,
        execution_id: UUID,
        success: bool,
        reason: BreakerFailureReason | None,
    ) -> BreakerDecision:
        if not isinstance(execution_id, UUID) or self._breaker_scope_tag is None:
            raise ControlUnavailableError
        try:
            return self._repository.record_breaker_result(
                execution_id=execution_id,
                scope_tag=self._breaker_scope_tag,
                success=success,
                failure_reason=reason,
                now_ns=self._now_ns(),
            )
        except ControlRepositoryError as error:
            raise ControlUnavailableError from error

    def _budget_scope_tags(self, request: DialogueRequestV1) -> BudgetScopeTags:
        player_tag = derive_scope_tag(
            key=self._scope_key,
            dimension=ScopeDimension.PLAYER,
            identifier=request.player_id,
        )
        npc_tag = derive_scope_tag(
            key=self._scope_key,
            dimension=ScopeDimension.NPC,
            identifier=request.npc_id,
        )
        return BudgetScopeTags(
            player_scope_tag=player_tag,
            npc_scope_tag=npc_tag,
            player_npc_scope_tag=self._control_tag(
                ControlScope.PLAYER_NPC,
                f"{player_tag}\0{npc_tag}",
            ),
        )

    def _scope_tags(self, request: DialogueRequestV1) -> PermitScopeTags:
        player_tag = derive_scope_tag(
            key=self._scope_key,
            dimension=ScopeDimension.PLAYER,
            identifier=request.player_id,
        )
        npc_tag = derive_scope_tag(
            key=self._scope_key,
            dimension=ScopeDimension.NPC,
            identifier=request.npc_id,
        )
        conversation_tag = derive_scope_tag(
            key=self._scope_key,
            dimension=ScopeDimension.CONVERSATION,
            identifier=str(request.conversation_id),
        )
        return PermitScopeTags(
            player_scope_tag=player_tag,
            player_npc_scope_tag=self._control_tag(
                ControlScope.PLAYER_NPC,
                f"{player_tag}\0{npc_tag}",
            ),
            conversation_scope_tag=conversation_tag,
        )

    def _control_tag(self, scope: ControlScope, identifier: str) -> str:
        domain = f"cyber-town:f009:control:v1:{scope.value}\0".encode()
        return hmac.new(
            self._scope_key,
            domain + identifier.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _now_ns(self) -> int:
        value = self._clock_ns()
        if type(value) is not int or value <= 0:
            raise ControlUnavailableError
        return value

    @staticmethod
    def _raise_for_decision(decision: BucketConsumptionResult) -> None:
        if not isinstance(decision, BucketConsumptionResult):
            raise ControlUnavailableError
        if decision.outcome is RateLimitOutcome.ALLOWED:
            return
        if decision.outcome is RateLimitOutcome.REJECTED:
            if decision.retry_after_seconds is None:
                raise ControlUnavailableError
            raise RateLimitExceededError(decision.retry_after_seconds)
        raise ControlUnavailableError

    def __repr__(self) -> str:
        return "SafetyControl()"


def retry_after_seconds(*, missing_microtokens: int, refill_per_minute: int) -> int:
    """Return the public bounded delay without exposing a bucket balance."""

    if type(missing_microtokens) is not int or missing_microtokens <= 0:
        raise ValueError("Missing control token amount is invalid")
    if type(refill_per_minute) is not int or refill_per_minute <= 0:
        raise ValueError("Control refill is invalid")
    seconds = math.ceil(missing_microtokens * 60 / (refill_per_minute * 1_000_000))
    return min(60, max(1, seconds))


def _require_tag(value: object) -> None:
    if not isinstance(value, str):
        raise TypeError("Control scope tag is invalid")
    if _TAG_PATTERN.fullmatch(value) is None:
        raise ValueError("Control scope tag is invalid")
