"""Versioned SQLite repository for F-009 rate admission and provider permits."""

from __future__ import annotations

import hashlib
import math
import re
import sqlite3
import time
from collections.abc import Iterator, Sequence
from contextlib import closing, contextmanager
from pathlib import Path
from threading import local
from typing import Any, cast
from uuid import UUID

from cyber_town.application.budget import (
    ATTEMPT_WINDOW_SPECS,
    BUDGET_POLICY_VERSION,
    COST_WINDOW_SPECS,
    BudgetLimitClass,
    BudgetRejectedError,
    BudgetReservation,
    BudgetScopeTags,
    BudgetSettlement,
    PricingPolicy,
)
from cyber_town.application.control import (
    CONTROL_POLICY_VERSION,
    BucketConsumptionResult,
    BucketRequest,
    ControlRepositoryError,
    PermitScopeTags,
    retry_after_seconds,
)
from cyber_town.application.observability import ProviderKind
from cyber_town.application.provider import ProviderUsage
from cyber_town.application.retry import (
    BREAKER_FAILURE_THRESHOLD,
    BREAKER_FAILURE_WINDOW_SECONDS,
    BREAKER_OPEN_SECONDS,
    BREAKER_POLICY_VERSION,
    BREAKER_PROBE_SUCCESSES,
    BreakerDecision,
    BreakerFailureReason,
)
from cyber_town.application.safety import BreakerOutcome, BreakerState, RateLimitOutcome
from cyber_town.infrastructure.persistence.sqlite_connection import BoundedSqliteWriter

CONTROL_MIGRATIONS = (
    (1, "0001_safety_cost_control.sql"),
    (2, "0002_budget_cost_control.sql"),
    (3, "0003_retry_circuit_breaker.sql"),
    (4, "0004_leaf_table_storage_layout.sql"),
    (5, "0005_budget_window_projection.sql"),
    (6, "0006_control_execution_intent.sql"),
    (7, "0007_drop_redundant_budget_owner_npc_index.sql"),
    (8, "0008_budget_projection_integrity.sql"),
    (9, "0009_provider_permit_scope_storage.sql"),
)
_BUSY_TIMEOUT_MILLISECONDS = 2_000
_MICROTOKENS = 1_000_000
_REFILL_DENOMINATOR = 60_000_000_000
_PERMIT_RELEASE_REASONS = {
    "completed",
    "cancelled",
    "failed",
    "control_failure",
    "abandoned_after_restart",
}

_BUDGET_WINDOW_SCOPES = ("player_npc", "player", "npc", "global")
_BUDGET_PROJECTION_VERSION = "f-009-budget-window-projection-v1"
_GLOBAL_BUDGET_SCOPE_TAG = "0" * 64
_BUDGET_HOUR_NS = 3_600 * 1_000_000_000
_BUDGET_DAY_NS = 86_400 * 1_000_000_000
_EXECUTION_INTENT_POLICY_VERSION = "f-009-control-execution-intent-v1"

# Fixed SQL shapes only. Admission reads four projection rows and never scans
# the authoritative reservation ledger. The ledger is consulted only when a
# cutoff advances over newly expired rows or when the projection is rebuilt.
_BUDGET_WINDOW_TOTALS_SQL = (
    "WITH requested(scope_class,scope_tag,ordinal) AS (VALUES "
    "(?,?,0),(?,?,1),(?,?,2),(?,?,3)) "
    "SELECT requested.scope_class, t.scope_class IS NOT NULL, "
    "COALESCE(t.attempts_1h,0), COALESCE(t.attempts_24h,0), "
    "COALESCE(t.cost_24h_micro_usd,0), "
    "COALESCE(t.checked_attempts_1h,0), COALESCE(t.checked_attempts_24h,0), "
    "COALESCE(t.checked_cost_24h_micro_usd,0) FROM requested "
    "LEFT JOIN budget_window_totals t USING(scope_class,scope_tag) "
    "ORDER BY requested.ordinal"
)
_BUDGET_SCOPE_UPSERT_SQL = (
    "INSERT INTO budget_window_totals "
    "(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd,"
    "revision,updated_at_ns,checked_attempts_1h,checked_attempts_24h,"
    "checked_cost_24h_micro_usd) VALUES "
    + ",".join("(?,?,?,?,?,?,?,?,?,?)" for _ in range(4))
    + " ON CONFLICT(scope_class,scope_tag) DO UPDATE SET "
    "attempts_1h=budget_window_totals.attempts_1h+excluded.attempts_1h, "
    "attempts_24h=budget_window_totals.attempts_24h+excluded.attempts_24h, "
    "cost_24h_micro_usd="
    "budget_window_totals.cost_24h_micro_usd+excluded.cost_24h_micro_usd, "
    "checked_attempts_1h=budget_window_totals.checked_attempts_1h+excluded.checked_attempts_1h, "
    "checked_attempts_24h=budget_window_totals.checked_attempts_24h+excluded.checked_attempts_24h, "
    "checked_cost_24h_micro_usd="
    "budget_window_totals.checked_cost_24h_micro_usd+excluded.checked_cost_24h_micro_usd, "
    "revision=excluded.revision, updated_at_ns=excluded.updated_at_ns"
)
_BUDGET_SCOPE_UPDATE_SQL = (
    "WITH deltas(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h) AS (VALUES "
    + ",".join("(?,?,?,?,?)" for _ in range(4))
    + ") UPDATE budget_window_totals AS t SET "
    "attempts_1h=t.attempts_1h+d.attempts_1h, "
    "attempts_24h=t.attempts_24h+d.attempts_24h, "
    "cost_24h_micro_usd=t.cost_24h_micro_usd+d.cost_24h, "
    "checked_attempts_1h=t.checked_attempts_1h+d.attempts_1h, "
    "checked_attempts_24h=t.checked_attempts_24h+d.attempts_24h, "
    "checked_cost_24h_micro_usd=t.checked_cost_24h_micro_usd+d.cost_24h, "
    "revision=?, updated_at_ns=? FROM deltas AS d "
    "WHERE t.scope_class=d.scope_class AND t.scope_tag=d.scope_tag "
    "AND t.attempts_1h=t.checked_attempts_1h AND t.attempts_24h=t.checked_attempts_24h "
    "AND t.cost_24h_micro_usd=t.checked_cost_24h_micro_usd "
    "RETURNING scope_class,scope_tag"
)
_BUDGET_EXPIRATION_PROBE_SQL = (
    "SELECT 1 FROM budget_reservations WHERE status<>'released' AND "
    "((reserved_at_ns>? AND reserved_at_ns<=?) OR "
    "(reserved_at_ns>? AND reserved_at_ns<=?)) LIMIT 1"
)
_BUDGET_EXPIRATION_UPDATE_SQL = (
    "WITH expired AS ("
    "SELECT o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag,"
    "r.status,r.reserved_micro_usd,s.actual_cost_micro_usd,"
    "CASE WHEN r.reserved_at_ns>? AND r.reserved_at_ns<=? THEN 1 ELSE 0 END hour_expired,"
    "CASE WHEN r.reserved_at_ns>? AND r.reserved_at_ns<=? THEN 1 ELSE 0 END day_expired "
    "FROM budget_reservations r JOIN budget_execution_owners o USING(execution_id) "
    "LEFT JOIN budget_settlements s USING(execution_id,attempt_number) "
    "WHERE r.status<>'released' AND ((r.reserved_at_ns>? AND r.reserved_at_ns<=?) OR "
    "(r.reserved_at_ns>? AND r.reserved_at_ns<=?))"
    "), scoped(scope_class,scope_tag,cost,hour_expired,day_expired) AS ("
    "SELECT 'player_npc',player_npc_scope_tag,"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END,"
    "hour_expired,day_expired FROM expired UNION ALL "
    "SELECT 'player',player_scope_tag,"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END,"
    "hour_expired,day_expired FROM expired UNION ALL "
    "SELECT 'npc',npc_scope_tag,"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END,"
    "hour_expired,day_expired FROM expired UNION ALL "
    f"SELECT 'global','{_GLOBAL_BUDGET_SCOPE_TAG}',"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END,"
    "hour_expired,day_expired FROM expired"
    "), deltas AS ("
    "SELECT scope_class,scope_tag,-SUM(hour_expired) attempts_1h,"
    "-SUM(day_expired) attempts_24h,-SUM(cost*day_expired) cost_24h "
    "FROM scoped GROUP BY scope_class,scope_tag"
    ") UPDATE budget_window_totals AS t SET "
    "attempts_1h=t.attempts_1h+d.attempts_1h, "
    "attempts_24h=t.attempts_24h+d.attempts_24h, "
    "cost_24h_micro_usd=t.cost_24h_micro_usd+d.cost_24h, "
    "checked_attempts_1h=t.checked_attempts_1h+d.attempts_1h, "
    "checked_attempts_24h=t.checked_attempts_24h+d.attempts_24h, "
    "checked_cost_24h_micro_usd=t.checked_cost_24h_micro_usd+d.cost_24h, "
    "revision=?, updated_at_ns=? FROM deltas AS d "
    "WHERE t.scope_class=d.scope_class AND t.scope_tag=d.scope_tag "
    "AND NOT EXISTS (SELECT 1 FROM deltas AS required "
    "LEFT JOIN budget_window_totals AS existing "
    "ON existing.scope_class=required.scope_class AND existing.scope_tag=required.scope_tag "
    "WHERE existing.scope_class IS NULL "
    "OR existing.attempts_1h<>existing.checked_attempts_1h "
    "OR existing.attempts_24h<>existing.checked_attempts_24h "
    "OR existing.cost_24h_micro_usd<>existing.checked_cost_24h_micro_usd) "
    "RETURNING scope_class,scope_tag"
)


class SafetyControlStorageError(ControlRepositoryError):
    """Safe control storage failure with no database or scope details."""

    def __repr__(self) -> str:
        return "SafetyControlStorageError()"


