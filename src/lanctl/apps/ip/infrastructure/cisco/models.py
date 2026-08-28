from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Risk(str, Enum):
    READ_ONLY = "READ_ONLY"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    DISRUPTIVE = "DESTRUCTIVE_OR_DISRUPTIVE"
    PERSIST_CONFIG = "PERSIST_CONFIG"

    @property
    def requires_confirmation(self) -> bool:
        return self is not Risk.READ_ONLY


@dataclass(frozen=True)
class PortProfile:
    id: str
    native: str
    aliases: tuple[str, ...] = ()
    label: str = ""

    def references(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.id, self.native, self.label, *self.aliases)))


@dataclass(frozen=True)
class SwitchProfile:
    id: str
    model: str
    ports: tuple[PortProfile, ...]

    def resolve_port(self, reference: str) -> PortProfile:
        wanted = reference.strip().casefold()
        matches = [
            port
            for port in self.ports
            if wanted and any(wanted == value.casefold() for value in port.references() if value)
        ]
        if not matches:
            raise ValueError(f"puerto no reconocido por el perfil {self.id}: {reference}")
        if len(matches) > 1:
            raise ValueError(f"la referencia de puerto es ambigua: {reference}")
        return matches[0]


@dataclass(frozen=True)
class CommandSpec:
    id: str
    path: tuple[str, ...]
    aliases: tuple[tuple[str, ...], ...]
    context: tuple[str, ...]
    risk: Risk
    help: str
    templates: tuple[str, ...]
    port_required: bool = False
    argument: str = ""
    response_parser: Callable[[str], Any] | None = None


@dataclass(frozen=True)
class CommandPlan:
    command_id: str
    device_id: str
    device_label: str
    endpoint: str
    risk: Risk
    native_commands: tuple[str, ...]
    target: str = ""
    native_target: str = ""
    arguments: dict[str, str] = field(default_factory=dict)

    @property
    def confirmation_required(self) -> bool:
        return self.risk.requires_confirmation
