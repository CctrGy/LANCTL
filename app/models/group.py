from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.models.device import normalize_mac


@dataclass(slots=True)
class Group:
    """Grupo editable de dispositivos, identificado por un nombre único."""

    name: str
    description: str = "-"
    members: list[str] = field(default_factory=list)
    editable: bool = True

    def __post_init__(self) -> None:
        self.name = self.name.upper()
        self.description = self.description or "-"
        if len(self.description) > 42:
            raise ValueError("la descripción de un grupo no puede superar 42 caracteres")
        self.members = list(dict.fromkeys(normalize_mac(mac) for mac in self.members))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Group:
        return cls(
            name=str(value["name"]),
            description=str(value.get("description", "-")),
            members=[str(mac) for mac in value.get("members", [])],
            editable=bool(value.get("editable", str(value.get("name", "")).upper() != "BASIC")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "members": self.members,
            "editable": self.editable,
        }
