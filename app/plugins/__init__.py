"""Sistema unificado de complementos LANCTL (LCP)."""

from app.plugins.contracts import EventContract, FunctionResult
from app.plugins.events import EventBus, EventRegistry, HookDecision
from app.plugins.manager import PluginManager, get_plugin_manager
from app.plugins.models import PluginManifest, PluginState

__all__ = [
    "EventBus", "EventContract", "EventRegistry", "FunctionResult",
    "HookDecision", "PluginManager", "PluginManifest", "PluginState",
    "get_plugin_manager",
]
