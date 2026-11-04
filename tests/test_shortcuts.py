"""P118: isolated plans and atomic desktop files, without launching applications."""

import os
import shutil
import subprocess
import sys
from unittest.mock import patch

import pytest

from lanctl.core.shortcuts import LAUNCHERS, create_linux_shortcut, plan_linux_shortcut

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Linux desktop shortcut fixtures"
)


@pytest.fixture
def distribution(tmp_path):
    directory = tmp_path / 'LANCTL é $` " space'
    directory.mkdir()
    for launcher in LAUNCHERS:
        executable = directory / launcher
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
    return directory


@pytest.mark.parametrize("launcher", sorted(LAUNCHERS))
@pytest.mark.parametrize("mode", ["cli", "tui", "gui"])
def test_explicit_plan(distribution, tmp_path, launcher, mode):
    plan = plan_linux_shortcut(distribution, launcher, mode, "LANCTL prueba", destination=tmp_path)
    assert plan.arguments == (f"--{mode}",)
    assert plan.terminal == (mode != "gui")
    assert plan.working_directory == distribution
    assert plan.target.parent == tmp_path
    content = plan.content()
    assert "\\\\$" in content
    assert "\\\\`" in content
    assert '\\\\"' in content
    assert "\\s" in content
    assert "X-LANCTL-Shortcut-Version=1" in content
    assert "sudo" not in content
    target = create_linux_shortcut(plan)
    assert target.read_text() == content
    assert target.stat().st_mode & 0o777 == 0o755
    assert not list(tmp_path.glob(".lanctl-shortcut-*"))


@pytest.mark.parametrize(
    "name", ["", "../escape", "a/b", "a\\b", "a\nExec=bad", "a\t", "..", " trailing "]
)
def test_invalid_name(distribution, name):
    with pytest.raises(ValueError, match=r"SHORTCUT\.INVALID_NAME"):
        plan_linux_shortcut(distribution, "lanctl", "tui", name)


@pytest.mark.parametrize(
    "launcher,mode", [("sh", "cli"), ("lanctl", "--password=secret"), ("lanctl", "default")]
)
def test_no_arbitrary_commands(distribution, launcher, mode):
    with pytest.raises(ValueError, match=r"SHORTCUT\.INVALID_LAUNCH_MODE"):
        plan_linux_shortcut(distribution, launcher, mode, "test")


def test_gui_absent(distribution):
    with pytest.raises(ValueError, match=r"SHORTCUT\.GUI_UNAVAILABLE"):
        plan_linux_shortcut(distribution, "lanctl", "gui", "test", gui_available=False)


def test_missing_executable(distribution):
    (distribution / "lanip").unlink()
    with pytest.raises(ValueError, match=r"SHORTCUT\.EXECUTABLE_UNAVAILABLE"):
        plan_linux_shortcut(distribution, "lanip", "cli", "test")


@pytest.mark.parametrize("symlink", [False, True])
def test_collision_does_not_replace(distribution, tmp_path, symlink):
    plan = plan_linux_shortcut(distribution, "lanctl", "tui", "test")
    original = tmp_path / "original"
    original.write_text("preserved")
    if symlink:
        plan.target.symlink_to(original)
    else:
        plan.target.write_text("preserved")
    with pytest.raises(FileExistsError):
        create_linux_shortcut(plan)
    assert plan.target.read_text() == "preserved"
    assert original.read_text() == "preserved"
    assert not list(distribution.glob(".lanctl-shortcut-*"))


def test_publication_failure_cleans_temporary(distribution):
    plan = plan_linux_shortcut(distribution, "lanctl", "cli", "test")
    with (
        patch("lanctl.core.shortcuts.os.link", side_effect=PermissionError("denied")),
        pytest.raises(PermissionError, match="denied"),
    ):
        create_linux_shortcut(plan)
    assert not plan.target.exists()
    assert not list(distribution.glob(".lanctl-shortcut-*"))


def test_two_creators_only_one_wins(distribution):
    plan = plan_linux_shortcut(distribution, "lanctl", "cli", "test")
    create_linux_shortcut(plan)
    with pytest.raises(FileExistsError):
        create_linux_shortcut(plan)
    assert os.access(plan.target, os.X_OK)


def test_native_desktop_validator(distribution):
    validator = shutil.which("desktop-file-validate")
    if validator is None:
        pytest.skip("desktop-file-utils is not installed")
    plan = plan_linux_shortcut(distribution, "lanctl", "gui", "LANCTL prueba")
    target = create_linux_shortcut(plan)
    result = subprocess.run([validator, str(target)], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def test_gio_preserves_special_executable_path(distribution, tmp_path):
    """Launch a harmless temporary recorder through the native desktop parser."""
    import json

    system_python = "/usr/bin/python3"
    if not os.path.isfile(system_python):
        pytest.skip("System Python is unavailable")
    probe = subprocess.run(
        [system_python, "-c", "from gi.repository import Gio"], capture_output=True, check=False
    )
    if probe.returncode:
        pytest.skip("System Gio bindings are unavailable")
    output = tmp_path / "record.json"
    executable = distribution / "lanctl"
    executable.write_text(
        "#!/usr/bin/python3\nimport json, pathlib, sys\n"
        f"pathlib.Path({str(output)!r}).write_text(json.dumps([sys.argv, str(pathlib.Path.cwd())]))\n"
    )
    plan = plan_linux_shortcut(distribution, "lanctl", "gui", "LANCTL prueba")
    target = create_linux_shortcut(plan)
    script = """
import pathlib, sys, time
from gi.repository import Gio
app = Gio.DesktopAppInfo.new_from_filename(sys.argv[1])
assert app is not None
app.launch([], None)
output = pathlib.Path(sys.argv[2])
for attempt in range(100):
    if output.exists() and output.stat().st_size:
        break
    time.sleep(0.02)
assert output.exists()
"""
    result = subprocess.run(
        [system_python, "-c", script, str(target), str(output)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(output.read_text()) == [[str(executable), "--gui"], str(distribution)]


def test_percent_in_executable_path_is_explicitly_rejected(tmp_path):
    directory = tmp_path / "LANCTL %"
    directory.mkdir()
    executable = directory / "lanctl"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    with pytest.raises(ValueError, match=r"SHORTCUT\.INVALID_PATH"):
        plan_linux_shortcut(directory, "lanctl", "gui", "test")
    assert not list(directory.glob("*.desktop"))
