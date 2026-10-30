from __future__ import annotations

import argparse
import json

from lanctl.apps.ip.domain.models import normalize_protocol
from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.credentials import CredentialStore
from lanctl.core.database import DeviceDatabase
from lanctl.core.secret_input import read_secret
from lanctl.shared.i18n import t


def register_credential_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "credential",
        aliases=["credentials", "auth"],
        help=t("LANCTL.UI.HELP.ASSOCIATE_ENCRYPTED_CREDENTIALS_WITH_AN_ELEMENT_AND_PROTOCOL"),
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.ELEMENT_IP_MAC_OR_ALIAS"))
    command.add_argument(
        "action",
        nargs="?",
        choices=("set", "list", "delete"),
        help=t("LANCTL.UI.HELP.CREDENTIAL_OPERATION"),
    )
    command.add_argument(
        "protocol", nargs="?", help=t("LANCTL.UI.HELP.PROTOCOL_FOR_EXAMPLE_TR_064")
    )
    command.add_argument(
        "-user", "--username", dest="username", help=t("LANCTL.UI.HELP.REMOTE_USERNAME")
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.add_argument(
        "--store",
        default=config["credentials"],
        help=t("LANCTL.UI.TEXT.ENCRYPTED_CREDENTIAL_STORE"),
    )
    command.set_defaults(handler=run_credential)


def run_credential(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    if args.selector.casefold() == "list" and args.action is None:
        store = CredentialStore(args.store)
        rows = []
        for device in database.load():
            for protocol, reference in device.credentials.items():
                credential = store.get(reference)
                rows.append(
                    {
                        "element": device.alias or device.name or device.ip or device.mac,
                        "ip": device.ip,
                        "protocol": protocol,
                        "credentialId": reference,
                        "username": credential["username"],
                    }
                )
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    if args.action is None:
        raise ValueError("indica una operación: set, list o delete")
    device = database.resolve(args.selector)
    store = CredentialStore(args.store)

    if args.action == "list":
        rows = [
            {
                "protocol": protocol,
                "credentialId": reference,
                "username": store.get(reference)["username"],
            }
            for protocol, reference in device.credentials.items()
        ]
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0

    if not args.protocol:
        raise ValueError(f"falta el protocolo para credential {args.action}")
    protocol = normalize_protocol(args.protocol)

    if args.action == "set":
        if not args.username:
            raise ValueError("indica el usuario con -user USUARIO")
        password = read_secret(t("LANCTL.UI.PROMPT.PASSWORD_NOT_DISPLAYED"))
        if not password:
            raise ValueError("la contraseña no puede estar vacía")
        confirmation = read_secret(t("LANCTL.UI.PROMPT.REPEAT_PASSWORD"))
        if password != confirmation:
            raise ValueError("las contraseñas no coinciden")
        credential_id = store.set(device.device_id, protocol, args.username, password)
        updated = database.bind_credential(args.selector, protocol, credential_id)
        ok(
            t("LANCTL.UI.STATUS.CREDENTIAL"),
            f"{updated.alias or updated.ip} | {protocol} -> {credential_id}",
        )
        return 0

    reference = device.credentials.get(protocol)
    if not reference:
        raise ValueError(f"{device.alias or device.ip} no tiene credencial para {protocol}")
    store.delete(reference)
    database.unbind_credential(args.selector, protocol)
    ok(t("LANCTL.UI.STATUS.DELETED"), f"{device.alias or device.ip} | {protocol}")
    return 0
