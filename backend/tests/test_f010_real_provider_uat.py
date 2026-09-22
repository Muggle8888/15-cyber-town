from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import pytest
from pydantic import SecretStr
from scripts import f010_real_provider_uat as uat

from cyber_town.application.provider import ProviderCompletion, ProviderUsage
from cyber_town.config import LlmProvider, Settings
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.persistence.acceptance_ledger import AcceptanceLedger, AcceptanceStep


class _FakeClock:
    def __init__(self) -> None:
        self.now_ns = time.time_ns()

    def __call__(self) -> int:
        return self.now_ns

    async def pace(self) -> None:
        self.now_ns += 4_000_000_000
        await asyncio.sleep(0)


def _completion(reply: str) -> ProviderCompletion:
    return ProviderCompletion(
        content=reply,
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="fake",
        model="deepseek-flash",
        usage=ProviderUsage(prompt_tokens=24, completion_tokens=12),
        relationship_suggestion={"category": "friendly", "confidence": 95},
    )


def test_f010_uat_fake_readiness_preserves_call_budget_memory_and_scope_isolation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uat_root = tmp_path / "uat"
    ledger_root = tmp_path / "ledger"
    uat_root.mkdir()
    ledger_root.mkdir()
    monkeypatch.setattr(uat, "UAT_ROOT", uat_root)
    monkeypatch.setattr(uat, "BUSINESS_DATABASE", uat_root / "cyber-town.sqlite3")
    monkeypatch.setattr(uat, "CONTROL_DATABASE", uat_root / "cyber-town-control.sqlite3")

    ledger = AcceptanceLedger(
        database_path=ledger_root / "f-010.sqlite3",
        allowed_root=ledger_root,
    )
    ledger.initialize()
    provider = FakeProvider(
        [
            _completion("我是 Nia，负责夜间导览。"),  # noqa: RUF001
            _completion("Nia"),
            _completion("霓虹夜市"),
            _completion("我是 Ivo，负责信号档案。"),  # noqa: RUF001
            _completion("不知道。"),
            _completion("我是 Rhea，负责夜间投递。"),  # noqa: RUF001
            _completion("收到，谢谢你的信任。"),  # noqa: RUF001
        ]
    )
    settings = Settings.model_validate(
        {
            "llm_provider": LlmProvider.DEEPSEEK,
            "llm_model": "deepseek-flash",
            "llm_api_key": SecretStr("synthetic-provider-value"),
        }
    )

    clock = _FakeClock()
    outcome = asyncio.run(
        uat.run_uat(
            settings=settings,
            provider=provider,
            ledger=ledger,
            clock_ns=clock,
            pace=clock.pace,
        )
    )

    assert provider.call_count == 7
    assert outcome.summary.total_calls == 7
    assert outcome.summary.pending_calls == 0
    assert outcome.summary.total_prompt_tokens == 168
    assert outcome.summary.total_completion_tokens == 84
    assert outcome.summary.total_micro_usd == 154
    assert tuple(fact.fact_value for fact in provider.requests[2].long_term_facts) == ("霓虹夜市",)
    assert provider.requests[3].long_term_facts == ()
    assert provider.requests[4].long_term_facts == ()


