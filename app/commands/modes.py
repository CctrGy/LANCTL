from __future__ import annotations

import shlex
import sys
from collections.abc import Callable
from dataclasses import dataclass

from colorama import Fore, Style

from app.core.parser import colorize_help
from app.core.config import load_config
from app.core.console import error as print_error, ok
from app.core.database import DeviceDatabase
from app.core.layout import fit_text, terminal_columns
from app.i18n import t


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

Cuando hay un elemento seleccionado puedes omitirlo, por ejemplo:
  select SW
  element
  scan --ports 22,80,443
  ssh probe
  switch port list
"""

CONTEXTUAL_COMMANDS = {
    "alias", "call", "cnf", "credential", "element", "name", "protocol",
    "ping", "scan", "search", "ssh", "switch", "terminal",
}


@dataclass
class CliSelection:
    selector: str = ""
    label: str = ""


def _clear_screen(stream=None) -> None:
    stream = stream or sys.stdout
    stream.write("\x1b[2J\x1b[H")
    stream.flush()


def _selected_command(parts: list[str], selection: CliSelection, database: DeviceDatabase) -> list[str]:
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


def run_global_cli(input_fn: Callable[[str], str] = input) -> int:
    from app.cli import main

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
            parts = shlex.split(raw)
        except ValueError as error:
            print_error(str(error))
            continue
        command = parts[0].casefold()
        history.append(raw)
        if command in ("exit", "quit", "salir"):
            return 0
        if command in ("help", "?", "commands"):
            if len(parts) == 1:
                print(colorize_help(GLOBAL_HELP), end="")
            else:
                main([parts[1], "/?"])
            continue
        if command in ("clear", "cls"):
            _clear_screen()
            continue
        if command == "history" and (len(parts) == 1 or parts[1:] == ["--commands"]):
            width = terminal_columns() or 120
            for number, entry in enumerate(history, 1):
                prefix = f"{number:>3}  "
                print(prefix + fit_text(entry, max(1, width - len(prefix))))
            continue
        if command == "history":
            main(parts)
            continue
        if command == "version":
            from app import __version__
            print(f"LANCTL {__version__}")
            continue
        if command == "select":
            if len(parts) != 2:
                print_error(t("LANCTL.CLI.ERROR.SELECT_USAGE"))
                continue
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
                    continue
            # La MAC sigue identificando el elemento aunque su IP cambie.
            selection.selector = device.mac or device.alias or device.ip
            selection.label = device.alias or device.name or device.ip or device.mac
            ok(t("LANCTL.CLI.STATUS.SELECTED"), f"{selection.label} | {device.ip or '-'} | {device.mac or '-'}")
            continue
        if command in ("info", "selected"):
            if not selection.selector:
                print_error(t("LANCTL.CLI.ERROR.NO_SELECTION"))
            else:
                main(["element", selection.selector])
            continue
        if command == "deselect":
            selection = CliSelection()
            ok(t("LANCTL.CLI.STATUS.SELECTION"), t("LANCTL.CLI.STATUS.DESELECTED"))
            continue
        contextual = _selected_command(parts, selection, database)
        try:
            main(contextual)
        except SystemExit:
            continue
