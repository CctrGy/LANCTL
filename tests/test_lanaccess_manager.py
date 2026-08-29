from unittest.mock import patch

from lanctl.apps.access.manager_cli import AccessManager, main
from lanctl.apps.ip.domain.models import Device
from lanctl.core.database import DeviceDatabase


def _manager(tmp_path):
    database_path = tmp_path / "devices.json"
    database = DeviceDatabase(database_path)
    database.save_devices([Device(ip="192.0.2.10", alias="switch", mac="00:11:22:33:44:55")])
    manager = AccessManager(str(database_path), str(tmp_path / "credentials.dc"))
    manager.store._protect = lambda value: value
    manager.store._unprotect = lambda value: value
    return manager


def test_access_manager_owns_secret_and_exposes_only_metadata(tmp_path):
    manager = _manager(tmp_path)
    with patch("lanctl.apps.access.manager_cli.read_secret", side_effect=["secret", "secret"]):
        identifier = manager.set("switch", "SSH", "operator")
    rows = manager.list()
    assert rows[0]["credentialId"] == identifier
    assert rows[0]["username"] == "operator"
    assert "password" not in rows[0]
    assert manager.delete(identifier)
    assert manager.list() == []


def test_lanaccess_tui_can_exit_without_credentials(tmp_path):
    manager = _manager(tmp_path)
    with (
        patch("lanctl.apps.access.manager_cli.AccessManager", return_value=manager),
        patch("builtins.input", return_value="q"),
    ):
        assert main(["--database", "ignored", "--store", "ignored", "--tui"]) == 0
