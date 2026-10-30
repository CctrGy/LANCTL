from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict
from time import perf_counter

from lanctl.apps.ip.infrastructure.repositories import MemoryDeviceRepository
from lanctl.apps.ip.infrastructure.services.discovery_provider import RealDiscoveryProvider
from lanctl.apps.ip.infrastructure.services.element_scanner import parse_ports, scan_tcp_ports
from lanctl.apps.ip.infrastructure.services.lan_scanner import (
    LanScanner,
    local_ipv4,
    resolve_network,
)
from lanctl.apps.ip.infrastructure.services.scan_profiles import apply_profile
from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.output import write_records
from lanctl.core.progress import ScanProgress
from lanctl.shared.i18n import t


def register_ephemeral_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "ephemeral",
        aliases=["-e"],
        help=t("LANCTL.UI.HELP.SCAN_ACTIVE_HOSTS_WITHOUT_READING_OR_SAVING_ANY_INVENTORY"),
        description=(
            t(
                "LANCTL.UI.HELP.PERFORM_ACTUAL_DISCOVERY_IN_AN_ISOLATED_IN_MEMORY_SESSION_DOES_NOT_OPEN_MODIFY_OR_SAVE_PROJECTS"
            )
        ),
    )
    profiles = command.add_mutually_exclusive_group()
    for name, description in (
        ("fast", "Prioriza un barrido ARP rápido."),
        ("normal", "Combina ICMP, ARP y descubrimiento de servicios."),
        ("accurate", "Añade reintentos y reconocimiento más profundo."),
    ):
        profiles.add_argument(
            f"--{name}", dest="profile", action="store_const", const=name, help=description
        )
    command.add_argument(
        "--range",
        dest="network",
        default=config.get("range"),
        help=t("LANCTL.UI.HELP.CIDR_RANGE_TO_EXPLORE_ONLY_DURING_THIS_EXECUTION"),
    )
    command.add_argument(
        "--resolve-names",
        action="store_true",
        help=t("LANCTL.UI.HELP.RESOLVE_NAMES_WITHOUT_STORING_THEM"),
    )
    command.add_argument(
        "--ports", help=t("LANCTL.UI.HELP.OPTIONAL_TCP_PORTS_FOR_EXAMPLE_22_80_443")
    )
    command.add_argument(
        "--json", action="store_true", help=t("LANCTL.UI.HELP.RETURN_THE_SESSION_AS_JSON")
    )
    command.add_argument(
        "--workers",
        type=int,
        default=config.get("workers", 64),
        help=t("LANCTL.UI.HELP.CONCURRENT_PROBES"),
    )
    command.add_argument(
        "--timeout",
        type=float,
        default=config.get("timeout", 0.8),
        help=t("LANCTL.UI.HELP.BASE_TIMEOUT_PER_PROBE_IN_SECONDS"),
    )
    command.add_argument(
        "--max-hosts",
        type=int,
        default=config.get("maxHosts", 4096),
        help=t("LANCTL.UI.HELP.DEFENSIVE_LIMIT_ON_AUTHORIZED_ADDRESSES"),
    )
    command.add_argument(
        "--scan-order",
        choices=("ascending", "descending", "random"),
        default=config.get("scanOrder", "ascending"),
        help=t("LANCTL.UI.HELP.ADDRESS_EXPLORATION_ORDER"),
    )
    command.set_defaults(
        handler=run_ephemeral,
        profile=config.get("scanProfile", "normal"),
        configured_gateway=config.get("gateway"),
        progress=bool(config.get("progress", True)),
        project_independent=True,
    )


def _active_records(records, scanner: LanScanner):
    active = []
    for device in records:
        methods = scanner.discovery_for(device).split("+")
        confirmed = [method for method in methods if method not in {"-", "BASIC", "CACHE"}]
        if scanner.is_confirmed(device) and confirmed:
            device.discovery_methods = confirmed
            device.last_discovery = "+".join(confirmed)
            active.append(device)
    return active


