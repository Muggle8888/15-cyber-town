"""D0: physical page ownership for fresh synthetic databases, not a product fix."""

from __future__ import annotations

import asyncio
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
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
from scripts.f009_step5_index_preflight import (
    CONTROL_INDEXES,
    COUNT,
    OBSERVABILITY_INDEXES,
    _apply_candidate,
    _file_sizes,
    _snapshot,
    growth_failures,
    occupied_growth,
)

ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,120}\Z")
_CATEGORIES = {"schema", "table", "constraint_index", "nonunique_index"}


@dataclass(frozen=True)
class RootSpec:
    name: str
    table: str
    category: str
    page: int


@dataclass
class _Stats:
    btree_pages: int = 0
    overflow_pages: int = 0
    leaf_cells: int = 0
    interior_cells: int = 0
    payload_bytes: int = 0
    structure_bytes: int = 0
    unused_bytes: int = 0
    unallocated_gap_bytes: int = 0
    freeblock_bytes: int = 0
    fragmented_bytes: int = 0
    overflow_unused_bytes: int = 0


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError("storage_" + code)


def _uint(data: bytes, offset: int, size: int) -> int:
    _require(0 <= offset <= len(data) - size, "truncated_integer")
    return int.from_bytes(data[offset : offset + size], "big")


def _varint(data: bytes, offset: int) -> tuple[int, int]:
    result = 0
    for index in range(9):
        value = _uint(data, offset + index, 1)
        if index == 8:
            return (result << 8) | value, offset + 9
        result = (result << 7) | (value & 127)
        if value < 128:
            return result, offset + index + 1
    raise ValueError("storage_invalid_varint")


def catalog(connection: sqlite3.Connection) -> tuple[RootSpec, ...]:
    """Call only on a new owned synthetic connection, before closing it."""
    entries = connection.execute(
        "SELECT name,tbl_name,type,rootpage FROM sqlite_schema WHERE rootpage>0 ORDER BY name"
    ).fetchall()
    unique: dict[str, bool] = {}
    for name, _, kind, _ in entries:
        _require(bool(_NAME.fullmatch(name)), "invalid_catalog_name")
        if kind == "table":
            unique.update(
                (row[1], bool(row[2])) for row in connection.execute(f'PRAGMA index_list("{name}")')
            )
    roots = [RootSpec("sqlite_schema", "sqlite_schema", "schema", 1)]
    for name, table, kind, page in entries:
        _require(kind in ("table", "index"), "unsupported_catalog_object")
        category = (
            "table"
            if kind == "table"
            else ("constraint_index" if unique.get(name) else "nonunique_index")
        )
        roots.append(RootSpec(name, table, category, page))
    return tuple(roots)


