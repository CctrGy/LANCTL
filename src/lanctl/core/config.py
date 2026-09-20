from __future__ import annotations

import ipaddress
import json
import os
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

from lanctl.core.file_transaction import atomic_write_json, locked_file, transactional_file
from lanctl.core.paths import application_path

CONFIG_PATH = application_path("data/lc/.config")
CONFIG_SCHEMA_VERSION = 2

_LEGACY_DEFAULT_FOOTER_BUTTONS = [
    "help",
    "info",
    "ping",
    "refresh",
    "plugins",
    "projects",
    "settings",
    "history",
    "search",
    "reload",
    "edit",
    "groups",
    "ports",
    "open",
    "save",
    "differences",
    "copyLine",
    "copyJson",
    "console",
    "quit",
    "select",
    "execute",
    "exit",
]

_DEFAULT_FOOTER_BUTTONS = [
    "help",
    "info",
    "ping",
    "refresh",
    "plugins",
    "projects",
    "settings",
    "select",
]

DOCUMENT_DEFAULTS = {
    "schemaVersion": CONFIG_SCHEMA_VERSION,
    "storage": {
        "credentials": "data/lc/.credentials",
        "iconsDirectory": "data/lc/icons",
    },
    "logging": {
        "directory": "data/lc/log",
        "programDirectory": "data/lc/log",
        "cleanupEnabled": False,
        "retentionDays": 90,
        "errorLevel": 20,
    },
    "projects": {
        "active": None,
        "saveMode": "manual",
        "saveIntervalMinutes": 5,
        "directory": None,
        "workspace": {
            "active": None,
            "directory": "data/lc/projects/workspaces/default",
            "databases": {
                "devices": "data/lc/projects/workspaces/default/database/devices.json",
                "groups": "data/lc/projects/workspaces/default/database/groups.json",
                "monitor": "data/lc/projects/workspaces/default/monitoring/monitor.db",
                "physical": "data/lc/projects/workspaces/default/physical/idf.db",
            },
            "monitoring": {
                "runtime": "data/lc/projects/workspaces/default/monitoring/sessions.json",
                "incidents": "data/lc/projects/workspaces/default/monitoring/incidents.json",
                "lock": "data/lc/projects/workspaces/default/monitoring/monitor.lock",
                "profiles": "data/lc/projects/workspaces/default/monitoring/profiles.json",
                "assignments": "data/lc/projects/workspaces/default/monitoring/assignments.json",
            },
        },
        "networkDatabase": None,
        "networkGroups": None,
        "databaseLog": None,
    },
    "plugins": {
        "directory": "data/lc/plugins",
        "registry": "data/lc/plugins.registry",
        "storage": "data/lc/plugin-storage",
        "safeMode": False,
    },
    "localization": {"language": "en", "languagesDirectory": "data/lc/languages"},
    "cli": {
        "promptSaveOnCommandExit": False,
        "commandChaining": True,
    },
    "network": {
        "range": None,
        "dhcpRange": None,
        "tr064Port": 49000,
        "gateway": None,
        "subnetMask": None,
        "dhcpEnabled": None,
        "dnsServers": [],
        "domainName": "",
        "reservedAddresses": [],
        "tr064Host": None,
        "dhcpLeaseTime": None,
        "settingsDownloadedAt": None,
    },
    "ip": {
        "workers": 64,
        "timeout": 0.8,
        "maxHosts": 4096,
        "discovery": "hybrid",
        "scanProfile": "normal",
        "scanOrder": "ascending",
        "progress": True,
        "serviceIdentification": True,
        "disconnectedRetention": "permanent",
        "disconnectedRetentionTarget": "unconfirmed",
        "disconnectedRetentionScope": "all",
        "listColumns": ["ip", "cnf", "alias", "mac", "name", "group", "description"],
        "ciscoProfiles": "data/lc/cisco_profiles.json",
        "radminViewer": None,
    },
    "tui": {
        "schemaVersion": 2,
        "panelLayout": "cli.bottom",
        "cliHeightPercent": 28,
        "columnWidths": {
            "IP": "15ch",
            "responseMs": "4%",
            "cnf": "2%",
            "ALIAS": "10%",
            "MAC": "17ch",
            "NAME": "12%",
            "GROUP": "12%",
            "description": "33%",
            "manufacturer": "17%",
            "users": "10%",
        },
        "keyBindings": {
            "help": "F1",
            "info": "F2",
            "ping": "F3",
            "refresh": "F5",
            "plugins": "F7",
            "projects": "F9",
            "settings": "F12",
            "history": "CTRL_H",
            "search": "CTRL_F",
            "reload": "CTRL_R",
            "edit": "CTRL_E",
            "groups": "CTRL_G",
            "ports": "CTRL_P",
            "open": "CTRL_O",
            "save": "CTRL_S",
            "differences": "CTRL_D",
            "copyLine": "CTRL_X",
            "copyJson": "CTRL_J",
            "console": "CTRL_L",
            "quit": "CTRL_Q",
            "deviceHistory": None,
            "scanSelected": None,
            "filterActive": None,
            "filterDisconnected": None,
            "filterAll": None,
            "ssh": None,
            "terminal": None,
            "credentials": None,
            "wakeOnLan": None,
            "copyIp": None,
            "copyMac": None,
            "projectStatus": None,
        },
        "footerButtons": list(_DEFAULT_FOOTER_BUTTONS),
    },
    "wol": {
        "port": 9,
        "repeat": 3,
        "interval": 0.5,
        "wait": 60,
        "method": "auto",
        "sequences": "data/lc/wol-sequences.json",
    },
    "access": {
        "config": "data/lc/access/config.json",
        "users": "data/lc/access/users.dc",
        "remote": {
            "enabled": False,
            "bind": "",
            "cidr": "",
            "port": 2222,
            "passwordAuthentication": False,
            "backend": "service",
            "forcedView": "off",
        },
    },
    "monitor": {
        "enabled": False,
        "profile": "normal",
        "mode": "permanent",
        "authority": "observe",
        "execution": {
            "workers": 32,
            "timeout": 0.8,
            "scanOrder": "ascending",
            "failureThreshold": 3,
            "recoveryThreshold": 2,
        },
        "intervals": {
            "criticalDevices": 15,
            "deviceStatus": 60,
            "networkDiscovery": 300,
            "serviceScan": 1800,
            "fullScan": 86400,
        },
        "retention": {
            "rawSamples": "24h",
            "fiveMinuteAggregates": "30d",
            "hourlyAggregates": "365d",
            "events": "permanent",
        },
    },
}

