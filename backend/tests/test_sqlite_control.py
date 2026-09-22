from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from cyber_town.application.budget import BudgetScopeTags
from cyber_town.application.control import PermitScopeTags
from cyber_town.infrastructure.control import sqlite_control as control_module
from cyber_town.infrastructure.control.sqlite_control import (
    SafetyControlStorageError,
    SqliteSafetyControlRepository,
)

_CANDIDATE_INDEX = "idx_budget_owners_npc"


def _v9_legacy_fixture(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: int = 8,
) -> dict[str, Any]:
    from contextlib import closing

    from scripts import f009_step6_qa as qa

    with monkeypatch.context() as legacy:
        legacy.setattr(
            control_module, "CONTROL_MIGRATIONS", control_module.CONTROL_MIGRATIONS[:version]
        )
        repository = make_repository(root)
        try:
            reasons = (
                "completed",
                "cancelled",
                "failed",
                "control_failure",
                "abandoned_after_restart",
            )
            with closing(repository._connect()) as connection:
                for index in range(6):
                    execution = str(UUID(int=1000 + index))
                    connection.execute(
                        "INSERT INTO execution_admissions VALUES (?,?,?,?,?,?,?)",
                        (
                            execution,
                            str(UUID(int=2000 + index)),
                            "f-009-safety-control-v1",
                            "a" * 64,
                            "b" * 64,
                            "c" * 64,
                            1000 + index,
                        ),
                    )
                    connection.execute(
                        "INSERT INTO provider_permits VALUES (?,?,?,?,?,?,?,?)",
                        (
                            execution,
                            "f-009-safety-control-v1",
                            "a" * 64,
                            "b" * 64,
                            "c" * 64,
                            1000 + index,
                            2000 + index if index < 5 else None,
                            reasons[index] if index < 5 else None,
                        ),
                    )
                connection.commit()
                result = qa.space_logical_digest(connection, candidate=False)
                result["permit_rows"] = connection.execute(
                    "SELECT * FROM provider_permits ORDER BY execution_id"
                ).fetchall()
                return result
        finally:
            repository.close()


@pytest.mark.parametrize("version", (7, 8))
def test_v9_product_upgrade_preserves_rows_and_restarts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: int,
) -> None:
    import hashlib
    from contextlib import closing

    from scripts import f009_step6_qa as qa

    migrations = control_module.CONTROL_MIGRATIONS
    monkeypatch.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:9])
    before = _v9_legacy_fixture(tmp_path, monkeypatch, version)
    repository = make_repository(tmp_path)
    try:
        repository.initialize()
        with closing(repository._connect()) as connection:
            after = qa.space_logical_digest(connection, candidate=True)
            if version == 8:
                assert after["digest"] == before["digest"]
            else:
                assert [
                    row[1] for row in connection.execute("PRAGMA table_info(budget_window_totals)")
                ][-3:] == [
                    "checked_attempts_1h",
                    "checked_attempts_24h",
                    "checked_cost_24h_micro_usd",
                ]
            assert (
                connection.execute(
                    "SELECT execution_id,policy_version,lower(hex(player_scope_tag)),"
                    "lower(hex(player_npc_scope_tag)),lower(hex(conversation_scope_tag)),"
                    "acquired_at_ns,released_at_ns,release_reason "
                    "FROM provider_permits ORDER BY execution_id"
                ).fetchall()
                == before["permit_rows"]
            )
            assert after["row_counts"] == before["row_counts"]
            assert after["migration_rows"][:version] == before["migration_rows"]
            assert after["user_version"] == 9
            raw = (
                Path(control_module.__file__).parent / "migrations" / qa.SPACE_MIGRATION_NAME
            ).read_bytes()
            assert raw == qa.SPACE_DRAFT_SQL.encode("utf-8")
            assert after["migration_rows"][-1][2] == hashlib.sha256(raw).hexdigest()
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)
            assert connection.execute("PRAGMA synchronous").fetchone() == (2,)
        assert repository.try_acquire_permit(
            execution_id=UUID(int=1005),
            scope_tags=tags(),
            acquired_at_ns=3000,
        )
        assert not repository.try_acquire_permit(
            execution_id=UUID(int=1000),
            scope_tags=tags(),
            acquired_at_ns=3000,
        )
        assert repository.recover_open_permits(now_ns=4000) == 1
        assert repository.recover_open_permits(now_ns=5000) == 0
    finally:
        repository.close()
    with monkeypatch.context() as legacy:
        legacy.setattr(control_module, "CONTROL_MIGRATIONS", control_module.CONTROL_MIGRATIONS[:8])
        old = SqliteSafetyControlRepository(
            database_path=tmp_path / "control.sqlite3",
            allowed_root=tmp_path,
        )
        try:
            with pytest.raises(SafetyControlStorageError):
                old.initialize()
        finally:
            old.close()


