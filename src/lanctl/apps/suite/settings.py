"""Settings application service shared by CLI, TUI and GUI adapters."""

from contextlib import ExitStack

from lanctl.core.config import canonical_config, load_config, update_config
from lanctl.core.project_context import project_operation
from lanctl.core.settings_catalog import CATEGORIES, catalog, leaves
from lanctl.core.settings_policy import (
    SettingsContext,
    preference_visible,
    prepare_program_changes,
    restriction,
)


def active_settings_project():
    from lanctl.core.projects.current import active_project_info

    project = active_project_info()
    if not project or not project["valid"]:
        raise ValueError("Selecciona un proyecto VLF válido antes de configurar el proyecto")
    return project["path"]


def settings_entries(context, *, project_path=None):
    with project_operation():
        if context.scope == "project":
            from lanctl.core.projects.settings import project_settings

            return [
                {
                    "path": path,
                    "category": path.split(".")[0],
                    "value": value,
                    "readOnly": "",
                }
                for path, value in leaves(
                    project_settings(project_path or active_settings_project())
                )
                if preference_visible(context, path)
            ]
        config = load_config()
        entries = catalog(config)
        entries.append(
            {
                "path": "access.remote",
                "category": "access",
                "value": {
                    key: value
                    for key, value in canonical_config(config)["access"]["remote"].items()
                    if preference_visible(context, f"access.remote.{key}")
                },
                "readOnly": "",
            }
        )
        result = []
        for entry in entries:
            if not preference_visible(context, entry["path"]):
                continue
            entry["readOnly"] = restriction(context, entry["path"])
            result.append(entry)
        return sorted(result, key=lambda entry: list(CATEGORIES).index(entry["category"]))


def save_program_changes(changes, context):
    if not changes:
        return load_config()

    def apply(config):
        candidate = prepare_program_changes(config, changes, context)
        if any(path == "access.remote" or path.startswith("access.remote.") for path in changes):
            from lanctl.apps.access.settings_lifecycle import remote_settings_transaction

            transaction.enter_context(remote_settings_transaction(config, candidate))
        return candidate

    with project_operation(), ExitStack() as transaction:
        return update_config(apply)


def _form_path(key):
    from lanctl.core.config import _LEGACY_PATHS

    if key.startswith("tuiKey."):
        return "tui.keyBindings." + key.split(".", 1)[1]
    if key.startswith("tuiColumn."):
        return "tui.columnWidths." + key.split(".", 1)[1]
    if key in _LEGACY_PATHS:
        return ".".join(_LEGACY_PATHS[key])
    raise ValueError(f"Campo de configuración desconocido: {key}")


def form_preference_visible(context, key):
    if key.startswith(("tuiFixed.", "tuiFooter.")):
        from lanctl.apps.ip.interfaces.tui.keyboard import FOOTER_ACTIONS

        return key.split(".", 1)[1] in FOOTER_ACTIONS and preference_visible(
            context, "tui.footerButtons"
        )
    try:
        return preference_visible(context, _form_path(key))
    except ValueError:
        return False


def form_changes(values, config, *, visibility=None):
    """Decode legacy field names at the form boundary, without CLI parsing."""
    from lanctl.core.config import DOCUMENT_DEFAULTS, normalize_dhcp_range

    defaults = dict(leaves(DOCUMENT_DEFAULTS))
    changes = {}
    for key, raw in values.items():
        path = _form_path(key)
        if path not in defaults:
            raise ValueError(f"Campo de configuración no editable: {key}")
        default = defaults[path]
        value = raw.strip() if isinstance(raw, str) else raw
        if type(default) is bool:
            if isinstance(value, str) and value.casefold() in {"on", "off"}:
                value = value.casefold() == "on"
        elif path.startswith("tui.keyBindings.") and isinstance(value, str):
            value = value.upper().replace("+", "_")
            if value in {"NONE", "NULL", "OFF", "-"}:
                value = None
        elif path == "network.dhcpRange" and isinstance(value, str):
            value = normalize_dhcp_range(value or "off")
        elif path == "ip.listColumns" and isinstance(value, str):
            value = [part.strip() for part in value.split(",")]
        elif (
            path == "projects.directory"
            and isinstance(value, str)
            and value.casefold() in {"", "auto", "default"}
        ):
            value = None
        elif path == "tui.cliHeightPercent":
            from lanctl.apps.ip.interfaces.tui.layout import normalize_cli_percent

            value = normalize_cli_percent(value)
        elif isinstance(value, str) and (
            type(default) in {int, float} or path == "projects.saveIntervalMinutes"
        ):
            try:
                value = (
                    float(value)
                    if type(default) is float or path == "projects.saveIntervalMinutes"
                    else int(value)
                )
            except ValueError as error:
                raise ValueError(f"{path}: número no válido") from error
        changes[path] = value
    if visibility:
        from lanctl.apps.ip.interfaces.tui.keyboard import FOOTER_ACTIONS, normalize_footer_actions

        visible = normalize_footer_actions(config.get("tuiFooterButtons"))
        for action, state in visibility.items():
            if action not in FOOTER_ACTIONS or state not in {"on", "off"}:
                raise ValueError("Visibilidad TUI no válida")
            if state == "on" and action not in visible:
                visible.append(action)
            elif state == "off" and action in visible:
                visible.remove(action)
        changes["tui.footerButtons"] = [action for action in FOOTER_ACTIONS if action in visible]
    return changes


def save_form_values(values, context, *, visibility=None):
    if not isinstance(values, dict):
        raise ValueError("Configuración no válida")
    if not values and not visibility:
        return load_config()

    # Conversion and mutation use the same locked snapshot (including footer state).
    def apply(config):
        changes = form_changes(values, config, visibility=visibility)
        candidate = prepare_program_changes(config, changes, context)
        if any(path.startswith("access.remote.") for path in changes):
            from lanctl.apps.access.settings_lifecycle import remote_settings_transaction

            transaction.enter_context(remote_settings_transaction(config, candidate))
        return candidate

    with project_operation(), ExitStack() as transaction:
        return update_config(apply)


def save_setting(context, path, value, *, project_path=None):
    with project_operation():
        if context.scope == "program":
            return save_program_changes({path: value}, context)
        from lanctl.core.projects.settings import update_project_setting

        target = project_path or active_settings_project()
        entries = {entry["path"]: entry for entry in settings_entries(context, project_path=target)}
        if path not in entries or entries[path]["readOnly"]:
            raise ValueError("Ajuste de proyecto desconocido o de solo lectura")
        category, key = path.split(".", 1)
        return update_project_setting(target, category, key, value)


def cli_context(scope="program", *, legacy_paths=False):
    import os

    remote = os.environ.get("LANCTL_REMOTE_SETTINGS") == "1"
    if remote and scope == "project" and os.environ.get("LANCTL_REMOTE_PROJECT_SETTINGS") != "1":
        raise PermissionError("La configuración del proyecto remoto requiere project.manage")
    return SettingsContext(
        "remote" if remote else "cli", scope=scope, legacy_paths=legacy_paths and not remote
    )
