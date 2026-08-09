from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.config import load_config
from app.projects.paths import resolve_project_path


def active_project_info(config: Mapping[str, Any] | None = None) -> dict | None:
    """Devuelve una identidad presentable del proyecto activo.

    La interfaz debe poder mostrar la ruta aunque el archivo se haya movido o
    esté temporalmente dañado; por eso los errores de inspección no impiden
    obtener el nombre derivado del archivo.
    """
    settings = dict(config or load_config())
    configured = settings.get("activeProject")
    if not configured:
        return None
    path = resolve_project_path(configured, settings.get("projectsDirectory"))
    result = {
        "path": str(path),
        "name": path.stem,
        "id": "",
        "available": path.is_file(),
        "valid": False,
    }
    if not path.is_file():
        return result
    try:
        from app.projects.vlf import inspect_project

        metadata = inspect_project(path)
    except (OSError, ValueError):
        return result
    result.update(
        name=metadata.get("name") or path.stem,
        id=metadata.get("id", ""),
        valid=True,
    )
    return result
