from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import SecretStr

from cyber_town.api.composition import build_dialogue_service
from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import (
    BUCKET_SPECS,
    CONTROL_POLICY_VERSION,
    BucketRequest,
    ControlScope,
    ControlUnavailableError,
    RateLimitExceededError,
    SafetyControl,
)
from cyber_town.application.observability import ProviderKind
from cyber_town.config import LlmProvider, Settings
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.infrastructure.control.sqlite_control import (
    SqliteSafetyControlRepository,
)
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import (
    SqliteRelationshipRepository,
)

KEY = b"synthetic-f009-control-key-v1"
REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")
EXECUTION_ID = UUID("22222222-2222-4222-8222-222222222222")
CONVERSATION_ID = UUID("33333333-3333-4333-8333-333333333333")


class FakeClock:
    def __init__(self, now_ns: int = 1_800_000_000_000_000_000) -> None:
        self.now_ns = now_ns

    def __call__(self) -> int:
        return self.now_ns

    def advance(self, seconds: float) -> None:
        self.now_ns += round(seconds * 1_000_000_000)


def make_request(
    *,
    request_id: UUID = REQUEST_ID,
    player_id: str = "synthetic_player",
    npc_id: str = "neon_guide",
    conversation_id: UUID = CONVERSATION_ID,
) -> DialogueRequestV1:
    return DialogueRequestV1(
        request_id=request_id,
        player_id=player_id,
        npc_id=npc_id,
        conversation_id=conversation_id,
        message="Synthetic local control test.",
    )


def make_control(
    tmp_path: Path, clock: FakeClock
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
            clock_ns=clock,
            pricing_policy=PricingPolicy.zero_cost(
                provider_kind=ProviderKind.FAKE,
                model="deepseek-v4-flash",
            ),
        ),
        repository,
    )


def test_policy_and_scope_contract_is_fixed() -> None:
    assert CONTROL_POLICY_VERSION == "f-009-safety-control-v1"
    assert tuple(ControlScope) == (
        ControlScope.INGRESS_GLOBAL,
        ControlScope.DIRECT_PEER,
        ControlScope.PLAYER,
        ControlScope.PLAYER_NPC,
        ControlScope.CONVERSATION,
    )


def test_ingress_global_burst_and_continuous_refill(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)

    for suffix in range(1, 31):
        control.admit_ingress(peer_host=f"192.0.2.{suffix}")

    with pytest.raises(RateLimitExceededError) as captured:
        control.admit_ingress(peer_host="192.0.2.31")
    assert captured.value.retry_after_seconds == 1
    assert repr(captured.value) == "RateLimitExceededError()"

    clock.advance(0.5)
    control.admit_ingress(peer_host="192.0.2.31")


def test_direct_peer_bucket_ignores_other_peer_usage(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)

    for _ in range(15):
        control.admit_ingress(peer_host="198.51.100.10")

    with pytest.raises(RateLimitExceededError):
        control.admit_ingress(peer_host="198.51.100.10")
    control.admit_ingress(peer_host="198.51.100.11")


@pytest.mark.parametrize(
    ("scope", "expected_retry_after"),
    (
        (ControlScope.INGRESS_GLOBAL, 1),
        (ControlScope.DIRECT_PEER, 1),
        (ControlScope.PLAYER, 3),
        (ControlScope.PLAYER_NPC, 6),
        (ControlScope.CONVERSATION, 10),
    ),
)
def test_each_fixed_bucket_exhausts_and_refills_one_token(
    tmp_path: Path,
    scope: ControlScope,
    expected_retry_after: int,
) -> None:
    clock = FakeClock()
    _, repository = make_control(tmp_path, clock)
    spec = BUCKET_SPECS[scope]
    bucket = BucketRequest(spec=spec, scope_tag="a" * 64)

    for _ in range(spec.burst):
        assert (
            repository.consume_ingress(buckets=(bucket,), now_ns=clock()).retry_after_seconds
            is None
        )
    rejected = repository.consume_ingress(buckets=(bucket,), now_ns=clock())
    assert rejected.retry_after_seconds == expected_retry_after

    clock.advance(60 / spec.refill_per_minute)
    allowed = repository.consume_ingress(buckets=(bucket,), now_ns=clock())
    assert allowed.retry_after_seconds is None


