"""V26 synthetic-only preflight for one redundant control index candidate."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import re
import sqlite3
import subprocess
import time
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID

from cyber_town.application.budget import BudgetScopeTags, PricingPolicy
from cyber_town.application.control import SafetyControl
from cyber_town.application.observability import ProviderKind
from cyber_town.application.provider import ProviderUsage
from cyber_town.contracts.v1 import DialogueRequestV1
from cyber_town.infrastructure.control import sqlite_control as control_module
from cyber_town.infrastructure.control.sqlite_control import (
    SafetyControlStorageError,
    SqliteSafetyControlRepository,
)

V26_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v26-control-space-index")
QUERY_PLAN_FIX_ROOT = Path(
    r"E:\Agent\cyber-town-f009-step5-tests\performance-v26-control-space-query-plan-fix"
)
SQLITE_TOOL = Path(r"E:\adb\sqlite3.exe")
CANDIDATE_INDEX = "idx_budget_owners_npc"
DROP_CANDIDATE_SQL = "DROP INDEX idx_budget_owners_npc"
SPACE_LIMIT_BYTES = 256 * 1024
REQUIRED_SAVING_BYTES = 2 * 4096
HISTORY_SIZES = (100, 1_000, 10_000)
SPACE_PAIR_COUNT = 5
SPACE_EXECUTIONS = 100
QUERY_P95_LIMIT_MS = 50.0
SYNTHETIC_KEY = b"f009-v26-synthetic-scope-key-0001"
_HEX_TAG = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
_FORBIDDEN_SUMMARY_VALUES = (
    "bench_player_",
    "Synthetic local benchmark",
    "api-key-synthetic-secret",
)


@dataclass(frozen=True, slots=True)
class SpaceSnapshot:
    initial_occupied_bytes: int
    final_occupied_bytes: int
    initial_freelist_pages: int
    final_freelist_pages: int
    candidate_index_pages: int

    @property
    def occupied_growth_bytes(self) -> int:
        return self.final_occupied_bytes - self.initial_occupied_bytes


def manifest(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    directories: list[Path] = [
        root,
        root / "pytest-red-01",
        root / "pytest-green-01",
        root / "pytest-green-02",
        root / "pytest-green-03",
        root / "pytest-green-04",
        root / "tmp",
        root / "query-plan-01",
    ]
    for size in HISTORY_SIZES:
        directories.extend((root / f"history-{size}-baseline", root / f"history-{size}-candidate"))
    for pair in range(1, SPACE_PAIR_COUNT + 1):
        pair_root = root / f"space-pair-{pair:02d}"
        directories.extend((pair_root, pair_root / "baseline", pair_root / "candidate"))
    return tuple(directories), (root / "summary.json",)


def query_plan_fix_manifest(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    return (
        (
            root,
            root / "tmp",
            root / "pytest-red-01",
            root / "pytest-green-01",
            root / "query-plan-01",
            root / "query-plan-01" / "baseline",
            root / "query-plan-01" / "candidate",
        ),
        (root / "summary.json",),
    )


def validate_candidate_sql(sql: str) -> None:
    if sql != DROP_CANDIDATE_SQL:
        raise ValueError("V26 candidate SQL is outside the approved boundary")


def sanitize_query_plan(rows: tuple[str, ...]) -> tuple[str, ...]:
    for row in rows:
        if (
            not isinstance(row, str)
            or _HEX_TAG.search(row)
            or any(value in row for value in _FORBIDDEN_SUMMARY_VALUES)
        ):
            raise ValueError("V26 query plan metadata contains a forbidden value")
    return rows


def evaluate_query_plan_probe(
    baseline: dict[str, object],
    candidate: dict[str, object],
) -> tuple[str, ...]:
    failures: list[str] = []
    if not baseline["sqlite_master_has_candidate"]:
        failures.append("baseline_sqlite_master_missing_index")
    if not baseline["index_list_has_candidate"]:
        failures.append("baseline_index_list_missing_index")
    if cast(int, baseline["candidate_index_pages"]) <= 0:
        failures.append("baseline_dbstat_missing_index_pages")
    if candidate["sqlite_master_has_candidate"]:
        failures.append("candidate_sqlite_master_retained_index")
    if candidate["index_list_has_candidate"]:
        failures.append("candidate_index_list_retained_index")
    if cast(int, candidate["candidate_index_pages"]) != 0:
        failures.append("candidate_dbstat_retained_index_pages")

    baseline_normal = cast(dict[str, tuple[str, ...]], baseline["normal"])
    candidate_normal = cast(dict[str, tuple[str, ...]], candidate["normal"])
    if any(CANDIDATE_INDEX in line for plan in baseline_normal.values() for line in plan):
        failures.append("candidate_index_used_by_normal_query")
    if baseline_normal != candidate_normal:
        failures.append("candidate_normal_query_plan_regressed")

    baseline_active = cast(tuple[str, ...], baseline["active_npc"])
    candidate_active = cast(tuple[str, ...], candidate["active_npc"])
    if not any(CANDIDATE_INDEX in line for line in baseline_active):
        failures.append("baseline_active_npc_plan_missing_candidate_index")
    if any(CANDIDATE_INDEX in line for line in candidate_active):
        failures.append("candidate_query_plan_retained_dropped_index")
    return tuple(failures)


def evaluate_space_pair(
    baseline: SpaceSnapshot,
    candidate: SpaceSnapshot,
) -> tuple[str, ...]:
    failures: list[str] = []
    if candidate.occupied_growth_bytes > SPACE_LIMIT_BYTES:
        failures.append("candidate_occupied_growth_exceeded")
    if baseline.occupied_growth_bytes - candidate.occupied_growth_bytes < REQUIRED_SAVING_BYTES:
        failures.append("candidate_occupied_saving_below_8192")
    if candidate.candidate_index_pages != 0:
        failures.append("candidate_index_still_present")
    return tuple(failures)


class _SyntheticClock:
    def __init__(self) -> None:
        self.value = 2_000_000_000_000_000_000

    def time_ns(self) -> int:
        return self.value

    def monotonic(self) -> float:
        return self.value / 1_000_000_000

    def advance(self, seconds: float) -> None:
        self.value += round(seconds * 1_000_000_000)


def _tag(value: str) -> str:
    return hashlib.sha256(f"v26:{value}".encode()).hexdigest()


def _percentile(samples: list[float], fraction: float) -> float:
    ordered = sorted(samples)
    return round(ordered[max(0, math.ceil(len(ordered) * fraction) - 1)], 6)


def _validate_root(root: Path) -> Path:
    if not isinstance(root, Path) or root != V26_ROOT:
        raise ValueError("V26 root is outside the registered boundary")
    resolved = root.resolve(strict=False)
    if resolved != V26_ROOT:
        raise ValueError("V26 root canonical path changed")
    approved_parent = V26_ROOT.parent.resolve(strict=True)
    if resolved.parent != approved_parent:
        raise ValueError("V26 root parent changed")
    for current in (approved_parent, *approved_parent.parents):
        if current.is_symlink() or current.is_junction():
            raise ValueError("V26 root traverses a reparse boundary")
        if current == Path("E:\\"):
            break
    return resolved


def _validate_query_plan_fix_root(root: Path) -> Path:
    if not isinstance(root, Path) or root != QUERY_PLAN_FIX_ROOT:
        raise ValueError("V26 query-plan fix root is outside the registered boundary")
    resolved = root.resolve(strict=True)
    if resolved != QUERY_PLAN_FIX_ROOT:
        raise ValueError("V26 query-plan fix root canonical path changed")
    approved_parent = QUERY_PLAN_FIX_ROOT.parent.resolve(strict=True)
    if resolved.parent != approved_parent:
        raise ValueError("V26 query-plan fix root parent changed")
    for current in (resolved, approved_parent, *approved_parent.parents):
        if current.is_symlink() or current.is_junction():
            raise ValueError("V26 query-plan fix root traverses a reparse boundary")
        if current == Path("E:\\"):
            break
    return resolved


def _connect_for_setup(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    return connection


def _initialize_database(directory: Path, *, candidate: bool) -> Path:
    directory.mkdir()
    database = directory / "control.sqlite3"
    repository = SqliteSafetyControlRepository(database_path=database, allowed_root=directory)
    repository.initialize()
    repository.close()
    if candidate:
        validate_candidate_sql(DROP_CANDIDATE_SQL)
        with closing(_connect_for_setup(database)) as connection:
            connection.execute(DROP_CANDIDATE_SQL)
            connection.commit()
    return database


def _query_plan(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[object, ...],
) -> tuple[str, ...]:
    rows = connection.execute("EXPLAIN QUERY PLAN " + sql, parameters).fetchall()
    return sanitize_query_plan(tuple(str(row[3]) for row in rows))


def _query_plan_scenario(directory: Path) -> dict[str, object]:
    database = _initialize_database(directory, candidate=False)
    tag = "0" * 64
    normal_queries = {
        "projection_totals": (
            control_module._BUDGET_WINDOW_TOTALS_SQL,
            ("player_npc", tag, "player", tag, "npc", tag, "global", tag),
        ),
        "owner_by_execution": (
            "SELECT * FROM budget_execution_owners WHERE execution_id=?",
            (str(UUID(int=1)),),
        ),
        "expiration_join": (
            "SELECT o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag "
            "FROM budget_reservations r JOIN budget_execution_owners o USING(execution_id) "
            "WHERE r.status<>'released' AND r.reserved_at_ns>?",
            (1,),
        ),
    }
    active_query = (
        "SELECT 1 FROM budget_reservations r JOIN budget_execution_owners o "
        "USING(execution_id) WHERE o.npc_scope_tag=? AND r.status<>'released' "
        "AND r.reserved_at_ns>? LIMIT 1"
    )
    with closing(sqlite3.connect(database)) as connection:
        baseline_normal = {
            name: _query_plan(connection, sql, parameters)
            for name, (sql, parameters) in normal_queries.items()
        }
        baseline_active = _query_plan(connection, active_query, (tag, 1))
        connection.execute(DROP_CANDIDATE_SQL)
        candidate_normal = {
            name: _query_plan(connection, sql, parameters)
            for name, (sql, parameters) in normal_queries.items()
        }
        candidate_active = _query_plan(connection, active_query, (tag, 1))
        connection.rollback()
    normal_candidate_uses = [
        name
        for name, plan in baseline_normal.items()
        if any(CANDIDATE_INDEX in line for line in plan)
    ]
    failures: list[str] = []
    if normal_candidate_uses:
        failures.append("candidate_index_used_by_normal_query")
    if any(CANDIDATE_INDEX in line for line in candidate_active):
        failures.append("candidate_query_plan_retained_dropped_index")
    return {
        "baseline_normal": baseline_normal,
        "candidate_normal": candidate_normal,
        "baseline_active_npc": baseline_active,
        "candidate_active_npc": candidate_active,
        "normal_candidate_index_uses": normal_candidate_uses,
        "failures": failures,
    }


def _query_plan_inputs() -> tuple[
    dict[str, tuple[str, tuple[object, ...]]],
    tuple[str, tuple[object, ...]],
]:
    tag = "0" * 64
    normal_queries = {
        "projection_totals": (
            control_module._BUDGET_WINDOW_TOTALS_SQL,
            ("player_npc", tag, "player", tag, "npc", tag, "global", tag),
        ),
        "owner_by_execution": (
            "SELECT * FROM budget_execution_owners WHERE execution_id=?",
            (str(UUID(int=1)),),
        ),
        "expiration_join": (
            "SELECT o.player_scope_tag,o.npc_scope_tag,o.player_npc_scope_tag "
            "FROM budget_reservations r JOIN budget_execution_owners o USING(execution_id) "
            "WHERE r.status<>'released' AND r.reserved_at_ns>?",
            (1,),
        ),
    }
    active_query = (
        "SELECT 1 FROM budget_reservations r JOIN budget_execution_owners o "
        "USING(execution_id) WHERE o.npc_scope_tag=? AND r.status<>'released' "
        "AND r.reserved_at_ns>? LIMIT 1",
        (tag, 1),
    )
    return normal_queries, active_query


def _initialize_registered_query_plan_database(directory: Path) -> Path:
    if not directory.is_dir() or directory.is_symlink() or directory.is_junction():
        raise ValueError("V26 query-plan database directory is not a registered plain directory")
    database = directory / "control.sqlite3"
    if database.exists():
        raise ValueError("V26 query-plan database already exists")
    repository = SqliteSafetyControlRepository(database_path=database, allowed_root=directory)
    repository.initialize()
    repository.close()
    return database


def _fresh_query_plan_snapshot(database: Path) -> dict[str, object]:
    normal_queries, active_query = _query_plan_inputs()
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        sqlite_master_has_candidate = bool(
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
                (CANDIDATE_INDEX,),
            ).fetchone()
        )
        index_names = tuple(
            str(row[1])
            for row in connection.execute("PRAGMA index_list('budget_execution_owners')")
        )
        normal = {
            name: _query_plan(connection, sql, parameters)
            for name, (sql, parameters) in normal_queries.items()
        }
        active_npc = _query_plan(connection, active_query[0], active_query[1])
    pages = _dbstat_pages(database)
    return {
        "sqlite_master_has_candidate": sqlite_master_has_candidate,
        "index_list_has_candidate": CANDIDATE_INDEX in index_names,
        "candidate_index_pages": pages.get(CANDIDATE_INDEX, 0),
        "normal": normal,
        "active_npc": active_npc,
    }


def run_query_plan_fix(root: Path) -> dict[str, object]:
    root = _validate_query_plan_fix_root(root)
    directories, files = query_plan_fix_manifest(root)
    if any(not directory.is_dir() for directory in directories):
        raise ValueError("V26 query-plan fix manifest directory is missing")
    if files[0].exists():
        raise ValueError("V26 query-plan fix summary already exists")

    baseline_database = _initialize_registered_query_plan_database(
        root / "query-plan-01" / "baseline"
    )
    baseline = _fresh_query_plan_snapshot(baseline_database)

    candidate_database = _initialize_registered_query_plan_database(
        root / "query-plan-01" / "candidate"
    )
    validate_candidate_sql(DROP_CANDIDATE_SQL)
    with closing(_connect_for_setup(candidate_database)) as drop_connection:
        drop_connection.execute(DROP_CANDIDATE_SQL)
        drop_connection.commit()
    candidate = _fresh_query_plan_snapshot(candidate_database)

    failures = evaluate_query_plan_probe(baseline, candidate)
    summary: dict[str, object] = {
        "schema_version": "f-009-v26-query-plan-fix-v1",
        "connection_contract": {
            "baseline_explain_fresh_connection": True,
            "drop_committed_before_close": True,
            "drop_connection_closed_before_candidate_probe": True,
            "candidate_probe_fresh_connection": True,
        },
        "candidate_index": CANDIDATE_INDEX,
        "baseline": baseline,
        "candidate": candidate,
        "failures": list(failures),
        "status": "query_plan_gate_passed" if not failures else "failed",
    }
    serialized = json.dumps(summary, indent=2, sort_keys=True)
    if any(value in serialized for value in _FORBIDDEN_SUMMARY_VALUES) or _HEX_TAG.search(
        serialized
    ):
        raise ValueError("V26 query-plan fix summary contains forbidden synthetic payload")
    files[0].write_text(serialized + "\n", encoding="utf-8")
    return summary


def _insert_history(connection: sqlite3.Connection, *, count: int, now_ns: int) -> BudgetScopeTags:
    npc_tags = tuple(_tag(f"npc-{index}") for index in range(3))
    selected: BudgetScopeTags | None = None
    connection.execute("BEGIN IMMEDIATE")
    for index in range(count):
        execution_id = str(UUID(int=10_000_000 + index))
        request_id = str(UUID(int=20_000_000 + index))
        player = _tag(f"player-{index}")
        npc = npc_tags[index % 3]
        player_npc = _tag(f"player-npc-{index}-{index % 3}")
        conversation = _tag(f"conversation-{index}")
        created = now_ns - (count - index) * 1_000_000
        connection.execute(
            "INSERT INTO execution_admissions VALUES (?,?,?,?,?,?,?)",
            (
                execution_id,
                request_id,
                "f-009-safety-control-v1",
                player,
                player_npc,
                conversation,
                created,
            ),
        )
        connection.execute(
            "INSERT INTO budget_execution_owners VALUES (?,?,?,?,?,?)",
            (execution_id, "f-009-budget-policy-v1", player, npc, player_npc, created),
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
                created,
                None,
                None,
                None,
                None,
            ),
        )
        if index == 0:
            selected = BudgetScopeTags(player, npc, player_npc)
    assert selected is not None
    revision = 1
    for scope_class, scope_tag in (
        ("player_npc", selected.player_npc_scope_tag),
        ("player", selected.player_scope_tag),
        ("global", "0" * 64),
    ):
        connection.execute(
            "INSERT INTO budget_window_totals VALUES (?,?,?,?,?,?,?)",
            (scope_class, scope_tag, 0, 0, 0, revision, now_ns),
        )
    connection.execute(
        "INSERT INTO budget_window_projection_state VALUES (1,?,?,?,?,?,?)",
        (
            "f-009-budget-window-projection-v1",
            "f-009-budget-policy-v1",
            now_ns - 3_600_000_000_000,
            now_ns - 86_400_000_000_000,
            revision,
            now_ns,
        ),
    )
    connection.commit()
    return selected


def _timed_active_lookup(
    connection: sqlite3.Connection,
    *,
    scope_tag: str,
    now_ns: int,
) -> tuple[bool, list[float]]:
    for _ in range(10):
        SqliteSafetyControlRepository._projection_scope_has_active_ledger(
            connection,
            scope_class="npc",
            scope_tag=scope_tag,
            day_cutoff_ns=now_ns - 86_400_000_000_000,
        )
    samples: list[float] = []
    value = False
    for _ in range(100):
        started = time.perf_counter_ns()
        value = SqliteSafetyControlRepository._projection_scope_has_active_ledger(
            connection,
            scope_class="npc",
            scope_tag=scope_tag,
            day_cutoff_ns=now_ns - 86_400_000_000_000,
        )
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return value, samples


def _logical_digest(database: Path) -> str:
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as connection:
        tables = tuple(
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name<>'schema_migrations' ORDER BY name"
            )
        )
        payload: list[object] = []
        for table in tables:
            rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
            payload.append((table, sorted((tuple(row) for row in rows), key=repr)))
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def _history_scenario(directory: Path, *, count: int, candidate: bool) -> dict[str, object]:
    database = _initialize_database(directory, candidate=candidate)
    now_ns = 2_000_000_000_000_000_000
    with closing(_connect_for_setup(database)) as connection:
        selected = _insert_history(connection, count=count, now_ns=now_ns)
        active_value, active_samples = _timed_active_lookup(
            connection, scope_tag=selected.npc_scope_tag, now_ns=now_ns
        )
        missing_value, missing_samples = _timed_active_lookup(
            connection, scope_tag=_tag("npc-not-present"), now_ns=now_ns
        )
        active_failed_closed = False
        try:
            SqliteSafetyControlRepository._all_window_totals(
                connection,
                scope_tags=selected,
                now_ns=now_ns,
            )
        except SafetyControlStorageError:
            active_failed_closed = True
        negative_rejected = False
        try:
            connection.execute(
                "INSERT INTO budget_window_totals VALUES ('npc',?,-1,0,0,1,?)",
                (_tag("negative"), now_ns),
            )
        except sqlite3.IntegrityError:
            negative_rejected = True
        wrong_version_rejected = False
        try:
            connection.execute(
                "UPDATE budget_window_projection_state SET projection_version='wrong' "
                "WHERE singleton=1"
            )
        except sqlite3.IntegrityError:
            wrong_version_rejected = True
        connection.rollback()
    repository = SqliteSafetyControlRepository(database_path=database, allowed_root=directory)
    released, settled = repository.recover_open_budget_attempts(now_ns=now_ns + 1)
    repeated = repository.recover_open_budget_attempts(now_ns=now_ns + 2)
    with closing(_connect_for_setup(database)) as connection:
        connection.execute("DELETE FROM budget_window_projection_state")
        connection.commit()
    rebuilt = repository.recover_open_budget_attempts(now_ns=now_ns + 3)
    repository.close()
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as connection:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_key_errors = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        state_count = int(
            connection.execute("SELECT COUNT(*) FROM budget_window_projection_state").fetchone()[0]
        )
        released_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM budget_reservations WHERE status='released'"
            ).fetchone()[0]
        )
    failures: list[str] = []
    if not active_value or missing_value or not active_failed_closed:
        failures.append("projection_missing_scope_fail_closed_mismatch")
    if not negative_rejected or not wrong_version_rejected:
        failures.append("projection_constraint_rejection_failed")
    active_p95 = _percentile(active_samples, 0.95)
    missing_p95 = _percentile(missing_samples, 0.95)
    if max(active_p95, missing_p95) > QUERY_P95_LIMIT_MS:
        failures.append("projection_failure_lookup_p95_exceeded")
    if (
        released != count
        or settled != 0
        or repeated != (0, 0)
        or rebuilt != (0, 0)
        or state_count != 1
        or released_count != count
        or integrity != "ok"
        or foreign_key_errors != 0
    ):
        failures.append("projection_recovery_mismatch")
    return {
        "count": count,
        "variant": "candidate" if candidate else "baseline",
        "active": {"result": active_value, "p95_ms": active_p95},
        "missing": {"result": missing_value, "p95_ms": missing_p95},
        "active_missing_total_failed_closed": active_failed_closed,
        "negative_total_rejected": negative_rejected,
        "wrong_version_rejected": wrong_version_rejected,
        "first_recovery": [released, settled],
        "repeated_recovery": list(repeated),
        "missing_state_rebuild": list(rebuilt),
        "integrity": integrity,
        "foreign_key_errors": foreign_key_errors,
        "logical_digest": _logical_digest(database),
        "failures": failures,
    }


def _database_snapshot(database: Path) -> dict[str, int]:
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as connection:
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        freelist = int(connection.execute("PRAGMA freelist_count").fetchone()[0])
    return {
        "page_size": page_size,
        "page_count": page_count,
        "freelist_pages": freelist,
        "main_bytes": database.stat().st_size,
        "occupied_bytes": (page_count - freelist) * page_size,
    }


def _dbstat_pages(database: Path) -> dict[str, int]:
    if not SQLITE_TOOL.is_file():
        raise RuntimeError("V26 trusted dbstat tool is unavailable")
    completed = subprocess.run(
        (
            str(SQLITE_TOOL),
            "-readonly",
            "-json",
            str(database),
            "SELECT name,count(*) pages FROM dbstat GROUP BY name ORDER BY name",
        ),
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    )
    rows = json.loads(completed.stdout or "[]")
    return {str(row["name"]): int(row["pages"]) for row in rows}


def _audit_control_database(database: Path) -> dict[str, object]:
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as connection:
        counts = {
            table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in (
                "execution_admissions",
                "provider_permits",
                "budget_execution_owners",
                "budget_reservations",
                "budget_settlements",
                "breaker_execution_results",
                "control_execution_intents",
            )
        }
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_key_errors = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        unsettled = int(
            connection.execute(
                "SELECT COUNT(*) FROM budget_reservations WHERE status<>'settled'"
            ).fetchone()[0]
        )
        open_permits = int(
            connection.execute(
                "SELECT COUNT(*) FROM provider_permits WHERE released_at_ns IS NULL"
            ).fetchone()[0]
        )
        nonzero_cost = int(
            connection.execute(
                "SELECT COUNT(*) FROM budget_settlements WHERE actual_cost_micro_usd<>0"
            ).fetchone()[0]
        )
        intent_nonterminal = int(
            connection.execute(
                "SELECT COUNT(*) FROM control_execution_intents WHERE state<>'settled'"
            ).fetchone()[0]
        )
        journal = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
    return {
        "counts": counts,
        "integrity": integrity,
        "foreign_key_errors": foreign_key_errors,
        "unsettled_reservations": unsettled,
        "open_permits": open_permits,
        "nonzero_cost_settlements": nonzero_cost,
        "nonterminal_intents": intent_nonterminal,
        "journal_mode": journal,
        "synchronous": synchronous,
    }


async def _populate_full_control(directory: Path, *, candidate: bool) -> dict[str, object]:
    database = _initialize_database(directory, candidate=candidate)
    repository = SqliteSafetyControlRepository(database_path=database, allowed_root=directory)
    clock = _SyntheticClock()
    control = SafetyControl(
        repository=repository,
        scope_key=SYNTHETIC_KEY,
        clock_ns=clock.time_ns,
        monotonic_clock=clock.monotonic,
        pricing_policy=PricingPolicy.zero_cost(provider_kind=ProviderKind.FAKE, model="fake-model"),
    )
    initial = _database_snapshot(database)
    peak_wal = 0
    peak_shm = 0
    try:
        for index in range(SPACE_EXECUTIONS):
            request = DialogueRequestV1(
                request_id=UUID(int=30_000_000 + index),
                player_id=f"bench_player_{index:03d}",
                npc_id=("neon_guide", "signal_archivist", "night_courier")[index % 3],
                conversation_id=UUID(int=40_000_000 + index),
                message="Synthetic local benchmark.",
            )
            execution_id = UUID(int=50_000_000 + index)
            control.admit_ingress(peer_host="127.0.0.1")
            control.admit_execution(request=request, execution_id=execution_id)
            admission = await control.admit_provider_dispatch(
                request=request,
                execution_id=execution_id,
                attempt_number=1,
            )
            await control.finalize_provider_success(admission, usage=ProviderUsage(0, 0))
            clock.advance(2.0)
            wal = Path(str(database) + "-wal")
            shm = Path(str(database) + "-shm")
            peak_wal = max(peak_wal, wal.stat().st_size if wal.exists() else 0)
            peak_shm = max(peak_shm, shm.stat().st_size if shm.exists() else 0)
    finally:
        repository.close()
    final = _database_snapshot(database)
    pages = _dbstat_pages(database)
    return {
        "database": database,
        "initial": initial,
        "final": final,
        "object_pages": pages,
        "candidate_index_pages": pages.get(CANDIDATE_INDEX, 0),
        "peak_wal_bytes": peak_wal,
        "peak_shm_bytes": peak_shm,
        "audit": _audit_control_database(database),
        "logical_digest": _logical_digest(database),
    }


def _space_result_for_json(result: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in result.items() if key != "database"}


def _space_pair_snapshot(result: dict[str, object]) -> SpaceSnapshot:
    initial = result["initial"]
    final = result["final"]
    assert isinstance(initial, dict) and isinstance(final, dict)
    candidate_index_pages = result["candidate_index_pages"]
    assert isinstance(candidate_index_pages, int)
    return SpaceSnapshot(
        initial_occupied_bytes=cast(int, initial["occupied_bytes"]),
        final_occupied_bytes=cast(int, final["occupied_bytes"]),
        initial_freelist_pages=cast(int, initial["freelist_pages"]),
        final_freelist_pages=cast(int, final["freelist_pages"]),
        candidate_index_pages=candidate_index_pages,
    )


def _audit_failures(audit: dict[str, object]) -> list[str]:
    counts = audit["counts"]
    assert isinstance(counts, dict)
    expected = {name: SPACE_EXECUTIONS for name in counts}
    if counts != expected:
        return ["control_row_ownership_mismatch"]
    if (
        audit["integrity"] != "ok"
        or audit["foreign_key_errors"] != 0
        or audit["unsettled_reservations"] != 0
        or audit["open_permits"] != 0
        or audit["nonzero_cost_settlements"] != 0
        or audit["nonterminal_intents"] != 0
        or audit["journal_mode"] != "wal"
        or audit["synchronous"] != 2
    ):
        return ["control_database_audit_failed"]
    return []


async def run_preflight(root: Path) -> dict[str, object]:
    root = _validate_root(root)
    directories, files = manifest(root)
    if files[0].exists():
        raise ValueError("V26 summary already exists")
    scenario_start = directories.index(root / "query-plan-01")
    for directory in directories[scenario_start:]:
        if directory.exists():
            raise ValueError("V26 scenario path already exists")
    query_plan = _query_plan_scenario(root / "query-plan-01")
    history: list[dict[str, object]] = []
    for size in HISTORY_SIZES:
        history.append(
            _history_scenario(root / f"history-{size}-baseline", count=size, candidate=False)
        )
        history.append(
            _history_scenario(root / f"history-{size}-candidate", count=size, candidate=True)
        )
    history_failures = [
        failure for item in history for failure in cast(list[str], item["failures"])
    ]
    for size in HISTORY_SIZES:
        baseline, candidate = (item for item in history if item["count"] == size)
        if baseline["logical_digest"] != candidate["logical_digest"]:
            history_failures.append(f"history_{size}_logical_digest_mismatch")
    space_pairs: list[dict[str, object]] = []
    for pair in range(1, SPACE_PAIR_COUNT + 1):
        pair_root = root / f"space-pair-{pair:02d}"
        pair_root.mkdir()
        baseline = await _populate_full_control(pair_root / "baseline", candidate=False)
        candidate = await _populate_full_control(pair_root / "candidate", candidate=True)
        failures = list(
            evaluate_space_pair(_space_pair_snapshot(baseline), _space_pair_snapshot(candidate))
        )
        if baseline["logical_digest"] != candidate["logical_digest"]:
            failures.append("space_pair_logical_digest_mismatch")
        failures.extend(_audit_failures(cast(dict[str, object], baseline["audit"])))
        failures.extend(_audit_failures(cast(dict[str, object], candidate["audit"])))
        space_pairs.append(
            {
                "pair": pair,
                "baseline": _space_result_for_json(baseline),
                "candidate": _space_result_for_json(candidate),
                "occupied_saving_bytes": (
                    _space_pair_snapshot(baseline).occupied_growth_bytes
                    - _space_pair_snapshot(candidate).occupied_growth_bytes
                ),
                "failures": failures,
            }
        )
    all_failures = [*cast(list[str], query_plan["failures"]), *history_failures]
    all_failures.extend(
        failure for pair in space_pairs for failure in cast(list[str], pair["failures"])
    )
    summary: dict[str, object] = {
        "schema_version": "f-009-v26-control-space-preflight-v1",
        "candidate_index": CANDIDATE_INDEX,
        "space_limit_bytes": SPACE_LIMIT_BYTES,
        "required_saving_bytes": REQUIRED_SAVING_BYTES,
        "query_plan": query_plan,
        "history": history,
        "space_pairs": space_pairs,
        "failures": sorted(set(str(value) for value in all_failures)),
        "status": "synthetic_candidate_passed" if not all_failures else "failed",
    }
    serialized = json.dumps(summary, indent=2, sort_keys=True)
    if any(value in serialized for value in _FORBIDDEN_SUMMARY_VALUES):
        raise ValueError("V26 summary contains forbidden synthetic payload")
    files[0].write_text(serialized + "\n", encoding="utf-8")
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--query-plan-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.query_plan_only:
        summary = run_query_plan_fix(args.root)
        print(
            json.dumps(
                {
                    "status": summary["status"],
                    "failure_codes": summary["failures"],
                },
                sort_keys=True,
            )
        )
        return 0 if summary["status"] == "query_plan_gate_passed" else 1
    summary = asyncio.run(run_preflight(args.root))
    space_pairs = cast(list[dict[str, object]], summary["space_pairs"])
    print(
        json.dumps(
            {
                "status": summary["status"],
                "failure_codes": summary["failures"],
                "space_pair_count": len(space_pairs),
            },
            sort_keys=True,
        )
    )
    return 0 if summary["status"] == "synthetic_candidate_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
