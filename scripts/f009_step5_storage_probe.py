"""Inspect immutable-schema storage lower bounds using synthetic metadata only."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests")


def _varint_size(value: int) -> int:
    return min(9, max(1, (value.bit_length() + 6) // 7))


def _serial(value: object) -> tuple[int, int]:
    if value is None:
        return 0, 0
    if isinstance(value, int):
        if value in (0, 1):
            return 8 + value, 0
        for serial, length in ((1, 1), (2, 2), (3, 3), (4, 4), (5, 6), (6, 8)):
            if -(1 << (length * 8 - 1)) <= value < (1 << (length * 8 - 1)):
                return serial, length
    if isinstance(value, str):
        length = len(value.encode("utf-8"))
        return 13 + length * 2, length
    raise ValueError("Unexpected synthetic metadata storage type")


def _record_size(values: tuple[object, ...]) -> int:
    serials = tuple(_serial(value) for value in values)
    header_payload = sum(_varint_size(serial) for serial, _ in serials)
    header_size = header_payload + 1
    while header_size != header_payload + _varint_size(header_size):
        header_size = header_payload + _varint_size(header_size)
    return header_size + sum(length for _, length in serials)


def main() -> None:
    root = ROOT.resolve(strict=True)
    output_root = root / "storage-probe"
    output_root.mkdir()
    source = root / "performance/sqlite-observability-1/observability.sqlite3"
    with sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True) as connection:
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL "
            "AND name NOT LIKE 'sqlite_%' ORDER BY type DESC, name"
        ).fetchall()
        dump = "\n".join(connection.iterdump())
        lower_bound: dict[str, int] = {}
        for table in ("trace_runs", "trace_stage_events", "execution_links"):
            table_total = 0
            rows = connection.execute(f'SELECT rowid, * FROM "{table}"').fetchall()
            for row in rows:
                payload = _record_size(tuple(row[1:]))
                table_total += payload + _varint_size(payload) + _varint_size(row[0]) + 2
            lower_bound[table] = table_total
            indexes = connection.execute(f'PRAGMA index_list("{table}")').fetchall()
            for index in indexes:
                index_name = index[1]
                columns = connection.execute(f'PRAGMA index_info("{index_name}")').fetchall()
                names = ", ".join(f'"{item[2]}"' for item in columns)
                indexed_rows = connection.execute(
                    f'SELECT {names}, rowid FROM "{table}"'
                ).fetchall()
                lower_bound[index_name] = sum(
                    _record_size(tuple(row)) + _varint_size(_record_size(tuple(row))) + 2
                    for row in indexed_rows
                )
    layouts: list[dict[str, int]] = []
    for page_size in (512, 1024, 2048, 4096, 8192, 16384):
        empty_path = output_root / f"empty-{page_size}.sqlite3"
        full_path = output_root / f"full-{page_size}.sqlite3"
        with sqlite3.connect(empty_path) as connection:
            connection.execute(f"PRAGMA page_size = {page_size}")
            for (statement,) in schema:
                connection.execute(statement)
        with sqlite3.connect(full_path) as connection:
            connection.execute(f"PRAGMA page_size = {page_size}")
            connection.executescript(dump)
        layouts.append(
            {
                "page_size": page_size,
                "empty_bytes": empty_path.stat().st_size,
                "full_bytes": full_path.stat().st_size,
                "growth_bytes": full_path.stat().st_size - empty_path.stat().st_size,
            }
        )
    result = {
        "schema_version": 1,
        "trace_count": 100,
        "stage_count": 1400,
        "minimum_record_and_cell_bytes": sum(lower_bound.values()),
        "components": lower_bound,
        "page_layouts": layouts,
        "limit_bytes": 512 * 1024,
    }
    (root / "storage-probe.json").write_text(
        json.dumps(result, sort_keys=True, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
