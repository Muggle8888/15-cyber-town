"""Connection reuse must not batch commits or weaken isolation/durability."""

from __future__ import annotations

import sqlite3
import stat
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from scripts.f009_step5_benchmark import _stages, _trace

from cyber_town.application.observability import RecordStatus
from cyber_town.infrastructure.observability.sqlite_observability import (
    ObservabilityStorageError,
    SqliteObservabilityRepository,
)
from cyber_town.infrastructure.persistence import sqlite_connection as writer_module
from cyber_town.infrastructure.persistence.sqlite_connection import BoundedSqliteWriter


def test_one_writer_connection_keeps_every_stage_commit_durable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = sqlite3.connect
    opened: list[sqlite3.Connection] = []
    commits: list[str] = []

    def connect(*args: object, **kwargs: object) -> sqlite3.Connection:
        connection = original(*args, **kwargs)  # type: ignore[call-overload]
        connection.set_trace_callback(
            lambda sql: commits.append("commit") if sql == "COMMIT" else None
        )
        opened.append(connection)
        return cast(sqlite3.Connection, connection)

    monkeypatch.setattr(sqlite3, "connect", connect)
    repo = SqliteObservabilityRepository(
        database_path=tmp_path / "observability.sqlite3", allowed_root=tmp_path
    )
    repo.initialize()
    complete = _trace()
    pending = replace(
        complete, record_status=RecordStatus.OPEN, terminal_outcome=None, finished_at_utc=None
    )
    repo.start_trace(pending)
    for stage in _stages(complete)[:13]:
        repo.record_progress(pending, stage)
        with closing(original(repo.database_path)) as reader:
            assert reader.execute("SELECT COUNT(*) FROM trace_stage_events").fetchone() == (
                stage.sequence,
            )
    repo.finish_trace(complete, _stages(complete))
    assert len(opened) == 1
    assert len(commits) == 16  # schema + durable open + 13 progress + terminal
    repo.close()
    with pytest.raises(sqlite3.ProgrammingError):
        opened[0].execute("SELECT 1")


def test_writer_serializes_threads_and_keeps_transactions_separate(tmp_path: Path) -> None:
    writer = BoundedSqliteWriter(tmp_path / "threads.sqlite3")
    with closing(writer.borrow(timeout_ms=1000)) as connection:
        connection.execute("CREATE TABLE counters(value INTEGER NOT NULL)")
        connection.execute("INSERT INTO counters VALUES(0)")

    def increment(_: int) -> None:
        with closing(writer.borrow(timeout_ms=1000)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("UPDATE counters SET value=value+1")
            connection.commit()

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(increment, range(20)))
    with closing(writer.borrow(timeout_ms=1000)) as connection:
        assert connection.execute("SELECT value FROM counters").fetchone() == (20,)
    writer.close()
    writer.close()
    with pytest.raises(sqlite3.OperationalError, match="unavailable"):
        writer.borrow(timeout_ms=1)


def test_lease_timeout_does_not_steal_active_transaction(tmp_path: Path) -> None:
    writer = BoundedSqliteWriter(tmp_path / "timeout.sqlite3")
    lease = writer.borrow(timeout_ms=1000)
    lease.execute("BEGIN IMMEDIATE")
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(writer.borrow, timeout_ms=1)
        with pytest.raises(sqlite3.OperationalError, match="unavailable"):
            future.result(timeout=5)
    assert lease.in_transaction
    lease.close()
    with closing(writer.borrow(timeout_ms=1000)) as connection:
        assert not connection.in_transaction
    writer.close()


def test_lease_rolls_back_uncommitted_work_and_resets_row_factory(tmp_path: Path) -> None:
    repo = SqliteObservabilityRepository(
        database_path=tmp_path / "observability.sqlite3", allowed_root=tmp_path
    )
    repo.initialize()
    with closing(repo._connect()) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("UPDATE schema_migrations SET checksum=?", ("0" * 64,))
    with closing(repo._connect()) as connection:
        assert connection.row_factory is None
        assert connection.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE checksum=?", ("0" * 64,)
        ).fetchone() == (0,)
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert connection.execute("PRAGMA synchronous").fetchone() == (2,)
    repo.close()


def test_cached_writer_rechecks_reparse_boundary_before_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = SqliteObservabilityRepository(
        database_path=tmp_path / "observability.sqlite3", allowed_root=tmp_path
    )
    repo.initialize()
    original = Path.lstat
    monkeypatch.setattr(
        Path,
        "lstat",
        lambda path: (
            SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
            if path == tmp_path
            else original(path)
        ),
    )
    with pytest.raises(ObservabilityStorageError):
        repo.start_trace(
            replace(
                _trace(),
                record_status=RecordStatus.OPEN,
                terminal_outcome=None,
                finished_at_utc=None,
            )
        )
    repo.close()