DEFAULTS = {
    "database": "data/lc/devices.json",
    # Base SQLite de infraestructura física. LANCTL solo publica la ruta;
    # LANWIRE conserva la propiedad y el esquema de este archivo.
    "physicalDatabase": "data/lc/physical/idf.db",
    "groups": "data/lc/groups.json",
    "log": "data/lc/log",
    "programLog": "data/lc/log",
    "errorLogLevel": 20,
    "activeProject": None,
    "projectSaveMode": "manual",
    "projectSaveIntervalMinutes": 5,
    # `None` conserva una ruta portable y evita vincular la configuración al
    # usuario que la creó.
    "projectsDirectory": None,
    "projectWorkspace": None,
    "networkDatabase": None,
    "networkGroups": None,
    "databaseLog": None,
    "plugins": "data/lc/plugins",
    "pluginRegistry": "data/lc/plugins.registry",
    "pluginSafeMode": False,
    "language": "en",
    "languagesDirectory": "data/lc/languages",
    "cliPromptSaveOnCommandExit": False,
    "cliCommandChaining": True,
    "iconsDirectory": "data/lc/icons",
    "logCleanupEnabled": False,
    "logRetentionDays": 90,
    "credentials": "data/lc/.credentials",
    "range": None,
    "dhcpRange": None,
    "tr064Port": 49000,
    "gateway": None,
    "subnetMask": None,
    "dhcpEnabled": None,
    "dnsServers": [],
    "domainName": "",
    "reservedAddresses": [],
    "tr064Host": None,
    "dhcpLeaseTime": None,
    "settingsDownloadedAt": None,
    "radminViewer": None,
    "tuiKeyBindings": deepcopy(DOCUMENT_DEFAULTS["tui"]["keyBindings"]),
    "tuiFooterButtons": deepcopy(DOCUMENT_DEFAULTS["tui"]["footerButtons"]),
    "tuiPanelLayout": "cli.bottom",
    "tuiCliHeightPercent": 28,
    "tuiColumnWidths": deepcopy(DOCUMENT_DEFAULTS["tui"]["columnWidths"]),
    "wol": {"port": 9, "repeat": 3, "interval": 0.5, "wait": 60, "method": "auto"},
    "wolSequences": "data/lc/wol-sequences.json",
    "monitorRuntime": "data/lc/monitor-sessions.json",
    "monitorIncidents": "data/lc/monitor-incidents.json",
    "monitorLock": "data/lc/monitor.lock",
    "accessConfig": "data/lc/access/config.json",
    "accessUsers": "data/lc/access/users.dc",
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
    "disconnectedRetention": "permanent",
    "disconnectedRetentionTarget": "unconfirmed",
    "disconnectedRetentionScope": "all",
    "listColumns": ["ip", "cnf", "alias", "mac", "name", "group", "description"],
}

