"""Owned synthetic diagnostics, not a replacement for the frozen performance gate."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import ExitStack, asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import asdict
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Any
from unittest.mock import patch
from urllib.parse import urlsplit

import httpx

from cyber_town.application.observability import (
    InMemoryObservabilityRecorder,
    NoOpObservabilityRecorder,
)
from cyber_town.infrastructure.control.sqlite_control import SqliteSafetyControlRepository
from cyber_town.infrastructure.observability.sqlite_observability import (
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.persistence import sqlite_connection as writer_module
from cyber_town.infrastructure.persistence.sqlite_connection import BoundedSqliteWriter
from scripts import f009_step5_benchmark as benchmark

APPROVED_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v3-diagnostic")
GATE_ROOT = Path(r"E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate")
REMOTE_LATENCY: ContextVar[float | None] = ContextVar("synthetic_remote_latency", default=None)
SQL_KINDS = frozenset(
    {"select", "insert", "update", "delete", "pragma", "begin", "create", "alter", "drop"}
)


def database_label(database: object) -> str:
    value = str(database)
    if value == ":memory:":
        return "control_memory"
    name = Path(urlsplit(value).path if value.startswith("file:") else value).name
    if name in {"control.sqlite3", "observability.sqlite3", "business.sqlite3"}:
        return name.removesuffix(".sqlite3")
    raise ValueError("Synthetic database label is invalid")


def _quantile(samples: list[float], fraction: float) -> float:
    import math

    return sorted(samples)[max(0, math.ceil(len(samples) * fraction) - 1)]


class SteadyProfile:
    """Fixed labels only. Method durations are inclusive; never sum nested rows."""

    def __init__(self) -> None:
        self.phase = "setup"
        self.segment = "all"
        self.values: defaultdict[tuple[str, str, str, str], list[float]] = defaultdict(list)

    def record(self, database: str, operation: str, started: float) -> None:
        self.values[self.phase, self.segment, database, operation].append(
            (time.perf_counter() - started) * 1000
        )

    def snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "phase": phase,
                "segment": segment,
                "database": database,
                "operation": operation,
                "count": len(values),
                "total_ms": sum(values),
                "p50_ms": _quantile(values, 0.5),
                "p95_ms": _quantile(values, 0.95),
                "max_ms": max(values),
            }
            for (phase, segment, database, operation), values in sorted(self.values.items())
        ]

    @contextmanager
    def instrument(self) -> Iterator[None]:
        profile = self
        original_connect = sqlite3.connect

        def connect(database: Any, *args: Any, **kwargs: Any) -> sqlite3.Connection:
            label = database_label(database)
            factory = kwargs.pop("factory", sqlite3.Connection)

            class MeasuredConnection(factory):  # type: ignore[misc,valid-type]
                def execute(self, sql: str, parameters: Any = (), /) -> Any:
                    tokens = sql.split(maxsplit=1)
                    kind = tokens[0].lower() if tokens else "other"
                    kind = kind if kind in SQL_KINDS else "other"
                    if kind == "begin":
                        self.begin_changes = self.total_changes
                        self.durability = (
                            super().execute("PRAGMA journal_mode").fetchone()[0],
                            super().execute("PRAGMA synchronous").fetchone()[0],
                        )
                    started = time.perf_counter()
                    try:
                        return super().execute(sql, parameters)
                    finally:
                        profile.record(label, kind, started)

                def commit(self) -> None:
                    written = self.total_changes > getattr(
                        self, "begin_changes", self.total_changes
                    )
                    started = time.perf_counter()
                    try:
                        super().commit()
                    finally:
                        profile.record(label, "commit", started)
                        if written:
                            profile.record(label, "write_commit", started)
                            if getattr(self, "durability", None) == ("wal", 2):
                                profile.record(label, "wal_full_write_commit", started)

                def close(self) -> None:
                    started = time.perf_counter()
                    try:
                        super().close()
                    finally:
                        profile.record(label, "close", started)

            started = time.perf_counter()
            try:
                return original_connect(database, *args, factory=MeasuredConnection, **kwargs)
            finally:
                profile.record(label, "connect", started)

        def measured(function: Callable[..., Any], label: str, name: str) -> Callable[..., Any]:
            @wraps(function)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                started = time.perf_counter()
                try:
                    return function(*args, **kwargs)
                finally:
                    profile.record(label, "method." + name, started)

            return wrapper

        class MeasuredLock:
            def __init__(self) -> None:
                self.lock = Lock()

            def acquire(self, *args: Any, **kwargs: Any) -> bool:
                started = time.perf_counter()
                try:
                    return self.lock.acquire(*args, **kwargs)
                finally:
                    profile.record("writer", "lock_wait", started)

            def release(self) -> None:
                self.lock.release()

            def __enter__(self) -> MeasuredLock:
                self.acquire()
                return self

            def __exit__(self, *args: Any) -> None:
                self.release()

        with ExitStack() as stack:
            stack.enter_context(patch.object(sqlite3, "connect", connect))
            stack.enter_context(patch.object(writer_module, "Lock", MeasuredLock))
            stack.enter_context(
                patch.object(
                    writer_module,
                    "validate_sqlite_path",
                    measured(writer_module.validate_sqlite_path, "writer", "validate_sqlite_path"),
                )
            )
            for name in ("resolve", "stat", "lstat", "is_symlink", "is_junction"):
                stack.enter_context(
                    patch.object(Path, name, measured(getattr(Path, name), "path", name))
                )
            for cls, label, names in (
                (
                    SqliteSafetyControlRepository,
                    "control",
                    (
                        "reserve_budget",
                        "_window_attempt_count",
                        "_window_cost",
                        "_window_totals",
                        "_all_window_totals",
                        "_connect",
                    ),
                ),
                (
                    SqliteObservabilityRepository,
                    "observability",
                    ("start_trace", "record_progress", "finish_trace", "_validate_current_path"),
                ),
                (BoundedSqliteWriter, "writer", ("borrow",)),
            ):
                for name in names:
                    if not hasattr(cls, name):
                        continue
                    descriptor = inspect.getattr_static(cls, name)
                    function = (
                        descriptor.__func__
                        if isinstance(descriptor, (classmethod, staticmethod))
                        else descriptor
                    )
                    replacement: Any = measured(function, label, name)
                    if isinstance(descriptor, classmethod):
                        replacement = classmethod(replacement)
                    elif isinstance(descriptor, staticmethod):
                        replacement = staticmethod(replacement)
                    stack.enter_context(patch.object(cls, name, replacement))
            yield


def validate_client_url(url: str) -> None:
    parts = urlsplit(url)
    if (
        parts.scheme != "http"
        or parts.hostname != "127.0.0.1"
        or parts.username is not None
        or parts.password is not None
        or parts.port is None
        or not 1 <= parts.port <= 65535
        or parts.path not in ("", "/")
        or parts.query
        or parts.fragment
    ):
        raise ValueError("Synthetic client destination is invalid")


def client_result(index: int, status: int, body: object, elapsed: float) -> dict[str, Any]:
    return {
        "index": index,
        "status_code": status,
        "completed": isinstance(body, dict) and body.get("status") == "completed",
        "elapsed_ms": elapsed,
    }


async def _client_worker(url: str) -> None:
    validate_client_url(url)
    async with httpx.AsyncClient(base_url=url, trust_env=False, timeout=30) as client:
        print(json.dumps({"ready": True, "pid": os.getpid()}), flush=True)

        async def send(command: dict[str, Any]) -> None:
            started = time.perf_counter()
            try:
                response = await client.post(
                    "/api/v1/dialogue",
                    content=command["content"],
                    headers={"Content-Type": "application/json"},
                )
                body = response.json()
                result = client_result(
                    command["index"],
                    response.status_code,
                    body,
                    (time.perf_counter() - started) * 1000,
                )
            except Exception:
                result = client_result(command["index"], 0, None, 0)
            print(json.dumps(result), flush=True)

        tasks: list[asyncio.Task[None]] = []
        while line := await asyncio.to_thread(sys.stdin.readline):
            tasks.append(asyncio.create_task(send(json.loads(line))))
        await asyncio.gather(*tasks)


class RemoteResponse:
    def __init__(self, result: dict[str, Any]) -> None:
        self.status_code = result["status_code"]
        self.completed = result["completed"]

    def json(self) -> dict[str, str]:
        return {"status": "completed" if self.completed else "error"}


class RemoteClient:
    def __init__(self, process: asyncio.subprocess.Process) -> None:
        self.process = process
        self.pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self.reader = asyncio.create_task(self._read())

    async def _read(self) -> None:
        assert self.process.stdout is not None
        try:
            while line := await self.process.stdout.readline():
                result = json.loads(line)
                future = self.pending[result["index"]]
                if not future.done():
                    future.set_result(result)
        finally:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(RuntimeError("Synthetic client ended"))

    async def post(self, path: str, *, content: str, headers: dict[str, str]) -> RemoteResponse:
        if path != "/api/v1/dialogue" or headers != {"Content-Type": "application/json"}:
            raise ValueError("Synthetic client request is invalid")
        index = len(self.pending)
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self.pending[index] = future
        assert self.process.stdin is not None
        # Synthetic request is transient pipe transport only, never a persisted report.
        self.process.stdin.write((json.dumps({"index": index, "content": content}) + "\n").encode())
        await self.process.stdin.drain()
        result = await asyncio.wait_for(future, 40)
        REMOTE_LATENCY.set(float(result["elapsed_ms"]))
        return RemoteResponse(result)

    async def close(self) -> None:
        assert self.process.stdin is not None
        self.process.stdin.close()
        try:
            await asyncio.wait_for(self.process.wait(), 10)
        except TimeoutError:
            self.process.terminate()
            await self.process.wait()
        await self.reader
        if self.process.returncode:
            raise RuntimeError("Synthetic client failed")


@asynccontextmanager
async def _remote_client(url: str) -> AsyncIterator[RemoteClient]:
    validate_client_url(url)
    safe_env = {
        name: value
        for name, value in os.environ.items()
        if name.upper()
        in {
            "SYSTEMROOT",
            "WINDIR",
            "PATH",
            "TEMP",
            "TMP",
            "PYTHONPATH",
            "PYTHONDONTWRITEBYTECODE",
            "CYBER_TOWN_LOAD_DOTENV",
            "LLM_PROVIDER",
        }
    }
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-B",
        "-m",
        "scripts.f009_step5_steady_profile",
        "--client-url",
        url,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        env=safe_env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
    )
    try:
        assert process.stdout is not None
        ready = json.loads(await asyncio.wait_for(process.stdout.readline(), 20))
        if ready.get("ready") is not True or ready["pid"] == os.getpid():
            raise RuntimeError("Synthetic client startup failed")
        client = RemoteClient(process)
        try:
            yield client
        finally:
            await client.close()
    finally:
        if process.returncode is None:
            process.terminate()
            await process.wait()


async def run_case(root: Path, label: str, *, profiled: bool = True) -> dict[str, Any]:
    root.mkdir()
    profile = SteadyProfile()
    original_timed = benchmark._timed_call
    original_client = benchmark._http_client
    memory = label.startswith("memory-")
    separated = "separated" in label
    index = 0
    endpoint: str | None = None

    async def timed(action: Callable[..., Any]) -> float:
        nonlocal index
        index += 1
        profile.phase = "steady"
        profile.segment = (
            ("first_100" if index <= 100 else "last_100" if index > 900 else "middle_800")
            if memory
            else f"pair_{(index - 1) // 2:03d}"
        )
        latency_marker = REMOTE_LATENCY.set(None)
        try:
            elapsed = await original_timed(action)
            remote = REMOTE_LATENCY.get()
            return remote if separated and remote is not None else elapsed
        finally:
            REMOTE_LATENCY.reset(latency_marker)
            if memory:
                profile.phase = "teardown"

    @asynccontextmanager
    async def http_client(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        nonlocal endpoint
        async with original_client(*args, **kwargs) as client:
            endpoint = str(client.base_url)
            print(
                json.dumps({"case": label, "endpoint": endpoint, "status": "started"}), flush=True
            )
            if separated:
                async with _remote_client(endpoint) as remote:
                    profile.phase = "steady"
                    try:
                        yield remote
                    finally:
                        profile.phase = "teardown"
            else:
                profile.phase = "steady"
                try:
                    yield client
                finally:
                    profile.phase = "teardown"

    with ExitStack() as stack:
        if profiled:
            stack.enter_context(profile.instrument())
        stack.enter_context(patch.object(benchmark, "_INDEPENDENT_CLIENT", False))
        stack.enter_context(patch.object(benchmark, "_timed_call", timed))
        stack.enter_context(patch.object(benchmark, "_http_client", http_client))
        if memory:
            result = await benchmark._memory_control_run(
                root,
                InMemoryObservabilityRecorder
                if label.endswith("on")
                else NoOpObservabilityRecorder,
            )
        else:
            result = await benchmark._loopback_run(root, control_on=label.endswith("on"))
    return {
        "case": label,
        "profiled": profiled,
        "run": asdict(result),
        "p95_ms": _quantile(list(result.samples_ms), 0.95),
        "p99_ms": _quantile(list(result.samples_ms), 0.99),
        "operations": profile.snapshot(),
        "endpoint": endpoint,
        "client_timing": "independent_process" if separated else "colocated",
        "method_rows_are_inclusive": True,
        "is_final_gate": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-url")
    parser.add_argument("--label", choices=("baseline", "baseline-02", "after-query"))
    parser.add_argument("--feasibility", action="store_true")
    parser.add_argument(
        "--feasibility-label",
        choices=("feasibility-01", "after-optimized-01"),
        default="feasibility-01",
    )
    args = parser.parse_args()
    if args.client_url:
        asyncio.run(_client_worker(args.client_url))
        return
    if args.feasibility:
        root = GATE_ROOT.resolve(strict=True)
        for path in (GATE_ROOT, *GATE_ROOT.parents):
            if path.is_symlink() or path.is_junction():
                raise ValueError("Synthetic diagnostic root is invalid")
        output = root / args.feasibility_label
        output.mkdir()
        result = asyncio.run(run_case(output / "http-separated-on", "http-separated-on"))
        with (output / "summary.json").open("x", encoding="utf-8") as stream:
            json.dump(result, stream, sort_keys=True, indent=2)
        print(json.dumps({"p95_ms": result["p95_ms"], "p99_ms": result["p99_ms"]}))
        return
    if args.label is None:
        raise ValueError("Synthetic diagnostic label is required")
    root = APPROVED_ROOT.resolve(strict=True)
    for path in (APPROVED_ROOT, *APPROVED_ROOT.parents):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Synthetic diagnostic root is invalid")
    output = root / args.label
    output.mkdir()
    cases = []
    for label in (
        "memory-off",
        "memory-on",
        "http-colocated-off",
        "http-colocated-on",
        "http-separated-off",
        "http-separated-on",
    ):
        result = asyncio.run(run_case(output / label, label))
        cases.append(result)
        print(
            json.dumps({"case": label, "p95_ms": result["p95_ms"], "status": "finished"}),
            flush=True,
        )
    summary = {"schema_version": 1, "cases": cases, "final_performance_gate": False}
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, sort_keys=True, indent=2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Synthetic diagnostic failed; no payload details emitted") from None
