from __future__ import annotations

import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID

import pytest
from scripts import f009_step5_architecture_probe as probe


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (1, "first_100"),
        (100, "first_100"),
        (101, "middle_800"),
        (900, "middle_800"),
        (901, "last_100"),
        (1000, "last_100"),
    ],
)
def test_memory_segments(index: int, expected: str) -> None:
    assert probe.memory_segment(index) == expected


def test_metadata_summary_has_no_payload() -> None:
    assert probe.sample_summary([1.0, 2.0, 3.0]) == {
        "count": 3,
        "p50_ms": 2.0,
        "p95_ms": 3.0,
        "p99_ms": 3.0,
        "max_ms": 3.0,
    }


def test_sync_interface_fidelity_gate_reports_missing_await_boundary() -> None:
    finding = probe.interface_fidelity()
    assert finding["faithful_drop_in_async_adapter"] is False
    assert finding["failure_code"] == "synchronous_persistence_contract_requires_await_boundary"
    assert finding["sync_stage"] is True
    assert finding["sync_reserve_budget"] is True
    # The current V21 call graph no longer holds the global idempotency lock
    # around the relationship write; the V5 diagnostic must reflect current code.
    assert finding["relationship_write_inside_idempotency_lock"] is False


def test_async_lock_observation_preserves_exclusion() -> None:
    async def scenario() -> None:
        profile = probe.SteadyProfile()
        lock = probe.MeasuredAsyncLock(asyncio.Lock(), profile, "scope")
        order: list[int] = []

        async def worker(value: int) -> None:
            async with lock:
                order.append(value)
                await asyncio.sleep(0)
                order.append(value)

        await asyncio.gather(worker(1), worker(2))
        assert order == [1, 1, 2, 2]
        assert not lock.locked()
        rows = profile.snapshot()
        assert {row["operation"] for row in rows} == {"scope_wait", "scope_hold"}
        assert "payload" not in json.dumps(rows)

    asyncio.run(scenario())


def test_heartbeat_measures_synthetic_event_loop_blocking() -> None:
    import time

    async def scenario() -> None:
        async with probe.loop_heartbeat() as samples:
            time.sleep(0.025)
            await asyncio.sleep(0.01)
        assert max(samples) >= 15

    asyncio.run(scenario())


def test_v23_three_fence_success_replay_and_unique_side_effects(tmp_path: Path) -> None:
    store = probe.SyntheticExecutionIntentStore(tmp_path / "control.sqlite3")
    store.initialize()

    assert store.aggregate()["execution_count"] == 0
    owner = store.prepare_provider_attempt(
        request_id=UUID(int=1),
        execution_id=UUID(int=101),
        fingerprint="a" * 64,
    )
    assert owner.outcome is probe.SyntheticIntentOutcome.OWNER
    assert owner.durable_fence_count == 2
    assert store.claim_provider_dispatch(owner) is True
    assert store.claim_provider_dispatch(owner) is False

    assert store.finalize_success(owner, fail_before_commit=False) is True
    assert store.finalize_success(owner, fail_before_commit=False) is False
    replay = store.prepare_provider_attempt(
        request_id=UUID(int=1),
        execution_id=UUID(int=999),
        fingerprint="a" * 64,
    )
    assert replay.outcome is probe.SyntheticIntentOutcome.REPLAY
    assert replay.execution_id == UUID(int=101)

    totals = store.aggregate()
    assert totals == {
        "execution_count": 1,
        "execution_quota_count": 1,
        "dispatch_intent_count": 1,
        "settlement_count": 1,
        "release_count": 0,
        "business_claim_count": 1,
        "conservative_count": 0,
    }
    assert owner.durable_fence_count + 1 == 3  # ingress + intent + final
    store.close()


def test_v23_clean_cancellation_releases_before_provider(tmp_path: Path) -> None:
    store = probe.SyntheticExecutionIntentStore(tmp_path / "control.sqlite3")
    store.initialize()
    owner = store.prepare_provider_attempt(
        request_id=UUID(int=2),
        execution_id=UUID(int=102),
        fingerprint="b" * 64,
    )

    assert store.cancel_clean_before_provider(owner) is True
    assert store.cancel_clean_before_provider(owner) is False
    assert store.claim_provider_dispatch(owner) is False
    assert store.recover_unknown_intents() == 0
    totals = store.aggregate()
    assert totals["release_count"] == 1
    assert totals["settlement_count"] == 0
    assert totals["business_claim_count"] == 0
    store.close()


