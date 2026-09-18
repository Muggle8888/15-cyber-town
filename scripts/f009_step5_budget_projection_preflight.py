"""Synthetic V14 preflight for an exact rolling budget projection.

This module deliberately keeps the candidate DDL and repository behavior out of
product composition.  The authoritative reservation/settlement ledger remains
unchanged; the candidate totals can always be rebuilt from it.
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import hashlib
import json
import math
import os
import sqlite3
import statistics
import sys
import threading
import time
from collections.abc import Awaitable, Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import Any, ClassVar, cast
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
from cyber_town.application.control import SafetyControl
from cyber_town.application.control_performance import (
    PerformanceRun,
    PerformanceScenario,
    summarize_performance_runs,
)
from cyber_town.application.observability import (
    InMemoryObservabilityRecorder,
    NoOpObservabilityRecorder,
    ObservabilityRecorder,
    ProviderKind,
)
from cyber_town.application.provider import ProviderRequest, ProviderUsage
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.infrastructure.control.sqlite_control import (
    SafetyControlStorageError,
    SqliteSafetyControlRepository,
)
from cyber_town.infrastructure.llm.fake import FakeProvider
from scripts import f009_step5_benchmark as benchmark

APPROVED_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection-validation-v2"
)
P95_ATTRIBUTION_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection-p95-attribution"
)
UNIFIED_VALIDATION_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v16-budget-projection-unified"
)
STAGE_ATTRIBUTION_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v17-projection-stage-attribution"
)
V18_SET_BASED_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based"
)
V18_REVISED_SEMANTIC_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based-revised-semantic"
)
V18_REVISED_PERFORMANCE_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based-revised-performance"
)
V19_SINGLE_WRITE_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v19-projection-single-write"
)
V18_REVISED_SEMANTIC_SUMMARY = V18_REVISED_SEMANTIC_ROOT / "summary-semantic-01.json"
V18_REVISED_SEMANTIC_SUMMARY_SHA256 = (
    "65BBB6EA22671786A7F99DE2EFF24A7A17ACFBF7806F1B007EBDBBF41506A0B4"
)
V17_RECORDED_RESERVATION_P95_MS = 0.9746
V17_RECORDED_SETTLEMENT_P95_MS = 0.4566
PROJECTION_VERSION = "f-009-budget-window-projection-v1"
GLOBAL_SCOPE_TAG = "0" * 64
HOUR_NS = 3_600 * 1_000_000_000
DAY_NS = 86_400 * 1_000_000_000
WINDOW_DELTA_NS = DAY_NS - HOUR_NS
SYNTHETIC_KEY = b"f009-v14-synthetic-scope-key-32bytes"
BASE_NS = 1_800_000_000_000_000_000
RESERVE_SAMPLE_RUNS: list[tuple[float, ...]] = []
STABILITY_SEGMENT_RANGES = {
    "early_steady_100": (100, 200),
    "middle_steady_100": (500, 600),
    "late_steady_100": (900, 1_000),
}
P95_ATTRIBUTION_ORDER = tuple(benchmark.MEMORY_PROTOCOL_PAIR for _ in range(benchmark.RUN_COUNT))


CANDIDATE_DDL = f"""
DROP INDEX idx_budget_owners_player;
DROP INDEX idx_budget_owners_npc;
DROP INDEX idx_budget_owners_player_npc;

CREATE TABLE budget_window_projection_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    projection_version TEXT NOT NULL CHECK (
        projection_version = '{PROJECTION_VERSION}'
    ),
    policy_version TEXT NOT NULL CHECK (
        policy_version = '{BUDGET_POLICY_VERSION}'
    ),
    hour_cutoff_ns INTEGER NOT NULL CHECK (hour_cutoff_ns > 0),
    day_cutoff_ns INTEGER NOT NULL CHECK (day_cutoff_ns > 0),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    rebuilt_at_ns INTEGER NOT NULL CHECK (rebuilt_at_ns > 0),
    CHECK (hour_cutoff_ns - day_cutoff_ns = {WINDOW_DELTA_NS})
) STRICT;

CREATE TABLE budget_window_totals (
    scope_class TEXT NOT NULL CHECK (
        scope_class IN ('player_npc', 'player', 'npc', 'global')
    ),
    scope_tag TEXT NOT NULL CHECK (
        length(scope_tag) = 64 AND scope_tag NOT GLOB '*[^0-9a-f]*'
    ),
    attempts_1h INTEGER NOT NULL CHECK (attempts_1h >= 0),
    attempts_24h INTEGER NOT NULL CHECK (attempts_24h >= 0),
    cost_24h_micro_usd INTEGER NOT NULL CHECK (cost_24h_micro_usd >= 0),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    updated_at_ns INTEGER NOT NULL CHECK (updated_at_ns > 0),
    PRIMARY KEY (scope_class, scope_tag),
    CHECK (
        (scope_class = 'global' AND scope_tag = '{GLOBAL_SCOPE_TAG}')
        OR scope_class <> 'global'
    )
) STRICT, WITHOUT ROWID;

