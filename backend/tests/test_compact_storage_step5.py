"""Candidate C: fail-first codec and synthetic layout checks, never real data."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from cyber_town.infrastructure.observability.storage_codec import (
    CODEC_VERSION,
    ENUM_FIELDS,
    decode_value,
    encode_value,
)


def test_codec_version_is_explicit() -> None:
    assert CODEC_VERSION == "f009-observability-storage-v1"


@pytest.mark.parametrize("field", list(ENUM_FIELDS))
def test_each_fixed_enum_round_trips_without_aliases(field: tuple[str, str]) -> None:
    mapping = ENUM_FIELDS[field]
    assert len(set(mapping.values())) == len(mapping)
    for word, code in mapping.items():
        assert encode_value(*field, word) == code
        assert decode_value(*field, code) == word
        assert type(code) is int
    for invalid in (True, False, -1, 1000000, "secret-sentinel", b"secret-sentinel"):
        with pytest.raises(ValueError, match=r"^Invalid observability storage value$"):
            decode_value(*field, invalid)


@pytest.mark.parametrize("table", ["execution_links", "safety_cost_events", "retry_breaker_events"])
def test_execution_uuid_has_lossless_fixed_binary_encoding(table: str) -> None:
    value = "12345678-1234-4234-8234-abcdefabcdef"
    encoded = encode_value(table, "execution_id", value)
    assert isinstance(encoded, bytes) and len(encoded) == 16
    assert decode_value(table, "execution_id", encoded) == value
    for invalid in (value.upper(), " " + value, value.replace("-", ""), "x" * 36, 1, None):
        with pytest.raises(ValueError):
            encode_value(table, "execution_id", invalid)
    for invalid_binary in (b"x" * 15, b"x" * 17, "x" * 16, bytearray(16)):
        with pytest.raises(ValueError):
            decode_value(table, "execution_id", invalid_binary)


@pytest.mark.parametrize("column", ["player_scope_tag", "npc_scope_tag", "player_npc_scope_tag"])
def test_hmac_is_binary_only_at_storage_boundary(column: str) -> None:
    tag = "abc01234" * 8
    encoded = encode_value("safety_cost_events", column, tag)
    assert isinstance(encoded, bytes) and len(encoded) == 32
    assert decode_value("safety_cost_events", column, encoded) == tag
    for invalid in (tag.upper(), "g" * 64, tag[:-1], 0, None):
        with pytest.raises(ValueError):
            encode_value("safety_cost_events", column, invalid)


def test_null_is_allowed_only_for_nullable_failure_reason() -> None:
    assert encode_value("retry_breaker_events", "failure_reason", None) is None
    assert decode_value("retry_breaker_events", "failure_reason", None) is None
    with pytest.raises(ValueError):
        encode_value("trace_stage_events", "stage", None)


def test_invalid_input_is_not_echoed_and_mapping_is_immutable(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sentinel = "synthetic-raw-secret-must-not-appear"
    for table, column in (("trace_stage_events", "stage"), (sentinel, sentinel)):
        with pytest.raises(ValueError) as caught:
            encode_value(table, column, sentinel)
        assert sentinel not in str(caught.value)
        assert sentinel not in repr(caught.value)
        assert caught.value.__cause__ is None
    assert sentinel not in caplog.text
    with pytest.raises(TypeError):
        ENUM_FIELDS[("trace_stage_events", "stage")]["new"] = 99  # type: ignore[index]


def test_synthetic_compact_layout_has_exact_decoded_rows() -> None:
    from scripts.f009_step5_compact_preflight import compact_rebuild, decoded_digest

    from test_layout_preflight_step5 import database

    with closing(database("observability")) as connection:
        before = decoded_digest(connection)
        compact_rebuild(connection, "observability")
        assert decoded_digest(connection) == before
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert connection.execute(
            "SELECT typeof(stage) FROM trace_stage_events LIMIT 1"
        ).fetchone() == ("integer",)
        assert connection.execute(
            "SELECT length(execution_id) FROM execution_links"
        ).fetchone() == (16,)


@pytest.mark.parametrize("position", [1, 2, 3, 4])
def test_compact_rebuild_is_atomic_at_each_table(position: int) -> None:
    from scripts.f009_step5_compact_preflight import compact_rebuild

    from test_layout_preflight_step5 import database

    with closing(database("observability")) as connection:
        before = connection.serialize()
        with pytest.raises(ValueError, match="compact_injected_failure"):
            compact_rebuild(connection, "observability", fail_after=position)
        assert connection.serialize() == before
        assert not connection.in_transaction


def test_invalid_legacy_uuid_fails_instead_of_repairing_or_dropping() -> None:
    from scripts.f009_step5_compact_preflight import compact_rebuild

    from test_layout_preflight_step5 import database

    with closing(database("observability")) as connection:
        connection.execute("UPDATE execution_links SET execution_id=?", ("x" * 36,))
        connection.commit()
        before = connection.serialize()
        with pytest.raises((ValueError, sqlite3.Error)):
            compact_rebuild(connection, "observability")
        assert connection.serialize() == before


@pytest.mark.parametrize(
    "table", ["trace_stage_events", "execution_links", "safety_cost_events", "retry_breaker_events"]
)
def test_fields_keys_fk_defaults_and_every_not_null_are_preserved(table: str) -> None:
    from scripts.f009_step5_compact_preflight import compact_rebuild

    from cyber_town.infrastructure.observability.storage_codec import ENCODED_FIELDS
    from test_layout_preflight_step5 import database, outcome

    with (
        closing(database("observability")) as original,
        closing(database("observability")) as candidate,
    ):
        compact_rebuild(candidate, "observability")
        old_columns = original.execute(f'PRAGMA table_xinfo("{table}")').fetchall()
        new_columns = candidate.execute(f'PRAGMA table_xinfo("{table}")').fetchall()
        assert len(old_columns) == len(new_columns)
        assert (
            original.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
            == candidate.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
        )
        for old, new in zip(old_columns, new_columns, strict=True):
            assert old[:2] == new[:2] and old[3] == new[3] and old[5:] == new[5:]
            field = (table, old[1])
            if field not in ENCODED_FIELDS:
                assert old == new
                for value in (None, -1, 0, 1, 257, 32769, "!", "", "b" * 64, b"x"):
                    sql = f'UPDATE "{table}" SET "{old[1]}"=?'
                    assert outcome(original, sql, value) == outcome(candidate, sql, value)
            elif old[4] is not None:
                assert decode_value(*field, int(new[4])) == old[4].strip("'")
            if old[3]:
                with pytest.raises(sqlite3.IntegrityError):
                    candidate.execute(f'UPDATE "{table}" SET "{old[1]}"=NULL')
                candidate.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            candidate.execute(f'INSERT INTO "{table}" SELECT * FROM "{table}" LIMIT 1')
        candidate.rollback()


@pytest.mark.parametrize("field", list(ENUM_FIELDS))
def test_sql_enum_domain_and_cross_column_checks_match(field: tuple[str, str]) -> None:
    from scripts.f009_step5_compact_preflight import compact_rebuild

    from test_layout_preflight_step5 import database, outcome

    with (
        closing(database("observability")) as original,
        closing(database("observability")) as candidate,
    ):
        compact_rebuild(candidate, "observability")
        table, column = field
        sql = f'UPDATE "{table}" SET "{column}"=?'
        for word, code in ENUM_FIELDS[field].items():
            assert outcome(original, sql, word) == outcome(candidate, sql, code)
        assert outcome(candidate, sql, 1000000) != "accepted"
        assert outcome(candidate, sql, "secret-sentinel") != "accepted"


def test_unique_dispatch_owner_rejects_second_trace_and_shared_waiter_still_works() -> None:
    from dataclasses import replace
    from uuid import UUID

    from scripts.f009_step5_benchmark import _stages, _trace
    from scripts.f009_step5_compact_preflight import _ExperimentalConnection, compact_rebuild

    from cyber_town.application.observability import AttemptKind, IdempotencyOutcome
    from cyber_town.infrastructure.observability.sqlite_observability import (
        SqliteObservabilityRepository,
    )
    from test_layout_preflight_step5 import EXECUTION, database

    with closing(database("observability")) as connection:
        compact_rebuild(connection, "observability")
        adapter = _ExperimentalConnection(connection)
        trace = replace(_trace(), trace_id=UUID(int=4), execution_id=UUID(EXECUTION))
        SqliteObservabilityRepository._insert_trace(connection, trace)
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError):
            SqliteObservabilityRepository._insert_execution_link_if_needed(adapter, trace)  # type: ignore[arg-type]
        connection.rollback()
        trace = replace(
            trace,
            attempt_kind=AttemptKind.CONCURRENT_WAITER,
            provider_dispatch_count=0,
            idempotency_outcome=IdempotencyOutcome.INFLIGHT_SHARED,
        )
        SqliteObservabilityRepository._insert_execution_link_if_needed(adapter, trace)  # type: ignore[arg-type]
        for stage in _stages(trace):
            SqliteObservabilityRepository._upsert_stage(adapter, stage)  # type: ignore[arg-type]
        SqliteObservabilityRepository._validate_persisted_stages(adapter, trace.trace_id)  # type: ignore[arg-type]
        assert adapter.execute(
            "SELECT execution_id, link_kind FROM execution_links WHERE trace_id=?",
            (str(trace.trace_id),),
        ).fetchone() == (EXECUTION, "shared_waiter")
        connection.commit()


@pytest.mark.parametrize("violation", ["kind", "incoming_fk", "repeat"])
def test_compact_preflight_refuses_unsafe_boundaries(violation: str) -> None:
    from scripts.f009_step5_compact_preflight import compact_rebuild

    from test_layout_preflight_step5 import database

    with closing(database("observability")) as connection:
        if violation == "incoming_fk":
            connection.execute(
                "CREATE TABLE child (id TEXT REFERENCES execution_links(trace_id)) STRICT"
            )
        elif violation == "repeat":
            compact_rebuild(connection, "observability")
        before = connection.serialize()
        with pytest.raises(ValueError, match=r"^compact_"):
            compact_rebuild(connection, "unknown" if violation == "kind" else "observability")
        assert connection.serialize() == before
