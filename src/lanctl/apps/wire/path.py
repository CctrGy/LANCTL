"""Compatibilidad de rutas de LANWIRE sobre el contrato común de LANCTL."""

from __future__ import annotations

import os
from pathlib import Path

from lanctl.core.paths import (
    PORTABLE_MARKER,
    PORTABLE_MARKER_CONTENT,
    application_directory,
    is_portable_install,
)
from lanctl.core.paths import (
    application_path as core_application_path,
)
from lanctl.core.paths import (
    data_root as core_data_root,
)


def data_root() -> Path:
    """Usa la raíz de la suite y conserva el alias histórico de LANWIRE."""
    if "LANCTL_DATA_DIR" not in os.environ and os.environ.get("LANWRE_DATA_DIR"):
        candidate = Path(os.environ["LANWRE_DATA_DIR"]).expanduser()
        if not candidate.is_absolute():
            raise ValueError("LANWRE_DATA_DIR debe ser una ruta absoluta")
        return candidate.resolve()
    return core_data_root()


def application_path(value: str | Path) -> Path:
    """Resuelve una ruta absoluta o una ruta relativa interna de LANWIRE."""
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()

    normalized = candidate.as_posix()
    if normalized == "data/lc" or normalized.startswith("data/lc/"):
        return core_application_path(candidate)
    if normalized == "data/lw" or normalized.startswith("data/lw/"):
        suffix = Path(*candidate.parts[2:]) if len(candidate.parts) > 2 else Path()
        return (data_root() / "physical" / suffix).resolve()
    if normalized == "data/logs" or normalized.startswith("data/logs/"):
        suffix = Path(*candidate.parts[2:]) if len(candidate.parts) > 2 else Path()
        return (data_root() / "physical" / "logs" / suffix).resolve()
    if candidate.parts and candidate.parts[0].casefold() == "data":
        suffix = Path(*candidate.parts[1:]) if len(candidate.parts) > 1 else Path()
        return (data_root() / suffix).resolve()
    return (application_directory() / candidate).resolve()


__all__ = [
    "PORTABLE_MARKER",
    "PORTABLE_MARKER_CONTENT",
    "application_directory",
    "application_path",
    "data_root",
    "is_portable_install",
]
