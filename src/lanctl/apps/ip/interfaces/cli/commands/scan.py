from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import asdict

from colorama import Fore, Style

from lanctl.apps.ip.infrastructure.services.element_scanner import ElementScanner, parse_ports
from lanctl.apps.ip.infrastructure.services.manufacturer import detect_manufacturer
from lanctl.core.config import load_config
from lanctl.core.database import DeviceDatabase
from lanctl.core.layout import fit_text, terminal_columns, wrapped_lines
from lanctl.core.logger import write_log
from lanctl.shared.i18n import t


def register_scan_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "scan",
        help=t("LANCTL.UI.HELP.INSPECT_A_SINGLE_LAN_ELEMENT_IN_DEPTH"),
        description=(
            t(
                "LANCTL.UI.HELP.RESOLVE_AN_ELEMENT_BY_IP_MAC_OR_ALIAS_AND_CHECK_IDENTITY_AVAILABILITY_AND_TCP_PORTS_DOES_NOT_MO"
            )
        ),
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.IP_MAC_OR_ALIAS_REGISTERED_IN_LANCTL"))
    command.add_argument(
        "--ports",
        default="common",
        metavar="LISTA",
        help=t("LANCTL.UI.HELP.PORTS_OR_RANGES_22_80_443_8000_8100_DEFAULT_COMMON"),
    )
    command.add_argument(
        "--all-ports",
        action="store_true",
        help=t("LANCTL.UI.HELP.EXPLICITLY_AUTHORIZE_A_TCP_1_65535_SCAN"),
    )
    command.add_argument(
        "--timeout",
        type=float,
        default=0.5,
        help=t("LANCTL.UI.HELP.MAXIMUM_TIMEOUT_PER_CONNECTION_IN_SECONDS"),
    )
    command.add_argument(
        "--workers",
        type=int,
        default=128,
        help=t("LANCTL.UI.HELP.MAXIMUM_NUMBER_OF_CONCURRENT_CONNECTIONS"),
    )
    command.add_argument(
        "--banners",
        action="store_true",
        help=t("LANCTL.UI.HELP.READ_PASSIVE_BANNERS_DO_NOT_SEND_PROTOCOL_SPECIFIC_PROBES"),
    )
    command.add_argument(
        "--identify",
        action="store_true",
        default=bool(config.get("serviceIdentification", True)),
        help=t("LANCTL.UI.HELP.RECOGNIZE_SERVICES_AND_INFER_DEVICE_TYPE_FROM_EVIDENCE"),
    )
    command.add_argument("--json", action="store_true", help=t("LANCTL.UI.HELP.JSON_OUTPUT"))
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.set_defaults(handler=run_scan)


def _color(value: str, color: str) -> str:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return value
    return f"{Style.BRIGHT}{color}{value}{Style.RESET_ALL}"


def _shown(value) -> str:
    return "-" if value in (None, "", []) else str(value)


