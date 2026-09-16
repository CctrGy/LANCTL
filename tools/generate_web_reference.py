from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lanctl import __version__  # noqa: E402
from lanctl.apps.access.manager_cli import build_parser as access_parser  # noqa: E402
from lanctl.apps.ip.interfaces.cli.main import build_parser as ip_parser  # noqa: E402
from lanctl.apps.rack.cli import build_parser as rack_parser  # noqa: E402
from lanctl.apps.wire.cli.main import build_parser as wire_parser  # noqa: E402
from lanctl.bootstrap.lanctl import build_parser as suite_parser  # noqa: E402
from lanctl.bootstrap.lanmon import build_parser as monitor_parser  # noqa: E402

OUTPUT = ROOT / "reference" / "catalog.js"
REPOSITORY = "https://github.com/CctrGy/LANCTL"

ROOTS = (
    (("LANCTL",), suite_parser, False),
    (("LANIP",), lambda: ip_parser(program_name="LANIP"), True),
    (("LANWIRE",), wire_parser, True),
    (("LANRACK",), rack_parser, True),
    (("LANACCESS",), access_parser, True),
    (("LANMON",), monitor_parser, True),
)

CATEGORY_RULES = {
    "project": "Proyectos",
    "plugin": "Plugins y expansiones",
    "extension": "Plugins y expansiones",
    "language": "Configuración",
    "settings": "Configuración",
    "database": "Datos y exportación",
    "history": "Datos y exportación",
    "list": "Inventario y búsqueda",
    "search": "Inventario y búsqueda",
    "scan": "Descubrimiento de red",
    "ephemeral": "Descubrimiento de red",
    "ping": "Diagnóstico de red",
    "monitor": "Monitorización",
    "wol": "Automatización",
    "element": "Inventario y edición",
    "group": "Grupos de comandos",
    "access": "Acceso remoto",
    "credential": "Acceso remoto",
    "protocol": "Acceso remoto",
    "ssh": "Acceso remoto",
    "smb": "Acceso remoto",
    "radmin": "Acceso remoto",
    "terminal": "Acceso remoto",
    "lab": "Laboratorio virtual",
    "demo": "Laboratorio virtual",
    "lanwire": "Cableado y topología",
    "switch": "Infraestructura de red",
}

EXAMPLES = {
    "LANIP": ["lanip --tui", "lanip --help"],
    "LANCTL": ["lanctl --tui", "lanctl lanip --help"],
    "LANIP list": ["lanip list --active", "lanip list --format json"],
    "LANIP scan": ["lanip scan NAS --identify --banners"],
    "LANIP project": ["lanip project status", "lanip project list MiRed.vlf"],
    "LANIP project create": ['lanip project create Casa.vlf --name "Red de casa"'],
    "LANIP project verify": ["lanip project verify Casa.vlf"],
    "LANIP plugin": ["lanip plugin list", "lanip plugin verify extension.lcp"],
    "LANIP plugin install": ["lanip plugin install extension.lcp"],
    "LANIP plugin enable": ["lanip plugin enable extension-id --grant-all"],
    "LANIP plugin pack": ["lanip plugin pack mi-plugin extension.lcp"],
    "LANWIRE": ["lanwire list", "lanwire --tui"],
    "LANRACK": ["lanrack list", "lanrack --tui"],
    "LANACCESS": ["lanaccess list", "lanaccess --tui"],
    "LANMON": ["lanmon status", "lanmon --help"],
}

CONCEPTS = (
    {
        "id": "concept-project-vlf",
        "name": "Proyecto VLF",
        "kind": "concept",
        "category": "Proyectos",
        "group": "Formato de proyecto",
        "description": "Contenedor portable de inventario, configuración, auditoría y hashes.",
        "details": "Los proyectos .vlf permiten guardar, verificar, clonar y trasladar un entorno LANCTL completo.",
        "examples": [
            'lanip project create Casa.vlf --name "Red de casa"',
            "lanip project verify Casa.vlf",
        ],
        "docs": ["VLF.md", "STORAGE.md"],
    },
    {
        "id": "concept-plugin-lcp",
        "name": "Plugin LCP",
        "kind": "concept",
        "category": "Plugins y expansiones",
        "group": "Formato de extensión",
        "description": "Paquete verificable de extensión con manifiesto, permisos y runtimes controlados.",
        "details": "Los paquetes .lcp se validan antes de instalarse y permanecen desactivados hasta conceder sus permisos.",
        "examples": ["lanip plugin install extension.lcp", "lanip plugin permissions extension-id"],
        "docs": ["LCP.md", "SECURITY.md"],
    },
    {
        "id": "concept-command-groups",
        "name": "Grupos de comandos",
        "kind": "concept",
        "category": "Grupos de comandos",
        "group": "Organización del CLI",
        "description": "Árboles de subcomandos que agrupan acciones relacionadas bajo una raíz común.",
        "details": "Usa --help en cualquier nivel para consultar sus acciones, argumentos y opciones disponibles.",
        "examples": ["lanip project --help", "lanip plugin publisher --help"],
        "docs": ["CLI.md", "CLI-REFERENCE.md"],
    },
)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def category_for(path: tuple[str, ...]) -> str:
    if len(path) == 1:
        return "Launchers"
    launcher = path[0]
    if launcher == "LANWIRE":
        return "Cableado y topología"
    if launcher == "LANRACK":
        return "Racks y salas técnicas"
    if launcher == "LANACCESS":
        return "Credenciales y acceso"
    if launcher == "LANMON":
        return "Monitorización"
    for token in path[1:]:
        if token.casefold() in CATEGORY_RULES:
            return CATEGORY_RULES[token.casefold()]
    return "Comandos"


