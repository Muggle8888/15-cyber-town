"""Opt-in local application composition without SDK leakage into core layers."""

from __future__ import annotations

from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import SafetyControl, SafetyControlProtocol
from cyber_town.application.dialogue import DialogueExecutionConfig, DialogueService
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.observability import (
    ObservabilityRecorder,
    ProviderKind,
    StorageExecutor,
)
from cyber_town.application.provider import ProviderProtocol
from cyber_town.application.relationship import RelationshipService
from cyber_town.config import (
    PROJECT_ROOT,
    SAFETY_CONTROL_DATABASE_PATH,
    LlmProvider,
    Settings,
)
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import SqliteRelationshipRepository


def build_dialogue_service(
    settings: Settings,
    *,
    provider: ProviderProtocol | None = None,
    long_term_repository: SqliteLongTermMemoryRepository | None = None,
    relationship_repository: SqliteRelationshipRepository | None = None,
    observability_recorder: ObservabilityRecorder | None = None,
    observability_scope_key: bytes | None = None,
    observability_provider_kind: ProviderKind | None = None,
    safety_control: SafetyControlProtocol | None = None,
    control_repository: SqliteSafetyControlRepository | None = None,
    control_scope_key: bytes | None = None,
    pricing_policy: PricingPolicy | None = None,
    storage_executor: StorageExecutor | None = None,
) -> DialogueService | None:
    """Build the dialogue use case only when the approved provider is enabled."""

    if settings.llm_provider is LlmProvider.DISABLED:
        return None

    provider_was_injected = provider is not None
    if safety_control is None:
        if control_scope_key is None:
            raise ValueError("The enabled dialogue provider requires a safety control key.")
        if pricing_policy is None:
            raise ValueError("The enabled dialogue provider requires an approved pricing policy.")
        if pricing_policy.model != settings.llm_model:
            raise ValueError("The approved pricing policy does not match the configured model.")
        if not provider_was_injected and pricing_policy.provider_kind is not ProviderKind.DEEPSEEK:
            raise ValueError("The approved pricing policy does not match the enabled provider.")
    if provider is None:
        if settings.llm_api_key is None:
            raise ValueError("The enabled dialogue provider requires a configured API key.")
        from cyber_town.infrastructure.llm.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(
            credential=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    if long_term_repository is None:
        data_root = PROJECT_ROOT / "data"
        data_root.mkdir(parents=True, exist_ok=True)
        long_term_repository = SqliteLongTermMemoryRepository(
            database_path=PROJECT_ROOT / settings.long_term_memory_database_path,
            allowed_root=data_root,
        )
        long_term_repository.initialize()

    if relationship_repository is None:
        relationship_repository = SqliteRelationshipRepository(
            database_path=long_term_repository.database_path,
            allowed_root=long_term_repository.database_path.parent,
        )
        relationship_repository.initialize()

    if safety_control is None:
        assert control_scope_key is not None
        assert pricing_policy is not None
        if control_repository is None:
            data_root = PROJECT_ROOT / "data"
            data_root.mkdir(parents=True, exist_ok=True)
            control_repository = SqliteSafetyControlRepository(
                database_path=PROJECT_ROOT / SAFETY_CONTROL_DATABASE_PATH,
                allowed_root=data_root,
            )
            control_repository.initialize()
        safety_control = SafetyControl(
            repository=control_repository,
            scope_key=control_scope_key,
            pricing_policy=pricing_policy,
        )

    return DialogueService(
        storage_executor=storage_executor or AsyncSqliteExecutor(),
        personas=load_bundled_personas(),
        provider=provider,
        config=DialogueExecutionConfig(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
            max_concurrency=settings.llm_max_concurrency,
            idempotency_ttl_seconds=settings.llm_idempotency_ttl_seconds,
            idempotency_max_entries=settings.llm_idempotency_max_entries,
        ),
        long_term_memory=LongTermMemoryService(repository=long_term_repository),
        long_term_retriever=LongTermMemoryRetriever(repository=long_term_repository),
        relationship_service=RelationshipService(repository=relationship_repository),
        safety_control=safety_control,
        observability_recorder=observability_recorder,
        observability_scope_key=observability_scope_key,
        observability_provider_kind=(
            observability_provider_kind
            if observability_provider_kind is not None
            else ProviderKind(settings.llm_provider.value)
        ),
    )
