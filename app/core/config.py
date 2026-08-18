from __future__ import annotations

import ipaddress
import json
import os
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.core.file_transaction import atomic_write_json, locked_file, transactional_file
from app.core.paths import application_path

CONFIG_PATH = application_path("data/lc/.config")
DEFAULTS = {
    "database": "data/lc/devices.json",
    "groups": "data/lc/groups.json",
    "log": "data/lc/log",
    "programLog": "data/lc/log",
    "activeProject": None,
    "projectSaveMode": "manual",
    "projectSaveIntervalMinutes": 5,
    # `None` conserva una ruta portable y evita vincular la configuración al
    # usuario que la creó.
    "projectsDirectory": None,
    "plugins": "data/lc/plugins",
    "pluginRegistry": "data/lc/plugins.registry",
    "pluginSafeMode": False,
    "language": "en",
    "languagesDirectory": "data/lc/languajes",
    "iconsDirectory": "data/lc/icons",
    "logCleanupEnabled": False,
    "logRetentionDays": 90,
    "credentials": "data/lc/.credentials",
    "range": None,
    "dhcpRange": None,
    "tr064Port": 49000,
    "radminViewer": None,
    "wol": {"port": 9, "repeat": 3, "interval": 0.5, "wait": 60, "method": "auto"},
    "wolSequences": "data/lc/wol-sequences.json",
    "monitorRuntime": "data/lc/monitor-sessions.json",
    "monitorIncidents": "data/lc/monitor-incidents.json",
    "monitorLock": "data/lc/monitor.lock",
    "accessConfig": "data/lc/access/config.json",
    "accessUsers": "data/lc/access/users.json",
    "remoteAccessEnabled": False,
    "remoteAccessBind": "",
    "remoteAccessCidr": "",
    "remoteAccessPort": 2222,
    "remoteAccessPasswordAuthentication": False,
    "remoteAccessBackend": "service",
    "remoteAccessForcedView": "off",
    "monitorDatabase": "data/lc/monitor.db",
    "monitorProfiles": "data/lc/monitor-profiles.json",
    "monitorAssignments": "data/lc/monitor-assignments.json",
    "monitor": {
        "enabled": False,
        "profile": "normal",
        "mode": "permanent",
        "authority": "observe",
        "intervals": {
            "criticalDevices": 15,
            "deviceStatus": 60,
            "networkDiscovery": 300,
            "serviceScan": 1800,
            "fullScan": 86400,
        },
        "workers": 32,
        "timeout": 0.8,
        "scanOrder": "ascending",
        "failureThreshold": 3,
        "recoveryThreshold": 2,
        "retention": {
            "rawSamples": "24h",
            "fiveMinuteAggregates": "30d",
            "hourlyAggregates": "365d",
            "events": "permanent",
        },
    },
    "smbStorage": "data/lc/plugin-storage",
    "ciscoProfiles": "data/lc/cisco_profiles.json",
    "workers": 64,
    "timeout": 0.8,
    "maxHosts": 4096,
    "discovery": "hybrid",
    "scanProfile": "normal",
    "scanOrder": "ascending",
    "progress": True,
    "serviceIdentification": True,
    "listColumns": ["ip", "cnf", "alias", "mac", "name", "group", "description"],
}


def normalize_dhcp_range(value: str) -> str | None:
    normalized = value.strip()
    if normalized.casefold() in ("off", "none", "null", "auto", "-"):
        return None
    parts = [part.strip() for part in normalized.split("-", 1)]
    if len(parts) != 2 or not all(parts):
        raise ValueError(
            "el rango DHCP debe usar INICIO-FIN, por ejemplo 192.168.1.20-192.168.1.200"
        )
    try:
        start = ipaddress.ip_address(parts[0])
        end = ipaddress.ip_address(parts[1])
    except ValueError as error:
        raise ValueError(f"rango DHCP no válido: {value}") from error
    if not isinstance(start, ipaddress.IPv4Address) or not isinstance(end, ipaddress.IPv4Address):
        raise ValueError("el rango DHCP debe contener direcciones IPv4")
    if int(start) > int(end):
        raise ValueError("el inicio del rango DHCP no puede ser mayor que el final")
    return f"{start}-{end}"


def load_config() -> dict:
    """Lee una instantánea atómica sin crear archivos ni locks.

    Los escritores usan ``os.replace``, por lo que un lector siempre observa
    el JSON anterior o el nuevo. Esto mantiene ``--version`` y ``--help`` como
    operaciones estrictamente de solo lectura.
    """
    from app.core.data_migration import migrate_config_paths

    if not CONFIG_PATH.exists():
        # Hay diccionarios y listas anidados. Una copia superficial permitiría
        # que un consumidor modificase los valores globales para todo el proceso.
        return deepcopy(DEFAULTS)
    try:
        original = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        stored = migrate_config_paths(original)
    except json.JSONDecodeError as error:
        raise ValueError(f"configuración JSON no válida: {CONFIG_PATH}") from error
    if not isinstance(stored, dict):
        raise ValueError(f"la configuración debe ser un objeto JSON: {CONFIG_PATH}")
    # Migración de la clave usada por versiones anteriores.
    if "network" in stored and "range" not in stored:
        stored["range"] = stored.pop("network")
    if "SaveMode" in stored and "projectSaveMode" not in stored:
        stored["projectSaveMode"] = stored.pop("SaveMode")
    if "log" in stored:
        log_root = str(stored["log"]).rstrip("/\\")
        stored.setdefault("programLog", log_root)
        if str(stored.get("programLog", "")).rstrip("/\\") == f"{log_root}/program":
            stored["programLog"] = log_root
    project_directory = stored.get("projectsDirectory")
    if project_directory:
        raw_project_directory = str(project_directory).replace("/", "\\")
        legacy_default = str(Path.home() / "Documents" / "LanCTL")
        if (
            raw_project_directory.casefold() == r"%USERPROFILE%\Documents\LanCTL".casefold()
            or os.path.normcase(os.path.normpath(str(project_directory)))
            == os.path.normcase(os.path.normpath(legacy_default))
        ):
            stored["projectsDirectory"] = DEFAULTS["projectsDirectory"]
    stored.pop("scanColumns", None)
    merged = {**deepcopy(DEFAULTS), **stored}
    monitor = {**DEFAULTS["monitor"], **stored.get("monitor", {})}
    monitor["intervals"] = {
        **DEFAULTS["monitor"]["intervals"],
        **stored.get("monitor", {}).get("intervals", {}),
    }
    monitor["retention"] = {
        **DEFAULTS["monitor"]["retention"],
        **stored.get("monitor", {}).get("retention", {}),
    }
    merged["monitor"] = monitor
    return merged


@transactional_file(CONFIG_PATH)
def save_config(config: dict) -> Path:
    atomic_write_json(CONFIG_PATH, config)
    return CONFIG_PATH.resolve()


def update_config(update: Callable[[dict], Any]) -> dict:
    """Actualiza la configuración dentro de una transacción interproceso."""

    with locked_file(CONFIG_PATH):
        config = load_config()
        replacement = update(config)
        if replacement is not None:
            config = replacement
        save_config(config)
        return config
