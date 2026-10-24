"""Scoped Clink registration using native executable arguments, never a command shell."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from lanctl.core.coordination import principal_id
from lanctl.core.file_transaction import atomic_write_json, locked_file
from lanctl.core.local_permissions import elevated
from lanctl.core.paths import application_directory


def _find_clink(*, trusted_only=False):
    candidates = []
    if not trusted_only:
        candidates.extend(
            shutil.which(name) for name in ("clink.exe", "clink_x64.exe", "clink_x86.exe")
        )
    if trusted_only:
        import winreg

        bases = []
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            ) as key:
                for name in ("ProgramFilesDir", "ProgramFilesDir (x86)"):
                    try:
                        value, kind = winreg.QueryValueEx(key, name)
                        if kind == winreg.REG_SZ and isinstance(value, str):
                            bases.append(value)
                    except FileNotFoundError:
                        continue
        except OSError:
            return None
    else:
        bases = (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"))
    for base in bases:
        if base:
            candidates.extend(
                str(Path(base) / "clink" / name)
                for name in ("clink_x64.exe", "clink.exe", "clink_x86.exe")
            )
    return next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()), None)


def _marker(directory):
    key = hashlib.sha256(os.path.normcase(str(directory)).encode()).hexdigest()[:24]
    return (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LANCTL" / "clink" / f"{key}.json"
    )


def _registration_matches(executable, scripts, action):
    """Clink returns 1 for an already installed/absent path; verify its actual state."""
    listing = subprocess.run(
        [executable, "installscripts", "--list"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if listing.returncode:
        return False
    expected = os.path.normcase(os.path.normpath(str(scripts)))
    registered = any(
        os.path.normcase(os.path.normpath(line.strip())) == expected
        for line in listing.stdout.splitlines()
        if line.strip()
    )
    return registered == (action == "install")


def configure_clink(action, directory=None):
    if action not in {"install", "uninstall"}:
        raise ValueError("acción Clink no válida")
    scripts = (
        Path(directory).resolve()
        if directory is not None
        else application_directory()
        / ("clink" if getattr(sys, "frozen", False) else "packaging/clink")
    )
    result = {"action": action, "directory": str(scripts), "status": "unavailable"}
    if os.name != "nt":
        return {**result, "status": "unsupported-platform"}
    admin = elevated()
    if action == "install" and admin:
        return {**result, "status": "normal-user-required"}
    marker = _marker(scripts)
    if action == "uninstall" and not marker.exists():
        return {**result, "status": "not-registered-for-user"}
    if action == "install" and not (scripts / "lanctl.lua").is_file():
        raise ValueError("no se encuentra el completado LANCTL de esta distribución")
    executable = _find_clink(trusted_only=admin)
    if executable is None:
        return result
    with locked_file(marker):
        if marker.exists():
            state = json.loads(marker.read_text(encoding="utf-8"))
            if (
                not isinstance(state, dict)
                or state.get("schemaVersion") != 1
                or state.get("owner") != principal_id()
                or state.get("directory") != str(scripts)
            ):
                raise ValueError("registro de completado no corresponde al usuario/directorio")
        command = "installscripts" if action == "install" else "uninstallscripts"
        try:
            completed = subprocess.run(
                [executable, command, str(scripts)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            already_applied = completed.returncode == 1 and _registration_matches(
                executable, scripts, action
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("Clink no respondió dentro de 10 segundos") from exc
        if completed.returncode and not already_applied:
            raise OSError(f"Clink no pudo {command}: código {completed.returncode}")
        if action == "install":
            atomic_write_json(
                marker, {"schemaVersion": 1, "owner": principal_id(), "directory": str(scripts)}
            )
        elif marker.exists():
            marker.unlink()
    return {**result, "status": "registered" if action == "install" else "unregistered"}
