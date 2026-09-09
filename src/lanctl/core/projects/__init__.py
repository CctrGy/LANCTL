"""API pública y diferida de los proyectos VLF."""

from importlib import import_module

_EXPORTS = {
    "ProjectCatalog": ("lanctl.core.projects.catalog", "ProjectCatalog"),
    "ProjectCatalogEntry": ("lanctl.core.projects.catalog", "ProjectCatalogEntry"),
    "VLF_FORMAT_VERSION": ("lanctl.core.projects.vlf", "VLF_FORMAT_VERSION"),
    "ProjectWorkspace": ("lanctl.core.projects.workspace", "ProjectWorkspace"),
    "activate_project_workspace": ("lanctl.core.projects.workspace", "activate_project_workspace"),
    "active_project_info": ("lanctl.core.projects.current", "active_project_info"),
    "create_project": ("lanctl.core.projects.vlf", "create_project"),
    "default_project_directory": ("lanctl.core.projects.paths", "default_project_directory"),
    "ensure_active_project_workspace": (
        "lanctl.core.projects.workspace",
        "ensure_active_project_workspace",
    ),
    "inspect_project": ("lanctl.core.projects.vlf", "inspect_project"),
    "list_project_entries": ("lanctl.core.projects.vlf", "list_project_entries"),
    "prepare_project_workspace": ("lanctl.core.projects.workspace", "prepare_project_workspace"),
    "resolve_project_path": ("lanctl.core.projects.paths", "resolve_project_path"),
    "SaveMode": ("lanctl.core.projects.save_policy", "SaveMode"),
    "SaveTrigger": ("lanctl.core.projects.save_policy", "SaveTrigger"),
    "available_save_modes": ("lanctl.core.projects.save_policy", "available_save_modes"),
    "close_active_project": ("lanctl.core.projects.save_policy", "close_active_project"),
    "normalize_save_mode": ("lanctl.core.projects.save_policy", "normalize_save_mode"),
    "save_active_project": ("lanctl.core.projects.save_policy", "save_active_project"),
    "start_autosave_scheduler": ("lanctl.core.projects.save_policy", "start_autosave_scheduler"),
    "update_project": ("lanctl.core.projects.vlf", "update_project"),
    "verify_project": ("lanctl.core.projects.vlf", "verify_project"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted((*globals(), *__all__))
