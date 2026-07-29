from __future__ import annotations

import argparse
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


VIRTUAL_HELP = """CLI virtual de LANCTL

Gestiona la representación lógica de la LAN: elementos, IP, MAC, nombres,
grupos, escaneos, protocolos, terminales y control gestionado.

Escribe un comando sin el prefijo `run virtual`, por ejemplo:
  list
  scan ESP
  element GATEWAY
  switch SW --dry-run show version
  project create Casa.vlf --name "Red de casa"
  project verify Casa.vlf
  help
  exit
"""

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
    print(f"{Style.BRIGHT}{Fore.CYAN}LANCTL CLI{Style.RESET_ALL}")
    print("Escribe 'help' para ver los comandos y 'exit' para salir.")
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
                main(["virtual", parts[1], "/?"])
            continue
        if command in ("clear", "cls"):
            _clear_screen()
            continue
        if command == "history":
            width = terminal_columns() or 120
            for number, entry in enumerate(history, 1):
                prefix = f"{number:>3}  "
                print(prefix + fit_text(entry, max(1, width - len(prefix))))
            continue
        if command == "version":
            from app import __version__
            print(f"LANCTL {__version__}")
            continue
        if command == "select":
            if len(parts) != 2:
                print_error("usa: select ELEMENTO")
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
            ok("SELECCIONADO", f"{selection.label} | {device.ip or '-'} | {device.mac or '-'}")
            continue
        if command in ("info", "selected"):
            if not selection.selector:
                print_error("no hay ningún elemento seleccionado")
            else:
                main(["virtual", "element", selection.selector])
            continue
        if command == "deselect":
            selection = CliSelection()
            ok("SELECCION", "Contexto de elemento eliminado.")
            continue
        contextual = _selected_command(parts, selection, database)
        try:
            main(["virtual", *contextual])
        except SystemExit:
            continue


def _interactive_loop(
    scope: str,
    help_text: str,
    dispatch: Callable[[list[str]], int],
    input_fn: Callable[[str], str] = input,
) -> int:
    print(f"{Style.BRIGHT}{Fore.CYAN}LANCTL/{scope}{Style.RESET_ALL}")
    print("Escribe 'help' para ver los comandos y 'exit' para salir.")
    while True:
        try:
            raw = input_fn(f"LANCTL/{scope}> ").strip()
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
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {error}")
            continue
        command = parts[0].casefold()
        if command in ("exit", "quit", "salir"):
            return 0
        if command in ("clear", "cls"):
            _clear_screen()
            continue
        if command in ("help", "?"):
            print(colorize_help(help_text), end="")
            continue
        try:
            dispatch(parts)
        except SystemExit:
            # argparse usa SystemExit para ayuda y errores; no debe cerrar el REPL.
            continue


def run_virtual_mode(args: argparse.Namespace) -> int:
    if not args.cli:
        args.mode_parser.print_help()
        return 0
    from app.cli import main

    return _interactive_loop(
        "virtual",
        VIRTUAL_HELP,
        lambda parts: main(["virtual", *parts]),
    )


def register_virtual_mode(
    commands: argparse._SubParsersAction,
    register_commands: Callable[[argparse._SubParsersAction], None],
) -> None:
    mode = commands.add_parser(
        "virtual",
        help="Inventario lógico, red, dispositivos y protocolos.",
    )
    mode.add_argument(
        "--cli",
        action="store_true",
        help="Abre la CLI virtual interactiva.",
    )
    nested = mode.add_subparsers(dest="virtual_command", metavar="COMANDO")
    register_commands(nested)
    mode.set_defaults(handler=run_virtual_mode, mode_parser=mode)
