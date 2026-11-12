from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from lanctl.apps.ip.domain.models.device import normalize_mac


@dataclass(slots=True)
class Group:
    """Grupo editable de dispositivos, identificado por un nombre único."""

    name: str
    description: str = "-"
    members: list[str] = field(default_factory=list)
    editable: bool = True
    member_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.upper()
        self.description = self.description or "-"
        if len(self.description) > 42:
            raise ValueError("la descripción de un grupo no puede superar 42 caracteres")
        self.members = list(dict.fromkeys(normalize_mac(mac) for mac in self.members))
        if not isinstance(self.member_ids, list) or any(
            not isinstance(value, str) or not value.strip() for value in self.member_ids
        ):
            from lanctl.shared.i18n import t

            raise ValueError(t("LANCTL.STORAGE.ERROR.GROUP_RECORD"))
        self.member_ids = list(dict.fromkeys(self.member_ids))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Group:
        if ("memberIds" in value or "membershipSchemaVersion" in value) and (
            type(value.get("membershipSchemaVersion")) is not int
            or value["membershipSchemaVersion"] != 1
        ):
            from lanctl.shared.i18n import t

            raise ValueError(t("LANCTL.STORAGE.ERROR.GROUP_RECORD"))
        return cls(
            name=str(value["name"]),
            description=str(value.get("description", "-")),
            members=[str(mac) for mac in value.get("members", [])],
            editable=bool(value.get("editable", str(value.get("name", "")).upper() != "BASIC")),
            member_ids=value.get("memberIds", []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "members": self.members,
            "editable": self.editable,
            **(
                {"membershipSchemaVersion": 1, "memberIds": self.member_ids}
                if self.member_ids
                else {}
            ),
        }
