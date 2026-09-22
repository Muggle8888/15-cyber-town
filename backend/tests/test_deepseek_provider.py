from __future__ import annotations

import asyncio
import importlib
import logging
import subprocess
import sys
import traceback
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import httpx2
import openai
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from cyber_town.api.app import create_app
from cyber_town.api.composition import build_dialogue_service
from cyber_town.application.control import NoOpSafetyControl
from cyber_town.application.dialogue import DialogueFailureKind, DialogueUseCaseError
from cyber_town.application.provider import (
    ProviderCompletion,
    ProviderHistoryMessage,
    ProviderInvalidResponseError,
    ProviderLongTermFact,
    ProviderRequest,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderUsage,
)
from cyber_town.config import LlmProvider, Settings
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.infrastructure.llm import deepseek
from cyber_town.infrastructure.llm.deepseek import DeepSeekProvider
from cyber_town.infrastructure.llm.fake import FakeProvider

REQUEST = ProviderRequest(
    system_prompt="Frozen synthetic persona prompt.",
    user_message="Where is the quiet street?",
    model="deepseek-flash",
    temperature=0.6,
    max_tokens=256,
    timeout_seconds=12.0,
)


@pytest.fixture(autouse=True)
def isolate_provider_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setattr("cyber_town.api.composition.PROJECT_ROOT", tmp_path)
    (tmp_path / "data").mkdir()


def test_offline_composition_resolves_its_database_inside_pytest_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured_paths: list[tuple[Path, Path]] = []

    def block_repository(*, database_path: Path, allowed_root: Path) -> None:
        captured_paths.append((database_path, allowed_root))
        raise RuntimeError("synthetic repository boundary")

    monkeypatch.setattr(
        "cyber_town.api.composition.SqliteLongTermMemoryRepository", block_repository
    )

    with pytest.raises(RuntimeError, match="synthetic repository boundary"):
        build_dialogue_service(
            enabled_settings(),
            provider=FakeProvider([]),
            safety_control=NoOpSafetyControl(),
        )

    assert captured_paths == [(tmp_path / "data" / "cyber-town.sqlite3", tmp_path / "data")]


class StubCompletions:
    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class StubSdkClient:
    def __init__(self, outcome: Any) -> None:
        self.completions = StubCompletions(outcome)
        self.chat = SimpleNamespace(completions=self.completions)


def sdk_response(
    *,
    content: Any = (
        '{"reply":"The east arcade stays quiet after midnight.",'
        '"relationship":{"category":"neutral","confidence":100}}'
    ),
    finish_reason: Any = "stop",
    choice_count: int = 1,
    tool_calls: Any = None,
    reasoning_content: Any = None,
    usage: Any = "default",
    model: Any = "deepseek-flash",
) -> SimpleNamespace:
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
        reasoning_content=reasoning_content,
    )
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    token_usage = (
        SimpleNamespace(prompt_tokens=23, completion_tokens=11, total_tokens=34)
        if usage == "default"
        else usage
    )
    return SimpleNamespace(choices=[choice] * choice_count, model=model, usage=token_usage)


def response_with_choices(choices: object) -> SimpleNamespace:
    response = sdk_response()
    response.choices = choices
    return response


def adapter(outcome: Any) -> tuple[DeepSeekProvider, StubSdkClient]:
    client = StubSdkClient(outcome)
    return (
        DeepSeekProvider(
            credential=SecretStr("synthetic-provider-value"),
            base_url="https://api.deepseek.com",
            timeout_seconds=12.0,
            client=client,
        ),
        client,
    )


def dialogue_request() -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=UUID("11111111-1111-4111-8111-111111111111"),
        player_id="local_player",
        npc_id="neon_guide",
        conversation_id=UUID("22222222-2222-4222-8222-222222222222"),
        message="Where is the quiet street?",
    )


