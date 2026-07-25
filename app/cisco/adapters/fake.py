from __future__ import annotations

from app.cisco.models import CommandPlan


class FakeCiscoAdapter:
    """Adaptador sin red: conserva planes para pruebas y devuelve salida simulada."""

    def __init__(self):
        self.executed: list[CommandPlan] = []

    def execute(self, plan: CommandPlan) -> list[str]:
        self.executed.append(plan)
        return [f"SIMULADO: {command}" for command in plan.native_commands]