def test_f010_uat_allows_one_previously_settled_failed_semantic_call(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uat_root = tmp_path / "uat"
    ledger_root = tmp_path / "ledger"
    uat_root.mkdir()
    ledger_root.mkdir()
    monkeypatch.setattr(uat, "UAT_ROOT", uat_root)
    monkeypatch.setattr(uat, "BUSINESS_DATABASE", uat_root / "cyber-town.sqlite3")
    monkeypatch.setattr(uat, "CONTROL_DATABASE", uat_root / "cyber-town-control.sqlite3")

    ledger = AcceptanceLedger(
        database_path=ledger_root / "f-010.sqlite3",
        allowed_root=ledger_root,
    )
    ledger.initialize()
    previous = ledger.reserve(
        authorization_id=uat.AUTHORIZATION_ID,
        step=AcceptanceStep.F010_REAL_PROVIDER_UAT,
        model="deepseek-flash",
        reserved_micro_usd=uat.RESERVED_MICRO_USD_PER_CALL,
    )
    ledger.record_usage(
        previous,
        prompt_tokens=10,
        completion_tokens=10,
        actual_micro_usd=15,
    )
    provider = FakeProvider(
        [
            _completion("Nia"),
            _completion("Nia"),
            _completion("霓虹夜市"),
            _completion("Ivo"),
            _completion("不知道。"),
            _completion("Rhea"),
            _completion("收到。"),
        ]
    )
    settings = Settings.model_validate(
        {
            "llm_provider": LlmProvider.DEEPSEEK,
            "llm_model": "deepseek-flash",
            "llm_api_key": SecretStr("synthetic-provider-value"),
        }
    )
    clock = _FakeClock()

    outcome = asyncio.run(
        uat.run_uat(
            settings=settings,
            provider=provider,
            ledger=ledger,
            clock_ns=clock,
            pace=clock.pace,
        )
    )

    assert provider.call_count == 7
    assert outcome.summary.total_calls == 8
    assert outcome.summary.pending_calls == 0


def test_f010_recovery_conservatively_carries_unknown_and_finishes_at_hard_cap(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uat_root = tmp_path / "uat"
    ledger_root = tmp_path / "ledger"
    uat_root.mkdir()
    ledger_root.mkdir()
    monkeypatch.setattr(uat, "UAT_ROOT", uat_root)
    monkeypatch.setattr(uat, "BUSINESS_DATABASE", uat_root / "cyber-town.sqlite3")
    monkeypatch.setattr(uat, "CONTROL_DATABASE", uat_root / "cyber-town-control.sqlite3")
    ledger = AcceptanceLedger(
        database_path=ledger_root / "f-010.sqlite3",
        allowed_root=ledger_root,
    )
    ledger.initialize()
    for _ in range(2):
        completed = ledger.reserve(
            authorization_id=uat.AUTHORIZATION_ID,
            step=AcceptanceStep.F010_REAL_PROVIDER_UAT,
            model="deepseek-flash",
            reserved_micro_usd=uat.RESERVED_MICRO_USD_PER_CALL,
        )
        ledger.record_usage(
            completed,
            prompt_tokens=10,
            completion_tokens=10,
            actual_micro_usd=15,
        )
    unknown = ledger.reserve(
        authorization_id=uat.AUTHORIZATION_ID,
        step=AcceptanceStep.F010_REAL_PROVIDER_UAT,
        model="deepseek-flash",
        reserved_micro_usd=uat.RESERVED_MICRO_USD_PER_CALL,
    )
    ledger.mark_unknown(unknown)
    ledger.resolve_single_unknown_as_charged(
        authorization_id=uat.AUTHORIZATION_ID,
        step=AcceptanceStep.F010_REAL_PROVIDER_UAT,
        reason_code="provider_outcome_unresolved",
    )
    provider = FakeProvider(
        [
            _completion("Nia"),
            _completion("Nia"),
            _completion("霓虹夜市"),
            _completion("Ivo 不知道。"),
            _completion("Rhea"),
            _completion("收到。"),
        ]
    )
    settings = Settings.model_validate(
        {
            "llm_provider": LlmProvider.DEEPSEEK,
            "llm_model": "deepseek-flash",
            "llm_api_key": SecretStr("synthetic-provider-value"),
        }
    )
    clock = _FakeClock()

    outcome = asyncio.run(
        uat.run_recovery_uat(
            settings=settings,
            provider=provider,
            ledger=ledger,
            clock_ns=clock,
            pace=clock.pace,
        )
    )

    assert provider.call_count == 6
    assert outcome.summary.total_calls == 9
    assert outcome.summary.pending_calls == 0
    assert outcome.summary.total_micro_usd == 10_300


def test_f010_preflight_rejects_missing_or_wrong_authorization_without_creating_resources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "must-not-exist"
    monkeypatch.setattr(uat, "UAT_ROOT", target)
    monkeypatch.setattr(sys, "argv", ["f010_real_provider_uat.py", "--preflight"])

    assert uat.main() == 2
    assert not target.exists()
    assert "authorization_id_mismatch" in capsys.readouterr().out
