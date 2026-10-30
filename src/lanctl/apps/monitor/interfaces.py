"""LANMON CLI and read-only event console; no dependency on the LANIP interface."""

from __future__ import annotations

import json

from rich.console import Group
from rich.table import Table

from lanctl.apps.monitor.event_view import read_events
from lanctl.core.config import load_config
from lanctl.shared.i18n import t


def event_console(*, project=None, tui=False):
    from lanctl.core.terminal_ui import ManagementScreen

    if tui:
        with ManagementScreen() as screen:
            return _loop(project, screen)
    return _loop(project, None)


def _loop(project, screen):
    import shutil

    source, minimum = "all", 1
    page = 0
    while True:
        rows = read_events(load_config(), project=project, source=source, minimum=minimum)
        if screen:
            size = max(1, shutil.get_terminal_size((100, 30)).lines - 10)
            pages = max(1, (len(rows) + size - 1) // size)
            page = min(page, pages - 1)
            table = Table(title=t("LANCTL.UI.TEXT.LANMON_PROGRAM_AND_PROJECT_EVENTS"), expand=True)
            for title in (
                t("LANCTL.UI.TEXT.SOURCE"),
                t("LANCTL.UI.TEXT.FILE"),
                t("LANCTL.UI.TEXT.LEVEL"),
                t("LANCTL.UI.TEXT.EVENT"),
            ):
                table.add_column(title, no_wrap=True)
            for row in list(reversed(rows))[page * size : (page + 1) * size]:
                from rich.text import Text

                table.add_row(
                    row["source"], row["file"], str(row["level"] or "—"), Text(row["message"])
                )
            screen.draw(
                Group(
                    table,
                    t("LANCTL.MONITOR.VIEW.PAGE", page=page + 1, pages=pages),
                )
            )
        else:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            print(t("LANCTL.UI.TEXT.R_RELOAD_P_PROGRAM_J_PROJECT_A_BOTH_LEVEL_1_59_Q_QUIT"))
        try:
            command = input("LANMON> ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            return 0
        if command in {"q", "exit", "quit"}:
            return 0
        if screen and command in {"n", "b"}:
            page = max(0, min(pages - 1, page + (1 if command == "n" else -1)))
        if command in {"p", "j", "a"}:
            source = {"p": "program", "j": "project", "a": "all"}[command]
        elif command.startswith("level "):
            value = command[6:].strip()
            if value.isdecimal() and 1 <= int(value) <= 59:
                minimum = int(value)
            else:
                print(t("LANCTL.UI.TEXT.VALID_LEVEL_1_59"))