_LEGACY_PATHS = {
    "database": ("projects", "workspace", "databases", "devices"),
    "physicalDatabase": ("projects", "workspace", "databases", "physical"),
    "groups": ("projects", "workspace", "databases", "groups"),
    "credentials": ("storage", "credentials"),
    "iconsDirectory": ("storage", "iconsDirectory"),
    "log": ("logging", "directory"),
    "programLog": ("logging", "programDirectory"),
    "logCleanupEnabled": ("logging", "cleanupEnabled"),
    "logRetentionDays": ("logging", "retentionDays"),
    "errorLogLevel": ("logging", "errorLevel"),
    "activeProject": ("projects", "active"),
    "projectSaveMode": ("projects", "saveMode"),
    "projectSaveIntervalMinutes": ("projects", "saveIntervalMinutes"),
    "projectsDirectory": ("projects", "directory"),
    "projectWorkspace": ("projects", "workspace", "active"),
    "networkDatabase": ("projects", "networkDatabase"),
    "networkGroups": ("projects", "networkGroups"),
    "databaseLog": ("projects", "databaseLog"),
    "plugins": ("plugins", "directory"),
    "pluginRegistry": ("plugins", "registry"),
    "smbStorage": ("plugins", "storage"),
    "pluginSafeMode": ("plugins", "safeMode"),
    "language": ("localization", "language"),
    "languagesDirectory": ("localization", "languagesDirectory"),
    "cliPromptSaveOnCommandExit": ("cli", "promptSaveOnCommandExit"),
    "cliCommandChaining": ("cli", "commandChaining"),
    "range": ("network", "range"),
    "dhcpRange": ("network", "dhcpRange"),
    "tr064Port": ("network", "tr064Port"),
    "gateway": ("network", "gateway"),
    "subnetMask": ("network", "subnetMask"),
    "dhcpEnabled": ("network", "dhcpEnabled"),
    "dnsServers": ("network", "dnsServers"),
    "domainName": ("network", "domainName"),
    "reservedAddresses": ("network", "reservedAddresses"),
    "tr064Host": ("network", "tr064Host"),
    "dhcpLeaseTime": ("network", "dhcpLeaseTime"),
    "settingsDownloadedAt": ("network", "settingsDownloadedAt"),
    "workers": ("ip", "workers"),
    "timeout": ("ip", "timeout"),
    "maxHosts": ("ip", "maxHosts"),
    "discovery": ("ip", "discovery"),
    "scanProfile": ("ip", "scanProfile"),
    "scanOrder": ("ip", "scanOrder"),
    "progress": ("ip", "progress"),
    "serviceIdentification": ("ip", "serviceIdentification"),
    "disconnectedRetention": ("ip", "disconnectedRetention"),
    "disconnectedRetentionTarget": ("ip", "disconnectedRetentionTarget"),
    "disconnectedRetentionScope": ("ip", "disconnectedRetentionScope"),
    "listColumns": ("ip", "listColumns"),
    "ciscoProfiles": ("ip", "ciscoProfiles"),
    "radminViewer": ("ip", "radminViewer"),
    "tuiKeyBindings": ("tui", "keyBindings"),
    "tuiFooterButtons": ("tui", "footerButtons"),
    "tuiPanelLayout": ("tui", "panelLayout"),
    "tuiCliHeightPercent": ("tui", "cliHeightPercent"),
    "tuiColumnWidths": ("tui", "columnWidths"),
    "wolSequences": ("wol", "sequences"),
    "accessConfig": ("access", "config"),
    "accessUsers": ("access", "users"),
    "remoteAccessEnabled": ("access", "remote", "enabled"),
    "remoteAccessBind": ("access", "remote", "bind"),
    "remoteAccessCidr": ("access", "remote", "cidr"),
    "remoteAccessPort": ("access", "remote", "port"),
    "remoteAccessPasswordAuthentication": ("access", "remote", "passwordAuthentication"),
    "remoteAccessBackend": ("access", "remote", "backend"),
    "remoteAccessForcedView": ("access", "remote", "forcedView"),
    "monitorRuntime": ("projects", "workspace", "monitoring", "runtime"),
    "monitorIncidents": ("projects", "workspace", "monitoring", "incidents"),
    "monitorLock": ("projects", "workspace", "monitoring", "lock"),
    "monitorDatabase": ("projects", "workspace", "databases", "monitor"),
    "monitorProfiles": ("projects", "workspace", "monitoring", "profiles"),
    "monitorAssignments": ("projects", "workspace", "monitoring", "assignments"),
}


