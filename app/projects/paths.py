from __future__ import annotations

import os
from pathlib import Path


def windows_documents_directory() -> Path:
    """Documentos del usuario; no depende del directorio del ejecutable."""
    profile = os.environ.get("USERPROFILE")
    return (Path(profile) if profile else Path.home()) / "Documents"


def default_project_directory() -> Path:
    return windows_documents_directory() / "LanCTL"


def resolve_project_path(value: str | Path, configured_directory: str | Path | None = None) -> Path:
    """Las rutas relativas pertenecen a Documentos/LanCTL; las absolutas se respetan."""
    expanded = Path(os.path.expandvars(str(value))).expanduser()
    if not expanded.is_absolute():
        root = (
            Path(os.path.expandvars(str(configured_directory))).expanduser()
            if configured_directory else default_project_directory()
        )
        expanded = root / expanded
    if expanded.suffix.casefold() != ".vlf":
        expanded = expanded.with_suffix(".vlf")
    return expanded.resolve()