def enabled_settings() -> Settings:
    return Settings.model_validate(
        {
            "llm_provider": LlmProvider.DEEPSEEK,
            "llm_api_key": SecretStr("synthetic-provider-value"),
        }
    )


def test_sdk_client_uses_approved_endpoint_timeout_and_zero_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def build_client(**kwargs: Any) -> StubSdkClient:
        captured.update(kwargs)
        return StubSdkClient(sdk_response())

    monkeypatch.setattr(deepseek, "AsyncOpenAI", build_client)

    provider = DeepSeekProvider(
        credential=SecretStr("synthetic-provider-value"),
        base_url="https://api.deepseek.com",
        timeout_seconds=12.0,
    )

    assert isinstance(provider, DeepSeekProvider)
    assert captured == {
        "api_key": "synthetic-provider-value",
        "base_url": "https://api.deepseek.com",
        "timeout": 12.0,
        "max_retries": 0,
    }


def test_adapter_sends_frozen_non_thinking_non_streaming_request() -> None:
    provider, client = adapter(sdk_response())

    result = asyncio.run(provider.complete(REQUEST))

    assert len(client.completions.calls) == 1
    assert client.completions.calls[0] == {
        "model": "deepseek-flash",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Frozen synthetic persona prompt.\n\n" + deepseek._RELATIONSHIP_JSON_INSTRUCTION
                ),
            },
            {"role": "user", "content": "Where is the quiet street?"},
        ],
        "temperature": 0.6,
        "max_tokens": 256,
        "stream": False,
        "timeout": 12.0,
        "response_format": {"type": "json_object"},
        "extra_body": {"thinking": {"type": "disabled"}},
    }
    assert result == ProviderCompletion(
        content="The east arcade stays quiet after midnight.",
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="deepseek",
        model="deepseek-flash",
        usage=ProviderUsage(prompt_tokens=23, completion_tokens=11),
        relationship_suggestion={"category": "neutral", "confidence": 100},
    )


@pytest.mark.parametrize(
    "provider_request",
    [
        replace(REQUEST, thinking_enabled=True),
        replace(REQUEST, stream=True),
        replace(REQUEST, model="unapproved-model"),
    ],
)
def test_adapter_rejects_unapproved_request_before_sdk_call(
    provider_request: ProviderRequest,
) -> None:
    provider, client = adapter(sdk_response())

    with pytest.raises(ProviderUnavailableError):
        asyncio.run(provider.complete(provider_request))

    assert client.completions.calls == []


def test_adapter_orders_unique_persona_complete_history_and_current_user() -> None:
    provider, client = adapter(sdk_response())
    request = replace(
        REQUEST,
        history_messages=(
            ProviderHistoryMessage("user", "First synthetic question"),
            ProviderHistoryMessage("assistant", "First synthetic reply"),
            ProviderHistoryMessage("user", "Second synthetic question"),
            ProviderHistoryMessage("assistant", "Second synthetic reply"),
        ),
    )

    asyncio.run(provider.complete(request))

    messages = client.completions.calls[0]["messages"]
    assert messages == [
        {
            "role": "system",
            "content": "Frozen synthetic persona prompt.\n\n"
            + deepseek._RELATIONSHIP_JSON_INSTRUCTION,
        },
        {"role": "user", "content": "First synthetic question"},
        {"role": "assistant", "content": "First synthetic reply"},
        {"role": "user", "content": "Second synthetic question"},
        {"role": "assistant", "content": "Second synthetic reply"},
        {"role": "user", "content": "Where is the quiet street?"},
    ]
    assert sum(message["role"] == "system" for message in messages) == 1


def test_adapter_extracts_only_an_exact_relationship_json_envelope() -> None:
    provider, _ = adapter(
        sdk_response(
            content=(
                '{"reply":"Nia acknowledges the visit.",'
                '"relationship":{"category":"friendly","confidence":80}}'
            )
        )
    )

    completion = asyncio.run(provider.complete(REQUEST))

    assert completion.content == "Nia acknowledges the visit."
    assert completion.relationship_suggestion == {"category": "friendly", "confidence": 80}