class ConfigSnapshot(dict):
    """Vista plana compatible asociada al documento canónico que la originó."""

    def __init__(self, values: dict, document: dict | None = None) -> None:
        super().__init__(values)
        self.document = deepcopy(document) if document is not None else None

    def __deepcopy__(self, memo):
        return ConfigSnapshot(deepcopy(dict(self), memo), deepcopy(self.document, memo))


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _path_get(document: dict, path: tuple[str, ...]):
    value: Any = document
    for part in path:
        if not isinstance(value, dict) or part not in value:
            raise KeyError(".".join(path))
        value = value[part]
    return deepcopy(value)


def _path_set(document: dict, path: tuple[str, ...], value: Any) -> None:
    target = document
    for part in path[:-1]:
        target = target.setdefault(part, {})
    target[path[-1]] = deepcopy(value)


def _legacy_monitor(document: dict) -> dict:
    monitor = document["monitor"]
    return {
        "enabled": monitor["enabled"],
        "profile": monitor["profile"],
        "mode": monitor["mode"],
        "authority": monitor["authority"],
        **deepcopy(monitor["execution"]),
        "intervals": deepcopy(monitor["intervals"]),
        "retention": deepcopy(monitor["retention"]),
    }


def _document_to_legacy(document: dict) -> ConfigSnapshot:
    values = deepcopy(DEFAULTS)
    for key, path in _LEGACY_PATHS.items():
        values[key] = _path_get(document, path)
    values["wol"] = {
        key: deepcopy(value) for key, value in document["wol"].items() if key != "sequences"
    }
    values["monitor"] = _legacy_monitor(document)
    return ConfigSnapshot(values, document)


def _legacy_to_document(config: dict) -> dict:
    base = (
        config.document
        if isinstance(config, ConfigSnapshot) and config.document
        else DOCUMENT_DEFAULTS
    )
    document = _deep_merge(DOCUMENT_DEFAULTS, base)
    for key, path in _LEGACY_PATHS.items():
        if key in config:
            _path_set(document, path, config[key])
    if isinstance(config.get("wol"), dict):
        for key, value in config["wol"].items():
            if key != "sequences":
                document["wol"][key] = deepcopy(value)
    if isinstance(config.get("monitor"), dict):
        monitor = config["monitor"]
        for key in ("enabled", "profile", "mode", "authority"):
            if key in monitor:
                document["monitor"][key] = deepcopy(monitor[key])
        for key in ("workers", "timeout", "scanOrder", "failureThreshold", "recoveryThreshold"):
            if key in monitor:
                document["monitor"]["execution"][key] = deepcopy(monitor[key])
        for key in ("intervals", "retention"):
            if isinstance(monitor.get(key), dict):
                document["monitor"][key] = _deep_merge(document["monitor"][key], monitor[key])
    document["schemaVersion"] = CONFIG_SCHEMA_VERSION
    return document