def test_domain_buckets_are_atomic_on_rejection(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    request = make_request()

    control.admit_execution(request=request, execution_id=EXECUTION_ID)
    control.admit_execution(
        request=make_request(request_id=UUID("44444444-4444-4444-8444-444444444444")),
        execution_id=UUID("55555555-5555-4555-8555-555555555555"),
    )
    before = repository.bucket_snapshot()
    with pytest.raises(RateLimitExceededError):
        control.admit_execution(
            request=make_request(request_id=UUID("66666666-6666-4666-8666-666666666666")),
            execution_id=UUID("77777777-7777-4777-8777-777777777777"),
        )
    after = repository.bucket_snapshot()

    assert after == before
    assert repository.admission_count() == 2


def test_concurrent_domain_admission_allows_only_conversation_burst(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    barrier = threading.Barrier(3)

    def admit(index: int) -> bool:
        barrier.wait()
        try:
            control.admit_execution(
                request=make_request(request_id=UUID(int=index + 1)),
                execution_id=UUID(int=index + 101),
            )
        except RateLimitExceededError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = tuple(executor.map(admit, range(3)))

    assert results.count(True) == 2
    assert results.count(False) == 1
    assert repository.admission_count() == 2


def test_same_execution_admission_is_idempotent(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    request = make_request()

    control.admit_execution(request=request, execution_id=EXECUTION_ID)
    first = repository.bucket_snapshot()
    control.admit_execution(request=request, execution_id=EXECUTION_ID)

    assert repository.bucket_snapshot() == first
    assert repository.admission_count() == 1


def test_clock_reversal_never_refills_tokens(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    control.admit_execution(request=make_request(), execution_id=EXECUTION_ID)
    before = repository.bucket_snapshot()

    clock.advance(-60)
    control.admit_execution(request=make_request(), execution_id=EXECUTION_ID)

    assert repository.bucket_snapshot() == before


def test_invalid_peer_and_repository_failure_are_secret_safe(tmp_path: Path) -> None:
    clock = FakeClock()
    control, _ = make_control(tmp_path, clock)

    with pytest.raises(ControlUnavailableError) as captured:
        control.admit_ingress(peer_host="not-a-socket-peer")

    assert str(captured.value) == "Safety control is unavailable."
    assert "not-a-socket-peer" not in repr(captured.value)


def test_control_sqlite_contains_no_raw_scope_or_peer(tmp_path: Path) -> None:
    clock = FakeClock()
    control, repository = make_control(tmp_path, clock)
    request = make_request()
    peer = "203.0.113.77"

    control.admit_ingress(peer_host=peer)
    control.admit_execution(request=request, execution_id=EXECUTION_ID)
    database_bytes = repository.database_path.read_bytes()

    for forbidden in (
        peer,
        request.player_id,
        request.npc_id,
        str(request.conversation_id),
        request.message,
    ):
        assert forbidden.encode() not in database_bytes


def test_enabled_composition_requires_explicit_control_key(tmp_path: Path) -> None:
    business = tmp_path / "business.sqlite3"
    memory = SqliteLongTermMemoryRepository(database_path=business, allowed_root=tmp_path)
    memory.initialize()
    relationship = SqliteRelationshipRepository(database_path=business, allowed_root=tmp_path)
    relationship.initialize()
    settings = Settings.model_validate(
        {
            "llm_provider": LlmProvider.DEEPSEEK,
            "llm_api_key": SecretStr("synthetic-provider-value"),
        }
    )

    with pytest.raises(ValueError, match="safety control key"):
        build_dialogue_service(
            settings,
            provider=FakeProvider([]),
            long_term_repository=memory,
            relationship_repository=relationship,
        )

    assert not (tmp_path / "cyber-town-control.sqlite3").exists()


def test_composition_uses_injected_isolated_control_repository(tmp_path: Path) -> None:
    business = tmp_path / "business.sqlite3"
    memory = SqliteLongTermMemoryRepository(database_path=business, allowed_root=tmp_path)
    memory.initialize()
    relationship = SqliteRelationshipRepository(database_path=business, allowed_root=tmp_path)
    relationship.initialize()
    control_repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    control_repository.initialize()
    settings = Settings.model_validate(
        {
            "llm_provider": LlmProvider.DEEPSEEK,
            "llm_api_key": SecretStr("synthetic-provider-value"),
        }
    )

    with pytest.raises(ValueError, match="approved pricing policy"):
        build_dialogue_service(
            settings,
            provider=FakeProvider([]),
            long_term_repository=memory,
            relationship_repository=relationship,
            control_repository=control_repository,
            control_scope_key=KEY,
        )

    service = build_dialogue_service(
        settings,
        provider=FakeProvider([]),
        long_term_repository=memory,
        relationship_repository=relationship,
        control_repository=control_repository,
        control_scope_key=KEY,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model=settings.llm_model,
        ),
    )

    assert service is not None
    assert service.safety_control.enabled is True
    assert control_repository.database_path.is_file()