def test_adapter_rejects_a_malformed_relationship_envelope() -> None:
    provider, _ = adapter(sdk_response(content='{"reply":"Nia acknowledges the visit."}'))

    with pytest.raises(ProviderInvalidResponseError, match="invalid response"):
        asyncio.run(provider.complete(REQUEST))


def test_adapter_places_untrusted_long_term_facts_before_complete_short_term_history() -> None:
    provider, client = adapter(sdk_response())
    fact = ProviderLongTermFact("game_alias", "BLUE-47")
    request = replace(
        REQUEST,
        long_term_facts=(fact,),
        history_messages=(
            ProviderHistoryMessage("user", "Earlier synthetic question"),
            ProviderHistoryMessage("assistant", "Earlier synthetic reply"),
        ),
    )

    asyncio.run(provider.complete(request))

    messages = client.completions.calls[0]["messages"]
    assert tuple(message["role"] for message in messages) == (
        "system",
        "user",
        "user",
        "assistant",
        "user",
    )
    assert messages[1]["content"] == fact.as_user_content()
    assert "UNTRUSTED_LONG_TERM_MEMORY" in messages[1]["content"]
    assert sum(message["role"] == "system" for message in messages) == 1


def test_adapter_rejects_tampered_long_term_fact_before_sdk_call() -> None:
    provider, client = adapter(sdk_response())
    fact = ProviderLongTermFact("game_alias", "BLUE-47")
    request = replace(REQUEST, long_term_facts=(fact,))
    object.__setattr__(fact, "fact_key", "system")

    with pytest.raises(ProviderUnavailableError):
        asyncio.run(provider.complete(request))

    assert client.completions.calls == []


@pytest.mark.parametrize("injected_role", ["system", "developer", "tool"])
def test_adapter_rejects_tampered_history_role_before_sdk_call(injected_role: str) -> None:
    provider, client = adapter(sdk_response())
    user = ProviderHistoryMessage("user", "Synthetic history")
    assistant = ProviderHistoryMessage("assistant", "Synthetic reply")
    request = replace(REQUEST, history_messages=(user, assistant))
    object.__setattr__(user, "role", injected_role)

    with pytest.raises(ProviderUnavailableError, match="not approved"):
        asyncio.run(provider.complete(request))

    assert client.completions.calls == []


@pytest.mark.parametrize(
    "response",
    [
        sdk_response(choice_count=0),
        sdk_response(choice_count=2),
        sdk_response(tool_calls=[object()]),
        sdk_response(reasoning_content="synthetic reasoning"),
    ],
)
def test_adapter_rejects_untrusted_shape_before_application_validation(
    response: SimpleNamespace,
) -> None:
    provider, _ = adapter(response)

    with pytest.raises(ProviderInvalidResponseError, match="invalid response"):
        asyncio.run(provider.complete(REQUEST))


@pytest.mark.parametrize(
    "invalid_usage",
    [
        None,
        SimpleNamespace(prompt_tokens=-1, completion_tokens=1, total_tokens=0),
        SimpleNamespace(prompt_tokens="23", completion_tokens=1, total_tokens=24),
        SimpleNamespace(prompt_tokens=23, completion_tokens=True, total_tokens=24),
        SimpleNamespace(prompt_tokens=23, completion_tokens=11, total_tokens=35),
    ],
)
def test_missing_or_invalid_usage_fails_closed(invalid_usage: Any) -> None:
    provider, client = adapter(sdk_response(usage=invalid_usage))

    with pytest.raises(ProviderInvalidResponseError, match="invalid response"):
        asyncio.run(provider.complete(REQUEST))

    assert len(client.completions.calls) == 1


