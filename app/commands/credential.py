from __future__ import annotations

import argparse
import getpass
import json

from app.core.config import load_config
from app.core.console import ok
from app.core.credentials import CredentialStore
from app.core.database import DeviceDatabase
from app.models import normalize_protocol


def register_credential_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "credential",
        aliases=["credentials", "auth"],
        help="Asocia credenciales cifradas a un elemento y protocolo.",
    )
    command.add_argument("selector", help="IP, MAC o alias del elemento.")
    command.add_argument("action", choices=("set", "list", "delete"), help="Operación sobre la credencial.")
    command.add_argument("protocol", nargs="?", help="Protocolo, por ejemplo tr-064.")
    command.add_argument("-user", "--username", dest="username", help="Nombre de usuario remoto.")
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.add_argument("--store", default=config["credentials"], help="Almacén cifrado de credenciales.")
    command.set_defaults(handler=run_credential)


def run_credential(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
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
        password = getpass.getpass("Contraseña (no se mostrará): ")
        if not password:
            raise ValueError("la contraseña no puede estar vacía")
        confirmation = getpass.getpass("Repite la contraseña: ")
        if password != confirmation:
            raise ValueError("las contraseñas no coinciden")
        credential_id = store.set(
            device.device_id, protocol, args.username, password
        )
        updated = database.bind_credential(args.selector, protocol, credential_id)
        ok(
            "CREDENCIAL",
            f"{updated.alias or updated.ip} | {protocol} -> {credential_id}",
        )
        return 0

    reference = device.credentials.get(protocol)
    if not reference:
        raise ValueError(
            f"{device.alias or device.ip} no tiene credencial para {protocol}"
        )
    store.delete(reference)
    database.unbind_credential(args.selector, protocol)
    ok("ELIMINADA", f"{device.alias or device.ip} | {protocol}")
    return 0
