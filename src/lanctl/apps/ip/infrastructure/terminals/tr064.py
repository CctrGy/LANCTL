from __future__ import annotations

import json
import shlex
from collections.abc import Callable

from lanctl.apps.ip.domain.models import Device
from lanctl.core.parser import colorize_help
from lanctl.core.tr064 import Tr064Client
from lanctl.shared.i18n import t, translate_label

HELP = """Comandos TR-064:
  services
  call SERVICIO ACCION [Nombre=Valor ...]
  help
  exit

Por seguridad, ACCION debe comenzar por Get. Esta terminal es de solo lectura."""


def parse_call(parts: list[str]) -> tuple[str, str, dict[str, str]]:
    if len(parts) < 3:
        raise ValueError("usa: call SERVICIO GetACCION [Nombre=Valor ...]")
    service, action = parts[1], parts[2]
    if not action.casefold().startswith("get"):
        raise ValueError("la terminal TR-064 solo permite acciones de consulta Get...")
    arguments: dict[str, str] = {}
    for value in parts[3:]:
        if "=" not in value:
            raise ValueError(f"argumento no válido: {value}; usa Nombre=Valor")
        name, content = value.split("=", 1)
        if not name:
            raise ValueError("el nombre de un argumento no puede estar vacío")
        arguments[name] = content
    return service, action, arguments


def run_tr064_terminal(
    device: Device,
    credential: dict[str, str],
    port: int = 49000,
    input_fn: Callable[[str], str] = input,
) -> int:
    client = Tr064Client(
        device.ip,
        credential["username"],
        credential["password"],
        port=port,
    )
    print(
        t(
            "LANCTL.UI.DETAIL.TR_064_TERMINAL_FOR_VALUE_READ_ONLY",
            value0=f"{device.alias or device.ip}",
        )
    )
    print(t("LANCTL.CLI.HEADER.INTRO"))
    while True:
        try:
            raw = input_fn(f"tr064:{device.alias or device.ip}> ").strip()
        except EOFError:
            print()
            return 0
        if not raw:
            continue
        try:
            parts = shlex.split(raw)
            command = parts[0].casefold()
            if command in ("exit", "quit", "salir"):
                return 0
            if command in ("help", "?"):
                print(colorize_help(translate_label(HELP)), end="")
                continue
            if command == "services":
                for service in client.discover():
                    print(f"{service.service_id or '-'} | {service.service_type}")
                continue
            if command == "call":
                service, action, arguments = parse_call(parts)
                print(
                    json.dumps(
                        client.call(service, action, arguments), indent=2, ensure_ascii=False
                    )
                )
                continue
            print(t("LANCTL.UI.PROMPT.UNKNOWN_COMMAND_TYPE_HELP"))
        except (OSError, ValueError) as error:
            print(f"[ERROR] {error}")