@pytest.mark.parametrize("point", range(1, 9))
def test_v9_product_migration_fault_is_atomic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    point: int,
) -> None:
    from contextlib import closing

    _v9_legacy_fixture(tmp_path, monkeypatch)
    with closing(sqlite3.connect(tmp_path / "control.sqlite3")) as connection:
        before = tuple(connection.iterdump())
    original = SqliteSafetyControlRepository._migration_statements

    def fault(script: str) -> tuple[str, ...]:
        statements = original(script)
        if "CREATE TABLE v9_provider_permits" in script:
            return (*statements[:point], "SELECT * FROM synthetic_v9_fault", *statements[point:])
        return statements

    monkeypatch.setattr(SqliteSafetyControlRepository, "_migration_statements", staticmethod(fault))
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    try:
        with pytest.raises(SafetyControlStorageError):
            repository.initialize()
        with closing(repository._connect()) as connection:
            assert tuple(connection.iterdump()) == before
            assert connection.execute("PRAGMA user_version").fetchone() == (8,)
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        repository.close()


@pytest.mark.parametrize(
    "column", ("player_scope_tag", "player_npc_scope_tag", "conversation_scope_tag")
)
@pytest.mark.parametrize("bad", ("A" * 64, "a" * 63, b"a" * 64, None))
def test_v9_product_damaged_old_scope_rejects_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    column: str,
    bad: object,
) -> None:
    from contextlib import closing

    _v9_legacy_fixture(tmp_path, monkeypatch)
    with closing(sqlite3.connect(tmp_path / "control.sqlite3")) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        # Build a deliberately weak synthetic legacy table, without disabling safety pragmas.
        rows = connection.execute("SELECT * FROM provider_permits").fetchall()
        connection.execute("DROP TABLE provider_permits")
        connection.execute(
            "CREATE TABLE provider_permits (execution_id TEXT PRIMARY KEY REFERENCES "
            "execution_admissions(execution_id), policy_version TEXT NOT NULL, "
            "player_scope_tag ANY, player_npc_scope_tag ANY, conversation_scope_tag ANY, "
            "acquired_at_ns INTEGER NOT NULL, released_at_ns INTEGER, release_reason TEXT) "
            "STRICT, WITHOUT ROWID"
        )
        connection.executemany("INSERT INTO provider_permits VALUES (?,?,?,?,?,?,?,?)", rows)
        connection.execute(
            f"UPDATE provider_permits SET {column}=? WHERE execution_id=?",
            (bad, str(UUID(int=1005))),
        )
        connection.commit()
        before = tuple(connection.iterdump())
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    try:
        with pytest.raises(SafetyControlStorageError):
            repository.initialize()
        with closing(repository._connect()) as connection:
            assert tuple(connection.iterdump()) == before
            assert connection.execute("PRAGMA user_version").fetchone() == (8,)
            assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
            assert connection.execute("PRAGMA trusted_schema").fetchone() == (0,)
    finally:
        repository.close()


