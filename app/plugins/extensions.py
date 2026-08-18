from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EXTENSION_TYPES = {
    "command",
    "theme",
    "language",
    "settings",
    "automation",
    "network",
    "analysis",
    "ui-panel",
    "ui-action",
    "security",
    "config",
    "protocol",
    "scanner",
    "device-adapter",
    "parser",
    "exporter",
    "project-handler",
    "project-save-mode",
    "physical-model",
    "icon",
}


@dataclass(frozen=True, slots=True)
class Extension:
    extension_id: str
    extension_type: str
    owner: str
    specification: dict[str, Any] = field(default_factory=dict)


class ExtensionRegistry:
    """Registro común consumible por CLI, TUI y la futura GUI."""

    def __init__(self) -> None:
        self._items: dict[str, Extension] = {}

    def register(
        self, extension_id: str, extension_type: str, owner: str, specification: dict | None = None
    ) -> Extension:
        kind = extension_type.casefold()
        if kind not in EXTENSION_TYPES:
            raise ValueError(f"tipo de extensión desconocido: {extension_type}")
        key = extension_id.casefold()
        if key in self._items:
            raise ValueError(f"extensión ya registrada: {extension_id}")
        item = Extension(extension_id, kind, owner, dict(specification or {}))
        self._items[key] = item
        return item

    def remove_owner(self, owner: str) -> None:
        self._items = {key: item for key, item in self._items.items() if item.owner != owner}

    def list(self, extension_type: str | None = None) -> list[Extension]:
        values = self._items.values()
        if extension_type:
            values = (item for item in values if item.extension_type == extension_type.casefold())
        return sorted(values, key=lambda item: (item.extension_type, item.extension_id.casefold()))
