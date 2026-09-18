"""Candidate C experiment only: existing repository transactions, compact SQL values.

The SQL adapter is deliberately confined to this diagnostic. No product migration
is registered, and no latency claim may be made from this instrumented ASGI run.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from cyber_town.application.observability import TraceMetadata, TraceStageMetadata
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.observability.storage_codec import (
    ENCODED_FIELDS,
    ENUM_FIELDS,
    TAG_FIELDS,
    UUID_FIELDS,
    WORD_CODES,
    decode_value,
    encode_value,
)
from scripts import f009_step5_layout_preflight as layout
from scripts.f009_step5_benchmark import SYNTHETIC_KEY, _completion
from scripts.f009_step5_index_preflight import growth_failures
from scripts.f009_step5_storage_breakdown import _growth

ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\compact-preflight-v1")
_ORIGINAL_REBUILD = layout.rebuild_layout
_TABLES = layout.LEAF_TABLES["observability"]
_CONTROL_SCOPE_COLUMNS = frozenset(
    {"player_scope_tag", "player_npc_scope_tag", "conversation_scope_tag"}
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError("compact_" + code)


def _is_compact(connection: sqlite3.Connection, table: str) -> bool:
    return any(
        (table, row[1]) in ENCODED_FIELDS and row[2] != "TEXT"
        for row in connection.execute(f'PRAGMA table_xinfo("{table}")')
    )


def _decode_control_scope(value: object) -> str:
    if type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None:
        return value
    if type(value) is bytes and len(value) == 32:
        return value.hex()
    raise ValueError("compact_invalid_control_scope")


def decoded_digest(connection: sqlite3.Connection, *, exclude_migration_time: bool = False) -> str:
    tables = layout._tables(connection)
    result = []
    for table in tables:
        columns = [row[1] for row in connection.execute(f'PRAGMA table_xinfo("{table}")')]
        if exclude_migration_time and table == "schema_migrations":
            columns = [
                c for c in columns if c not in ("applied_at", "applied_at_ns", "applied_at_ms")
            ]
        names = ",".join(f'"{c}"' for c in columns)
        compact = table in _TABLES and _is_compact(connection, table)
        rows = [
            tuple(
                _decode_control_scope(value)
                if table == "provider_permits" and column in _CONTROL_SCOPE_COLUMNS
                else decode_value(table, column, value)
                if compact and (table, column) in ENCODED_FIELDS
                else value
                for column, value in zip(columns, row, strict=True)
            )
            for row in connection.execute(f'SELECT {names} FROM "{table}"')
        ]
        result.append((table, sorted(rows, key=lambda row: json.dumps(row))))
    return hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()


def compact_ddl(table: str, original: str, temporary: str) -> str:
    require(table in _TABLES and original.endswith(") STRICT"), "ddl_boundary")
    body = original[original.index("(") :]
    for owner, column in sorted(ENCODED_FIELDS):
        if owner != table:
            continue
        target = "INTEGER" if (owner, column) in ENUM_FIELDS else "BLOB"
        body, count = re.subn(rf"\b{column} TEXT\b", f"{column} {target}", body)
        require(count == 1, "column_boundary")
        if (owner, column) in UUID_FIELDS | TAG_FIELDS:
            old, new = (36, 16) if (owner, column) in UUID_FIELDS else (64, 32)
            body, count = re.subn(
                rf"length\({column}\) = {old}\b", f"length({column}) = {new}", body
            )
            require(count == 1, "length_boundary")
    allowed = {
        word for (owner, _), words in ENUM_FIELDS.items() if owner == table for word in words
    }
    # Codes are globally stable, so shared words in CHECK/default clauses have
    # the same representation. No arbitrary SQL literals are transformed.
    for word in sorted(allowed):
        body = body.replace("'" + word + "'", str(WORD_CODES[word]))
    return f'CREATE TABLE "{temporary}" ' + body + ", WITHOUT ROWID"


def compact_rebuild(
    connection: sqlite3.Connection, kind: str, *, fail_after: int | None = None
) -> dict[str, Any]:
    if kind == "control":
        with patch.object(layout, "ROOT", ROOT), patch.object(layout, "row_digest", decoded_digest):
            return _ORIGINAL_REBUILD(connection, kind, fail_after=fail_after)
    require(kind == "observability", "kind")
    filename = connection.execute("PRAGMA database_list").fetchone()[2]
    if filename:
        path = Path(filename)
        require(path.resolve().is_relative_to(ROOT.resolve()), "database_boundary")
        require(
            not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)), "reparse"
        )
    require(not connection.in_transaction, "transaction_already_active")
    require(connection.execute("PRAGMA foreign_keys").fetchone() == (1,), "fk_required")
    require(connection.execute("PRAGMA page_size").fetchone() == (4096,), "page_size")
    require(connection.execute("PRAGMA user_version").fetchone() == (3,), "schema_version")
    info = {row[1]: row for row in connection.execute("PRAGMA table_list")}
    require(all(info[t][4:] == (0, 1) for t in _TABLES), "initial_layout")
    require(
        not any(
            row[2] in _TABLES
            for t in layout._tables(connection)
            for row in connection.execute(f'PRAGMA foreign_key_list("{t}")')
        ),
        "incoming_fk",
    )
    digest = decoded_digest(connection)
    indexes = dict(
        connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL"
        )
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for index, table in layout.REMOVED_INDEXES[kind].items():
            entries = [
                row
                for row in connection.execute(f'PRAGMA index_list("{table}")')
                if row[1] == index
            ]
            require(len(entries) == 1 and entries[0][2:4] == (0, "c"), "index_boundary")
            connection.execute(f'DROP INDEX "{index}"')
        for position, table in enumerate(_TABLES, 1):
            original = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE name=?", (table,)
            ).fetchone()[0]
            temporary = "compact_new_" + table
            connection.execute(compact_ddl(table, original, temporary))
            columns = [row[1] for row in connection.execute(f'PRAGMA table_xinfo("{table}")')]
            names = ",".join(f'"{c}"' for c in columns)
            rows = connection.execute(f'SELECT {names} FROM "{table}"').fetchall()
            # Fully validate/encode before dropping the original; any exception
            # rolls back every table and index in this database transaction.
            converted = [
                tuple(
                    encode_value(table, c, v) if (table, c) in ENCODED_FIELDS else v
                    for c, v in zip(columns, row, strict=True)
                )
                for row in rows
            ]
            placeholders = ",".join("?" for _ in columns)
            connection.executemany(
                f'INSERT INTO "{temporary}" ({names}) VALUES ({placeholders})', converted
            )
            retained = [
                row[0]
                for row in connection.execute(
                    "SELECT sql FROM sqlite_schema WHERE type='index' AND tbl_name=? "
                    "AND sql IS NOT NULL ORDER BY name",
                    (table,),
                )
            ]
            connection.execute(f'DROP TABLE "{table}"')
            connection.execute(f'ALTER TABLE "{temporary}" RENAME TO "{table}"')
            for sql in retained:
                connection.execute(sql)
            if fail_after == position:
                raise ValueError("compact_injected_failure")
        require(decoded_digest(connection) == digest, "decoded_rows_changed")
        require(
            dict(
                connection.execute(
                    "SELECT name, sql FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL"
                )
            )
            == {k: v for k, v in indexes.items() if k not in layout.REMOVED_INDEXES[kind]},
            "indexes_changed",
        )
        require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "foreign_keys")
        require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "integrity")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return {
        "tables": list(_TABLES),
        "removed_indexes": sorted(layout.REMOVED_INDEXES[kind]),
        "decoded_rows_unchanged": True,
        "experimental_codec": True,
    }


class _ExperimentalConnection:
    """Translate only the four explicit leaf-table SQL shapes used by the v3 repo.

    This temporary adapter is not proposed as the production implementation. It
    leaves transaction boundaries and stage ordering entirely in the original repo.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.raw = connection
        connection.create_function("compact_encode", 3, encode_value, deterministic=True)
        connection.create_function("compact_decode", 3, decode_value, deterministic=True)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.raw, name)

    def execute(self, sql: str, parameters: Any = ()) -> sqlite3.Cursor:
        for table in _TABLES:
            match = re.match(
                rf"(INSERT(?: OR IGNORE)? INTO {table}\s*\()([^)]*)\)\s*VALUES\s*\(([^)]*)\)(.*)",
                sql,
                re.S,
            )
            if match:
                columns = [c.strip() for c in match[2].split(",")]
                values = [v.strip() for v in match[3].split(",")]
                require(len(columns) == len(values), "adapter_columns")
                encoded = [
                    f"compact_encode('{table}','{c}',{v})" if (table, c) in ENCODED_FIELDS else v
                    for c, v in zip(columns, values, strict=True)
                ]
                sql = match[1] + match[2] + ") VALUES (" + ",".join(encoded) + ")" + match[4]
                break
            selected = re.match(rf'SELECT (.*?) FROM "?{table}"?\b(.*)', sql, re.S)
            if selected:
                columns = [c.strip() for c in selected[1].split(",")]
                expressions = [
                    f"compact_decode('{table}','{c}',{c}) AS {c}"
                    if (table, c) in ENCODED_FIELDS
                    else c
                    for c in columns
                ]
                tail = selected[2]
                for owner, column in ENCODED_FIELDS:
                    if owner == table:
                        tail = re.sub(
                            rf"\b{column}\s*=\s*\?",
                            f"{column} = compact_encode('{table}','{column}',?)",
                            tail,
                        )
                sql = "SELECT " + ",".join(expressions) + " FROM " + table + tail
                break
            if sql.startswith("UPDATE " + table + " SET retention_status"):
                sql = sql.replace(
                    "SET retention_status = 'expired'",
                    f"SET retention_status = {WORD_CODES['expired']}",
                )
                sql = sql.replace(
                    "WHERE retention_status = 'active'",
                    f"WHERE retention_status = {WORD_CODES['active']}",
                )
                break
        return self.raw.execute(sql, parameters)