def test_v9_product_missing_unhex_preserves_v8(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from contextlib import closing

    _v9_legacy_fixture(tmp_path, monkeypatch)
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    original = repository._connect
    with closing(original()) as connection:
        before = tuple(connection.iterdump())

    def unsupported() -> sqlite3.Connection:
        connection = original()
        connection.create_function("unhex", 1, lambda _: None)
        return connection

    monkeypatch.setattr(repository, "_connect", unsupported)
    try:
        with pytest.raises(SafetyControlStorageError):
            repository.initialize()
        with closing(original()) as connection:
            assert tuple(connection.iterdump()) == before
            assert connection.execute("PRAGMA user_version").fetchone() == (8,)
    finally:
        repository.close()


@pytest.mark.parametrize("table", ("provider_permits", "execution_admissions"))
@pytest.mark.parametrize(
    "column", ("player_scope_tag", "player_npc_scope_tag", "conversation_scope_tag")
)
def test_v9_product_each_scope_remains_independently_checked(
    tmp_path: Path,
    table: str,
    column: str,
) -> None:
    from contextlib import closing

    repository = make_repository(tmp_path)
    execution = UUID(int=3000)
    try:
        repository.record_admission(
            execution_id=execution,
            request_id=UUID(int=4000),
            scope_tags=tags(),
            admitted_at_ns=1000,
        )
        assert repository.try_acquire_permit(
            execution_id=execution,
            scope_tags=tags(),
            acquired_at_ns=1001,
        )
        value = b"\xff" * 32 if table == "provider_permits" else "f" * 64
        with closing(repository._connect()) as connection:
            connection.execute(f"UPDATE {table} SET {column}=?", (value,))
            connection.commit()
            before = tuple(connection.iterdump())
        with pytest.raises(SafetyControlStorageError):
            repository.try_acquire_permit(
                execution_id=execution,
                scope_tags=tags(),
                acquired_at_ns=1002,
            )
        with closing(repository._connect()) as connection:
            assert tuple(connection.iterdump()) == before
        assert repository.active_permit_count() == 1
    finally:
        repository.close()


@pytest.mark.parametrize("column_index", (0, 1, 2))
@pytest.mark.parametrize("bad", ("a" * 64, b"a" * 31, b"a" * 33, 123, None))
def test_v9_product_permit_matcher_rejects_invalid_storage(
    tmp_path: Path,
    column_index: int,
    bad: object,
) -> None:
    from contextlib import closing

    repository = make_repository(tmp_path)
    try:
        values: list[object] = [bytes.fromhex(value * 64) for value in ("a", "b", "c")]
        values[column_index] = bad
        with closing(repository._connect()) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT ? AS player_scope_tag, ? AS player_npc_scope_tag, "
                "? AS conversation_scope_tag",
                values,
            ).fetchone()
            assert not repository._permit_scope_matches(row, repository._permit_scope_bytes(tags()))
    finally:
        repository.close()


