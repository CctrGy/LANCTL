"""Windows Shell Link adapter. Data is never interpolated into PowerShell code."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from lanctl.core.shortcuts import LAUNCHERS, MODES, _single_line

# Microsoft WScript.Shell exposes separate target/argument/working-dir fields.
# Read JSON on stdin with ASCII escaping, independent of the console code page.
_WRITE_LINK = """
$ErrorActionPreference = 'Stop'
try {
    $data = ConvertFrom-Json -InputObject ([Console]::In.ReadToEnd())
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut([string]$data.output)
    $link.TargetPath = [string]$data.executable
    $link.Arguments = [string]$data.arguments
    $link.WorkingDirectory = [string]$data.workingDirectory
    $link.IconLocation = [string]$data.icon
    $link.WindowStyle = 1
    $link.Save()
    $saved = $shell.CreateShortcut([string]$data.output)
    if ($saved.TargetPath -ine [string]$data.executable -or
        $saved.Arguments -cne [string]$data.arguments -or
        $saved.WorkingDirectory -ine [string]$data.workingDirectory) {
        throw 'SHORTCUT.LINK_VERIFICATION_FAILED'
    }
    exit 0
} catch {
    [Console]::Error.WriteLine($_.Exception.ToString())
    exit 1
}
"""


@dataclass(frozen=True)
class WindowsShortcutPlan:
    executable: Path
    arguments: tuple[str, ...]
    working_directory: Path
    target: Path
    icon: Path
    name: str
    terminal: bool


def plan_windows_shortcut(
    distribution: Path,
    launcher: str,
    mode: str,
    name: str,
    *,
    destination: Path | None = None,
    working_directory: Path | None = None,
    icon: Path | None = None,
    gui_available: bool = True,
) -> WindowsShortcutPlan:
    if launcher not in LAUNCHERS or mode not in MODES:
        raise ValueError("SHORTCUT.INVALID_LAUNCH_MODE")
    if mode == "gui" and not gui_available:
        raise ValueError("SHORTCUT.GUI_UNAVAILABLE")
    devices = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    devices.update(prefix + number for prefix in ("COM", "LPT") for number in "123456789¹²³")
    if (
        not _single_line(name)
        or name != name.strip()
        or name.endswith(".")
        or any(char in name for char in '/\\<>:"|?*')
        or name.split(".")[0].upper() in devices
    ):
        raise ValueError("SHORTCUT.INVALID_NAME")
    distribution = distribution.resolve(strict=True)
    launcher_executable = distribution / f"{launcher}.exe"
    executable = distribution / "lanctl-window.exe" if mode == "gui" else launcher_executable
    if not executable.is_file() or not launcher_executable.is_file():
        raise ValueError("SHORTCUT.EXECUTABLE_UNAVAILABLE")
    directory = (destination if destination is not None else distribution).resolve(strict=True)
    working = (working_directory if working_directory is not None else distribution).resolve(
        strict=True
    )
    if not directory.is_dir() or not working.is_dir():
        raise ValueError("SHORTCUT.INVALID_DIRECTORY")
    if icon is None:
        terminal_icon = distribution / "assets/launcher-icons/terminal.ico"
        icon = terminal_icon if mode != "gui" and terminal_icon.is_file() else launcher_executable
    icon = icon.resolve(strict=True)
    if not icon.is_file():
        raise ValueError("SHORTCUT.INVALID_ICON")
    if any(not _single_line(str(path)) for path in (executable, directory, working, icon)):
        raise ValueError("SHORTCUT.INVALID_PATH")
    # Shell Link/WSH can interpret environment variables. Reject rather than
    # silently pointing at a different executable or working directory.
    if any("%" in str(path) for path in (executable, working, icon)):
        raise ValueError("SHORTCUT.INVALID_PATH")
    arguments = (() if launcher == "lanctl" else (launcher,)) if mode == "gui" else (f"--{mode}",)
    return WindowsShortcutPlan(
        executable, arguments, working, directory / f"{name}.lnk", icon, name, mode != "gui"
    )


def _powershell() -> Path:
    # Use the Windows system copy, not a program found in cwd or user PATH.
    root = Path(os.environ.get("SYSTEMROOT", ""))
    if not root.is_absolute():
        raise OSError("SHORTCUT.POWERSHELL_UNAVAILABLE")
    executable = root / "System32/WindowsPowerShell/v1.0/powershell.exe"
    if not executable.is_file():
        raise OSError("SHORTCUT.POWERSHELL_UNAVAILABLE")
    return executable


def create_windows_shortcut(plan: WindowsShortcutPlan) -> Path:
    if sys.platform != "win32":
        raise OSError("SHORTCUT.UNSUPPORTED_PLATFORM")
    if plan.target.exists() or plan.target.is_symlink():
        raise FileExistsError(str(plan.target))
    powershell = _powershell()
    # Keep WSH output private until Save succeeds. Windows rename is atomic and
    # refuses an existing destination (including a racing creator); no replace.
    with tempfile.TemporaryDirectory(
        prefix=".lanctl-shortcut-", dir=plan.target.parent
    ) as temporary:
        output = Path(temporary) / "shortcut.lnk"
        data = {
            "output": str(output),
            "executable": str(plan.executable),
            "arguments": subprocess.list2cmdline(plan.arguments),
            "workingDirectory": str(plan.working_directory),
            "icon": f"{plan.icon},0",
        }
        subprocess.run(
            [str(powershell), "-NoProfile", "-NonInteractive", "-Command", _WRITE_LINK],
            input=json.dumps(data, ensure_ascii=True).encode("ascii"),
            capture_output=True,
            check=True,
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if not output.is_file() or output.stat().st_size == 0:
            raise OSError("SHORTCUT.LINK_NOT_CREATED")
        os.rename(output, plan.target)
    return plan.target
