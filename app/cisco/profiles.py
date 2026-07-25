from __future__ import annotations

import json
from pathlib import Path

from app.cisco.models import PortProfile, SwitchProfile
from app.core.paths import application_path


PROFILE_PATH = application_path("data/als/cisco_profiles.json")


def _s300_profile() -> SwitchProfile:
    ports = [
        PortProfile(f"port:{number}", f"gi1/0/{number}", (str(number), f"p{number}", f"x{number}"))
        for number in range(1, 25)
    ]
    ports.extend((
        PortProfile("port:25", "gi1/0/25", ("25", "p25", "xg1"), "UPLINK1"),
        PortProfile("port:26", "gi1/0/26", ("26", "p26", "xg2"), "UPLINK2"),
    ))
    return SwitchProfile("cisco-s300-24", "Cisco S300 24-port", tuple(ports))


BUILTIN_PROFILES = {"cisco-s300-24": _s300_profile()}


def _from_dict(value: dict) -> SwitchProfile:
    ports = tuple(
        PortProfile(
            str(port["id"]), str(port["native"]),
            tuple(str(alias) for alias in port.get("aliases", [])),
            str(port.get("label", "")),
        )
        for port in value.get("ports", [])
    )
    if not ports:
        raise ValueError("un perfil Cisco debe declarar al menos un puerto")
    return SwitchProfile(str(value["id"]), str(value.get("model", value["id"])), ports)


def load_profiles(path: str | Path = PROFILE_PATH) -> dict[str, SwitchProfile]:
    profiles = dict(BUILTIN_PROFILES)
    source = application_path(path)
    if source.exists():
        raw = json.loads(source.read_text(encoding="utf-8"))
        values = raw.get("profiles", raw) if isinstance(raw, dict) else raw
        if not isinstance(values, list):
            raise ValueError(f"perfiles Cisco no válidos: {source}")
        for value in values:
            profile = _from_dict(value)
            profiles[profile.id] = profile
    return profiles


def load_profile(profile_id: str, path: str | Path = PROFILE_PATH) -> SwitchProfile:
    try:
        return load_profiles(path)[profile_id]
    except KeyError as error:
        raise ValueError(f"perfil Cisco no encontrado: {profile_id}") from error
