"""Thin HTTP boundary for the version-one dialogue use case."""

from __future__ import annotations

import json
from functools import partial
from typing import Annotated, Protocol, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from cyber_town.application.control import (
    ControlUnavailableError,
    NoOpSafetyControl,
    RateLimitExceededError,
    SafetyControlProtocol,
)
from cyber_town.application.dialogue import DialogueFailureKind, DialogueUseCaseError
from cyber_town.application.observability import (
    DialogueObservability,
    ObservabilityRecorder,
    StorageExecutor,
    TerminalOutcome,
    TraceErrorCode,
    call_storage,
)
from cyber_town.contracts.v1 import (
    ApiErrorCode,
    ApiErrorV1,
    DialogueRequestV1,
    DialogueResponseV1,
)

DIALOGUE_PATH = "/api/v1/dialogue"
MAX_DIALOGUE_BODY_BYTES = 8_192
MAX_JSON_CONTAINER_DEPTH = 4
MAX_JSON_CONTAINER_ITEMS = 16


class DialoguePayloadTooLargeError(Exception):
    """The request exceeded the public byte budget before JSON decoding."""


class DialogueApplication(Protocol):
    """The only application capability exposed to the HTTP adapter."""

    async def execute(
        self,
        dialogue_request: DialogueRequestV1,
        *,
        trace_id: UUID,
    ) -> DialogueResponseV1: ...


router = APIRouter()


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    if len(pairs) > MAX_JSON_CONTAINER_ITEMS:
        raise ValueError("JSON object member count exceeds the approved limit")
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object member")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    del value
    raise ValueError("Non-finite JSON values are not permitted")


def _preflight_json_shape(text: str) -> None:
    """Bound nesting and container fan-out without retaining parsed values."""

    stack: list[int] = []
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "{[":
            stack.append(0)
            if len(stack) > MAX_JSON_CONTAINER_DEPTH:
                raise ValueError("JSON nesting exceeds the approved limit")
        elif character in "}]":
            if stack:
                stack.pop()
        elif character == "," and stack:
            stack[-1] += 1
            if stack[-1] >= MAX_JSON_CONTAINER_ITEMS:
                raise ValueError("JSON container item count exceeds the approved limit")


def _validate_json_tree(value: object, *, depth: int = 1) -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ValueError("JSON strings cannot contain surrogate code points")
        return
    if type(value) is dict:
        if depth > MAX_JSON_CONTAINER_DEPTH:
            raise ValueError("JSON nesting exceeds the approved limit")
        if len(value) > MAX_JSON_CONTAINER_ITEMS:
            raise ValueError("JSON object member count exceeds the approved limit")
        for key, item in value.items():
            _validate_json_tree(key, depth=depth)
            _validate_json_tree(item, depth=depth + 1)
        return
    if type(value) is list:
        if depth > MAX_JSON_CONTAINER_DEPTH:
            raise ValueError("JSON nesting exceeds the approved limit")
        if len(value) > MAX_JSON_CONTAINER_ITEMS:
            raise ValueError("JSON array item count exceeds the approved limit")
        for item in value:
            _validate_json_tree(item, depth=depth + 1)


async def _read_bounded_body(request: Request) -> bytes:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_DIALOGUE_BODY_BYTES:
            # Reject as soon as the running byte count exceeds the locked cap;
            # never retain or decode bytes beyond that boundary.
            raise DialoguePayloadTooLargeError
        body.extend(chunk)
    return bytes(body)


