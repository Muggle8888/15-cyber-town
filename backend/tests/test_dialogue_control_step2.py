from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import Callable
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from cyber_town.api.app import create_app
from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import (
    SafetyControl,
)
from cyber_town.application.dialogue import (
    DialogueExecutionConfig,
    DialogueFailureKind,
    DialogueService,
    DialogueUseCaseError,
)
from cyber_town.application.memory import ConversationScope, ShortTermSessionStore
from cyber_town.application.observability import (
    InMemoryObservabilityRecorder,
    ProviderKind,
    TraceErrorCode,
    TraceMetadata,
)
from cyber_town.application.provider import (
    ProviderCompletion,
    ProviderProtocol,
    ProviderRequest,
    ProviderUnavailableError,
)
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import (
    SafetyControlStorageError,
    SqliteSafetyControlRepository,
)
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.persistence import sqlite_connection

KEY = b"synthetic-f009-control-key-v1"


class FakeClock:
    def __init__(self) -> None:
        self.now_ns = 1_800_000_000_000_000_000

    def time_ns(self) -> int:
        return self.now_ns


class BlockingProvider:
    def __init__(self) -> None:
        self.started = 0
        self.active = 0
        self.maximum_active = 0
        self.release = asyncio.Event()

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        del request
        self.started += 1
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        try:
            await self.release.wait()
            return completion()
        finally:
            self.active -= 1


def completion() -> ProviderCompletion:
    return ProviderCompletion(
        content="Synthetic local response.",
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="fake",
        model="fake-model",
    )


def request(
    *,
    request_id: UUID | None = None,
    npc_id: str = "neon_guide",
    conversation_id: UUID | None = None,
) -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=request_id or uuid4(),
        player_id="synthetic_player",
        npc_id=npc_id,
        conversation_id=conversation_id or uuid4(),
        message="Synthetic local dialogue.",
    )


def make_control(
    tmp_path: Path,
    clock: FakeClock,
    *,
    permit_wait_seconds: float = 2.0,
) -> tuple[SafetyControl, SqliteSafetyControlRepository]:
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    repository.initialize()
    control = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock.time_ns,
        permit_wait_seconds=permit_wait_seconds,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="deepseek-flash",
        ),
    )
    return control, repository


def make_service(
    provider: ProviderProtocol,
    control: SafetyControl,
    *,
    session_store: ShortTermSessionStore | None = None,
    recorder: InMemoryObservabilityRecorder | None = None,
) -> DialogueService:
    return DialogueService(
        personas=load_bundled_personas(),
        provider=provider,
        config=DialogueExecutionConfig(
            model="deepseek-flash",
            temperature=0.6,
            max_tokens=256,
            timeout_seconds=12.0,
            max_concurrency=2,
            idempotency_ttl_seconds=600.0,
            idempotency_max_entries=256,
        ),
        safety_control=control,
        session_store=session_store,
        observability_recorder=recorder,
        observability_scope_key=KEY if recorder is not None else None,
        observability_provider_kind=ProviderKind.FAKE,
    )


