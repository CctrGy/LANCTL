from __future__ import annotations

import argparse
import json

from lanctl.core.error_catalog import find_error
from lanctl.shared.i18n import t


def register_error_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "error",
        aliases=("errors",),
        help=t("LANCTL.UI.HELP.QUERY_THE_CATALOG_BY_IDENTIFIER_0EXXXXXXXX"),
    )
    command.add_argument(
        "error_id", metavar="0eXXXXXXXX", help=t("LANCTL.UI.HELP.STABLE_ERROR_IDENTIFIER")
    )
    command.add_argument(
        "--json", action="store_true", help=t("LANCTL.UI.HELP.OUTPUT_THE_RESULT_AS_JSON")
    )
    command.set_defaults(handler=run_error)


def run_error(args: argparse.Namespace) -> int:
    entry = find_error(args.error_id)
    if entry is None:
        raise ValueError(f"error no catalogado: {args.error_id}")
    if args.json:
        print(json.dumps(entry.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"ERROR {entry.error_id}")
        print(t("LANCTL.UI.DETAIL.LEVEL_VALUE", value0=f"{entry.level}"))
        print(t("LANCTL.UI.DETAIL.ORIGIN_VALUE", value0=f"{entry.origin}"))
        print(
            t(
                "LANCTL.UI.DETAIL.SOURCE_VALUE_VALUE",
                value0=f"{entry.source}",
                value1=f"{entry.line}",
            )
        )
        print(t("LANCTL.UI.DETAIL.TYPE_VALUE", value0=f"{entry.kind}"))
    return 0
