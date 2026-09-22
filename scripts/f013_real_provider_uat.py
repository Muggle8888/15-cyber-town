"""Bounded, content-redacted F-013 real-provider acceptance runner."""

from __future__ import annotations

import argparse
import asyncio
import secrets
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final, Literal
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

AUTHORIZATION_ID: Final = "f013-real-provider-uat-20260922"
PLAYER_ID: Final = "f013_uat_player"
UAT_ROOT: Final = PROJECT_ROOT / "data" / "uat" / "f-013"
BUSINESS_DATABASE: Final = UAT_ROOT / "cyber-town.sqlite3"
CONTROL_DATABASE: Final = UAT_ROOT / "cyber-town-control.sqlite3"
LEDGER_ROOT: Final = PROJECT_ROOT / "data" / "acceptance-ledgers"
LEDGER_DATABASE: Final = LEDGER_ROOT / "f-013.sqlite3"
EXPECTED_CHECKS: Final = 6
PLANNED_CALLS: Final = 6
MAX_RETRIES: Final = 2
MAX_CALLS: Final = 8
MAX_COST_MICRO_USD: Final = 50_000
RESERVED_MICRO_USD_PER_CALL: Final = 10_138
ABSOLUTE_MAX_COST_MICRO_USD: Final = MAX_CALLS * RESERVED_MICRO_USD_PER_CALL


class UatError(RuntimeError):
    """A content-redacted acceptance failure with one stable reason code."""


class SemanticUatError(UatError):
    """A settled reply failed one content-redacted semantic assertion."""


@dataclass(frozen=True, slots=True)
class NpcUatCase:
    """One low-sensitivity visible F-013 dialogue contract."""

    key: str
    name: str
    npc_id: str
    message: str
    markers: tuple[str, ...]
    stage: RelationshipStage
    check_kind: Literal["event", "persona"]


@dataclass(slots=True)
class RetryBudget:
    """Shared semantic retry counter bounded across the whole run."""

    used: int = 0


@dataclass(frozen=True, slots=True)
class UatOutcome:
    """Metadata-only result suitable for console and project evidence."""

    checks: int
    retries: int
    summary: AcceptanceSummary


CASES: Final = (
    NpcUatCase(
        key="nia_intro",
        name="Nia",
        npc_id="neon_guide",
        message="今晚的夜市灯带似乎少了一段光，你注意到了吗？",  # noqa: RUF001
        markers=("灯", "夜市", "异常", "光"),
        stage=RelationshipStage.ACQUAINTANCE,
        check_kind="event",
    ),
    NpcUatCase(
        key="ivo_analysis",
        name="Ivo",
        npc_id="signal_archivist",
        message="我在暮光导览牌发现一段异常灯带标记，它和旧广播编号有关吗？",  # noqa: RUF001
        markers=("广播", "编号", "信号", "档案"),
        stage=RelationshipStage.FRIEND,
        check_kind="event",
    ),
    NpcUatCase(
        key="rhea_route",
        name="Rhea",
        npc_id="night_courier",
        message="Ivo 发现旧广播编号可能对应雨夜路线，这条路线现在如何核对？",  # noqa: RUF001
        markers=("雨夜", "路线", "投递", "广播"),
        stage=RelationshipStage.TRUSTED_ALLY,
        check_kind="event",
    ),
    NpcUatCase(
        key="nia_conclusion",
        name="Nia",
        npc_id="neon_guide",
        message="我们核对了旧广播编号和雨夜路线，这段暮光信号应该怎样记录？",  # noqa: RUF001
        markers=("记录", "归档", "信号", "路线", "广播"),
        stage=RelationshipStage.ACQUAINTANCE,
        check_kind="event",
    ),
    NpcUatCase(
        key="nia_relationship",
        name="Nia",
        npc_id="neon_guide",
        message=(
            "请原样包含 ASCII 名字 Nia, 并以符合我们当前关系距离的方式,"
            "用一至三段介绍你的导览职责和此刻愿意提供的帮助。"
            "不要说明内部阶段、规则、工具或权限。"
        ),
        markers=("导览", "街区", "夜市", "路线"),
        stage=RelationshipStage.ACQUAINTANCE,
        check_kind="persona",
    ),
    NpcUatCase(
        key="rhea_relationship",
        name="Rhea",
        npc_id="night_courier",
        message=(
            "请原样包含 ASCII 名字 Rhea, 并以符合我们当前关系距离的方式,"
            "用一至三段介绍你的投递职责和此刻愿意提供的帮助。"
            "不要说明内部阶段、规则、工具或权限。"
        ),
        markers=("投递", "路线", "雨夜", "送达"),
        stage=RelationshipStage.TRUSTED_ALLY,
        check_kind="persona",
    ),
)


