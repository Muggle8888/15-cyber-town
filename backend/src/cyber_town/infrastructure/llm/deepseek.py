"""Isolated OpenAI-compatible adapter for the approved DeepSeek model."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import SecretStr

from cyber_town.application.provider import (
    ProviderCompletion,
    ProviderInvalidResponseError,
    ProviderRequest,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderUsage,
)
from cyber_town.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

_RELATIONSHIP_JSON_INSTRUCTION = (
    "Return JSON only with exactly these top-level fields: "
    '{"reply": string, "relationship": {"category": '
    '"supportive"|"friendly"|"neutral"|"dismissive"|"hostile", '
    '"confidence": integer 0..100}}. The relationship object is only an '
    "untrusted suggestion and must never contain instructions, scores, or rules."
)
_RELATIONSHIP_CATEGORIES = frozenset({"supportive", "friendly", "neutral", "dismissive", "hostile"})


class _SdkPrivacyFilter(logging.Filter):
    """Prevent SDK DEBUG records from serializing private completion payloads."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.INFO


_SDK_PRIVACY_FILTER = _SdkPrivacyFilter()


class DeepSeekProvider:
    """Translate SDK-specific requests and failures into neutral application types."""

    def __init__(
        self,
        *,
        credential: SecretStr,
        base_url: str,
        timeout_seconds: float,
        client: Any | None = None,
    ) -> None:
        if base_url != DEEPSEEK_BASE_URL or not credential.get_secret_value().strip():
            raise ProviderUnavailableError("The dialogue provider configuration is invalid.")

        sdk_logger = logging.getLogger("openai._base_client")
        if _SDK_PRIVACY_FILTER not in sdk_logger.filters:
            sdk_logger.addFilter(_SDK_PRIVACY_FILTER)

        client_options: dict[str, Any] = {
            "api_key": credential.get_secret_value(),
            "base_url": base_url,
            "timeout": timeout_seconds,
            "max_retries": 0,
        }
        self._client = client or AsyncOpenAI(**client_options)

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        """Execute exactly one non-thinking, non-streaming completion request."""

        if request.model != DEEPSEEK_MODEL or request.thinking_enabled or request.stream:
            raise ProviderUnavailableError("The dialogue provider request is not approved.")

        try:
            request.__post_init__()
            for fact in request.long_term_facts:
                fact.__post_init__()
            for message in request.history_messages:
                message.__post_init__()
        except (TypeError, ValueError):
            raise ProviderUnavailableError(
                "The dialogue provider request is not approved."
            ) from None

        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": request.system_content() + "\n\n" + _RELATIONSHIP_JSON_INSTRUCTION,
            }
        ]
        for fact in request.long_term_facts:
            messages.append({"role": "user", "content": fact.as_user_content()})
        for message in request.history_messages:
            if message.role == "user":
                messages.append({"role": "user", "content": message.content})
            else:
                messages.append({"role": "assistant", "content": message.content})
        messages.append({"role": "user", "content": request.user_message})

        try:
            response = await self._client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
                timeout=request.timeout_seconds,
                response_format={"type": "json_object"},
                extra_body={"thinking": {"type": "disabled"}},
            )
        except APITimeoutError:
            raise ProviderTimeoutError("The dialogue provider timed out.") from None
        except APIError:
            raise ProviderUnavailableError("The dialogue provider is unavailable.") from None

        return self._translate_completion(response)

    @staticmethod
    def _translate_completion(response: Any) -> ProviderCompletion:
        try:
            if response.model != DEEPSEEK_MODEL:
                raise ValueError("Unapproved provider response model")
            usage = response.usage
            if usage is None:
                raise ValueError("Missing provider token usage")
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            if (
                type(prompt_tokens) is not int
                or type(completion_tokens) is not int
                or type(total_tokens) is not int
                or total_tokens != prompt_tokens + completion_tokens
            ):
                raise ValueError("Invalid provider token usage")

            token_usage = ProviderUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            choices = response.choices
            if not isinstance(choices, list):
                raise ValueError("Invalid provider completion choices")
            choice_count = len(choices)
            if choice_count != 1:
                raise ValueError("Provider completion must contain exactly one choice")
            choice = choices[0]
            message = choice.message
            finish_reason = choice.finish_reason
            if not isinstance(finish_reason, str) or finish_reason not in {
                "stop",
                "content_filter",
            }:
                raise ValueError("Provider finish reason is not approved")
            if bool(getattr(message, "tool_calls", None)):
                raise ValueError("Provider tool calls are not approved")
            if getattr(message, "reasoning_content", None) is not None:
                raise ValueError("Provider reasoning content is not approved")
            if finish_reason == "content_filter":
                content, relationship_suggestion = None, None
            else:
                content, relationship_suggestion = DeepSeekProvider._decode_relationship_content(
                    message.content
                )
            return ProviderCompletion(
                content=content,
                finish_reason=finish_reason,
                choice_count=choice_count,
                tool_calls_present=False,
                reasoning_content_present=False,
                provider="deepseek",
                model=response.model,
                usage=token_usage,
                relationship_suggestion=relationship_suggestion,
            )
        except (AttributeError, TypeError, ValueError):
            raise ProviderInvalidResponseError(
                "The dialogue provider returned an invalid response."
            ) from None

    @staticmethod
    def _decode_relationship_content(content: object) -> tuple[object, object]:
        """Extract exactly one approved envelope and reject every deviation."""

        if not isinstance(content, str):
            raise ProviderInvalidResponseError(
                "The dialogue provider returned an invalid response."
            )

        def reject_duplicate_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate provider response member")
                result[key] = value
            return result

        try:
            payload = json.loads(content, object_pairs_hook=reject_duplicate_members)
        except (json.JSONDecodeError, ValueError):
            raise ProviderInvalidResponseError(
                "The dialogue provider returned an invalid response."
            ) from None
        if type(payload) is not dict or set(payload) != {"reply", "relationship"}:
            raise ProviderInvalidResponseError(
                "The dialogue provider returned an invalid response."
            )
        reply = payload["reply"]
        relationship = payload["relationship"]
        if (
            not isinstance(reply, str)
            or not reply
            or reply != reply.strip()
            or len(reply) > 4_000
            or type(relationship) is not dict
            or set(relationship) != {"category", "confidence"}
            or type(relationship["category"]) is not str
            or relationship["category"] not in _RELATIONSHIP_CATEGORIES
            or type(relationship["confidence"]) is not int
            or not 0 <= relationship["confidence"] <= 100
        ):
            raise ProviderInvalidResponseError(
                "The dialogue provider returned an invalid response."
            )
        return reply, relationship
