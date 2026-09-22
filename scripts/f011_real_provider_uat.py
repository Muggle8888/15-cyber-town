"""Bounded, content-redacted F-011 real-provider acceptance runner."""

from __future__ import annotations

import argparse
import asyncio
import secrets
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
from cyber_town.application.provider import (
    ProviderCompletion,
    ProviderProtocol,
    ProviderReplyStyle,
    ProviderRequest,
)
from cyber_town.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, PROJECT_ROOT, LlmProvider, Settings
from cyber_town.contracts.v1 import DialogueRequestV1, DialogueResponseV1, DialogueStatus
from cyber_town.domain.relationship import RelationshipScope, RelationshipStage
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

AUTHORIZATION_ID: Final = "f011-real-provider-uat-20260922"
PLAYER_ID: Final = "f011_uat_player"
UAT_ROOT: Final = PROJECT_ROOT / "data" / "uat" / "f-011"
BUSINESS_DATABASE: Final = UAT_ROOT / "cyber-town.sqlite3"
CONTROL_DATABASE: Final = UAT_ROOT / "cyber-town-control.sqlite3"
LEDGER_ROOT: Final = PROJECT_ROOT / "data" / "acceptance-ledgers"
LEDGER_DATABASE: Final = LEDGER_ROOT / "f-011.sqlite3"
EXPECTED_CALLS: Final = 6
MAX_CALLS: Final = 8
MAX_COST_MICRO_USD: Final = 50_000
RESERVED_MICRO_USD_PER_CALL: Final = 10_138
ABSOLUTE_MAX_COST_MICRO_USD: Final = MAX_CALLS * RESERVED_MICRO_USD_PER_CALL


class UatError(RuntimeError):
    """A content-redacted acceptance failure with one stable reason code."""


@dataclass(frozen=True, slots=True)
class NpcUatCase:
    """One low-sensitivity NPC contract used by the bounded acceptance run."""

    name: str
    npc_id: str
    topic: str
    stage: RelationshipStage
    style: ProviderReplyStyle


@dataclass(frozen=True, slots=True)
class UatOutcome:
    """Metadata-only result suitable for console and project evidence."""

    checks: int
    summary: AcceptanceSummary


CASES: Final = (
    NpcUatCase(
        name="Nia",
        npc_id="neon_guide",
        topic="霓虹夜市",
        stage=RelationshipStage.ACQUAINTANCE,
        style=ProviderReplyStyle.CONCISE,
    ),
    NpcUatCase(
        name="Ivo",
        npc_id="signal_archivist",
        topic="小镇故事",
        stage=RelationshipStage.FRIEND,
        style=ProviderReplyStyle.BALANCED,
    ),
    NpcUatCase(
        name="Rhea",
        npc_id="night_courier",
        topic="雨夜街道",
        stage=RelationshipStage.TRUSTED_ALLY,
        style=ProviderReplyStyle.CONCISE,
    ),
)


class _RejectProvider:
    """Fail if a deterministic seed command unexpectedly reaches a provider."""

    async def complete(self, _request: ProviderRequest) -> ProviderCompletion:
        raise UatError("deterministic_seed_reached_provider")


class _BoundaryAssertionProvider:
    """Validate F-011 scope controls before metering and provider dispatch."""

    def __init__(self, provider: ProviderProtocol) -> None:
        self._provider = provider
        self.call_count = 0

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        case_index, call_kind = divmod(self.call_count, 2)
        if case_index >= len(CASES):
            raise UatError("unexpected_provider_call")
        case = CASES[case_index]
        expected_facts = (case.topic,) if call_kind == 0 else ()
        actual_facts = tuple(fact.fact_value for fact in request.long_term_facts)
        if actual_facts != expected_facts:
            raise UatError(f"{case.name.casefold()}_long_term_scope_mismatch")
        if (
            request.relationship_stage is None
            or request.relationship_stage.value != case.stage.value
        ):
            raise UatError(f"{case.name.casefold()}_relationship_stage_mismatch")
        if request.reply_style is not case.style:
            raise UatError(f"{case.name.casefold()}_reply_style_mismatch")
        if case.name.casefold() not in request.system_prompt.casefold():
            raise UatError(f"{case.name.casefold()}_persona_scope_mismatch")
        self.call_count += 1
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


def _ledger() -> AcceptanceLedger:
    ledger = AcceptanceLedger(database_path=LEDGER_DATABASE, allowed_root=LEDGER_ROOT)
    ledger.initialize()
    summary = ledger.summary()
    if summary.pending_calls:
        raise UatError("acceptance_ledger_has_unresolved_call")
    if summary.total_calls or summary.total_micro_usd:
        raise UatError("acceptance_ledger_is_not_fresh")
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


