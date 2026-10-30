"""Shared CLI/TUI command host. Application dispatch remains in its adapter."""

from __future__ import annotations

import io
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from pathlib import Path

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from lanctl import __version__
from lanctl.core.command_line import split_command_line
from lanctl.core.console import error as print_error
from lanctl.core.errors import LanctlError, errors
from lanctl.core.terminal_ui import ManagementScreen
from lanctl.shared.i18n import t

CONSOLE_HELP = """Comandos de consola:
  clear | cls       Limpiar la pantalla (no borra datos ni logs).
  pwd               Mostrar el directorio de trabajo.
  commands          Mostrar estos comandos básicos.
  help [comando]    Mostrar ayuda general o de un comando.
  version           Mostrar la versión.
  exit | quit | q   Salir o volver al llamador.
"""


def command_console(
    name, dispatch, *, tui=False, overview="", shortcuts=None, on_close=None, notifications=None
):
    """Run commands with native streams: passwords and child TUIs are never captured."""
    shortcuts = shortcuts or {}
    status = t("LANCTL.UI.TEXT.READY_HELP_LISTS_COMMANDS_EXIT_RETURNS_OR_EXITS")
    with ManagementScreen() if tui else nullcontext(None) as screen:
        if not screen:
            print(f"{name} CLI {__version__} | help | exit")
        while True:
            pending = notifications() if notifications else []
            if pending:
                with screen.suspended() if screen else nullcontext():
                    for message in pending:
                        print(message)
            # A failed inventory read must not tear down the whole console.
            try:
                content = overview() if screen and callable(overview) else overview
            except (OSError, RuntimeError, ValueError) as exc:
                errors.from_exception(
                    exc, origin="LANCTL.Suite.Console.Render", code="CONSOLE.VIEW.FAILED", level=34
                )
                content = t("LANCTL.UI.TEXT.COULD_NOT_LOAD_THE_PANEL_YOU_CAN_VIEW_HELP_OR_EXIT")
                status = str(exc)
            if screen:
                screen.draw(
                    Group(
                        Panel(
                            Text(content),
                            title=f"{name} TUI · {__version__}",
                        ),
                        Panel(Text(status), title=t("LANCTL.UI.TEXT.STATUS")),
                        Text(
                            t(
                                "LANCTL.UI.TEXT.ENTER_A_COMMAND_AND_PRESS_ENTER_HELP_FOR_HELP_EXIT_TO_QUIT"
                            )
                        ),
                    )
                )
            try:
                line = input(f"{name}> ").strip()
                if line.casefold() in {"exit", "quit", "q"}:
                    if on_close is None:
                        return 0
                    with screen.suspended() if screen else nullcontext():
                        if on_close():
                            return 0
                    status = t("LANCTL.UI.TEXT.CLOSE_CANCELLED_THE_CONSOLE_REMAINS_OPEN")
                    continue
                if not line:
                    continue
                words = split_command_line(line)
                if not words:
                    continue
                words = list(shortcuts.get(line.casefold(), words))
                builtin = words[0].casefold()
                if builtin in {"clear", "cls", "pwd", "commands"}:
                    if len(words) != 1:
                        status = t("LANCTL.CONSOLE.USAGE.NO_ARGUMENTS", command=builtin)
                        if not screen:
                            print(status)
                        continue
                    if builtin in {"clear", "cls"}:
                        status = t("LANCTL.UI.TEXT.READY")
                        if not screen:
                            console = Console()
                            if console.is_terminal:
                                console.clear()
                        continue
                    content = str(Path.cwd()) if builtin == "pwd" else t("LANCTL.CONSOLE.HELP.TEXT")
                    if screen:
                        screen.show_text(content, title=f"{name} · {builtin}")
                    else:
                        print(content)
                    status = "Última operación: correcta (código 0)."
                    continue
                general_help = len(words) == 1 and builtin in {"help", "--help", "-h", "/?"}
                if words[0].casefold() == "help":
                    words = [*words[1:], "--help"]
                elif len(words) == 1 and builtin == "version":
                    words = ["--version"]
                if words[0] in {"--cli", "-cli", "--tui", "-tui"}:
                    status = "Ya estás en una consola. Usa comandos, no anides esta interfaz."
                    if not screen:
                        print(status)
                    continue
                # Help is read-only content, not a child interactive session.
                # Capture only explicit help/version requests; passwords and
                # real CLI/TUI applications retain their native terminal streams.
                if screen and (
                    any(word in {"--help", "-h", "/?"} for word in words) or words == ["--version"]
                ):
                    output = io.StringIO()
                    with redirect_stdout(output), redirect_stderr(output):
                        if general_help:
                            print(t("LANCTL.CONSOLE.HELP.TEXT"))
                        try:
                            result = dispatch(words)
                            code = result if isinstance(result, int) else 0
                        except SystemExit as exc:
                            code = exc.code if isinstance(exc.code, int) else 1
                    screen.show_text(
                        output.getvalue() or t("LANCTL.UI.PROMPT.THE_COMMAND_RETURNED_NO_CONTENT"),
                        title=f"{name} · {' '.join(words)}",
                    )
                    status = t(
                        "LANCTL.UI.MESSAGE.LAST_OPERATION_VALUE_CODE_VALUE",
                        value0=f"{('correcta' if code == 0 else 'fallida')}",
                        value1=f"{code}",
                    )
                    continue
                # A child TUI owns the terminal until it returns. No nested alternate buffers.
                with screen.suspended() if screen else nullcontext():
                    try:
                        if general_help:
                            print(t("LANCTL.CONSOLE.HELP.TEXT"))
                        result = dispatch(words)
                        code = result if isinstance(result, int) else 0
                    except SystemExit as exc:
                        code = exc.code if isinstance(exc.code, int) else 1
                    except LanctlError as exc:
                        if exc.print_output:
                            print_error(exc.event.terminal_message())
                        code = exc.exit_code
                    except KeyboardInterrupt:
                        # Cancel the operation, not its parent management console.
                        print(t("LANCTL.CORE.APP.CANCELLED"))
                        code = 130
                    status = t(
                        "LANCTL.UI.MESSAGE.LAST_OPERATION_VALUE_CODE_VALUE",
                        value0=f"{('correcta' if code == 0 else 'fallida')}",
                        value1=f"{code}",
                    )
                    if screen:
                        input(t("LANCTL.UI.SCREEN.PRESS_ENTER_TO_RETURN_TO_THE_PANEL"))
            except (EOFError, KeyboardInterrupt):
                if on_close is None:
                    return 0
                with screen.suspended() if screen else nullcontext():
                    return 0 if on_close(interactive=False) else 1
            except (OSError, RuntimeError, ValueError) as exc:
                errors.from_exception(
                    exc,
                    origin="LANCTL.Suite.Console.Command",
                    code="CONSOLE.COMMAND.FAILED",
                    level=34,
                )
                status = str(exc)
                if not screen:
                    print(status)
