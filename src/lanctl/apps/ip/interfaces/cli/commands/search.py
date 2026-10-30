from __future__ import annotations

import argparse
import json

from lanctl.apps.ip.interfaces.cli.commands.call import public_device
from lanctl.core.config import load_config
from lanctl.core.database import DeviceDatabase
from lanctl.core.output import write_records
from lanctl.shared.i18n import t

SEARCH_COLUMNS = (
    "ip",
    "cnf",
    "alias",
    "mac",
    "name",
    "group",
    "description",
    "manufacturer",
    "device-id",
    "protocols",
)


def register_search_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "search",
        help=t("LANCTL.UI.HELP.SEARCH_DEVICES_BY_ALIAS_NAME_IP_OR_MAC"),
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.EXACT_ALIAS_NAME_IP_OR_MAC"))
    command.add_argument(
        "--json",
        action="store_true",
        help=t("LANCTL.UI.HELP.RETURN_THE_COMPLETE_RECORD_AS_JSON_FOR_SCRIPTS"),
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.set_defaults(handler=run_search)


def run_search(args: argparse.Namespace) -> int:
    devices = DeviceDatabase(args.database).search(args.selector)
    if args.json:
        result = [public_device(device) for device in devices]
        print(
            json.dumps(
                result[0] if len(result) == 1 else result,
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        write_records(
            devices,
            output_format="table",
            columns=SEARCH_COLUMNS,
        )
    return 0
