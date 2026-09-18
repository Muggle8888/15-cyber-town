from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from cyber_town.api.app import create_app
from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import (
    CircuitOpenError,
    SafetyControl,
)
from cyber_town.application.dialogue import (
    DialogueExecutionConfig,
    DialogueFailureKind,
    DialogueService,
    DialogueUseCaseError,
)
from cyber_town.application.memory import ConversationScope, ShortTermSessionStore
from cyber_town.application.observability import ProviderKind
from cyber_town.application.provider import (
    ProviderCompletion,
    ProviderInvalidResponseError,
    ProviderProtocol,
    ProviderRequest,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderUsage,
)
from cyber_town.application.retry import (
    BREAKER_POLICY_VERSION,
    PROVIDER_ATTEMPT_TIMEOUT_SECONDS,
    PROVIDER_EXECUTION_DEADLINE_SECONDS,
    BreakerFailureReason,
    ProviderRetryPolicy,
    RetryBreakerMetadata,
    RetryBreakerRecorder,
)
from cyber_town.application.safety import BreakerOutcome, BreakerState
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import (
    SafetyControlStorageError,
    SqliteSafetyControlRepository,
)
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.observability.storage_codec import decode_value

KEY = b"synthetic-f009-retry-breaker-key-v1"
BASE_NS = 1_900_000_000_000_000_000


class FakeClock:
    def __init__(self) -> None:
        self.now_ns = BASE_NS

    def time_ns(self) -> int:
        return self.now_ns

    def monotonic(self) -> float:
        return self.now_ns / 1_000_000_000

    def advance(self, seconds: float) -> None:
        self.now_ns += round(seconds * 1_000_000_000)


class SequenceProvider:
    def __init__(self, items: list[ProviderCompletion | Exception]) -> None:
        self._items = list(items)
        self.call_count = 0
        self.requests: list[ProviderRequest] = []

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        self.requests.append(request)
        self.call_count += 1
        item = self._items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def completion() -> ProviderCompletion:
    return ProviderCompletion(
        content="Synthetic retry response.",
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="fake",
        model="fake-model",
        usage=ProviderUsage(prompt_tokens=10, completion_tokens=5),
    )


def request(*, request_id: UUID | None = None) -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=request_id or uuid4(),
        player_id="synthetic_player",
        npc_id="neon_guide",
        conversation_id=uuid4(),
        message="Synthetic retry test.",
    )


def make_control(
    tmp_path: Path,
    clock: FakeClock,
) -> tuple[SafetyControl, SqliteSafetyControlRepository]:
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    repository.initialize()
    return (
        SafetyControl(
            repository=repository,
            scope_key=KEY,
            clock_ns=clock.time_ns,
            monotonic_clock=clock.monotonic,
            pricing_policy=PricingPolicy.zero_cost(
                provider_kind=ProviderKind.FAKE,
                model="fake-model",
            ),
        ),
        repository,
    )


def make_service(
    provider: ProviderProtocol,
    control: SafetyControl,
    clock: FakeClock,
    *,
    sleep: Callable[[float], Awaitable[None]] | None = None,
    observability: SqliteObservabilityRepository | None = None,
    retry_recorder: RetryBreakerRecorder | None = None,
    sessions: ShortTermSessionStore | None = None,
) -> DialogueService:
    async def advancing_sleep(seconds: float) -> None:
        clock.advance(seconds)

    return DialogueService(
        personas=load_bundled_personas(),
        provider=provider,
        config=DialogueExecutionConfig(
            model="fake-model",
            temperature=0.6,
            max_tokens=256,
            timeout_seconds=12.0,
            max_concurrency=2,
            idempotency_ttl_seconds=600.0,
            idempotency_max_entries=256,
        ),
        safety_control=control,
        clock=clock.monotonic,
        retry_sleep=advancing_sleep if sleep is None else sleep,
        retry_jitter=lambda: 0.1,
        observability_recorder=observability,
        observability_scope_key=KEY if observability is not None else None,
        observability_provider_kind=ProviderKind.FAKE,
        safety_cost_recorder=observability,
        retry_breaker_recorder=retry_recorder or observability,
        session_store=sessions,
    )


def test_retry_and_breaker_policy_is_fixed() -> None:
    policy = ProviderRetryPolicy()
    assert BREAKER_POLICY_VERSION == "f-009-retry-breaker-v1"
    assert PROVIDER_ATTEMPT_TIMEOUT_SECONDS == 5.0
    assert PROVIDER_EXECUTION_DEADLINE_SECONDS == 12.0
    assert policy.max_attempts == 2
    assert policy.backoff_seconds == 0.2
    assert policy.max_jitter_seconds == 0.2


