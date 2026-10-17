"""Organización CPD versionada dentro del inventario físico compartido."""

import hashlib
import json
from copy import deepcopy
from uuid import uuid4

from lanctl.apps.wire.xfile import read, update_json


def organization(document):
    # Las bases anteriores no contienen CPD; se conservan sin asignaciones.
    value = document.get("cpdOrganization", {"schemaVersion": 1, "rooms": {}})
    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value.get("schemaVersion") != 1
    ):
        raise ValueError("Esquema CPD no compatible")
    rooms = value.get("rooms")
    if not isinstance(rooms, dict):
        raise ValueError("Colección CPD inválida")
    for key, room in rooms.items():
        if not isinstance(room, dict) or room.get("id") != key:
            raise ValueError("Identidad CPD inválida")
        if not all(isinstance(room.get(k, ""), str) for k in ("name", "description", "location")):
            raise ValueError("Metadatos CPD inválidos")
        if not room.get("name", "").strip():
            raise ValueError("El CPD necesita un nombre")
    for record in document["records"].values():
        data = record.get("data") or {}
        cpd = (data.get("location") or {}).get("cpd")
        if cpd and (data.get("type") != "rack" or cpd not in rooms):
            raise ValueError("Asignación CPD inválida")
    return deepcopy(value)


def token(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()


def snapshot(database):
    document = read(database.path)
    database._validate_database(document)
    return {
        "cpds": list(organization(document)["rooms"].values()),
        "organizationRevision": token(document),
    }


def mutate(database, expected, operation, values):
    result = {}

    def change(document):
        database._validate_database(document)
        groups = organization(document)
        if token(document) != expected:
            raise ValueError("El inventario cambió en otra ventana; actualiza antes de guardar")
        rooms = groups["rooms"]
        identifier = values.get("id")
        if operation in {"create", "edit"}:
            if operation == "edit" and identifier not in rooms:
                raise ValueError("El CPD ya no existe")
            identifier = identifier if operation == "edit" else "CPD-" + uuid4().hex
            room = {"id": identifier}
            for key in ("name", "description", "location"):
                value = values.get(key, "")
                if not isinstance(value, str):
                    raise ValueError("Los datos del CPD deben ser texto")
                room[key] = value.strip()
            if not room["name"]:
                raise ValueError("El CPD necesita un nombre")
            rooms[identifier] = room
        elif operation == "assign":
            rack = document["records"].get(values.get("rack"))
            if not rack or rack.get("data", {}).get("type") != "rack":
                raise ValueError("Selecciona un armario rack existente")
            if identifier and identifier not in rooms:
                raise ValueError("El CPD de destino no existe")
            rack["data"].setdefault("location", {})["cpd"] = identifier or ""
            rack["updated_at"] = database._timestamp()
        elif operation == "delete":
            if identifier not in rooms:
                raise ValueError("El CPD ya no existe")
            target = values.get("target") or ""
            if target == identifier or (target and target not in rooms):
                raise ValueError("El CPD de destino no es válido")
            for rack in document["records"].values():
                location = (rack.get("data") or {}).get("location") or {}
                if location.get("cpd") == identifier:
                    location["cpd"] = target
                    rack["updated_at"] = database._timestamp()
            del rooms[identifier]
        else:
            raise ValueError("Operación CPD desconocida")
        document["cpdOrganization"] = groups
        organization(document)
        result["id"] = identifier

    update_json(database.path, dict, change)
    return result
