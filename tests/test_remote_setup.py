import json
import os
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.apps.access import remote_setup as setup
from lanctl.apps.access.auth import AuthenticationService
from lanctl.apps.access.store import AccessStore


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "require_admin", lambda: None)
    return setup.InitialRemoteAccount(tmp_path / "service" / "users.dc")


def test_first_account_uses_existing_hash_and_authentication_without_exposing_secret(service):
    api = setup.RemoteSetupApi(service)
    password = "synthetic-setup-password"
    assert api.setup_status()["canCreate"]

    result = api.create_initial_user("  First.Admin  ", password, password)

    assert result["ok"] and result["username"] == "first.admin"
    assert result["scope"] == "service"
    stored = service.path.read_text(encoding="utf-8")
    assert password not in stored + json.dumps(result) + json.dumps(api.setup_status())
    document = json.loads(stored)
    assert document["users"][0]["passwordHash"].startswith("scrypt$16384$")
    assert document["users"][0]["roles"] == ["administrator"]
    assert document["users"][0]["sshKeys"] == []
    assert not api.setup_status()["canCreate"]
    user = AuthenticationService(AccessStore(service.path)).authenticate_password(
        "first.admin", password, "127.0.0.1"
    )
    assert user.username == "first.admin"
    assert not (service.path.parent / "config.json").exists()


@pytest.mark.parametrize("operation", ["status", "create"])
def test_unprivileged_rpc_never_creates_store(service, monkeypatch, operation):
    def denied():
        raise PermissionError("administrador requerido")

    monkeypatch.setattr(setup, "require_admin", denied)
    with pytest.raises(PermissionError):
        if operation == "status":
            service.status()
        else:
            service.create("admin", "synthetic-password", "synthetic-password")
    assert not service.path.parent.exists()


@pytest.mark.parametrize(
    "username,password,confirmation",
    [
        (None, "synthetic-password", "synthetic-password"),
        ("ab", "synthetic-password", "synthetic-password"),
        ("<script>", "synthetic-password", "synthetic-password"),
        ("x" * 65, "synthetic-password", "synthetic-password"),
        ("admin", None, None),
        ("admin", "short", "short"),
        ("admin", "x" * 1025, "x" * 1025),
        ("admin", "synthetic-password", "different-password"),
    ],
)
def test_invalid_setup_input_never_saves_account(service, username, password, confirmation):
    with pytest.raises(ValueError):
        service.create(username, password, confirmation)
    assert not service.path.exists()


def test_update_and_duplicate_preserve_all_existing_users_sessions_and_roles(service):
    service.create("first", "synthetic-password", "synthetic-password")
    before = service.path.read_bytes()
    with pytest.raises(ValueError, match="Ya existen cuentas"):
        service.create("second", "different-password", "different-password")
    assert service.path.read_bytes() == before


def test_concurrent_wizards_create_exactly_one_account(service):
    def create(username):
        try:
            return service.create(username, "synthetic-password", "synthetic-password")
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(create, ("first", "second")))
    assert sum(result is not None for result in results) == 1
    assert len(AccessStore(service.path).users()) == 1


def test_legacy_accounts_are_preserved_by_existing_migration(service):
    service.create("legacy", "synthetic-password", "synthetic-password")
    before = service.path.read_bytes()
    legacy = service.path.with_name("users.json")
    service.path.rename(legacy)
    assert service.status()["hasUsers"]
    assert service.path.read_bytes() == before
    assert not legacy.exists()


def test_corrupt_existing_store_is_not_replaced(service):
    service.path.parent.mkdir()
    service.path.write_text('{"schemaVersion":999,"users":[]}', encoding="utf-8")
    before = service.path.read_bytes()
    with pytest.raises(ValueError, match="version de almacen"):
        service.create("admin", "synthetic-password", "synthetic-password")
    assert service.path.read_bytes() == before


def test_cancel_does_not_create_account_and_rejects_late_submission(service):
    api = setup.RemoteSetupApi(service)
    api._window = Mock()
    assert api.request_close()["closed"]
    assert not api.create_initial_user("admin", "synthetic-password", "synthetic-password")["ok"]
    api._window.destroy.assert_called_once()
    assert not service.path.exists()


