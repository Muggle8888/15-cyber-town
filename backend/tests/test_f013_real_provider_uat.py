from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import pytest
from pydantic import SecretStr
from scripts import f013_real_provider_uat as uat

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
    uat_root = data_root / "uat" / "f-013"
    ledger_root.mkdir(parents=True)
    uat_root.parent.mkdir(parents=True)
    monkeypatch.setattr(uat, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(uat, "UAT_ROOT", uat_root)
    monkeypatch.setattr(uat, "BUSINESS_DATABASE", uat_root / "cyber-town.sqlite3")
    monkeypatch.setattr(uat, "CONTROL_DATABASE", uat_root / "cyber-town-control.sqlite3")
    monkeypatch.setattr(uat, "LEDGER_ROOT", ledger_root)
    monkeypatch.setattr(uat, "LEDGER_DATABASE", ledger_root / "f-013.sqlite3")
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


def _ledger(ledger_root: Path) -> AcceptanceLedger:
    ledger = AcceptanceLedger(
        database_path=ledger_root / "f-013.sqlite3",
        allowed_root=ledger_root,
    )
    ledger.initialize()
    return ledger


def _successful_replies() -> list[ProviderCompletion]:
    return [
        _completion("夜市灯光确实出现异常，我会先核对缺失的灯带。"),  # noqa: RUF001
        _completion("这段广播编号属于信号档案中的旧记录。"),
        _completion("这条雨夜路线仍用于投递，旧广播记录能帮助核对。"),  # noqa: RUF001
        _completion("我会把暮光信号和雨夜路线一起归档记录。"),
        _completion("我是 Nia，负责街区导览，也愿意帮你规划夜市路线。"),  # noqa: RUF001
        _completion("我是 Rhea，负责雨夜投递，也会确保路线可靠。"),  # noqa: RUF001
    ]


def test_f013_uat_fake_readiness_preserves_visible_text_scope_stage_and_budget(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uat_root, ledger_root = _patch_resources(monkeypatch, tmp_path)
    uat_root.mkdir()
    provider = FakeProvider(_successful_replies())
    clock = _FakeClock()

    outcome = asyncio.run(
        uat.run_uat(
            settings=_settings(),
            provider=provider,
            ledger=_ledger(ledger_root),
            clock_ns=clock,
            pace=clock.pace,
        )
    )

    assert provider.call_count == 6
    assert outcome.checks == 6
    assert outcome.retries == 0
    assert outcome.summary.total_calls == 6
    assert outcome.summary.pending_calls == 0
    assert outcome.summary.total_prompt_tokens == 144
    assert outcome.summary.total_completion_tokens == 72
    assert outcome.summary.total_micro_usd == 132
    assert [request.user_message for request in provider.requests] == [
        case.message for case in uat.CASES
    ]
    assert all(request.long_term_facts == () for request in provider.requests)
    assert all(request.history_messages == () for request in provider.requests)
    assert all(request.reply_style is None for request in provider.requests)
    assert [
        None if request.relationship_stage is None else request.relationship_stage.value
        for request in provider.requests
    ] == [
        "acquaintance",
        "friend",
        "trusted_ally",
        "acquaintance",
        "acquaintance",
        "trusted_ally",
    ]


def test_f013_uat_uses_one_bounded_semantic_retry_without_changing_visible_message(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uat_root, ledger_root = _patch_resources(monkeypatch, tmp_path)
    uat_root.mkdir()
    replies = _successful_replies()
    provider = FakeProvider([_completion("暂时无法判断。"), replies[0], *replies[1:]])
    clock = _FakeClock()

    outcome = asyncio.run(
        uat.run_uat(
            settings=_settings(),
            provider=provider,
            ledger=_ledger(ledger_root),
            clock_ns=clock,
            pace=clock.pace,
        )
    )

    assert provider.call_count == 7
    assert outcome.checks == 6
    assert outcome.retries == 1
    assert outcome.summary.total_calls == 7
    assert provider.requests[0].user_message == uat.CASES[0].message
    assert provider.requests[1].user_message == uat.CASES[0].message


def test_f013_uat_stops_after_two_failed_semantic_retries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uat_root, ledger_root = _patch_resources(monkeypatch, tmp_path)
    uat_root.mkdir()
    provider = FakeProvider([_completion("无法判断。") for _ in range(3)])
    clock = _FakeClock()
    ledger = _ledger(ledger_root)

    with pytest.raises(uat.SemanticUatError, match="nia_intro_context_not_understood"):
        asyncio.run(
            uat.run_uat(
                settings=_settings(),
                provider=provider,
                ledger=ledger,
                clock_ns=clock,
                pace=clock.pace,
            )
        )

    assert provider.call_count == 3
    assert ledger.summary().total_calls == 3
    assert ledger.summary().pending_calls == 0


def test_f013_offline_preflight_does_not_read_credentials_or_create_uat_resources(
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
            "f013_real_provider_uat.py",
            "--offline-preflight",
            "--authorization-id",
            uat.AUTHORIZATION_ID,
        ],
    )

    assert uat.main() == 0
    assert not uat_root.exists()
    output = capsys.readouterr().out
    assert "F013_REAL_UAT_OFFLINE_PREFLIGHT=PASS" in output
    assert "max_retries=2" in output
    assert "cost_first_stop=true" in output


def test_f013_preflight_rejects_missing_authorization_without_creating_resources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    uat_root, _ledger_root = _patch_resources(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["f013_real_provider_uat.py", "--offline-preflight"])

    assert uat.main() == 2
    assert not uat_root.exists()
    assert "authorization_id_mismatch" in capsys.readouterr().out
