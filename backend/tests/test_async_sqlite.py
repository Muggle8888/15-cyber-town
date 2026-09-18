"""Synthetic tests for full-operation async storage ownership."""

from __future__ import annotations

import asyncio
import threading

import pytest

from cyber_town.infrastructure.persistence.async_sqlite import AsyncSqliteExecutor


async def wait_started(event: threading.Event) -> None:
    async with asyncio.timeout(3):
        while not event.is_set():
            await asyncio.sleep(0.001)


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_capacity_is_strict(capacity: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        AsyncSqliteExecutor(capacity=capacity)  # type: ignore[arg-type]


def test_one_thread_per_lane_and_event_loop_remains_available() -> None:
    async def scenario() -> None:
        executor = AsyncSqliteExecutor(capacity=2)
        started, release = threading.Event(), threading.Event()
        owner = threading.get_ident()

        def transaction() -> int:
            started.set()
            assert release.wait(3)
            return threading.get_ident()

        task = asyncio.create_task(executor.run("control", transaction))
        try:
            await wait_started(started)
            assert not task.done()
            other = await executor.run("observability", threading.get_ident)
            assert other != owner
            release.set()
            first = await task
            second = await executor.run("control", threading.get_ident)
            assert first == second and first != other
        finally:
            release.set()
            await executor.aclose()

    asyncio.run(scenario())


def test_idle_executor_accepts_sequential_closed_event_loops() -> None:
    executor = AsyncSqliteExecutor()
    assert asyncio.run(executor.run("control", lambda: 1)) == 1
    assert asyncio.run(executor.run("control", lambda: 2)) == 2
    asyncio.run(executor.aclose())


@pytest.mark.parametrize("finish_on_cancel", [False, True])
def test_started_cancellation_never_returns_before_operation_finishes(
    finish_on_cancel: bool,
) -> None:
    async def scenario() -> None:
        executor = AsyncSqliteExecutor(capacity=2)
        started, release, committed = threading.Event(), threading.Event(), threading.Event()

        def transaction() -> int:
            started.set()
            assert release.wait(3)
            committed.set()
            return 7

        task = asyncio.create_task(
            executor.run(
                "business",
                transaction,
                finish_on_cancel=finish_on_cancel,
            )
        )
        try:
            await wait_started(started)
            task.cancel()
            await asyncio.sleep(0)
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done() and not committed.is_set()
            release.set()
            if finish_on_cancel:
                assert await task == 7
                assert task.cancelling() >= 1
            else:
                with pytest.raises(asyncio.CancelledError):
                    await task
            assert committed.is_set()
        finally:
            release.set()
            await executor.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("capacity", [1, 2])
def test_cancel_before_start_never_executes_queued_work(capacity: int) -> None:
    async def scenario() -> None:
        executor = AsyncSqliteExecutor(capacity=capacity)
        started, release = threading.Event(), threading.Event()
        calls: list[int] = []

        def first() -> None:
            started.set()
            assert release.wait(3)

        task = asyncio.create_task(executor.run("business", first))
        try:
            await wait_started(started)
            queued = asyncio.create_task(executor.run("business", lambda: calls.append(1)))
            await asyncio.sleep(0)
            queued.cancel()
            with pytest.raises(asyncio.CancelledError):
                await queued
            release.set()
            await task
            assert calls == []
        finally:
            release.set()
            await executor.aclose()

    asyncio.run(scenario())


def test_failure_keeps_lane_usable_and_shutdown_is_idempotent() -> None:
    async def scenario() -> None:
        executor = AsyncSqliteExecutor()

        def fail() -> None:
            raise ValueError("synthetic fixed failure")

        with pytest.raises(ValueError, match="synthetic fixed failure"):
            await executor.run("control", fail)
        assert await executor.run("control", lambda: 11) == 11
        await executor.aclose()
        await executor.aclose()
        with pytest.raises(RuntimeError, match="unavailable"):
            await executor.run("control", lambda: 12)

    asyncio.run(scenario())


def test_close_drains_started_work_even_when_close_is_cancelled() -> None:
    async def scenario() -> None:
        executor = AsyncSqliteExecutor()
        started, release = threading.Event(), threading.Event()

        def transaction() -> int:
            started.set()
            assert release.wait(3)
            return 9

        task = asyncio.create_task(executor.run("control", transaction))
        await wait_started(started)
        closing = asyncio.create_task(executor.aclose())
        try:
            await asyncio.sleep(0)
            closing.cancel()
            await asyncio.sleep(0)
            assert not closing.done()
            release.set()
            assert await task == 9
            await closing
            with pytest.raises(RuntimeError):
                await executor.run("business", lambda: 1)
        finally:
            release.set()
            await executor.aclose()

    asyncio.run(scenario())
