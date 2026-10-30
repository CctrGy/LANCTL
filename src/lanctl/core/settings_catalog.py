"""Complete, schema-driven settings catalog shared by interactive interfaces."""

from __future__ import annotations

import ipaddress
import math
import re
from copy import deepcopy

from lanctl.core.config import (
    DOCUMENT_DEFAULTS,
    canonical_config,
)
from lanctl.shared.i18n import t

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
# Append new categories so existing numbered CLI navigation keeps its meaning.
CATEGORIES["gui"] = "Apariencia y GUI"


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


VALUE_CHOICES = {
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


def validate_value(path, value, default):
    if path.startswith("gui.") and path != "gui.schemaVersion":
        from lanctl.core.gui_preferences import validate_preferences

        values = {k: v for k, v in DOCUMENT_DEFAULTS["gui"].items() if k != "schemaVersion"}
        key = path.split(".", 1)[1]
        values[key] = value
        return validate_preferences(values)[key]
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
    if path in VALUE_CHOICES and value not in VALUE_CHOICES[path]:
        raise ValueError(f"{path}: opciones {', '.join(VALUE_CHOICES[path])}")
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
            if not isinstance(address, str):
                raise ValueError(f"{path}: requiere direcciones IP en texto")
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
    """Compatible single-value adapter using the shared preference policy."""
    from lanctl.apps.suite.settings import save_program_changes
    from lanctl.core.settings_policy import SettingsContext

    return save_program_changes({path: value}, SettingsContext("direct"))


_CATEGORY_KEYS = {
    "storage": "LANCTL.UI.TEXT.STORAGE_AND_CREDENTIALS",
    "logging": "LANCTL.UI.TEXT.LOGS_AND_DIAGNOSTICS",
    "projects": "LANCTL.UI.TEXT.PROJECTS_SAVING_AND_WORKSPACE",
    "localization": "LANCTL.UI.TEXT.LANGUAGE_AND_TRANSLATIONS",
    "cli": "LANCTL.UI.TEXT.CLI_CONSOLE",
    "network": "LANCTL.UI.TEXT.NETWORK_DHCP_DNS_AND_TR_064",
    "ip": "LANCTL.UI.TEXT.LANIP_DISCOVERY_AND_INVENTORY",
    "tui": "LANCTL.UI.TEXT.TUI_LAYOUT_COLUMNS_AND_KEYBOARD",
    "access": "LANCTL.UI.TEXT.LANACCESS_AND_REMOTE_ACCESS",
    "monitor": "LANCTL.UI.TEXT.LANMON_RUNTIME_INTERVALS_AND_RETENTION",
    "schemaVersion": "LANCTL.UI.TEXT.FORMAT_INFORMATION",
    "startup": "LANCTL.UI.TEXT.LANCTL_STARTUP_AND_WINDOWS",
    "gui": "LANCTL.UI.TEXT.APPEARANCE_AND_GUI",
}


def category_labels():
    """Localized display labels; category IDs and ordering stay canonical."""
    return {
        key: t(_CATEGORY_KEYS[key]) if key in _CATEGORY_KEYS else label
        for key, label in CATEGORIES.items()
    }
