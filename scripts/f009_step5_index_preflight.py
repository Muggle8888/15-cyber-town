"""Synthetic index-only storage preflight; never installs a product migration."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any
from uuid import UUID

from httpx import ASGITransport, AsyncClient

from cyber_town.api.app import create_app
from cyber_town.application.budget import PricingPolicy
from cyber_town.application.control import SafetyControl
from cyber_town.application.dialogue import DialogueExecutionConfig, DialogueService
from cyber_town.application.long_term_memory import LongTermMemoryRetriever, LongTermMemoryService
from cyber_town.application.observability import ProviderKind
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
from scripts.f009_step5_benchmark import SYNTHETIC_KEY, SyntheticClock, _completion

ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests")
COUNT = 100
CONTROL_INDEXES = {
    "execution_admissions_request_idx": "execution_admissions",
    "idx_budget_attempt_execution_status": "budget_reservations",
    "idx_budget_cost_window_time": "budget_settlements",
    "breaker_results_scope_time_idx": "breaker_execution_results",
}
OBSERVABILITY_INDEXES = {
    "idx_trace_stage_events_stage_outcome": "trace_stage_events",
    "idx_trace_stage_events_retention": "trace_stage_events",
    "idx_execution_links_retention": "execution_links",
    "idx_safety_cost_player_window": "safety_cost_events",
    "idx_safety_cost_npc_window": "safety_cost_events",
    "idx_safety_cost_player_npc_window": "safety_cost_events",
}


def growth_failures(*, control: int, observability: int) -> tuple[str, ...]:
    failures: list[str] = []
    if control > 256 * 1024:
        failures.append("control_growth_exceeded")
    if observability > 512 * 1024:
        failures.append("observability_growth_exceeded")
    if control + observability > 768 * 1024:
        failures.append("combined_growth_exceeded")
    return tuple(failures)


def occupied_growth(
    before_pages: int, before_free: int, after_pages: int, after_free: int, page_size: int
) -> int:
    return ((after_pages - after_free) - (before_pages - before_free)) * page_size


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _schema_and_rows(connection: sqlite3.Connection) -> tuple[str, str]:
    tables = connection.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    unique: list[tuple[str, tuple[Any, ...], Any]] = []
    rows = []
    for name, _ in tables:
        # Names originate only from the freshly initialized bundled schemas.
        unique.extend(
            (
                name,
                entry,
                connection.execute(
                    "SELECT sql FROM sqlite_master WHERE name=?", (entry[1],)
                ).fetchone(),
            )
            for entry in connection.execute(f'PRAGMA index_list("{name}")')
            if entry[2]
        )
        rows.append((name, connection.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall()))
    # index_list sequence numbers may change when a non-unique index is removed.
    stable_unique = sorted((name, entry[1:], sql) for name, entry, sql in unique)
    return _digest((tables, stable_unique)), _digest(rows)


def _apply_candidate(path: Path, candidates: dict[str, str]) -> dict[str, object]:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        before = _schema_and_rows(connection)
        before_indexes = set(
            connection.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        )
        connection.execute("BEGIN IMMEDIATE")
        try:
            for name, table in candidates.items():
                indexes = {
                    row[1]: row for row in connection.execute(f'PRAGMA index_list("{table}")')
                }
                if name not in indexes or indexes[name][2] != 0 or indexes[name][3] != "c":
                    raise ValueError("candidate_index_boundary_mismatch")
                connection.execute(f'DROP INDEX "{name}"')
            after_indexes = set(
                connection.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
            )
            if before_indexes - after_indexes != {(name,) for name in candidates}:
                raise ValueError("candidate_index_set_mismatch")
            if _schema_and_rows(connection) != before:
                raise ValueError("candidate_changed_schema_or_rows")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("candidate_foreign_key_failure")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return {"removed_indexes": sorted(candidates), "schema_constraints_rows_unchanged": True}


def _snapshot(path: Path) -> dict[str, Any]:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA wal_checkpoint(FULL)")
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        result = {
            "page_size": connection.execute("PRAGMA page_size").fetchone()[0],
            "page_count": connection.execute("PRAGMA page_count").fetchone()[0],
            "freelist_count": connection.execute("PRAGMA freelist_count").fetchone()[0],
            "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "integrity_ok": connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)],
            "foreign_key_errors": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
            "rows": {
                name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                for name in tables
            },
        }
    result.update(_file_sizes(path))
    return result


def _file_sizes(path: Path) -> dict[str, int]:
    return {
        kind: item.stat().st_size if item.exists() else 0
        for kind, item in (
            ("main_bytes", path),
            ("wal_bytes", Path(str(path) + "-wal")),
            ("shm_bytes", Path(str(path) + "-shm")),
        )
    }


def _query_checks(path: Path, *, control: bool) -> dict[str, object]:
    if control:
        queries = {
            "admission_pk": "SELECT COUNT(*) FROM execution_admissions WHERE execution_id=?",
            "attempt_pk": (
                "SELECT COUNT(*) FROM budget_reservations "
                "WHERE execution_id=? AND status<>'released'"
            ),
            "breaker_result_pk": (
                "SELECT COUNT(*) FROM breaker_execution_results WHERE execution_id=?"
            ),
            "budget_window": (
                "SELECT COALESCE(SUM(s.actual_cost_micro_usd),0) "
                "FROM budget_reservations r JOIN budget_execution_owners o USING(execution_id) "
                "LEFT JOIN budget_settlements s USING(execution_id,attempt_number) "
                "WHERE r.reserved_at_ns>0 AND o.player_scope_tag=?"
            ),
        }
        seed_sql = "SELECT execution_id,player_scope_tag FROM execution_admissions LIMIT 1"
    else:
        queries = {
            "stage_pk": "SELECT COUNT(*) FROM trace_stage_events WHERE trace_id=?",
            "stage_retention_count": (
                "SELECT COUNT(*) FROM trace_stage_events "
                "WHERE retention_status='active' AND ? IS NOT NULL"
            ),
            "link_retention_count": (
                "SELECT COUNT(*) FROM execution_links "
                "WHERE retention_status='active' AND ? IS NOT NULL"
            ),
            "safety_cost_pk": (
                "SELECT COUNT(*) FROM safety_cost_events WHERE trace_id=? AND attempt_number=1"
            ),
        }
        seed_sql = "SELECT trace_id,trace_id FROM trace_runs LIMIT 1"
    result: dict[str, object] = {}
    with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)) as connection:
        seed = connection.execute(seed_sql).fetchone()
        for label, sql in queries.items():
            params = (seed[1] if label == "budget_window" else seed[0],)
            plan = [row[3] for row in connection.execute("EXPLAIN QUERY PLAN " + sql, params)]
            samples = []
            rows: list[tuple[Any, ...]] = []
            for _ in range(20):
                started = time.perf_counter()
                rows = connection.execute(sql, params).fetchall()
                samples.append((time.perf_counter() - started) * 1000)
            result[label] = {"plan": plan, "result": rows, "max_ms": max(samples)}
    return result


async def _run_variant(root: Path, *, candidate: bool) -> dict[str, Any]:
    root.mkdir()
    paths = {name: root / f"{name}.sqlite3" for name in ("business", "control", "observability")}
    memory = SqliteLongTermMemoryRepository(database_path=paths["business"], allowed_root=root)
    memory.initialize()
    relationship = SqliteRelationshipRepository(database_path=paths["business"], allowed_root=root)
    relationship.initialize()
    control = SqliteSafetyControlRepository(database_path=paths["control"], allowed_root=root)
    control.initialize()
    recorder = SqliteObservabilityRepository(
        database_path=paths["observability"], allowed_root=root
    )
    recorder.initialize()
    candidate_changes = {}
    if candidate:
        candidate_changes = {
            "control": _apply_candidate(paths["control"], CONTROL_INDEXES),
            "observability": _apply_candidate(paths["observability"], OBSERVABILITY_INDEXES),
        }
    before = {name: _snapshot(path) for name, path in paths.items()}
    clock = SyntheticClock()
    provider = FakeProvider(_completion() for _ in range(COUNT))
    safety = SafetyControl(
        repository=control,
        scope_key=SYNTHETIC_KEY,
        clock_ns=clock.time_ns,
        monotonic_clock=clock.monotonic,
        pricing_policy=PricingPolicy.zero_cost(provider_kind=ProviderKind.FAKE, model="fake-model"),
    )
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
        long_term_memory=LongTermMemoryService(repository=memory),
        long_term_retriever=LongTermMemoryRetriever(repository=memory),
        relationship_service=RelationshipService(repository=relationship),
        safety_control=safety,
        observability_recorder=recorder,
        observability_scope_key=SYNTHETIC_KEY,
        observability_provider_kind=ProviderKind.FAKE,
        safety_cost_recorder=recorder,
        retry_breaker_recorder=recorder,
    )
    app = create_app(service, observability_recorder=recorder)
    peaks = {name: sum(_file_sizes(path).values()) for name, path in paths.items()}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        for offset in range(0, COUNT, 2):

            async def send(index: int) -> int:
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
                return response.status_code

            statuses = await asyncio.gather(send(offset), send(offset + 1))
            if any(code != 200 for code in statuses):
                raise ValueError("preflight_business_request_failed")
            clock.advance(2.0)
            for name, path in paths.items():
                peaks[name] = max(peaks[name], sum(_file_sizes(path).values()))
            if (offset + 2) % 20 == 0:
                print(json.dumps({"variant": root.name, "completed": offset + 2}), flush=True)
    after = {name: _snapshot(path) for name, path in paths.items()}
    growth = {}
    for name in paths:
        initial, final = before[name], after[name]
        physical = final["main_bytes"] - initial["main_bytes"]
        occupied = occupied_growth(
            initial["page_count"],
            initial["freelist_count"],
            final["page_count"],
            final["freelist_count"],
            final["page_size"],
        )
        growth[name] = {
            "main_growth_bytes": physical,
            "occupied_growth_bytes": occupied,
            "conservative_growth_bytes": max(physical, occupied),
            "sampled_surface_peak_bytes": peaks[name],
        }
    with closing(
        sqlite3.connect(f"{paths['observability'].as_uri()}?mode=ro", uri=True)
    ) as connection:
        completed = connection.execute(
            "SELECT COUNT(*) FROM trace_runs WHERE terminal_outcome='completed'"
        ).fetchone()[0]
        malformed = connection.execute(
            "SELECT COUNT(*) FROM (SELECT trace_id FROM trace_stage_events "
            "GROUP BY trace_id HAVING COUNT(*)<>14)"
        ).fetchone()[0]
        costs = connection.execute(
            "SELECT SUM(actual_cost_micro_usd) FROM safety_cost_events"
        ).fetchone()[0]
    return {
        "candidate_changes": candidate_changes,
        "before": before,
        "after": after,
        "growth": growth,
        "provider_dispatch_count": provider.call_count,
        "completed_count": completed,
        "malformed_stage_trace_count": malformed,
        "actual_cost_micro_usd": costs,
        "queries": {
            name: _query_checks(paths[name], control=name == "control")
            for name in ("control", "observability")
        },
    }


def main() -> int:
    root = ROOT.resolve(strict=True)
    if root != ROOT or any(p.is_symlink() or p.is_junction() for p in (ROOT, *ROOT.parents)):
        raise ValueError("preflight_root_boundary_mismatch")
    output = root / "index-v4-preflight"
    output.mkdir()
    baseline = asyncio.run(_run_variant(output / "baseline-v3", candidate=False))
    candidate = asyncio.run(_run_variant(output / "candidate-indexes", candidate=True))
    failures = list(
        growth_failures(
            control=candidate["growth"]["control"]["conservative_growth_bytes"],
            observability=candidate["growth"]["observability"]["conservative_growth_bytes"],
        )
    )
    for result in (baseline, candidate):
        if (
            result["completed_count"] != COUNT
            or result["provider_dispatch_count"] != COUNT
            or result["malformed_stage_trace_count"] != 0
            or result["actual_cost_micro_usd"] != 0
            or result["after"]["observability"]["rows"]["trace_stage_events"] != COUNT * 14
            or result["after"]["observability"]["rows"]["safety_cost_events"] != COUNT * 3
        ):
            failures.append("workload_metadata_invariant_failed")
    if any(
        baseline["after"][name]["rows"] != candidate["after"][name]["rows"]
        for name in baseline["after"]
    ):
        failures.append("variant_row_counts_changed")
    for name in candidate["queries"]:
        for label, result in candidate["queries"][name].items():
            if result["result"] != baseline["queries"][name][label]["result"]:
                failures.append("query_result_changed")
    report = {
        "schema_version": 1,
        "fixture_version": "f009-index-preflight-v1",
        "transport": "in_process_asgi_http_not_latency_acceptance",
        "product_migration_applied": False,
        "database_user_version": 3,
        "baseline": baseline,
        "candidate": candidate,
        "failure_codes": failures,
    }
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
    print(json.dumps({"growth": candidate["growth"], "failure_codes": failures}), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
