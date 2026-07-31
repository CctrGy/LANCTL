from __future__ import annotations

import argparse
from collections import Counter

from colorama import Fore, Style

from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.logger import write_log
from app.plugins.manager import get_plugin_manager


SAFE_ACTIONS = {"inventory.summary"}


def register_declarative_commands(commands: argparse._SubParsersAction) -> None:
    occupied = {str(name).casefold() for name in commands.choices}
    for extension in get_plugin_manager().extensions.list("command"):
        spec = extension.specification
        name = str(spec.get("name", "")).strip().casefold()
        aliases = [str(value).strip().casefold() for value in spec.get("aliases", [])]
        action = str(spec.get("action", "")).casefold()
        if not name or action not in SAFE_ACTIONS:
            raise ValueError(f"comando declarativo no válido en {extension.extension_id}")
        collision = occupied.intersection([name, *aliases])
        if collision:
            raise ValueError(f"comando de plugin duplicado: {', '.join(sorted(collision))}")
        parser = commands.add_parser(name, aliases=aliases, help=str(spec.get("help") or name))
        parser.set_defaults(handler=_run, plugin_extension=extension, plugin_action=action)
        occupied.update([name, *aliases])


def _run(args: argparse.Namespace) -> int:
    extension = args.plugin_extension
    manager = get_plugin_manager()
    try:
        if args.plugin_action == "inventory.summary":
            result = _inventory_summary()
        else:
            raise ValueError(f"acción declarativa no soportada: {args.plugin_action}")
        manager.audit(extension.owner, "COMMAND", extension.extension_id, "OK")
        return result
    except Exception as error:
        manager.audit(extension.owner, "COMMAND", extension.extension_id, "ERROR", str(error))
        raise


def _inventory_summary() -> int:
    devices = DeviceDatabase(load_config()["database"]).load()
    cnf = Counter(device.cnf for device in devices)
    groups = Counter(group for device in devices for group in device.groups)
    protocols = Counter(protocol for device in devices for protocol in device.protocols)
    with_ip = sum(device.ip not in ("", "-") for device in devices)
    with_mac = sum(bool(device.mac) for device in devices)
    print(f"{Style.BRIGHT}{Fore.CYAN}NETWORK INVENTORY SUMMARY{Style.RESET_ALL}")
    print(f" Devices       : {len(devices)}")
    print(f" With IP / MAC : {with_ip} / {with_mac}")
    print(f" CNF O/X/S/-   : {cnf['O']} / {cnf['X']} / {cnf['S']} / {cnf['-']}")
    print(f" Groups        : {', '.join(f'{key}={value}' for key, value in groups.most_common()) or '-'}")
    print(f" Protocols     : {', '.join(f'{key}={value}' for key, value in protocols.most_common()) or '-'}")
    return 0
