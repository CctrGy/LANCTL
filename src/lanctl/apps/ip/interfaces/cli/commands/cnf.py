from __future__ import annotations

import argparse

from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.database import DeviceDatabase
from lanctl.shared.i18n import t


def register_cnf_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "cnf",
        help=t("LANCTL.UI.HELP.ASSIGN_AN_ELEMENT_S_CNF_STATE_BY_IP_MAC_OR_ALIAS"),
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.ELEMENT_IP_MAC_OR_ALIAS"))
    command.add_argument(
        "value",
        nargs="?",
        help=(
            t(
                "LANCTL.UI.HELP.O_OK_X_UNKNOWN_UNRECOGNIZED_S_MARKED_OR_F_FIXED_WITHOUT_A_VALUE_RELEASE_F_AND_RESTORE_O"
            )
        ),
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.set_defaults(handler=run_cnf)


def run_cnf(args: argparse.Namespace) -> int:
    current = DeviceDatabase(args.database).resolve(args.selector)
    value = args.value
    if value is None:
        if current.cnf != "F":
            ok(
                t("LANCTL.UI.STATUS.UNCHANGED"),
                f"{current.alias or current.ip} | cnf = {current.cnf}",
            )
            return 0
        value = "O"
    device = DeviceDatabase(args.database).edit_device(args.selector, "cnf", value)
    ok(t("LANCTL.UI.STATUS.UPDATED"), f"{device.alias or device.ip} | cnf = {device.cnf}")
    return 0
