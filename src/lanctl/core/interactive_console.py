"""Shared CLI/TUI command host. Application dispatch remains in its adapter."""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from lanctl import __version__
from lanctl.core.command_line import split_command_line
from lanctl.core.console import error as print_error
from lanctl.core.errors import LanctlError, errors
from lanctl.core.terminal_ui import ManagementScreen

CONSOLE_HELP = """Comandos de consola:
  clear | cls       Limpiar la pantalla (no borra datos ni logs).
  pwd               Mostrar el directorio de trabajo.
  commands          Mostrar estos comandos básicos.
  help [comando]    Mostrar ayuda general o de un comando.
  version           Mostrar la versión.
  exit | quit | q   Salir o volver al llamador.
"""


def command_console(name, dispatch, *, tui=False, overview="", shortcuts=None):
    """Run commands with native streams: passwords and child TUIs are never captured."""
    shortcuts = shortcuts or {}
    status = "Preparado. help muestra los comandos; exit vuelve o sale."
    with ManagementScreen() if tui else nullcontext(None) as screen:
        if not screen:
            print(f"{name} CLI {__version__} | help | exit")
        while True:
            # A failed inventory read must not tear down the whole console.
            try:
                content = overview() if screen and callable(overview) else overview
            except (OSError, RuntimeError, ValueError) as exc:
                errors.from_exception(
                    exc, origin="LANCTL.Suite.Console.Render", code="CONSOLE.VIEW.FAILED", level=34
                )
                content = "No se pudo cargar el panel. Puedes consultar ayuda o salir."
                status = str(exc)
            if screen:
                screen.draw(
                    Group(
                        Panel(
                            Text(content),
                            title=f"{name} TUI · {__version__}",
                        ),
                        Panel(Text(status), title="Estado"),
                        Text("Introduce un comando y pulsa Enter · help ayuda · exit salir"),
                    )
                )
            try:
                line = input(f"{name}> ").strip()
                if line.casefold() in {"exit", "quit", "q"}:
                    return 0
                if not line:
                    continue
                words = split_command_line(line)
                if not words:
                    continue
                words = list(shortcuts.get(line.casefold(), words))
                builtin = words[0].casefold()
                if builtin in {"clear", "cls", "pwd", "commands"}:
                    if len(words) != 1:
                        status = f"Uso: {builtin} (sin argumentos)."
                        if not screen:
                            print(status)
                        continue
                    if builtin in {"clear", "cls"}:
                        status = "Preparado."
                        if not screen:
                            console = Console()
                            if console.is_terminal:
                                console.clear()
                        continue
                    with screen.suspended() if screen else nullcontext():
                        print(str(Path.cwd()) if builtin == "pwd" else CONSOLE_HELP)
                        if screen:
                            input("Pulsa Enter para volver al panel…")
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
                # A child TUI owns the terminal until it returns. No nested alternate buffers.
                with screen.suspended() if screen else nullcontext():
                    try:
                        if general_help:
                            print(CONSOLE_HELP)
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
                        print("Operación cancelada.")
                        code = 130
                    status = f"Última operación: {'correcta' if code == 0 else 'fallida'} (código {code})."
                    if screen:
                        input("Pulsa Enter para volver al panel…")
            except (EOFError, KeyboardInterrupt):
                return 0
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
