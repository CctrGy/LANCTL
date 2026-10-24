"""Frentes genéricos de equipos; la apariencia no crea puertos de inventario."""

from copy import deepcopy

from lanctl.apps.rack.organization import token
from lanctl.apps.wire.xfile import update_json

# Public import adapters retained for existing callers.
from lanctl.core.physical_placement import appearance as appearance
from lanctl.core.physical_placement import span as span
from lanctl.core.physical_placement import validate_location as validate_location


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