def run_ephemeral(args: argparse.Namespace) -> int:
    if args.workers < 1 or args.max_hosts < 1:
        raise ValueError("--workers y --max-hosts deben ser mayores que cero")
    if args.timeout <= 0:
        raise ValueError("--timeout debe ser mayor que cero")
    network = resolve_network(args.network)
    own_ip = local_ipv4(network)
    if own_ip not in network:
        raise ValueError(f"la IP local {own_ip} no pertenece al rango efímero {network}")

    profile, timeout, workers = apply_profile(args.profile, args.timeout, args.workers)
    scanner = LanScanner(
        network,
        workers,
        timeout,
        args.max_hosts,
        args.scan_order,
        gateway=args.configured_gateway,
    )
    progress = ScanProgress(args.progress and not args.json)
    started = perf_counter()
    scan_id = str(uuid.uuid4())
    from lanctl.core.plugins import get_plugin_manager

    plugin_manager = get_plugin_manager()
    event = {
        "scan_id": scan_id,
        "target_range": str(network),
        "running": True,
        "active": True,
        "devices": 0,
    }
    _, decision = plugin_manager.events.emit(
        "LANCTL.Network.Scan.BeforeStart", event, correlation_id=scan_id
    )
    if not decision.allowed:
        raise ValueError(decision.reason or "el escaneo efímero fue cancelado por un complemento")
    plugin_manager.events.emit("LANCTL.Network.Scan.Begin", event, correlation_id=scan_id)
    try:
        result = RealDiscoveryProvider(scanner).discover(
            include_unknown=True,
            resolve_names=args.resolve_names or profile.resolve_names,
            discovery=profile.discovery,
            include_arp_cache=False,
            attempts=profile.attempts,
            extra_methods=profile.extra_methods,
            progress=progress,
            registered_total=0,
            registered_identities={},
        )
    finally:
        progress.clear()

    with MemoryDeviceRepository() as repository:
        devices = repository.replace(_active_records(result.devices, scanner))
        plugin_manager.events.emit(
            "LANCTL.Network.Scan.End",
            {
                **event,
                "running": False,
                "active": bool(devices),
                "devices": len(devices),
            },
            correlation_id=scan_id,
        )
        port_map = {}
        if args.ports:
            ports = parse_ports(args.ports)
            for device in devices:
                port_map[device.device_id] = scan_tcp_ports(
                    device.ip, ports, timeout, workers, banners=False, identify=True
                )

        rows = []
        for device in devices:
            row = device.to_dict()
            row["NAME"] = device.default_name or device.name
            row["discovery"] = scanner.discovery_for(device)
            row["responseMs"] = scanner.response_time_for(device)
            row["openPorts"] = (
                ",".join(str(item.port) for item in port_map.get(device.device_id, [])) or "-"
            )
            rows.append(row)

        elapsed = perf_counter() - started
        columns = ["ip", "ms", "mac", "name", "manufacturer", "discovery"]
        if args.ports:
            columns.append("ports")
        if args.json:
            json_devices = []
            for row, device in zip(rows, devices):
                json_devices.append(
                    {
                        "ip": row["IP"],
                        "mac": row["MAC"],
                        "name": row["NAME"],
                        "manufacturer": row["manufacturer"],
                        "discovery": row["discovery"],
                        "responseMs": row["responseMs"],
                        "openPorts": row["openPorts"],
                        "openPortDetails": [
                            asdict(item) for item in port_map.get(device.device_id, [])
                        ],
                    }
                )
            payload = {
                "mode": "ephemeral",
                "network": str(network),
                "profile": profile.name,
                "active": len(rows),
                "saved": 0,
                "duration": round(elapsed, 3),
                "devices": json_devices,
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(t("LANCTL.UI.STATUS.LANIP_EPHEMERAL_SCAN"))
            print(
                t("LANCTL.UI.BLOCK.RESULTS_EXIST_ONLY_DURING_THIS_EXECUTION_AND_WILL_NOT_BE_STORED")
            )
            write_records(
                rows, output_format="table", columns=columns, active_rows=[True] * len(rows)
            )
            ok(
                t("LANCTL.UI.STATUS.EPHEMERAL"),
                t(
                    "LANCTL.UI.MESSAGE.ACTIVE_VALUE_SAVED_0_DURATION_VALUE_S",
                    value0=f"{len(rows)}",
                    value1=f"{elapsed:.2f}",
                ),
            )
    return 0
