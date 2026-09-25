"""OS identity diagnostics; application roles do not grant OS privileges."""

from __future__ import annotations

import ctypes
import os


def elevated() -> bool:
    return bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name == "nt" else os.geteuid() == 0


def require_admin() -> None:
    if not elevated():
        raise PermissionError("operación administrativa: abre una terminal elevada (UAC/sudo)")


def status() -> dict:
    return {
        "elevated": elevated(),
        "policy": "OS permissions; explicit elevation",
        "tpmProvider": "not implemented",
    }


def launch_elevated(arguments: list[str]) -> int:
    import subprocess
    import sys

    if os.name != "nt":
        raise PermissionError("usa sudo lanctl seguido del launcher; no se eleva automáticamente")
    if not getattr(sys, "frozen", False):
        raise PermissionError(
            "--admin requiere la distribución instalada; en desarrollo abre PowerShell como administrador"
        )
    execute = ctypes.windll.shell32.ShellExecuteW
    execute.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_int,
    ]
    execute.restype = ctypes.c_void_p
    result = execute(None, "runas", sys.executable, subprocess.list2cmdline(arguments), None, 1)
    if not result or result <= 32:
        raise PermissionError("elevación cancelada o rechazada por Windows")
    return 0
