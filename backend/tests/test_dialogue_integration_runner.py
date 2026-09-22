from __future__ import annotations

from pathlib import Path

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