def test_breaker_persists_open_half_open_and_two_probe_successes(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)

    for _ in range(5):
        execution_id = uuid4()
        decision = control.check_provider_breaker(execution_id=execution_id)
        assert decision.outcome is BreakerOutcome.ALLOWED
        control.record_provider_failure(
            execution_id=execution_id,
            reason=BreakerFailureReason.TIMEOUT,
        )

    with pytest.raises(CircuitOpenError) as opened:
        control.check_provider_breaker(execution_id=uuid4())
    assert opened.value.retry_after_seconds == 30

    restarted = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock.time_ns,
        monotonic_clock=clock.monotonic,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )
    with pytest.raises(CircuitOpenError):
        restarted.check_provider_breaker(execution_id=uuid4())

    clock.advance(30)
    first_probe = uuid4()
    assert restarted.check_provider_breaker(execution_id=first_probe).outcome is (
        BreakerOutcome.PROBE_ALLOWED
    )
    with pytest.raises(CircuitOpenError) as concurrent_probe:
        restarted.check_provider_breaker(execution_id=uuid4())
    assert concurrent_probe.value.retry_after_seconds == 1
    restarted.record_provider_success(execution_id=first_probe)

    second_probe = uuid4()
    assert restarted.check_provider_breaker(execution_id=second_probe).outcome is (
        BreakerOutcome.PROBE_ALLOWED
    )
    restarted.record_provider_success(execution_id=second_probe)
    assert restarted.check_provider_breaker(execution_id=uuid4()).state is BreakerState.CLOSED


