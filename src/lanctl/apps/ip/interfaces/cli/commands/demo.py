from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

from lanctl import __version__
from lanctl.core.database import DeviceDatabase
from lanctl.core.file_transaction import atomic_write_json, atomic_write_text
from lanctl.core.projects.vlf import create_project, verify_project


def register_demo_command(commands) -> None:
    command = commands.add_parser(
        "demo",
        help="Genera un recorrido reproducible sin depender de una red real.",
        description=(
            "Crea inventario, proyecto VLF, evidencias, monitorización y un informe "
            "de demostración aislados de los datos del usuario."
        ),
    )
    command.add_argument(
        "--output",
        default="LANCTL-demo",
        metavar="DIRECTORIO",
        help="Directorio donde se guardará el proyecto y el informe.",
    )
    command.add_argument("--force", action="store_true", help="Reemplaza una demo anterior.")
    command.add_argument(
        "--format",
        choices=("json", "html", "all"),
        default="all",
        help="Formato del informe exportado.",
    )
    command.set_defaults(handler=run_demo)


def _sample_devices(stamp: str) -> list[dict]:
    return [
        {
            "IP": "192.168.50.1",
            "MAC": "00:1A:2B:00:00:01",
            "cnf": "O",
            "ALIAS": "GATEWAY",
            "NAME": "Router principal",
            "defaultName": "router-demo.local",
            "manufacturer": "LANCTL Demo Networks",
            "GROUP": ["Infraestructura"],
            "protocols": ["https", "ssh"],
            "discoveryMethods": ["icmp", "arp", "mdns"],
            "lastSeen": stamp,
        },
        {
            "IP": "192.168.50.10",
            "MAC": "00:1A:2B:00:00:10",
            "cnf": "O",
            "ALIAS": "CORE-SW",
            "NAME": "Switch de distribución",
            "defaultName": "switch-core.local",
            "manufacturer": "LANCTL Demo Networks",
            "GROUP": ["Infraestructura"],
            "protocols": ["ssh", "snmp"],
            "discoveryMethods": ["icmp", "arp", "ssdp"],
            "lastSeen": stamp,
        },
        {
            "IP": "192.168.50.20",
            "MAC": "00:1A:2B:00:00:20",
            "cnf": "O",
            "ALIAS": "DEMO-SRV",
            "NAME": "Servidor de presentación",
            "defaultName": "demo-server.local",
            "manufacturer": "LANCTL Demo Systems",
            "GROUP": ["Servidores"],
            "protocols": ["https", "smb", "wol"],
            "discoveryMethods": ["arp", "mdns", "smb"],
            "lastSeen": stamp,
        },
    ]


def _report(devices, project: Path, stamp: str) -> dict:
    identities = []
    for index, device in enumerate(devices):
        evidence = list(device.discovery_methods)
        identities.append(
            {
                "deviceId": device.device_id,
                "ip": device.ip,
                "mac": device.mac,
                "name": device.name,
                "manufacturer": device.manufacturer,
                "confidence": 96 - index * 3,
                "evidence": evidence,
                "explanation": " + ".join(evidence),
            }
        )
    return {
        "schemaVersion": 1,
        "lanctlVersion": __version__,
        "generatedAt": stamp,
        "mode": "reproducible-sample",
        "project": str(project),
        "summary": {
            "devicesDiscovered": len(devices),
            "online": 2,
            "offline": 1,
            "incidents": 1,
        },
        "identities": identities,
        "monitoring": [
            {"device": devices[0].device_id, "presence": "online", "latencyMs": 1.8},
            {"device": devices[1].device_id, "presence": "online", "latencyMs": 2.6},
            {"device": devices[2].device_id, "presence": "offline", "latencyMs": None},
        ],
        "history": [
            {"at": stamp, "event": "demo.discovery.completed", "result": "success"},
            {"at": stamp, "event": "demo.monitor.sampled", "result": "warning"},
            {
                "at": stamp,
                "event": "demo.wol.diagnostic",
                "result": "simulated",
                "target": devices[2].mac,
                "note": "No se enviaron paquetes a la red real.",
            },
        ],
    }


def _render_html(report: dict) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['name'])}</td>"
        f"<td>{html.escape(item['ip'])}</td>"
        f"<td>{item['confidence']}%</td>"
        f"<td>{html.escape(', '.join(item['evidence']))}</td>"
        "</tr>"
        for item in report["identities"]
    )
    return (
        "<!doctype html><html lang='es'><meta charset='utf-8'>"
        "<title>LANCTL Demo Report</title>"
        "<style>body{font:16px system-ui;margin:3rem;color:#172033}"
        "table{border-collapse:collapse;width:100%}th,td{padding:.7rem;border:1px solid #ccd}"
        "th{background:#eaf2ff;text-align:left}</style>"
        f"<h1>LANCTL {html.escape(report['lanctlVersion'])}</h1>"
        "<p>Recorrido reproducible: descubrimiento, identificación, monitorización y WOL.</p>"
        "<table><thead><tr><th>Dispositivo</th><th>IP</th><th>Confianza</th>"
        f"<th>Evidencias</th></tr></thead><tbody>{rows}</tbody></table></html>"
    )


def run_demo(args) -> int:
    output = Path(args.output).expanduser().resolve()
    if output.exists() and any(output.iterdir()) and not args.force:
        raise ValueError(f"el directorio de demo no está vacío: {output}; usa --force")
    output.mkdir(parents=True, exist_ok=True)
    database_path = output / "devices.json"
    groups_path = output / "groups.json"
    project_path = output / "LANCTL-Presentation-Demo.vlf"
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    atomic_write_json(groups_path, [])
    database = DeviceDatabase(str(database_path))
    devices = database.upsert(_sample_devices(stamp))
    config = {
        "database": str(database_path),
        "groups": str(groups_path),
        "credentials": str(output / "credentials.dc"),
        "range": "192.168.50.0/24",
        "dhcpRange": "192.168.50.100-192.168.50.200",
        "discovery": True,
        "scanProfile": "accurate",
        "scanOrder": "ascending",
        "projectSaveMode": "manual",
        "projectSaveIntervalMinutes": 5,
    }
    create_project(
        project_path,
        name="LANCTL Presentation Demo",
        description="Recorrido reproducible para presentación",
        author="LANCTL",
        lan_name="Demo LAN",
        location="Entorno de muestra",
        config=config,
        overwrite=args.force,
    )
    verify_project(project_path)
    report = _report(devices, project_path, stamp)
    if args.format in {"json", "all"}:
        atomic_write_json(output / "demo-report.json", report)
    if args.format in {"html", "all"}:
        atomic_write_text(output / "demo-report.html", _render_html(report))
    print(f"Demo preparada: {output}")
    print(f"Proyecto verificado: {project_path}")
    print(f"Dispositivos: {len(devices)} | monitor: 2 online, 1 offline | WOL: simulado")
    return 0