@pytest.mark.anyio
async def test_success_request_uses_three_durable_control_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One valid request persists ingress, provider intent, and final state."""

    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    service = make_service(FakeProvider([completion()]), control)
    application = create_app(dialogue_service=service)
    transport = ASGITransport(
        app=application,
        raise_app_exceptions=False,
        client=("198.51.100.44", 40000),
    )
    commit_count = 0
    path_check_count = 0
    original_connect = repository._connect
    original_validate = sqlite_connection.validate_sqlite_path

    def traced_connect() -> sqlite3.Connection:
        nonlocal commit_count
        connection = original_connect()

        def trace(statement: str) -> None:
            nonlocal commit_count
            if statement == "COMMIT":
                commit_count += 1

        connection.set_trace_callback(trace)
        return connection

    def traced_validate(
        path: Path,
        allowed_root: Path,
    ) -> tuple[object | None, tuple[tuple[int, int], ...]]:
        nonlocal path_check_count
        path_check_count += 1
        return original_validate(path, allowed_root)

    monkeypatch.setattr(repository, "_connect", traced_connect)
    monkeypatch.setattr(sqlite_connection, "validate_sqlite_path", traced_validate)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/dialogue",
            content=request().model_dump_json(),
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 200
    assert (commit_count, path_check_count) == (3, 3)
    intents = repository.execution_intent_snapshot()
    assert len(intents) == 1
    assert intents[0]["state"] == "settled"
    assert intents[0]["terminal_reason"] == "trusted_usage"


@pytest.mark.anyio
async def test_invalid_requests_consume_ingress_and_ignore_forwarded_headers(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    recorder = InMemoryObservabilityRecorder()
    service = make_service(FakeProvider([completion()]), control, recorder=recorder)
    application = create_app(dialogue_service=service)
    transport = ASGITransport(
        app=application,
        raise_app_exceptions=False,
        client=("198.51.100.44", 40000),
    )

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        for index in range(15):
            response = await client.post(
                "/api/v1/dialogue",
                content=b"{",
                headers={
                    "content-type": "application/json",
                    "x-forwarded-for": f"203.0.113.{index + 1}",
                },
            )
            assert response.status_code == 422
        rejected = await client.post(
            "/api/v1/dialogue",
            content=b"{",
            headers={"content-type": "application/json", "forwarded": "for=192.0.2.90"},
        )

    assert rejected.status_code == 429
    assert rejected.json()["code"] == "rate_limited"
    assert rejected.json()["retryable"] is True
    assert rejected.headers["retry-after"] == "1"
    summaries = tuple(record for record in recorder.snapshot() if isinstance(record, TraceMetadata))
    assert len(summaries) == 16
    assert summaries[-1].error_code is TraceErrorCode.RATE_LIMITED
    assert summaries[-1].request_id is None
    assert summaries[-1].scope_tags is None
    assert summaries[-1].provider_dispatch_count == 0


@pytest.mark.anyio
async def test_unknown_npc_and_conflict_do_not_consume_domain_tokens(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    service = make_service(provider, control)
    first = request(request_id=UUID("11111111-1111-4111-8111-111111111111"))

    await service.execute(first, trace_id=uuid4())
    baseline = repository.bucket_snapshot()
    unknown = request(npc_id="neon_guide")
    object.__setattr__(unknown, "npc_id", "unknown_npc")
    with pytest.raises(DialogueUseCaseError) as unknown_error:
        await service.execute(unknown, trace_id=uuid4())
    assert unknown_error.value.kind is DialogueFailureKind.NPC_NOT_FOUND
    conflict = request(
        request_id=first.request_id,
        conversation_id=UUID("22222222-2222-4222-8222-222222222222"),
    )
    with pytest.raises(DialogueUseCaseError) as conflict_error:
        await service.execute(conflict, trace_id=uuid4())
    assert conflict_error.value.kind is DialogueFailureKind.CONFLICT

    assert repository.bucket_snapshot() == baseline
    assert repository.admission_count() == 1
    assert provider.call_count == 1


@pytest.mark.anyio
async def test_replay_and_concurrent_waiter_share_one_admission_and_dispatch(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = BlockingProvider()
    service = make_service(provider, control)
    shared_request = request()

    owner = asyncio.create_task(service.execute(shared_request, trace_id=uuid4()))
    await asyncio.wait_for(_wait_until(lambda: provider.started == 1), timeout=1)
    waiter = asyncio.create_task(service.execute(shared_request, trace_id=uuid4()))
    await asyncio.sleep(0)
    provider.release.set()
    await asyncio.gather(owner, waiter)
    await service.execute(shared_request, trace_id=uuid4())

    assert provider.started == 1
    assert repository.admission_count() == 1
    assert repository.active_permit_count() == 0


@pytest.mark.anyio
async def test_global_and_player_concurrency_limits_do_not_amplify_dispatch(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = BlockingProvider()
    service = make_service(provider, control)
    requests = (
        request(npc_id="neon_guide"),
        request(npc_id="signal_archivist"),
        request(npc_id="night_courier"),
    )

    tasks = [asyncio.create_task(service.execute(item, trace_id=uuid4())) for item in requests]
    await asyncio.wait_for(_wait_until(lambda: provider.started == 2), timeout=1)
    assert provider.maximum_active == 2
    assert repository.active_permit_count() == 2
    provider.release.set()
    await asyncio.gather(*tasks)

    assert provider.started == 3
    assert provider.maximum_active == 2
    assert repository.active_permit_count() == 0


@pytest.mark.anyio
async def test_same_player_npc_is_serial_across_conversations(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = BlockingProvider()
    service = make_service(provider, control)
    tasks = [
        asyncio.create_task(service.execute(request(), trace_id=uuid4())),
        asyncio.create_task(service.execute(request(), trace_id=uuid4())),
    ]

    await asyncio.wait_for(_wait_until(lambda: provider.started == 1), timeout=1)
    assert provider.maximum_active == 1
    assert repository.active_permit_count() == 1
    provider.release.set()
    await asyncio.gather(*tasks)

    assert provider.started == 2
    assert provider.maximum_active == 1
    assert repository.active_permit_count() == 0


@pytest.mark.anyio
async def test_provider_permit_queue_timeout_does_not_amplify_dispatch(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock, permit_wait_seconds=0.01)
    provider = BlockingProvider()
    service = make_service(provider, control)
    owner = asyncio.create_task(service.execute(request(), trace_id=uuid4()))
    await asyncio.wait_for(_wait_until(lambda: provider.started == 1), timeout=1)

    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(request(), trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.PROVIDER_UNAVAILABLE
    assert provider.started == 1
    assert repository.active_permit_count() == 1
    provider.release.set()
    await owner
    assert repository.active_permit_count() == 0


@pytest.mark.anyio
async def test_domain_rate_rejection_has_zero_extra_dispatch_or_state_write(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    provider = FakeProvider([completion(), completion()])
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, session_store=sessions)
    conversation_id = uuid4()

    for _ in range(2):
        await service.execute(request(conversation_id=conversation_id), trace_id=uuid4())
    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(request(conversation_id=conversation_id), trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.RATE_LIMITED
    assert captured.value.retry_after_seconds == 10
    assert provider.call_count == 2
    assert (
        len(sessions.history(ConversationScope("synthetic_player", "neon_guide", conversation_id)))
        == 2
    )


@pytest.mark.anyio
async def test_control_repository_failure_before_dispatch_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, session_store=sessions)
    item = request()

    def fail_admission(**_values: object) -> object:
        raise SafetyControlStorageError

    monkeypatch.setattr(repository, "consume_execution_admission", fail_admission)
    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(item, trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.CONTROL_UNAVAILABLE
    assert provider.call_count == 0
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


@pytest.mark.anyio
async def test_provider_permit_failure_before_dispatch_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, session_store=sessions)
    item = request()

    def fail_permit(**_values: object) -> bool:
        raise SafetyControlStorageError

    monkeypatch.setattr(repository, "try_acquire_permit", fail_permit)
    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(item, trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.CONTROL_UNAVAILABLE
    assert provider.call_count == 0
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


@pytest.mark.anyio
async def test_provider_permit_release_failure_aborts_state_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, session_store=sessions)
    item = request()

    def fail_release(**_values: object) -> None:
        raise SafetyControlStorageError

    monkeypatch.setattr(repository, "release_permit", fail_release)
    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(item, trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.CONTROL_UNAVAILABLE
    assert provider.call_count == 1
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


@pytest.mark.anyio
async def test_provider_failure_releases_permit_without_state_commit(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider(
        [
            ProviderUnavailableError("synthetic private provider detail"),
            ProviderUnavailableError("synthetic private provider detail"),
        ]
    )
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, session_store=sessions)
    item = request()

    with pytest.raises(DialogueUseCaseError) as captured:
        await service.execute(item, trace_id=uuid4())

    assert captured.value.kind is DialogueFailureKind.PROVIDER_UNAVAILABLE
    assert provider.call_count == 2
    assert repository.active_permit_count() == 0
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


@pytest.mark.anyio
async def test_control_observability_snapshot_contains_no_raw_scope_or_payload(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    recorder = InMemoryObservabilityRecorder()
    service = make_service(FakeProvider([completion()]), control, recorder=recorder)
    item = request()

    await service.execute(item, trace_id=uuid4())
    snapshot = repr(recorder.snapshot())

    for forbidden in (
        item.player_id,
        item.npc_id,
        str(item.conversation_id),
        item.message,
        "Synthetic local response.",
        "synthetic private provider detail",
    ):
        assert forbidden not in snapshot


@pytest.mark.anyio
async def test_ingress_repository_failure_returns_safe_503(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = FakeProvider([completion()])
    service = make_service(provider, control)

    def fail_ingress(**_values: object) -> object:
        raise SafetyControlStorageError

    monkeypatch.setattr(repository, "consume_ingress", fail_ingress)
    application = create_app(dialogue_service=service)
    transport = ASGITransport(
        app=application,
        raise_app_exceptions=False,
        client=("192.0.2.55", 40000),
    )
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/dialogue",
            json=request().model_dump(mode="json"),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "control_unavailable"
    assert response.json()["retryable"] is True
    assert "retry-after" not in response.headers
    assert provider.call_count == 0


@pytest.mark.anyio
async def test_cancelled_owner_releases_permit_and_never_commits_late_state(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = BlockingProvider()
    sessions = ShortTermSessionStore()
    service = make_service(provider, control, session_store=sessions)
    item = request()
    task = asyncio.create_task(service.execute(item, trace_id=uuid4()))
    await asyncio.wait_for(_wait_until(lambda: provider.started == 1), timeout=1)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.wait_for(_wait_until(lambda: repository.active_permit_count() == 0), timeout=1)

    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


async def _wait_until(predicate: Callable[[], bool]) -> None:
    for _ in range(1_000):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("Synthetic condition was not reached")
