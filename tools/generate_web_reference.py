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


def compatibility() -> dict[str, str]:
    """Versión contra la que se verificó una entrada del catálogo.

    Las entradas podrán añadir `since`, `until` u `only` cuando exista un
    historial verificable; no se inventan límites para comandos anteriores.
    """
    return {"verified": __version__}


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

WORKFLOWS = (
    {
        "id": "workflow-project-create-save",
        "title": "Crear y guardar un proyecto VLF",
        "summary": "Prepara un proyecto aislado, añade el inventario y verifica el archivo antes de compartirlo.",
        "level": "Inicial",
        "time": "5-10 min",
        "docs": ["VLF.md", "STORAGE.md"],
        "related": [
            "command-lanip-project-create",
            "command-lanip-project-save",
            "command-lanip-project-verify",
        ],
        "steps": [
            {
                "title": "Elegir el directorio",
                "description": "Opcionalmente define dónde se guardarán los proyectos.",
                "commands": ["lanip settings --projects-directory D:\\ProyectosLANCTL"],
            },
            {
                "title": "Crear el proyecto",
                "description": "Crea un VLF vacío con un nombre reconocible.",
                "commands": ['lanip project create Casa.vlf --name "Red de casa"'],
            },
            {
                "title": "Activarlo",
                "description": "Selecciona el proyecto como destino del inventario y la auditoría.",
                "commands": ["lanip project use Casa.vlf", "lanip project status"],
            },
            {
                "title": "Descubrir e inventariar",
                "description": "Escanea la LAN y revisa los dispositivos antes de guardar.",
                "commands": ["lanip list --normal", "lanip list --active"],
            },
            {
                "title": "Guardar y verificar",
                "description": "Persiste los cambios y comprueba estructura, hashes y SQLite.",
                "commands": ["lanip project save", "lanip project verify Casa.vlf"],
            },
        ],
    },
    {
        "id": "workflow-plugin-import",
        "title": "Importar y activar un plugin LCP",
        "summary": "Verifica el paquete, inspecciona permisos y actívalo de forma explícita.",
        "level": "Intermedio",
        "time": "5 min",
        "docs": ["LCP.md", "SECURITY.md"],
        "related": [
            "command-lanip-plugin-verify",
            "command-lanip-plugin-install",
            "command-lanip-plugin-enable",
        ],
        "steps": [
            {
                "title": "Verificar el paquete",
                "description": "Comprueba estructura, manifiesto, firma y seguridad antes de instalar.",
                "commands": ["lanip plugin verify MiPlugin.lcp"],
            },
            {
                "title": "Instalar desactivado",
                "description": "Importa el LCP sin ejecutar todavía su código.",
                "commands": ["lanip plugin install MiPlugin.lcp"],
            },
            {
                "title": "Revisar manifiesto y permisos",
                "description": "Consulta identidad, capacidades y permisos solicitados.",
                "commands": ["lanip plugin info plugin-id", "lanip plugin permissions plugin-id"],
            },
            {
                "title": "Conceder y activar",
                "description": "Concede solamente los permisos necesarios. --grant-all debe reservarse para paquetes confiables.",
                "commands": ["lanip plugin enable plugin-id --grant permiso.necesario"],
            },
            {
                "title": "Comprobar el resultado",
                "description": "Confirma que el plugin aparece activo y revisa sus extensiones registradas.",
                "commands": ["lanip plugin list", "lanip plugin extensions"],
            },
        ],
    },
    {
        "id": "workflow-lan-environment",
        "title": "Configurar el entorno de la LAN",
        "summary": "Define red, DHCP, descubrimiento y perfil de escaneo antes de inventariar.",
        "level": "Inicial",
        "time": "10 min",
        "docs": ["CONFIGURATION.md", "CLI.md"],
        "related": ["command-lanip-settings", "command-lanip-list", "command-lanip-ephemeral"],
        "steps": [
            {
                "title": "Identificar la red",
                "description": "Obtén el CIDR y el rango DHCP desde tu router o administrador.",
                "commands": ["ipconfig  # Windows", "ip address  # Linux"],
            },
            {
                "title": "Guardar el rango LAN",
                "description": "Configura la red autorizada que LANCTL puede explorar.",
                "commands": ["lanip settings --range 192.168.1.0/24"],
            },
            {
                "title": "Definir DHCP",
                "description": "Separa direcciones dinámicas de equipos con IP fija.",
                "commands": ["lanip settings --dhcp-range 192.168.1.100-192.168.1.200"],
            },
            {
                "title": "Elegir descubrimiento",
                "description": "Hybrid combina ICMP y ARP; normal es el perfil equilibrado.",
                "commands": [
                    "lanip settings --discovery hybrid --scan-profile normal --progress on"
                ],
            },
            {
                "title": "Probar sin persistencia",
                "description": "Valida primero el alcance mediante una sesión efímera.",
                "commands": ["lanip ephemeral --normal --range 192.168.1.0/24"],
            },
            {
                "title": "Crear el inventario",
                "description": "Cuando el resultado sea correcto, ejecuta el escaneo persistente.",
                "commands": ["lanip list --normal --active"],
            },
        ],
    },
    {
        "id": "workflow-ssh-credentials",
        "title": "Configurar credenciales y conexión SSH",
        "summary": "Asocia el protocolo, guarda el secreto cifrado y valida la huella antes de abrir una sesión.",
        "level": "Intermedio",
        "time": "10 min",
        "docs": ["ACCESS.md", "SECURITY.md"],
        "related": ["command-lanip-protocol", "command-lanip-credential", "command-lanip-ssh"],
        "steps": [
            {
                "title": "Localizar el dispositivo",
                "description": "Usa alias, IP o MAC y confirma que se trata del equipo correcto.",
                "commands": ["lanip search NAS", "lanip call NAS --json"],
            },
            {
                "title": "Configurar SSH",
                "description": "Registra el puerto del servicio. Cambia 22 si el equipo utiliza otro.",
                "commands": ["lanip protocol NAS configure ssh --port 22"],
            },
            {
                "title": "Guardar la credencial",
                "description": "LANCTL solicitará la contraseña mediante entrada segura y no la mostrará.",
                "commands": ["lanip credential NAS set ssh --username administrador"],
            },
            {
                "title": "Comprobar y leer la huella",
                "description": "Verifica conectividad y compara la huella con la indicada por el equipo.",
                "commands": ["lanip ssh NAS probe", "lanip ssh NAS fingerprint"],
            },
            {
                "title": "Confiar y conectar",
                "description": "Solo confía en la huella después de validarla por un canal independiente.",
                "commands": ["lanip ssh NAS trust SHA256:HUELLA", "lanip ssh NAS open"],
            },
        ],
    },
    {
        "id": "workflow-remote-access",
        "title": "Habilitar acceso remoto a LANCTL",
        "summary": "Inicializa usuarios y limita SSH/HTTPS a una dirección y un CIDR autorizados.",
        "level": "Avanzado",
        "time": "15 min",
        "docs": ["ACCESS.md", "ENTERPRISE.md"],
        "related": ["command-lanip-access", "command-lanip-settings"],
        "steps": [
            {
                "title": "Inicializar",
                "description": "Crea la estructura local sin exponer todavía ningún servicio.",
                "commands": ["lanip access init"],
            },
            {
                "title": "Configurar el enlace",
                "description": "Usa una IP LAN concreta y nunca publiques directamente el servicio en Internet.",
                "commands": [
                    "lanip access configure ssh --bind 192.168.1.31 --cidr 192.168.1.0/24 --port 2222"
                ],
            },
            {
                "title": "Crear un usuario",
                "description": "Asigna el rol mínimo necesario.",
                "commands": ["lanip access user add operador --role operator"],
            },
            {
                "title": "Validar antes de activar",
                "description": "Revisa configuración y estado desde el propio nodo.",
                "commands": ["lanip access status --json"],
            },
            {
                "title": "Probar desde otro equipo",
                "description": "Conecta desde un host dentro del CIDR permitido y conserva los logs de la prueba.",
                "commands": ["ssh -p 2222 operador@192.168.1.31"],
            },
        ],
    },
    {
        "id": "workflow-monitor-project",
        "title": "Monitorizar un proyecto",
        "summary": "Comprueba el proyecto, inicia una sesión controlada y revisa sus incidencias.",
        "level": "Intermedio",
        "time": "10 min",
        "docs": ["MONITOR.md", "VLF.md"],
        "related": ["command-lanip-monitor", "command-lanip-project-verify"],
        "steps": [
            {
                "title": "Verificar el proyecto",
                "description": "No monitorices un contenedor dañado o de procedencia desconocida.",
                "commands": ["lanip project verify Oficina.vlf"],
            },
            {
                "title": "Activarlo",
                "description": "Selecciona el inventario que se observará.",
                "commands": ["lanip project use Oficina.vlf"],
            },
            {
                "title": "Ejecutar una comprobación",
                "description": "Empieza con una pasada única antes de crear una sesión prolongada.",
                "commands": ["lanip monitor once --type presence"],
            },
            {
                "title": "Iniciar una sesión temporal",
                "description": "Ajusta duración e intervalo al tamaño de la red.",
                "commands": ["lanip monitor start --mode temporary --duration 1h --interval 60"],
            },
            {
                "title": "Revisar resultados",
                "description": "Consulta sesiones e incidencias y detén la monitorización al terminar.",
                "commands": [
                    "lanip monitor session list",
                    "lanip monitor incidents",
                    "lanip monitor stop",
                ],
            },
        ],
    },
    {
        "id": "workflow-backup-restore",
        "title": "Crear y verificar una copia de seguridad",
        "summary": "Exporta los datos, verifica el ZIP y practica una restauración controlada.",
        "level": "Inicial",
        "time": "5 min",
        "docs": ["STORAGE.md", "TROUBLESHOOTING.md"],
        "related": ["command-lanip-database"],
        "steps": [
            {
                "title": "Diagnosticar",
                "description": "Resuelve problemas existentes antes de crear la copia.",
                "commands": ["lanip database --diagnose"],
            },
            {
                "title": "Exportar",
                "description": "Crea un archivo portable en una ubicación con espacio suficiente.",
                "commands": ["lanip database --export LANCTL-backup.zip"],
            },
            {
                "title": "Verificar",
                "description": "Comprueba estructura y hashes inmediatamente.",
                "commands": ["lanip database --verify LANCTL-backup.zip"],
            },
            {
                "title": "Guardar fuera del equipo",
                "description": "Conserva otra copia en un medio o ubicación independiente.",
                "commands": [],
            },
            {
                "title": "Restaurar solo cuando sea necesario",
                "description": "Revisa el destino y conserva los datos actuales antes de confirmar.",
                "commands": [
                    "lanip database --import LANCTL-backup.zip",
                    "lanip database --restore ARCHIVO.bak --yes",
                ],
            },
        ],
    },
    {
        "id": "workflow-new-device",
        "title": "Añadir y documentar un dispositivo",
        "summary": "Descubre un equipo, confirma su identidad y completa nombre, grupo y protocolos.",
        "level": "Inicial",
        "time": "5 min",
        "docs": ["CLI.md", "CONFIGURATION.md"],
        "related": ["command-lanip-scan", "command-lanip-element", "command-lanip-group"],
        "steps": [
            {
                "title": "Escanear el objetivo",
                "description": "Confirma disponibilidad, identidad y servicios sin modificarlo.",
                "commands": ["lanip scan 192.168.1.50 --identify --banners"],
            },
            {
                "title": "Revisar el registro",
                "description": "Consulta la información capturada antes de editar.",
                "commands": ["lanip call 192.168.1.50 --json"],
            },
            {
                "title": "Asignar identidad legible",
                "description": "Añade nombre, alias y descripción en una operación validada.",
                "commands": [
                    'lanip element 192.168.1.50 -name Servidor -alias NAS -description "Almacenamiento principal"'
                ],
            },
            {
                "title": "Clasificar",
                "description": "Crea el grupo si no existe y añade el dispositivo.",
                "commands": ["lanip group SERVIDORES -new", "lanip group SERVIDORES -add NAS"],
            },
            {
                "title": "Registrar protocolos",
                "description": "Añade únicamente servicios que hayas confirmado.",
                "commands": ["lanip element NAS -protocol ssh"],
            },
        ],
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
        "compatibility": compatibility(),
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
                "compatibility": compatibility(),
            }
        )
    return entries


def generate_data() -> dict:
    variables = ("LANCTL_CANONICAL_HELP", "LOGNAME", "USER", "LNAME", "USERNAME")
    previous = {name: os.environ.get(name) for name in variables}
    try:
        os.environ["LANCTL_CANONICAL_HELP"] = "1"
        for variable in variables[1:]:
            os.environ[variable] = "user"
        entries: list[dict] = []
        for path, builder, recursive in ROOTS:
            parsers = parser_tree(builder(), path) if recursive else ((path, builder(), ()),)
            for parser_path, parser, _aliases in parsers:
                entries.append(command_entry(parser_path, parser))
        entries.extend({**entry, "compatibility": compatibility()} for entry in CONCEPTS)
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
            "workflows": [{**workflow, "compatibility": compatibility()} for workflow in WORKFLOWS],
        }
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


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
