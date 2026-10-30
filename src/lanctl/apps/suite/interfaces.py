"""CLI and TUI adapters for the root launcher."""

from lanctl.core.interactive_console import command_console
from lanctl.shared.i18n import t


def run_console(*, tui=False):
    from lanctl.bootstrap.lanctl import main

    return command_console(
        "LANCTL",
        main,
        tui=tui,
        overview=(t("LANCTL.SUITE.OVERVIEW.TEXT")),
        shortcuts={
            str(i): [app, "--tui"]
            for i, app in enumerate(("lanip", "lanwire", "lanrack", "lanaccess", "lanmon"), 1)
        },
    )