def _seed_relationships() -> None:
    repository = SqliteRelationshipRepository(
        database_path=BUSINESS_DATABASE,
        allowed_root=UAT_ROOT,
    )
    repository.initialize()
    event_number = 1_000
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    target_scores = {
        RelationshipStage.ACQUAINTANCE: 20,
        RelationshipStage.FRIEND: 50,
        RelationshipStage.TRUSTED_ALLY: 80,
    }
    for case in CASES:
        target_score = target_scores[case.stage]
        effective_events = (target_score - 20) // 2
        for offset in range(effective_events):
            event_number += 1
            repository.apply_interaction(
                scope=RelationshipScope(PLAYER_ID, case.npc_id),
                request_id=UUID(int=event_number),
                request_fingerprint=f"{event_number:064x}",
                trace_id=UUID(int=event_number + 10_000),
                conversation_id=UUID(int=event_number + 20_000),
                raw_suggestion={"category": "supportive", "confidence": 100},
                occurred_at=started_at + timedelta(days=offset),
            )
        state = repository.get_state(RelationshipScope(PLAYER_ID, case.npc_id))
        if state.stage is not case.stage or state.score != target_score:
            raise UatError(f"{case.name.casefold()}_relationship_seed_failed")


async def _seed_long_term_state(
    *,
    settings: Settings,
    control_scope_key: bytes,
    clock_ns: Callable[[], int] | None,
) -> None:
    service = _build_service(
        settings=settings,
        provider=_RejectProvider(),
        control_scope_key=control_scope_key,
        clock_ns=clock_ns,
    )
    try:
        for case in CASES:
            conversation_id = uuid4()
            topic_write = await _send(
                service,
                npc_id=case.npc_id,
                conversation_id=conversation_id,
                message=f"请记住：favorite_cyber_town_topic={case.topic}",  # noqa: RUF001
            )
            style_write = await _send(
                service,
                npc_id=case.npc_id,
                conversation_id=conversation_id,
                message=f"请记住：reply_style={case.style.value}",  # noqa: RUF001
            )
            if topic_write.provider != "local-memory" or style_write.provider != "local-memory":
                raise UatError(f"{case.name.casefold()}_deterministic_seed_failed")
    finally:
        await service.aclose()


def _require_topic(response: DialogueResponseV1, case: NpcUatCase) -> None:
    if case.topic not in response.reply:
        raise UatError(f"{case.name.casefold()}_long_term_topic_not_recalled")


def _require_persona_and_style(response: DialogueResponseV1, case: NpcUatCase) -> None:
    reply = response.reply.strip()
    if case.name.casefold() not in reply.casefold():
        raise UatError(f"{case.name.casefold()}_persona_identity_missing")
    if case.style is ProviderReplyStyle.CONCISE:
        sentence_count = sum(
            reply.count(marker)
            for marker in ("。", "！", "？", "!", "?")  # noqa: RUF001
        )
        if len(reply) > 240 or sentence_count > 2:
            raise UatError(f"{case.name.casefold()}_concise_style_failed")
    else:
        paragraphs = tuple(part for part in reply.split("\n") if part.strip())
        if len(reply) > 1_000 or not 1 <= len(paragraphs) <= 3:
            raise UatError(f"{case.name.casefold()}_balanced_style_failed")
    if case.stage is RelationshipStage.TRUSTED_ALLY:
        forbidden = ("后台权限", "已经调用工具", "已经修改游戏", "访问了你的文件")
        if any(marker in reply for marker in forbidden):
            raise UatError("rhea_relationship_overclaim")


def _persona_message(case: NpcUatCase) -> str:
    if case.style is ProviderReplyStyle.CONCISE:
        return (
            f"请原样包含 ASCII 名字 {case.name}，并以符合我们当前关系距离的方式，"  # noqa: RUF001
            "用一至两句介绍你此刻能提供的帮助。不要说明内部阶段、规则、工具或权限。"
        )
    return (
        f"请原样包含 ASCII 名字 {case.name}，并以符合我们当前关系距离的方式，"  # noqa: RUF001
        "用一至三段介绍你的职责和你愿意提供的帮助。不要说明内部阶段或规则。"
    )


