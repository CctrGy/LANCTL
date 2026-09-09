from __future__ import annotations

import ipaddress
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lanctl.apps.ip.domain.models import normalize_mac
from lanctl.core.file_transaction import atomic_write_json, load_json_unlocked, locked_file
from lanctl.core.paths import application_path

SCHEMA_VERSION = 1
PROFILES = ("home", "office", "datacenter", "industrial", "chaotic")
KINDS = {
    "home": ("gateway", "access-point", "nas", "mobile", "workstation", "iot"),
    "office": ("gateway", "switch", "access-point", "printer", "server", "workstation", "voip"),
    "datacenter": ("router", "switch", "server", "storage", "hypervisor"),
    "industrial": ("gateway", "plc", "hmi", "camera", "sensor"),
    "chaotic": ("unknown", "iot", "server", "workstation"),
}


def _mac(rng: random.Random, local: bool = False) -> str:
    first = rng.randrange(256)
    first = (first | 2) if local else (first & 0xFC)
    return ":".join(f"{value:02X}" for value in (first, *(rng.randrange(256) for _ in range(5))))


def validate_scenario(value: dict[str, Any]) -> dict[str, Any]:
    if int(value.get("schemaVersion", 0)) != SCHEMA_VERSION:
        raise ValueError("versión de escenario LANLAB no compatible")
    network = ipaddress.ip_network(str(value.get("cidr", "")), strict=False)
    if not isinstance(network, ipaddress.IPv4Network):
        raise ValueError("LANLAB solo admite IPv4")
    devices = value.get("devices")
    if not isinstance(devices, list) or len(devices) > min(network.num_addresses - 2, 4096):
        raise ValueError("cantidad de dispositivos no válida para el CIDR")
    ips: set[str] = set()
    macs: set[str] = set()
    allow_duplicates = str(value.get("profile", "")) == "chaotic" or bool(
        value.get("allowDuplicates")
    )
    for item in devices:
        ip = str(ipaddress.IPv4Address(item["ip"]))
        if ipaddress.IPv4Address(ip) not in network:
            raise ValueError(f"IP fuera del escenario: {ip}")
        mac = normalize_mac(str(item["mac"]))
        if not allow_duplicates and (ip in ips or mac in macs):
            raise ValueError("IP o MAC duplicada")
        ips.add(ip)
        macs.add(mac)
    return value


def generate_scenario(
    *,
    name: str,
    cidr: str = "192.0.2.0/24",
    profile: str = "home",
    devices: int = 20,
    seed: int = 1,
    active_percent: float = 80.0,
    dhcp_percent: float = 70.0,
    mode: str = "snapshot",
) -> dict[str, Any]:
    profile = profile.casefold()
    if profile not in PROFILES:
        raise ValueError(f"perfil desconocido: {profile}")
    if mode not in ("snapshot", "timeline", "chaos"):
        raise ValueError("tipo de escenario debe ser snapshot, timeline o chaos")
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = list(network.hosts())
    if devices < 1 or devices > min(len(hosts), 4096):
        raise ValueError("cantidad de dispositivos fuera de límites")
    rng = random.Random(seed)
    selected = rng.sample(hosts, devices)
    rows = []
    for index, address in enumerate(selected, 1):
        kind = rng.choice(KINDS[profile])
        active = rng.random() * 100 < active_percent
        services = {
            "gateway": [53, 80],
            "server": [22, 443],
            "nas": [22, 445],
            "printer": [80, 9100],
            "plc": [502],
            "hmi": [80],
        }.get(kind, [])
        rows.append(
            {
                "id": f"sim-{index:04d}",
                "ip": str(address),
                "mac": _mac(rng, profile == "chaotic" and rng.random() < 0.4),
                "active": active,
                "cnf": "X",
                "alias": f"{kind.upper().replace('-', '_')}_{index}",
                "name": f"{kind}-{index}",
                "hostname": f"{kind}-{index}.lab",
                "group": profile.upper(),
                "description": f"{kind} simulado"[:42],
                "manufacturer": "LANLAB",
                "kind": kind,
                "confidence": round(rng.uniform(0.55, 0.99), 2),
                "evidence": ["scenario"],
                "methods": ["SIMULATED", "ICMP"] if active else ["SIMULATED"],
                "ttl": rng.choice((32, 64, 128, 255)),
                "latencyMs": round(rng.uniform(0.3, 80), 2),
                "lossPercent": round(rng.uniform(0, 8), 1),
                "assignment": "dhcp" if rng.random() * 100 < dhcp_percent else "static",
                "ports": [
                    {
                        "port": port,
                        "state": "open",
                        "service": {
                            22: "ssh",
                            53: "dns",
                            80: "http",
                            443: "https",
                            445: "smb",
                            502: "modbus",
                            9100: "printer",
                        }.get(port, "unknown"),
                        "banner": "LANLAB simulated",
                    }
                    for port in services
                ],
                "credentialRef": "SIMULATED-ONLY",
            }
        )
    events = []
    if mode in ("timeline", "chaos"):
        for index in range(max(1, devices // 5)):
            target = rng.choice(rows)
            events.append(
                {
                    "at": (index + 1) * 30,
                    "action": rng.choice(("online", "offline", "latency")),
                    "deviceId": target["id"],
                    "value": round(rng.uniform(100, 1000), 1),
                }
            )
    scenario = {
        "schemaVersion": SCHEMA_VERSION,
        "id": str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"lanlab:{name}:{seed}:{cidr}:{profile}:{devices}")
        ),
        "name": name,
        "type": mode,
        "cidr": str(network),
        "profile": profile,
        "seed": seed,
        "created": datetime.now(timezone.utc).isoformat(),
        "clock": 0.0,
        "active": False,
        "allowDuplicates": profile == "chaotic",
        "devices": rows,
        "events": events,
        "metadata": {"source": "simulated", "provider": "lanctl.lab.network-emulator"},
    }
    return validate_scenario(scenario)


class LabRepository:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = application_path(root or "data/lc/plugin-storage/lanctl.lab.network-emulator")
        self.index = self.root / "state.json"

    def path(self, name: str) -> Path:
        safe = "".join(char for char in name if char.isalnum() or char in "-_")
        if not safe:
            raise ValueError("nombre de escenario no válido")
        return self.root / "scenarios" / f"{safe}.json"

    def save(self, scenario: dict[str, Any]) -> Path:
        validate_scenario(scenario)
        return atomic_write_json(self.path(str(scenario["name"])), scenario, sort_keys=True)

    def load(self, name: str) -> dict[str, Any]:
        path = self.path(name)
        if not path.is_file():
            raise ValueError(f"escenario no encontrado: {name}")
        with locked_file(path):
            return validate_scenario(load_json_unlocked(path, dict))

    def names(self) -> list[str]:
        return [path.stem for path in sorted((self.root / "scenarios").glob("*.json"))]

    def set_active(self, name: str | None) -> None:
        if name:
            self.load(name)
        atomic_write_json(self.index, {"schemaVersion": 1, "activeScenario": name})

    def active_name(self) -> str | None:
        if not self.index.exists():
            return None
        with locked_file(self.index):
            return load_json_unlocked(self.index, dict).get("activeScenario")

    def active(self) -> dict[str, Any] | None:
        name = self.active_name()
        return self.load(name) if name else None
