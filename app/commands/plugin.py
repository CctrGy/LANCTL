from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from colorama import Fore, Style

from app.core.console import ok
from app.plugins.manager import get_plugin_manager
from app.plugins.package import build_package


def register_plugin_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("plugin", aliases=["plugins", "addon", "addons"], help="Gestiona complementos unificados LANCTL .lcp.")
    actions = command.add_subparsers(dest="plugin_action", metavar="ACCIÓN", required=True)
    actions.add_parser("list", help="Lista complementos instalados.").set_defaults(plugin_handler=_list)
    info = actions.add_parser("info", help="Muestra manifiesto, permisos y estado.")
    info.add_argument("plugin_id", help="Identificador estable del complemento.")
    info.set_defaults(plugin_handler=_info)
    install = actions.add_parser("install", help="Verifica e instala un paquete .lcp desactivado.")
    install.add_argument("file", help="Archivo de paquete con extensión .lcp.")
    install.set_defaults(plugin_handler=_install)
    enable = actions.add_parser("enable", help="Concede permisos y activa un complemento.")
    enable.add_argument("plugin_id", help="Identificador del complemento instalado.")
    enable.add_argument("--grant", nargs="*", default=None, metavar="PERMISO", help="Permisos concretos que se conceden.")
    enable.add_argument("--grant-all", action="store_true", help="Concede todos los permisos solicitados.")
    enable.add_argument("--trust", action="store_true", help="Autoriza código trusted dentro del proceso.")
    enable.set_defaults(plugin_handler=_enable)
    for name, handler, help_text in (
        ("disable", _disable, "Desactiva el complemento."),
        ("reload", _reload, "Recarga un complemento activo."),
        ("uninstall", _uninstall, "Desinstala el complemento."),
    ):
        item = actions.add_parser(name, help=help_text)
        item.add_argument("plugin_id", help="Identificador del complemento instalado.")
        item.set_defaults(plugin_handler=handler)
    verify = actions.add_parser("verify", help="Verifica un .lcp o plugin instalado.")
    verify.add_argument("target", help="Identificador instalado o ruta de un archivo .lcp.")
    verify.set_defaults(plugin_handler=_verify)
    permissions = actions.add_parser("permissions", help="Muestra permisos solicitados y concedidos.")
    permissions.add_argument("plugin_id", help="Identificador del complemento instalado.")
    permissions.set_defaults(plugin_handler=_permissions)
    extensions = actions.add_parser("extensions", help="Lista extensiones para CLI, TUI y futura GUI.")
    extensions.add_argument("--type", help="Filtra por tipo de extensión unificada.")
    extensions.set_defaults(plugin_handler=_extensions)
    pack = actions.add_parser("pack", help="Construye un paquete .lcp desde un directorio.")
    pack.add_argument("directory", help="Directorio fuente que contiene plugin.info.")
    pack.add_argument("output", help="Archivo .lcp de salida.")
    pack.add_argument("--force", action="store_true", help="Sobrescribe el paquete de salida existente.")
    pack.set_defaults(plugin_handler=_pack)
    command.set_defaults(handler=lambda args: args.plugin_handler(args))


def _list(args) -> int:
    values = get_plugin_manager().list()
    print(f"{Style.BRIGHT}{Fore.CYAN}{'ID':<30} {'VERSION':<14} {'STATE':<14} TYPES{Style.RESET_ALL}")
    print("-" * 90)
    for plugin in values:
        print(f"{plugin.manifest.plugin_id:<30} {plugin.manifest.version:<14} {plugin.state.value:<14} {','.join(plugin.manifest.capabilities)}")
    if not values:
        print("No hay complementos instalados.")
    return 0


def _info(args) -> int:
    plugin = get_plugin_manager().get(args.plugin_id)
    data = asdict(plugin.manifest)
    data.update({"state": plugin.state.value, "granted": sorted(plugin.granted), "trusted": plugin.trusted, "error": plugin.error, "path": str(plugin.path)})
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _install(args) -> int:
    plugin = get_plugin_manager().install(args.file)
    ok("PLUGIN INSTALADO", f"{plugin.manifest.plugin_id} {plugin.manifest.version} | desactivado")
    print(" Actívalo con: lanctl plugin enable ID --grant-all")
    return 0


def _enable(args) -> int:
    manager = get_plugin_manager()
    plugin = manager.get(args.plugin_id)
    grants = set(plugin.manifest.permissions) if args.grant_all else (set(args.grant) if args.grant is not None else set(plugin.granted))
    manager.enable(args.plugin_id, grant=grants, trusted=args.trust)
    ok("PLUGIN ACTIVO", args.plugin_id)
    return 0


def _disable(args) -> int:
    get_plugin_manager().disable(args.plugin_id); ok("PLUGIN DESACTIVADO", args.plugin_id); return 0


def _reload(args) -> int:
    get_plugin_manager().reload(args.plugin_id); ok("PLUGIN RECARGADO", args.plugin_id); return 0


def _uninstall(args) -> int:
    get_plugin_manager().uninstall(args.plugin_id); ok("PLUGIN ELIMINADO", args.plugin_id); return 0


def _verify(args) -> int:
    result = get_plugin_manager().verify(args.target)
    manifest = result["manifest"]
    ok("LCP VÁLIDO", f"{manifest.plugin_id} {manifest.version}")
    if result.get("checksum"): print(f" SHA-256 : {result['checksum']}")
    if result.get("signature"): print(f" Firma   : {result['signature']}")
    return 0


def _permissions(args) -> int:
    plugin = get_plugin_manager().get(args.plugin_id)
    granted = set(plugin.granted)
    for permission in plugin.manifest.permissions:
        print(f" {'O' if permission in granted else 'X'}  {permission}")
    return 0


def _extensions(args) -> int:
    values = get_plugin_manager().extensions.list(args.type)
    print(f"{'TYPE':<20} {'ID':<36} OWNER")
    print("-" * 90)
    for item in values: print(f"{item.extension_type:<20} {item.extension_id:<36} {item.owner}")
    return 0


def _pack(args) -> int:
    result = build_package(args.directory, args.output, overwrite=args.force)
    ok("LCP CREADO", result["path"])
    print(f" SHA-256 : {result['checksum']}")
    return 0
