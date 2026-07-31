from __future__ import annotations

from app.plugins.extensions import ExtensionRegistry


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

    def log(self, action: str, target: str = "-", result: str = "OK", detail: str = "") -> None:
        self._manager.audit(self.plugin_id, action, target, result, detail)


class _PluginEvents:
    def __init__(self, api: PluginApi) -> None:
        self.api = api

    def subscribe(self, event_id, handler, *, version=1, priority=100):
        self.api.require("events.listen")
        self.api._manager.events.subscribe(event_id, handler, plugin_id=self.api.plugin_id, version=version, priority=priority)

    def emit(self, event_id, values, *, version=1, correlation_id=None):
        self.api.require("events.emit")
        if event_id.casefold().startswith("lanctl."):
            raise PermissionError("un plugin no puede emitir eventos reservados del core")
        return self.api._manager.events.emit(event_id, values, source=self.api.plugin_id, version=version, correlation_id=correlation_id)

    def register(self, event_id, contract, *, version=1, cancelable=False):
        self.api.require("events.register")
        return self.api._manager.event_registry.register(event_id, contract, owner=self.api.plugin_id, version=version, cancelable=cancelable)


class _PluginExtensions:
    def __init__(self, api: PluginApi, registry: ExtensionRegistry) -> None:
        self.api, self.registry = api, registry

    def register(self, extension_id: str, extension_type: str, specification=None):
        self.api.require(f"{extension_type}.register")
        return self.registry.register(extension_id, extension_type, self.api.plugin_id, specification)


class _PluginFunctions:
    def __init__(self, api: PluginApi) -> None:
        self.api = api

    def register(self, function_id, handler, return_contract):
        self.api.require("functions.register")
        if function_id.casefold().startswith("lanctl."):
            raise PermissionError("namespace de funciones LANCTL reservado")
        self.api._manager.functions.register(function_id, handler, return_contract, owner=self.api.plugin_id)

    def call(self, function_id, *args, **kwargs):
        self.api.require("functions.call")
        return self.api._manager.functions.call(function_id, *args, caller=self.api.plugin_id, **kwargs)
