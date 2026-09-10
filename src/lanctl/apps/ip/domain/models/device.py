from __future__ import annotations

import hashlib
import ipaddress
import re
from collections.abc import Iterator, Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

MAC_PATTERN = re.compile(r"^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$")
CNF_STATES = ("O", "X", "-", "S", "F")
RESERVED_DEVICE_DEFAULTS = {
    "GATEWAY": {
        "description": "Puerta de enlace de la red",
        "groups": ("BASIC",),
    },
    "BRODCAST": {
        "description": "Difusion general de la LAN",
        "groups": ("BASIC",),
        "mac": "FF:FF:FF:FF:FF:FF",
    },
}


def reserved_device_role(alias: str, default_alias: str = "") -> str:
    """Devuelve el rol estructural canónico, si el elemento lo tiene."""
    for candidate in (default_alias, alias):
        normalized = str(candidate).strip().upper()
        if normalized in RESERVED_DEVICE_DEFAULTS:
            return normalized
    return ""


def reserved_devices_for_network(
    network: ipaddress.IPv4Network, gateway: str | None = None
) -> tuple[Device, Device]:
    """Construye los dos elementos estructurales de una LAN IPv4."""
    gateway_ip = str(gateway or "").strip()
    try:
        parsed_gateway = ipaddress.IPv4Address(gateway_ip) if gateway_ip else None
    except ipaddress.AddressValueError:
        parsed_gateway = None
    if (
        parsed_gateway is None
        or parsed_gateway not in network
        or parsed_gateway in (network.network_address, network.broadcast_address)
    ):
        parsed_gateway = next(network.hosts(), network.network_address)
    return (
        Device(
            ip=str(parsed_gateway),
            cnf="O",
            alias="GATEWAY",
            default_alias="GATEWAY",
        ),
        Device(
            ip=str(network.broadcast_address),
            cnf="O",
            mac="FF:FF:FF:FF:FF:FF",
            alias="BRODCAST",
            default_alias="BRODCAST",
        ),
    )


def normalize_mac(value: str) -> str:
    normalized = value.strip().replace("-", ":").upper()
    if not MAC_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"dirección MAC no válida: {value}. Usa XX:XX:XX:XX:XX:XX o XX-XX-XX-XX-XX-XX"
        )
    return normalized


def is_private_mac(value: str) -> bool:
    """Indica si la MAC usa el bit local (incluye direcciones aleatorias)."""
    try:
        return bool(int(normalize_mac(value).split(":", 1)[0], 16) & 0x02)
    except ValueError:
        return False


def device_identifier(mac: str, ip: str) -> str:
    """Identificador estable y no secreto para enlazar datos auxiliares."""
    source = normalize_mac(mac) if mac else f"ip:{ip.strip().casefold()}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
    return f"dev_{digest}"


def normalize_protocol(value: str) -> str:
    normalized = value.strip().casefold().replace("_", "-")
    if not re.fullmatch(r"[a-z][a-z0-9+.-]{0,31}", normalized):
        raise ValueError(f"protocolo no válido: {value}")
    return normalized


def normalize_cnf(value: Any) -> str:
    if isinstance(value, bool):
        return "O" if value else "X"
    aliases = {
        "o": "O",
        "ok": "O",
        "true": "O",
        "1": "O",
        "yes": "O",
        "si": "O",
        "sí": "O",
        "x": "X",
        "unknown": "X",
        "uknow": "X",
        "false": "X",
        "0": "X",
        "no": "X",
        "-": "-",
        "unrecognized": "-",
        "unrecognised": "-",
        "s": "S",
        "marked": "S",
        "marqued": "S",
        "marcado": "S",
        "f": "F",
        "fixed": "F",
        "fijo": "F",
        "fijado": "F",
    }
    normalized = aliases.get(str(value).strip().casefold())
    if normalized is None:
        raise ValueError(
            "cnf debe ser O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) o F (FIXED)"
        )
    return normalized


