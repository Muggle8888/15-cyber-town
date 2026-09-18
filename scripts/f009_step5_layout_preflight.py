"""D1 candidate B: synthetic leaf layouts only, never a product migration."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
from contextlib import ExitStack, closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import NAMESPACE_URL, UUID, uuid5

from httpx import ASGITransport, AsyncClient

from cyber_town.api.app import create_app
from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import SafetyControl
from cyber_town.application.dialogue import DialogueExecutionConfig, DialogueService
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.observability import (
    DialogueObservability,
    ProviderKind,
    RecordStatus,
    TraceMetadata,
    TraceStageMetadata,
)
from cyber_town.application.relationship import RelationshipService
from cyber_town.domain.persona import load_bundled_personas
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.llm.fake import FakeProvider
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.persistence.sqlite_long_term_memory import (
    SqliteLongTermMemoryRepository,
)
from cyber_town.infrastructure.persistence.sqlite_relationship import SqliteRelationshipRepository
from scripts.f009_step5_benchmark import SYNTHETIC_KEY, SyntheticClock, _completion, _stages, _trace
from scripts.f009_step5_index_preflight import (
    CONTROL_INDEXES,
    OBSERVABILITY_INDEXES,
    _file_sizes,
    _snapshot,
    growth_failures,
)
from scripts.f009_step5_storage_breakdown import _growth, analyze_image, catalog

ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2")
COUNT = 100
LEAF_TABLES = {
    "control": (
        "token_buckets",
        "provider_permits",
        "budget_settlements",
        "breaker_execution_results",
    ),
    "observability": (
        "trace_stage_events",
        "execution_links",
        "safety_cost_events",
        "retry_breaker_events",
    ),
}
REMOVED_INDEXES = {"control": CONTROL_INDEXES, "observability": OBSERVABILITY_INDEXES}


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError("layout_" + code)


def _tables(connection: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"
        )
    ]


def row_digest(connection: sqlite3.Connection, *, exclude_migration_time: bool = False) -> str:
    """Hash, never return, synthetic records; no dependence on rowid/physical order."""
    rows = []
    for table in _tables(connection):
        columns = [row[1] for row in connection.execute(f'PRAGMA table_xinfo("{table}")')]
        if exclude_migration_time and table == "schema_migrations":
            columns = [
                name
                for name in columns
                if name not in ("applied_at", "applied_at_ms", "applied_at_ns")
            ]
        names = ",".join(f'"{name}"' for name in columns)
        values = connection.execute(f'SELECT {names} FROM "{table}" ORDER BY {names}').fetchall()
        rows.append((table, values))
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def schema_contract(connection: sqlite3.Connection) -> dict[str, Any]:
    """Compare all logical DDL, defaults, columns, FKs and unique keys, not locators."""
    result: dict[str, Any] = {}
    excluded = set(CONTROL_INDEXES) | set(OBSERVABILITY_INDEXES)
    for table in _tables(connection):
        sql = connection.execute("SELECT sql FROM sqlite_schema WHERE name=?", (table,)).fetchone()[
            0
        ]
        body = sql[sql.index("(") :].replace(", WITHOUT ROWID", "")
        unique = []
        for index in connection.execute(f'PRAGMA index_list("{table}")'):
            if index[2]:
                keys = tuple(
                    row[2] for row in connection.execute(f'PRAGMA index_info("{index[1]}")')
                )
                unique.append((index[3], keys, index[4]))
        result[table] = {
            "body": body,
            "columns": connection.execute(f'PRAGMA table_xinfo("{table}")').fetchall(),
            "foreign_keys": connection.execute(f'PRAGMA foreign_key_list("{table}")').fetchall(),
            "unique": sorted(unique),
        }
    result["named_indexes"] = [
        row
        for row in connection.execute(
            "SELECT name, tbl_name, sql FROM sqlite_schema "
            "WHERE type='index' AND sql IS NOT NULL ORDER BY name"
        )
        if row[0] not in excluded
    ]
    return result


def rebuild_layout(
    connection: sqlite3.Connection, kind: str, *, fail_after: int | None = None
) -> dict[str, Any]:
    """Atomic leaf rebuild on an owned experimental DB, or an in-memory test DB."""
    _require(kind in LEAF_TABLES, "kind")
    filename = connection.execute("PRAGMA database_list").fetchone()[2]
    if filename:
        path = Path(filename)
        _require(path.resolve().is_relative_to(ROOT.resolve()), "database_boundary")
        _require(
            not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)), "reparse"
        )
    _require(not connection.in_transaction, "transaction_already_active")
    _require(connection.execute("PRAGMA foreign_keys").fetchone() == (1,), "foreign_keys_required")
    _require(connection.execute("PRAGMA page_size").fetchone() == (4096,), "page_size")
    _require(connection.execute("PRAGMA user_version").fetchone() == (3,), "version")
    leafs = LEAF_TABLES[kind]
    info = {row[1]: row for row in connection.execute("PRAGMA table_list")}
    for table in leafs:
        _require(table in info and info[table][4:] == (0, 1), "initial_layout")
    for table in _tables(connection):
        _require(
            not any(
                row[2] in leafs for row in connection.execute(f'PRAGMA foreign_key_list("{table}")')
            ),
            "incoming_fk",
        )
    contract, digest = schema_contract(connection), row_digest(connection)
    all_indexes = dict(
        connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL"
        )
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for index, table in REMOVED_INDEXES[kind].items():
            entry = next(
                (
                    row
                    for row in connection.execute(f'PRAGMA index_list("{table}")')
                    if row[1] == index
                ),
                None,
            )
            _require(entry is not None and entry[2:4] == (0, "c"), "index_boundary")
            connection.execute(f'DROP INDEX "{index}"')
        for position, table in enumerate(leafs, 1):
            old_sql = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE name=?", (table,)
            ).fetchone()[0]
            _require(old_sql.endswith(") STRICT"), "ddl_shape")
            temporary = "d1_new_" + table
            # Keep the complete original column/constraint body verbatim. Only the
            # physical layout and temporary table name change; FKs remain enabled.
            connection.execute(
                f'CREATE TABLE "{temporary}" ' + old_sql[old_sql.index("(") :] + ", WITHOUT ROWID"
            )
            columns = ",".join(
                f'"{row[1]}"' for row in connection.execute(f'PRAGMA table_xinfo("{table}")')
            )
            connection.execute(
                f'INSERT INTO "{temporary}" ({columns}) SELECT {columns} FROM "{table}"'
            )
            retained = [
                row[0]
                for row in connection.execute(
                    "SELECT sql FROM sqlite_schema WHERE type='index' "
                    "AND tbl_name=? AND sql IS NOT NULL ORDER BY name",
                    (table,),
                )
            ]
            connection.execute(f'DROP TABLE "{table}"')
            connection.execute(f'ALTER TABLE "{temporary}" RENAME TO "{table}"')
            for sql in retained:
                connection.execute(sql)
            if fail_after == position:
                raise ValueError("layout_injected_failure")
        _require(schema_contract(connection) == contract, "logical_contract_changed")
        _require(row_digest(connection) == digest, "rows_changed")
        final_indexes = dict(
            connection.execute(
                "SELECT name, sql FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL"
            )
        )
        _require(
            final_indexes
            == {k: v for k, v in all_indexes.items() if k not in REMOVED_INDEXES[kind]},
            "named_indexes_changed",
        )
        _require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "fk_integrity")
        _require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "integrity")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return {
        "tables": list(leafs),
        "removed_indexes": sorted(REMOVED_INDEXES[kind]),
        "logical_contract_unchanged": True,
        "rows_unchanged": True,
    }


def _capture(path: Path) -> dict[str, Any]:
    _require(path.resolve().is_relative_to(ROOT.resolve()), "capture_boundary")
    with closing(sqlite3.connect(path)) as connection:
        checkpoint = connection.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
        _require(checkpoint[0] == 0 and checkpoint[1] == checkpoint[2], "checkpoint_busy")
        roots = catalog(connection)
    sizes = _file_sizes(path)
    _require(sizes["wal_bytes"] == 0, "uncheckpointed_wal")
    result = analyze_image(path.read_bytes(), roots)
    result["closed_file_sizes"] = sizes
    return result


class _CheckedRecorder(SqliteObservabilityRepository):
    """Read back each committed stage on a fresh connection; no batching changes."""

    def __init__(self, *, database_path: Path, allowed_root: Path) -> None:
        super().__init__(database_path=database_path, allowed_root=allowed_root)
        self.path = database_path
        self.open_checks = 0
        self.progress_checks = 0

    def start_trace(self, trace: TraceMetadata) -> None:
        super().start_trace(trace)
        with closing(sqlite3.connect(self.path)) as connection:
            _require(
                connection.execute(
                    "SELECT record_status FROM trace_runs WHERE trace_id=?", (str(trace.trace_id),)
                ).fetchone()
                == ("open",),
                "open_not_durable",
            )
        self.open_checks += 1

    def record_progress(self, trace: TraceMetadata, stage: TraceStageMetadata) -> None:
        super().record_progress(trace, stage)
        with closing(sqlite3.connect(self.path)) as connection:
            _require(
                connection.execute(
                    "SELECT stage, outcome FROM trace_stage_events WHERE trace_id=? AND sequence=?",
                    (str(trace.trace_id), stage.sequence),
                ).fetchone()
                == (stage.stage.value, stage.outcome.value),
                "stage_not_durable",
            )
        self.progress_checks += 1


def _ids(label: str) -> list[UUID]:
    return [uuid5(NAMESPACE_URL, f"f009-d1-synthetic/{label}/{i:03d}") for i in range(COUNT)]


async def _variant(root: Path, *, candidate: bool) -> dict[str, Any]:
    root.mkdir()
    paths = {name: root / f"{name}.sqlite3" for name in ("business", "control", "observability")}
    # Fresh empty files only. Page size is fixed before any bundled schema exists.
    for path in paths.values():
        _require(not path.exists(), "database_exists")
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("PRAGMA page_size=4096")
    memory = SqliteLongTermMemoryRepository(database_path=paths["business"], allowed_root=root)
    memory.initialize()
    relationship = SqliteRelationshipRepository(database_path=paths["business"], allowed_root=root)
    relationship.initialize()
    control = SqliteSafetyControlRepository(database_path=paths["control"], allowed_root=root)
    control.initialize()
    recorder = _CheckedRecorder(database_path=paths["observability"], allowed_root=root)
    recorder.initialize()
    changes = {}
    if candidate:
        for kind in LEAF_TABLES:
            with closing(sqlite3.connect(paths[kind])) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA temp_store=MEMORY")
                changes[kind] = rebuild_layout(connection, kind)
    before = {name: _snapshot(path) for name, path in paths.items()}
    before_objects = {name: _capture(paths[name]) for name in LEAF_TABLES}
    clock = SyntheticClock()

    def wall() -> datetime:
        return datetime.fromtimestamp(clock.time_ns() / 1_000_000_000, tz=UTC)

    provider = FakeProvider(_completion() for _ in range(COUNT))
    safety = SafetyControl(
        repository=control,
        scope_key=SYNTHETIC_KEY,
        clock_ns=clock.time_ns,
        monotonic_clock=clock.monotonic,
        pricing_policy=PricingPolicy.zero_cost(provider_kind=ProviderKind.FAKE, model="fake-model"),
    )
    with ExitStack() as stack:
        # Patch only composition factories/ID sources inside this diagnostic run.
        # No production clocks, event counts, commit semantics or files are edited.
        stack.enter_context(
            patch(
                "cyber_town.application.dialogue.DialogueObservability",
                partial(DialogueObservability, wall_clock=wall),
            )
        )
        for module, label in (
            ("api.dialogue", "trace"),
            ("application.dialogue", "execution"),
            ("infrastructure.persistence.sqlite_relationship", "relationship"),
        ):
            stack.enter_context(patch("cyber_town." + module + ".uuid4", side_effect=_ids(label)))
        service = DialogueService(
            personas=load_bundled_personas(),
            provider=provider,
            config=DialogueExecutionConfig(
                model="fake-model",
                temperature=0.6,
                max_tokens=256,
                timeout_seconds=12,
                max_concurrency=2,
                idempotency_ttl_seconds=600,
                idempotency_max_entries=256,
            ),
            clock=clock.monotonic,
            long_term_memory=LongTermMemoryService(
                repository=memory, clock=lambda: clock.time_ns() // 1_000_000_000
            ),
            long_term_retriever=LongTermMemoryRetriever(
                repository=memory, clock=lambda: clock.time_ns() // 1_000_000_000
            ),
            relationship_service=RelationshipService(repository=relationship, now=wall),
            safety_control=safety,
            observability_recorder=recorder,
            observability_scope_key=SYNTHETIC_KEY,
            observability_provider_kind=ProviderKind.FAKE,
            safety_cost_recorder=recorder,
            retry_breaker_recorder=recorder,
        )
        app = create_app(service, observability_recorder=recorder)
        peaks = {name: _file_sizes(path) for name, path in paths.items()}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://localhost"
        ) as client:
            for index in range(COUNT):
                response = await client.post(
                    "/api/v1/dialogue",
                    json={
                        "request_id": str(UUID(int=1000 + index)),
                        "player_id": f"bench_player_{index:03d}",
                        "npc_id": ("neon_guide", "signal_archivist", "night_courier")[index % 3],
                        "conversation_id": str(UUID(int=index + 1)),
                        "message": "Synthetic local benchmark.",
                    },
                )
                _require(response.status_code == 200, "request_failed")
                clock.advance(1.0)
                for name, path in paths.items():
                    for kind, size in _file_sizes(path).items():
                        peaks[name][kind] = max(peaks[name][kind], size)
                if (index + 1) % 20 == 0:
                    print(json.dumps({"variant": root.name, "completed": index + 1}), flush=True)
    after = {name: _snapshot(path) for name, path in paths.items()}
    digests = {}
    for name, path in paths.items():
        with closing(sqlite3.connect(path)) as connection:
            digests[name] = row_digest(connection, exclude_migration_time=True)
    with closing(sqlite3.connect(paths["observability"])) as connection:
        completed = connection.execute(
            "SELECT COUNT(*) FROM trace_runs WHERE terminal_outcome='completed'"
        ).fetchone()[0]
        malformed = connection.execute(
            "SELECT COUNT(*) FROM (SELECT trace_id FROM trace_stage_events "
            "GROUP BY trace_id HAVING COUNT(*)<>14)"
        ).fetchone()[0]
        cost = connection.execute(
            "SELECT SUM(actual_cost_micro_usd) FROM safety_cost_events"
        ).fetchone()[0]
    return {
        "before": before,
        "after": after,
        "before_objects": before_objects,
        "after_objects": {name: _capture(paths[name]) for name in LEAF_TABLES},
        "changes": changes,
        "sampled_after_request_surface_peaks": peaks,
        "completed_count": completed,
        "provider_dispatch_count": provider.call_count,
        "malformed_stage_trace_count": malformed,
        "actual_cost_micro_usd": cost,
        "durable_open_checks": recorder.open_checks,
        "durable_progress_checks": recorder.progress_checks,
        "synthetic_row_digests_excluding_migration_time": digests,
    }


def _restart_check(root: Path) -> dict[str, Any]:
    root.mkdir()
    path = root / "observability.sqlite3"
    recorder = _CheckedRecorder(database_path=path, allowed_root=root)
    recorder.initialize()
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        rebuild_layout(connection, "observability")
    complete = replace(
        _trace(),
        trace_id=_ids("restart-trace")[0],
        request_id=_ids("restart-request")[0],
        execution_id=_ids("restart-execution")[0],
    )
    recorder.save_trace(complete, _stages(complete))
    pending = replace(
        complete,
        trace_id=_ids("restart-trace")[1],
        request_id=_ids("restart-request")[1],
        execution_id=_ids("restart-execution")[1],
        record_status=RecordStatus.OPEN,
        terminal_outcome=None,
        finished_at_utc=None,
    )
    recorder.start_trace(pending)
    stages = tuple(replace(s, trace_id=pending.trace_id) for s in _stages(complete))
    for stage in stages[:9]:
        recorder.record_progress(pending, stage)
    with closing(sqlite3.connect(path)) as connection:
        complete_before = connection.execute(
            "SELECT * FROM trace_runs WHERE trace_id=?", (str(complete.trace_id),)
        ).fetchone()
        stages_before = connection.execute(
            "SELECT * FROM trace_stage_events WHERE trace_id=? ORDER BY sequence",
            (str(complete.trace_id),),
        ).fetchall()
    restarted = SqliteObservabilityRepository(database_path=path, allowed_root=root)
    restarted.initialize()
    now = complete.started_at_utc + timedelta(seconds=30)
    _require(restarted.recover_open_traces(now_utc=now) == 1, "recovery_count")
    with closing(sqlite3.connect(path)) as connection:
        digest = row_digest(connection)
        _require(
            connection.execute(
                "SELECT record_status, terminal_outcome FROM trace_runs WHERE trace_id=?",
                (str(pending.trace_id),),
            ).fetchone()
            == ("partial", "abandoned_after_restart"),
            "recovery_outcome",
        )
        _require(
            connection.execute(
                "SELECT * FROM trace_runs WHERE trace_id=?", (str(complete.trace_id),)
            ).fetchone()
            == complete_before,
            "recovery_changed_completed",
        )
        _require(
            connection.execute(
                "SELECT * FROM trace_stage_events WHERE trace_id=? ORDER BY sequence",
                (str(complete.trace_id),),
            ).fetchall()
            == stages_before,
            "recovery_changed_completed_stages",
        )
        _require(
            connection.execute("SELECT COUNT(*) FROM trace_stage_events").fetchone() == (28,),
            "recovery_stages",
        )
    _require(restarted.recover_open_traces(now_utc=now) == 0, "recovery_not_idempotent")
    with closing(sqlite3.connect(path)) as connection:
        _require(row_digest(connection) == digest, "recovery_repeated_write")
    return {
        "durable_open_checks": recorder.open_checks,
        "durable_progress_checks": recorder.progress_checks,
        "abandoned_count": 1,
        "complete_unchanged": True,
        "recovery_idempotent": True,
        "snapshot": _snapshot(path),
    }


def main() -> int:
    _require(ROOT.resolve(strict=True) == ROOT, "root_boundary")
    _require(
        not any(p.is_symlink() or p.is_junction() for p in (ROOT, *ROOT.parents)), "root_reparse"
    )
    paired_root = ROOT / "paired-fixed"
    _require(not paired_root.exists(), "output_exists")
    paired_root.mkdir()
    restart = _restart_check(paired_root / "restart")
    results = {
        "baseline": asyncio.run(_variant(paired_root / "baseline-v3", candidate=False)),
        "candidate": asyncio.run(_variant(paired_root / "candidate-b", candidate=True)),
    }
    for result in results.values():
        _require(
            result["completed_count"]
            == result["provider_dispatch_count"]
            == result["durable_open_checks"]
            == COUNT,
            "execution_count",
        )
        _require(
            result["malformed_stage_trace_count"] == result["actual_cost_micro_usd"] == 0,
            "event_invariants",
        )
        _require(result["durable_progress_checks"] >= 13 * COUNT, "incremental_stage_count")
        rows = result["after"]["observability"]["rows"]
        _require(
            rows["trace_stage_events"] == 14 * COUNT
            and rows["safety_cost_events"] == 3 * COUNT
            and rows["retry_breaker_events"] == 2 * COUNT,
            "event_counts",
        )
        for state in result["after"].values():
            _require(
                state["integrity_ok"]
                and state["foreign_key_errors"] == 0
                and state["page_size"] == 4096,
                "database_integrity",
            )
        result["growth"] = {name: _growth(result, name) for name in LEAF_TABLES}
        result["business_growth_bytes"] = (
            result["after"]["business"]["main_bytes"] - result["before"]["business"]["main_bytes"]
        )
    _require(
        results["baseline"]["synthetic_row_digests_excluding_migration_time"]
        == results["candidate"]["synthetic_row_digests_excluding_migration_time"],
        "paired_data_mismatch",
    )
    failures = growth_failures(
        control=results["candidate"]["growth"]["control"]["occupied_growth_bytes"],
        observability=results["candidate"]["growth"]["observability"]["occupied_growth_bytes"],
    )
    report = {
        "diagnostic_version": "f009-layout-preflight-v2",
        "schema_version": 1,
        "transport": "in_process_asgi_not_latency_acceptance",
        "product_migration_applied": False,
        "workload": "100_unique_executions_fixed_serial_order_three_npc_fake_full_three_db",
        "clock": "fixed_synthetic_wall_and_monotonic_per_request_not_latency_measurement",
        "migration_time_excluded_from_paired_digest": True,
        "growth_failures": failures,
        "restart": restart,
        **results,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True)
    sentinels = [
        SYNTHETIC_KEY.decode(),
        "bench_player_",
        "Synthetic local benchmark.",
        str(_completion().content),
        "neon_guide",
        "signal_archivist",
        "night_courier",
        *(str(UUID(int=i + 1)) for i in range(COUNT)),
    ]
    _require(not any(value in encoded for value in sentinels), "forbidden_content")
    with (paired_root / "summary.json").open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    print(
        json.dumps(
            {
                "prevalidation_passed": not failures,
                "growth_failures": failures,
                "paired_data_equal": True,
                "forbidden_content_hits": 0,
            }
        ),
        flush=True,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
