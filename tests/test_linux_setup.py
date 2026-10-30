"""Linux setup: privilege boundary, protected accounts and a responsive real Qt wizard."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging/linux"))
model = importlib.import_module("setup_model")


def test_install_uses_apt_as_admin_but_defaults_remain_user_scoped(tmp_path):
    package = tmp_path / "a package; echo bad.deb"
    selection = model.Selection(language="es", plugins=[], network_tools=False, completion=False)
    command = model.install_command(package, selection)
    assert command == [
        "/usr/bin/pkexec",
        "/usr/bin/apt-get",
        "install",
        "--yes",
        "--no-install-recommends",
        str(package),
    ]
    assert selection.defaults_command() == [
        "/opt/lanctl/lanctl",
        "setup-defaults",
        "--theme",
        "graphite",
        "--plugins",
        "none",
        "--language",
        "es",
    ]
    selection.change_language = True
    assert selection.defaults_command()[-1] == "--change-language"
    selection.plugins = ["unknown"]
    with pytest.raises(ValueError):
        selection.defaults_command()


def test_environment_does_not_leak_source_data_or_frozen_libraries(monkeypatch):
    monkeypatch.setenv("LANCTL_DATA_DIR", "/temporary-demo")
    monkeypatch.setenv("LANCTL_SECRET_DIR", "/temporary-secrets")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/temporary-frozen-libs")
    monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)
    env = model.clean_environment()
    assert not any(key.startswith("LANCTL_") for key in env)
    assert "LD_LIBRARY_PATH" not in env
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/original")
    assert model.clean_environment()["LD_LIBRARY_PATH"] == "/original"


def test_package_integrity_and_identity_checked_before_install(tmp_path, monkeypatch):
    package = tmp_path / "lanctl.deb"
    package.write_bytes(b"sample package")
    arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine())
    metadata = {
        "schemaVersion": 1,
        "package": package.name,
        "version": "0.3.4-alpha.2",
        "arch": arch,
        "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
        "languages": [{"code": "en", "nativeName": "English"}],
    }
    (tmp_path / "setup.json").write_text(json.dumps(metadata))
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda *a, **kw: f"Package: lanctl\nVersion: 0.3.4-alpha.2\nArchitecture: {arch}\n",
    )
    assert model.load_distribution(tmp_path) == metadata
    package.write_bytes(b"modified")
    with pytest.raises(ValueError, match="checksum"):
        model.load_distribution(tmp_path)
    metadata["package"] = "../lanctl.deb"
    (tmp_path / "setup.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="filename"):
        model.load_distribution(tmp_path)


def test_shortcuts_and_completion_only_touch_selected_user_files(tmp_path):
    selection = model.Selection(ipgui=True, events=True, access_admin=True)
    model.write_shortcuts(selection, tmp_path)
    applications = tmp_path / ".local/share/applications"
    assert len(list(applications.glob("*.desktop"))) == 4
    assert "Terminal=false" in (applications / "lanctl-setup.desktop").read_text()
    assert "Terminal=true" in (applications / "lanmon-setup.desktop").read_text()
    completion = tmp_path / ".local/share/bash-completion/completions/lanctl"
    assert "--gui" in completion.read_text()
    selection.completion = False
    model.write_shortcuts(selection, tmp_path)
    assert not completion.exists()
    completion.write_text("# custom user completion")
    model.write_shortcuts(selection, tmp_path)
    assert completion.read_text() == "# custom user completion"
    assert not (tmp_path / ".bashrc").exists()


def test_remote_accounts_require_root_and_reject_symlinks(tmp_path, monkeypatch):
    account = importlib.import_module("setup_account")
    monkeypatch.setattr(account.os, "geteuid", lambda: 1000)
    with pytest.raises(PermissionError):
        account.create_account({}, tmp_path)
    monkeypatch.setattr(account.os, "geteuid", lambda: 0)
    (tmp_path / "redirect").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="Redirected"):
        account.create_account({}, tmp_path / "redirect")


@pytest.fixture
def qt_app(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    qt = pytest.importorskip("PyQt6.QtWidgets")
    app = qt.QApplication.instance() or qt.QApplication([])
    yield app


def wizard():
    gui = importlib.import_module("setup_gui")
    return gui.Installer(
        Path("/package"),
        {
            "version": "0.3.4-alpha.2",
            "arch": "amd64",
            "package": "lanctl.deb",
            "languages": [
                {"code": "en", "nativeName": "English"},
                {"code": "es", "nativeName": "Español"},
                {"code": "fr", "nativeName": "Français"},
            ],
        },
    )


def test_real_wizard_language_controls_and_review(qt_app):
    window = wizard()
    window.show()
    qt_app.processEvents()
    window.installer_language.setCurrentIndex(1)
    assert window.program_language.currentData() == "es"
    assert window.checks["completion"].text().startswith("Activar")
    window.program_language.setCurrentIndex(2)
    assert window.selection().language == "fr"
    window.checks["monitor"].setChecked(True)
    window.checks["tools"].setChecked(False)
    while window.currentPage() != window.pages_by_key["review"]:
        window.next()
        qt_app.processEvents()
    assert "Français" in window.summary.toPlainText()
    assert "Activar LANMON como servicio del sistema: Sí" in window.summary.toPlainText()
    assert window.selection().monitor
    assert not window.selection().network_tools
    window.close()


def test_install_progress_is_async_and_failure_does_not_claim_success(qt_app, monkeypatch):
    gui = importlib.import_module("setup_gui")
    window = wizard()
    monkeypatch.setattr(
        gui,
        "install_command",
        lambda *a: [sys.executable, "-c", "import time; time.sleep(.1); print('APT OK')"],
    )
    monkeypatch.setattr(
        model.Selection,
        "defaults_command",
        lambda _s: [sys.executable, "-c", "print('DEFAULTS OK')"],
    )
    shortcuts = []
    monkeypatch.setattr(gui, "write_shortcuts", lambda *a: shortcuts.append(a))
    window.show()
    window.start_installation()
    assert window.running and not window.completed
    deadline = time.monotonic() + 8
    while window.running and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.01)
    assert window.completed
    assert len(shortcuts) == 1
    assert "APT OK" in window.log.toPlainText()
    assert "DEFAULTS OK" in window.log.toPlainText()
    monkeypatch.setattr(
        gui, "install_command", lambda *a: [sys.executable, "-c", "raise SystemExit(7)"]
    )
    window.start_installation()
    deadline = time.monotonic() + 8
    while window.running and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.01)
    assert not window.completed and not window.running
    assert "Exit: 7" in window.log.toPlainText()
    assert len(shortcuts) == 1
    window.close()


def test_remote_password_uses_stdin_and_is_cleared_after_delivery(qt_app, monkeypatch):
    gui = importlib.import_module("setup_gui")
    window = wizard()
    window.checks["remote_account"].setChecked(True)
    values = {
        "username": "tester",
        "password": "Long-test-password!",
        "confirmation": "Long-test-password!",
    }
    for key, value in values.items():
        window.account_fields[key].setText(value)
    started, written = [], []
    monkeypatch.setattr(
        window.process, "start", lambda program, args: started.append([program, *args])
    )
    monkeypatch.setattr(window.process, "write", lambda raw: written.append(bytes(raw)))
    monkeypatch.setattr(window.process, "closeWriteChannel", lambda: None)
    monkeypatch.setattr(gui, "install_command", lambda *a: ["apt", "install"])
    window.start_installation()
    window.next_command()  # user-scoped defaults
    window.next_command()  # privileged account helper
    assert started[-1] == [
        "/usr/bin/pkexec",
        sys.executable,
        str(Path(gui.__file__).resolve()),
        "--create-account",
    ]
    assert values["password"] not in repr(started)
    window.process_started()
    assert json.loads(written[0]) == values
    assert window.account_input is None
    assert not window.account_fields["password"].text()
    assert values["password"] not in window.log.toPlainText()
    window.running = False
    window.close()


def test_missing_process_and_bad_account_leave_wizard_recoverable(qt_app, monkeypatch):
    gui = importlib.import_module("setup_gui")
    window = wizard()
    window.show()
    monkeypatch.setattr(
        gui, "install_command", lambda *a: ["/nonexistent/lanctl-installer-command"]
    )
    window.start_installation()
    deadline = time.monotonic() + 5
    while window.running and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.01)
    assert not window.completed and not window.running
    assert window.button(gui.QWizard.WizardButton.CancelButton).isEnabled()
    window.checks["remote_account"].setChecked(True)
    window.restart()
    while window.currentPage() != window.pages_by_key["account"]:
        window.next()
    messages = []
    monkeypatch.setattr(gui.QMessageBox, "warning", lambda *a: messages.append(a))
    assert not window.validateCurrentPage()
    assert len(messages) == 1
    window.close()


def test_first_account_reuses_auth_store_and_preserves_existing_users(tmp_path, monkeypatch):
    from types import SimpleNamespace

    account = importlib.import_module("setup_account")
    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LANCTL_SECRET_DIR", str(tmp_path / "secrets"))
    (tmp_path / "data/config").mkdir(parents=True)
    (tmp_path / "data/config/migration-v2.complete").write_text("LANCTL-DATA-V2\n")
    service = SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid())
    monkeypatch.setattr(account.os, "geteuid", lambda: 0)
    monkeypatch.setattr(account.pwd, "getpwnam", lambda _name: service)
    drops = []
    for operation in ("setgroups", "setgid", "setuid"):
        monkeypatch.setattr(
            account.os, operation, lambda value, operation=operation: drops.append(operation)
        )
    original_umask = os.umask(0o077)
    try:
        root = tmp_path / "access"
        root.mkdir()
        request = {
            "username": "admin-test",
            "password": "Long-test-password!",
            "confirmation": "Long-test-password!",
        }
        assert account.create_account(request, root)["created"]
        from lanctl.apps.access.auth import verify_password
        from lanctl.apps.access.store import AccessStore

        users = AccessStore(root / "users.dc").users()
        assert len(users) == 1 and users[0].username == "admin-test"
        assert verify_password(request["password"], users[0].passwordHash)
        assert drops[:3] == ["setgroups", "setgid", "setuid"]
        before = (root / "users.dc").read_bytes()
        result = account.create_account({"username": "other"}, root)
        assert result == {"created": False, "preservedExistingUsers": True}
        assert (root / "users.dc").read_bytes() == before
        assert request["password"] not in before.decode()
    finally:
        os.umask(original_umask)
