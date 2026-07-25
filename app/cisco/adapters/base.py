from __future__ import annotations

from typing import Protocol

from app.cisco.models import CommandPlan


class CiscoAdapter(Protocol):
    def execute(self, plan: CommandPlan) -> list[str]: ...
