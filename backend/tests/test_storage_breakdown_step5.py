"""Resource-free tests for D0 page ownership; no product layout changes."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any

import pytest
from scripts.f009_step5_storage_breakdown import RootSpec, analyze_image, catalog


def _database(page_size: int = 512) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(f"PRAGMA page_size={page_size}")
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute(
        "CREATE TABLE sample (id TEXT PRIMARY KEY, number INTEGER NOT NULL, value BLOB) STRICT"
    )
    connection.execute("CREATE INDEX sample_partial ON sample(number) WHERE number%2=0")
    connection.executemany(
        "INSERT INTO sample VALUES (?, ?, ?)",
        ((f"synthetic-{i:05}", i, b"synthetic-sentinel-" * 8) for i in range(500)),
    )
    connection.commit()
    return connection


def _object(report: dict[str, Any], name: str) -> dict[str, Any]:
    return next(item for item in report["objects"] if item["name"] == name)


@pytest.mark.parametrize("page_size", [512, 4096, 65536])
def test_physical_pages_and_bytes_conserve_without_record_content(page_size: int) -> None:
    with closing(_database(page_size)) as connection:
        roots = catalog(connection)
        report = analyze_image(connection.serialize(), roots)
        assert report["page_count"] == connection.execute("PRAGMA page_count").fetchone()[0]
        assert report["page_size"] == page_size
        assert report["unaccounted_pages"] == 0
        assert report["physical_bytes"] == report["accounted_bytes"]
        for item in report["objects"]:
            assert item["physical_bytes"] == (
                item["payload_bytes"] + item["structure_bytes"] + item["unused_bytes"]
            )
        assert _object(report, "sample")["leaf_cells"] == 500
        partial = _object(report, "sample_partial")
        assert partial["leaf_cells"] + partial["interior_cells"] == 250
        assert partial["category"] == "nonunique_index"
        assert _object(report, "sqlite_autoindex_sample_1")["category"] == "constraint_index"
        assert "synthetic-sentinel" not in json.dumps(report)
        assert "synthetic-00000" not in json.dumps(report)


def test_overflow_and_freelist_are_separate_from_live_payload() -> None:
    with closing(_database()) as connection:
        connection.execute("UPDATE sample SET value=? WHERE number=0", (b"x" * 12000,))
        connection.commit()
        first = analyze_image(connection.serialize(), catalog(connection))
        assert _object(first, "sample")["overflow_pages"] > 0
        connection.execute("DELETE FROM sample WHERE number>0")
        connection.commit()
        final = analyze_image(connection.serialize(), catalog(connection))
        assert final["freelist_pages"] > 0
        assert final["freelist_pages"] == connection.execute("PRAGMA freelist_count").fetchone()[0]
        assert final["physical_bytes"] == final["accounted_bytes"]
        assert _object(final, "sample")["leaf_cells"] == 1


def test_index_overflow_and_interior_keys_are_accounted() -> None:
    with closing(_database()) as connection:
        connection.execute("CREATE INDEX sample_value ON sample(value)")
        connection.execute("UPDATE sample SET value=? WHERE number=0", (b"z" * 10000,))
        connection.commit()
        report = analyze_image(connection.serialize(), catalog(connection))
        item = _object(report, "sample_value")
        assert item["overflow_pages"] > 0
        assert item["interior_cells"] > 0
        assert item["leaf_cells"] + item["interior_cells"] == 500
        assert report["physical_bytes"] == report["accounted_bytes"]


@pytest.mark.parametrize("mutation", ["header", "truncated", "reserved", "pointer_map"])
def test_unsupported_or_corrupt_image_fails_closed(mutation: str) -> None:
    with closing(_database()) as connection:
        data = bytearray(connection.serialize())
        roots = catalog(connection)
    if mutation == "header":
        data[0] = 0
    elif mutation == "truncated":
        data = data[:-1]
    elif mutation == "reserved":
        data[20] = 1
    else:
        data[52:56] = (1).to_bytes(4, "big")
    with pytest.raises(ValueError, match=r"^storage_") as caught:
        analyze_image(bytes(data), roots)
    assert "synthetic" not in str(caught.value)


def test_duplicate_and_missing_roots_cannot_produce_apparent_conservation() -> None:
    with closing(_database()) as connection:
        data, roots = connection.serialize(), catalog(connection)
    with pytest.raises(ValueError, match=r"^storage_"):
        analyze_image(data, (*roots, roots[-1]))
    with pytest.raises(ValueError, match=r"^storage_"):
        analyze_image(data, roots[:-1])


def test_root_name_and_invalid_page_do_not_echo_untrusted_values() -> None:
    with closing(_database()) as connection:
        data, roots = connection.serialize(), catalog(connection)
    for root in (
        RootSpec("raw secret sentinel!", "sample", "table", 2),
        RootSpec("sample", "sample", "table", 999999),
    ):
        with pytest.raises(ValueError, match=r"^storage_") as caught:
            analyze_image(data, (root, *roots[1:]))
        assert "raw secret sentinel" not in str(caught.value)


def test_overlapping_cell_pointer_is_rejected() -> None:
    with closing(_database(65536)) as connection:
        data, roots = bytearray(connection.serialize()), catalog(connection)
    sample = next(root for root in roots if root.name == "sample_partial")
    offset = (sample.page - 1) * 65536
    assert data[offset] == 10
    data[offset + 10 : offset + 12] = data[offset + 8 : offset + 10]
    with pytest.raises(ValueError, match=r"^storage_"):
        analyze_image(bytes(data), roots)
