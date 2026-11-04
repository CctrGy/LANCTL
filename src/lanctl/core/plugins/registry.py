"""Pure validation of persisted plugin authorization snapshots."""

from lanctl.core.plugins.models import PluginState
from lanctl.shared.i18n import t


def validate_registry(data: object) -> dict:
    # The exact empty-object legacy initializer is still accepted by the reader.
    if data == {}:
        return {}
    if (
        not isinstance(data, dict)
        or type(data.get("schemaVersion")) is not int
        or data["schemaVersion"] != 1
    ):
        raise ValueError(t("LANCTL.STORAGE.ERROR.REGISTRY_SCHEMA"))
    values = data.get("plugins")
    if not isinstance(values, dict):
        raise ValueError(t("LANCTL.STORAGE.ERROR.REGISTRY_PLUGINS"))
    for key, entry in values.items():
        if not isinstance(entry, dict):
            raise ValueError(t("LANCTL.STORAGE.ERROR.REGISTRY_ENTRY", entry_id=key))
        PluginState(entry.get("state", "DISABLED"))
        granted = entry.get("granted", [])
        if (
            not isinstance(granted, list)
            or not all(isinstance(p, str) for p in granted)
            or not isinstance(entry.get("trusted", False), bool)
            or any(
                not isinstance(entry.get(k, ""), str)
                for k in ("checksum", "signature", "error", "version")
            )
        ):
            raise ValueError(t("LANCTL.STORAGE.ERROR.REGISTRY_AUTH", entry_id=key))
    return values