@dataclass(slots=True)
class Device(MutableMapping[str, Any]):
    """Un dispositivo LAN y todos los datos vinculados a su identidad."""

    ip: str
    cnf: str = "X"
    mac: str = ""
    name: str = ""
    default_name: str = ""
    alias: str = ""
    default_alias: str = ""
    groups: list[str] = field(default_factory=list)
    description: str = "-"
    manufacturer: str = ""
    name_deleted: bool = False
    alias_deleted: bool = False
    device_id: str = ""
    protocols: list[str] = field(default_factory=list)
    credentials: dict[str, str] = field(default_factory=dict)
    protocol_options: dict[str, dict[str, Any]] = field(default_factory=dict)
    discovery_methods: list[str] = field(default_factory=list)
    last_discovery: str = ""
    last_seen: str = ""
    previous_ips: list[str] = field(default_factory=list)
    icon_id: str = ""

    JSON_FIELDS: ClassVar[dict[str, str]] = {
        "IP": "ip",
        "cnf": "cnf",
        "ALIAS": "alias",
        "MAC": "mac",
        "NAME": "name",
        "GROUP": "groups",
        "description": "description",
        "manufacturer": "manufacturer",
        "defaultAlias": "default_alias",
        "defaultName": "default_name",
        "nameDeleted": "name_deleted",
        "aliasDeleted": "alias_deleted",
        "deviceId": "device_id",
        "protocols": "protocols",
        "credentials": "credentials",
        "protocolOptions": "protocol_options",
        "discoveryMethods": "discovery_methods",
        "lastDiscovery": "last_discovery",
        "lastSeen": "last_seen",
        "previousIPs": "previous_ips",
        "iconId": "icon_id",
    }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Device:
        has_default_name = "defaultName" in value
        alias = str(value.get("ALIAS", ""))
        raw_groups = value.get("GROUP", value.get("group", []))
        if isinstance(raw_groups, str):
            raw_groups = [raw_groups] if raw_groups else []
        description = str(value.get("description", "-")) or "-"
        if len(description) > 42:
            raise ValueError("la descripción de un elemento no puede superar 42 caracteres")
        return cls(
            ip=str(value["IP"]),
            cnf=normalize_cnf(value.get("cnf", False)),
            mac=(normalize_mac(str(value.get("MAC", ""))) if value.get("MAC") else ""),
            name=str(value.get("NAME", "")) if has_default_name else "",
            default_name=str(value.get("defaultName", value.get("NAME", ""))),
            alias=alias,
            default_alias=str(
                value.get(
                    "defaultAlias",
                    alias if alias in ("GATEWAY", "BRODCAST") else "",
                )
            ),
            groups=[str(group).upper() for group in raw_groups],
            description=description,
            manufacturer=str(value.get("manufacturer", "")),
            name_deleted=bool(value.get("nameDeleted", False)),
            alias_deleted=bool(value.get("aliasDeleted", False)),
            device_id=str(value.get("deviceId", "")),
            protocols=[normalize_protocol(str(item)) for item in value.get("protocols", [])],
            credentials={
                normalize_protocol(str(protocol)): str(reference)
                for protocol, reference in value.get("credentials", {}).items()
            },
            protocol_options={
                normalize_protocol(str(protocol)): dict(options)
                for protocol, options in value.get("protocolOptions", {}).items()
                if isinstance(options, Mapping)
            },
            discovery_methods=[
                str(method).strip().upper()
                for method in value.get("discoveryMethods", [])
                if str(method).strip()
            ],
            last_discovery=str(value.get("lastDiscovery", "")),
            last_seen=str(value.get("lastSeen", "")),
            previous_ips=[
                str(address) for address in value.get("previousIPs", []) if str(address).strip()
            ],
            icon_id=str(value.get("iconId", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            json_name: getattr(self, attribute) for json_name, attribute in self.JSON_FIELDS.items()
        }

    def __post_init__(self) -> None:
        self.cnf = normalize_cnf(self.cnf)
        if self.mac:
            self.mac = normalize_mac(self.mac)
        if len(self.description) > 42:
            raise ValueError("la descripción de un elemento no puede superar 42 caracteres")
        self.groups = list(dict.fromkeys(group.upper() for group in self.groups))
        self.device_id = self.device_id or device_identifier(self.mac, self.ip)
        self.protocols = list(dict.fromkeys(normalize_protocol(item) for item in self.protocols))
        self.credentials = {
            normalize_protocol(protocol): str(reference)
            for protocol, reference in self.credentials.items()
        }
        self.protocol_options = {
            normalize_protocol(protocol): dict(options)
            for protocol, options in self.protocol_options.items()
        }
        self.discovery_methods = list(
            dict.fromkeys(
                method.strip().upper() for method in self.discovery_methods if method.strip()
            )
        )
        self.previous_ips = list(
            dict.fromkeys(
                address for address in self.previous_ips if address and address != self.ip
            )
        )
        self.apply_reserved_defaults()

    def apply_reserved_defaults(self) -> str:
        """Impone las propiedades inmutables de los elementos de infraestructura."""
        role = reserved_device_role(self.alias, self.default_alias)
        if not role:
            return ""
        defaults = RESERVED_DEVICE_DEFAULTS[role]
        self.cnf = "O"
        self.alias = role
        self.default_alias = role
        self.alias_deleted = False
        self.groups = list(dict.fromkeys([*self.groups, *defaults["groups"]]))
        if not self.description or self.description == "-":
            self.description = str(defaults["description"])
        if defaults.get("mac"):
            self.mac = str(defaults["mac"])
            self.device_id = device_identifier(self.mac, self.ip)
        return role

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, self.JSON_FIELDS[key])
        except KeyError as error:
            raise KeyError(key) from error

    def __setitem__(self, key: str, value: Any) -> None:
        try:
            attribute = self.JSON_FIELDS[key]
        except KeyError as error:
            raise KeyError(key) from error
        setattr(self, attribute, value)

    def __delitem__(self, key: str) -> None:
        raise TypeError("los campos de Device no se pueden eliminar")

    def __iter__(self) -> Iterator[str]:
        return iter(self.JSON_FIELDS)

    def __len__(self) -> int:
        return len(self.JSON_FIELDS)

    def copy(self) -> Device:
        return Device.from_dict(self.to_dict())

    def in_group(self, name: str) -> bool:
        """Comprueba pertenencia usando la normalización propia del modelo."""

        return name.strip().upper() in self.groups
