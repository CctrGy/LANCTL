from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shutil
import sys
from dataclasses import MISSING, asdict, dataclass, field, make_dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock

from app import __version__
from app.core.config import load_config
from app.core.logger import write_database_log, write_log
from app.core.paths import application_path
from app.plugins.api import PluginApi
from app.plugins.contracts import DeviceRemoteEvent, EventContract, LifecycleEvent, NetworkScanEvent, ProjectFileEvent
from app.plugins.events import EventBus, EventRegistry
from app.plugins.extensions import ExtensionRegistry
from app.plugins.functions import FunctionRegistry
from app.plugins.models import PluginManifest, PluginState
from app.plugins.package import install_package, inspect_package, verify_package
from app.plugins.builtin import bootstrap_builtin_plugins
from app.gui_theme import validate_theme_specification


PLUGIN_ROOT = application_path("data/lc/plugins")
PLUGIN_REGISTRY = application_path("data/lc/plugins.registry")


@dataclass(slots=True)
class InstalledPlugin:
    manifest: PluginManifest
    path: Path
    state: PluginState = PluginState.DISABLED
    granted: set[str] | None = None
    trusted: bool = False
    error: str = ""
    module: object | None = None

    def __post_init__(self):
        self.granted = set(self.granted or ())


class PluginManager:
    def __init__(self, root: Path = PLUGIN_ROOT, registry_path: Path = PLUGIN_REGISTRY) -> None:
        self.root, self.registry_path = root, registry_path
        self.event_registry = EventRegistry()
        self.extensions = ExtensionRegistry()
        self.events = EventBus(self.event_registry, self.audit)
        self.functions = FunctionRegistry(self.audit)
        self.plugins: dict[str, InstalledPlugin] = {}
        self.initialized = False
        self._lock = RLock()
        self._register_core_events()
        bootstrap_builtin_plugins(self.root)
        self.discover()

    def _register_core_events(self) -> None:
        definitions = (
            ("LANCTL.Core.Lifecycle.Startup", LifecycleEvent, False),
            ("LANCTL.Core.Lifecycle.Shutdown", LifecycleEvent, False),
            ("LANCTL.Project.File.Open", ProjectFileEvent, False),
            ("LANCTL.Project.File.Save", ProjectFileEvent, False),
            ("LANCTL.Project.File.Reload", ProjectFileEvent, False),
            ("LANCTL.Project.File.Close", ProjectFileEvent, False),
            ("LANCTL.Network.Scan.BeforeStart", NetworkScanEvent, True),
            ("LANCTL.Network.Scan.Begin", NetworkScanEvent, False),
            ("LANCTL.Network.Scan.End", NetworkScanEvent, False),
            ("LANCTL.Device.Remote.Connect", DeviceRemoteEvent, False),
            ("LANCTL.Device.Remote.Disconnect", DeviceRemoteEvent, False),
        )
        for event_id, contract, cancelable in definitions:
            self.event_registry.register(event_id, contract, owner="LANCTL", cancelable=cancelable)

    def discover(self) -> list[InstalledPlugin]:
        persisted = self._read_registry()
        self.root.mkdir(parents=True, exist_ok=True)
        discovered: dict[str, InstalledPlugin] = {}
        for info in self.root.glob("*/plugin.info"):
            try:
                manifest = PluginManifest.from_dict(json.loads(info.read_text(encoding="utf-8")))
                saved = persisted.get(manifest.plugin_id, {})
                default_enabled = bool(manifest.raw.get("builtIn") and manifest.raw.get("defaultEnabled"))
                state = PluginState(saved.get("state", "ENABLED" if default_enabled else "DISABLED"))
                granted = set(saved.get("granted", manifest.permissions if default_enabled else []))
                discovered[manifest.plugin_id] = InstalledPlugin(
                    manifest, info.parent, state, granted,
                    bool(saved.get("trusted", False)), str(saved.get("error", "")),
                )
            except Exception as error:
                self.audit(info.parent.name, "DISCOVER", str(info), "ERROR", str(error))
        self.plugins = discovered
        return self.list()

    def activate_enabled(self) -> bool:
        if self.initialized:
            return False
        for plugin in self.list():
            if plugin.state == PluginState.ENABLED:
                try:
                    self._activate(plugin)
                except Exception as error:
                    self.events.unsubscribe_plugin(plugin.manifest.plugin_id)
                    self.event_registry.remove_owner(plugin.manifest.plugin_id)
                    self.extensions.remove_owner(plugin.manifest.plugin_id)
                    self.functions.remove_owner(plugin.manifest.plugin_id)
                    from app.i18n import get_language_manager
                    get_language_manager().remove_provider(plugin.manifest.plugin_id)
                    from app.assets.icons import get_icon_manager
                    get_icon_manager().remove_provider(plugin.manifest.plugin_id)
                    plugin.state, plugin.error = PluginState.ERROR, str(error)
                    self.audit(plugin.manifest.plugin_id, "LOAD", plugin.manifest.version, "ERROR", str(error))
        self._save_registry()
        self.initialized = True
        return True

    def install(self, package: str | Path) -> InstalledPlugin:
        incoming = inspect_package(package)
        existing = self.plugins.get(incoming.plugin_id)
        if existing and existing.manifest.raw.get("builtIn"):
            raise PermissionError("un complemento integrado no se puede reemplazar con plugin install")
        manifest, destination, result = install_package(package, self.root)
        plugin = InstalledPlugin(manifest, destination)
        self.plugins[manifest.plugin_id] = plugin
        self._save_registry()
        self.audit(manifest.plugin_id, "INSTALL", manifest.version, "OK", f"checksum={result['checksum']}")
        return plugin

    def uninstall(self, plugin_id: str) -> None:
        plugin = self.get(plugin_id)
        if plugin.manifest.raw.get("builtIn"):
            raise PermissionError("los complementos integrados pueden desactivarse, pero no desinstalarse")
        self.disable(plugin_id)
        shutil.rmtree(plugin.path)
        self.plugins.pop(plugin.manifest.plugin_id, None)
        self._save_registry()
        self.audit(plugin.manifest.plugin_id, "UNINSTALL", plugin.manifest.version, "OK")

    def enable(self, plugin_id: str, *, grant: set[str] | None = None, trusted: bool = False) -> InstalledPlugin:
        plugin = self.get(plugin_id)
        if grant is not None:
            plugin.granted = {item.casefold() for item in grant}
        requested = set(plugin.manifest.permissions)
        missing = requested - plugin.granted
        if missing:
            plugin.state = PluginState.BLOCKED
            plugin.error = f"permisos sin conceder: {', '.join(sorted(missing))}"
            self._save_registry()
            raise PermissionError(plugin.error)
        plugin.trusted = plugin.trusted or trusted
        self._check_compatibility(plugin)
        self._check_dependencies(plugin)
        plugin.error = ""
        try:
            self._activate(plugin)
        except Exception as error:
            self.events.unsubscribe_plugin(plugin.manifest.plugin_id)
            self.event_registry.remove_owner(plugin.manifest.plugin_id)
            self.extensions.remove_owner(plugin.manifest.plugin_id)
            self.functions.remove_owner(plugin.manifest.plugin_id)
            from app.i18n import get_language_manager
            get_language_manager().remove_provider(plugin.manifest.plugin_id)
            from app.assets.icons import get_icon_manager
            get_icon_manager().remove_provider(plugin.manifest.plugin_id)
            plugin.module = None
            plugin.state, plugin.error = PluginState.BLOCKED, str(error)
            self._save_registry()
            self.audit(plugin.manifest.plugin_id, "ENABLE", plugin.manifest.version, "ERROR", str(error))
            raise
        plugin.state = PluginState.ENABLED
        self._save_registry()
        self.audit(plugin.manifest.plugin_id, "ENABLE", plugin.manifest.version, "OK")
        return plugin

    def disable(self, plugin_id: str) -> InstalledPlugin:
        plugin = self.get(plugin_id)
        if plugin.module and hasattr(plugin.module, "deactivate"):
            try:
                plugin.module.deactivate()
            except Exception as error:
                self.audit(plugin.manifest.plugin_id, "UNLOAD", plugin.manifest.version, "ERROR", str(error))
        self.events.unsubscribe_plugin(plugin.manifest.plugin_id)
        self.event_registry.remove_owner(plugin.manifest.plugin_id)
        self.extensions.remove_owner(plugin.manifest.plugin_id)
        self.functions.remove_owner(plugin.manifest.plugin_id)
        from app.i18n import get_language_manager
        get_language_manager().remove_provider(plugin.manifest.plugin_id)
        from app.assets.icons import get_icon_manager
        get_icon_manager().remove_provider(plugin.manifest.plugin_id)
        plugin.module, plugin.state = None, PluginState.DISABLED
        self._save_registry()
        self.audit(plugin.manifest.plugin_id, "DISABLE", plugin.manifest.version, "OK")
        return plugin

    def reload(self, plugin_id: str) -> InstalledPlugin:
        plugin = self.get(plugin_id)
        granted, trusted = set(plugin.granted), plugin.trusted
        self.disable(plugin_id)
        return self.enable(plugin_id, grant=granted, trusted=trusted)

    def verify(self, plugin_id_or_file: str) -> dict:
        path = Path(plugin_id_or_file)
        if path.suffix.casefold() == ".lcp" or path.exists():
            return verify_package(path)
        plugin = self.get(plugin_id_or_file)
        return {"valid": True, "installed": True, "manifest": plugin.manifest, "path": str(plugin.path), "state": plugin.state.value}

    def get(self, plugin_id: str) -> InstalledPlugin:
        try:
            return self.plugins[plugin_id.casefold()]
        except KeyError as error:
            raise ValueError(f"plugin no instalado: {plugin_id}") from error

    def list(self) -> list[InstalledPlugin]:
        return sorted(self.plugins.values(), key=lambda item: item.manifest.name.casefold())

    def audit(self, plugin_id: str, action: str, target: str = "-", result: str = "OK", detail: str = "") -> None:
        clean = " | ".join(str(detail).splitlines()).strip()
        message = f"PLUGIN id={plugin_id} action={action} target={target} result={result}"
        if clean:
            message += f" detail={clean}"
        write_log(message)
        try:
            write_database_log(message)
        except (OSError, ValueError):
            pass

    def project_registry(self) -> dict:
        return {"schemaVersion": 1, "plugins": [
            {"id": p.manifest.plugin_id, "version": p.manifest.version, "state": p.state.value,
             "required": False, "capabilities": list(p.manifest.capabilities)} for p in self.list()
        ]}

    def _activate(self, plugin: InstalledPlugin) -> None:
        self._load_declarative_events(plugin)
        self._load_declarative_extensions(plugin)
        entry = plugin.path / plugin.manifest.entry_point
        if not entry.exists():
            return
        if plugin.manifest.runtime == "isolated":
            self.audit(plugin.manifest.plugin_id, "LOAD", plugin.manifest.version, "OK", "runtime=isolated declarative")
            return
        if not plugin.trusted:
            raise PermissionError("el código in-process requiere confianza explícita (--trust)")
        module_name = "lanctl_plugin_" + plugin.manifest.plugin_id.replace(".", "_").replace("-", "_")
        loader = importlib.machinery.SourceFileLoader(module_name, str(entry))
        spec = importlib.util.spec_from_loader(module_name, loader)
        if not spec:
            raise ImportError(f"no se puede cargar {entry}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        loader.exec_module(module)
        api = PluginApi(plugin.manifest.plugin_id, set(plugin.granted), self)
        self._load_declared_hooks(plugin, module)
        activate = getattr(module, "activate", None)
        if not callable(activate):
            raise ValueError("main.exec debe definir activate(api)")
        activate(api)
        plugin.module = module

    def _load_declared_hooks(self, plugin: InstalledPlugin, module) -> None:
        hooks = plugin.path / "api/hooks"
        if not hooks.exists():
            return
        if "events.listen" not in plugin.granted:
            raise PermissionError("falta el permiso events.listen para cargar hooks")
        for path in sorted(hooks.glob("*.hook")):
            document = json.loads(path.read_text(encoding="utf-8"))
            handler_name = str(document.get("handler", ""))
            handler = getattr(module, handler_name, None)
            if not callable(handler):
                raise ValueError(f"hook {path.name}: handler inexistente {handler_name}")
            self.events.subscribe(
                str(document["event"]), handler,
                plugin_id=plugin.manifest.plugin_id,
                version=int(document.get("version", 1)),
                priority=int(document.get("priority", 100)),
            )

    def _load_declarative_extensions(self, plugin: InstalledPlugin) -> None:
        api_map = plugin.path / "api/api.map"
        if not api_map.exists():
            return
        data = json.loads(api_map.read_text(encoding="utf-8"))
        for item in data.get("extensions", []):
            kind = str(item["type"]).casefold()
            specification = item.get("specification", {})
            permission = f"{kind}.register"
            if permission not in plugin.granted:
                raise PermissionError(f"falta el permiso {permission}")
            if kind == "command":
                import re
                name = str(specification.get("name", ""))
                if not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", name) or specification.get("action") not in {"inventory.summary"}:
                    raise ValueError(f"especificación de comando declarativo no válida: {item.get('id')}")
            if kind == "theme":
                specification = validate_theme_specification(specification)
            self.extensions.register(str(item["id"]), kind, plugin.manifest.plugin_id, specification)
            if kind == "language":
                relative = Path(str(specification.get("file", "")))
                target = (plugin.path / relative).resolve()
                if not relative.parts or ".." in relative.parts or not target.is_relative_to(plugin.path.resolve()):
                    raise ValueError("ruta de catálogo de idioma no segura")
                from app.i18n import get_language_manager
                language_manager = get_language_manager()
                catalog = language_manager.add_provider(plugin.manifest.plugin_id, target)
                configured = str(load_config().get("language", "en"))
                if language_manager.resolve_code(configured) == catalog.code:
                    language_manager.select(catalog.code)
            elif kind == "icon":
                relative = Path(str(specification.get("file", "")))
                target = (plugin.path / relative).resolve()
                if not relative.parts or ".." in relative.parts or not target.is_relative_to(plugin.path.resolve()):
                    raise ValueError("ruta de icono no segura")
                from app.assets.icons import get_icon_manager
                get_icon_manager().add_provider(
                    plugin.manifest.plugin_id, target,
                    icon_id=str(specification.get("iconId") or item["id"]),
                    name=str(specification.get("name") or item["id"]),
                    category=str(specification.get("category") or "general"),
                    tags=tuple(specification.get("tags", [])),
                )

    def _load_declarative_events(self, plugin: InstalledPlugin) -> None:
        schema_path = plugin.path / "api/events.schema"
        if not schema_path.exists():
            return
        if "events.register" not in plugin.granted:
            raise PermissionError("falta el permiso events.register")
        document = json.loads(schema_path.read_text(encoding="utf-8"))
        definitions = document.get("events", document)
        registry_path = plugin.path / "api/events.registry"
        class_names = {}
        if registry_path.exists():
            class_names = json.loads(registry_path.read_text(encoding="utf-8"))
        for event_id, spec in definitions.items():
            arguments = spec.get("arguments", {})
            required, optional = [], []
            for name, declared in arguments.items():
                kind = str(declared)
                is_optional = kind.endswith("?")
                annotation = _schema_type(kind.rstrip("?"))
                target = optional if is_optional else required
                target.append((name, annotation, field(default=None)) if is_optional else (name, annotation))
            class_name = class_names.get(event_id) or event_id.replace(".", "_")
            contract = make_dataclass(
                class_name, [*required, *optional], bases=(EventContract,),
                frozen=True, slots=True,
            )
            self.event_registry.register(
                event_id, contract, owner=plugin.manifest.plugin_id,
                version=int(spec.get("version", 1)),
                cancelable=bool(spec.get("cancelable", False)),
            )

    def _check_dependencies(self, plugin: InstalledPlugin) -> None:
        missing = [dep.plugin_id for dep in plugin.manifest.dependencies if dep.plugin_id not in self.plugins or self.plugins[dep.plugin_id].state != PluginState.ENABLED]
        if missing:
            raise ValueError(f"dependencias no activas: {', '.join(missing)}")

    def _check_compatibility(self, plugin: InstalledPlugin) -> None:
        # Comparación conservadora de versiones numéricas base; prereleases comparten base.
        current = _version_tuple(__version__)
        if current < _version_tuple(plugin.manifest.minimum_lanctl):
            plugin.state = PluginState.INCOMPATIBLE
            raise ValueError(f"requiere LANCTL >= {plugin.manifest.minimum_lanctl}")
        maximum = plugin.manifest.maximum_lanctl
        if maximum not in ("", "*") and not _matches_maximum(current, maximum):
            plugin.state = PluginState.INCOMPATIBLE
            raise ValueError(f"no es compatible con LANCTL {__version__}")

    def _read_registry(self) -> dict:
        if not self.registry_path.exists():
            return {}
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            return data.get("plugins", {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_registry(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"schemaVersion": 1, "plugins": {p.manifest.plugin_id: {
            "state": p.state.value, "granted": sorted(p.granted), "trusted": p.trusted,
            "error": p.error, "version": p.manifest.version,
        } for p in self.list()}}
        temporary = self.registry_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.registry_path)


def _version_tuple(value: str) -> tuple[int, int, int]:
    numbers = []
    for part in value.split("-", 1)[0].split(".")[:3]:
        try: numbers.append(int(part))
        except ValueError: numbers.append(0)
    return tuple((numbers + [0, 0, 0])[:3])


def _matches_maximum(current: tuple[int, int, int], maximum: str) -> bool:
    if maximum.endswith(".x"):
        prefix = tuple(int(v) for v in maximum[:-2].split(".") if v)
        return current[:len(prefix)] == prefix
    return current <= _version_tuple(maximum)


def _schema_type(value: str):
    return {
        "string": str, "integer": int, "number": float, "boolean": bool,
        "datetime": datetime, "object": dict, "array": list,
    }.get(value.casefold(), object)


_MANAGER: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = PluginManager()
    return _MANAGER
