"""Topología inicial reproducible para desarrollo y pruebas de LANWIRE."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from lanctl.apps.wire.idf.database import IDFDatabaseManager

COPPER = "wire.copper"
FIBER = "wire.fiber"
DAC = "wire.dac"

SAMPLE_PREFIXES = {
    "RK": ("Rack", "Armario físico que contiene equipos de red."),
    "RT": ("Router", "Router, gateway o equipo de encaminamiento."),
    "SW": ("Switch", "Conmutador de red con puertos físicos."),
    "AP": ("Access Point", "Punto de acceso inalámbrico."),
    "PX": ("Toma Xarxa", "Toma o terminal físico de red."),
    "PC": ("Ordenador", "Ordenador conectado a la red."),
    "PR": ("Raspberry Pi", "Terminal basado en Raspberry Pi."),
    "FB": ("Fibra", "Cable o enlace de fibra óptica."),
    "WL": ("Link", "Enlace de red entre dos puertos."),
    "WE": ("Wire", "Cable físico de red."),
    "PN": ("Panel", "Panel de conexiones instalado en un rack."),
    "CM": ("Compañía", "Suministro o infraestructura externa de la compañía."),
}


def _ports(names: list[str], kind: str = COPPER) -> dict[str, dict[str, Any]]:
    return {name: {"kind": kind, "poe": False} for name in names}


def sample_elements() -> dict[str, dict[str, Any]]:
    """Devuelve datos nuevos para que el llamador no modifique la plantilla."""
    switch_rack_ports = _ports([str(number) for number in range(1, 25)])
    wirecore_ports = _ports([str(number) for number in range(1, 27)])
    wirecore_ports.update({"27": {"kind": DAC, "poe": False}, "28": {"kind": DAC, "poe": False}})
    poe_ports = _ports([f"X{number}" for number in range(1, 7)])
    for number in range(1, 5):
        poe_ports[f"X{number}"]["poe"] = True
    rt02_ports = _ports(["WLAN", "LAN1", "LAN2", "LAN3", "LAN4"])
    rt02_ports["WLAN"]["speeds"] = ["2.5G", "1G", "100M", "10M"]
    for name in ("LAN1", "LAN2", "LAN3", "LAN4"):
        rt02_ports[name]["speeds"] = ["1G", "100M", "10M"]
    for name, port in wirecore_ports.items():
        port["speeds"] = ["10G", "1G", "100M"] if int(name) >= 25 else ["1G", "100M", "10M"]
    panel_ports = {
        f"{number:02d}": {
            "kind": COPPER,
            "poe": False,
            "mark": f"P1-X{number}",
            "outlet": f"PX-{number:02d}",
        }
        for number in range(1, 18)
    }

    elements = {
        "RK-00": {
            "type": "rack",
            "alias": "R0",
            "name": "Rack principal",
            "size_units": 18,
            "layout": [
                {"unit": 3, "height": 2, "kind": "tray", "label_lines": ["Bandeja", ""]},
                {"unit": 5, "height": 4, "kind": "case", "label_lines": ["", "Server", "Case", ""]},
                {"unit": 10, "height": 1, "kind": "panel", "idf": "PN-01", "label": "PN-01"},
                {"unit": 11, "height": 1, "kind": "panel", "idf": "PN-02", "label": "PN-02"},
                {"unit": 13, "height": 1, "kind": "switch", "idf": "SW-01", "label": "SW-01"},
                {"unit": 14, "height": 1, "kind": "cover", "label": "tapa"},
                {"unit": 15, "height": 1, "kind": "comb", "label": "peine"},
                {"unit": 16, "height": 1, "kind": "pdu", "label": "Schuko"},
            ],
        },
        "RT-01": {
            "type": "device.gateway",
            "alias": "OTG",
            "name": "OTG de compañía",
            "ports": {
                "FIBER": {"kind": FIBER, "poe": False},
                "LAN": {"kind": COPPER, "poe": False},
            },
        },
        "RT-02": {
            "type": "device.router",
            "alias": None,
            "name": "Router neutro",
            "ports": rt02_ports,
        },
        "SW-01": {
            "type": "device.switch",
            "alias": None,
            "name": "Switch Rack",
            "location": {"rack": "RK-00", "unit": 13},
            "ports": switch_rack_ports,
        },
        "SW-02": {
            "type": "device.switch",
            "alias": None,
            "name": "Switch WireCore",
            "ports": wirecore_ports,
        },
        "SW-03": {"type": "device.switch", "alias": None, "name": "Switch PoE", "ports": poe_ports},
        "PN-01": {
            "type": "device.panel",
            "name": "Patch panel 1",
            "location": {"rack": "RK-00", "unit": 10},
            "ports": panel_ports,
        },
        "PN-02": {
            "type": "panel",
            "name": "Patch panel 2",
            "location": {"rack": "RK-00", "unit": 11},
        },
        "CM-00": {"type": "external.supply", "name": "Suministro de compañía"},
        "FB-01": {
            "type": "wire",
            "name": "Entrada de fibra OTG",
            "kind": FIBER,
            "source": "CM-00",
            "endpoints": [{"device": "RT-01", "port": "FIBER"}],
        },
        "WL-01": {
            "type": "wire",
            "name": "OTG a router neutro",
            "kind": COPPER,
            "endpoints": [{"device": "RT-01", "port": "LAN"}, {"device": "RT-02", "port": "WLAN"}],
        },
        "WL-02": {
            "type": "wire",
            "name": "Router a Switch Rack",
            "kind": COPPER,
            "endpoints": [{"device": "RT-02", "port": "LAN1"}, {"device": "SW-01", "port": "23"}],
        },
        "WL-03": {
            "type": "wire",
            "name": "Router a Switch WireCore",
            "kind": COPPER,
            "endpoints": [{"device": "RT-02", "port": "LAN2"}, {"device": "SW-02", "port": "24"}],
        },
        "WL-04": {
            "type": "wire",
            "name": "Router a Switch PoE",
            "kind": COPPER,
            "endpoints": [{"device": "RT-02", "port": "LAN3"}, {"device": "SW-03", "port": "X5"}],
        },
        "WE-12": {
            "type": "wire",
            "name": "Salida PoE X1",
            "kind": COPPER,
            "endpoints": [{"device": "SW-03", "port": "X1"}],
        },
    }
    for number in range(1, 18):
        identifier = f"PX-{number:02d}"
        elements[identifier] = {
            "type": "device.outlet",
            "name": f"Toma de pared {number:02d}",
            "mark": f"P1-X{number}",
            "panel_endpoint": {"device": "PN-01", "port": f"{number:02d}"},
            "ports": {"ROOM": {"kind": COPPER, "poe": False}},
        }
    return deepcopy(elements)


def validate_topology(elements: dict[str, dict[str, Any]]) -> None:
    """Comprueba referencias, medios y que ningún puerto se use dos veces."""
    occupied: dict[tuple[str, str], str] = {}
    racks = {identifier for identifier, data in elements.items() if data.get("type") == "rack"}
    for identifier, data in elements.items():
        location = data.get("location")
        if location and location.get("rack") not in racks:
            raise ValueError(f"rack inexistente en {identifier}: {location.get('rack')}")
        if data.get("type") != "wire":
            continue
        endpoints = data.get("endpoints", [])
        if not 1 <= len(endpoints) <= 2:
            raise ValueError(f"{identifier} debe tener uno o dos extremos")
        for endpoint in endpoints:
            device_id, port_name = endpoint.get("device"), str(endpoint.get("port"))
            device = elements.get(device_id)
            if not device or not str(device.get("type", "")).startswith("device."):
                raise ValueError(f"dispositivo inexistente en {identifier}: {device_id}")
            port = device.get("ports", {}).get(port_name)
            if port is None:
                raise ValueError(f"puerto inexistente en {identifier}: {device_id}/{port_name}")
            if port.get("kind") != data.get("kind"):
                raise ValueError(f"medio incompatible en {identifier}: {device_id}/{port_name}")
            key = (device_id, port_name)
            if key in occupied:
                raise ValueError(
                    f"puerto ocupado por {occupied[key]} y {identifier}: {device_id}/{port_name}"
                )
            occupied[key] = identifier


def seed_sample_topology(database: IDFDatabaseManager) -> tuple[str, ...]:
    """Añade solo los elementos ausentes y rechaza conflictos de contenido."""
    created: list[str] = list(migrate_legacy_links(database))
    migrate_zero_based_switch_ports(database)
    elements = sample_elements()
    validate_topology(elements)
    for prefix, (name, description) in SAMPLE_PREFIXES.items():
        database.define_prefix(prefix, name, description)
    for identifier, data in elements.items():
        existing = database.get(identifier)
        if existing is None:
            database.add(identifier, data)
            created.append(identifier)
        elif existing.get("data") != data:
            raise ValueError(f"el registro existente difiere de la plantilla: {identifier}")
    return tuple(created)


def migrate_legacy_links(database: IDFDatabaseManager) -> tuple[str, ...]:
    """Migra los antiguos WT-xx al prefijo oficial WL sin perder sus datos."""
    migrated: list[str] = []
    for number in range(1, 5):
        old_id, new_id = f"WT-{number:02d}", f"WL-{number:02d}"
        old = database.get(old_id)
        if old is None:
            continue
        current = database.get(new_id)
        if current is not None and current.get("data") != old.get("data"):
            raise ValueError(f"no se puede migrar {old_id}: {new_id} contiene otros datos")
        if current is None:
            database.add(new_id, old.get("data") or {})
            migrated.append(new_id)
        database.delete(old_id)
    if database.get_prefix("WT") is not None:
        database.delete_prefix("WT")
    return tuple(migrated)


def migrate_zero_based_switch_ports(database: IDFDatabaseManager) -> tuple[str, ...]:
    """Elimina el puerto 00 heredado sin alterar los puertos 01..N."""
    migrated: list[str] = []
    for identifier in ("SW-01", "SW-02"):
        record = database.get(identifier)
        if record is None:
            continue
        data = record.get("data") or {}
        ports = data.get("ports")
        if not isinstance(ports, dict) or "0" not in ports:
            continue
        data["ports"] = {name: value for name, value in ports.items() if name != "0"}
        database.update(identifier, data)
        migrated.append(identifier)
    return tuple(migrated)


__all__ = [
    "migrate_legacy_links",
    "migrate_zero_based_switch_ports",
    "sample_elements",
    "seed_sample_topology",
    "validate_topology",
]
