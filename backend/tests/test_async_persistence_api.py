"""Synthetic API wiring, validation metadata and lifecycle checks."""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from cyber_town.api.app import create_app
from cyber_town.infrastructure.observability.sqlite_observability import ObservabilityQuery
from test_dialogue_async_persistence import build, command
from test_dialogue_async_persistence import database_root as shared_database_root

database_root = shared_database_root


def test_api_awaits_persistence_and_lifespan_closes_executor(database_root: Path) -> None:
    async def scenario() -> None:
        service, provider, recorder, control = build(database_root)
        app = create_app(service)
        try:
            async with (
                app.router.lifespan_context(app),
                AsyncClient(transport=ASGITransport(app), base_url="http://test") as client,
            ):
                response = await client.post(
                    "/api/v1/dialogue",
                    content=command().model_dump_json(),
                    headers={"Content-Type": "application/json"},
                )
                assert response.status_code == 200
                invalid = await client.post(
                    "/api/v1/dialogue",
                    content="{}",
                    headers={"Content-Type": "application/json"},
                )
                assert invalid.status_code == 422
                traces = recorder.query_traces(ObservabilityQuery(limit=100))
                assert len(traces) == 2
                rejected = next(trace for trace in traces if trace["request_id"] is None)
                assert rejected["player_scope_tag"] is None
                assert rejected["execution_id"] is None
                assert provider.call_count == 1
            assert service._closing
            assert service.storage_executor is not None
            try:
                await service.storage_executor.run("control", lambda: None)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Lifespan did not close the executor")
        finally:
            await service.aclose()
            recorder.close()
            control.close()

    asyncio.run(scenario())
