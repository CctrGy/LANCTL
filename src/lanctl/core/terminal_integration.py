"""Optional terminal routing; no OS-specific dependency in the launcher."""

from __future__ import annotations

FUNCTION = "TerminalIntegration.Runtime.Tui.Route"
OWNER = "lanctl.integration.terminal"


def route_tui(manager, arguments: list[str]) -> bool:
    try:
        owner = manager.functions.owner(FUNCTION)
    except ValueError:
        return False
    if owner != OWNER:
        return False
    result = manager.functions.call(FUNCTION, list(arguments), caller="LANCTL")
    if not result.success:
        # Failure leaves the current terminal usable; it must not lose the TUI.
        from lanctl.core.console import error

        error(result.message, log=False)
        return False
    return isinstance(result.data, dict) and result.data.get("relaunched") is True
