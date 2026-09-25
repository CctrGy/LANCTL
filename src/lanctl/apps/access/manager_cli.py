"""Gestor CLI/TUI de credenciales locales y de dispositivos."""

from __future__ import annotations

import json
import sys
from contextlib import suppress
from pathlib import Path

from lanctl import __version__
from lanctl.apps.ip.domain.models import normalize_protocol
from lanctl.core.config import load_config
from lanctl.core.credentials import CredentialStore
from lanctl.core.database import DeviceDatabase
from lanctl.core.file_transaction import locked_files
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
    parser.add_argument(
        "--cipher",
        choices=("auto", "dpapi", "portable"),
        default="auto",
        help="Proveedor de cifrado; portable pide contraseña.",
    )
    parser.add_argument(
        "--scope",
        choices=("program", "windows", "project"),
        default="program",
        help="Ubicación; no cambia permisos ni copia secretos automáticamente.",
    )
    parser.add_argument(
        "--project-dir", help="Directorio del proyecto para su almacén independiente."
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
    credential = commands.add_parser(
        "credential", help="Gestión, transporte y recuperación de credenciales."
    )
    actions = credential.add_subparsers(dest="credential_action", required=True)
    actions.add_parser("list", help="Lista metadatos.")
    for action in ("show", "delete"):
        child = actions.add_parser(action, help=f"{action} por identificador.")
        child.add_argument("credential_id")
    child = actions.add_parser("set", help="Guarda y vincula una credencial.")
    child.add_argument("element")
    child.add_argument("protocol")
    child.add_argument("--username", required=True)
    for action in ("export", "import"):
        child = actions.add_parser(action, help="Transporta un almacén cifrado; nunca texto plano.")
        child.add_argument("file")
    child = actions.add_parser("copy", help="Copia a otro almacén y verifica; origen conservado.")
    child.add_argument("file")
    child.add_argument("--target-cipher", choices=("dpapi", "portable"), default="portable")
    child = actions.add_parser(
        "recover", help="Repara referencias ausentes; no elimina ni sobrescribe secretos."
    )
    child.add_argument(
        "--yes", action="store_true", help="Aplica reparaciones; por defecto sólo diagnostica."
    )
    commands.add_parser("doctor", help="Comprueba vínculos y permisos sin cambiar datos.")
    settings = commands.add_parser("settings", help="Muestra o selecciona el almacén compartido.")
    settings.add_argument("action", choices=("show", "use-store"), nargs="?", default="show")
    settings.add_argument("file", nargs="?")
    settings.add_argument(
        "--yes",
        action="store_true",
        help="Confirma cambiar el almacén configurado sin mover secretos.",
    )
    protocol = commands.add_parser("protocol", help="Resumen por protocolos del almacén.")
    protocol.add_argument("action", choices=("list", "configure"), default="list", nargs="?")
    protocol.add_argument("element", nargs="?")
    protocol.add_argument("protocol", nargs="?")
    protocol.add_argument("--port", type=int, help="Puerto 1-65535.")
    protocol.add_argument("--driver", help="Driver del protocolo.")
    user = commands.add_parser("user", help="Usuarios del acceso remoto; no cuentas de Windows.")
    user.add_argument("action", choices=("list", "add", "enable", "disable", "delete"))
    user.add_argument("username", nargs="?")
    user.add_argument(
        "--role", choices=("viewer", "operator", "manager", "administrator"), default="viewer"
    )
    user.add_argument("--yes", action="store_true", help="Confirma eliminación.")
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
        with locked_files([self.store.path, self.database.path]):
            previous = self.store._load()
            identifier = self.store.set(device.device_id, normalized, username, password)
            try:
                self.database.bind_credential(selector, normalized, identifier)
            except (OSError, ValueError):
                self.store._save(previous)
                raise
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
    from lanctl.core.terminal_ui import ManagementScreen

    with ManagementScreen() as screen:
        return _tui_loop(manager, screen)


def _tui_loop(manager, screen):
    import shutil

    from rich.console import Group
    from rich.table import Table
    from rich.text import Text

    page = 0
    while True:
        rows = manager.list()
        size = max(1, shutil.get_terminal_size((100, 30)).lines - 11)
        pages = max(1, (len(rows) + size - 1) // size)
        page = min(page, pages - 1)
        table = Table(title=f"LANACCESS {__version__} · Credenciales", expand=True)
        for heading in ("ID", "Elemento", "Protocolo", "Usuario"):
            table.add_column(heading, no_wrap=True)
        for row in rows[page * size : (page + 1) * size]:
            table.add_row(
                *(
                    Text(row.get(key, ""))
                    for key in ("credentialId", "element", "protocol", "username")
                )
            )
        screen.draw(
            Group(
                table,
                Text(
                    f"Página {page + 1}/{pages} · N/B páginas | L Refrescar | A Añadir | E Eliminar | C Comando | D Diagnóstico | Q Salir"
                ),
                Text(
                    "credential export/import ARCHIVO · credential recover · protocol list · user list · settings"
                ),
            )
        )
        try:
            action = input("Opción: ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            return 0
        if action in {"q", "quit", "exit"}:
            return 0
        if action in {"n", "b"}:
            page = max(0, min(pages - 1, page + (1 if action == "n" else -1)))
            continue
        try:
            if action == "d":
                from lanctl.apps.access.vault_service import audit_bindings

                print(json.dumps(audit_bindings(manager), indent=2))
                input("Pulsa Intro para continuar…")
            elif action == "c":
                _interactive_command(manager, input("Comando LANACCESS: "))
                input("Pulsa Intro para continuar…")
            elif action in {"a", "add", "set"}:
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
            from lanctl.core.errors import errors

            errors.from_exception(
                error, origin="LANCTL.Access.TUI.Action", code="ACCESS.TUI.ACTION_FAILED", level=42
            )
            input("Pulsa Intro para continuar…")


def run_cli(manager: AccessManager) -> int:
    print(f"LANACCESS CLI {__version__} | list, credential, protocol, user, settings, doctor, exit")
    while True:
        try:
            command = input("LANACCESS> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not command:
            continue
        if command.casefold() in {"exit", "quit"}:
            return 0
        _interactive_command(manager, command)


def _interactive_command(manager, command):
    from lanctl.core.command_line import split_command_line

    try:
        words = split_command_line(command)
    except ValueError as exc:
        from lanctl.core.errors import errors

        errors.from_exception(
            exc, origin="LANCTL.Access.CLI.Input", code="ACCESS.INPUT.INVALID", level=31
        )
        return
    if not words or words[0] in {"--cli", "--tui", "-tui"}:
        return
    try:
        main(
            [
                "--database",
                str(manager.database.path),
                "--store",
                str(manager.store.path),
                "--cipher",
                manager.store.cipher,
                *words,
            ]
        )
    except SystemExit as exc:
        if exc.code:
            print("Comando no válido; consulta --help")


def _main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    args = build_parser().parse_args(arguments)
    if args.scope == "windows":
        import os

        if os.name != "nt":
            raise ValueError("el ámbito windows sólo está disponible en Windows")
        args.store = str(
            Path(os.environ["LOCALAPPDATA"]) / "LANCTL" / "access" / "device-credentials.dat"
        )
    elif args.scope == "project":
        if not args.project_dir:
            raise ValueError(
                "--scope project requiere --project-dir; nunca se deduce otro proyecto"
            )
        args.store = str(Path(args.project_dir).resolve() / "access" / "credentials.vault")
        if args.cipher == "auto" and not Path(args.store).exists():
            args.cipher = "portable"
    manager = AccessManager(args.database, args.store)
    manager.store.cipher = args.cipher
    if args.command == "credential":
        args.command = args.credential_action
    if args.command in {
        "export",
        "import",
        "copy",
        "recover",
        "doctor",
        "settings",
        "protocol",
        "user",
    }:
        return _extended_command(manager, args)
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


def main(argv: list[str] | None = None) -> int:
    from lanctl.core.errors import errors

    try:
        return _main(argv)
    except (OSError, ValueError) as exc:
        errors.from_exception(
            exc, origin="LANCTL.Access.CLI.Command", code="ACCESS.COMMAND.FAILED", level=42
        )
        return 2


def _extended_command(manager, args):
    from lanctl.apps.access.vault_service import audit_bindings, transfer
    from lanctl.core.local_permissions import status

    if args.command in {"export", "copy"}:
        cipher = getattr(args, "target_cipher", "portable")
        password = None
        if cipher == "portable":
            password = read_secret("Contraseña del destino (mínimo 12 caracteres): ")
            if password != read_secret("Repite la contraseña del destino: "):
                raise ValueError("las contraseñas no coinciden")
        target = CredentialStore(args.file, cipher=cipher, password=password)
        payload = {"copied": transfer(manager.store, target), "sourcePreserved": True}
        from lanctl.apps.access.audit import completed

        completed(args.command, payload["copied"])
    elif args.command == "import":
        source = CredentialStore(args.file, cipher="portable")
        payload = {
            "imported": transfer(source, manager.store),
            "next": "credential recover --yes para vincular IDs coincidentes",
        }
        from lanctl.apps.access.audit import completed

        completed("import", payload["imported"])
    elif args.command in {"doctor", "recover"}:
        payload = audit_bindings(manager, repair=getattr(args, "yes", False))
    elif args.command == "settings":
        if args.action == "use-store":
            from lanctl.core.config import update_config

            if not args.file or not args.yes:
                raise ValueError(
                    "usa settings use-store ARCHIVO --yes; valida y selecciona, sin mover datos"
                )
            target = CredentialStore(args.file)
            if not target.path.is_file():
                raise ValueError("el almacén debe existir antes de seleccionarlo")
            target.metadata()

            def select_store(config):
                config["credentials"] = str(target.path.resolve())

            update_config(select_store)
            manager.store = target
        payload = {
            "store": str(manager.store.path),
            "cipher": manager.store.cipher,
            "scope": args.scope,
            **status(),
        }
    elif args.command == "protocol":
        if args.action == "configure":
            if not args.element or not args.protocol:
                raise ValueError(
                    "usa protocol configure ELEMENTO PROTOCOLO --port N --driver DRIVER"
                )
            if args.port is not None and not 1 <= args.port <= 65535:
                raise ValueError("puerto fuera del intervalo 1-65535")
            device = manager.database.resolve(args.element)
            protocol = normalize_protocol(args.protocol)
            options = dict(device.protocol_options.get(protocol, {}))
            if args.port is not None:
                options["port"] = args.port
            if args.driver:
                options["driver"] = args.driver
            manager.database.configure_protocol(args.element, protocol, options)
            payload = {"protocol": protocol, "options": options}
        else:
            rows = manager.list()
            payload = [
                {
                    "protocol": protocol,
                    "credentials": sum(row["protocol"] == protocol for row in rows),
                }
                for protocol in sorted({row["protocol"] for row in rows})
            ]
    else:
        payload = _user_command(args)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _user_command(args):
    from lanctl.apps.access.auth import AuthenticationService
    from lanctl.apps.access.store import AccessStore
    from lanctl.core.local_permissions import require_admin
    from lanctl.core.paths import application_path

    # Remote user administration is privileged; an application role cannot grant OS access.
    require_admin()
    store = AccessStore(application_path(load_config()["accessUsers"]))
    auth = AuthenticationService(store)
    if args.action == "list":
        return [
            {"username": user.username, "roles": user.roles, "enabled": user.enabled}
            for user in store.users()
        ]
    if not args.username:
        raise ValueError("indica el usuario remoto")
    if args.action == "add":
        password = read_secret("Contraseña del usuario remoto: ")
        if password != read_secret("Repite la contraseña: "):
            raise ValueError("las contraseñas no coinciden")
        auth.add_user(args.username, roles=(args.role,), password=password)
    else:
        user = auth.user(args.username)
        if args.action == "delete":
            if not args.yes:
                raise ValueError("eliminar usuario requiere --yes")
            store.delete_user(user.userId)
        else:

            def change(current):
                current.enabled = args.action == "enable"
                return current

            store.update_user(user.userId, change)
    return {"status": "completed", "action": args.action, "username": args.username}
