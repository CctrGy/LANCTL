"""Modelos de datos de LANCTL."""

from app.models.device import (
    Device,
    device_identifier,
    normalize_cnf,
    normalize_mac,
    normalize_protocol,
)
from app.models.group import Group

__all__ = [
    "Device",
    "Group",
    "device_identifier",
    "normalize_cnf",
    "normalize_mac",
    "normalize_protocol",
]
