"""Bounded, content-redacted F-010 real-provider acceptance runner."""

from __future__ import annotations

import argparse
import asyncio
import secrets
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Final
from uuid import UUID, uuid4

from pydantic import SecretStr

from cyber_town.api.composition import build_dialogue_service
from cyber_town.application.acceptance import MeteredAcceptanceProvider
from cyber_town.application.budget import (
    DEEPSEEK_FLASH_PEAK_PRICING_POLICY,
    calculate_cost_micro_usd,
)
from cyber_town.application.control import SafetyControl
from cyber_town.application.dialogue import DialogueService
from cyber_town.application.provider import ProviderCompletion, ProviderProtocol, ProviderRequest
from cyber_town.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, PROJECT_ROOT, LlmProvider, Settings
from cyber_town.contracts.v1 import DialogueRequestV1, DialogueResponseV1, DialogueStatus
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.llm.deepseek import DeepSeekProvider
from cyber_town.infrastructure.persistence.acceptance_ledger import (
    AcceptanceLedger,
    AcceptanceStep,
    AcceptanceSummary,
)
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import (
    SqliteRelationshipRepository,
)

AUTHORIZATION_ID: Final = "f010-real-provider-uat-20260922"
PLAYER_ID: Final = "f010_uat_player"
UAT_ROOT: Final = PROJECT_ROOT / "data" / "uat" / "f-010"
BUSINESS_DATABASE: Final = UAT_ROOT / "cyber-town.sqlite3"
CONTROL_DATABASE: Final = UAT_ROOT / "cyber-town-control.sqlite3"
LEDGER_ROOT: Final = PROJECT_ROOT / "data" / "acceptance-ledgers"
LEDGER_DATABASE: Final = LEDGER_ROOT / "f-010.sqlite3"
EXPECTED_CALLS: Final = 7
RECOVERY_CALLS: Final = 6
MAX_CALLS: Final = 9
MAX_COST_MICRO_USD: Final = 50_000
RESERVED_MICRO_USD_PER_CALL: Final = 10_138

_NPC_IDS: Final = {
    "Nia": "neon_guide",
    "Ivo": "signal_archivist",
    "Rhea": "night_courier",
}
_UNKNOWN_MARKERS: Final = ("不知道", "不清楚", "没有", "未曾", "未记录", "unknown")
_TOPIC: Final = "霓虹夜市"


class UatError(RuntimeError):
    """A content-redacted acceptance failure with one stable reason code."""


@dataclass(frozen=True, slots=True)
class UatOutcome:
    """Metadata-only result suitable for console and project evidence."""

    checks: int
    summary: AcceptanceSummary


class _RecoveryScopeAssertionProvider:
    """Assert redacted long-term scope at the provider boundary before metering."""

    def __init__(self, provider: ProviderProtocol) -> None:
        self._provider = provider
        self.call_count = 0

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        self.call_count += 1
        if self.call_count == 3 and tuple(fact.fact_value for fact in request.long_term_facts) != (
            _TOPIC,
        ):
            raise UatError("nia_long_term_scope_missing")
        if self.call_count == 4 and request.long_term_facts:
            raise UatError("ivo_cross_npc_long_term_scope_leak")
        return await self._provider.complete(request)


def _settings_from_authorized_dotenv() -> Settings:
    settings = Settings(
        llm_provider=LlmProvider.DEEPSEEK,
        llm_model=DEEPSEEK_MODEL,
        llm_base_url=DEEPSEEK_BASE_URL,
        llm_max_tokens=256,
        llm_timeout_seconds=12.0,
        llm_max_retries=0,
        llm_thinking_enabled=False,
        llm_stream=False,
    )
    if settings.llm_api_key is None or not settings.llm_api_key.get_secret_value().strip():
        raise UatError("provider_credential_unavailable")
    return settings


