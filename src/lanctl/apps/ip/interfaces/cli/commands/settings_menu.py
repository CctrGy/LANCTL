"""Categorized CLI editor; legacy settings flags remain supported."""

from __future__ import annotations

import argparse
import json
import sys

from lanctl.core.settings_catalog import CATEGORIES


def register_catalog_options(command):
    action = command.add_mutually_exclusive_group()
    action.add_argument(
        "--menu",
        action="store_true",
        help="Editor interactivo por categorías de programa y proyecto.",
    )
    action.add_argument(
        "--catalog",
        action="store_true",
        help="Lista preferencias comunes y CLI por categorías, con valor y estado editable.",
    )
    action.add_argument(
        "--get", metavar="RUTA", help="Consulta un ajuste por su ruta, por ejemplo ip.workers."
    )
    action.add_argument(
        "--set",
        nargs=2,
        metavar=("RUTA", "VALOR"),
        help="Modifica una preferencia común o CLI; listas y booleanos usan JSON.",
    )
    command.add_argument(
        "--scope",
        choices=("program", "project"),
        default="program",
        help="Ámbito de configuración (predeterminado: program).",
    )
    command.add_argument(
        "--category", help="Filtra el catálogo por categoría, por ejemplo network o monitor."
    )


def _project():
    from lanctl.apps.suite.settings import active_settings_project

    return active_settings_project()


def _entries(scope):
    from lanctl.apps.suite.settings import cli_context, settings_entries

    return settings_entries(
        cli_context(scope), project_path=_project() if scope == "project" else None
    )


def _decode(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _set(scope, path, text):
    from lanctl.apps.suite.settings import cli_context, save_setting
    from lanctl.core.project_context import project_operation

    with project_operation():
        save_setting(
            cli_context(scope),
            path,
            _decode(text),
            project_path=_project() if scope == "project" else None,
        )


def _print_entries(entries):
    previous = None
    for entry in entries:
        category = entry["category"]
        if category != previous:
            print(f"\n[{category}] {CATEGORIES.get(category, category)}")
            previous = category
        state = f" [solo lectura: {entry['readOnly']}]" if entry["readOnly"] else ""
        print(f"  {entry['path']} = {json.dumps(entry['value'], ensure_ascii=False)}{state}")


def configuration_menu():
    try:
        while True:
            print("\nConfiguración LANCTL\n1. Programa completo\n2. Proyecto activo\n0. Volver")
            choice = input("> ").strip()
            if choice in {"0", "", "q"}:
                return 0
            if choice not in {"1", "2"}:
                continue
            scope = "program" if choice == "1" else "project"
            try:
                entries = _entries(scope)
            except ValueError as error:
                print(error)
                continue
            while True:
                categories = list(dict.fromkeys(entry["category"] for entry in entries))
                for number, category in enumerate(categories, 1):
                    print(f"{number}. {CATEGORIES.get(category, category)} ({category})")
                selection = input("Categoría (0: volver): ").strip()
                if selection in {"0", "", "q"}:
                    break
                if not selection.isdigit() or not 1 <= int(selection) <= len(categories):
                    continue
                category = categories[int(selection) - 1]
                while True:
                    entries = _entries(scope)
                    subset = [entry for entry in entries if entry["category"] == category]
                    for number, entry in enumerate(subset, 1):
                        state = " [solo lectura]" if entry["readOnly"] else ""
                        print(
                            f"{number}. {entry['path']} = {json.dumps(entry['value'], ensure_ascii=False)}{state}"
                        )
                    selected = input("Ajuste (0: volver): ").strip()
                    if selected in {"0", "", "q"}:
                        break
                    if not selected.isdigit() or not 1 <= int(selected) <= len(subset):
                        continue
                    entry = subset[int(selected) - 1]
                    if entry["readOnly"]:
                        print(entry["readOnly"])
                        continue
                    from lanctl.core.config import load_config
                    from lanctl.core.project_context import (
                        project_identity,
                        project_operation,
                        require_project,
                    )

                    expected = project_identity(load_config())
                    text = input("Nuevo valor (JSON para listas/booleanos; vacío: cancelar): ")
                    if not text:
                        continue
                    try:
                        with project_operation():
                            require_project(expected)
                            _set(scope, entry["path"], text)
                        print("Configuración guardada.")
                    except (ValueError, OSError) as error:
                        print(f"No se ha podido guardar: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nConfiguración cerrada.")
        return 0


def dispatch_settings(args):
    from .settings import run_settings

    requested = (
        args.menu
        or args.catalog
        or args.get is not None
        or args.set is not None
        or args.category
        or args.scope == "project"
    )
    legacy = [
        key
        for key, value in vars(args).items()
        if key not in {"handler", "command", "menu", "catalog", "get", "set", "scope", "category"}
        and value is not None
    ]
    # Parser namespaces may contain launcher metadata. Only the options registered
    # on the settings parser count as legacy mutations.
    parser = argparse.ArgumentParser()
    from .settings import register_settings_command

    sub = parser.add_subparsers()
    register_settings_command(sub)
    defaults = vars(parser.parse_args(["settings"]))
    legacy = [key for key in legacy if key in defaults and vars(args)[key] != defaults[key]]
    if requested and legacy:
        raise ValueError("Usa el menú/catálogo separado de las opciones clásicas de modificación")
    if args.menu or (not requested and not legacy and sys.stdin.isatty() and sys.stdout.isatty()):
        return configuration_menu()
    if not requested:
        return run_settings(args)
    if args.set is not None:
        if args.category:
            raise ValueError("--category filtra consultas, no modificaciones")
        _set(args.scope, *args.set)
        print("Configuración guardada.")
        return 0
    entries = _entries(args.scope)
    if args.category:
        entries = [entry for entry in entries if entry["category"] == args.category]
        if not entries:
            raise ValueError(f"Categoría desconocida: {args.category}")
    if args.get is not None:
        found = next((entry for entry in entries if entry["path"] == args.get), None)
        if found is None:
            raise ValueError(f"Ajuste desconocido: {args.get}")
        print(json.dumps(found["value"], ensure_ascii=False, indent=2))
    else:
        _print_entries(entries)
    return 0