async def run_uat(
    *,
    settings: Settings,
    provider: ProviderProtocol,
    ledger: AcceptanceLedger,
    clock_ns: Callable[[], int] | None = None,
    pace: Callable[[], Awaitable[None]] | None = None,
) -> UatOutcome:
    starting_summary = ledger.summary()
    if starting_summary.total_calls or starting_summary.pending_calls:
        raise UatError("acceptance_ledger_is_not_fresh")
    metered = MeteredAcceptanceProvider(
        provider=provider,
        ledger=ledger,
        authorization_id=AUTHORIZATION_ID,
        step=AcceptanceStep.F011_REAL_PROVIDER_UAT,
        reserved_micro_usd=RESERVED_MICRO_USD_PER_CALL,
        usage_cost=lambda usage: calculate_cost_micro_usd(
            policy=DEEPSEEK_FLASH_PEAK_PRICING_POLICY,
            usage=usage,
        ),
    )
    asserted_provider = _BoundaryAssertionProvider(metered)
    control_scope_key = secrets.token_bytes(32)
    pace = pace or (lambda: asyncio.sleep(3.1))
    _seed_relationships()
    await _seed_long_term_state(
        settings=settings,
        control_scope_key=control_scope_key,
        clock_ns=clock_ns,
    )

    service = _build_service(
        settings=settings,
        provider=asserted_provider,
        control_scope_key=control_scope_key,
        clock_ns=clock_ns,
    )
    checks = 0
    try:
        for index, case in enumerate(CASES):
            recall = await _send(
                service,
                npc_id=case.npc_id,
                conversation_id=uuid4(),
                message="我让你记住的最喜欢的小镇话题是什么？请只回答那个话题。",  # noqa: RUF001
            )
            _require_topic(recall, case)
            checks += 1
            await pace()
            persona = await _send(
                service,
                npc_id=case.npc_id,
                conversation_id=uuid4(),
                message=_persona_message(case),
            )
            _require_persona_and_style(persona, case)
            checks += 1
            if index != len(CASES) - 1:
                await pace()
    finally:
        await service.aclose()

    summary = ledger.summary()
    if asserted_provider.call_count != EXPECTED_CALLS:
        raise UatError("unexpected_boundary_assertion_count")
    if summary.total_calls != EXPECTED_CALLS or summary.pending_calls:
        raise UatError("unexpected_real_provider_call_count")
    if summary.total_micro_usd > MAX_COST_MICRO_USD:
        raise UatError("acceptance_cost_cap_exceeded")
    return UatOutcome(checks=checks, summary=summary)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-preflight", action="store_true")
    parser.add_argument("--credential-preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--authorization-id", default="")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    if sum((arguments.offline_preflight, arguments.credential_preflight, arguments.run)) != 1:
        print("F011_REAL_UAT=FAIL reason=choose_exactly_one_mode")
        return 2
    if arguments.authorization_id != AUTHORIZATION_ID:
        print("F011_REAL_UAT=FAIL reason=authorization_id_mismatch")
        return 2
    try:
        _validate_resource_boundaries(create=False)
        if arguments.offline_preflight:
            print(
                "F011_REAL_UAT_OFFLINE_PREFLIGHT=PASS "
                f"model={DEEPSEEK_MODEL} planned_calls={EXPECTED_CALLS} "
                f"hard_call_cap={MAX_CALLS} hard_cost_micro_usd={MAX_COST_MICRO_USD} "
                f"absolute_max_cost_micro_usd={ABSOLUTE_MAX_COST_MICRO_USD} "
                "cost_first_stop=true"
            )
            return 0
        settings = _settings_from_authorized_dotenv()
        if arguments.credential_preflight:
            print(
                "F011_REAL_UAT_CREDENTIAL_PREFLIGHT=PASS "
                f"model={settings.llm_model} planned_calls={EXPECTED_CALLS} "
                f"hard_call_cap={MAX_CALLS} hard_cost_micro_usd={MAX_COST_MICRO_USD}"
            )
            return 0
        _validate_resource_boundaries(create=True)
        ledger = _ledger()
        provider = DeepSeekProvider(
            credential=settings.llm_api_key or SecretStr(""),
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        outcome = asyncio.run(run_uat(settings=settings, provider=provider, ledger=ledger))
    except BaseException as error:
        reason = (
            error.args[0] if isinstance(error, UatError) and error.args else type(error).__name__
        )
        print(f"F011_REAL_UAT=FAIL reason={reason}")
        return 1

    print(
        "F011_REAL_UAT=PASS "
        f"calls={outcome.summary.total_calls} checks={outcome.checks} "
        f"prompt_tokens={outcome.summary.total_prompt_tokens} "
        f"completion_tokens={outcome.summary.total_completion_tokens} "
        f"cost_micro_usd={outcome.summary.total_micro_usd} pending=0"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