async def parse_dialogue_request(request: Request) -> DialogueRequestV1:
    """Validate the JSON bytes in Pydantic's strict JSON mode.

    Strict UUID contracts intentionally accept canonical JSON strings while rejecting
    Python-side string coercion, so FastAPI's decoded-dict validation cannot be used here.
    """

    try:
        peer = request.client
        peer_host = "" if peer is None else peer.host
        try:
            safety_control = _safety_control_for(request)
            operation = partial(safety_control.admit_ingress, peer_host=peer_host)
            await call_storage(
                cast(
                    StorageExecutor | None,
                    getattr(request.app.state.dialogue_service, "storage_executor", None),
                ),
                "control",
                operation,
            )
        except RateLimitExceededError as error:
            raise DialogueUseCaseError(
                kind=DialogueFailureKind.RATE_LIMITED,
                code=ApiErrorCode.RATE_LIMITED,
                public_message="The dialogue request rate limit was exceeded.",
                retryable=True,
                retry_after_seconds=error.retry_after_seconds,
            ) from None
        except ControlUnavailableError:
            raise DialogueUseCaseError(
                kind=DialogueFailureKind.CONTROL_UNAVAILABLE,
                code=ApiErrorCode.CONTROL_UNAVAILABLE,
                public_message="The dialogue safety control is temporarily unavailable.",
                retryable=True,
            ) from None
        body = await _read_bounded_body(request)
        content_type = request.headers.get("content-type", "").partition(";")[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Dialogue requests require application/json")
        content_encoding = request.headers.get("content-encoding")
        if content_encoding is not None and content_encoding.strip().lower() != "identity":
            raise ValueError("Dialogue requests require identity content encoding")
        text = body.decode("utf-8", errors="strict")
        _preflight_json_shape(text)
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
        if type(decoded) is not dict:
            raise ValueError("Dialogue JSON root must be an object")
        _validate_json_tree(decoded)
        dialogue_request = DialogueRequestV1.model_validate_json(body)
        request.state.dialogue_validated = True
        return dialogue_request
    except (UnicodeDecodeError, ValidationError, ValueError):
        raise RequestValidationError([]) from None


def trace_id_for(request: Request) -> UUID:
    """Return one server-generated correlation id for this HTTP attempt."""

    trace_id = getattr(request.state, "trace_id", None)
    if isinstance(trace_id, UUID):
        return trace_id
    trace_id = uuid4()
    request.state.trace_id = trace_id
    return trace_id


def _dialogue_service_for(request: Request) -> DialogueApplication:
    service = cast(
        DialogueApplication | None,
        getattr(request.app.state, "dialogue_service", None),
    )
    if service is None:
        raise DialogueUseCaseError(
            kind=DialogueFailureKind.PROVIDER_UNAVAILABLE,
            code=ApiErrorCode.PROVIDER_UNAVAILABLE,
            public_message="The dialogue service is disabled.",
            retryable=True,
        )
    return service


def _safety_control_for(request: Request) -> SafetyControlProtocol:
    control = getattr(request.app.state, "dialogue_safety_control", None)
    if isinstance(control, SafetyControlProtocol):
        return control
    return NoOpSafetyControl()


@router.post(
    DIALOGUE_PATH,
    response_model=DialogueResponseV1,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorV1},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorV1},
        status.HTTP_409_CONFLICT: {"model": ApiErrorV1},
        status.HTTP_413_CONTENT_TOO_LARGE: {"model": ApiErrorV1},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": ApiErrorV1},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ApiErrorV1},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ApiErrorV1},
        status.HTTP_502_BAD_GATEWAY: {"model": ApiErrorV1},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ApiErrorV1},
        status.HTTP_504_GATEWAY_TIMEOUT: {"model": ApiErrorV1},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": DialogueRequestV1.model_json_schema(mode="validation")
                }
            },
        }
    },
)
async def dialogue(
    dialogue_request: Annotated[DialogueRequestV1, Depends(parse_dialogue_request)],
    request: Request,
) -> DialogueResponseV1:
    """Validate the public request and delegate all behavior to the use case."""

    return await _dialogue_service_for(request).execute(
        dialogue_request,
        trace_id=trace_id_for(request),
    )


def _status_for(error: DialogueUseCaseError) -> int:
    if error.kind == DialogueFailureKind.PROVIDER_INVALID_RESPONSE:
        return status.HTTP_502_BAD_GATEWAY

    return {
        ApiErrorCode.UNSAFE_CONTENT: status.HTTP_400_BAD_REQUEST,
        ApiErrorCode.PAYLOAD_TOO_LARGE: status.HTTP_413_CONTENT_TOO_LARGE,
        ApiErrorCode.NPC_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ApiErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
        ApiErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
        ApiErrorCode.BUDGET_EXHAUSTED: status.HTTP_429_TOO_MANY_REQUESTS,
        ApiErrorCode.PROVIDER_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        ApiErrorCode.PROVIDER_INVALID_RESPONSE: status.HTTP_502_BAD_GATEWAY,
        ApiErrorCode.CIRCUIT_OPEN: status.HTTP_503_SERVICE_UNAVAILABLE,
        ApiErrorCode.CONTROL_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        ApiErrorCode.PROVIDER_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
        ApiErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ApiErrorCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_CONTENT,
    }[error.code]


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: ApiErrorCode,
    message: str,
    retryable: bool,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    error = ApiErrorV1(
        trace_id=trace_id_for(request),
        code=code,
        message=message,
        retryable=retryable,
    )
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(mode="json"),
        headers=headers,
    )


