"""Presentation policy; never filter the storage used by mutations."""

import ipaddress

RACK_ONLY = frozenset(
    {
        "tray",
        "device.tray",
        "rack.cable-comb",
        "rack.organizer",
        "rack.ventilation",
        "rack.pdu",
        "device.pdu",
    }
)
UPS = frozenset({"rack.ups", "device.ups", "ups"})


def has_ip(value):
    try:
        ipaddress.ip_address(str(value or ""))
        return True
    except ValueError:
        return False


def visible_in(data, launcher, *, logical_ip=None):
    kind = str(data.get("type", "")).casefold()
    if kind == "external.fiber-entry":
        return launcher == "lanwire"
    if launcher == "lanrack":
        return True
    kind = str(data.get("type", "")).casefold()
    if kind in RACK_ONLY:
        return False
    addressed = has_ip(data.get("ip")) or has_ip(logical_ip)
    if kind in UPS and not addressed:
        return False
    management = data.get("management") or {}
    return not (
        launcher not in {"lanwire", "lanrack"}
        and kind == "device.switch"
        and management.get("managed") is False
        and not addressed
    )


def logical_devices(devices, config, launcher="lanip"):
    """Use explicit physical IDs, never name matching or transient scan status."""
    from lanctl.apps.wire.idf.database import IDFDatabaseManager
    from lanctl.core.paths import application_path

    path = config.get("physicalDatabase")
    if not path or not application_path(path).is_file():
        return devices
    records = {
        row["id"].casefold(): row["data"]
        for row in IDFDatabaseManager(application_path(path)).all()
    }
    return [
        device
        for device in devices
        if visible_in(records.get(device.idf.casefold(), {}), launcher, logical_ip=device.ip)
    ]


def validate_management(value):
    from lanctl.shared.i18n import t

    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value["schemaVersion"] != 1
        or type(value.get("managed")) is not bool
    ):
        raise ValueError(t("LANCTL.PHYSICAL.MANAGEMENT.INVALID"))
    return {"schemaVersion": 1, "managed": value["managed"]}
