from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timezone

from lanctl.core.history import HistoryService
from lanctl.shared.i18n import t


def register_history_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "history", help=t("LANCTL.UI.HELP.QUERY_STRUCTURED_EVENTS_FROM_THE_ACTIVE_VLF_PROJECT")
    )
    command.add_argument(
        "selector",
        nargs="?",
        help=t("LANCTL.UI.HELP.DEVICEID_ALIAS_NAME_MAC_CURRENT_OR_HISTORICAL_IP"),
    )
    command.add_argument(
        "--all",
        action="store_true",
        help=t("LANCTL.UI.HELP.INCLUDE_GENERAL_EVENTS_FROM_THE_ENTIRE_LAN"),
    )
    command.add_argument(
        "--commands",
        action="store_true",
        help=t("LANCTL.UI.HELP.IN_THE_INTERACTIVE_CLI_SHOW_SESSION_COMMANDS"),
    )
    command.add_argument(
        "--today",
        action="store_true",
        help=t("LANCTL.UI.HELP.LIMIT_THE_QUERY_TO_THE_CURRENT_LOCAL_DAY"),
    )
    command.add_argument(
        "--from",
        dest="date_from",
        type=date.fromisoformat,
        metavar="FECHA",
        help=t("LANCTL.UI.HELP.START_DATE_YYYY_MM_DD"),
    )
    command.add_argument(
        "--to",
        dest="date_to",
        type=date.fromisoformat,
        metavar="FECHA",
        help=t("LANCTL.UI.HELP.END_DATE_YYYY_MM_DD"),
    )
    command.add_argument(
        "--type",
        dest="types",
        action="append",
        default=[],
        help=t("LANCTL.UI.HELP.CANONICAL_TYPE_MAY_BE_REPEATED"),
    )
    command.add_argument("--source", help=t("LANCTL.UI.HELP.FILTER_BY_SOURCE"))
    command.add_argument("--result", help=t("LANCTL.UI.HELP.FILTER_BY_RESULT"))
    command.add_argument("--errors", action="store_true", help=t("LANCTL.UI.HELP.SHOW_ERRORS_ONLY"))
    command.add_argument("--search", help=t("LANCTL.UI.HELP.SEARCH_SAFE_TEXT"))
    command.add_argument(
        "--limit", type=int, default=100, help=t("LANCTL.UI.HELP.MAXIMUM_NUMBER_OF_EVENTS_1_10000")
    )
    command.add_argument(
        "--reverse", action="store_true", help=t("LANCTL.UI.HELP.DESCENDING_ORDER")
    )
    command.add_argument(
        "--format",
        choices=("table", "json", "csv"),
        default="table",
        help=t("LANCTL.UI.HELP.OUTPUT_FORMAT"),
    )
    command.set_defaults(handler=run_history)


def run_history(args: argparse.Namespace) -> int:
    if args.commands:
        raise ValueError("--commands solo está disponible dentro de la CLI interactiva")
    if not args.selector and not args.all:
        raise ValueError("indica NAME o usa --all")
    today = datetime.now(timezone.utc).astimezone().date() if args.today else None
    rows = HistoryService().query(
        None if args.all else args.selector,
        date_from=today or args.date_from,
        date_to=today or args.date_to,
        types=args.types,
        source=args.source,
        result=args.result,
        errors=args.errors,
        search=args.search,
        limit=args.limit,
        reverse=args.reverse,
    )
    values = [event.to_dict() for event in rows]
    if args.format == "json":
        print(json.dumps(values, indent=2, ensure_ascii=False))
        return 0
    if args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(("timestamp", "device", "source", "type", "result", "summary"))
        for e in rows:
            writer.writerow(
                (
                    e.timestamp,
                    e.device.label if e.device else "",
                    e.source,
                    e.type,
                    e.result,
                    e.summary,
                )
            )
        return 0
    print(t("LANCTL.UI.SUMMARY.HISTORY_VALUE", value0=f"{args.selector or 'LAN'}"))
    print(t("LANCTL.UI.STATUS.DATE_ELEMENT_EVENT_RESULT_SUMMARY"))
    for e in rows:
        print(
            f"{e.timestamp} | {e.device.label if e.device else '-'} | {e.type} | {e.result} | {e.summary}"
        )
    return 0
