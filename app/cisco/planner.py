from __future__ import annotations

import re

from app.cisco.catalog import find_spec
from app.cisco.models import CommandPlan, CommandSpec, PortProfile, SwitchProfile
from app.models import Device


SAFE_TEXT = re.compile(r"^[^\r\n;]{1,64}$")


class CiscoPlanner:
    def __init__(self, device: Device, profile: SwitchProfile):
        self.device = device
        self.profile = profile

    def _port(self, reference: str | None, selected: PortProfile | None) -> PortProfile:
        if reference:
            return self.profile.resolve_port(reference)
        if selected:
            return selected
        raise ValueError("falta el puerto; indícalo o selecciónalo primero")

    @staticmethod
    def _validate(spec: CommandSpec, value: str) -> str:
        if not SAFE_TEXT.fullmatch(value):
            raise ValueError("el valor contiene caracteres no permitidos o supera 64 caracteres")
        if spec.argument == "speed" and value.casefold() not in {"auto", "10", "100", "1000", "10000"}:
            raise ValueError("speed debe ser auto, 10, 100, 1000 o 10000")
        if spec.argument == "duplex" and value.casefold() not in {"auto", "half", "full"}:
            raise ValueError("duplex debe ser auto, half o full")
        return value

    def plan(self, tokens: list[str], selected_port: PortProfile | None = None) -> CommandPlan:
        if not tokens:
            raise ValueError("falta el comando Cisco")
        lowered = [token.casefold() for token in tokens]
        # En contexto de puerto se omite el prefijo repetitivo `port`.
        if selected_port and lowered[0] == "show" and len(tokens) == 2:
            tokens = ["port", *tokens]
        elif selected_port and lowered[0] == "set":
            tokens = ["port", *tokens]
        elif selected_port and lowered[0] in ("enable", "disable"):
            tokens = ["port", *tokens]
        lowered = [token.casefold() for token in tokens]
        port: PortProfile | None = None
        value = ""

        if lowered[0] in ("start", "stop", "reset"):
            spec = find_spec((lowered[0],))
            port = self._port(tokens[1] if len(tokens) > 1 else None, selected_port)
            if len(tokens) > 2:
                raise ValueError("demasiados argumentos para " + tokens[0])
        elif lowered[:2] == ["port", "show"]:
            kinds = {"status", "description", "config", "configuration", "errors", "vlan"}
            if len(tokens) == 3 and lowered[2] in kinds:
                kind, reference = lowered[2], None
            elif len(tokens) == 4 and lowered[3] in kinds:
                reference, kind = tokens[2], lowered[3]
            else:
                raise ValueError("usa: port show [PUERTO] status|description|config|errors|vlan")
            spec = find_spec(("port", "show", kind))
            port = self._port(reference, selected_port)
        elif lowered[:2] == ["port", "set"]:
            fields = {"description", "speed", "duplex"}
            if len(tokens) >= 4 and lowered[2] in fields:
                reference, field, values = None, lowered[2], tokens[3:]
            elif len(tokens) >= 5 and lowered[3] in fields:
                reference, field, values = tokens[2], lowered[3], tokens[4:]
            else:
                raise ValueError("usa: port set [PUERTO] description|speed|duplex VALOR")
            spec = find_spec(("port", "set", field))
            port = self._port(reference, selected_port)
            value = self._validate(spec, " ".join(values).strip())
        elif lowered[:2] in (["port", "enable"], ["port", "disable"], ["port", "reset"]):
            spec = find_spec(tuple(lowered[:2]))
            port = self._port(tokens[2] if len(tokens) > 2 else None, selected_port)
            if len(tokens) > 3:
                raise ValueError("demasiados argumentos para " + " ".join(tokens[:2]))
        else:
            spec = find_spec(tuple(lowered))

        values = {"native_port": port.native if port else "", "value": value}
        commands = tuple(template.format(**values) for template in spec.templates)
        label = self.device.alias or self.device.name or self.device.ip
        return CommandPlan(
            spec.id, self.device.device_id, label, self.device.ip, spec.risk,
            commands, port.id if port else "", port.native if port else "",
            {spec.argument: value} if spec.argument else {},
        )
