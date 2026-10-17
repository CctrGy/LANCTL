from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import re
import shutil
import sys
from contextlib import suppress
from copy import deepcopy
from dataclasses import dataclass, field, make_dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from threading import RLock

from lanctl import __version__
from lanctl.core.config import load_config
from lanctl.core.file_transaction import atomic_write_json, locked_file
from lanctl.core.logger import write_database_log, write_log
from lanctl.core.paths import application_path
from lanctl.core.plugins.api import PluginApi
from lanctl.core.plugins.authorization import RuntimeAuthorizations
from lanctl.core.plugins.builtin import BUILTIN_PLUGIN_IDS, bootstrap_builtin_plugins
from lanctl.core.plugins.contracts import (
    DeviceRemoteEvent,
    EventContract,
    LifecycleEvent,
    NetworkLabEvent,
    NetworkScanEvent,
    ProjectFileEvent,
)
from lanctl.core.plugins.events import EventBus, EventRegistry
from lanctl.core.plugins.extensions import ExtensionRegistry
from lanctl.core.plugins.functions import FunctionRegistry
from lanctl.core.plugins.models import PluginManifest, PluginState
from lanctl.core.plugins.package import (
    inspect_package,
    install_package,
    verify_directory,
    verify_package,
)
from lanctl.core.plugins.publishers import TrustedPublisherStore
from lanctl.core.plugins.theme import validate_theme_specification

PLUGIN_ROOT = application_path("data/lc/plugins")
PLUGIN_REGISTRY = application_path("data/lc/plugins.registry")


def _synchronized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        depth = self._authorization.depth
        depth.value = getattr(depth, "value", 0) + 1
        try:
            with self._lock, locked_file(self.registry_path):
                return method(self, *args, **kwargs)
        finally:
            depth.value -= 1
            if not depth.value:
                # External deactivate/stop runs only after all registry locks
                # in this thread have been released.
                self._authorization.drain()

    return wrapped


@dataclass(slots=True)
class InstalledPlugin:
    manifest: PluginManifest
    path: Path
    state: PluginState = PluginState.DISABLED
    granted: set[str] | None = None
    trusted: bool = False
    error: str = ""
    signature: str = "UNSIGNED"
    checksum: str = ""
    module: object | None = None
    isolated_runtime: object | None = None
    restart_required: bool = False

    def __post_init__(self):
        self.granted = set(self.granted or ())


