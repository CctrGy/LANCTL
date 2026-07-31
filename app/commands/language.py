from __future__ import annotations

import argparse
import json

from colorama import Fore, Style

from app.core.config import load_config, save_config
from app.core.console import ok
from app.i18n import get_language_manager, t


def register_language_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("language", aliases=["languages", "lang"], help=t("LANCTL.LANGUAGE.COMMAND.HELP"))
    actions = command.add_subparsers(dest="language_action", metavar="ACTION", required=True)
    actions.add_parser("list", help=t("LANCTL.LANGUAGE.ACTION.LIST")).set_defaults(language_handler=_list)
    use = actions.add_parser("use", help=t("LANCTL.LANGUAGE.ACTION.USE"))
    use.add_argument("language", help="Language code or name, for example en or Español.")
    use.set_defaults(language_handler=_use)
    info = actions.add_parser("info", help=t("LANCTL.LANGUAGE.ACTION.INFO"))
    info.add_argument("language", nargs="?", help="Language code or name; active language by default.")
    info.set_defaults(language_handler=_info)
    install = actions.add_parser("install", help=t("LANCTL.LANGUAGE.ACTION.INSTALL"))
    install.add_argument("file", help="Language catalog with .lang extension.")
    install.set_defaults(language_handler=_install)
    validate = actions.add_parser("validate", help=t("LANCTL.LANGUAGE.ACTION.VALIDATE"))
    validate.add_argument("file", help="Language catalog with .lang extension.")
    validate.set_defaults(language_handler=_validate)
    export = actions.add_parser("export", help=t("LANCTL.LANGUAGE.ACTION.EXPORT"))
    export.add_argument("file", help="Destination .lang file.")
    export.set_defaults(language_handler=_export)
    command.set_defaults(handler=lambda args: args.language_handler(args))


def _list(args) -> int:
    manager = get_language_manager()
    print(f"{Style.BRIGHT}{Fore.CYAN}{t('LANCTL.LANGUAGE.FIELD.CODE'):<10} {t('LANCTL.LANGUAGE.FIELD.LANGUAGE'):<20} {t('LANCTL.LANGUAGE.FIELD.REGION'):<18} {t('LANCTL.LANGUAGE.FIELD.COVERAGE'):>10} {t('LANCTL.LANGUAGE.FIELD.ACTIVE'):>8}{Style.RESET_ALL}")
    print("-" * 72)
    for catalog in manager.list():
        result = manager.validate(catalog.path) if catalog.path else {"coverage": 100.0}
        print(f"{catalog.code:<10} {catalog.native_name:<20} {catalog.region or '-':<18} {result['coverage']:>9.1f}% {'O' if catalog.code == manager.selected else '-':>8}")
    return 0


def _use(args) -> int:
    manager = get_language_manager()
    requested = args.language.casefold()
    code = manager.resolve_code(args.language)
    english_aliases = ("en", "english", "inglés", "ingles")
    if code == "en" and requested not in english_aliases:
        raise ValueError(t("LANCTL.LANGUAGE.ERROR.NOT_FOUND", language=args.language))
    catalog = manager.select(code)
    config = load_config()
    config["language"] = catalog.code
    save_config(config)
    ok(t("LANCTL.LANGUAGE.STATUS.SELECTED"), f"{catalog.native_name} [{catalog.code}]")
    print("Restart LANCTL to apply the language to every interface component.")
    return 0


def _info(args) -> int:
    manager = get_language_manager()
    catalog = manager.catalogs[manager.resolve_code(args.language or manager.selected)]
    result = manager.validate(catalog.path) if catalog.path else {"translated": len(catalog.strings), "total": len(catalog.strings), "coverage": 100.0}
    print(json.dumps({
        "code": catalog.code, "name": catalog.name, "nativeName": catalog.native_name,
        "region": catalog.region, "version": catalog.version, "author": catalog.author,
        "owner": catalog.owner, "active": catalog.code == manager.selected,
        "translated": result["translated"], "total": result["total"], "coverage": result["coverage"],
        "path": str(catalog.path) if catalog.path else "built-in",
    }, ensure_ascii=False, indent=2))
    print(t("LANCTL.LANGUAGE.INFO.FALLBACK"))
    return 0


def _install(args) -> int:
    catalog = get_language_manager().install(args.file)
    ok(t("LANCTL.LANGUAGE.STATUS.INSTALLED"), f"{catalog.native_name} [{catalog.code}]")
    return 0


def _validate(args) -> int:
    result = get_language_manager().validate(args.file)
    ok(t("LANCTL.LANGUAGE.STATUS.VALID"), f"{result['catalog'].native_name} | {result['coverage']:.1f}%")
    return 0


def _export(args) -> int:
    path = get_language_manager().export_template(args.file)
    ok(t("LANCTL.LANGUAGE.STATUS.EXPORTED"), str(path))
    return 0