def test_sdk_timeout_is_classified_without_exposing_raw_details() -> None:
    request = httpx2.Request("POST", "https://api.deepseek.com/chat/completions")
    sdk_error = openai.APITimeoutError(request=request)
    provider, client = adapter(sdk_error)

    with pytest.raises(ProviderTimeoutError, match="timed out") as captured:
        asyncio.run(provider.complete(REQUEST))

    assert captured.value.__cause__ is None
    assert len(client.completions.calls) == 1


@pytest.mark.parametrize("status_code", [401, 429, 500, 503])
def test_sdk_status_failures_are_classified_and_redacted(status_code: int) -> None:
    request = httpx2.Request("POST", "https://api.deepseek.com/chat/completions")
    response = httpx2.Response(status_code, request=request)
    raw_error = "synthetic-private-provider-detail"
    sdk_error = openai.APIStatusError(raw_error, response=response, body={"detail": raw_error})
    provider, client = adapter(sdk_error)

    with pytest.raises(ProviderUnavailableError) as captured:
        asyncio.run(provider.complete(REQUEST))

    assert raw_error not in str(captured.value)
    assert raw_error not in "".join(traceback.format_exception(captured.value))
    assert captured.value.__cause__ is None
    assert len(client.completions.calls) == 1


def test_sdk_connection_failure_is_classified_without_automatic_retry() -> None:
    request = httpx2.Request("POST", "https://api.deepseek.com/chat/completions")
    sdk_error = openai.APIConnectionError(message="synthetic-network-detail", request=request)
    provider, client = adapter(sdk_error)

    with pytest.raises(ProviderUnavailableError) as captured:
        asyncio.run(provider.complete(REQUEST))

    assert "synthetic-network-detail" not in str(captured.value)
    assert len(client.completions.calls) == 1


COMPOSITION_IMPORT_CHILD = r"""
import asyncio
import importlib.abc
import json
import sys
from pathlib import Path

case, temporary = sys.argv[1:]
targets = ("cyber_town.infrastructure.llm.deepseek", "openai")
assert all(name not in sys.modules for name in targets)
attempts = []

class BlockSdk(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in targets or fullname.startswith("openai."):
            attempts.append(fullname)
            raise ImportError("synthetic_sdk_import_blocked")
        return None

blocker = BlockSdk()
sys.meta_path.insert(0, blocker)
try:
    from cyber_town.api import composition
    from cyber_town.application.control import NoOpSafetyControl
    from cyber_town.config import Settings
    from cyber_town.infrastructure.llm.fake import FakeProvider

    composition.PROJECT_ROOT = Path(temporary)
    if case == "disabled":
        assert composition.build_dialogue_service(Settings.model_validate({})) is None
    else:
        settings = Settings.model_validate({
            "llm_provider": "deepseek", "llm_api_key": "synthetic-provider-value"
        })
        if case == "injected":
            provider = FakeProvider([])
            service = composition.build_dialogue_service(
                settings, provider=provider, safety_control=NoOpSafetyControl()
            )
            assert service is not None
            assert provider.call_count == 0
            asyncio.run(service.aclose())
        else:
            assert case == "import_error"
            try:
                composition.build_dialogue_service(settings, safety_control=NoOpSafetyControl())
            except ImportError as error:
                assert str(error) == "synthetic_sdk_import_blocked"
            else:
                raise AssertionError("expected SDK import error was not propagated")
    assert attempts == ([targets[0]] if case == "import_error" else [])
    assert all(name not in sys.modules for name in targets)
finally:
    sys.meta_path.remove(blocker)
assert blocker not in sys.meta_path
print(json.dumps({"case": case, "sdk_loaded": False, "completed": True}))
"""


