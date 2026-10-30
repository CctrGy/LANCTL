from __future__ import annotations

import argparse
import getpass
import json
import tempfile
from pathlib import Path

from colorama import Fore, Style

from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.layout import fit_text, terminal_columns
from lanctl.core.logger import write_log
from lanctl.core.projects import (
    activate_project_workspace,
    active_project_info,
    create_project,
    inspect_project,
    list_project_entries,
    resolve_project_path,
    verify_project,
)
from lanctl.shared.i18n import t


def register_project_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "project",
        aliases=["projects"],
        help=t("LANCTL.UI.HELP.CREATE_UPDATE_AND_INSPECT_LANCTL_VLF_PROJECTS"),
    )
    actions = command.add_subparsers(dest="project_action", metavar="ACCIÓN")

    status = actions.add_parser("status", help=t("LANCTL.UI.HELP.SHOW_THE_ACTIVE_PROJECT"))
    status.add_argument("--json", action="store_true", help=t("LANCTL.UI.HELP.RETURN_JSON"))
    status.set_defaults(project_handler=_status)

    create = actions.add_parser(
        "create", help=t("LANCTL.UI.HELP.CREATE_AN_EMPTY_VLF_PROJECT_BY_DEFAULT")
    )
    create.add_argument("file", help=t("LANCTL.UI.HELP.OUTPUT_FILE_VLF_IS_APPENDED_IF_MISSING"))
    create.add_argument("--name", help=t("LANCTL.UI.HELP.HUMAN_READABLE_PROJECT_NAME"))
    create.add_argument("--description", default="", help=t("LANCTL.UI.HELP.GENERAL_DESCRIPTION"))
    create.add_argument(
        "--author", default=getpass.getuser(), help=t("LANCTL.UI.HELP.PROJECT_AUTHOR")
    )
    create.add_argument("--lan-name", default="", help=t("LANCTL.UI.HELP.HUMAN_READABLE_LAN_NAME"))
    create.add_argument("--location", default="", help=t("LANCTL.UI.HELP.PHYSICAL_LOCATION"))
    create.add_argument("--company", default="", help=t("LANCTL.UI.HELP.COMPANY_OR_ORGANIZATION"))
    create.add_argument(
        "--responsible", default="", help=t("LANCTL.UI.HELP.PERSON_RESPONSIBLE_FOR_THE_LAN")
    )
    create.add_argument(
        "--empty",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    create.add_argument(
        "--clone-current",
        action="store_true",
        help=t(
            "LANCTL.UI.HELP.CREATE_THE_PROJECT_BY_EXPLICITLY_COPYING_THE_ACTIVE_INVENTORY_AND_GROUPS"
        ),
    )
    create.add_argument(
        "--force", action="store_true", help=t("LANCTL.UI.HELP.OVERWRITE_AN_EXISTING_VLF")
    )
    create.set_defaults(project_handler=_create)

    update = actions.add_parser(
        "update",
        help=t("LANCTL.UI.HELP.UPDATE_ACTIVE_DATA_WHILE_PRESERVING_SUPPLEMENTARY_INFORMATION"),
    )
    update.add_argument("file", help=t("LANCTL.UI.HELP.EXISTING_VLF_PROJECT"))
    update.set_defaults(project_handler=_update)

    save = actions.add_parser("save", help=t("LANCTL.UI.HELP.MANUALLY_SAVE_THE_ACTIVE_VLF_PROJECT"))
    save.set_defaults(project_handler=_save)

    physical = actions.add_parser(
        "import-physical",
        help=t(
            "LANCTL.UI.HELP.COPY_A_HISTORICAL_IDF_DATABASE_INTO_THE_ACTIVE_EMPTY_PHYSICAL_PROJECT"
        ),
    )
    physical.add_argument(
        "file", help=t("LANCTL.UI.HELP.SOURCE_IDF_DB_DATABASE_PRESERVED_UNCHANGED")
    )
    physical.set_defaults(project_handler=_import_physical)

    info = actions.add_parser("info", help=t("LANCTL.UI.HELP.SHOW_PROJECT_METADATA"))
    info.add_argument("file", help=t("LANCTL.UI.HELP.VLF_PROJECT"))
    info.add_argument("--json", action="store_true", help=t("LANCTL.UI.HELP.RETURN_JSON"))
    info.set_defaults(project_handler=_info)

    verify = actions.add_parser(
        "verify", help=t("LANCTL.UI.HELP.CHECK_HASHES_STRUCTURE_AND_SQLITE")
    )
    verify.add_argument("file", help=t("LANCTL.UI.HELP.VLF_PROJECT"))
    verify.add_argument("--json", action="store_true", help=t("LANCTL.UI.HELP.RETURN_JSON"))
    verify.set_defaults(project_handler=_verify)

    use = actions.add_parser(
        "use", help=t("LANCTL.UI.HELP.SELECT_THE_VLF_PROJECT_THAT_RECEIVES_THE_AUDIT")
    )
    use.add_argument("file", help=t("LANCTL.UI.HELP.EXISTING_VLF_PROJECT"))
    use.set_defaults(project_handler=_use)

    listing = actions.add_parser(
        "list", help=t("LANCTL.UI.HELP.LIST_INTERNAL_CONTENTS_WITHOUT_EXTRACTING_THEM")
    )
    listing.add_argument("file", help=t("LANCTL.UI.HELP.VLF_PROJECT"))
    listing.set_defaults(project_handler=_list)
    command.set_defaults(handler=run_project, project_handler=_status, json=False)


def run_project(args: argparse.Namespace) -> int:
    return args.project_handler(args)


def _status(args) -> int:
    info = active_project_info()
    if getattr(args, "json", False):
        print(json.dumps(info or {}, ensure_ascii=False, indent=2))
        return 0
    if info is None:
        ok(t("LANCTL.UI.STATUS.PROJECT"), t("LANCTL.UI.PROMPT.NO_PROJECT_SELECTED"))
        return 0
    state = "válido" if info["valid"] else "no disponible o dañado"
    ok(t("LANCTL.UI.STATUS.ACTIVE_PROJECT"), f"{info['name']} | {state}")
    print(t("LANCTL.UI.DETAIL.FILE_VALUE_539A9E46", value0=f"{info['path']}"))
    if info["id"]:
        print(f" UUID    : {info['id']}")
    settings = load_config()
    print(
        t(
            "LANCTL.UI.DETAIL.SAVEMODE_VALUE_603C21DC",
            value0=f"{settings.get('projectSaveMode', 'manual')}",
        )
    )
    if str(settings.get("projectSaveMode", "")).casefold() == "automatic.timetosave":
        print(
            t(
                "LANCTL.UI.DETAIL.INTERVAL_VALUE_MINUTES",
                value0=f"{settings.get('projectSaveIntervalMinutes', 5)}",
            )
        )
    return 0


def _create(args) -> int:
    settings = load_config()
    destination = Path(args.file).expanduser()
    if destination.suffix.casefold() != ".vlf":
        destination = destination.with_suffix(".vlf")
    active = str(settings.get("activeProject") or "").strip()
    if args.force and active and destination.resolve() == Path(active).expanduser().resolve():
        raise ValueError(
            "no se puede sobrescribir con --force el proyecto activo; crea otro proyecto"
        )
    options = {
        "name": args.name or "",
        "description": args.description,
        "author": args.author,
        "lan_name": args.lan_name,
        "location": args.location,
        "company": args.company,
        "responsible": args.responsible,
        "overwrite": args.force,
    }
    if not getattr(args, "clone_current", False):
        with tempfile.TemporaryDirectory(prefix="lanctl-project-create-") as temporary:
            empty_config = dict(load_config())
            empty_config["database"] = str(Path(temporary) / "devices.json")
            empty_config["groups"] = str(Path(temporary) / "groups.json")
            result = create_project(
                args.file,
                config=empty_config,
                initialize_reserved=False,
                **options,
            )
    else:
        result = create_project(args.file, **options)
    project = result["project"]
    _set_active_project(result["path"])
    from lanctl.core.plugins import get_plugin_manager

    get_plugin_manager().events.emit(
        "LANCTL.Project.File.Open",
        {
            "path": result["path"],
            "project_id": project["id"],
        },
    )
    write_log(f"PROJECT CREATE id={project['id']} path={result['path']}")
    ok(
        t("LANCTL.UI.STATUS.PROJECT"),
        t(
            "LANCTL.UI.SUMMARY.VALUE_VALUE_DEVICES",
            value0=f"{project['name']}",
            value1=f"{project['devices']}",
        ),
    )
    print(t("LANCTL.UI.DETAIL.FILE_VALUE_539A9E46", value0=f"{result['path']}"))
    print(f" UUID    : {project['id']}")
    print(f" SHA-256 : {result['checksum']}")
    return 0


def _update(args) -> int:
    settings = load_config()
    active = str(settings.get("activeProject") or "").strip()
    target = resolve_project_path(args.file, settings.get("projectsDirectory"))
    if not active or target.resolve() != Path(active).expanduser().resolve():
        raise ValueError(
            "project update solo puede guardar el proyecto activo; usa project use primero"
        )
    # ``update`` conserva el alias histórico, pero usa la misma transacción y
    # verificación semántica que ``save`` y Ctrl+S.
    from lanctl.core.projects.save_policy import save_active_project

    saved = save_active_project(force=True, config=settings)
    if not saved.saved:
        raise ValueError("no hay un proyecto activo que guardar")
    _set_active_project(saved.path)
    verified = verify_project(saved.path)
    backup = str(Path(saved.path).with_suffix(Path(saved.path).suffix + ".bak"))
    write_log(f"PROJECT UPDATE path={saved.path}")
    ok(t("LANCTL.UI.STATUS.UPDATED"), saved.path)
    print(t("LANCTL.UI.DETAIL.BACKUP_VALUE", value0=f"{backup}"))
    print(f" SHA-256 : {verified['checksum']}")
    return 0


def _save(args) -> int:
    from lanctl.core.projects.save_policy import save_active_project

    result = save_active_project(force=True)
    if not result.saved:
        raise ValueError("no hay un proyecto activo que guardar")
    ok(
        t("LANCTL.UI.STATUS.SAVED"),
        t(
            "LANCTL.UI.DETAIL.VALUE_SAVEMODE_VALUE",
            value0=f"{result.path}",
            value1=f"{result.mode}",
        ),
    )
    return 0


def _import_physical(args) -> int:
    from lanctl.core.project_context import project_identity
    from lanctl.core.projects.physical import import_inventory

    result = import_inventory(args.file, project_identity(load_config()))
    ok(
        t("LANCTL.UI.STATUS.PHYSICAL_INVENTORY"),
        t(
            "LANCTL.UI.SUMMARY.VALUE_ELEMENTS_IMPORTED_SAVE_THE_PROJECT_WITH_PROJECT_SAVE",
            value0=f"{result['records']}",
        ),
    )
    return 0


def _set_active_project(path: str) -> None:
    activate_project_workspace(path)


def _use(args) -> int:
    result = verify_project(args.file)
    from pathlib import Path

    resolved = str(resolve_project_path(args.file, load_config().get("projectsDirectory")))
    _set_active_project(resolved)
    from lanctl.core.plugins import get_plugin_manager

    project_info = inspect_project(resolved)
    get_plugin_manager().events.emit(
        "LANCTL.Project.File.Open",
        {
            "path": resolved,
            "project_id": project_info.get("id"),
        },
    )
    ok(
        t("LANCTL.UI.STATUS.ACTIVE_PROJECT"),
        f"{project_info.get('name') or Path(resolved).stem} | {resolved}",
    )
    print(f" SHA-256 : {result['checksum']}")
    return 0


def _info(args) -> int:
    info = inspect_project(args.file)
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0
    fields = (
        (t("LANCTL.UI.STATUS.PROJECT"), info.get("name")),
        ("DESCRIPCIÓN", info.get("description")),
        ("AUTOR", info.get("author")),
        ("UUID", info.get("id")),
        ("FORMATO", info.get("formatVersion")),
        ("LANCTL", info.get("lanctlVersion")),
        (t("LANCTL.UI.STATUS.CREATED"), info.get("created")),
        (t("LANCTL.UI.STATUS.UPDATED"), info.get("updated")),
        ("DISPOSITIVOS", info.get("devices")),
        ("GRUPOS", info.get("groups")),
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
        ok(
            t("LANCTL.UI.STATUS.VLF_VALID"),
            t(
                "LANCTL.UI.DETAIL.FORMAT_VALUE_VALUE_FILES",
                value0=f"{result['formatVersion']}",
                value1=f"{result['entries']}",
            ),
        )
        print(f" SHA-256 : {result['checksum']}")
        print(t("LANCTL.UI.MESSAGE.SIZE_VALUE_BYTES", value0=f"{result['size']}"))
    return 0


def _list(args) -> int:
    entries = list_project_entries(args.file)
    width = terminal_columns() or 120
    path_width = max(10, width - 27)
    print(
        f"{Style.BRIGHT}{Fore.CYAN}{'PATH':<{path_width}}  {'SIZE':>10}  {'COMPRESSED':>10}{Style.RESET_ALL}"
    )
    print("-" * min(width, path_width + 24))
    for entry in entries:
        print(
            f"{fit_text(entry['path'], path_width):<{path_width}}  "
            f"{entry['size']:>10}  {entry['compressed']:>10}"
        )
    return 0
