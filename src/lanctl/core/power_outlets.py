"""Versioned descriptive outlets, independent of network ports and wiring."""

from lanctl.shared.i18n import t


def validate_outlets(value):
    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value["schemaVersion"] != 1
        or value.get("type") not in {"schuko", "iec-c13"}
        or type(value.get("count")) is not int
        or not 1 <= value["count"] <= 24
    ):
        raise ValueError(t("LANCTL.PDU.INVALID"))
    return {"schemaVersion": 1, "type": value["type"], "count": value["count"]}
