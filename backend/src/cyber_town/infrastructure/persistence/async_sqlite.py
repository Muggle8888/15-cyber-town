"""Bounded per-database execution of complete synchronous storage operations.

A started operation is never treated as cancelled SQLite work. The default
waits for completion and propagates cancellation. Ownership-sensitive callers
may request its result despite cancellation so they can reconcile committed
state on the event loop; they must check cancellation/ownership before their
next business action. No transaction, path check, or commit is split here.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Literal

type StorageLane = Literal["business", "control", "observability"]


class AsyncSqliteExecutor:
    def __init__(self, *, capacity: int = 16) -> None:
        if type(capacity) is not int or not 1 <= capacity <= 64:
            raise ValueError("Storage queue capacity is invalid")
        self._capacity = capacity
        self._pools: dict[StorageLane, ThreadPoolExecutor] = {}
        self._slots: dict[StorageLane, asyncio.Semaphore] = {}
        self._pending: set[asyncio.Future[object]] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._closing = False
        self._closed = False
        self._close_task: asyncio.Task[None] | None = None

    def _bind_loop(self) -> None:
        loop = asyncio.get_running_loop()
        if self._loop is None:
            self._loop = loop
        elif self._loop is not loop:
            if self._loop.is_closed() and not self._pending and not self._closing:
                # Legacy synchronous callers may use sequential asyncio.run calls.
                # Never allow concurrently live loops to share asyncio state.
                self._slots.clear()
                self._loop = loop
            else:
                raise RuntimeError("Storage executor is unavailable")

    async def run[T](
        self,
        lane: StorageLane,
        operation: Callable[[], T],
        *,
        finish_on_cancel: bool = False,
    ) -> T:
        self._bind_loop()
        if self._closing or lane not in {"business", "control", "observability"}:
            raise RuntimeError("Storage executor is unavailable")
        slots = self._slots.setdefault(lane, asyncio.Semaphore(self._capacity))
        await slots.acquire()
        if self._closing:
            slots.release()
            raise RuntimeError("Storage executor is unavailable")
        try:
            pool = self._pools.get(lane)
            if pool is None:
                pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sqlite-worker")
                self._pools[lane] = pool
            concurrent: Future[T] = pool.submit(operation)
        except BaseException:
            slots.release()
            raise
        future = asyncio.wrap_future(concurrent)
        self._pending.add(future)  # type: ignore[arg-type]
        cancelled = False
        try:
            while True:
                try:
                    result = await asyncio.shield(future)
                    break
                except asyncio.CancelledError:
                    cancelled = True
                    if concurrent.cancel():
                        raise
                    # Running threads cannot be cancelled. Drain them before the
                    # lease/result may be released, including repeated cancels.
                    if future.done():
                        result = future.result()
                        break
            if cancelled and not finish_on_cancel:
                raise asyncio.CancelledError
            return result
        finally:
            self._pending.discard(future)
            slots.release()

    async def aclose(self) -> None:
        self._bind_loop()
        if self._closed:
            return
        if self._close_task is None:
            self._closing = True
            self._close_task = asyncio.create_task(self._drain_and_close())
        while True:
            try:
                await asyncio.shield(self._close_task)
                return
            except asyncio.CancelledError:
                if self._close_task.done():
                    self._close_task.result()
                    return

    async def _drain_and_close(self) -> None:
        if self._pending:
            await asyncio.gather(*tuple(self._pending), return_exceptions=True)
        # All submitted operations have finished. No disk IO remains to join.
        for pool in self._pools.values():
            pool.shutdown(wait=True)
        self._closed = True

    def __repr__(self) -> str:
        return "AsyncSqliteExecutor()"
