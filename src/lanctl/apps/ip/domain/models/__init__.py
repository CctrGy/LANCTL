"""Modelos de datos de LANCTL."""

from lanctl.apps.ip.domain.models.device import (
    Device,
    device_identifier,
    normalize_cnf,
    normalize_mac,
    normalize_protocol,
)
from lanctl.apps.ip.domain.models.group import Group

__all__ = [
    "Device",
    "Group",
    "device_identifier",
    "normalize_cnf",
    "normalize_mac",
    "normalize_protocol",
]