def aliases_by_parser(parser: argparse.ArgumentParser) -> dict[int, list[str]]:
    aliases: dict[int, list[str]] = {}
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        for name, child in action.choices.items():
            aliases.setdefault(id(child), []).append(name)
    return aliases


def parser_tree(parser: argparse.ArgumentParser, path: tuple[str, ...]):
    yield path, parser, ()
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        names = aliases_by_parser(parser)
        seen: set[int] = set()
        for name, child in action.choices.items():
            if id(child) in seen:
                continue
            seen.add(id(child))
            all_names = names[id(child)]
            yield from parser_tree(child, (*path, all_names[0]))


def action_data(action: argparse.Action) -> dict | None:
    if isinstance(action, (argparse._HelpAction, argparse._SubParsersAction)):
        return None
    flags = list(action.option_strings)
    label = ", ".join(flags) if flags else action.dest
    default = None if action.default in (None, argparse.SUPPRESS, False) else str(action.default)
    choices = [str(value) for value in action.choices] if action.choices else []
    return {
        "label": label,
        "flags": flags,
        "required": bool(action.required),
        "metavar": str(action.metavar or ""),
        "choices": choices,
        "default": default,
        "description": action.help or "",
    }


def command_entry(path: tuple[str, ...], parser: argparse.ArgumentParser) -> dict:
    title = " ".join(path)
    actions = [data for action in parser._actions if (data := action_data(action))]
    child_names: list[str] = []
    aliases: list[str] = []
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        names = aliases_by_parser(parser)
        for values in names.values():
            child_names.append(values[0])
            aliases.extend(values[1:])
    description = parser.description or parser.format_usage().strip()
    related_docs = ["CLI-REFERENCE.md", "CLI.md"]
    if "project" in (token.casefold() for token in path):
        related_docs = ["VLF.md", "STORAGE.md", *related_docs]
    elif "plugin" in (token.casefold() for token in path):
        related_docs = ["LCP.md", "SECURITY.md", *related_docs]
    elif path[0] == "LANWIRE":
        related_docs = ["LANWIRE.md", *related_docs]
    elif path[0] == "LANMON" or "monitor" in (token.casefold() for token in path):
        related_docs = ["MONITOR.md", *related_docs]
    return {
        "id": f"command-{slug(title)}",
        "name": path[-1],
        "title": title,
        "kind": "launcher" if len(path) == 1 else "command",
        "category": category_for(path),
        "group": path[0] if len(path) == 1 else " ".join(path[:-1]),
        "launcher": path[0],
        "path": list(path),
        "description": description,
        "usage": parser.format_usage().removeprefix("usage: ").strip(),
        "details": parser.format_help().strip(),
        "aliases": aliases,
        "children": child_names,
        "arguments": actions,
        "examples": EXAMPLES.get(title, [title.casefold() + " --help"]),
        "docs": related_docs,
    }


def first_paragraph(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem.replace("-", " ").title()
    body = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    paragraphs = [
        re.sub(r"\s+", " ", block).strip()
        for block in re.split(r"\n\s*\n", body)
        if block.strip() and not block.lstrip().startswith(("#", "|", "- ", ">"))
    ]
    return title, (paragraphs[0] if paragraphs else f"Documentación sobre {title}.")


def document_entries() -> list[dict]:
    entries = []
    for path in sorted((ROOT / "docs").glob("*.md")):
        title, description = first_paragraph(path)
        entries.append(
            {
                "id": f"doc-{slug(path.stem)}",
                "name": path.name,
                "title": title,
                "kind": "document",
                "category": "Archivos de documentación",
                "group": "docs/",
                "description": description,
                "details": f"Documento mantenido en docs/{path.name}.",
                "examples": [],
                "docs": [path.name],
                "url": f"{REPOSITORY}/blob/main/docs/{path.name}",
            }
        )
    return entries


def generate_data() -> dict:
    os.environ["LANCTL_CANONICAL_HELP"] = "1"
    entries: list[dict] = []
    for path, builder, recursive in ROOTS:
        parsers = parser_tree(builder(), path) if recursive else ((path, builder(), ()),)
        for parser_path, parser, _aliases in parsers:
            entries.append(command_entry(parser_path, parser))
    entries.extend(CONCEPTS)
    entries.extend(document_entries())
    categories = []
    for entry in entries:
        if entry["category"] not in categories:
            categories.append(entry["category"])
    return {
        "meta": {
            "name": "LANCTL Reference",
            "version": __version__,
            "repository": REPOSITORY,
            "entryCount": len(entries),
        },
        "categories": categories,
        "entries": entries,
    }


def generate() -> str:
    payload = json.dumps(generate_data(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"// Generado por tools/generate_web_reference.py. No editar.\nwindow.LANCTL_REFERENCE = {payload};\n"


def main() -> int:
    content = generate()
    if "--check" in sys.argv:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            print(f"Web reference is stale: {OUTPUT}", file=sys.stderr)
            return 1
        print(f"Web reference verified: {OUTPUT}")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"Web reference generated: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
