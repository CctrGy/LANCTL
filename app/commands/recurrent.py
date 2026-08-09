from __future__ import annotations

import argparse

from app.core.output import write_records
from app.core.recurrent_elements import RecurrentElementDatabase

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
        help="Consulta los elementos recurrentes conocidos por LANCTL.",
        description=(
            "Muestra identidades recurrentes por MAC. No incluye IP porque "
            "puede cambiar en cada LAN."
        ),
    )
    command.add_argument(
        "-list",
        "--list",
        dest="list_elements",
        action="store_true",
        required=True,
        help="Lista todos los elementos recurrentes sin sus IP.",
    )
    command.add_argument(
        "-f",
        "--format",
        choices=("table", "json", "csv", "html", "xml"),
        default="table",
        help="Formato de salida (por defecto: table).",
    )
    command.add_argument("-o", "--output", help="Guarda la salida en un archivo.")
    command.set_defaults(handler=run_recurrent)


def run_recurrent(args: argparse.Namespace) -> int:
    write_records(
        RecurrentElementDatabase().load(),
        output_format=args.format,
        destination=args.output,
        columns=RECURRENT_COLUMNS,
    )
    return 0