class _ComposedTransactionConnection:
    """Map existing transaction-owning methods to savepoints in one short commit."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._sequence = 0
        self._savepoints: list[str] = []

    @property
    def row_factory(self) -> Any:
        return self._connection.row_factory

    @row_factory.setter
    def row_factory(self, value: Any) -> None:
        self._connection.row_factory = value

    def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor:
        if sql.lstrip().upper().startswith("BEGIN"):
            self._sequence += 1
            name = f"f009_control_{self._sequence}"
            self._connection.execute(f"SAVEPOINT {name}")
            self._savepoints.append(name)
            return self._connection.execute("SELECT 1 WHERE 0")
        return self._connection.execute(sql, parameters)

    def commit(self) -> None:
        if not self._savepoints:
            raise sqlite3.OperationalError("Safety control transaction is unavailable")
        self._connection.execute(f"RELEASE SAVEPOINT {self._savepoints.pop()}")

    def rollback(self) -> None:
        if not self._savepoints:
            return
        name = self._savepoints.pop()
        self._connection.execute(f"ROLLBACK TO SAVEPOINT {name}")
        self._connection.execute(f"RELEASE SAVEPOINT {name}")

    def close(self) -> None:
        if self._savepoints:
            raise sqlite3.OperationalError("Safety control transaction is incomplete")
        return None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


class SqliteSafetyControlRepository:
    """Persist only HMAC-tagged bucket and permit metadata."""

    def __init__(self, *, database_path: Path, allowed_root: Path) -> None:
        if not isinstance(database_path, Path) or not isinstance(allowed_root, Path):
            raise TypeError("Safety control database boundaries must be paths")
        resolved_root = allowed_root.resolve(strict=False)
        resolved_database = database_path.resolve(strict=False)
        if not resolved_database.is_relative_to(resolved_root):
            raise ValueError("Safety control database must stay inside its approved root")
        if resolved_database.suffix != ".sqlite3":
            raise ValueError("Safety control database must use an approved SQLite filename")
        if not resolved_root.is_dir() or not resolved_database.parent.is_dir():
            raise ValueError("Safety control database parent must already exist")
        for current in (database_path, *database_path.parents):
            if current.is_symlink() or current.is_junction():
                raise ValueError("Safety control database must not traverse linked paths")
            if current.resolve(strict=False) == resolved_root:
                break
        self.database_path = resolved_database
        self._allowed_root = resolved_root
        self._busy_timeout_milliseconds = _BUSY_TIMEOUT_MILLISECONDS
        self._writer = BoundedSqliteWriter(
            resolved_database, trusted_schema=False, allowed_root=resolved_root
        )
        self._composed = local()

    def __repr__(self) -> str:
        return "SqliteSafetyControlRepository()"

    def initialize(self) -> None:
        migrations: list[tuple[int, str, str, str]] = []
        for version, name in CONTROL_MIGRATIONS:
            migration_path = Path(__file__).parent / "migrations" / name
            try:
                migration_bytes = migration_path.read_bytes()
                migration = migration_bytes.decode("utf-8")
            except (OSError, UnicodeDecodeError) as error:
                raise SafetyControlStorageError from error
            migrations.append(
                (version, name, hashlib.sha256(migration_bytes).hexdigest(), migration)
            )
        try:
            with closing(self._connect()) as connection:
                if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
                    raise SafetyControlStorageError
                existing_tables = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table' "
                        "AND name NOT LIKE 'sqlite_%'"
                    )
                }
                if existing_tables and "schema_migrations" not in existing_tables:
                    raise SafetyControlStorageError
                if CONTROL_MIGRATIONS[-1][0] >= 9 and connection.execute(
                    "SELECT typeof(unhex('00ff')), length(unhex('00ff'))"
                ).fetchone() != ("blob", 2):
                    raise SafetyControlStorageError
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        "CREATE TABLE IF NOT EXISTS schema_migrations ("
                        "version INTEGER PRIMARY KEY CHECK (version > 0), "
                        "name TEXT NOT NULL UNIQUE, "
                        "checksum TEXT NOT NULL CHECK (length(checksum) = 64), "
                        "applied_at_ns INTEGER NOT NULL CHECK (applied_at_ns > 0)"
                        ") STRICT"
                    )
                    existing = connection.execute(
                        "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
                    ).fetchall()
                    expected = [item[:3] for item in migrations]
                    if existing != expected[: len(existing)]:
                        raise SafetyControlStorageError
                    for version, name, checksum, migration in migrations[len(existing) :]:
                        for statement in self._migration_statements(migration):
                            connection.execute(statement)
                        connection.execute(
                            "INSERT INTO schema_migrations "
                            "(version, name, checksum, applied_at_ns) VALUES (?, ?, ?, ?)",
                            (version, name, checksum, time.time_ns()),
                        )
                    if connection.execute("PRAGMA user_version").fetchone() != (
                        CONTROL_MIGRATIONS[-1][0],
                    ):
                        raise SafetyControlStorageError
                    self._validate_tables(connection)
                    connection.commit()
                except (sqlite3.Error, SafetyControlStorageError):
                    connection.rollback()
                    raise
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def consume_ingress(
        self,
        *,
        buckets: Sequence[BucketRequest],
        now_ns: int,
    ) -> BucketConsumptionResult:
        return self._consume(buckets=buckets, now_ns=now_ns)

    def consume_execution_admission(
        self,
        *,
        buckets: Sequence[BucketRequest],
        execution_id: UUID,
        request_id: UUID,
        scope_tags: PermitScopeTags,
        now_ns: int,
    ) -> BucketConsumptionResult:
        self._require_admission(execution_id, request_id, scope_tags, now_ns)
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    existing = connection.execute(
                        "SELECT * FROM execution_admissions WHERE execution_id = ?",
                        (str(execution_id),),
                    ).fetchone()
                    if existing is not None:
                        if not self._admission_matches(
                            existing,
                            request_id=request_id,
                            scope_tags=scope_tags,
                        ):
                            raise SafetyControlStorageError
                        connection.commit()
                        return BucketConsumptionResult(RateLimitOutcome.ALLOWED, None)
                    decision = self._consume_in_transaction(
                        connection,
                        buckets=buckets,
                        now_ns=now_ns,
                    )
                    if decision.outcome is RateLimitOutcome.REJECTED:
                        connection.rollback()
                        return decision
                    self._insert_admission(
                        connection,
                        execution_id=execution_id,
                        request_id=request_id,
                        scope_tags=scope_tags,
                        admitted_at_ns=now_ns,
                    )
                    connection.commit()
                    return decision
                except (sqlite3.Error, SafetyControlStorageError):
                    connection.rollback()
                    raise
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def record_admission(
        self,
        *,
        execution_id: UUID,
        request_id: UUID,
        scope_tags: PermitScopeTags,
        admitted_at_ns: int,
    ) -> None:
        self._require_admission(execution_id, request_id, scope_tags, admitted_at_ns)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_admission(
                    connection,
                    execution_id=execution_id,
                    request_id=request_id,
                    scope_tags=scope_tags,
                    admitted_at_ns=admitted_at_ns,
                )
                connection.commit()
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def try_acquire_permit(
        self,
        *,
        execution_id: UUID,
        scope_tags: PermitScopeTags,
        acquired_at_ns: int,
    ) -> bool:
        if not isinstance(execution_id, UUID) or not isinstance(scope_tags, PermitScopeTags):
            raise TypeError("Safety control permit metadata is invalid")
        self._require_time(acquired_at_ns)
        encoded_scopes = self._permit_scope_bytes(scope_tags)
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    admission = connection.execute(
                        "SELECT * FROM execution_admissions WHERE execution_id = ?",
                        (str(execution_id),),
                    ).fetchone()
                    if admission is None or not self._scope_matches(admission, scope_tags):
                        raise SafetyControlStorageError
                    existing = connection.execute(
                        "SELECT * FROM provider_permits WHERE execution_id = ?",
                        (str(execution_id),),
                    ).fetchone()
                    if existing is not None:
                        if not self._permit_scope_matches(existing, encoded_scopes):
                            raise SafetyControlStorageError
                        if existing["released_at_ns"] is None:
                            connection.commit()
                            return True
                        connection.commit()
                        return False
                    counts = connection.execute(
                        "SELECT COUNT(*), "
                        "SUM(CASE WHEN player_scope_tag = ? THEN 1 ELSE 0 END), "
                        "SUM(CASE WHEN player_npc_scope_tag = ? THEN 1 ELSE 0 END), "
                        "SUM(CASE WHEN conversation_scope_tag = ? THEN 1 ELSE 0 END) "
                        "FROM provider_permits WHERE released_at_ns IS NULL",
                        encoded_scopes,
                    ).fetchone()
                    global_count, player_count, player_npc_count, conversation_count = (
                        int(value or 0) for value in counts
                    )
                    if (
                        global_count >= 2
                        or player_count >= 2
                        or player_npc_count >= 1
                        or conversation_count >= 1
                    ):
                        connection.commit()
                        return False
                    connection.execute(
                        "INSERT INTO provider_permits ("
                        "execution_id, policy_version, player_scope_tag, "
                        "player_npc_scope_tag, conversation_scope_tag, acquired_at_ns"
                        ") VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            str(execution_id),
                            CONTROL_POLICY_VERSION,
                            *encoded_scopes,
                            acquired_at_ns,
                        ),
                    )
                    connection.commit()
                    return True
                except (sqlite3.Error, SafetyControlStorageError):
                    connection.rollback()
                    raise
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def release_permit(
        self,
        *,
        execution_id: UUID,
        released_at_ns: int,
        reason: str,
    ) -> None:
        if not isinstance(execution_id, UUID):
            raise TypeError("Safety control permit identifier is invalid")
        self._require_time(released_at_ns)
        if reason not in _PERMIT_RELEASE_REASONS:
            raise ValueError("Safety control permit release reason is invalid")
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT released_at_ns FROM provider_permits WHERE execution_id = ?",
                    (str(execution_id),),
                ).fetchone()
                if row is None:
                    connection.rollback()
                    raise SafetyControlStorageError
                if row[0] is None:
                    connection.execute(
                        "UPDATE provider_permits SET released_at_ns = ?, release_reason = ? "
                        "WHERE execution_id = ? AND released_at_ns IS NULL",
                        (released_at_ns, reason, str(execution_id)),
                    )
                connection.commit()
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def recover_open_permits(self, *, now_ns: int) -> int:
        self._require_time(now_ns)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    "UPDATE provider_permits SET released_at_ns = ?, "
                    "release_reason = 'abandoned_after_restart' "
                    "WHERE released_at_ns IS NULL",
                    (now_ns,),
                )
                connection.commit()
                return cursor.rowcount
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def recover_open_execution_intents(self, *, now_ns: int) -> int:
        """Conservatively settle every durable intent with an unknown receipt."""

        self._require_time(now_ns)
        with self._composed_transaction() as connection:
            connection.row_factory = sqlite3.Row
            try:
                rows = connection.execute(
                    "SELECT i.execution_id,i.attempt_number,i.created_at_ns,r.status,"
                    "r.policy_version,r.pricing_version,r.reserved_micro_usd "
                    "FROM control_execution_intents i JOIN budget_reservations r "
                    "USING(execution_id,attempt_number) WHERE i.state='dispatch_intent' "
                    "ORDER BY i.execution_id,i.attempt_number"
                ).fetchall()
                for row in rows:
                    status = str(row["status"])
                    if status == "reserved":
                        connection.execute(
                            "UPDATE budget_reservations SET status='dispatched', "
                            "dispatched_at_ns=? WHERE execution_id=? AND attempt_number=? "
                            "AND status='reserved'",
                            (int(row["created_at_ns"]), row["execution_id"], row["attempt_number"]),
                        )
                    elif status != "dispatched":
                        raise SafetyControlStorageError
                    connection.execute(
                        "INSERT INTO budget_settlements ("
                        "execution_id,attempt_number,policy_version,pricing_version,"
                        "reserved_micro_usd,actual_cost_micro_usd,released_micro_usd,"
                        "prompt_tokens,completion_tokens,conservative,reason,settled_at_ns"
                        ") VALUES (?,?,?,?,?,?,0,0,0,1,'abandoned_after_restart',?)",
                        (
                            row["execution_id"],
                            row["attempt_number"],
                            row["policy_version"],
                            row["pricing_version"],
                            row["reserved_micro_usd"],
                            row["reserved_micro_usd"],
                            now_ns,
                        ),
                    )
                    connection.execute(
                        "UPDATE budget_reservations SET status='settled',settled_at_ns=? "
                        "WHERE execution_id=? AND attempt_number=? AND status='dispatched'",
                        (now_ns, row["execution_id"], row["attempt_number"]),
                    )
                    connection.execute(
                        "UPDATE provider_permits SET released_at_ns=?,"
                        "release_reason='abandoned_after_restart' "
                        "WHERE execution_id=? AND released_at_ns IS NULL",
                        (now_ns, row["execution_id"]),
                    )
                    connection.execute(
                        "DELETE FROM breaker_probe_leases WHERE execution_id=?",
                        (row["execution_id"],),
                    )
                    changed = connection.execute(
                        "UPDATE control_execution_intents SET state='settled',conservative=1,"
                        "finalized_at_ns=?,terminal_reason='abandoned_after_restart',"
                        "revision=revision+1 WHERE execution_id=? AND attempt_number=? "
                        "AND state='dispatch_intent'",
                        (now_ns, row["execution_id"], row["attempt_number"]),
                    ).rowcount
                    if changed != 1:
                        raise SafetyControlStorageError
                if rows:
                    self._rebuild_budget_projection(connection, now_ns=now_ns)
                connection.commit()
                return len(rows)
            except (sqlite3.Error, ControlRepositoryError) as error:
                connection.rollback()
                if isinstance(error, ControlRepositoryError):
                    raise
                raise SafetyControlStorageError from error

    def recover_open_budget_attempts(self, *, now_ns: int) -> tuple[int, int]:
        self._require_time(now_ns)
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    dispatched = connection.execute(
                        "SELECT * FROM budget_reservations WHERE status = 'dispatched'"
                    ).fetchall()
                    for row in dispatched:
                        connection.execute(
                            "INSERT INTO budget_settlements ("
                            "execution_id, attempt_number, policy_version, pricing_version, "
                            "reserved_micro_usd, actual_cost_micro_usd, released_micro_usd, "
                            "prompt_tokens, completion_tokens, conservative, reason, "
                            "settled_at_ns) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 1, "
                            "'abandoned_after_restart', ?)",
                            (
                                row["execution_id"],
                                row["attempt_number"],
                                row["policy_version"],
                                row["pricing_version"],
                                row["reserved_micro_usd"],
                                row["reserved_micro_usd"],
                                now_ns,
                            ),
                        )
                    settled_count = connection.execute(
                        "UPDATE budget_reservations SET status = 'settled', settled_at_ns = ? "
                        "WHERE status = 'dispatched'",
                        (now_ns,),
                    ).rowcount
                    released_count = connection.execute(
                        "UPDATE budget_reservations SET status = 'released', released_at_ns = ?, "
                        "release_reason = 'cancelled_before_dispatch' WHERE status = 'reserved'",
                        (now_ns,),
                    ).rowcount
                    self._rebuild_budget_projection(connection, now_ns=now_ns)
                    connection.commit()
                    return released_count, settled_count
                except sqlite3.Error:
                    connection.rollback()
                    raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def recover_open_breaker_probes(self, *, now_ns: int) -> int:
        self._require_time(now_ns)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute("DELETE FROM breaker_probe_leases")
                connection.execute(
                    "UPDATE circuit_breakers SET updated_at_ns = ? WHERE state = 'half_open'",
                    (now_ns,),
                )
                connection.commit()
                return cursor.rowcount
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def check_breaker(
        self,
        *,
        execution_id: UUID,
        scope_tag: str,
        now_ns: int,
    ) -> BreakerDecision:
        self._require_breaker_inputs(execution_id, scope_tag, now_ns)
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    row = connection.execute(
                        "SELECT * FROM circuit_breakers WHERE scope_tag = ?", (scope_tag,)
                    ).fetchone()
                    if row is None:
                        connection.execute(
                            "INSERT INTO circuit_breakers (scope_tag, policy_version, state, "
                            "failure_count, failure_window_started_ns, open_until_ns, "
                            "probe_success_count, updated_at_ns) "
                            "VALUES (?, ?, 'closed', 0, NULL, NULL, 0, ?)",
                            (scope_tag, BREAKER_POLICY_VERSION, now_ns),
                        )
                        connection.commit()
                        return BreakerDecision(BreakerState.CLOSED, BreakerOutcome.ALLOWED)

                    state = BreakerState(str(row["state"]))
                    if state is BreakerState.CLOSED:
                        connection.commit()
                        return BreakerDecision(state, BreakerOutcome.ALLOWED)
                    if state is BreakerState.OPEN:
                        open_until_ns = int(row["open_until_ns"])
                        if now_ns < open_until_ns:
                            retry_after = min(
                                BREAKER_OPEN_SECONDS,
                                max(1, math.ceil((open_until_ns - now_ns) / 1_000_000_000)),
                            )
                            connection.commit()
                            return BreakerDecision(state, BreakerOutcome.REJECTED, retry_after)
                        connection.execute(
                            "UPDATE circuit_breakers SET state = 'half_open', failure_count = 0, "
                            "failure_window_started_ns = NULL, open_until_ns = NULL, "
                            "probe_success_count = 0, updated_at_ns = ? WHERE scope_tag = ?",
                            (now_ns, scope_tag),
                        )
                        state = BreakerState.HALF_OPEN

                    lease = connection.execute(
                        "SELECT execution_id FROM breaker_probe_leases WHERE scope_tag = ?",
                        (scope_tag,),
                    ).fetchone()
                    if lease is not None:
                        if str(lease["execution_id"]) == str(execution_id):
                            connection.commit()
                            return BreakerDecision(state, BreakerOutcome.PROBE_ALLOWED)
                        connection.commit()
                        return BreakerDecision(state, BreakerOutcome.REJECTED, 1)
                    connection.execute(
                        "INSERT INTO breaker_probe_leases "
                        "(scope_tag, execution_id, acquired_at_ns) VALUES (?, ?, ?)",
                        (scope_tag, str(execution_id), now_ns),
                    )
                    connection.commit()
                    return BreakerDecision(state, BreakerOutcome.PROBE_ALLOWED)
                except (sqlite3.Error, ValueError):
                    connection.rollback()
                    raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def record_breaker_result(
        self,
        *,
        execution_id: UUID,
        scope_tag: str,
        success: bool,
        failure_reason: BreakerFailureReason | None,
        now_ns: int,
    ) -> BreakerDecision:
        self._require_breaker_inputs(execution_id, scope_tag, now_ns)
        if type(success) is not bool:
            raise TypeError("Circuit-breaker result is invalid")
        if success:
            if failure_reason is not None:
                raise ValueError("Successful circuit-breaker result cannot carry a reason")
        elif not isinstance(failure_reason, BreakerFailureReason):
            raise TypeError("Circuit-breaker failure reason is invalid")
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    existing = connection.execute(
                        "SELECT outcome FROM breaker_execution_results WHERE execution_id = ?",
                        (str(execution_id),),
                    ).fetchone()
                    row = connection.execute(
                        "SELECT * FROM circuit_breakers WHERE scope_tag = ?", (scope_tag,)
                    ).fetchone()
                    if row is None:
                        connection.execute(
                            "INSERT INTO circuit_breakers (scope_tag, policy_version, state, "
                            "failure_count, failure_window_started_ns, open_until_ns, "
                            "probe_success_count, updated_at_ns) "
                            "VALUES (?, ?, 'closed', 0, NULL, NULL, 0, ?)",
                            (scope_tag, BREAKER_POLICY_VERSION, now_ns),
                        )
                        row = connection.execute(
                            "SELECT * FROM circuit_breakers WHERE scope_tag = ?", (scope_tag,)
                        ).fetchone()
                    assert row is not None
                    state = BreakerState(str(row["state"]))
                    if existing is not None:
                        connection.commit()
                        return BreakerDecision(state, BreakerOutcome.NOT_REACHED)

                    connection.execute(
                        "INSERT INTO breaker_execution_results "
                        "(execution_id, scope_tag, outcome, failure_reason, recorded_at_ns) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            str(execution_id),
                            scope_tag,
                            "success" if success else "failure",
                            None if failure_reason is None else failure_reason.value,
                            now_ns,
                        ),
                    )
                    lease = connection.execute(
                        "SELECT execution_id FROM breaker_probe_leases WHERE scope_tag = ?",
                        (scope_tag,),
                    ).fetchone()
                    owns_probe = lease is not None and str(lease["execution_id"]) == str(
                        execution_id
                    )
                    transitioned = False
                    if state is BreakerState.CLOSED:
                        if success:
                            connection.execute(
                                "UPDATE circuit_breakers SET failure_count = 0, "
                                "failure_window_started_ns = NULL, probe_success_count = 0, "
                                "updated_at_ns = ? WHERE scope_tag = ?",
                                (now_ns, scope_tag),
                            )
                        else:
                            window_started = row["failure_window_started_ns"]
                            if (
                                window_started is None
                                or now_ns - int(window_started)
                                > BREAKER_FAILURE_WINDOW_SECONDS * 1_000_000_000
                            ):
                                failure_count = 1
                                window_started = now_ns
                            else:
                                failure_count = int(row["failure_count"]) + 1
                            if failure_count >= BREAKER_FAILURE_THRESHOLD:
                                state = BreakerState.OPEN
                                transitioned = True
                                connection.execute(
                                    "UPDATE circuit_breakers SET state = 'open', "
                                    "failure_count = ?, failure_window_started_ns = ?, "
                                    "open_until_ns = ?, probe_success_count = 0, "
                                    "updated_at_ns = ? WHERE scope_tag = ?",
                                    (
                                        BREAKER_FAILURE_THRESHOLD,
                                        int(window_started),
                                        now_ns + BREAKER_OPEN_SECONDS * 1_000_000_000,
                                        now_ns,
                                        scope_tag,
                                    ),
                                )
                            else:
                                connection.execute(
                                    "UPDATE circuit_breakers SET failure_count = ?, "
                                    "failure_window_started_ns = ?, updated_at_ns = ? "
                                    "WHERE scope_tag = ?",
                                    (failure_count, int(window_started), now_ns, scope_tag),
                                )
                    elif state is BreakerState.HALF_OPEN and owns_probe:
                        connection.execute(
                            "DELETE FROM breaker_probe_leases WHERE scope_tag = ? "
                            "AND execution_id = ?",
                            (scope_tag, str(execution_id)),
                        )
                        if success:
                            successes = int(row["probe_success_count"]) + 1
                            if successes >= BREAKER_PROBE_SUCCESSES:
                                state = BreakerState.CLOSED
                                transitioned = True
                                connection.execute(
                                    "UPDATE circuit_breakers SET state = 'closed', "
                                    "failure_count = 0, failure_window_started_ns = NULL, "
                                    "open_until_ns = NULL, probe_success_count = 0, "
                                    "updated_at_ns = ? WHERE scope_tag = ?",
                                    (now_ns, scope_tag),
                                )
                            else:
                                connection.execute(
                                    "UPDATE circuit_breakers SET probe_success_count = ?, "
                                    "updated_at_ns = ? WHERE scope_tag = ?",
                                    (successes, now_ns, scope_tag),
                                )
                        else:
                            state = BreakerState.OPEN
                            transitioned = True
                            connection.execute(
                                "UPDATE circuit_breakers SET state = 'open', failure_count = 0, "
                                "failure_window_started_ns = NULL, open_until_ns = ?, "
                                "probe_success_count = 0, updated_at_ns = ? WHERE scope_tag = ?",
                                (
                                    now_ns + BREAKER_OPEN_SECONDS * 1_000_000_000,
                                    now_ns,
                                    scope_tag,
                                ),
                            )
                    connection.commit()
                    return BreakerDecision(
                        state,
                        BreakerOutcome.TRANSITIONED if transitioned else BreakerOutcome.ALLOWED,
                    )
                except (sqlite3.Error, ValueError):
                    connection.rollback()
                    raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def release_breaker_probe(
        self,
        *,
        execution_id: UUID,
        scope_tag: str,
        now_ns: int,
    ) -> None:
        self._require_breaker_inputs(execution_id, scope_tag, now_ns)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "DELETE FROM breaker_probe_leases WHERE scope_tag = ? AND execution_id = ?",
                    (scope_tag, str(execution_id)),
                )
                connection.execute(
                    "UPDATE circuit_breakers SET updated_at_ns = ? WHERE scope_tag = ?",
                    (now_ns, scope_tag),
                )
                connection.commit()
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def reserve_budget(
        self,
        *,
        execution_id: UUID,
        attempt_number: int,
        scope_tags: BudgetScopeTags,
        pricing_policy: PricingPolicy,
        now_ns: int,
    ) -> BudgetReservation:
        self._require_budget_inputs(
            execution_id,
            attempt_number,
            scope_tags,
            pricing_policy,
            now_ns,
        )
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    existing = connection.execute(
                        "SELECT r.*, o.player_scope_tag, o.npc_scope_tag, "
                        "o.player_npc_scope_tag FROM budget_reservations r "
                        "JOIN budget_execution_owners o USING (execution_id) "
                        "WHERE r.execution_id = ? AND r.attempt_number = ?",
                        (str(execution_id), attempt_number),
                    ).fetchone()
                    if existing is not None:
                        reservation = self._reservation_from_row(existing, scope_tags)
                        if (
                            reservation.pricing_version != pricing_policy.version
                            or reservation.reserved_micro_usd
                            != pricing_policy.max_reservation_micro_usd
                        ):
                            raise SafetyControlStorageError
                        connection.commit()
                        return reservation

                    admission = connection.execute(
                        "SELECT * FROM execution_admissions WHERE execution_id = ?",
                        (str(execution_id),),
                    ).fetchone()
                    if admission is None or not self._budget_admission_matches(
                        admission,
                        scope_tags,
                    ):
                        raise SafetyControlStorageError
                    owner = connection.execute(
                        "SELECT * FROM budget_execution_owners WHERE execution_id = ?",
                        (str(execution_id),),
                    ).fetchone()
                    if owner is None:
                        connection.execute(
                            "INSERT INTO budget_execution_owners ("
                            "execution_id, policy_version, player_scope_tag, npc_scope_tag, "
                            "player_npc_scope_tag, created_at_ns) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                str(execution_id),
                                BUDGET_POLICY_VERSION,
                                scope_tags.player_scope_tag,
                                scope_tags.npc_scope_tag,
                                scope_tags.player_npc_scope_tag,
                                now_ns,
                            ),
                        )
                    elif not self._budget_owner_matches(owner, scope_tags):
                        raise SafetyControlStorageError

                    existing_attempts = int(
                        connection.execute(
                            "SELECT COUNT(*) FROM budget_reservations "
                            "WHERE execution_id = ? AND status <> 'released'",
                            (str(execution_id),),
                        ).fetchone()[0]
                    )
                    if existing_attempts >= 2 or attempt_number != existing_attempts + 1:
                        raise BudgetRejectedError(
                            BudgetLimitClass.EXECUTION_ATTEMPTS,
                            scope_tags=scope_tags,
                            pricing_policy=pricing_policy,
                        )

                    warning = False
                    # Transaction-local only: one consistent snapshot for all scopes, no
                    # cross-request cache or change to rejection precedence.
                    _, _, projection_revision = self._advance_budget_projection(
                        connection,
                        now_ns=now_ns,
                    )
                    windows = self._all_window_totals(
                        connection, scope_tags=scope_tags, now_ns=now_ns
                    )
                    for spec in ATTEMPT_WINDOW_SPECS:
                        scope = spec.limit_class.value.rsplit("_attempts_", 1)[0]
                        count = windows[scope][0 if spec.window_seconds == 3_600 else 1]
                        if count >= spec.hard_limit:
                            raise BudgetRejectedError(
                                spec.limit_class,
                                scope_tags=scope_tags,
                                pricing_policy=pricing_policy,
                            )
                        warning = warning or count + 1 >= spec.warning_threshold
                    for spec in COST_WINDOW_SPECS:
                        scope = spec.limit_class.value.rsplit("_cost_", 1)[0]
                        cost = windows[scope][2]
                        proposed = cost + pricing_policy.max_reservation_micro_usd
                        if proposed > spec.hard_limit:
                            raise BudgetRejectedError(
                                spec.limit_class,
                                scope_tags=scope_tags,
                                pricing_policy=pricing_policy,
                            )
                        warning = warning or proposed >= spec.warning_threshold

                    connection.execute(
                        "INSERT INTO budget_reservations ("
                        "execution_id, attempt_number, policy_version, pricing_version, "
                        "provider_kind, provider_model, reserved_micro_usd, soft_warning, "
                        "status, reserved_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'reserved', ?)",
                        (
                            str(execution_id),
                            attempt_number,
                            BUDGET_POLICY_VERSION,
                            pricing_policy.version,
                            pricing_policy.provider_kind.value,
                            pricing_policy.model,
                            pricing_policy.max_reservation_micro_usd,
                            int(warning),
                            now_ns,
                        ),
                    )
                    self._apply_budget_projection_deltas(
                        connection,
                        deltas=tuple(
                            (
                                scope_class,
                                scope_tag,
                                1,
                                1,
                                pricing_policy.max_reservation_micro_usd,
                            )
                            for scope_class, scope_tag in self._budget_scope_pairs(scope_tags)
                        ),
                        revision=projection_revision,
                        now_ns=now_ns,
                    )
                    connection.commit()
                    return BudgetReservation(
                        execution_id=execution_id,
                        attempt_number=attempt_number,
                        policy_version=BUDGET_POLICY_VERSION,
                        pricing_version=pricing_policy.version,
                        provider_kind=pricing_policy.provider_kind,
                        reserved_micro_usd=pricing_policy.max_reservation_micro_usd,
                        soft_warning=warning,
                        scope_tags=scope_tags,
                    )
                except (sqlite3.Error, SafetyControlStorageError, BudgetRejectedError):
                    connection.rollback()
                    raise
        except (SafetyControlStorageError, BudgetRejectedError):
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def mark_budget_dispatched(self, *, reservation: BudgetReservation, now_ns: int) -> None:
        self._require_reservation(reservation)
        self._require_time(now_ns)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT status FROM budget_reservations "
                    "WHERE execution_id = ? AND attempt_number = ?",
                    (str(reservation.execution_id), reservation.attempt_number),
                ).fetchone()
                if row is None or row[0] == "released":
                    connection.rollback()
                    raise SafetyControlStorageError
                if row[0] == "reserved":
                    connection.execute(
                        "UPDATE budget_reservations SET status = 'dispatched', "
                        "dispatched_at_ns = ? WHERE execution_id = ? AND attempt_number = ? "
                        "AND status = 'reserved'",
                        (now_ns, str(reservation.execution_id), reservation.attempt_number),
                    )
                connection.commit()
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def settle_budget(
        self,
        *,
        reservation: BudgetReservation,
        usage: ProviderUsage | None,
        actual_cost_micro_usd: int,
        conservative: bool,
        reason: str,
        now_ns: int,
    ) -> BudgetSettlement:
        self._require_reservation(reservation)
        self._require_time(now_ns)
        if type(actual_cost_micro_usd) is not int or not (
            0 <= actual_cost_micro_usd <= reservation.reserved_micro_usd
        ):
            raise ValueError("Budget settlement cost is invalid")
        if type(conservative) is not bool:
            raise TypeError("Budget settlement mode is invalid")
        prompt_tokens = 0 if usage is None else usage.prompt_tokens
        completion_tokens = 0 if usage is None else usage.completion_tokens
        released = reservation.reserved_micro_usd - actual_cost_micro_usd
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    existing = connection.execute(
                        "SELECT * FROM budget_settlements WHERE execution_id = ? "
                        "AND attempt_number = ?",
                        (str(reservation.execution_id), reservation.attempt_number),
                    ).fetchone()
                    if existing is not None:
                        settlement = self._settlement_from_row(existing)
                        if (
                            settlement.actual_cost_micro_usd != actual_cost_micro_usd
                            or settlement.prompt_tokens != prompt_tokens
                            or settlement.completion_tokens != completion_tokens
                            or settlement.conservative != conservative
                        ):
                            raise SafetyControlStorageError
                        connection.commit()
                        return settlement
                    row = connection.execute(
                        "SELECT r.status,r.reserved_micro_usd,r.pricing_version,r.reserved_at_ns,"
                        "o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag "
                        "FROM budget_reservations r JOIN budget_execution_owners o "
                        "USING(execution_id) WHERE r.execution_id=? AND r.attempt_number=?",
                        (str(reservation.execution_id), reservation.attempt_number),
                    ).fetchone()
                    if row is not None and row["status"] == "reserved":
                        intent = connection.execute(
                            "SELECT state FROM control_execution_intents "
                            "WHERE execution_id=? AND attempt_number=?",
                            (str(reservation.execution_id), reservation.attempt_number),
                        ).fetchone()
                        if intent is not None and intent["state"] == "dispatch_intent":
                            connection.execute(
                                "UPDATE budget_reservations SET status='dispatched',"
                                "dispatched_at_ns=? WHERE execution_id=? AND attempt_number=? "
                                "AND status='reserved'",
                                (now_ns, str(reservation.execution_id), reservation.attempt_number),
                            )
                            row = connection.execute(
                                "SELECT r.status,r.reserved_micro_usd,r.pricing_version,"
                                "r.reserved_at_ns,o.player_scope_tag,o.npc_scope_tag,"
                                "o.player_npc_scope_tag FROM budget_reservations r "
                                "JOIN budget_execution_owners o USING(execution_id) "
                                "WHERE r.execution_id=? AND r.attempt_number=?",
                                (str(reservation.execution_id), reservation.attempt_number),
                            ).fetchone()
                    if (
                        row is None
                        or row["status"] != "dispatched"
                        or int(row["reserved_micro_usd"]) != reservation.reserved_micro_usd
                        or row["pricing_version"] != reservation.pricing_version
                    ):
                        raise SafetyControlStorageError
                    _, day_cutoff, projection_revision = self._advance_budget_projection(
                        connection,
                        now_ns=now_ns,
                    )
                    connection.execute(
                        "INSERT INTO budget_settlements ("
                        "execution_id, attempt_number, policy_version, pricing_version, "
                        "reserved_micro_usd, actual_cost_micro_usd, released_micro_usd, "
                        "prompt_tokens, completion_tokens, conservative, reason, settled_at_ns"
                        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            str(reservation.execution_id),
                            reservation.attempt_number,
                            reservation.policy_version,
                            reservation.pricing_version,
                            reservation.reserved_micro_usd,
                            actual_cost_micro_usd,
                            released,
                            prompt_tokens,
                            completion_tokens,
                            int(conservative),
                            reason,
                            now_ns,
                        ),
                    )
                    connection.execute(
                        "UPDATE budget_reservations SET status = 'settled', settled_at_ns = ? "
                        "WHERE execution_id = ? AND attempt_number = ? AND status = 'dispatched'",
                        (now_ns, str(reservation.execution_id), reservation.attempt_number),
                    )
                    intent = connection.execute(
                        "SELECT state FROM control_execution_intents "
                        "WHERE execution_id=? AND attempt_number=?",
                        (str(reservation.execution_id), reservation.attempt_number),
                    ).fetchone()
                    if intent is not None:
                        if intent["state"] != "dispatch_intent":
                            raise SafetyControlStorageError
                        changed = connection.execute(
                            "UPDATE control_execution_intents SET state='settled',"
                            "conservative=?,finalized_at_ns=?,terminal_reason=?,"
                            "revision=revision+1 WHERE execution_id=? AND attempt_number=? "
                            "AND state='dispatch_intent'",
                            (
                                int(conservative),
                                now_ns,
                                reason,
                                str(reservation.execution_id),
                                reservation.attempt_number,
                            ),
                        ).rowcount
                        if changed != 1:
                            raise SafetyControlStorageError
                    if int(row["reserved_at_ns"]) > day_cutoff:
                        self._apply_budget_projection_deltas(
                            connection,
                            deltas=tuple(
                                (
                                    scope_class,
                                    scope_tag,
                                    0,
                                    0,
                                    actual_cost_micro_usd - reservation.reserved_micro_usd,
                                )
                                for scope_class, scope_tag in self._budget_row_scope_pairs(row)
                            ),
                            revision=projection_revision,
                            now_ns=now_ns,
                        )
                    connection.commit()
                    return BudgetSettlement(
                        execution_id=reservation.execution_id,
                        attempt_number=reservation.attempt_number,
                        policy_version=reservation.policy_version,
                        pricing_version=reservation.pricing_version,
                        reserved_micro_usd=reservation.reserved_micro_usd,
                        actual_cost_micro_usd=actual_cost_micro_usd,
                        released_micro_usd=released,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        conservative=conservative,
                    )
                except (sqlite3.Error, SafetyControlStorageError):
                    connection.rollback()
                    raise
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def release_budget(
        self,
        *,
        reservation: BudgetReservation,
        reason: str,
        now_ns: int,
    ) -> None:
        self._require_reservation(reservation)
        self._require_time(now_ns)
        if reason != "cancelled_before_dispatch":
            raise ValueError("Budget release reason is invalid")
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT r.status,r.reserved_at_ns,r.reserved_micro_usd,"
                    "o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag "
                    "FROM budget_reservations r JOIN budget_execution_owners o "
                    "USING(execution_id) WHERE r.execution_id=? AND r.attempt_number=?",
                    (str(reservation.execution_id), reservation.attempt_number),
                ).fetchone()
                if row is None or row["status"] in ("dispatched", "settled"):
                    connection.rollback()
                    raise SafetyControlStorageError
                if row["status"] == "reserved":
                    hour_cutoff, day_cutoff, projection_revision = self._advance_budget_projection(
                        connection, now_ns=now_ns
                    )
                    connection.execute(
                        "UPDATE budget_reservations SET status = 'released', released_at_ns = ?, "
                        "release_reason = ? WHERE execution_id = ? AND attempt_number = ?",
                        (
                            now_ns,
                            reason,
                            str(reservation.execution_id),
                            reservation.attempt_number,
                        ),
                    )
                    intent = connection.execute(
                        "SELECT state FROM control_execution_intents "
                        "WHERE execution_id=? AND attempt_number=?",
                        (str(reservation.execution_id), reservation.attempt_number),
                    ).fetchone()
                    if intent is not None:
                        if intent["state"] != "dispatch_intent":
                            raise SafetyControlStorageError
                        changed = connection.execute(
                            "UPDATE control_execution_intents SET state='released',"
                            "finalized_at_ns=?,terminal_reason='cancelled_before_dispatch',"
                            "revision=revision+1 WHERE execution_id=? AND attempt_number=? "
                            "AND state='dispatch_intent'",
                            (now_ns, str(reservation.execution_id), reservation.attempt_number),
                        ).rowcount
                        if changed != 1:
                            raise SafetyControlStorageError
                    reserved_at_ns = int(row["reserved_at_ns"])
                    self._apply_budget_projection_deltas(
                        connection,
                        deltas=tuple(
                            (
                                scope_class,
                                scope_tag,
                                -int(reserved_at_ns > hour_cutoff),
                                -int(reserved_at_ns > day_cutoff),
                                -int(row["reserved_micro_usd"])
                                if reserved_at_ns > day_cutoff
                                else 0,
                            )
                            for scope_class, scope_tag in self._budget_row_scope_pairs(row)
                        ),
                        revision=projection_revision,
                        now_ns=now_ns,
                    )
                connection.commit()
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def budget_attempt_count(self) -> int:
        return self._count_table("budget_reservations")

    def budget_settlement_count(self) -> int:
        return self._count_table("budget_settlements")

    def breaker_result_count(self) -> int:
        return self._count_table("breaker_execution_results")

    def execution_intent_snapshot(self) -> tuple[sqlite3.Row, ...]:
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                return tuple(
                    connection.execute(
                        "SELECT execution_id,attempt_number,policy_version,state,conservative,"
                        "created_at_ns,finalized_at_ns,terminal_reason,revision "
                        "FROM control_execution_intents ORDER BY execution_id,attempt_number"
                    ).fetchall()
                )
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def breaker_snapshot(self) -> tuple[sqlite3.Row, ...]:
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                return tuple(
                    connection.execute("SELECT * FROM circuit_breakers ORDER BY scope_tag")
                )
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def budget_attempt_snapshot(self) -> tuple[sqlite3.Row, ...]:
        try:
            with closing(self._connect()) as connection:
                connection.row_factory = sqlite3.Row
                return tuple(
                    connection.execute(
                        "SELECT r.*, COALESCE(s.actual_cost_micro_usd, 0) "
                        "AS actual_cost_micro_usd, COALESCE(s.conservative, 0) AS conservative "
                        "FROM budget_reservations r LEFT JOIN budget_settlements s "
                        "USING (execution_id, attempt_number) "
                        "ORDER BY r.reserved_at_ns, r.execution_id, r.attempt_number"
                    ).fetchall()
                )
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def active_permit_count(self) -> int:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT COUNT(*) FROM provider_permits WHERE released_at_ns IS NULL"
                ).fetchone()
                return int(row[0])
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def admission_count(self) -> int:
        try:
            with closing(self._connect()) as connection:
                return int(
                    connection.execute("SELECT COUNT(*) FROM execution_admissions").fetchone()[0]
                )
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def bucket_snapshot(self) -> tuple[tuple[object, ...], ...]:
        try:
            with closing(self._connect()) as connection:
                return tuple(
                    connection.execute(
                        "SELECT scope_class, scope_tag, tokens_micro, refill_remainder, "
                        "last_refill_ns FROM token_buckets ORDER BY scope_class, scope_tag"
                    ).fetchall()
                )
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def _consume(
        self,
        *,
        buckets: Sequence[BucketRequest],
        now_ns: int,
    ) -> BucketConsumptionResult:
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                decision = self._consume_in_transaction(
                    connection,
                    buckets=buckets,
                    now_ns=now_ns,
                )
                if decision.outcome is RateLimitOutcome.REJECTED:
                    connection.rollback()
                else:
                    connection.commit()
                return decision
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def _consume_in_transaction(
        self,
        connection: sqlite3.Connection,
        *,
        buckets: Sequence[BucketRequest],
        now_ns: int,
    ) -> BucketConsumptionResult:
        self._require_time(now_ns)
        if not buckets or any(not isinstance(bucket, BucketRequest) for bucket in buckets):
            raise TypeError("Safety control bucket request is invalid")
        if len({bucket.spec.scope for bucket in buckets}) != len(buckets):
            raise ValueError("Safety control bucket scope is duplicated")
        states: list[tuple[BucketRequest, int, int, int]] = []
        retry_values: list[int] = []
        for bucket in buckets:
            row = connection.execute(
                "SELECT policy_version, refill_per_minute, burst_microtokens, "
                "tokens_micro, refill_remainder, last_refill_ns "
                "FROM token_buckets WHERE scope_class = ? AND scope_tag = ?",
                (bucket.spec.scope.value, bucket.scope_tag),
            ).fetchone()
            burst_micro = bucket.spec.burst * _MICROTOKENS
            if row is None:
                tokens_micro = burst_micro
                remainder = 0
                last_refill_ns = now_ns
            else:
                if (
                    row[0] != CONTROL_POLICY_VERSION
                    or int(row[1]) != bucket.spec.refill_per_minute
                    or int(row[2]) != burst_micro
                ):
                    raise SafetyControlStorageError
                tokens_micro, remainder, last_refill_ns = (int(value) for value in row[3:])
                effective_now = max(now_ns, last_refill_ns)
                numerator = (
                    effective_now - last_refill_ns
                ) * bucket.spec.refill_per_minute * _MICROTOKENS + remainder
                tokens_micro = min(
                    burst_micro,
                    tokens_micro + numerator // _REFILL_DENOMINATOR,
                )
                remainder = 0 if tokens_micro == burst_micro else numerator % _REFILL_DENOMINATOR
                last_refill_ns = effective_now
            states.append((bucket, tokens_micro, remainder, last_refill_ns))
            if tokens_micro < _MICROTOKENS:
                retry_values.append(
                    retry_after_seconds(
                        missing_microtokens=_MICROTOKENS - tokens_micro,
                        refill_per_minute=bucket.spec.refill_per_minute,
                    )
                )
        if retry_values:
            return BucketConsumptionResult(RateLimitOutcome.REJECTED, max(retry_values))
        for bucket, tokens_micro, remainder, last_refill_ns in states:
            connection.execute(
                "INSERT INTO token_buckets ("
                "scope_class, scope_tag, policy_version, refill_per_minute, "
                "burst_microtokens, tokens_micro, refill_remainder, last_refill_ns"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(scope_class, scope_tag) DO UPDATE SET "
                "tokens_micro = excluded.tokens_micro, "
                "refill_remainder = excluded.refill_remainder, "
                "last_refill_ns = excluded.last_refill_ns",
                (
                    bucket.spec.scope.value,
                    bucket.scope_tag,
                    CONTROL_POLICY_VERSION,
                    bucket.spec.refill_per_minute,
                    bucket.spec.burst * _MICROTOKENS,
                    tokens_micro - _MICROTOKENS,
                    remainder,
                    last_refill_ns,
                ),
            )
        return BucketConsumptionResult(RateLimitOutcome.ALLOWED, None)

    @staticmethod
    def _insert_admission(
        connection: sqlite3.Connection,
        *,
        execution_id: UUID,
        request_id: UUID,
        scope_tags: PermitScopeTags,
        admitted_at_ns: int,
    ) -> None:
        connection.execute(
            "INSERT INTO execution_admissions ("
            "execution_id, request_id, policy_version, player_scope_tag, "
            "player_npc_scope_tag, conversation_scope_tag, admitted_at_ns"
            ") VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(execution_id),
                str(request_id),
                CONTROL_POLICY_VERSION,
                scope_tags.player_scope_tag,
                scope_tags.player_npc_scope_tag,
                scope_tags.conversation_scope_tag,
                admitted_at_ns,
            ),
        )

    @staticmethod
    def _admission_matches(
        row: sqlite3.Row,
        *,
        request_id: UUID,
        scope_tags: PermitScopeTags,
    ) -> bool:
        return bool(
            row["request_id"] == str(request_id)
            and SqliteSafetyControlRepository._scope_matches(row, scope_tags)
        )

    @staticmethod
    def _permit_scope_bytes(scope_tags: PermitScopeTags) -> tuple[bytes, bytes, bytes]:
        values = (
            scope_tags.player_scope_tag,
            scope_tags.player_npc_scope_tag,
            scope_tags.conversation_scope_tag,
        )
        if any(
            not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
            for value in values
        ):
            raise SafetyControlStorageError
        return bytes.fromhex(values[0]), bytes.fromhex(values[1]), bytes.fromhex(values[2])

    @staticmethod
    def _permit_scope_matches(row: sqlite3.Row, expected: tuple[bytes, bytes, bytes]) -> bool:
        columns = ("player_scope_tag", "player_npc_scope_tag", "conversation_scope_tag")
        return all(
            isinstance(row[column], bytes) and len(row[column]) == 32 and row[column] == value
            for column, value in zip(columns, expected, strict=True)
        )

    @staticmethod
    def _scope_matches(row: sqlite3.Row, scope_tags: PermitScopeTags) -> bool:
        return bool(
            row["player_scope_tag"] == scope_tags.player_scope_tag
            and row["player_npc_scope_tag"] == scope_tags.player_npc_scope_tag
            and row["conversation_scope_tag"] == scope_tags.conversation_scope_tag
        )

    @staticmethod
    def _require_admission(
        execution_id: object,
        request_id: object,
        scope_tags: object,
        admitted_at_ns: object,
    ) -> None:
        if not isinstance(execution_id, UUID) or not isinstance(request_id, UUID):
            raise TypeError("Safety control admission identifier is invalid")
        if not isinstance(scope_tags, PermitScopeTags):
            raise TypeError("Safety control admission scope is invalid")
        SqliteSafetyControlRepository._require_time(admitted_at_ns)

    @staticmethod
    def _require_time(value: object) -> None:
        if type(value) is not int or value <= 0:
            raise ValueError("Safety control timestamp is invalid")

    @classmethod
    def _require_breaker_inputs(
        cls,
        execution_id: object,
        scope_tag: object,
        now_ns: object,
    ) -> None:
        if not isinstance(execution_id, UUID):
            raise TypeError("Circuit-breaker execution identifier is invalid")
        if (
            not isinstance(scope_tag, str)
            or len(scope_tag) != 64
            or any(character not in "0123456789abcdef" for character in scope_tag)
        ):
            raise ValueError("Circuit-breaker scope is invalid")
        cls._require_time(now_ns)

    @staticmethod
    def _require_budget_inputs(
        execution_id: object,
        attempt_number: object,
        scope_tags: object,
        pricing_policy: object,
        now_ns: object,
    ) -> None:
        if not isinstance(execution_id, UUID):
            raise TypeError("Budget execution identifier is invalid")
        if type(attempt_number) is not int or not 1 <= attempt_number <= 2:
            raise ValueError("Budget attempt number is invalid")
        if not isinstance(scope_tags, BudgetScopeTags):
            raise TypeError("Budget scope metadata is invalid")
        if not isinstance(pricing_policy, PricingPolicy):
            raise TypeError("Budget pricing metadata is invalid")
        SqliteSafetyControlRepository._require_time(now_ns)

    @staticmethod
    def _require_reservation(reservation: object) -> None:
        if not isinstance(reservation, BudgetReservation):
            raise TypeError("Budget reservation is invalid")

    @staticmethod
    def _budget_admission_matches(row: sqlite3.Row, scope_tags: BudgetScopeTags) -> bool:
        return bool(
            row["player_scope_tag"] == scope_tags.player_scope_tag
            and row["player_npc_scope_tag"] == scope_tags.player_npc_scope_tag
        )

    @staticmethod
    def _budget_owner_matches(row: sqlite3.Row, scope_tags: BudgetScopeTags) -> bool:
        return bool(
            row["policy_version"] == BUDGET_POLICY_VERSION
            and row["player_scope_tag"] == scope_tags.player_scope_tag
            and row["npc_scope_tag"] == scope_tags.npc_scope_tag
            and row["player_npc_scope_tag"] == scope_tags.player_npc_scope_tag
        )

    @staticmethod
    def _scope_filter(
        limit_class: BudgetLimitClass,
        scope_tags: BudgetScopeTags,
    ) -> tuple[str, tuple[str, ...]]:
        if limit_class.value.startswith("player_npc_"):
            return "o.player_npc_scope_tag = ?", (scope_tags.player_npc_scope_tag,)
        if limit_class.value.startswith("player_"):
            return "o.player_scope_tag = ?", (scope_tags.player_scope_tag,)
        if limit_class.value.startswith("npc_"):
            return "o.npc_scope_tag = ?", (scope_tags.npc_scope_tag,)
        if limit_class.value.startswith("global_"):
            return "1 = 1", ()
        raise SafetyControlStorageError

    @staticmethod
    def _budget_scope_pairs(scope_tags: BudgetScopeTags) -> tuple[tuple[str, str], ...]:
        return (
            ("player_npc", scope_tags.player_npc_scope_tag),
            ("player", scope_tags.player_scope_tag),
            ("npc", scope_tags.npc_scope_tag),
            ("global", _GLOBAL_BUDGET_SCOPE_TAG),
        )

    @staticmethod
    def _budget_row_scope_pairs(row: sqlite3.Row) -> tuple[tuple[str, str], ...]:
        return (
            ("player_npc", str(row["player_npc_scope_tag"])),
            ("player", str(row["player_scope_tag"])),
            ("npc", str(row["npc_scope_tag"])),
            ("global", _GLOBAL_BUDGET_SCOPE_TAG),
        )

    @classmethod
    def _apply_budget_projection_deltas(
        cls,
        connection: sqlite3.Connection,
        *,
        deltas: tuple[tuple[str, str, int, int, int], ...],
        revision: int,
        now_ns: int,
    ) -> None:
        if (
            len(deltas) != 4
            or {item[0] for item in deltas} != set(_BUDGET_WINDOW_SCOPES)
            or len({(item[0], item[1]) for item in deltas}) != 4
        ):
            raise SafetyControlStorageError
        is_reservation = all(
            attempts_1h == 1 and attempts_24h == 1 and cost_24h >= 0
            for _, _, attempts_1h, attempts_24h, cost_24h in deltas
        )
        if is_reservation:
            parameters: list[str | int] = []
            for scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h in deltas:
                parameters.extend(
                    (
                        scope_class,
                        scope_tag,
                        attempts_1h,
                        attempts_24h,
                        cost_24h,
                        revision,
                        now_ns,
                        attempts_1h,
                        attempts_24h,
                        cost_24h,
                    )
                )
            connection.execute(_BUDGET_SCOPE_UPSERT_SQL, tuple(parameters))
            return
        parameters = []
        for scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h in deltas:
            parameters.extend((scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h))
        parameters.extend((revision, now_ns))
        updated = connection.execute(_BUDGET_SCOPE_UPDATE_SQL, tuple(parameters)).fetchall()
        if len(updated) != 4 or {(str(row[0]), str(row[1])) for row in updated} != {
            (scope_class, scope_tag) for scope_class, scope_tag, *_ in deltas
        }:
            raise SafetyControlStorageError

    @classmethod
    def _rebuild_budget_projection(
        cls,
        connection: sqlite3.Connection,
        *,
        now_ns: int,
    ) -> None:
        cls._require_time(now_ns)
        connection.row_factory = sqlite3.Row
        prior = connection.execute(
            "SELECT revision FROM budget_window_projection_state WHERE singleton=1"
        ).fetchone()
        revision = 1 if prior is None else int(prior[0]) + 1
        totals: dict[tuple[str, str], list[int]] = {}
        rows = connection.execute(
            "SELECT o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag,"
            "r.status,r.reserved_at_ns,r.reserved_micro_usd,s.actual_cost_micro_usd "
            "FROM budget_reservations r JOIN budget_execution_owners o USING(execution_id) "
            "LEFT JOIN budget_settlements s USING(execution_id,attempt_number) "
            "WHERE r.status<>'released' AND r.reserved_at_ns>?",
            (now_ns - _BUDGET_DAY_NS,),
        ).fetchall()
        for row in rows:
            attempt_1h = int(int(row["reserved_at_ns"]) > now_ns - _BUDGET_HOUR_NS)
            cost = (
                int(row["actual_cost_micro_usd"])
                if row["status"] == "settled"
                else int(row["reserved_micro_usd"])
            )
            for key in cls._budget_row_scope_pairs(row):
                current = totals.setdefault(key, [0, 0, 0])
                current[0] += attempt_1h
                current[1] += 1
                current[2] += cost
        connection.execute("DELETE FROM budget_window_totals")
        for (scope_class, scope_tag), values in totals.items():
            connection.execute(
                "INSERT INTO budget_window_totals "
                "(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd,"
                "revision,updated_at_ns,checked_attempts_1h,checked_attempts_24h,"
                "checked_cost_24h_micro_usd) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (scope_class, scope_tag, *values, revision, now_ns, *values),
            )
        connection.execute(
            "INSERT INTO budget_window_projection_state "
            "(singleton,projection_version,policy_version,hour_cutoff_ns,day_cutoff_ns,"
            "revision,rebuilt_at_ns) VALUES (1,?,?,?,?,?,?) "
            "ON CONFLICT(singleton) DO UPDATE SET "
            "projection_version=excluded.projection_version,"
            "policy_version=excluded.policy_version,hour_cutoff_ns=excluded.hour_cutoff_ns,"
            "day_cutoff_ns=excluded.day_cutoff_ns,revision=excluded.revision,"
            "rebuilt_at_ns=excluded.rebuilt_at_ns",
            (
                _BUDGET_PROJECTION_VERSION,
                BUDGET_POLICY_VERSION,
                now_ns - _BUDGET_HOUR_NS,
                now_ns - _BUDGET_DAY_NS,
                revision,
                now_ns,
            ),
        )

    @classmethod
    def _advance_budget_projection(
        cls,
        connection: sqlite3.Connection,
        *,
        now_ns: int,
    ) -> tuple[int, int, int]:
        connection.row_factory = sqlite3.Row
        hour_cutoff = now_ns - _BUDGET_HOUR_NS
        day_cutoff = now_ns - _BUDGET_DAY_NS
        state = connection.execute(
            "SELECT * FROM budget_window_projection_state WHERE singleton=1"
        ).fetchone()
        if (
            state is None
            or state["projection_version"] != _BUDGET_PROJECTION_VERSION
            or state["policy_version"] != BUDGET_POLICY_VERSION
            or hour_cutoff < int(state["hour_cutoff_ns"])
            or day_cutoff < int(state["day_cutoff_ns"])
        ):
            cls._rebuild_budget_projection(connection, now_ns=now_ns)
            rebuilt = connection.execute(
                "SELECT * FROM budget_window_projection_state WHERE singleton=1"
            ).fetchone()
            if rebuilt is None:
                raise SafetyControlStorageError
            return (
                int(rebuilt["hour_cutoff_ns"]),
                int(rebuilt["day_cutoff_ns"]),
                int(rebuilt["revision"]),
            )
        old_hour = int(state["hour_cutoff_ns"])
        old_day = int(state["day_cutoff_ns"])
        if hour_cutoff == old_hour and day_cutoff == old_day:
            return old_hour, old_day, int(state["revision"])
        revision = int(state["revision"]) + 1
        probe = (old_hour, hour_cutoff, old_day, day_cutoff)
        if connection.execute(_BUDGET_EXPIRATION_PROBE_SQL, probe).fetchone() is not None:
            parameters = (
                old_hour,
                hour_cutoff,
                old_day,
                day_cutoff,
                old_hour,
                hour_cutoff,
                old_day,
                day_cutoff,
                revision,
                now_ns,
            )
            if not connection.execute(_BUDGET_EXPIRATION_UPDATE_SQL, parameters).fetchall():
                raise SafetyControlStorageError
        connection.execute(
            "UPDATE budget_window_projection_state SET hour_cutoff_ns=?,day_cutoff_ns=?,"
            "revision=? WHERE singleton=1",
            (hour_cutoff, day_cutoff, revision),
        )
        return hour_cutoff, day_cutoff, revision

    @classmethod
    def _all_window_totals(
        cls,
        connection: sqlite3.Connection,
        *,
        scope_tags: BudgetScopeTags,
        now_ns: int,
    ) -> dict[str, tuple[int, int, int]]:
        pairs = cls._budget_scope_pairs(scope_tags)
        rows = connection.execute(
            _BUDGET_WINDOW_TOTALS_SQL,
            tuple(value for pair in pairs for value in pair),
        ).fetchall()
        if len(rows) != 4 or tuple(str(row[0]) for row in rows) != _BUDGET_WINDOW_SCOPES:
            raise SafetyControlStorageError
        result: dict[str, tuple[int, int, int]] = {}
        for row, (_, scope_tag) in zip(rows, pairs, strict=True):
            scope = str(row[0])
            # Both copies are maintained by the same ledger transaction. A
            # damaged projection must never be used to grant fresh quota.
            # This is corruption detection, not authentication of a DB writer.
            if tuple(row[2:5]) != tuple(row[5:8]):
                raise SafetyControlStorageError
            if not bool(row[1]) and cls._projection_scope_has_active_ledger(
                connection,
                scope_class=scope,
                scope_tag=scope_tag,
                day_cutoff_ns=now_ns - _BUDGET_DAY_NS,
            ):
                raise SafetyControlStorageError
            result[scope] = (int(row[2]), int(row[3]), int(row[4]))
        return result

    @staticmethod
    def _projection_scope_has_active_ledger(
        connection: sqlite3.Connection,
        *,
        scope_class: str,
        scope_tag: str,
        day_cutoff_ns: int,
    ) -> bool:
        if scope_class == "global":
            row = connection.execute(
                "SELECT 1 FROM budget_reservations WHERE status<>'released' "
                "AND reserved_at_ns>? LIMIT 1",
                (day_cutoff_ns,),
            ).fetchone()
            return row is not None
        columns = {
            "player_npc": "player_npc_scope_tag",
            "player": "player_scope_tag",
            "npc": "npc_scope_tag",
        }
        column = columns.get(scope_class)
        if column is None:
            raise SafetyControlStorageError
        row = connection.execute(
            "SELECT 1 FROM budget_reservations r JOIN budget_execution_owners o "
            f"USING(execution_id) WHERE o.{column}=? AND r.status<>'released' "
            "AND r.reserved_at_ns>? LIMIT 1",
            (scope_tag, day_cutoff_ns),
        ).fetchone()
        return row is not None

    @staticmethod
    def _reservation_from_row(
        row: sqlite3.Row,
        scope_tags: BudgetScopeTags,
    ) -> BudgetReservation:
        if not SqliteSafetyControlRepository._budget_owner_matches(row, scope_tags):
            raise SafetyControlStorageError
        return BudgetReservation(
            execution_id=UUID(row["execution_id"]),
            attempt_number=int(row["attempt_number"]),
            policy_version=row["policy_version"],
            pricing_version=row["pricing_version"],
            provider_kind=ProviderKind(row["provider_kind"]),
            reserved_micro_usd=int(row["reserved_micro_usd"]),
            soft_warning=bool(row["soft_warning"]),
            scope_tags=scope_tags,
        )

    @staticmethod
    def _settlement_from_row(row: sqlite3.Row) -> BudgetSettlement:
        return BudgetSettlement(
            execution_id=UUID(row["execution_id"]),
            attempt_number=int(row["attempt_number"]),
            policy_version=row["policy_version"],
            pricing_version=row["pricing_version"],
            reserved_micro_usd=int(row["reserved_micro_usd"]),
            actual_cost_micro_usd=int(row["actual_cost_micro_usd"]),
            released_micro_usd=int(row["released_micro_usd"]),
            prompt_tokens=int(row["prompt_tokens"]),
            completion_tokens=int(row["completion_tokens"]),
            conservative=bool(row["conservative"]),
        )

    def _count_table(self, table: str) -> int:
        if table not in {
            "budget_reservations",
            "budget_settlements",
            "breaker_execution_results",
            "control_execution_intents",
        }:
            raise ValueError("Control count table is invalid")
        try:
            with closing(self._connect()) as connection:
                return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def try_admit_provider_dispatch(
        self,
        *,
        execution_id: UUID,
        attempt_number: int,
        request_id: UUID,
        execution_buckets: Sequence[BucketRequest],
        permit_scope_tags: PermitScopeTags,
        budget_scope_tags: BudgetScopeTags,
        pricing_policy: PricingPolicy,
        breaker_scope_tag: str,
        now_ns: int,
    ) -> tuple[
        BucketConsumptionResult | None,
        BreakerDecision,
        BudgetReservation | None,
        bool,
    ]:
        """Persist the complete pre-provider fence with one physical commit."""

        with self._composed_transaction() as connection:
            try:
                breaker = self.check_breaker(
                    execution_id=execution_id,
                    scope_tag=breaker_scope_tag,
                    now_ns=now_ns,
                )
                if breaker.outcome is BreakerOutcome.REJECTED:
                    connection.commit()
                    return None, breaker, None, False
                rate_decision = self.consume_execution_admission(
                    buckets=execution_buckets,
                    execution_id=execution_id,
                    request_id=request_id,
                    scope_tags=permit_scope_tags,
                    now_ns=now_ns,
                )
                if rate_decision.outcome is RateLimitOutcome.REJECTED:
                    connection.rollback()
                    return rate_decision, breaker, None, False
                try:
                    reservation = self.reserve_budget(
                        execution_id=execution_id,
                        attempt_number=attempt_number,
                        scope_tags=budget_scope_tags,
                        pricing_policy=pricing_policy,
                        now_ns=now_ns,
                    )
                except BudgetRejectedError:
                    self.release_breaker_probe(
                        execution_id=execution_id,
                        scope_tag=breaker_scope_tag,
                        now_ns=now_ns,
                    )
                    connection.commit()
                    raise
                try:
                    acquired = self.try_acquire_permit(
                        execution_id=execution_id,
                        scope_tags=permit_scope_tags,
                        acquired_at_ns=now_ns,
                    )
                except ControlRepositoryError:
                    self.release_budget(
                        reservation=reservation,
                        reason="cancelled_before_dispatch",
                        now_ns=now_ns,
                    )
                    self.release_breaker_probe(
                        execution_id=execution_id,
                        scope_tag=breaker_scope_tag,
                        now_ns=now_ns,
                    )
                    connection.commit()
                    raise
                if not acquired:
                    connection.rollback()
                    return None, breaker, None, False
                existing_intent = connection.execute(
                    "SELECT policy_version,state FROM control_execution_intents "
                    "WHERE execution_id=? AND attempt_number=?",
                    (str(execution_id), attempt_number),
                ).fetchone()
                if existing_intent is None:
                    connection.execute(
                        "INSERT INTO control_execution_intents ("
                        "execution_id,attempt_number,policy_version,state,conservative,"
                        "created_at_ns,finalized_at_ns,terminal_reason,revision"
                        ") VALUES (?,? ,?,'dispatch_intent',0,?,NULL,NULL,1)",
                        (
                            str(execution_id),
                            attempt_number,
                            _EXECUTION_INTENT_POLICY_VERSION,
                            now_ns,
                        ),
                    )
                elif (
                    existing_intent["policy_version"] != _EXECUTION_INTENT_POLICY_VERSION
                    or existing_intent["state"] != "dispatch_intent"
                ):
                    raise SafetyControlStorageError
                connection.commit()
                return rate_decision, breaker, reservation, True
            except BudgetRejectedError:
                raise
            except (sqlite3.Error, ControlRepositoryError) as error:
                connection.rollback()
                if isinstance(error, ControlRepositoryError):
                    raise
                raise SafetyControlStorageError from error

    def finalize_provider_success(
        self,
        *,
        reservation: BudgetReservation,
        usage: ProviderUsage,
        actual_cost_micro_usd: int,
        breaker_scope_tag: str,
        now_ns: int,
    ) -> tuple[BudgetSettlement, BreakerDecision]:
        """Persist successful settlement, breaker result, and permit release once."""

        with self._composed_transaction() as connection:
            try:
                settlement = self.settle_budget(
                    reservation=reservation,
                    usage=usage,
                    actual_cost_micro_usd=actual_cost_micro_usd,
                    conservative=False,
                    reason="trusted_usage",
                    now_ns=now_ns,
                )
            except ControlRepositoryError:
                self.release_permit(
                    execution_id=reservation.execution_id,
                    released_at_ns=now_ns,
                    reason="control_failure",
                )
                connection.commit()
                raise
            try:
                breaker = self.record_breaker_result(
                    execution_id=reservation.execution_id,
                    scope_tag=breaker_scope_tag,
                    success=True,
                    failure_reason=None,
                    now_ns=now_ns,
                )
            except ControlRepositoryError:
                self.release_permit(
                    execution_id=reservation.execution_id,
                    released_at_ns=now_ns,
                    reason="control_failure",
                )
                connection.commit()
                raise
            try:
                self.release_permit(
                    execution_id=reservation.execution_id,
                    released_at_ns=now_ns,
                    reason="completed",
                )
                connection.commit()
                return settlement, breaker
            except ControlRepositoryError:
                connection.commit()
                raise

    @contextmanager
    def _composed_transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            with closing(self._writer.borrow(timeout_ms=self._busy_timeout_milliseconds)) as raw:
                raw.execute("BEGIN IMMEDIATE")
                self._composed.connection = _ComposedTransactionConnection(raw)
                try:
                    yield raw
                except BaseException:
                    if raw.in_transaction:
                        raw.rollback()
                    raise
                finally:
                    del self._composed.connection
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def _connect(self) -> sqlite3.Connection:
        composed = getattr(self._composed, "connection", None)
        if composed is not None:
            return cast(sqlite3.Connection, composed)
        try:
            return self._writer.borrow(timeout_ms=self._busy_timeout_milliseconds)
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def close(self) -> None:
        """Release the owned writer after all callers have finished."""
        self._writer.close()

    @staticmethod
    def _migration_statements(script: str) -> tuple[str, ...]:
        statements: list[str] = []
        buffer = ""
        for line in script.splitlines(keepends=True):
            buffer += line
            if sqlite3.complete_statement(buffer):
                statement = buffer.strip()
                if statement:
                    statements.append(statement)
                buffer = ""
        if buffer.strip():
            raise SafetyControlStorageError
        return tuple(statements)

    @staticmethod
    def _validate_tables(connection: sqlite3.Connection) -> None:
        required = {
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
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if tables != required:
            raise SafetyControlStorageError
