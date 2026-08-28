"""Modelos físicos heredados y acceso al gestor IDF."""

from lanctl.apps.wire.idf.database import IDFDatabaseManager

from .basics import EMPTY, NetworkConnector, NetworkEmpty, NetworkWire, WireClass
from .panel import NetworkPanel
from .rack import NetworkRack, RackElement
from .switch import NetworkSwitch
from .terminal import NetworkTerminal

__all__ = [
    "EMPTY",
    "IDFDatabaseManager",
    "NetworkConnector",
    "NetworkEmpty",
    "NetworkPanel",
    "NetworkRack",
    "NetworkSwitch",
    "NetworkTerminal",
    "NetworkWire",
    "RackElement",
    "WireClass",
]