def test_path_validation_reads_each_ancestor_once_without_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "not-created.sqlite3"
    calls: list[Path] = []
    original = Path.lstat

    def lstat(path: Path) -> object:
        calls.append(path)
        return original(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(Path, "resolve", lambda *a, **k: pytest.fail("redundant resolve"))
    leaf, parents = writer_module.validate_sqlite_path(database, tmp_path)
    assert leaf is None
    assert len(parents) == len(database.parents)
    assert calls == [database, *database.parents]


@pytest.mark.parametrize("kind", ["symlink", "junction", "other_reparse", "denied", "missing"])
@pytest.mark.parametrize("location", ["leaf", "root", "above_root"])
def test_path_validation_rejects_all_ancestor_redirection_and_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, location: str
) -> None:
    database = tmp_path / "not-created.sqlite3"
    target = {"leaf": database, "root": tmp_path, "above_root": tmp_path.parent}[location]
    original = Path.lstat

    def lstat(path: Path) -> object:
        if path != target:
            return original(path)
        if kind == "denied":
            raise PermissionError("synthetic secret path")
        if kind == "missing":
            raise FileNotFoundError("synthetic secret path")
        return SimpleNamespace(
            st_mode=stat.S_IFLNK if kind == "symlink" else stat.S_IFDIR,
            st_file_attributes=0x400 if kind != "symlink" else 0,
        )

    monkeypatch.setattr(Path, "lstat", lstat)
    if location == "leaf" and kind == "missing":
        assert writer_module.validate_sqlite_path(database, tmp_path)[0] is None
    else:
        with pytest.raises(sqlite3.OperationalError) as captured:
            writer_module.validate_sqlite_path(database, tmp_path)
        assert "secret" not in str(captured.value)


@pytest.mark.parametrize("mutation", ["missing", "replaced", "reparse"])
def test_writer_rechecks_identity_after_wait_without_touching_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    path = tmp_path / "identity.sqlite3"
    writer = BoundedSqliteWriter(path)
    lease = writer.borrow(timeout_ms=1000)
    lease.execute("CREATE TABLE sample(value INTEGER)")
    waiting = threading.Event()
    original = Path.lstat

    def lstat(current: Path) -> object:
        if current != path:
            return original(current)
        if mutation == "missing":
            raise FileNotFoundError("synthetic secret")
        info = original(current)
        return SimpleNamespace(
            st_mode=info.st_mode,
            st_file_attributes=0x400 if mutation == "reparse" else 0,
            st_dev=info.st_dev,
            st_ino=info.st_ino + 1,
        )

    def acquire() -> None:
        waiting.set()
        with closing(writer.borrow(timeout_ms=1000)):
            pytest.fail("changed identity accepted")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(acquire)
        assert waiting.wait(5)
        monkeypatch.setattr(Path, "lstat", lstat)
        lease.close()
        with pytest.raises(sqlite3.OperationalError, match="unavailable"):
            future.result(timeout=5)
    monkeypatch.setattr(Path, "lstat", original)
    with pytest.raises(sqlite3.OperationalError, match="unavailable"):
        writer.borrow(timeout_ms=1000)
    writer.close()


def test_profile_counts_only_written_commits() -> None:
    from scripts.f009_step5_steady_profile import SteadyProfile

    profile = SteadyProfile()
    with profile.instrument(), closing(sqlite3.connect(":memory:", isolation_level=None)) as c:
        c.execute("CREATE TABLE sample(value INTEGER)")
        profile.phase = "steady"
        c.execute("BEGIN IMMEDIATE")
        c.commit()
        c.execute("BEGIN IMMEDIATE")
        c.execute("INSERT INTO sample VALUES(1)")
        c.commit()
    counts = {
        row["operation"]: row["count"] for row in profile.snapshot() if row["phase"] == "steady"
    }
    assert counts["commit"] == 2 and counts["write_commit"] == 1
    assert "wal_full_write_commit" not in counts


def test_unprofiled_benchmark_uses_independent_tcp_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import asyncio

    from scripts import f009_step5_benchmark as benchmark

    monkeypatch.setattr(benchmark, "SQLITE_TRACE_COUNT", 2)
    monkeypatch.setattr(benchmark, "_INDEPENDENT_CLIENT", True)
    result = asyncio.run(benchmark._loopback_run(tmp_path, control_on=True))
    assert result.provider_dispatch_count == 2 and len(result.samples_ms) == 2
    details = benchmark.RUN_DETAILS[tmp_path.name]
    assert isinstance(details, dict) and details["independent_client"] is True
