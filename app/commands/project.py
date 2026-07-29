from __future__ import annotations

import argparse
import getpass
import json

from colorama import Fore, Style

from app.core.console import ok
from app.core.layout import fit_text, terminal_columns
from app.core.logger import write_log
from app.core.config import load_config, save_config
from app.projects import (
    create_project, inspect_project, list_project_entries,
    update_project, verify_project,
)


def register_project_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "project", aliases=["projects"],
        help="Crea, actualiza e inspecciona proyectos LANCTL .vlf.",
    )
    actions = command.add_subparsers(dest="project_action", metavar="ACCIÓN", required=True)

    create = actions.add_parser("create", help="Empaqueta la LAN activa en un proyecto VLF.")
    create.add_argument("file", help="Archivo de salida; se añade .vlf si falta.")
    create.add_argument("--name", help="Nombre humano del proyecto.")
    create.add_argument("--description", default="", help="Descripción general.")
    create.add_argument("--author", default=getpass.getuser(), help="Autor del proyecto.")
    create.add_argument("--lan-name", default="", help="Nombre humano de la LAN.")
    create.add_argument("--location", default="", help="Ubicación física.")
    create.add_argument("--company", default="", help="Empresa u organización.")
    create.add_argument("--responsible", default="", help="Responsable de la LAN.")
    create.add_argument("--force", action="store_true", help="Sobrescribe un VLF existente.")
    create.set_defaults(project_handler=_create)

    update = actions.add_parser("update", help="Actualiza datos activos conservando información complementaria.")
    update.add_argument("file", help="Proyecto VLF existente.")
    update.set_defaults(project_handler=_update)

    info = actions.add_parser("info", help="Muestra los metadatos del proyecto.")
    info.add_argument("file", help="Proyecto VLF.")
    info.add_argument("--json", action="store_true", help="Devuelve JSON.")
    info.set_defaults(project_handler=_info)

    verify = actions.add_parser("verify", help="Comprueba hashes, estructura y SQLite.")
    verify.add_argument("file", help="Proyecto VLF.")
    verify.add_argument("--json", action="store_true", help="Devuelve JSON.")
    verify.set_defaults(project_handler=_verify)

    use = actions.add_parser("use", help="Selecciona el proyecto VLF que recibirá la auditoría.")
    use.add_argument("file", help="Proyecto VLF existente.")
    use.set_defaults(project_handler=_use)

    listing = actions.add_parser("list", help="Lista el contenido interno sin extraerlo.")
    listing.add_argument("file", help="Proyecto VLF.")
    listing.set_defaults(project_handler=_list)
    command.set_defaults(handler=run_project)


def run_project(args: argparse.Namespace) -> int:
    return args.project_handler(args)


def _create(args) -> int:
    result = create_project(
        args.file, name=args.name or "", description=args.description,
        author=args.author, lan_name=args.lan_name, location=args.location,
        company=args.company, responsible=args.responsible,
        overwrite=args.force,
    )
    project = result["project"]
    _set_active_project(result["path"])
    write_log(f"PROJECT CREATE id={project['id']} path={result['path']}")
    ok("PROYECTO", f"{project['name']} | {project['devices']} dispositivos")
    print(f" Archivo : {result['path']}")
    print(f" UUID    : {project['id']}")
    print(f" SHA-256 : {result['checksum']}")
    return 0


def _update(args) -> int:
    result = update_project(args.file)
    _set_active_project(result["path"])
    write_log(f"PROJECT UPDATE path={result['path']}")
    ok("ACTUALIZADO", result["path"])
    print(f" Backup  : {result['backup']}")
    print(f" SHA-256 : {result['checksum']}")
    return 0


def _set_active_project(path: str) -> None:
    config = load_config()
    config["activeProject"] = str(path)
    config.pop("databaseLog", None)
    save_config(config)


def _use(args) -> int:
    result = verify_project(args.file)
    from pathlib import Path

    project = Path(args.file).expanduser()
    if project.suffix.casefold() != ".vlf":
        project = project.with_suffix(".vlf")
    resolved = str(project.resolve())
    _set_active_project(resolved)
    ok("PROYECTO ACTIVO", resolved)
    print(f" SHA-256 : {result['checksum']}")
    return 0


def _info(args) -> int:
    info = inspect_project(args.file)
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0
    fields = (
        ("PROYECTO", info.get("name")), ("DESCRIPCIÓN", info.get("description")),
        ("AUTOR", info.get("author")), ("UUID", info.get("id")),
        ("FORMATO", info.get("formatVersion")), ("LANCTL", info.get("lanctlVersion")),
        ("CREADO", info.get("created")), ("ACTUALIZADO", info.get("updated")),
        ("DISPOSITIVOS", info.get("devices")), ("GRUPOS", info.get("groups")),
        ("CONTENT HASH", info.get("contentHash")),
    )
    width = terminal_columns() or 120
    for label, value in fields:
        print(
            f"{Style.BRIGHT}{Fore.CYAN}{label:<13}{Style.RESET_ALL} "
            f"{fit_text(value or '-', max(1, width - 15))}"
        )
    return 0


def _verify(args) -> int:
    result = verify_project(args.file)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        ok("VLF VÁLIDO", f"Formato {result['formatVersion']} | {result['entries']} archivos")
        print(f" SHA-256 : {result['checksum']}")
        print(f" Tamaño  : {result['size']} bytes")
    return 0


def _list(args) -> int:
    entries = list_project_entries(args.file)
    width = terminal_columns() or 120
    path_width = max(10, width - 27)
    print(f"{Style.BRIGHT}{Fore.CYAN}{'PATH':<{path_width}}  {'SIZE':>10}  {'COMPRESSED':>10}{Style.RESET_ALL}")
    print("-" * min(width, path_width + 24))
    for entry in entries:
        print(
            f"{fit_text(entry['path'], path_width):<{path_width}}  "
            f"{entry['size']:>10}  {entry['compressed']:>10}"
        )
    return 0
