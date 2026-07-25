from __future__ import annotations

from pathlib import Path
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
    return (application_directory() / path).resolve()
