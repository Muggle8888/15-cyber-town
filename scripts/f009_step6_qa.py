"""Isolate the authorized F-009 Step 6 QA without changing product behavior."""

from __future__ import annotations

import argparse
import importlib
import io
import json
import os
import re
import stat
import sys
import tempfile
import threading
import time
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager, redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from types import FrameType
from typing import IO, Any, NoReturn, Protocol, TextIO
from urllib.parse import parse_qs, unquote, urlsplit


def load_s1_runtime() -> Any:
    """Support both package import and direct script execution without two implementations."""
    try:
        return importlib.import_module("scripts.f009_step6_runtime")
    except ModuleNotFoundError as error:
        if error.name != "scripts":
            raise
        return importlib.import_module("f009_step6_runtime")


s1_runtime: Any = load_s1_runtime()

QA_ROOT = Path(r"E:\Agent\cyber-town-f009-step6-qa")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORMAL_PROJECT_ROOT = Path(r"E:\Agent\comprehensive-cases\15-cyber-town")
EVIDENCE = FORMAL_PROJECT_ROOT / "docs/project-management/evidence.md"
CURRENT_TASK = FORMAL_PROJECT_ROOT / "docs/project-management/current-task.md"
ARCHIVED_EVIDENCE = Path(
    r"E:\Agent\comprehensive-cases\15-cyber-town\docs\archive"
    r"\F-009-过程记录-20260905\evidence.md"
)
RECOVERY_ROOT = QA_ROOT / "recovery-20260905-01"
PREVIOUS_TOOL_CONTRACT_ROOT = RECOVERY_ROOT / "qa-tool-contract-01"
PREVIOUS_TOOL_CONTRACT_ROOT_02 = RECOVERY_ROOT / "qa-tool-contract-02"
PREVIOUS_TOOL_CONTRACT_ROOT_03 = RECOVERY_ROOT / "qa-tool-contract-03"
PREVIOUS_NATIVE_QUALITY_ROOT = RECOVERY_ROOT / "native-quality-03"
TOOL_CONTRACT_ROOT = RECOVERY_ROOT / "qa-tool-contract-16"
CURRENT_TOOL_READINESS_ROOT = s1_runtime.S1_ROOTS[7]
NATIVE_QUALITY_ROOT = RECOVERY_ROOT / "native-quality-10"
PREVIOUS_STARTUP_ROOT = RECOVERY_ROOT / "connectivity-startup-diagnostic-01"
PREVIOUS_STARTUP_ROOT_02 = RECOVERY_ROOT / "connectivity-startup-diagnostic-02"
PREVIOUS_STARTUP_ROOT_03 = RECOVERY_ROOT / "connectivity-startup-diagnostic-03"
PREVIOUS_STARTUP_ROOT_04 = RECOVERY_ROOT / "connectivity-startup-diagnostic-04"
STARTUP_ROOT = RECOVERY_ROOT / "connectivity-startup-diagnostic-05"
COMPOSITION_ROOT = RECOVERY_ROOT / "composition-import-validation-01"
COMPOSITION_STARTUP_ROOT = RECOVERY_ROOT / "composition-startup-readiness-01"
TERMINATION_ROOT = RECOVERY_ROOT / "launcher-termination-report-validation-01"
PREVIOUS_REPORT_READINESS_ROOT = RECOVERY_ROOT / "startup-report-integration-readiness-01"
REPORT_READINESS_ROOT = RECOVERY_ROOT / "startup-report-integration-readiness-02"
CLEANUP_CONTROL_ROOT = RECOVERY_ROOT / "startup-cleanup-control-validation-01"
CLEANUP_SEMANTICS_ROOT = RECOVERY_ROOT / "startup-cleanup-report-semantics-validation-01"
LAUNCHER_EXIT_ROOT = RECOVERY_ROOT / "launcher-exit-contract-validation-02"
OBSERVER_FAILURE_ROOT = RECOVERY_ROOT / "observer-failure-evidence-validation-01"
OBSERVER_CAPACITY_ROOT = RECOVERY_ROOT / "observer-capacity-validation-01"
MIGRATION_DIGEST_ROOT = RECOVERY_ROOT / "migration-digest-validation-01"
NATIVE_BUFFER_BYTES = 262144
STARTUP_READINESS_ROOTS = tuple(
    RECOVERY_ROOT / f"startup-phase-readiness-{index:02d}" for index in range(1, 4)
)
IDENTITY_ROOT = RECOVERY_ROOT / "startup-process-observation-validation-01"
EXIT_VALIDATION_ROOTS = (
    RECOVERY_ROOT / "startup-process-exit-validation-01",
    RECOVERY_ROOT / "startup-process-exit-validation-02",
)
IDENTITY_VALIDATION_ROOTS = frozenset(
    {
        IDENTITY_ROOT,
        COMPOSITION_ROOT,
        COMPOSITION_STARTUP_ROOT,
        TERMINATION_ROOT,
        REPORT_READINESS_ROOT,
        CLEANUP_CONTROL_ROOT,
        CLEANUP_SEMANTICS_ROOT,
        LAUNCHER_EXIT_ROOT,
        OBSERVER_FAILURE_ROOT,
        OBSERVER_CAPACITY_ROOT,
        MIGRATION_DIGEST_ROOT,
        *EXIT_VALIDATION_ROOTS,
        *STARTUP_READINESS_ROOTS,
        *s1_runtime.S1_ROOTS,
    }
)
BATCH_LIMITS = {
    TOOL_CONTRACT_ROOT: 256 * 1024 * 1024,
    NATIVE_QUALITY_ROOT: 1024**3,
    STARTUP_ROOT: 128 * 1024 * 1024,
    IDENTITY_ROOT: 32 * 1024 * 1024,
    COMPOSITION_ROOT: 32 * 1024 * 1024,
    COMPOSITION_STARTUP_ROOT: 32 * 1024 * 1024,
    TERMINATION_ROOT: 32 * 1024 * 1024,
    REPORT_READINESS_ROOT: 32 * 1024 * 1024,
    CLEANUP_CONTROL_ROOT: 32 * 1024 * 1024,
    CLEANUP_SEMANTICS_ROOT: 32 * 1024 * 1024,
    LAUNCHER_EXIT_ROOT: 32 * 1024 * 1024,
    OBSERVER_FAILURE_ROOT: 32 * 1024 * 1024,
    OBSERVER_CAPACITY_ROOT: 32 * 1024 * 1024,
    MIGRATION_DIGEST_ROOT: 32 * 1024 * 1024,
    **dict.fromkeys(EXIT_VALIDATION_ROOTS, 32 * 1024 * 1024),
    **dict.fromkeys(STARTUP_READINESS_ROOTS, 32 * 1024 * 1024),
    **dict.fromkeys(s1_runtime.S1_ROOTS, s1_runtime.S1_BATCH_LIMIT),
}
STARTUP_FILE_LIMITS = {
    "machine-ledger.md": 8 * 1024 * 1024,
    "invocation.json": 64 * 1024,
    "timeline.jsonl": 1024 * 1024,
    "stderr-redacted.txt": 1024 * 1024,
    "stdout-redacted.txt": 256 * 1024,
    "native-summary.json": 8 * 1024 * 1024,
    "synthetic-summary.json": 1024 * 1024,
    "pytest-summary.json": 1024 * 1024,
    "preconditions-summary.json": 64 * 1024,
    "phase-events.jsonl": 64 * 1024,
    "position-events.jsonl": 16 * 1024,
    "evidence-status.json": 64 * 1024,
}
EVIDENCE_SNAPSHOT = RECOVERY_ROOT / "ledger-separation-01/evidence-before-split.md"
HISTORICAL_LEDGERS = (
    ARCHIVED_EVIDENCE,
    ARCHIVED_EVIDENCE.with_name("recovery-20260905-01-evidence-ledger.md"),
    EVIDENCE_SNAPSHOT,
    PREVIOUS_TOOL_CONTRACT_ROOT / "machine-ledger.md",
    PREVIOUS_TOOL_CONTRACT_ROOT_02 / "machine-ledger.md",
    PREVIOUS_TOOL_CONTRACT_ROOT_03 / "machine-ledger.md",
    PREVIOUS_NATIVE_QUALITY_ROOT / "machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-04/machine-ledger.md",
    RECOVERY_ROOT / "native-quality-04/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-05/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-06/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-07/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-08/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-09/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-10/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-11/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-12/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-13/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-14/machine-ledger.md",
    RECOVERY_ROOT / "qa-tool-contract-15/machine-ledger.md",
    RECOVERY_ROOT / "native-quality-06/machine-ledger.md",
    RECOVERY_ROOT / "native-quality-05/machine-ledger.md",
    RECOVERY_ROOT / "native-quality-07/machine-ledger.md",
    RECOVERY_ROOT / "native-quality-08/machine-ledger.md",
    RECOVERY_ROOT / "native-quality-09/machine-ledger.md",
    RECOVERY_ROOT / "s1-qa-stabilization-i0/machine-ledger.md",
    RECOVERY_ROOT / "s1-qa-stabilization-r1/machine-ledger.md",
    RECOVERY_ROOT / "s1-qa-stabilization-r2/machine-ledger.md",
    RECOVERY_ROOT / "s1-qa-stabilization-r3/machine-ledger.md",
    RECOVERY_ROOT / "s1-qa-stabilization-r4/machine-ledger.md",
    RECOVERY_ROOT / "s1-qa-stabilization-r5/machine-ledger.md",
    RECOVERY_ROOT / "s1-qa-stabilization-r6/machine-ledger.md",
    RECOVERY_ROOT / "startup-report-integration-readiness-02/machine-ledger.md",
    RECOVERY_ROOT / "connectivity-startup-diagnostic-05/machine-ledger.md",
    PREVIOUS_STARTUP_ROOT / "machine-ledger.md",
    PREVIOUS_STARTUP_ROOT_02 / "machine-ledger.md",
    IDENTITY_ROOT / "machine-ledger.md",
    *(root / "machine-ledger.md" for root in EXIT_VALIDATION_ROOTS),
    PREVIOUS_STARTUP_ROOT_03 / "machine-ledger.md",
    RECOVERY_ROOT / "connectivity-startup-readiness-01/machine-ledger.md",
    RECOVERY_ROOT / "startup-phase-readiness-01/machine-ledger.md",
    RECOVERY_ROOT / "startup-phase-readiness-02/machine-ledger.md",
    PREVIOUS_STARTUP_ROOT_04 / "machine-ledger.md",
    COMPOSITION_ROOT / "machine-ledger.md",
    COMPOSITION_STARTUP_ROOT / "machine-ledger.md",
    TERMINATION_ROOT / "machine-ledger.md",
    PREVIOUS_REPORT_READINESS_ROOT / "machine-ledger.md",
    CLEANUP_CONTROL_ROOT / "machine-ledger.md",
    CLEANUP_SEMANTICS_ROOT / "machine-ledger.md",
)
LEDGER_LIMIT = 8 * 1024 * 1024

IDENTITY_APIS = frozenset({"GetProcessId", "GetProcessTimes", "QueryFullProcessImageNameW"})
IDENTITY_STAGES = frozenset(
    {
        "unknown",
        "initial_bind",
        "binding_recheck",
        "business_bind",
        "observation",
        "stop_entry",
        "termination_handle",
        "pre_terminate",
        "post_wait",
    }
)
IDENTITY_RECORD_LIMIT = 2048


def identity_diagnostic(value: object) -> dict[str, Any]:
    """Only this closed, bounded schema may cross the failure-report boundary."""
    enums = {
        "api": IDENTITY_APIS,
        "stage": IDENTITY_STAGES,
        "process_role": {"unknown", "launcher", "business"},
        "handle_role": {"unknown", "query", "termination"},
        "image_status": {"unknown", "approved"},
    }
    integers = {"pid", "expected_pid", "created_100ns", "last_observed_ns"}
    required = set(enums) | integers | {"last_alive", "active_cleanup", "win32_error"}
    if type(value) is not dict or set(value) != required:
        raise RuntimeError("step6_identity_diagnostic_invalid")
    for key, choices in enums.items():
        if type(value[key]) is not str or value[key] not in choices:
            raise RuntimeError("step6_identity_diagnostic_invalid")
    for key in integers:
        item = value[key]
        if item is not None and (type(item) is not int or not 0 <= item < 2**64):
            raise RuntimeError("step6_identity_diagnostic_invalid")
    if (
        (value["last_alive"] is not None and type(value["last_alive"]) is not bool)
        or type(value["active_cleanup"]) is not bool
        or type(value["win32_error"]) is not int
        or not 0 <= value["win32_error"] < 2**32
        or len(json.dumps(value).encode("utf-8")) > IDENTITY_RECORD_LIMIT
    ):
        raise RuntimeError("step6_identity_diagnostic_invalid")
    return dict(value)


def termination_diagnostic(value: object) -> dict[str, Any]:
    """A termination attempt is distinct from identity validation and final exit."""
    enums = {
        "api": {"TerminateProcess"},
        "stage": {"terminate_returned", "post_terminate_state", "post_terminate_state_failed"},
        "process_role": {"unknown", "launcher", "business"},
        "handle_role": {"termination"},
        "identity_evidence": {"initial_binding"},
        "state_error": {"none", "step6_startup_process_wait_failed", "unknown"},
    }
    integers = {"pid", "parent_pid", "created_100ns", "attempt_ns", "state_ns"}
    nullable_bools = {"after_alive", "after_exit_code_available"}
    required = (
        set(enums)
        | integers
        | nullable_bools
        | {"after_exit_code", "active_cleanup", "win32_error"}
    )
    if type(value) is not dict or set(value) != required:
        raise RuntimeError("step6_termination_diagnostic_invalid")
    for key, choices in enums.items():
        if type(value[key]) is not str or value[key] not in choices:
            raise RuntimeError("step6_termination_diagnostic_invalid")
    for key in integers:
        item = value[key]
        if item is not None and (type(item) is not int or not 0 <= item < 2**64):
            raise RuntimeError("step6_termination_diagnostic_invalid")
    for key in nullable_bools:
        if value[key] is not None and type(value[key]) is not bool:
            raise RuntimeError("step6_termination_diagnostic_invalid")
    for key in ("win32_error", "after_exit_code"):
        item = value[key]
        if item is None and key == "after_exit_code":
            continue
        if type(item) is not int or not 0 <= item < 2**32:
            raise RuntimeError("step6_termination_diagnostic_invalid")
    if type(value["active_cleanup"]) is not bool or len(json.dumps(value).encode()) > 2048:
        raise RuntimeError("step6_termination_diagnostic_invalid")
    return dict(value)


class StartupTerminationError(OSError):
    def __init__(self, diagnostic: dict[str, Any]) -> None:
        self.diagnostic = termination_diagnostic(diagnostic)
        super().__init__(self.diagnostic["win32_error"], "step6_startup_owned_termination_failed")


def cleanup_diagnostic(value: object) -> dict[str, Any]:
    """Popen call completion is not proof of kernel termination or a signaled handle."""
    enums = {
        "process_role": {"launcher"},
        "source": {"popen_handle"},
        "failure_kind": {"none", "oserror", "timeout", "unknown"},
        "error_source": {"unknown", "winerror", "errno"},
    }
    integers = {"pid", "observed_ns", "exit_code_before_cleanup", "final_exit_code", "error_code"}
    flags = {
        "attempted",
        "cleanup_call_completed",
        "termination_requested",
        "terminate_call_completed",
        "wait_returned",
        "exit_code_available",
    }
    unknowns = {"terminate_api_succeeded", "signaled_confirmed"}
    if type(value) is not dict or set(value) != set(enums) | integers | flags | unknowns:
        raise RuntimeError("step6_cleanup_diagnostic_invalid")
    for key, choices in enums.items():
        if type(value[key]) is not str or value[key] not in choices:
            raise RuntimeError("step6_cleanup_diagnostic_invalid")
    for key in integers:
        item = value[key]
        if item is not None and (type(item) is not int or not -(2**63) <= item < 2**64):
            raise RuntimeError("step6_cleanup_diagnostic_invalid")
    if any(type(value[key]) is not bool for key in flags) or len(json.dumps(value).encode()) > 1024:
        raise RuntimeError("step6_cleanup_diagnostic_invalid")
    if any(value[key] is not None for key in unknowns) or value["exit_code_available"] is not (
        type(value["final_exit_code"]) is int
    ):
        raise RuntimeError("step6_cleanup_diagnostic_invalid")
    return dict(value)


class StartupIdentityError(RuntimeError):
    def __init__(self, api: str, code: int, pid: int | None) -> None:
        super().__init__("step6_startup_process_identity_unavailable")
        self.diagnostic = identity_diagnostic(
            {
                "api": api,
                "stage": "unknown",
                "process_role": "unknown",
                "handle_role": "unknown",
                "pid": pid,
                "expected_pid": None,
                "created_100ns": None,
                "image_status": "unknown",
                "last_alive": None,
                "last_observed_ns": None,
                "active_cleanup": False,
                "win32_error": code,
            }
        )


def require_identity_capacity(root: Path) -> None:
    files = {
        str(path.relative_to(root)): path.stat().st_size
        for path in root.rglob("*")
        if path.is_file()
    }
    fixed = {
        "machine-ledger.md": 8 * 1024**2,
        "identity-events.jsonl": 1024**2,
        "termination-events.jsonl": 1024**2,
        "pytest-summary.json": 1024**2,
        "invocation.json": 64 * 1024,
        "stderr-redacted.txt": 1024**2,
        "stdout-redacted.txt": 256 * 1024,
    }
    observers = {"native-summary.json", "native-monitor-ready.json", "native-monitor-drain.marker"}
    if (
        any(files.get(name, 0) > limit for name, limit in fixed.items())
        or sum(size for name, size in files.items() if name in observers) > 8 * 1024**2
        or sum(size for name, size in files.items() if name not in fixed and name not in observers)
        > 8 * 1024**2
    ):
        raise RuntimeError("step6_identity_artifact_limit")


class CanonicalPathError(RuntimeError):
    def __init__(self, resolved: Path, *, expected: Path | None = None) -> None:
        super().__init__("step6_resource_canonical_mismatch")
        self.resolved = resolved
        self.diagnostic = canonical_diagnostic(expected, resolved) if expected is not None else {}


def canonical_diagnostic(expected: Path, resolved: Path) -> dict[str, object]:
    """Capture metadata after rejection without resolving or opening the target."""
    inside = expected.is_absolute() and expected.is_relative_to(QA_ROOT)
    target = Path(str(resolved).removeprefix("\\\\?\\"))
    retired = QA_ROOT.drive + "\\$Extend\\$Deleted"
    if target.parent == Path(retired) and re.fullmatch(r"[0-9a-fA-F]{16,64}", target.name):
        target_class = "ntfs_retired"
    elif target.is_relative_to(QA_ROOT):
        target_class = "different_qa_path"
    else:
        target_class = "outside_qa_root"
    suffix = next(
        (value for value in ("-journal", "-wal", "-shm") if str(expected).endswith(value)),
        "",
    )
    role = (
        "sqlite_" + suffix.removeprefix("-")
        if suffix
        else "sqlite_main"
        if expected.suffix in {".sqlite3", ".db"}
        else "other"
    )
    chain: list[dict[str, object]] = []
    if inside:
        for level, path in enumerate((expected, *expected.parents)):
            row: dict[str, object] = {"level": level}
            try:
                status = path.lstat()
            except OSError as error:
                row["state"] = "absent" if isinstance(error, FileNotFoundError) else "unavailable"
            else:
                row.update(
                    state="present",
                    device=str(status.st_dev),
                    file_id=str(status.st_ino),
                    reparse=bool(status.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT),
                )
            chain.append(row)
    return {
        "code": "step6_resource_canonical_mismatch",
        "expected_qa_path": str(expected) if inside else None,
        "resolved_target_class": target_class,
        "resource_role": role,
        "event": "canonical_validation",
        "snapshot_timing": "after_rejection_not_atomic",
        "identity_parent_chain": chain,
    }


def validate_path(path: Path) -> Path:
    """Reject aliases and reparse points before allowing a QA resource path."""
    absolute = Path(os.path.abspath(path))
    if not absolute.is_relative_to(QA_ROOT):
        raise RuntimeError("step6_resource_outside_authorized_root")
    for parent in (absolute, *absolute.parents):
        try:
            attributes = parent.lstat().st_file_attributes
        except FileNotFoundError:
            continue
        if attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError("step6_resource_reparse_point")
    resolved = absolute.resolve()
    # Windows realpath can retain the DOS prefix if a resolved file disappears
    # before its second OS lookup. Only that exact path spelling is equivalent.
    if resolved != absolute and resolved != Path("\\\\?\\" + str(absolute)):
        raise CanonicalPathError(resolved, expected=absolute)
    return absolute


class MachineLedger:
    """Pin an append-only metadata file; never infer the project from its location."""

    def __init__(self, path: Path) -> None:
        self._path = validate_path(path)
        status = self.path.lstat()
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            raise RuntimeError("step6_machine_ledger_identity_invalid")
        self.identity = (status.st_dev, status.st_ino)
        self.minimum_size = status.st_size
        self.lock = threading.RLock()

    @property
    def path(self) -> Path:
        return self._path

    def check(self) -> os.stat_result:
        status = validate_path(self.path).lstat()
        if (status.st_dev, status.st_ino) != self.identity or status.st_nlink != 1:
            raise RuntimeError("step6_machine_ledger_identity_changed")
        if status.st_size < self.minimum_size:
            raise RuntimeError("step6_machine_ledger_truncated")
        if status.st_size > LEDGER_LIMIT:
            raise RuntimeError("step6_machine_ledger_capacity_exceeded")
        return status

    def append(self, label: str, payload: str) -> None:
        data = ("\n- Step6 " + label + ": " + payload + "\n").encode("utf-8")
        with self.lock:
            status = self.check()
            if status.st_size + len(data) > LEDGER_LIMIT:
                raise RuntimeError("step6_machine_ledger_capacity_exceeded")
            with self.path.open("ab", buffering=0) as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino) != self.identity:
                    raise RuntimeError("step6_machine_ledger_identity_changed")
                if stream.write(data) != len(data):
                    raise RuntimeError("step6_machine_ledger_short_write")
                stream.flush()
            self.minimum_size = self.check().st_size

    def read_since(self, offset: int) -> tuple[bytes, int]:
        with self.lock:
            status = self.check()
            if offset > status.st_size:
                raise RuntimeError("step6_machine_ledger_truncated")
            with self.path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino) != self.identity:
                    raise RuntimeError("step6_machine_ledger_identity_changed")
                stream.seek(offset)
                chunk = stream.read()
                end = stream.tell()
            self.minimum_size = max(self.minimum_size, end)
            self.check()
            return chunk, end


_machine_ledger: MachineLedger | None = None


def batch_ledger_path(root: Path) -> Path:
    if root not in BATCH_LIMITS:
        raise RuntimeError("step6_machine_ledger_batch_not_approved")
    return root / "machine-ledger.md"


def machine_ledger(root: Path | None = None) -> MachineLedger:
    """Bind once per process; never switch a running observer's writer."""
    global _machine_ledger
    if _machine_ledger is not None:
        if root is not None and batch_ledger_path(root) != _machine_ledger.path:
            raise RuntimeError("step6_machine_ledger_batch_switch")
        return _machine_ledger
    if root is None:
        inherited = os.environ.get("F009_MACHINE_LEDGER")
        if not inherited:
            raise RuntimeError("step6_machine_ledger_batch_not_bound")
        path = Path(inherited)
        root = path.parent
        if path != batch_ledger_path(root):
            raise RuntimeError("step6_machine_ledger_path_mismatch")
        native = os.environ.get("F009_NATIVE_ROOT")
        if native is not None and Path(native) != root:
            raise RuntimeError("step6_machine_ledger_parent_child_mismatch")
    _machine_ledger = MachineLedger(batch_ledger_path(root))
    return _machine_ledger


def require_batch_capacity(root: Path, batch_bytes: int, total_bytes: int) -> None:
    batch_ledger_path(root)
    if batch_bytes > BATCH_LIMITS[root] or total_bytes > 2 * 1024**3:
        raise RuntimeError("step6_contract_resource_capacity_exceeded")


