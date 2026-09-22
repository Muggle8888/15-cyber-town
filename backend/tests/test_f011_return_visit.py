from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest

from cyber_town.application.dialogue import DialogueExecutionConfig, DialogueService
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.provider import (
    RELATIONSHIP_STYLE_CONTEXT_VERSION,
    ProviderCompletion,
    ProviderRelationshipStage,
    ProviderReplyStyle,
    ProviderRequest,
)
from cyber_town.application.relationship import RelationshipService
from cyber_town.contracts.v1 import DialogueRequestV1, DialogueResponseV1
from cyber_town.domain.persona import load_bundled_persona
from cyber_town.domain.relationship import RelationshipStage
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import (
    RelationshipStorageError,
    SqliteRelationshipRepository,
)


def _completion(text: str = "Synthetic ordinary reply.") -> ProviderCompletion:
    return ProviderCompletion(
        content=text,
        finish_reason="stop",
        choice_count=1,
        tool_calls_present=False,
        reasoning_content_present=False,
        provider="fake",
        model="deepseek-flash",
        relationship_suggestion={"category": "neutral", "confidence": 100},
    )


def _request(
    message: str,
    *,
    index: int,
    npc_id: str = "neon_guide",
    conversation_index: int = 100,
) -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=UUID(int=index),
        player_id="local_player",
        npc_id=npc_id,
        conversation_id=UUID(int=conversation_index),
        message=message,
    )


def _service(
    repository: SqliteLongTermMemoryRepository,
    provider: FakeProvider,
    *,
    relationship_service: object | None = None,
) -> DialogueService:
    personas = [
        load_bundled_persona("nia_v1.json"),
        load_bundled_persona("ivo_v1.json"),
        load_bundled_persona("rhea_v1.json"),
    ]
    return DialogueService(
        personas={persona.npc_id: persona for persona in personas},
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
        long_term_memory=LongTermMemoryService(repository=repository, clock=lambda: 1_700_000_000),
        long_term_retriever=LongTermMemoryRetriever(
            repository=repository,
            clock=lambda: 1_700_000_000,
        ),
        relationship_service=cast(Any, relationship_service),
    )


@pytest.fixture
def memory_repository(tmp_path: Path) -> SqliteLongTermMemoryRepository:
    repository = SqliteLongTermMemoryRepository(
        database_path=tmp_path / "f011.sqlite3",
        allowed_root=tmp_path,
    )
    repository.initialize()
    return repository


@pytest.mark.parametrize("stage", list(ProviderRelationshipStage))
@pytest.mark.parametrize("style", list(ProviderReplyStyle))
def test_controlled_context_covers_all_stages_and_styles_without_hidden_scores(
    stage: ProviderRelationshipStage,
    style: ProviderReplyStyle,
) -> None:
    request = ProviderRequest(
        system_prompt="PERSONA_AUTHORITY",
        user_message="hello",
        model="deepseek-flash",
        temperature=0.6,
        max_tokens=256,
        timeout_seconds=12.0,
        relationship_stage=stage,
        reply_style=style,
    )

    content = request.system_content()

    assert content.startswith("PERSONA_AUTHORITY")
    assert RELATIONSHIP_STYLE_CONTEXT_VERSION in content
    assert f"RELATIONSHIP_STAGE: {stage.value}" in content
    assert f"REPLY_STYLE: {style.value}" in content
    assert "score" not in content.lower()
    assert "reason_code" not in content


@pytest.mark.parametrize(
    ("field", "value"),
    [("relationship_stage", "friend"), ("reply_style", "concise")],
)
def test_provider_context_rejects_untyped_values(field: str, value: str) -> None:
    values: dict[str, object] = {
        "system_prompt": "persona",
        "user_message": "hello",
        "model": "deepseek-flash",
        "temperature": 0.6,
        "max_tokens": 256,
        "timeout_seconds": 12.0,
        field: value,
    }
    with pytest.raises(TypeError):
        ProviderRequest(**values)  # type: ignore[arg-type]


