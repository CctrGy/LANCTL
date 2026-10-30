from __future__ import annotations

import argparse

from lanctl.core.output import write_records
from lanctl.core.recurrent_elements import RecurrentElementDatabase
from lanctl.shared.i18n import t

RECURRENT_COLUMNS = (
    "cnf",
    "alias",
    "mac",
    "name",
    "group",
    "description",
    "manufacturer",
)


def register_recurrent_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "recurrent",
        help=t("LANCTL.UI.HELP.QUERY_RECURRING_ELEMENTS_KNOWN_TO_LANCTL"),
        description=(
            t(
                "LANCTL.UI.HELP.SHOW_RECURRING_IDENTITIES_BY_MAC_DOES_NOT_INCLUDE_IP_BECAUSE_IT_CAN_CHANGE_ON_EACH_LAN"
            )
        ),
    )
    command.add_argument(
        "-list",
        "--list",
        dest="list_elements",
        action="store_true",
        required=True,
        help=t("LANCTL.UI.HELP.LIST_ALL_RECURRING_ELEMENTS_WITHOUT_THEIR_IPS"),
    )
    command.add_argument(
        "-f",
        "--format",
        choices=("table", "json", "csv", "html", "xml", "yaml"),
        default="table",
        help=t("LANCTL.UI.HELP.OUTPUT_FORMAT_DEFAULT_TABLE"),
    )
    command.add_argument("-o", "--output", help=t("LANCTL.UI.HELP.SAVE_OUTPUT_TO_A_FILE"))
    command.set_defaults(handler=run_recurrent)


def run_recurrent(args: argparse.Namespace) -> int:
    write_records(
        RecurrentElementDatabase().load(),
        output_format=args.format,
        destination=args.output,
        columns=RECURRENT_COLUMNS,
    )
    return 0
