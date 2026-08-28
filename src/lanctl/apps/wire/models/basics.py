# src/models/basics.py
from __future__ import annotations

from lanctl.apps.wire.error import Error
from lanctl.apps.wire.idf import IDF


class NetworkEmpty:
    """Valor vacío para extremos y puertos sin cable."""


EMPTY = NetworkEmpty()


class WireClass:
    FIBER = "wire.fiber"
    COPPER = "wire.copper"
    DAC = "wire.dac"


class NetworkWire:
    def __init__(self, idf: IDF, kind: str):
        self.idf = idf
        self.kind = kind
        self.extreme: list[IDF | NetworkEmpty] = [EMPTY, EMPTY]

    def attach_connector(self, connector_idf: IDF):
        if self.extreme[0] is EMPTY:
            self.extreme[0] = connector_idf
        elif self.extreme[1] is EMPTY:
            self.extreme[1] = connector_idf
        else:
            return Error(
                40,
                "NetworkWire.attach_connector",
                f"El cable {self.idf} ya tiene los dos extremos ocupados.",
                breakable=True,
            )

    def detach_connector(self, connector_idf: IDF):
        if self.extreme[0] == connector_idf:
            self.extreme[0] = EMPTY
        elif self.extreme[1] == connector_idf:
            self.extreme[1] = EMPTY
        else:
            return Error(
                30, "NetworkWire.detach_connector", f"El extremo {connector_idf} no está conectado."
            )


class NetworkConnector:
    def __init__(self, kind: str, num: int, name: str, idf: IDF):
        self.kind = kind
        self.num = num
        self.name = name
        self.idf = idf
        self.wire: NetworkWire | NetworkEmpty = EMPTY

    def attach_wire(self, wire: NetworkWire):
        self.wire = wire
        wire.attach_connector(self.idf)

    def detach_wire(self):
        if self.wire is EMPTY:
            return Error(
                30, "NetworkConnector.detach_wire", f"El conector {self.idf} no tiene cable."
            )
        self.wire.detach_connector(self.idf)
        self.wire = EMPTY