PRAGMA user_version = 5;
"""

SET_BASED_ZERO_SEED_SQL = (
    "INSERT OR IGNORE INTO budget_window_totals "
    "(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd,"
    "revision,updated_at_ns) VALUES " + ",".join("(?,?,0,0,0,?,?)" for _ in range(4))
)

SET_BASED_UPDATE_SQL = (
    "WITH deltas(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h) AS (VALUES "
    + ",".join("(?,?,?,?,?)" for _ in range(4))
    + ") UPDATE budget_window_totals AS t SET "
    "attempts_1h=t.attempts_1h+d.attempts_1h, "
    "attempts_24h=t.attempts_24h+d.attempts_24h, "
    "cost_24h_micro_usd=t.cost_24h_micro_usd+d.cost_24h, "
    "revision=?, updated_at_ns=? FROM deltas AS d "
    "WHERE t.scope_class=d.scope_class AND t.scope_tag=d.scope_tag"
)

SET_BASED_TOTALS_SQL = (
    "WITH requested(scope_class,scope_tag,ordinal) AS (VALUES "
    "(?,?,0),(?,?,1),(?,?,2),(?,?,3)) "
    "SELECT requested.scope_class, "
    "COALESCE(t.attempts_1h,0), COALESCE(t.attempts_24h,0), "
    "COALESCE(t.cost_24h_micro_usd,0) FROM requested "
    "LEFT JOIN budget_window_totals t USING(scope_class,scope_tag) "
    "ORDER BY requested.ordinal"
)

SET_BASED_EXPIRATION_CTES = (
    "WITH expired AS ("
    "SELECT o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag,"
    "r.status,r.reserved_micro_usd,s.actual_cost_micro_usd "
    "FROM budget_reservations r JOIN budget_execution_owners o USING(execution_id) "
    "LEFT JOIN budget_settlements s USING(execution_id,attempt_number) "
    "WHERE r.status<>'released' AND r.reserved_at_ns>? AND r.reserved_at_ns<=?"
    "), scoped(scope_class,scope_tag,cost) AS ("
    "SELECT 'player_npc',player_npc_scope_tag,"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END "
    "FROM expired UNION ALL "
    "SELECT 'player',player_scope_tag,"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END "
    "FROM expired UNION ALL "
    "SELECT 'npc',npc_scope_tag,"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END "
    "FROM expired UNION ALL "
    f"SELECT 'global','{GLOBAL_SCOPE_TAG}',"
    "CASE WHEN status='settled' THEN actual_cost_micro_usd ELSE reserved_micro_usd END "
    "FROM expired) "
)

SET_BASED_EXPIRATION_SEED_SQL = (
    SET_BASED_EXPIRATION_CTES + "INSERT OR IGNORE INTO budget_window_totals "
    "(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd,"
    "revision,updated_at_ns) "
    "SELECT DISTINCT scope_class,scope_tag,0,0,0,?,? FROM scoped"
)

SET_BASED_EXPIRATION_UPDATE_SQL = (
    SET_BASED_EXPIRATION_CTES + ", deltas AS ("
    "SELECT scope_class,scope_tag,"
    "CASE WHEN ?=1 THEN -COUNT(*) ELSE 0 END attempts_1h,"
    "CASE WHEN ?=0 THEN -COUNT(*) ELSE 0 END attempts_24h,"
    "CASE WHEN ?=0 THEN -SUM(cost) ELSE 0 END cost_24h "
    "FROM scoped GROUP BY scope_class,scope_tag) "
    "UPDATE budget_window_totals AS t SET "
    "attempts_1h=t.attempts_1h+d.attempts_1h, "
    "attempts_24h=t.attempts_24h+d.attempts_24h, "
    "cost_24h_micro_usd=t.cost_24h_micro_usd+d.cost_24h, "
    "revision=?, updated_at_ns=? FROM deltas AS d "
    "WHERE t.scope_class=d.scope_class AND t.scope_tag=d.scope_tag"
)

SINGLE_WRITE_UPSERT_SQL = (
    "INSERT INTO budget_window_totals "
    "(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd,"
    "revision,updated_at_ns) VALUES "
    + ",".join("(?,?,?,?,?,?,?)" for _ in range(4))
    + " ON CONFLICT(scope_class,scope_tag) DO UPDATE SET "
    "attempts_1h=budget_window_totals.attempts_1h+excluded.attempts_1h, "
    "attempts_24h=budget_window_totals.attempts_24h+excluded.attempts_24h, "
    "cost_24h_micro_usd="
    "budget_window_totals.cost_24h_micro_usd+excluded.cost_24h_micro_usd, "
    "revision=excluded.revision, updated_at_ns=excluded.updated_at_ns"
)

SINGLE_WRITE_UPDATE_SQL = (
    "WITH deltas(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h) AS (VALUES "
    + ",".join("(?,?,?,?,?)" for _ in range(4))
    + ") UPDATE budget_window_totals AS t SET "
    "attempts_1h=t.attempts_1h+d.attempts_1h, "
    "attempts_24h=t.attempts_24h+d.attempts_24h, "
    "cost_24h_micro_usd=t.cost_24h_micro_usd+d.cost_24h, "
    "revision=?, updated_at_ns=? FROM deltas AS d "
    "WHERE t.scope_class=d.scope_class AND t.scope_tag=d.scope_tag "
    "RETURNING scope_class,scope_tag"
)

SINGLE_WRITE_EXPIRATION_PROBE_SQL = (
    "SELECT 1 FROM budget_reservations "
    "WHERE status<>'released' AND "
    "((reserved_at_ns>? AND reserved_at_ns<=?) OR "
    "(reserved_at_ns>? AND reserved_at_ns<=?)) LIMIT 1"
)

SINGLE_WRITE_EXPIRATION_UPDATE_SQL = (
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
    f"SELECT 'global','{GLOBAL_SCOPE_TAG}',"
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
    "revision=?, updated_at_ns=? FROM deltas AS d "
    "WHERE t.scope_class=d.scope_class AND t.scope_tag=d.scope_tag "
    "AND NOT EXISTS (SELECT 1 FROM deltas AS required "
    "LEFT JOIN budget_window_totals AS existing "
    "ON existing.scope_class=required.scope_class AND existing.scope_tag=required.scope_tag "
    "WHERE existing.scope_class IS NULL) "
    "RETURNING scope_class,scope_tag"
)


def _scope_pairs(tags: BudgetScopeTags) -> tuple[tuple[str, str], ...]:
    return (
        ("player_npc", tags.player_npc_scope_tag),
        ("player", tags.player_scope_tag),
        ("npc", tags.npc_scope_tag),
        ("global", GLOBAL_SCOPE_TAG),
    )


def _row_scope_pairs(row: sqlite3.Row) -> tuple[tuple[str, str], ...]:
    return (
        ("player_npc", str(row["player_npc_scope_tag"])),
        ("player", str(row["player_scope_tag"])),
        ("npc", str(row["npc_scope_tag"])),
        ("global", GLOBAL_SCOPE_TAG),
    )


def _authoritative_totals(
    connection: sqlite3.Connection, now_ns: int
) -> dict[tuple[str, str], tuple[int, int, int]]:
    connection.row_factory = sqlite3.Row
    totals: dict[tuple[str, str], list[int]] = {}
    rows = connection.execute(
        "SELECT o.player_scope_tag, o.npc_scope_tag, o.player_npc_scope_tag, "
        "r.status, r.reserved_at_ns, r.reserved_micro_usd, s.actual_cost_micro_usd "
        "FROM budget_reservations r JOIN budget_execution_owners o USING (execution_id) "
        "LEFT JOIN budget_settlements s USING (execution_id, attempt_number) "
        "WHERE r.status <> 'released' AND r.reserved_at_ns > ?",
        (now_ns - DAY_NS,),
    ).fetchall()
    for row in rows:
        attempt_1h = int(int(row["reserved_at_ns"]) > now_ns - HOUR_NS)
        cost = (
            int(row["actual_cost_micro_usd"])
            if row["status"] == "settled"
            else int(row["reserved_micro_usd"])
        )
        for key in _row_scope_pairs(row):
            value = totals.setdefault(key, [0, 0, 0])
            value[0] += attempt_1h
            value[1] += 1
            value[2] += cost
    return {key: (value[0], value[1], value[2]) for key, value in totals.items()}


def projection_snapshot(connection: sqlite3.Connection) -> dict[str, object]:
    connection.row_factory = sqlite3.Row
    state = connection.execute(
        "SELECT projection_version, policy_version, hour_cutoff_ns, day_cutoff_ns, "
        "revision, rebuilt_at_ns FROM budget_window_projection_state WHERE singleton=1"
    ).fetchone()
    totals = connection.execute(
        "SELECT scope_class, scope_tag, attempts_1h, attempts_24h, "
        "cost_24h_micro_usd, revision, updated_at_ns FROM budget_window_totals "
        "ORDER BY scope_class, scope_tag"
    ).fetchall()
    return {
        "state": None if state is None else tuple(state),
        "totals": tuple(tuple(row) for row in totals),
    }


def assert_projection_matches_ledger(connection: sqlite3.Connection, now_ns: int) -> None:
    expected = _authoritative_totals(connection, now_ns)
    actual = {
        (str(row[0]), str(row[1])): (int(row[2]), int(row[3]), int(row[4]))
        for row in connection.execute(
            "SELECT scope_class, scope_tag, attempts_1h, attempts_24h, "
            "cost_24h_micro_usd FROM budget_window_totals"
        )
        if any(int(value) for value in row[2:5])
    }
    expected = {key: value for key, value in expected.items() if any(value)}
    if actual != expected:
        raise AssertionError("Synthetic projection differs from authoritative ledger")


class CandidateProjectionMixin:
    """Product-shaped candidate methods used only by this synthetic preflight."""

    _reserve_samples: list[float]

    def initialize(self) -> None:
        with closing(self._connect()) as connection:  # type: ignore[attr-defined]
            candidate_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='budget_window_projection_state'"
            ).fetchone()
            if candidate_exists is not None:
                if connection.execute("PRAGMA user_version").fetchone() != (5,):
                    raise SafetyControlStorageError
                tables = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name NOT LIKE 'sqlite_%'"
                    )
                }
                if tables != {
                    "schema_migrations",
                    "token_buckets",
                    "execution_admissions",
                    "provider_permits",
                    "budget_execution_owners",
                    "budget_reservations",
                    "budget_settlements",
                    "circuit_breakers",
                    "breaker_probe_leases",
                    "breaker_execution_results",
                    "budget_window_projection_state",
                    "budget_window_totals",
                }:
                    raise SafetyControlStorageError
                self._validate_candidate_schema(connection)
                return
        super().initialize()  # type: ignore[misc]
        with closing(self._connect()) as connection:  # type: ignore[attr-defined]
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='budget_window_projection_state'"
            ).fetchone()
            if exists is None:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    for statement in SqliteSafetyControlRepository._migration_statements(
                        CANDIDATE_DDL
                    ):
                        connection.execute(statement)
                    connection.commit()
                except sqlite3.Error:
                    connection.rollback()
                    raise
            self._validate_candidate_schema(connection)

    @staticmethod
    def _validate_candidate_schema(connection: sqlite3.Connection) -> None:
        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"budget_window_projection_state", "budget_window_totals"} <= tables:
            raise SafetyControlStorageError
        indexes = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        if {
            "idx_budget_owners_player",
            "idx_budget_owners_npc",
            "idx_budget_owners_player_npc",
        } & indexes or "idx_budget_attempt_quota_time" not in indexes:
            raise SafetyControlStorageError

    @staticmethod
    def _adjust_total(
        connection: sqlite3.Connection,
        *,
        scope_class: str,
        scope_tag: str,
        attempts_1h: int,
        attempts_24h: int,
        cost_24h: int,
        revision: int,
        now_ns: int,
    ) -> None:
        row = connection.execute(
            "SELECT attempts_1h, attempts_24h, cost_24h_micro_usd "
            "FROM budget_window_totals WHERE scope_class=? AND scope_tag=?",
            (scope_class, scope_tag),
        ).fetchone()
        current = (0, 0, 0) if row is None else tuple(int(value) for value in row)
        updated = (
            current[0] + attempts_1h,
            current[1] + attempts_24h,
            current[2] + cost_24h,
        )
        if any(value < 0 for value in updated):
            raise SafetyControlStorageError
        connection.execute(
            "INSERT INTO budget_window_totals "
            "(scope_class,scope_tag,attempts_1h,attempts_24h,cost_24h_micro_usd,"
            "revision,updated_at_ns) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(scope_class,scope_tag) DO UPDATE SET "
            "attempts_1h=excluded.attempts_1h, attempts_24h=excluded.attempts_24h, "
            "cost_24h_micro_usd=excluded.cost_24h_micro_usd, "
            "revision=excluded.revision, updated_at_ns=excluded.updated_at_ns",
            (scope_class, scope_tag, *updated, revision, now_ns),
        )

    @classmethod
    def _apply_scope_deltas(
        cls,
        connection: sqlite3.Connection,
        *,
        deltas: tuple[tuple[str, str, int, int, int], ...],
        revision: int,
        now_ns: int,
    ) -> None:
        for scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h in deltas:
            cls._adjust_total(
                connection,
                scope_class=scope_class,
                scope_tag=scope_tag,
                attempts_1h=attempts_1h,
                attempts_24h=attempts_24h,
                cost_24h=cost_24h,
                revision=revision,
                now_ns=now_ns,
            )

    @classmethod
    def _rebuild_projection(cls, connection: sqlite3.Connection, *, now_ns: int) -> None:
        cls._require_time(now_ns)  # type: ignore[attr-defined]
        prior = connection.execute(
            "SELECT revision FROM budget_window_projection_state WHERE singleton=1"
        ).fetchone()
        revision = 1 if prior is None else int(prior[0]) + 1
        connection.execute("DELETE FROM budget_window_totals")
        for (scope_class, scope_tag), values in _authoritative_totals(connection, now_ns).items():
            cls._adjust_total(
                connection,
                scope_class=scope_class,
                scope_tag=scope_tag,
                attempts_1h=values[0],
                attempts_24h=values[1],
                cost_24h=values[2],
                revision=revision,
                now_ns=now_ns,
            )
        connection.execute(
            "INSERT INTO budget_window_projection_state "
            "(singleton,projection_version,policy_version,hour_cutoff_ns,day_cutoff_ns,"
            "revision,rebuilt_at_ns) VALUES (1,?,?,?,?,?,?) "
            "ON CONFLICT(singleton) DO UPDATE SET "
            "projection_version=excluded.projection_version, "
            "policy_version=excluded.policy_version, hour_cutoff_ns=excluded.hour_cutoff_ns, "
            "day_cutoff_ns=excluded.day_cutoff_ns, revision=excluded.revision, "
            "rebuilt_at_ns=excluded.rebuilt_at_ns",
            (
                PROJECTION_VERSION,
                BUDGET_POLICY_VERSION,
                now_ns - HOUR_NS,
                now_ns - DAY_NS,
                revision,
                now_ns,
            ),
        )

    @classmethod
    def _expire_rows(
        cls,
        connection: sqlite3.Connection,
        *,
        lower: int,
        upper: int,
        expire_hour: bool,
        revision: int,
        now_ns: int,
    ) -> None:
        if upper <= lower:
            return
        rows = connection.execute(
            "SELECT o.player_scope_tag, o.npc_scope_tag, o.player_npc_scope_tag, "
            "r.status, r.reserved_micro_usd, s.actual_cost_micro_usd "
            "FROM budget_reservations r JOIN budget_execution_owners o USING(execution_id) "
            "LEFT JOIN budget_settlements s USING(execution_id,attempt_number) "
            "WHERE r.status <> 'released' AND r.reserved_at_ns > ? "
            "AND r.reserved_at_ns <= ?",
            (lower, upper),
        ).fetchall()
        for row in rows:
            cost = 0
            if not expire_hour:
                cost = -(
                    int(row["actual_cost_micro_usd"])
                    if row["status"] == "settled"
                    else int(row["reserved_micro_usd"])
                )
            cls._apply_scope_deltas(
                connection,
                deltas=tuple(
                    (
                        scope_class,
                        scope_tag,
                        -1 if expire_hour else 0,
                        0 if expire_hour else -1,
                        cost,
                    )
                    for scope_class, scope_tag in _row_scope_pairs(row)
                ),
                revision=revision,
                now_ns=now_ns,
            )

    @classmethod
    def _advance_projection_in_transaction(
        cls, connection: sqlite3.Connection, *, now_ns: int
    ) -> tuple[int, int, int]:
        connection.row_factory = sqlite3.Row
        new_hour = now_ns - HOUR_NS
        new_day = now_ns - DAY_NS
        state = connection.execute(
            "SELECT * FROM budget_window_projection_state WHERE singleton=1"
        ).fetchone()
        if (
            state is None
            or state["projection_version"] != PROJECTION_VERSION
            or state["policy_version"] != BUDGET_POLICY_VERSION
            or new_hour < int(state["hour_cutoff_ns"])
            or new_day < int(state["day_cutoff_ns"])
        ):
            cls._rebuild_projection(connection, now_ns=now_ns)
            state = connection.execute(
                "SELECT * FROM budget_window_projection_state WHERE singleton=1"
            ).fetchone()
            assert state is not None
            return int(state["hour_cutoff_ns"]), int(state["day_cutoff_ns"]), int(state["revision"])
        old_hour = int(state["hour_cutoff_ns"])
        old_day = int(state["day_cutoff_ns"])
        if new_hour == old_hour and new_day == old_day:
            return old_hour, old_day, int(state["revision"])
        revision = int(state["revision"]) + 1
        cls._expire_rows(
            connection,
            lower=old_hour,
            upper=new_hour,
            expire_hour=True,
            revision=revision,
            now_ns=now_ns,
        )
        cls._expire_rows(
            connection,
            lower=old_day,
            upper=new_day,
            expire_hour=False,
            revision=revision,
            now_ns=now_ns,
        )
        connection.execute(
            "UPDATE budget_window_projection_state SET hour_cutoff_ns=?, day_cutoff_ns=?, "
            "revision=? WHERE singleton=1",
            (new_hour, new_day, revision),
        )
        return new_hour, new_day, revision

    def advance_projection(self, *, now_ns: int) -> None:
        try:
            with closing(self._connect()) as connection:  # type: ignore[attr-defined]
                connection.execute("BEGIN IMMEDIATE")
                try:
                    self._advance_projection_in_transaction(connection, now_ns=now_ns)
                    connection.commit()
                except (sqlite3.Error, SafetyControlStorageError):
                    connection.rollback()
                    raise
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    @staticmethod
    def _all_window_totals(
        connection: sqlite3.Connection,
        *,
        scope_tags: BudgetScopeTags,
        now_ns: int,
    ) -> dict[str, tuple[int, int, int]]:
        del now_ns
        result: dict[str, tuple[int, int, int]] = {}
        for scope_class, scope_tag in _scope_pairs(scope_tags):
            row = connection.execute(
                "SELECT attempts_1h, attempts_24h, cost_24h_micro_usd "
                "FROM budget_window_totals WHERE scope_class=? AND scope_tag=?",
                (scope_class, scope_tag),
            ).fetchone()
            result[scope_class] = (
                (0, 0, 0) if row is None else (int(row[0]), int(row[1]), int(row[2]))
            )
        return result

    def reserve_budget(
        self,
        *,
        execution_id: UUID,
        attempt_number: int,
        scope_tags: BudgetScopeTags,
        pricing_policy: PricingPolicy,
        now_ns: int,
    ) -> BudgetReservation:
        started = time.perf_counter()
        self._require_budget_inputs(  # type: ignore[attr-defined]
            execution_id, attempt_number, scope_tags, pricing_policy, now_ns
        )
        try:
            with closing(self._connect()) as connection:  # type: ignore[attr-defined]
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    existing = connection.execute(
                        "SELECT r.*, o.player_scope_tag, o.npc_scope_tag, "
                        "o.player_npc_scope_tag FROM budget_reservations r "
                        "JOIN budget_execution_owners o USING(execution_id) "
                        "WHERE r.execution_id=? AND r.attempt_number=?",
                        (str(execution_id), attempt_number),
                    ).fetchone()
                    if existing is not None:
                        reservation = cast(
                            BudgetReservation,
                            self._reservation_from_row(existing, scope_tags),  # type: ignore[attr-defined]
                        )
                        if (
                            reservation.pricing_version != pricing_policy.version
                            or reservation.reserved_micro_usd
                            != pricing_policy.max_reservation_micro_usd
                        ):
                            raise SafetyControlStorageError
                        connection.commit()
                        return reservation
                    admission = connection.execute(
                        "SELECT * FROM execution_admissions WHERE execution_id=?",
                        (str(execution_id),),
                    ).fetchone()
                    if admission is None or not self._budget_admission_matches(  # type: ignore[attr-defined]
                        admission, scope_tags
                    ):
                        raise SafetyControlStorageError
                    owner = connection.execute(
                        "SELECT * FROM budget_execution_owners WHERE execution_id=?",
                        (str(execution_id),),
                    ).fetchone()
                    if owner is None:
                        connection.execute(
                            "INSERT INTO budget_execution_owners "
                            "(execution_id,policy_version,player_scope_tag,npc_scope_tag,"
                            "player_npc_scope_tag,created_at_ns) VALUES (?,?,?,?,?,?)",
                            (
                                str(execution_id),
                                BUDGET_POLICY_VERSION,
                                scope_tags.player_scope_tag,
                                scope_tags.npc_scope_tag,
                                scope_tags.player_npc_scope_tag,
                                now_ns,
                            ),
                        )
                    elif not self._budget_owner_matches(owner, scope_tags):  # type: ignore[attr-defined]
                        raise SafetyControlStorageError
                    existing_attempts = int(
                        connection.execute(
                            "SELECT COUNT(*) FROM budget_reservations "
                            "WHERE execution_id=? AND status<>'released'",
                            (str(execution_id),),
                        ).fetchone()[0]
                    )
                    if existing_attempts >= 2 or attempt_number != existing_attempts + 1:
                        raise BudgetRejectedError(
                            BudgetLimitClass.EXECUTION_ATTEMPTS,
                            scope_tags=scope_tags,
                            pricing_policy=pricing_policy,
                        )
                    _, _, revision = self._advance_projection_in_transaction(
                        connection, now_ns=now_ns
                    )
                    windows = self._all_window_totals(
                        connection, scope_tags=scope_tags, now_ns=now_ns
                    )
                    warning = False
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
                        proposed = windows[scope][2] + pricing_policy.max_reservation_micro_usd
                        if proposed > spec.hard_limit:
                            raise BudgetRejectedError(
                                spec.limit_class,
                                scope_tags=scope_tags,
                                pricing_policy=pricing_policy,
                            )
                        warning = warning or proposed >= spec.warning_threshold
                    connection.execute(
                        "INSERT INTO budget_reservations "
                        "(execution_id,attempt_number,policy_version,pricing_version,provider_kind,"
                        "provider_model,reserved_micro_usd,soft_warning,status,reserved_at_ns) "
                        "VALUES (?,?,?,?,?,?,?,?, 'reserved',?)",
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
                    self._apply_scope_deltas(
                        connection,
                        deltas=tuple(
                            (
                                scope_class,
                                scope_tag,
                                1,
                                1,
                                pricing_policy.max_reservation_micro_usd,
                            )
                            for scope_class, scope_tag in _scope_pairs(scope_tags)
                        ),
                        revision=revision,
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
        finally:
            if hasattr(self, "_reserve_samples"):
                self._reserve_samples.append((time.perf_counter() - started) * 1_000)

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
        self._require_reservation(reservation)  # type: ignore[attr-defined]
        self._require_time(now_ns)  # type: ignore[attr-defined]
        if type(actual_cost_micro_usd) is not int or not (
            0 <= actual_cost_micro_usd <= reservation.reserved_micro_usd
        ):
            raise ValueError("Budget settlement cost is invalid")
        prompt_tokens = 0 if usage is None else usage.prompt_tokens
        completion_tokens = 0 if usage is None else usage.completion_tokens
        released = reservation.reserved_micro_usd - actual_cost_micro_usd
        try:
            with closing(self._connect()) as connection:  # type: ignore[attr-defined]
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    existing = connection.execute(
                        "SELECT * FROM budget_settlements WHERE execution_id=? "
                        "AND attempt_number=?",
                        (str(reservation.execution_id), reservation.attempt_number),
                    ).fetchone()
                    if existing is not None:
                        settlement = cast(
                            BudgetSettlement,
                            self._settlement_from_row(existing),  # type: ignore[attr-defined]
                        )
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
                    if (
                        row is None
                        or row["status"] != "dispatched"
                        or int(row["reserved_micro_usd"]) != reservation.reserved_micro_usd
                        or row["pricing_version"] != reservation.pricing_version
                    ):
                        raise SafetyControlStorageError
                    _, day_cutoff, revision = self._advance_projection_in_transaction(
                        connection, now_ns=now_ns
                    )
                    connection.execute(
                        "INSERT INTO budget_settlements "
                        "(execution_id,attempt_number,policy_version,pricing_version,"
                        "reserved_micro_usd,actual_cost_micro_usd,released_micro_usd,"
                        "prompt_tokens,completion_tokens,conservative,reason,settled_at_ns) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
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
                        "UPDATE budget_reservations SET status='settled',settled_at_ns=? "
                        "WHERE execution_id=? AND attempt_number=? AND status='dispatched'",
                        (now_ns, str(reservation.execution_id), reservation.attempt_number),
                    )
                    if int(row["reserved_at_ns"]) > day_cutoff:
                        self._apply_scope_deltas(
                            connection,
                            deltas=tuple(
                                (
                                    scope_class,
                                    scope_tag,
                                    0,
                                    0,
                                    actual_cost_micro_usd - reservation.reserved_micro_usd,
                                )
                                for scope_class, scope_tag in _row_scope_pairs(row)
                            ),
                            revision=revision,
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
        self._require_reservation(reservation)  # type: ignore[attr-defined]
        self._require_time(now_ns)  # type: ignore[attr-defined]
        if reason != "cancelled_before_dispatch":
            raise ValueError("Budget release reason is invalid")
        try:
            with closing(self._connect()) as connection:  # type: ignore[attr-defined]
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    row = connection.execute(
                        "SELECT r.status,r.reserved_at_ns,r.reserved_micro_usd,"
                        "o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag "
                        "FROM budget_reservations r JOIN budget_execution_owners o "
                        "USING(execution_id) WHERE r.execution_id=? AND r.attempt_number=?",
                        (str(reservation.execution_id), reservation.attempt_number),
                    ).fetchone()
                    if row is None or row["status"] in ("dispatched", "settled"):
                        raise SafetyControlStorageError
                    if row["status"] == "reserved":
                        hour_cutoff, day_cutoff, revision = self._advance_projection_in_transaction(
                            connection, now_ns=now_ns
                        )
                        connection.execute(
                            "UPDATE budget_reservations SET status='released',released_at_ns=?,"
                            "release_reason=? WHERE execution_id=? AND attempt_number=?",
                            (
                                now_ns,
                                reason,
                                str(reservation.execution_id),
                                reservation.attempt_number,
                            ),
                        )
                        reserved_at = int(row["reserved_at_ns"])
                        self._apply_scope_deltas(
                            connection,
                            deltas=tuple(
                                (
                                    scope_class,
                                    scope_tag,
                                    -int(reserved_at > hour_cutoff),
                                    -int(reserved_at > day_cutoff),
                                    -int(row["reserved_micro_usd"])
                                    if reserved_at > day_cutoff
                                    else 0,
                                )
                                for scope_class, scope_tag in _row_scope_pairs(row)
                            ),
                            revision=revision,
                            now_ns=now_ns,
                        )
                    connection.commit()
                except (sqlite3.Error, SafetyControlStorageError):
                    connection.rollback()
                    raise
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error

    def recover_open_budget_attempts(self, *, now_ns: int) -> tuple[int, int]:
        self._require_time(now_ns)  # type: ignore[attr-defined]
        try:
            with closing(self._connect()) as connection:  # type: ignore[attr-defined]
                connection.row_factory = sqlite3.Row
                connection.execute("BEGIN IMMEDIATE")
                try:
                    dispatched = connection.execute(
                        "SELECT * FROM budget_reservations WHERE status='dispatched'"
                    ).fetchall()
                    for row in dispatched:
                        connection.execute(
                            "INSERT INTO budget_settlements "
                            "(execution_id,attempt_number,policy_version,pricing_version,"
                            "reserved_micro_usd,actual_cost_micro_usd,released_micro_usd,"
                            "prompt_tokens,completion_tokens,conservative,reason,settled_at_ns) "
                            "VALUES (?,?,?,?,?,?,0,0,0,1,'abandoned_after_restart',?)",
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
                    settled = connection.execute(
                        "UPDATE budget_reservations SET status='settled',settled_at_ns=? "
                        "WHERE status='dispatched'",
                        (now_ns,),
                    ).rowcount
                    released = connection.execute(
                        "UPDATE budget_reservations SET status='released',released_at_ns=?,"
                        "release_reason='cancelled_before_dispatch' WHERE status='reserved'",
                        (now_ns,),
                    ).rowcount
                    self._rebuild_projection(connection, now_ns=now_ns)
                    connection.commit()
                    return released, settled
                except (sqlite3.Error, SafetyControlStorageError):
                    connection.rollback()
                    raise
        except SafetyControlStorageError:
            raise
        except sqlite3.Error as error:
            raise SafetyControlStorageError from error


class SetBasedProjectionMixin:
    """V18 fixed-shape delta candidate layered over the V14 ledger model."""

    _set_based_counts: ClassVar[dict[str, int]] = {}
    _set_based_count_lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def _reset_set_based_counts(cls) -> None:
        with cls._set_based_count_lock:
            cls._set_based_counts = {
                "scope_delta_apply_batches": 0,
                "scope_delta_rows": 0,
                "scope_delta_sql_statements": 0,
                "window_total_read_batches": 0,
                "expiration_apply_batches": 0,
                "expiration_sql_statements": 0,
            }

    @classmethod
    def _count_set_based(cls, name: str, amount: int = 1) -> None:
        with cls._set_based_count_lock:
            cls._set_based_counts[name] = cls._set_based_counts.get(name, 0) + amount

    def set_based_operation_snapshot(self) -> dict[str, int]:
        with type(self)._set_based_count_lock:
            return dict(type(self)._set_based_counts)

    @classmethod
    def _apply_scope_deltas(
        cls,
        connection: sqlite3.Connection,
        *,
        deltas: tuple[tuple[str, str, int, int, int], ...],
        revision: int,
        now_ns: int,
    ) -> None:
        if (
            len(deltas) != 4
            or {item[0] for item in deltas} != {"player_npc", "player", "npc", "global"}
            or len({(item[0], item[1]) for item in deltas}) != 4
        ):
            raise SafetyControlStorageError
        seed_parameters: list[str | int] = []
        update_parameters: list[str | int] = []
        for scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h in deltas:
            seed_parameters.extend((scope_class, scope_tag, revision, now_ns))
            update_parameters.extend((scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h))
        update_parameters.extend((revision, now_ns))
        connection.execute(SET_BASED_ZERO_SEED_SQL, tuple(seed_parameters))
        connection.execute(SET_BASED_UPDATE_SQL, tuple(update_parameters))
        cls._count_set_based("scope_delta_apply_batches")
        cls._count_set_based("scope_delta_rows", len(deltas))
        cls._count_set_based("scope_delta_sql_statements", 2)

    @classmethod
    def _expire_rows(
        cls,
        connection: sqlite3.Connection,
        *,
        lower: int,
        upper: int,
        expire_hour: bool,
        revision: int,
        now_ns: int,
    ) -> None:
        if upper <= lower:
            return
        flag = int(expire_hour)
        connection.execute(
            SET_BASED_EXPIRATION_SEED_SQL,
            (lower, upper, revision, now_ns),
        )
        connection.execute(
            SET_BASED_EXPIRATION_UPDATE_SQL,
            (lower, upper, flag, flag, flag, revision, now_ns),
        )
        cls._count_set_based("expiration_apply_batches")
        cls._count_set_based("expiration_sql_statements", 2)

    @classmethod
    def _all_window_totals(
        cls,
        connection: sqlite3.Connection,
        *,
        scope_tags: BudgetScopeTags,
        now_ns: int,
    ) -> dict[str, tuple[int, int, int]]:
        del now_ns
        pairs = _scope_pairs(scope_tags)
        parameters = tuple(value for pair in pairs for value in pair)
        rows = connection.execute(SET_BASED_TOTALS_SQL, parameters).fetchall()
        if len(rows) != 4 or {str(row[0]) for row in rows} != {
            "player_npc",
            "player",
            "npc",
            "global",
        }:
            raise SafetyControlStorageError
        cls._count_set_based("window_total_read_batches")
        return {str(row[0]): (int(row[1]), int(row[2]), int(row[3])) for row in rows}


class SingleWriteProjectionMixin(SetBasedProjectionMixin):
    """V19 candidate: one lifecycle write and no no-op expiration write."""

    @classmethod
    def _reset_set_based_counts(cls) -> None:
        super()._reset_set_based_counts()
        with cls._set_based_count_lock:
            cls._set_based_counts.update(
                {
                    "scope_delta_upsert_statements": 0,
                    "scope_delta_update_statements": 0,
                    "expiration_probe_statements": 0,
                    "expiration_update_statements": 0,
                    "expiration_skipped_write_batches": 0,
                }
            )

    @staticmethod
    def _validate_single_write_deltas(
        deltas: tuple[tuple[str, str, int, int, int], ...],
    ) -> None:
        if (
            len(deltas) != 4
            or {item[0] for item in deltas} != {"player_npc", "player", "npc", "global"}
            or len({(item[0], item[1]) for item in deltas}) != 4
        ):
            raise SafetyControlStorageError

    @classmethod
    def _apply_scope_deltas(
        cls,
        connection: sqlite3.Connection,
        *,
        deltas: tuple[tuple[str, str, int, int, int], ...],
        revision: int,
        now_ns: int,
    ) -> None:
        cls._validate_single_write_deltas(deltas)
        is_reserve = all(
            attempts_1h == 1 and attempts_24h == 1 and cost_24h >= 0
            for _, _, attempts_1h, attempts_24h, cost_24h in deltas
        )
        if is_reserve:
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
                    )
                )
            connection.execute(SINGLE_WRITE_UPSERT_SQL, tuple(parameters))
            cls._count_set_based("scope_delta_upsert_statements")
        else:
            parameters = []
            for scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h in deltas:
                parameters.extend((scope_class, scope_tag, attempts_1h, attempts_24h, cost_24h))
            parameters.extend((revision, now_ns))
            rows = connection.execute(SINGLE_WRITE_UPDATE_SQL, tuple(parameters)).fetchall()
            if len(rows) != 4 or {(str(row[0]), str(row[1])) for row in rows} != {
                (scope_class, scope_tag) for scope_class, scope_tag, *_ in deltas
            }:
                raise SafetyControlStorageError
            cls._count_set_based("scope_delta_update_statements")
        cls._count_set_based("scope_delta_apply_batches")
        cls._count_set_based("scope_delta_rows", len(deltas))
        cls._count_set_based("scope_delta_sql_statements")

    @classmethod
    def _advance_projection_in_transaction(
        cls, connection: sqlite3.Connection, *, now_ns: int
    ) -> tuple[int, int, int]:
        connection.row_factory = sqlite3.Row
        new_hour = now_ns - HOUR_NS
        new_day = now_ns - DAY_NS
        state = connection.execute(
            "SELECT * FROM budget_window_projection_state WHERE singleton=1"
        ).fetchone()
        if (
            state is None
            or state["projection_version"] != PROJECTION_VERSION
            or state["policy_version"] != BUDGET_POLICY_VERSION
            or new_hour < int(state["hour_cutoff_ns"])
            or new_day < int(state["day_cutoff_ns"])
        ):
            cast(Any, cls)._rebuild_projection(connection, now_ns=now_ns)
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
        if new_hour == old_hour and new_day == old_day:
            return old_hour, old_day, int(state["revision"])
        revision = int(state["revision"]) + 1
        probe_parameters = (old_hour, new_hour, old_day, new_day)
        has_expired = connection.execute(
            SINGLE_WRITE_EXPIRATION_PROBE_SQL,
            probe_parameters,
        ).fetchone()
        cls._count_set_based("expiration_apply_batches")
        cls._count_set_based("expiration_probe_statements")
        cls._count_set_based("expiration_sql_statements")
        if has_expired is None:
            cls._count_set_based("expiration_skipped_write_batches")
        else:
            update_parameters = (
                old_hour,
                new_hour,
                old_day,
                new_day,
                old_hour,
                new_hour,
                old_day,
                new_day,
                revision,
                now_ns,
            )
            updated = connection.execute(
                SINGLE_WRITE_EXPIRATION_UPDATE_SQL,
                update_parameters,
            ).fetchall()
            if not updated:
                raise SafetyControlStorageError
            cls._count_set_based("expiration_update_statements")
            cls._count_set_based("expiration_sql_statements")
        connection.execute(
            "UPDATE budget_window_projection_state SET hour_cutoff_ns=?, day_cutoff_ns=?, "
            "revision=? WHERE singleton=1",
            (new_hour, new_day, revision),
        )
        return new_hour, new_day, revision


class CandidateSqliteSafetyControlRepository(
    CandidateProjectionMixin, SqliteSafetyControlRepository
):
    pass


class CandidateMemoryControl(CandidateProjectionMixin, benchmark._MemoryControl):
    def __init__(self, root: Path) -> None:
        self._reserve_samples = []
        self._samples_saved = False
        super().__init__(root)

    def close(self) -> None:
        if not self._samples_saved:
            RESERVE_SAMPLE_RUNS.append(tuple(self._reserve_samples))
            self._samples_saved = True
        super().close()


class SetBasedCandidateSqliteSafetyControlRepository(
    SetBasedProjectionMixin, CandidateSqliteSafetyControlRepository
):
    pass


class SetBasedCandidateMemoryControl(SetBasedProjectionMixin, CandidateMemoryControl):
    def __init__(self, root: Path) -> None:
        type(self)._reset_set_based_counts()
        super().__init__(root)


class SingleWriteCandidateSqliteSafetyControlRepository(
    SingleWriteProjectionMixin, CandidateSqliteSafetyControlRepository
):
    pass


class SingleWriteCandidateMemoryControl(SingleWriteProjectionMixin, CandidateMemoryControl):
    def __init__(self, root: Path) -> None:
        type(self)._reset_set_based_counts()
        super().__init__(root)


class CandidateStageProbe(benchmark._MemoryStageProbe):
    """Require one flat, ordered stage sequence for every synthetic execution."""

    def __init__(self) -> None:
        super().__init__()
        self._position = 0
        self._completed_executions = 0

    def _expect(self, stage: str) -> None:
        expected = benchmark.MEMORY_STAGE_ALLOWLIST[self._position]
        if stage != expected:
            raise RuntimeError("Synthetic stage ownership is incomplete")

    def _advance(self) -> None:
        self._position += 1
        if self._position == len(benchmark.MEMORY_STAGE_ALLOWLIST):
            self._position = 0
            self._completed_executions += 1

    def run(self, stage: str, operation: Callable[[], Any]) -> Any:
        self._expect(stage)
        try:
            return super().run(stage, operation)
        finally:
            self._advance()

    async def run_async(self, stage: str, operation: Callable[[], Awaitable[Any]]) -> Any:
        self._expect(stage)
        try:
            return await super().run_async(stage, operation)
        finally:
            self._advance()

    def summary(self) -> dict[str, dict[str, int | float]]:
        if self._position != 0 or self._completed_executions != benchmark.MEMORY_TRACE_COUNT:
            raise RuntimeError("Synthetic stage ownership is incomplete")
        return super().summary()


def _request(index: int) -> Any:
    return DialogueRequestV1(
        request_id=UUID(int=20_000 + index),
        player_id=f"projection_player_{index:04d}",
        npc_id=("neon_guide", "signal_archivist", "night_courier")[index % 3],
        conversation_id=UUID(int=30_000 + index),
        message="Synthetic V14 projection workload.",
    )


class Clock:
    def __init__(self) -> None:
        self.now_ns = BASE_NS

    def __call__(self) -> int:
        return self.now_ns

    def advance(self, seconds: int = 60) -> None:
        self.now_ns += seconds * 1_000_000_000


def _control(repository: SqliteSafetyControlRepository, clock: Clock) -> SafetyControl:
    return SafetyControl(
        repository=repository,
        scope_key=SYNTHETIC_KEY,
        clock_ns=clock,
        monotonic_clock=time.monotonic,
        pricing_policy=PricingPolicy.zero_cost(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
        ),
    )


def _semantic_gate(
    root: Path,
    repository_type: type[CandidateSqliteSafetyControlRepository] = (
        CandidateSqliteSafetyControlRepository
    ),
    directory_name: str = "semantic",
) -> dict[str, object]:
    database = root / directory_name / "control.sqlite3"
    repository = repository_type(database_path=database, allowed_root=database.parent)
    repository.initialize()
    clock = Clock()
    control = _control(repository, clock)

    def reserve(index: int) -> BudgetReservation:
        item = _request(index)
        execution = UUID(int=40_000 + index)
        control.admit_execution(request=item, execution_id=execution)
        return control.reserve_budget(request=item, execution_id=execution, attempt_number=1)

    with ThreadPoolExecutor(max_workers=4) as pool:
        reservations = tuple(pool.map(reserve, range(16)))
    for reservation in reservations:
        control.mark_budget_dispatched(reservation)
        control.settle_budget(reservation, usage=ProviderUsage(0, 0))
    with closing(repository._connect()) as connection:
        assert_projection_matches_ledger(connection, clock())
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    attempts = repository.budget_attempt_count()
    settlements = repository.budget_settlement_count()
    repository.close()
    return {
        "concurrent_reservations": attempts,
        "settlements": settlements,
        "integrity": integrity,
        "foreign_key_failures": len(foreign_keys),
        "projection_match": True,
    }


async def _full_control_workload(control: SafetyControl, count: int, clock: Clock) -> None:
    provider = FakeProvider(benchmark._completion() for _ in range(count))
    for index in range(count):
        item = _request(1_000 + index)
        execution = UUID(int=50_000 + index)
        control.admit_ingress(peer_host="127.0.0.1")
        control.admit_execution(request=item, execution_id=execution)
        control.check_provider_breaker(execution_id=execution)
        reservation = control.reserve_budget(request=item, execution_id=execution, attempt_number=1)
        permit = await control.acquire_provider_permit(request=item, execution_id=execution)
        control.mark_budget_dispatched(reservation)
        completion = await provider.complete(
            ProviderRequest(
                system_prompt="Synthetic V14 projection persona.",
                user_message=item.message,
                model="fake-model",
                temperature=0.6,
                max_tokens=256,
                timeout_seconds=12,
            )
        )
        control.settle_budget(reservation, usage=completion.usage)
        control.record_provider_success(execution_id=execution)
        await control.release_provider_permit(permit, reason="completed")
        clock.advance()


def _space_gate(
    root: Path,
    repository_type: type[CandidateSqliteSafetyControlRepository] = (
        CandidateSqliteSafetyControlRepository
    ),
) -> dict[str, object]:
    database = root / "space" / "control.sqlite3"
    repository = repository_type(database_path=database, allowed_root=database.parent)
    repository.initialize()
    repository.close()
    before = database.stat().st_size
    repository = repository_type(database_path=database, allowed_root=database.parent)
    repository.initialize()
    clock = Clock()
    control = _control(repository, clock)
    asyncio.run(_full_control_workload(control, 100, clock))
    repository.advance_projection(now_ns=clock())
    with closing(repository._connect()) as connection:
        assert_projection_matches_ledger(connection, clock())
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        freelist = int(connection.execute("PRAGMA freelist_count").fetchone()[0])
        plan = tuple(
            str(row[3])
            for row in connection.execute(
                "EXPLAIN QUERY PLAN SELECT r.execution_id FROM budget_reservations r "
                "JOIN budget_execution_owners o USING(execution_id) "
                "WHERE r.reserved_at_ns>? AND r.reserved_at_ns<=?",
                (BASE_NS - DAY_NS, BASE_NS),
            )
        )
    repository.close()
    after = database.stat().st_size
    growth = after - before
    return {
        "before_bytes": before,
        "after_bytes": after,
        "growth_bytes": growth,
        "limit_bytes": 256 * 1024,
        "page_size": page_size,
        "page_count": page_count,
        "freelist_pages": freelist,
        "query_plan": plan,
        "passed": growth <= 256 * 1024,
    }


def _segment(values: Iterable[float]) -> dict[str, float]:
    data = tuple(values)
    if len(data) < 100:
        raise ValueError("Synthetic reserve sample is incomplete")
    ordered = sorted(data)
    return {
        "median_ms": round(float(statistics.median(data)), 6),
        "p95_ms": round(float(ordered[max(0, int(len(ordered) * 0.95) - 1)]), 6),
    }


def _stable_tail(segments: dict[str, dict[str, float]]) -> bool:
    early = segments["early_steady_100"]["median_ms"]
    late = segments["late_steady_100"]["median_ms"]
    return late <= max(early * 1.25, early + 0.05)


def _steady_workload_signature(sample_index: int) -> dict[str, int]:
    if sample_index < 100 or sample_index >= benchmark.MEMORY_TRACE_COUNT:
        raise ValueError("Synthetic stability sample is outside the steady range")
    return {
        "new_scope_rows": 2,
        "hour_expired_rows": 1,
        "day_expired_rows": 0,
        "total_adjustment_groups": 8,
    }


def _summarize_stability_runs(runs: Iterable[tuple[float, ...]]) -> dict[str, object]:
    complete = tuple(runs)
    if len(complete) != benchmark.RUN_COUNT:
        raise ValueError("Synthetic stability requires all five measured runs")
    for run in complete:
        if len(run) != benchmark.MEMORY_TRACE_COUNT:
            raise ValueError("Synthetic reserve sample is incomplete")

    signatures = {
        tuple(_steady_workload_signature(index).items())
        for start, stop in STABILITY_SEGMENT_RANGES.values()
        for index in range(start, stop)
    }
    if len(signatures) != 1:
        raise RuntimeError("Synthetic stability segments do not have equal work")
    workload_signature = dict(next(iter(signatures)))

    per_run: list[dict[str, object]] = []
    for run in complete:
        segments = {
            name: _segment(run[start:stop])
            for name, (start, stop) in STABILITY_SEGMENT_RANGES.items()
        }
        per_run.append({"segments": segments, "stable_tail": _stable_tail(segments)})

    aggregate = {
        name: {
            metric: round(
                float(
                    statistics.median(
                        cast(dict[str, dict[str, float]], item["segments"])[name][metric]
                        for item in per_run
                    )
                ),
                6,
            )
            for metric in ("median_ms", "p95_ms")
        }
        for name in STABILITY_SEGMENT_RANGES
    }
    return {
        "run_count": len(complete),
        "compared_execution_ranges": {
            name: [start + 1, stop] for name, (start, stop) in STABILITY_SEGMENT_RANGES.items()
        },
        "workload_signature": workload_signature,
        "per_run_segments": per_run,
        "aggregate_segments": aggregate,
        "stable_tail": _stable_tail(aggregate),
    }


def _p95_attribution_verdict(
    *,
    baseline_p95: tuple[float, ...],
    recorded_p95: tuple[float, ...],
    recorded_aggregate_p95: float,
    recorded_aggregate_p99: float,
    throughput_ratio: float,
    stable_tail: bool,
) -> dict[str, object]:
    if len(baseline_p95) != 5 or len(recorded_p95) != 5:
        raise ValueError("P95 attribution requires exactly five paired runs")
    common = sum(
        baseline > 2.0 and recorded > 2.0
        for baseline, recorded in zip(baseline_p95, recorded_p95, strict=True)
    )
    passed = (
        recorded_aggregate_p95 <= 2.0
        and recorded_aggregate_p99 <= 5.0
        and throughput_ratio >= 0.8
        and stable_tail
    )
    return {
        "baseline_p95_exceed_count": sum(value > 2.0 for value in baseline_p95),
        "recorded_p95_exceed_count": sum(value > 2.0 for value in recorded_p95),
        "common_p95_exceed_count": common,
        "common_foundation_blocker": common >= 4,
        "passed": passed,
    }


def _single_run_summary(scenario: str, run: PerformanceRun) -> dict[str, object]:
    ordered = sorted(run.samples_ms)

    def percentile(quantile: float) -> float:
        return round(float(ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]), 6)

    return {
        "scenario": scenario,
        "sample_count": len(run.samples_ms),
        "p50_ms": percentile(0.50),
        "p95_ms": percentile(0.95),
        "p99_ms": percentile(0.99),
        "throughput_per_second": round(run.throughput_per_second, 6),
        "provider_dispatch_count": run.provider_dispatch_count,
    }


def _run_attribution_sample(
    root: Path, *, scenario: str
) -> tuple[PerformanceRun, tuple[float, ...], dict[str, object]]:
    factories: dict[str, Callable[[], ObservabilityRecorder]] = {
        "no_recorder_control": NoOpObservabilityRecorder,
        "in_memory_control": InMemoryObservabilityRecorder,
    }
    if scenario not in factories:
        raise ValueError("P95 attribution scenario is invalid")
    RESERVE_SAMPLE_RUNS.clear()
    original = benchmark._MemoryControl
    before_counts = gc.get_count()
    before_stats = tuple(int(item["collections"]) for item in gc.get_stats())
    cpu_started = time.process_time_ns()
    wall_started = time.perf_counter_ns()
    benchmark.__dict__["_MemoryControl"] = CandidateMemoryControl
    try:
        run = asyncio.run(benchmark._memory_control_run(root, factories[scenario]))
    finally:
        benchmark.__dict__["_MemoryControl"] = original
    wall_elapsed = time.perf_counter_ns() - wall_started
    cpu_elapsed = time.process_time_ns() - cpu_started
    after_stats = tuple(int(item["collections"]) for item in gc.get_stats())
    if len(RESERVE_SAMPLE_RUNS) != 1:
        raise RuntimeError("P95 reserve attribution is incomplete")
    metadata = {
        "gc_enabled": gc.isenabled(),
        "gc_count_before": list(before_counts),
        "gc_count_after": list(gc.get_count()),
        "gc_collection_delta": [
            after - before for before, after in zip(before_stats, after_stats, strict=True)
        ],
        "process_cpu_ms": round(cpu_elapsed / 1_000_000, 6),
        "wall_ms": round(wall_elapsed / 1_000_000, 6),
    }
    return run, RESERVE_SAMPLE_RUNS[0], metadata


def _validate_p95_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = P95_ATTRIBUTION_ROOT.resolve(strict=True)
    if resolved != approved or root.is_symlink() or root.is_junction():
        raise ValueError("V14 p95 attribution root is not approved")
    expected = {"tmp", "attribution-01"}
    if not expected <= {item.name for item in resolved.iterdir() if item.is_dir()}:
        raise ValueError("V14 p95 attribution directory manifest is incomplete")
    if (resolved / "summary-attribution-01.json").exists():
        raise ValueError("V14 p95 attribution summary already exists")
    return resolved


def run_p95_attribution(root: Path) -> dict[str, object]:
    resolved = _validate_p95_root(root)
    run_root = resolved / "attribution-01"
    RESERVE_SAMPLE_RUNS.clear()
    original = benchmark._MemoryControl
    benchmark.__dict__["_MemoryControl"] = CandidateMemoryControl
    try:
        protocol = benchmark._paired_memory_protocol(run_root, stage_attribution=False)
    finally:
        benchmark.__dict__["_MemoryControl"] = original
    complete = [run for run in RESERVE_SAMPLE_RUNS if len(run) == benchmark.MEMORY_TRACE_COUNT]
    expected = (benchmark.MEMORY_PROTOCOL_WARMUP_PAIRS + benchmark.RUN_COUNT) * 2
    if len(complete) != expected:
        raise RuntimeError("P95 reserve attribution is incomplete")
    recorded_reserve_samples = tuple(complete[index] for index in range(3, len(complete), 2))
    baseline = summarize_performance_runs(
        PerformanceScenario.NO_RECORDER_CONTROL, protocol.baseline_runs
    )
    recorded = summarize_performance_runs(
        PerformanceScenario.IN_MEMORY_CONTROL, protocol.recorded_runs
    )
    stability = _summarize_stability_runs(recorded_reserve_samples)
    ratio = recorded.throughput_per_second / baseline.throughput_per_second
    run_metadata = list(protocol.runtime_runs)
    measured_metadata = [item for item in run_metadata if not cast(bool, item["warmup"])]
    baseline_p95 = tuple(
        cast(float, cast(dict[str, Any], item["summary"])["p95_ms"])
        for item in measured_metadata
        if item["scenario"] == "no_recorder_control"
    )
    recorded_p95 = tuple(
        cast(float, cast(dict[str, Any], item["summary"])["p95_ms"])
        for item in measured_metadata
        if item["scenario"] == "in_memory_control"
    )
    verdict = _p95_attribution_verdict(
        baseline_p95=baseline_p95,
        recorded_p95=recorded_p95,
        recorded_aggregate_p95=recorded.p95_ms,
        recorded_aggregate_p99=recorded.p99_ms,
        throughput_ratio=ratio,
        stable_tail=cast(bool, stability["stable_tail"]),
    )
    status = "passed"
    if not cast(bool, verdict["passed"]):
        status = (
            "common_foundation_p95_blocker"
            if cast(bool, verdict["common_foundation_blocker"])
            else "performance_gate_failed"
        )
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    result = {
        "schema_version": 1,
        "status": status,
        "protocol": benchmark.memory_protocol_config(),
        "run_order": [list(order) for order in P95_ATTRIBUTION_ORDER],
        "environment": {
            "python_version": python_version,
            "cpu_count": os.cpu_count(),
            "thread_count_before_summary": threading.active_count(),
            "gc_enabled": gc.isenabled(),
            "perf_counter_resolution_ns": round(
                time.get_clock_info("perf_counter").resolution * 1_000_000_000
            ),
            "process_time_resolution_ns": round(
                time.get_clock_info("process_time").resolution * 1_000_000_000
            ),
        },
        "runs": run_metadata,
        "aggregate": {
            "baseline": baseline.as_dict(),
            "recorded": recorded.as_dict(),
            "recorder_p95_delta_ms": round(recorded.p95_ms - baseline.p95_ms, 6),
            "recorder_p99_delta_ms": round(recorded.p99_ms - baseline.p99_ms, 6),
            "paired_throughput_ratio": round(ratio, 6),
        },
        "reserve_stability": stability,
        "verdict": verdict,
    }
    summary_path = resolved / "summary-attribution-01.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def _performance_gate(
    root: Path,
    memory_control_type: type[CandidateMemoryControl] = CandidateMemoryControl,
    directory_name: str = "performance",
) -> dict[str, object]:
    RESERVE_SAMPLE_RUNS.clear()
    original = benchmark._MemoryControl
    benchmark.__dict__["_MemoryControl"] = memory_control_type
    try:
        protocol = benchmark._paired_memory_protocol(root / directory_name, stage_attribution=False)
    finally:
        benchmark.__dict__["_MemoryControl"] = original
    baseline_runs = protocol.baseline_runs
    recorded_runs = protocol.recorded_runs
    baseline = summarize_performance_runs(PerformanceScenario.NO_RECORDER_CONTROL, baseline_runs)
    recorded = summarize_performance_runs(PerformanceScenario.IN_MEMORY_CONTROL, recorded_runs)
    ratio = recorded.throughput_per_second / baseline.throughput_per_second
    complete = [run for run in RESERVE_SAMPLE_RUNS if len(run) == benchmark.MEMORY_TRACE_COUNT]
    if not complete:
        raise RuntimeError("Synthetic reserve attribution is incomplete")
    expected_sample_runs = (benchmark.RUN_COUNT + 1) * 2
    if len(complete) != expected_sample_runs:
        raise RuntimeError("Synthetic paired reserve attribution is incomplete")
    recorded_samples = tuple(complete[index] for index in range(3, len(complete), 2))
    stability = _summarize_stability_runs(recorded_samples)
    stable = cast(bool, stability["stable_tail"])
    passed = recorded.p95_ms <= 2.0 and recorded.p99_ms <= 5.0 and ratio >= 0.8 and stable
    return {
        "protocol": benchmark.memory_protocol_config(),
        "runtime_runs": list(protocol.runtime_runs),
        "run_count": len(recorded_runs),
        "warmup_runs": benchmark.MEMORY_PROTOCOL_WARMUP_PAIRS,
        "execution_per_run": benchmark.MEMORY_TRACE_COUNT,
        "baseline": baseline.as_dict(),
        "recorded": recorded.as_dict(),
        "paired_throughput_ratio": round(ratio, 6),
        "reserve_stability": stability,
        "stable_tail": stable,
        "passed": passed,
    }


def _validate_unified_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = UNIFIED_VALIDATION_ROOT.resolve(strict=True)
    if resolved != approved or root.is_symlink() or root.is_junction():
        raise ValueError("V16 unified validation root is not approved")
    allowed_top = {"tmp", "pytest-red-01", "pytest-green-01", "validation-01"}
    actual_top = {item.name for item in resolved.iterdir()}
    if actual_top != allowed_top:
        raise ValueError("V16 unified validation root manifest is invalid")
    validation = resolved / "validation-01"
    expected_validation = {"semantic", "space", "performance"}
    if not validation.is_dir():
        raise ValueError("V16 unified validation run manifest is invalid")
    actual_validation = {item.name for item in validation.iterdir()}
    if actual_validation != expected_validation:
        raise ValueError("V16 unified validation run manifest is invalid")
    if (resolved / "summary-unified-01.json").exists():
        raise ValueError("V16 unified validation summary already exists")
    return resolved


def run_unified_validation(root: Path) -> dict[str, object]:
    resolved = _validate_unified_root(root)
    run_root = resolved / "validation-01"
    semantic = _semantic_gate(run_root)
    space = _space_gate(run_root)
    performance: dict[str, object] | None = None
    if cast(bool, space["passed"]):
        performance = _performance_gate(run_root)
    status = (
        "passed"
        if performance is not None and cast(bool, performance["passed"])
        else "space_gate_failed"
        if not cast(bool, space["passed"])
        else "performance_gate_failed"
    )
    result = {
        "schema_version": 2,
        "status": status,
        "candidate": "rolling_budget_projection_synthetic_v1",
        "protocol": benchmark.memory_protocol_config(),
        "semantic": semantic,
        "space": space,
        "performance": performance,
    }
    summary_path = resolved / "summary-unified-01.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def _candidate_stage_protocol_result(
    protocol: benchmark.MemoryProtocolResult,
) -> dict[str, object]:
    config = benchmark.memory_protocol_config()
    expected_runs = (benchmark.MEMORY_PROTOCOL_WARMUP_PAIRS + benchmark.RUN_COUNT) * 2
    if len(protocol.runtime_runs) != expected_runs:
        raise RuntimeError("Synthetic stage runtime count is incomplete")
    if (
        len(protocol.baseline_runs) != benchmark.RUN_COUNT
        or len(protocol.recorded_runs) != benchmark.RUN_COUNT
    ):
        raise RuntimeError("Synthetic measured stage runs are incomplete")

    execution_count = benchmark.MEMORY_TRACE_COUNT
    exported_runs: list[dict[str, object]] = []
    for index, item in enumerate(protocol.runtime_runs):
        pair_index = index // 2
        order_position = index % 2 + 1
        expected_scenario = benchmark.MEMORY_PROTOCOL_PAIR[index % 2]
        if (
            item["pair_index"] != pair_index
            or item["order_position"] != order_position
            or item["scenario"] != expected_scenario
            or item["warmup"] != (pair_index < benchmark.MEMORY_PROTOCOL_WARMUP_PAIRS)
            or item["gating"] is not False
        ):
            raise RuntimeError("Synthetic stage protocol order changed")
        summary = cast(dict[str, int | float], item["summary"])
        stages = cast(dict[str, dict[str, int | float]] | None, item["stage_attribution"])
        if stages is None or set(stages) != set(benchmark.MEMORY_STAGE_ALLOWLIST):
            raise RuntimeError("Synthetic stage attribution surface is incomplete")
        if (
            summary["count"] != execution_count
            or summary["provider_dispatch_count"] != execution_count
            or any(stage["count"] != execution_count for stage in stages.values())
        ):
            raise RuntimeError("Synthetic stage ownership is incomplete")
        stage_total_ms = round(sum(float(stage["total_ms"]) for stage in stages.values()), 6)
        overall_total_ms = float(summary["total_ms"])
        if stage_total_ms > overall_total_ms:
            raise RuntimeError("Synthetic stage intervals overlap")
        unattributed_total_ms = round(overall_total_ms - stage_total_ms, 6)
        exported_runs.append(
            {
                **item,
                "attribution_boundary": {
                    "stage_topology": "flat_non_overlapping_siblings",
                    "stage_total_ms": stage_total_ms,
                    "unattributed_total_ms": unattributed_total_ms,
                    "unattributed_per_execution_ms": round(
                        unattributed_total_ms / execution_count, 6
                    ),
                },
            }
        )

    metrics = ("total_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms")

    def aggregate(scenario: str) -> dict[str, object]:
        measured = [
            item
            for item in exported_runs
            if item["scenario"] == scenario and item["warmup"] is False
        ]
        if len(measured) != benchmark.RUN_COUNT:
            raise RuntimeError("Synthetic stage scenario is incomplete")
        stage_aggregate: dict[str, dict[str, float | int]] = {}
        for stage_name in benchmark.MEMORY_STAGE_ALLOWLIST:
            stage_aggregate[stage_name] = {
                "count_per_run": execution_count,
                **{
                    metric: round(
                        float(
                            statistics.median(
                                cast(dict[str, dict[str, int | float]], item["stage_attribution"])[
                                    stage_name
                                ][metric]
                                for item in measured
                            )
                        ),
                        6,
                    )
                    for metric in metrics
                },
            }
        unattributed = [
            cast(dict[str, object], item["attribution_boundary"])["unattributed_per_execution_ms"]
            for item in measured
        ]
        return {
            "run_count": len(measured),
            "stages": stage_aggregate,
            "unattributed_per_execution_ms": {
                "per_run": unattributed,
                "median": round(float(statistics.median(cast(list[float], unattributed))), 6),
            },
        }

    baseline_aggregate = aggregate("no_recorder_control")
    recorded_aggregate = aggregate("in_memory_control")
    baseline_stages = cast(dict[str, dict[str, float | int]], baseline_aggregate["stages"])
    recorded_stages = cast(dict[str, dict[str, float | int]], recorded_aggregate["stages"])
    deltas = {
        stage: {
            metric: round(
                float(recorded_stages[stage][metric]) - float(baseline_stages[stage][metric]),
                6,
            )
            for metric in metrics
        }
        for stage in benchmark.MEMORY_STAGE_ALLOWLIST
    }
    baseline = summarize_performance_runs(
        PerformanceScenario.NO_RECORDER_CONTROL, protocol.baseline_runs
    )
    recorded = summarize_performance_runs(
        PerformanceScenario.IN_MEMORY_CONTROL, protocol.recorded_runs
    )
    return {
        "protocol": config,
        "stage_topology": "flat_non_overlapping_siblings",
        "attribution_completeness_percent": 100.0,
        "runtime_runs": exported_runs,
        "instrumented_performance": {
            "baseline": baseline.as_dict(),
            "recorded": recorded.as_dict(),
        },
        "stage_aggregates": {
            "no_recorder_control": baseline_aggregate,
            "in_memory_control": recorded_aggregate,
            "recorded_minus_baseline": deltas,
        },
    }


def _validate_stage_attribution_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = STAGE_ATTRIBUTION_ROOT.resolve(strict=True)
    if resolved != approved:
        raise ValueError("V17 stage attribution root is not approved")
    for current in (resolved, *resolved.parents):
        if current.is_symlink() or current.is_junction():
            raise ValueError("V17 stage attribution crosses a reparse boundary")
        if current == Path(current.anchor):
            break
    expected = {"tmp", "pytest-red-01", "pytest-green-01", "attribution-01"}
    if {item.name for item in resolved.iterdir()} != expected:
        raise ValueError("V17 stage attribution manifest is invalid")
    if any((resolved / "attribution-01").iterdir()):
        raise ValueError("V17 stage attribution run root is not fresh")
    if (resolved / "summary-attribution-01.json").exists():
        raise ValueError("V17 stage attribution summary already exists")
    return resolved


def run_stage_attribution(root: Path) -> dict[str, object]:
    resolved = _validate_stage_attribution_root(root)
    original_control = benchmark._MemoryControl
    original_probe = benchmark._MemoryStageProbe
    RESERVE_SAMPLE_RUNS.clear()
    benchmark.__dict__["_MemoryControl"] = CandidateMemoryControl
    benchmark.__dict__["_MemoryStageProbe"] = CandidateStageProbe
    try:
        protocol = benchmark._paired_memory_protocol(
            resolved / "attribution-01", stage_attribution=True
        )
    finally:
        benchmark.__dict__["_MemoryControl"] = original_control
        benchmark.__dict__["_MemoryStageProbe"] = original_probe
    attribution = _candidate_stage_protocol_result(protocol)
    result = {
        "schema_version": 1,
        "status": "completed",
        "candidate": "rolling_budget_projection_synthetic_v1",
        "non_gating": True,
        **attribution,
    }
    summary_path = resolved / "summary-attribution-01.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def _validate_set_based_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = V18_SET_BASED_ROOT.resolve(strict=True)
    if resolved != approved:
        raise ValueError("V18 set-based root is not approved")
    for current in (resolved, *resolved.parents):
        if current.is_symlink() or current.is_junction():
            raise ValueError("V18 set-based root crosses a reparse boundary")
        if current == Path(current.anchor):
            break
    expected_top = {"tmp", "pytest-red-01", "pytest-green-01", "preflight-01"}
    if {item.name for item in resolved.iterdir()} != expected_top:
        raise ValueError("V18 set-based root manifest is invalid")
    preflight = resolved / "preflight-01"
    if {item.name for item in preflight.iterdir()} != {"semantic", "space", "plain", "stage"}:
        raise ValueError("V18 set-based preflight manifest is invalid")
    if any(any((preflight / name).iterdir()) for name in ("semantic", "space", "plain", "stage")):
        raise ValueError("V18 set-based preflight directories are not fresh")
    if (resolved / "summary-preflight-01.json").exists():
        raise ValueError("V18 set-based summary already exists")
    return resolved


def _validate_revised_semantic_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = V18_REVISED_SEMANTIC_ROOT.resolve(strict=True)
    if resolved != approved:
        raise ValueError("V18 revised semantic root is not approved")
    for current in (resolved, *resolved.parents):
        if current.is_symlink() or current.is_junction():
            raise ValueError("V18 revised semantic root crosses a reparse boundary")
        if current == Path(current.anchor):
            break
    expected = {"tmp", "pytest-red-01", "pytest-green-01", "semantic-01"}
    if {item.name for item in resolved.iterdir()} != expected:
        raise ValueError("V18 revised semantic root manifest is invalid")
    if any((resolved / "semantic-01").iterdir()):
        raise ValueError("V18 revised semantic root is not fresh")
    if (resolved / "summary-semantic-01.json").exists():
        raise ValueError("V18 revised semantic summary already exists")
    return resolved


def run_revised_semantic_gate(root: Path) -> dict[str, object]:
    resolved = _validate_revised_semantic_root(root)
    semantic = _semantic_gate(
        resolved,
        repository_type=SetBasedCandidateSqliteSafetyControlRepository,
        directory_name="semantic-01",
    )
    database = resolved / "semantic-01" / "control.sqlite3"
    repository = SetBasedCandidateSqliteSafetyControlRepository(
        database_path=database,
        allowed_root=database.parent,
    )
    repository.initialize()
    checkpoints: list[dict[str, object]] = []
    try:
        for name, now_ns in (
            ("hour_cutoff_exact", BASE_NS + HOUR_NS),
            ("day_cutoff_exact", BASE_NS + DAY_NS),
            ("clock_rollback_rebuild", BASE_NS + DAY_NS - 1),
        ):
            repository.advance_projection(now_ns=now_ns)
            with closing(repository._connect()) as connection:
                assert_projection_matches_ledger(connection, now_ns)
                checkpoints.append(
                    {
                        "name": name,
                        "projection_match": True,
                        "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
                        "foreign_key_failures": len(
                            connection.execute("PRAGMA foreign_key_check").fetchall()
                        ),
                    }
                )
    finally:
        repository.close()
    semantic_passed = (
        semantic["concurrent_reservations"] == 16
        and semantic["settlements"] == 16
        and semantic["projection_match"] is True
        and semantic["integrity"] == "ok"
        and semantic["foreign_key_failures"] == 0
        and all(
            checkpoint["projection_match"] is True
            and checkpoint["integrity"] == "ok"
            and checkpoint["foreign_key_failures"] == 0
            for checkpoint in checkpoints
        )
    )
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "passed" if semantic_passed else "semantic_gate_failed",
        "candidate": "set_based_zero_seed_update_synthetic_v2",
        "semantic": semantic,
        "window_checkpoints": checkpoints,
        "privacy_forbidden_hits": 0,
        "performance_executed": False,
        "product_0005_created": False,
    }
    serialized = json.dumps(result, sort_keys=True)
    forbidden = (
        "projection_player",
        "Synthetic projection preflight.",
        "f009-v14-synthetic-scope-key-32bytes",
    )
    privacy_hits = sum(serialized.count(value) for value in forbidden)
    result["privacy_forbidden_hits"] = privacy_hits
    if privacy_hits:
        result["status"] = "semantic_gate_failed"
    summary_path = resolved / "summary-semantic-01.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def _validate_revised_performance_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = V18_REVISED_PERFORMANCE_ROOT.resolve(strict=True)
    if resolved != approved:
        raise ValueError("V18 revised performance root is not approved")
    for current in (resolved, *resolved.parents):
        if current.is_symlink() or current.is_junction():
            raise ValueError("V18 revised performance root crosses a reparse boundary")
        if current == Path(current.anchor):
            break
    expected = {"tmp", "pytest-red-01", "pytest-green-01", "validation-01"}
    if {item.name for item in resolved.iterdir()} != expected:
        raise ValueError("V18 revised performance root manifest is invalid")
    validation = resolved / "validation-01"
    if {item.name for item in validation.iterdir()} != {"space", "plain", "stage"}:
        raise ValueError("V18 revised performance validation manifest is invalid")
    if any(any((validation / name).iterdir()) for name in ("space", "plain", "stage")):
        raise ValueError("V18 revised performance root is not fresh")
    if (resolved / "summary-performance-01.json").exists():
        raise ValueError("V18 revised performance summary already exists")
    return resolved


def _validate_single_write_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = V19_SINGLE_WRITE_ROOT.resolve(strict=True)
    if resolved != approved:
        raise ValueError("V19 single-write root is not approved")
    for current in (resolved, *resolved.parents):
        if current.is_symlink() or current.is_junction():
            raise ValueError("V19 single-write root crosses a reparse boundary")
        if current == Path(current.anchor):
            break
    expected = {
        "tmp",
        "pytest-red-01",
        "pytest-green-01",
        "validation-01",
        "validation-02",
        "validation-03",
        "summary-v19-02.json",
    }
    actual = {item.name for item in resolved.iterdir()}
    if actual not in (expected, expected | {"summary-v19-03.json"}):
        raise ValueError("V19 single-write root manifest is invalid")
    expected_runs = {"semantic", "space", "plain", "stage"}
    first_validation = resolved / "validation-01"
    second_validation = resolved / "validation-02"
    validation = resolved / "validation-03"
    if (
        {item.name for item in first_validation.iterdir()} != expected_runs
        or {item.name for item in second_validation.iterdir()} != expected_runs
        or {item.name for item in validation.iterdir()} != expected_runs
    ):
        raise ValueError("V19 single-write validation manifest is invalid")
    if any(any((validation / name).iterdir()) for name in expected_runs):
        raise ValueError("V19 single-write root is not fresh")
    if (resolved / "summary-v19-03.json").exists():
        raise ValueError("V19 single-write summary already exists")
    return resolved


def _load_revised_semantic_reference() -> dict[str, object]:
    digest = hashlib.sha256(V18_REVISED_SEMANTIC_SUMMARY.read_bytes()).hexdigest().upper()
    if digest != V18_REVISED_SEMANTIC_SUMMARY_SHA256:
        raise ValueError("V18 revised semantic summary fingerprint changed")
    loaded = cast(dict[str, object], json.loads(V18_REVISED_SEMANTIC_SUMMARY.read_text("utf-8")))
    if (
        loaded.get("status") != "passed"
        or loaded.get("performance_executed") is not False
        or loaded.get("product_0005_created") is not False
        or loaded.get("privacy_forbidden_hits") != 0
    ):
        raise ValueError("V18 revised semantic summary is not eligible")
    return loaded


def run_revised_performance_preflight(root: Path) -> dict[str, object]:
    resolved = _validate_revised_performance_root(root)
    semantic_reference = _load_revised_semantic_reference()
    run_root = resolved / "validation-01"
    space = _space_gate(
        run_root,
        repository_type=SetBasedCandidateSqliteSafetyControlRepository,
    )
    if space["passed"] is not True:
        result: dict[str, object] = {
            "schema_version": 1,
            "status": "space_gate_failed",
            "candidate": "set_based_zero_seed_update_synthetic_v2",
            "semantic_reference": {
                "sha256": V18_REVISED_SEMANTIC_SUMMARY_SHA256,
                "status": semantic_reference["status"],
            },
            "space": space,
            "plain": None,
            "stage_companion": None,
            "product_0005_created": False,
        }
    else:
        plain = _performance_gate(
            run_root,
            memory_control_type=SetBasedCandidateMemoryControl,
            directory_name="plain",
        )
        plain_operation_counts = dict(SetBasedCandidateMemoryControl._set_based_counts)
        original_control = benchmark._MemoryControl
        original_probe = benchmark._MemoryStageProbe
        benchmark.__dict__["_MemoryControl"] = SetBasedCandidateMemoryControl
        benchmark.__dict__["_MemoryStageProbe"] = CandidateStageProbe
        try:
            stage_protocol = benchmark._paired_memory_protocol(
                run_root / "stage", stage_attribution=True
            )
        finally:
            benchmark.__dict__["_MemoryControl"] = original_control
            benchmark.__dict__["_MemoryStageProbe"] = original_probe
        stage = _candidate_stage_protocol_result(stage_protocol)
        stage_operation_counts = dict(SetBasedCandidateMemoryControl._set_based_counts)
        stage_aggregates = cast(dict[str, object], stage["stage_aggregates"])
        recorded_aggregate = cast(dict[str, object], stage_aggregates["in_memory_control"])
        recorded_stages = cast(dict[str, dict[str, float | int]], recorded_aggregate["stages"])
        reservation_p95_ms = float(recorded_stages["budget_reservation"]["p95_ms"])
        settlement_p95_ms = float(recorded_stages["budget_settlement"]["p95_ms"])
        recorded = cast(dict[str, float | int | str], plain["recorded"])
        privacy_surface = json.dumps(
            {
                "space": space,
                "plain": plain,
                "stage": stage,
                "plain_operation_counts": plain_operation_counts,
                "stage_operation_counts": stage_operation_counts,
            },
            sort_keys=True,
        )
        forbidden = (
            "bench_player_0000",
            "Synthetic local benchmark.",
            "Synthetic local diagnostic persona.",
            "f009-synthetic-scope-key-32bytes!!",
        )
        privacy_hits = sum(privacy_surface.count(value) for value in forbidden)
        verdict = _set_based_gate_verdict(
            reservation_p95_ms=reservation_p95_ms,
            settlement_p95_ms=settlement_p95_ms,
            recorded_p95_ms=float(recorded["p95_ms"]),
            recorded_p99_ms=float(recorded["p99_ms"]),
            throughput_ratio=cast(float, plain["paired_throughput_ratio"]),
            stable_tail=cast(bool, plain["stable_tail"]),
            control_growth_bytes=cast(int, space["growth_bytes"]),
            semantic_passed=True,
            privacy_hits=privacy_hits,
        )
        result = {
            "schema_version": 1,
            "status": "passed" if verdict["passed"] is True else "performance_gate_failed",
            "candidate": "set_based_zero_seed_update_synthetic_v2",
            "semantic_reference": {
                "sha256": V18_REVISED_SEMANTIC_SUMMARY_SHA256,
                "status": semantic_reference["status"],
            },
            "protocol": benchmark.memory_protocol_config(),
            "space": space,
            "plain": plain,
            "stage_companion": stage,
            "stage_candidate_metrics": {
                "reservation_p95_ms": reservation_p95_ms,
                "settlement_p95_ms": settlement_p95_ms,
            },
            "set_based_operation_counts": {
                "plain_last_run": plain_operation_counts,
                "stage_last_run": stage_operation_counts,
            },
            "privacy_forbidden_hits": privacy_hits,
            "verdict": verdict,
            "product_0005_created": False,
        }
    summary_path = resolved / "summary-performance-01.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def _set_based_gate_verdict(
    *,
    reservation_p95_ms: float,
    settlement_p95_ms: float,
    recorded_p95_ms: float,
    recorded_p99_ms: float,
    throughput_ratio: float,
    stable_tail: bool,
    control_growth_bytes: int,
    semantic_passed: bool,
    privacy_hits: int,
) -> dict[str, object]:
    reservation_reduction = (
        (V17_RECORDED_RESERVATION_P95_MS - reservation_p95_ms)
        / V17_RECORDED_RESERVATION_P95_MS
        * 100
    )
    settlement_reduction = (
        (V17_RECORDED_SETTLEMENT_P95_MS - settlement_p95_ms) / V17_RECORDED_SETTLEMENT_P95_MS * 100
    )
    gates = {
        "reservation_reduction": reservation_reduction >= 35.0,
        "settlement_reduction": settlement_reduction >= 20.0,
        "recorded_p95": recorded_p95_ms <= 2.0,
        "recorded_p99": recorded_p99_ms <= 5.0,
        "paired_throughput": throughput_ratio >= 0.8,
        "equal_work_stability": stable_tail,
        "control_growth": control_growth_bytes <= 256 * 1024,
        "semantic": semantic_passed,
        "privacy": privacy_hits == 0,
    }
    return {
        "passed": all(gates.values()),
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "gates": gates,
        "reservation_reference_p95_ms": V17_RECORDED_RESERVATION_P95_MS,
        "reservation_reduction_percent": round(reservation_reduction, 6),
        "settlement_reference_p95_ms": V17_RECORDED_SETTLEMENT_P95_MS,
        "settlement_reduction_percent": round(settlement_reduction, 6),
    }


def run_single_write_preflight(root: Path) -> dict[str, object]:
    resolved = _validate_single_write_root(root)
    run_root = resolved / "validation-03"
    SingleWriteCandidateSqliteSafetyControlRepository._reset_set_based_counts()
    semantic = _semantic_gate(
        run_root,
        repository_type=SingleWriteCandidateSqliteSafetyControlRepository,
        directory_name="semantic",
    )
    semantic_database = run_root / "semantic" / "control.sqlite3"
    repository = SingleWriteCandidateSqliteSafetyControlRepository(
        database_path=semantic_database,
        allowed_root=semantic_database.parent,
    )
    repository.initialize()
    checkpoints: list[dict[str, object]] = []
    try:
        for name, now_ns in (
            ("no_expiration_advance", BASE_NS + 60 * 1_000_000_000),
            ("hour_cutoff_exact", BASE_NS + HOUR_NS),
            ("day_cutoff_exact", BASE_NS + DAY_NS),
            ("clock_rollback_rebuild", BASE_NS + DAY_NS - 1),
        ):
            repository.advance_projection(now_ns=now_ns)
            with closing(repository._connect()) as connection:
                assert_projection_matches_ledger(connection, now_ns)
                checkpoints.append(
                    {
                        "name": name,
                        "projection_match": True,
                        "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
                        "foreign_key_failures": len(
                            connection.execute("PRAGMA foreign_key_check").fetchall()
                        ),
                    }
                )
    finally:
        repository.close()
    semantic_counts = SingleWriteCandidateSqliteSafetyControlRepository._set_based_counts.copy()
    semantic_passed = (
        semantic["concurrent_reservations"] == 16
        and semantic["settlements"] == 16
        and semantic["projection_match"] is True
        and semantic["integrity"] == "ok"
        and semantic["foreign_key_failures"] == 0
        and all(
            checkpoint["projection_match"] is True
            and checkpoint["integrity"] == "ok"
            and checkpoint["foreign_key_failures"] == 0
            for checkpoint in checkpoints
        )
        and semantic_counts.get("scope_delta_sql_statements")
        == semantic_counts.get("scope_delta_apply_batches")
        and semantic_counts.get("expiration_skipped_write_batches", 0) > 0
    )
    if not semantic_passed:
        result: dict[str, object] = {
            "schema_version": 1,
            "status": "semantic_gate_failed",
            "candidate": "single_write_rolling_budget_projection_synthetic_v1",
            "semantic": semantic,
            "window_checkpoints": checkpoints,
            "operation_counts": {"semantic": semantic_counts},
            "space": None,
            "plain": None,
            "stage_companion": None,
            "privacy_forbidden_hits": 0,
            "product_0005_created": False,
        }
    else:
        space = _space_gate(
            run_root,
            repository_type=SingleWriteCandidateSqliteSafetyControlRepository,
        )
        if space["passed"] is not True:
            result = {
                "schema_version": 1,
                "status": "space_gate_failed",
                "candidate": "single_write_rolling_budget_projection_synthetic_v1",
                "semantic": semantic,
                "window_checkpoints": checkpoints,
                "operation_counts": {"semantic": semantic_counts},
                "space": space,
                "plain": None,
                "stage_companion": None,
                "privacy_forbidden_hits": 0,
                "product_0005_created": False,
            }
        else:
            plain = _performance_gate(
                run_root,
                memory_control_type=SingleWriteCandidateMemoryControl,
                directory_name="plain",
            )
            plain_counts = SingleWriteCandidateMemoryControl._set_based_counts.copy()
            original_control = benchmark._MemoryControl
            original_probe = benchmark._MemoryStageProbe
            benchmark.__dict__["_MemoryControl"] = SingleWriteCandidateMemoryControl
            benchmark.__dict__["_MemoryStageProbe"] = CandidateStageProbe
            try:
                stage_protocol = benchmark._paired_memory_protocol(
                    run_root / "stage", stage_attribution=True
                )
            finally:
                benchmark.__dict__["_MemoryControl"] = original_control
                benchmark.__dict__["_MemoryStageProbe"] = original_probe
            stage = _candidate_stage_protocol_result(stage_protocol)
            stage_counts = SingleWriteCandidateMemoryControl._set_based_counts.copy()
            stage_aggregates = cast(dict[str, object], stage["stage_aggregates"])
            recorded_aggregate = cast(dict[str, object], stage_aggregates["in_memory_control"])
            recorded_stages = cast(dict[str, dict[str, float | int]], recorded_aggregate["stages"])
            reservation_p95_ms = float(recorded_stages["budget_reservation"]["p95_ms"])
            settlement_p95_ms = float(recorded_stages["budget_settlement"]["p95_ms"])
            recorded = cast(dict[str, float | int | str], plain["recorded"])
            privacy_surface = json.dumps(
                {
                    "semantic": semantic,
                    "checkpoints": checkpoints,
                    "space": space,
                    "plain": plain,
                    "stage": stage,
                    "counts": {
                        "semantic": semantic_counts,
                        "plain": plain_counts,
                        "stage": stage_counts,
                    },
                },
                sort_keys=True,
            )
            forbidden = (
                "projection_player",
                "bench_player_0000",
                "Synthetic projection preflight.",
                "Synthetic local benchmark.",
                "Synthetic local diagnostic persona.",
                "f009-v14-synthetic-scope-key-32bytes",
                "f009-synthetic-scope-key-32bytes!!",
            )
            privacy_hits = sum(privacy_surface.count(value) for value in forbidden)
            verdict = _set_based_gate_verdict(
                reservation_p95_ms=reservation_p95_ms,
                settlement_p95_ms=settlement_p95_ms,
                recorded_p95_ms=float(recorded["p95_ms"]),
                recorded_p99_ms=float(recorded["p99_ms"]),
                throughput_ratio=cast(float, plain["paired_throughput_ratio"]),
                stable_tail=cast(bool, plain["stable_tail"]),
                control_growth_bytes=cast(int, space["growth_bytes"]),
                semantic_passed=True,
                privacy_hits=privacy_hits,
            )
            result = {
                "schema_version": 1,
                "status": "passed" if verdict["passed"] is True else "performance_gate_failed",
                "candidate": "single_write_rolling_budget_projection_synthetic_v1",
                "protocol": benchmark.memory_protocol_config(),
                "semantic": semantic,
                "window_checkpoints": checkpoints,
                "space": space,
                "plain": plain,
                "stage_companion": stage,
                "stage_candidate_metrics": {
                    "reservation_p95_ms": reservation_p95_ms,
                    "settlement_p95_ms": settlement_p95_ms,
                },
                "operation_counts": {
                    "semantic": semantic_counts,
                    "plain_last_run": plain_counts,
                    "stage_last_run": stage_counts,
                },
                "privacy_forbidden_hits": privacy_hits,
                "verdict": verdict,
                "product_0005_created": False,
            }
    summary_path = resolved / "summary-v19-03.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def run_set_based_preflight(root: Path) -> dict[str, object]:
    resolved = _validate_set_based_root(root)
    run_root = resolved / "preflight-01"
    semantic = _semantic_gate(
        run_root,
        repository_type=SetBasedCandidateSqliteSafetyControlRepository,
    )
    semantic_passed = (
        semantic["concurrent_reservations"] == 16
        and semantic["settlements"] == 16
        and semantic["integrity"] == "ok"
        and semantic["foreign_key_failures"] == 0
        and semantic["projection_match"] is True
    )
    space = _space_gate(
        run_root,
        repository_type=SetBasedCandidateSqliteSafetyControlRepository,
    )
    plain = _performance_gate(
        run_root,
        memory_control_type=SetBasedCandidateMemoryControl,
    )
    plain_operation_counts = dict(SetBasedCandidateMemoryControl._set_based_counts)

    original_control = benchmark._MemoryControl
    original_probe = benchmark._MemoryStageProbe
    benchmark.__dict__["_MemoryControl"] = SetBasedCandidateMemoryControl
    benchmark.__dict__["_MemoryStageProbe"] = CandidateStageProbe
    try:
        stage_protocol = benchmark._paired_memory_protocol(
            run_root / "stage", stage_attribution=True
        )
    finally:
        benchmark.__dict__["_MemoryControl"] = original_control
        benchmark.__dict__["_MemoryStageProbe"] = original_probe
    stage = _candidate_stage_protocol_result(stage_protocol)
    stage_operation_counts = dict(SetBasedCandidateMemoryControl._set_based_counts)
    stage_aggregates = cast(dict[str, object], stage["stage_aggregates"])
    recorded_aggregate = cast(dict[str, object], stage_aggregates["in_memory_control"])
    recorded_stages = cast(dict[str, dict[str, float | int]], recorded_aggregate["stages"])
    reservation_p95_ms = float(recorded_stages["budget_reservation"]["p95_ms"])
    settlement_p95_ms = float(recorded_stages["budget_settlement"]["p95_ms"])
    recorded = cast(dict[str, float | int | str], plain["recorded"])
    privacy_probe = {
        "semantic": semantic,
        "space": space,
        "plain": plain,
        "stage": stage,
        "plain_operation_counts": plain_operation_counts,
        "stage_operation_counts": stage_operation_counts,
    }
    serialized = json.dumps(privacy_probe, sort_keys=True)
    forbidden = (
        "bench_player_0000",
        "Synthetic local benchmark.",
        "Synthetic local diagnostic persona.",
        "f009-synthetic-scope-key-32bytes!!",
        "Synthetic V14 projection persona.",
    )
    privacy_hits = sum(serialized.count(value) for value in forbidden)
    verdict = _set_based_gate_verdict(
        reservation_p95_ms=reservation_p95_ms,
        settlement_p95_ms=settlement_p95_ms,
        recorded_p95_ms=float(recorded["p95_ms"]),
        recorded_p99_ms=float(recorded["p99_ms"]),
        throughput_ratio=cast(float, plain["paired_throughput_ratio"]),
        stable_tail=cast(bool, plain["stable_tail"]),
        control_growth_bytes=cast(int, space["growth_bytes"]),
        semantic_passed=semantic_passed,
        privacy_hits=privacy_hits,
    )
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "passed" if verdict["passed"] is True else "synthetic_gate_failed",
        "candidate": "set_based_rolling_budget_projection_synthetic_v1",
        "protocol": benchmark.memory_protocol_config(),
        "semantic": semantic,
        "space": space,
        "plain": plain,
        "stage_companion": stage,
        "stage_candidate_metrics": {
            "reservation_p95_ms": reservation_p95_ms,
            "settlement_p95_ms": settlement_p95_ms,
        },
        "set_based_operation_counts": {
            "plain_last_run": plain_operation_counts,
            "stage_last_run": stage_operation_counts,
        },
        "privacy_forbidden_hits": privacy_hits,
        "verdict": verdict,
    }
    summary_path = resolved / "summary-preflight-01.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def _validate_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    approved = APPROVED_ROOT.resolve(strict=True)
    if resolved != approved or root.is_symlink() or root.is_junction():
        raise ValueError("V14 preflight root is not approved")
    expected = {"tmp", "validation-01"}
    if not expected <= {item.name for item in resolved.iterdir() if item.is_dir()}:
        raise ValueError("V14 preflight directory manifest is incomplete")
    return resolved


def run_preflight(root: Path) -> dict[str, object]:
    resolved = _validate_root(root)
    run_root = resolved / "validation-01"
    expected_run_dirs = {run_root / name for name in ("semantic", "space", "performance")}
    if not run_root.is_dir() or not all(path.is_dir() for path in expected_run_dirs):
        raise ValueError("V14 validation-01 manifest is incomplete")
    summary_path = resolved / "summary-validation-01.json"
    if summary_path.exists():
        raise ValueError("V14 preflight summary already exists")
    semantic = _semantic_gate(run_root)
    space = _space_gate(run_root)
    if not cast(bool, space["passed"]):
        result = {
            "schema_version": 1,
            "status": "space_gate_failed",
            "semantic": semantic,
            "space": space,
            "performance": None,
        }
    else:
        performance = _performance_gate(run_root)
        result = {
            "schema_version": 1,
            "status": "passed" if cast(bool, performance["passed"]) else "performance_gate_failed",
            "semantic": semantic,
            "space": space,
            "performance": performance,
        }
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=(
            "corrected-validation",
            "p95-attribution",
            "unified-validation",
            "stage-attribution",
            "set-based-preflight",
            "revised-semantic",
            "revised-performance",
            "single-write-preflight",
        ),
        default="corrected-validation",
    )
    args = parser.parse_args()
    if args.mode == "p95-attribution":
        result = run_p95_attribution(args.output_root)
    elif args.mode == "unified-validation":
        result = run_unified_validation(args.output_root)
    elif args.mode == "stage-attribution":
        result = run_stage_attribution(args.output_root)
    elif args.mode == "set-based-preflight":
        result = run_set_based_preflight(args.output_root)
    elif args.mode == "revised-semantic":
        result = run_revised_semantic_gate(args.output_root)
    elif args.mode == "revised-performance":
        result = run_revised_performance_preflight(args.output_root)
    elif args.mode == "single-write-preflight":
        result = run_single_write_preflight(args.output_root)
    else:
        result = run_preflight(args.output_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in {"passed", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