@pytest.mark.parametrize("case", ("disabled", "injected", "import_error"))
def test_composition_sdk_import_contract_in_fresh_process(
    case: str, tmp_path: Path, record_property: Callable[[str, object], None]
) -> None:
    import json

    project = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "-B", "-c", COMPOSITION_IMPORT_CHILD, case, str(tmp_path)],
        cwd=project,
        capture_output=True,
        timeout=30,
    )
    record_property("composition_case", case)
    record_property("composition_child_exit_code", completed.returncode)
    assert completed.returncode == 0
    assert len(completed.stdout) <= 256
    assert len(completed.stderr) <= 1024 * 1024
    assert json.loads(completed.stdout) == {"case": case, "sdk_loaded": False, "completed": True}


@pytest.mark.parametrize("case", ("control_key", "pricing", "api_key"))
def test_composition_validates_before_sdk_construction(
    case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        deepseek,
        "DeepSeekProvider",
        lambda **_kwargs: pytest.fail("configuration rejection must precede SDK construction"),
    )
    settings = enabled_settings()
    if case == "control_key":
        with pytest.raises(
            ValueError, match=r"^The enabled dialogue provider requires a safety control key\.$"
        ):
            build_dialogue_service(settings)
    elif case == "pricing":
        with pytest.raises(
            ValueError,
            match=r"^The enabled dialogue provider requires an approved pricing policy\.$",
        ):
            build_dialogue_service(settings, control_scope_key=b"synthetic-control-key")
    else:
        settings = settings.model_copy(update={"llm_api_key": None})
        with pytest.raises(
            ValueError, match=r"^The enabled dialogue provider requires a configured API key\.$"
        ):
            build_dialogue_service(settings, safety_control=NoOpSafetyControl())


def test_composition_preserves_sdk_arguments_and_constructor_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = RuntimeError("synthetic SDK constructor failure")
    captured: list[dict[str, object]] = []

    def construct(**kwargs: object) -> None:
        captured.append(kwargs)
        raise expected

    monkeypatch.setattr(deepseek, "DeepSeekProvider", construct)
    settings = enabled_settings()
    with pytest.raises(RuntimeError, match=r"^synthetic SDK constructor failure$") as failure:
        build_dialogue_service(settings, safety_control=NoOpSafetyControl())
    assert failure.value is expected
    assert captured == [
        {
            "credential": settings.llm_api_key,
            "base_url": settings.llm_base_url,
            "timeout_seconds": settings.llm_timeout_seconds,
        }
    ]


def test_disabled_composition_never_constructs_a_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cyber_town.infrastructure.llm.deepseek.DeepSeekProvider",
        lambda **_kwargs: pytest.fail("disabled provider attempted SDK construction"),
    )

    assert build_dialogue_service(Settings.model_validate({})) is None


def test_enabled_composition_accepts_only_an_injected_offline_test_provider() -> None:
    completion = ProviderCompletion(
        content="Nia points toward the quiet east arcade.",
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="fake",
        model="deepseek-flash",
        usage=ProviderUsage(prompt_tokens=23, completion_tokens=11),
    )
    provider = FakeProvider([completion])
    service = build_dialogue_service(
        enabled_settings(), provider=provider, safety_control=NoOpSafetyControl()
    )

    assert service is not None
    result = asyncio.run(
        service.execute(
            dialogue_request(),
            trace_id=UUID("33333333-3333-4333-8333-333333333333"),
        )
    )
    assert result.reply == "Nia points toward the quiet east arcade."
    assert provider.call_count == 1


def test_invalid_sdk_completion_becomes_a_safe_application_failure() -> None:
    provider, _ = adapter(sdk_response(reasoning_content="synthetic hidden reasoning"))
    service = build_dialogue_service(
        enabled_settings(), provider=provider, safety_control=NoOpSafetyControl()
    )

    assert service is not None
    with pytest.raises(DialogueUseCaseError) as captured:
        asyncio.run(
            service.execute(
                dialogue_request(),
                trace_id=UUID("33333333-3333-4333-8333-333333333333"),
            )
        )

    assert captured.value.kind is DialogueFailureKind.PROVIDER_INVALID_RESPONSE
    assert "synthetic hidden reasoning" not in captured.value.public_message


