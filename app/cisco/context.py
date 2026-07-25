from __future__ import annotations

from dataclasses import dataclass

from app.cisco.models import PortProfile, SwitchProfile


@dataclass
class CiscoContext:
    profile: SwitchProfile
    selected_port: PortProfile | None = None

    def select(self, reference: str) -> PortProfile:
        self.selected_port = self.profile.resolve_port(reference)
        return self.selected_port

    def deselect(self) -> None:
        self.selected_port = None