def test_v23_crash_recovery_is_conservative_idempotent_and_drops_late_result(
    tmp_path: Path,
) -> None:
    path = tmp_path / "control.sqlite3"
    first = probe.SyntheticExecutionIntentStore(path)
    first.initialize()
    owner = first.prepare_provider_attempt(
        request_id=UUID(int=3),
        execution_id=UUID(int=103),
        fingerprint="c" * 64,
    )
    assert store_state(first, owner) == "dispatch_intent"
    first.close()

    restarted = probe.SyntheticExecutionIntentStore(path)
    restarted.initialize()
    assert restarted.recover_unknown_intents() == 1
    assert restarted.recover_unknown_intents() == 0
    assert restarted.finalize_success(owner, fail_before_commit=False) is False
    totals = restarted.aggregate()
    assert totals["settlement_count"] == 1
    assert totals["conservative_count"] == 1
    assert totals["business_claim_count"] == 0
    restarted.close()


def store_state(store: probe.SyntheticExecutionIntentStore, intent: probe.SyntheticIntent) -> str:
    return store.state_for(intent.execution_id)


def test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner(tmp_path: Path) -> None:
    path = tmp_path / "control.sqlite3"
    store = probe.SyntheticExecutionIntentStore(path)
    store.initialize()

    def prepare(index: int) -> probe.SyntheticIntent:
        local = probe.SyntheticExecutionIntentStore(path)
        try:
            return local.prepare_provider_attempt(
                request_id=UUID(int=4),
                execution_id=UUID(int=200 + index),
                fingerprint="d" * 64,
            )
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(prepare, range(16)))
    assert sum(item.outcome is probe.SyntheticIntentOutcome.OWNER for item in results) == 1
    assert sum(item.outcome is probe.SyntheticIntentOutcome.WAITER for item in results) == 15
    assert len({item.execution_id for item in results}) == 1

    conflict = store.prepare_provider_attempt(
        request_id=UUID(int=4),
        execution_id=UUID(int=999),
        fingerprint="e" * 64,
    )
    assert conflict.outcome is probe.SyntheticIntentOutcome.CONFLICT
    assert store.aggregate()["execution_quota_count"] == 1
    store.close()


def test_v23_prepare_and_finalize_roll_back_atomically(tmp_path: Path) -> None:
    store = probe.SyntheticExecutionIntentStore(tmp_path / "control.sqlite3")
    store.initialize()
    with pytest.raises(sqlite3.OperationalError):
        store.prepare_provider_attempt(
            request_id=UUID(int=5),
            execution_id=UUID(int=105),
            fingerprint="f" * 64,
            fail_before_commit=True,
        )
    assert store.aggregate()["execution_count"] == 0

    owner = store.prepare_provider_attempt(
        request_id=UUID(int=5),
        execution_id=UUID(int=105),
        fingerprint="f" * 64,
    )
    with pytest.raises(sqlite3.OperationalError):
        store.finalize_success(owner, fail_before_commit=True)
    assert store_state(store, owner) == "dispatch_intent"
    assert store.aggregate()["settlement_count"] == 0
    assert store.finalize_success(owner, fail_before_commit=False) is True
    store.close()


def test_v23_metadata_summary_never_serializes_identifiers_or_payload(tmp_path: Path) -> None:
    store = probe.SyntheticExecutionIntentStore(tmp_path / "control.sqlite3")
    store.initialize()
    sentinel = "synthetic-secret-payload-never-serialize"
    owner = store.prepare_provider_attempt(
        request_id=UUID(int=6),
        execution_id=UUID(int=106),
        fingerprint="1" * 64,
    )
    store.finalize_success(owner, fail_before_commit=False)
    encoded = json.dumps(probe.synthetic_intent_summary(store), sort_keys=True)
    assert sentinel not in encoded
    assert str(owner.execution_id) not in encoded
    assert "fingerprint" not in encoded
    assert "player_id" not in encoded
    assert "npc_id" not in encoded
    assert "conversation_id" not in encoded
    assert "raw_scope" not in encoded
    store.close()
