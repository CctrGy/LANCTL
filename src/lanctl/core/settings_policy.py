"""Preference policy and validation, independent of command parsers."""

from copy import deepcopy
from dataclasses import dataclass

from lanctl.core.config import DOCUMENT_DEFAULTS, canonical_config, config_from_document
from lanctl.core.settings_catalog import _assign, leaves, read_only, validate_value

LAUNCHER_CATEGORIES = {
    "lanctl": None,
    "lanip": ("ip", "network", "wol"),
    "lanwire": ("projects", "storage"),
    "lanrack": ("projects", "storage"),
    "lanaccess": ("access", "storage"),
    "lanmon": ("monitor", "logging"),
}

INTERNAL_PATHS = frozenset(
    [
        "storage.credentials",
        "storage.iconsDirectory",
        "logging.directory",
        "logging.programDirectory",
        "projects.networkDatabase",
        "projects.networkGroups",
        "projects.legacyPhysicalDatabase",
        "projects.databaseLog",
        "plugins.directory",
        "plugins.registry",
        "plugins.storage",
        "localization.languagesDirectory",
        "ip.ciscoProfiles",
        "ip.radminViewer",
        "wol.sequences",
        "access.config",
        "access.users",
    ]
)

# Explicit user-preference registry. A new schema leaf is NOT automatically an
# editable preference. None means shared by all launchers; LANCTL administers
# all domains but still respects the interface dimension.
_INTERFACES = frozenset({"cli", "tui", "gui"})
_PREFERENCES = {}
for _paths, _interfaces, _launchers in (
    (
        (
            "logging.cleanupEnabled logging.retentionDays logging.errorLevel "
            "projects.saveMode projects.saveIntervalMinutes projects.directory "
            "localization.language plugins.safeMode startup.interface"
        ),
        _INTERFACES,
        None,
    ),
    ("cli.promptSaveOnCommandExit cli.commandChaining", {"cli"}, None),
    ("gui.theme gui.density gui.fontScale gui.reducedMotion", {"gui"}, None),
    ("startup.closeGuiOnLaunch", {"gui"}, {"lanctl"}),
    (
        (
            "network.range network.dhcpRange network.tr064Port network.gateway "
            "network.subnetMask network.dhcpEnabled network.dnsServers network.domainName "
            "network.reservedAddresses network.tr064Host network.dhcpLeaseTime"
        ),
        _INTERFACES,
        {"lanip", "lanmon"},
    ),
    (
        (
            "ip.workers ip.timeout ip.maxHosts ip.discovery ip.scanProfile ip.scanOrder "
            "ip.serviceIdentification ip.disconnectedRetention ip.disconnectedRetentionTarget "
            "ip.disconnectedRetentionScope wol.port wol.repeat wol.interval wol.wait wol.method"
        ),
        _INTERFACES,
        {"lanip"},
    ),
    ("ip.progress", {"cli"}, {"lanip"}),
    ("ip.listColumns", {"cli", "tui"}, {"lanip"}),
    (
        (
            "tui.panelLayout tui.cliHeightPercent tui.footerButtons "
            "tui.columnWidths.IP tui.columnWidths.responseMs tui.columnWidths.cnf "
            "tui.columnWidths.ALIAS tui.columnWidths.MAC tui.columnWidths.NAME "
            "tui.columnWidths.GROUP tui.columnWidths.description tui.columnWidths.manufacturer "
            "tui.columnWidths.users tui.keyBindings.help tui.keyBindings.info tui.keyBindings.ping "
            "tui.keyBindings.refresh tui.keyBindings.plugins tui.keyBindings.projects "
            "tui.keyBindings.settings tui.keyBindings.history tui.keyBindings.search "
            "tui.keyBindings.reload tui.keyBindings.edit tui.keyBindings.groups "
            "tui.keyBindings.ports tui.keyBindings.open tui.keyBindings.save "
            "tui.keyBindings.differences tui.keyBindings.copyLine tui.keyBindings.copyJson "
            "tui.keyBindings.console tui.keyBindings.quit tui.keyBindings.deviceHistory "
            "tui.keyBindings.scanSelected tui.keyBindings.filterActive "
            "tui.keyBindings.filterDisconnected tui.keyBindings.filterAll tui.keyBindings.ssh "
            "tui.keyBindings.terminal tui.keyBindings.credentials tui.keyBindings.wakeOnLan "
            "tui.keyBindings.copyIp tui.keyBindings.copyMac tui.keyBindings.projectStatus"
        ),
        {"tui"},
        {"lanip"},
    ),
    (
        (
            "access.remote access.remote.enabled access.remote.bind access.remote.cidr "
            "access.remote.port access.remote.passwordAuthentication access.remote.backend "
            "access.remote.forcedView"
        ),
        _INTERFACES,
        {"lanaccess"},
    ),
    (
        (
            "monitor.enabled monitor.profile monitor.mode monitor.authority monitor.interface "
            "monitor.cidr monitor.duration monitor.execution.workers monitor.execution.timeout "
            "monitor.execution.scanOrder monitor.execution.failureThreshold "
            "monitor.execution.recoveryThreshold monitor.intervals.criticalDevices "
            "monitor.intervals.deviceStatus monitor.intervals.networkDiscovery "
            "monitor.intervals.serviceScan monitor.intervals.fullScan monitor.retention.rawSamples "
            "monitor.retention.fiveMinuteAggregates monitor.retention.hourlyAggregates "
            "monitor.retention.events"
        ),
        _INTERFACES,
        {"lanmon"},
    ),
):
    for _path in _paths.split():
        _PREFERENCES[_path] = (frozenset(_interfaces), _launchers)


