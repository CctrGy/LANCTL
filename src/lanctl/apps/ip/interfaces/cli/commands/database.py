from __future__ import annotations

import argparse
import json
from pathlib import Path

from lanctl.core.config import load_config
from lanctl.core.paths import application_path, data_root
from lanctl.core.persistence import checks_as_dict, diagnose_storage, export_storage, verify_export


def register_database_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("database", aliases=("db",), help="Diagnostica y exporta datos.")
    actions = command.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--diagnose", action="store_true", help="Valida los almacenes configurados."
    )
    actions.add_argument(
        "--export", metavar="ARCHIVO.zip", help="Exporta datos con hashes verificables."
    )
    actions.add_argument(
        "--verify", metavar="ARCHIVO.zip", help="Verifica una exportación sin importarla."
    )
    command.add_argument("--json", action="store_true", help="Emite el diagnóstico como JSON.")
    command.set_defaults(handler=run_database)


def _configured_paths() -> list[Path]:
    config = load_config()
    keys = ("database", "groups", "physicalDatabase")
    paths = [application_path(config[key]) for key in keys if config.get(key)]
    paths.extend((data_root() / "config/config.json", data_root() / "plugins/registry.json"))
    return paths


def run_database(args: argparse.Namespace) -> int:
    if args.verify:
        manifest = verify_export(args.verify)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    if args.export:
        print(export_storage(_configured_paths(), args.export))
        return 0
    checks = diagnose_storage(_configured_paths())
    if args.json:
        print(json.dumps(checks_as_dict(checks), ensure_ascii=False, indent=2))
    else:
        for check in checks:
            print(
                f"{'OK' if check.valid else 'ERROR':<5} {check.kind:<11} {check.path} {check.detail}"
            )
    return 0 if all(check.valid for check in checks) else 2
