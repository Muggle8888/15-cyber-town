from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path

import pytest
from scripts import f009_step5_benchmark as benchmark
from scripts import f009_step5_steady_profile as diagnostic


def test_memory_case_creates_boundary_directory_without_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(benchmark, "MEMORY_TRACE_COUNT", 2)
    root = tmp_path / "memory-on"
    result = asyncio.run(diagnostic.run_case(root, "memory-on"))
    assert result["run"]["provider_dispatch_count"] == 2
    assert root.is_dir() and list(root.iterdir()) == []


def test_separate_client_completes_real_http_and_reports_only_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(benchmark, "SQLITE_TRACE_COUNT", 2)
    monkeypatch.setattr(benchmark, "_INDEPENDENT_CLIENT", True)
    result = asyncio.run(diagnostic.run_case(tmp_path / "http", "http-separated-on"))
    assert result["run"]["provider_dispatch_count"] == 2
    assert len(result["run"]["samples_ms"]) == 2
    assert result["client_timing"] == "independent_process"
    assert "synthetic noodles" not in json.dumps(result)
    assert any(row["database"] == "observability" for row in result["operations"])
    assert benchmark._INDEPENDENT_CLIENT is True


def test_profile_separates_phases_and_never_retains_sql_or_parameters() -> None:
    profile = diagnostic.SteadyProfile()
    with profile.instrument():
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE secret_payload (value TEXT)")
        profile.phase = "steady"
        connection.execute("INSERT INTO secret_payload VALUES (?)", ("sentinel-secret",))
        connection.commit()
        profile.phase = "teardown"
        connection.close()
    rows = profile.snapshot()
    assert any(row["phase"] == "setup" and row["operation"] == "create" for row in rows)
    assert any(row["phase"] == "steady" and row["operation"] == "commit" for row in rows)
    assert any(row["phase"] == "teardown" and row["operation"] == "close" for row in rows)
    assert "secret_payload" not in json.dumps(rows)
    assert "sentinel-secret" not in json.dumps(rows)


def test_profile_preserves_custom_memory_connection_close_semantics() -> None:
    class MemoryConnection(sqlite3.Connection):
        def close(self) -> None:
            self.rollback()

    with diagnostic.SteadyProfile().instrument():
        connection = sqlite3.connect(":memory:", factory=MemoryConnection)
        connection.close()
        assert connection.execute("SELECT 1").fetchone() == (1,)
        sqlite3.Connection.close(connection)


@pytest.mark.parametrize("name", ["control", "observability", "business"])
def test_database_labels_are_fixed_and_do_not_include_paths(name: str) -> None:
    assert diagnostic.database_label(Path("synthetic-private") / f"{name}.sqlite3") == name
    assert diagnostic.database_label(":memory:") == "control_memory"


def test_unknown_database_label_is_rejected_without_echoing_path() -> None:
    with pytest.raises(ValueError) as error:
        diagnostic.database_label(Path("sentinel-secret.sqlite3"))
    assert "sentinel" not in str(error.value)


def test_child_result_keeps_only_metadata() -> None:
    row = diagnostic.client_result(3, 200, {"status": "completed", "reply": "secret"}, 7.5)
    assert row == {"index": 3, "status_code": 200, "completed": True, "elapsed_ms": 7.5}
    assert "secret" not in json.dumps(row)


@pytest.mark.parametrize(
    "url", ["https://example.com", "http://localhost:80", "http://127.0.0.1.evil:1"]
)
def test_client_rejects_non_loopback_destination(url: str) -> None:
    with pytest.raises(ValueError, match="Synthetic client destination is invalid"):
        diagnostic.validate_client_url(url)
