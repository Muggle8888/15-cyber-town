"""Single-turn, provider-neutral dialogue application service."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from functools import partial
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from cyber_town.application.budget import (
    BUDGET_POLICY_VERSION,
    BudgetEventKind,
    BudgetRejectedError,
    BudgetReservation,
    BudgetSettlement,
    NoOpSafetyCostRecorder,
    SafetyCostMetadata,
    SafetyCostRecorder,
)
from cyber_town.application.context_budget import (
    ContextBudgetError,
    ContextBudgetFailure,
    estimate_context_units,
    select_context_messages,
    select_history_messages,
)
from cyber_town.application.control import (
    CircuitOpenError,
    ControlCapacityError,
    ControlUnavailableError,
    NoOpSafetyControl,
    ProviderPermit,
    RateLimitExceededError,
    SafetyControl,
    SafetyControlProtocol,
)
from cyber_town.application.memory import (
    ConversationScope,
    ConversationTurn,
    SessionCapacityError,
    ShortTermSessionStore,
)
from cyber_town.application.observability import (
    AttemptKind,
    DialogueObservability,
    DialogueTrace,
    IdempotencyOutcome,
    LongTermOutcome,
    ObservabilityRecorder,
    ProviderKind,
    RelationshipOutcome,
    ShortTermOutcome,
    StageOutcome,
    StorageExecutor,
    TerminalOutcome,
    TraceErrorCode,
    TraceReasonCode,
    TraceStage,
    call_storage,
    finish_cleanup,
)
from cyber_town.application.provider import (
    ProviderCompletion,
    ProviderHistoryMessage,
    ProviderInvalidResponseError,
    ProviderLongTermFact,
    ProviderProtocol,
    ProviderRequest,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderUsage,
)
from cyber_town.application.retry import (
    BreakerDecision,
    BreakerFailureReason,
    NoOpRetryBreakerRecorder,
    ProviderRetryPolicy,
    RetryBreakerEventKind,
    RetryBreakerMetadata,
    RetryBreakerRecorder,
)
from cyber_town.application.safety import (
    BreakerOutcome,
    BreakerState,
    BudgetOutcome,
    InputSecurityPolicy,
    RetryOutcome,
    SafetyOutcome,
)
from cyber_town.contracts.v1 import (
    ApiErrorCode,
    DialogueRequestV1,
    DialogueResponseV1,
    DialogueStatus,
)
from cyber_town.domain.long_term_memory import LongTermMemoryScope
from cyber_town.domain.persona import PersonaDefinition
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import LongTermMemoryStorageError
from cyber_town.infrastructure.persistence.sqlite_relationship import (
    RelationshipConflictError,
    RelationshipStorageError,
)

if TYPE_CHECKING:
    from cyber_town.application.long_term_memory import (
        LongTermMemoryRetriever,
        LongTermMemoryService,
    )
    from cyber_town.application.relationship import RelationshipService

LOGGER = logging.getLogger("cyber_town.dialogue")
NO_HISTORY_REPLY_ZH = "当前会话中还没有你先前告诉我的信息\uff0c因此我不知道。"
NO_HISTORY_REPLY_EN = "You have not told me that in this conversation yet, so I do not know."
_HISTORY_REFERENCE_MARKERS = (
    "刚才",
    "刚刚",
    "之前",
    "先前",
    "此前",
    "告诉过",
    "说过",
    "提过",
    "记得",
    "earlier",
    "before",
    "previous",
    "last time",
    "told you",
    "tell you",
    "mentioned",
    "remember",
)
_HISTORY_QUERY_MARKERS = (
    "?",
    "\uff1f",
    "什么",
    "多少",
    "哪",
    "谁",
    "是否",
    "有没有",
    "能否",
    "吗",
    "what ",
    "which ",
    "who ",
    "when ",
    "where ",
    "do you ",
    "did i ",
    "can you ",
)


class DialogueFailureKind(StrEnum):
    """Internal failure categories kept separate from public v1 error codes."""

    NPC_NOT_FOUND = "npc_not_found"
    CONFLICT = "conflict"
    VALIDATION_ERROR = "validation_error"
    UNSAFE_CONTENT = "unsafe_content"
    RATE_LIMITED = "rate_limited"
    BUDGET_EXHAUSTED = "budget_exhausted"
    CONTROL_UNAVAILABLE = "control_unavailable"
    CIRCUIT_OPEN = "circuit_open"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_INVALID_RESPONSE = "provider_invalid_response"
    INTERNAL_ERROR = "internal_error"


class DialogueUseCaseError(Exception):
    """A safe application error ready for HTTP translation in a later Step."""

    def __init__(
        self,
        *,
        kind: DialogueFailureKind,
        code: ApiErrorCode,
        public_message: str,
        retryable: bool,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(public_message)
        self.kind = kind
        self.code = code
        self.public_message = public_message
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True, slots=True)
class DialogueExecutionConfig:
    """Validated execution values supplied by the future composition root."""

    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    max_concurrency: int
    idempotency_ttl_seconds: float
    idempotency_max_entries: int

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("Dialogue model cannot be blank")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Dialogue temperature must be between 0 and 2")
        if not 1 <= self.max_tokens <= 1_024:
            raise ValueError("Dialogue max tokens must be between 1 and 1024")
        if not 0.1 <= self.timeout_seconds <= 60.0:
            raise ValueError("Dialogue timeout must be between 0.1 and 60 seconds")
        if not 1 <= self.max_concurrency <= 8:
            raise ValueError("Dialogue concurrency must be between 1 and 8")
        if not 1.0 <= self.idempotency_ttl_seconds <= 3_600.0:
            raise ValueError("Dialogue idempotency TTL must be between 1 and 3600 seconds")
        if not 1 <= self.idempotency_max_entries <= 4_096:
            raise ValueError("Dialogue idempotency capacity must be between 1 and 4096")


@dataclass(frozen=True, slots=True)
class _DialogueResult:
    reply: str
    status: DialogueStatus
    provider: str
    provider_model: str
    persona_version: str
    usage: ProviderUsage
    latency_ms: int
    provider_wait_ms: int = 0
    relationship_suggestion: object = None


@dataclass(slots=True)
class _IdempotencyEntry:
    fingerprint: str
    task: asyncio.Task[_DialogueResult] | None
    result: _DialogueResult | None
    expires_at: float
    waiters: int = 0
    long_term_revision: int = 0
    execution_id: UUID | None = None


@dataclass(slots=True)
class _OwnershipLock:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    users: int = 0


@dataclass(slots=True)
class _BudgetAttemptState:
    reservation: BudgetReservation
    dispatched: bool = False
    settled: bool = False


class DialogueService:
    """Execute one validated player-to-NPC command without persistence."""

    def __init__(
        self,
        *,
        personas: Mapping[str, PersonaDefinition],
        provider: ProviderProtocol,
        config: DialogueExecutionConfig,
        session_store: ShortTermSessionStore | None = None,
        clock: Callable[[], float] | None = None,
        long_term_memory: LongTermMemoryService | None = None,
        long_term_retriever: LongTermMemoryRetriever | None = None,
        relationship_service: RelationshipService | None = None,
        input_security_policy: InputSecurityPolicy | None = None,
        safety_control: SafetyControlProtocol | None = None,
        observability_recorder: ObservabilityRecorder | None = None,
        observability_scope_key: bytes | None = None,
        observability_provider_kind: ProviderKind = ProviderKind.UNKNOWN,
        safety_cost_recorder: SafetyCostRecorder | None = None,
        retry_breaker_recorder: RetryBreakerRecorder | None = None,
        retry_sleep: Callable[[float], Awaitable[None]] | None = None,
        retry_jitter: Callable[[], float] | None = None,
        storage_executor: StorageExecutor | None = None,
    ) -> None:
        if any(key != persona.npc_id for key, persona in personas.items()):
            raise ValueError("Persona mapping keys must match persona npc_id values")
        self._storage_executor = storage_executor
        self._closing = False
        self._close_task: asyncio.Task[None] | None = None
        self._active_requests: set[asyncio.Task[object]] = set()
        self._personas = dict(personas)
        self._provider = provider
        self._config = config
        self._long_term_memory = long_term_memory
        self._long_term_retriever = long_term_retriever
        self._relationship_service = relationship_service
        self._input_security_policy = input_security_policy or InputSecurityPolicy()
        self._safety_control = safety_control or NoOpSafetyControl()
        if not isinstance(self._safety_control, SafetyControlProtocol):
            raise TypeError("Dialogue safety control is invalid")
        if storage_executor is not None and isinstance(self._safety_control, SafetyControl):
            self._safety_control.bind_storage_executor(storage_executor)
        self._clock = clock or time.monotonic
        self._retry_policy = ProviderRetryPolicy() if self._safety_control.enabled else None
        self._retry_sleep = retry_sleep or asyncio.sleep
        self._retry_jitter = retry_jitter or (lambda: 0.0)
        self._session_store = session_store or ShortTermSessionStore(clock=self._clock)
        self._provider_slots = asyncio.Semaphore(config.max_concurrency)
        self._idempotency_lock = asyncio.Lock()
        self._ownership_locks: dict[UUID | LongTermMemoryScope, _OwnershipLock] = {}
        self._pending_admissions: set[UUID] = set()
        self._idempotency: OrderedDict[UUID, _IdempotencyEntry] = OrderedDict()
        self._long_term_revisions: dict[LongTermMemoryScope, int] = {}
        self._scope_locks: dict[ConversationScope, asyncio.Lock] = {}
        self._scope_waiters: dict[ConversationScope, int] = {}
        self._orphan_tasks: set[asyncio.Task[None]] = set()
        self._failed_attempts: OrderedDict[UUID, float] = OrderedDict()
        self._observability = DialogueObservability(
            recorder=observability_recorder,
            scope_key=observability_scope_key,
            provider_kind=observability_provider_kind,
            monotonic_clock=self._clock,
            executor=storage_executor,
        )
        if safety_cost_recorder is not None:
            self._safety_cost_recorder = safety_cost_recorder
        elif isinstance(observability_recorder, SafetyCostRecorder):
            self._safety_cost_recorder = observability_recorder
        else:
            self._safety_cost_recorder = NoOpSafetyCostRecorder()
        if retry_breaker_recorder is not None:
            self._retry_breaker_recorder = retry_breaker_recorder
        elif isinstance(observability_recorder, RetryBreakerRecorder):
            self._retry_breaker_recorder = observability_recorder
        else:
            self._retry_breaker_recorder = NoOpRetryBreakerRecorder()

    @property
    def storage_executor(self) -> StorageExecutor | None:
        return self._storage_executor

    @asynccontextmanager
    async def _ownership_guard(
        self, key: UUID | LongTermMemoryScope, *, admission: bool = False
    ) -> AsyncIterator[None]:
        # Event-loop-owned registry: count both holders and queued acquirers.
        # Order is request -> player+npc; no reverse acquisition is permitted.
        # A request fence covers owner checks through durable acknowledgement,
        # while the scope fence serializes revision changes with business commit.
        guard = self._ownership_locks.setdefault(key, _OwnershipLock())
        guard.users += 1
        acquired = False
        try:
            await guard.lock.acquire()
            acquired = True
            yield
        finally:
            if acquired:
                if admission and isinstance(key, UUID):
                    self._pending_admissions.discard(key)
                guard.lock.release()
            guard.users -= 1
            if guard.users == 0:
                del self._ownership_locks[key]

    async def _control_call[**P, T](
        self,
        operation: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        durable_operation = partial(operation, *args, **kwargs)
        return await call_storage(
            self._storage_executor,
            "control",
            durable_operation,
            finish_on_cancel=True,
        )

    async def _business_call[**P, T](
        self,
        operation: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        return await call_storage(
            self._storage_executor,
            "business",
            partial(operation, *args, **kwargs),
            finish_on_cancel=True,
        )

    async def _observe[**P](
        self,
        operation: Callable[P, None],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        await call_storage(
            self._storage_executor,
            "observability",
            partial(operation, *args, **kwargs),
            finish_on_cancel=True,
        )

    @staticmethod
    def _check_cancelled() -> None:
        task = asyncio.current_task()
        if task is not None and task.cancelling():
            raise asyncio.CancelledError

    async def aclose(self) -> None:
        self._closing = True
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._drain_storage())
        await finish_cleanup(self._close_task)

    async def _drain_storage(self) -> None:
        current = asyncio.current_task()
        requests = [task for task in self._active_requests if task is not current]
        if requests:
            await asyncio.gather(*requests, return_exceptions=True)
        executions = [entry.task for entry in self._idempotency.values() if entry.task is not None]
        if executions:
            await asyncio.gather(*executions, return_exceptions=True)
        if self._orphan_tasks:
            await asyncio.gather(*tuple(self._orphan_tasks), return_exceptions=True)
        if self._storage_executor is not None:
            await self._storage_executor.aclose()

    async def execute(
        self,
        request: DialogueRequestV1,
        *,
        trace_id: UUID,
    ) -> DialogueResponseV1:
        if self._closing:
            raise self._scope_unavailable("The dialogue service is temporarily unavailable.")
        task = asyncio.current_task()
        if task is not None:
            self._active_requests.add(task)
        try:
            return await self._execute_attempt(request, trace_id=trace_id)
        finally:
            if task is not None:
                self._active_requests.discard(task)

    async def _execute_attempt(
        self,
        request: DialogueRequestV1,
        *,
        trace_id: UUID,
    ) -> DialogueResponseV1:
        observation = await self._observability.start_validated_async(
            trace_id=trace_id,
            request_id=request.request_id,
            player_id=request.player_id,
            npc_id=request.npc_id,
            conversation_id=request.conversation_id,
            input_chars=len(request.message),
        )
        try:
            persona = self._personas.get(request.npc_id)
            if persona is None:
                if observation is not None:
                    await observation.astage(
                        TraceStage.PERSONA_RESOLUTION,
                        StageOutcome.FAILED,
                        error_code=TraceErrorCode.NPC_NOT_FOUND,
                    )
                # A running storage call drains before reporting its result.
                # Reconcile cancellation before choosing the rejection terminal.
                self._check_cancelled()
                raise DialogueUseCaseError(
                    kind=DialogueFailureKind.NPC_NOT_FOUND,
                    code=ApiErrorCode.NPC_NOT_FOUND,
                    public_message="NPC is not available.",
                    retryable=False,
                )
            if observation is not None:
                observation.persona_version = persona.version
                await observation.astage(TraceStage.PERSONA_RESOLUTION)

            self._check_cancelled()
            safety_decision = self._input_security_policy.evaluate(request.message)
            if safety_decision.outcome is SafetyOutcome.REJECTED:
                raise DialogueUseCaseError(
                    kind=DialogueFailureKind.UNSAFE_CONTENT,
                    code=ApiErrorCode.UNSAFE_CONTENT,
                    public_message="The message could not be processed safely.",
                    retryable=False,
                )
            result, from_cache = await self._execute_idempotent(
                request,
                persona,
                trace_id=trace_id,
                observation=observation,
            )
            response = DialogueResponseV1(
                request_id=request.request_id,
                trace_id=trace_id,
                npc_id=request.npc_id,
                conversation_id=request.conversation_id,
                reply=result.reply,
                status=result.status,
                provider=result.provider,
            )
            if observation is not None:
                await observation.astage(TraceStage.RESPONSE_MAPPING)
            # A committed execution stays committed. Reconcile attempt cancellation
            # after the stage worker drains, before choosing a success terminal.
            self._check_cancelled()
        except asyncio.CancelledError:
            if observation is not None:
                await observation.afinish(
                    terminal_outcome=(
                        TerminalOutcome.ORPHANED
                        if observation.orphaned
                        else TerminalOutcome.CANCELLED
                    ),
                    reason_code=(
                        TraceReasonCode.ORPHANED
                        if observation.orphaned
                        else TraceReasonCode.CANCELLED
                    ),
                    from_cache=observation.attempt_kind is AttemptKind.CACHE_REPLAY,
                )
            raise
        except DialogueUseCaseError as error:
            if observation is not None:
                terminal, error_code = self._observability_failure(error)
                await observation.afinish(
                    terminal_outcome=terminal,
                    reason_code=TraceReasonCode.NOT_REACHED,
                    error_code=error_code,
                    retryable=error.retryable,
                )
            self._log_failure(request, trace_id, error, observation=observation)
            raise

        if observation is not None:
            observation.output_chars = len(result.reply)
            if observation.attempt_kind not in {
                AttemptKind.CACHE_REPLAY,
                AttemptKind.CONCURRENT_WAITER,
            }:
                observation.usage_prompt_tokens = result.usage.prompt_tokens
                observation.usage_completion_tokens = result.usage.completion_tokens
                observation.provider_latency_ms = result.latency_ms
                observation.provider_wait_ms = result.provider_wait_ms
            if from_cache:
                terminal_outcome = TerminalOutcome.REPLAYED
                reason_code = TraceReasonCode.CACHE_REPLAY
            elif observation.attempt_kind is AttemptKind.CONCURRENT_WAITER:
                terminal_outcome = (
                    TerminalOutcome.DEGRADED
                    if result.status is DialogueStatus.DEGRADED
                    else TerminalOutcome.COMPLETED
                )
                reason_code = TraceReasonCode.SHARED_EXECUTION
            elif result.status is DialogueStatus.DEGRADED:
                terminal_outcome = TerminalOutcome.DEGRADED
                reason_code = (
                    TraceReasonCode.DEGRADED_CONTENT_FILTER
                    if result.provider == "local-fallback"
                    else TraceReasonCode.DEGRADED_NO_HISTORY
                )
            else:
                terminal_outcome = TerminalOutcome.COMPLETED
                reason_code = (
                    TraceReasonCode.LOCAL_MEMORY_COMMAND
                    if result.provider == "local-memory"
                    else TraceReasonCode.COMPLETED
                )
            await observation.afinish(
                terminal_outcome=terminal_outcome,
                reason_code=reason_code,
                from_cache=from_cache,
            )
        self._log_success(request, trace_id, result, from_cache=from_cache, observation=observation)
        return response

    async def _execute_idempotent(
        self,
        request: DialogueRequestV1,
        persona: PersonaDefinition,
        *,
        trace_id: UUID,
        observation: DialogueTrace | None,
    ) -> tuple[_DialogueResult, bool]:
        fingerprint = self._fingerprint(request)
        now = self._clock()
        long_term_scope = LongTermMemoryScope(request.player_id, request.npc_id)
        if observation is not None and request.request_id in self._failed_attempts:
            observation.attempt_kind = AttemptKind.RETRY

        async with self._ownership_guard(request.request_id, admission=True):
            async with self._idempotency_lock:
                self._purge_expired(now)
            entry = self._idempotency.get(request.request_id)
            from_cache = False
            if entry is not None:
                if entry.fingerprint != fingerprint:
                    if observation is not None:
                        observation.idempotency_outcome = IdempotencyOutcome.CONFLICT
                        await observation.astage(
                            TraceStage.IDEMPOTENCY_RESOLUTION,
                            StageOutcome.FAILED,
                            error_code=TraceErrorCode.CONFLICT,
                        )
                    raise DialogueUseCaseError(
                        kind=DialogueFailureKind.CONFLICT,
                        code=ApiErrorCode.CONFLICT,
                        public_message="The request conflicts with an existing request.",
                        retryable=False,
                    )
                self._idempotency.move_to_end(request.request_id)
                if entry.result is not None:
                    if (
                        entry.result.provider != "local-memory"
                        and entry.long_term_revision
                        != self._long_term_revisions.get(long_term_scope, 0)
                    ):
                        if observation is not None:
                            observation.idempotency_outcome = IdempotencyOutcome.CONFLICT
                            await observation.astage(
                                TraceStage.IDEMPOTENCY_RESOLUTION,
                                StageOutcome.FAILED,
                                error_code=TraceErrorCode.CONFLICT,
                            )
                        raise DialogueUseCaseError(
                            kind=DialogueFailureKind.CONFLICT,
                            code=ApiErrorCode.CONFLICT,
                            public_message="The request conflicts with an existing request.",
                            retryable=False,
                        )
                    if observation is not None:
                        observation.attempt_kind = AttemptKind.CACHE_REPLAY
                        observation.execution_id = None
                        observation.idempotency_outcome = IdempotencyOutcome.CACHE_REPLAY
                        observation.provider_kind = self._provider_kind_for_result(entry.result)
                        await observation.astage(
                            TraceStage.IDEMPOTENCY_RESOLUTION,
                            reason_code=TraceReasonCode.CACHE_REPLAY,
                        )
                    from_cache = True
                    return entry.result, True
                if entry.task is None:
                    raise RuntimeError("Invalid in-memory idempotency entry")
                task = entry.task
                entry.waiters += 1
                if observation is not None:
                    observation.attempt_kind = AttemptKind.CONCURRENT_WAITER
                    observation.execution_id = entry.execution_id
                    observation.idempotency_outcome = IdempotencyOutcome.INFLIGHT_SHARED
                    await observation.astage(
                        TraceStage.IDEMPOTENCY_RESOLUTION,
                        reason_code=TraceReasonCode.SHARED_EXECUTION,
                    )
            else:
                durable_replay = False
                if self._long_term_memory is not None:
                    try:
                        durable_fingerprint = await self._business_call(
                            self._long_term_memory.operation_fingerprint, request.request_id
                        )
                    except LongTermMemoryStorageError:
                        raise self._scope_unavailable(
                            "The dialogue service is temporarily unavailable."
                        ) from None
                    if durable_fingerprint is not None and durable_fingerprint != fingerprint:
                        if observation is not None:
                            observation.idempotency_outcome = IdempotencyOutcome.CONFLICT
                            await observation.astage(
                                TraceStage.IDEMPOTENCY_RESOLUTION,
                                StageOutcome.FAILED,
                                error_code=TraceErrorCode.CONFLICT,
                            )
                        raise DialogueUseCaseError(
                            kind=DialogueFailureKind.CONFLICT,
                            code=ApiErrorCode.CONFLICT,
                            public_message="The request conflicts with an existing request.",
                            retryable=False,
                        )
                    durable_replay = durable_fingerprint is not None
                self._make_capacity()
                # Reserve capacity before an admission await; unrelated requests
                # cannot overbook the map while this request has no task yet.
                self._pending_admissions.add(request.request_id)
                execution_id = uuid4()
                if observation is not None:
                    observation.execution_id = execution_id
                    observation.idempotency_outcome = IdempotencyOutcome.NEW
                    await observation.astage(TraceStage.IDEMPOTENCY_RESOLUTION)
                task = asyncio.create_task(
                    self._generate(
                        request,
                        persona,
                        trace_id=trace_id,
                        request_fingerprint=fingerprint,
                        durable_replay=durable_replay,
                        execution_id=execution_id,
                        observation=observation,
                    )
                )
                entry = _IdempotencyEntry(
                    fingerprint=fingerprint,
                    task=task,
                    result=None,
                    expires_at=now + self._config.idempotency_ttl_seconds,
                    waiters=1,
                    long_term_revision=self._long_term_revisions.get(long_term_scope, 0),
                    execution_id=execution_id,
                )
                self._idempotency[request.request_id] = entry

        try:
            self._check_cancelled()
            result = await asyncio.shield(task)
        except asyncio.CancelledError:
            orphaned = await self._detach_cancelled_waiter(request.request_id, task)
            if observation is not None:
                observation.orphaned = orphaned
            raise
        except Exception:
            await self._remove_failed_entry(request.request_id, task)
            raise

        async with self._ownership_guard(request.request_id):
            current = self._idempotency.get(request.request_id)
            if current is not None and current.task is task:
                current.waiters -= 1
                current.task = None
                current.result = result
                # The execution records its revision at business commit. A later
                # memory command must not relabel an older cached result.
                current.expires_at = self._clock() + self._config.idempotency_ttl_seconds
                self._idempotency.move_to_end(request.request_id)
            elif current is not None and current.result is not None:
                current.waiters = max(0, current.waiters - 1)

        return result, from_cache

    async def _detach_cancelled_waiter(
        self,
        request_id: UUID,
        task: asyncio.Task[_DialogueResult],
    ) -> bool:
        async with self._ownership_guard(request_id):
            current = self._idempotency.get(request_id)
            if current is None or current.task is not task:
                return False
            current.waiters -= 1
            if current.waiters == 0:
                cleanup = asyncio.create_task(self._cancel_orphan(request_id, task))
                self._orphan_tasks.add(cleanup)
                cleanup.add_done_callback(self._orphan_tasks.discard)
                return True
            return False

    async def _cancel_orphan(
        self,
        request_id: UUID,
        task: asyncio.Task[_DialogueResult],
    ) -> None:
        # Allow an immediate replacement waiter to adopt the shielded request.
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        async with self._ownership_guard(request_id):
            current = self._idempotency.get(request_id)
            if current is None or current.task is not task or current.waiters:
                return
            if not task.done():
                task.cancel()

    async def _remove_failed_entry(
        self,
        request_id: UUID,
        task: asyncio.Task[_DialogueResult],
    ) -> None:
        async with self._ownership_guard(request_id):
            current = self._idempotency.get(request_id)
            if current is not None and current.task is task:
                del self._idempotency[request_id]
                self._failed_attempts[request_id] = (
                    self._clock() + self._config.idempotency_ttl_seconds
                )
                self._failed_attempts.move_to_end(request_id)
                while len(self._failed_attempts) > self._config.idempotency_max_entries:
                    self._failed_attempts.popitem(last=False)

    def _purge_expired(self, now: float) -> None:
        for request_id, expires_at in tuple(self._failed_attempts.items()):
            if expires_at <= now:
                del self._failed_attempts[request_id]
        for request_id, entry in list(self._idempotency.items()):
            if entry.task is None or not entry.task.done():
                continue
            try:
                result = entry.task.result()
            except (asyncio.CancelledError, Exception):
                del self._idempotency[request_id]
                continue
            entry.task = None
            entry.result = result
            entry.expires_at = now + self._config.idempotency_ttl_seconds

        expired = [
            request_id
            for request_id, entry in self._idempotency.items()
            if entry.result is not None and entry.expires_at <= now
        ]
        for request_id in expired:
            del self._idempotency[request_id]

    def _make_capacity(self) -> None:
        while (
            len(self._idempotency) + len(self._pending_admissions)
            >= self._config.idempotency_max_entries
        ):
            completed_id = next(
                (
                    request_id
                    for request_id, entry in self._idempotency.items()
                    if entry.result is not None
                ),
                None,
            )
            if completed_id is None:
                raise DialogueUseCaseError(
                    kind=DialogueFailureKind.PROVIDER_UNAVAILABLE,
                    code=ApiErrorCode.PROVIDER_UNAVAILABLE,
                    public_message="The dialogue service is temporarily at capacity.",
                    retryable=True,
                )
            del self._idempotency[completed_id]

    async def _generate(
        self,
        request: DialogueRequestV1,
        persona: PersonaDefinition,
        *,
        trace_id: UUID,
        request_fingerprint: str,
        durable_replay: bool,
        execution_id: UUID,
        observation: DialogueTrace | None,
    ) -> _DialogueResult:
        if self._long_term_memory is not None:
            async with (
                self._ownership_guard(request.request_id),
                self._ownership_guard(LongTermMemoryScope(request.player_id, request.npc_id)),
            ):
                entry = self._idempotency.get(request.request_id)
                if entry is None or entry.task is not asyncio.current_task() or not entry.waiters:
                    raise asyncio.CancelledError
                try:
                    superseded_value = await self._business_call(
                        self._long_term_memory.superseded_fact_value, request
                    )
                    local_response = await self._business_call(
                        self._long_term_memory.execute, request, trace_id=trace_id
                    )
                except LongTermMemoryStorageError:
                    raise self._scope_unavailable(
                        "The dialogue service is temporarily unavailable."
                    ) from None
                except ValueError:
                    raise DialogueUseCaseError(
                        kind=DialogueFailureKind.VALIDATION_ERROR,
                        code=ApiErrorCode.VALIDATION_ERROR,
                        public_message="The memory command does not match its approved format.",
                        retryable=False,
                    ) from None
                if local_response is not None:
                    if observation is not None:
                        observation.long_term_outcome = LongTermOutcome.COMMAND_COMPLETED
                        observation.provider_kind = ProviderKind.LOCAL_MEMORY
                        await observation.astage(TraceStage.LONG_TERM_RETRIEVAL)
                        await observation.astage(TraceStage.STATE_COMMIT)
                    if superseded_value is not None and not durable_replay:
                        long_term_scope = LongTermMemoryScope(request.player_id, request.npc_id)
                        self._long_term_revisions[long_term_scope] = (
                            self._long_term_revisions.get(long_term_scope, 0) + 1
                        )
                        self._session_store.discard_fact_value(
                            request.player_id,
                            request.npc_id,
                            superseded_value,
                        )
                    return _DialogueResult(
                        reply=local_response.reply,
                        status=local_response.status,
                        provider=local_response.provider,
                        provider_model=self._config.model,
                        persona_version=persona.version,
                        usage=ProviderUsage(),
                        latency_ms=0,
                    )
        elif observation is not None:
            observation.long_term_outcome = LongTermOutcome.NOT_CONFIGURED

        try:
            select_history_messages(persona.system_prompt, request.message, ())
        except ContextBudgetError as error:
            if observation is not None:
                await observation.astage(
                    TraceStage.CONTEXT_BUDGET_SELECTION,
                    StageOutcome.FAILED,
                    error_code=TraceErrorCode.VALIDATION_ERROR,
                )
            raise self._context_budget_error(error) from None

        scope = ConversationScope(request.player_id, request.npc_id, request.conversation_id)
        lock = self._scope_locks.setdefault(scope, asyncio.Lock())
        self._scope_waiters[scope] = self._scope_waiters.get(scope, 0) + 1
        acquired = False
        reserved = False
        try:
            scope_lock_started = observation.wall_clock() if observation is not None else None
            if lock.locked():
                try:
                    await asyncio.wait_for(lock.acquire(), timeout=2.0)
                except TimeoutError:
                    raise self._scope_unavailable(
                        "The dialogue session is temporarily busy."
                    ) from None
            else:
                await lock.acquire()
            acquired = True
            if observation is not None:
                await observation.astage(
                    TraceStage.SCOPE_LOCK,
                    started_at_utc=scope_lock_started,
                )

            try:
                history = self._session_store.begin(scope)
            except SessionCapacityError:
                if observation is not None:
                    observation.short_term_outcome = ShortTermOutcome.FAILED
                    await observation.astage(
                        TraceStage.SHORT_TERM_SELECTION,
                        StageOutcome.FAILED,
                        error_code=TraceErrorCode.PROVIDER_UNAVAILABLE,
                    )
                raise self._scope_unavailable(
                    "The dialogue service is temporarily at capacity."
                ) from None
            reserved = True
            if observation is not None:
                observation.selected_short_term_turns = len(history)
                observation.short_term_outcome = (
                    ShortTermOutcome.SELECTED if history else ShortTermOutcome.EMPTY
                )
                await observation.astage(
                    TraceStage.SHORT_TERM_SELECTION,
                    item_count=len(history),
                )

            long_term_facts: tuple[ProviderLongTermFact, ...] = ()
            long_term_scope = LongTermMemoryScope(request.player_id, request.npc_id)
            long_term_revision = self._long_term_revisions.get(long_term_scope, 0)
            if self._long_term_retriever is not None:
                try:
                    long_term_facts = await self._business_call(
                        self._long_term_retriever.retrieve, long_term_scope, request.message
                    )
                except LongTermMemoryStorageError:
                    if observation is not None:
                        observation.long_term_outcome = LongTermOutcome.FAILED
                        await observation.astage(
                            TraceStage.LONG_TERM_RETRIEVAL,
                            StageOutcome.FAILED,
                            error_code=TraceErrorCode.PROVIDER_UNAVAILABLE,
                        )
                    raise self._scope_unavailable(
                        "The dialogue service is temporarily unavailable."
                    ) from None
                if long_term_facts:
                    history = tuple(
                        turn
                        for turn in history
                        if not self._long_term_retriever.is_recall_request(turn.user_message)
                    )
                if observation is not None:
                    observation.long_term_outcome = (
                        LongTermOutcome.RETRIEVED if long_term_facts else LongTermOutcome.EMPTY
                    )
                    await observation.astage(
                        TraceStage.LONG_TERM_RETRIEVAL,
                        item_count=len(long_term_facts),
                    )
            elif observation is not None:
                await observation.astage(
                    TraceStage.LONG_TERM_RETRIEVAL,
                    StageOutcome.SKIPPED,
                    reason_code=TraceReasonCode.NOT_REACHED,
                )
            selected_context = select_context_messages(
                persona.system_prompt, request.message, history, long_term_facts
            )
            if observation is not None:
                observation.selected_short_term_turns = len(selected_context.history_messages) // 2
                observation.selected_long_term_facts = len(selected_context.long_term_facts)
                observation.context_budget_units = estimate_context_units(
                    persona.system_prompt,
                    request.message,
                    selected_context.history_messages,
                    long_term_facts=selected_context.long_term_facts,
                )
                await observation.astage(
                    TraceStage.CONTEXT_BUDGET_SELECTION,
                    item_count=(
                        len(selected_context.history_messages)
                        + len(selected_context.long_term_facts)
                    ),
                )
            needs_memory = self._requires_conversation_history(request.message) or (
                self._long_term_retriever is not None
                and self._long_term_retriever.is_recall_request(request.message)
            )
            try:
                suppressed_memory = (
                    self._long_term_retriever is not None
                    and not selected_context.long_term_facts
                    and await self._business_call(
                        self._long_term_retriever.is_suppressed_recall,
                        long_term_scope,
                        request.message,
                    )
                )
            except LongTermMemoryStorageError:
                raise self._scope_unavailable(
                    "The dialogue service is temporarily unavailable."
                ) from None
            if suppressed_memory or (
                not selected_context.history_messages
                and not selected_context.long_term_facts
                and needs_memory
            ):
                result = self._empty_history_fallback(request.message, persona)
                if observation is not None:
                    observation.provider_kind = ProviderKind.LOCAL_FALLBACK
                    await observation.astage(
                        TraceStage.PROVIDER_QUEUE,
                        StageOutcome.SKIPPED,
                        reason_code=TraceReasonCode.DEGRADED_NO_HISTORY,
                    )
                    await observation.astage(
                        TraceStage.PROVIDER_COMPLETION,
                        StageOutcome.SKIPPED,
                        reason_code=TraceReasonCode.DEGRADED_NO_HISTORY,
                    )
            else:
                result = await self._complete_provider(
                    request,
                    persona,
                    selected_context.history_messages,
                    selected_context.long_term_facts,
                    execution_id=execution_id,
                    observation=observation,
                )

            if result.status is DialogueStatus.COMPLETED:
                async with (
                    self._ownership_guard(request.request_id),
                    self._ownership_guard(long_term_scope),
                ):
                    if self._long_term_revisions.get(long_term_scope, 0) != long_term_revision:
                        self._session_store.abort(scope)
                        if observation is not None:
                            observation.short_term_outcome = ShortTermOutcome.ABORTED
                        reserved = False
                        raise self._scope_unavailable("The dialogue session changed; please retry.")
                    entry = self._idempotency.get(request.request_id)
                    if (
                        entry is None
                        or entry.waiters == 0
                        or entry.task is not asyncio.current_task()
                    ):
                        self._session_store.abort(scope)
                        if observation is not None:
                            observation.short_term_outcome = ShortTermOutcome.ABORTED
                        reserved = False
                        raise asyncio.CancelledError
                    if self._relationship_service is not None:
                        try:
                            relationship_event = await self._business_call(
                                self._relationship_service.record_completed_dialogue,
                                player_id=request.player_id,
                                npc_id=request.npc_id,
                                request_id=request.request_id,
                                request_fingerprint=request_fingerprint,
                                trace_id=trace_id,
                                conversation_id=request.conversation_id,
                                raw_suggestion=result.relationship_suggestion,
                            )
                            if observation is not None:
                                observation.relationship_outcome = (
                                    RelationshipOutcome.APPLIED
                                    if relationship_event.applied_delta != 0
                                    else RelationshipOutcome.INERT
                                )
                                await observation.astage(TraceStage.RELATIONSHIP_EVALUATION)
                        except RelationshipConflictError:
                            if observation is not None:
                                observation.relationship_outcome = RelationshipOutcome.FAILED
                                await observation.astage(
                                    TraceStage.RELATIONSHIP_EVALUATION,
                                    StageOutcome.FAILED,
                                    error_code=TraceErrorCode.CONFLICT,
                                )
                            self._session_store.abort(scope)
                            if observation is not None:
                                observation.short_term_outcome = ShortTermOutcome.ABORTED
                            reserved = False
                            raise DialogueUseCaseError(
                                kind=DialogueFailureKind.CONFLICT,
                                code=ApiErrorCode.CONFLICT,
                                public_message="The request conflicts with an existing request.",
                                retryable=False,
                            ) from None
                        except RelationshipStorageError:
                            if observation is not None:
                                observation.relationship_outcome = RelationshipOutcome.FAILED
                                await observation.astage(
                                    TraceStage.RELATIONSHIP_EVALUATION,
                                    StageOutcome.FAILED,
                                    error_code=TraceErrorCode.PROVIDER_UNAVAILABLE,
                                )
                            self._session_store.abort(scope)
                            if observation is not None:
                                observation.short_term_outcome = ShortTermOutcome.ABORTED
                            reserved = False
                            raise self._scope_unavailable(
                                "The dialogue service is temporarily unavailable."
                            ) from None
                    elif observation is not None:
                        observation.relationship_outcome = RelationshipOutcome.NOT_CONFIGURED
                        await observation.astage(
                            TraceStage.RELATIONSHIP_EVALUATION,
                            StageOutcome.SKIPPED,
                            reason_code=TraceReasonCode.NOT_REACHED,
                        )
                    self._session_store.commit(
                        scope, ConversationTurn(request.message, result.reply)
                    )
                    entry.long_term_revision = long_term_revision
                    reserved = False
                    if observation is not None:
                        observation.short_term_outcome = ShortTermOutcome.COMMITTED
                        await observation.astage(TraceStage.STATE_COMMIT)
            else:
                self._session_store.abort(scope)
                reserved = False
                if observation is not None:
                    observation.short_term_outcome = ShortTermOutcome.ABORTED
                    observation.relationship_outcome = (
                        RelationshipOutcome.NOT_CONFIGURED
                        if self._relationship_service is None
                        else RelationshipOutcome.NOT_REACHED
                    )
                    await observation.astage(
                        TraceStage.RELATIONSHIP_EVALUATION,
                        StageOutcome.SKIPPED,
                        reason_code=TraceReasonCode.NOT_REACHED,
                    )
                    await observation.astage(
                        TraceStage.STATE_COMMIT,
                        StageOutcome.SKIPPED,
                        reason_code=TraceReasonCode.NOT_REACHED,
                    )
            return result
        finally:
            if reserved:
                self._session_store.abort(scope)
                if observation is not None:
                    observation.short_term_outcome = ShortTermOutcome.ABORTED
            if acquired:
                lock.release()
            self._scope_waiters[scope] -= 1
            if self._scope_waiters[scope] == 0:
                del self._scope_waiters[scope]
                del self._scope_locks[scope]

    async def _complete_provider(
        self,
        request: DialogueRequestV1,
        persona: PersonaDefinition,
        history_messages: tuple[ProviderHistoryMessage, ...],
        long_term_facts: tuple[ProviderLongTermFact, ...],
        *,
        execution_id: UUID,
        observation: DialogueTrace | None,
    ) -> _DialogueResult:
        permit: ProviderPermit | None = None
        release_reason = "failed"
        policy = self._retry_policy
        max_attempts = 1 if policy is None else policy.max_attempts
        execution_deadline = (
            self._clock() + self._config.timeout_seconds
            if policy is None
            else self._clock() + policy.execution_deadline_seconds
        )
        try:
            for attempt_number in range(1, max_attempts + 1):
                remaining = execution_deadline - self._clock()
                if remaining <= 0:
                    raise DialogueUseCaseError(
                        kind=DialogueFailureKind.PROVIDER_TIMEOUT,
                        code=ApiErrorCode.PROVIDER_TIMEOUT,
                        public_message="The dialogue provider timed out.",
                        retryable=True,
                    )
                breaker_decision = BreakerDecision(
                    BreakerState.CLOSED,
                    BreakerOutcome.NOT_REACHED,
                )
                budget_state: _BudgetAttemptState | None = None
                provider_admission = None
                try:
                    if self._safety_control.enabled:
                        try:
                            provider_admission = await self._safety_control.admit_provider_dispatch(
                                request=request,
                                execution_id=execution_id,
                                attempt_number=attempt_number,
                            )
                            breaker_decision = provider_admission.breaker_decision
                            reservation = provider_admission.reservation
                            budget_state = _BudgetAttemptState(
                                reservation,
                            )
                            if permit is None:
                                permit = provider_admission.permit
                            elif permit.execution_id != provider_admission.permit.execution_id:
                                raise ControlUnavailableError
                            await self._record_retry_breaker_event(
                                observation,
                                execution_id=execution_id,
                                attempt_number=attempt_number,
                                event_kind=RetryBreakerEventKind.BREAKER_CHECK,
                                retry_outcome=RetryOutcome.NOT_REACHED,
                                breaker_decision=breaker_decision,
                                deadline_remaining_seconds=remaining,
                            )
                            await self._record_budget_event(
                                observation,
                                budget_state,
                                event_kind=BudgetEventKind.RESERVATION,
                                outcome=BudgetOutcome.RESERVED,
                            )
                        except CircuitOpenError as error:
                            rejected = BreakerDecision(
                                BreakerState.OPEN,
                                BreakerOutcome.REJECTED,
                                error.retry_after_seconds,
                            )
                            await self._record_retry_breaker_event(
                                observation,
                                execution_id=execution_id,
                                attempt_number=attempt_number,
                                event_kind=RetryBreakerEventKind.BREAKER_CHECK,
                                retry_outcome=RetryOutcome.NOT_ELIGIBLE,
                                breaker_decision=rejected,
                                deadline_remaining_seconds=remaining,
                            )
                            if observation is not None:
                                await observation.astage(
                                    TraceStage.PROVIDER_QUEUE,
                                    StageOutcome.FAILED,
                                    error_code=TraceErrorCode.CIRCUIT_OPEN,
                                )
                            raise self._circuit_open(error.retry_after_seconds) from None
                        except RateLimitExceededError as error:
                            if observation is not None:
                                await observation.astage(
                                    TraceStage.PROVIDER_QUEUE,
                                    StageOutcome.FAILED,
                                    error_code=TraceErrorCode.RATE_LIMITED,
                                )
                            raise self._rate_limited(error.retry_after_seconds) from None
                        except ControlUnavailableError:
                            raise self._control_unavailable() from None
                    if not await self._execution_has_active_waiter(request.request_id):
                        raise asyncio.CancelledError
                    result = await self._complete_provider_dispatch(
                        request,
                        persona,
                        history_messages,
                        long_term_facts,
                        observation=observation,
                        budget_state=budget_state,
                        attempt_timeout_seconds=(
                            min(self._config.timeout_seconds, remaining)
                            if policy is None
                            else min(policy.attempt_timeout_seconds, remaining)
                        ),
                    )
                except BudgetRejectedError as error:
                    await self._record_budget_rejection(
                        observation,
                        execution_id=execution_id,
                        attempt_number=attempt_number,
                        error=error,
                    )
                    await self._release_breaker_probe(execution_id)
                    if observation is not None:
                        await observation.astage(
                            TraceStage.PROVIDER_QUEUE,
                            StageOutcome.FAILED,
                            error_code=TraceErrorCode.BUDGET_EXHAUSTED,
                        )
                    raise DialogueUseCaseError(
                        kind=DialogueFailureKind.BUDGET_EXHAUSTED,
                        code=ApiErrorCode.BUDGET_EXHAUSTED,
                        public_message="The dialogue budget is exhausted.",
                        retryable=False,
                    ) from None
                except ControlCapacityError:
                    await self._release_breaker_probe(execution_id)
                    if observation is not None:
                        await observation.astage(
                            TraceStage.PROVIDER_QUEUE,
                            StageOutcome.FAILED,
                            error_code=TraceErrorCode.PROVIDER_UNAVAILABLE,
                        )
                    raise self._scope_unavailable(
                        "The dialogue provider is temporarily busy."
                    ) from None
                except ControlUnavailableError:
                    raise self._control_unavailable() from None
                except asyncio.CancelledError:
                    await self._release_breaker_probe(execution_id, ignore_failure=True)
                    await self._record_retry_breaker_event(
                        observation,
                        execution_id=execution_id,
                        attempt_number=attempt_number,
                        event_kind=RetryBreakerEventKind.PROBE_RELEASE,
                        retry_outcome=RetryOutcome.CANCELLED,
                        breaker_decision=breaker_decision,
                        deadline_remaining_seconds=max(0.0, execution_deadline - self._clock()),
                    )
                    raise
                except DialogueUseCaseError as error:
                    failure_reason = self._breaker_failure_reason(error)
                    retry_eligible = error.kind in {
                        DialogueFailureKind.PROVIDER_TIMEOUT,
                        DialogueFailureKind.PROVIDER_UNAVAILABLE,
                    }
                    can_retry = (
                        retry_eligible and attempt_number < max_attempts and policy is not None
                    )
                    if can_retry:
                        assert policy is not None
                        jitter = self._retry_jitter()
                        delay = policy.delay_seconds(jitter)
                        remaining_after_attempt = execution_deadline - self._clock()
                        if remaining_after_attempt > delay:
                            await self._record_retry_breaker_event(
                                observation,
                                execution_id=execution_id,
                                attempt_number=attempt_number,
                                event_kind=RetryBreakerEventKind.RETRY_SCHEDULED,
                                retry_outcome=RetryOutcome.SCHEDULED,
                                breaker_decision=breaker_decision,
                                failure_reason=failure_reason,
                                backoff_seconds=delay,
                                jitter_seconds=float(jitter),
                                deadline_remaining_seconds=remaining_after_attempt,
                            )
                            try:
                                await self._retry_sleep(delay)
                            except asyncio.CancelledError:
                                await self._release_breaker_probe(
                                    execution_id,
                                    ignore_failure=True,
                                )
                                await self._record_retry_breaker_event(
                                    observation,
                                    execution_id=execution_id,
                                    attempt_number=attempt_number,
                                    event_kind=RetryBreakerEventKind.PROBE_RELEASE,
                                    retry_outcome=RetryOutcome.CANCELLED,
                                    breaker_decision=breaker_decision,
                                    failure_reason=failure_reason,
                                    deadline_remaining_seconds=max(
                                        0.0,
                                        execution_deadline - self._clock(),
                                    ),
                                )
                                raise
                            continue
                    if failure_reason is not None:
                        if not await self._execution_has_active_waiter(request.request_id):
                            if budget_state is not None and budget_state.dispatched:
                                await self._settle_budget_conservatively(
                                    budget_state,
                                    reason="cancelled_after_dispatch",
                                    observation=observation,
                                )
                            await self._release_breaker_probe(
                                execution_id,
                                ignore_failure=True,
                            )
                            raise asyncio.CancelledError from None
                        try:
                            final_decision = await self._control_call(
                                self._safety_control.record_provider_failure,
                                execution_id=execution_id,
                                reason=failure_reason,
                            )
                        except ControlUnavailableError:
                            raise self._control_unavailable() from None
                        await self._record_retry_breaker_event(
                            observation,
                            execution_id=execution_id,
                            attempt_number=attempt_number,
                            event_kind=RetryBreakerEventKind.BREAKER_RESULT,
                            retry_outcome=(
                                RetryOutcome.EXHAUSTED
                                if retry_eligible
                                else RetryOutcome.NOT_ELIGIBLE
                            ),
                            breaker_decision=final_decision,
                            failure_reason=failure_reason,
                            deadline_remaining_seconds=max(0.0, execution_deadline - self._clock()),
                        )
                    else:
                        await self._release_breaker_probe(execution_id)
                    raise
                else:
                    if self._safety_control.enabled:
                        if not await self._execution_has_active_waiter(request.request_id):
                            if budget_state is not None and budget_state.dispatched:
                                await self._settle_budget_conservatively(
                                    budget_state,
                                    reason="cancelled_after_dispatch",
                                    observation=observation,
                                )
                            await self._release_breaker_probe(
                                execution_id,
                                ignore_failure=True,
                            )
                            raise asyncio.CancelledError
                        try:
                            if provider_admission is None or budget_state is None:
                                raise ControlUnavailableError
                            finalization = await self._safety_control.finalize_provider_success(
                                provider_admission,
                                usage=result.usage,
                            )
                            permit = None
                            budget_state.settled = True
                        except ControlUnavailableError:
                            raise self._control_unavailable() from None
                        await self._record_budget_event(
                            observation,
                            budget_state,
                            event_kind=BudgetEventKind.SETTLEMENT,
                            outcome=BudgetOutcome.SETTLED,
                            settlement=finalization.settlement,
                        )
                        final_decision = finalization.breaker_decision
                        await self._record_retry_breaker_event(
                            observation,
                            execution_id=execution_id,
                            attempt_number=attempt_number,
                            event_kind=RetryBreakerEventKind.BREAKER_RESULT,
                            retry_outcome=(
                                RetryOutcome.ATTEMPTED
                                if attempt_number > 1
                                else RetryOutcome.NOT_REACHED
                            ),
                            breaker_decision=final_decision,
                            deadline_remaining_seconds=max(0.0, execution_deadline - self._clock()),
                        )
                    release_reason = "completed"
                    return result
                finally:
                    if budget_state is not None and not budget_state.dispatched:
                        try:
                            await self._control_call(
                                self._safety_control.release_budget,
                                budget_state.reservation,
                                reason="cancelled_before_dispatch",
                            )
                            await self._record_budget_event(
                                observation,
                                budget_state,
                                event_kind=BudgetEventKind.RELEASE,
                                outcome=BudgetOutcome.NOT_REACHED,
                            )
                        except ControlUnavailableError:
                            if release_reason != "cancelled":
                                raise self._control_unavailable() from None
            raise RuntimeError("Provider retry loop ended without a result")
        except asyncio.CancelledError:
            release_reason = "cancelled"
            raise
        finally:
            if permit is not None:
                try:
                    await self._safety_control.release_provider_permit(
                        permit,
                        reason=release_reason,
                    )
                except ControlUnavailableError:
                    if release_reason != "cancelled":
                        raise self._control_unavailable() from None

    async def _complete_provider_dispatch(
        self,
        request: DialogueRequestV1,
        persona: PersonaDefinition,
        history_messages: tuple[ProviderHistoryMessage, ...],
        long_term_facts: tuple[ProviderLongTermFact, ...],
        *,
        observation: DialogueTrace | None,
        budget_state: _BudgetAttemptState | None,
        attempt_timeout_seconds: float,
    ) -> _DialogueResult:
        provider_request = ProviderRequest(
            system_prompt=persona.system_prompt,
            user_message=request.message,
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            timeout_seconds=attempt_timeout_seconds,
            thinking_enabled=False,
            stream=False,
            history_messages=history_messages,
            long_term_facts=long_term_facts,
        )
        queue_started = self._clock()
        queue_started_utc = observation.wall_clock() if observation is not None else None
        acquired = False
        provider_wait_ms = 0
        started = queue_started
        provider_started_utc = queue_started_utc

        try:
            await self._provider_slots.acquire()
            acquired = True
            async with self._ownership_guard(request.request_id):
                entry = self._idempotency.get(request.request_id)
                if entry is None or entry.task is not asyncio.current_task() or not entry.waiters:
                    raise asyncio.CancelledError
                provider_wait_ms = max(0, round((self._clock() - queue_started) * 1_000))
                if observation is not None:
                    observation.provider_wait_ms = provider_wait_ms
                    # Observability v1 deliberately retains its binary execution-dispatch
                    # linkage. Exact attempt cardinality is append-only in F-009 0003.
                    observation.provider_dispatch_count = 1
                    await observation.astage(
                        TraceStage.PROVIDER_QUEUE,
                        started_at_utc=queue_started_utc,
                    )
                started = self._clock()
                provider_started_utc = observation.wall_clock() if observation is not None else None
                if budget_state is not None:
                    await self._record_budget_event(
                        observation,
                        budget_state,
                        event_kind=BudgetEventKind.DISPATCH,
                        outcome=BudgetOutcome.RESERVED,
                    )
                    budget_state.dispatched = True
            async with asyncio.timeout(attempt_timeout_seconds):
                completion = await self._provider.complete(provider_request)
        except asyncio.CancelledError:
            if budget_state is not None and budget_state.dispatched:
                await self._settle_budget_conservatively(
                    budget_state,
                    reason="cancelled_after_dispatch",
                    observation=observation,
                )
            raise
        except (TimeoutError, ProviderTimeoutError):
            if budget_state is not None and budget_state.dispatched:
                await self._settle_budget_conservatively(
                    budget_state,
                    reason="provider_timeout",
                    observation=observation,
                )
            await self._mark_provider_failure(
                observation,
                TraceErrorCode.PROVIDER_TIMEOUT,
                started_at_utc=provider_started_utc if acquired else queue_started_utc,
            )
            raise DialogueUseCaseError(
                kind=DialogueFailureKind.PROVIDER_TIMEOUT,
                code=ApiErrorCode.PROVIDER_TIMEOUT,
                public_message="The dialogue provider timed out.",
                retryable=True,
            ) from None
        except ProviderInvalidResponseError:
            if budget_state is not None and budget_state.dispatched:
                await self._settle_budget_conservatively(
                    budget_state,
                    reason="provider_invalid_response",
                    observation=observation,
                )
            await self._mark_provider_failure(
                observation,
                TraceErrorCode.PROVIDER_INVALID_RESPONSE,
                started_at_utc=provider_started_utc if acquired else queue_started_utc,
            )
            raise self._invalid_provider_response() from None
        except ProviderUnavailableError:
            if budget_state is not None and budget_state.dispatched:
                await self._settle_budget_conservatively(
                    budget_state,
                    reason="provider_unavailable",
                    observation=observation,
                )
            await self._mark_provider_failure(
                observation,
                TraceErrorCode.PROVIDER_UNAVAILABLE,
                started_at_utc=provider_started_utc if acquired else queue_started_utc,
            )
            raise DialogueUseCaseError(
                kind=DialogueFailureKind.PROVIDER_UNAVAILABLE,
                code=ApiErrorCode.PROVIDER_UNAVAILABLE,
                public_message="The dialogue provider is unavailable.",
                retryable=True,
            ) from None
        except ControlUnavailableError:
            raise self._control_unavailable() from None
        except Exception:
            if budget_state is not None and budget_state.dispatched:
                await self._settle_budget_conservatively(
                    budget_state,
                    reason="internal_error",
                    observation=observation,
                )
            await self._mark_provider_failure(
                observation,
                TraceErrorCode.INTERNAL_ERROR,
                started_at_utc=provider_started_utc if acquired else queue_started_utc,
            )
            raise DialogueUseCaseError(
                kind=DialogueFailureKind.INTERNAL_ERROR,
                code=ApiErrorCode.INTERNAL_ERROR,
                public_message="The dialogue request could not be completed.",
                retryable=False,
            ) from None

        finally:
            if acquired:
                self._provider_slots.release()

        latency_ms = max(0, round((self._clock() - started) * 1_000))
        if observation is not None:
            observation.provider_latency_ms = latency_ms
        try:
            result = self._validate_completion(
                completion,
                persona,
                expected_model=self._config.model,
                max_completion_tokens=self._config.max_tokens,
                latency_ms=latency_ms,
                provider_wait_ms=provider_wait_ms,
            )
        except DialogueUseCaseError:
            if budget_state is not None and budget_state.dispatched:
                await self._settle_budget_conservatively(
                    budget_state,
                    reason="provider_invalid_response",
                    observation=observation,
                )
            await self._mark_provider_failure(
                observation,
                TraceErrorCode.PROVIDER_INVALID_RESPONSE,
                started_at_utc=provider_started_utc,
            )
            raise
        if observation is not None:
            observation.provider_kind = self._provider_kind_for_result(result)
            try:
                await observation.astage(
                    TraceStage.PROVIDER_COMPLETION,
                    started_at_utc=provider_started_utc,
                    item_count=1,
                )
            except asyncio.CancelledError:
                if budget_state is not None and budget_state.dispatched:
                    await self._settle_budget_conservatively(
                        budget_state,
                        reason="cancelled_after_dispatch",
                        observation=observation,
                    )
                raise
        return result

    async def _settle_budget_conservatively(
        self,
        state: _BudgetAttemptState,
        *,
        reason: str,
        observation: DialogueTrace | None,
    ) -> None:
        if state.settled:
            return
        try:
            settlement = await self._control_call(
                self._safety_control.settle_budget_conservatively,
                state.reservation,
                reason=reason,
            )
            state.settled = True
            await self._record_budget_event(
                observation,
                state,
                event_kind=BudgetEventKind.SETTLEMENT,
                outcome=BudgetOutcome.SETTLED,
                settlement=settlement,
            )
        except ControlUnavailableError:
            raise self._control_unavailable() from None

    async def _record_budget_event(
        self,
        observation: DialogueTrace | None,
        state: _BudgetAttemptState,
        *,
        event_kind: BudgetEventKind,
        outcome: BudgetOutcome,
        settlement: BudgetSettlement | None = None,
    ) -> None:
        if observation is None:
            return
        try:
            await self._observe(
                self._safety_cost_recorder.record_safety_cost,
                SafetyCostMetadata(
                    trace_id=observation.trace_id,
                    execution_id=state.reservation.execution_id,
                    attempt_number=state.reservation.attempt_number,
                    event_kind=event_kind,
                    outcome=outcome,
                    policy_version=state.reservation.policy_version,
                    pricing_version=state.reservation.pricing_version,
                    provider_kind=state.reservation.provider_kind,
                    scope_tags=state.reservation.scope_tags,
                    reserved_micro_usd=state.reservation.reserved_micro_usd,
                    actual_cost_micro_usd=(
                        0 if settlement is None else settlement.actual_cost_micro_usd
                    ),
                    prompt_tokens=0 if settlement is None else settlement.prompt_tokens,
                    completion_tokens=(0 if settlement is None else settlement.completion_tokens),
                    conservative=False if settlement is None else settlement.conservative,
                    recorded_at_utc=observation.wall_clock(),
                ),
            )
        except Exception:
            return

    async def _record_budget_rejection(
        self,
        observation: DialogueTrace | None,
        *,
        execution_id: UUID,
        attempt_number: int,
        error: BudgetRejectedError,
    ) -> None:
        if observation is None or error.scope_tags is None or error.pricing_policy is None:
            return
        try:
            await self._observe(
                self._safety_cost_recorder.record_safety_cost,
                SafetyCostMetadata(
                    trace_id=observation.trace_id,
                    execution_id=execution_id,
                    attempt_number=attempt_number,
                    event_kind=BudgetEventKind.REJECTION,
                    outcome=BudgetOutcome.REJECTED,
                    policy_version=BUDGET_POLICY_VERSION,
                    pricing_version=error.pricing_policy.version,
                    provider_kind=error.pricing_policy.provider_kind,
                    scope_tags=error.scope_tags,
                    reserved_micro_usd=error.pricing_policy.max_reservation_micro_usd,
                    actual_cost_micro_usd=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    conservative=False,
                    recorded_at_utc=observation.wall_clock(),
                ),
            )
        except Exception:
            return

    async def _execution_has_active_waiter(self, request_id: UUID) -> bool:
        async with self._ownership_guard(request_id):
            entry = self._idempotency.get(request_id)
            return entry is not None and entry.task is asyncio.current_task() and entry.waiters > 0

    @staticmethod
    def _breaker_failure_reason(
        error: DialogueUseCaseError,
    ) -> BreakerFailureReason | None:
        return {
            DialogueFailureKind.PROVIDER_TIMEOUT: BreakerFailureReason.TIMEOUT,
            DialogueFailureKind.PROVIDER_UNAVAILABLE: BreakerFailureReason.UNAVAILABLE,
            DialogueFailureKind.PROVIDER_INVALID_RESPONSE: BreakerFailureReason.INVALID_RESPONSE,
        }.get(error.kind)

    async def _release_breaker_probe(
        self,
        execution_id: UUID,
        *,
        ignore_failure: bool = False,
    ) -> None:
        if not self._safety_control.enabled:
            return
        try:
            await self._control_call(
                self._safety_control.release_breaker_probe, execution_id=execution_id
            )
        except ControlUnavailableError:
            if not ignore_failure:
                raise self._control_unavailable() from None

    async def _record_retry_breaker_event(
        self,
        observation: DialogueTrace | None,
        *,
        execution_id: UUID,
        attempt_number: int,
        event_kind: RetryBreakerEventKind,
        retry_outcome: RetryOutcome,
        breaker_decision: BreakerDecision,
        deadline_remaining_seconds: float,
        failure_reason: BreakerFailureReason | None = None,
        backoff_seconds: float = 0.0,
        jitter_seconds: float = 0.0,
    ) -> None:
        if observation is None:
            return
        try:
            await self._observe(
                self._retry_breaker_recorder.record_retry_breaker,
                RetryBreakerMetadata(
                    trace_id=observation.trace_id,
                    execution_id=execution_id,
                    attempt_number=attempt_number,
                    event_kind=event_kind,
                    retry_outcome=retry_outcome,
                    breaker_state=breaker_decision.state,
                    breaker_outcome=breaker_decision.outcome,
                    failure_reason=failure_reason,
                    backoff_ms=min(400, max(0, round(backoff_seconds * 1_000))),
                    jitter_ms=min(200, max(0, round(jitter_seconds * 1_000))),
                    deadline_remaining_ms=min(
                        12_000,
                        max(0, round(deadline_remaining_seconds * 1_000)),
                    ),
                    recorded_at_utc=observation.wall_clock(),
                ),
            )
        except Exception:
            return

    @staticmethod
    def _requires_conversation_history(message: str) -> bool:
        normalized = message.casefold()
        return any(marker in normalized for marker in _HISTORY_REFERENCE_MARKERS) and any(
            marker in normalized for marker in _HISTORY_QUERY_MARKERS
        )

    def _empty_history_fallback(
        self,
        message: str,
        persona: PersonaDefinition,
    ) -> _DialogueResult:
        has_chinese = any("\u4e00" <= character <= "\u9fff" for character in message)
        return _DialogueResult(
            reply=NO_HISTORY_REPLY_ZH if has_chinese else NO_HISTORY_REPLY_EN,
            status=DialogueStatus.DEGRADED,
            provider="local-fallback",
            provider_model=self._config.model,
            persona_version=persona.version,
            usage=ProviderUsage(),
            latency_ms=0,
        )

    @staticmethod
    def _context_budget_error(error: ContextBudgetError) -> DialogueUseCaseError:
        if error.failure is ContextBudgetFailure.CURRENT_MESSAGE:
            return DialogueUseCaseError(
                kind=DialogueFailureKind.VALIDATION_ERROR,
                code=ApiErrorCode.VALIDATION_ERROR,
                public_message="The dialogue message exceeds the available context budget.",
                retryable=False,
            )
        return DialogueService._scope_unavailable(
            "The dialogue service is temporarily unavailable."
        )

    @staticmethod
    def _scope_unavailable(message: str) -> DialogueUseCaseError:
        return DialogueUseCaseError(
            kind=DialogueFailureKind.PROVIDER_UNAVAILABLE,
            code=ApiErrorCode.PROVIDER_UNAVAILABLE,
            public_message=message,
            retryable=True,
        )

    @staticmethod
    def _validate_completion(
        completion: ProviderCompletion,
        persona: PersonaDefinition,
        *,
        expected_model: str,
        max_completion_tokens: int,
        latency_ms: int,
        provider_wait_ms: int,
    ) -> _DialogueResult:
        try:
            completion.usage.__post_init__()
        except (AttributeError, TypeError, ValueError):
            raise DialogueService._invalid_provider_response() from None
        invalid = (
            completion.choice_count != 1
            or completion.tool_calls_present
            or completion.reasoning_content_present
            or not isinstance(completion.finish_reason, str)
            or completion.provider not in {"fake", "deepseek"}
            or completion.model
            not in (
                {expected_model}
                if completion.provider == "deepseek"
                else {expected_model, "fake-model"}
            )
            or completion.usage.completion_tokens > max_completion_tokens
        )
        if invalid:
            raise DialogueService._invalid_provider_response()

        if completion.finish_reason == "content_filter":
            return _DialogueResult(
                reply=(
                    f"{persona.display_name} pauses, keeping the conversation within "
                    "safe boundaries."
                ),
                status=DialogueStatus.DEGRADED,
                provider="local-fallback",
                provider_model=completion.model,
                persona_version=persona.version,
                usage=completion.usage,
                latency_ms=latency_ms,
                provider_wait_ms=provider_wait_ms,
            )

        if completion.finish_reason != "stop" or not isinstance(completion.content, str):
            raise DialogueService._invalid_provider_response()

        if len(completion.content) > 4_000 or completion.content != completion.content.strip():
            raise DialogueService._invalid_provider_response()
        reply = completion.content
        if not reply:
            raise DialogueService._invalid_provider_response()

        return _DialogueResult(
            reply=reply,
            status=DialogueStatus.COMPLETED,
            provider=completion.provider,
            provider_model=completion.model,
            persona_version=persona.version,
            usage=completion.usage,
            latency_ms=latency_ms,
            provider_wait_ms=provider_wait_ms,
            relationship_suggestion=completion.relationship_suggestion,
        )

    @property
    def relationship_service(self) -> RelationshipService | None:
        """Expose the optional read capability without expanding Dialogue v1."""

        return self._relationship_service

    @property
    def observability(self) -> DialogueObservability:
        """Expose the internal boundary recorder to the HTTP validation adapter."""

        return self._observability

    @property
    def safety_control(self) -> SafetyControlProtocol:
        """Expose only ingress admission to the HTTP boundary."""

        return self._safety_control

    @staticmethod
    async def _mark_provider_failure(
        observation: DialogueTrace | None,
        error_code: TraceErrorCode,
        *,
        started_at_utc: datetime | None,
    ) -> None:
        if observation is None:
            return
        await observation.astage(
            TraceStage.PROVIDER_COMPLETION,
            StageOutcome.FAILED,
            error_code=error_code,
            started_at_utc=started_at_utc,
        )

    @staticmethod
    def _provider_kind_for_result(result: _DialogueResult) -> ProviderKind:
        try:
            return ProviderKind(result.provider)
        except ValueError:
            return ProviderKind.UNKNOWN

    @staticmethod
    def _observability_failure(
        error: DialogueUseCaseError,
    ) -> tuple[TerminalOutcome, TraceErrorCode]:
        error_code = {
            DialogueFailureKind.NPC_NOT_FOUND: TraceErrorCode.NPC_NOT_FOUND,
            DialogueFailureKind.CONFLICT: TraceErrorCode.CONFLICT,
            DialogueFailureKind.VALIDATION_ERROR: TraceErrorCode.VALIDATION_ERROR,
            DialogueFailureKind.UNSAFE_CONTENT: TraceErrorCode.UNSAFE_CONTENT,
            DialogueFailureKind.RATE_LIMITED: TraceErrorCode.RATE_LIMITED,
            DialogueFailureKind.BUDGET_EXHAUSTED: TraceErrorCode.BUDGET_EXHAUSTED,
            DialogueFailureKind.CONTROL_UNAVAILABLE: TraceErrorCode.CONTROL_UNAVAILABLE,
            DialogueFailureKind.CIRCUIT_OPEN: TraceErrorCode.CIRCUIT_OPEN,
            DialogueFailureKind.PROVIDER_TIMEOUT: TraceErrorCode.PROVIDER_TIMEOUT,
            DialogueFailureKind.PROVIDER_UNAVAILABLE: TraceErrorCode.PROVIDER_UNAVAILABLE,
            DialogueFailureKind.PROVIDER_INVALID_RESPONSE: (
                TraceErrorCode.PROVIDER_INVALID_RESPONSE
            ),
            DialogueFailureKind.INTERNAL_ERROR: TraceErrorCode.INTERNAL_ERROR,
        }[error.kind]
        terminal = {
            DialogueFailureKind.NPC_NOT_FOUND: TerminalOutcome.REJECTED,
            DialogueFailureKind.VALIDATION_ERROR: TerminalOutcome.REJECTED,
            DialogueFailureKind.UNSAFE_CONTENT: TerminalOutcome.REJECTED,
            DialogueFailureKind.RATE_LIMITED: TerminalOutcome.REJECTED,
            DialogueFailureKind.CONFLICT: TerminalOutcome.CONFLICT,
        }.get(error.kind, TerminalOutcome.FAILED)
        return terminal, error_code

    @staticmethod
    def _rate_limited(retry_after_seconds: int) -> DialogueUseCaseError:
        return DialogueUseCaseError(
            kind=DialogueFailureKind.RATE_LIMITED,
            code=ApiErrorCode.RATE_LIMITED,
            public_message="The dialogue request rate limit was exceeded.",
            retryable=True,
            retry_after_seconds=retry_after_seconds,
        )

    @staticmethod
    def _control_unavailable() -> DialogueUseCaseError:
        return DialogueUseCaseError(
            kind=DialogueFailureKind.CONTROL_UNAVAILABLE,
            code=ApiErrorCode.CONTROL_UNAVAILABLE,
            public_message="The dialogue safety control is temporarily unavailable.",
            retryable=True,
        )

    @staticmethod
    def _circuit_open(retry_after_seconds: int) -> DialogueUseCaseError:
        return DialogueUseCaseError(
            kind=DialogueFailureKind.CIRCUIT_OPEN,
            code=ApiErrorCode.CIRCUIT_OPEN,
            public_message="The dialogue provider circuit is temporarily open.",
            retryable=True,
            retry_after_seconds=retry_after_seconds,
        )

    @staticmethod
    def _invalid_provider_response() -> DialogueUseCaseError:
        return DialogueUseCaseError(
            kind=DialogueFailureKind.PROVIDER_INVALID_RESPONSE,
            code=ApiErrorCode.PROVIDER_INVALID_RESPONSE,
            public_message="The dialogue provider returned an invalid response.",
            retryable=False,
        )

    @staticmethod
    def _fingerprint(request: DialogueRequestV1) -> str:
        payload = json.dumps(
            request.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _log_success(
        request: DialogueRequestV1,
        trace_id: UUID,
        result: _DialogueResult,
        *,
        from_cache: bool,
        observation: DialogueTrace | None,
    ) -> None:
        scope_tags = None if observation is None else observation.scope_tags
        audit = {
            "event": "dialogue_completed",
            "trace_id": str(trace_id),
            "request_id": str(request.request_id),
            "player_scope_tag": (None if scope_tags is None else scope_tags.player_scope_tag),
            "npc_scope_tag": None if scope_tags is None else scope_tags.npc_scope_tag,
            "conversation_scope_tag": (
                None if scope_tags is None else scope_tags.conversation_scope_tag
            ),
            "persona_version": result.persona_version,
            "provider": result.provider,
            "outcome": result.status.value,
            "retryable": False,
            "from_cache": from_cache,
            "latency_ms": result.latency_ms,
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
            "input_chars": len(request.message),
            "output_chars": len(result.reply),
        }
        LOGGER.info("dialogue_completed", extra={"dialogue_audit": audit})

    @staticmethod
    def _log_failure(
        request: DialogueRequestV1,
        trace_id: UUID,
        error: DialogueUseCaseError,
        *,
        observation: DialogueTrace | None,
    ) -> None:
        scope_tags = None if observation is None else observation.scope_tags
        audit = {
            "event": "dialogue_failed",
            "trace_id": str(trace_id),
            "request_id": str(request.request_id),
            "player_scope_tag": (None if scope_tags is None else scope_tags.player_scope_tag),
            "npc_scope_tag": None if scope_tags is None else scope_tags.npc_scope_tag,
            "conversation_scope_tag": (
                None if scope_tags is None else scope_tags.conversation_scope_tag
            ),
            "persona_version": (None if observation is None else observation.persona_version),
            "outcome": error.kind.value,
            "error_code": error.code.value,
            "retryable": error.retryable,
            "input_chars": len(request.message),
        }
        LOGGER.info("dialogue_failed", extra={"dialogue_audit": audit})
