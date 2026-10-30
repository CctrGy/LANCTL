from __future__ import annotations

import argparse
import json

from lanctl.core.config import load_config
from lanctl.core.database import DeviceDatabase
from lanctl.shared.i18n import t

FIELDS = {
    "ip": "IP",
    "cnf": "cnf",
    "mac": "MAC",
    "alias": "ALIAS",
    "name": "NAME",
    "group": "GROUP",
    "description": "description",
    "manufacturer": "manufacturer",
    "default-name": "defaultName",
    "device-id": "deviceId",
    "protocols": "protocols",
}


def public_device(device) -> dict:
    return {
        "IP": device.ip,
        "cnf": device.cnf,
        "ALIAS": device.alias,
        "MAC": device.mac,
        "NAME": device.name,
        "GROUP": device.groups,
        "description": device.description,
        "manufacturer": device.manufacturer,
        "defaultName": device.default_name,
        "deviceId": device.device_id,
        "protocols": device.protocols,
        "credentials": device.credentials,
        "protocolOptions": device.protocol_options,
    }


def register_call_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "call",
        help=t("LANCTL.UI.HELP.RESOLVE_AN_ALIAS_IP_OR_MAC_TO_DEVICE_DATA"),
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.DEVICE_ALIAS_IP_OR_MAC"))
    command.add_argument(
        "-f",
        "--field",
        choices=tuple(FIELDS),
        default="ip",
        help=t("LANCTL.UI.HELP.RETURNED_FIELD_DEFAULT_IP"),
    )
    command.add_argument(
        "--json",
        action="store_true",
        help=t("LANCTL.UI.HELP.RETURN_THE_COMPLETE_RECORD_AS_JSON"),
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.set_defaults(handler=run_call)


def run_call(args: argparse.Namespace) -> int:
    device = DeviceDatabase(args.database).resolve(args.selector)
    if args.json:
        print(json.dumps(public_device(device), indent=2, ensure_ascii=False))
    else:
        value = device[FIELDS[args.field]]
        print(",".join(value) if isinstance(value, list) else value)
    return 0