class PluginManager:
    def __init__(self, root: Path = PLUGIN_ROOT, registry_path: Path = PLUGIN_REGISTRY) -> None:
        self.root, self.registry_path = root, registry_path
        self.publishers = TrustedPublisherStore(registry_path.with_name("trusted-publishers.json"))
        self.event_registry = EventRegistry()
        self.extensions = ExtensionRegistry()
        self.events = EventBus(self.event_registry, self.audit)
        self.functions = FunctionRegistry(self.audit)
        self.plugins: dict[str, InstalledPlugin] = {}
        self.initialized = False
        self._active: set[str] = set()
        self._registry_known: dict = {}
        self._registry_baseline: dict = {}
        self._lock = RLock()
        self._authorization = RuntimeAuthorizations(self)
        self._register_core_events()
        bootstrap_builtin_plugins(self.root)
        self.discover()

    def _register_core_events(self) -> None:
        from lanctl.core.plugins.contracts import VaultOperationEvent

        definitions = (
            ("LANCTL.Access.Vault.Completed", VaultOperationEvent, False),
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
            ("LANCTL.Network.Lab.Created", NetworkLabEvent, False),
            ("LANCTL.Network.Lab.Start", NetworkLabEvent, False),
            ("LANCTL.Network.Lab.Stop", NetworkLabEvent, False),
            ("LANCTL.Network.Lab.Tick", NetworkLabEvent, False),
            ("LANCTL.Network.Lab.Host", NetworkLabEvent, False),
            ("LANCTL.Network.Lab.Anomaly", NetworkLabEvent, False),
            ("LANCTL.Network.Lab.Error", NetworkLabEvent, False),
        )
        for event_id, contract, cancelable in definitions:
            self.event_registry.register(event_id, contract, owner="LANCTL", cancelable=cancelable)

    @_synchronized
    def discover(self) -> list[InstalledPlugin]:
        persisted = self._read_registry()
        for plugin in self.plugins.values():
            self._release_runtime(plugin)
        self.initialized = False
        self.root.mkdir(parents=True, exist_ok=True)
        discovered: dict[str, InstalledPlugin] = {}
        infos = [
            *self.root.glob("*/plugin.info"),
            *sorted((self.root / ".quarantine").glob("*/plugin.info"), reverse=True),
        ]
        for info in infos:
            try:
                manifest = PluginManifest.from_dict(json.loads(info.read_text(encoding="utf-8")))
                quarantined = info.parent.parent == self.root / ".quarantine"
                saved = persisted.get(manifest.plugin_id, {})
                if quarantined and (
                    manifest.plugin_id in discovered or saved.get("state") != "QUARANTINED"
                ):
                    continue
                if not quarantined and info.parent.name != manifest.plugin_id:
                    raise ValueError("el directorio no coincide con el id del plugin")
                is_builtin = manifest.plugin_id in BUILTIN_PLUGIN_IDS
                # La procedencia integrada pertenece al núcleo, nunca al manifiesto
                # controlado por el complemento.
                manifest.raw["builtIn"] = is_builtin
                default_enabled = bool(is_builtin and manifest.raw.get("defaultEnabled"))
                expected_checksum = str(saved.get("checksum", "")).casefold()
                try:
                    if quarantined:
                        raise ValueError(
                            "el plugin sigue en cuarentena; reinstala un LCP verificado"
                        )
                    verified = verify_directory(
                        info.parent,
                        expected_checksum=expected_checksum,
                        expected_signature=saved.get("signature"),
                    )
                except (OSError, ValueError) as error:
                    quarantine = (
                        info.parent if quarantined else self._quarantine_path(manifest.plugin_id)
                    )
                    try:
                        info.parent.replace(quarantine)
                        plugin_path = quarantine
                    except OSError:
                        plugin_path = info.parent
                    discovered[manifest.plugin_id] = InstalledPlugin(
                        manifest,
                        plugin_path,
                        PluginState.QUARANTINED,
                        set(),
                        False,
                        f"integridad del plugin modificada: {error}",
                        str(saved.get("signature", "UNSIGNED")),
                        expected_checksum,
                    )
                    self.audit(
                        manifest.plugin_id,
                        "INTEGRITY",
                        str(info.parent),
                        "QUARANTINED",
                        str(error),
                    )
                    continue
                state = PluginState(
                    saved.get("state", "ENABLED" if default_enabled else "DISABLED")
                )
                granted = set(saved.get("granted", manifest.permissions if default_enabled else []))
                discovered[manifest.plugin_id] = InstalledPlugin(
                    manifest,
                    info.parent,
                    state,
                    granted,
                    bool(saved.get("trusted", False)),
                    str(saved.get("error", "")),
                    verified["signature"],
                    verified["checksum"],
                )
            except Exception as error:  # noqa: BLE001 - manifiesto externo
                from lanctl.core.errors import errors

                errors.from_exception(
                    error,
                    origin="LANCTL.Plugin.Discovery.Manifest",
                    code="PLUGIN.MANIFEST.SKIPPED",
                    level=16,
                    details={"path": str(info)},
                    print_output=False,
                )
                self.audit(info.parent.name, "DISCOVER", str(info), "ERROR", str(error))
        self.plugins = discovered
        self._registry_known = deepcopy(persisted)
        self._registry_baseline = self._registry_entries()
        for plugin_id, plugin in self.plugins.items():
            if plugin.state == PluginState.QUARANTINED:
                self._registry_baseline[plugin_id] = deepcopy(persisted.get(plugin_id, {}))
        if any(p.state == PluginState.QUARANTINED for p in self.plugins.values()):
            self._save_registry()
        return self.list()

    @_synchronized
    def activate_enabled(self) -> bool:
        if self.initialized:
            from lanctl.core.errors import errors

            errors.emit(
                level=6,
                origin="LANCTL.Plugin.Activation.State",
                code="PLUGIN.ACTIVATION.ALREADY_INITIALIZED",
                message="Se omitió una segunda inicialización de plugins",
                print_output=False,
                once_key="plugins.activation.already-initialized",
            )
            return False
        if self._read_registry() != self._registry_known:
            self.discover()
        pending = {p.manifest.plugin_id: p for p in self.list() if p.state == PluginState.ENABLED}
        while pending:
            ready = [
                p
                for p in pending.values()
                if not any(d.plugin_id in pending for d in p.manifest.dependencies)
            ]
            if not ready:
                # A dependency cycle cannot be activated in any order.
                ready = list(pending.values())
            for plugin in ready:
                pending.pop(plugin.manifest.plugin_id)
                try:
                    self._validate_activation(plugin)
                    if plugin.manifest.plugin_id not in self._active:
                        self._activate(plugin)
                        self._active.add(plugin.manifest.plugin_id)
                    plugin.error = ""
                except Exception as error:  # noqa: BLE001 - código de plugin
                    from lanctl.core.errors import errors

                    errors.from_exception(
                        error,
                        origin="LANCTL.Plugin.Activation.Startup",
                        code="PLUGIN.ACTIVATION.ISOLATED",
                        level=18,
                        details={"pluginId": plugin.manifest.plugin_id},
                        print_output=False,
                    )
                    self._release_runtime(plugin)
                    if plugin.state not in (PluginState.INCOMPATIBLE, PluginState.QUARANTINED):
                        plugin.state = PluginState.ERROR
                    plugin.error = str(error)
                    self.audit(
                        plugin.manifest.plugin_id,
                        "LOAD",
                        plugin.manifest.version,
                        "ERROR",
                        str(error),
                    )
        try:
            self._save_registry()
        except OSError as error:
            for plugin in self.plugins.values():
                if plugin.manifest.plugin_id in self._active:
                    self._release_runtime(plugin)
                    plugin.state, plugin.error = PluginState.ERROR, str(error)
            raise
        self.initialized = True
        return True

    @_synchronized
    def install(self, package: str | Path) -> InstalledPlugin:
        incoming = inspect_package(package)
        if self._read_registry().get(incoming.plugin_id) != self._registry_known.get(
            incoming.plugin_id
        ):
            raise ValueError(
                f"el estado de {incoming.plugin_id} cambió en otro proceso; recarga los plugins"
            )
        existing = self.plugins.get(incoming.plugin_id)
        if existing:
            self._ensure_current(existing)
        if incoming.plugin_id in BUILTIN_PLUGIN_IDS or (
            existing and existing.manifest.plugin_id in BUILTIN_PLUGIN_IDS
        ):
            raise PermissionError(
                "un complemento integrado no se puede reemplazar con plugin install"
            )
        # Verify first so a rejected replacement does not interrupt a valid runtime.
        verify_package(package)
        if existing:
            self.disable(existing.manifest.plugin_id)
        manifest, destination, result = install_package(package, self.root)
        plugin = InstalledPlugin(
            manifest,
            destination,
            signature=str(result["signature"]),
            checksum=str(result["checksum"]),
        )
        self.plugins[manifest.plugin_id] = plugin
        self._save_registry()
        self.audit(
            manifest.plugin_id, "INSTALL", manifest.version, "OK", f"checksum={result['checksum']}"
        )
        return plugin

    @_synchronized
    def uninstall(self, plugin_id: str) -> None:
        plugin = self.get(plugin_id)
        if plugin.manifest.plugin_id in BUILTIN_PLUGIN_IDS:
            raise PermissionError(
                "los complementos integrados pueden desactivarse, pero no desinstalarse"
            )
        self.disable(plugin_id)
        shutil.rmtree(plugin.path)
        self.plugins.pop(plugin.manifest.plugin_id, None)
        self._save_registry()
        self.audit(plugin.manifest.plugin_id, "UNINSTALL", plugin.manifest.version, "OK")

    @_synchronized
    def enable(
        self, plugin_id: str, *, grant: set[str] | None = None, trusted: bool = False
    ) -> InstalledPlugin:
        plugin = self.get(plugin_id)
        self._ensure_current(plugin)
        previous_grants = set(plugin.granted)
        if grant is not None:
            plugin.granted = {item.casefold() for item in grant}
        plugin.trusted = plugin.trusted or trusted
        try:
            self._validate_activation(plugin)
            if plugin.manifest.plugin_id in self._active and previous_grants == plugin.granted:
                return plugin
            self._release_runtime(plugin)
            self._activate(plugin)
            self._active.add(plugin.manifest.plugin_id)
            plugin.state = PluginState.ENABLED
            plugin.error = ""
            self._save_registry()
        except Exception as error:
            self._release_runtime(plugin)
            if plugin.state not in (PluginState.INCOMPATIBLE, PluginState.QUARANTINED):
                plugin.state = PluginState.BLOCKED
            plugin.error = str(error)
            # A failed atomic write must not leave executable code active. Keep
            # the original exception if persisting the failure also hits the disk error.
            with suppress(OSError):
                self._save_registry()
            self.audit(
                plugin.manifest.plugin_id, "ENABLE", plugin.manifest.version, "ERROR", str(error)
            )
            raise
        self.audit(plugin.manifest.plugin_id, "ENABLE", plugin.manifest.version, "OK")
        return plugin

    def _release_runtime(self, plugin: InstalledPlugin) -> None:
        self._active.discard(plugin.manifest.plugin_id)
        module = plugin.module
        self._authorization.retire(plugin)
        self.events.unsubscribe_plugin(plugin.manifest.plugin_id)
        self.event_registry.remove_owner(plugin.manifest.plugin_id)
        self.extensions.remove_owner(plugin.manifest.plugin_id)
        self.functions.remove_owner(plugin.manifest.plugin_id)
        from lanctl.shared.i18n import get_language_manager

        get_language_manager().remove_provider(plugin.manifest.plugin_id)
        from lanctl.shared.assets.icons import get_icon_manager

        get_icon_manager().remove_provider(plugin.manifest.plugin_id)
        checks = getattr(self, "monitor_checks", None)
        if checks is not None:
            checks.remove_owner(plugin.manifest.plugin_id)
        if module is not None and sys.modules.get(module.__name__) is module:
            sys.modules.pop(module.__name__, None)

    @_synchronized
    def disable(self, plugin_id: str) -> InstalledPlugin:
        plugin = self.get(plugin_id)
        self._ensure_current(plugin)
        self._release_runtime(plugin)
        if plugin.state != PluginState.QUARANTINED:
            plugin.state = PluginState.DISABLED
            plugin.error = ""
        for dependent in list(self.plugins.values()):
            if dependent.manifest.plugin_id in self._active and any(
                d.plugin_id == plugin.manifest.plugin_id for d in dependent.manifest.dependencies
            ):
                self.disable(dependent.manifest.plugin_id)
        self._save_registry()
        self.audit(plugin.manifest.plugin_id, "DISABLE", plugin.manifest.version, "OK")
        return plugin

    def reload(self, plugin_id: str) -> InstalledPlugin:
        with self._lock:
            plugin = self.get(plugin_id)
            granted, trusted = set(plugin.granted), plugin.trusted
        self.disable(plugin_id)
        return self.enable(plugin_id, grant=granted, trusted=trusted)

    @_synchronized
    def revoke(self, plugin_id: str, permissions: set[str] | None = None) -> InstalledPlugin:
        """Revoca permisos y desactiva el plugin si deja de cumplir su manifiesto."""

        plugin = self.get(plugin_id)
        self._ensure_current(plugin)
        revoked = (
            set(plugin.granted)
            if permissions is None
            else {item.casefold() for item in permissions}
        )
        unknown = revoked - set(plugin.granted)
        if unknown:
            raise ValueError(f"permisos no concedidos: {', '.join(sorted(unknown))}")
        if plugin.state == PluginState.ENABLED:
            self.disable(plugin_id)
        plugin.granted.difference_update(revoked)
        plugin.trusted = False
        plugin.error = (
            f"permisos revocados: {', '.join(sorted(revoked))}" if revoked else "confianza revocada"
        )
        self._save_registry()
        self.audit(
            plugin.manifest.plugin_id,
            "REVOKE",
            ",".join(sorted(revoked)) or "trust",
            "OK",
        )
        return plugin

    @_synchronized
    def verify(self, plugin_id_or_file: str) -> dict:
        path = Path(plugin_id_or_file)
        if path.suffix.casefold() == ".lcp" or path.exists():
            return verify_package(path)
        plugin = self.get(plugin_id_or_file)
        verified = self._verify_installed(plugin)
        return {
            **verified,
            "installed": True,
            "manifest": plugin.manifest,
            "path": str(plugin.path),
            "state": plugin.state.value,
        }

    def get(self, plugin_id: str) -> InstalledPlugin:
        try:
            return self.plugins[plugin_id.casefold()]
        except KeyError as error:
            raise ValueError(f"plugin no instalado: {plugin_id}") from error

    def list(self) -> list[InstalledPlugin]:
        return sorted(self.plugins.values(), key=lambda item: item.manifest.name.casefold())

    @_synchronized
    def refresh_authorizations(self) -> None:
        """Reconcile revocation without automatically granting or loading code."""
        try:
            current = self._read_registry()
            publishers = self.publishers._read()
        except (OSError, ValueError):
            for plugin in tuple(self.plugins.values()):
                if plugin.manifest.plugin_id in self._authorization.leases:
                    self._release_runtime(plugin)
                    plugin.state = PluginState.BLOCKED
                    plugin.error = (
                        "Autorización no verificable; se han retirado los accesos al Core"
                    )
            # Do not write a corrupt or unavailable authority back to disk.
            self._registry_baseline = self._registry_entries()
            raise
        observed = set()
        for plugin_id, plugin in tuple(self.plugins.items()):
            saved = current.get(plugin_id)
            changed = saved != self._registry_known.get(plugin_id)
            untrusted = (
                plugin.manifest.runtime == "trusted"
                and plugin_id in self._authorization.leases
                and plugin.signature.removeprefix("VALID_ED25519:").casefold() not in publishers
            )
            runtime = plugin.isolated_runtime
            terminated = (
                plugin_id in self._active
                and runtime is not None
                and (runtime.process is None or not runtime.process.is_alive())
            )
            if not changed and not untrusted and not terminated:
                continue
            self._release_runtime(plugin)
            if saved is not None:
                plugin.granted = set(saved.get("granted", ()))
                plugin.trusted = bool(saved.get("trusted", False))
                state = PluginState(saved.get("state", "DISABLED"))
            else:
                plugin.granted = set()
                plugin.trusted = False
                state = PluginState.DISABLED
            plugin.state = PluginState.BLOCKED if state == PluginState.ENABLED else state
            plugin.error = (
                "Editor revocado; accesos al Core retirados"
                if untrusted
                else "Autorización modificada en otro proceso; recarga antes de activar"
            )
            if terminated:
                plugin.state = PluginState.ERROR
                plugin.error = "El proceso aislado terminó; se han retirado los accesos al Core"
            observed.add(plugin_id)
        # Revocation cascades through every level of active dependencies.
        while True:
            dependents = [
                p
                for p in self.plugins.values()
                if p.manifest.plugin_id in self._active
                and any(d.plugin_id not in self._active for d in p.manifest.dependencies)
            ]
            if not dependents:
                break
            for plugin in dependents:
                self._release_runtime(plugin)
                plugin.state = PluginState.BLOCKED
                plugin.error = "Dependencia revocada o desactivada; recarga antes de activar"
                observed.add(plugin.manifest.plugin_id)
        if observed:
            entries = self._registry_entries()
            for plugin_id in observed:
                if plugin_id in current:
                    self._registry_known[plugin_id] = deepcopy(current[plugin_id])
                else:
                    self._registry_known.pop(plugin_id, None)
                self._registry_baseline[plugin_id] = deepcopy(entries[plugin_id])

    def runtime_status(self, plugin_id: str) -> dict:
        self.refresh_authorizations()
        with self._lock:
            plugin = self.get(plugin_id)
            closing = self._authorization.cleanups.get(plugin.manifest.plugin_id)
            return {
                "schemaVersion": 1,
                "active": plugin.manifest.plugin_id in self._active,
                "coreAccess": plugin.manifest.plugin_id in self._authorization.leases,
                "restartRequired": plugin.restart_required
                or plugin.manifest.plugin_id in self._authorization.restart_required,
                "cleanupPending": bool(closing and (closing.ident is None or closing.is_alive())),
                "execution": "legacy-in-process"
                if plugin.manifest.runtime == "trusted"
                else "isolated",
            }

    @_synchronized
    def close(self) -> None:
        self._authorization.stopped.set()
        for plugin in tuple(self.plugins.values()):
            self._release_runtime(plugin)
        self.initialized = False

    def _quarantine_path(self, plugin_id: str) -> Path:
        root = self.root / ".quarantine"
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
        return root / f"{plugin_id}-{stamp}"

    def audit(
        self, plugin_id: str, action: str, target: str = "-", result: str = "OK", detail: str = ""
    ) -> None:
        clean = " | ".join(str(detail).splitlines()).strip()
        message = f"PLUGIN id={plugin_id} action={action} target={target} result={result}"
        if clean:
            message += f" detail={clean}"
        write_log(message)
        with suppress(OSError, ValueError):
            write_database_log(message)

    def project_registry(self) -> dict:
        return {
            "schemaVersion": 1,
            "plugins": [
                {
                    "id": p.manifest.plugin_id,
                    "version": p.manifest.version,
                    "state": p.state.value,
                    "required": False,
                    "capabilities": list(p.manifest.capabilities),
                }
                for p in self.list()
            ],
        }

    def _activate(self, plugin: InstalledPlugin) -> None:
        self._authorization.begin(plugin.manifest.plugin_id)
        self._load_declarative_events(plugin)
        self._load_declarative_extensions(plugin)
        entry = plugin.path / plugin.manifest.entry_point
        if not entry.exists():
            return
        if plugin.manifest.runtime == "isolated":
            from lanctl.core.plugins.isolated_runtime import IsolatedPluginRuntime
            from lanctl.core.plugins.settings import PluginSettings

            limits = plugin.manifest.raw.get("limits", {})
            plugin.isolated_runtime = IsolatedPluginRuntime(
                plugin.manifest.plugin_id,
                entry,
                timeout=float(limits.get("timeoutSeconds", 5)),
                memory_mb=int(limits.get("memoryMb", 128)),
                max_calls=int(limits.get("maxCalls", 1000)),
                audit=self.audit,
                settings=PluginSettings(plugin).load(),
            ).start()
            self.audit(
                plugin.manifest.plugin_id,
                "LOAD",
                plugin.manifest.version,
                "OK",
                f"runtime=isolated pid={plugin.isolated_runtime.pid}",
            )
            return
        if not plugin.trusted:
            raise PermissionError("el código in-process requiere confianza explícita (--trust)")
        if plugin.manifest.plugin_id not in BUILTIN_PLUGIN_IDS and not self.publishers.is_trusted(
            plugin.signature
        ):
            raise PermissionError("la firma del editor trusted no está autorizada o fue revocada")
        module_name = "lanctl_plugin_" + plugin.manifest.plugin_id.replace(".", "_").replace(
            "-", "_"
        )
        loader = importlib.machinery.SourceFileLoader(module_name, str(entry))
        spec = importlib.util.spec_from_loader(module_name, loader)
        if not spec:
            raise ImportError(f"no se puede cargar {entry}")
        module = importlib.util.module_from_spec(spec)
        plugin.module = module
        sys.modules[module_name] = module
        previous_bytecode_policy = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous_bytecode_policy
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
                str(document["event"]),
                self._authorization.guarded(
                    plugin.manifest.plugin_id,
                    self._authorization.leases[plugin.manifest.plugin_id],
                    handler,
                    "events.listen",
                ),
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
                action = specification.get("action")
                function_id = str(specification.get("function", ""))
                valid_function = action != "function.call" or bool(
                    re.fullmatch(
                        r"(?!LANCTL\.)[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z][A-Za-z0-9_-]*){2,}",
                        function_id,
                        re.IGNORECASE,
                    )
                )
                if (
                    not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", name)
                    or action not in {"inventory.summary", "function.call"}
                    or not valid_function
                ):
                    raise ValueError(
                        f"especificación de comando declarativo no válida: {item.get('id')}"
                    )
            if kind == "theme":
                specification = validate_theme_specification(specification)
            if kind in {"ui-panel", "ui-action"}:
                from lanctl.core.plugins.ui_contracts import (
                    validate_ui_action,
                    validate_ui_panel,
                )

                specification = (
                    validate_ui_panel(specification)
                    if kind == "ui-panel"
                    else validate_ui_action(specification)
                )
            self.extensions.register(
                str(item["id"]), kind, plugin.manifest.plugin_id, specification
            )
            if kind == "language":
                relative = Path(str(specification.get("file", "")))
                target = (plugin.path / relative).resolve()
                if (
                    not relative.parts
                    or ".." in relative.parts
                    or not target.is_relative_to(plugin.path.resolve())
                ):
                    raise ValueError("ruta de catálogo de idioma no segura")
                from lanctl.shared.i18n import get_language_manager

                language_manager = get_language_manager()
                catalog = language_manager.add_provider(plugin.manifest.plugin_id, target)
                configured = str(load_config().get("language", "en"))
                if language_manager.resolve_code(configured) == catalog.code:
                    language_manager.select(catalog.code)
            elif kind == "icon":
                relative = Path(str(specification.get("file", "")))
                target = (plugin.path / relative).resolve()
                if (
                    not relative.parts
                    or ".." in relative.parts
                    or not target.is_relative_to(plugin.path.resolve())
                ):
                    raise ValueError("ruta de icono no segura")
                from lanctl.shared.assets.icons import get_icon_manager

                get_icon_manager().add_provider(
                    plugin.manifest.plugin_id,
                    target,
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
                target.append(
                    (name, annotation, field(default=None)) if is_optional else (name, annotation)
                )
            class_name = class_names.get(event_id) or event_id.replace(".", "_")
            contract = make_dataclass(
                class_name,
                [*required, *optional],
                bases=(EventContract,),
                frozen=True,
                slots=True,
            )
            self.event_registry.register(
                event_id,
                contract,
                owner=plugin.manifest.plugin_id,
                version=int(spec.get("version", 1)),
                cancelable=bool(spec.get("cancelable", False)),
            )

    def _verify_installed(self, plugin: InstalledPlugin) -> dict:
        if plugin.state == PluginState.QUARANTINED:
            raise ValueError("integridad del plugin no válida; reinstala un LCP verificado")
        try:
            result = verify_directory(
                plugin.path,
                expected_checksum=plugin.checksum,
                expected_signature=plugin.signature,
            )
            if result["manifest"].plugin_id != plugin.manifest.plugin_id:
                raise ValueError("integridad del plugin modificada: id distinto")
            return result
        except (OSError, ValueError):
            self._release_runtime(plugin)
            plugin.state = PluginState.QUARANTINED
            plugin.error = "integridad del plugin modificada; reinstala un LCP verificado"
            self._save_registry()
            raise

    def _validate_activation(self, plugin: InstalledPlugin) -> None:
        self._verify_installed(plugin)
        requested = set(plugin.manifest.permissions)
        missing = requested - plugin.granted
        if missing:
            raise PermissionError(f"permisos sin conceder: {', '.join(sorted(missing))}")
        extra = plugin.granted - requested
        if extra:
            raise PermissionError(f"permisos no solicitados: {', '.join(sorted(extra))}")
        self._check_compatibility(plugin)
        self._check_dependencies(plugin)
        if plugin.manifest.runtime == "trusted":
            if not plugin.signature.startswith("VALID_ED25519:"):
                raise PermissionError(
                    "el runtime trusted requiere un LCP firmado por un editor confiable; "
                    "el paquete instalado no tiene firma; instala el LCP firmado por su editor"
                )
            if not self.publishers.is_trusted(plugin.signature):
                raise PermissionError(
                    "el runtime trusted requiere un editor confiable; la firma es válida "
                    "pero su editor no está autorizado o fue revocado; usa plugin publisher trust"
                )
            if not plugin.trusted:
                raise PermissionError("el código in-process requiere confianza explícita (--trust)")

    def _check_dependencies(self, plugin: InstalledPlugin) -> None:
        missing = [
            dep.plugin_id
            for dep in plugin.manifest.dependencies
            if dep.plugin_id not in self.plugins
            or self.plugins[dep.plugin_id].state != PluginState.ENABLED
            or dep.plugin_id not in self._active
        ]
        if missing:
            raise ValueError(f"dependencias no activas: {', '.join(missing)}")
        for dep in plugin.manifest.dependencies:
            if not _matches_dependency(self.plugins[dep.plugin_id].manifest.version, dep.version):
                raise ValueError(
                    f"dependencia incompatible: {dep.plugin_id} requiere {dep.version}"
                )

    def _check_compatibility(self, plugin: InstalledPlugin) -> None:
        # Se comparan los componentes numéricos de la versión; las versiones
        # preliminares comparten la misma base que su versión estable.
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
            with locked_file(self.registry_path):
                data = json.loads(self.registry_path.read_text(encoding="utf-8"))
                # Legacy initialization wrote exactly an empty object, without a schema.
                # Migrate only that format; never recover authorization from invalid data.
                if data == {}:
                    data = {"schemaVersion": 1, "plugins": {}}
                    atomic_write_json(self.registry_path, data)
            if not isinstance(data, dict) or data.get("schemaVersion") != 1:
                raise ValueError("schema de registro no compatible")
            values = data.get("plugins")
            if not isinstance(values, dict):
                raise ValueError("plugins debe ser un objeto")
            for key, entry in values.items():
                if not isinstance(entry, dict):
                    raise ValueError(f"entrada no válida: {key}")
                PluginState(entry.get("state", "DISABLED"))
                granted = entry.get("granted", [])
                if (
                    not isinstance(granted, list)
                    or not all(isinstance(p, str) for p in granted)
                    or not isinstance(entry.get("trusted", False), bool)
                    or any(
                        not isinstance(entry.get(k, ""), str)
                        for k in ("checksum", "signature", "error", "version")
                    )
                ):
                    raise ValueError(f"autorización no válida: {key}")
            return values
        except (ValueError, OSError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.Plugin.Registry.Load",
                code="PLUGIN.REGISTRY.FALLBACK",
                level=18,
                details={"path": str(self.registry_path)},
                print_output=False,
            )
            raise ValueError(f"registro de plugins no válido: {self.registry_path}") from error

    def _registry_entries(self) -> dict:
        return {
            p.manifest.plugin_id: {
                "state": p.state.value,
                "granted": sorted(p.granted),
                "trusted": p.trusted,
                "error": p.error,
                "signature": p.signature,
                "checksum": p.checksum,
                "version": p.manifest.version,
            }
            for p in self.plugins.values()
        }

    def _ensure_current(self, plugin: InstalledPlugin) -> None:
        plugin_id = plugin.manifest.plugin_id
        if self._read_registry().get(plugin_id) != self._registry_known.get(plugin_id):
            self._release_runtime(plugin)
            plugin.state = PluginState.BLOCKED
            plugin.error = (
                f"el estado de {plugin_id} cambió en otro proceso; vuelve a cargar los plugins"
            )
            # This local refusal must not overwrite the newer persisted authorization.
            self._registry_baseline[plugin_id] = self._registry_entries()[plugin_id]
            raise ValueError(plugin.error)

    def _save_registry(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with locked_file(self.registry_path):
            current = self._read_registry()
            entries = self._registry_entries()
            changed = {
                key for key, value in entries.items() if self._registry_baseline.get(key) != value
            }
            removed = self._registry_baseline.keys() - entries.keys()
            for key in changed | removed:
                if current.get(key) not in (self._registry_known.get(key), entries.get(key)):
                    raise ValueError(
                        f"el registro de {key} cambió en otro proceso; recarga los plugins"
                    )
            for key in removed:
                current.pop(key, None)
            for key, entry in entries.items():
                if key in changed or (key not in current and key not in self._registry_known):
                    current[key] = entry
            atomic_write_json(self.registry_path, {"schemaVersion": 1, "plugins": current})
            # Keep the observed revision only for entries this manager actually owns.
            # Unchanged local objects may still be stale compared with another process.
            for key in changed:
                self._registry_known[key] = deepcopy(entries[key])
            for key in removed:
                self._registry_known.pop(key, None)
            for key in entries:
                if key not in self._registry_known and entries[key] == current.get(key):
                    self._registry_known[key] = deepcopy(entries[key])
            self._registry_baseline = deepcopy(entries)


def _version_tuple(value: str) -> tuple[int, int, int]:
    numbers = []
    for part in value.split("-", 1)[0].split(".")[:3]:
        try:
            numbers.append(int(part))
        except ValueError:
            numbers.append(0)
    return tuple([*numbers, 0, 0, 0][:3])


def _matches_maximum(current: tuple[int, int, int], maximum: str) -> bool:
    if maximum.endswith(".x"):
        prefix = tuple(int(v) for v in maximum[:-2].split(".") if v)
        return current[: len(prefix)] == prefix
    return current <= _version_tuple(maximum)


def _matches_dependency(version: str, requirement: str) -> bool:
    if requirement.strip() in ("", "*"):
        return True
    current = _version_tuple(version)
    for part in requirement.split(","):
        match = re.fullmatch(
            r"\s*(>=|<=|==|!=|>|<|=)?\s*(\d+(?:\.\d+){0,2}|\d+(?:\.\d+)?\.[x*])\s*", part
        )
        if not match:
            raise ValueError(f"versión de dependencia no válida: {requirement}")
        operator, expected = match.groups()
        if expected.endswith((".x", ".*")):
            if operator not in (None, "=", "==", "!="):
                raise ValueError(f"rango de dependencia no válido: {requirement}")
            matched = _matches_maximum(current, expected[:-1] + "x")
            if matched == (operator == "!="):
                return False
        else:
            target = _version_tuple(expected)
            if not {
                None: current == target,
                "=": current == target,
                "==": current == target,
                "!=": current != target,
                ">=": current >= target,
                "<=": current <= target,
                ">": current > target,
                "<": current < target,
            }[operator]:
                return False
    return True


def _schema_type(value: str):
    return {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "datetime": datetime,
        "object": dict,
        "array": list,
    }.get(value.casefold(), object)


_MANAGER: PluginManager | None = None
_MANAGER_LOCK = RLock()


def active_theme_extensions():
    """Read initialized themes without bootstrapping or enabling plugin code."""
    if _MANAGER is None:
        return []
    _MANAGER.refresh_authorizations()
    return _MANAGER.extensions.list("theme")


def get_plugin_manager() -> PluginManager:
    global _MANAGER
    with _MANAGER_LOCK:
        if _MANAGER is None:
            _MANAGER = PluginManager()
            _MANAGER._authorization.start_watch()
        return _MANAGER