@pytest.mark.parametrize("limit", ("global", "player", "player_npc", "conversation"))
def test_v9_independent_writers_keep_limits_and_release(tmp_path: Path, limit: str) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    count = 3 if limit in {"global", "player"} else 2
    repositories = [make_repository(tmp_path) for _ in range(count)]
    scopes = []
    for index in range(count):
        player = "a" if limit in {"player", "player_npc"} else str(index + 1)
        pair = "b" if limit == "player_npc" else str(index + 4)
        conversation = "c" if limit == "conversation" else str(index + 7)
        scopes.append(PermitScopeTags(player * 64, pair * 64, conversation * 64))
    barrier = Barrier(count)

    def acquire(index: int) -> bool:
        barrier.wait(timeout=10)
        return repositories[index].try_acquire_permit(
            execution_id=UUID(int=5000 + index),
            scope_tags=scopes[index],
            acquired_at_ns=2000,
        )

    try:
        for index, scope in enumerate(scopes):
            repositories[0].record_admission(
                execution_id=UUID(int=5000 + index),
                request_id=UUID(int=6000 + index),
                scope_tags=scope,
                admitted_at_ns=1000,
            )
        with ThreadPoolExecutor(max_workers=count) as pool:
            results = list(pool.map(acquire, range(count)))
        assert sum(results) == (2 if count == 3 else 1)
        winner, blocked = results.index(True), results.index(False)
        assert repositories[winner].try_acquire_permit(
            execution_id=UUID(int=5000 + winner),
            scope_tags=scopes[winner],
            acquired_at_ns=2500,
        )
        repositories[winner].release_permit(
            execution_id=UUID(int=5000 + winner),
            released_at_ns=3000,
            reason="completed",
        )
        assert not repositories[winner].try_acquire_permit(
            execution_id=UUID(int=5000 + winner),
            scope_tags=scopes[winner],
            acquired_at_ns=4000,
        )
        assert repositories[blocked].try_acquire_permit(
            execution_id=UUID(int=5000 + blocked),
            scope_tags=scopes[blocked],
            acquired_at_ns=4000,
        )
        assert repositories[0].active_permit_count() == (2 if count == 3 else 1)
    finally:
        for repository in repositories:
            repository.close()


@pytest.mark.parametrize(
    "reason", ("completed", "cancelled", "failed", "control_failure", "abandoned_after_restart")
)
def test_v9_product_release_reasons_remain_idempotent(tmp_path: Path, reason: str) -> None:
    from contextlib import closing

    repository = make_repository(tmp_path)
    try:
        repository.record_admission(
            execution_id=UUID(int=7000),
            request_id=UUID(int=8000),
            scope_tags=tags(),
            admitted_at_ns=1000,
        )
        assert repository.try_acquire_permit(
            execution_id=UUID(int=7000),
            scope_tags=tags(),
            acquired_at_ns=1001,
        )
        repository.release_permit(execution_id=UUID(int=7000), released_at_ns=2000, reason=reason)
        repository.release_permit(execution_id=UUID(int=7000), released_at_ns=3000, reason=reason)
        with closing(repository._connect()) as connection:
            assert connection.execute(
                "SELECT released_at_ns,release_reason FROM provider_permits"
            ).fetchone() == (2000, reason)
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        repository.close()


def test_v8_upgrade_rebuilds_corrupted_v7_projection_from_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migrations = control_module.CONTROL_MIGRATIONS
    monkeypatch.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:8])
    with monkeypatch.context() as legacy:
        legacy.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:7])
        repository = make_repository(tmp_path)
        repository.close()
    database = tmp_path / "control.sqlite3"
    identity = _insert_v6_owner(database)
    now = 1_800_000_000_000_000_000
    scope = BudgetScopeTags("a" * 64, "d" * 64, "b" * 64)
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "INSERT INTO budget_reservations "
            "(execution_id,attempt_number,policy_version,pricing_version,provider_kind,"
            "provider_model,reserved_micro_usd,soft_warning,status,reserved_at_ns) "
            "VALUES (?,1,'f-009-budget-policy-v1','synthetic-v7','fake',"
            "'fake-model',0,0,'reserved',?)",
            (identity, now),
        )
        for kind, tag in repository._budget_scope_pairs(scope):
            connection.execute(
                "INSERT INTO budget_window_totals VALUES (?,?,0,0,0,1,?)",
                (kind, tag, now),
            )
        connection.execute(
            "INSERT INTO budget_window_projection_state VALUES (1,?,?,?,?,?,?)",
            (
                "f-009-budget-window-projection-v1",
                "f-009-budget-policy-v1",
                now - 3_600_000_000_000,
                now - 86_400_000_000_000,
                1,
                now,
            ),
        )
    upgraded = make_repository(tmp_path)
    try:
        with sqlite3.connect(database) as connection:
            assert connection.execute("PRAGMA user_version").fetchone() == (8,)
            assert connection.execute(
                "SELECT COUNT(*) FROM budget_window_projection_state"
            ).fetchone() == (0,)
            connection.execute("BEGIN IMMEDIATE")
            upgraded._advance_budget_projection(connection, now_ns=now)
            totals = upgraded._all_window_totals(connection, scope_tags=scope, now_ns=now)
            assert set(totals.values()) == {(1, 1, 0)}
            connection.commit()
            connection.row_factory = None
            assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        upgraded.close()


