from __future__ import annotations

from pathlib import Path
from typing import Any

from lanctl.apps.ip.interfaces.tui.modal import ModalState


def plugin_detail(plugin: Any) -> list[str]:
    manifest = plugin.manifest
    return [
        f"Nombre       : {manifest.name}",
        f"ID           : {manifest.plugin_id}",
        f"Versión      : {manifest.version}",
        f"Estado       : {plugin.state.value}",
        f"Autor        : {manifest.author or '-'}",
        f"Runtime      : {manifest.runtime}",
        f"Descripción  : {manifest.description or '-'}",
        f"Capacidades  : {', '.join(manifest.capabilities) or '-'}",
        f"Permisos     : {', '.join(manifest.permissions) or '-'}",
        f"Concedidos   : {', '.join(sorted(plugin.granted)) or '-'}",
        f"Ruta         : {plugin.path}",
        f"Error        : {plugin.error or '-'}",
    ]


def project_detail(path: Path, active: str) -> list[str]:
    try:
        from lanctl.core.projects.vlf import inspect_project

        info = inspect_project(path)
        return [
            f"Nombre       : {info.get('name') or path.stem}",
            f"Activo       : {'Sí' if str(path.resolve()).casefold() == str(active).casefold() else 'No'}",
            f"UUID         : {info.get('id') or '-'}",
            f"Descripción  : {info.get('description') or '-'}",
            f"Autor        : {info.get('author') or '-'}",
            f"LANCTL       : {info.get('lanctlVersion') or '-'}",
            f"Actualizado  : {info.get('updated') or '-'}",
            f"Dispositivos : {info.get('devices', '-')}",
            f"Grupos       : {info.get('groups', '-')}",
            f"Ruta         : {path}",
        ]
    except (OSError, ValueError) as error:
        return [f"Proyecto: {path.stem}", f"Ruta: {path}", f"Error: {error}"]


def plugin_manager_modal(plugins: list[Any]) -> ModalState:
    listing = [
        f"{item.manifest.name:<24} {item.manifest.version:<12} {item.state.value}"
        for item in plugins
    ] or ["(No hay plugins instalados)"]
    details = [plugin_detail(item) for item in plugins]
    return ModalState(
        kind="plugins",
        title="PLUGIN",
        tabs=["Plugins", "Información"],
        pages=[listing, details[0] if details else ["No hay información disponible."]],
        items=plugins,
        footer="↑/↓ seleccionar  → información  Ctrl+R recargar  Esc cerrar",
    )


def project_manager_modal(projects: list[Path], active: str, root: Path) -> ModalState:
    listing = [
        f"{'*' if str(path.resolve()).casefold() == str(active).casefold() else ' '} "
        f"{path.stem:<28} {path}"
        for path in projects
    ] or [f"(No hay proyectos en {root})"]
    details = [project_detail(path, active) for path in projects]
    return ModalState(
        kind="projects",
        title="PROJECT MANAGER",
        tabs=["Proyectos", "Información"],
        pages=[listing, details[0] if details else ["No hay información disponible."]],
        items=projects,
        footer="↑/↓ seleccionar  → información  Enter activar  Ctrl+R recargar  Esc cerrar",
    )