def _preference_restriction(context, path):
    rule = _PREFERENCES.get(path)
    if rule is None:
        return "No es una preferencia editable del usuario"
    interfaces, launchers = rule
    interface = "cli" if context.interface == "remote" else context.interface
    if interface != "direct" and interface not in interfaces:
        return "El ajuste no pertenece a esta interfaz"
    if launchers is not None and context.launcher != "lanctl" and context.launcher not in launchers:
        return "El ajuste no pertenece a este launcher"
    return ""


def preference_visible(context, path):
    """Visibility never grants the separate authorization required on save."""
    if context.scope == "project":
        return not restriction(context, path)
    return not internal_path(path) and not _preference_restriction(context, path)


def internal_path(path):
    return path in INTERNAL_PATHS or path.startswith("projects.workspace.")


@dataclass(frozen=True)
class SettingsContext:
    # Constructed by the adapter, never deserialized from an RPC payload.
    interface: str
    launcher: str = "lanctl"
    scope: str = "program"
    legacy_paths: bool = False

    def __post_init__(self):
        if self.interface not in {"cli", "gui", "tui", "direct", "remote"}:
            raise ValueError("Interfaz de configuración desconocida")
        if self.launcher not in LAUNCHER_CATEGORIES:
            raise ValueError("Launcher de configuración desconocido")
        if self.scope not in {"program", "project"}:
            raise ValueError("Ámbito de configuración desconocido")
        if self.legacy_paths and self.interface != "cli":
            raise PermissionError("Las rutas administrativas requieren la CLI local")


def restriction(context, path):
    if context.scope == "program":
        if reason := read_only(path):
            return reason
        if internal_path(path):
            if context.legacy_paths:
                return ""
            return "Ruta interna: utiliza el comando administrativo local correspondiente"
        if reason := _preference_restriction(context, path):
            return reason
        if context.interface == "remote" and (
            path.startswith("access.") or path == "projects.directory"
        ):
            return "La administración de rutas y acceso requiere una sesión local"
        return ""
    from lanctl.core.projects.settings import PROJECT_EDITABLE

    category, _, key = path.partition(".")
    # VLAN inventories have a dedicated editor; they are not scalar preferences.
    if key not in PROJECT_EDITABLE.get(category, set()) or path == "vlan.vlans":
        return "Campo automático, interno o gestionado por su editor específico"
    return ""


def prepare_program_changes(config, changes, context):
    if context.scope != "program" or not isinstance(changes, dict):
        raise ValueError("Se requiere un lote de ajustes de programa")
    defaults = dict(leaves(DOCUMENT_DEFAULTS))
    expanded = {}
    for path, value in changes.items():
        if path == "access.remote":
            if not isinstance(value, dict) or not value:
                raise ValueError("access.remote requiere un objeto con ajustes remotos")
            for key, item in value.items():
                target = f"access.remote.{key}"
                if target in changes or target in expanded:
                    raise ValueError(f"Ajuste repetido: {target}")
                expanded[target] = item
        else:
            expanded[path] = value
    document = canonical_config(config)
    for path, value in expanded.items():
        if path not in defaults:
            raise ValueError(f"Ajuste desconocido: {path}")
        if reason := restriction(context, path):
            raise ValueError(f"{path}: solo lectura. {reason}")
        _assign(document, path, validate_value(path, value, defaults[path]))
    if any(path.startswith("tui.keyBindings.") for path in expanded):
        from lanctl.apps.ip.interfaces.tui.keyboard import validate_key_bindings

        validate_key_bindings(document["tui"]["keyBindings"])
    replacement = config_from_document(document)
    from lanctl.core.session import PROJECT_KEYS

    replacement.project_base = {key: deepcopy(config.get(key)) for key in PROJECT_KEYS}
    replacement.base_values = deepcopy(dict(config))
    if any(path.startswith("monitor.") for path in expanded):
        from lanctl.apps.monitor.configuration import ConfigProvider, validate_monitor_settings

        validate_monitor_settings(replacement["monitor"])
        ConfigProvider(replacement).monitor()
    return replacement


def changed_values(before, after):
    original = dict(leaves(canonical_config(before)))
    return {
        path: value
        for path, value in leaves(canonical_config(after))
        if value != original.get(path)
    }