def test_v8_migration_failure_rolls_back_columns_and_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migrations = control_module.CONTROL_MIGRATIONS
    monkeypatch.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:8])
    with monkeypatch.context() as legacy:
        legacy.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:7])
        repository = make_repository(tmp_path)
        repository.close()
    original = SqliteSafetyControlRepository._migration_statements

    def broken(script: str) -> tuple[str, ...]:
        return (*original(script), "SELECT * FROM synthetic_missing_table")

    with monkeypatch.context() as fault:
        fault.setattr(SqliteSafetyControlRepository, "_migration_statements", staticmethod(broken))
        repository = SqliteSafetyControlRepository(
            database_path=tmp_path / "control.sqlite3", allowed_root=tmp_path
        )
        try:
            with pytest.raises(SafetyControlStorageError):
                repository.initialize()
        finally:
            repository.close()
    with sqlite3.connect(tmp_path / "control.sqlite3") as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (7,)
        assert "checked_attempts_1h" not in {
            row[1] for row in connection.execute("PRAGMA table_info(budget_window_totals)")
        }
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone() == (7,)
    retried = make_repository(tmp_path)
    retried.close()
    with sqlite3.connect(tmp_path / "control.sqlite3") as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (8,)


def make_repository(tmp_path: Path) -> SqliteSafetyControlRepository:
    repository = SqliteSafetyControlRepository(
        database_path=tmp_path / "control.sqlite3",
        allowed_root=tmp_path,
    )
    repository.initialize()
    return repository


def tags(seed: str = "a") -> PermitScopeTags:
    return PermitScopeTags(
        player_scope_tag=seed * 64,
        player_npc_scope_tag="b" * 64,
        conversation_scope_tag="c" * 64,
    )


def test_migrations_are_strict_and_append_only_through_current_version(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)

    with sqlite3.connect(repository.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        strict = {
            row[1]: row[-1]
            for row in connection.execute("PRAGMA table_list").fetchall()
            if row[1] in tables
        }
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        migration_versions = tuple(
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        )
        indexes = {
            row[1] for row in connection.execute("PRAGMA index_list('budget_execution_owners')")
        }

    assert tables == {
        "schema_migrations",
        "token_buckets",
        "execution_admissions",
        "provider_permits",
        "budget_execution_owners",
        "budget_reservations",
        "budget_settlements",
        "budget_window_projection_state",
        "budget_window_totals",
        "circuit_breakers",
        "breaker_probe_leases",
        "breaker_execution_results",
        "control_execution_intents",
    }
    assert set(strict) == tables
    assert all(value == 1 for value in strict.values())
    assert control_module.CONTROL_MIGRATIONS[-1] == (
        10,
        "0010_deepseek_flash_pricing_reservation.sql",
    )
    assert migration_versions == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    assert user_version == 10
    assert _CANDIDATE_INDEX not in indexes


def test_v10_pricing_reservation_upgrade_preserves_v9_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migrations = control_module.CONTROL_MIGRATIONS
    with monkeypatch.context() as legacy:
        legacy.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:9])
        repository = make_repository(tmp_path)
        repository.close()
    database = tmp_path / "control.sqlite3"
    execution_id = _insert_v6_owner(database)
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "INSERT INTO budget_reservations "
            "(execution_id,attempt_number,policy_version,pricing_version,provider_kind,"
            "provider_model,reserved_micro_usd,soft_warning,status,reserved_at_ns,"
            "released_at_ns,release_reason) VALUES "
            "(?,1,'f-009-budget-policy-v1','legacy-price-v1','deepseek',"
            "'deepseek-flash',2000,0,'released',1000,2000,'cancelled_before_dispatch')",
            (execution_id,),
        )

    upgraded = make_repository(tmp_path)
    upgraded.close()
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (10,)
        assert connection.execute(
            "SELECT execution_id,reserved_micro_usd,status FROM budget_reservations"
        ).fetchone() == (execution_id, 2000, "released")
        reservation_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='budget_reservations'"
        ).fetchone()[0]
        settlement_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='budget_settlements'"
        ).fetchone()[0]
        assert "BETWEEN 0 AND 11000" in reservation_sql
        assert "BETWEEN 0 AND 11000" in settlement_sql
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def _initialize_v6(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[tuple[int, str], ...]:
    migrations = control_module.CONTROL_MIGRATIONS
    monkeypatch.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:6])
    repository = make_repository(tmp_path)
    repository.close()
    monkeypatch.setattr(control_module, "CONTROL_MIGRATIONS", migrations)
    return migrations


