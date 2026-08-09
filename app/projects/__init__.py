"""API pública y diferida de los proyectos VLF."""

from importlib import import_module

_EXPORTS = {
    "VLF_FORMAT_VERSION": ("app.projects.vlf", "VLF_FORMAT_VERSION"),
    "ProjectWorkspace": ("app.projects.workspace", "ProjectWorkspace"),
    "activate_project_workspace": ("app.projects.workspace", "activate_project_workspace"),
    "active_project_info": ("app.projects.current", "active_project_info"),
    "create_project": ("app.projects.vlf", "create_project"),
    "default_project_directory": ("app.projects.paths", "default_project_directory"),
    "ensure_active_project_workspace": (
        "app.projects.workspace",
        "ensure_active_project_workspace",
    ),
    "inspect_project": ("app.projects.vlf", "inspect_project"),
    "list_project_entries": ("app.projects.vlf", "list_project_entries"),
    "prepare_project_workspace": ("app.projects.workspace", "prepare_project_workspace"),
    "resolve_project_path": ("app.projects.paths", "resolve_project_path"),
    "update_project": ("app.projects.vlf", "update_project"),
    "verify_project": ("app.projects.vlf", "verify_project"),
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
