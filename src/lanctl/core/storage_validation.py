"""Validate storage snapshots without constructing mutating store managers."""

from pathlib import Path

from lanctl.shared.i18n import t


def configured_contracts() -> dict[Path, str]:
    """Resolve actual configured destinations, including external workspaces."""
    from lanctl.core.config import CONFIG_PATH, load_config
    from lanctl.core.paths import application_path

    config = load_config()
    result = {CONFIG_PATH.resolve(): "config"}
    result[application_path("data/lc/plugins/registry.json").resolve()] = "plugins"
    for key, contract in (
        ("database", "devices"),
        ("groups", "groups"),
        ("physicalDatabase", "physical"),
    ):
        if config.get(key):
            path = application_path(config[key]).resolve()
            if path in result and result[path] != contract:
                raise ValueError(t("LANCTL.STORAGE.ERROR.CONFLICT", path=path))
            result[path] = contract
    return result


def validate_document(value: object, contract: str, *, path: Path) -> None:
    if contract == "devices":
        from lanctl.core.database import DeviceDatabase

        DeviceDatabase.validate_document(value, path=path)
    elif contract == "groups":
        from lanctl.core.group_database import GroupDatabase

        GroupDatabase.validate_document(value)
    elif contract == "physical":
        from lanctl.apps.wire.idf.database import IDFDatabaseManager

        IDFDatabaseManager._validate_database(value)
    elif contract == "config":
        from lanctl.core.config import canonical_config

        if not isinstance(value, dict):
            raise ValueError(t("LANCTL.STORAGE.ERROR.OBJECT", path=path))
        canonical_config(value)
    elif contract == "plugins":
        from lanctl.core.plugins.registry import validate_registry

        validate_registry(value)
    else:
        raise ValueError(t("LANCTL.STORAGE.ERROR.CONTRACT", contract=contract))
