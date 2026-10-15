"""Categorized CLI editor; legacy settings flags remain supported."""

from __future__ import annotations

import argparse
import json
import sys

from lanctl.core.config import load_config
from lanctl.core.settings_catalog import CATEGORIES, catalog, leaves, set_program_value


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
        help="Lista todos los ajustes por categorías, con valor y estado editable.",
    )
    action.add_argument(
        "--get", metavar="RUTA", help="Consulta un ajuste por su ruta, por ejemplo ip.workers."
    )
    action.add_argument(
        "--set",
        nargs=2,
        metavar=("RUTA", "VALOR"),
        help="Modifica un ajuste; listas y booleanos usan JSON.",
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
    from lanctl.core.projects.current import active_project_info

    project = active_project_info()
    if not project or not project["valid"]:
        raise ValueError(
            "Selecciona un proyecto VLF válido con project use antes de configurar el proyecto"
        )
    return project["path"]


def _entries(scope):
    if scope == "program":
        entries = catalog(load_config())
        from lanctl.core.config import canonical_config

        entries.append(
            {
                "path": "access.remote",
                "category": "access",
                "value": canonical_config(load_config())["access"]["remote"],
                "readOnly": "",
            }
        )
        return sorted(entries, key=lambda entry: list(CATEGORIES).index(entry["category"]))
    from lanctl.core.projects.settings import PROJECT_EDITABLE, project_settings

    return [
        {
            "path": path,
            "category": path.split(".")[0],
            "value": value,
            "readOnly": "Campo automático o derivado"
            if path.split(".")[1] not in PROJECT_EDITABLE.get(path.split(".")[0], set())
            else "",
        }
        for path, value in leaves(project_settings(_project()))
    ]


def _decode(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _set(scope, path, text):
    entries = {entry["path"]: entry for entry in _entries(scope)}
    if path not in entries:
        raise ValueError(f"Ajuste desconocido: {path}")
    if entries[path]["readOnly"]:
        raise ValueError(f"{path}: solo lectura. {entries[path]['readOnly']}")
    value = _decode(text)
    if scope == "project":
        from lanctl.core.projects.settings import update_project_setting

        category, key = path.split(".", 1)
        update_project_setting(_project(), category, key, value)
        return
    # Reuse the existing command for remote settings: it validates the endpoint
    # and applies the service backend, rather than just changing a JSON flag.
    if path == "access.remote" or path.startswith("access.remote."):
        from .settings import register_settings_command, run_settings

        flags = {
            "enabled": "--remote-access",
            "bind": "--remote-bind",
            "cidr": "--remote-cidr",
            "port": "--remote-port",
            "passwordAuthentication": "--remote-password-auth",
            "backend": "--remote-backend",
            "forcedView": "--remote-forced-view",
        }
        from lanctl.core.config import DOCUMENT_DEFAULTS
        from lanctl.core.settings_catalog import validate_value

        values = value if path == "access.remote" else {path.rsplit(".", 1)[1]: value}
        if not isinstance(values, dict) or not values:
            raise ValueError("access.remote requiere un objeto JSON con ajustes remotos")
        arguments = ["settings"]
        for key, item in values.items():
            if key not in flags:
                raise ValueError(f"Ajuste remoto desconocido: {key}")
            validate_value(f"access.remote.{key}", item, DOCUMENT_DEFAULTS["access"]["remote"][key])
            rendered = ("on" if item else "off") if isinstance(item, bool) else str(item)
            arguments.extend([flags[key], rendered])
        parser = argparse.ArgumentParser()
        register_settings_command(parser.add_subparsers())
        run_settings(parser.parse_args(arguments))
    else:
        set_program_value(path, value)


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
                    text = input("Nuevo valor (JSON para listas/booleanos; vacío: cancelar): ")
                    if not text:
                        continue
                    try:
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
