from __future__ import annotations

import argparse

from app.core.config import load_config
from app.core.credentials import CredentialStore
from app.core.database import DeviceDatabase
from app.models import normalize_protocol
from app.terminals import available_terminals, open_terminal


def register_terminal_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "terminal",
        aliases=["cli"],
        help="Abre la terminal propia de un elemento según su protocolo.",
    )
    command.add_argument("selector", help="IP, MAC o alias del elemento.")
    command.add_argument("-p", "--protocol", help="Protocolo si hay varias terminales.")
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.add_argument("--store", default=config["credentials"], help="Almacén cifrado de credenciales.")
    command.set_defaults(handler=run_terminal)


def choose_terminal(device, requested: str | None) -> str:
    available = available_terminals(device)
    if requested:
        protocol = normalize_protocol(requested)
        if protocol not in available:
            raise ValueError(f"{device.alias or device.ip} no ofrece una terminal {protocol}")
        return protocol
    if not available:
        raise ValueError(f"{device.alias or device.ip} no tiene terminales configuradas")
    if len(available) > 1:
        raise ValueError(
            "hay varias terminales disponibles: " + ", ".join(available)
            + "; usa --protocol PROTOCOLO"
        )
    return available[0]


def run_terminal(args: argparse.Namespace) -> int:
    config = load_config()
    device = DeviceDatabase(args.database).resolve(args.selector)
    protocol = choose_terminal(device, args.protocol)
    reference = device.credentials.get(protocol)
    if not reference:
        raise ValueError(
            f"{device.alias or device.ip} no tiene credencial {protocol}; ejecuta "
            f"run credential {device.alias or device.ip} set {protocol} -user USUARIO"
        )
    credential = CredentialStore(args.store).get(reference)
    return open_terminal(device, protocol, credential, config)