def bootstrap_registrations(root: Path) -> list[str]:
    required = {str(root), str(batch_ledger_path(root))}
    lines = []
    for line in CURRENT_TASK.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Step6 resource pre-registration: `"):
            metadata = json.loads(line.split("`", 1)[1].rstrip("`"))
            if metadata.get("path") in required:
                expected_limit = (
                    BATCH_LIMITS[root] if metadata["path"] == str(root) else LEDGER_LIMIT
                )
                if (
                    metadata.get("state") != "registered_before_operation"
                    or metadata.get("task") != "F009-Step6"
                    or metadata.get("max_bytes") != expected_limit
                ):
                    raise RuntimeError("step6_machine_ledger_bootstrap_not_registered")
                lines.append(line)
    if len(lines) != 2 or not required <= registered_resource_paths((CURRENT_TASK,)):
        raise RuntimeError("step6_machine_ledger_bootstrap_not_registered")
    return lines


class ResourceGuard:
    """Register exact Python-created paths before creation, retaining only metadata."""

    def __init__(self, *, ledger: MachineLedger | None = None) -> None:
        self.active = False
        self.registration_stream: Any = sys.__stdout__
        self.registered: set[str] = set()
        self.reconciled_sqlite_sidecars: set[str] = set()
        self.lock = threading.RLock()
        self.violations: Counter[str] = Counter()
        self.native_root: Path | None = None
        self.ledger = ledger

    def record(self, label: str, payload: str) -> None:
        (self.ledger or machine_ledger()).append(label, payload)

    def register(self, path: Path, category: str) -> None:
        try:
            absolute = validate_path(path)
        except CanonicalPathError as error:
            error.diagnostic["event"] = (
                "sqlite_surface_registration"
                if category == "synthetic_sqlite_surface"
                else "resource_registration"
            )
            with self.lock:
                if self._reconcile_registered_sqlite_sidecar(path, category, error):
                    return
            raise
        key = str(absolute)
        with self.lock:
            if key in self.registered:
                return
            metadata = {
                "task": "F009-Step6",
                "registered_at": datetime.now(UTC).isoformat(),
                "path": key,
                "category": category,
                "state": "registered_before_operation",
                "retention": "until_step6_close_user_manual_removal",
            }
            line = json.dumps(metadata, ensure_ascii=True, sort_keys=True)
            self.record("resource pre-registration", "`" + line + "`")
            self.registered.add(key)
            print(line, file=self.registration_stream, flush=True)

    def _reconcile_registered_sqlite_sidecar(
        self, path: Path, category: str, error: CanonicalPathError
    ) -> bool:
        """Accept only a previously registered sidecar retired during a repeat audit."""
        absolute = Path(os.path.abspath(path))
        suffix = next(
            (item for item in ("-journal", "-wal", "-shm") if str(absolute).endswith(item)),
            None,
        )
        retired_parent = Path("\\\\?\\" + QA_ROOT.drive + "\\$Extend\\$Deleted")
        if (
            category != "synthetic_sqlite_surface"
            or suffix is None
            or not absolute.is_relative_to(QA_ROOT)
            or error.resolved.parent != retired_parent
            or not re.fullmatch(r"[0-9a-fA-F]{16,64}", error.resolved.name)
            or str(absolute) not in self.registered
            or str(absolute)[: -len(suffix)] not in self.registered
        ):
            return False
        try:
            absolute.lstat()
        except FileNotFoundError:
            current_state = "absent"
        else:
            validate_path(absolute)
            current_state = "current_path_strictly_revalidated"
        parent = validate_path(absolute.parent)
        if not parent.is_dir():
            return False
        key = str(absolute)
        if key not in self.reconciled_sqlite_sidecars:
            self.reconciled_sqlite_sidecars.add(key)
            self.record(
                "retired registered SQLite sidecar reconciliation",
                json.dumps({"path": key, "current_state": current_state}, sort_keys=True),
            )
        return True

    def reject(self, code: str) -> NoReturn:
        self.violations[code] += 1
        raise RuntimeError(code)

    def audit(self, event: str, args: tuple[Any, ...]) -> None:
        if not self.active:
            return
        if event in {"os.symlink", "os.link"}:
            self.reject("step6_resource_alias_creation_blocked")
        if event in {"socket.connect", "socket.bind"}:
            address = args[1]
            if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "::1"}:
                self.reject("step6_non_loopback_socket")
        if event == "os.mkdir":
            self.register(Path(args[0]), "synthetic_directory")
        elif event == "sqlite3.connect" and args[0] != ":memory:":
            raw_path = str(args[0])
            if raw_path.startswith("file:"):
                uri = urlsplit(raw_path)
                query = parse_qs(uri.query, strict_parsing=True)
                if uri.netloc or query.get("mode") != ["ro"] or set(query) - {"mode", "immutable"}:
                    self.reject("step6_sqlite_uri_not_readonly_local")
                decoded = unquote(uri.path)
                if os.name == "nt" and len(decoded) > 3 and decoded[0] == "/" and decoded[2] == ":":
                    decoded = decoded[1:]
                path = validate_path(Path(decoded))
            else:
                path = Path(args[0])
            for suffix in ("", "-wal", "-shm", "-journal"):
                self.register(Path(str(path) + suffix), "synthetic_sqlite_surface")
        elif event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0]))
            absolute = Path(os.path.abspath(path))
            if absolute.suffix.casefold() == ".keystore":
                self.reject("step6_python_keystore_access_blocked")
            mode, flags = args[1], args[2]
            writing = isinstance(mode, str) and any(char in mode for char in "wax+")
            writing = writing or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if absolute == machine_ledger().path:
                if writing and not flags & os.O_APPEND:
                    self.reject("step6_machine_ledger_nonappend_write")
                return
            if (
                writing
                and absolute.name == "machine-ledger.md"
                and absolute.is_relative_to(RECOVERY_ROOT)
            ):
                self.reject("step6_inactive_machine_ledger_write")
            if absolute == EVIDENCE and writing:
                self.reject("step6_formal_evidence_runtime_write")
            if writing:
                if str(absolute).upper() in {"NUL", "\\\\.\\NUL"}:
                    return
                self.register(absolute, "synthetic_test_or_metadata_file")
            elif not absolute.is_relative_to(QA_ROOT):
                if absolute.name.startswith(".env") and absolute.name != ".env.example":
                    self.reject("step6_real_env_read_blocked")
                if ".sqlite3" in absolute.name or absolute.suffix == ".db":
                    self.reject("step6_old_database_read_blocked")


def configure_environment() -> None:
    validate_path(QA_ROOT)
    for source in (PROJECT_ROOT, PROJECT_ROOT / "backend/src"):
        if str(source) not in sys.path:
            sys.path.insert(0, str(source))
    native = os.environ.get("F009_NATIVE_ROOT")
    root = validate_path(Path(native)) if native else QA_ROOT
    if native and root not in NATIVE_ROOTS:
        raise RuntimeError("step6_native_precreation_boundary_unavailable")
    temp = validate_path(root / "tmp")
    if not temp.is_dir():
        raise RuntimeError("step6_temp_not_registered")
    os.environ.update(command_environment(dict(os.environ), root))
    tempfile.tempdir = str(temp)
    if Path(tempfile.gettempdir()).resolve() != temp:
        raise RuntimeError("step6_temp_resolution_mismatch")


def command_environment(environment: dict[str, str], root: Path) -> dict[str, str]:
    """Apply the same cache policy even when callers supply a custom child env."""
    root = validate_path(root)
    if root != QA_ROOT and root not in NATIVE_ROOTS:
        raise RuntimeError("step6_command_environment_root_not_approved")
    result = {key: value for key, value in environment.items() if key.casefold() != "llm_api_key"}
    if root in BATCH_LIMITS:
        result["F009_MACHINE_LEDGER"] = str(batch_ledger_path(root))
    elif _machine_ledger is not None or os.environ.get("F009_MACHINE_LEDGER"):
        result["F009_MACHINE_LEDGER"] = str(machine_ledger().path)
    else:
        result.pop("F009_MACHINE_LEDGER", None)
    if root == QA_ROOT:
        for key in tuple(result):
            if key.upper() in {"F009_NATIVE_ROOT", "F009_NATIVE_PID"}:
                result.pop(key)
    result.update(
        TEMP=str(root / "tmp"),
        TMP=str(root / "tmp"),
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTEST_ADDOPTS="",
        CYBER_TOWN_DISABLE_DOTENV="1",
        LLM_PROVIDER="disabled",
        UV_OFFLINE="1",
        UV_NO_CACHE="0" if root in NATIVE_ROOTS else "1",
        UV_CACHE_DIR=str(root / "cache/uv"),
        UV_PYTHON=sys.executable,
        UV_PYTHON_DOWNLOADS="never",
        RUFF_NO_CACHE="true",
        RUFF_CACHE_DIR=str(root / "cache/ruff"),
        MYPY_CACHE_DIR=str(root / "cache" / "mypy"),
    )
    return result


@contextmanager
def command_scope() -> Iterator[None]:
    from unittest.mock import patch

    previous_temp, previous_path = tempfile.tempdir, list(sys.path)
    try:
        with patch.dict(os.environ, dict(os.environ), clear=True):
            configure_environment()
            yield
    finally:
        tempfile.tempdir = previous_temp
        sys.path[:] = previous_path


class BenchmarkConfiguration(Protocol):
    CORE_REVALIDATION_ROOT: Path
    _INDEPENDENT_CLIENT: bool


@contextmanager
def benchmark_root_binding(module: BenchmarkConfiguration) -> Iterator[None]:
    """Change only the explicitly authorized root configuration for this scope."""
    validate_path(QA_ROOT)
    original_root = module.CORE_REVALIDATION_ROOT
    original_client = module._INDEPENDENT_CLIENT
    module.CORE_REVALIDATION_ROOT = QA_ROOT
    try:
        yield
    finally:
        module.CORE_REVALIDATION_ROOT = original_root
        module._INDEPENDENT_CLIENT = original_client


SPACE_PERFORMANCE_ROOT = RECOVERY_ROOT / "performance"


@contextmanager
def space_performance_root_binding(module: BenchmarkConfiguration) -> Iterator[Path]:
    """Bind the separately authorized C batch and restore both runner settings."""
    root = validate_path(SPACE_PERFORMANCE_ROOT)
    before = root.lstat()
    if not stat.S_ISDIR(before.st_mode) or (root / "full-matrix-01").exists():
        raise RuntimeError("step6_space_performance_root_not_fresh")
    original_root = module.CORE_REVALIDATION_ROOT
    original_client = module._INDEPENDENT_CLIENT
    module.CORE_REVALIDATION_ROOT = root
    try:
        yield root
    finally:
        module.CORE_REVALIDATION_ROOT = original_root
        module._INDEPENDENT_CLIENT = original_client
        after = validate_path(root).lstat()
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise RuntimeError("step6_space_performance_root_identity_changed")


def verified_report_classes(
    module: object,
) -> tuple[type[BaseException], type[BaseException], type[BaseException]]:
    """Read only a verified module's definitions, never its active runtime instances."""
    from importlib.machinery import ModuleSpec
    from types import FunctionType, ModuleType

    expected = Path(__file__).resolve()
    if not isinstance(module, ModuleType):
        raise RuntimeError("step6_report_module_source_unverified")
    namespace = vars(module)
    origin = namespace.get("__file__")
    spec = namespace.get("__spec__")
    if (
        type(origin) is not str
        or Path(origin).resolve() != expected
        or not isinstance(spec, ModuleSpec)
        or spec.name != "scripts.f009_step6_qa"
        or type(spec.origin) is not str
        or Path(spec.origin).resolve() != expected
    ):
        raise RuntimeError("step6_report_module_source_unverified")
    identity = namespace.get("StartupIdentityError")
    canonical = namespace.get("CanonicalPathError")
    termination = namespace.get("StartupTerminationError")
    if (
        not isinstance(identity, type)
        or not isinstance(canonical, type)
        or not isinstance(termination, type)
    ):
        raise RuntimeError("step6_report_exception_source_unverified")
    for definition, base in (
        (identity, RuntimeError),
        (canonical, RuntimeError),
        (termination, OSError),
    ):
        if (
            not isinstance(definition, type)
            or not issubclass(definition, base)
            or definition.__module__ != "scripts.f009_step6_qa"
            or not isinstance(vars(definition).get("__init__"), FunctionType)
            or Path(vars(definition)["__init__"].__code__.co_filename).resolve() != expected
        ):
            raise RuntimeError("step6_report_exception_source_unverified")
    return identity, canonical, termination


class MetadataReporter:
    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.results: list[dict[str, object]] = []
        self.canonical_failures: dict[tuple[str, str], dict[str, object]] = {}
        self.identity_failures: dict[tuple[str, str], dict[str, Any]] = {}
        self.identity_rejections: list[dict[str, str]] = []
        self.termination_failures: dict[tuple[str, str], dict[str, Any]] = {}
        self.termination_rejections: list[dict[str, str]] = []
        self.failure_lock = threading.Lock()

    def pytest_runtest_makereport(self, item: Any, call: Any) -> None:
        if call.excinfo is None:
            return
        identity_types: tuple[type[BaseException], ...] = (StartupIdentityError,)
        canonical_types: tuple[type[BaseException], ...] = (CanonicalPathError,)
        termination_types: tuple[type[BaseException], ...] = (StartupTerminationError,)
        module = sys.modules.get("scripts.f009_step6_qa")
        if module is not None:
            identity_class, canonical_class, termination_class = verified_report_classes(module)
            identity_types = (*identity_types, identity_class)
            canonical_types = (*canonical_types, canonical_class)
            termination_types = (*termination_types, termination_class)
        if type(call.excinfo.value) in termination_types:
            try:
                termination = termination_diagnostic(call.excinfo.value.diagnostic)
            except RuntimeError:
                with self.failure_lock:
                    self.termination_rejections.append(
                        {
                            "nodeid": item.nodeid,
                            "phase": call.when,
                            "code": "step6_termination_diagnostic_invalid",
                        }
                    )
                raise
            with self.failure_lock:
                self.termination_failures[(item.nodeid, call.when)] = termination
        if type(call.excinfo.value) in identity_types:
            try:
                diagnostic = identity_diagnostic(call.excinfo.value.diagnostic)
            except RuntimeError:
                with self.failure_lock:
                    self.identity_rejections.append(
                        {
                            "nodeid": item.nodeid,
                            "phase": call.when,
                            "code": "step6_identity_diagnostic_invalid",
                        }
                    )
                raise
            with self.failure_lock:
                self.identity_failures[(item.nodeid, call.when)] = diagnostic
        if isinstance(call.excinfo.value, canonical_types):
            with self.failure_lock:
                self.canonical_failures[(item.nodeid, call.when)] = vars(call.excinfo.value)[
                    "diagnostic"
                ]

    def pytest_runtest_logreport(self, report: Any) -> None:
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
            self.counts[report.outcome] += 1
            result = {
                "nodeid": report.nodeid,
                "phase": report.when,
                "outcome": report.outcome,
                "metadata": [
                    (key, value)
                    for key, value in report.user_properties
                    if key not in {"startup_termination_observation", "startup_cleanup_report"}
                ],
            }
            observed = [
                termination_diagnostic(value)
                for key, value in report.user_properties
                if key == "startup_termination_observation"
            ]
            cleanups = [
                cleanup_diagnostic(value)
                for key, value in report.user_properties
                if key == "startup_cleanup_report"
            ]
            if len(observed) > 2 or len(cleanups) > 1:
                raise RuntimeError("step6_termination_diagnostic_invalid")
            if observed:
                result["termination_observations"] = observed
            if cleanups:
                result["cleanup_report"] = cleanups[0]
            if report.failed and hasattr(report.longrepr, "reprcrash"):
                result["failure_location"] = {
                    "path": report.longrepr.reprcrash.path,
                    "line": report.longrepr.reprcrash.lineno,
                }
            with self.failure_lock:
                diagnostic = self.canonical_failures.pop((report.nodeid, report.when), None)
            if report.failed and diagnostic is not None:
                result["canonical_diagnostic"] = diagnostic
            with self.failure_lock:
                identity = self.identity_failures.pop((report.nodeid, report.when), None)
            if report.failed and identity is not None:
                result["startup_identity_diagnostic"] = identity_diagnostic(identity)
            with self.failure_lock:
                termination = self.termination_failures.pop((report.nodeid, report.when), None)
            if report.failed and termination is not None:
                result["startup_termination_diagnostic"] = termination_diagnostic(termination)
            self.results.append(result)


@contextmanager
def pytest_directory_scope(basetemp: Path) -> Iterator[Counter[str]]:
    """Keep numbered pytest directories without optional current aliases."""
    from unittest.mock import patch

    from _pytest import pathlib as pytest_paths

    basetemp = validate_path(basetemp)
    suppressed: Counter[str] = Counter()

    def omit_current_alias(root: Path, target: Any, link_to: Any) -> None:
        root = validate_path(root)
        alias = validate_path(root / target)
        destination = validate_path(Path(link_to))
        prefix = str(target).removesuffix("current")
        if (
            not root.is_relative_to(basetemp)
            or alias.parent != root
            or destination.parent != root
            or not str(target).endswith("current")
            or not prefix
            or not re.fullmatch(re.escape(prefix) + r"[0-9]+", destination.name)
            or not destination.is_dir()
            or alias.exists()
        ):
            raise RuntimeError("step6_pytest_alias_request_invalid")
        suppressed["current_aliases_not_created"] += 1

    with patch.object(pytest_paths, "_force_symlink", omit_current_alias):
        yield suppressed


def run_pytest(arguments: list[str], *, batch: str, output: str) -> int:
    import pytest

    basetemp = validate_path(QA_ROOT / batch)
    if basetemp.exists():
        raise RuntimeError("step6_pytest_basetemp_not_fresh")
    reporter = MetadataReporter()
    guard = ResourceGuard()
    configure_environment()
    attach_native_monitor(guard)
    sys.addaudithook(guard.audit)
    guard.active = True
    captured = io.StringIO()
    try:
        with (
            pytest_directory_scope(basetemp) as aliases,
            subprocess_isolation(guard),
            redirect_stdout(captured),
            redirect_stderr(captured),
        ):
            code = int(
                pytest.main(
                    [
                        "-p",
                        "no:cacheprovider",
                        "-p",
                        "anyio.pytest_plugin",
                        "-s",
                        "-q",
                        "--tb=no",
                        "-x",
                        "--show-capture=no",
                        "--basetemp=" + basetemp.as_posix(),
                        *arguments,
                    ],
                    plugins=[reporter],
                )
            )
        summary = {
            "schema_version": 1,
            "batch": batch,
            "exit_code": code,
            "counts": dict(reporter.counts),
            "results": reporter.results,
            "identity_diagnostic_rejections": reporter.identity_rejections,
            "termination_diagnostic_rejections": reporter.termination_rejections,
            "registered_path_count": len(guard.registered),
            "boundary_violations": dict(guard.violations),
            "pytest_directory_metadata": dict(aliases),
            "raw_output_retained": False,
            "temp_path": str(tempfile.gettempdir()),
        }
        write_pytest_summary(validate_path(QA_ROOT / output), summary, max_bytes=1024**2)
        print(json.dumps(summary, sort_keys=True), file=sys.__stdout__)
        return code
    finally:
        captured.close()
        guard.active = False


@contextmanager
def subprocess_isolation(guard: ResourceGuard) -> Iterator[None]:
    """Guard child Python and refuse native launches without precreation coverage."""
    import importlib
    import subprocess

    original = subprocess.Popen
    windows = importlib.import_module("asyncio.windows_utils") if os.name == "nt" else None
    original_windows = windows.Popen if windows is not None else None

    def prepare_and_launch(factory: Any, command: Any, *args: Any, **kwargs: Any) -> Any:
        if args or kwargs.get("shell") or kwargs.get("executable") is not None:
            guard.reject("step6_subprocess_launch_override_blocked")
        if not isinstance(command, (list, tuple)) or not command:
            guard.reject("step6_subprocess_requires_argument_vector")
        kwargs["env"] = command_environment(
            dict(kwargs.get("env") or os.environ), guard.native_root or QA_ROOT
        )
        argv = [os.fspath(item) for item in command]
        executable = Path(argv[0])
        if executable.is_absolute() and executable.resolve() == Path(sys.executable).resolve():
            remaining = argv[1:]
            flags = []
            while remaining and remaining[0] in {"-B", "-u"}:
                flags.append(remaining.pop(0))
            if not remaining or (remaining[0] in {"-c", "-m"} and len(remaining) < 2):
                guard.reject("step6_python_entrypoint_missing")
            if remaining[0].startswith("-") and remaining[0] not in {"-c", "-m"}:
                guard.reject("step6_python_option_not_supported")
            # A caller-supplied comment is not evidence that a child is guarded.
            launcher = (
                "# step6 child\nfrom scripts.f009_step6_qa import child_entrypoint\n"
                "child_entrypoint(" + repr(remaining) + ")\n"
            )
            argv = [str(Path(sys.executable).resolve()), "-B", *flags, "-c", launcher]
            environment = dict(kwargs.get("env") or os.environ)
            search = environment.get("PYTHONPATH", "")
            environment["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + search
            kwargs["env"] = environment
        else:
            argv = isolated_native_argv(guard, argv, kwargs)
        return factory(argv, *args, **kwargs)

    def isolated_popen(command: Any, *args: Any, **kwargs: Any) -> Any:
        return prepare_and_launch(original, command, *args, **kwargs)

    def isolated_windows_popen(command: Any, *args: Any, **kwargs: Any) -> Any:
        return prepare_and_launch(original_windows, command, *args, **kwargs)

    from unittest.mock import patch

    with ExitStack() as stack:
        stack.enter_context(patch.object(subprocess, "Popen", isolated_popen))
        if windows is not None:
            stack.enter_context(patch.object(windows, "Popen", isolated_windows_popen))
        yield


def child_entrypoint(arguments: list[str]) -> None:
    with startup_child_observation(arguments) as stages:
        _guarded_child_entrypoint(arguments, stages)


def _guarded_child_entrypoint(arguments: list[str], stages: Any) -> None:
    """Run the original child entrypoint with only process-local QA isolation."""
    import runpy

    configure_environment()
    stages("configured")
    guard = ResourceGuard()
    guard.registration_stream = sys.__stderr__
    attach_native_monitor(guard)
    stages("owner_verified")
    sys.addaudithook(guard.audit)
    guard.active = True
    stages("guard_active")
    original_temporary = tempfile.TemporaryDirectory

    def retained_temporary(*args: Any, **kwargs: Any) -> Any:
        kwargs["delete"] = False
        return original_temporary(*args, **kwargs)

    from unittest.mock import patch

    try:
        with (
            patch.object(tempfile, "TemporaryDirectory", retained_temporary),
            subprocess_isolation(guard),
        ):
            if arguments[0] == "-m":
                stages("module_entry")
                sys.argv = [arguments[1], *arguments[2:]]
                runpy.run_module(arguments[1], run_name="__main__", alter_sys=True)
            elif arguments[0] == "-c":
                sys.argv = ["-c", *arguments[2:]]
                exec(compile(arguments[1], "<step6-child>", "exec"), {"__name__": "__main__"})
            else:
                target = Path(arguments[0]).resolve()
                if not target.is_relative_to(PROJECT_ROOT):
                    raise RuntimeError("step6_child_script_outside_project")
                sys.argv = [str(target), *arguments[1:]]
                runpy.run_path(str(target), run_name="__main__")
    finally:
        guard.active = False


NATIVE_PROBE_ROOT = RECOVERY_ROOT / "tool-validation-01"
RECOVERY_TOOL_VALIDATION_ROOT_03 = RECOVERY_ROOT / "tool-validation-03"
RECOVERY_NATIVE_ROOT = RECOVERY_ROOT / "native-quality"
RECOVERY_NATIVE_ROOT_02 = RECOVERY_ROOT / "native-quality-02"
NATIVE_ROOTS = frozenset(
    {
        NATIVE_PROBE_ROOT,
        RECOVERY_TOOL_VALIDATION_ROOT_03,
        RECOVERY_NATIVE_ROOT,
        RECOVERY_NATIVE_ROOT_02,
        TOOL_CONTRACT_ROOT,
        NATIVE_QUALITY_ROOT,
        STARTUP_ROOT,
        IDENTITY_ROOT,
        COMPOSITION_ROOT,
        COMPOSITION_STARTUP_ROOT,
        TERMINATION_ROOT,
        REPORT_READINESS_ROOT,
        CLEANUP_CONTROL_ROOT,
        CLEANUP_SEMANTICS_ROOT,
        LAUNCHER_EXIT_ROOT,
        OBSERVER_FAILURE_ROOT,
        OBSERVER_CAPACITY_ROOT,
        MIGRATION_DIGEST_ROOT,
        *EXIT_VALIDATION_ROOTS,
        *STARTUP_READINESS_ROOTS,
        *s1_runtime.S1_ROOTS,
    }
)
GIT_EXE = Path(r"D:\Git\cmd\git.exe")
GODOT_EXE = Path(r"E:\Agent.tools\godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe")
UV_EXE = Path(r"C:\Users\24696\.cherrystudio\bin\uv.exe")


def native_category(root: Path, path: Path) -> str | None:
    relative = path.relative_to(root)
    parts = relative.parts
    if path.suffix.casefold() == ".keystore":
        if root not in NATIVE_ROOTS or path != root / "appdata/Godot/keystores/debug.keystore":
            raise RuntimeError("step6_native_key_path_not_approved")
        return "approved_local_godot_debug_keystore"
    if root not in NATIVE_ROOTS:
        return None
    if relative == Path("cache/uv") or relative.is_relative_to("cache/uv"):
        return "uv_offline_lock_cache"
    if ".git" in parts:
        owner = root.joinpath(*parts[: parts.index(".git")])
        if owner == root / "git-fixture" or owner.is_relative_to(root / "pytest"):
            return "synthetic_git_internal"
        return None
    if relative == Path("game/.godot") or relative.is_relative_to("game/.godot"):
        return "godot_import_cache"
    if relative == Path("appdata/Godot") or relative.is_relative_to("appdata/Godot"):
        return "godot_editor_configuration_or_test_userdata"
    if relative == Path("localappdata/Godot") or relative.is_relative_to("localappdata/Godot"):
        return "godot_local_cache"
    return None


def kernel_api() -> Any:
    import ctypes
    from ctypes import wintypes as w

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateFileW": (
            [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE],
            w.HANDLE,
        ),
        "CreateEventW": ([w.LPVOID, w.BOOL, w.BOOL, w.LPCWSTR], w.HANDLE),
        "ReadDirectoryChangesW": (
            [w.HANDLE, w.LPVOID, w.DWORD, w.BOOL, w.DWORD, w.LPVOID, w.LPVOID, w.LPVOID],
            w.BOOL,
        ),
        "GetOverlappedResult": ([w.HANDLE, w.LPVOID, w.LPVOID, w.BOOL], w.BOOL),
        "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD),
        "ResetEvent": ([w.HANDLE], w.BOOL),
        "CancelIoEx": ([w.HANDLE, w.LPVOID], w.BOOL),
        "CloseHandle": ([w.HANDLE], w.BOOL),
        "OpenProcess": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes = arguments
        function.restype = result
    return kernel


NATIVE_FAILURE_CODES = frozenset(
    {
        "step6_native_watch_overflow",
        "step6_native_watch_read_failed",
        "step6_native_watch_wait_failed",
        "step6_native_watch_arm_failed",
        "step6_native_watch_drain_timeout",
        "step6_native_watch_thread_not_closed",
        "step6_native_event_truncated",
        "step6_native_event_malformed",
        "step6_native_event_offset_invalid",
        "step6_native_event_outside_batch",
        "step6_native_unregistered_other_tool_resource",
        "step6_owned_tree_snapshot_failed",
        "step6_machine_ledger_short_write",
        "step6_machine_ledger_identity_changed",
        "step6_machine_ledger_truncated",
        "step6_machine_ledger_capacity_exceeded",
    }
)


def native_error_code(error: BaseException | None) -> str | None:
    if error is None:
        return None
    if (
        len(error.args) == 1
        and type(error.args[0]) is str
        and error.args[0] in NATIVE_FAILURE_CODES
    ):
        return error.args[0]
    return "step6_native_failure_unclassified"


def native_failure_details(watcher: NativeWatcher) -> dict[str, object]:
    """Copy only bounded scalars, never exception attributes or arbitrary paths."""
    raw = getattr(watcher, "failure_details", {})
    choices = {
        "stage": {"wait", "read", "rearm", "record", "unknown"},
        "api": {"WaitForSingleObject", "GetOverlappedResult", "ReadDirectoryChangesW", "unknown"},
    }
    result: dict[str, object] = {}
    for name, allowed in choices.items():
        value = raw.get(name)
        result[name] = value if type(value) is str and value in allowed else "unknown"
    for name in ("transferred_bytes", "win32_error", "observed_ns"):
        value = raw.get(name)
        result[name] = value if type(value) is int and 0 <= value < 2**64 else None
    for name in ("observer_pid", "event_count"):
        value = getattr(watcher, name, None)
        result[name] = value if type(value) is int and 0 <= value < 2**64 else None
    event = getattr(watcher, "last_event", {})
    path = event.get("path")
    relative = None
    if type(path) is str and len(path) <= 1024:
        try:
            candidate = Path(path).relative_to(watcher.root)
        except ValueError:
            pass
        else:
            if ".." not in candidate.parts and len(str(candidate)) <= 512:
                relative = candidate.as_posix()
    result["last_relative_path"] = relative
    action = event.get("action")
    result["last_action"] = action if type(action) is int and action in {1, 2, 3, 4, 5} else None
    written = getattr(watcher, "failure_record_written", None)
    result["ledger_failure_record_written"] = written if type(written) is bool else None
    failure_code = getattr(watcher, "failure_record_error", None)
    result["ledger_failure_code"] = (
        failure_code
        if type(failure_code) is str
        and failure_code in NATIVE_FAILURE_CODES | {"step6_native_failure_unclassified"}
        else None
    )
    return result


class NativeWatcher:
    """Observe approved native lifecycles; this is not a precreation sandbox."""

    def __init__(self, root: Path, registered: set[str] | None = None) -> None:
        import ctypes
        from ctypes import wintypes as w

        class Overlapped(ctypes.Structure):
            _fields_ = [
                ("internal", ctypes.c_size_t),
                ("internal_high", ctypes.c_size_t),
                ("offset", w.DWORD),
                ("offset_high", w.DWORD),
                ("event", w.HANDLE),
            ]

        self.root = validate_path(root)
        root_status = self.root.lstat()
        self.root_identity = (root_status.st_dev, root_status.st_ino)
        self.renamed_notifications: list[dict[str, object]] = []
        self.uv_cache_identity: tuple[int, int] | None = None
        if self.root in NATIVE_ROOTS:
            anchor = validate_path(self.root / "cache/uv")
            status = anchor.lstat()
            if not stat.S_ISDIR(status.st_mode):
                raise RuntimeError("step6_uv_cache_anchor_not_directory")
            self.uv_cache_identity = (status.st_dev, status.st_ino)
        self.retired_uv_notifications: list[dict[str, object]] = []
        self.kernel = kernel_api()
        self.overlapped = Overlapped()
        self.buffer = ctypes.create_string_buffer(NATIVE_BUFFER_BYTES)
        self.handle = self.kernel.CreateFileW(
            str(root), 1, 7, None, 3, 0x02000000 | 0x40000000, None
        )
        if not self.handle or self.handle == ctypes.c_void_p(-1).value:
            raise RuntimeError("step6_native_watch_open_failed")
        self.overlapped.event = self.kernel.CreateEventW(None, True, False, None)
        if not self.overlapped.event:
            self.kernel.CloseHandle(self.handle)
            raise RuntimeError("step6_native_watch_event_failed")
        self.stop_requested = threading.Event()
        self.seen: set[str] = set()
        self.native: dict[str, dict[str, Any]] = {}
        self.error: str | None = None
        self.last_event: dict[str, object] = {}
        self.observer_pid = os.getpid()
        self.failure_details: dict[str, object] = {}
        self.failure_record_written: bool | None = None
        self.failure_record_error: str | None = None
        self.ledger = machine_ledger()
        self.evidence_offset = self.ledger.check().st_size
        self.evidence_pending = b""
        self.python_registered: set[str] = set(registered or ())
        self.sqlite_surfaces: set[str] = set()
        self.retired_sqlite_sidecars: dict[str, str] = {}
        self.event_count = 0
        self.thread = threading.Thread(target=self._run, name="f009-native-observer", daemon=True)
        try:
            self._arm()
            self.thread.start()
        except BaseException:
            self.kernel.CloseHandle(self.overlapped.event)
            self.kernel.CloseHandle(self.handle)
            raise

    def _arm(self) -> None:
        import ctypes

        self.kernel.ResetEvent(self.overlapped.event)
        if not self.kernel.ReadDirectoryChangesW(
            self.handle,
            self.buffer,
            len(self.buffer),
            True,
            0x1F,
            None,
            ctypes.byref(self.overlapped),
            None,
        ):
            self.failure_details.update(
                api="ReadDirectoryChangesW", win32_error=ctypes.get_last_error()
            )
            raise RuntimeError("step6_native_watch_arm_failed")

    def _record(self, raw: bytes) -> None:
        import struct

        offset = 0
        while True:
            if len(raw) - offset < 12:
                raise RuntimeError("step6_native_event_truncated")
            following, action, size = struct.unpack_from("<III", raw, offset)
            end = offset + 12 + size
            if size % 2 or end > len(raw) or action not in {1, 2, 3, 4, 5}:
                raise RuntimeError("step6_native_event_malformed")
            name = raw[offset + 12 : end].decode("utf-16-le", errors="strict")
            self.last_event = {"path": str(self.root / name), "action": action}
            try:
                path = self._notification_path(self.root / name)
            except RuntimeError as error:
                self.last_event["resolved_path"] = str(
                    error.resolved
                    if isinstance(error, CanonicalPathError)
                    else (self.root / name).resolve()
                )
                raise
            if not path.is_relative_to(self.root):
                raise RuntimeError("step6_native_event_outside_batch")
            self.event_count += 1
            key = str(path)
            category = native_category(self.root, path)
            if not category and action in {1, 5}:
                self._refresh_python_registrations()
                if key not in self.python_registered:
                    raise RuntimeError("step6_native_unregistered_other_tool_resource")
            if category:
                item = self.native.setdefault(
                    key,
                    {
                        "category": category,
                        "actions": {},
                        "first_seen": datetime.now(UTC).isoformat(),
                    },
                )
                actions = item["actions"]
                first_action = str(action) not in actions
                actions[str(action)] = actions.get(str(action), 0) + 1
                if first_action:
                    line = json.dumps(
                        {
                            "path": key,
                            "action": action,
                            "category": category,
                            "observed_at": datetime.now(UTC).isoformat(),
                            "mode": "approved_native_runtime_observation",
                        },
                        sort_keys=True,
                    )
                    self._write_observation("native runtime event", line)
            self.seen.add(key)
            if not following:
                break
            if following < 12 or following % 4 or offset + following >= len(raw):
                raise RuntimeError("step6_native_event_offset_invalid")
            offset += following

    def _write_observation(self, label: str, payload: str) -> None:
        """Keep production evidence fixed while replay tests replace only their sink."""
        (getattr(self, "ledger", None) or machine_ledger()).append(label, payload)

    def _notification_path(self, path: Path) -> Path:
        """Validate late notifications without accepting an NTFS target for access."""
        try:
            return validate_path(path)
        except CanonicalPathError as error:
            absolute = Path(os.path.abspath(path))
            if self._renamed_notification(absolute, error):
                return absolute
            if self._retired_uv_notification(absolute, error):
                return absolute
            retired_parent = Path("\\\\?\\" + QA_ROOT.drive + "\\$Extend\\$Deleted")
            if (
                not absolute.is_relative_to(self.root)
                or error.resolved.parent != retired_parent
                or not re.fullmatch(r"[0-9a-fA-F]{16,64}", error.resolved.name)
            ):
                raise
            suffix = next(
                (item for item in ("-journal", "-wal", "-shm") if str(absolute).endswith(item)),
                None,
            )
            if suffix is None:
                raise
            self._refresh_python_registrations()
            key = str(absolute)
            if key not in self.sqlite_surfaces or key[: -len(suffix)] not in self.sqlite_surfaces:
                raise
            # SQLite can recreate the same journal before this late event is
            # consumed. Any currently present path must pass the strict check.
            try:
                current_status = absolute.lstat()
            except FileNotFoundError:
                current_state = "absent"
                current_identity = None
            else:
                validate_path(absolute)
                current_state = "current_path_strictly_revalidated"
                current_identity = str(current_status.st_ino)
            parent = validate_path(absolute.parent)
            if not parent.is_dir():
                raise error
            if key not in self.retired_sqlite_sidecars:
                self.retired_sqlite_sidecars[key] = str(error.resolved)
                self._write_observation(
                    "retired SQLite sidecar notification",
                    json.dumps(
                        {
                            "path": key,
                            "retired_target": str(error.resolved),
                            "current_state": current_state,
                            "current_file_id": current_identity,
                        }
                    ),
                )
            return absolute

    def _retired_uv_notification(self, absolute: Path, error: CanonicalPathError) -> bool:
        """Reconcile previously observed uv removals only after strict revalidation."""
        if (
            self.root not in NATIVE_ROOTS
            or not absolute.is_relative_to(self.root / "cache/uv")
            or self.last_event.get("action") not in {2, 4}
            or str(absolute) not in getattr(self, "seen", set())
        ):
            return False
        previous = getattr(self, "native", {}).get(str(absolute), {})
        if previous.get("category") != "uv_offline_lock_cache" or not any(
            previous.get("actions", {}).get(action) for action in ("1", "5")
        ):
            return False
        retired_parent = Path("\\\\?\\" + QA_ROOT.drive + "\\$Extend\\$Deleted")
        try:
            relative = error.resolved.relative_to(retired_parent)
        except ValueError:
            return False
        if not relative.parts or not re.fullmatch(r"[0-9a-fA-F]{16,64}", relative.parts[0]):
            return False
        tail = relative.parts[1:]
        if tail and (
            len(tail) >= len(absolute.relative_to(self.root / "cache/uv").parts)
            or absolute.parts[-len(tail) :] != tail
        ):
            return False
        # The original path and every extant parent must be canonical now.
        # The NTFS target is metadata only and is never used for an operation.
        validate_path(absolute)
        anchor = validate_path(self.root / "cache/uv")
        status = anchor.lstat()
        if not stat.S_ISDIR(status.st_mode) or (status.st_dev, status.st_ino) != getattr(
            self, "uv_cache_identity", None
        ):
            raise RuntimeError("step6_uv_cache_anchor_identity_changed")
        metadata = {
            "path": str(absolute),
            "retired_target": str(error.resolved),
            "action": self.last_event["action"],
            "category": "uv_offline_lock_cache",
            "original_path_strictly_revalidated": True,
            "anchor_device": str(status.st_dev),
            "anchor_file_id": str(status.st_ino),
        }
        self.retired_uv_notifications.append(metadata)
        self._write_observation("retired uv notification", json.dumps(metadata))
        return True

    def _renamed_notification(self, absolute: Path, error: CanonicalPathError) -> bool:
        """Recheck approved same-directory renames without granting alias access."""
        target = error.resolved
        if (
            not absolute.is_relative_to(self.root)
            or target.parent != absolute.parent
            or self.last_event.get("action") not in {1, 3, 4}
        ):
            return False
        category = native_category(self.root, absolute)
        if (
            category
            not in {
                "godot_import_cache",
                "godot_editor_configuration_or_test_userdata",
                "godot_local_cache",
            }
            or native_category(self.root, target) != category
            or not re.fullmatch(re.escape(target.name) + r"[0-9]{1,20}\.tmp", absolute.name)
        ):
            self._refresh_python_registrations()
            if not {str(absolute), str(target)} <= self.python_registered:
                return False
            category = "python_preregistered_rename"
        validate_path(absolute)
        try:
            absolute.lstat()
        except FileNotFoundError:
            pass
        else:
            return False
        root_status = validate_path(self.root).lstat()
        if (root_status.st_dev, root_status.st_ino) != getattr(self, "root_identity", None):
            raise RuntimeError("step6_native_root_identity_changed")
        parent = validate_path(absolute.parent).lstat()
        before = validate_path(target).lstat()
        if (
            not stat.S_ISDIR(parent.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_dev != root_status.st_dev
        ):
            raise RuntimeError("step6_godot_rename_target_identity_invalid")
        after = validate_path(target).lstat()
        final_parent = validate_path(absolute.parent).lstat()
        if (before.st_dev, before.st_ino, before.st_nlink) != (
            after.st_dev,
            after.st_ino,
            after.st_nlink,
        ) or (parent.st_dev, parent.st_ino) != (final_parent.st_dev, final_parent.st_ino):
            raise RuntimeError("step6_godot_rename_identity_changed")
        metadata = {
            "path": str(absolute),
            "renamed_target": str(target),
            "action": self.last_event["action"],
            "category": category,
            "original_absent_and_strictly_revalidated": True,
            "root_device": str(root_status.st_dev),
            "root_file_id": str(root_status.st_ino),
            "parent_file_id": str(parent.st_ino),
            "target_file_id": str(before.st_ino),
        }
        self.renamed_notifications.append(metadata)
        self._write_observation("renamed notification", json.dumps(metadata))
        return True

    def _refresh_python_registrations(self) -> None:
        chunk, self.evidence_offset = self.ledger.read_since(self.evidence_offset)
        lines = (self.evidence_pending + chunk).split(b"\n")
        self.evidence_pending = lines.pop()
        marker = b"Step6 resource pre-registration: " + bytes([96])
        for line in lines:
            if marker in line:
                payload = line.split(marker, 1)[1].rsplit(bytes([96]), 1)[0]
                metadata = json.loads(payload)
                self.python_registered.add(metadata["path"])
                if metadata["category"] == "synthetic_sqlite_surface":
                    self.sqlite_surfaces.add(metadata["path"])

    def _run(self) -> None:
        import ctypes
        from ctypes import wintypes as w

        try:
            while not self.stop_requested.is_set():
                self.failure_details = {"stage": "wait", "api": "WaitForSingleObject"}
                state = self.kernel.WaitForSingleObject(self.overlapped.event, 100)
                if state == 258:
                    continue
                if state != 0:
                    if state == 0xFFFFFFFF:
                        self.failure_details["win32_error"] = ctypes.get_last_error()
                    raise RuntimeError("step6_native_watch_wait_failed")
                count = w.DWORD()
                self.failure_details.update(stage="read", api="GetOverlappedResult")
                if not self.kernel.GetOverlappedResult(
                    self.handle, ctypes.byref(self.overlapped), ctypes.byref(count), False
                ):
                    win32_error = ctypes.get_last_error()
                    self.failure_details["win32_error"] = win32_error
                    if self.stop_requested.is_set() and win32_error == 995:
                        break
                    raise RuntimeError("step6_native_watch_read_failed")
                self.failure_details["transferred_bytes"] = count.value
                if count.value == 0:
                    raise RuntimeError("step6_native_watch_overflow")
                raw = self.buffer.raw[: count.value]
                self.failure_details.update(stage="rearm", api="ReadDirectoryChangesW")
                self._arm()
                self.failure_details.update(stage="record", api="unknown")
                self._record(raw)
        except Exception as error:
            self.failure_details["observed_ns"] = time.monotonic_ns()
            self.error = str(error) if str(error).startswith("step6_") else type(error).__name__
            try:
                self._write_observation(
                    "native observer failure",
                    json.dumps(
                        {"code": native_error_code(error), **native_failure_details(self)},
                        sort_keys=True,
                    ),
                )
                self.failure_record_written = True
            except Exception as report_error:
                # The parent still fails on self.error and reports this missing evidence.
                self.failure_record_written = False
                self.failure_record_error = native_error_code(report_error)

    def check(self) -> None:
        if self.error:
            raise RuntimeError(self.error)
        if hasattr(self, "ledger"):
            self.ledger.check()
        if getattr(self, "root", None) in BATCH_LIMITS:
            batch_bytes = sum(
                path.stat().st_size for path in self.root.rglob("*") if path.is_file()
            )
            total_bytes = sum(
                path.stat().st_size for path in RECOVERY_ROOT.rglob("*") if path.is_file()
            )
            require_batch_capacity(self.root, batch_bytes, total_bytes)
            if self.root in IDENTITY_VALIDATION_ROOTS:
                require_identity_capacity(self.root)
            if self.root == STARTUP_ROOT:
                for name, limit in STARTUP_FILE_LIMITS.items():
                    path = self.root / name
                    if path.exists() and path.stat().st_size > limit:
                        raise RuntimeError("step6_startup_artifact_limit")

    def drain(self, guard: ResourceGuard) -> None:
        import time

        marker = self.root / "native-monitor-drain.marker"
        guard.register(marker, "metadata_native_monitor_drain_marker")
        marker.write_text("synthetic observer drain", encoding="utf-8")
        deadline = time.monotonic() + 10
        while str(marker) not in self.seen:
            if self.error:
                raise RuntimeError(self.error)
            if time.monotonic() > deadline:
                raise RuntimeError("step6_native_watch_drain_timeout")
            self.stop_requested.wait(0.01)
        self.check()

    def close(self) -> None:
        import ctypes

        self.stop_requested.set()
        self.kernel.CancelIoEx(self.handle, ctypes.byref(self.overlapped))
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError("step6_native_watch_thread_not_closed")
        self.kernel.CloseHandle(self.overlapped.event)
        self.kernel.CloseHandle(self.handle)
        self.check()


def attach_native_monitor(guard: ResourceGuard) -> None:
    value = os.environ.get("F009_NATIVE_ROOT")
    if not value:
        return
    root = validate_path(Path(value))
    if root not in NATIVE_ROOTS:
        guard.reject("step6_native_precreation_boundary_unavailable")
    metadata = json.loads((root / "native-monitor-ready.json").read_text(encoding="utf-8"))
    if metadata["root"] != str(root) or str(metadata["pid"]) != os.environ.get("F009_NATIVE_PID"):
        guard.reject("step6_native_monitor_owner_mismatch")
    kernel = kernel_api()
    handle = kernel.OpenProcess(0x100000, False, metadata["pid"])
    if not handle:
        guard.reject("step6_native_monitor_owner_not_alive")
    try:
        if kernel.WaitForSingleObject(handle, 0) != 258:
            guard.reject("step6_native_monitor_owner_not_alive")
    finally:
        kernel.CloseHandle(handle)
    guard.native_root = root


def isolated_native_argv(
    guard: ResourceGuard, argv: list[str], kwargs: dict[str, Any]
) -> list[str]:
    root = guard.native_root
    if root is None:
        ruff = Path(sys.executable).parent / "ruff.exe"
        if Path(argv[0]).is_absolute() and Path(argv[0]).resolve() == ruff.resolve():
            allowed = static_commands() + space_format_commands() + space_static_commands()
            if argv in allowed:
                kwargs["env"] = command_environment(dict(kwargs.get("env") or os.environ), QA_ROOT)
                return argv
        guard.reject("step6_native_precreation_boundary_unavailable")
    cwd = Path(kwargs.get("cwd") or Path.cwd()).resolve()
    executable = Path(argv[0])
    name = executable.name.casefold()
    env = dict(kwargs.get("env") or os.environ)
    for key in tuple(env):
        if key.upper().startswith("GIT_") or key.casefold() == "llm_api_key":
            env.pop(key)
    env.update(
        APPDATA=str(root / "appdata"),
        LOCALAPPDATA=str(root / "localappdata"),
        TEMP=str(root / "tmp"),
        TMP=str(root / "tmp"),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="NUL",
        GIT_TEMPLATE_DIR=str(root / "git-template"),
        GIT_TERMINAL_PROMPT="0",
        GIT_OPTIONAL_LOCKS="0",
        GIT_NO_LAZY_FETCH="1",
        GIT_CONFIG_COUNT="3",
        GIT_CONFIG_KEY_0="core.hooksPath",
        GIT_CONFIG_VALUE_0="NUL",
        GIT_CONFIG_KEY_1="core.fsmonitor",
        GIT_CONFIG_VALUE_1="false",
        GIT_CONFIG_KEY_2="protocol.allow",
        GIT_CONFIG_VALUE_2="never",
        UV_OFFLINE="1",
        UV_NO_CACHE="0",
        UV_CACHE_DIR=str(root / "cache/uv"),
        UV_PYTHON=sys.executable,
        UV_PYTHON_DOWNLOADS="never",
        RUFF_NO_CACHE="true",
    )
    kwargs["env"] = env
    if name in {"git", "git.exe"}:
        if executable.is_absolute() and executable.resolve() != GIT_EXE.resolve():
            guard.reject("step6_native_executable_mismatch")
        rest = argv[1:]
        if rest[:1] == ["-C"] and len(rest) > 2:
            cwd = Path(rest[1]).resolve()
            rest = rest[2:]
        if not rest:
            guard.reject("step6_native_git_command_not_approved")
        operation = rest[0]
        readonly = {"show", "ls-files", "cat-file", "rev-parse", "check-ignore", "status"}
        writes = {"init", "add", "hash-object", "update-index"}
        if operation not in readonly | writes:
            guard.reject("step6_native_git_command_not_approved")
        if operation in writes:
            if not cwd.is_relative_to(root) or not (
                cwd.is_relative_to(root / "pytest") or cwd == root / "git-fixture"
            ):
                guard.reject("step6_native_precreation_boundary_unavailable")
            validate_path(cwd)
            if operation == "init" and rest[1:] not in ([], ["--quiet"]):
                guard.reject("step6_native_git_init_target_not_approved")
        elif cwd != PROJECT_ROOT and not cwd.is_relative_to(root):
            guard.reject("step6_native_git_read_root_not_approved")
        return [str(GIT_EXE), *argv[1:]]
    if executable.is_absolute() and executable.resolve() == GODOT_EXE.resolve():
        # Godot's debug-keystore helper uses the existing HotSpot JDK. Its
        # optional JVM counter file is not an approved QA resource category.
        for option in ("_JAVA_OPTIONS", "JDK_JAVA_OPTIONS"):
            env.pop(option, None)
        env["JAVA_TOOL_OPTIONS"] = "-XX:-UsePerfData"
        if "--version" in argv:
            return argv
        if "--headless" not in argv or "--path" not in argv:
            guard.reject("step6_native_godot_command_not_approved")
        position = argv.index("--path") + 1
        source = (cwd / argv[position]).resolve()
        if source not in {PROJECT_ROOT / "game", root / "game"}:
            guard.reject("step6_native_godot_project_not_approved")
        argv[position] = str(root / "game")
        if any(flag.startswith("--export") for flag in argv):
            guard.reject("step6_native_godot_export_not_approved")
        if "--log-file" not in argv:
            argv[1:1] = ["--log-file", "NUL"]
        return argv
    if name in {"uv", "uv.exe"} and argv[1:] == ["lock", "--check"]:
        if executable.is_absolute() and executable.resolve() != UV_EXE.resolve():
            guard.reject("step6_native_executable_mismatch")
        return [str(UV_EXE), *argv[1:]]
    ruff = Path(sys.executable).parent / "ruff.exe"
    if executable.is_absolute() and executable.resolve() == ruff.resolve():
        if "check" not in argv or "--fix" in argv:
            guard.reject("step6_native_ruff_command_not_approved")
        if "--no-cache" not in argv:
            argv.insert(2, "--no-cache")
        return argv
    guard.reject("step6_native_precreation_boundary_unavailable")


def resource_ledger_sources(active: Path) -> tuple[Path, ...]:
    """Select read dependencies without binding a writer or touching future batches."""
    if active != batch_ledger_path(active.parent):
        raise RuntimeError("step6_machine_ledger_path_mismatch")
    prerequisite = (
        (batch_ledger_path(CURRENT_TOOL_READINESS_ROOT),)
        if active.parent == NATIVE_QUALITY_ROOT
        else ()
    )
    return (*HISTORICAL_LEDGERS, *prerequisite, CURRENT_TASK, active)


def require_ledger_sources(sources: tuple[Path, ...]) -> None:
    """Required history must exist; never filter out a missing source."""
    for source in sources:
        if not source.is_file():
            raise RuntimeError("step6_resource_ledger_missing")


def registered_resource_paths(sources: tuple[Path, ...] | None = None) -> set[str]:
    """Stream the immutable historical ledger and the compact current ledger."""
    registrations: set[str] = set()
    pattern = re.compile(r"Step6 resource pre-registration: " + chr(96) + r"(\{[^\n]+\})")
    if sources is None:
        sources = resource_ledger_sources(machine_ledger().path)
    for source in sources:
        require_ledger_sources((source,))
        with source.open("r", encoding="utf-8") as stream:
            for line in stream:
                match = pattern.search(line)
                if match:
                    registrations.add(json.loads(match[1])["path"])
    return registrations


def native_inventory(root: Path, watcher: NativeWatcher, prepared: set[str]) -> dict[str, Any]:
    registrations = set(prepared)
    registrations.update(registered_resource_paths())
    files = []
    paths = set()
    for path in root.rglob("*"):
        validate_path(path)
        key = str(path)
        paths.add(key)
        category = native_category(root, path)
        if key not in registrations and (not category or key not in watcher.seen):
            raise RuntimeError("step6_native_final_path_without_registration_or_event")
        if path.is_file():
            status = path.stat()
            files.append(
                {
                    "path": key,
                    "category": category or "python_preregistered",
                    "bytes": status.st_size,
                    "device": status.st_dev,
                    "file_id": status.st_ino,
                    "hardlinks": status.st_nlink,
                }
            )
    unexplained = watcher.seen - registrations - set(watcher.native)
    if unexplained:
        raise RuntimeError("step6_native_transient_path_not_approved")
    return {
        "files": files,
        "file_count": len(files),
        "bytes": sum(item["bytes"] for item in files),
        "event_count": watcher.event_count,
        "native_events": watcher.native,
        "retired_sqlite_sidecars": watcher.retired_sqlite_sidecars,
        "retired_uv_notifications": watcher.retired_uv_notifications,
        "renamed_notifications": watcher.renamed_notifications,
        "transient_native_paths": sorted(set(watcher.native) - paths),
        "unknown_paths": [],
        "reparse": 0,
        "overflow": False,
        "mode": "approved_directory_category_preregistration_runtime_observation_final_inventory",
    }


def copy_game_for_native(root: Path, guard: ResourceGuard) -> dict[str, str]:
    import hashlib
    import subprocess

    environment = dict(os.environ)
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="NUL", GIT_OPTIONAL_LOCKS="0")
    listed = subprocess.check_output(
        [
            str(GIT_EXE),
            "-C",
            str(PROJECT_ROOT),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "game",
        ],
        env=environment,
    )
    hashes = {}
    for raw in sorted(set(listed.split(b"\0")) - {b""}):
        relative = Path(os.fsdecode(raw))
        source = PROJECT_ROOT / relative
        destination = validate_path(root / relative)
        for directory in reversed((destination.parent, *destination.parent.parents)):
            if directory.is_relative_to(root) and not directory.exists():
                guard.register(directory, "frozen_game_copy_directory")
                directory.mkdir()
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        guard.register(destination, "hash_verified_frozen_game_resource")
        with destination.open("xb") as stream:
            stream.write(data)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise RuntimeError("step6_native_game_copy_hash_mismatch")
        hashes[str(relative)] = digest
    return hashes


@contextmanager
def native_session(root: Path, guard: ResourceGuard) -> Iterator[NativeWatcher]:
    from unittest.mock import patch

    require_native_quality_boundary(guard, root)
    prepare_quality_resources(root, guard)
    hashes = (
        {}
        if root in {PREVIOUS_STARTUP_ROOT, *IDENTITY_VALIDATION_ROOTS}
        else copy_game_for_native(root, guard)
    )
    prepared = set(guard.registered)
    watcher = NativeWatcher(root, prepared)
    ready = root / "native-monitor-ready.json"
    guard.register(ready, "metadata_native_monitor_ownership")
    ready.write_text(json.dumps({"root": str(root), "pid": os.getpid()}), encoding="utf-8")
    previous_temp = tempfile.tempdir
    previous_path = list(sys.path)
    environment = dict(os.environ)
    environment.update(F009_NATIVE_ROOT=str(root), F009_NATIVE_PID=str(os.getpid()))
    guard.native_root = root
    sys.addaudithook(guard.audit)
    guard.active = True
    error: BaseException | None = None
    drain_attempted = False
    drain_completed = False
    try:
        with patch.dict(os.environ, environment, clear=True):
            configure_environment()
            yield watcher
            drain_attempted = True
            watcher.drain(guard)
            drain_completed = True
    except BaseException as problem:
        error = problem
        raise
    finally:
        try:
            finish_native_session(
                root,
                guard,
                watcher,
                prepared,
                hashes,
                error,
                drain_attempted=drain_attempted,
                drain_completed=drain_completed,
            )
        finally:
            guard.active = False
            guard.native_root = None
            tempfile.tempdir = previous_temp
            sys.path[:] = previous_path


def finish_native_session(
    root: Path,
    guard: ResourceGuard,
    watcher: NativeWatcher,
    prepared: set[str],
    hashes: dict[str, str],
    error: BaseException | None,
    *,
    drain_attempted: bool = False,
    drain_completed: bool = False,
) -> None:
    """Release once, preserve the primary failure, and never certify an incomplete watch."""
    import hashlib

    primary = error
    drain_error = error if drain_attempted and not drain_completed else None
    close_error: BaseException | None = None
    try:
        if watcher.error is None and not drain_attempted:
            if not (root / "native-monitor-drain.marker").exists():
                watcher.drain(guard)
            drain_completed = True
    except BaseException as problem:
        drain_error = problem
        primary = primary or problem
    try:
        watcher.close()
    except BaseException as problem:
        close_error = problem
        primary = primary or problem
    inventory: dict[str, Any] = {}
    if primary is None:
        try:
            inventory = native_inventory(root, watcher, prepared)
            for relative, digest in hashes.items():
                if hashlib.sha256((root / relative).read_bytes()).hexdigest() != digest:
                    raise RuntimeError("step6_native_game_copy_changed")
                if hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest() != digest:
                    raise RuntimeError("step6_native_game_source_changed")
            inventory.update(game_hashes=hashes, completed=True)
        except BaseException as problem:
            primary = problem
    if primary is not None:
        inventory = {
            "completed": False,
            "observation_complete": False,
            "inventory_complete": False,
            "overflow": True if watcher.error == "step6_native_watch_overflow" else None,
            "unknown_paths": None,
            "primary_error": native_error_code(primary),
            "drain_error": native_error_code(drain_error),
            "close_error": native_error_code(close_error),
            "drain_completed": drain_completed,
            "close_returned": close_error is None,
            "failure": native_failure_details(watcher),
            "mode": "incomplete_native_observation_not_acceptance",
        }
    try:
        output = root / "native-summary.json"
        guard.register(output, "metadata_native_inventory")
        payload = json.dumps(inventory, indent=2, sort_keys=True)
        if len(payload.encode("utf-8")) > (64 * 1024 if primary is not None else 8 * 1024**2):
            raise RuntimeError("step6_native_failure_report_limit")
        if root in BATCH_LIMITS:
            size = len(payload.encode("utf-8"))
            require_batch_capacity(
                root,
                size + sum(path.stat().st_size for path in root.rglob("*") if path.is_file()),
                size
                + sum(path.stat().st_size for path in RECOVERY_ROOT.rglob("*") if path.is_file()),
            )
        with output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
        if root in IDENTITY_VALIDATION_ROOTS:
            require_identity_capacity(root)
    except BaseException as problem:
        primary = primary or problem
        native_report_unavailable(primary)
    if primary is not None:
        raise primary


def native_report_unavailable(primary: BaseException) -> None:
    """A fixed stderr notice is not an alternate evidence file or a successful report."""
    primary.add_note("step6_native_failure_report_unavailable")
    try:
        print(
            '{"evidence_complete":false,"code":"step6_native_failure_report_unavailable"}',
            file=sys.__stderr__,
            flush=True,
        )
    except Exception:
        primary.add_note("step6_native_failure_notice_unavailable")


def prepare_quality_resources(root: Path, guard: ResourceGuard) -> None:
    root = validate_path(root)
    if root.exists():
        raise RuntimeError("step6_quality_root_not_fresh")
    if root in BATCH_LIMITS:
        # The two bootstrap operations have exact prior registrations in the task card.
        ledger_path = batch_ledger_path(root)
        required = {str(root), str(ledger_path)}
        lines = bootstrap_registrations(root)
        validate_path(ledger_path)
        root.mkdir()
        with ledger_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(lines) + "\n")
            stream.flush()
        machine_ledger(root)
        guard.registered.update(required)
    for path in (
        root,
        root / "tmp",
        root / "cache",
        root / "cache/mypy",
        root / "cache/uv",
        root / "appdata",
        root / "localappdata",
        root / "git-template",
        root / "git-template/info",
        root / "appdata/Godot",
        root / "appdata/Godot/app_userdata",
        root / "appdata/Godot/app_userdata/Cyber Town Connectivity",
    ):
        if path == root and root in BATCH_LIMITS:
            continue
        guard.register(path, "synthetic_quality_directory_or_native_tool_cache")
        path.mkdir()
    exclude = root / "git-template/info/exclude"
    guard.register(exclude, "synthetic_git_template")
    exclude.write_text("# Synthetic QA template; no ignore rules.\n", encoding="utf-8")
    for relative in ("cache/uv/CACHEDIR.TAG", "cache/uv/.gitignore", "cache/uv/.lock"):
        guard.register(root / relative, "fixed_native_uv_cache_metadata")


def stop_owned_tree(process: Any) -> None:
    """Stop only the still-running child and its current descendants after a QA fault."""
    import ctypes
    from ctypes import wintypes as w

    if process.poll() is not None:
        return

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("size", w.DWORD),
            ("usage", w.DWORD),
            ("pid", w.DWORD),
            ("heap", ctypes.c_size_t),
            ("module", w.DWORD),
            ("threads", w.DWORD),
            ("parent", w.DWORD),
            ("priority", w.LONG),
            ("flags", w.DWORD),
            ("executable", w.WCHAR * 260),
        ]

    kernel = kernel_api()
    kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    for name in ("Process32FirstW", "Process32NextW"):
        getattr(kernel, name).argtypes = [w.HANDLE, ctypes.POINTER(ProcessEntry)]
        getattr(kernel, name).restype = w.BOOL
    kernel.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
    kernel.TerminateProcess.restype = w.BOOL
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        process.terminate()
        process.wait(timeout=10)
        raise RuntimeError("step6_owned_tree_snapshot_failed")
    parents = {}
    entry = ProcessEntry()
    entry.size = ctypes.sizeof(entry)
    try:
        available = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while available:
            parents[entry.pid] = entry.parent
            available = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    owned = [process.pid]
    for pid in owned:
        owned.extend(
            child for child, parent in parents.items() if parent == pid and child not in owned
        )
    for pid in reversed(owned):
        handle = kernel.OpenProcess(1 | 0x100000, False, pid)
        if handle:
            try:
                kernel.TerminateProcess(handle, 2)
                kernel.WaitForSingleObject(handle, 10000)
            finally:
                kernel.CloseHandle(handle)
    process.wait(timeout=10)


def run_observed(
    command: list[str],
    watcher: NativeWatcher,
    *,
    cwd: Path = PROJECT_ROOT,
    status: dict[str, object] | None = None,
) -> tuple[int, str, str]:
    import subprocess

    state = status if status is not None else {}
    state.update(
        state="not_started",
        pid=None,
        exit_code=None,
        exit_code_source="unknown",
        cleanup_attempted=False,
        cleanup_error=None,
        primary_error=None,
    )
    watcher.check()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    state.update(state="started", pid=process.pid)
    primary: BaseException | None = None
    try:
        while True:
            watcher.check()
            try:
                stdout, stderr = process.communicate(timeout=0.5)
                watcher.check()
                state.update(
                    state="completed",
                    exit_code=process.returncode,
                    exit_code_source="held_popen_returncode",
                )
                return process.returncode, stdout, stderr
            except subprocess.TimeoutExpired:
                continue
    except BaseException as problem:
        primary = problem
        state.update(
            state="interrupted", primary_error=native_error_code(problem), cleanup_attempted=True
        )
        try:
            stop_owned_tree(process)
        except BaseException as cleanup:
            state["cleanup_error"] = native_error_code(cleanup)
            primary.add_note("step6_native_command_cleanup_failed")
        finally:
            if type(process.returncode) is int:
                state.update(
                    exit_code=process.returncode,
                    exit_code_source="held_popen_returncode_after_cleanup",
                )
        raise
    finally:
        close_errors = []
        for pipe in (process.stdout, process.stderr):
            if pipe:
                try:
                    pipe.close()
                except BaseException as problem:
                    close_errors.append(problem)
        state["pipe_close_errors"] = [native_error_code(problem) for problem in close_errors]
        if close_errors:
            if primary is None:
                raise close_errors[0]
            primary.add_note("step6_native_command_pipe_close_failed")


def run_native_probe() -> int:
    root = NATIVE_PROBE_ROOT
    guard = ResourceGuard()
    commands: list[dict[str, object]] = []
    with native_session(root, guard) as watcher, subprocess_isolation(guard):
        fixture = root / "git-fixture"
        fixture.mkdir()
        (fixture / "fixture.txt").write_text("synthetic native resource probe", encoding="utf-8")
        matrix = [
            ("git-init", [str(GIT_EXE), "init", "--quiet"], fixture),
            ("git-add", [str(GIT_EXE), "add", "fixture.txt"], fixture),
            ("git-hash", [str(GIT_EXE), "hash-object", "-w", "fixture.txt"], fixture),
            ("git-index", [str(GIT_EXE), "ls-files", "--stage"], fixture),
            ("lock", [str(UV_EXE), "lock", "--check"], PROJECT_ROOT),
            (
                "ruff",
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    "scripts/f009_step6_qa.py",
                    "backend/tests/test_f009_step6_qa.py",
                ],
                PROJECT_ROOT,
            ),
            (
                "godot-import",
                [str(GODOT_EXE), "--headless", "--editor", "--path", "game", "--quit"],
                PROJECT_ROOT,
            ),
            (
                "godot-unit",
                [
                    str(GODOT_EXE),
                    "--headless",
                    "--path",
                    "game",
                    "--script",
                    "res://tests/run_tests.gd",
                ],
                PROJECT_ROOT,
            ),
        ]
        try:
            for label, argv, cwd in matrix:
                print(json.dumps({"starting": label}), flush=True)
                code, stdout, stderr = run_observed(argv, watcher, cwd=cwd)
                item = {
                    "label": label,
                    "exit_code": code,
                    "raw_output_retained": False,
                    "error_classes": sorted(set(re.findall(r"^([A-Za-z]+Error):", stderr, re.M))),
                }
                commands.append(item)
                print(json.dumps(item), flush=True)
                if code:
                    raise RuntimeError("step6_native_probe_command_failed")
                if label == "git-index" and "fixture.txt" not in stdout:
                    raise RuntimeError("step6_native_git_index_missing")
                if label == "git-hash":
                    blob = stdout.strip()
                    if not re.fullmatch(r"[0-9a-f]{40}", blob):
                        raise RuntimeError("step6_native_git_blob_invalid")
                    update_code, _, _ = run_observed(
                        [
                            str(GIT_EXE),
                            "update-index",
                            "--add",
                            "--cacheinfo",
                            f"100644,{blob},fixture-alias.txt",
                        ],
                        watcher,
                        cwd=fixture,
                    )
                    commands.append({"label": "git-update-index", "exit_code": update_code})
                    if update_code:
                        raise RuntimeError("step6_native_git_update_failed")
        finally:
            output = root / "probe-summary.json"
            with output.open("x", encoding="utf-8") as stream:
                json.dump({"commands": commands, "raw_output_retained": False}, stream, indent=2)
    return 0


def connectivity_diagnostics(stdout: str, stderr: str) -> dict[str, object]:
    """Keep only known scenario names and failure categories, never raw messages."""
    scenarios = (
        "connected",
        "unavailable",
        "duplicate_rejected",
        "non_string_rejected",
        "redirect_rejected",
        "stopped_service",
        "http_error_recovery",
        "invalid_recovery",
        "timeout_recovery",
    )
    passed: set[str] = set()
    failed: set[str] = set()
    categories: set[str] = set()
    runner_failure = False
    godot_categories = {
        "unknown or missing --scenario value:": "unknown_scenario",
        "main scene could not be loaded": "scene_load",
        "scenario exceeded 15-second safety deadline": "scenario_deadline",
        "state sequence mismatch": "state_sequence",
        "status text mismatch": "status_text",
        "Retry must be visible and enabled": "retry_availability",
        "Retry policy mismatch": "retry_policy",
        "Retry must be hidden after connection succeeds": "retry_visibility",
    }
    for line in (stdout + "\n" + stderr).splitlines():
        for scenario in scenarios:
            if line.startswith(f"Godot integration scenario passed: {scenario} -> "):
                passed.add(scenario)
            prefix = f"Godot integration scenario failed ({scenario}): "
            if line.startswith(prefix):
                failed.add(scenario)
                message = line[len(prefix) :]
                categories.update(
                    "godot_" + category
                    for marker, category in godot_categories.items()
                    if message.startswith(marker)
                )
        prefix = "Connectivity integration failed: "
        if not line.startswith(prefix):
            continue
        runner_failure = True
        message = line[len(prefix) :]
        patterns = {
            "loopback_busy": (
                r"(?:integration requires a free|refusing to replace existing listener on) "
                r"127\.0\.0\.1:800[01]"
            ),
            "port_open_timeout": r"127\.0\.0\.1:800[01] did not become open",
            "port_release_timeout": r"127\.0\.0\.1:800[01] did not become released",
            "readiness_response": r"unexpected FastAPI readiness response: .*",
            "fixture_shutdown": r"fixture server did not stop for mode [a-z_]+",
            "request_count": (
                r"[a-z_]+ expected exactly (?:one|two)(?: source)? requests?, got [0-9]+"
            ),
            "redirect_followed": r"redirect target must not be requested",
            "listener_left_running": r"integration left a loopback listener running",
            "subprocess_nonzero": r"Command .+ returned non-zero exit status -?[0-9]+\.",
            "qa_boundary": r"step6_[a-z_]+",
        }
        categories.update(
            "runner_" + category
            for category, pattern in patterns.items()
            if re.fullmatch(pattern, message)
        )
    return {
        "passed_scenario_markers": sorted(passed),
        "failed_scenario_markers": sorted(failed),
        "failure_categories": sorted(categories),
        "runner_failure_marker": runner_failure,
        "raw_output_retained": False,
    }


def run_quality_acceptance(batch: str = "recovery-20260905-01/native-quality-10") -> int:
    """Run the original quality command set with the approved native observer."""
    guard = ResourceGuard()
    root = validate_path(QA_ROOT / batch)
    require_native_quality_boundary(guard, root)
    if root != NATIVE_QUALITY_ROOT:
        guard.reject("step6_native_precreation_boundary_unavailable")
    readiness_receipt = read_current_readiness_receipt()
    probe = NATIVE_PROBE_ROOT
    if not (probe / "native-summary.json").is_file():
        guard.reject("step6_native_probe_not_complete")
    inventory = json.loads((probe / "native-summary.json").read_text(encoding="utf-8"))
    outcomes = json.loads((probe / "probe-summary.json").read_text(encoding="utf-8"))
    required = {
        "git-init",
        "git-add",
        "git-hash",
        "git-update-index",
        "git-index",
        "lock",
        "ruff",
        "godot-import",
        "godot-unit",
    }
    completed = {item["label"] for item in outcomes["commands"] if item["exit_code"] == 0}
    if inventory.get("completed") is not True or completed != required:
        guard.reject("step6_native_probe_not_complete")
    configure_environment()
    import cyber_town.quality as quality

    commands: list[dict[str, object]] = []
    original_command = quality._run_command
    code = 1
    failure: BaseException | None = None
    try:
        with native_session(root, guard) as watcher, subprocess_isolation(guard):
            guard.register(root / "quality-summary.json", "synthetic_test_or_metadata_file")

            def launch(label: str, command: Any, root: Path) -> None:
                argv = list(command)
                if label == "pytest":
                    argv = [
                        sys.executable,
                        "-B",
                        str(PROJECT_ROOT / "scripts/f009_step6_qa.py"),
                        "--batch",
                        batch + "/pytest",
                        "--output",
                        batch + "/pytest-summary.json",
                        "backend/tests",
                    ]
                state: dict[str, object] = {}
                item: dict[str, object] = {
                    "label": label,
                    "argv": argv,
                    "cwd": str(root),
                    "exit_code": None,
                    "raw_output_retained": False,
                    "execution": state,
                    "boundary_codes": None,
                    "error_classes": None,
                }
                commands.append(item)
                print(json.dumps({"starting": label}), flush=True)
                try:
                    result, stdout, stderr = run_observed(argv, watcher, cwd=root, status=state)
                except BaseException as problem:
                    item["failure_code"] = native_error_code(problem)
                    raise
                item.update(
                    exit_code=result,
                    boundary_codes=sorted(
                        set(re.findall(r"^RuntimeError: (step6_[a-z_]+)$", stderr, re.M))
                    ),
                    error_classes=sorted(set(re.findall(r"^([A-Za-z]+Error):", stderr, re.M))),
                )
                if label == "connectivity":
                    item["diagnostics"] = connectivity_diagnostics(stdout, stderr)
                print(json.dumps(item, sort_keys=True), flush=True)
                if result:
                    raise quality.QualityCheckError(label + " failed; raw output not retained")

            quality._run_command = launch
            try:
                code = quality.main()
            finally:
                quality._run_command = original_command
    except BaseException as problem:
        failure = problem
        code = 1
        raise
    finally:
        try:
            output = root / "quality-summary.json"
            guard.register(output, "synthetic_test_or_metadata_file")
            payload = json.dumps(
                {
                    "exit_code": code,
                    "completed": code == 0 and failure is None,
                    "failure_code": native_error_code(failure),
                    "commands": commands,
                    "readiness_receipt": readiness_receipt,
                    "raw_output_retained": False,
                },
                sort_keys=True,
                indent=2,
            )
            if len(payload.encode("utf-8")) > 1024**2:
                raise RuntimeError("step6_native_failure_report_limit")
            if root in BATCH_LIMITS:
                size = len(payload.encode("utf-8"))
                require_batch_capacity(
                    root,
                    size + sum(path.stat().st_size for path in root.rglob("*") if path.is_file()),
                    size
                    + sum(
                        path.stat().st_size for path in RECOVERY_ROOT.rglob("*") if path.is_file()
                    ),
                )
            with output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        except BaseException:
            if failure is None:
                raise
            native_report_unavailable(failure)
    return code


def require_native_quality_boundary(guard: ResourceGuard, root: Path | None = None) -> None:
    """Accept only the explicitly approved fresh recovery batches."""
    if root not in NATIVE_ROOTS:
        guard.reject("step6_native_precreation_boundary_unavailable")
    if root is None or root.exists():
        guard.reject("step6_quality_root_not_fresh")
    validate_path(root)


def static_commands() -> list[list[str]]:
    executable = str(Path(sys.executable).parent / "ruff.exe")
    sources = [
        str(PROJECT_ROOT / "scripts/f009_step6_qa.py"),
        str(PROJECT_ROOT / "backend/tests/test_f009_step6_qa.py"),
    ]
    return [
        [executable, "check", "--no-cache", *sources],
        [executable, "format", "--check", "--no-cache", *sources],
    ]


def protected_cache_metadata() -> dict[str, tuple[int, int, int, int]]:
    result = {}
    for project in (PROJECT_ROOT, FORMAL_PROJECT_ROOT):
        for name in (".ruff_cache", ".mypy_cache", ".pytest_cache"):
            root = project / name
            if not root.exists():
                continue
            for path in (root, *root.rglob("*")):
                status = path.lstat()
                if status.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise RuntimeError("step6_protected_cache_reparse")
                result[str(path)] = (
                    status.st_dev,
                    status.st_ino,
                    status.st_size,
                    status.st_mtime_ns,
                )
    return result


def run_static_checks() -> int:
    import subprocess

    before = protected_cache_metadata()
    guard = ResourceGuard()
    sys.addaudithook(guard.audit)
    guard.active = True
    outcomes = []
    try:
        with subprocess_isolation(guard):
            for command in static_commands():
                result = subprocess.run(
                    command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
                )
                outcomes.append({"check": command[1], "exit_code": result.returncode})
                if result.returncode:
                    # Ruff diagnostics refer only to the two approved QA source files.
                    print(result.stdout)
                    print(result.stderr)
                    break
        after = protected_cache_metadata()
        if before != after:
            guard.reject("step6_protected_cache_changed")
        metadata = {
            "checks": outcomes,
            "protected_cache_entries": len(before),
            "protected_cache_unchanged": True,
            "boundary_violations": dict(guard.violations),
        }
        guard.record("unified static checks", json.dumps(metadata))
        print(json.dumps(metadata), flush=True)
        return int(any(item["exit_code"] for item in outcomes))
    finally:
        guard.active = False


SPACE_ROOT = QA_ROOT / "control-space-v1"
SPACE_MIGRATION_NAME = "0009_provider_permit_scope_storage.sql"
SPACE_SCOPE_COLUMNS = ("player_scope_tag", "player_npc_scope_tag", "conversation_scope_tag")
SPACE_SEEDS = tuple(f"F009-permit-layout-{index:02}" for index in range(1, 4))
SPACE_SCHEDULES = ("serial", "fifo", "lifo", "recovery")
SPACE_PYTHON_SOURCES = (
    "scripts/f009_step6_qa.py",
    "backend/tests/test_f009_step6_qa.py",
    "backend/src/cyber_town/infrastructure/control/sqlite_control.py",
    "backend/tests/test_sqlite_control.py",
    "backend/tests/test_budget_control_step3.py",
    "backend/tests/test_retry_breaker_step4.py",
)
SPACE_DRAFT_SQL = """-- Append-only v9: lossless full permit scopes; transactional rebuild.
CREATE TABLE v9_provider_permits (
    execution_id TEXT PRIMARY KEY
        REFERENCES execution_admissions(execution_id) ON DELETE RESTRICT,
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-safety-control-v1'),
    player_scope_tag BLOB NOT NULL CHECK (
        typeof(player_scope_tag) = 'blob' AND length(player_scope_tag) = 32
    ),
    player_npc_scope_tag BLOB NOT NULL CHECK (
        typeof(player_npc_scope_tag) = 'blob' AND length(player_npc_scope_tag) = 32
    ),
    conversation_scope_tag BLOB NOT NULL CHECK (
        typeof(conversation_scope_tag) = 'blob' AND length(conversation_scope_tag) = 32
    ),
    acquired_at_ns INTEGER NOT NULL CHECK (acquired_at_ns > 0),
    released_at_ns INTEGER CHECK (
        released_at_ns IS NULL OR released_at_ns >= acquired_at_ns
    ),
    release_reason TEXT CHECK (
        release_reason IS NULL OR release_reason IN (
            'completed', 'cancelled', 'failed', 'control_failure',
            'abandoned_after_restart'
        )
    ),
    CHECK (
        (released_at_ns IS NULL AND release_reason IS NULL)
        OR (released_at_ns IS NOT NULL AND release_reason IS NOT NULL)
    )
) STRICT, WITHOUT ROWID;

INSERT INTO v9_provider_permits (
    execution_id, policy_version, player_scope_tag, player_npc_scope_tag,
    conversation_scope_tag, acquired_at_ns, released_at_ns, release_reason
)
SELECT execution_id, policy_version,
    CASE WHEN typeof(player_scope_tag) = 'text'
          AND length(player_scope_tag) = 64
          AND player_scope_tag NOT GLOB '*[^0-9a-f]*'
         THEN unhex(player_scope_tag) ELSE NULL END,
    CASE WHEN typeof(player_npc_scope_tag) = 'text'
          AND length(player_npc_scope_tag) = 64
          AND player_npc_scope_tag NOT GLOB '*[^0-9a-f]*'
         THEN unhex(player_npc_scope_tag) ELSE NULL END,
    CASE WHEN typeof(conversation_scope_tag) = 'text'
          AND length(conversation_scope_tag) = 64
          AND conversation_scope_tag NOT GLOB '*[^0-9a-f]*'
         THEN unhex(conversation_scope_tag) ELSE NULL END,
    acquired_at_ns, released_at_ns, release_reason
FROM provider_permits;

DROP TABLE provider_permits;
ALTER TABLE v9_provider_permits RENAME TO provider_permits;

CREATE INDEX provider_permits_active_conversation_idx
ON provider_permits (conversation_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_player_idx
ON provider_permits (player_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_player_npc_idx
ON provider_permits (player_npc_scope_tag) WHERE released_at_ns IS NULL;

PRAGMA user_version = 9;
"""


def space_require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError("step6_space_" + code)


def space_format_commands() -> list[list[str]]:
    """Read-only stdin formatting for approved Python sources; no native files."""
    return [
        [
            str(Path(sys.executable).parent / "ruff.exe"),
            "format",
            "--no-cache",
            "--stdin-filename",
            str(PROJECT_ROOT / name),
        ]
        for name in SPACE_PYTHON_SOURCES
    ]


def space_static_commands() -> list[list[str]]:
    executable = str(Path(sys.executable).parent / "ruff.exe")
    sources = [str(PROJECT_ROOT / name) for name in SPACE_PYTHON_SOURCES]
    return [
        [executable, "check", "--no-cache", *sources],
        [executable, "format", "--check", "--no-cache", *sources],
    ]


def space_events(seed: str, schedule: str) -> list[tuple[str, int, int]]:
    """A fixed lifecycle plan, independent of observed database size."""
    space_require(seed in SPACE_SEEDS and schedule in SPACE_SCHEDULES, "invalid_plan")
    events: list[tuple[str, int, int]] = []
    for first in range(0, 100, 2):
        if schedule == "serial":
            operations = [
                ("acquire", first),
                ("release", first),
                ("acquire", first + 1),
                ("release", first + 1),
            ]
        else:
            operations = [("acquire", first), ("acquire", first + 1)]
            if schedule == "recovery":
                operations += [("recover", first)]
            else:
                order = (first, first + 1) if schedule == "fifo" else (first + 1, first)
                operations += [("release", index) for index in order]
        for operation, index in operations:
            events.append((operation, index, 1_000_000_000 + len(events) * 1_000_000))
    return events


def space_record(seed: str, index: int) -> tuple[str, str, tuple[str, str, str]]:
    """Deterministic UUIDv4-shaped IDs and full synthetic HMAC scopes."""
    import hashlib
    import hmac
    from uuid import UUID

    space_require(seed in SPACE_SEEDS and 0 <= index < 100, "invalid_record")
    ids = tuple(
        str(UUID(bytes=hashlib.sha256(f"{seed}/{kind}/{index}".encode()).digest()[:16], version=4))
        for kind in ("execution", "request")
    )
    scopes = tuple(
        hmac.new(b"synthetic-f009-permit-layout", f"{seed}/{kind}".encode(), "sha256").hexdigest()
        for kind in ("player", f"npc/{index % 2}", f"conversation/{index % 2}")
    )
    return ids[0], ids[1], (scopes[0], scopes[1], scopes[2])


def space_encode_scope(value: object) -> bytes:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("step6_space_invalid_scope")
    return bytes.fromhex(value)


def space_plan() -> dict[str, Any]:
    import hashlib

    paths = {SPACE_ROOT, SPACE_ROOT / "layout"}
    for name in ("pytest-layout-01", "pytest-semantic-01"):
        paths.add(SPACE_ROOT / name)
    for name in (
        "layout-plan.json",
        "layout-summary.json",
        "semantic-summary.json",
        "evaluator-process-01.json",
        "evaluator-process-02.json",
        "evaluator-process-03.json",
        "pytest-layout-01/qa-summary.json",
    ):
        paths.add(SPACE_ROOT / name)
    cases = []
    for number, seed in enumerate(SPACE_SEEDS, 1):
        for schedule in SPACE_SCHEDULES:
            case_root = SPACE_ROOT / "layout" / f"seed-{number:02}" / schedule
            cases.append(
                {
                    "seed": seed,
                    "schedule": schedule,
                    "executions": 100,
                    "input_digest": hashlib.sha256(
                        json.dumps(
                            {
                                "records": [space_record(seed, i) for i in range(100)],
                                "events": space_events(seed, schedule),
                            },
                            sort_keys=True,
                        ).encode()
                    ).hexdigest(),
                }
            )
            paths.update((case_root.parent, case_root))
            for variant in ("baseline", "candidate"):
                directory = case_root / variant
                paths.add(directory)
                for suffix in ("", "-wal", "-shm", "-journal"):
                    paths.add(directory / ("control.sqlite3" + suffix))
    return {
        "schema_version": 1,
        "task": "F009-Step6-SPACE-01-A",
        "root": str(SPACE_ROOT),
        "cases": cases,
        "minimum_saving_bytes": 8192,
        "migration_sha256": hashlib.sha256(SPACE_DRAFT_SQL.encode()).hexdigest(),
        "paths": [str(path) for path in sorted(paths)],
        "raw_values_retained": False,
    }


def space_new_v8(path: Path) -> Any:
    """Create only a fresh owned fixture from unchanged migrations 1 through 8."""
    import hashlib
    import sqlite3

    from cyber_town.infrastructure.control import sqlite_control as control

    path = validate_path(path)
    space_require(path.is_relative_to(SPACE_ROOT), "fixture_outside_specialist_root")
    for suffix in ("", "-wal", "-shm", "-journal"):
        space_require(not os.path.lexists(str(path) + suffix), "fixture_not_fresh")
    connection = sqlite3.connect(path, isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY CHECK(version>0),"
            "name TEXT NOT NULL UNIQUE, checksum TEXT NOT NULL CHECK(length(checksum)=64),"
            "applied_at_ns INTEGER NOT NULL CHECK(applied_at_ns>0)) STRICT"
        )
        for version, name in control.CONTROL_MIGRATIONS[:8]:
            raw = (Path(control.__file__).parent / "migrations" / name).read_bytes()
            for statement in control.SqliteSafetyControlRepository._migration_statements(
                raw.decode()
            ):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?,?,?,?)",
                (version, name, hashlib.sha256(raw).hexdigest(), 1),
            )
        space_require(connection.execute("PRAGMA user_version").fetchone() == (8,), "v8_fixture")
        connection.commit()
    except BaseException:
        connection.rollback()
        connection.close()
        raise
    return connection


def space_apply_candidate(connection: Any, *, fail_after: int | None = None) -> None:
    """Exercise the exact candidate statements, including transactional ledger append."""
    import hashlib
    import sqlite3

    from cyber_town.infrastructure.control import sqlite_control as control

    space_require(
        connection.execute("SELECT typeof(unhex('00ff')),length(unhex('00ff'))").fetchone()
        == ("blob", 2),
        "unhex_unavailable",
    )
    space_require(connection.execute("PRAGMA user_version").fetchone() == (8,), "migration_version")
    expected = [
        (
            version,
            name,
            hashlib.sha256(
                (Path(control.__file__).parent / "migrations" / name).read_bytes()
            ).hexdigest(),
        )
        for version, name in control.CONTROL_MIGRATIONS[:8]
    ]
    space_require(
        connection.execute(
            "SELECT version,name,checksum FROM schema_migrations ORDER BY version"
        ).fetchall()
        == expected,
        "migration_prefix",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        statements = control.SqliteSafetyControlRepository._migration_statements(SPACE_DRAFT_SQL)
        count = 0
        for count, statement in enumerate(statements, 1):
            connection.execute(statement)
            if fail_after == count:
                raise sqlite3.OperationalError("synthetic_space_migration_fault")
        connection.execute(
            "INSERT INTO schema_migrations VALUES (?,?,?,?)",
            (9, SPACE_MIGRATION_NAME, hashlib.sha256(SPACE_DRAFT_SQL.encode()).hexdigest(), 9),
        )
        if fail_after == count + 1:
            raise sqlite3.OperationalError("synthetic_space_migration_fault")
        space_require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "migration_fk")
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def space_insert(connection: Any, seed: str, index: int, now: int, *, candidate: bool) -> None:
    execution, request_id, scopes = space_record(seed, index)
    connection.execute(
        "INSERT INTO execution_admissions VALUES (?,?,?,?,?,?,?)",
        (execution, request_id, "f-009-safety-control-v1", *scopes, now),
    )
    values = tuple(space_encode_scope(value) for value in scopes) if candidate else scopes
    connection.execute(
        "INSERT INTO provider_permits VALUES (?,?,?,?,?,?,NULL,NULL)",
        (execution, "f-009-safety-control-v1", *values, now),
    )


def space_logical_digest(connection: Any, *, candidate: bool) -> dict[str, Any]:
    """Hash every application column/row; normalize only the three permit scopes."""
    import hashlib

    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    contents = []
    counts = {}
    for table in tables:
        space_require(re.fullmatch(r"[a-z][a-z0-9_]*", table) is not None, "table_name")
        if table == "schema_migrations":
            continue
        cursor = connection.execute(f'SELECT * FROM "{table}"')
        columns = [item[0] for item in cursor.description]
        rows = []
        for original in cursor.fetchall():
            row = list(original)
            if table == "provider_permits":
                for column in SPACE_SCOPE_COLUMNS:
                    index = columns.index(column)
                    value = row[index]
                    if candidate:
                        space_require(isinstance(value, bytes) and len(value) == 32, "blob_scope")
                        row[index] = value.hex()
                    else:
                        space_encode_scope(value)
            rows.append(tuple(row))
        counts[table] = len(rows)
        contents.append((table, columns, sorted(rows, key=repr)))
    return {
        "digest": hashlib.sha256(repr(contents).encode()).hexdigest(),
        "row_counts": counts,
        "migration_rows": connection.execute(
            "SELECT version,name,checksum,applied_at_ns FROM schema_migrations ORDER BY version"
        ).fetchall(),
        "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
    }


def space_surface_sizes(path: Path) -> dict[str, int]:
    result = {}
    for name, suffix in (("main", ""), ("wal", "-wal"), ("shm", "-shm"), ("journal", "-journal")):
        surface = validate_path(Path(str(path) + suffix))
        result[name] = surface.stat().st_size if surface.exists() else 0
    return result


def space_snapshot(connection: Any, path: Path) -> dict[str, Any]:
    from scripts.f009_step5_storage_breakdown import analyze_image, catalog

    sizes_before = space_surface_sizes(path)
    checkpoint = connection.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
    space_require(checkpoint[0] == 0 and checkpoint[1] == checkpoint[2], "checkpoint_busy")
    space_require(connection.execute("PRAGMA integrity_check").fetchone() == ("ok",), "integrity")
    space_require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "foreign_keys")
    space_require(connection.execute("PRAGMA journal_mode").fetchone() == ("wal",), "wal")
    space_require(connection.execute("PRAGMA synchronous").fetchone() == (2,), "full")
    identity = path.stat()
    report = analyze_image(path.read_bytes(), catalog(connection))
    after = path.stat()
    space_require(
        (identity.st_dev, identity.st_ino, identity.st_size, identity.st_mtime_ns)
        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
        "snapshot_identity",
    )
    report.update(
        occupied_bytes=report["physical_bytes"] - report["freelist_bytes"],
        surfaces_before_checkpoint=sizes_before,
        surfaces_after_checkpoint=space_surface_sizes(path),
        identity=[identity.st_dev, identity.st_ino],
    )
    return report


def space_layout_variant(
    path: Path, seed: str, schedule: str, *, candidate: bool
) -> dict[str, Any]:
    from contextlib import closing

    with closing(space_new_v8(path)) as connection:
        initialized = space_snapshot(connection, path)
        migration_surfaces = None
        if candidate:
            space_apply_candidate(connection)
            migration_surfaces = space_surface_sizes(path)
        before = space_snapshot(connection, path)
        peak = space_surface_sizes(path)
        for operation, index, now in space_events(seed, schedule):
            connection.execute("BEGIN IMMEDIATE")
            try:
                if operation == "acquire":
                    space_insert(connection, seed, index, now, candidate=candidate)
                elif operation == "release":
                    connection.execute(
                        "UPDATE provider_permits SET released_at_ns=?,release_reason='completed' "
                        "WHERE execution_id=? AND released_at_ns IS NULL",
                        (now, space_record(seed, index)[0]),
                    )
                else:
                    connection.execute(
                        "UPDATE provider_permits SET released_at_ns=?,"
                        "release_reason='abandoned_after_restart' WHERE released_at_ns IS NULL",
                        (now,),
                    )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
            for name, size in space_surface_sizes(path).items():
                peak[name] = max(peak[name], size)
        logical = space_logical_digest(connection, candidate=candidate)
        after = space_snapshot(connection, path)
        space_require(
            initialized["identity"] == before["identity"] == after["identity"], "lifecycle_identity"
        )
        space_require(logical["row_counts"]["provider_permits"] == 100, "permit_count")
        space_require(
            connection.execute(
                "SELECT COUNT(*) FROM provider_permits WHERE released_at_ns IS NULL"
            ).fetchone()
            == (0,),
            "active_permits",
        )
        return {
            "initialized": initialized,
            "before": before,
            "after": after,
            "logical": logical,
            "growth_bytes": max(
                0,
                after["physical_bytes"] - before["physical_bytes"],
                after["occupied_bytes"] - before["occupied_bytes"],
            ),
            "peak_observed_surfaces": peak,
            "migration_surfaces": migration_surfaces,
        }


def run_space_prevalidation() -> int:
    """One fixed candidate batch. A failure never enables product implementation."""
    import hashlib

    plan = space_plan()
    for raw_path in plan["paths"]:
        path = validate_path(Path(raw_path))
        space_require(not os.path.lexists(path), "planned_resource_not_fresh")
    before_cache = protected_cache_metadata()
    guard = ResourceGuard()
    sys.addaudithook(guard.audit)
    guard.active = True
    result: dict[str, Any] = {
        "phase": "A",
        "cases": [],
        "passed": False,
        "product_modified": False,
        "plan_digest": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest(),
    }
    try:
        for raw_path in plan["paths"]:
            guard.register(Path(raw_path), "space_AB_registered_python_resource")
        SPACE_ROOT.mkdir()
        with (SPACE_ROOT / "layout-plan.json").open("x", encoding="utf-8") as stream:
            json.dump(plan, stream, sort_keys=True, indent=2)
        with subprocess_isolation(guard):
            code = run_pytest(
                ["backend/tests/test_f009_step6_qa.py", "-k", "space_candidate"],
                batch="control-space-v1/pytest-layout-01",
                output="control-space-v1/pytest-layout-01/qa-summary.json",
            )
            result["test_exit_code"] = code
            if code:
                result["failure_code"] = "candidate_tests_failed"
                return code
            for number, seed in enumerate(SPACE_SEEDS, 1):
                for schedule in SPACE_SCHEDULES:
                    case_root = SPACE_ROOT / "layout" / f"seed-{number:02}" / schedule
                    pair: dict[str, Any] = {"seed": seed, "schedule": schedule}
                    for variant in ("baseline", "candidate"):
                        directory = case_root / variant
                        directory.mkdir(parents=True)
                        pair[variant] = space_layout_variant(
                            directory / "control.sqlite3",
                            seed,
                            schedule,
                            candidate=variant == "candidate",
                        )
                    baseline, candidate = pair["baseline"], pair["candidate"]
                    left, right = baseline["logical"], candidate["logical"]
                    pair["logical_equal"] = (
                        left["digest"] == right["digest"]
                        and left["row_counts"] == right["row_counts"]
                        and left["migration_rows"] == right["migration_rows"][:8]
                        and (left["user_version"], right["user_version"]) == (8, 9)
                        and len(right["migration_rows"]) == 9
                        and right["migration_rows"][-1]
                        == (9, SPACE_MIGRATION_NAME, plan["migration_sha256"], 9)
                    )
                    pair["saving_bytes"] = (
                        baseline["after"]["occupied_bytes"] - candidate["after"]["occupied_bytes"]
                    )
                    result["cases"].append(pair)
                    space_require(pair["logical_equal"], "logical_mismatch")
                    space_require(
                        pair["saving_bytes"] >= plan["minimum_saving_bytes"], "margin_failed"
                    )
                    print(
                        json.dumps(
                            {
                                "seed": seed,
                                "schedule": schedule,
                                "saving_bytes": pair["saving_bytes"],
                                "logical_equal": True,
                            }
                        ),
                        flush=True,
                    )
        result["passed"] = True
        return 0
    except Exception as error:
        message = str(error)
        result["failure_code"] = (
            message
            if re.fullmatch(r"step6_space_[a-z_]+", message)
            else "candidate_exception_" + type(error).__name__
        )
        return 1
    finally:
        result["protected_cache_unchanged"] = before_cache == protected_cache_metadata()
        result["boundary_violations"] = dict(guard.violations)
        if guard.violations or not result["protected_cache_unchanged"]:
            result["passed"] = False
        with (SPACE_ROOT / "layout-summary.json").open("x", encoding="utf-8") as stream:
            json.dump(result, stream, sort_keys=True, indent=2)
        guard.active = False
        print(
            json.dumps(
                {
                    "phase": "A",
                    "passed": result["passed"],
                    "completed_cases": len(result["cases"]),
                    "failure_code": result.get("failure_code"),
                    "boundary_violations": dict(guard.violations),
                }
            ),
            flush=True,
        )
        if guard.violations or not result["protected_cache_unchanged"]:
            raise RuntimeError("step6_space_resource_closure_failed")


SPACE_RESUME_BASELINE = "e44a494daf31675fe6a36ed3e0b05a9f1eb863621e5c2d4be99e0f6a40df7dc3"
SPACE_REMAINING_TESTS = (
    "test_long_term_memory_application.py",
    "test_long_term_retrieval.py",
    "test_sqlite_long_term_memory.py",
    "test_sqlite_observability.py",
    "test_observability_step5.py",
)
SPACE_DEFERRED_NATIVE_TEST = (
    "backend/tests/test_long_term_dialogue_integration.py::"
    "test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback"
)
SPACE_RESUME_QA_TESTS = (
    "test_qa_space_resume_preserves_failure_and_exact_remaining_scope",
    "test_qa_space_resume_rejects_unapproved_history",
    "test_qa_space_resume_artifact_integrity",
)
SPACE_RESUME_HASHES = {
    "semantic-summary.json": ("8e2f04d70cf3b61f61ea722bd98ae33f07814135a98dcb49f9e33b7ddd45f7bd"),
    "semantic-summary-02.json": (
        "449180083836cc58de3d0f39bd562af021f29118aeb8885fea0430506925afba"
    ),
    "pytest-semantic-01/qa-summary.json": (
        "d38a942990cad13d0f2c2907ac29749803bfaa6739b31cd3d5c18ffda66da86a"
    ),
}


def space_read_resume_artifact(path: Path, expected_sha256: str) -> dict[str, Any]:
    """Read an immutable metadata artifact only after canonical and identity checks."""
    import hashlib

    path = validate_path(path)
    before = path.lstat()
    space_require(stat.S_ISREG(before.st_mode), "resume_artifact_not_regular")
    payload = path.read_bytes()
    after = path.lstat()
    identity = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    space_require(
        all(getattr(before, field) == getattr(after, field) for field in identity),
        "resume_artifact_changed",
    )
    space_require(
        hashlib.sha256(payload).hexdigest() == expected_sha256,
        "resume_artifact_hash_mismatch",
    )
    result: dict[str, Any] = json.loads(payload)
    return result


def space_resume_record(previous: dict[str, Any], pytest_report: dict[str, Any]) -> dict[str, Any]:
    """Carry the approved partial result without converting its native failure to a pass."""
    counts = {"passed": 757, "skipped": 55, "failed": 1}
    results = pytest_report["results"]
    failed = [row for row in results if row["outcome"] == "failed"]
    checks = previous["checks"]
    completed_files = {row["nodeid"].split("::")[0] for row in results}
    remaining_files = {"backend/tests/" + name for name in SPACE_REMAINING_TESTS}
    space_require(
        previous["passed"] is False
        and previous["failure_code"] == "semantic_tests_failed"
        and previous["pytest_exit_code"] == pytest_report["exit_code"] == 1
        and previous["protected_cache_unchanged"] is True
        and previous["boundary_violations"] == {}
        and previous["full_quality_started"] is False
        and previous["performance_started"] is False
        and previous["evaluators"] == []
        and len(checks) == 4
        and all(check["exit_code"] == 0 for check in checks)
        and previous["tests"][-len(SPACE_REMAINING_TESTS) :] == list(SPACE_REMAINING_TESTS)
        and pytest_report["counts"] == counts
        and dict(Counter(row["outcome"] for row in results)) == counts
        and len({row["nodeid"] for row in results}) == len(results)
        and len(failed) == 1
        and failed[0]["nodeid"] == SPACE_DEFERRED_NATIVE_TEST
        and failed[0]["phase"] == "call"
        and pytest_report["boundary_violations"]
        == {"step6_native_precreation_boundary_unavailable": 1}
        and completed_files.isdisjoint(remaining_files),
        "resume_history_not_approved",
    )
    return {
        "snapshot_sha256": SPACE_RESUME_BASELINE,
        "counts": counts,
        "failed_node_preserved": SPACE_DEFERRED_NATIVE_TEST,
        "boundary_violations": dict(pytest_report["boundary_violations"]),
        "results_reexecuted": False,
    }


def run_space_semantics() -> int:
    """Complete the approved Python remainder while retaining the pending native gate."""
    import hashlib
    import subprocess

    root = validate_path(SPACE_ROOT)
    layout = json.loads((root / "layout-summary.json").read_text(encoding="utf-8"))
    plan = json.loads((root / "layout-plan.json").read_text(encoding="utf-8"))
    space_require(
        layout["passed"]
        and len(layout["cases"]) == 12
        and layout["plan_digest"]
        == hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest(),
        "layout_not_passed",
    )
    fresh_names = [
        "semantic-summary-04.json",
        "pytest-semantic-02",
        *(f"evaluator-process-{i:02}.json" for i in range(1, 4)),
    ]
    space_require(
        all(not validate_path(root / name).exists() for name in fresh_names),
        "semantic_not_fresh",
    )
    migration = (
        PROJECT_ROOT
        / "backend/src/cyber_town/infrastructure/control/migrations"
        / SPACE_MIGRATION_NAME
    ).read_bytes()
    space_require(
        migration == SPACE_DRAFT_SQL.encode()
        and hashlib.sha256(migration).hexdigest() == plan["migration_sha256"],
        "migration_draft_mismatch",
    )
    artifacts = {
        name: space_read_resume_artifact(root / name, digest)
        for name, digest in SPACE_RESUME_HASHES.items()
    }
    prior = space_resume_record(
        artifacts["semantic-summary-02.json"],
        artifacts["pytest-semantic-01/qa-summary.json"],
    )
    tests = list(SPACE_REMAINING_TESTS)
    qa_tests = ["backend/tests/test_f009_step6_qa.py::" + name for name in SPACE_RESUME_QA_TESTS]
    before_cache = protected_cache_metadata()
    guard = ResourceGuard()
    sys.addaudithook(guard.audit)
    guard.active = True
    summary: dict[str, Any] = {
        "phase": "B",
        "scope": "python_semantic_remainder",
        "prior_result": prior,
        "prior_artifact_sha256": dict(SPACE_RESUME_HASHES),
        "pending_native_quality_tests": [SPACE_DEFERRED_NATIVE_TEST],
        "step6_complete": False,
        "qa_tests": qa_tests,
        "passed": False,
        "checks": [],
        "tests": tests,
        "evaluators": [],
        "full_quality_started": False,
        "performance_started": False,
    }
    try:
        with subprocess_isolation(guard):
            commands = [
                *space_static_commands(),
                [sys.executable, "-B", "-m", "mypy", "backend/src", "backend/tests", "scripts"],
                [sys.executable, "-B", "-m", "cyber_town.contracts.export", "--check"],
            ]
            for command in commands:
                result = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                summary["checks"].append({"argv": command, "exit_code": result.returncode})
                if result.returncode:
                    summary["failure_code"] = "static_check_failed"
                    # Only static compiler diagnostics; never retain application stdout.
                    print(result.stdout, flush=True)
                    print(result.stderr, flush=True)
                    return result.returncode
            code = run_pytest(
                [*qa_tests, *("backend/tests/" + name for name in tests)],
                batch="control-space-v1/pytest-semantic-02",
                output="control-space-v1/pytest-semantic-02/qa-summary.json",
            )
            summary["pytest_exit_code"] = code
            pytest_report = json.loads(
                (root / "pytest-semantic-02/qa-summary.json").read_text(encoding="utf-8")
            )
            summary["pytest_counts"] = pytest_report["counts"]
            summary["pytest_boundary_violations"] = pytest_report["boundary_violations"]
            if code:
                summary["failure_code"] = "semantic_tests_failed"
                return code
            space_require(not pytest_report["boundary_violations"], "semantic_resource_boundary")
            space_require(not pytest_report["counts"].get("skipped", 0), "semantic_unexpected_skip")
            script = """
import json, os
from datetime import UTC, datetime
from pathlib import Path
from cyber_town.application.control_evaluation import (
    build_control_baseline_observations, evaluate_control_fixture,
    load_control_evaluation_fixture,
)
fixture = load_control_evaluation_fixture(
    Path("backend/tests/fixtures/f009_control_evaluation_v1.json")
)
report = evaluate_control_fixture(
    fixture, build_control_baseline_observations(fixture),
    b"f009-step5-synthetic-evaluation-key",
).as_dict()
report["dimension_count"] = len({case.dimension for case in fixture.cases})
report["process_id"] = os.getpid()
report["process_reported_at"] = datetime.now(UTC).isoformat()
print(json.dumps(report, sort_keys=True))
"""
            for index in range(1, 4):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", script],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                space_require(result.returncode == 0, "evaluator_process_failed")
                report = json.loads(result.stdout)
                path = root / f"evaluator-process-{index:02}.json"
                with path.open("x", encoding="utf-8") as stream:
                    json.dump(report, stream, sort_keys=True, indent=2)
                summary["evaluators"].append(report)
                space_require(
                    report["case_count"] == report["passed_count"] == 25
                    and report["failed_count"] == 0
                    and report["dimension_count"] == 11
                    and report["canonical_digest"]
                    == "1986a20db79cce74dfe458193ce0f2ab52e0d457d047b31d2e9465aeadf624bb",
                    "evaluator_regression",
                )
            space_require(
                len({report["process_id"] for report in summary["evaluators"]}) == 3,
                "evaluator_process_identity",
            )
            summary["passed"] = True
            return 0
    except Exception as error:
        message = str(error)
        summary["failure_code"] = (
            message
            if re.fullmatch(r"step6_space_[a-z_]+", message)
            else "semantic_exception_" + type(error).__name__
        )
        return 1
    finally:
        summary["protected_cache_unchanged"] = before_cache == protected_cache_metadata()
        summary["boundary_violations"] = dict(guard.violations)
        if guard.violations or not summary["protected_cache_unchanged"]:
            summary["passed"] = False
        with (root / "semantic-summary-04.json").open("x", encoding="utf-8") as stream:
            json.dump(summary, stream, sort_keys=True, indent=2)
        guard.active = False
        print(
            json.dumps(
                {
                    "phase": "B",
                    "scope": "python_semantic_remainder",
                    "passed": summary["passed"],
                    "failure_code": summary.get("failure_code"),
                    "boundary_violations": dict(guard.violations),
                }
            ),
            flush=True,
        )
        if guard.violations or not summary["protected_cache_unchanged"]:
            raise RuntimeError("step6_space_resource_closure_failed")


TOOL_CONTRACT_TESTS = (
    "backend/tests/test_f009_step6_qa.py::test_qa_ledger_sources_separate_lifecycles",
    "backend/tests/test_f009_step6_qa.py::test_s1_current_root_allowed_and_external_root_rejected",
    "backend/tests/test_f009_step6_qa.py::test_qa_ledger_preserved_history_and_precreation_contract",
    "backend/tests/test_f009_step6_qa.py::test_qa_ledger_required_sources_fail_closed",
    "backend/tests/test_f009_step6_qa.py::test_qa_ledger_native_inventory_after_real_observer",
    "backend/tests/test_f009_step6_qa.py::test_entry_readiness_contract",
    "backend/tests/test_f009_step6_qa.py::test_qa_canonical_diagnostic_keeps_rejection_and_redacts_target",
    "backend/tests/test_f009_step6_qa.py::test_qa_canonical_diagnostic_classifies_retired_without_access",
    "backend/tests/test_f009_step6_qa.py::test_qa_repeat_registration_reconciles_only_registered_retired_sqlite_sidecar",
    "backend/tests/test_f009_step6_qa.py::test_qa_retired_sqlite_registration_rejects_incomplete_prior_registration",
    "backend/tests/test_f009_step6_qa.py::test_qa_resource_ledger_streams_archive_and_current",
    "backend/tests/test_f009_step6_qa.py::test_qa_canonical_diagnostic_reports_concurrent_failures_without_cross_talk",
    "backend/tests/test_f009_step6_qa.py::test_qa_benchmark_root_binding_restores_configuration_on_error",
    "backend/tests/test_f009_step6_qa.py::test_qa_space_performance_binding_restores_configuration",
    "backend/tests/test_f009_step6_qa.py::test_qa_space_performance_binding_rejects_invalid_root",
    "backend/tests/test_f009_step6_qa.py::test_qa_space_performance_binding_rejects_changed_identity_after_restore",
    "backend/tests/test_f009_step6_qa.py::test_qa_resource_guard_rejects_unsafe_sqlite_uri_before_connect",
    "backend/tests/test_f009_step6_qa.py::test_qa_subprocess_wrapper_restores_and_preserves_python_arguments",
    "backend/tests/test_f009_step6_qa.py::test_qa_child_temporary_directories_are_retained",
    "backend/tests/test_f009_step6_qa.py::test_qa_native_commands_cannot_launch_or_register_parent_as_coverage",
    "backend/tests/test_f009_step6_qa.py::test_qa_launch_overrides_cannot_bypass_python_boundary",
    "backend/tests/test_f009_step6_qa.py::test_qa_untrusted_child_marker_still_runs_inside_guard",
    "backend/tests/test_f009_step6_qa.py::test_qa_quality_preflight_stops_before_resource_creation",
    "backend/tests/test_f009_step6_qa.py::test_qa_real_python_child_registers_file_and_blocks_native_git",
    "backend/tests/test_f009_step6_qa.py::test_qa_native_key_exception_is_exact",
    "backend/tests/test_f009_step6_qa.py::test_qa_native_notification_corruption_fails_closed",
    "backend/tests/test_f009_step6_qa.py::test_qa_windows_observer_records_creation_before_native_probe",
    "backend/tests/test_f009_step6_qa.py::test_qa_native_observer_overflow_is_a_hard_failure",
    "backend/tests/test_f009_step6_qa.py::test_qa_uv_cache_git_marker_is_not_a_synthetic_git_repository",
    "backend/tests/test_f009_step6_qa.py::test_qa_keystore_exception_cannot_extend_to_another_batch",
    "backend/tests/test_f009_step6_qa.py::test_qa_other_native_cache_creation_is_rejected_with_event_metadata",
    "backend/tests/test_f009_step6_qa.py::test_qa_uv_exception_is_scoped_to_active_approved_roots",
    "backend/tests/test_f009_step6_qa.py::test_qa_canonical_failure_preserves_original_notification",
    "backend/tests/test_f009_step6_qa.py::test_qa_real_notification_rename_checks_preregistered_paths",
    "backend/tests/test_f009_step6_qa.py::test_qa_unified_child_environment_overrides_inherited_cache_settings",
    "backend/tests/test_f009_step6_qa.py::test_qa_static_entrypoint_refuses_omitted_no_cache",
    "backend/tests/test_f009_step6_qa.py::test_qa_command_scope_restores_environment_and_temp",
    "backend/tests/test_f009_step6_qa.py::test_qa_windows_disappearance_keeps_exact_canonical_dos_identity",
    "backend/tests/test_f009_step6_qa.py::test_qa_extended_prefix_never_accepts_a_different_resolved_target",
    "backend/tests/test_f009_step6_qa.py::test_qa_notification_keeps_first_failed_resolution_without_second_lookup",
    "backend/tests/test_f009_step6_qa.py::test_qa_godot_jvm_counter_is_disabled_only_in_child_environment",
    "backend/tests/test_f009_step6_qa.py::test_qa_jvm_option_does_not_change_other_native_tools",
    "backend/tests/test_f009_step6_qa.py::test_qa_jvm_counter_files_remain_outside_native_exception",
    "backend/tests/test_f009_step6_qa.py::test_qa_late_sqlite_notification_requires_registered_absent_sidecar",
    "backend/tests/test_f009_step6_qa.py::test_qa_real_sqlite_journal_lifecycles_keep_guarded_notifications",
    "backend/tests/test_f009_step6_qa.py::test_qa_nested_guard_does_not_restore_revoked_native_environment",
    "backend/tests/test_f009_step6_qa.py::test_qa_real_restricted_child_cannot_inherit_native_monitor",
    "backend/tests/test_f009_step6_qa.py::test_qa_real_numbered_pytest_directory_has_no_alias_notification",
    "backend/tests/test_f009_step6_qa.py::test_qa_alias_audit_blocks_creation_before_registration",
    "backend/tests/test_f009_step6_qa.py::test_qa_pytest_alias_scope_rejects_invalid_request_and_restores",
    "backend/tests/test_f009_step6_qa.py::test_qa_async_child_registers_file_and_inherits_audit",
    "backend/tests/test_f009_step6_qa.py::test_qa_uv_retired_notification_requires_observed_removal_and_stable_anchor",
    "backend/tests/test_f009_step6_qa.py::test_qa_async_native_and_shell_launch_are_blocked_and_restored",
    "backend/tests/test_f009_step6_qa.py::test_qa_godot_rename_notification_strictly_revalidates_paths_and_identity",
    "backend/tests/test_f009_step6_qa.py::test_qa_connectivity_diagnostics_classify_wrapped_runner_failure",
    "backend/tests/test_f009_step6_qa.py::test_qa_connectivity_diagnostics_keep_scenario_and_discard_details",
    "backend/tests/test_f009_step6_qa.py::test_qa_connectivity_diagnostics_do_not_invent_causes_or_retain_unknown_output",
    "backend/tests/test_f009_step6_qa.py::test_qa_observation_replay_preserves_formal_registration_under_active_guard",
    "backend/tests/test_f009_step6_qa.py::test_qa_contract_context_requires_current_live_owner",
    "backend/tests/test_f009_step6_qa.py::test_qa_contract_ledger_registration_precedes_operation",
    "backend/tests/test_f009_step6_qa.py::test_qa_contract_ledger_half_line_is_retained_until_complete",
    "backend/tests/test_f009_step6_qa.py::test_qa_contract_ledger_rejects_changed_metadata_without_modifying_evidence",
    "backend/tests/test_f009_step6_qa.py::test_qa_contract_ledger_write_failure_does_not_grant_registration",
    "backend/tests/test_f009_step6_qa.py::test_qa_contract_ledger_concurrent_writers_visible_to_real_observer",
    "backend/tests/test_f009_step6_qa.py::test_qa_contract_history_covers_preserved_sources_and_fixed_ledger",
    "backend/tests/test_f009_step6_qa.py::test_qa_space_resume_preserves_failure_and_exact_remaining_scope",
    "backend/tests/test_f009_step6_qa.py::test_qa_space_resume_rejects_unapproved_history",
    "backend/tests/test_f009_step6_qa.py::test_qa_space_resume_artifact_integrity",
    "backend/tests/test_architecture_probe_step5.py::"
    "test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_ledger_paths_are_exact_and_distinct",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_binding_cannot_switch_active_ledger",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_bootstrap_has_exact_preoperation_records",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_capacity_rejects_excess_before_creation",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_prior_ledgers_are_read_only",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_quality_requires_current_tool_contract_receipt",
    "backend/tests/test_f009_step6_qa.py::test_qa_current_tool_observer_receipt",
    "backend/tests/test_f009_step6_qa.py::test_qa_current_tool_command_context",
    "backend/tests/test_f009_step6_qa.py::test_startup_phase_context_separation",
    "backend/tests/test_f009_step6_qa.py::test_startup_root_and_owner",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_reporting",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_cleanup_failures",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_completion_requirements",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_evidence_failure",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_wait_contract",
    "backend/tests/test_f009_step6_qa.py::test_popen_cleanup_report_semantics",
    "backend/tests/test_f009_step6_qa.py::test_startup_real_pytest_report_path",
    "backend/tests/test_f009_step6_qa.py::test_termination_real_pytest_report_path",
    "backend/tests/test_f009_step6_qa.py::test_startup_identity_after_exit",
    "backend/tests/test_f009_step6_qa.py::test_startup_exit_transition",
    "backend/tests/test_f009_step6_qa.py::test_startup_process_rejects_identity_changes",
    "backend/tests/test_f009_step6_qa.py::test_startup_cleanup_reporting",
    "backend/tests/test_f009_step6_qa.py::test_cleanup_schema_and_limits",
    "backend/tests/test_f009_step6_qa.py::test_termination_schema_and_limits",
    "backend/tests/test_f009_step6_qa.py::test_startup_identity_summary_limit",
    "backend/tests/test_f009_step6_qa.py::test_summary_limit_root_contract",
    "backend/tests/test_f009_step6_qa.py::test_summary_write_byte_boundary",
    "backend/tests/test_f009_step6_qa.py::test_summary_real_runner_limit",
    "backend/tests/test_f009_step6_qa.py::test_summary_writer_entry_contract",
    "backend/tests/test_f009_step6_qa.py::test_launcher_exit_batch_contract",
    "backend/tests/test_f009_step6_qa.py::test_launcher_exit_wait_contract",
    "backend/tests/test_f009_step6_qa.py::test_startup_process_observation",
    "backend/tests/test_f009_step6_qa.py::test_startup_exited_initial_binding_rejected",
    "backend/tests/test_f009_step6_qa.py::test_startup_live_identity_failure",
    "backend/tests/test_f009_step6_qa.py::test_startup_retained_handle_state_api",
    "backend/tests/test_f009_step6_qa.py::test_startup_termination_error_capture",
    "backend/tests/test_f009_step6_qa.py::test_startup_exit_during_termination",
    "backend/tests/test_f009_step6_qa.py::test_termination_wait_real_pytest_report_path",
    "backend/tests/test_f009_step6_qa.py::test_observer_capacity_batch_contract",
    "backend/tests/test_f009_step6_qa.py::test_observer_failure_batch_contract",
    "backend/tests/test_f009_step6_qa.py::test_observer_capacity_real_constructor",
    "backend/tests/test_f009_step6_qa.py::test_observer_capacity_large_notification_block",
    "backend/tests/test_f009_step6_qa.py::test_observer_receive_failure_contract",
    "backend/tests/test_f009_step6_qa.py::test_observer_failure_fields",
    "backend/tests/test_f009_step6_qa.py::test_observer_finish_failure_contract",
    "backend/tests/test_f009_step6_qa.py::test_observer_session_failure_restoration",
    "backend/tests/test_f009_step6_qa.py::test_observer_quality_failure_report",
    "backend/tests/test_f009_step6_qa.py::test_observer_command_failure_order",
    "backend/tests/test_f009_step6_qa.py::test_observer_actual_command_evidence",
    "backend/tests/test_f009_step6_qa.py::test_native_drain_single_post_ack_check",
    "backend/tests/test_f009_step6_qa.py::test_migration_digest_batch_contract",
    "backend/tests/test_f009_step6_qa.py::test_migration_digest_real_report",
    "backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_representations",
    "backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_change_is_visible",
    "backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_rejects_invalid",
    "backend/tests/test_storage_migrations_v4.py::test_migration_digest_unknown_blob_is_not_converted",
    "backend/tests/test_storage_migrations_v4.py::test_migration_digest_keeps_non_scope_coverage",
    "backend/tests/test_storage_migrations_v4.py::test_migration_digest_clock_exclusion_is_explicit",
    "backend/tests/test_storage_migrations_v4.py::test_version_four_is_append_only_registered",
    "backend/tests/test_storage_migrations_v4.py::test_populated_v3_upgrade_preserves_decoded_rows_and_constraints",
    "backend/tests/test_storage_migrations_v4.py::test_migration_interruption_rolls_back_all_prior_changes",
    "backend/tests/test_storage_migrations_v4.py::test_invalid_old_uuid_aborts_entire_observability_upgrade",
    "backend/tests/test_compact_storage_step5.py::test_synthetic_compact_layout_has_exact_decoded_rows",
    "backend/tests/test_compact_storage_step5.py::test_compact_rebuild_is_atomic_at_each_table",
    "backend/tests/test_compact_storage_step5.py::test_invalid_legacy_uuid_fails_instead_of_repairing_or_dropping",
    "backend/tests/test_sqlite_control.py::test_v9_product_upgrade_preserves_rows_and_restarts",
    "backend/tests/test_storage_migrations_v4.py::test_repository_populated_upgrade_repeat_and_cli_boundary",
    "backend/tests/test_f009_step6_qa.py::test_startup_observe_actual_business_child",
)


TOOL_CONTRACT_COUNTS = {
    ("backend/tests/test_f009_step6_qa.py::test_observer_capacity_batch_contract"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_observer_failure_batch_contract"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_observer_capacity_real_constructor"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_observer_capacity_large_notification_block"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_observer_receive_failure_contract"): 6,
    ("backend/tests/test_f009_step6_qa.py::test_observer_failure_fields"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_observer_finish_failure_contract"): 10,
    ("backend/tests/test_f009_step6_qa.py::test_observer_session_failure_restoration"): 2,
    ("backend/tests/test_f009_step6_qa.py::test_observer_quality_failure_report"): 5,
    ("backend/tests/test_f009_step6_qa.py::test_observer_command_failure_order"): 3,
    ("backend/tests/test_f009_step6_qa.py::test_observer_actual_command_evidence"): 2,
    ("backend/tests/test_f009_step6_qa.py::test_native_drain_single_post_ack_check"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_ledger_sources_separate_lifecycles"): 5,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_s1_current_root_allowed_and_external_root_rejected"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_ledger_preserved_history_and_precreation_contract"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_ledger_required_sources_fail_closed"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_qa_ledger_native_inventory_after_real_observer"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_entry_readiness_contract"): 20,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_canonical_diagnostic_keeps_rejection_and_redacts_target"
    ): 4,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_canonical_diagnostic_classifies_retired_without_access"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_repeat_registration_reconciles_only_registered_retired_sqlite_sidecar"
    ): 2,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_retired_sqlite_registration_rejects_incomplete_prior_registration"
    ): 2,
    ("backend/tests/test_f009_step6_qa.py::test_qa_resource_ledger_streams_archive_and_current"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_canonical_diagnostic_reports_concurrent_failures_without_cross_talk"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_benchmark_root_binding_restores_configuration_on_error"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_space_performance_binding_restores_configuration"
    ): 2,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_space_performance_binding_rejects_invalid_root"
    ): 3,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_space_performance_binding_rejects_changed_identity_after_restore"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_resource_guard_rejects_unsafe_sqlite_uri_before_connect"
    ): 3,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_subprocess_wrapper_restores_and_preserves_python_arguments"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_child_temporary_directories_are_retained"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_native_commands_cannot_launch_or_register_parent_as_coverage"
    ): 9,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_launch_overrides_cannot_bypass_python_boundary"
    ): 2,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_untrusted_child_marker_still_runs_inside_guard"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_quality_preflight_stops_before_resource_creation"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_real_python_child_registers_file_and_blocks_native_git"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_native_key_exception_is_exact"): 2,
    ("backend/tests/test_f009_step6_qa.py::test_qa_native_notification_corruption_fails_closed"): 3,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_windows_observer_records_creation_before_native_probe"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_native_observer_overflow_is_a_hard_failure"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_uv_cache_git_marker_is_not_a_synthetic_git_repository"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_keystore_exception_cannot_extend_to_another_batch"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_other_native_cache_creation_is_rejected_with_event_metadata"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_uv_exception_is_scoped_to_active_approved_roots"
    ): 5,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_canonical_failure_preserves_original_notification"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_real_notification_rename_checks_preregistered_paths"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_unified_child_environment_overrides_inherited_cache_settings"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_static_entrypoint_refuses_omitted_no_cache"): 2,
    ("backend/tests/test_f009_step6_qa.py::test_qa_command_scope_restores_environment_and_temp"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_windows_disappearance_keeps_exact_canonical_dos_identity"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_extended_prefix_never_accepts_a_different_resolved_target"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_notification_keeps_first_failed_resolution_without_second_lookup"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_godot_jvm_counter_is_disabled_only_in_child_environment"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::test_qa_jvm_option_does_not_change_other_native_tools"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_jvm_counter_files_remain_outside_native_exception"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_late_sqlite_notification_requires_registered_absent_sidecar"
    ): 8,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_real_sqlite_journal_lifecycles_keep_guarded_notifications"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_nested_guard_does_not_restore_revoked_native_environment"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_real_restricted_child_cannot_inherit_native_monitor"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_real_numbered_pytest_directory_has_no_alias_notification"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_alias_audit_blocks_creation_before_registration"
    ): 2,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_pytest_alias_scope_rejects_invalid_request_and_restores"
    ): 3,
    (
        "backend/tests/test_f009_step6_qa.py::test_qa_async_child_registers_file_and_inherits_audit"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_uv_retired_notification_requires_observed_removal_and_stable_anchor"
    ): 17,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_async_native_and_shell_launch_are_blocked_and_restored"
    ): 2,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_godot_rename_notification_strictly_revalidates_paths_and_identity"
    ): 26,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_connectivity_diagnostics_classify_wrapped_runner_failure"
    ): 13,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_connectivity_diagnostics_keep_scenario_and_discard_details"
    ): 8,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_connectivity_diagnostics_do_not_invent_causes_or_retain_unknown_output"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_observation_replay_preserves_formal_registration_under_active_guard"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::test_qa_contract_context_requires_current_live_owner"
    ): 5,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_contract_ledger_registration_precedes_operation"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_contract_ledger_half_line_is_retained_until_complete"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_contract_ledger_rejects_changed_metadata_without_modifying_evidence"
    ): 3,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_contract_ledger_write_failure_does_not_grant_registration"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_contract_ledger_concurrent_writers_visible_to_real_observer"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_contract_history_covers_preserved_sources_and_fixed_ledger"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_space_resume_preserves_failure_and_exact_remaining_scope"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_space_resume_rejects_unapproved_history"): 13,
    ("backend/tests/test_f009_step6_qa.py::test_qa_space_resume_artifact_integrity"): 3,
    (
        "backend/tests/test_architecture_probe_step5.py::"
        "test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_batch_ledger_paths_are_exact_and_distinct"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_qa_batch_binding_cannot_switch_active_ledger"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked"
    ): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_batch_bootstrap_has_exact_preoperation_records"
    ): 2,
    (
        "backend/tests/test_f009_step6_qa.py::test_qa_batch_capacity_rejects_excess_before_creation"
    ): 6,
    ("backend/tests/test_f009_step6_qa.py::test_qa_batch_prior_ledgers_are_read_only"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_batch_quality_requires_current_tool_contract_receipt"
    ): 9,
    ("backend/tests/test_f009_step6_qa.py::test_qa_current_tool_observer_receipt"): 7,
    ("backend/tests/test_f009_step6_qa.py::test_qa_current_tool_command_context"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_startup_phase_context_separation"): 5,
    ("backend/tests/test_f009_step6_qa.py::test_startup_root_and_owner"): 3,
    ("backend/tests/test_f009_step6_qa.py::test_startup_entry_reporting"): 9,
    ("backend/tests/test_f009_step6_qa.py::test_startup_entry_cleanup_failures"): 10,
    ("backend/tests/test_f009_step6_qa.py::test_startup_entry_completion_requirements"): 3,
    ("backend/tests/test_f009_step6_qa.py::test_startup_entry_evidence_failure"): 3,
    ("backend/tests/test_f009_step6_qa.py::test_startup_entry_wait_contract"): 6,
    ("backend/tests/test_f009_step6_qa.py::test_popen_cleanup_report_semantics"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_startup_real_pytest_report_path"): 10,
    ("backend/tests/test_f009_step6_qa.py::test_termination_real_pytest_report_path"): 14,
    ("backend/tests/test_f009_step6_qa.py::test_startup_identity_after_exit"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_startup_exit_transition"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_startup_process_rejects_identity_changes"): 2,
    ("backend/tests/test_f009_step6_qa.py::test_startup_cleanup_reporting"): 6,
    ("backend/tests/test_f009_step6_qa.py::test_cleanup_schema_and_limits"): 9,
    ("backend/tests/test_f009_step6_qa.py::test_termination_schema_and_limits"): 7,
    ("backend/tests/test_f009_step6_qa.py::test_startup_identity_summary_limit"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_summary_limit_root_contract"): 9,
    ("backend/tests/test_f009_step6_qa.py::test_summary_write_byte_boundary"): 6,
    ("backend/tests/test_f009_step6_qa.py::test_summary_real_runner_limit"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_summary_writer_entry_contract"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_launcher_exit_batch_contract"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_launcher_exit_wait_contract"): 12,
    ("backend/tests/test_f009_step6_qa.py::test_startup_process_observation"): 8,
    ("backend/tests/test_f009_step6_qa.py::test_startup_exited_initial_binding_rejected"): 5,
    ("backend/tests/test_f009_step6_qa.py::test_startup_live_identity_failure"): 12,
    ("backend/tests/test_f009_step6_qa.py::test_startup_retained_handle_state_api"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_startup_termination_error_capture"): 2,
    ("backend/tests/test_f009_step6_qa.py::test_startup_exit_during_termination"): 4,
    ("backend/tests/test_f009_step6_qa.py::test_termination_wait_real_pytest_report_path"): 6,
    ("backend/tests/test_f009_step6_qa.py::test_migration_digest_batch_contract"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_migration_digest_real_report"): 4,
    ("backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_representations"): 8,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_change_is_visible"
    ): 3,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_rejects_invalid"
    ): 27,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_digest_unknown_blob_is_not_converted"
    ): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_digest_keeps_non_scope_coverage"
    ): 4,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_digest_clock_exclusion_is_explicit"
    ): 3,
    ("backend/tests/test_storage_migrations_v4.py::test_version_four_is_append_only_registered"): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::test_populated_v3_upgrade_preserves_decoded_rows_and_constraints"
    ): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_interruption_rolls_back_all_prior_changes"
    ): 8,
    (
        "backend/tests/test_storage_migrations_v4.py::test_invalid_old_uuid_aborts_entire_observability_upgrade"
    ): 1,
    (
        "backend/tests/test_compact_storage_step5.py::test_synthetic_compact_layout_has_exact_decoded_rows"
    ): 1,
    (
        "backend/tests/test_compact_storage_step5.py::test_compact_rebuild_is_atomic_at_each_table"
    ): 4,
    (
        "backend/tests/test_compact_storage_step5.py::test_invalid_legacy_uuid_fails_instead_of_repairing_or_dropping"
    ): 1,
    (
        "backend/tests/test_sqlite_control.py::test_v9_product_upgrade_preserves_rows_and_restarts"
    ): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::test_repository_populated_upgrade_repeat_and_cli_boundary"
    ): 2,
    ("backend/tests/test_f009_step6_qa.py::test_startup_observe_actual_business_child"): 2,
}


def qa_code_fingerprints(extra: tuple[str, ...] = ()) -> dict[str, str]:
    import hashlib

    return {
        name: hashlib.sha256((PROJECT_ROOT / name).read_bytes()).hexdigest()
        for name in (
            "scripts/f009_step6_qa.py",
            "backend/tests/test_f009_step6_qa.py",
            "backend/src/cyber_town/api/__main__.py",
            *extra,
        )
    }


def require_current_tool_receipt(receipt: dict[str, Any]) -> None:
    if not (
        receipt.get("passed") is True
        and receipt.get("all_selected_functions_executed") is True
        and receipt.get("formal_evidence_unchanged") is True
        and receipt.get("code_fingerprints") == qa_code_fingerprints(TOOL_CODE_FILES)
        and receipt.get("migration_stage_evidence_complete") is True
        and receipt.get("tests") == list(TOOL_CONTRACT_TESTS)
        and receipt.get("parameter_counts") == TOOL_CONTRACT_COUNTS
        and receipt.get("counts") == {"passed": sum(TOOL_CONTRACT_COUNTS.values())}
        and receipt.get("command") == tool_contract_command()
        and receipt.get("cwd") == str(PROJECT_ROOT)
        and type(receipt.get("observer_pid")) is int
        and receipt["observer_pid"] > 0
        and receipt.get("batch") == str(TOOL_CONTRACT_ROOT)
        and receipt.get("ledger") == str(batch_ledger_path(TOOL_CONTRACT_ROOT))
    ):
        raise RuntimeError("step6_current_tool_contract_not_ready")


def tool_contract_command() -> list[str]:
    batch = TOOL_CONTRACT_ROOT.relative_to(QA_ROOT).as_posix()
    return [
        sys.executable,
        "-B",
        str(PROJECT_ROOT / "scripts/f009_step6_qa.py"),
        "--batch",
        batch + "/pytest",
        "--output",
        batch + "/pytest-summary.json",
        *TOOL_CONTRACT_TESTS,
    ]


def tool_contract_artifact(name: str, limit: int) -> dict[str, Any]:
    import hashlib

    path = validate_path(TOOL_CONTRACT_ROOT / name)
    if path.stat().st_size > limit:
        raise RuntimeError("step6_tool_contract_artifact_limit")
    return space_read_resume_artifact(path, hashlib.sha256(path.read_bytes()).hexdigest())


def require_current_tool_observer(native: dict[str, Any], owner: dict[str, Any], pid: int) -> None:
    if (
        type(pid) is not int
        or pid <= 0
        or owner != {"root": str(TOOL_CONTRACT_ROOT), "pid": pid}
        or native.get("completed") is not True
        or native.get("overflow") is not False
        or native.get("unknown_paths") != []
        or native.get("reparse") != 0
    ):
        raise RuntimeError("step6_current_tool_observer_not_complete")


def require_current_readiness_receipt(
    root: Path,
    report: dict[str, Any],
    invocation: dict[str, Any],
    pytest_summary: dict[str, Any],
    native: dict[str, Any],
    owner: dict[str, Any],
) -> None:
    """Require the current frozen S1 receipt before any formal quality resource exists."""
    expected_counts = Counter(S1_READINESS_COUNTS)
    completed = report.get("completed")
    rows = pytest_summary.get("results")
    try:
        s1_runtime.require_readiness_passed(report)
    except RuntimeError as error:
        raise RuntimeError("step6_current_readiness_not_ready") from error
    if not (
        root == CURRENT_TOOL_READINESS_ROOT
        and report.get("root") == str(root)
        and report.get("selected") == list(S1_READINESS_TESTS)
        and isinstance(completed, list)
        and Counter(node.split("[", 1)[0] for node in completed) == expected_counts
        and invocation.get("command") == identity_validation_command(root, S1_READINESS_TESTS)
        and invocation.get("cwd") == str(PROJECT_ROOT)
        and invocation.get("code_fingerprints")
        == qa_code_fingerprints(("scripts/f009_step6_runtime.py",))
        and invocation.get("batch") == str(root)
        and invocation.get("ledger") == str(batch_ledger_path(root))
        and invocation.get("native_observer_parallel") is True
        and invocation.get("fake_only") is True
        and invocation.get("product_start_attempts") == 0
        and type(invocation.get("observer_pid")) is int
        and invocation["observer_pid"] > 0
        and pytest_summary.get("batch") == str(root.relative_to(QA_ROOT) / "pytest")
        and pytest_summary.get("exit_code") == 0
        and pytest_summary.get("counts") == {"passed": sum(expected_counts.values())}
        and isinstance(rows, list)
        and len(rows) == sum(expected_counts.values())
        and all(row.get("outcome") == "passed" for row in rows)
        and pytest_summary.get("boundary_violations") == {}
        and pytest_summary.get("identity_diagnostic_rejections") == []
        and pytest_summary.get("termination_diagnostic_rejections") == []
        and pytest_summary.get("raw_output_retained") is False
        and owner == {"root": str(root), "pid": invocation["observer_pid"]}
        and native.get("completed") is True
        and native.get("overflow") is False
        and native.get("unknown_paths") == []
        and native.get("reparse") == 0
    ):
        raise RuntimeError("step6_current_readiness_not_ready")


def current_readiness_artifact(name: str, limit: int) -> tuple[dict[str, Any], str]:
    """Read one bounded frozen artifact without trusting a mutable path or stale tool receipt."""
    import hashlib

    path = validate_path(CURRENT_TOOL_READINESS_ROOT / name)
    if not path.is_file() or path.stat().st_size > limit:
        raise RuntimeError("step6_current_readiness_artifact_invalid")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return space_read_resume_artifact(path, digest), digest


def read_current_readiness_receipt() -> dict[str, Any]:
    """Load and validate the one current post-repair readiness receipt for S2."""
    artifacts: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for name, limit in (
        ("tool-readiness-summary.json", 1024**2),
        ("invocation.json", 64 * 1024),
        ("pytest-summary.json", 1024**2),
        ("native-summary.json", 8 * 1024**2),
        ("native-monitor-ready.json", 4096),
    ):
        artifacts[name], hashes[name] = current_readiness_artifact(name, limit)
    require_current_readiness_receipt(
        CURRENT_TOOL_READINESS_ROOT,
        artifacts["tool-readiness-summary.json"],
        artifacts["invocation.json"],
        artifacts["pytest-summary.json"],
        artifacts["native-summary.json"],
        artifacts["native-monitor-ready.json"],
    )
    return {
        "root": str(CURRENT_TOOL_READINESS_ROOT),
        "artifact_sha256": hashes,
        "code_fingerprints": artifacts["invocation.json"]["code_fingerprints"],
        "passed": True,
        "tests": list(S1_READINESS_TESTS),
        "counts": artifacts["pytest-summary.json"]["counts"],
    }


def run_tool_contract() -> int:
    """One authorized tool-only batch using the existing native/child adapters."""
    require_ledger_sources(HISTORICAL_LEDGERS)
    root = TOOL_CONTRACT_ROOT
    guard = ResourceGuard()
    before_evidence = EVIDENCE.read_bytes()
    summary: dict[str, Any] = {
        "tests": list(TOOL_CONTRACT_TESTS),
        "native_observer_parallel": True,
        "full_quality_started": False,
        "performance_started": False,
        "raw_output_retained": False,
        "passed": False,
        "batch": str(root),
        "ledger": str(batch_ledger_path(root)),
        "code_fingerprints": qa_code_fingerprints(TOOL_CODE_FILES),
        "migration_stage_evidence_complete": False,
        "command": tool_contract_command(),
        "cwd": str(PROJECT_ROOT),
        "observer_pid": os.getpid(),
    }
    with native_session(root, guard) as watcher, subprocess_isolation(guard):
        output = root / "contract-summary.json"
        guard.register(output, "metadata_tool_contract_summary")
        try:
            argv = tool_contract_command()
            code, _, stderr = run_observed(argv, watcher)
            summary["exit_code"] = code
            summary["error_classes"] = sorted(set(re.findall(r"^([A-Za-z]+Error):", stderr, re.M)))
            report = tool_contract_artifact("pytest-summary.json", 1024**2)
            summary["counts"] = report["counts"]
            summary["boundary_violations"] = report["boundary_violations"]
            executed = {row["nodeid"].split("[", 1)[0] for row in report["results"]}
            summary["all_selected_functions_executed"] = executed == set(TOOL_CONTRACT_TESTS)
            parameter_counts = Counter(row["nodeid"].split("[", 1)[0] for row in report["results"])
            summary["parameter_counts"] = dict(parameter_counts)
            summary["uv_instances"] = sum(
                "test_qa_uv_retired_notification_requires_observed_removal_and_stable_anchor["
                in row["nodeid"]
                for row in report["results"]
            )
            summary["godot_replay_instances"] = sum(
                "test_qa_godot_rename_notification_strictly_revalidates_paths_and_identity["
                in row["nodeid"]
                for row in report["results"]
            )
            if code == 0:
                require_migration_digest_stage_evidence(report)
                summary["migration_stage_evidence_complete"] = True
            summary["formal_evidence_unchanged"] = EVIDENCE.read_bytes() == before_evidence
            summary["passed"] = (
                code == 0
                and not report["boundary_violations"]
                and summary["all_selected_functions_executed"]
                and parameter_counts == TOOL_CONTRACT_COUNTS
                and report["identity_diagnostic_rejections"] == []
                and report["termination_diagnostic_rejections"] == []
                and summary["uv_instances"] == 17
                and summary["godot_replay_instances"] == 26
                and summary["formal_evidence_unchanged"]
                and all(row["outcome"] == "passed" for row in report["results"])
            )
            if not summary["passed"]:
                raise RuntimeError("step6_tool_contract_tests_failed")
        finally:
            write_contract_summary(output, summary)
            print(json.dumps(summary), flush=True)
    return 0


STARTUP_MODULES = (
    "cyber_town",
    "cyber_town.api",
    "cyber_town.api.__main__",
    "cyber_town.api.app",
    "cyber_town.api.composition",
    "cyber_town.config",
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic_settings",
)
STARTUP_STAGES = frozenset(
    {
        "wrapper_entered",
        "configured",
        "owner_verified",
        "guard_active",
        "module_entry",
        "wrapper_finished",
    }
)
STARTUP_PHASES = (
    "before_composition_import",
    "composition_import_returned",
    "main_entered",
    "settings_returned",
    "before_service_assembly",
    "before_uvicorn_run",
)
STARTUP_POSITION_SOURCES = frozenset(
    {
        "feature/backend/src/cyber_town/api/__main__.py",
        "feature/backend/src/cyber_town/api/composition.py",
        "feature/backend/src/cyber_town/api/app.py",
        "feature/backend/src/cyber_town/config.py",
        "feature/backend/src/cyber_town/infrastructure/llm/deepseek.py",
        "feature/scripts/f009_step6_qa.py",
        "python/Lib/importlib/_bootstrap.py",
        "python/Lib/importlib/_bootstrap_external.py",
        "python/Lib/asyncio/base_events.py",
        "python/Lib/asyncio/windows_events.py",
        "python/Lib/asyncio/events.py",
        "python/Lib/asyncio/runners.py",
        "venv/Lib/site-packages/openai/__init__.py",
        "venv/Lib/site-packages/openai/_client.py",
        "venv/Lib/site-packages/openai/_base_client.py",
        "venv/Lib/site-packages/pydantic/main.py",
        "venv/Lib/site-packages/pydantic_settings/main.py",
        "venv/Lib/site-packages/uvicorn/main.py",
        "venv/Lib/site-packages/uvicorn/config.py",
        "venv/Lib/site-packages/uvicorn/server.py",
        "venv/Lib/site-packages/uvicorn/lifespan/on.py",
    }
)
STARTUP_POSITION_STATUS = frozenset(
    {
        "sampled",
        "unknown",
        "target_ended",
        "identity_unknown",
        "frame_missing",
        "cancelled",
        "capture_failed",
        "metadata_failed",
    }
)


class StartupPositions:
    """Two slots bound by the business entry thread itself, never by frame enumeration."""

    def __init__(self, entered: float) -> None:
        self.target = threading.current_thread()
        self.ident = threading.get_ident()
        self.native_id = threading.get_native_id()
        self.pid = os.getpid()
        self.entered = entered
        self.next_slot = 0

    def take(
        self,
        now: float,
        *,
        cancelled: bool = False,
        capture: Callable[[], dict[int, FrameType]] = sys._current_frames,
    ) -> dict[str, Any] | None:
        if self.next_slot >= 2:
            return None
        planned = self.entered + (1.5, 3.5)[self.next_slot]
        if not cancelled and now < planned:
            return None
        self.next_slot += 1
        record: dict[str, Any] = {
            "t": now,
            "planned": planned,
            "slot": self.next_slot,
            "pid": self.pid,
            "thread_id": self.ident,
            "native_thread_id": self.native_id,
            "late": now > planned + 0.1,
            "status": "cancelled",
            "source": "unknown",
            "line": None,
        }
        if cancelled:
            return record
        if not self.target.is_alive():
            record["status"] = "target_ended"
            return record
        if (
            os.getpid() != self.pid
            or self.target.ident != self.ident
            or self.target.native_id != self.native_id
        ):
            record["status"] = "identity_unknown"
            return record
        frames = None
        frame = None
        code = None
        record["status"] = "capture_failed"
        try:
            frames = capture()
            # The interface obtains all frames; ONLY this pre-bound key is accessed.
            try:
                frame = frames.get(self.ident)
            finally:
                frames = None
            record["status"] = "frame_missing"
            if frame is not None:
                record["status"] = "metadata_failed"
                code = frame.f_code
                filename, line = code.co_filename, frame.f_lineno
                code = None
                frame = None
                location = {
                    "<frozen importlib._bootstrap>": "python/Lib/importlib/_bootstrap.py",
                    "<frozen importlib._bootstrap_external>": (
                        "python/Lib/importlib/_bootstrap_external.py"
                    ),
                }.get(filename)
                if location is None:
                    location = startup_location(filename)
                record["status"] = "unknown"
                if location in STARTUP_POSITION_SOURCES:
                    record.update(status="sampled", source=location, line=line)
        except Exception:
            # Fixed failure category, no exception/frame/traceback retention.
            pass
        finally:
            code = None
            frame = None
            frames = None
        return record


def startup_observation_record(item: dict[str, Any]) -> bool:
    """Strict phase/binding/position schema, shared by pipe and evidence validation."""
    if type(item.get("t")) not in {int, float} or not 0 <= item["t"] < 10**15:
        return False
    identity = {"pid", "thread_id", "native_thread_id"}
    if not all(type(item.get(key)) is int and 0 < item[key] < 2**64 for key in identity):
        return False
    common = {"t", *identity}
    if set(item) == common | {"phase"}:
        return type(item["phase"]) is str and item["phase"] in STARTUP_PHASES
    if set(item) == common | {"binding"}:
        binding: object = item["binding"]
        return type(binding) is str and binding == "business_entry_thread"
    if set(item) != common | {"planned", "slot", "late", "status", "source", "line"}:
        return False
    return (
        type(item["planned"]) in {int, float}
        and 0 <= item["planned"] < 10**15
        and type(item["slot"]) is int
        and item["slot"] in {1, 2}
        and type(item["late"]) is bool
        and type(item["status"]) is str
        and item["status"] in STARTUP_POSITION_STATUS
        and type(item["source"]) is str
        and (
            (
                item["status"] == "sampled"
                and item["source"] in STARTUP_POSITION_SOURCES
                and type(item["line"]) is int
                and 0 < item["line"] < 10**7
            )
            or (
                item["status"] != "sampled" and item["source"] == "unknown" and item["line"] is None
            )
        )
    )


STARTUP_ERRORS = frozenset(
    {
        "ImportError",
        "ModuleNotFoundError",
        "NameError",
        "AttributeError",
        "TypeError",
        "ValueError",
        "RuntimeError",
        "OSError",
        "PermissionError",
        "FileNotFoundError",
        "ValidationError",
        "SystemExit",
        "KeyboardInterrupt",
        "SyntaxError",
    }
)
STARTUP_CODES = frozenset(
    {
        "step6_native_monitor_owner_mismatch",
        "step6_native_monitor_owner_not_alive",
        "step6_native_precreation_boundary_unavailable",
        "step6_non_loopback_socket",
        "step6_real_env_read_blocked",
        "step6_old_database_read_blocked",
        "step6_startup_context_mismatch",
        "step6_temp_not_registered",
        "step6_temp_resolution_mismatch",
        "step6_machine_ledger_batch_switch",
        "step6_inactive_machine_ledger_write",
        "step6_formal_evidence_runtime_write",
    }
)


def startup_location(filename: str) -> str | None:
    """Keep code locations only; never include arbitrary runtime or data paths."""
    path = Path(os.path.abspath(filename))
    for root, label in (
        (PROJECT_ROOT / "backend/src", "feature/backend/src"),
        (PROJECT_ROOT / "scripts", "feature/scripts"),
        (Path(sys.prefix) / "Lib/site-packages", "venv/Lib/site-packages"),
        (Path(sys.base_prefix) / "Lib", "python/Lib"),
        (FORMAL_PROJECT_ROOT / "backend/src", "formal/backend/src"),
    ):
        if path.is_relative_to(root) and path.suffix in {".py", ".pyd"}:
            relative = path.relative_to(root).as_posix()
            if re.fullmatch(r"[A-Za-z0-9_./-]+", relative):
                return label + "/" + relative
    return None


def startup_redact(line: str) -> dict[str, Any] | None:
    """Allow known structured metadata and error categories, never raw payloads."""
    if line.startswith("F009_STARTUP "):
        try:
            item = json.loads(line.removeprefix("F009_STARTUP "))
        except (ValueError, TypeError):
            return None
        if (
            not isinstance(item, dict)
            or type(item.get("t")) not in {int, float}
            or not 0 <= item["t"] < 10**15
        ):
            return None
        if startup_observation_record(item):
            return item
        if (
            set(item) == {"t", "observation_error"}
            and type(item["observation_error"]) is str
            and item["observation_error"]
            in {
                "product_output_failed",
                "observer_failed",
            }
        ):
            return item
        if set(item) == {"t", "stage", "pid", "ppid"} and (
            isinstance(item["stage"], str)
            and item["stage"] in STARTUP_STAGES
            and all(type(item[key]) is int and item[key] > 0 for key in ("pid", "ppid"))
        ):
            return item
        if set(item) == {"t", "module", "location"} and item["module"] in STARTUP_MODULES:
            location = item["location"]
            if (
                isinstance(location, str)
                and re.fullmatch(
                    r"(?:feature/(?:backend/src|scripts)|formal/backend/src|"
                    r"venv/Lib/site-packages|python/Lib)/[A-Za-z0-9_./-]+\.(?:py|pyd)",
                    location,
                )
                and ".." not in location.split("/")
            ):
                return item
        if set(item) == {"t", "error_class", "code"} and (
            isinstance(item["error_class"], str)
            and item["error_class"] in STARTUP_ERRORS
            and (
                item["code"] is None
                or (isinstance(item["code"], str) and item["code"] in STARTUP_CODES)
            )
        ):
            return item
        return None
    match = re.match(r'\s*File "([^"]+)", line ([0-9]+)', line)
    if match:
        location = startup_location(match[1])
        return {"location": location, "line": int(match[2])} if location else None
    match = re.match(r"(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z]+Error|SystemExit):", line)
    if match and match[1] in STARTUP_ERRORS:
        result: dict[str, Any] = {"error_class": match[1]}
        message = line[match.end() :].strip()
        if message in STARTUP_CODES:
            result["code"] = message
        for marker, description in (
            ("No module named ", "module_not_found"),
            ("cannot import name ", "import_name_unavailable"),
            ("[WinError 10048]", "address_in_use"),
            ("[WinError 10013]", "socket_access_denied"),
        ):
            if message.startswith(marker):
                result["description"] = description
        return result
    for marker, lifecycle in (
        ("INFO:     Started server process [", "uvicorn_process_started"),
        ("INFO:     Waiting for application startup.", "application_starting"),
        ("INFO:     Application startup complete.", "application_started"),
        ("INFO:     Uvicorn running on http://127.0.0.1:8000", "uvicorn_listening"),
        ("INFO:     Shutting down", "uvicorn_stopping"),
    ):
        if line.startswith(marker):
            return {"lifecycle": lifecycle}
    return None


def startup_observation_root(synthetic_root: Path | None) -> Path:
    """Separate the diagnostic destination from a live, already-approved test batch."""
    if synthetic_root is None:
        return STARTUP_ROOT
    if synthetic_root not in BATCH_LIMITS or synthetic_root not in NATIVE_ROOTS:
        raise RuntimeError("step6_startup_context_mismatch")
    return synthetic_root


@contextmanager
def startup_child_observation(
    arguments: list[str],
    *,
    synthetic_root: Path | None = None,
) -> Iterator[Any]:
    """Sample already-loaded modules only in the one explicit diagnostic child."""
    if os.environ.get("F009_STARTUP_DIAGNOSTIC") != "1":
        yield lambda _stage: None
        return
    stop = threading.Event()
    output_lock = threading.Lock()
    seen: set[str] = set()

    failed = False
    entered = time.monotonic()
    positions = StartupPositions(entered)

    def emit(item: dict[str, Any]) -> None:
        nonlocal failed
        with output_lock:
            try:
                if sys.__stderr__ is None:
                    raise OSError("diagnostic output unavailable")
                sys.__stderr__.write(
                    "F009_STARTUP " + json.dumps({"t": time.monotonic(), **item}) + "\n"
                )
                sys.__stderr__.flush()
            except Exception:
                failed = True

    def stage(name: str) -> None:
        emit({"stage": name, "pid": os.getpid(), "ppid": os.getppid()})

    def sample() -> None:
        nonlocal failed
        try:
            while not stop.is_set():
                if record := positions.take(time.monotonic()):
                    emit(record)
                for name in STARTUP_MODULES:
                    module = sys.modules.get(name)
                    if name == "cyber_town.api.__main__":
                        candidate = sys.modules.get("__main__")
                        if getattr(getattr(candidate, "__spec__", None), "name", None) == name:
                            module = candidate
                        if getattr(module, "_startup_observation_failed", False) is True:
                            emit({"observation_error": "product_output_failed"})
                            return
                    filename = getattr(module, "__file__", None)
                    if name not in seen and isinstance(filename, str):
                        location = startup_location(filename)
                        if location:
                            emit({"module": name, "location": location})
                            seen.add(name)
                stop.wait(0.05)
        except Exception:
            failed = True
            emit({"observation_error": "observer_failed"})

    thread = threading.Thread(target=sample, name="f009-startup-modules", daemon=True)
    emit({"t": entered, "stage": "wrapper_entered", "pid": os.getpid(), "ppid": os.getppid()})
    try:
        expected_root = startup_observation_root(synthetic_root)
        if synthetic_root is not None:
            attach_native_monitor(ResourceGuard())
        if arguments != ["-m", "cyber_town.api"] or (
            os.environ.get("F009_NATIVE_ROOT") != str(expected_root)
            or os.environ.get("F009_MACHINE_LEDGER") != str(batch_ledger_path(expected_root))
        ):
            raise RuntimeError("step6_startup_context_mismatch")
        emit(
            {
                "binding": "business_entry_thread",
                "pid": positions.pid,
                "thread_id": positions.ident,
                "native_thread_id": positions.native_id,
            }
        )
        thread.start()
        yield stage
    except BaseException as error:
        error_class = type(error).__name__
        emit(
            {
                "error_class": error_class if error_class in STARTUP_ERRORS else "RuntimeError",
                "code": str(error) if str(error) in STARTUP_CODES else None,
            }
        )
        raise
    finally:
        stop.set()
        if thread.ident is not None:
            thread.join(timeout=1)
            if thread.is_alive():
                failed = True
        while record := positions.take(time.monotonic(), cancelled=True):
            emit(record)
        if failed:
            emit({"observation_error": "observer_failed"})
        stage("wrapper_finished")


class StartupPipe:
    """Continuously drain a pipe; only bounded, classified records reach disk."""

    def __init__(self, source: IO[bytes], target: TextIO, limit: int) -> None:
        self.source, self.target, self.limit = source, target, limit
        self.written = 0
        self.dropped = 0
        self.records: list[dict[str, Any]] = []
        self.error: str | None = None
        self.observation_bytes = {"phase": 0, "position": 0}
        self.thread = threading.Thread(target=self._drain, name="f009-startup-pipe", daemon=True)

    def _drain(self) -> None:
        pending = b""
        discarding = False
        try:
            while chunk := os.read(self.source.fileno(), 4096):
                for part in chunk.splitlines(keepends=True):
                    ended = part.endswith(b"\n")
                    if not discarding:
                        pending += part
                        if len(pending) > 8192:
                            pending = b""
                            discarding = True
                            self.dropped += 1
                    if ended:
                        if not discarding:
                            self._line(pending.decode("utf-8", errors="replace").strip())
                        pending, discarding = b"", False
            if pending and not discarding:
                self._line(pending.decode("utf-8", errors="replace").strip())
        except (OSError, ValueError, RuntimeError):
            self.error = "step6_startup_pipe_read_or_write_failed"

    def _line(self, line: str) -> None:
        record = startup_redact(line)
        if record is None:
            self.dropped += 1
            return
        encoded = json.dumps(record, sort_keys=True) + "\n"
        size = len(encoded.encode("utf-8"))
        category = "phase" if "phase" in record else "position" if "slot" in record else None
        if category is not None:
            self.observation_bytes[category] += size
            if self.observation_bytes[category] > (64 * 1024 if category == "phase" else 16 * 1024):
                self.error = "step6_startup_observation_limit"
                return
        if self.written + size > self.limit or len(self.records) >= 4096:
            self.error = "step6_startup_output_limit"
            return
        if self.error is None:
            self.target.write(encoded)
            self.target.flush()
            self.written += size
            self.records.append(record)

    def start(self) -> None:
        self.thread.start()

    def finish(self) -> None:
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError("step6_startup_pipe_not_drained")
        if self.error:
            raise RuntimeError(self.error)


def startup_classification(returncode: int | None, opened: bool, expired: bool) -> str:
    if returncode is not None:
        return "early_exit"
    if opened:
        return "port_open"
    return "listen_timeout" if expired else "waiting"


def startup_phase_evidence(records: list[dict[str, Any]], *, complete: bool) -> dict[str, Any]:
    bindings = [item for item in records if "binding" in item]
    phases = [item for item in records if "phase" in item]
    positions = [item for item in records if "slot" in item]
    if len(bindings) != 1 or any("observation_error" in item for item in records):
        raise RuntimeError("step6_startup_phase_observation_failed")
    binding = bindings[0]
    if not startup_observation_record(binding):
        raise RuntimeError("step6_startup_phase_identity_mismatch")
    rows = [*phases, *positions]
    if any(
        not startup_observation_record(row)
        or any(row[key] != binding[key] for key in ("pid", "thread_id", "native_thread_id"))
        for row in rows
    ):
        raise RuntimeError("step6_startup_phase_identity_mismatch")
    names = [item["phase"] for item in phases]
    if names != list(STARTUP_PHASES[: len(names)]) or (complete and len(names) != 6):
        raise RuntimeError("step6_startup_phase_sequence_invalid")
    if [item["slot"] for item in positions] != [1, 2] or any(
        item["status"] in {"capture_failed", "metadata_failed", "identity_unknown", "frame_missing"}
        for item in positions
    ):
        raise RuntimeError("step6_startup_position_observation_failed")
    if any(b["t"] < a["t"] for a, b in pairwise(phases)):
        raise RuntimeError("step6_startup_phase_sequence_invalid")
    return {
        "binding": binding,
        "phases": phases,
        "positions": positions,
        "last_completed_marker": names[-1] if names else None,
        "unobserved_markers": list(STARTUP_PHASES[len(names) :]),
        "phase_intervals": [
            {"from": a["phase"], "to": b["phase"], "seconds": b["t"] - a["t"]}
            for a, b in pairwise(phases)
        ],
        "full_phase_sequence": len(names) == 6,
        "locations_are_top_frame_only": True,
    }


def pytest_summary_limit(path: Path, max_bytes: int | None) -> int | None:
    """Keep the identity-root default separate from an explicit caller limit."""
    return (
        min(max_bytes or 1024**2, 1024**2)
        if any(path.is_relative_to(root) for root in IDENTITY_VALIDATION_ROOTS)
        else max_bytes
    )


def write_contract_summary(path: Path, summary: dict[str, Any]) -> None:
    text = json.dumps(summary, sort_keys=True, indent=2)
    if len(text.encode("utf-8")) > 1024**2:
        raise RuntimeError("step6_tool_contract_artifact_limit")
    with validate_path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def write_pytest_summary(
    path: Path, summary: dict[str, Any], *, max_bytes: int | None = None
) -> None:
    for row in summary["results"]:
        if "startup_termination_diagnostic" in row:
            row["startup_termination_diagnostic"] = termination_diagnostic(
                row["startup_termination_diagnostic"]
            )
        if "termination_observations" in row:
            values = row["termination_observations"]
            if type(values) is not list or len(values) > 2:
                raise RuntimeError("step6_termination_diagnostic_invalid")
            row["termination_observations"] = [termination_diagnostic(value) for value in values]
        if "cleanup_report" in row:
            row["cleanup_report"] = cleanup_diagnostic(row["cleanup_report"])
        if "startup_identity_diagnostic" in row:
            row["startup_identity_diagnostic"] = identity_diagnostic(
                row["startup_identity_diagnostic"]
            )
    text = json.dumps(summary, sort_keys=True, indent=2)
    limit = pytest_summary_limit(path, max_bytes)
    if limit is not None and len(text.encode("utf-8")) > limit:
        raise RuntimeError("step6_identity_summary_limit")
    with validate_path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


class StartupProcessAPI:
    """Local Win32 observation only; query handles never carry termination rights."""

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes as w

        self.kernel = kernel_api()
        for name, args, result in (
            ("GetProcessId", [w.HANDLE], w.DWORD),
            ("GetProcessTimes", [w.HANDLE, w.LPVOID, w.LPVOID, w.LPVOID, w.LPVOID], w.BOOL),
            ("QueryFullProcessImageNameW", [w.HANDLE, w.DWORD, w.LPWSTR, w.LPVOID], w.BOOL),
            ("GetExitCodeProcess", [w.HANDLE, w.LPVOID], w.BOOL),
            ("TerminateProcess", [w.HANDLE, w.UINT], w.BOOL),
            ("CreateToolhelp32Snapshot", [w.DWORD, w.DWORD], w.HANDLE),
        ):
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = args, result
        self.ctypes = ctypes

    def open(self, pid: int, *, terminate: bool = False) -> Any:
        handle = self.kernel.OpenProcess(0x1000 | 0x100000 | int(terminate), False, pid)
        if not handle:
            raise RuntimeError("step6_startup_process_handle_unavailable")
        return handle

    def identity(self, handle: Any) -> dict[str, Any]:
        from ctypes import wintypes as w

        c = self.ctypes
        times = [w.FILETIME() for _ in range(4)]
        size, image = w.DWORD(32768), c.create_unicode_buffer(32768)
        pid = int(self.kernel.GetProcessId(handle))
        if not pid:
            code = c.get_last_error()
            raise StartupIdentityError("GetProcessId", code, None)
        if not self.kernel.GetProcessTimes(handle, *(c.byref(item) for item in times)):
            code = c.get_last_error()
            raise StartupIdentityError("GetProcessTimes", code, pid)
        if not self.kernel.QueryFullProcessImageNameW(handle, 0, image, c.byref(size)):
            code = c.get_last_error()
            raise StartupIdentityError("QueryFullProcessImageNameW", code, pid)
        return {
            "pid": pid,
            "created_100ns": (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
            "executable": os.path.normcase(image.value),
        }

    def parent(self, pid: int) -> int:
        """One snapshot on initial binding, not a recurring system process scan."""
        import ctypes
        from ctypes import wintypes as w

        c = self.ctypes

        class Entry(ctypes.Structure):
            _fields_ = [
                ("size", w.DWORD),
                ("usage", w.DWORD),
                ("pid", w.DWORD),
                ("heap", c.c_size_t),
                ("module", w.DWORD),
                ("threads", w.DWORD),
                ("parent", w.DWORD),
                ("priority", w.LONG),
                ("flags", w.DWORD),
                ("executable", w.WCHAR * 260),
            ]

        for name in ("Process32FirstW", "Process32NextW"):
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = [w.HANDLE, c.POINTER(Entry)], w.BOOL
        snapshot = self.kernel.CreateToolhelp32Snapshot(2, 0)
        if snapshot == c.c_void_p(-1).value:
            raise RuntimeError("step6_startup_parent_snapshot_failed")
        entry = Entry()
        entry.size = c.sizeof(entry)
        try:
            available = self.kernel.Process32FirstW(snapshot, c.byref(entry))
            while available:
                if entry.pid == pid:
                    return int(entry.parent)
                available = self.kernel.Process32NextW(snapshot, c.byref(entry))
        finally:
            self.close(snapshot)
        raise RuntimeError("step6_startup_parent_unavailable")

    def state(self, handle: Any) -> dict[str, Any]:
        from ctypes import wintypes as w

        waited = self.kernel.WaitForSingleObject(handle, 0)
        if waited not in {0, 258}:
            raise RuntimeError("step6_startup_process_wait_failed")
        if waited == 258:
            return {"alive": True, "exit_code": None, "exit_code_available": False}
        code = w.DWORD()
        known = bool(self.kernel.GetExitCodeProcess(handle, self.ctypes.byref(code)))
        return {
            "alive": False,
            "exit_code": int(code.value) if known else None,
            "exit_code_available": known,
        }

    def terminate(self, handle: Any) -> int | None:
        if not self.kernel.TerminateProcess(handle, 1):
            return int(self.ctypes.get_last_error())
        return None

    def wait(self, handle: Any) -> None:
        if self.kernel.WaitForSingleObject(handle, 5000) != 0:
            raise RuntimeError("step6_startup_owned_process_not_closed")

    def close(self, handle: Any) -> None:
        self.kernel.CloseHandle(handle)


class StartupProcess:
    """Pin one OS identity, checking ancestry before granting local ownership."""

    def __init__(
        self,
        api: Any,
        pid: int,
        parent_pid: int,
        not_before: int,
        images: set[str],
        *,
        role: str = "unknown",
    ) -> None:
        self.api = api
        self._role = role
        self._expected_pid = pid
        self._last_alive: bool | None = None
        self._last_observed_ns: int | None = None
        self._active_cleanup = False
        self._terminated_by_diagnostic = False
        self.termination_failure: dict[str, Any] | None = None
        self.handle = api.open(pid)
        try:
            identity = self._query_identity(self.handle, "initial_bind", "query")
            parent = api.parent(pid)
            if (
                identity["pid"] != pid
                or parent != parent_pid
                or identity["created_100ns"] < not_before
                or identity["executable"] not in images
            ):
                raise RuntimeError("step6_startup_process_ownership_mismatch")
            self.identity = identity
            self.parent_pid = parent
            self.check(stage="binding_recheck")
        except BaseException:
            api.close(self.handle)
            raise

    def _query_identity(self, handle: Any, stage: str, handle_role: str) -> dict[str, Any]:
        try:
            result: dict[str, Any] = self.api.identity(handle)
            return result
        except StartupIdentityError as error:
            known = getattr(self, "identity", None)
            error.diagnostic = identity_diagnostic(
                {
                    **error.diagnostic,
                    "stage": stage,
                    "process_role": self._role,
                    "handle_role": handle_role,
                    "expected_pid": self._expected_pid,
                    "created_100ns": known["created_100ns"] if known is not None else None,
                    "image_status": "approved" if known is not None else "unknown",
                    "last_alive": self._last_alive,
                    "last_observed_ns": self._last_observed_ns,
                    "active_cleanup": self._active_cleanup,
                }
            )
            raise

    def check(self, *, stage: str = "observation") -> dict[str, Any]:
        # Only a successfully bound, continuously retained handle may observe exit.
        result: dict[str, Any] = self.api.state(self.handle)
        if result["alive"] or stage == "pre_terminate":
            if self._query_identity(self.handle, stage, "query") != self.identity:
                raise RuntimeError("step6_startup_process_identity_changed")
            result = self.api.state(self.handle)
        self._last_alive = result["alive"]
        self._last_observed_ns = time.monotonic_ns()
        return result

    def stop(self, before: dict[str, Any]) -> dict[str, Any]:
        self._active_cleanup = True
        state = self.check(stage="stop_entry")
        terminated = False
        attempted = False
        termination_error: int | None = None
        if state["alive"]:
            handle = self.api.open(self.identity["pid"], terminate=True)
            try:
                if (
                    self._query_identity(handle, "termination_handle", "termination")
                    != self.identity
                ):
                    raise RuntimeError("step6_startup_process_identity_changed")
                # The query-only handle remains open while the termination handle is checked.
                state = self.check(stage="pre_terminate")
                if state["alive"]:
                    attempted = True
                    termination_error = self.api.terminate(handle)
                    if termination_error is None:
                        terminated = True
                        self._terminated_by_diagnostic = True
                    else:
                        # Preserve the already captured ctypes error before the original recheck.
                        self.termination_failure = {
                            "api": "TerminateProcess",
                            "stage": "terminate_returned",
                            "process_role": self._role,
                            "handle_role": "termination",
                            "pid": self.identity["pid"],
                            "parent_pid": self.parent_pid,
                            "created_100ns": self.identity["created_100ns"],
                            "identity_evidence": "initial_binding",
                            "attempt_ns": time.monotonic_ns(),
                            "state_ns": None,
                            "win32_error": termination_error,
                            "after_alive": None,
                            "after_exit_code": None,
                            "after_exit_code_available": None,
                            "active_cleanup": True,
                            "state_error": "none",
                        }
                        try:
                            after = self.api.state(self.handle)
                        except BaseException as problem:
                            self.termination_failure.update(
                                stage="post_terminate_state_failed",
                                state_ns=time.monotonic_ns(),
                                state_error=(
                                    "step6_startup_process_wait_failed"
                                    if type(problem) is RuntimeError
                                    and problem.args == ("step6_startup_process_wait_failed",)
                                    else "unknown"
                                ),
                            )
                            raise
                        self.termination_failure.update(
                            stage="post_terminate_state",
                            state_ns=time.monotonic_ns(),
                            after_alive=after["alive"],
                            after_exit_code=after["exit_code"],
                            after_exit_code_available=after["exit_code_available"],
                        )
                        if after["alive"] and not (
                            self._role == "launcher" and termination_error == 5
                        ):
                            raise StartupTerminationError(self.termination_failure)
                    # A failed call is not a successful termination. Only the retained
                    # handle's signaled state permits completion of exit observation.
            finally:
                self.api.close(handle)
        self.api.wait(self.handle)
        final = self.check(stage="post_wait")
        if (
            self._role == "launcher"
            and termination_error == 5
            and (final["alive"] or not final["exit_code_available"])
        ):
            raise RuntimeError("step6_startup_launcher_exit_observation_missing")
        natural_unknown = self._terminated_by_diagnostic or self.termination_failure is not None
        return {
            "identity": self.identity,
            "identity_evidence": "initial_binding",
            "final_state_source": "retained_query_handle",
            "parent_pid": self.parent_pid,
            "natural_exit_code": None if natural_unknown else final["exit_code"],
            "natural_exit_code_available": (
                False if natural_unknown else final["exit_code_available"]
            ),
            "alive_before_cleanup": before["alive"],
            "termination_attempted": attempted,
            "termination_error_code": termination_error,
            "terminated_by_diagnostic": terminated,
            "final": final,
        }

    def close(self) -> None:
        self.api.close(self.handle)


def startup_bind_business(
    launcher: StartupProcess, pid: int, reported_parent: int, images: set[str]
) -> StartupProcess:
    if pid == launcher.identity["pid"]:
        launcher.check(stage="business_bind")
        if reported_parent != launcher.parent_pid:
            raise RuntimeError("step6_startup_process_ownership_mismatch")
        return launcher
    if (
        reported_parent != launcher.identity["pid"]
        or not launcher.check(stage="business_bind")["alive"]
    ):
        raise RuntimeError("step6_startup_process_ownership_mismatch")
    return StartupProcess(
        launcher.api,
        pid,
        launcher.identity["pid"],
        launcher.identity["created_100ns"],
        images,
        role="business",
    )


def startup_stop_owned(
    process: Any,
    pid: int,
    parent_pid: int,
    *,
    observation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Use only the retained Popen; report calls without inferring their kernel effects."""
    if process.pid != pid or os.getpid() != parent_pid:
        raise RuntimeError("step6_startup_process_identity_mismatch")
    state = observation if observation is not None else {}
    before = process.poll()
    state["exit_code_before_cleanup"] = before
    state["termination_requested"] = before is None
    if before is None:
        process.terminate()
        state["terminate_call_completed"] = True
    process.wait(timeout=5)
    state["wait_returned"] = True
    state["final_exit_code"] = process.returncode
    state["exit_code_available"] = type(process.returncode) is int
    state["terminate_api_succeeded"] = None
    state["signaled_confirmed"] = None
    return state


def startup_report_owned_cleanup(
    process: Any, pid: int, parent_pid: int, record: Callable[[str, object], None]
) -> None:
    """Report the existing test-finally cleanup; no additional poll, wait or retry."""
    import subprocess

    result: dict[str, Any] | None = None
    observation: dict[str, Any] = {}
    attempted = False
    problem: BaseException | None = None
    try:
        if process.poll() is None:
            attempted = True
            result = startup_stop_owned(process, pid, parent_pid, observation=observation)
        else:
            observation.update(
                exit_code_before_cleanup=process.returncode,
                final_exit_code=process.returncode,
            )
            result = observation
    except BaseException as error:
        problem = error
        raise
    finally:
        code = None
        source = "unknown"
        kind = "none" if problem is None else "unknown"
        if isinstance(problem, OSError):
            kind = "oserror"
            if type(problem.winerror if hasattr(problem, "winerror") else None) is int:
                code, source = problem.winerror, "winerror"
            elif type(problem.errno) is int:
                code, source = problem.errno, "errno"
        elif isinstance(problem, subprocess.TimeoutExpired):
            kind = "timeout"
        record(
            "startup_cleanup_report",
            cleanup_diagnostic(
                {
                    "pid": process.pid,
                    "process_role": "launcher",
                    "source": "popen_handle",
                    "observed_ns": time.monotonic_ns(),
                    "attempted": attempted,
                    "cleanup_call_completed": result is not None,
                    "termination_requested": observation.get("termination_requested", False),
                    "terminate_call_completed": observation.get("terminate_call_completed", False),
                    "wait_returned": observation.get("wait_returned", False),
                    "terminate_api_succeeded": None,
                    "signaled_confirmed": None,
                    "exit_code_before_cleanup": observation.get("exit_code_before_cleanup"),
                    "final_exit_code": observation.get("final_exit_code"),
                    "exit_code_available": type(observation.get("final_exit_code")) is int,
                    "failure_kind": kind,
                    "error_code": code,
                    "error_source": source,
                }
            ),
        )


STARTUP_TESTS = tuple(
    "backend/tests/test_f009_step6_qa.py::" + name
    for name in (
        "test_startup_redaction",
        "test_startup_pipe_limit_and_unknown",
        "test_startup_two_pipes_drain",
        "test_startup_classifications",
        "test_startup_owned_process",
        "test_startup_context_and_restoration",
        "test_startup_root_and_owner",
        "test_startup_loaded_module_location",
        "test_startup_actual_owned_child",
        "test_startup_process_observation",
        "test_startup_process_rejects_identity_changes",
        "test_startup_preconditions_order_and_assertions",
        "test_startup_observe_actual_business_child",
    )
)


def startup_write_json(path: Path, payload: Any) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > STARTUP_FILE_LIMITS[path.name]:
        raise RuntimeError("step6_startup_artifact_limit")
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


STARTUP_PRECONDITIONS = (
    "stopped_service",
    "unavailable",
    "duplicate_rejected",
    "non_string_rejected",
    "redirect_rejected",
)


def startup_preconditions(connectivity: Any) -> None:
    """Only the first five original connectivity scenarios and their original assertions."""
    if connectivity._port_is_open() or connectivity._port_is_open(8001):
        raise RuntimeError("step6_startup_port_busy")
    connectivity._run_godot(GODOT_EXE, "stopped_service")
    for mode, scenario in (
        ("always_unavailable", "unavailable"),
        ("duplicate_key", "duplicate_rejected"),
        ("non_string_field", "non_string_rejected"),
    ):
        with connectivity._fixture_server(mode) as server:
            connectivity._run_godot(GODOT_EXE, scenario)
            if server.request_count != 1:
                raise RuntimeError("step6_startup_fixture_request_count")
    with (
        connectivity._fixture_server("always_healthy", 8001) as target,
        connectivity._fixture_server("redirect") as source,
    ):
        connectivity._run_godot(GODOT_EXE, "redirect_rejected")
        if source.request_count != 1:
            raise RuntimeError("step6_startup_fixture_request_count")
        if target.request_count != 0:
            raise RuntimeError("step6_startup_redirect_target_requested")
    if connectivity._port_is_open() or connectivity._port_is_open(8001):
        raise RuntimeError("step6_startup_fixture_listener_remains")
    print("F009_PRECONDITIONS " + json.dumps(list(STARTUP_PRECONDITIONS)))


def startup_require_readiness(
    root: Path, invocation: dict[str, Any], report: dict[str, Any], native: dict[str, Any]
) -> None:
    """Require the exact current preparation, including its completed parent observer."""
    tests = startup_readiness_tests(root)
    extra = (
        COMPOSITION_CODE_FILES if root in {COMPOSITION_STARTUP_ROOT, REPORT_READINESS_ROOT} else ()
    )
    expected_command = [
        sys.executable,
        "-B",
        str(PROJECT_ROOT / "scripts/f009_step6_qa.py"),
        "--batch",
        str(root.relative_to(QA_ROOT) / "pytest"),
        "--output",
        str(root.relative_to(QA_ROOT) / "pytest-summary.json"),
        *tests,
    ]
    rows = report.get("results", [])
    expected = set(tests)
    seen: set[str] = set()
    for row in rows:
        node = row.get("nodeid")
        if (
            not isinstance(node, str)
            or node in seen
            or (node not in expected and node.split("[", 1)[0] not in expected)
            or row.get("outcome") != "passed"
        ):
            raise RuntimeError("step6_startup_readiness_invalid")
        seen.add(node)
    missing = expected - seen - {node.split("[", 1)[0] for node in seen}
    if (
        root not in {*STARTUP_READINESS_ROOTS, COMPOSITION_STARTUP_ROOT, REPORT_READINESS_ROOT}
        or invocation.get("command") != expected_command
        or invocation.get("cwd") != str(PROJECT_ROOT)
        or invocation.get("batch") != str(root)
        or invocation.get("ledger") != str(batch_ledger_path(root))
        or invocation.get("code_fingerprints") != qa_code_fingerprints(extra)
        or invocation.get("native_observer_parallel") is not True
        or invocation.get("fake_only") is not True
        or invocation.get("product_start_attempts") != 0
        or type(invocation.get("observer_pid")) is not int
        or native.get("owner") != {"root": str(root), "pid": invocation.get("observer_pid")}
        or report.get("batch") != str(root.relative_to(QA_ROOT) / "pytest")
        or report.get("exit_code") != 0
        or report.get("boundary_violations") != {}
        or report.get("identity_diagnostic_rejections") != []
        or report.get("termination_diagnostic_rejections") != []
        or report.get("raw_output_retained") is not False
        or report.get("counts") != {"passed": len(rows)}
        or (
            root == REPORT_READINESS_ROOT
            and Counter(row["nodeid"].split("::")[-1].split("[", 1)[0] for row in rows)
            != REPORT_READINESS_COUNTS
        )
        or missing
        or not rows
        or native.get("completed") is not True
        or native.get("overflow") is not False
        or native.get("unknown_paths") != []
        or native.get("reparse") != 0
    ):
        raise RuntimeError("step6_startup_readiness_invalid")


def startup_read_readiness(root: Path) -> dict[str, Any]:
    import hashlib

    if root not in {*STARTUP_READINESS_ROOTS, COMPOSITION_STARTUP_ROOT, REPORT_READINESS_ROOT}:
        raise RuntimeError("step6_startup_readiness_invalid")
    artifacts = {}
    hashes = {}
    for name, limit in (
        ("invocation.json", 64 * 1024),
        ("pytest-summary.json", 1024**2),
        ("native-summary.json", 8 * 1024**2),
        ("native-monitor-ready.json", 4096),
    ):
        path = validate_path(root / name)
        if path.stat().st_size > limit:
            raise RuntimeError("step6_startup_artifact_limit")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        artifacts[name] = space_read_resume_artifact(path, digest)
        hashes[name] = digest
    artifacts["native-summary.json"]["owner"] = artifacts["native-monitor-ready.json"]
    startup_require_readiness(
        root,
        artifacts["invocation.json"],
        artifacts["pytest-summary.json"],
        artifacts["native-summary.json"],
    )
    return {
        "root": str(root),
        "artifact_sha256": hashes,
        "passed": True,
        "counts": artifacts["pytest-summary.json"]["counts"],
        "tests": startup_readiness_tests(root),
        "code_fingerprints": qa_code_fingerprints(
            COMPOSITION_CODE_FILES
            if root in {COMPOSITION_STARTUP_ROOT, REPORT_READINESS_ROOT}
            else ()
        ),
        "synthetic_rerun": False,
        "real_start_attempts": 0,
    }


def startup_entry_failure(
    error: BaseException, role: str, stage: str, event: Callable[..., None]
) -> None:
    """Report fixed entry operations, never arbitrary exception attributes or text."""
    if role not in {"business", "launcher", "unknown"} or stage not in {
        "observation",
        "business_stop",
        "launcher_stop",
        "cleanup",
        "output",
        "port_release",
    }:
        raise RuntimeError("step6_startup_entry_report_invalid")
    fields: dict[str, Any] = {
        "error_kind": "unknown",
        "error_code": None,
        "error_source": "unknown",
    }
    if type(error) is StartupTerminationError:
        fields = {"termination": termination_diagnostic(error.diagnostic)}
    elif type(error) is StartupIdentityError:
        fields = {"identity": identity_diagnostic(error.diagnostic)}
    elif isinstance(error, OSError):
        fields["error_kind"] = "oserror"
        code = getattr(error, "winerror", None)
        if type(code) is int and 0 <= code < 2**32:
            fields.update(error_code=code, error_source="winerror")
        elif type(error.errno) is int and 0 <= error.errno < 2**32:
            fields.update(error_code=error.errno, error_source="errno")
    event("operation_failure", process_role=role, operation=stage, **fields)


def startup_entry_stop(
    process: StartupProcess, before: dict[str, Any], role: str, event: Callable[..., None]
) -> dict[str, Any]:
    """Observe the original single stop call without adding any process operations."""
    try:
        return process.stop(before)
    except BaseException as error:
        startup_entry_failure(error, role, role + "_stop", event)
        raise
    finally:
        if process.termination_failure is not None:
            event("termination_observation", **termination_diagnostic(process.termination_failure))


def startup_finish_output(
    root: Path, readers: list[StartupPipe], ended: float, event: Callable[..., None]
) -> list[dict[str, Any]]:
    """Drain both existing readers and preserve bounded partial evidence on failure."""
    problem: BaseException | None = None
    for reader in readers:
        try:
            reader.finish()
        except BaseException as error:
            if problem is None:
                problem = error
            startup_entry_failure(error, "unknown", "output", event)
    records = [item for reader in readers for item in reader.records]
    bindings = [row for row in records if "binding" in row]
    entered = [row for row in records if row.get("stage") == "wrapper_entered"]
    if len(bindings) == 1 and len(entered) == 1:
        for slot, delay in enumerate((1.5, 3.5), 1):
            planned = entered[0]["t"] + delay
            if planned > ended and not any(row.get("slot") == slot for row in records):
                records.append(
                    {
                        "t": ended,
                        "planned": planned,
                        "slot": slot,
                        **{
                            key: bindings[0][key]
                            for key in ("pid", "thread_id", "native_thread_id")
                        },
                        "late": False,
                        "status": "cancelled",
                        "source": "unknown",
                        "line": None,
                    }
                )
    for name, key in (("phase-events.jsonl", "phase"), ("position-events.jsonl", "slot")):
        encoded = "".join(json.dumps(row, sort_keys=True) + "\n" for row in records if key in row)
        if len(encoded.encode("utf-8")) > STARTUP_FILE_LIMITS[name]:
            raise RuntimeError("step6_startup_observation_limit")
        with (root / name).open("x", encoding="utf-8") as stream:
            stream.write(encoded)
    event(
        "output_preserved",
        readers_finished=problem is None,
        phase_count=sum("phase" in row for row in records),
        position_count=sum("slot" in row for row in records),
        completion_validated=False,
    )
    if problem is not None:
        raise problem
    return records


def run_startup_diagnostic(readiness_root: Path) -> int:
    """Consume completed preparation, then run the authorized five scenes and one startup."""
    import subprocess

    from scripts import connectivity_integration as connectivity

    root = STARTUP_ROOT
    extra = (
        COMPOSITION_CODE_FILES
        if readiness_root in {COMPOSITION_STARTUP_ROOT, REPORT_READINESS_ROOT}
        else ()
    )
    frozen = qa_code_fingerprints(extra)
    evidence_before = EVIDENCE.read_bytes()
    receipt = startup_read_readiness(readiness_root)
    guard = ResourceGuard()
    with native_session(root, guard) as watcher, subprocess_isolation(guard):
        for name in STARTUP_FILE_LIMITS:
            if name != "machine-ledger.md":
                guard.register(root / name, "bounded_startup_diagnostic_metadata")
        startup_write_json(root / "synthetic-summary.json", receipt)
        if frozen != qa_code_fingerprints(extra) or evidence_before != EVIDENCE.read_bytes():
            raise RuntimeError("step6_startup_prelaunch_drift")
        if connectivity._port_is_open() or connectivity._port_is_open(8001):
            raise RuntimeError("step6_startup_port_busy")
        precondition_command = [
            sys.executable,
            "-c",
            "from scripts import connectivity_integration as c; "
            "from scripts.f009_step6_qa import startup_preconditions; startup_preconditions(c)",
        ]
        precode, preout, preerr = run_observed(precondition_command, watcher)
        marker = "F009_PRECONDITIONS " + json.dumps(list(STARTUP_PRECONDITIONS))
        prepassed = precode == 0 and marker in preout.splitlines()
        startup_write_json(
            root / "preconditions-summary.json",
            {
                "command": precondition_command,
                "exit_code": precode,
                "scenarios": STARTUP_PRECONDITIONS,
                "all_original_assertions_passed": prepassed,
                "diagnostics": connectivity_diagnostics(preout, preerr),
                "raw_output_retained": False,
            },
        )
        if not prepassed:
            raise RuntimeError("step6_startup_preconditions_failed")
        if frozen != qa_code_fingerprints(extra) or evidence_before != EVIDENCE.read_bytes():
            raise RuntimeError("step6_startup_prelaunch_drift")
        if connectivity._port_is_open() or connectivity._port_is_open(8001):
            raise RuntimeError("step6_startup_port_busy")
        watcher.check()
        process_api = StartupProcessAPI()
        images = {
            os.path.normcase(os.path.abspath(path))
            for path in (sys.executable, getattr(sys, "_base_executable", sys.executable))
        }
        environment = command_environment(dict(os.environ), root)
        environment.update(APP_HOST="127.0.0.1", APP_PORT="8000", F009_STARTUP_DIAGNOSTIC="1")
        business_command = [sys.executable, "-m", "cyber_town.api"]
        timeline_path = root / "timeline.jsonl"
        with (
            timeline_path.open("x", encoding="utf-8", newline="\n") as timeline,
            (root / "stdout-redacted.txt").open("x", encoding="utf-8", newline="\n") as out,
            (root / "stderr-redacted.txt").open("x", encoding="utf-8", newline="\n") as err,
        ):
            written = 0
            evidence_error: BaseException | None = None

            def event(kind: str, **details: Any) -> None:
                nonlocal written
                line = (
                    json.dumps({"event": kind, "t": time.monotonic(), **details}, sort_keys=True)
                    + "\n"
                )
                written += len(line.encode("utf-8"))
                if written > STARTUP_FILE_LIMITS["timeline.jsonl"]:
                    raise RuntimeError("step6_startup_timeline_limit")
                timeline.write(line)
                timeline.flush()

            def cleanup_event(kind: str, **details: Any) -> None:
                # Only cleanup reporting is deferred; process operations still raise normally.
                nonlocal evidence_error
                try:
                    event(kind, **details)
                except BaseException as error:
                    if evidence_error is None:
                        evidence_error = error

            not_before = time.time_ns() // 100 + 116444736000000000
            process = subprocess.Popen(
                business_command,
                cwd=PROJECT_ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Original deadline begins after Popen returns, before readiness probes.
            wait_started = time.monotonic()
            deadline = wait_started + 5.0
            assert process.stdout is not None and process.stderr is not None
            readers = [
                StartupPipe(process.stdout, out, STARTUP_FILE_LIMITS["stdout-redacted.txt"]),
                StartupPipe(process.stderr, err, STARTUP_FILE_LIMITS["stderr-redacted.txt"]),
            ]
            outcome = "observation_failure"
            observation_ended: float | None = None
            cleanup: dict[str, Any] = {}
            launcher: StartupProcess | None = None
            business: StartupProcess | None = None
            try:
                for reader in readers:
                    reader.start()
                startup_write_json(
                    root / "invocation.json",
                    {
                        "business_command": business_command,
                        "wrapped_command": process.args,
                        "cwd": str(PROJECT_ROOT),
                        "pid": process.pid,
                        "parent_pid": os.getpid(),
                        "owner": json.loads((root / "native-monitor-ready.json").read_text()),
                        "safe_environment": {
                            key: environment[key]
                            for key in (
                                "APP_HOST",
                                "APP_PORT",
                                "CYBER_TOWN_DISABLE_DOTENV",
                                "LLM_PROVIDER",
                                "TEMP",
                                "TMP",
                                "PYTHONDONTWRITEBYTECODE",
                                "UV_CACHE_DIR",
                                "MYPY_CACHE_DIR",
                                "F009_NATIVE_ROOT",
                                "F009_NATIVE_PID",
                                "F009_MACHINE_LEDGER",
                            )
                        },
                        "code_fingerprints": frozen,
                        "readiness": receipt,
                        "wait_started": wait_started,
                        "deadline": deadline,
                        "differences": [
                            "new_batch_cache_ledger",
                            "stream_redaction_and_module_sampling",
                            "os_process_handles_and_initial_parent_snapshots",
                            "five_original_preconditions_but_no_six_engineering_gates",
                            "conditional_six_phase_events_and_two_bound_thread_samples",
                        ],
                    },
                )
                event("spawned", pid=process.pid, parent_pid=os.getpid(), wait_started=wait_started)
                launcher = StartupProcess(
                    process_api, process.pid, os.getpid(), not_before, images, role="launcher"
                )
                event("launcher_identity", **launcher.identity, parent_pid=launcher.parent_pid)
                while time.monotonic() < deadline:
                    if watcher.error:
                        raise RuntimeError(watcher.error)
                    watcher.ledger.check()
                    if any(reader.error for reader in readers):
                        raise RuntimeError("step6_startup_pipe_failure")
                    if any(
                        sum(reader.observation_bytes[key] for reader in readers) > limit
                        for key, limit in (("phase", 64 * 1024), ("position", 16 * 1024))
                    ):
                        raise RuntimeError("step6_startup_observation_limit")
                    if any(
                        "observation_error" in row
                        or row.get("status")
                        in {
                            "capture_failed",
                            "metadata_failed",
                            "identity_unknown",
                            "frame_missing",
                        }
                        for reader in readers
                        for row in reader.records
                    ):
                        raise RuntimeError("step6_startup_phase_observation_failed")
                    stages = [
                        item for reader in readers for item in reader.records if "stage" in item
                    ]
                    if stages and business is None:
                        candidate = stages[0]
                        business = startup_bind_business(
                            launcher, candidate["pid"], candidate["ppid"], images
                        )
                        event(
                            "business_identity", **business.identity, parent_pid=business.parent_pid
                        )
                    if business is not None and any(
                        row["pid"] != business.identity["pid"] or row["ppid"] != business.parent_pid
                        for row in stages
                    ):
                        raise RuntimeError("step6_startup_process_identity_changed")
                    launch_state = launcher.check()
                    business_state = business.check() if business is not None else None
                    before = process.poll()
                    opened = connectivity._port_is_open()
                    event(
                        "probe",
                        poll=before,
                        tcp_open=opened,
                        launcher=launch_state,
                        business=business_state,
                    )
                    outcome = startup_classification(before, opened, False)
                    if not launch_state["alive"] or (
                        business_state is not None and not business_state["alive"]
                    ):
                        outcome = "early_exit"
                    if outcome == "early_exit":
                        break
                    if opened:
                        try:
                            connectivity._read_health()
                            outcome = "health_passed"
                        except (OSError, RuntimeError, ValueError) as error:
                            outcome = "health_failed"
                            event("health_error", error_class=type(error).__name__)
                        event("health", passed=outcome == "health_passed")
                        break
                    time.sleep(0.05)
                else:
                    outcome = startup_classification(process.poll(), False, True)
                event("result", classification=outcome, poll=process.poll())
            except BaseException as error:
                startup_entry_failure(error, "unknown", "observation", cleanup_event)
                raise
            finally:
                observation_ended = time.monotonic()
                cleanup_completed = False
                try:
                    if launcher is not None:
                        launch_before = launcher.check()
                        try:
                            if business is not None:
                                business_before = business.check()
                                cleanup["business"] = startup_entry_stop(
                                    business, business_before, "business", cleanup_event
                                )
                        finally:
                            cleanup["launcher"] = (
                                cleanup["business"]
                                if business is launcher and "business" in cleanup
                                else startup_entry_stop(
                                    launcher, launch_before, "launcher", cleanup_event
                                )
                            )
                        cleanup["cleanup_triggered_by_diagnostic"] = True
                    else:
                        cleanup["launcher_fallback"] = startup_stop_owned(
                            process, process.pid, os.getpid()
                        )
                    process.wait(timeout=5)
                    cleanup_completed = True
                except BaseException as error:
                    startup_entry_failure(error, "unknown", "cleanup", cleanup_event)
                    raise
                finally:
                    pending = sys.exc_info()[1]
                    finalization_error: BaseException | None = None
                    close_error: BaseException | None = None
                    try:
                        if business is not None and business is not launcher:
                            business.close()
                    except BaseException as error:
                        close_error = error
                        finalization_error = error
                        startup_entry_failure(error, "business", "cleanup", cleanup_event)
                    finally:
                        try:
                            if launcher is not None:
                                launcher.close()
                        except BaseException as error:
                            close_error = error
                            finalization_error = error
                            startup_entry_failure(error, "launcher", "cleanup", cleanup_event)
                        cleanup_event(
                            "process_closed",
                            business=cleanup.get("business"),
                            launcher=cleanup.get("launcher"),
                            launcher_fallback=cleanup.get("launcher_fallback"),
                            cleanup_completed=cleanup_completed,
                            final_state_source="stop_return_only_unknown_if_missing",
                        )
                        try:
                            records = startup_finish_output(
                                root, readers, observation_ended, cleanup_event
                            )
                        except BaseException as error:
                            if finalization_error is None:
                                finalization_error = error
                            startup_entry_failure(error, "unknown", "output", cleanup_event)
                        finally:
                            for source in (process.stdout, process.stderr):
                                try:
                                    source.close()
                                except BaseException as error:
                                    if finalization_error is None:
                                        finalization_error = error
                                    startup_entry_failure(error, "unknown", "output", cleanup_event)
                            try:
                                connectivity._wait_for_port(False)
                                cleanup_event("port_released", port=8000)
                            except BaseException as error:
                                if finalization_error is None:
                                    finalization_error = error
                                startup_entry_failure(
                                    error, "unknown", "port_release", cleanup_event
                                )
                                cleanup_event("port_release_unknown", port=8000)
                    try:
                        startup_write_json(
                            root / "evidence-status.json",
                            {
                                "reporting_complete": evidence_error is None,
                                "finalization_complete": finalization_error is None,
                                "cleanup_completed": cleanup_completed,
                                "normal_completion_validated": False,
                            },
                        )
                    except BaseException as error:
                        if evidence_error is None:
                            evidence_error = error
                    propagating = close_error or pending or finalization_error
                    if evidence_error is not None and propagating is not None:
                        propagating.add_note("step6_startup_evidence_incomplete")
                    if close_error is not None:
                        raise close_error
                    if pending is None:
                        if finalization_error is not None:
                            raise finalization_error
                        if evidence_error is not None:
                            raise evidence_error
            # These are normal-completion requirements, never exception-cleanup substitutes.
            watcher.check()
            phase_evidence = startup_phase_evidence(records, complete=outcome == "health_passed")
            if business is None or phase_evidence["binding"]["pid"] != business.identity["pid"]:
                raise RuntimeError("step6_startup_phase_identity_mismatch")
            event("phase_evidence", **phase_evidence)
            event(
                "observations",
                stages=sorted({item["stage"] for item in records if "stage" in item}),
                modules={item["module"]: item["location"] for item in records if "module" in item},
                unobserved_modules=sorted(
                    set(STARTUP_MODULES) - {item["module"] for item in records if "module" in item}
                ),
                dropped_lines=sum(reader.dropped for reader in readers),
                boundary_violations=dict(guard.violations),
            )
            if outcome == "health_passed" and not {
                "owner_verified",
                "guard_active",
                "module_entry",
            }.issubset({item["stage"] for item in records if "stage" in item}):
                raise RuntimeError("step6_startup_missing_child_observation")
            if business is None or any(
                not row["final"]["exit_code_available"]
                for key, row in cleanup.items()
                if key in {"launcher", "business"}
            ):
                raise RuntimeError("step6_startup_business_exit_observation_missing")
        if frozen != qa_code_fingerprints(extra) or evidence_before != EVIDENCE.read_bytes():
            raise RuntimeError("step6_startup_postrun_drift")
        print(json.dumps({"classification": outcome, **cleanup, "real_start_attempts": 1}))
    return 0


IDENTITY_TESTS = tuple(
    "backend/tests/test_f009_step6_qa.py::" + name
    for name in (
        "test_startup_identity_api_failure",
        "test_startup_identity_after_exit",
        "test_startup_process_observation",
        "test_startup_process_rejects_identity_changes",
        "test_startup_exited_initial_binding_rejected",
        "test_startup_live_identity_failure",
        "test_startup_retained_handle_state_api",
        "test_startup_exit_transition",
        "test_startup_exit_batch_contract",
        "test_startup_termination_error_capture",
        "test_startup_exit_during_termination",
        "test_startup_identity_report_chain",
        "test_startup_identity_report_rejects_invalid_fields",
        "test_startup_identity_summary_limit",
        "test_qa_canonical_diagnostic_reports_concurrent_failures_without_cross_talk",
        "test_startup_report_module_source_rejection",
        "test_startup_real_pytest_report_path",
        "test_startup_observe_actual_business_child[False]",
        "test_startup_observe_actual_business_child[True]",
    )
)

STARTUP_READINESS_TESTS = (
    "backend/tests/test_f009_step6_qa.py::test_startup_phase_context_separation",
    "backend/tests/test_f009_step6_qa.py::test_startup_position_access_contract",
    "backend/tests/test_f009_step6_qa.py::test_startup_phase_report_contract",
    "backend/tests/test_f009_step6_qa.py::test_startup_actual_product_phase_path",
    *IDENTITY_TESTS[:-2],
    *(
        node
        for node in STARTUP_TESTS
        if node not in {item.split("[", 1)[0] for item in IDENTITY_TESTS}
    ),
    "backend/tests/test_f009_step6_qa.py::test_startup_readiness_contract",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_binding_cannot_switch_active_ledger",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_prior_ledgers_are_read_only",
    "backend/tests/test_f009_step6_qa.py::test_qa_space_resume_artifact_integrity",
    *IDENTITY_TESTS[-2:],
)


COMPOSITION_CODE_FILES = (
    "backend/src/cyber_town/api/composition.py",
    "backend/tests/test_deepseek_provider.py",
    "backend/tests/test_long_term_dialogue_integration.py",
)
COMPOSITION_STARTUP_TESTS = (
    *(
        "backend/tests/test_f009_step6_qa.py::" + name
        for name in (
            "test_composition_startup_readiness_contract",
            "test_startup_root_and_owner",
            "test_startup_phase_context_separation",
            "test_qa_batch_binding_cannot_switch_active_ledger",
            "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
            "test_qa_batch_prior_ledgers_are_read_only",
            "test_startup_phase_report_contract",
            "test_startup_actual_product_phase_path",
            "test_startup_redaction",
            "test_startup_pipe_limit_and_unknown",
            "test_startup_two_pipes_drain",
            "test_startup_classifications",
            "test_startup_preconditions_order_and_assertions",
            "test_startup_loaded_module_location",
            "test_startup_real_pytest_report_path",
            "test_startup_exit_transition",
        )
    ),
    *IDENTITY_TESTS[-2:],
)
TERMINATION_TESTS = (
    *(
        "backend/tests/test_f009_step6_qa.py::" + name
        for name in (
            "test_termination_batch_contract",
            "test_qa_batch_binding_cannot_switch_active_ledger",
            "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
            "test_qa_batch_prior_ledgers_are_read_only",
            "test_startup_termination_error_capture",
            "test_startup_exit_during_termination",
            "test_startup_exit_transition",
            "test_startup_process_rejects_identity_changes",
            "test_startup_identity_after_exit",
            "test_startup_exited_initial_binding_rejected",
            "test_startup_cleanup_reporting",
            "test_termination_schema_and_limits",
            "test_cleanup_schema_and_limits",
            "test_termination_report_isolation",
            "test_startup_report_module_source_rejection",
            "test_startup_real_pytest_report_path",
            "test_termination_real_pytest_report_path",
        )
    ),
    *IDENTITY_TESTS[-2:],
)
COMPOSITION_TESTS = (
    *(
        "backend/tests/test_f009_step6_qa.py::" + name
        for name in (
            "test_composition_batch_configuration_and_owner",
            "test_qa_batch_binding_cannot_switch_active_ledger",
            "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
            "test_qa_batch_prior_ledgers_are_read_only",
            "test_qa_canonical_diagnostic_reports_concurrent_failures_without_cross_talk",
            "test_startup_real_pytest_report_path",
            "test_startup_exit_transition",
        )
    ),
    *(
        "backend/tests/test_deepseek_provider.py::" + name
        for name in (
            "test_composition_sdk_import_contract_in_fresh_process",
            "test_composition_validates_before_sdk_construction",
            "test_composition_preserves_sdk_arguments_and_constructor_error",
            "test_disabled_composition_never_constructs_a_provider",
            "test_enabled_composition_accepts_only_an_injected_offline_test_provider",
            "test_offline_composition_resolves_its_database_inside_pytest_isolation",
            "test_composed_offline_provider_is_reachable_through_the_dialogue_route",
        )
    ),
    "backend/tests/test_long_term_dialogue_integration.py::"
    "test_default_application_entrypoint_wires_memory_without_external_provider_calls",
    *IDENTITY_TESTS[-2:],
)


REPORT_READINESS_TESTS = (
    "backend/tests/test_f009_step6_qa.py::test_entry_readiness_contract",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_reporting",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_cleanup_failures",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_completion_requirements",
    "backend/tests/test_f009_step6_qa.py::test_startup_entry_evidence_failure",
    "backend/tests/test_f009_step6_qa.py::test_popen_cleanup_report_semantics",
    *(
        node
        for node in COMPOSITION_STARTUP_TESTS[:-2]
        if not node.endswith("test_composition_startup_readiness_contract")
    ),
    *(
        node
        for node in TERMINATION_TESTS[:-2]
        if node not in COMPOSITION_STARTUP_TESTS
        and not node.endswith("test_termination_batch_contract")
    ),
    *IDENTITY_TESTS[-2:],
)


REPORT_READINESS_COUNTS = {
    "test_startup_phase_context_separation": 5,
    "test_startup_phase_report_contract": 8,
    "test_startup_actual_product_phase_path": 18,
    "test_startup_redaction": 8,
    "test_startup_pipe_limit_and_unknown": 1,
    "test_startup_two_pipes_drain": 1,
    "test_startup_classifications": 6,
    "test_startup_root_and_owner": 3,
    "test_startup_loaded_module_location": 1,
    "test_startup_process_rejects_identity_changes": 2,
    "test_startup_preconditions_order_and_assertions": 6,
    "test_startup_identity_after_exit": 4,
    "test_startup_exited_initial_binding_rejected": 5,
    "test_startup_exit_transition": 4,
    "test_startup_termination_error_capture": 2,
    "test_startup_exit_during_termination": 4,
    "test_startup_report_module_source_rejection": 4,
    "test_startup_real_pytest_report_path": 10,
    "test_entry_readiness_contract": 20,
    "test_startup_entry_reporting": 9,
    "test_startup_entry_cleanup_failures": 10,
    "test_startup_entry_completion_requirements": 3,
    "test_startup_entry_evidence_failure": 3,
    "test_popen_cleanup_report_semantics": 4,
    "test_startup_cleanup_reporting": 6,
    "test_termination_real_pytest_report_path": 14,
    "test_termination_schema_and_limits": 7,
    "test_cleanup_schema_and_limits": 9,
    "test_termination_report_isolation": 1,
    "test_startup_observe_actual_business_child": 2,
    "test_qa_batch_binding_cannot_switch_active_ledger": 1,
    "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked": 1,
    "test_qa_batch_prior_ledgers_are_read_only": 1,
}


CLEANUP_CONTROL_TESTS = (
    *(
        "backend/tests/test_f009_step6_qa.py::" + name
        for name in (
            "test_cleanup_control_batch_contract",
            "test_qa_batch_binding_cannot_switch_active_ledger",
            "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
            "test_qa_batch_prior_ledgers_are_read_only",
            "test_startup_entry_reporting",
            "test_startup_entry_cleanup_failures",
            "test_startup_entry_completion_requirements",
            "test_startup_entry_evidence_failure",
            "test_startup_two_pipes_drain",
            "test_termination_report_isolation",
            "test_startup_report_module_source_rejection",
            "test_startup_real_pytest_report_path",
            "test_termination_real_pytest_report_path",
        )
    ),
    *IDENTITY_TESTS[-2:],
)


CLEANUP_SEMANTICS_TESTS = (
    *(
        "backend/tests/test_f009_step6_qa.py::" + name
        for name in (
            "test_cleanup_semantics_batch_contract",
            "test_qa_batch_binding_cannot_switch_active_ledger",
            "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
            "test_qa_batch_prior_ledgers_are_read_only",
            "test_startup_owned_process",
            "test_startup_cleanup_reporting",
            "test_popen_cleanup_report_semantics",
            "test_cleanup_schema_and_limits",
        )
    ),
    *(
        "backend/tests/test_f009_step6_qa.py::test_termination_real_pytest_report_path"
        + f"[{case}-{mode}]"
        for case in ("cleanup_success", "cleanup_failure")
        for mode in ("import", "runpy")
    ),
)


LAUNCHER_EXIT_TESTS = (
    *(
        "backend/tests/test_f009_step6_qa.py::" + name
        for name in (
            "test_launcher_exit_batch_contract",
            "test_qa_batch_binding_cannot_switch_active_ledger",
            "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked",
            "test_qa_batch_prior_ledgers_are_read_only",
            "test_launcher_exit_wait_contract",
            "test_startup_process_observation",
            "test_startup_process_rejects_identity_changes",
            "test_startup_exited_initial_binding_rejected",
            "test_startup_live_identity_failure",
            "test_startup_retained_handle_state_api",
            "test_startup_identity_after_exit",
            "test_startup_exit_transition",
            "test_startup_termination_error_capture",
            "test_startup_exit_during_termination",
            "test_popen_cleanup_report_semantics",
            "test_startup_cleanup_reporting",
            "test_termination_schema_and_limits",
            "test_cleanup_schema_and_limits",
            "test_startup_real_pytest_report_path",
            "test_termination_real_pytest_report_path",
            "test_termination_wait_real_pytest_report_path",
        )
    ),
    *IDENTITY_TESTS[-2:],
)

LAUNCHER_EXIT_COUNTS = {
    "test_launcher_exit_batch_contract": 1,
    "test_qa_batch_binding_cannot_switch_active_ledger": 1,
    "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked": 1,
    "test_qa_batch_prior_ledgers_are_read_only": 1,
    "test_launcher_exit_wait_contract": 12,
    "test_startup_process_observation": 8,
    "test_startup_process_rejects_identity_changes": 2,
    "test_startup_exited_initial_binding_rejected": 5,
    "test_startup_live_identity_failure": 12,
    "test_startup_retained_handle_state_api": 4,
    "test_startup_identity_after_exit": 4,
    "test_startup_exit_transition": 4,
    "test_startup_termination_error_capture": 2,
    "test_startup_exit_during_termination": 4,
    "test_popen_cleanup_report_semantics": 4,
    "test_startup_cleanup_reporting": 6,
    "test_termination_schema_and_limits": 7,
    "test_cleanup_schema_and_limits": 9,
    "test_startup_real_pytest_report_path": 10,
    "test_termination_real_pytest_report_path": 14,
    "test_termination_wait_real_pytest_report_path": 6,
    "test_startup_observe_actual_business_child": 2,
}


OBSERVER_FAILURE_COUNTS = {
    "test_observer_failure_batch_contract": 1,
    "test_qa_batch_binding_cannot_switch_active_ledger": 1,
    "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked": 1,
    "test_qa_batch_prior_ledgers_are_read_only": 1,
    "test_qa_native_observer_overflow_is_a_hard_failure": 1,
    "test_observer_receive_failure_contract": 6,
    "test_observer_failure_fields": 1,
    "test_observer_finish_failure_contract": 10,
    "test_observer_session_failure_restoration": 2,
    "test_observer_quality_failure_report": 5,
    "test_observer_command_failure_order": 3,
    "test_qa_ledger_native_inventory_after_real_observer": 1,
    "test_observer_actual_command_evidence": 2,
}
OBSERVER_FAILURE_TESTS = tuple(
    "backend/tests/test_f009_step6_qa.py::" + name for name in OBSERVER_FAILURE_COUNTS
)


OBSERVER_CAPACITY_COUNTS = {
    "test_observer_capacity_batch_contract": 1,
    "test_qa_contract_context_requires_current_live_owner": 5,
    "test_qa_contract_ledger_registration_precedes_operation": 1,
    "test_observer_failure_batch_contract": 1,
    "test_qa_batch_binding_cannot_switch_active_ledger": 1,
    "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked": 1,
    "test_qa_batch_prior_ledgers_are_read_only": 1,
    "test_observer_capacity_real_constructor": 1,
    "test_observer_capacity_large_notification_block": 4,
    "test_qa_native_notification_corruption_fails_closed": 3,
    "test_qa_native_observer_overflow_is_a_hard_failure": 1,
    "test_observer_receive_failure_contract": 6,
    "test_observer_failure_fields": 1,
    "test_observer_finish_failure_contract": 10,
    "test_observer_session_failure_restoration": 2,
    "test_observer_quality_failure_report": 5,
    "test_observer_command_failure_order": 3,
    "test_qa_ledger_native_inventory_after_real_observer": 1,
    "test_observer_actual_command_evidence": 2,
    "test_qa_contract_ledger_half_line_is_retained_until_complete": 1,
    "test_qa_contract_ledger_write_failure_does_not_grant_registration": 1,
    "test_qa_contract_ledger_concurrent_writers_visible_to_real_observer": 1,
    "test_qa_repeat_registration_reconciles_only_registered_retired_sqlite_sidecar": 2,
    "test_qa_retired_sqlite_registration_rejects_incomplete_prior_registration": 2,
    "test_qa_late_sqlite_notification_requires_registered_absent_sidecar": 8,
    "test_qa_real_sqlite_journal_lifecycles_keep_guarded_notifications": 1,
    "test_qa_real_notification_rename_checks_preregistered_paths": 1,
    "test_qa_uv_retired_notification_requires_observed_removal_and_stable_anchor": 17,
    "test_qa_godot_rename_notification_strictly_revalidates_paths_and_identity": 26,
    "test_qa_canonical_failure_preserves_original_notification": 1,
    "test_observer_capacity_real_load": 1,
}
OBSERVER_CAPACITY_TESTS = tuple(
    "backend/tests/test_f009_step6_qa.py::" + name for name in OBSERVER_CAPACITY_COUNTS
)


MIGRATION_DIGEST_CODE_FILES = (
    "scripts/f009_step5_compact_preflight.py",
    "backend/tests/test_storage_migrations_v4.py",
    "backend/tests/test_compact_storage_step5.py",
    "backend/tests/test_sqlite_control.py",
)
MIGRATION_DIGEST_COUNTS = {
    ("backend/tests/test_f009_step6_qa.py::test_migration_digest_batch_contract"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::test_qa_contract_context_requires_current_live_owner"
    ): 5,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_contract_ledger_registration_precedes_operation"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_batch_binding_cannot_switch_active_ledger"): 1,
    (
        "backend/tests/test_f009_step6_qa.py::"
        "test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked"
    ): 1,
    ("backend/tests/test_f009_step6_qa.py::test_qa_batch_prior_ledgers_are_read_only"): 1,
    ("backend/tests/test_f009_step6_qa.py::test_migration_digest_real_report"): 4,
    ("backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_representations"): 8,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_change_is_visible"
    ): 3,
    (
        "backend/tests/test_storage_migrations_v4.py::test_migration_digest_scope_rejects_invalid"
    ): 27,
    (
        "backend/tests/test_storage_migrations_v4.py::"
        "test_migration_digest_unknown_blob_is_not_converted"
    ): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::"
        "test_migration_digest_keeps_non_scope_coverage"
    ): 4,
    (
        "backend/tests/test_storage_migrations_v4.py::"
        "test_migration_digest_clock_exclusion_is_explicit"
    ): 3,
    ("backend/tests/test_storage_migrations_v4.py::test_version_four_is_append_only_registered"): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::"
        "test_populated_v3_upgrade_preserves_decoded_rows_and_constraints"
    ): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::"
        "test_migration_interruption_rolls_back_all_prior_changes"
    ): 8,
    (
        "backend/tests/test_storage_migrations_v4.py::"
        "test_invalid_old_uuid_aborts_entire_observability_upgrade"
    ): 1,
    (
        "backend/tests/test_compact_storage_step5.py::"
        "test_synthetic_compact_layout_has_exact_decoded_rows"
    ): 1,
    (
        "backend/tests/test_compact_storage_step5.py::test_compact_rebuild_is_atomic_at_each_table"
    ): 4,
    (
        "backend/tests/test_compact_storage_step5.py::"
        "test_invalid_legacy_uuid_fails_instead_of_repairing_or_dropping"
    ): 1,
    (
        "backend/tests/test_sqlite_control.py::test_v9_product_upgrade_preserves_rows_and_restarts"
    ): 2,
    (
        "backend/tests/test_storage_migrations_v4.py::"
        "test_repository_populated_upgrade_repeat_and_cli_boundary"
    ): 2,
}
MIGRATION_DIGEST_TESTS = tuple(MIGRATION_DIGEST_COUNTS)
TOOL_CODE_FILES = (*COMPOSITION_CODE_FILES, *MIGRATION_DIGEST_CODE_FILES)
S1_READINESS_TESTS = (
    "backend/tests/test_f009_step6_qa.py::test_observer_quality_failure_report",
    "backend/tests/test_f009_step6_qa.py::test_observer_command_failure_order",
    "backend/tests/test_f009_step6_qa.py::test_observer_actual_command_evidence",
    "backend/tests/test_f009_step6_qa.py::test_native_drain_single_post_ack_check",
    "backend/tests/test_f009_step6_qa.py::"
    "test_qa_subprocess_wrapper_restores_and_preserves_python_arguments",
    "backend/tests/test_f009_step6_qa.py::test_qa_command_scope_restores_environment_and_temp",
    "backend/tests/test_f009_step6_qa.py::"
    "test_qa_contract_ledger_rejects_changed_metadata_without_modifying_evidence",
    "backend/tests/test_f009_step6_qa.py::test_qa_batch_prior_ledgers_are_read_only",
    "backend/tests/test_f009_step6_qa.py::"
    "test_qa_canonical_diagnostic_keeps_rejection_and_redacts_target",
    "backend/tests/test_f009_step6_qa.py::test_qa_quality_preflight_stops_before_resource_creation",
    "backend/tests/test_f009_step6_qa.py::test_s1_fixture_and_call_signature_matrix",
    "backend/tests/test_f009_step6_qa.py::test_s1_runner_success_and_controlled_failure",
    "backend/tests/test_f009_step6_qa.py::"
    "test_s1_original_failure_precedence_and_not_run_reporting",
    "backend/tests/test_f009_step6_qa.py::test_s1_process_port_environment_temp_restoration",
    "backend/tests/test_f009_step6_qa.py::test_s1_current_root_allowed_and_external_root_rejected",
    "backend/tests/test_f009_step6_qa.py::test_s2_current_readiness_receipt",
    "backend/tests/test_f009_step6_qa.py::test_s2_root_and_readiness_binding",
    "backend/tests/test_f009_step6_qa.py::test_qa_ledger_sources_separate_lifecycles",
)
S1_READINESS_COUNTS = {
    S1_READINESS_TESTS[0]: 5,
    S1_READINESS_TESTS[1]: 3,
    S1_READINESS_TESTS[2]: 2,
    S1_READINESS_TESTS[3]: 1,
    S1_READINESS_TESTS[4]: 1,
    S1_READINESS_TESTS[5]: 1,
    S1_READINESS_TESTS[6]: 3,
    S1_READINESS_TESTS[7]: 1,
    S1_READINESS_TESTS[8]: 4,
    S1_READINESS_TESTS[9]: 1,
    S1_READINESS_TESTS[10]: 1,
    S1_READINESS_TESTS[11]: 1,
    S1_READINESS_TESTS[12]: 1,
    S1_READINESS_TESTS[13]: 1,
    S1_READINESS_TESTS[14]: 1,
    S1_READINESS_TESTS[15]: 10,
    S1_READINESS_TESTS[16]: 1,
    S1_READINESS_TESTS[17]: 5,
}


def identity_validation_command(root: Path, tests: tuple[str, ...]) -> list[str]:
    """Build the one protected pytest command used by identity and readiness batches."""
    return [
        sys.executable,
        "-B",
        str(PROJECT_ROOT / "scripts/f009_step6_qa.py"),
        "--batch",
        str(root.relative_to(QA_ROOT) / "pytest"),
        "--output",
        str(root.relative_to(QA_ROOT) / "pytest-summary.json"),
        *tests,
    ]


def startup_readiness_tests(root: Path) -> tuple[str, ...]:
    if root == REPORT_READINESS_ROOT:
        return REPORT_READINESS_TESTS
    if root == COMPOSITION_STARTUP_ROOT:
        return COMPOSITION_STARTUP_TESTS
    return STARTUP_READINESS_TESTS


def run_identity_validation(
    root: Path = IDENTITY_ROOT,
    *,
    tests_override: tuple[str, ...] | None = None,
    extra_override: tuple[str, ...] = (),
    result: dict[str, Any] | None = None,
) -> int:
    """One protected synthetic collection; never calls a product diagnostic entrypoint."""
    if root not in IDENTITY_VALIDATION_ROOTS:
        raise RuntimeError("step6_identity_validation_root_unapproved")
    tests = STARTUP_READINESS_TESTS if root in STARTUP_READINESS_ROOTS else IDENTITY_TESTS
    extra: tuple[str, ...] = (
        COMPOSITION_CODE_FILES
        if root in {COMPOSITION_ROOT, COMPOSITION_STARTUP_ROOT, REPORT_READINESS_ROOT}
        else ()
    )
    if root == COMPOSITION_ROOT:
        tests = COMPOSITION_TESTS
    elif root == COMPOSITION_STARTUP_ROOT:
        tests = COMPOSITION_STARTUP_TESTS
    elif root == TERMINATION_ROOT:
        tests = TERMINATION_TESTS
    elif root == REPORT_READINESS_ROOT:
        tests = REPORT_READINESS_TESTS
    elif root == CLEANUP_CONTROL_ROOT:
        tests = CLEANUP_CONTROL_TESTS
    elif root == CLEANUP_SEMANTICS_ROOT:
        tests = CLEANUP_SEMANTICS_TESTS
    elif root == LAUNCHER_EXIT_ROOT:
        tests = LAUNCHER_EXIT_TESTS
    elif root == OBSERVER_FAILURE_ROOT:
        tests = OBSERVER_FAILURE_TESTS
    elif root == OBSERVER_CAPACITY_ROOT:
        tests = OBSERVER_CAPACITY_TESTS
    elif root == MIGRATION_DIGEST_ROOT:
        tests = MIGRATION_DIGEST_TESTS
        extra = MIGRATION_DIGEST_CODE_FILES
    if tests_override is not None:
        if root not in s1_runtime.S1_ROOTS or tests_override != S1_READINESS_TESTS:
            raise RuntimeError("step6_s1_test_selection_not_approved")
        tests = tests_override
    extra = (*extra, *extra_override)
    frozen = qa_code_fingerprints(extra)
    evidence = EVIDENCE.read_bytes()
    guard = ResourceGuard()
    with native_session(root, guard) as watcher, subprocess_isolation(guard):
        event_name = (
            "termination-events.jsonl"
            if root
            in {
                TERMINATION_ROOT,
                REPORT_READINESS_ROOT,
                CLEANUP_CONTROL_ROOT,
                CLEANUP_SEMANTICS_ROOT,
                LAUNCHER_EXIT_ROOT,
            }
            else "identity-events.jsonl"
        )
        for name in ("invocation.json", event_name, "pytest-summary.json"):
            guard.register(root / name, "bounded_identity_validation_metadata")
        command = identity_validation_command(root, tests)
        invocation = {
            "command": command,
            "cwd": str(PROJECT_ROOT),
            "code_fingerprints": frozen,
            "batch": str(root),
            "ledger": str(batch_ledger_path(root)),
            "observer_pid": os.getpid(),
            "native_observer_parallel": True,
            "fake_only": True,
            "product_start_attempts": 0,
        }
        payload = json.dumps(invocation, sort_keys=True, indent=2)
        if len(payload.encode("utf-8")) > 64 * 1024:
            raise RuntimeError("step6_identity_artifact_limit")
        with (root / "invocation.json").open("x", encoding="utf-8") as stream:
            stream.write(payload)
        command_state: dict[str, object] = {}
        if result is not None:
            result["command_state"] = command_state
        code, _, _ = run_observed(command, watcher, status=command_state)
        report = json.loads((root / "pytest-summary.json").read_text(encoding="utf-8"))
        if result is not None:
            result.update(code=code, pytest_summary=report)
        events = [
            identity_diagnostic(row["startup_identity_diagnostic"])
            for row in report["results"]
            if "startup_identity_diagnostic" in row
        ]
        if root in {
            TERMINATION_ROOT,
            REPORT_READINESS_ROOT,
            CLEANUP_CONTROL_ROOT,
            CLEANUP_SEMANTICS_ROOT,
            LAUNCHER_EXIT_ROOT,
        }:
            fields = {
                "startup_termination_diagnostic",
                "termination_observations",
                "cleanup_report",
            }
            events = [
                {
                    "nodeid": row["nodeid"],
                    "phase": row["phase"],
                    **{key: row[key] for key in fields if key in row},
                }
                for row in report["results"]
                if fields.intersection(row)
            ]
        encoded = "".join(json.dumps(event, sort_keys=True) + "\n" for event in events)
        if len(encoded.encode("utf-8")) > 1024**2:
            raise RuntimeError("step6_identity_artifact_limit")
        with (root / event_name).open("x", encoding="utf-8") as stream:
            stream.write(encoded)
        watcher.check()
        if frozen != qa_code_fingerprints(extra) or evidence != EVIDENCE.read_bytes():
            raise RuntimeError("step6_identity_validation_drift")
        failed = [row for row in report["results"] if row["outcome"] != "passed"]
        if code or report["boundary_violations"] or failed:
            raise RuntimeError("step6_identity_validation_failed")
        expected = set(tests)
        for row in report["results"]:
            expected.discard(row["nodeid"])
            expected.discard(row["nodeid"].split("[", 1)[0])
        if expected:
            raise RuntimeError("step6_identity_validation_missing_tests")
        if root == LAUNCHER_EXIT_ROOT and (
            report.get("identity_diagnostic_rejections") != []
            or report.get("termination_diagnostic_rejections") != []
            or Counter(row["nodeid"].split("::")[-1].split("[", 1)[0] for row in report["results"])
            != LAUNCHER_EXIT_COUNTS
        ):
            raise RuntimeError("step6_launcher_exit_validation_incomplete")
        if root == REPORT_READINESS_ROOT and (
            report.get("identity_diagnostic_rejections") != []
            or report.get("termination_diagnostic_rejections") != []
            or Counter(row["nodeid"].split("::")[-1].split("[", 1)[0] for row in report["results"])
            != REPORT_READINESS_COUNTS
        ):
            raise RuntimeError("step6_startup_readiness_invalid")
        if root == OBSERVER_FAILURE_ROOT and (
            Counter(row["nodeid"].split("::")[-1].split("[", 1)[0] for row in report["results"])
            != OBSERVER_FAILURE_COUNTS
        ):
            raise RuntimeError("step6_observer_failure_validation_incomplete")
        if root == OBSERVER_CAPACITY_ROOT and (
            Counter(row["nodeid"].split("::")[-1].split("[", 1)[0] for row in report["results"])
            != OBSERVER_CAPACITY_COUNTS
        ):
            raise RuntimeError("step6_observer_capacity_validation_incomplete")
        if root == MIGRATION_DIGEST_ROOT:
            actual = Counter(row["nodeid"].split("[", 1)[0] for row in report["results"])
            if actual != MIGRATION_DIGEST_COUNTS:
                raise RuntimeError("step6_migration_digest_validation_incomplete")
            require_migration_digest_stage_evidence(report)
    return 0


def require_migration_digest_stage_evidence(report: dict[str, Any]) -> None:
    expected = {
        "backend/tests/test_storage_migrations_v4.py::"
        "test_repository_populated_upgrade_repeat_and_cli_boundary[" + variant + "]"
        for variant in ("control", "observability")
    }
    rows = [row for row in report["results"] if row["nodeid"] in expected]
    if len(rows) != 2 or {row["nodeid"] for row in rows} != expected:
        raise RuntimeError("step6_migration_digest_stage_evidence_missing")
    for row in rows:
        stages = [value for key, value in row["metadata"] if key == "migration_stage"]
        if stages != [
            "initialize",
            "initialize_returned",
            "first_digest",
            "first_digest_returned",
            "repeat_initialize",
            "repeat_initialize_returned",
            "repeat_digest",
            "repeat_digest_returned",
        ]:
            raise RuntimeError("step6_migration_digest_stage_evidence_missing")


def readiness_snapshot() -> dict[str, object]:
    """Capture only opaque comparison values needed by the S1 closeout."""
    return {
        "ports": s1_runtime.port_state(),
        "environment": s1_runtime.environment_fingerprint(),
        "temp": s1_runtime.temp_fingerprint(),
        "evidence": s1_runtime.file_fingerprints((*HISTORICAL_LEDGERS, EVIDENCE)),
    }


def write_readiness_report(root: Path, report: dict[str, Any]) -> None:
    """Register and create the final bounded report after native-session restoration."""
    output = validate_path(root / "tool-readiness-summary.json")
    payload = s1_runtime.encode_readiness_report(report)
    encoded = payload.encode("utf-8")
    guard = ResourceGuard(ledger=machine_ledger(root))
    guard.register(output, "bounded_s1_tool_readiness_report")
    batch_bytes = len(encoded) + sum(
        path.stat().st_size for path in root.rglob("*") if path.is_file()
    )
    total_bytes = len(encoded) + sum(
        path.stat().st_size for path in RECOVERY_ROOT.rglob("*") if path.is_file()
    )
    require_batch_capacity(root, batch_bytes, total_bytes)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)


def run_tool_readiness(raw_root: str) -> int:
    """Run exactly one approved S1 readiness collection; never dispatch full quality."""
    root = s1_runtime.authorize_readiness_root(raw_root, validate_path)
    before = readiness_snapshot()
    result: dict[str, Any] = {}
    primary: BaseException | None = None
    try:
        run_identity_validation(
            root,
            tests_override=S1_READINESS_TESTS,
            extra_override=("scripts/f009_step6_runtime.py",),
            result=result,
        )
    except BaseException as error:
        primary = error
    try:
        after = readiness_snapshot()
    except BaseException as error:
        primary = primary or error
        after = {}
    report = s1_runtime.build_readiness_report(
        root=root,
        selected=S1_READINESS_TESTS,
        pytest_summary=result.get("pytest_summary"),
        command_state=result.get("command_state", {}),
        restoration=s1_runtime.restoration_flags(before, after),
        outer_failure=s1_runtime.safe_failure_code(primary),
    )
    try:
        write_readiness_report(root, report)
    except BaseException as report_error:
        if primary is None:
            raise
        primary.add_note("step6_s1_readiness_report_unavailable:" + type(report_error).__name__)
        raise primary from report_error
    print(json.dumps(report, sort_keys=True), file=sys.__stdout__)
    try:
        s1_runtime.require_readiness_passed(report)
    except RuntimeError as readiness_error:
        if primary is not None:
            raise primary from readiness_error
        raise
    return 0


def dispatch_main() -> int:
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--tool-readiness", "--root"]:
        return run_tool_readiness(sys.argv[3])
    if "--tool-readiness" in sys.argv[1:]:
        raise RuntimeError("step6_s1_tool_readiness_arguments_invalid")
    if sys.argv[1:] == ["--migration-digest-validation"]:
        return run_identity_validation(MIGRATION_DIGEST_ROOT)
    if sys.argv[1:] == ["--observer-capacity-validation"]:
        return run_identity_validation(OBSERVER_CAPACITY_ROOT)
    if sys.argv[1:] == ["--observer-failure-validation"]:
        return run_identity_validation(OBSERVER_FAILURE_ROOT)
    if sys.argv[1:] == ["--launcher-exit-contract-validation"]:
        return run_identity_validation(LAUNCHER_EXIT_ROOT)
    if sys.argv[1:] == ["--cleanup-report-semantics-validation"]:
        return run_identity_validation(CLEANUP_SEMANTICS_ROOT)
    if sys.argv[1:] == ["--cleanup-control-validation"]:
        return run_identity_validation(CLEANUP_CONTROL_ROOT)
    if sys.argv[1:] == ["--startup-report-readiness"]:
        return run_identity_validation(REPORT_READINESS_ROOT)
    if sys.argv[1:] == ["--startup-report-diagnostic"]:
        return run_startup_diagnostic(REPORT_READINESS_ROOT)
    if sys.argv[1:] == ["--launcher-termination-validation"]:
        return run_identity_validation(TERMINATION_ROOT)
    if sys.argv[1:] == ["--composition-startup-readiness"]:
        return run_identity_validation(COMPOSITION_STARTUP_ROOT)
    if sys.argv[1:] == ["--composition-startup-diagnostic"]:
        return run_startup_diagnostic(COMPOSITION_STARTUP_ROOT)
    if sys.argv[1:] == ["--composition-validation"]:
        return run_identity_validation(COMPOSITION_ROOT)
    if len(sys.argv) == 3 and sys.argv[1] in {"--startup-readiness", "--startup-diagnostic"}:
        roots = {f"{index:02d}": root for index, root in enumerate(STARTUP_READINESS_ROOTS, 1)}
        if sys.argv[2] not in roots:
            raise RuntimeError("step6_startup_readiness_invalid")
        if sys.argv[1] == "--startup-readiness":
            return run_identity_validation(roots[sys.argv[2]])
        return run_startup_diagnostic(roots[sys.argv[2]])
    if len(sys.argv) == 3 and sys.argv[1] == "--exit-validation":
        roots = {"01": EXIT_VALIDATION_ROOTS[0], "02": EXIT_VALIDATION_ROOTS[1]}
        if sys.argv[2] not in roots:
            raise RuntimeError("step6_identity_validation_root_unapproved")
        return run_identity_validation(roots[sys.argv[2]])
    if sys.argv[1:] == ["--identity-validation"]:
        return run_identity_validation()
    if sys.argv[1:] == ["--tool-contract"]:
        return run_tool_contract()
    if sys.argv[1:] == ["--space-semantic"]:
        return run_space_semantics()
    if sys.argv[1:] == ["--space-prevalidation"]:
        return run_space_prevalidation()
    if sys.argv[1:] == ["--static-checks"]:
        return run_static_checks()
    if sys.argv[1:] == ["--native-probe"]:
        return run_native_probe()
    if len(sys.argv) in {2, 3} and sys.argv[1] == "--quality":
        try:
            return run_quality_acceptance(
                sys.argv[2] if len(sys.argv) == 3 else "recovery-20260905-01/native-quality-10"
            )
        except RuntimeError as error:
            if str(error) != "step6_native_precreation_boundary_unavailable":
                raise
            print(json.dumps({"state": "blocked", "code": str(error), "quality_started": False}))
            return 2
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("tests", nargs="+")
    args = parser.parse_args()
    return run_pytest(args.tests, batch=args.batch, output=args.output)


def main() -> int:
    with command_scope():
        return dispatch_main()


if __name__ == "__main__":
    raise SystemExit(main())
