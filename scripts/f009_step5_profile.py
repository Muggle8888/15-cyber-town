"""Metadata-only profiling of the synthetic Step 5 workload."""

from __future__ import annotations

import argparse
import asyncio
import cProfile
import json
import pstats
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts import f009_step5_benchmark as benchmark

ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v2")
COUNTS: Counter[str] = Counter()
SECONDS: defaultdict[str, float] = defaultdict(float)
type ProfileStats = dict[tuple[str, int, str], tuple[int, int, float, float, object]]


class ProfileConnection(sqlite3.Connection):
    def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor:
        kind = sql.split(maxsplit=1)[0].lower()
        started = time.perf_counter()
        try:
            return super().execute(sql, parameters)
        finally:
            COUNTS[kind] += 1
            SECONDS[kind] += time.perf_counter() - started

    def commit(self) -> None:
        started = time.perf_counter()
        try:
            super().commit()
        finally:
            COUNTS["commit"] += 1
            SECONDS["commit"] += time.perf_counter() - started

    def close(self) -> None:
        started = time.perf_counter()
        try:
            super().close()
        finally:
            COUNTS["close"] += 1
            SECONDS["close"] += time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=("profile-after",))
    args = parser.parse_args()
    root = ROOT.resolve(strict=True)
    if root.is_symlink() or root.is_junction():
        raise ValueError("Profiling root is invalid")
    output_root = root / args.label
    output_root.mkdir()
    original_connect = sqlite3.connect

    def counted_connect(*args: Any, **kwargs: Any) -> ProfileConnection:
        kwargs["factory"] = ProfileConnection
        started = time.perf_counter()
        connection = original_connect(*args, **kwargs)
        assert isinstance(connection, ProfileConnection)
        COUNTS["connect"] += 1
        SECONDS["connect"] += time.perf_counter() - started
        return connection

    benchmark.SQLITE_TRACE_COUNT = 4
    sqlite3.connect = counted_connect  # type: ignore[assignment]
    profile = cProfile.Profile()
    profile.enable()
    try:
        measured = asyncio.run(benchmark._loopback_run(output_root, control_on=True))
    finally:
        profile.disable()
        sqlite3.connect = original_connect
    statistics = pstats.Stats(profile)
    raw_stats: ProfileStats = statistics.stats  # type: ignore[attr-defined]
    top = sorted(raw_stats.items(), key=lambda item: item[1][3], reverse=True)[:30]
    functions = [
        {
            "file": Path(key[0]).name,
            "function": key[2],
            "calls": values[1],
            "total_seconds": values[2],
            "cumulative_seconds": values[3],
        }
        for key, values in top
    ]
    baseline_path = output_root / "observability.sqlite3"
    from contextlib import closing

    with closing(original_connect(f"{baseline_path.as_uri()}?mode=ro", uri=True)) as connection:
        page_usage = {
            "page_size": connection.execute("PRAGMA page_size").fetchone()[0],
            "page_count": connection.execute("PRAGMA page_count").fetchone()[0],
            "freelist_count": connection.execute("PRAGMA freelist_count").fetchone()[0],
            "trace_count": connection.execute("SELECT COUNT(*) FROM trace_runs").fetchone()[0],
            "stage_count": connection.execute("SELECT COUNT(*) FROM trace_stage_events").fetchone()[
                0
            ],
        }
    result = {
        "schema_version": 1,
        "execution_count": 4,
        "provider_dispatch_count": measured.provider_dispatch_count,
        "operation_count": dict(COUNTS),
        "operation_seconds": dict(SECONDS),
        "functions": functions,
        "observability_pages": page_usage,
    }
    (root / f"{args.label}.json").write_text(
        json.dumps(result, sort_keys=True, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
