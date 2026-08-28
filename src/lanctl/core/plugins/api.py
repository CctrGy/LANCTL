from __future__ import annotations

from lanctl.core.plugins.extensions import ExtensionRegistry


class PluginApi:
    """Fachada con permisos; evita entregar objetos internos del core."""

    def __init__(self, plugin_id: str, permissions: set[str], manager) -> None:
        self.plugin_id = plugin_id
        self.permissions = permissions
        self._manager = manager

    def require(self, permission: str) -> None:
        if permission.casefold() not in self.permissions:
            raise PermissionError(f"{self.plugin_id} no tiene el permiso {permission}")

    @property
    def events(self):
        return _PluginEvents(self)

    @property
    def extensions(self):
        return _PluginExtensions(self, self._manager.extensions)

    @property
    def functions(self):
        return _PluginFunctions(self)

    @property
    def network(self):
        return _PluginNetwork(self)

    @property
    def credentials(self):
        return _PluginCredentials(self)

    @property
    def inventory(self):
        return _PluginInventory(self)

    @property
    def storage(self):
        return _PluginStorage(self)

    @property
    def history(self):
        return _PluginHistory(self)

    @property
    def monitor(self):
        return _PluginMonitor(self)

    @property
    def errors(self):
        """Canal estructurado de errores limitado al namespace del plugin."""
        return _PluginErrors(self)

    def log(self, action: str, target: str = "-", result: str = "OK", detail: str = "") -> None:
        self._manager.audit(self.plugin_id, action, target, result, detail)


class _PluginErrors:
    def __init__(self, api: PluginApi) -> None:
        self.api = api

    def _origin(self, point: str) -> str:
        cleaned = str(point).strip().strip(".")
        if not cleaned:
            cleaned = "Runtime"
        prefix = f"Plugin.{self.api.plugin_id}."
        if cleaned.casefold().startswith(prefix.casefold()):
            return cleaned
        if cleaned.casefold().startswith(("plugin.", "lanctl.")):
            raise PermissionError("el origen del error pertenece a otro namespace")
        return prefix + cleaned

    def emit(
        self,
        code: str,
        message: str,
        *,
        origin: str = "Runtime",
        level=42,
        recoverable: bool = True,
        details=None,
        correlation_id=None,
        break_execution: bool = False,
        print_output: bool = False,
        exit_code: int = 2,
    ):
        from lanctl.core.errors import errors

        return errors.emit(
            level=level,
            origin=self._origin(origin),
            code=code,
            message=message,
            recoverable=recoverable,
            details=details,
            correlation_id=correlation_id,
            break_execution=break_execution,
            print_output=print_output,
            exit_code=exit_code,
        )

    def interpolate(self, exception: Exception, *, code: str, origin: str = "Runtime", **options):
        """Convierte una excepción propia o externa al contrato común LANCTL."""
        from lanctl.core.errors import LanctlError, errors

        if isinstance(exception, LanctlError):
            details = dict(options.pop("details", {}) or {})
            details.setdefault("upstreamOrigin", exception.event.origin)
            details.setdefault("upstreamCode", exception.event.code)
            options["details"] = details
            exception = RuntimeError(exception.event.message)
        return errors.from_exception(exception, origin=self._origin(origin), code=code, **options)


class _PluginEvents:
    def __init__(self, api: PluginApi) -> None:
        self.api = api

    def subscribe(self, event_id, handler, *, version=1, priority=100):
        self.api.require("events.listen")
        self.api._manager.events.subscribe(
            event_id, handler, plugin_id=self.api.plugin_id, version=version, priority=priority
        )

    def emit(self, event_id, values, *, version=1, correlation_id=None):
        self.api.require("events.emit")
        if event_id.casefold().startswith("lanctl."):
            raise PermissionError("un plugin no puede emitir eventos reservados del core")
        return self.api._manager.events.emit(
            event_id,
            values,
            source=self.api.plugin_id,
            version=version,
            correlation_id=correlation_id,
        )

    def register(self, event_id, contract, *, version=1, cancelable=False):
        self.api.require("events.register")
        return self.api._manager.event_registry.register(
            event_id, contract, owner=self.api.plugin_id, version=version, cancelable=cancelable
        )


class _PluginExtensions:
    def __init__(self, api: PluginApi, registry: ExtensionRegistry) -> None:
        self.api, self.registry = api, registry

    def register(self, extension_id: str, extension_type: str, specification=None):
        self.api.require(f"{extension_type}.register")
        return self.registry.register(
            extension_id, extension_type, self.api.plugin_id, specification
        )


class _PluginFunctions:
    def __init__(self, api: PluginApi) -> None:
        self.api = api

    def register(self, function_id, handler, return_contract):
        self.api.require("functions.register")
        if function_id.casefold().startswith("lanctl."):
            raise PermissionError("namespace de funciones LANCTL reservado")
        self.api._manager.functions.register(
            function_id, handler, return_contract, owner=self.api.plugin_id
        )

    def call(self, function_id, *args, **kwargs):
        self.api.require("functions.call")
        return self.api._manager.functions.call(
            function_id, *args, caller=self.api.plugin_id, **kwargs
        )