def _insert_v6_owner(database: Path) -> str:
    execution_id = "11111111-1111-4111-8111-111111111111"
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "INSERT INTO execution_admissions VALUES (?,?,?,?,?,?,?)",
            (
                execution_id,
                "22222222-2222-4222-8222-222222222222",
                "f-009-safety-control-v1",
                "a" * 64,
                "b" * 64,
                "c" * 64,
                1_800_000_000_000_000_000,
            ),
        )
        connection.execute(
            "INSERT INTO budget_execution_owners VALUES (?,?,?,?,?,?)",
            (
                execution_id,
                "f-009-budget-policy-v1",
                "a" * 64,
                "d" * 64,
                "b" * 64,
                1_800_000_000_000_000_000,
            ),
        )
    return execution_id


def test_populated_v6_upgrades_atomically_to_v7(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migrations = _initialize_v6(tmp_path, monkeypatch)
    monkeypatch.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:7])
    database = tmp_path / "control.sqlite3"
    execution_id = _insert_v6_owner(database)

    upgraded = SqliteSafetyControlRepository(database_path=database, allowed_root=tmp_path)
    upgraded.initialize()
    upgraded.close()
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (7,)
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert versions == [
            (1,),
            (2,),
            (3,),
            (4,),
            (5,),
            (6,),
            (7,),
        ]
        assert connection.execute(
            "SELECT execution_id FROM budget_execution_owners"
        ).fetchone() == (execution_id,)
        assert _CANDIDATE_INDEX not in {
            row[1] for row in connection.execute("PRAGMA index_list('budget_execution_owners')")
        }

    repeated = SqliteSafetyControlRepository(database_path=database, allowed_root=tmp_path)
    repeated.initialize()
    repeated.close()


def test_v7_migration_failure_rolls_back_drop_and_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migrations = _initialize_v6(tmp_path, monkeypatch)
    monkeypatch.setattr(control_module, "CONTROL_MIGRATIONS", migrations[:7])
    database = tmp_path / "control.sqlite3"
    original = SqliteSafetyControlRepository._migration_statements

    def broken_statements(script: str) -> tuple[str, ...]:
        return (*original(script), "SELECT * FROM synthetic_missing_table")

    monkeypatch.setattr(
        SqliteSafetyControlRepository,
        "_migration_statements",
        staticmethod(broken_statements),
    )
    broken = SqliteSafetyControlRepository(database_path=database, allowed_root=tmp_path)
    with pytest.raises(SafetyControlStorageError):
        broken.initialize()
    broken.close()

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (6,)
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone() == (6,)
        assert _CANDIDATE_INDEX in {
            row[1] for row in connection.execute("PRAGMA index_list('budget_execution_owners')")
        }

    monkeypatch.setattr(
        SqliteSafetyControlRepository,
        "_migration_statements",
        staticmethod(original),
    )
    retried = SqliteSafetyControlRepository(database_path=database, allowed_root=tmp_path)
    retried.initialize()
    retried.close()
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (7,)
        assert _CANDIDATE_INDEX not in {
            row[1] for row in connection.execute("PRAGMA index_list('budget_execution_owners')")
        }


