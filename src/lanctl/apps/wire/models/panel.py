# src/models/panel.py
from __future__ import annotations

from lanctl.apps.wire.error import Error
from lanctl.apps.wire.idf import IDF
from lanctl.apps.wire.models.basics import EMPTY, NetworkConnector, NetworkWire, WireClass


class NetworkPanel:
    """
    Panel de informática, normalmente 24 puertos RJ45.
    """

    def __init__(self, name: str, idf: IDF, port_count: int = 24, port_name_format: str = "P{n}"):

        self.name = name
        self.idf = idf
        self.kind = WireClass.COPPER

        self.ports: list[NetworkConnector] = []
        for n in range(1, port_count + 1):
            pname = port_name_format.format(n=n)
            pidf = IDF(f"{idf}.{pname}")
            self.ports.append(NetworkConnector(self.kind, n, pname, pidf))

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
                "NetworkPanel.attach_wire_to_port",
                f"Puerto '{sel}' no encontrado.",
                breakable=True,
            )
        port.attach_wire(wire)

    def __repr__(self):
        return f"<NetworkPanel {self.name} ports={len(self.ports)}>"
