"""Append-only v4 migrations preserve logical metadata and atomic rollback."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Literal

import pytest
from scripts.f009_step5_compact_preflight import decoded_digest

from cyber_town.infrastructure.control.sqlite_control import CONTROL_MIGRATIONS
from cyber_town.infrastructure.observability.sqlite_observability import (
    OBSERVABILITY_MIGRATIONS,
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.observability.storage_codec import encode_value
from test_layout_preflight_step5 import database

INFRA = Path(__file__).resolve().parents[1] / "src/cyber_town/infrastructure"
NAMES = {
    "control": "0004_leaf_table_storage_layout.sql",
    "observability": "0004_compact_event_storage.sql",
}

SCOPE_COLUMNS = ("player_scope_tag", "player_npc_scope_tag", "conversation_scope_tag")
SCOPE_TEXT = ("1a" * 32, "2b" * 32, "3c" * 32)


def scope_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    columns = ",".join(f'"{column}" BLOB' for column in SCOPE_COLUMNS)
    connection.execute(f"CREATE TABLE provider_permits ({columns}, marker INTEGER)")
    connection.execute("INSERT INTO provider_permits VALUES (?,?,?,1)", SCOPE_TEXT)
    return connection


def recorded_digest(
    connection: sqlite3.Connection,
    record_property: Callable[[str, object], None],
    phase: Literal["first_digest", "repeat_digest", "synthetic_digest"],
) -> str:
    record_property("migration_stage", phase)
    try:
        result = decoded_digest(connection)
    except (TypeError, ValueError) as error:
        record_property(
            "migration_failure_code",
            "unsupported_json_value" if isinstance(error, TypeError) else "invalid_storage_value",
        )
        raise
    record_property("migration_stage", phase + "_returned")
    return result


@pytest.mark.parametrize("mask", range(8))
def test_migration_digest_scope_representations(mask: int) -> None:
    with closing(scope_database()) as connection:
        before = decoded_digest(connection)
        for index, column in enumerate(SCOPE_COLUMNS):
            if mask & (1 << index):
                connection.execute(
                    f'UPDATE provider_permits SET "{column}"=?',
                    (bytes.fromhex(SCOPE_TEXT[index]),),
                )
        assert decoded_digest(connection) == before


@pytest.mark.parametrize("column", SCOPE_COLUMNS)
def test_migration_digest_scope_change_is_visible(column: str) -> None:
    with closing(scope_database()) as connection:
        before = decoded_digest(connection)
        connection.execute(f'UPDATE provider_permits SET "{column}"=?', (b"\x00" * 32,))
        assert decoded_digest(connection) != before


@pytest.mark.parametrize("column", SCOPE_COLUMNS)
@pytest.mark.parametrize(
    "case",
    (
        "null",
        "integer",
        "float",
        "short_blob",
        "long_blob",
        "short_text",
        "long_text",
        "upper",
        "nonhex",
    ),
)
def test_migration_digest_scope_rejects_invalid(column: str, case: str) -> None:
    values = {
        "null": None,
        "integer": 1,
        "float": 1.5,
        "short_blob": b"\x00" * 31,
        "long_blob": b"\x00" * 33,
        "short_text": "a" * 63,
        "long_text": "a" * 65,
        "upper": "A" * 64,
        "nonhex": "x" * 64,
    }
    with closing(scope_database()) as connection:
        connection.execute(f'UPDATE provider_permits SET "{column}"=?', (values[case],))
        with pytest.raises(ValueError, match=r"^compact_invalid_control_scope$"):
            decoded_digest(connection)


@pytest.mark.parametrize("target", ("other_column", "other_table"))
def test_migration_digest_unknown_blob_is_not_converted(target: str) -> None:
    with closing(scope_database()) as connection:
        if target == "other_column":
            connection.execute("UPDATE provider_permits SET marker=?", (b"\x00" * 32,))
        else:
            connection.execute("CREATE TABLE unrelated (player_scope_tag BLOB)")
            connection.execute("INSERT INTO unrelated VALUES (?)", (b"\x00" * 32,))
        with pytest.raises(TypeError, match=r"^Object of type bytes is not JSON serializable$"):
            decoded_digest(connection)


@pytest.mark.parametrize("change", ("other_column", "extra_row", "extra_table", "migration"))
def test_migration_digest_keeps_non_scope_coverage(change: str) -> None:
    with closing(scope_database()) as connection:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER, applied_at_ns INTEGER)"
        )
        connection.execute("INSERT INTO schema_migrations VALUES (1,10)")
        before = decoded_digest(connection)
        statements = {
            "other_column": "UPDATE provider_permits SET marker=2",
            "extra_row": "INSERT INTO provider_permits SELECT * FROM provider_permits",
            "extra_table": "CREATE TABLE unrelated (value INTEGER)",
            "migration": "UPDATE schema_migrations SET version=2",
        }
        connection.execute(statements[change])
        assert decoded_digest(connection) != before


@pytest.mark.parametrize("clock", ("applied_at", "applied_at_ns", "applied_at_ms"))
def test_migration_digest_clock_exclusion_is_explicit(clock: str) -> None:
    with closing(scope_database()) as connection:
        connection.execute(f"CREATE TABLE schema_migrations (version INTEGER, {clock} INTEGER)")
        connection.execute("INSERT INTO schema_migrations VALUES (1,10)")
        complete = decoded_digest(connection)
        excluded = decoded_digest(connection, exclude_migration_time=True)
        connection.execute(f"UPDATE schema_migrations SET {clock}=11")
        assert decoded_digest(connection) != complete
        assert decoded_digest(connection, exclude_migration_time=True) == excluded
        connection.execute("UPDATE schema_migrations SET version=2")
        assert decoded_digest(connection, exclude_migration_time=True) != excluded


@pytest.mark.parametrize("kind", NAMES)
def test_version_four_is_append_only_registered(kind: str) -> None:
    migrations = CONTROL_MIGRATIONS if kind == "control" else OBSERVABILITY_MIGRATIONS
    assert len(migrations) >= 4
    assert migrations[3] == (4, NAMES[kind])


def migrate(connection: sqlite3.Connection, kind: str, fail_after: int | None = None) -> None:
    sql = (INFRA / kind / "migrations" / NAMES[kind]).read_text(encoding="utf-8")
    statements = SqliteObservabilityRepository._migration_statements(sql)
    connection.create_function("observability_encode_v1", 3, encode_value, deterministic=True)
    connection.execute("BEGIN IMMEDIATE")
    try:
        for i, statement in enumerate(statements):
            connection.execute(statement)
            if fail_after == i:
                raise RuntimeError("synthetic_migration_interruption")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        connection.commit()
    except Exception:
        connection.rollback()
        raise


@pytest.mark.parametrize("kind", NAMES)
def test_populated_v3_upgrade_preserves_decoded_rows_and_constraints(kind: str) -> None:
    with closing(database(kind)) as connection:
        before = decoded_digest(connection)
        migrate(connection, kind)
        assert connection.execute("PRAGMA user_version").fetchone() == (4,)
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert decoded_digest(connection) == before


@pytest.mark.parametrize("kind", NAMES)
@pytest.mark.parametrize("statement", [0, 5, 10, 15])
def test_migration_interruption_rolls_back_all_prior_changes(kind: str, statement: int) -> None:
    with closing(database(kind)) as connection:
        before = connection.serialize()
        with pytest.raises(RuntimeError, match="synthetic_migration_interruption"):
            migrate(connection, kind, fail_after=statement)
        assert connection.serialize() == before
        assert connection.execute("PRAGMA user_version").fetchone() == (3,)


def test_invalid_old_uuid_aborts_entire_observability_upgrade() -> None:
    with closing(database("observability")) as connection:
        connection.execute("UPDATE execution_links SET execution_id=?", ("x" * 36,))
        connection.commit()
        before = connection.serialize()
        with pytest.raises(sqlite3.OperationalError):
            migrate(connection, "observability")
        assert connection.serialize() == before


@pytest.mark.parametrize("kind", NAMES)
def test_repository_populated_upgrade_repeat_and_cli_boundary(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_property: Callable[[str, object], None],
) -> None:
    import hashlib

    from cyber_town.infrastructure.control import sqlite_control
    from cyber_town.infrastructure.observability import sqlite_observability

    module = sqlite_control if kind == "control" else sqlite_observability
    repo_type = (
        sqlite_control.SqliteSafetyControlRepository
        if kind == "control"
        else sqlite_observability.SqliteObservabilityRepository
    )
    migration_attr = "CONTROL_MIGRATIONS" if kind == "control" else "OBSERVABILITY_MIGRATIONS"
    migrations = getattr(module, migration_attr)
    repo = repo_type(database_path=tmp_path / f"{kind}.sqlite3", allowed_root=tmp_path)
    # The fixture contains every approved leaf table, all built with old SQL.
    with closing(database(kind)) as seed, closing(sqlite3.connect(repo.database_path)) as target:
        seed.backup(target)
        time_column = "applied_at_ns" if kind == "control" else "applied_at_ms"
        target.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY CHECK(version>0), "
            "name TEXT NOT NULL UNIQUE, checksum TEXT NOT NULL CHECK(length(checksum)=64), "
            f"{time_column} INTEGER NOT NULL CHECK({time_column}>0)) STRICT"
        )
        target.executemany(
            "INSERT INTO schema_migrations VALUES (?,?,?,1)",
            [
                (
                    version,
                    name,
                    hashlib.sha256((INFRA / kind / "migrations" / name).read_bytes()).hexdigest(),
                )
                for version, name in migrations[:3]
            ],
        )
        target.commit()
    if kind != "control":
        with monkeypatch.context() as context:
            context.setattr(module, migration_attr, migrations[:3])
            repo.initialize()
    record_property("migration_stage", "initialize")
    repo.initialize()
    record_property("migration_stage", "initialize_returned")
    with closing(sqlite3.connect(repo.database_path)) as connection:
        digest = recorded_digest(connection, record_property, "first_digest")
        expected_version = migrations[-1][0]
        assert connection.execute("PRAGMA user_version").fetchone() == (expected_version,)
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone() == (
            expected_version,
        )
    record_property("migration_stage", "repeat_initialize")
    repo.initialize()
    record_property("migration_stage", "repeat_initialize_returned")
    with closing(sqlite3.connect(repo.database_path)) as connection:
        assert recorded_digest(connection, record_property, "repeat_digest") == digest
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    if isinstance(repo, sqlite_observability.SqliteObservabilityRepository):
        query = sqlite_observability.ObservabilityQuery(limit=10)
        assert len(repo.query_traces(query)) == 1
        assert repo.query_traces(query)[0]["provider_kind"] == "fake"