def _validate_resource_boundaries(*, create: bool) -> None:
    data_root = (PROJECT_ROOT / "data").resolve(strict=True)
    for path in (UAT_ROOT, LEDGER_ROOT, BUSINESS_DATABASE, CONTROL_DATABASE, LEDGER_DATABASE):
        resolved = path.resolve(strict=False)
        if not resolved.is_relative_to(data_root):
            raise UatError("resource_outside_project_data")
        for current in (path, *path.parents):
            if current.exists() and (current.is_symlink() or current.is_junction()):
                raise UatError("resource_reparse_boundary")
            if current.resolve(strict=False) == data_root:
                break
    if not LEDGER_ROOT.is_dir():
        raise UatError("acceptance_ledger_parent_unavailable")
    if create:
        UAT_ROOT.mkdir(parents=False, exist_ok=True)


def _ledger(*, allow_unresolved: bool = False) -> AcceptanceLedger:
    ledger = AcceptanceLedger(database_path=LEDGER_DATABASE, allowed_root=LEDGER_ROOT)
    ledger.initialize()
    summary = ledger.summary()
    if summary.pending_calls and not allow_unresolved:
        raise UatError("acceptance_ledger_has_unresolved_call")
    if summary.total_calls > MAX_CALLS or summary.total_micro_usd > MAX_COST_MICRO_USD:
        raise UatError("acceptance_ledger_exceeds_authorization")
    return ledger


def _build_service(
    *,
    settings: Settings,
    provider: ProviderProtocol,
    control_scope_key: bytes,
    clock_ns: Callable[[], int] | None = None,
) -> DialogueService:
    memory = SqliteLongTermMemoryRepository(
        database_path=BUSINESS_DATABASE,
        allowed_root=UAT_ROOT,
    )
    memory.initialize()
    relationships = SqliteRelationshipRepository(
        database_path=BUSINESS_DATABASE,
        allowed_root=UAT_ROOT,
    )
    relationships.initialize()
    control = SqliteSafetyControlRepository(
        database_path=CONTROL_DATABASE,
        allowed_root=UAT_ROOT,
    )
    control.initialize()
    safety_control = SafetyControl(
        repository=control,
        scope_key=control_scope_key,
        clock_ns=clock_ns,
        pricing_policy=DEEPSEEK_FLASH_PEAK_PRICING_POLICY,
    )
    service = build_dialogue_service(
        settings,
        provider=provider,
        long_term_repository=memory,
        relationship_repository=relationships,
        safety_control=safety_control,
    )
    if service is None:
        raise UatError("dialogue_service_unavailable")
    return service


async def _send(
    service: DialogueService,
    *,
    npc_id: str,
    conversation_id: UUID,
    message: str,
) -> DialogueResponseV1:
    response = await service.execute(
        DialogueRequestV1(
            request_id=uuid4(),
            player_id=PLAYER_ID,
            npc_id=npc_id,
            conversation_id=conversation_id,
            message=message,
        ),
        trace_id=uuid4(),
    )
    if response.status is not DialogueStatus.COMPLETED:
        raise UatError(f"dialogue_status_{response.status.value}_{response.provider}")
    if not response.reply.strip():
        raise UatError("dialogue_reply_blank")
    return response


def _require_name(response: DialogueResponseV1, expected_name: str) -> None:
    if expected_name.casefold() not in response.reply.casefold():
        raise UatError(f"persona_identity_{expected_name.casefold()}_missing")


def _require_topic(response: DialogueResponseV1) -> None:
    if _TOPIC not in response.reply:
        raise UatError("long_term_topic_not_recalled")


def _require_unknown_without_topic(response: DialogueResponseV1) -> None:
    folded = response.reply.casefold()
    if _TOPIC in response.reply or not any(
        marker.casefold() in folded for marker in _UNKNOWN_MARKERS
    ):
        raise UatError("cross_npc_memory_isolation_failed")


def _require_relationship_event(
    service: DialogueService,
    *,
    npc_id: str,
    request_id: UUID,
) -> None:
    relationships = service.relationship_service
    if relationships is None:
        raise UatError("relationship_service_unavailable")
    same_scope = relationships.read(
        player_id=PLAYER_ID,
        npc_id=npc_id,
        request_id=request_id,
    )
    if same_scope.event is None:
        raise UatError("relationship_event_missing")
    other_npc_id = next(candidate for candidate in _NPC_IDS.values() if candidate != npc_id)
    other_scope = relationships.read(
        player_id=PLAYER_ID,
        npc_id=other_npc_id,
        request_id=request_id,
    )
    if other_scope.event is not None:
        raise UatError("relationship_event_cross_npc_leak")


