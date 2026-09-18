"""One bounded writer per repository, with explicit leases and shutdown.

Leases never commit. Existing repository methods remain responsible for each
durable transaction. The owner must close the manager when its lifetime ends.
"""

from __future__ import annotations

import os
import sqlite3
import stat
from contextlib import suppress
from pathlib import Path
from threading import Lock
from typing import Any, cast


def validate_sqlite_path(
    path: Path,
    allowed_root: Path,
) -> tuple[os.stat_result | None, tuple[tuple[int, int], ...]]:
    """Inspect a canonical path afresh, with one lstat per component.

    No verdict is cached. Repositories resolve their path at construction;
    rejecting every linked component preserves that canonical identity without
    repeatedly resolving overlapping ancestor chains on every lease.
    """
    if (
        not path.is_absolute()
        or not allowed_root.is_absolute()
        or ".." in path.parts
        or ".." in allowed_root.parts
        or path == allowed_root
        or not path.is_relative_to(allowed_root)
    ):
        raise sqlite3.OperationalError("SQLite writer is unavailable")
    leaf = None
    parents = []
    try:
        for current in (path, *path.parents):
            try:
                info = current.lstat()
            except FileNotFoundError:
                if current == path:
                    continue
                raise
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise sqlite3.OperationalError("SQLite writer is unavailable")
            if current == path:
                if not stat.S_ISREG(info.st_mode):
                    raise sqlite3.OperationalError("SQLite writer is unavailable")
                leaf = info
            else:
                if not stat.S_ISDIR(info.st_mode):
                    raise sqlite3.OperationalError("SQLite writer is unavailable")
                parents.append((info.st_dev, info.st_ino))
    except OSError:
        raise sqlite3.OperationalError("SQLite writer is unavailable") from None
    return leaf, tuple(parents)


class _Lease:
    def __init__(self, owner: BoundedSqliteWriter, connection: sqlite3.Connection) -> None:
        self._owner = owner
        self._connection = connection
        self._released = False

    def __getattr__(self, name: str) -> Any:
        if self._released:
            raise sqlite3.ProgrammingError("SQLite lease is closed")
        return getattr(self._connection, name)

    @property
    def row_factory(self) -> Any:
        if self._released:
            raise sqlite3.ProgrammingError("SQLite lease is closed")
        return self._connection.row_factory

    @row_factory.setter
    def row_factory(self, value: Any) -> None:
        if self._released:
            raise sqlite3.ProgrammingError("SQLite lease is closed")
        self._connection.row_factory = value

    def close(self) -> None:
        if self._released:
            return
        self._released = True
        try:
            if self._connection.in_transaction:
                self._connection.rollback()
            self._connection.row_factory = None
        except sqlite3.Error:
            self._owner.discard()
            raise
        finally:
            self._owner.release()


class BoundedSqliteWriter:
    """Serialize synchronous leases without sharing a transaction across callers."""

    def __init__(
        self,
        path: Path,
        *,
        trusted_schema: bool = True,
        allowed_root: Path | None = None,
    ) -> None:
        self._path = path
        self._allowed_root = allowed_root if allowed_root is not None else path.parent
        self._trusted_schema = trusted_schema
        self._lock = Lock()
        self._connection: sqlite3.Connection | None = None
        self._identity: tuple[int, int] | None = None
        self._pid = os.getpid()
        self._closed = False

    def borrow(self, *, timeout_ms: int) -> sqlite3.Connection:
        if not self._lock.acquire(timeout=timeout_ms / 1000):
            raise sqlite3.OperationalError("SQLite writer is unavailable")
        try:
            if self._closed or self._pid != os.getpid():
                raise sqlite3.OperationalError("SQLite writer is unavailable")
            try:
                info, parent_identity = validate_sqlite_path(self._path, self._allowed_root)
            except sqlite3.Error:
                self._closed = True
                raise
            if self._connection is None:
                initial_identity = None if info is None else (info.st_dev, info.st_ino)
                connection = sqlite3.connect(
                    self._path,
                    timeout=timeout_ms / 1000,
                    isolation_level=None,
                    check_same_thread=False,
                )
                self._connection = connection
                info, after_parents = validate_sqlite_path(self._path, self._allowed_root)
                if (
                    info is None
                    or parent_identity != after_parents
                    or (
                        initial_identity is not None
                        and initial_identity != (info.st_dev, info.st_ino)
                    )
                ):
                    self._closed = True
                    raise sqlite3.OperationalError("SQLite writer is unavailable")
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute("PRAGMA journal_mode = WAL")
                if not self._trusted_schema:
                    connection.execute("PRAGMA trusted_schema = OFF")
                self._identity = (info.st_dev, info.st_ino)
            if info is None:
                self._closed = True
                raise sqlite3.OperationalError("SQLite writer is unavailable")
            if self._identity != (info.st_dev, info.st_ino):
                self._closed = True
                raise sqlite3.OperationalError("SQLite writer is unavailable")
            self._connection.execute(f"PRAGMA busy_timeout = {timeout_ms:d}")
            return cast(sqlite3.Connection, _Lease(self, self._connection))
        except (sqlite3.Error, OSError):
            try:
                self.discard()
            finally:
                self._lock.release()
            raise sqlite3.OperationalError("SQLite writer is unavailable") from None
        except BaseException:
            try:
                self.discard()
            finally:
                self._lock.release()
            raise

    def discard(self) -> None:
        connection, self._connection = self._connection, None
        self._identity = None
        if connection is not None:
            connection.close()

    def release(self) -> None:
        self._lock.release()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self.discard()

    def __del__(self) -> None:
        # Best-effort last resort, not a substitute for the owning caller.close().
        with suppress(sqlite3.Error, AttributeError):
            self.discard()
