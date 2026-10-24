"""A shared selection between operations; a consistent snapshot within one."""

import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

_operation_config = ContextVar("lanctl_project_operation", default=None)


@contextmanager
def project_operation(config=None):
    """Do not redirect an in-flight scan/write when another window switches."""
    if _operation_config.get() is not None:
        yield
        return
    if config is None:
        from lanctl.core.config import load_config

        config = load_config()
    token = _operation_config.set(deepcopy(config))
    try:
        yield
    finally:
        _operation_config.reset(token)


def operation_config():
    value = _operation_config.get()
    return deepcopy(value) if value is not None else None


def commit_operation_config(config):
    if _operation_config.get() is not None:
        from lanctl.core.session import PROJECT_KEYS

        value = deepcopy(config)
        if hasattr(value, "project_base"):
            value.project_base = {key: deepcopy(value.get(key)) for key in PROJECT_KEYS}
            value.base_values = deepcopy(dict(value))
        _operation_config.set(value)


def project_identity(config):
    """Bind displayed data to its project and stores without exporting secrets."""
    paths = {
        key: config.get(key)
        for key in (
            "groups",
            "physicalDatabase",
            "monitorDatabase",
            "monitorRuntime",
            "monitorIncidents",
            "monitorLock",
            "monitorProfiles",
            "monitorAssignments",
            "credentials",
        )
    }
    digest = hashlib.sha256(json.dumps(paths, sort_keys=True).encode()).hexdigest()
    return [config.get("activeProject") or "", config.get("database") or "", digest]


def require_project(expected):
    from lanctl.core.config import load_config

    if expected != project_identity(load_config()):
        raise ValueError(
            "El proyecto cambió en otra ventana. Cierra el formulario y actualiza "
            "la vista antes de continuar; no se han aplicado los cambios."
        )
