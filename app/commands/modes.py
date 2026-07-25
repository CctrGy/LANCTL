from __future__ import annotations

import argparse
import shlex
from collections.abc import Callable

from colorama import Fore, Style

from app.core.parser import colorize_help


VIRTUAL_HELP = """CLI virtual de LANCTL

Gestiona la representación lógica de la LAN: elementos, IP, MAC, nombres,
grupos, escaneos, protocolos, terminales y control gestionado.

Escribe un comando sin el prefijo `run virtual`, por ejemplo:
  list
  scan ESP
  element GATEWAY
  switch SW --dry-run show version
  help
  exit
"""


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
