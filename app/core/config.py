from __future__ import annotations

import json
import ipaddress
import os
from pathlib import Path
from app.core.paths import application_path


CONFIG_PATH = application_path("data/lc/.config")
DEFAULTS = {
    "database": "data/lc/devices.json",
    "groups": "data/lc/groups.json",
    "log": "data/lc/log",
    "programLog": "data/lc/log",
    "activeProject": None,
    # Variable portable: no vincula la configuración al usuario que la creó.
    "projectsDirectory": r"%USERPROFILE%\Documents\LanCTL",
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
    "ciscoProfiles": "data/lc/cisco_profiles.json",
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
    from app.core.data_migration import ensure_data_layout, migrate_config_paths
    ensure_data_layout()
    if not CONFIG_PATH.exists():
        return DEFAULTS.copy()
    try:
        original = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        stored = migrate_config_paths(original)
    except json.JSONDecodeError as error:
        raise ValueError(f"configuración JSON no válida: {CONFIG_PATH}") from error
    if not isinstance(stored, dict):
        raise ValueError(f"la configuración debe ser un objeto JSON: {CONFIG_PATH}")
    if stored != original:
        temporary = CONFIG_PATH.with_suffix(".migration.tmp")
        temporary.write_text(
            json.dumps(stored, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(CONFIG_PATH)
    # Migración de la clave usada por versiones anteriores.
    if "network" in stored and "range" not in stored:
        stored["range"] = stored.pop("network")
    if "log" in stored:
        log_root = str(stored["log"]).rstrip("/\\")
        stored.setdefault("programLog", log_root)
        if str(stored.get("programLog", "")).rstrip("/\\") == f"{log_root}/program":
            stored["programLog"] = log_root
    project_directory = stored.get("projectsDirectory")
    if project_directory:
        legacy_default = str(Path.home() / "Documents" / "LanCTL")
        if os.path.normcase(os.path.normpath(str(project_directory))) == os.path.normcase(
            os.path.normpath(legacy_default)
        ):
            stored["projectsDirectory"] = DEFAULTS["projectsDirectory"]
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
