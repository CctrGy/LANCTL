from __future__ import annotations

import argparse

from lanctl.apps.ip.infrastructure.protocols.ssh import (
    SshProfile,
    arp_mac,
    host_fingerprint,
    open_interactive,
    run_show_command,
    tcp_available,
    verify_pinned_host,
)
from lanctl.core.config import load_config
from lanctl.core.credentials import CredentialStore
from lanctl.core.database import DeviceDatabase
from lanctl.shared.i18n import t


def register_ssh_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "ssh", help=t("LANCTL.UI.HELP.OPEN_SSH_OR_RUN_A_READ_ONLY_SHOW_QUERY")
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.IP_MAC_OR_ALIAS"))
    command.add_argument(
        "action",
        choices=("probe", "fingerprint", "trust", "open", "show"),
        help=t("LANCTL.UI.HELP.SSH_OPERATION"),
    )
    command.add_argument(
        "remote_command",
        nargs="*",
        metavar="COMANDO",
        help=t("LANCTL.UI.HELP.FINGERPRINT_OR_REMOTE_COMMAND_DEPENDING_ON_THE_OPERATION"),
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.add_argument(
        "--store",
        default=config["credentials"],
        help=t("LANCTL.UI.TEXT.ENCRYPTED_CREDENTIAL_STORE"),
    )
    command.add_argument(
        "--host",
        help=t("LANCTL.UI.HELP.CANDIDATE_IP_FOR_PROBE_FINGERPRINT_WITHOUT_CHANGING_THE_DATABASE"),
    )
    command.set_defaults(handler=run_ssh)


def run_ssh(args: argparse.Namespace) -> int:
    device = DeviceDatabase(args.database).resolve(args.selector)
    from lanctl.apps.ip.domain.discovery import require_real_target

    require_real_target(device)
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
        print(t("LANCTL.UI.DETAIL.ELEMENT_VALUE", value0=f"{device.alias or device.ip}"))
        print(t("LANCTL.UI.DETAIL.PROFILE_VALUE", value0=f"{profile_name}"))
        print(
            t("LANCTL.UI.SUMMARY.PROBED_IP_VALUE", value0=f"{host}")
            + (t("LANCTL.UI.VALUE.CANDIDATE") if args.host else "")
        )
        print(
            t(
                "LANCTL.UI.SUMMARY.REGISTERED_MAC_VALUE_7A1F0852",
                value0=f"{device.mac or t('LANCTL.UI.VALUE.UNKNOWN')}",
            )
        )
        print(
            t(
                "LANCTL.UI.SUMMARY.MAC_OBSERVED_IN_ARP_VALUE",
                value0=f"{observed or t('LANCTL.UI.VALUE.UNOBSERVED')}",
            )
        )
        if observed:
            identity_match = "s\u00ed" if observed == device.mac else "NO"
            print(t("LANCTL.UI.MESSAGE.IDENTITY_MATCH_VALUE", value0=f"{identity_match}"))
        if profile_name == "ssh_legacy_cisco_s300":
            expected_oui = device.mac.upper().startswith("5C:71:0D:")
            oui_status = "s\u00ed" if expected_oui else t("LANCTL.UI.VALUE.UNCONFIRMED")
            print(t("LANCTL.UI.MESSAGE.CISCO_IDENTITY_BY_OUI_VALUE", value0=f"{oui_status}"))
        elif profile_name == "ssh_esp32_rack_monitor":
            print(t("LANCTL.UI.PROMPT.REGISTERED_FUNCTION_ESP32_RACK_MANAGER_MONITOR"))
        print(
            f"SSH TCP/{profile.port}: {t('LANCTL.UI.VALUE.AVAILABLE') if available else t('LANCTL.UI.VALUE.UNAVAILABLE')}"
        )
        return 0 if available else 1
    if args.action == "fingerprint":
        fingerprint, legacy = host_fingerprint(host, profile)
        print(fingerprint)
        print(
            t(
                "LANCTL.UI.DETAIL.MODE_VALUE",
                value0=f"{('LEGACY SSH' if legacy else 'SSH moderno')}",
            )
        )
        print(t("LANCTL.UI.PROMPT.THE_FINGERPRINT_WAS_ONLY_QUERIED_IT_HAS_NOT_BEEN_SAVED_YET"))
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
        print(
            t(
                "LANCTL.UI.MESSAGE.FINGERPRINT_PINNED_FOR_VALUE_VALUE",
                value0=f"{device.alias or device.ip}",
                value1=f"{fingerprint}",
            )
        )
        negotiation = "LEGACY SSH activo" if legacy else "negociaci\u00f3n moderna"
        print(t("LANCTL.UI.DETAIL.WARNING_VALUE", value0=f"{negotiation}"))
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
        print(t("LANCTL.UI.PRESENTATION.LEGACY_SSH_WARNING"))
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