class _Image:
    """Bounded page parser. Never decodes or exposes record payload/key values."""

    def __init__(self, data: bytes) -> None:
        _require(len(data) >= 100 and data[:16] == b"SQLite format 3\x00", "invalid_header")
        size = _uint(data, 16, 2)
        self.size = 65536 if size == 1 else size
        _require(512 <= self.size <= 65536 and self.size & (self.size - 1) == 0, "page_size")
        _require(len(data) <= 128 * 1024 * 1024, "image_too_large")
        _require(len(data) % self.size == 0, "truncated_image")
        _require(data[20] == 0, "reserved_bytes_unsupported")
        _require(_uint(data, 52, 4) == 0, "pointer_map_unsupported")
        self.count = len(data) // self.size
        _require(_uint(data, 28, 4) == self.count, "page_count_mismatch")
        self.data = data
        self.claimed: set[int] = set()

    def take(self, number: int) -> bytes:
        _require(1 <= number <= self.count, "page_out_of_bounds")
        _require(number not in self.claimed, "duplicate_page_owner")
        self.claimed.add(number)
        start = (number - 1) * self.size
        return self.data[start : start + self.size]

    def overflow(self, number: int, remaining: int, stats: _Stats) -> None:
        while remaining:
            page = self.take(number)
            payload = min(remaining, self.size - 4)
            stats.overflow_pages += 1
            stats.payload_bytes += payload
            stats.structure_bytes += 4
            stats.overflow_unused_bytes += self.size - 4 - payload
            stats.unused_bytes += self.size - 4 - payload
            remaining -= payload
            number = _uint(page, 0, 4)
        _require(number == 0, "overflow_tail")

    def cell(self, page: bytes, start: int, kind: int, stats: _Stats) -> tuple[int, int | None]:
        cursor = start
        child = None
        if kind in (2, 5):
            child = _uint(page, cursor, 4)
            cursor += 4
        if kind == 5:
            _, cursor = _varint(page, cursor)
            stats.structure_bytes += cursor - start
            return cursor, child
        payload, cursor = _varint(page, cursor)
        if kind == 13:
            _, cursor = _varint(page, cursor)
        maximum = self.size - 35 if kind == 13 else ((self.size - 12) * 64 // 255) - 23
        minimum = ((self.size - 12) * 32 // 255) - 23
        local = payload
        if payload > maximum:
            local = minimum + (payload - minimum) % (self.size - 4)
            if local > maximum:
                local = minimum
        stats.payload_bytes += local
        cursor += local
        if payload > local:
            overflow_page = _uint(page, cursor, 4)
            cursor += 4
            self.overflow(overflow_page, payload - local, stats)
        end = max(start + 4, cursor)
        _require(end <= self.size, "cell_out_of_bounds")
        stats.structure_bytes += end - start - local
        return end, child

    def btree(self, root: RootSpec) -> dict[str, Any]:
        stats = _Stats()
        stack = [root.page]
        tree_family: int | None = None
        while stack:
            number = stack.pop()
            page = self.take(number)
            offset = 100 if number == 1 else 0
            kind = page[offset]
            _require(kind in (2, 5, 10, 13), "btree_type")
            family = 1 if kind in (5, 13) else 2
            if tree_family is None:
                tree_family = family
            _require(family == tree_family, "mixed_btree_family")
            interior = kind in (2, 5)
            header = 12 if interior else 8
            cells = _uint(page, offset + 3, 2)
            pointer_end = offset + header + cells * 2
            content_start = _uint(page, offset + 5, 2) or 65536
            _require(pointer_end <= content_start <= self.size, "content_boundary")
            stats.btree_pages += 1
            stats.structure_bytes += pointer_end
            if interior:
                stats.interior_cells += cells
                stack.append(_uint(page, offset + 8, 4))
            else:
                stats.leaf_cells += cells
            intervals: list[tuple[int, int]] = []
            for index in range(cells):
                start = _uint(page, offset + header + index * 2, 2)
                _require(content_start <= start < self.size, "cell_pointer")
                end, child = self.cell(page, start, kind, stats)
                intervals.append((start, end))
                if child is not None:
                    stack.append(child)
            freeblock = _uint(page, offset + 1, 2)
            block_bytes = 0
            previous = 0
            while freeblock:
                _require(content_start <= freeblock <= self.size - 4, "freeblock_boundary")
                _require(freeblock > previous, "freeblock_cycle")
                length = _uint(page, freeblock + 2, 2)
                _require(length >= 4 and freeblock + length <= self.size, "freeblock_length")
                intervals.append((freeblock, freeblock + length))
                block_bytes += length
                previous, freeblock = freeblock, _uint(page, freeblock, 2)
            intervals.sort()
            last = content_start
            fragments = 0
            for start, end in intervals:
                _require(start >= last, "overlapping_cells")
                fragments += start - last
                last = end
            fragments += self.size - last
            _require(fragments == page[offset + 7] and fragments <= 60, "fragment_mismatch")
            gap = content_start - pointer_end
            stats.unallocated_gap_bytes += gap
            stats.freeblock_bytes += block_bytes
            stats.fragmented_bytes += fragments
            stats.unused_bytes += gap + block_bytes + fragments
        physical = (stats.btree_pages + stats.overflow_pages) * self.size
        _require(
            physical == stats.payload_bytes + stats.structure_bytes + stats.unused_bytes,
            "object_byte_conservation",
        )
        return {**asdict(root), **asdict(stats), "physical_bytes": physical}

    def freelist(self) -> int:
        expected = _uint(self.data, 36, 4)
        number = _uint(self.data, 32, 4)
        before = len(self.claimed)
        while number:
            page = self.take(number)
            leaves = _uint(page, 4, 4)
            _require(leaves <= self.size // 4 - 2, "freelist_length")
            for index in range(leaves):
                self.take(_uint(page, 8 + index * 4, 4))
            number = _uint(page, 0, 4)
        count = len(self.claimed) - before
        _require(count == expected, "freelist_count_mismatch")
        return count


def analyze_image(data: bytes, roots: tuple[RootSpec, ...]) -> dict[str, Any]:
    """Pure byte/count result. Unknown layouts fail closed, without raw data errors."""
    image = _Image(data)
    names: set[str] = set()
    for root in roots:
        _require(
            bool(_NAME.fullmatch(root.name)) and bool(_NAME.fullmatch(root.table)), "root_name"
        )
        _require(root.category in _CATEGORIES and root.name not in names, "root_metadata")
        names.add(root.name)
    objects = [image.btree(root) for root in roots]
    free = image.freelist()
    _require(len(image.claimed) == image.count, "unaccounted_pages")
    accounted = sum(item["physical_bytes"] for item in objects) + free * image.size
    _require(accounted == len(data), "database_byte_conservation")
    return {
        "page_size": image.size,
        "page_count": image.count,
        "physical_bytes": len(data),
        "accounted_bytes": accounted,
        "freelist_pages": free,
        "freelist_bytes": free * image.size,
        "unaccounted_pages": 0,
        "objects": objects,
    }


def _capture(path: Path) -> dict[str, Any]:
    _require(path.resolve().is_relative_to(ROOT.resolve()), "capture_path_boundary")
    _require(path.name in ("control.sqlite3", "observability.sqlite3"), "capture_database_kind")
    with closing(sqlite3.connect(path)) as connection:
        checkpoint = connection.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
        _require(checkpoint[0] == 0 and checkpoint[1] == checkpoint[2], "checkpoint_busy")
        roots = catalog(connection)
    sizes = _file_sizes(path)
    _require(sizes["wal_bytes"] == 0, "uncheckpointed_wal")
    report = analyze_image(path.read_bytes(), roots)
    report["closed_file_sizes"] = sizes
    return report


async def _variant(root: Path, *, candidate: bool) -> dict[str, Any]:
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
    changes = {}
    if candidate:
        changes = {
            "control": _apply_candidate(paths["control"], CONTROL_INDEXES),
            "observability": _apply_candidate(paths["observability"], OBSERVABILITY_INDEXES),
        }
    before = {name: _snapshot(path) for name, path in paths.items()}
    before_objects = {name: _capture(paths[name]) for name in ("control", "observability")}
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
    peaks = {name: _file_sizes(path) for name, path in paths.items()}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        for offset in range(0, COUNT, 2):

            async def send(index: int) -> None:
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

            await asyncio.gather(send(offset), send(offset + 1))
            clock.advance(2.0)
            for name, path in paths.items():
                for kind, size in _file_sizes(path).items():
                    peaks[name][kind] = max(peaks[name][kind], size)
            if (offset + 2) % 20 == 0:
                print(json.dumps({"variant": root.name, "completed": offset + 2}), flush=True)
    after = {name: _snapshot(path) for name, path in paths.items()}
    with closing(sqlite3.connect(paths["observability"])) as connection:
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
    after_objects = {name: _capture(paths[name]) for name in ("control", "observability")}
    return {
        "before": before,
        "after": after,
        "before_objects": before_objects,
        "after_objects": after_objects,
        "candidate_changes": changes,
        "sampled_after_request_pair_surface_peaks": peaks,
        "completed_count": completed,
        "provider_dispatch_count": provider.call_count,
        "malformed_stage_trace_count": malformed,
        "actual_cost_micro_usd": costs,
    }


def _growth(result: dict[str, Any], name: str) -> dict[str, Any]:
    before, after = result["before"][name], result["after"][name]
    object_before = {row["name"]: row for row in result["before_objects"][name]["objects"]}
    objects = []
    for row in result["after_objects"][name]["objects"]:
        initial = object_before[row["name"]]
        objects.append(
            {
                "name": row["name"],
                "table": row["table"],
                "category": row["category"],
                "physical_growth_bytes": row["physical_bytes"] - initial["physical_bytes"],
                "payload_growth_bytes": row["payload_bytes"] - initial["payload_bytes"],
                "structure_growth_bytes": row["structure_bytes"] - initial["structure_bytes"],
                "unused_growth_bytes": row["unused_bytes"] - initial["unused_bytes"],
            }
        )
    occupied = occupied_growth(
        before["page_count"],
        before["freelist_count"],
        after["page_count"],
        after["freelist_count"],
        after["page_size"],
    )
    _require(
        sum(row["physical_growth_bytes"] for row in objects) == occupied, "growth_conservation"
    )
    return {
        "main_growth_bytes": after["main_bytes"] - before["main_bytes"],
        "occupied_growth_bytes": occupied,
        "objects": objects,
    }


def main() -> int:
    _require(ROOT.resolve(strict=True) == ROOT, "root_boundary")
    _require(
        not any(p.is_symlink() or p.is_junction() for p in (ROOT, *ROOT.parents)), "root_reparse"
    )
    _require(not (ROOT / "summary.json").exists(), "report_exists")
    results = {
        "baseline": asyncio.run(_variant(ROOT / "baseline-v3", candidate=False)),
        "candidate": asyncio.run(_variant(ROOT / "candidate-indexes", candidate=True)),
    }
    for result in results.values():
        rows = result["after"]["observability"]["rows"]
        _require(
            result["completed_count"] == result["provider_dispatch_count"] == COUNT,
            "execution_counts",
        )
        _require(
            result["malformed_stage_trace_count"] == result["actual_cost_micro_usd"] == 0,
            "event_invariants",
        )
        _require(
            rows["trace_stage_events"] == COUNT * 14
            and rows["safety_cost_events"] == COUNT * 3
            and rows["retry_breaker_events"] == COUNT * 2,
            "event_counts",
        )
        for state in result["after"].values():
            _require(
                state["integrity_ok"] and state["foreign_key_errors"] == 0, "database_integrity"
            )
        result["growth"] = {name: _growth(result, name) for name in ("control", "observability")}
    for name in results["baseline"]["after"]:
        _require(
            results["baseline"]["after"][name]["rows"]
            == results["candidate"]["after"][name]["rows"],
            "variant_row_counts",
        )
    growth = results["candidate"]["growth"]
    failures = growth_failures(
        control=growth["control"]["occupied_growth_bytes"],
        observability=growth["observability"]["occupied_growth_bytes"],
    )
    report = {
        "schema_version": 1,
        "diagnostic_version": "f009-storage-breakdown-v2",
        "transport": "in_process_asgi_not_latency_acceptance",
        "product_migration_applied": False,
        "database_user_version": 3,
        "known_growth_failures": failures,
        "physical_page_conservation": True,
        **results,
    }
    with (ROOT / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
    print(json.dumps({"diagnostic_complete": True, "known_growth_failures": failures}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
