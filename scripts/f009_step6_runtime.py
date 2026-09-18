"""Small, side-effect-free runtime contract for F-009 S1 tool readiness."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

QA_ROOT = Path(r"E:\Agent\cyber-town-f009-step6-qa")
RECOVERY_ROOT = QA_ROOT / "recovery-20260905-01"
S1_ROOTS = tuple(
    RECOVERY_ROOT / name
    for name in (
        "s1-qa-stabilization-i0",
        "s1-qa-stabilization-r1",
        "s1-qa-stabilization-r2",
        "s1-qa-stabilization-r3",
        "s1-qa-stabilization-r4",
        "s1-qa-stabilization-r5",
        "s1-qa-stabilization-r6",
        "s1-qa-stabilization-r7",
    )
)
S1_BATCH_LIMIT = 64 * 1024**2
S1_REPORT_LIMIT = 1024**2
S1_PORTS = (8000, 8001)
CONTROLLED_ENV_KEYS = frozenset(
    {
        "TEMP",
        "TMP",
        "PYTHONDONTWRITEBYTECODE",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "PYTEST_ADDOPTS",
        "CYBER_TOWN_DISABLE_DOTENV",
        "LLM_PROVIDER",
        "UV_OFFLINE",
        "UV_NO_CACHE",
        "UV_CACHE_DIR",
        "UV_PYTHON",
        "UV_PYTHON_DOWNLOADS",
        "RUFF_NO_CACHE",
        "RUFF_CACHE_DIR",
        "MYPY_CACHE_DIR",
        "F009_MACHINE_LEDGER",
        "F009_NATIVE_ROOT",
        "F009_NATIVE_PID",
    }
)


def authorize_readiness_root(
    raw: str | Path,
    validator: Callable[[Path], Path],
    *,
    require_fresh: bool = True,
) -> Path:
    """Accept only one of the exact S1 roots after the existing canonical check."""
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise RuntimeError("step6_s1_root_not_exact")
    canonical = validator(candidate)
    if canonical not in S1_ROOTS or canonical.parent != RECOVERY_ROOT:
        raise RuntimeError("step6_s1_root_not_approved")
    index = S1_ROOTS.index(canonical)
    if any(not predecessor.is_dir() for predecessor in S1_ROOTS[:index]):
        raise RuntimeError("step6_s1_root_order_invalid")
    if require_fresh and canonical.exists():
        raise RuntimeError("step6_s1_root_not_fresh")
    return canonical


def environment_fingerprint(environment: Mapping[str, str] | None = None) -> str:
    """Compare an environment without placing names or values in a QA report."""
    source = os.environ if environment is None else environment
    controlled = {key: source.get(key) for key in CONTROLLED_ENV_KEYS}
    encoded = json.dumps(sorted(controlled.items()), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def temp_fingerprint() -> str:
    """Compare tempfile state without exposing the path in the readiness report."""
    value = json.dumps(
        {"tempdir": tempfile.tempdir, "resolved": tempfile.gettempdir()},
        ensure_ascii=True,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def port_state(ports: Iterable[int] = S1_PORTS) -> dict[int, bool]:
    """Return local TCP listening reachability; no HTTP or product request is made."""
    state: dict[int, bool] = {}
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(0.05)
            state[port] = client.connect_ex(("127.0.0.1", port)) == 0
    return state


def file_fingerprints(paths: Iterable[Path]) -> dict[str, str]:
    """Hash required read-only evidence; a missing source is a hard failure."""
    result: dict[str, str] = {}
    for path in sorted(set(paths), key=lambda item: str(item).casefold()):
        if not path.is_file():
            raise RuntimeError("step6_s1_old_evidence_missing")
        result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def restoration_flags(before: Mapping[str, object], after: Mapping[str, object]) -> dict[str, bool]:
    """Convert opaque before/after snapshots into the four public restoration booleans."""
    return {
        "port_state_restored": before.get("ports") == after.get("ports"),
        "environment_restored": before.get("environment") == after.get("environment"),
        "temp_path_restored": before.get("temp") == after.get("temp"),
        "old_evidence_unchanged": before.get("evidence") == after.get("evidence"),
    }


def _selector_completed(selector: str, nodeids: Sequence[str]) -> bool:
    return any(nodeid == selector or nodeid.startswith(selector + "[") for nodeid in nodeids)


def safe_failure_code(error: BaseException | None) -> str | None:
    """Keep only a stable Step 6 code or the exception class, never raw exception text."""
    if error is None:
        return None
    message = str(error)
    if message.startswith("step6_") and all(
        character.isalnum() or character == "_" for character in message
    ):
        return message
    return type(error).__name__


def build_readiness_report(
    *,
    root: Path,
    selected: Sequence[str],
    pytest_summary: Mapping[str, Any] | None,
    command_state: Mapping[str, object],
    restoration: Mapping[str, bool],
    outer_failure: str | None = None,
) -> dict[str, Any]:
    """Build the single bounded S1 result with deterministic failure precedence."""
    rows = list(pytest_summary.get("results", [])) if pytest_summary is not None else []
    nodeids = [str(row.get("nodeid", "")) for row in rows if isinstance(row, Mapping)]
    failed = [
        str(row.get("nodeid", ""))
        for row in rows
        if isinstance(row, Mapping) and row.get("outcome") == "failed"
    ]
    skipped = [
        str(row.get("nodeid", ""))
        for row in rows
        if isinstance(row, Mapping) and row.get("outcome") == "skipped"
    ]
    not_run = [selector for selector in selected if not _selector_completed(selector, nodeids)]
    failures = [*failed]
    if outer_failure is not None:
        failures.append(outer_failure)
    pytest_exit_code = pytest_summary.get("exit_code") if pytest_summary is not None else None
    raw_not_retained = (
        pytest_summary is not None and pytest_summary.get("raw_output_retained") is False
    )
    no_diagnostic_rejections = pytest_summary is not None and not (
        pytest_summary.get("identity_diagnostic_rejections")
        or pytest_summary.get("termination_diagnostic_rejections")
    )
    restored = all(restoration.get(key) is True for key in restoration)
    owned_processes_closed = (
        command_state.get("state") == "completed"
        and command_state.get("exit_code") == 0
        and not command_state.get("cleanup_error")
        and not command_state.get("pipe_close_errors")
    )
    report_redacted = raw_not_retained and no_diagnostic_rejections
    passed = (
        pytest_exit_code == 0
        and not failed
        and not skipped
        and not not_run
        and outer_failure is None
        and owned_processes_closed
        and restored
        and report_redacted
    )
    return {
        "schema_version": 1,
        "state": "passed" if passed else "failed",
        "root": str(root),
        "quality_started": False,
        "performance_started": False,
        "product_service_started": False,
        "selected": list(selected),
        "completed": nodeids,
        "failed": failed,
        "skipped": skipped,
        "xfailed": [],
        "not_run": not_run,
        "first_failure": failures[0] if failures else None,
        "secondary_failures": failures[1:],
        "pytest_exit_code": pytest_exit_code,
        "owned_processes_closed": owned_processes_closed,
        "port_state_restored": restoration.get("port_state_restored") is True,
        "environment_restored": restoration.get("environment_restored") is True,
        "temp_path_restored": restoration.get("temp_path_restored") is True,
        "old_evidence_unchanged": restoration.get("old_evidence_unchanged") is True,
        "report_redacted": report_redacted,
    }


def require_readiness_passed(report: Mapping[str, Any]) -> None:
    """Freeze only a fully successful report; partial or ambiguous states fail closed."""
    required_true = {
        "owned_processes_closed",
        "port_state_restored",
        "environment_restored",
        "temp_path_restored",
        "old_evidence_unchanged",
        "report_redacted",
    }
    if not (
        report.get("state") == "passed"
        and report.get("pytest_exit_code") == 0
        and all(report.get(key) is True for key in required_true)
        and all(
            report.get(key) is False
            for key in (
                "quality_started",
                "performance_started",
                "product_service_started",
            )
        )
        and all(report.get(key) == [] for key in ("failed", "skipped", "xfailed", "not_run"))
        and report.get("first_failure") is None
        and report.get("secondary_failures") == []
    ):
        raise RuntimeError("step6_s1_tool_readiness_failed")


def encode_readiness_report(report: Mapping[str, Any]) -> str:
    """Serialize once with a fixed 1 MiB ceiling."""
    payload = json.dumps(dict(report), ensure_ascii=True, indent=2, sort_keys=True)
    if len(payload.encode("utf-8")) > S1_REPORT_LIMIT:
        raise RuntimeError("step6_s1_report_limit")
    return payload