def test_reply_style_applies_to_ordinary_dialogue_and_stays_scoped_by_npc(
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    provider = FakeProvider([_completion(), _completion()])
    service = _service(memory_repository, provider)

    async def scenario() -> None:
        remembered = await service.execute(
            _request("请记住\uff1areply_style=concise", index=1),
            trace_id=UUID(int=101),
        )
        assert remembered.provider == "local-memory"
        assert provider.call_count == 0

        await service.execute(_request("今晚怎么样\uff1f", index=2), trace_id=UUID(int=102))
        await service.execute(
            _request("档案亭怎么样\uff1f", index=3, npc_id="signal_archivist"),
            trace_id=UUID(int=103),
        )

    asyncio.run(scenario())

    assert provider.requests[0].reply_style is ProviderReplyStyle.CONCISE
    assert provider.requests[1].reply_style is None
    assert provider.requests[0].long_term_facts == ()


def test_topic_fact_is_injected_only_for_matching_topic_query(
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    provider = FakeProvider([_completion(), _completion()])
    service = _service(memory_repository, provider)

    async def scenario() -> None:
        await service.execute(
            _request("请记住\uff1afavorite_cyber_town_topic=霓虹夜市", index=1),
            trace_id=UUID(int=201),
        )
        await service.execute(_request("晚上好", index=2), trace_id=UUID(int=202))
        await service.execute(
            _request("你还记得我喜欢的话题吗\uff1f", index=3),
            trace_id=UUID(int=203),
        )

    asyncio.run(scenario())

    assert provider.requests[0].long_term_facts == ()
    assert len(provider.requests[1].long_term_facts) == 1
    assert provider.requests[1].long_term_facts[0].fact_key == "favorite_cyber_town_topic"
    assert provider.requests[1].long_term_facts[0].fact_value == "霓虹夜市"


class _ReadFailingRelationshipService:
    def read(self, **_values: object) -> object:
        raise RelationshipStorageError("private read failure")

    def record_completed_dialogue(self, **_values: object) -> object:
        return type("RelationshipEvent", (), {"applied_delta": 0})()


class _InvalidReadRelationshipService(_ReadFailingRelationshipService):
    def read(self, **_values: object) -> object:
        return SimpleNamespace(state=SimpleNamespace(stage=SimpleNamespace(value="unknown")))


def test_relationship_read_failure_omits_context_and_keeps_dialogue_available(
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    provider = FakeProvider([_completion()])
    service = _service(
        memory_repository,
        provider,
        relationship_service=_ReadFailingRelationshipService(),
    )

    response = asyncio.run(service.execute(_request("晚上好", index=1), trace_id=UUID(int=301)))

    assert response.status.value == "completed"
    assert provider.call_count == 1
    assert provider.requests[0].relationship_stage is None


def test_invalid_relationship_stage_is_omitted_instead_of_reaching_provider(
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    provider = FakeProvider([_completion()])
    service = _service(
        memory_repository,
        provider,
        relationship_service=_InvalidReadRelationshipService(),
    )

    asyncio.run(service.execute(_request("晚上好", index=1), trace_id=UUID(int=302)))

    assert provider.requests[0].relationship_stage is None


def test_real_relationship_snapshot_reaches_provider_as_enum_only(
    tmp_path: Path,
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    relationships = SqliteRelationshipRepository(
        database_path=tmp_path / "relationships.sqlite3",
        allowed_root=tmp_path,
    )
    relationships.initialize()
    provider = FakeProvider([_completion()])
    service = _service(
        memory_repository,
        provider,
        relationship_service=RelationshipService(repository=relationships),
    )

    asyncio.run(service.execute(_request("晚上好", index=1), trace_id=UUID(int=401)))

    assert provider.requests[0].relationship_stage is ProviderRelationshipStage.ACQUAINTANCE
    assert provider.requests[0].reply_style is None
    assert "20" not in provider.requests[0].system_content()
    assert "rule_" not in provider.requests[0].system_content()


class _AdvancingRelationshipService:
    def __init__(self) -> None:
        self.completed = 0

    def read(self, **_values: object) -> object:
        stage = RelationshipStage.ACQUAINTANCE if self.completed == 0 else RelationshipStage.FRIEND
        return SimpleNamespace(state=SimpleNamespace(stage=stage))

    def record_completed_dialogue(self, **_values: object) -> object:
        self.completed += 1
        return SimpleNamespace(applied_delta=1)


def test_relationship_change_affects_the_next_provider_request_only(
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    provider = FakeProvider([_completion(), _completion()])
    relationships = _AdvancingRelationshipService()
    service = _service(memory_repository, provider, relationship_service=relationships)

    async def scenario() -> None:
        await service.execute(_request("第一次交谈", index=1), trace_id=UUID(int=501))
        await service.execute(_request("下一次交谈", index=2), trace_id=UUID(int=502))

    asyncio.run(scenario())

    assert provider.requests[0].relationship_stage is ProviderRelationshipStage.ACQUAINTANCE
    assert provider.requests[1].relationship_stage is ProviderRelationshipStage.FRIEND


def test_topic_and_style_survive_service_restart(
    tmp_path: Path,
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    original = _service(memory_repository, FakeProvider([]))

    async def remember() -> None:
        await original.execute(
            _request("请记住\uff1afavorite_cyber_town_topic=霓虹夜市", index=1),
            trace_id=UUID(int=601),
        )
        await original.execute(
            _request("请记住\uff1areply_style=concise", index=2),
            trace_id=UUID(int=602),
        )

    asyncio.run(remember())

    restarted_repository = SqliteLongTermMemoryRepository(
        database_path=memory_repository.database_path,
        allowed_root=tmp_path,
    )
    restarted_repository.initialize()
    provider = FakeProvider([_completion()])
    restarted = _service(restarted_repository, provider)
    asyncio.run(
        restarted.execute(
            _request("你还记得我喜欢的话题吗\uff1f", index=3, conversation_index=200),
            trace_id=UUID(int=603),
        )
    )

    assert provider.requests[0].reply_style is ProviderReplyStyle.CONCISE
    assert provider.requests[0].long_term_facts[0].fact_value == "霓虹夜市"


def test_forgotten_topic_uses_deterministic_fallback_without_provider(
    memory_repository: SqliteLongTermMemoryRepository,
) -> None:
    provider = FakeProvider([])
    service = _service(memory_repository, provider)

    async def scenario() -> DialogueResponseV1:
        await service.execute(
            _request("请记住\uff1afavorite_cyber_town_topic=霓虹夜市", index=1),
            trace_id=UUID(int=701),
        )
        await service.execute(
            _request("请忘记\uff1afavorite_cyber_town_topic", index=2),
            trace_id=UUID(int=702),
        )
        return await service.execute(
            _request("你还记得我喜欢的话题吗\uff1f", index=3),
            trace_id=UUID(int=703),
        )

    response = asyncio.run(scenario())

    assert response.provider == "local-fallback"
    assert response.status.value == "degraded"
    assert provider.call_count == 0
