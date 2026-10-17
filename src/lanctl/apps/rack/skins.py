"""Frentes genéricos de equipos; la apariencia no crea puertos de inventario."""

from copy import deepcopy

from lanctl.apps.rack.organization import token
from lanctl.apps.wire.xfile import update_json


def profiles():
    result = [
        {
            "id": "auto",
            "name": "Automático según inventario",
            "kind": "auto",
            "rj45": 0,
            "sfp": 0,
            "units": 1,
            "rackmount": True,
        }
    ]
    for copper, fiber in [
        (12, 0),
        (24, 0),
        (48, 0),
        (24, 2),
        (24, 4),
        (48, 2),
        (50, 2),
        (48, 4),
        (48, 6),
        (48, 8),
    ]:
        result.append(
            {
                "id": f"switch-{copper}-{fiber}",
                "name": f"Switch {copper} RJ45" + (f" + {fiber} SFP" if fiber else ""),
                "kind": "switch",
                "rj45": copper,
                "sfp": fiber,
                "units": 1,
                "rackmount": True,
            }
        )
    for count in (5, 8, 12, 16, 24):
        result.append(
            {
                "id": f"desktop-{count}",
                "name": f"Switch de sobremesa {count} RJ45 (bandeja)",
                "kind": "switch",
                "rj45": count,
                "sfp": 0,
                "units": 1,
                "rackmount": False,
            }
        )
    for count in (12, 24, 48):
        result.append(
            {
                "id": f"panel-{count}",
                "name": f"Panel de conexiones {count} RJ45",
                "kind": "panel",
                "rj45": count,
                "sfp": 0,
                "units": 1,
                "rackmount": True,
            }
        )
    for kind, name, heights in [
        ("server", "Servidor", (1, 2, 4)),
        ("ups", "SAI / UPS", (2, 3, 4)),
        ("router", "Router / cortafuegos", (1,)),
        ("shelf", "Bandeja", (1, 2)),
        ("blank", "Panel ciego", (1, 2)),
    ]:
        for height in heights:
            result.append(
                {
                    "id": f"{kind}-{height}",
                    "name": f"{name} {height} U",
                    "kind": kind,
                    "rj45": 4 if kind == "router" else 0,
                    "sfp": 0,
                    "units": height,
                    "rackmount": True,
                }
            )
    return result


def appearance(values):
    if not isinstance(values, dict):
        raise ValueError("Apariencia de equipo inválida")
    kind = values.get("kind")
    if kind not in {"auto", "switch", "panel", "server", "ups", "router", "shelf", "blank"}:
        raise ValueError("Selecciona un tipo de frente válido")
    result = {"schemaVersion": 1, "kind": kind}
    for key, minimum, maximum in [("rj45", 0, 96), ("sfp", 0, 32), ("units", 1, 8)]:
        value = values.get(key)
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f"{key} debe estar entre {minimum} y {maximum}")
        result[key] = value
    if type(values.get("rackmount")) is not bool:
        raise ValueError("Selecciona el formato de montaje")
    result["rackmount"] = values["rackmount"]
    return result


def span(data):
    value = data.get("rackAppearance")
    if value is None:
        return 1
    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value.get("schemaVersion") != 1
    ):
        raise ValueError("Esquema de apariencia no compatible")
    return appearance(value)["units"]


def validate_location(records, identifier, data):
    location = data.get("location") or {}
    start = location.get("unit")
    rack_id = location.get("rack")
    if rack_id and start:
        rack = next((r for r in records if r["id"] == rack_id), None)
        if not rack or rack.get("data", {}).get("type") != "rack":
            raise ValueError("El rack asignado ya no existe")
        if start + span(data) - 1 > int(rack["data"].get("units", 42)):
            raise ValueError("El equipo sobrepasa la altura del armario")
        occupied = set(range(start, start + span(data)))
        for other in records:
            other_data = other.get("data") or {}
            other_location = other_data.get("location") or {}
            other_start = other_location.get("unit")
            if (
                other["id"] != identifier
                and other_location.get("rack") == rack_id
                and other_start
                and occupied.intersection(range(other_start, other_start + span(other_data)))
            ):
                raise ValueError(f"Las unidades están ocupadas por {other['id']}")


def save(database, expected, identifier, values):
    visual = appearance(values)

    def change(document):
        database._validate_database(document)
        if token(document) != expected:
            raise ValueError("El inventario cambió; actualiza antes de guardar el frente")
        record = document["records"].get(identifier)
        if not record or record.get("data", {}).get("type") in {"wire", "rack"}:
            raise ValueError("Selecciona un equipo del armario")
        data = record["data"]
        validate_location(
            list(document["records"].values()), identifier, {**data, "rackAppearance": visual}
        )
        record["data"] = {**data, "rackAppearance": deepcopy(visual)}
        record["updated_at"] = database._timestamp()

    update_json(database.path, dict, change)
    return {"id": identifier}