@pytest.mark.parametrize("count", (100, 1_000, 10_000))
def test_v7_missing_npc_projection_remains_fail_closed_at_history_scale(
    tmp_path: Path,
    count: int,
) -> None:
    repository = make_repository(tmp_path)
    database = repository.database_path
    repository.close()
    now_ns = 1_800_000_000_000_000_000
    selected = BudgetScopeTags("a" * 64, "d" * 64, "b" * 64)
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        for index in range(count):
            execution_id = str(UUID(int=10_000_000 + index))
            connection.execute(
                "INSERT INTO execution_admissions VALUES (?,?,?,?,?,?,?)",
                (
                    execution_id,
                    str(UUID(int=20_000_000 + index)),
                    "f-009-safety-control-v1",
                    "a" * 64,
                    "b" * 64,
                    "c" * 64,
                    now_ns - index,
                ),
            )
            connection.execute(
                "INSERT INTO budget_execution_owners VALUES (?,?,?,?,?,?)",
                (
                    execution_id,
                    "f-009-budget-policy-v1",
                    "a" * 64,
                    "d" * 64,
                    "b" * 64,
                    now_ns - index,
                ),
            )
            connection.execute(
                "INSERT INTO budget_reservations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    execution_id,
                    1,
                    "f-009-budget-policy-v1",
                    "f-009-zero-cost-v1",
                    "fake",
                    "fake-model",
                    0,
                    0,
                    "reserved",
                    now_ns - index,
                    None,
                    None,
                    None,
                    None,
                ),
            )
        for scope_class, scope_tag in (
            ("player_npc", selected.player_npc_scope_tag),
            ("player", selected.player_scope_tag),
            ("global", "0" * 64),
        ):
            connection.execute(
                "INSERT INTO budget_window_totals VALUES (?,?,?,?,?,?,?,?,?,?)",
                (scope_class, scope_tag, 0, 0, 0, 1, now_ns, 0, 0, 0),
            )
        connection.execute(
            "INSERT INTO budget_window_projection_state VALUES (1,?,?,?,?,?,?)",
            (
                "f-009-budget-window-projection-v1",
                "f-009-budget-policy-v1",
                now_ns - 3_600_000_000_000,
                now_ns - 86_400_000_000_000,
                1,
                now_ns,
            ),
        )
        connection.commit()
        plan = tuple(
            str(row[3])
            for row in connection.execute(
                "EXPLAIN QUERY PLAN SELECT 1 FROM budget_reservations r "
                "JOIN budget_execution_owners o USING(execution_id) "
                "WHERE o.npc_scope_tag=? AND r.status<>'released' "
                "AND r.reserved_at_ns>? LIMIT 1",
                (selected.npc_scope_tag, now_ns - 86_400_000_000_000),
            )
        )
        with pytest.raises(SafetyControlStorageError):
            SqliteSafetyControlRepository._all_window_totals(
                connection,
                scope_tags=selected,
                now_ns=now_ns,
            )
    assert all(_CANDIDATE_INDEX not in line for line in plan)


