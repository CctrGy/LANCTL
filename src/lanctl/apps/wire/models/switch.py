# src/models/switch.py
from __future__ import annotations

from lanctl.apps.wire.error import Error
from lanctl.apps.wire.idf import IDF
from lanctl.apps.wire.models.basics import EMPTY, NetworkConnector, NetworkWire, WireClass


class NetworkSwitch:
    def __init__(
        self,
        name: str,
        idf: IDF,
        port_count: int = 5,
        port_name_format: str = "LAN{n}",
        kind: str = WireClass.COPPER,
    ):

        self.name = name
        self.idf = idf
        self.kind = kind

        self.ports: list[NetworkConnector] = []
        for n in range(1, port_count + 1):
            pname = port_name_format.format(n=n)
            pidf = IDF(f"{idf}.{pname}")
            self.ports.append(NetworkConnector(kind, n, pname, pidf))

    def _get_port(self, sel):
        for port in self.ports:
            if port.num == sel or port.name == sel:
                return port
        return EMPTY

    def attach_wire_to_port(self, sel, wire: NetworkWire):
        port = self._get_port(sel)
        if port is EMPTY:
            return Error(
                40,
                "NetworkSwitch.attach_wire_to_port",
                f"Puerto '{sel}' no encontrado.",
                breakable=True,
            )
        port.attach_wire(wire)