class _PluginNetwork:
    def __init__(self, api: PluginApi) -> None:
        self.api = api

    def send_wol(
        self,
        mac: str,
        broadcast: str = "255.255.255.255",
        port: int = 9,
        repeat: int = 3,
        interval: float = 0.5,
        interface: str | None = None,
    ) -> int:
        self.api.require("network.udp")
        from lanctl.core.plugins.wol_runtime import send_magic_packet

        count = send_magic_packet(mac, broadcast, port, repeat, interval, interface)
        self.api.log("wol.send", target=mac, result="SENT", detail=f"packets={count} port={port}")
        return count


class _PluginCredentials:
    def __init__(self, api):
        self.api = api

    def get_for_device(self, device_id: str, protocol: str) -> dict:
        self.api.require("credentials.read.scoped")
        from lanctl.core.config import load_config
        from lanctl.core.credentials import CredentialStore
        from lanctl.core.database import DeviceDatabase

        device = DeviceDatabase(load_config()["database"]).resolve(device_id)
        normalized = protocol.casefold()
        reference = device.credentials.get(normalized)
        if not reference:
            raise ValueError(f"el dispositivo no tiene credencial {normalized}")
        value = CredentialStore(load_config()["credentials"]).get(reference)
        if value.get("deviceId") != device.device_id or value.get("protocol") != normalized:
            raise PermissionError("credencial fuera del alcance autorizado")
        return {"username": value["username"], "password": value["password"]}


class _PluginInventory:
    def __init__(self, api):
        self.api = api

    def list(self):
        self.api.require("inventory.read")
        from lanctl.core.config import load_config
        from lanctl.core.database import DeviceDatabase

        return [device.copy() for device in DeviceDatabase(load_config()["database"]).load()]


class _PluginStorage:
    def __init__(self, api):
        self.api = api

    def open(self):
        self.api.require("plugin.storage")
        from lanctl.core.config import load_config
        from lanctl.core.plugin_storage import PluginStorage

        return PluginStorage(load_config()["smbStorage"], self.api.plugin_id)


class _PluginHistory:
    def __init__(self, api):
        self.api = api

    def write(
        self,
        event_type: str,
        *,
        result="success",
        summary="",
        device=None,
        details=None,
        error=None,
        correlation_id=None,
    ):
        self.api.require("history.write")
        normalized = event_type.casefold()
        if normalized.startswith(("lanctl.", "device.", "wol.", "automation.")):
            raise PermissionError("el plugin no puede apropiarse de namespaces del núcleo")
        if not normalized.startswith(self.api.plugin_id + "."):
            raise PermissionError("el evento debe pertenecer al namespace del plugin")
        from lanctl.core.history import DeviceSnapshot, HistoryEvent, HistoryService

        snapshot = DeviceSnapshot(**device) if isinstance(device, dict) else None
        event = HistoryEvent(
            normalized,
            self.api.plugin_id,
            "plugin",
            result,
            summary,
            correlationId=correlation_id,
            device=snapshot,
            details=details or {},
            error=error,
        )
        HistoryService().write(event)
        self.api.log("history.write", normalized, result)
        return event.to_dict()


class _PluginMonitor:
    def __init__(self, api):
        self.api = api

    def register_check(self, check_id, handler, *, minimum_interval=10, timeout=1, critical=False):
        self.api.require("monitor.check.register")
        from lanctl.apps.monitor.checks import CheckRegistry
        from lanctl.apps.monitor.models import CheckSpec

        registry = getattr(self.api._manager, "monitor_checks", None)
        if registry is None:
            registry = CheckRegistry()
            self.api._manager.monitor_checks = registry
        return registry.register(
            CheckSpec(
                check_id,
                self.api.plugin_id,
                handler,
                float(minimum_interval),
                float(timeout),
                bool(critical),
            )
        )

    def state(self, device_id):
        self.api.require("monitor.state.read")
        service = getattr(self.api._manager, "monitor_service", None)
        if not service or not service.evaluator:
            return None
        state = service.evaluator.states.get(device_id)
        return vars(state).copy() if state else None

    def write_metric(self, result, session_id):
        self.api.require("monitor.metric.write")
        from lanctl.apps.monitor.models import CheckResult

        if not isinstance(result, CheckResult):
            raise TypeError("la métrica debe ser CheckResult")
        service = getattr(self.api._manager, "monitor_service", None)
        if not service:
            raise RuntimeError("no hay runtime monitor activo")
        owner = service.registry.get(result.checkId).owner
        if owner != self.api.plugin_id:
            raise PermissionError("el plugin no es propietario de este check")
        service.metrics.write(result, str(session_id))
        return True

    def emit_event(self, event_type, **values):
        self.api.require("monitor.event.emit")
        return self.api.history.write(event_type, **values)