async def run_uat(
    *,
    settings: Settings,
    provider: ProviderProtocol,
    ledger: AcceptanceLedger,
    clock_ns: Callable[[], int] | None = None,
    pace: Callable[[], Awaitable[None]] | None = None,
) -> UatOutcome:
    starting_summary = ledger.summary()
    if starting_summary.total_calls > MAX_CALLS - EXPECTED_CALLS:
        raise UatError("acceptance_retry_budget_unavailable")
    metered = MeteredAcceptanceProvider(
        provider=provider,
        ledger=ledger,
        authorization_id=AUTHORIZATION_ID,
        step=AcceptanceStep.F010_REAL_PROVIDER_UAT,
        reserved_micro_usd=RESERVED_MICRO_USD_PER_CALL,
        usage_cost=lambda usage: calculate_cost_micro_usd(
            policy=DEEPSEEK_FLASH_PEAK_PRICING_POLICY,
            usage=usage,
        ),
    )
    control_scope_key = secrets.token_bytes(32)
    checks = 0
    pace = pace or (lambda: asyncio.sleep(3.1))

    service = _build_service(
        settings=settings,
        provider=metered,
        control_scope_key=control_scope_key,
        clock_ns=clock_ns,
    )
    try:
        nia_conversation = uuid4()
        nia_intro = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=nia_conversation,
            message=(
                "请用一句话介绍你自己和你在小镇的职责；回复中必须原样包含 ASCII 名字 Nia。"  # noqa: RUF001
            ),
        )
        _require_name(nia_intro, "Nia")
        _require_relationship_event(
            service,
            npc_id=_NPC_IDS["Nia"],
            request_id=nia_intro.request_id,
        )
        checks += 2

        await pace()
        nia_followup = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=nia_conversation,
            message="你刚才说自己叫什么名字？只回答名字。",  # noqa: RUF001
        )
        _require_name(nia_followup, "Nia")
        checks += 1

        memory_write = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=nia_conversation,
            message=f"请记住：favorite_cyber_town_topic={_TOPIC}",  # noqa: RUF001
        )
        if memory_write.provider != "local-memory":
            raise UatError("long_term_write_used_provider")
        checks += 1
    finally:
        await service.aclose()

    service = _build_service(
        settings=settings,
        provider=metered,
        control_scope_key=control_scope_key,
        clock_ns=clock_ns,
    )
    try:
        await pace()
        nia_recall = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=uuid4(),
            message="我让你记住的最喜欢的小镇话题是什么？请只回答那个话题。",  # noqa: RUF001
        )
        _require_topic(nia_recall)
        checks += 1

        await pace()
        ivo_conversation = uuid4()
        ivo_intro = await _send(
            service,
            npc_id=_NPC_IDS["Ivo"],
            conversation_id=ivo_conversation,
            message=(
                "请用一句话介绍你自己和你在小镇的职责；回复中必须原样包含 ASCII 名字 Ivo。"  # noqa: RUF001
            ),
        )
        _require_name(ivo_intro, "Ivo")
        checks += 1

        await pace()
        ivo_isolation = await _send(
            service,
            npc_id=_NPC_IDS["Ivo"],
            conversation_id=ivo_conversation,
            message="我之前告诉过你最喜欢的小镇话题是什么？如果没有记录，请明确回答不知道。",  # noqa: RUF001
        )
        _require_unknown_without_topic(ivo_isolation)
        checks += 1

        await pace()
        rhea_conversation = uuid4()
        rhea_intro = await _send(
            service,
            npc_id=_NPC_IDS["Rhea"],
            conversation_id=rhea_conversation,
            message=(
                "请用一句话介绍你自己和你在小镇的职责；回复中必须原样包含 ASCII 名字 Rhea。"  # noqa: RUF001
            ),
        )
        _require_name(rhea_intro, "Rhea")
        checks += 1

        await pace()
        rhea_relationship = await _send(
            service,
            npc_id=_NPC_IDS["Rhea"],
            conversation_id=rhea_conversation,
            message="请简短回应：谢谢你可靠地完成夜间投递，我很信任你。",  # noqa: RUF001
        )
        _require_relationship_event(
            service,
            npc_id=_NPC_IDS["Rhea"],
            request_id=rhea_relationship.request_id,
        )
        checks += 1
    finally:
        await service.aclose()

    summary = ledger.summary()
    if summary.total_calls - starting_summary.total_calls != EXPECTED_CALLS:
        raise UatError("unexpected_real_provider_call_count")
    if summary.pending_calls:
        raise UatError("acceptance_ledger_has_unresolved_call")
    if summary.total_micro_usd > MAX_COST_MICRO_USD:
        raise UatError("acceptance_cost_cap_exceeded")
    return UatOutcome(checks=checks, summary=summary)


