from __future__ import annotations

import sys
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass

from colorama import Fore, Style

from lanctl.core.config import load_config
from lanctl.core.console import error as print_error
from lanctl.core.console import ok
from lanctl.core.database import DeviceDatabase
from lanctl.core.layout import fit_text, terminal_columns
from lanctl.core.parser import colorize_help
from lanctl.shared.i18n import t

GLOBAL_HELP = """CLI interactiva de LANCTL

Comandos de contexto:
  select ELEMENTO       Selecciona un elemento por IP, MAC, alias o nombre.
  info | selected       Muestra la información del elemento seleccionado.
  deselect              Limpia la selección actual.
  clear | cls           Limpia la pantalla y conserva el contexto.
  history               Muestra los comandos escritos durante la sesión.
  version               Muestra la versión de LANCTL.
  help [COMANDO]        Muestra ayuda general o la ayuda de un comando.
  exit                  Cierra la CLI.

Puedes encadenar órdenes con ; cuando la opción avanzada está activada:
  select JL1 ; element -cnf O ; info

Cuando hay un elemento seleccionado puedes omitirlo, por ejemplo:
  select SW
  element
  scan --ports 22,80,443
  ssh probe
  switch port list
"""

CONTEXTUAL_COMMANDS = {
    "alias",
    "call",
    "cnf",
    "credential",
    "element",
    "name",
    "protocol",
    "ping",
    "scan",
    "search",
    "ssh",
    "switch",
    "terminal",
}


@dataclass
class CliSelection:
    selector: str = ""
    label: str = ""


def _clear_screen(stream=None) -> None:
    stream = stream or sys.stdout
    stream.write("\x1b[2J\x1b[H")
    stream.flush()


def _selected_command(
    parts: list[str], selection: CliSelection, database: DeviceDatabase
) -> list[str]:
    """Inyecta la selección solamente si el comando no trae otro elemento válido."""
    if not selection.selector or not parts or parts[0].casefold() not in CONTEXTUAL_COMMANDS:
        return parts
    if len(parts) > 1:
        try:
            database.resolve(parts[1])
            return parts
        except ValueError:
            pass
    return [parts[0], selection.selector, *parts[1:]]


def _run_global_command(
    raw: str,
    selection: CliSelection,
    database: DeviceDatabase,
    history: list[str],
    execute: Callable[[list[str]], int],
) -> tuple[bool, CliSelection]:
    from lanctl.core.command_line import split_command_line

    try:
        parts = split_command_line(raw)
    except ValueError as error:
        print_error(str(error))
        return False, selection
    if not parts:
        return False, selection
    command = parts[0].casefold()
    history.append(raw)
    if command in ("exit", "quit", "salir"):
        return True, selection
    if command in ("help", "?", "commands"):
        if len(parts) == 1:
            print(colorize_help(GLOBAL_HELP), end="")
        else:
            execute([parts[1], "-h"])
        return False, selection
    if command in ("clear", "cls"):
        _clear_screen()
        return False, selection
    if command == "history" and (len(parts) == 1 or parts[1:] == ["--commands"]):
        width = terminal_columns() or 120
        for number, entry in enumerate(history, 1):
            prefix = f"{number:>3}  "
            print(prefix + fit_text(entry, max(1, width - len(prefix))))
        return False, selection
    if command == "history":
        execute(parts)
        return False, selection
    if command == "version":
        from lanctl import __version__

        print(f"LANCTL {__version__}")
        return False, selection
    if command == "select":
        if len(parts) != 2:
            print_error(t("LANCTL.CLI.ERROR.SELECT_USAGE"))
            return False, selection
        try:
            device = database.resolve(parts[1])
        except ValueError:
            try:
                matches = database.search(parts[1])
                if len(matches) != 1:
                    raise ValueError(
                        f"la selección coincide con {len(matches)} elementos; usa IP, MAC o alias"
                    )
                device = matches[0]
            except ValueError as error:
                print_error(str(error))
                return False, selection
        selection = CliSelection(
            selector=device.mac or device.alias or device.ip,
            label=device.alias or device.name or device.ip or device.mac,
        )
        ok(
            t("LANCTL.CLI.STATUS.SELECTED"),
            f"{selection.label} | {device.ip or '-'} | {device.mac or '-'}",
        )
        return False, selection
    if command in ("info", "selected"):
        if not selection.selector:
            print_error(t("LANCTL.CLI.ERROR.NO_SELECTION"))
        else:
            execute(["element", selection.selector])
        return False, selection
    if command == "deselect":
        ok(t("LANCTL.CLI.STATUS.SELECTION"), t("LANCTL.CLI.STATUS.DESELECTED"))
        return False, CliSelection()
    contextual = _selected_command(parts, selection, database)
    with suppress(SystemExit):
        execute(contextual)
    return False, selection


def run_global_cli(input_fn: Callable[[str], str] = input) -> int:
    from lanctl.apps.ip.interfaces.cli.main import main

    database = DeviceDatabase(load_config()["database"])
    selection = CliSelection()
    history: list[str] = []
    print(f"{Style.BRIGHT}{Fore.CYAN}{t('LANCTL.CLI.HEADER.TITLE')}{Style.RESET_ALL}")
    print(t("LANCTL.CLI.HEADER.INTRO"))
    while True:
        prompt = f"LANCTL[{selection.label}]> " if selection.label else "LANCTL> "
        try:
            raw = input_fn(prompt).strip()
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            continue
        if not raw:
            continue
        try:
            from lanctl.core.command_line import split_command_chain

            commands = split_command_chain(raw)
        except ValueError as error:
            print_error(str(error))
            continue
        if len(commands) > 1 and not bool(load_config().get("cliCommandChaining", True)):
            print_error("el encadenamiento de comandos está desactivado en SETTINGS/AVANZADO")
            continue
        for command_text in commands:
            should_exit, selection = _run_global_command(
                command_text, selection, database, history, main
            )
            if should_exit:
                return 0