def _normalize_v2_document(config: dict) -> dict:
    """Admite borradores v2 anteriores sin perder sus rutas."""

    document = deepcopy(config)
    tui = document.get("tui")
    if isinstance(tui, dict):
        tui_schema = int(tui.get("schemaVersion", 0) or 0)
        if tui_schema < 1:
            tui["keyBindings"] = _deep_merge(
                DOCUMENT_DEFAULTS["tui"]["keyBindings"], tui.get("keyBindings", {})
            )
        if tui_schema < 2:
            configured_buttons = tui.get("footerButtons")
            # La barra completa era el valor predeterminado de la versión 1.
            # Sólo se sustituye esa lista exacta; una selección personalizada
            # por el usuario se conserva íntegramente.
            if not isinstance(configured_buttons, list) or configured_buttons == (
                _LEGACY_DEFAULT_FOOTER_BUTTONS
            ):
                tui["footerButtons"] = list(_DEFAULT_FOOTER_BUTTONS)
            tui["schemaVersion"] = 2
    projects = document.setdefault("projects", {})
    workspace = projects.get("workspace")
    if not isinstance(workspace, dict):
        workspace = {"active": workspace}
        projects["workspace"] = workspace
    databases = workspace.setdefault("databases", {})
    monitoring = workspace.setdefault("monitoring", {})

    storage = document.get("storage")
    if isinstance(storage, dict):
        for old, new in (
            ("database", "devices"),
            ("groups", "groups"),
            ("physicalDatabase", "physical"),
        ):
            if old in storage and new not in databases:
                databases[new] = storage.pop(old)

    monitor = document.get("monitor")
    monitor_storage = monitor.get("storage") if isinstance(monitor, dict) else None
    if isinstance(monitor_storage, dict):
        if "database" in monitor_storage and "monitor" not in databases:
            databases["monitor"] = monitor_storage["database"]
        for old, new in (
            ("runtime", "runtime"),
            ("incidents", "incidents"),
            ("lock", "lock"),
            ("profiles", "profiles"),
            ("assignments", "assignments"),
        ):
            if old in monitor_storage and new not in monitoring:
                monitoring[new] = monitor_storage[old]
        monitor.pop("storage", None)
    return document


def canonical_config(config: dict) -> dict:
    """Devuelve la representación agrupada que se escribe en disco."""

    if int(config.get("schemaVersion", 0) or 0) == CONFIG_SCHEMA_VERSION:
        return _deep_merge(DOCUMENT_DEFAULTS, _normalize_v2_document(config))
    return _legacy_to_document(config)


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
    from lanctl.core.data_migration import migrate_config_paths

    if not CONFIG_PATH.exists():
        from lanctl.core.errors import errors

        errors.emit(
            level=8,
            origin="LANCTL.Config.Load.Defaults",
            code="CONFIG.DEFAULTS.USED",
            message="No existe configuración; se usan valores predeterminados",
            details={"path": str(CONFIG_PATH)},
            print_output=False,
            once_key="config.defaults.missing",
        )
        # Hay diccionarios y listas anidados. Una copia superficial permitiría
        # que un consumidor modificase los valores globales para todo el proceso.
        return _document_to_legacy(deepcopy(DOCUMENT_DEFAULTS))
    try:
        original = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        stored = migrate_config_paths(original)
    except json.JSONDecodeError as error:
        raise ValueError(f"configuración JSON no válida: {CONFIG_PATH}") from error
    if not isinstance(stored, dict):
        raise ValueError(f"la configuración debe ser un objeto JSON: {CONFIG_PATH}")
    if int(stored.get("schemaVersion", 0) or 0) == CONFIG_SCHEMA_VERSION:
        normalized = _normalize_v2_document(stored)
        return _document_to_legacy(_deep_merge(DOCUMENT_DEFAULTS, normalized))
    # Migración de la clave usada por versiones anteriores.
    if "network" in stored and "range" not in stored:
        stored["range"] = stored.pop("network")
    if "SaveMode" in stored and "projectSaveMode" not in stored:
        stored["projectSaveMode"] = stored.pop("SaveMode")
    if stored.get("accessUsers") == "data/lc/access/users.json":
        stored["accessUsers"] = DEFAULTS["accessUsers"]
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
    return _document_to_legacy(_legacy_to_document(merged))


@transactional_file(CONFIG_PATH)
def save_config(config: dict) -> Path:
    atomic_write_json(CONFIG_PATH, canonical_config(config))
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