async def run_recovery_uat(
    *,
    settings: Settings,
    provider: ProviderProtocol,
    ledger: AcceptanceLedger,
    clock_ns: Callable[[], int] | None = None,
    pace: Callable[[], Awaitable[None]] | None = None,
) -> UatOutcome:
    """Complete all remaining semantics after one failed and one unknown attempt."""

    starting_summary = ledger.summary()
    if (
        starting_summary.total_calls != MAX_CALLS - RECOVERY_CALLS
        or starting_summary.pending_calls
        or starting_summary.total_micro_usd > MAX_COST_MICRO_USD
    ):
        raise UatError("acceptance_recovery_baseline_invalid")
    metered = MeteredAcceptanceProvider(
        provider=provider,
        ledger=ledger,
        authorization_id=AUTHORIZATION_ID,
        step=AcceptanceStep.F010_REAL_PROVIDER_UAT,
        reserved_micro_usd=RESERVED_MICRO_USD_PER_CALL,
        usage_cost=lambda usage: calculate_cost_micro_usd(
            policy=DEEPSEEK_FLASH_PEAK_PRICING_POLICY,
            usage=usage,
        ),
    )
    asserted_provider = _RecoveryScopeAssertionProvider(metered)
    control_scope_key = secrets.token_bytes(32)
    checks = 0
    pace = pace or (lambda: asyncio.sleep(3.1))

    service = _build_service(
        settings=settings,
        provider=asserted_provider,
        control_scope_key=control_scope_key,
        clock_ns=clock_ns,
    )
    try:
        nia_conversation = uuid4()
        nia_intro = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=nia_conversation,
            message=(
                "请用一句话介绍你自己和你在小镇的职责；回复中必须原样包含 ASCII 名字 Nia。"  # noqa: RUF001
            ),
        )
        _require_name(nia_intro, "Nia")
        _require_relationship_event(
            service,
            npc_id=_NPC_IDS["Nia"],
            request_id=nia_intro.request_id,
        )
        checks += 2

        await pace()
        nia_followup = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=nia_conversation,
            message="你刚才说自己叫什么名字？只回答 ASCII 名字 Nia。",  # noqa: RUF001
        )
        _require_name(nia_followup, "Nia")
        checks += 1

        memory_write = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=nia_conversation,
            message=f"请记住：favorite_cyber_town_topic={_TOPIC}",  # noqa: RUF001
        )
        if memory_write.provider != "local-memory":
            raise UatError("long_term_write_used_provider")
        checks += 1
    finally:
        await service.aclose()

    service = _build_service(
        settings=settings,
        provider=asserted_provider,
        control_scope_key=control_scope_key,
        clock_ns=clock_ns,
    )
    try:
        await pace()
        nia_recall = await _send(
            service,
            npc_id=_NPC_IDS["Nia"],
            conversation_id=uuid4(),
            message="我让你记住的最喜欢的小镇话题是什么？请只回答那个话题。",  # noqa: RUF001
        )
        _require_topic(nia_recall)
        checks += 1

        await pace()
        ivo_combined = await _send(
            service,
            npc_id=_NPC_IDS["Ivo"],
            conversation_id=uuid4(),
            message=(
                "请原样写出 ASCII 名字 Ivo 并简述你的职责。"
                "随后明确写出不知道，不要补充任何用户偏好。"  # noqa: RUF001
            ),
        )
        _require_name(ivo_combined, "Ivo")
        _require_unknown_without_topic(ivo_combined)
        checks += 2

        await pace()
        rhea_conversation = uuid4()
        rhea_intro = await _send(
            service,
            npc_id=_NPC_IDS["Rhea"],
            conversation_id=rhea_conversation,
            message=(
                "请用一句话介绍你自己和你在小镇的职责；回复中必须原样包含 ASCII 名字 Rhea。"  # noqa: RUF001
            ),
        )
        _require_name(rhea_intro, "Rhea")
        checks += 1

        await pace()
        rhea_relationship = await _send(
            service,
            npc_id=_NPC_IDS["Rhea"],
            conversation_id=rhea_conversation,
            message="请简短回应：谢谢你可靠地完成夜间投递，我很信任你。",  # noqa: RUF001
        )
        _require_relationship_event(
            service,
            npc_id=_NPC_IDS["Rhea"],
            request_id=rhea_relationship.request_id,
        )
        checks += 1
    finally:
        await service.aclose()

    summary = ledger.summary()
    if summary.total_calls - starting_summary.total_calls != RECOVERY_CALLS:
        raise UatError("unexpected_recovery_provider_call_count")
    if asserted_provider.call_count != RECOVERY_CALLS:
        raise UatError("unexpected_recovery_scope_assertion_count")
    if summary.total_calls != MAX_CALLS or summary.pending_calls:
        raise UatError("acceptance_recovery_ledger_invalid")
    if summary.total_micro_usd > MAX_COST_MICRO_USD:
        raise UatError("acceptance_cost_cap_exceeded")
    return UatOutcome(checks=checks, summary=summary)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--resolve-unknown", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--authorization-id", default="")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    if sum((arguments.preflight, arguments.run, arguments.resolve_unknown, arguments.resume)) != 1:
        print("F010_REAL_UAT=FAIL reason=choose_exactly_one_mode")
        return 2
    if arguments.authorization_id != AUTHORIZATION_ID:
        print("F010_REAL_UAT=FAIL reason=authorization_id_mismatch")
        return 2
    try:
        _validate_resource_boundaries(create=False)
        if arguments.preflight:
            settings = _settings_from_authorized_dotenv()
            print(
                "F010_REAL_UAT_PREFLIGHT=PASS "
                f"model={settings.llm_model} planned_calls={EXPECTED_CALLS} "
                f"hard_call_cap={MAX_CALLS} hard_cost_micro_usd={MAX_COST_MICRO_USD}"
            )
            return 0

        if arguments.resolve_unknown:
            ledger = _ledger(allow_unresolved=True)
            ledger.resolve_single_unknown_as_charged(
                authorization_id=AUTHORIZATION_ID,
                step=AcceptanceStep.F010_REAL_PROVIDER_UAT,
                reason_code="provider_outcome_unresolved",
            )
            summary = ledger.summary()
            if summary.pending_calls or summary.total_calls != MAX_CALLS - RECOVERY_CALLS:
                raise UatError("acceptance_unknown_resolution_invalid")
            print(
                "F010_REAL_UAT_RESOLUTION=PASS "
                f"calls={summary.total_calls} pending=0 "
                f"conservative_cost_micro_usd={summary.total_micro_usd}"
            )
            return 0

        _validate_resource_boundaries(create=True)
        ledger = _ledger()
        settings = _settings_from_authorized_dotenv()
        provider = DeepSeekProvider(
            credential=settings.llm_api_key or SecretStr(""),
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        if arguments.resume:
            outcome = asyncio.run(
                run_recovery_uat(settings=settings, provider=provider, ledger=ledger)
            )
        else:
            outcome = asyncio.run(run_uat(settings=settings, provider=provider, ledger=ledger))
    except BaseException as error:
        reason = (
            error.args[0] if isinstance(error, UatError) and error.args else type(error).__name__
        )
        print(f"F010_REAL_UAT=FAIL reason={reason}")
        return 1

    print(
        "F010_REAL_UAT=PASS "
        f"calls={outcome.summary.total_calls} checks={outcome.checks} "
        f"prompt_tokens={outcome.summary.total_prompt_tokens} "
        f"completion_tokens={outcome.summary.total_completion_tokens} "
        f"cost_micro_usd={outcome.summary.total_micro_usd} pending=0"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