def test_composed_offline_provider_is_reachable_through_the_dialogue_route() -> None:
    provider, sdk_client = adapter(sdk_response())
    service = build_dialogue_service(
        enabled_settings(), provider=provider, safety_control=NoOpSafetyControl()
    )

    assert service is not None
    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/v1/dialogue",
            json=dialogue_request().model_dump(mode="json"),
        )

    assert response.status_code == 200
    assert response.json()["provider"] == "deepseek"
    assert response.json()["reply"] == "The east arcade stays quiet after midnight."
    assert len(sdk_client.completions.calls) == 1


@pytest.mark.parametrize(
    "malformed_response",
    [
        sdk_response(model="unapproved-response-model"),
        sdk_response(usage=None),
        sdk_response(
            usage=SimpleNamespace(prompt_tokens=True, completion_tokens=1, total_tokens=2)
        ),
        response_with_choices({"wrong": SimpleNamespace()}),
        response_with_choices({0: sdk_response().choices[0]}),
        response_with_choices(tuple(sdk_response().choices)),
    ],
)
def test_invalid_sdk_response_is_mapped_to_public_http_502(
    malformed_response: SimpleNamespace,
) -> None:
    provider, sdk_client = adapter(malformed_response)
    service = build_dialogue_service(
        enabled_settings(), provider=provider, safety_control=NoOpSafetyControl()
    )

    assert service is not None
    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/v1/dialogue",
            json=dialogue_request().model_dump(mode="json"),
        )

    assert response.status_code == 502
    assert response.json()["code"] == "provider_invalid_response"
    assert response.json()["retryable"] is False
    assert len(sdk_client.completions.calls) == 1


def test_sdk_debug_logging_never_emits_prompt_or_player_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    synthetic_prompt = "synthetic-private-system-prompt-7194"
    synthetic_message = "synthetic-private-player-message-3821"

    def handle(request: httpx2.Request) -> httpx2.Response:
        del request
        return httpx2.Response(
            200,
            json={
                "id": "synthetic-completion",
                "object": "chat.completion",
                "created": 0,
                "model": "deepseek-flash",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": (
                                '{"reply":"Synthetic reply.",'
                                '"relationship":{"category":"neutral","confidence":100}}'
                            ),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            },
        )

    sdk_options: dict[str, Any] = {"api_key": "synthetic-provider-value"}
    sdk_client = openai.AsyncOpenAI(
        **sdk_options,
        base_url="https://api.deepseek.com",
        max_retries=0,
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handle)),
    )
    provider = DeepSeekProvider(
        credential=SecretStr("synthetic-provider-value"),
        base_url="https://api.deepseek.com",
        timeout_seconds=12.0,
        client=sdk_client,
    )

    with caplog.at_level(logging.DEBUG, logger="openai._base_client"):
        asyncio.run(
            provider.complete(
                replace(REQUEST, system_prompt=synthetic_prompt, user_message=synthetic_message)
            )
        )

    assert synthetic_prompt not in caplog.text
    assert synthetic_message not in caplog.text


def test_entrypoint_installs_enabled_dialogue_service_before_startup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api_main = importlib.import_module("cyber_town.api.__main__")
    provider = FakeProvider([])
    service = build_dialogue_service(
        enabled_settings(), provider=provider, safety_control=NoOpSafetyControl()
    )
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    assert service is not None
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_API_KEY", "synthetic-provider-value")
    monkeypatch.setattr(api_main.app.state, "dialogue_service", None)
    monkeypatch.setattr(api_main, "build_dialogue_service", lambda _settings: service)
    monkeypatch.setattr(
        api_main.uvicorn,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    api_main.main()

    assert api_main.app.state.dialogue_service is service
    assert calls == [((api_main.app,), {"host": "127.0.0.1", "port": 8000})]
    assert provider.call_count == 0
