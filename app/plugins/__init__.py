"""API pública y diferida del sistema de complementos LANCTL (LCP).

El paquete no carga el gestor ni los plugins al importar un contrato aislado.
Esto mantiene ligeros el arranque de CLI y los módulos de descubrimiento.
"""

from importlib import import_module

_EXPORTS = {
    "EventBus": ("app.plugins.events", "EventBus"),
    "EventContract": ("app.plugins.contracts", "EventContract"),
    "EventRegistry": ("app.plugins.events", "EventRegistry"),
    "FunctionResult": ("app.plugins.contracts", "FunctionResult"),
    "HookDecision": ("app.plugins.events", "HookDecision"),
    "PluginManager": ("app.plugins.manager", "PluginManager"),
    "PluginManifest": ("app.plugins.models", "PluginManifest"),
    "PluginState": ("app.plugins.models", "PluginState"),
    "get_plugin_manager": ("app.plugins.manager", "get_plugin_manager"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted((*globals(), *__all__))
