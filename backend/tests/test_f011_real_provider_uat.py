from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import pytest
from pydantic import SecretStr
from scripts import f011_real_provider_uat as uat

from cyber_town.application.provider import ProviderCompletion, ProviderUsage
from cyber_town.config import LlmProvider, Settings
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.persistence.acceptance_ledger import AcceptanceLedger


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


def _patch_resources(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    data_root = tmp_path / "data"
    ledger_root = data_root / "acceptance-ledgers"
    uat_root = data_root / "uat" / "f-011"
    ledger_root.mkdir(parents=True)
    uat_root.parent.mkdir(parents=True)
    monkeypatch.setattr(uat, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(uat, "UAT_ROOT", uat_root)
    monkeypatch.setattr(uat, "BUSINESS_DATABASE", uat_root / "cyber-town.sqlite3")
    monkeypatch.setattr(uat, "CONTROL_DATABASE", uat_root / "cyber-town-control.sqlite3")
    monkeypatch.setattr(uat, "LEDGER_ROOT", ledger_root)
    monkeypatch.setattr(uat, "LEDGER_DATABASE", ledger_root / "f-011.sqlite3")
    return uat_root, ledger_root


def _settings() -> Settings:
    return Settings.model_validate(
        {
            "llm_provider": LlmProvider.DEEPSEEK,
            "llm_model": "deepseek-flash",
            "llm_api_key": SecretStr("synthetic-provider-value"),
            "llm_max_retries": 0,
        }
    )


def test_f011_uat_fake_readiness_preserves_scope_stage_style_and_budget(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uat_root, ledger_root = _patch_resources(monkeypatch, tmp_path)
    uat_root.mkdir()
    ledger = AcceptanceLedger(
        database_path=ledger_root / "f-011.sqlite3",
        allowed_root=ledger_root,
    )
    ledger.initialize()
    provider = FakeProvider(
        [
            _completion("霓虹夜市"),
            _completion("我是 Nia，可以为你介绍今晚的街区。"),  # noqa: RUF001
            _completion("小镇故事"),
            _completion("我是 Ivo。\n我负责保存小镇的信号档案。"),
            _completion("雨夜街道"),
            _completion("我是 Rhea，会可靠地完成夜间投递。"),  # noqa: RUF001
        ]
    )
    clock = _FakeClock()

    outcome = asyncio.run(
        uat.run_uat(
            settings=_settings(),
            provider=provider,
            ledger=ledger,
            clock_ns=clock,
            pace=clock.pace,
        )
    )

    assert provider.call_count == 6
    assert outcome.checks == 6
    assert outcome.summary.total_calls == 6
    assert outcome.summary.pending_calls == 0
    assert outcome.summary.total_prompt_tokens == 144
    assert outcome.summary.total_completion_tokens == 72
    assert outcome.summary.total_micro_usd == 132
    assert tuple(fact.fact_value for fact in provider.requests[0].long_term_facts) == ("霓虹夜市",)
    assert provider.requests[1].long_term_facts == ()
    assert tuple(fact.fact_value for fact in provider.requests[2].long_term_facts) == ("小镇故事",)
    assert provider.requests[3].long_term_facts == ()
    assert tuple(fact.fact_value for fact in provider.requests[4].long_term_facts) == ("雨夜街道",)
    assert provider.requests[5].long_term_facts == ()
    assert [
        None if request.relationship_stage is None else request.relationship_stage.value
        for request in provider.requests
    ] == [
        "acquaintance",
        "acquaintance",
        "friend",
        "friend",
        "trusted_ally",
        "trusted_ally",
    ]
    assert [
        None if request.reply_style is None else request.reply_style.value
        for request in provider.requests
    ] == [
        "concise",
        "concise",
        "balanced",
        "balanced",
        "concise",
        "concise",
    ]


def test_f011_offline_preflight_does_not_read_credentials_or_create_uat_resources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    uat_root, _ledger_root = _patch_resources(monkeypatch, tmp_path)
    monkeypatch.setattr(
        uat,
        "_settings_from_authorized_dotenv",
        lambda: (_ for _ in ()).throw(AssertionError("credential access is not allowed")),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "f011_real_provider_uat.py",
            "--offline-preflight",
            "--authorization-id",
            uat.AUTHORIZATION_ID,
        ],
    )

    assert uat.main() == 0
    assert not uat_root.exists()
    output = capsys.readouterr().out
    assert "F011_REAL_UAT_OFFLINE_PREFLIGHT=PASS" in output
    assert "cost_first_stop=true" in output


def test_f011_preflight_rejects_missing_authorization_without_creating_resources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    uat_root, _ledger_root = _patch_resources(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["f011_real_provider_uat.py", "--offline-preflight"])

    assert uat.main() == 2
    assert not uat_root.exists()
    assert "authorization_id_mismatch" in capsys.readouterr().out
