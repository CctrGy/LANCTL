from __future__ import annotations

import argparse

from lanctl.apps.ip.domain.models import normalize_protocol
from lanctl.apps.ip.infrastructure.terminals import available_terminals, open_terminal
from lanctl.core.config import load_config
from lanctl.core.credentials import CredentialStore
from lanctl.core.database import DeviceDatabase
from lanctl.shared.i18n import t


def register_terminal_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "terminal",
        aliases=["cli"],
        help=t("LANCTL.UI.HELP.OPEN_AN_ELEMENT_S_TERMINAL_ACCORDING_TO_ITS_PROTOCOL"),
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.ELEMENT_IP_MAC_OR_ALIAS"))
    command.add_argument(
        "-p", "--protocol", help=t("LANCTL.UI.HELP.PROTOCOL_WHEN_MULTIPLE_TERMINALS_ARE_AVAILABLE")
    )
    command.add_argument(
        "--native",
        action="store_true",
        help=t("LANCTL.UI.HELP.USE_THE_NATIVE_SSH_CLIENT_WITHOUT_LANCTL_S_COLOR_LAYER"),
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.add_argument(
        "--store",
        default=config["credentials"],
        help=t("LANCTL.UI.TEXT.ENCRYPTED_CREDENTIAL_STORE"),
    )
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
            "hay varias terminales disponibles: "
            + ", ".join(available)
            + "; usa --protocol PROTOCOLO"
        )
    return available[0]


def run_terminal(args: argparse.Namespace) -> int:
    config = load_config()
    device = DeviceDatabase(args.database).resolve(args.selector)
    from lanctl.apps.ip.domain.discovery import require_real_target

    require_real_target(device)
    protocol = choose_terminal(device, args.protocol)
    reference = device.credentials.get(protocol)
    if not reference:
        raise ValueError(
            f"{device.alias or device.ip} no tiene credencial {protocol}; ejecuta "
            f"run credential {device.alias or device.ip} set {protocol} -user USUARIO"
        )
    credential = CredentialStore(args.store).get(reference)
    terminal_config = dict(config)
    terminal_config["nativeTerminal"] = bool(getattr(args, "native", False))
    return open_terminal(device, protocol, credential, terminal_config)
