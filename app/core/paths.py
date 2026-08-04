from __future__ import annotations

from pathlib import Path
import os
import platform
import sys


def application_directory() -> Path:
    """Directorio estable de LANCTL, independiente del cwd del proceso."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def application_path(value: str | Path) -> Path:
    """Resuelve rutas relativas junto al EXE o la raíz del proyecto."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    normalized = path.as_posix()
    if getattr(sys, "frozen", False) and (normalized == "data/lc" or normalized.startswith("data/lc/")):
        executable_directory = Path(sys.executable).resolve().parent
        if (executable_directory / "LANCTL.portable").exists():
            root = executable_directory / "data" / "lc"
        elif os.environ.get("LANCTL_DATA_DIR"):
            root = Path(os.environ["LANCTL_DATA_DIR"]).expanduser()
        elif platform.system() == "Windows":
            root = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "LANCTL"
        else:
            root = Path("/var/lib/lanctl")
        suffix = Path(*path.parts[2:]) if len(path.parts)>2 else Path()
        return (root / suffix).resolve()
    return (application_directory() / path).resolve()