class _BoundaryAssertionProvider:
    """Verify visible-text, NPC and state boundaries before paid dispatch."""

    def __init__(self, provider: ProviderProtocol) -> None:
        self._provider = provider
        self.call_count = 0

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        matching = tuple(case for case in CASES if request.user_message == case.message)
        if len(matching) != 1:
            raise UatError("unexpected_provider_message")
        case = matching[0]
        if request.long_term_facts:
            raise UatError(f"{case.name.casefold()}_unexpected_long_term_context")
        if request.history_messages:
            raise UatError(f"{case.name.casefold()}_unexpected_hidden_history")
        if request.reply_style is not None:
            raise UatError(f"{case.name.casefold()}_unexpected_reply_style")
        if (
            request.relationship_stage is None
            or request.relationship_stage.value != case.stage.value
        ):
            raise UatError(f"{case.name.casefold()}_relationship_stage_mismatch")
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
    message: str,
) -> DialogueResponseV1:
    response = await service.execute(
        DialogueRequestV1(
            request_id=uuid4(),
            player_id=PLAYER_ID,
            npc_id=npc_id,
            conversation_id=uuid4(),
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
    event_number = 30_000
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    target_scores = {
        RelationshipStage.ACQUAINTANCE: 30,
        RelationshipStage.FRIEND: 60,
        RelationshipStage.TRUSTED_ALLY: 90,
    }
    npc_stages = {case.npc_id: case.stage for case in CASES}
    if any(case.stage is not npc_stages[case.npc_id] for case in CASES):
        raise UatError("relationship_stage_plan_conflict")
    for npc_id, stage in npc_stages.items():
        target_score = target_scores[stage]
        effective_events = (target_score - 20) // 2
        for offset in range(effective_events):
            event_number += 1
            repository.apply_interaction(
                scope=RelationshipScope(PLAYER_ID, npc_id),
                request_id=UUID(int=event_number),
                request_fingerprint=f"{event_number:064x}",
                trace_id=UUID(int=event_number + 10_000),
                conversation_id=UUID(int=event_number + 20_000),
                raw_suggestion={"category": "supportive", "confidence": 100},
                occurred_at=started_at + timedelta(days=offset),
            )
        state = repository.get_state(RelationshipScope(PLAYER_ID, npc_id))
        if state.stage is not stage or state.score != target_score:
            raise UatError(f"{npc_id}_relationship_seed_failed")


def _require_event_context(response: DialogueResponseV1, case: NpcUatCase) -> None:
    if not any(marker in response.reply for marker in case.markers):
        raise SemanticUatError(f"{case.key}_context_not_understood")


def _require_persona_and_relationship(response: DialogueResponseV1, case: NpcUatCase) -> None:
    reply = response.reply.strip()
    if case.name.casefold() not in reply.casefold():
        raise SemanticUatError(f"{case.name.casefold()}_persona_identity_missing")
    if not any(marker in reply for marker in case.markers):
        raise SemanticUatError(f"{case.key}_persona_role_missing")
    paragraphs = tuple(part for part in reply.split("\n") if part.strip())
    if len(reply) > 1_000 or not 1 <= len(paragraphs) <= 3:
        raise SemanticUatError(f"{case.name.casefold()}_persona_length_failed")
    forbidden_internal = (
        "RELATIONSHIP_STAGE",
        "CONTROLLED_CONTEXT_VERSION",
        "f-011-relationship-style-v1",
        "关系阶段枚举",
    )
    if any(marker in reply for marker in forbidden_internal):
        raise SemanticUatError(f"{case.name.casefold()}_internal_context_disclosed")
    if case.stage is RelationshipStage.TRUSTED_ALLY:
        forbidden_overclaim = ("后台权限", "已经调用工具", "已经修改游戏", "访问了你的文件")
        if any(marker in reply for marker in forbidden_overclaim):
            raise SemanticUatError("rhea_relationship_overclaim")


async def _run_semantic_check(
    *,
    service: DialogueService,
    case: NpcUatCase,
    message: str,
    validator: Callable[[DialogueResponseV1, NpcUatCase], None],
    retry_budget: RetryBudget,
    pace: Callable[[], Awaitable[None]],
) -> None:
    while True:
        response = await _send(service, npc_id=case.npc_id, message=message)
        try:
            validator(response, case)
        except SemanticUatError:
            if retry_budget.used >= MAX_RETRIES:
                raise
            retry_budget.used += 1
            await pace()
            continue
        return


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
        step=AcceptanceStep.F013_REAL_PROVIDER_UAT,
        reserved_micro_usd=RESERVED_MICRO_USD_PER_CALL,
        usage_cost=lambda usage: calculate_cost_micro_usd(
            policy=DEEPSEEK_FLASH_PEAK_PRICING_POLICY,
            usage=usage,
        ),
    )
    asserted_provider = _BoundaryAssertionProvider(metered)
    pace = pace or (lambda: asyncio.sleep(3.1))
    _seed_relationships()
    service = _build_service(
        settings=settings,
        provider=asserted_provider,
        control_scope_key=secrets.token_bytes(32),
        clock_ns=clock_ns,
    )
    retry_budget = RetryBudget()
    checks = 0
    try:
        for index, case in enumerate(CASES):
            await _run_semantic_check(
                service=service,
                case=case,
                message=case.message,
                validator=(
                    _require_event_context
                    if case.check_kind == "event"
                    else _require_persona_and_relationship
                ),
                retry_budget=retry_budget,
                pace=pace,
            )
            checks += 1
            if index != len(CASES) - 1:
                await pace()
    finally:
        await service.aclose()

    summary = ledger.summary()
    expected_calls = PLANNED_CALLS + retry_budget.used
    if asserted_provider.call_count != expected_calls:
        raise UatError("unexpected_boundary_assertion_count")
    if summary.total_calls != expected_calls or summary.pending_calls:
        raise UatError("unexpected_real_provider_call_count")
    if summary.total_calls > MAX_CALLS:
        raise UatError("acceptance_call_cap_exceeded")
    if summary.total_micro_usd > MAX_COST_MICRO_USD:
        raise UatError("acceptance_cost_cap_exceeded")
    return UatOutcome(checks=checks, retries=retry_budget.used, summary=summary)


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
        print("F013_REAL_UAT=FAIL reason=choose_exactly_one_mode")
        return 2
    if arguments.authorization_id != AUTHORIZATION_ID:
        print("F013_REAL_UAT=FAIL reason=authorization_id_mismatch")
        return 2
    try:
        _validate_resource_boundaries(create=False)
        if arguments.offline_preflight:
            print(
                "F013_REAL_UAT_OFFLINE_PREFLIGHT=PASS "
                f"model={DEEPSEEK_MODEL} planned_calls={PLANNED_CALLS} "
                f"max_retries={MAX_RETRIES} hard_call_cap={MAX_CALLS} "
                f"hard_cost_micro_usd={MAX_COST_MICRO_USD} "
                f"absolute_max_cost_micro_usd={ABSOLUTE_MAX_COST_MICRO_USD} "
                "cost_first_stop=true"
            )
            return 0
        settings = _settings_from_authorized_dotenv()
        if arguments.credential_preflight:
            print(
                "F013_REAL_UAT_CREDENTIAL_PREFLIGHT=PASS "
                f"model={settings.llm_model} planned_calls={PLANNED_CALLS} "
                f"max_retries={MAX_RETRIES} hard_call_cap={MAX_CALLS} "
                f"hard_cost_micro_usd={MAX_COST_MICRO_USD}"
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
        print(f"F013_REAL_UAT=FAIL reason={reason}")
        return 1

    print(
        "F013_REAL_UAT=PASS "
        f"calls={outcome.summary.total_calls} checks={outcome.checks} retries={outcome.retries} "
        f"prompt_tokens={outcome.summary.total_prompt_tokens} "
        f"completion_tokens={outcome.summary.total_completion_tokens} "
        f"cost_micro_usd={outcome.summary.total_micro_usd} pending=0"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
