"""D1 in-memory constraint tests; no product schema or persistent test fixtures."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from scripts.f009_step5_benchmark import _stages, _trace
from scripts.f009_step5_layout_preflight import (
    LEAF_TABLES,
    rebuild_layout,
    row_digest,
    schema_contract,
)
from scripts.f009_step5_storage_breakdown import analyze_image, catalog

from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)

INFRA = Path(__file__).resolve().parents[1] / "src/cyber_town/infrastructure"
EXECUTION = str(UUID(int=1))
TRACE = str(UUID(int=2))
TAG = "a" * 64
TABLES = [(kind, table) for kind, tables in LEAF_TABLES.items() for table in tables]


@pytest.mark.parametrize("column", ["applied_at", "applied_at_ns", "applied_at_ms"])
def test_pair_digest_excludes_each_migration_clock_but_not_workload(column: str) -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute(f"CREATE TABLE schema_migrations (version INTEGER, {column} INTEGER)")
        connection.execute("INSERT INTO schema_migrations VALUES (1, 10)")
        connection.execute("CREATE TABLE workload (recorded_at_ms INTEGER)")
        connection.execute("INSERT INTO workload VALUES (100)")
        digest = row_digest(connection, exclude_migration_time=True)
        connection.execute(f"UPDATE schema_migrations SET {column}=20")
        assert row_digest(connection, exclude_migration_time=True) == digest
        connection.execute("UPDATE workload SET recorded_at_ms=101")
        assert row_digest(connection, exclude_migration_time=True) != digest


def database(kind: str) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA page_size=4096")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA temp_store=MEMORY")
    for migration in sorted((INFRA / kind / "migrations").glob("000[1-3]_*.sql")):
        connection.executescript(migration.read_text(encoding="utf-8"))
    if kind == "control":
        connection.execute(
            "INSERT INTO token_buckets VALUES ('player', ?, 'f-009-safety-control-v1', "
            "10, 100, 50, 0, 1)",
            (TAG,),
        )
        connection.execute(
            "INSERT INTO execution_admissions VALUES (?, ?, 'f-009-safety-control-v1', ?, ?, ?, 1)",
            (EXECUTION, EXECUTION, TAG, TAG, TAG),
        )
        connection.execute(
            "INSERT INTO provider_permits VALUES (?, 'f-009-safety-control-v1', "
            "?, ?, ?, 1, NULL, NULL)",
            (EXECUTION, TAG, TAG, TAG),
        )
        connection.execute(
            "INSERT INTO budget_execution_owners VALUES (?, 'f-009-budget-policy-v1', ?, ?, ?, 1)",
            (EXECUTION, TAG, TAG, TAG),
        )
        connection.execute(
            "INSERT INTO budget_reservations VALUES (?, 1, 'f-009-budget-policy-v1', "
            "'synthetic', 'fake', 'fake-model', 0, 0, 'reserved', 1, NULL, NULL, NULL, NULL)",
            (EXECUTION,),
        )
        connection.execute(
            "INSERT INTO budget_settlements VALUES (?, 1, 'f-009-budget-policy-v1', "
            "'synthetic', 0, 0, 0, 0, 0, 0, 'trusted_usage', 1)",
            (EXECUTION,),
        )
        connection.execute(
            "INSERT INTO circuit_breakers VALUES (?, 'f-009-retry-breaker-v1', "
            "'closed', 0, NULL, NULL, 0, 1)",
            (TAG,),
        )
        connection.execute(
            "INSERT INTO breaker_execution_results VALUES (?, ?, 'success', NULL, 1)",
            (EXECUTION, TAG),
        )
    else:
        trace = replace(_trace(), trace_id=UUID(TRACE), execution_id=UUID(EXECUTION))
        SqliteObservabilityRepository._insert_trace(connection, trace)
        for stage in _stages(trace):
            SqliteObservabilityRepository._upsert_stage(connection, stage)
        connection.execute(
            "INSERT INTO execution_links VALUES (?, ?, 'dispatch_owner', 1, 'active')",
            (TRACE, EXECUTION),
        )
        connection.execute(
            "INSERT INTO safety_cost_events VALUES (?, ?, 1, 'reservation', "
            "'f-009-budget-policy-v1', 'synthetic', 'fake', 'reserved', ?, ?, ?, "
            "0, 0, 0, 0, 0, 1)",
            (TRACE, EXECUTION, TAG, TAG, TAG),
        )
        connection.execute(
            "INSERT INTO retry_breaker_events VALUES (?, ?, 1, 'breaker_check', "
            "'f-009-retry-breaker-v1', 'not_reached', 'closed', 'allowed', "
            "NULL, 0, 0, 12000, 1)",
            (TRACE, EXECUTION),
        )
    connection.commit()
    return connection


@pytest.mark.parametrize("kind", LEAF_TABLES)
def test_only_fixed_layout_and_ten_indexes_change_with_rows_preserved(kind: str) -> None:
    with closing(database(kind)) as connection:
        before, rows = schema_contract(connection), row_digest(connection)
        result = rebuild_layout(connection, kind)
        assert result["tables"] == list(LEAF_TABLES[kind])
        assert result["logical_contract_unchanged"]
        assert schema_contract(connection) == before
        assert row_digest(connection) == rows
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        wr = {row[1] for row in connection.execute("PRAGMA table_list") if row[4]}
        assert wr == set(LEAF_TABLES[kind])
        report = analyze_image(connection.serialize(), catalog(connection))
        assert report["page_size"] == 4096
        assert report["physical_bytes"] == report["accounted_bytes"]
        assert report["unaccounted_pages"] == 0
        assert TAG not in json.dumps(report)


@pytest.mark.parametrize(("kind", "table"), TABLES)
def test_duplicate_pk_and_every_not_null_column_still_reject(kind: str, table: str) -> None:
    with closing(database(kind)) as connection:
        rebuild_layout(connection, kind)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f'INSERT INTO "{table}" SELECT * FROM "{table}" LIMIT 1')
        connection.rollback()
        for column in connection.execute(f'PRAGMA table_xinfo("{table}")').fetchall():
            if not column[3]:
                continue
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(f'UPDATE "{table}" SET "{column[1]}"=NULL')
            connection.rollback()


def outcome(connection: sqlite3.Connection, sql: str, value: Any) -> str:
    connection.execute("SAVEPOINT mutation")
    try:
        connection.execute(sql, (value,))
        return "accepted"
    except sqlite3.IntegrityError as error:
        return str(error.sqlite_errorname)
    finally:
        connection.execute("ROLLBACK TO mutation")
        connection.execute("RELEASE mutation")


@pytest.mark.parametrize(("kind", "table"), TABLES)
def test_check_fk_strict_default_and_nullable_semantics_match(kind: str, table: str) -> None:
    with closing(database(kind)) as original, closing(database(kind)) as candidate:
        rebuild_layout(candidate, kind)
        before = row_digest(candidate)
        for column in original.execute(f'PRAGMA table_xinfo("{table}")').fetchall():
            sql = f'UPDATE "{table}" SET "{column[1]}"=?'
            for value in (None, -1, 0, 1, 3, 257, 32769, 60000000000, "!", "", "b" * 64, b"x"):
                assert outcome(original, sql, value) == outcome(candidate, sql, value)
        assert row_digest(candidate) == before
        assert original.execute(f'PRAGMA table_xinfo("{table}")').fetchall() == (
            candidate.execute(f'PRAGMA table_xinfo("{table}")').fetchall()
        )


@pytest.mark.parametrize(("kind", "position"), [(k, n) for k in LEAF_TABLES for n in range(1, 5)])
def test_all_table_rebuilds_and_index_changes_roll_back_atomically(
    kind: str, position: int
) -> None:
    with closing(database(kind)) as connection:
        before = connection.serialize()
        with pytest.raises(ValueError, match=r"^layout_injected_failure$"):
            rebuild_layout(connection, kind, fail_after=position)
        assert connection.serialize() == before
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)


def test_dispatch_owner_unique_and_secondary_stage_unique_are_retained() -> None:
    with closing(database("observability")) as connection:
        rebuild_layout(connection, "observability")
        unique = {row[1]: row for row in connection.execute('PRAGMA index_list("execution_links")')}
        assert unique["idx_execution_links_one_dispatch_owner"][2] == 1
        trace = replace(_trace(), trace_id=UUID(int=3), execution_id=UUID(EXECUTION))
        SqliteObservabilityRepository._insert_trace(connection, trace)
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            connection.execute(
                "INSERT INTO execution_links VALUES (?, ?, 'dispatch_owner', 1, 'active')",
                (str(trace.trace_id), EXECUTION),
            )
        connection.rollback()
        indexes = connection.execute('PRAGMA index_list("trace_stage_events")').fetchall()
        assert any(
            row[2] == 1
            and row[3] == "u"
            and [c[2] for c in connection.execute(f'PRAGMA index_info("{row[1]}")')]
            == ["trace_id", "stage"]
            for row in indexes
        )


@pytest.mark.parametrize("violation", ["kind", "incoming_fk", "repeat"])
def test_layout_refuses_unsafe_boundaries_without_changes(violation: str) -> None:
    with closing(database("control")) as connection:
        if violation == "incoming_fk":
            connection.execute(
                "CREATE TABLE child (id TEXT REFERENCES provider_permits(execution_id)) STRICT"
            )
        elif violation == "repeat":
            rebuild_layout(connection, "control")
        before = connection.serialize()
        with pytest.raises(ValueError, match=r"^layout_"):
            rebuild_layout(connection, "unknown" if violation == "kind" else "control")
        assert connection.serialize() == before
