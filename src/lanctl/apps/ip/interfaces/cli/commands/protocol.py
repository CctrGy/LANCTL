from __future__ import annotations

import argparse
import json

from lanctl.apps.ip.infrastructure.protocols.ssh import SSH_PROFILES, SshProfile
from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.database import DeviceDatabase
from lanctl.shared.i18n import t


def register_protocol_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "protocol", help=t("LANCTL.UI.HELP.QUERY_OR_CONFIGURE_AN_ELEMENT_S_PROTOCOL")
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.IP_MAC_OR_ALIAS"))
    command.add_argument(
        "action",
        choices=("show", "configure"),
        help=t("LANCTL.UI.HELP.QUERY_OR_CHANGE_THE_PROTOCOL"),
    )
    command.add_argument("protocol", help=t("LANCTL.UI.HELP.PROTOCOL_TO_CONFIGURE"))
    command.add_argument("--port", type=int, default=22, help=t("LANCTL.UI.HELP.REMOTE_PORT"))
    command.add_argument("--driver", default="autodetect", help=t("LANCTL.UI.HELP.DEVICE_DRIVER"))
    command.add_argument(
        "--host-key",
        action="append",
        default=[],
        help=t("LANCTL.UI.HELP.ALLOWED_HOST_KEY_ALGORITHM_MAY_BE_REPEATED"),
    )
    command.add_argument(
        "--kex",
        action="append",
        default=[],
        help=t("LANCTL.UI.HELP.KEY_EXCHANGE_ALGORITHM_MAY_BE_REPEATED"),
    )
    command.add_argument(
        "--profile", choices=tuple(SSH_PROFILES), help=t("LANCTL.UI.HELP.REUSABLE_SSH_PROFILE")
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.set_defaults(handler=run_protocol)


def run_protocol(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    device = database.resolve(args.selector)
    protocol = args.protocol.casefold()
    if args.action == "show":
        print(json.dumps(device.protocol_options.get(protocol, {}), indent=2))
        return 0
    if protocol != "ssh":
        raise ValueError("la configuración avanzada está implementada actualmente para ssh")
    options = (
        dict(SSH_PROFILES[args.profile])
        if args.profile
        else {
            "port": args.port,
            "driver": args.driver,
            "hostKeyAlgorithms": args.host_key,
            "kexAlgorithms": args.kex,
        }
    )
    SshProfile.from_options(options)
    updated = database.configure_protocol(args.selector, protocol, options)
    ok(
        t("LANCTL.UI.STATUS.PROTOCOL"),
        t(
            "LANCTL.UI.SUMMARY.VALUE_SSH_CONFIGURED_ONLY_FOR_THIS_ELEMENT",
            value0=f"{updated.alias or updated.ip}",
        ),
    )
    return 0
