from __future__ import annotations

import json
import ipaddress
from pathlib import Path
from app.core.paths import application_path


CONFIG_PATH = application_path("data/als/.config")
DEFAULTS = {
    "database": "data/als/devices.json",
    "groups": "data/als/groups.json",
    "log": "data/als/log",
    "logCleanupEnabled": False,
    "logRetentionDays": 90,
    "credentials": "data/als/.credentials",
    "range": None,
    "dhcpRange": None,
    "tr064Port": 49000,
    "ciscoProfiles": "data/als/cisco_profiles.json",
    "workers": 64,
    "timeout": 0.8,
    "maxHosts": 4096,
    "discovery": "hybrid",
    "scanProfile": "normal",
    "progress": True,
    "serviceIdentification": True,
    "listColumns": [
        "ip", "cnf", "alias", "mac", "name", "group", "description"
    ],
}


def normalize_dhcp_range(value: str) -> str | None:
    normalized = value.strip()
    if normalized.casefold() in ("off", "none", "null", "auto", "-"):
        return None
    parts = [part.strip() for part in normalized.split("-", 1)]
    if len(parts) != 2 or not all(parts):
        raise ValueError(
            "el rango DHCP debe usar INICIO-FIN, "
            "por ejemplo 192.168.1.20-192.168.1.200"
        )
    try:
        start = ipaddress.ip_address(parts[0])
        end = ipaddress.ip_address(parts[1])
    except ValueError as error:
        raise ValueError(f"rango DHCP no válido: {value}") from error
    if not isinstance(start, ipaddress.IPv4Address) or not isinstance(
        end, ipaddress.IPv4Address
    ):
        raise ValueError("el rango DHCP debe contener direcciones IPv4")
    if int(start) > int(end):
        raise ValueError("el inicio del rango DHCP no puede ser mayor que el final")
    return f"{start}-{end}"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULTS.copy()
    try:
        stored = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"configuración JSON no válida: {CONFIG_PATH}") from error
    if not isinstance(stored, dict):
        raise ValueError(f"la configuración debe ser un objeto JSON: {CONFIG_PATH}")
    # Migración de la clave usada por versiones anteriores.
    if "network" in stored and "range" not in stored:
        stored["range"] = stored.pop("network")
    stored.pop("scanColumns", None)
    return {**DEFAULTS, **stored}


def save_config(config: dict) -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(CONFIG_PATH)
    return CONFIG_PATH.resolve()
