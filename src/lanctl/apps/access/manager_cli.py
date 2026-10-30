"""Gestor CLI/TUI de credenciales locales y de dispositivos."""

from __future__ import annotations

import json
import sys
from contextlib import suppress
from pathlib import Path

from lanctl import __version__
from lanctl.apps.access.credential_service import CredentialService
from lanctl.apps.ip.domain.models import normalize_protocol
from lanctl.core.config import load_config
from lanctl.core.credentials import CredentialStore
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments
from lanctl.core.secret_input import read_secret
from lanctl.core.session import coordinated_launcher
from lanctl.shared.i18n import initialize_language, t


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> LANCTLArgumentParser:
    config = load_config()
    parser = LANCTLArgumentParser(
        prog="LANACCESS",
        description=t("LANCTL.UI.TEXT.MANAGE_ENCRYPTED_CREDENTIALS_IN_THE_LANCTL_ENVIRONMENT"),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help=t("LANCTL.UI.TEXT.SHOW_THE_COMMON_SUITE_VERSION_AND_EXIT"),
    )
    parser.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.TEXT.LANCTL_ELEMENT_DATABASE")
    )
    parser.add_argument(
        "--store",
        default=config["credentials"],
        help=t("LANCTL.UI.TEXT.ENCRYPTED_CREDENTIAL_STORE"),
    )
    parser.add_argument(
        "--cipher",
        choices=("auto", "dpapi", "portable"),
        default="auto",
        help=t("LANCTL.UI.TEXT.ENCRYPTION_PROVIDER_PORTABLE_PROMPTS_FOR_A_PASSWORD"),
    )
    parser.add_argument(
        "--scope",
        choices=("program", "windows", "project"),
        default="program",
        help=t("LANCTL.UI.TEXT.LOCATION_DOES_NOT_CHANGE_PERMISSIONS_OR_COPY_SECRETS_AUTOMATICALLY"),
    )
    parser.add_argument(
        "--project-dir", help=t("LANCTL.UI.TEXT.PROJECT_DIRECTORY_FOR_ITS_INDEPENDENT_STORE")
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--gui", action="store_true", help=t("LANCTL.UI.TEXT.OPEN_THE_DESKTOP_GRAPHICAL_INTERFACE")
    )
    mode.add_argument(
        "-tui",
        "--tui",
        action="store_true",
        help=t("LANCTL.UI.TEXT.OPEN_THE_FULL_SCREEN_INTERFACE"),
    )
    mode.add_argument(
        "--cli", "-cli", action="store_true", help=t("LANCTL.UI.TEXT.OPEN_THE_INTERACTIVE_CONSOLE")
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser(
        "remote-setup",
        help=t(
            "LANCTL.UI.TEXT.CREATE_THE_FIRST_REMOTE_SERVICE_ACCOUNT_ON_WINDOWS_ADMINISTRATOR_REQUIRED"
        ),
    )
    commands.add_parser(
        "list", aliases=["ls"], help=t("LANCTL.UI.TEXT.LIST_METADATA_NEVER_SECRETS")
    )
    show = commands.add_parser("show", help=t("LANCTL.UI.TEXT.SHOW_CREDENTIAL_METADATA"))
    show.add_argument("credential_id", help=t("LANCTL.UI.TEXT.CREDENTIAL_IDENTIFIER"))
    set_command = commands.add_parser("set", help=t("LANCTL.UI.TEXT.CREATE_OR_UPDATE_A_CREDENTIAL"))
    set_command.add_argument("element", help=t("LANCTL.UI.TEXT.DEVICE_IP_MAC_ALIAS_OR_ID"))
    set_command.add_argument(
        "protocol", help=t("LANCTL.UI.TEXT.ASSOCIATED_PROTOCOL_FOR_EXAMPLE_SSH")
    )
    set_command.add_argument(
        "--username", "-user", required=True, help=t("LANCTL.UI.TEXT.REMOTE_USERNAME")
    )
    delete = commands.add_parser(
        "delete", aliases=["del"], help=t("LANCTL.UI.TEXT.DELETE_A_CREDENTIAL")
    )
    delete.add_argument("credential_id", help=t("LANCTL.UI.TEXT.CREDENTIAL_IDENTIFIER"))
    credential = commands.add_parser(
        "credential", help=t("LANCTL.UI.TEXT.CREDENTIAL_MANAGEMENT_TRANSPORT_AND_RECOVERY")
    )
    actions = credential.add_subparsers(dest="credential_action", required=True)
    actions.add_parser("list", help=t("LANCTL.UI.TEXT.LIST_METADATA"))
    for action in ("show", "delete"):
        child = actions.add_parser(
            action, help=t("LANCTL.ACCESS.CREDENTIAL.ACTION_HELP", action=action)
        )
        child.add_argument("credential_id")
    child = actions.add_parser("set", help=t("LANCTL.UI.TEXT.SAVE_AND_LINK_A_CREDENTIAL"))
    child.add_argument("element")
    child.add_argument("protocol")
    child.add_argument("--username", required=True)
    for action in ("export", "import"):
        child = actions.add_parser(
            action, help=t("LANCTL.UI.TEXT.TRANSPORT_AN_ENCRYPTED_STORE_NEVER_PLAINTEXT")
        )
        child.add_argument("file")
    child = actions.add_parser(
        "copy", help=t("LANCTL.UI.TEXT.COPY_TO_ANOTHER_STORE_AND_VERIFY_PRESERVE_THE_SOURCE")
    )
    child.add_argument("file")
    child.add_argument("--target-cipher", choices=("dpapi", "portable"), default="portable")
    child = actions.add_parser(
        "recover",
        help=t("LANCTL.UI.TEXT.REPAIR_MISSING_REFERENCES_DO_NOT_DELETE_OR_OVERWRITE_SECRETS"),
    )
    child.add_argument(
        "--yes",
        action="store_true",
        help=t("LANCTL.UI.TEXT.APPLY_REPAIRS_DIAGNOSE_ONLY_BY_DEFAULT"),
    )
    commands.add_parser(
        "doctor", help=t("LANCTL.UI.TEXT.CHECK_LINKS_AND_PERMISSIONS_WITHOUT_CHANGING_DATA")
    )
    settings = commands.add_parser(
        "settings", help=t("LANCTL.UI.TEXT.SHOW_OR_SELECT_THE_SHARED_STORE")
    )
    settings.add_argument("action", choices=("show", "use-store"), nargs="?", default="show")
    settings.add_argument("file", nargs="?")
    settings.add_argument(
        "--yes",
        action="store_true",
        help=t("LANCTL.UI.TEXT.CONFIRM_CHANGING_THE_CONFIGURED_STORE_WITHOUT_MOVING_SECRETS"),
    )
    protocol = commands.add_parser("protocol", help=t("LANCTL.UI.TEXT.STORE_PROTOCOL_SUMMARY"))
    protocol.add_argument("action", choices=("list", "configure"), default="list", nargs="?")
    protocol.add_argument("element", nargs="?")
    protocol.add_argument("protocol", nargs="?")
    protocol.add_argument("--port", type=int, help=t("LANCTL.UI.TEXT.PORT_1_65535"))
    protocol.add_argument("--driver", help=t("LANCTL.UI.TEXT.PROTOCOL_DRIVER"))
    user = commands.add_parser(
        "user", help=t("LANCTL.UI.TEXT.REMOTE_ACCESS_USERS_NOT_WINDOWS_ACCOUNTS")
    )
    user.add_argument("action", choices=("list", "add", "enable", "disable", "delete"))
    user.add_argument("username", nargs="?")
    user.add_argument(
        "--role", choices=("viewer", "operator", "manager", "administrator"), default="viewer"
    )
    user.add_argument("--yes", action="store_true", help=t("LANCTL.UI.TEXT.CONFIRM_DELETION"))
    return parser


class AccessManager(CredentialService):
    """Compatible CLI adapter: obtain secrets interactively, then call the service."""

    def set(self, selector: str, protocol: str, username: str) -> str:
        password = read_secret(t("LANCTL.UI.PROMPT.PASSWORD_NOT_DISPLAYED"))
        confirmation = read_secret(t("LANCTL.UI.PROMPT.REPEAT_PASSWORD"))
        if not password:
            raise ValueError("la contraseña no puede estar vacía")
        if password != confirmation:
            raise ValueError("las contraseñas no coinciden")
        return self.set_secret(selector, protocol, username, password)


def _print_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        print(t("LANCTL.UI.PROMPT.NO_SAVED_CREDENTIALS"))
        return
    print(
        t(
            "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUE_USERNAME",
            value0=f"{'ID':<30}",
            value1=f"{'ELEMENTO':<24}",
            value2=f"{'PROTOCOLO':<12}",
        )
    )
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
        table = Table(
            title=t("LANCTL.UI.DETAIL.LANACCESS_VALUE_CREDENTIALS", value0=f"{__version__}"),
            expand=True,
        )
        for heading in (
            "ID",
            t("LANCTL.UI.TEXT.ELEMENT"),
            t("LANCTL.UI.TEXT.PROTOCOL"),
            t("LANCTL.UI.TEXT.USERNAME"),
        ):
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
                    t(
                        "LANCTL.UI.MESSAGE.PAGE_VALUE_VALUE_N_B_PAGES_L_REFRESH_A_ADD_E_DELETE_C_COMMAND_D_DIAGNOSTICS_Q_QUIT",
                        value0=f"{page + 1}",
                        value1=f"{pages}",
                    )
                ),
                Text(
                    "credential export/import ARCHIVO · credential recover · protocol list · user list · settings"
                ),
            )
        )
        try:
            action = input(t("LANCTL.UI.PROMPT.OPTION")).strip().casefold()
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
                input(t("LANCTL.UI.PROMPT.PRESS_ENTER_TO_CONTINUE"))
            elif action == "c":
                _interactive_command(manager, input(t("LANCTL.UI.PRESENTATION.ACCESS_COMMAND")))
                input(t("LANCTL.UI.PROMPT.PRESS_ENTER_TO_CONTINUE"))
            elif action in {"a", "add", "set"}:
                selector = input(t("LANCTL.UI.PRESENTATION.ELEMENT")).strip()
                protocol = input(t("LANCTL.UI.PRESENTATION.PROTOCOL")).strip()
                username = input(t("LANCTL.UI.PRESENTATION.USER")).strip()
                print(
                    t(
                        "LANCTL.UI.DETAIL.SAVED_VALUE",
                        value0=f"{manager.set(selector, protocol, username)}",
                    )
                )
                input(t("LANCTL.UI.PROMPT.PRESS_ENTER_TO_CONTINUE"))
            elif action in {"e", "delete", "del"}:
                identifier = input(t("LANCTL.UI.PRESENTATION.CREDENTIAL_ID")).strip()
                print(
                    t("LANCTL.UI.PRESENTATION.DELETED")
                    if manager.delete(identifier)
                    else t("LANCTL.UI.PROMPT.NOT_FOUND")
                )
                input(t("LANCTL.UI.PROMPT.PRESS_ENTER_TO_CONTINUE"))
        except (OSError, ValueError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error, origin="LANCTL.Access.TUI.Action", code="ACCESS.TUI.ACTION_FAILED", level=42
            )
            input(t("LANCTL.UI.PROMPT.PRESS_ENTER_TO_CONTINUE"))


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
            print(t("LANCTL.UI.PROMPT.INVALID_COMMAND_SEE_HELP"))


