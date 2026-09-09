"""Gestor CLI/TUI de credenciales locales y de dispositivos."""

from __future__ import annotations

import json
import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.apps.ip.domain.models import normalize_protocol
from lanctl.core.config import load_config
from lanctl.core.credentials import CredentialStore
from lanctl.core.database import DeviceDatabase
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments
from lanctl.core.secret_input import read_secret


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> LANCTLArgumentParser:
    config = load_config()
    parser = LANCTLArgumentParser(
        prog="LANACCESS", description="Gestiona credenciales cifradas del entorno LANCTL."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión común de la suite y termina.",
    )
    parser.add_argument("--database", default=config["database"], help="Base de elementos LANCTL.")
    parser.add_argument(
        "--store", default=config["credentials"], help="Almacén cifrado de credenciales."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-tui", "--tui", action="store_true", help="Abre la interfaz de pantalla completa."
    )
    mode.add_argument("--cli", action="store_true", help="Abre la consola interactiva.")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("list", aliases=["ls"], help="Lista metadatos; nunca secretos.")
    show = commands.add_parser("show", help="Muestra metadatos de una credencial.")
    show.add_argument("credential_id", help="Identificador de la credencial.")
    set_command = commands.add_parser("set", help="Crea o actualiza una credencial.")
    set_command.add_argument("element", help="IP, MAC, alias o ID del dispositivo.")
    set_command.add_argument("protocol", help="Protocolo asociado, por ejemplo ssh.")
    set_command.add_argument("--username", "-user", required=True, help="Usuario remoto.")
    delete = commands.add_parser("delete", aliases=["del"], help="Elimina una credencial.")
    delete.add_argument("credential_id", help="Identificador de la credencial.")
    return parser


class AccessManager:
    def __init__(self, database_path: str, store_path: str) -> None:
        self.database = DeviceDatabase(database_path)
        self.store = CredentialStore(store_path)

    def list(self) -> list[dict[str, str]]:
        devices = {device.device_id: device for device in self.database.load()}
        rows = self.store.metadata()
        for row in rows:
            device = devices.get(row["deviceId"])
            row["element"] = (
                device.alias or device.name or device.ip or device.mac
                if device
                else row["deviceId"]
            )
        return rows

    def set(self, selector: str, protocol: str, username: str) -> str:
        device = self.database.resolve(selector)
        normalized = normalize_protocol(protocol)
        password = read_secret("Contraseña (no se mostrará): ")
        confirmation = read_secret("Repite la contraseña: ")
        if not password:
            raise ValueError("la contraseña no puede estar vacía")
        if password != confirmation:
            raise ValueError("las contraseñas no coinciden")
        identifier = self.store.set(device.device_id, normalized, username, password)
        self.database.bind_credential(selector, normalized, identifier)
        return identifier

    def delete(self, identifier: str) -> bool:
        metadata = next(
            (row for row in self.store.metadata() if row["credentialId"] == identifier), None
        )
        if metadata is None:
            return False
        for device in self.database.load():
            for protocol, reference in tuple(device.credentials.items()):
                if reference == identifier:
                    self.database.unbind_credential(device.device_id, protocol)
        return self.store.delete(identifier)


def _print_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No hay credenciales guardadas.")
        return
    print(f"{'ID':<30} {'ELEMENTO':<24} {'PROTOCOLO':<12} USUARIO")
    for row in rows:
        print(
            f"{row['credentialId']:<30} {row.get('element', row['deviceId'])[:24]:<24} "
            f"{row['protocol']:<12} {row['username']}"
        )


def run_tui(manager: AccessManager) -> int:
    # El primer borrado prepara la pantalla. Después se repinta desde el origen
    # y se limpia sólo la cola sobrante, sin mostrar una pantalla vacía entre
    # frames.
    print("\x1b[2J\x1b[H", end="")
    while True:
        print("\x1b[H", end="")
        print(f"LANACCESS TUI {__version__}\n")
        _print_rows(manager.list())
        print("\n[L] refrescar  [A] añadir  [E] eliminar  [Q] salir\x1b[J")
        try:
            action = input("Opción: ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            return 0
        if action in {"q", "quit", "exit"}:
            return 0
        try:
            if action in {"a", "add", "set"}:
                selector = input("Elemento: ").strip()
                protocol = input("Protocolo: ").strip()
                username = input("Usuario: ").strip()
                print(f"Guardada: {manager.set(selector, protocol, username)}")
                input("Pulsa Intro para continuar…")
            elif action in {"e", "delete", "del"}:
                identifier = input("ID de credencial: ").strip()
                print("Eliminada." if manager.delete(identifier) else "No encontrada.")
                input("Pulsa Intro para continuar…")
        except (OSError, ValueError) as error:
            print(f"Error: {error}")
            input("Pulsa Intro para continuar…")


def run_cli(manager: AccessManager) -> int:
    print(f"LANACCESS CLI {__version__} | list, show ID, delete ID, exit")
    while True:
        try:
            parts = input("LANACCESS> ").strip().split()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not parts:
            continue
        if parts[0].casefold() in {"exit", "quit"}:
            return 0
        if parts[0].casefold() in {"list", "ls"}:
            _print_rows(manager.list())
        elif parts[0].casefold() == "show" and len(parts) == 2:
            print(
                json.dumps(
                    next((r for r in manager.list() if r["credentialId"] == parts[1]), {}),
                    indent=2,
                    ensure_ascii=False,
                )
            )
        elif parts[0].casefold() in {"delete", "del"} and len(parts) == 2:
            print("Eliminada." if manager.delete(parts[1]) else "No encontrada.")
        else:
            print("Usa: list | show ID | delete ID | exit; para altas usa `lanaccess set`. ")


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    args = build_parser().parse_args(arguments)
    manager = AccessManager(args.database, args.store)
    if args.tui or (not args.cli and args.command is None):
        return run_tui(manager)
    if args.cli:
        return run_cli(manager)
    if args.command in {"list", "ls"}:
        _print_rows(manager.list())
        return 0
    if args.command == "show":
        row = next((r for r in manager.list() if r["credentialId"] == args.credential_id), None)
        if row is None:
            raise ValueError(f"credencial no encontrada: {args.credential_id}")
        print(json.dumps(row, indent=2, ensure_ascii=False))
        return 0
    if args.command == "set":
        print(f"Guardada: {manager.set(args.element, args.protocol, args.username)}")
        return 0
    if args.command in {"delete", "del"}:
        if not manager.delete(args.credential_id):
            raise ValueError(f"credencial no encontrada: {args.credential_id}")
        print("Eliminada.")
        return 0
    return run_cli(manager)