def test_setup_errors_keep_origin_without_password_in_response_or_diagnostic(service, monkeypatch):
    from lanctl.core.errors import errors

    recorded = []
    original = errors.from_exception

    def capture(exc, **kwargs):
        recorded.append((str(exc), kwargs))
        return original(exc, **kwargs)

    monkeypatch.setattr(errors, "from_exception", capture)
    password = "synthetic-mismatch-secret"
    response = setup.RemoteSetupApi(service).create_initial_user("admin", password, "different")
    assert not response["ok"] and response["errorId"]
    assert password not in json.dumps(response) + str(recorded)
    assert recorded[0][1]["origin"] == "LANCTL.Access.Setup.Create"


def test_command_routes_without_creating_device_vault(monkeypatch):
    from lanctl.apps.access import manager_cli

    wizard = Mock(return_value=0)
    vault = Mock(side_effect=AssertionError("device vault must not be opened"))
    monkeypatch.setattr(setup, "run_remote_setup", wizard)
    monkeypatch.setattr(manager_cli, "AccessManager", vault)
    assert manager_cli._main(["remote-setup"]) == 0
    wizard.assert_called_once_with()
    vault.assert_not_called()
    with pytest.raises(SystemExit):
        manager_cli.build_parser().parse_args(["remote-setup", "--password", "not-accepted"])


@pytest.fixture
def installed(tmp_path, monkeypatch):
    if os.name != "nt":
        pytest.skip("Windows installed service scope")
    from lanctl.core import config, paths

    root = tmp_path / "LANCTL"
    (root / "access").mkdir(parents=True)
    monkeypatch.setattr(setup, "require_admin", lambda: None)
    monkeypatch.setattr(setup, "_program_data", lambda: tmp_path)
    monkeypatch.setattr(setup.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths, "is_portable_install", lambda: False)
    monkeypatch.setattr(config, "CONFIG_PATH", root / "config/config.json")
    monkeypatch.setattr(config, "load_config", lambda: {"accessUsers": "data/lc/access/users.dc"})
    monkeypatch.delenv("LANCTL_DATA_DIR", raising=False)
    monkeypatch.delenv("LANCTL_SECRET_DIR", raising=False)
    return root


def test_installed_scope_uses_os_directory_instead_of_elevated_profile(installed, monkeypatch):
    monkeypatch.setenv("PROGRAMDATA", str(installed / "spoofed"))
    monkeypatch.setenv("LOCALAPPDATA", str(installed / "another-admin"))
    assert setup._installed_store_path() == installed / "access/users.dc"
    assert not (installed / "spoofed").exists()
    assert not (installed / "another-admin").exists()


@pytest.mark.parametrize("variable", ["LANCTL_SECRET_DIR", "LANCTL_DATA_DIR"])
def test_installer_rejects_custom_data_environment(installed, monkeypatch, variable):
    monkeypatch.setenv(variable, str(installed / "custom"))
    with pytest.raises(ValueError, match="rutas de servicio"):
        setup._installed_store_path()


def test_installer_preserves_custom_user_store_configuration(installed, monkeypatch):
    from lanctl.core import config

    monkeypatch.setattr(
        config, "load_config", lambda: {"accessUsers": str(installed / "custom.dc")}
    )
    with pytest.raises(ValueError, match="almacén personalizado"):
        setup._installed_store_path()
    assert not (installed / "custom.dc").exists()


def test_reparse_points_are_rejected_before_any_store_write():
    path = Mock()
    path.lstat.return_value = SimpleNamespace(st_mode=0, st_file_attributes=0x400)
    with pytest.raises(ValueError, match="redirigidas"):
        setup._reject_redirected_paths([path])


def test_installed_scope_failure_is_displayed_in_wizard_instead_of_hidden_console(monkeypatch):
    def rejected():
        raise ValueError("El almacén personalizado requiere el administrador de acceso existente")

    monkeypatch.setattr(setup, "_installed_store_path", rejected)
    response = setup.RemoteSetupApi(setup._InstalledRemoteAccount()).setup_status()
    assert not response["ok"]
    assert "almacén personalizado" in response["error"]
    assert response["errorId"]