def _main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    parser = build_parser()
    default_database = parser.get_default("database")
    default_store = parser.get_default("store")
    parser.set_defaults(database=None, store=None)
    args = parser.parse_args(arguments)
    if args.command == "remote-setup":
        from lanctl.apps.access.remote_setup import run_remote_setup

        return run_remote_setup()
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
    if getattr(args, "gui", False):
        from lanctl.apps.suite.launcher_gui import run_gui

        return run_gui("lanaccess", database=args.database, store=args.store, cipher=args.cipher)
    if args.database is None:
        args.database = default_database
    if args.store is None:
        args.store = default_store
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
        print(
            t(
                "LANCTL.UI.DETAIL.SAVED_VALUE",
                value0=f"{manager.set(args.element, args.protocol, args.username)}",
            )
        )
        return 0
    if args.command in {"delete", "del"}:
        if not manager.delete(args.credential_id):
            raise ValueError(f"credencial no encontrada: {args.credential_id}")
        print(t("LANCTL.UI.PRESENTATION.DELETED"))
        return 0
    return run_cli(manager)


@coordinated_launcher("lanaccess")
def main(argv: list[str] | None = None) -> int:
    initialize_language()
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
            password = read_secret(
                t("LANCTL.UI.PROMPT.DESTINATION_PASSWORD_AT_LEAST_12_CHARACTERS")
            )
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
        password = read_secret(t("LANCTL.UI.PROMPT.REMOTE_USER_PASSWORD"))
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
