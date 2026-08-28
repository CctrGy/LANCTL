"""Lanzador del gestor de infraestructura física LANWIRE."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from lanctl.core.paths import application_directory, data_root


def register_lanwire_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "lanwire",
        aliases=["wire"],
        help="Abre LANWIRE o ejecuta uno de sus comandos sobre la base física compartida.",
    )
    command.add_argument(
        "--new-window",
        action="store_true",
        help="Abre LANWIRE en una consola independiente incluso si se indican argumentos.",
    )
    command.add_argument(
        "--version",
        dest="lanwire_version",
        action="store_true",
        help="Muestra la versión común de LANWIRE y termina.",
    )
    command.add_argument(
        "--database",
        dest="lanwire_database",
        metavar="ARCHIVO.db",
        help="Selecciona una base física IDF alternativa.",
    )
    mode = command.add_mutually_exclusive_group()
    mode.add_argument(
        "-tui",
        "--tui",
        dest="lanwire_tui",
        action="store_true",
        help="Abre la interfaz TUI de LANWIRE.",
    )
    mode.add_argument(
        "--cli",
        dest="lanwire_cli",
        action="store_true",
        help="Abre la consola interactiva de LANWIRE.",
    )
    command.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        metavar="ARGUMENTO",
        help="Argumentos enviados a LANWIRE, por ejemplo: list.",
    )
    command.set_defaults(handler=run_lanwire)


def lanwire_command(arguments: list[str] | None = None) -> list[str]:
    """Resuelve la segunda entrada de la suite junto a LANCTL o en sus fuentes."""

    values = list(arguments or [])
    if getattr(sys, "frozen", False):
        executable = application_directory() / "lanwire.exe"
        if not executable.is_file():
            raise FileNotFoundError(f"LANWIRE no está instalado junto a LANCTL: {executable}")
        return [str(executable), *values]

    entrypoint = application_directory() / "lanwire.py"
    if not entrypoint.is_file():
        raise FileNotFoundError(f"no se encontró la entrada raíz de LANWIRE: {entrypoint}")
    return [sys.executable, str(entrypoint), *values]


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["LANCTL_DATA_DIR"] = str(data_root())
    return environment


def run_lanwire(args: argparse.Namespace) -> int:
    forwarded: list[str] = []
    if getattr(args, "lanwire_version", False):
        forwarded.append("--version")
    if getattr(args, "lanwire_database", None):
        forwarded.extend(("--database", args.lanwire_database))
    if getattr(args, "lanwire_tui", False):
        forwarded.append("--tui")
    if getattr(args, "lanwire_cli", False):
        forwarded.append("--cli")
    forwarded.extend(args.arguments)
    command = lanwire_command(forwarded)
    environment = _environment()
    new_window = bool(args.new_window or not forwarded)
    if new_window:
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
        subprocess.Popen(command, env=environment, creationflags=flags)
        print(f"LANWIRE iniciado | datos: {environment['LANCTL_DATA_DIR']}")
        return 0
    return subprocess.run(command, env=environment, check=False).returncode