async def handle_dialogue_error(request: Request, exception: Exception) -> JSONResponse:
    """Translate a classified application failure without exposing its cause."""

    if not isinstance(exception, DialogueUseCaseError):
        raise TypeError("Unexpected dialogue exception type")
    if not getattr(request.state, "dialogue_validated", False) and exception.kind in {
        DialogueFailureKind.RATE_LIMITED,
        DialogueFailureKind.CONTROL_UNAVAILABLE,
    }:
        observability = cast(DialogueObservability, request.app.state.dialogue_observability)
        await observability.record_boundary_failure_async(
            trace_id_for(request),
            error_code=(
                TraceErrorCode.RATE_LIMITED
                if exception.kind is DialogueFailureKind.RATE_LIMITED
                else TraceErrorCode.CONTROL_UNAVAILABLE
            ),
            terminal_outcome=(
                TerminalOutcome.REJECTED
                if exception.kind is DialogueFailureKind.RATE_LIMITED
                else TerminalOutcome.FAILED
            ),
            retryable=exception.retryable,
        )
    headers = None
    if exception.code in {ApiErrorCode.RATE_LIMITED, ApiErrorCode.CIRCUIT_OPEN}:
        retry_after = exception.retry_after_seconds
        maximum = 60 if exception.code is ApiErrorCode.RATE_LIMITED else 30
        if type(retry_after) is not int or not 1 <= retry_after <= maximum:
            raise TypeError("Retryable control error requires a bounded retry delay")
        headers = {"Retry-After": str(retry_after)}
    return _error_response(
        request,
        status_code=_status_for(exception),
        code=exception.code,
        message=exception.public_message,
        retryable=exception.retryable,
        headers=headers,
    )


async def handle_validation_error(request: Request, exception: Exception) -> JSONResponse:
    """Replace FastAPI's detailed 422 body with the stable public contract."""

    if not isinstance(exception, RequestValidationError):
        raise TypeError("Unexpected validation exception type")
    observability = cast(
        DialogueObservability,
        request.app.state.dialogue_observability,
    )
    await observability.record_validation_failure_async(trace_id_for(request))
    return _error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code=ApiErrorCode.VALIDATION_ERROR,
        message="Request validation failed.",
        retryable=False,
    )


async def handle_payload_too_large(request: Request, exception: Exception) -> JSONResponse:
    """Reject an oversized body without exposing or decoding its payload."""

    if not isinstance(exception, DialoguePayloadTooLargeError):
        raise TypeError("Unexpected payload exception type")
    observability = cast(
        DialogueObservability,
        request.app.state.dialogue_observability,
    )
    await observability.record_validation_failure_async(trace_id_for(request))
    return _error_response(
        request,
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        code=ApiErrorCode.PAYLOAD_TOO_LARGE,
        message="Request payload is too large.",
        retryable=False,
    )


async def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
    """Fail closed at the HTTP boundary without returning exception details."""

    del exception
    return _error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code=ApiErrorCode.INTERNAL_ERROR,
        message="The dialogue request could not be completed.",
        retryable=False,
    )


def install_dialogue_boundary(
    application: FastAPI,
    dialogue_service: DialogueApplication | None,
    *,
    observability_recorder: ObservabilityRecorder | None = None,
) -> None:
    """Install the route, injectable use case and stable exception handlers."""

    application.state.dialogue_service = dialogue_service
    service_control = getattr(dialogue_service, "safety_control", None)
    application.state.dialogue_safety_control = (
        service_control
        if isinstance(service_control, SafetyControlProtocol)
        else NoOpSafetyControl()
    )
    service_observability = getattr(dialogue_service, "observability", None)
    application.state.dialogue_observability = (
        service_observability
        if isinstance(service_observability, DialogueObservability)
        else DialogueObservability(recorder=observability_recorder)
    )
    application.include_router(router)
    application.add_exception_handler(DialogueUseCaseError, handle_dialogue_error)
    application.add_exception_handler(DialoguePayloadTooLargeError, handle_payload_too_large)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(Exception, handle_unexpected_error)
