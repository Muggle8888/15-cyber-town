"""Run the local FastAPI application with validated project settings."""

import json
import os
import sys
import threading
import time
from ipaddress import ip_address
from typing import Literal

import uvicorn

from cyber_town.api.app import app

_STARTUP_DIAGNOSTIC = os.environ.get("F009_STARTUP_DIAGNOSTIC") == "1"
_startup_observation_failed = False


def _startup_phase(
    phase: Literal[
        "before_composition_import",
        "composition_import_returned",
        "main_entered",
        "settings_returned",
        "before_service_assembly",
        "before_uvicorn_run",
    ],
) -> None:
    """Optional bounded observations; output failure must not mask a business error."""
    global _startup_observation_failed
    if not _STARTUP_DIAGNOSTIC:
        return
    try:
        event = {
            "t": time.monotonic(),
            "phase": phase,
            "pid": os.getpid(),
            "thread_id": threading.get_ident(),
            "native_thread_id": threading.get_native_id(),
        }
        if sys.__stderr__ is None:
            raise OSError("startup diagnostic stream unavailable")
        sys.__stderr__.write("F009_STARTUP " + json.dumps(event) + "\n")
        sys.__stderr__.flush()
    except Exception:
        _startup_observation_failed = True
        try:
            failure = {"t": time.monotonic(), "observation_error": "product_output_failed"}
            os.write(2, ("F009_STARTUP " + json.dumps(failure) + "\n").encode("ascii"))
        except OSError:
            pass


# Conditional imports retain the original order, without an E402 exemption.
if _STARTUP_DIAGNOSTIC:
    _startup_phase("before_composition_import")
    from cyber_town.api.composition import build_dialogue_service

    _startup_phase("composition_import_returned")
    from cyber_town.config import Settings
else:
    from cyber_town.api.composition import build_dialogue_service
    from cyber_town.config import Settings


def _validated_loopback_host(host: str) -> str:
    try:
        address = ip_address(host)
    except ValueError as error:
        raise ValueError("APP_HOST must be a loopback IP address") from error
    if not address.is_loopback:
        raise ValueError("APP_HOST must be a loopback IP address")
    return host


def main() -> None:
    """Start the local server using APP_HOST and APP_PORT settings."""

    _startup_phase("main_entered")
    settings = Settings()
    _startup_phase("settings_returned")
    host = _validated_loopback_host(settings.app_host)
    _startup_phase("before_service_assembly")
    app.state.dialogue_service = build_dialogue_service(settings)
    app.state.relationship_service = (
        None
        if app.state.dialogue_service is None
        else app.state.dialogue_service.relationship_service
    )
    _startup_phase("before_uvicorn_run")
    uvicorn.run(
        app,
        host=host,
        port=settings.app_port,
    )


if __name__ == "__main__":
    main()
