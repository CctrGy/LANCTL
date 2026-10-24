"""Preferencias exclusivas de la interfaz de LANWIRE.

No reutilizan la configuración de LANIP: esta pantalla solo controla cómo se
presenta y opera el editor físico local.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from lanctl.apps.wire.path import application_path
from lanctl.apps.wire.xfile import read, write_json
from lanctl.core.file_transaction import locked_file

DEFAULT_SETTINGS = {
    "panelLayout": "cli.bottom",
    "cliHeight": 12,
    "tableDensity": "comfortable",
    "confirmExit": True,
    "showDescriptions": True,
    "showGroups": True,
    "columnWidths": {
        "idf": 10,
        "type": 14,
        "name": 18,
        "group": 12,
        "description": 0,
    },
}


def settings_path() -> Path:
    return application_path("data/lw/tui.config")


def load_settings() -> dict[str, Any]:
    path = settings_path()
    try:
        stored = read(path) if path.exists() else {}
    except (OSError, ValueError):
        stored = {}
    settings = deepcopy(DEFAULT_SETTINGS)
    if isinstance(stored, dict):
        settings.update({key: stored[key] for key in settings if key in stored})
    settings["cliHeight"] = _bounded_int(settings["cliHeight"], 8, 18, 12)
    settings["panelLayout"] = (
        settings["panelLayout"]
        if settings["panelLayout"] in {"cli.top", "cli.bottom"}
        else "cli.bottom"
    )
    settings["tableDensity"] = (
        settings["tableDensity"]
        if settings["tableDensity"] in {"compact", "comfortable"}
        else "comfortable"
    )
    settings["confirmExit"] = bool(settings["confirmExit"])
    settings["showDescriptions"] = bool(settings["showDescriptions"])
    settings["showGroups"] = bool(settings["showGroups"])
    widths = settings.get("columnWidths")
    if not isinstance(widths, dict):
        widths = {}
    settings["columnWidths"] = {
        name: _bounded_int(
            widths.get(name, default), 0 if name == "description" else 6, 60, default
        )
        for name, default in DEFAULT_SETTINGS["columnWidths"].items()
    }
    return settings


def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError, OverflowError):
        return default


def save_settings(settings: dict[str, Any]) -> Path:
    if not isinstance(settings, dict) or set(settings) - DEFAULT_SETTINGS.keys():
        raise ValueError("Preferencias TUI de LANWIRE desconocidas")
    for key, value in settings.items():
        if key in {"confirmExit", "showDescriptions", "showGroups"}:
            valid = type(value) is bool
        elif key == "cliHeight":
            valid = type(value) is int and 8 <= value <= 18
        elif key == "panelLayout":
            valid = isinstance(value, str) and value in {"cli.top", "cli.bottom"}
        elif key == "tableDensity":
            valid = isinstance(value, str) and value in {"compact", "comfortable"}
        else:
            valid = (
                isinstance(value, dict) and not set(value) - DEFAULT_SETTINGS["columnWidths"].keys()
            )
            if valid:
                valid = all(
                    type(width) is int and (0 if name == "description" else 6) <= width <= 60
                    for name, width in value.items()
                )
        if not valid:
            raise ValueError(f"Preferencia TUI de LANWIRE no válida: {key}")
    with locked_file(settings_path()):
        normalized = load_settings()
        for key, value in settings.items():
            if key == "columnWidths":
                normalized[key].update(value)
            else:
                normalized[key] = value
        return write_json(settings_path(), normalized)