@pytest.mark.anyio
async def test_timeout_retries_once_with_same_execution_and_attempt_budget(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = SequenceProvider([ProviderTimeoutError(), completion()])
    service = make_service(provider, control, clock)

    response = await service.execute(request(), trace_id=uuid4())

    assert response.status == "completed"
    assert provider.call_count == 2
    attempts = repository.budget_attempt_snapshot()
    assert len(attempts) == 2
    assert {int(row["attempt_number"]) for row in attempts} == {1, 2}
    assert len({str(row["execution_id"]) for row in attempts}) == 1
    assert repository.budget_settlement_count() == 2
    assert repository.breaker_result_count() == 1
    assert clock.monotonic() == pytest.approx(BASE_NS / 1_000_000_000 + 0.3)
    assert [item.timeout_seconds for item in provider.requests] == [5.0, 5.0]


@pytest.mark.anyio
async def test_execution_deadline_prevents_retry_amplification(tmp_path: Path) -> None:
    class DeadlineConsumingProvider:
        def __init__(self) -> None:
            self.call_count = 0

        async def complete(self, provider_request: ProviderRequest) -> ProviderCompletion:
            del provider_request
            self.call_count += 1
            clock.advance(11.9)
            raise ProviderUnavailableError

    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = DeadlineConsumingProvider()
    service = make_service(provider, control, clock)

    with pytest.raises(DialogueUseCaseError) as raised:
        await service.execute(request(), trace_id=uuid4())

    assert raised.value.kind is DialogueFailureKind.PROVIDER_UNAVAILABLE
    assert provider.call_count == 1
    assert repository.budget_attempt_count() == 1
    assert repository.breaker_result_count() == 1


@pytest.mark.anyio
async def test_unavailable_exhaustion_counts_one_execution_failure(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = SequenceProvider([ProviderUnavailableError(), ProviderUnavailableError()])
    service = make_service(provider, control, clock)

    with pytest.raises(DialogueUseCaseError) as raised:
        await service.execute(request(), trace_id=uuid4())

    assert raised.value.kind is DialogueFailureKind.PROVIDER_UNAVAILABLE
    assert provider.call_count == 2
    assert repository.budget_attempt_count() == 2
    assert repository.budget_settlement_count() == 2
    assert repository.breaker_result_count() == 1


@pytest.mark.anyio
async def test_invalid_response_never_retries_but_counts_for_breaker(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = SequenceProvider([ProviderInvalidResponseError()])
    service = make_service(provider, control, clock)

    with pytest.raises(DialogueUseCaseError) as raised:
        await service.execute(request(), trace_id=uuid4())

    assert raised.value.kind is DialogueFailureKind.PROVIDER_INVALID_RESPONSE
    assert provider.call_count == 1
    assert repository.budget_attempt_count() == 1
    assert repository.breaker_result_count() == 1


@pytest.mark.anyio
async def test_cancellation_during_backoff_stops_retry_and_does_not_count_failure(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = SequenceProvider([ProviderUnavailableError(), completion()])
    sleep_started = asyncio.Event()
    release_sleep = asyncio.Event()

    async def blocking_sleep(seconds: float) -> None:
        assert 0.2 <= seconds <= 0.4
        sleep_started.set()
        await release_sleep.wait()

    service = make_service(provider, control, clock, sleep=blocking_sleep)
    task = asyncio.create_task(service.execute(request(), trace_id=uuid4()))
    await sleep_started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert provider.call_count == 1
    assert repository.budget_attempt_count() == 1
    assert repository.breaker_result_count() == 0


def test_control_migration_is_append_only_v3(tmp_path: Path) -> None:
    _, repository = make_control(tmp_path, FakeClock())
    with sqlite3.connect(repository.database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (9,)
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
    assert {"circuit_breakers", "breaker_probe_leases", "breaker_execution_results"} <= tables


def test_half_open_allows_only_one_concurrent_probe(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    for _ in range(5):
        execution_id = uuid4()
        control.check_provider_breaker(execution_id=execution_id)
        control.record_provider_failure(
            execution_id=execution_id,
            reason=BreakerFailureReason.UNAVAILABLE,
        )
    clock.advance(30)
    execution_ids = (uuid4(), uuid4())

    def attempt(execution_id: UUID) -> str:
        try:
            return control.check_provider_breaker(execution_id=execution_id).outcome.value
        except CircuitOpenError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(attempt, execution_ids))

    assert sorted(outcomes) == ["probe_allowed", "rejected"]


def test_restart_releases_stale_probe_without_transition(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    for _ in range(5):
        execution_id = uuid4()
        control.check_provider_breaker(execution_id=execution_id)
        control.record_provider_failure(
            execution_id=execution_id,
            reason=BreakerFailureReason.INVALID_RESPONSE,
        )
    clock.advance(30)
    stale_execution = uuid4()
    assert control.check_provider_breaker(execution_id=stale_execution).state is (
        BreakerState.HALF_OPEN
    )

    restarted = SafetyControl(
        repository=repository,
        scope_key=KEY,
        clock_ns=clock.time_ns,
        monotonic_clock=clock.monotonic,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )
    replacement = uuid4()
    assert restarted.check_provider_breaker(execution_id=replacement).outcome is (
        BreakerOutcome.PROBE_ALLOWED
    )
    assert repository.breaker_result_count() == 5


@pytest.mark.anyio
async def test_open_breaker_returns_503_retry_after_without_dispatch_or_budget(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    for _ in range(5):
        execution_id = uuid4()
        control.check_provider_breaker(execution_id=execution_id)
        control.record_provider_failure(
            execution_id=execution_id,
            reason=BreakerFailureReason.TIMEOUT,
        )
    provider = SequenceProvider([completion()])
    service = make_service(provider, control, clock)
    application = create_app(dialogue_service=service)
    transport = ASGITransport(app=application, raise_app_exceptions=False)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/dialogue",
            json=request().model_dump(mode="json"),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "circuit_open"
    assert response.json()["retryable"] is True
    assert response.headers["retry-after"] == "30"
    assert provider.call_count == 0
    assert repository.budget_attempt_count() == 0


@pytest.mark.anyio
async def test_retry_breaker_events_are_metadata_only_and_durable(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    observability = SqliteObservabilityRepository(
        database_path=tmp_path / "observability.sqlite3",
        allowed_root=tmp_path,
    )
    observability.initialize()
    provider = SequenceProvider([ProviderUnavailableError(), completion()])
    service = make_service(provider, control, clock, observability=observability)
    item = request()

    await service.execute(item, trace_id=uuid4())

    with sqlite3.connect(observability.database_path) as connection:
        rows = connection.execute(
            "SELECT attempt_number, event_kind, retry_outcome, breaker_state, "
            "breaker_outcome, failure_reason, backoff_ms, jitter_ms "
            "FROM retry_breaker_events ORDER BY attempt_number, event_kind"
        ).fetchall()
    assert any(
        decode_value("retry_breaker_events", "event_kind", row[1]) == "retry_scheduled"
        and decode_value("retry_breaker_events", "retry_outcome", row[2]) == "scheduled"
        for row in rows
    )
    assert any(
        row[0] == 2
        and decode_value("retry_breaker_events", "event_kind", row[1]) == "breaker_result"
        for row in rows
    )
    database_bytes = observability.database_path.read_bytes()
    for forbidden in (
        item.player_id,
        item.npc_id,
        str(item.conversation_id),
        item.message,
        "Synthetic retry response.",
    ):
        assert forbidden.encode() not in database_bytes


@pytest.mark.anyio
async def test_retry_recorder_failure_does_not_change_execution_or_breaker(
    tmp_path: Path,
) -> None:
    class FailingRecorder:
        def record_retry_breaker(self, metadata: RetryBreakerMetadata) -> None:
            del metadata
            raise RuntimeError("synthetic recorder failure")

    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = SequenceProvider([ProviderUnavailableError(), completion()])
    service = make_service(
        provider,
        control,
        clock,
        retry_recorder=FailingRecorder(),
    )

    result = await service.execute(request(), trace_id=uuid4())

    assert result.status == "completed"
    assert provider.call_count == 2
    assert repository.budget_settlement_count() == 2
    assert repository.breaker_result_count() == 1


def test_half_open_failure_reopens_for_full_interval(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)
    for _ in range(5):
        execution_id = uuid4()
        control.check_provider_breaker(execution_id=execution_id)
        control.record_provider_failure(
            execution_id=execution_id,
            reason=BreakerFailureReason.TIMEOUT,
        )
    clock.advance(30)
    probe = uuid4()
    control.check_provider_breaker(execution_id=probe)
    decision = control.record_provider_failure(
        execution_id=probe,
        reason=BreakerFailureReason.UNAVAILABLE,
    )
    assert decision.state is BreakerState.OPEN
    with pytest.raises(CircuitOpenError) as reopened:
        control.check_provider_breaker(execution_id=uuid4())
    assert reopened.value.retry_after_seconds == 30


@pytest.mark.anyio
async def test_breaker_result_storage_failure_blocks_business_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    sessions = ShortTermSessionStore(clock=clock.monotonic)
    provider = SequenceProvider([completion()])
    service = make_service(provider, control, clock, sessions=sessions)
    item = request()

    def fail_result(**kwargs: object) -> object:
        del kwargs
        raise SafetyControlStorageError

    monkeypatch.setattr(repository, "record_breaker_result", fail_result)
    with pytest.raises(DialogueUseCaseError) as raised:
        await service.execute(item, trace_id=uuid4())

    assert raised.value.kind is DialogueFailureKind.CONTROL_UNAVAILABLE
    assert provider.call_count == 1
    assert repository.budget_settlement_count() == 1
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )


@pytest.mark.anyio
async def test_breaker_check_storage_failure_is_predispatch_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = SequenceProvider([completion()])
    service = make_service(provider, control, clock)

    def fail_check(**kwargs: object) -> object:
        del kwargs
        raise SafetyControlStorageError

    monkeypatch.setattr(repository, "check_breaker", fail_check)
    with pytest.raises(DialogueUseCaseError) as raised:
        await service.execute(request(), trace_id=uuid4())

    assert raised.value.kind is DialogueFailureKind.CONTROL_UNAVAILABLE
    assert provider.call_count == 0
    assert repository.budget_attempt_count() == 0


@pytest.mark.anyio
async def test_concurrent_waiter_shares_the_two_attempt_execution(tmp_path: Path) -> None:
    class RetryThenBlockProvider:
        def __init__(self) -> None:
            self.call_count = 0
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def complete(self, provider_request: ProviderRequest) -> ProviderCompletion:
            del provider_request
            self.call_count += 1
            if self.call_count == 1:
                raise ProviderUnavailableError
            self.started.set()
            await self.release.wait()
            return completion()

    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    provider = RetryThenBlockProvider()
    service = make_service(provider, control, clock)
    item = request()
    owner = asyncio.create_task(service.execute(item, trace_id=uuid4()))
    await provider.started.wait()
    waiter = asyncio.create_task(service.execute(item, trace_id=uuid4()))
    await asyncio.sleep(0)
    provider.release.set()
    owner_result, waiter_result = await asyncio.gather(owner, waiter)

    assert owner_result.reply == waiter_result.reply
    assert provider.call_count == 2
    assert repository.budget_attempt_count() == 2
    assert repository.breaker_result_count() == 1


@pytest.mark.anyio
async def test_cancel_resistant_late_completion_cannot_change_breaker_or_state(
    tmp_path: Path,
) -> None:
    class CancelResistantProvider:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.call_count = 0

        async def complete(self, provider_request: ProviderRequest) -> ProviderCompletion:
            del provider_request
            self.call_count += 1
            self.started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                return completion()
            raise AssertionError("unreachable synthetic provider path")

    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    sessions = ShortTermSessionStore(clock=clock.monotonic)
    provider = CancelResistantProvider()
    service = make_service(provider, control, clock, sessions=sessions)
    item = request()
    waiter = asyncio.create_task(service.execute(item, trace_id=uuid4()))
    await provider.started.wait()
    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    for _ in range(6):
        await asyncio.sleep(0)

    assert provider.call_count == 1
    assert repository.breaker_result_count() == 0
    assert repository.budget_settlement_count() == 1
    assert (
        sessions.history(ConversationScope(item.player_id, item.npc_id, item.conversation_id)) == ()
    )
