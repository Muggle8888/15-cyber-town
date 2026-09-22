from __future__ import annotations

import subprocess
from pathlib import Path

from pytest import MonkeyPatch
from scripts import dialogue_integration


def test_town_demo_prefers_matching_gui_binary_for_console_executable(tmp_path: Path) -> None:
    console = tmp_path / "Godot_v4.7.2-stable_win64_console.exe"
    gui = tmp_path / "Godot_v4.7.2-stable_win64.exe"
    console.touch()
    gui.touch()

    assert dialogue_integration._town_demo_executable(console) == gui


def test_town_demo_keeps_console_executable_when_gui_binary_is_absent(tmp_path: Path) -> None:
    console = tmp_path / "Godot_v4.7.2-stable_win64_console.exe"
    console.touch()

    assert dialogue_integration._town_demo_executable(console) == console


def test_town_demo_keeps_an_explicit_gui_executable(tmp_path: Path) -> None:
    gui = tmp_path / "Godot_v4.7.2-stable_win64.exe"
    gui.touch()

    assert dialogue_integration._town_demo_executable(gui) == gui


def test_aftermath_demo_uses_isolated_persistent_event_saves(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    console = tmp_path / "Godot_v4.7.2-stable_win64_console.exe"
    gui = tmp_path / "Godot_v4.7.2-stable_win64.exe"
    console.touch()
    gui.touch()
    observed: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: object) -> None:
        observed.append(command)

    monkeypatch.setattr(dialogue_integration, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run)

    dialogue_integration._run_town_demo_godot(console, aftermath_demo=True)

    command = observed[0]
    assert "--event-save-path=res://.godot/f014-user-uat-f013-v1.json" in command
    assert "--aftermath-save-path=res://.godot/f014-user-uat-v1.json" in command
    assert "--prepare-aftermath-demo" in command
