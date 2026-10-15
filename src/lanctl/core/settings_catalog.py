"""Complete, schema-driven settings catalog shared by interactive interfaces."""

from __future__ import annotations

import ipaddress
import math
import re
from copy import deepcopy

from lanctl.core.config import (
    DOCUMENT_DEFAULTS,
    canonical_config,
    config_from_document,
    update_config,
)

CATEGORIES = {
    "storage": "Almacenamiento y credenciales",
    "logging": "Registros y diagnóstico",
    "projects": "Proyectos, guardado y espacio de trabajo",
    "plugins": "Plugins",
    "localization": "Idioma y traducciones",
    "cli": "Consola CLI",
    "network": "Red, DHCP, DNS y TR-064",
    "ip": "LANIP: descubrimiento e inventario",
    "tui": "Interfaz TUI: distribución, columnas y teclado",
    "wol": "Wake on LAN",
    "access": "LANACCESS y acceso remoto",
    "monitor": "LANMON: ejecución, intervalos y retención",
    "schemaVersion": "Información del formato",
}


CATEGORIES["startup"] = "Inicio de LANCTL y ventanas"


def leaves(document, prefix=""):
    for key, value in document.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and value:
            yield from leaves(value, path)
        else:
            yield path, deepcopy(value)


def read_only(path):
    if path.endswith("schemaVersion") or path == "network.settingsDownloadedAt":
        return "Campo automático del formato o de la última descarga"
    if path in {"projects.active", "projects.workspace.active"}:
        return "Gestionado mediante project use / project create"
    return ""


def catalog(config):
    current = dict(leaves(canonical_config(config)))
    return [
        {
            "path": path,
            "category": path.split(".")[0],
            "value": value,
            "default": default,
            "readOnly": read_only(path),
        }
        for path, default in leaves(DOCUMENT_DEFAULTS)
        for value in [current.get(path, default)]
    ]


def _assign(document, path, value):
    parts = path.split(".")
    target = document
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value


