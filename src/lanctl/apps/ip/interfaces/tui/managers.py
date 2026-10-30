from __future__ import annotations

from pathlib import Path
from typing import Any

from lanctl.apps.ip.interfaces.tui.modal import ModalState
from lanctl.shared.i18n import t


def plugin_detail(plugin: Any) -> list[str]:
    manifest = plugin.manifest
    return [
        t("LANCTL.UI.DETAIL.NAME_VALUE", value0=f"{manifest.name}"),
        f"ID           : {manifest.plugin_id}",
        t("LANCTL.UI.MESSAGE.VERSION_VALUE", value0=f"{manifest.version}"),
        t("LANCTL.UI.DETAIL.STATE_VALUE", value0=f"{plugin.state.value}"),
        t("LANCTL.UI.DETAIL.AUTHOR_VALUE", value0=f"{manifest.author or '-'}"),
        t("LANCTL.UI.DETAIL.RUNTIME_VALUE", value0=f"{manifest.runtime}"),
        t("LANCTL.UI.MESSAGE.DESCRIPTION_VALUE", value0=f"{manifest.description or '-'}"),
        t(
            "LANCTL.UI.DETAIL.CAPABILITIES_VALUE",
            value0=f"{', '.join(manifest.capabilities) or '-'}",
        ),
        t("LANCTL.UI.DETAIL.PERMISSIONS_VALUE", value0=f"{', '.join(manifest.permissions) or '-'}"),
        t("LANCTL.UI.DETAIL.GRANTED_VALUE", value0=f"{', '.join(sorted(plugin.granted)) or '-'}"),
        t("LANCTL.UI.DETAIL.PATH_VALUE", value0=f"{plugin.path}"),
        t("LANCTL.UI.DETAIL.ERROR_VALUE_33EFAEFA", value0=f"{plugin.error or '-'}"),
    ]


def project_detail(project: Any, active: str) -> list[str]:
    path = project.path if hasattr(project, "path") else Path(project)
    try:
        from lanctl.core.projects.vlf import inspect_project

        info = inspect_project(path)
        from lanctl.core.projects.metadata import read_metadata

        metadata = read_metadata(path)["values"]
        return [
            t("LANCTL.UI.DETAIL.NAME_VALUE", value0=f"{info.get('name') or path.stem}"),
            t(
                "LANCTL.UI.DETAIL.ACTIVE_VALUE",
                value0=f"{(t('LANCTL.UI.TEXT.YES') if str(path.resolve()).casefold() == str(active).casefold() else t('LANCTL.UI.TEXT.NO'))}",
            ),
            f"UUID         : {info.get('id') or '-'}",
            t("LANCTL.UI.MESSAGE.DESCRIPTION_VALUE", value0=f"{info.get('description') or '-'}"),
            t("LANCTL.UI.DETAIL.AUTHOR_VALUE", value0=f"{info.get('author') or '-'}"),
            f"LAN          : {metadata['lan'] or '-'}",
            t("LANCTL.UI.MESSAGE.LOCATION_VALUE", value0=f"{metadata['location'] or '-'}"),
            t("LANCTL.UI.DETAIL.COMPANY_VALUE", value0=f"{metadata['company'] or '-'}"),
            t("LANCTL.UI.DETAIL.RESPONSIBLE_VALUE", value0=f"{metadata['responsible'] or '-'}"),
            f"LANCTL       : {info.get('lanctlVersion') or '-'}",
            t("LANCTL.UI.DETAIL.UPDATED_VALUE", value0=f"{info.get('updated') or '-'}"),
            t("LANCTL.UI.DETAIL.DEVICES_VALUE", value0=f"{info.get('devices', '-')}"),
            t("LANCTL.UI.DETAIL.GROUPS_VALUE", value0=f"{info.get('groups', '-')}"),
            t("LANCTL.UI.DETAIL.PATH_VALUE", value0=f"{path}"),
        ]
    except (OSError, ValueError) as error:
        return [
            t("LANCTL.UI.DETAIL.PROJECT_VALUE", value0=f"{path.stem}"),
            t("LANCTL.UI.DETAIL.PATH_VALUE_D419AD11", value0=f"{path}"),
            t("LANCTL.UI.DETAIL.ERROR_VALUE", value0=f"{error}"),
        ]


def plugin_manager_modal(plugins: list[Any]) -> ModalState:
    listing = [
        f"{item.manifest.name:<24} {item.manifest.version:<12} {item.state.value}"
        for item in plugins
    ] or [t("LANCTL.UI.SCREEN.NO_PLUGINS_INSTALLED")]
    details = [plugin_detail(item) for item in plugins]
    return ModalState(
        kind="plugins",
        title=t("LANCTL.UI.PRESENTATION.PLUGIN_TITLE"),
        tabs=["Plugins", t("LANCTL.COMMON.ACTION.INFO")],
        pages=[
            listing,
            details[0] if details else [t("LANCTL.UI.SCREEN.NO_INFORMATION_AVAILABLE")],
        ],
        items=plugins,
        footer=t("LANCTL.UI.SCREEN.SELECT_INFORMATION_CTRL_R_RELOAD_ESC_CLOSE"),
    )


def project_manager_modal(projects: list[Any], active: str, root: Path) -> ModalState:
    listing = [
        f"{'*' if str(item.path.resolve()).casefold() == str(active).casefold() else ' '} "
        f"{item.name:<28} "
        f"{'DOCUMENTOS' if item.in_default_directory else 'EXTERNO':<10} "
        f"{'DISPONIBLE' if item.available else 'NO DISPONIBLE':<13} {item.path}"
        for item in projects
    ] or [t("LANCTL.UI.MESSAGE.NO_PROJECTS_IN_VALUE", value0=f"{root}")]
    details = [project_detail(item, active) for item in projects]
    return ModalState(
        kind="projects",
        title=t("LANCTL.UI.PRESENTATION.PROJECT_MANAGER_TITLE"),
        tabs=[t("LANCTL.UI.TEXT.PROJECTS"), t("LANCTL.COMMON.ACTION.INFO")],
        pages=[
            listing,
            details[0] if details else [t("LANCTL.UI.SCREEN.NO_INFORMATION_AVAILABLE")],
        ],
        items=projects,
        footer=t(
            "LANCTL.UI.SCREEN.CTRL_N_NEW_CTRL_E_EDIT_CTRL_S_SAVE_DELETE_REMOVE_SELECT_INFORMATION_ENTER_ACTIVATE_CTRL_R_RELOA"
        ),
        max_width=120,
    )
