# src/models/rack.py
from __future__ import annotations

from lanctl.apps.wire.error import Error
from lanctl.apps.wire.models.basics import EMPTY, NetworkEmpty


class RackElement:
    """
    Elemento dentro del rack.
    Puede ser:
    - un dispositivo activo (switch, panel, terminal)
    - un elemento pasivo (blank, schuko, guide, empty)
    """

    def __init__(self, kind: str, obj=None):
        """
        kind: tipo de elemento (blank, schuko, guide, empty, device)
        obj: instancia del dispositivo activo (switch, panel, terminal)
        """
        self.kind = kind
        self.obj = obj  # puede ser None o un dispositivo activo

    def __repr__(self):
        if self.obj:
            return f"<RackElement {self.kind} {self.obj.idf}>"
        return f"<RackElement {self.kind}>"


class NetworkRack:
    """
    Representa un rack físico de X unidades (U).
    Cada U contiene un RackElement.
    """

    def __init__(self, name: str, size_u: int = 18):
        self.name = name
        self.size_u = size_u
        self.elements: list[RackElement] = [RackElement("empty") for _ in range(size_u)]

    def set_element(self, u: int, element: RackElement):
        """
        Inserta un elemento en una posición U del rack.
        """
        if not (1 <= u <= self.size_u):
            return Error(
                40, "NetworkRack.set_element", f"Posición U {u} fuera de rango.", breakable=True
            )

        self.elements[u - 1] = element

    def get_element(self, u: int) -> RackElement | NetworkEmpty:
        if not (1 <= u <= self.size_u):
            return EMPTY
        return self.elements[u - 1]

    def fill_blank(self, u: int):
        """Coloca una tapa ciega en la posición U."""
        self.set_element(u, RackElement("blank"))

    def fill_schuko(self, u: int):
        """Coloca una regleta schuko."""
        self.set_element(u, RackElement("schuko"))

    def fill_guide(self, u: int):
        """Coloca una guía de cables."""
        self.set_element(u, RackElement("guide"))

    def mount_device(self, u: int, device):
        """
        Monta un dispositivo activo (switch, panel, terminal).
        """
        self.set_element(u, RackElement("device", device))

    def __repr__(self):
        return f"<NetworkRack {self.name} U={self.size_u}>"
