from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.models import Device


TerminalHandler = Callable[[Device, dict[str, str], dict[str, Any]], int]


def _ssh_terminal(device: Device, credential: dict[str, str], config: dict[str, Any]) -> int:
    from app.protocols.ssh import (
        SshProfile, open_colored_interactive, open_interactive, verify_pinned_host,
    )
    from app.terminals.ssh_color import terminal_theme

    profile = SshProfile.from_options(device.protocol_options.get("ssh", {}))
    native = bool(config.get("nativeTerminal"))
    legacy = (
        verify_pinned_host(device.ip, profile)
        if native else bool(profile.host_key_algorithms or profile.kex_algorithms)
    )
    if legacy:
        print("[ADVERTENCIA] LEGACY SSH limitado a este dispositivo")
    adapter = device.protocol_options.get("ssh", {}).get("terminalAdapter")
    if adapter == "esp32_rack_monitor":
        print("Consola ESP32 del gestor/monitor del rack")
        print("Comandos principales: info, sens read, fan all read, lan show, help")
    if native:
        return open_interactive(device.ip, credential["username"], profile)
    print("Capa de color LANCTL activa | usa --native para OpenSSH directo")
    return open_colored_interactive(
        device.ip,
        credential["username"],
        credential["password"],
        profile,
        theme=terminal_theme(device.protocol_options.get("ssh", {})),
    )


def _tr064_terminal(device: Device, credential: dict[str, str], config: dict[str, Any]) -> int:
    from app.terminals.tr064 import run_tr064_terminal

    return run_tr064_terminal(
        device,
        credential,
        port=int(config.get("tr064Port", 49000)),
    )


TERMINALS: dict[str, TerminalHandler] = {
    "ssh": _ssh_terminal,
    "tr-064": _tr064_terminal,
}


def available_terminals(device: Device) -> list[str]:
    return [protocol for protocol in device.protocols if protocol in TERMINALS]


def open_terminal(
    device: Device,
    protocol: str,
    credential: dict[str, str],
    config: dict[str, Any],
) -> int:
    try:
        handler = TERMINALS[protocol]
    except KeyError as error:
        raise ValueError(f"el protocolo {protocol} no ofrece terminal") from error
    return handler(device, credential, config)