def test_repository_rejects_outside_root_without_creating_database(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-control.sqlite3"

    with pytest.raises(ValueError):
        SqliteSafetyControlRepository(database_path=outside, allowed_root=tmp_path)

    assert not outside.exists()


def test_wrong_schema_fails_closed(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    with sqlite3.connect(repository.database_path) as connection:
        connection.execute("PRAGMA user_version = 99")

    with pytest.raises(SafetyControlStorageError):
        repository.initialize()


def test_corrupt_database_fails_closed_without_details(tmp_path: Path) -> None:
    database_path = tmp_path / "control.sqlite3"
    database_path.write_bytes(b"synthetic-not-a-sqlite-database")
    repository = SqliteSafetyControlRepository(
        database_path=database_path,
        allowed_root=tmp_path,
    )

    with pytest.raises(SafetyControlStorageError) as captured:
        repository.initialize()

    assert repr(captured.value) == "SafetyControlStorageError()"
    assert str(database_path) not in repr(captured.value)


def test_busy_database_fails_closed(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    with sqlite3.connect(repository.database_path) as blocker:
        blocker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(SafetyControlStorageError):
            repository.record_admission(
                execution_id=UUID("11111111-1111-4111-8111-111111111111"),
                request_id=UUID("22222222-2222-4222-8222-222222222222"),
                scope_tags=tags(),
                admitted_at_ns=1_800_000_000_000_000_000,
            )


def test_repository_rejects_reparse_database_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "control.sqlite3"
    original_is_junction = Path.is_junction

    def synthetic_junction(path: Path) -> bool:
        return path == database_path or original_is_junction(path)

    monkeypatch.setattr(Path, "is_junction", synthetic_junction)
    with pytest.raises(ValueError):
        SqliteSafetyControlRepository(
            database_path=database_path,
            allowed_root=tmp_path,
        )

    assert not database_path.exists()


def test_restart_marks_open_permits_abandoned_once(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    execution_id = UUID("11111111-1111-4111-8111-111111111111")
    request_id = UUID("22222222-2222-4222-8222-222222222222")
    repository.record_admission(
        execution_id=execution_id,
        request_id=request_id,
        scope_tags=tags(),
        admitted_at_ns=1_800_000_000_000_000_000,
    )
    assert repository.try_acquire_permit(
        execution_id=execution_id,
        scope_tags=tags(),
        acquired_at_ns=1_800_000_000_000_000_001,
    )

    rebuilt = SqliteSafetyControlRepository(
        database_path=repository.database_path,
        allowed_root=tmp_path,
    )
    rebuilt.initialize()
    assert rebuilt.recover_open_permits(now_ns=1_800_000_000_000_000_002) == 1
    assert rebuilt.recover_open_permits(now_ns=1_800_000_000_000_000_003) == 0
    assert rebuilt.active_permit_count() == 0


def test_permit_limits_and_release_are_atomic(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    first = UUID("11111111-1111-4111-8111-111111111111")
    second = UUID("22222222-2222-4222-8222-222222222222")
    third = UUID("33333333-3333-4333-8333-333333333333")
    first_tags = tags("a")
    second_tags = PermitScopeTags(
        player_scope_tag="a" * 64,
        player_npc_scope_tag="d" * 64,
        conversation_scope_tag="e" * 64,
    )
    third_tags = PermitScopeTags(
        player_scope_tag="f" * 64,
        player_npc_scope_tag="1" * 64,
        conversation_scope_tag="2" * 64,
    )
    for execution_id, request_id, scope_tags in (
        (first, UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"), first_tags),
        (second, UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), second_tags),
        (third, UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), third_tags),
    ):
        repository.record_admission(
            execution_id=execution_id,
            request_id=request_id,
            scope_tags=scope_tags,
            admitted_at_ns=1_800_000_000_000_000_000,
        )

    assert repository.try_acquire_permit(
        execution_id=first,
        scope_tags=first_tags,
        acquired_at_ns=1_800_000_000_000_000_001,
    )
    assert repository.try_acquire_permit(
        execution_id=second,
        scope_tags=second_tags,
        acquired_at_ns=1_800_000_000_000_000_002,
    )
    assert not repository.try_acquire_permit(
        execution_id=third,
        scope_tags=third_tags,
        acquired_at_ns=1_800_000_000_000_000_003,
    )
    assert repository.active_permit_count() == 2

    repository.release_permit(
        execution_id=first,
        released_at_ns=1_800_000_000_000_000_004,
        reason="completed",
    )
    assert repository.try_acquire_permit(
        execution_id=third,
        scope_tags=third_tags,
        acquired_at_ns=1_800_000_000_000_000_005,
    )
