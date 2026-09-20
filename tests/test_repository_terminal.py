import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell.exe")


@pytest.mark.skipif(not POWERSHELL, reason="Windows PowerShell required")
@pytest.mark.parametrize(
    "arguments, expected, absent",
    [
        (["-DryRun"], "INSTALL:", "REMOTE:"),
        (["build", "-DryRun"], "BUILD:", "INSTALL:"),
        (["remote", "-Channel", "stable", "-DryRun"], "-Channel stable", "BUILD:"),
        (["help"], "Prerequisites:", "INSTALL:"),
    ],
)
def test_repository_command_plan(arguments, expected, absent, tmp_path):
    result = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "repositoryTerminal" / "repository.ps1"),
            *arguments,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert expected in result.stdout
    assert absent not in result.stdout


@pytest.mark.skipif(not POWERSHELL, reason="Windows PowerShell required")
def test_terminal_profile_creation_and_preservation(tmp_path):
    executable = tmp_path / "Program Files" / "LANCTL.exe"
    executable.parent.mkdir()
    executable.touch()
    local = tmp_path / "local"
    local.mkdir()
    env = dict(os.environ, LOCALAPPDATA=str(local), ProgramData=str(tmp_path / "shared"))
    command = [
        POWERSHELL,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT / "repositoryTerminal" / "terminal-profile.ps1"),
        "-Executable",
        str(executable),
    ]

    def run(*args):
        result = subprocess.run(
            command + list(args), env=env, capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    fragment = local / "Microsoft/Windows Terminal/Fragments/LANCTL/lanctl-cli.json"
    run("-DryRun")
    assert not fragment.exists()
    run()
    before = fragment.read_bytes()
    profile = json.loads(before)["profiles"][0]
    assert profile["commandline"] == f'"{executable}" --cli'
    assert profile["name"] == "LANCTL"
    assert "already exists" in run()
    assert fragment.read_bytes() == before
    fragment.unlink()
    settings = local / "Microsoft/Windows Terminal/settings.json"
    settings.write_text('{"profiles":{"list":[{"name":"LANCTL","commandline":"custom"}]}}')
    original = settings.read_bytes()
    assert "already exists" in run()
    assert not fragment.exists()
    assert settings.read_bytes() == original
