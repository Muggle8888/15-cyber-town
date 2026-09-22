"""Versioned, metadata-only pricing and budget contracts for F-009 Step 3."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from typing import Protocol, runtime_checkable
from uuid import UUID

from cyber_town.application.observability import ProviderKind
from cyber_town.application.provider import ProviderUsage
from cyber_town.application.safety import BudgetOutcome
from cyber_town.config import DEEPSEEK_MODEL

BUDGET_POLICY_VERSION = "f-009-budget-policy-v1"
SYNTHETIC_PRICING_VERSION = "f-009-synthetic-pricing-v1"
DEEPSEEK_FLASH_PRICING_VERSION = "deepseek-v4.1-flash-2026-09-10-peak-v1"
MAX_EXECUTION_ATTEMPTS = 2
MAX_RESERVATION_MICRO_USD = 11_000
_VERSION_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
_TAG_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_MILLION = 1_000_000


class BudgetLimitClass(StrEnum):
    EXECUTION_ATTEMPTS = "execution_attempts"
    PLAYER_NPC_ATTEMPTS_1H = "player_npc_attempts_1h"
    PLAYER_NPC_ATTEMPTS_24H = "player_npc_attempts_24h"
    PLAYER_ATTEMPTS_1H = "player_attempts_1h"
    PLAYER_ATTEMPTS_24H = "player_attempts_24h"
    NPC_ATTEMPTS_1H = "npc_attempts_1h"
    NPC_ATTEMPTS_24H = "npc_attempts_24h"
    GLOBAL_ATTEMPTS_1H = "global_attempts_1h"
    GLOBAL_ATTEMPTS_24H = "global_attempts_24h"
    PLAYER_NPC_COST_24H = "player_npc_cost_24h"
    PLAYER_COST_24H = "player_cost_24h"
    NPC_COST_24H = "npc_cost_24h"
    GLOBAL_COST_24H = "global_cost_24h"
    EXECUTION_RESERVE = "execution_reserve"


class BudgetEventKind(StrEnum):
    RESERVATION = "reservation"
    DISPATCH = "dispatch"
    SETTLEMENT = "settlement"
    RELEASE = "release"
    REJECTION = "rejection"


@dataclass(frozen=True, slots=True)
class BudgetWindowSpec:
    limit_class: BudgetLimitClass
    window_seconds: int
    hard_limit: int
    cost_window: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.limit_class, BudgetLimitClass):
            raise TypeError("Budget limit class is invalid")
        if type(self.window_seconds) is not int or self.window_seconds not in (3_600, 86_400):
            raise ValueError("Budget window duration is invalid")
        if type(self.hard_limit) is not int or self.hard_limit <= 0:
            raise ValueError("Budget hard limit is invalid")
        if type(self.cost_window) is not bool:
            raise TypeError("Budget window kind is invalid")

    @property
    def warning_threshold(self) -> int:
        return math.ceil(self.hard_limit * 4 / 5)


ATTEMPT_WINDOW_SPECS = (
    BudgetWindowSpec(BudgetLimitClass.PLAYER_NPC_ATTEMPTS_1H, 3_600, 15),
    BudgetWindowSpec(BudgetLimitClass.PLAYER_NPC_ATTEMPTS_24H, 86_400, 50),
    BudgetWindowSpec(BudgetLimitClass.PLAYER_ATTEMPTS_1H, 3_600, 30),
    BudgetWindowSpec(BudgetLimitClass.PLAYER_ATTEMPTS_24H, 86_400, 100),
    BudgetWindowSpec(BudgetLimitClass.NPC_ATTEMPTS_1H, 3_600, 120),
    BudgetWindowSpec(BudgetLimitClass.NPC_ATTEMPTS_24H, 86_400, 500),
    BudgetWindowSpec(BudgetLimitClass.GLOBAL_ATTEMPTS_1H, 3_600, 300),
    BudgetWindowSpec(BudgetLimitClass.GLOBAL_ATTEMPTS_24H, 86_400, 1_000),
)

COST_WINDOW_SPECS = (
    BudgetWindowSpec(BudgetLimitClass.PLAYER_NPC_COST_24H, 86_400, 25_000, True),
    BudgetWindowSpec(BudgetLimitClass.PLAYER_COST_24H, 86_400, 50_000, True),
    BudgetWindowSpec(BudgetLimitClass.NPC_COST_24H, 86_400, 250_000, True),
    BudgetWindowSpec(BudgetLimitClass.GLOBAL_COST_24H, 86_400, 500_000, True),
)


@dataclass(frozen=True, slots=True, repr=False)
class PricingPolicy:
    version: str
    provider_kind: ProviderKind
    model: str
    input_micro_usd_per_million_tokens: int
    output_micro_usd_per_million_tokens: int
    max_reservation_micro_usd: int

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or _VERSION_PATTERN.fullmatch(self.version) is None:
            raise ValueError("Pricing policy version is invalid")
        if not isinstance(self.provider_kind, ProviderKind):
            raise TypeError("Pricing provider kind is invalid")
        if not isinstance(self.model, str) or _MODEL_PATTERN.fullmatch(self.model) is None:
            raise ValueError("Pricing model is invalid")
        for value in (
            self.input_micro_usd_per_million_tokens,
            self.output_micro_usd_per_million_tokens,
            self.max_reservation_micro_usd,
        ):
            if type(value) is not int or value < 0:
                raise ValueError("Pricing amount is invalid")
        if self.max_reservation_micro_usd > MAX_RESERVATION_MICRO_USD:
            raise ValueError("Pricing reservation exceeds the approved cap")
        if self.provider_kind in (
            ProviderKind.FAKE,
            ProviderKind.LOCAL_FALLBACK,
            ProviderKind.DISABLED,
        ) and any(
            (
                self.input_micro_usd_per_million_tokens,
                self.output_micro_usd_per_million_tokens,
                self.max_reservation_micro_usd,
            )
        ):
            raise ValueError("Non-billable pricing must remain zero")
        maximum_cost = math.ceil(
            (
                32_768 * self.input_micro_usd_per_million_tokens
                + 256 * self.output_micro_usd_per_million_tokens
            )
            / _MILLION
        )
        if maximum_cost > self.max_reservation_micro_usd:
            raise ValueError("Pricing reservation cannot cover the approved token bounds")

    @classmethod
    def zero_cost(cls, *, provider_kind: ProviderKind, model: str) -> PricingPolicy:
        if provider_kind not in (
            ProviderKind.FAKE,
            ProviderKind.LOCAL_FALLBACK,
            ProviderKind.DISABLED,
        ):
            raise ValueError("Zero-cost policy provider is invalid")
        return cls(
            version=f"f-009-{provider_kind.value}-zero-v1",
            provider_kind=provider_kind,
            model=model,
            input_micro_usd_per_million_tokens=0,
            output_micro_usd_per_million_tokens=0,
            max_reservation_micro_usd=0,
        )


SYNTHETIC_PRICING_POLICY = PricingPolicy(
    version=SYNTHETIC_PRICING_VERSION,
    provider_kind=ProviderKind.DEEPSEEK,
    model="fake-model",
    input_micro_usd_per_million_tokens=1_000,
    output_micro_usd_per_million_tokens=2_000,
    max_reservation_micro_usd=2_000,
)

DEEPSEEK_FLASH_PEAK_PRICING_POLICY = PricingPolicy(
    version=DEEPSEEK_FLASH_PRICING_VERSION,
    provider_kind=ProviderKind.DEEPSEEK,
    model=DEEPSEEK_MODEL,
    input_micro_usd_per_million_tokens=300_000,
    output_micro_usd_per_million_tokens=1_200_000,
    max_reservation_micro_usd=10_138,
)


def calculate_cost_micro_usd(*, policy: PricingPolicy, usage: ProviderUsage) -> int:
    if not isinstance(policy, PricingPolicy) or not isinstance(usage, ProviderUsage):
        raise TypeError("Pricing calculation input is invalid")
    numerator = (
        usage.prompt_tokens * policy.input_micro_usd_per_million_tokens
        + usage.completion_tokens * policy.output_micro_usd_per_million_tokens
    )
    if numerator == 0:
        return 0
    return math.ceil(numerator / _MILLION)


@dataclass(frozen=True, slots=True, repr=False)
class BudgetScopeTags:
    player_scope_tag: str
    npc_scope_tag: str
    player_npc_scope_tag: str

    def __post_init__(self) -> None:
        if any(_TAG_PATTERN.fullmatch(value) is None for value in self.as_tuple()):
            raise ValueError("Budget scope tag is invalid")

    def as_tuple(self) -> tuple[str, str, str]:
        return self.player_scope_tag, self.npc_scope_tag, self.player_npc_scope_tag


@dataclass(frozen=True, slots=True, repr=False)
class BudgetReservation:
    execution_id: UUID
    attempt_number: int
    policy_version: str
    pricing_version: str
    provider_kind: ProviderKind
    reserved_micro_usd: int
    soft_warning: bool
    scope_tags: BudgetScopeTags
    outcome: BudgetOutcome = BudgetOutcome.RESERVED

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, UUID):
            raise TypeError("Budget execution identifier is invalid")
        if type(self.attempt_number) is not int or not 1 <= self.attempt_number <= 2:
            raise ValueError("Budget attempt number is invalid")
        if self.policy_version != BUDGET_POLICY_VERSION:
            raise ValueError("Budget policy version is invalid")
        if (
            not isinstance(self.pricing_version, str)
            or _VERSION_PATTERN.fullmatch(self.pricing_version) is None
        ):
            raise ValueError("Budget pricing version is invalid")
        if not isinstance(self.provider_kind, ProviderKind):
            raise TypeError("Budget provider kind is invalid")
        if (
            type(self.reserved_micro_usd) is not int
            or not 0 <= self.reserved_micro_usd <= MAX_RESERVATION_MICRO_USD
        ):
            raise ValueError("Budget reservation amount is invalid")
        if type(self.soft_warning) is not bool:
            raise TypeError("Budget warning metadata is invalid")
        if not isinstance(self.scope_tags, BudgetScopeTags):
            raise TypeError("Budget scope metadata is invalid")
        if self.outcome is not BudgetOutcome.RESERVED:
            raise ValueError("Budget reservation outcome is invalid")


@dataclass(frozen=True, slots=True, repr=False)
class BudgetSettlement:
    execution_id: UUID
    attempt_number: int
    policy_version: str
    pricing_version: str
    reserved_micro_usd: int
    actual_cost_micro_usd: int
    released_micro_usd: int
    prompt_tokens: int
    completion_tokens: int
    conservative: bool
    outcome: BudgetOutcome = BudgetOutcome.SETTLED

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, UUID):
            raise TypeError("Budget settlement execution is invalid")
        if type(self.attempt_number) is not int or not 1 <= self.attempt_number <= 2:
            raise ValueError("Budget settlement attempt is invalid")
        for value in (
            self.reserved_micro_usd,
            self.actual_cost_micro_usd,
            self.released_micro_usd,
            self.prompt_tokens,
            self.completion_tokens,
        ):
            if type(value) is not int or value < 0:
                raise ValueError("Budget settlement amount is invalid")
        if self.actual_cost_micro_usd + self.released_micro_usd != self.reserved_micro_usd:
            raise ValueError("Budget settlement totals are inconsistent")
        if type(self.conservative) is not bool:
            raise TypeError("Budget settlement mode is invalid")
        if self.outcome is not BudgetOutcome.SETTLED:
            raise ValueError("Budget settlement outcome is invalid")


class BudgetRejectedError(RuntimeError):
    def __init__(
        self,
        limit_class: BudgetLimitClass,
        *,
        scope_tags: BudgetScopeTags | None = None,
        pricing_policy: PricingPolicy | None = None,
    ) -> None:
        if not isinstance(limit_class, BudgetLimitClass):
            raise TypeError("Budget rejection class is invalid")
        super().__init__("Dialogue budget is exhausted.")
        self.limit_class = limit_class
        self.scope_tags = scope_tags
        self.pricing_policy = pricing_policy

    def __repr__(self) -> str:
        return "BudgetRejectedError()"


@dataclass(frozen=True, slots=True, repr=False)
class SafetyCostMetadata:
    trace_id: UUID
    execution_id: UUID
    attempt_number: int
    event_kind: BudgetEventKind
    outcome: BudgetOutcome
    policy_version: str
    pricing_version: str
    provider_kind: ProviderKind
    scope_tags: BudgetScopeTags
    reserved_micro_usd: int
    actual_cost_micro_usd: int
    prompt_tokens: int
    completion_tokens: int
    conservative: bool
    recorded_at_utc: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.trace_id, UUID) or not isinstance(self.execution_id, UUID):
            raise TypeError("Safety-cost linkage is invalid")
        if type(self.attempt_number) is not int or not 1 <= self.attempt_number <= 2:
            raise ValueError("Safety-cost attempt is invalid")
        if not isinstance(self.event_kind, BudgetEventKind):
            raise TypeError("Safety-cost event kind is invalid")
        if not isinstance(self.outcome, BudgetOutcome):
            raise TypeError("Safety-cost outcome is invalid")
        if self.policy_version != BUDGET_POLICY_VERSION:
            raise ValueError("Safety-cost policy version is invalid")
        if (
            not isinstance(self.pricing_version, str)
            or _VERSION_PATTERN.fullmatch(self.pricing_version) is None
        ):
            raise ValueError("Safety-cost pricing version is invalid")
        if not isinstance(self.provider_kind, ProviderKind):
            raise TypeError("Safety-cost provider kind is invalid")
        if not isinstance(self.scope_tags, BudgetScopeTags):
            raise TypeError("Safety-cost scope tags are invalid")
        for value in (
            self.reserved_micro_usd,
            self.actual_cost_micro_usd,
            self.prompt_tokens,
            self.completion_tokens,
        ):
            if type(value) is not int or value < 0:
                raise ValueError("Safety-cost numeric metadata is invalid")
        if self.actual_cost_micro_usd > self.reserved_micro_usd:
            raise ValueError("Safety-cost amount is invalid")
        if type(self.conservative) is not bool:
            raise TypeError("Safety-cost settlement mode is invalid")
        if (
            not isinstance(self.recorded_at_utc, datetime)
            or self.recorded_at_utc.tzinfo is None
            or self.recorded_at_utc.utcoffset() != UTC.utcoffset(self.recorded_at_utc)
        ):
            raise ValueError("Safety-cost timestamp must use UTC")


@runtime_checkable
class SafetyCostRecorder(Protocol):
    def record_safety_cost(self, record: SafetyCostMetadata) -> None: ...


class NoOpSafetyCostRecorder:
    __slots__ = ()

    def record_safety_cost(self, record: SafetyCostMetadata) -> None:
        if not isinstance(record, SafetyCostMetadata):
            raise TypeError("Safety-cost record is invalid")


class InMemorySafetyCostRecorder:
    __slots__ = ("_lock", "_records")

    def __init__(self) -> None:
        self._lock = Lock()
        self._records: list[SafetyCostMetadata] = []

    def record_safety_cost(self, record: SafetyCostMetadata) -> None:
        if not isinstance(record, SafetyCostMetadata):
            raise TypeError("Safety-cost record is invalid")
        with self._lock:
            self._records.append(record)

    def snapshot(self) -> Sequence[SafetyCostMetadata]:
        with self._lock:
            return tuple(self._records)


@runtime_checkable
class BudgetRepository(Protocol):
    def recover_open_budget_attempts(self, *, now_ns: int) -> tuple[int, int]: ...

    def reserve_budget(
        self,
        *,
        execution_id: UUID,
        attempt_number: int,
        scope_tags: BudgetScopeTags,
        pricing_policy: PricingPolicy,
        now_ns: int,
    ) -> BudgetReservation: ...

    def mark_budget_dispatched(self, *, reservation: BudgetReservation, now_ns: int) -> None: ...

    def settle_budget(
        self,
        *,
        reservation: BudgetReservation,
        usage: ProviderUsage | None,
        actual_cost_micro_usd: int,
        conservative: bool,
        reason: str,
        now_ns: int,
    ) -> BudgetSettlement: ...

    def release_budget(
        self,
        *,
        reservation: BudgetReservation,
        reason: str,
        now_ns: int,
    ) -> None: ...