def run_scan(args: argparse.Namespace) -> int:
    device = DeviceDatabase(args.database).resolve(args.selector)
    from lanctl.apps.ip.domain.discovery import require_real_target

    require_real_target(device)
    if device.ip in ("", "-"):
        raise ValueError(f"{args.selector} no tiene una IP registrada que pueda escanearse")
    if args.all_ports and args.ports != "common":
        raise ValueError("usa --all-ports o --ports, pero no ambos")
    ports = list(range(1, 65536)) if args.all_ports else parse_ports(args.ports)
    manufacturer = device.manufacturer or detect_manufacturer(device.mac)
    scanner = ElementScanner(timeout=args.timeout, workers=args.workers)
    from lanctl.core.plugins import get_plugin_manager

    plugin_manager = get_plugin_manager()
    scan_id = str(uuid.uuid4())
    event_values = {
        "scan_id": scan_id,
        "target_range": device.ip,
        "running": True,
        "active": True,
        "devices": 0,
    }
    _, decision = plugin_manager.events.emit(
        "LANCTL.Network.Scan.BeforeStart",
        event_values,
        correlation_id=scan_id,
    )
    if not decision.allowed:
        raise ValueError(decision.reason or "el escaneo ha sido cancelado por un complemento")
    plugin_manager.events.emit("LANCTL.Network.Scan.Begin", event_values, correlation_id=scan_id)
    result = scanner.scan(
        device.ip,
        ports,
        banners=args.banners,
        identify=args.identify,
        manufacturer=manufacturer,
    )
    plugin_manager.events.emit(
        "LANCTL.Network.Scan.End",
        {
            "scan_id": scan_id,
            "target_range": device.ip,
            "running": False,
            "active": result.reachable,
            "devices": int(result.reachable),
        },
        correlation_id=scan_id,
    )
    identity_match = (
        None
        if not result.observed_mac or not device.mac
        else result.observed_mac.casefold() == device.mac.casefold()
    )
    write_log(
        f"SCAN element={device.device_id} ip={device.ip} reachable={result.reachable} "
        f"ports={result.scanned_ports} open={len(result.open_ports)}"
    )

    if args.json:
        payload = {
            "element": {
                "deviceId": device.device_id,
                "ip": device.ip,
                "mac": device.mac,
                "alias": device.alias,
                "name": device.name,
                "manufacturer": manufacturer,
                "groups": device.groups,
            },
            "observation": {**asdict(result), "identityMatch": identity_match},
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    state = (
        _color(t("LANCTL.LANGUAGE.FIELD.ACTIVE"), Fore.LIGHTGREEN_EX)
        if result.reachable
        else _color("NO DETECTADO", Fore.LIGHTRED_EX)
    )
    print(f"\n{_color('ELEMENTO', Fore.CYAN)}")
    print(t("LANCTL.UI.DETAIL.STATE_VALUE_2921817C", value0=f"{state}"))
    print(
        t("LANCTL.UI.SUMMARY.REGISTERED_IP_VALUE", value0=f"{_color(device.ip, Fore.LIGHTBLUE_EX)}")
    )
    print(
        t(
            "LANCTL.UI.SUMMARY.REGISTERED_MAC_VALUE",
            value0=f"{_color(_shown(device.mac), Fore.LIGHTMAGENTA_EX)}",
        )
    )
    print(
        t("LANCTL.UI.SUMMARY.OBSERVED_MAC_VALUE_8B6BBDFA", value0=f"{_shown(result.observed_mac)}")
    )
    match_text = (
        t("LANCTL.UI.TEXT.YES")
        if identity_match is True
        else "NO"
        if identity_match is False
        else "-"
    )
    print(t("LANCTL.UI.DETAIL.MATCH_VALUE_67CFE32A", value0=f"{match_text}"))
    print(
        t(
            "LANCTL.UI.DETAIL.ALIAS_NAME_VALUE_VALUE",
            value0=f"{_shown(device.alias)}",
            value1=f"{_shown(device.name)}",
        )
    )
    print(t("LANCTL.UI.DETAIL.MANUFACTURER_VALUE_77F5D6AD", value0=f"{_shown(manufacturer)}"))
    print(
        t(
            "LANCTL.UI.DETAIL.HOSTNAME_VALUE",
            value0=f"{_shown(result.hostname or device.default_name)}",
        )
    )
    print(t("LANCTL.UI.DETAIL.GROUPS_VALUE_CBB70DC6", value0=f"{_shown(', '.join(device.groups))}"))
    print(
        t(
            "LANCTL.UI.DETAIL.LATENCY_TTL_VALUE_MS_VALUE",
            value0=f"{_shown(result.latency_ms)}",
            value1=f"{_shown(result.ttl)}",
        )
    )
    if args.identify:
        identification = result.identification
        print(
            t(
                "LANCTL.UI.MESSAGE.PROBABLE_TYPE_VALUE_1B275E0A",
                value0=f"{_shown(identification.device_type)}",
            )
        )
        print(
            t(
                "LANCTL.UI.DETAIL.CONFIDENCE_VALUE_584F7720",
                value0=f"{_shown(identification.confidence)}",
            )
        )
        print(
            t(
                "LANCTL.UI.DETAIL.EVIDENCE_VALUE_D2013F98",
                value0=f"{_shown('; '.join(identification.evidence))}",
            )
        )

    print(f"\n{_color('PUERTOS TCP ABIERTOS', Fore.CYAN)}")
    if result.open_ports:
        available = terminal_columns()
        banner_width = max(6, *(len(port.product or port.banner) for port in result.open_ports))
        if available:
            banner_width = max(6, min(banner_width, available - 43))
        print(
            f"  {'port':<5}  {'service':<16}  {'confidence':<10}  {'product/banner':<{banner_width}}"
        )
        print(f"  {'-' * 5}  {'-' * 16}  {'-' * 10}  {'-' * banner_width}")
        for port in result.open_ports:
            banner = fit_text(port.product or port.banner or "-", banner_width)
            print(
                f"  {_color(str(port.port).ljust(5), Fore.LIGHTGREEN_EX)}  "
                f"{fit_text(port.service, 16):<16}  {port.confidence:<10}  {banner}"
            )
    else:
        print(t("LANCTL.UI.PROMPT.NONE_DETECTED_IN_THE_EXAMINED_SET"))
    summary = t(
        "LANCTL.UI.MESSAGE.EXAMINED_VALUE_OPEN_VALUE_DURATION_VALUE_S",
        value0=f"{result.scanned_ports}",
        value1=f"{len(result.open_ports)}",
        value2=f"{result.duration:.2f}",
    )
    for index, line in enumerate(wrapped_lines(summary, max(1, (terminal_columns() or 120) - 2))):
        print(("\n  " if index == 0 else "  ") + line)
    if not args.all_ports:
        print(t("LANCTL.UI.PRESENTATION.COMMON_PORTS_SCOPE"))
    return 0 if result.reachable else 1
