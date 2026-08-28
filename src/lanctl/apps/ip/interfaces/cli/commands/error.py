from __future__ import annotations

import argparse
import json

from lanctl.core.error_catalog import find_error


def register_error_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "error",
        aliases=("errors",),
        help="Consulta el catálogo por identificador 0eXXXXXXXX.",
    )
    command.add_argument("error_id", metavar="0eXXXXXXXX", help="Identificador estable del error.")
    command.add_argument("--json", action="store_true", help="Emite el resultado como JSON.")
    command.set_defaults(handler=run_error)


def run_error(args: argparse.Namespace) -> int:
    entry = find_error(args.error_id)
    if entry is None:
        raise ValueError(f"error no catalogado: {args.error_id}")
    if args.json:
        print(json.dumps(entry.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"ERROR {entry.error_id}")
        print(f"Nivel: {entry.level}")
        print(f"Origen: {entry.origin}")
        print(f"Fuente: {entry.source}:{entry.line}")
        print(f"Tipo: {entry.kind}")
    return 0