def validate_value(path, value, default):
    if value is None and path.startswith("tui.keyBindings."):
        return None
    if (
        default is not None
        and type(value) is not type(default)
        and not (
            (type(default) is float or path == "projects.saveIntervalMinutes")
            and type(value) in (int, float)
        )
    ):
        raise ValueError(f"{path}: requiere {type(default).__name__}")
    if path == "monitor.duration":
        from lanctl.apps.monitor.configuration import parse_duration

        if value is None:
            return None
        seconds = parse_duration(value)
        if not 10 <= seconds <= 86400:
            raise ValueError("La duración del monitor debe estar entre 10s y 24h")
        return seconds
    if path == "monitor.cidr" and value:
        network = ipaddress.ip_network(value, strict=False)
        if network.version != 4 or network.num_addresses > 65536:
            raise ValueError("CIDR monitor no válido o demasiado amplio")
    if default is None and value is not None:
        expected = (
            bool
            if path == "network.dhcpEnabled"
            else int
            if path == "network.dhcpLeaseTime"
            else str
        )
        if type(value) is not expected:
            raise ValueError(f"{path}: requiere {expected.__name__} o null")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{path}: requiere un número finito no negativo")
        if (
            path.endswith(
                ("workers", "maxHosts", "failureThreshold", "recoveryThreshold", "retentionDays")
            )
            or ".intervals." in path
        ) and value < 1:
            raise ValueError(f"{path}: mínimo 1")
        if path == "projects.saveIntervalMinutes" and value < 0.1:
            raise ValueError("El intervalo de guardado debe ser de al menos 0.1 minutos")
        if path == "wol.repeat" and value < 1:
            raise ValueError("wol.repeat: mínimo 1")
        if path.endswith(("timeout", "saveIntervalMinutes")) and value <= 0:
            raise ValueError(f"{path}: debe ser mayor que cero")
        if path.endswith(("Port", ".port")) and not 1 <= value <= 65535:
            raise ValueError(f"{path}: puerto entre 1 y 65535")
        if path == "logging.errorLevel" and not 1 <= value <= 59:
            raise ValueError("logging.errorLevel: entre 1 y 59")
    enums = {
        "startup.interface": ("cli", "tui", "gui"),
        "ip.discovery": ("icmp", "arp", "hybrid"),
        "ip.scanProfile": ("fast", "normal", "accurate"),
        "ip.scanOrder": ("ascending", "descending", "random"),
        "monitor.execution.scanOrder": ("ascending", "descending", "random"),
        "ip.disconnectedRetention": ("permanent", "session", "forget"),
        "ip.disconnectedRetentionTarget": ("unconfirmed", "all"),
        "ip.disconnectedRetentionScope": ("all", "dhcp"),
        "monitor.authority": ("observe", "operate", "administer"),
        "monitor.mode": ("permanent", "temporary", "diagnostic", "once"),
        "access.remote.backend": ("service", "user"),
        "access.remote.forcedView": ("off", "gui", "tui", "plugins", "projects", "settings"),
        "wol.method": ("auto", "arp", "ping", "port"),
    }
    if path in enums and value not in enums[path]:
        raise ValueError(f"{path}: opciones {', '.join(enums[path])}")
    if path == "projects.saveMode":
        from lanctl.core.projects.save_policy import normalize_save_mode

        return normalize_save_mode(value)
    if path == "network.range" and value and ipaddress.ip_network(value, strict=False).version != 4:
        raise ValueError("Solo se admiten redes IPv4")
    if path == "network.dhcpRange" and value:
        from lanctl.core.config import normalize_dhcp_range

        return normalize_dhcp_range(value)
    if path in {"network.gateway", "network.tr064Host"} and value:
        ipaddress.ip_address(value)
    if path == "network.subnetMask" and value:
        ipaddress.IPv4Network(f"0.0.0.0/{value}")
    if path in {"network.dnsServers", "network.reservedAddresses"}:
        for address in value:
            ipaddress.ip_address(address)
    if path.startswith("monitor.retention.") and not re.fullmatch(
        r"(?:[1-9][0-9]*[smhdw]|permanent)", value
    ):
        raise ValueError(f"{path}: usa una duración como 24h, 30d o permanent")
    if path == "ip.listColumns":
        from lanctl.core.output import normalize_columns

        return normalize_columns(value)
    if path == "tui.cliHeightPercent":
        from lanctl.apps.ip.interfaces.tui.layout import normalize_cli_percent

        return normalize_cli_percent(value)
    if path == "tui.panelLayout":
        from lanctl.apps.ip.interfaces.tui.layout import normalize_panel_layout

        return normalize_panel_layout(value)
    if path.startswith("tui.columnWidths."):
        from lanctl.apps.ip.interfaces.tui.layout import normalize_column_spec

        return normalize_column_spec(path.rsplit(".", 1)[1], value)
    if path.startswith("tui.keyBindings.") and value is not None:
        from lanctl.apps.ip.interfaces.tui.keyboard import CONFIGURABLE_TUI_KEYS

        if value not in CONFIGURABLE_TUI_KEYS:
            raise ValueError(f"Tecla TUI no válida: {value}")
    if path == "tui.footerButtons":
        from lanctl.apps.ip.interfaces.tui.keyboard import FOOTER_ACTIONS

        if any(action not in FOOTER_ACTIONS for action in value):
            raise ValueError("Acción de barra TUI desconocida")
    return value


def set_program_value(path, value):
    defaults = dict(leaves(DOCUMENT_DEFAULTS))
    if path not in defaults:
        raise ValueError(f"Ajuste desconocido: {path}")
    if reason := read_only(path):
        raise ValueError(f"{path}: solo lectura. {reason}")
    value = validate_value(path, value, defaults[path])

    def apply(config):
        document = canonical_config(config)
        _assign(document, path, value)
        if path.startswith("tui.keyBindings."):
            from lanctl.apps.ip.interfaces.tui.keyboard import validate_key_bindings

            validate_key_bindings(document["tui"]["keyBindings"])
        replacement = config_from_document(document)
        if path.startswith("monitor."):
            from lanctl.apps.monitor.configuration import ConfigProvider, validate_monitor_settings

            validate_monitor_settings(replacement["monitor"])
            ConfigProvider(replacement).monitor()
        return replacement

    return update_config(apply)
