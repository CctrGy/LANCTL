from __future__ import annotations

import argparse

from app.core.config import load_config
from app.core.credentials import CredentialStore
from app.core.database import DeviceDatabase
from app.protocols.ssh import (
    SshProfile,
    arp_mac,
    host_fingerprint,
    open_interactive,
    run_show_command,
    tcp_available,
    verify_pinned_host,
)


def register_ssh_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "ssh", help="Abre SSH o ejecuta una consulta show de solo lectura."
    )
    command.add_argument("selector", help="IP, MAC o alias.")
    command.add_argument("action", choices=("probe", "fingerprint", "trust", "open", "show"), help="Operación SSH.")
    command.add_argument("remote_command", nargs="*", metavar="COMANDO", help="Huella o comando remoto, según la operación.")
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.add_argument("--store", default=config["credentials"], help="Almacén cifrado de credenciales.")
    command.add_argument(
        "--host", help="IP candidata para probe/fingerprint, sin modificar la base de datos."
    )
    command.set_defaults(handler=run_ssh)


def run_ssh(args: argparse.Namespace) -> int:
    device = DeviceDatabase(args.database).resolve(args.selector)
    if "ssh" not in device.protocols:
        raise ValueError(f"{device.alias or device.ip} no tiene SSH configurado")
    profile = SshProfile.from_options(device.protocol_options.get("ssh", {}))
    host = args.host or device.ip
    if args.host and args.action not in ("probe", "fingerprint"):
        raise ValueError("--host solo se permite con probe o fingerprint")
    if args.action == "probe":
        options = device.protocol_options.get("ssh", {})
        profile_name = str(options.get("profile", "ssh_generico"))
        observed = arp_mac(host)
        available = tcp_available(host, profile.port)
        print(f"Elemento: {device.alias or device.ip}")
        print(f"Perfil: {profile_name}")
        print(f"IP comprobada: {host}" + (" (candidata, no guardada)" if args.host else ""))
        print(f"MAC registrada: {device.mac or 'desconocida'}")
        print(f"MAC observada en ARP: {observed or 'no observada'}")
        if observed:
            identity_match = "s\u00ed" if observed == device.mac else "NO"
            print(f"Coincidencia de identidad: {identity_match}")
        if profile_name == "ssh_legacy_cisco_s300":
            expected_oui = device.mac.upper().startswith("5C:71:0D:")
            oui_status = "s\u00ed" if expected_oui else "no/no confirmada"
            print(f"Identidad Cisco por OUI: {oui_status}")
        elif profile_name == "ssh_esp32_rack_monitor":
            print("Funci\u00f3n registrada: gestor/monitor del rack ESP32")
        print(f"SSH TCP/{profile.port}: {'disponible' if available else 'no disponible'}")
        return 0 if available else 1
    if args.action == "fingerprint":
        fingerprint, legacy = host_fingerprint(host, profile)
        print(fingerprint)
        print(f"Modo: {'LEGACY SSH' if legacy else 'SSH moderno'}")
        print("La huella solo se ha consultado; todav\u00eda no est\u00e1 guardada.")
        return 0
    if args.action == "trust":
        fingerprint = " ".join(args.remote_command).strip()
        if not fingerprint.startswith("SHA256:"):
            raise ValueError("indica una huella SHA256:... obtenida con ssh fingerprint")
        current, legacy = host_fingerprint(device.ip, profile)
        if fingerprint != current:
            raise ValueError(f"la huella indicada no coincide con la presentada: {current}")
        options = dict(device.protocol_options.get("ssh", {}))
        options["hostFingerprint"] = fingerprint
        DeviceDatabase(args.database).configure_protocol(args.selector, "ssh", options)
        print(f"Huella fijada para {device.alias or device.ip}: {fingerprint}")
        negotiation = "LEGACY SSH activo" if legacy else "negociaci\u00f3n moderna"
        print(f"Advertencia: {negotiation}")
        return 0
    reference = device.credentials.get("ssh")
    if not reference:
        raise ValueError(
            f"{device.alias or device.ip} no tiene credencial SSH; ejecuta "
            f"run credential {device.alias or device.ip} set ssh -user USUARIO"
        )
    credential = CredentialStore(args.store).get(reference)
    legacy = verify_pinned_host(device.ip, profile)
    if legacy:
        print("[ADVERTENCIA] LEGACY SSH limitado a este dispositivo")
    if args.action == "open":
        if args.remote_command:
            raise ValueError("ssh open no acepta un comando remoto")
        return open_interactive(device.ip, credential["username"], profile)
    command = " ".join(args.remote_command).strip()
    if not command:
        raise ValueError("indica una consulta, por ejemplo: ssh SWITCH show show system")
    print(
        run_show_command(
            device.ip,
            credential["username"],
            credential["password"],
            profile,
            command,
        )
    )
    return 0
