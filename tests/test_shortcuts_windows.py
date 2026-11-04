"""Windows shortcut contract tests; COM/native verification requires Windows."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from lanctl.core.shortcuts import LAUNCHERS, create_shortcut, plan_shortcut
from lanctl.core.shortcuts_windows import (
    _WRITE_LINK,
    create_windows_shortcut,
    plan_windows_shortcut,
)


@pytest.fixture
def distribution(tmp_path):
    directory = tmp_path / "LANCTL ü $` ; space"
    directory.mkdir()
    for name in (*LAUNCHERS, "lanctl-window"):
        (directory / f"{name}.exe").write_bytes(b"executable placeholder")
    return directory


@pytest.mark.parametrize("launcher", sorted(LAUNCHERS))
@pytest.mark.parametrize("mode", ["cli", "tui", "gui"])
def test_windows_launch_plan(distribution, launcher, mode):
    plan = plan_windows_shortcut(distribution, launcher, mode, "Prueba ü")
    assert plan.target == distribution / "Prueba ü.lnk"
    assert plan.working_directory == distribution
    assert plan.terminal == (mode != "gui")
    if mode == "gui":
        assert plan.executable.name == "lanctl-window.exe"
        assert plan.arguments == (() if launcher == "lanctl" else (launcher,))
    else:
        assert plan.executable.name == f"{launcher}.exe"
        assert plan.arguments == (f"--{mode}",)
    assert plan.icon == distribution / f"{launcher}.exe"


@pytest.mark.parametrize(
    "name", ["CON", "NUL.txt", "com1", "LPT¹", "a:b", "a?b", "a*", 'a"', "x.", " x", "../x", "x\n"]
)
def test_windows_reserved_names(distribution, name):
    with pytest.raises(ValueError, match=r"SHORTCUT\.INVALID_NAME"):
        plan_windows_shortcut(distribution, "lanctl", "tui", name)


def test_gui_host_missing(distribution):
    (distribution / "lanctl-window.exe").unlink()
    with pytest.raises(ValueError, match=r"SHORTCUT\.EXECUTABLE_UNAVAILABLE"):
        plan_windows_shortcut(distribution, "lanctl", "gui", "test")


def test_no_gui_and_bad_options(distribution):
    with pytest.raises(ValueError, match=r"SHORTCUT\.GUI_UNAVAILABLE"):
        plan_windows_shortcut(distribution, "lanctl", "gui", "test", gui_available=False)
    with pytest.raises(ValueError, match=r"SHORTCUT\.INVALID_LAUNCH_MODE"):
        plan_windows_shortcut(distribution, "cmd", "cli", "test")


def test_native_icon_and_independent_directories(distribution, tmp_path):
    icon = distribution / "assets/launcher-icons/terminal.ico"
    icon.parent.mkdir(parents=True)
    icon.write_bytes(b"icon")
    plan = plan_windows_shortcut(
        distribution, "lanip", "cli", "test", destination=tmp_path, working_directory=tmp_path
    )
    assert plan.icon == icon
    assert plan.working_directory == tmp_path
    assert plan.target.parent == tmp_path


def fake_writer(command, **kwargs):
    data = json.loads(kwargs["input"])
    assert command[-1] == _WRITE_LINK
    assert data["executable"] not in command[-1]
    assert kwargs["check"] and kwargs["timeout"] == 15
    assert kwargs["capture_output"]
    assert data["arguments"] == "--tui"
    assert data["icon"].endswith(",0")
    Path(data["output"]).write_bytes(b"simulated shell link")
    return subprocess.CompletedProcess(command, 0)


def test_data_on_stdin_and_private_output(distribution):
    plan = plan_windows_shortcut(distribution, "lanctl", "tui", "test")
    with (
        patch("lanctl.core.shortcuts_windows.sys.platform", "win32"),
        patch("lanctl.core.shortcuts_windows._powershell", return_value=Path("powershell.exe")),
        patch("lanctl.core.shortcuts_windows.subprocess.run", side_effect=fake_writer),
    ):
        assert create_windows_shortcut(plan) == plan.target
    assert plan.target.read_bytes() == b"simulated shell link"
    assert not list(distribution.glob(".lanctl-shortcut-*"))


@pytest.mark.parametrize(
    "failure",
    [
        PermissionError("denied"),
        subprocess.CalledProcessError(1, "PowerShell", stderr=b"COM unavailable"),
        subprocess.TimeoutExpired("PowerShell", 15),
    ],
)
def test_native_failure_cleans_private_directory(distribution, failure):
    plan = plan_windows_shortcut(distribution, "lanctl", "tui", "test")
    with (
        patch("lanctl.core.shortcuts_windows.sys.platform", "win32"),
        patch("lanctl.core.shortcuts_windows._powershell", return_value=Path("powershell.exe")),
        patch("lanctl.core.shortcuts_windows.subprocess.run", side_effect=failure),
        pytest.raises(type(failure)),
    ):
        create_windows_shortcut(plan)
    assert not plan.target.exists()
    assert not list(distribution.glob(".lanctl-shortcut-*"))


def test_collision_never_calls_shell(distribution):
    plan = plan_windows_shortcut(distribution, "lanctl", "tui", "test")
    plan.target.write_text("original")
    with (
        patch("lanctl.core.shortcuts_windows.sys.platform", "win32"),
        patch("lanctl.core.shortcuts_windows._powershell") as shell,
        pytest.raises(FileExistsError),
    ):
        create_windows_shortcut(plan)
    assert plan.target.read_text() == "original"
    shell.assert_not_called()


def test_dispatch_selects_windows(distribution):
    with patch("sys.platform", "win32"):
        plan = plan_shortcut(distribution, "lanctl", "tui", "test")
    assert plan.target.suffix == ".lnk"
    with patch(
        "lanctl.core.shortcuts_windows.create_windows_shortcut", return_value=plan.target
    ) as create:
        assert create_shortcut(plan) == plan.target
    create.assert_called_once_with(plan)


@pytest.mark.skipif(sys.platform != "win32", reason="Requires native Windows WScript.Shell")
def test_windows_com_creates_real_link(distribution):
    # Readback verification runs inside the fixed PowerShell script. No .exe is
    # executed: placeholder binaries are sufficient to validate link properties.
    plan = plan_windows_shortcut(distribution, "lanip", "gui", "Real ü")
    create_windows_shortcut(plan)
    assert plan.target.stat().st_size > 0
    with pytest.raises(FileExistsError):
        create_windows_shortcut(plan)
