from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

PLUGIN_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
LCP_SCHEMA_VERSION = 1
EVENT_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z][A-Za-z0-9_-]*){3}$")
CAPABILITIES = {
    "plugin",
    "theme",
    "language",
    "settings",
    "automation",
    "network",
    "analysis",
    "ui",
    "security",
    "config",
    "commands",
    "protocol",
    "scanner",
    "device-adapter",
    "parser",
    "exporter",
    "project-handler",
    "physical-model",
    "icon",
}


class PluginState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    INCOMPATIBLE = "INCOMPATIBLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class PluginDependency:
    plugin_id: str
    version: str = "*"


@dataclass(frozen=True, slots=True)
class PluginManifest:
    schema_version: int
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    entry_point: str
    minimum_lanctl: str
    maximum_lanctl: str
    permissions: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ("plugin",)
    dependencies: tuple[PluginDependency, ...] = ()
    runtime: str = "isolated"
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> PluginManifest:
        if not isinstance(value, dict):
            raise ValueError("plugin.info debe contener un objeto JSON")
        schema_version = int(value.get("schemaVersion", 1))
        if schema_version != LCP_SCHEMA_VERSION:
            raise ValueError(
                f"schema LCP no compatible: {schema_version}; "
                f"esta versión admite {LCP_SCHEMA_VERSION}"
            )
        plugin_id = str(value.get("id", "")).strip().casefold()
        if not PLUGIN_ID.fullmatch(plugin_id):
            raise ValueError("id de plugin no válido; usa un identificador como lanctl.autoscan")
        capabilities = tuple(
            dict.fromkeys(str(v).casefold() for v in value.get("capabilities", ["plugin"]))
        )
        unknown = sorted(set(capabilities) - CAPABILITIES)
        if unknown:
            raise ValueError(f"capacidades LCP desconocidas: {', '.join(unknown)}")
        compat = value.get("lanctl") or {}
        dependencies = tuple(
            PluginDependency(str(item["id"]).casefold(), str(item.get("version", "*")))
            if isinstance(item, dict)
            else _parse_dependency(str(item))
            for item in value.get("depends", [])
        )
        entry = str(value.get("entryPoint", "main.exec")).replace("\\", "/")
        if entry.startswith("/") or ".." in entry.split("/"):
            raise ValueError("entryPoint no seguro")
        runtime = str(value.get("runtime", "isolated")).casefold()
        if runtime not in ("isolated", "trusted"):
            raise ValueError("runtime debe ser isolated o trusted")
        return cls(
            schema_version=schema_version,
            plugin_id=plugin_id,
            name=str(value.get("name") or plugin_id),
            version=str(value.get("version", "0.0.0")),
            description=str(value.get("description", "")),
            author=str(value.get("author", "")),
            entry_point=entry,
            minimum_lanctl=str(compat.get("minimumVersion", "0.0.0")),
            maximum_lanctl=str(compat.get("maximumVersion", "*")),
            permissions=tuple(
                dict.fromkeys(str(v).casefold() for v in value.get("permissions", []))
            ),
            capabilities=capabilities,
            dependencies=dependencies,
            runtime=runtime,
            raw=dict(value),
        )


def _parse_dependency(value: str) -> PluginDependency:
    parts = value.split(maxsplit=1)
    return PluginDependency(parts[0].casefold(), parts[1] if len(parts) > 1 else "*")