class CompactRecorder(layout._CheckedRecorder):
    def _connect(self) -> sqlite3.Connection:
        connection = super()._connect()
        if _is_compact(connection, "trace_stage_events"):
            return cast(sqlite3.Connection, _ExperimentalConnection(connection))
        return connection

    def record_progress(self, trace: TraceMetadata, stage: TraceStageMetadata) -> None:
        SqliteObservabilityRepository.record_progress(self, trace, stage)
        with closing(self._connect()) as connection:
            require(
                connection.execute(
                    "SELECT stage, outcome FROM trace_stage_events WHERE trace_id=? AND sequence=?",
                    (str(trace.trace_id), stage.sequence),
                ).fetchone()
                == (stage.stage.value, stage.outcome.value),
                "stage_not_durable",
            )
        self.progress_checks += 1


def main() -> int:
    require(ROOT.resolve(strict=True) == ROOT, "root_boundary")
    require(
        not any(p.is_symlink() or p.is_junction() for p in (ROOT, *ROOT.parents)), "root_reparse"
    )
    paired = ROOT / "paired-fixed"
    require(not paired.exists(), "output_exists")
    paired.mkdir()
    with patch.multiple(
        layout,
        ROOT=ROOT,
        _CheckedRecorder=CompactRecorder,
        SqliteObservabilityRepository=CompactRecorder,
        rebuild_layout=compact_rebuild,
        row_digest=decoded_digest,
    ):
        restart = layout._restart_check(paired / "restart")
        results = {
            "baseline": asyncio.run(layout._variant(paired / "baseline-v3", candidate=False)),
            "candidate": asyncio.run(layout._variant(paired / "candidate-c", candidate=True)),
        }
    for result in results.values():
        require(
            result["completed_count"]
            == result["provider_dispatch_count"]
            == result["durable_open_checks"]
            == 100,
            "execution_count",
        )
        require(
            result["malformed_stage_trace_count"] == result["actual_cost_micro_usd"] == 0, "events"
        )
        require(result["durable_progress_checks"] == 1300, "incremental_stages")
        rows = result["after"]["observability"]["rows"]
        require(
            rows["trace_stage_events"] == 1400
            and rows["safety_cost_events"] == 300
            and rows["retry_breaker_events"] == 200,
            "event_counts",
        )
        for snapshot in result["after"].values():
            require(
                snapshot["integrity_ok"]
                and snapshot["foreign_key_errors"] == 0
                and snapshot["page_size"] == 4096,
                "integrity",
            )
        result["growth"] = {kind: _growth(result, kind) for kind in layout.LEAF_TABLES}
        result["business_growth_bytes"] = (
            result["after"]["business"]["main_bytes"] - result["before"]["business"]["main_bytes"]
        )
    require(
        results["baseline"]["synthetic_row_digests_excluding_migration_time"]
        == results["candidate"]["synthetic_row_digests_excluding_migration_time"],
        "paired_rows_changed",
    )
    failures = growth_failures(
        control=results["candidate"]["growth"]["control"]["occupied_growth_bytes"],
        observability=results["candidate"]["growth"]["observability"]["occupied_growth_bytes"],
    )
    report = {
        "diagnostic_version": "f009-compact-preflight-v1",
        "schema_version": 1,
        "product_migration_applied": False,
        "transport": "in_process_asgi_not_latency_acceptance",
        "workload": "100_unique_fixed_serial_three_npc_full_three_db",
        "restart": restart,
        "growth_failures": failures,
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
    ]
    require(not any(s in encoded for s in sentinels), "forbidden_content")
    with (paired / "summary.json").open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    print(
        json.dumps(
            {
                "prevalidation_passed": not failures,
                "growth_failures": failures,
                "paired_data_equal": True,
                "forbidden_content_hits": 0,
                "growth": {
                    k: v["occupied_growth_bytes"] for k, v in results["candidate"]["growth"].items()
                },
            }
        ),
        flush=True,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
