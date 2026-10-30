from __future__ import annotations

import argparse
import json
from pathlib import Path

from lanctl.core.config import load_config
from lanctl.core.paths import application_path, data_root
from lanctl.core.persistence import (
    checks_as_dict,
    diagnose_storage,
    export_storage,
    import_storage,
    restore_backup,
    verify_export,
)
from lanctl.shared.i18n import t


def register_database_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "database", aliases=("db",), help=t("LANCTL.UI.HELP.DIAGNOSE_AND_EXPORT_DATA")
    )
    actions = command.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--diagnose", action="store_true", help=t("LANCTL.UI.HELP.VALIDATE_CONFIGURED_STORES")
    )
    actions.add_argument(
        "--export",
        metavar="ARCHIVO.zip",
        help=t("LANCTL.UI.HELP.EXPORT_DATA_WITH_VERIFIABLE_HASHES"),
    )
    actions.add_argument(
        "--verify",
        metavar="ARCHIVO.zip",
        help=t("LANCTL.UI.HELP.VERIFY_AN_EXPORT_WITHOUT_IMPORTING_IT"),
    )
    actions.add_argument(
        "--import",
        dest="import_file",
        metavar="ARCHIVO.zip",
        help=t("LANCTL.UI.HELP.IMPORT_VERIFIED_DATA"),
    )
    actions.add_argument(
        "--restore",
        metavar="ARCHIVO.bak",
        help=t("LANCTL.UI.HELP.RESTORE_A_VALIDATED_STORE_BACKUP"),
    )
    command.add_argument(
        "--target",
        choices=("database", "groups", "physical"),
        help=t("LANCTL.UI.HELP.STORE_TO_RESTORE"),
    )
    command.add_argument(
        "--yes", action="store_true", help=t("LANCTL.UI.HELP.CONFIRM_DATA_REPLACEMENT")
    )
    command.add_argument(
        "--json", action="store_true", help=t("LANCTL.UI.HELP.OUTPUT_DIAGNOSTICS_AS_JSON")
    )
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
    if args.import_file:
        if not args.yes:
            raise ValueError("database --import requiere --yes y una copia externa confirmada")
        imported = import_storage(args.import_file, data_root())
        print(t("LANCTL.UI.MESSAGE.IMPORTED_AND_VERIFIED_VALUE_FILES", value0=f"{len(imported)}"))
        return 0
    if args.restore:
        if not args.yes or not args.target:
            raise ValueError("database --restore requiere --target y --yes")
        config = load_config()
        key = {"database": "database", "groups": "groups", "physical": "physicalDatabase"}[
            args.target
        ]
        target = application_path(config[key])
        restore_backup(target, args.restore)
        print(t("LANCTL.UI.MESSAGE.RESTORED_AND_VALIDATED_VALUE", value0=f"{target}"))
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
