import json
import zipfile
from unittest.mock import patch

import pytest

from lanctl.apps.access.vault_service import transfer
from lanctl.apps.monitor.event_view import read_events
from lanctl.core.credentials import CredentialStore
from lanctl.core.vault_crypto import decrypt, encrypt

PASSWORD = "test passphrase only 123"


def test_portable_authenticated_roundtrip():
    encrypted = encrypt(b"sensitive", PASSWORD)
    assert b"sensitive" not in encrypted
    assert decrypt(encrypted, PASSWORD) == b"sensitive"
    with pytest.raises(ValueError):
        decrypt(encrypted, "incorrect password 456")
    with pytest.raises(ValueError):
        decrypt(encrypted[:-8] + b"tampered", PASSWORD)


def test_portable_store_auto_detection(tmp_path):
    path = tmp_path / "vault"
    store = CredentialStore(str(path), cipher="portable", password=PASSWORD)
    identifier = store.set("dev_example", "ssh", "admin", "device-password")
    with patch("lanctl.core.secret_input.read_secret", return_value=PASSWORD):
        opened = CredentialStore(str(path))
        assert opened.get(identifier)["password"] == "device-password"
        opened.set("dev_second", "ssh", "user", "second secret")
    assert len(store.metadata()) == 2
    assert b"device-password" not in path.read_bytes()


def test_transfer_conflict_and_source_survival(tmp_path):
    source = CredentialStore(str(tmp_path / "source"), cipher="portable", password=PASSWORD)
    target = CredentialStore(str(tmp_path / "target"), cipher="portable", password=PASSWORD)
    identifier = source.set("dev_example", "ssh", "admin", "first")
    assert transfer(source, target) == 1
    assert source.get(identifier) == target.get(identifier)
    target.set("dev_example", "ssh", "admin", "other")
    before = target.path.read_bytes()
    with pytest.raises(ValueError, match="conflicto"):
        transfer(source, target, move=True)
    assert target.path.read_bytes() == before
    assert source.get(identifier)["password"] == "first"


def test_log_union_filter_and_terminal_escape(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "25-09-2026.log").write_text(
        '10:00:00 ERROR_EVENT {"level": 12}\n10:00:01 hello\x1b[2J\n'
    )
    project = tmp_path / "test.vlf"
    with zipfile.ZipFile(project, "w") as archive:
        archive.writestr("logs/25-09-2026.log", '11:00:00 ERROR_EVENT {"level": 45}\n')
    rows = read_events({"programLog": str(logs), "activeProject": str(project)}, minimum=20)
    assert {r["source"] for r in rows} == {"program", "project"}
    assert all("\x1b" not in r["message"] for r in rows)
    assert len(rows) == 2


def test_monitor_compatibility_module():
    from lanctl.apps.ip.interfaces.cli.commands import monitor as legacy
    from lanctl.apps.monitor import commands

    assert legacy is commands


def test_binding_failure_restores_existing_secret(tmp_path):
    from lanctl.apps.access.manager_cli import AccessManager
    from lanctl.apps.ip.domain.models import Device
    from lanctl.core.database import DeviceDatabase

    path = tmp_path / "devices.json"
    db = DeviceDatabase(path)
    db.save_devices([Device(ip="192.0.2.1", mac="00:11:22:33:44:55", alias="test")])
    manager = AccessManager(str(path), str(tmp_path / "vault"))
    manager.store = CredentialStore(str(tmp_path / "vault"), cipher="portable", password=PASSWORD)
    identifier = manager.store.set(db.resolve("test").device_id, "ssh", "old", "old-secret")
    with (
        patch(
            "lanctl.apps.access.manager_cli.read_secret", side_effect=["new-secret", "new-secret"]
        ),
        patch.object(manager.database, "bind_credential", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        manager.set("test", "ssh", "new")
    assert manager.store.get(identifier)["password"] == "old-secret"


def test_recovery_is_explicit_and_never_overwrites_binding(tmp_path):
    from lanctl.apps.access.manager_cli import AccessManager
    from lanctl.apps.access.vault_service import audit_bindings
    from lanctl.apps.ip.domain.models import Device

    manager = AccessManager(str(tmp_path / "db.json"), str(tmp_path / "vault"))
    manager.database.save_devices([Device(ip="192.0.2.1", mac="00:11:22:33:44:55", alias="test")])
    manager.store = CredentialStore(str(tmp_path / "vault"), cipher="portable", password=PASSWORD)
    device = manager.database.resolve("test")
    identifier = manager.store.set(device.device_id, "ssh", "user", "secret")
    assert audit_bindings(manager)["unbound"] == [identifier]
    assert not manager.database.resolve("test").credentials
    assert audit_bindings(manager, repair=True)["repaired"] == 1
    manager.database.bind_credential("test", "ssh", "another-reference")
    assert audit_bindings(manager, repair=True)["repaired"] == 0
    assert manager.database.resolve("test").credentials["ssh"] == "another-reference"


def test_failed_target_write_never_removes_source(tmp_path):
    source = CredentialStore(str(tmp_path / "source"), cipher="portable", password=PASSWORD)
    target = CredentialStore(str(tmp_path / "target"), cipher="portable", password=PASSWORD)
    source.set("dev_example", "ssh", "admin", "secret")
    before = source.path.read_bytes()
    with patch.object(target, "_save", side_effect=OSError("disk full")), pytest.raises(OSError):
        transfer(source, target, move=True)
    assert source.path.read_bytes() == before


def test_user_management_rejects_unprivileged_caller():
    from argparse import Namespace

    from lanctl.apps.access.manager_cli import _user_command

    with (
        patch("lanctl.core.local_permissions.elevated", return_value=False),
        pytest.raises(PermissionError),
    ):
        _user_command(Namespace(action="list"))


def test_screen_renders_single_frame_and_restores_terminal():
    import io

    from rich.text import Text

    from lanctl.core.terminal_ui import ManagementScreen

    class Terminal(io.StringIO):
        def isatty(self):
            return True

    output = Terminal()
    with patch("sys.stdout", output), patch("sys.stdin", Terminal()), ManagementScreen() as screen:
        screen.draw(Text("Hello"))
        screen.draw(Text("Next"))
    assert "\x1b[?1049h" in output.getvalue()
    assert "\x1b[?1049l" in output.getvalue()
    assert "\x1b[2J" not in output.getvalue()


def test_lanmon_logs_cli(tmp_path, capsys):
    from lanctl.bootstrap.lanmon import main

    with (
        patch("lanctl.core.config.load_config", return_value={"programLog": str(tmp_path)}),
        patch("lanctl.bootstrap.lanmon.build_parser") as parser,
    ):
        from argparse import Namespace

        parser.return_value.parse_args.return_value = Namespace(
            cli=False, tui=False, words=["logs"], project=None, source="all", limit=10, level=1
        )
        assert main(["logs"]) == 0
    assert json.loads(capsys.readouterr().out) == []
