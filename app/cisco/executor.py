from __future__ import annotations

from dataclasses import dataclass

from app.cisco.adapters.base import CiscoAdapter
from app.cisco.models import CommandPlan


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    output: tuple[str, ...] = ()


class CiscoExecutor:
    """Aplica la política final antes de entregar un plan a un adaptador."""

    def __init__(self, adapter: CiscoAdapter):
        self.adapter = adapter

    def execute(
        self, plan: CommandPlan, *, dry_run: bool = False, approved: bool = False
    ) -> ExecutionResult:
        if dry_run:
            return ExecutionResult("DRY_RUN")
        if plan.confirmation_required and not approved:
            raise ValueError(
                f"el plan {plan.command_id} requiere autorización explícita "
                f"por riesgo {plan.risk.value}"
            )
        return ExecutionResult("EXECUTED", tuple(self.adapter.execute(plan)))
