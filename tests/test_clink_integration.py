import locale
import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.core import clink_integration as clink

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows Clink registration")


@pytest.fixture
def integration(tmp_path, monkeypatch):
    scripts = tmp_path / "path with spaces" / "clink"
    scripts.mkdir(parents=True)
    (scripts / "lanctl.lua").write_text("--test")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setattr(clink, "principal_id", lambda: "actual-user")
    monkeypatch.setattr(clink, "elevated", lambda: False)
    monkeypatch.setattr(clink, "_find_clink", lambda **kw: "C:/Program Files/clink/clink_x64.exe")
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(clink.subprocess, "run", run)
    return scripts, run


def test_register_update_unregister_exact_directory_without_shell(integration):
    scripts, run = integration
    assert clink.configure_clink("install", scripts)["status"] == "registered"
    assert clink.configure_clink("install", scripts)["status"] == "registered"
    assert clink.configure_clink("uninstall", scripts)["status"] == "unregistered"
    assert run.call_args.args[0][-2:] == ["uninstallscripts", str(scripts)]
    assert all(not call.kwargs.get("shell") for call in run.call_args_list)
    assert clink.configure_clink("uninstall", scripts)["status"] == "not-registered-for-user"
    assert run.call_count == 3


def test_wrong_principal_and_elevated_install_never_mutate_registry(integration, monkeypatch):
    scripts, run = integration
    monkeypatch.setattr(clink, "elevated", lambda: True)
    assert clink.configure_clink("install", scripts)["status"] == "normal-user-required"
    run.assert_not_called()
    monkeypatch.setattr(clink, "elevated", lambda: False)
    clink.configure_clink("install", scripts)
    monkeypatch.setattr(clink, "principal_id", lambda: "different-user")
    with pytest.raises(ValueError):
        clink.configure_clink("uninstall", scripts)
    assert run.call_count == 1


@pytest.mark.parametrize("action", ["install", "uninstall"])
def test_native_code_one_is_idempotent_only_when_registry_matches(integration, action):
    scripts, run = integration
    clink.configure_clink("install", scripts)
    run.reset_mock()
    listing = str(scripts).upper() + "\n" if action == "install" else "C:\\Other\\scripts\n"
    run.side_effect = [
        SimpleNamespace(returncode=1),
        SimpleNamespace(returncode=0, stdout=listing),
    ]

    result = clink.configure_clink(action, scripts)

    assert result["status"] == ("registered" if action == "install" else "unregistered")
    assert run.call_args.args[0][-2:] == ["installscripts", "--list"]
    assert clink._marker(scripts).exists() is (action == "install")
    assert all(not call.kwargs.get("shell") for call in run.call_args_list)


@pytest.mark.parametrize("list_status", [0, 1])
@pytest.mark.parametrize("action", ["install", "uninstall"])
def test_code_one_does_not_hide_failed_registration_or_unregistration(
    integration, action, list_status
):
    scripts, run = integration
    if action == "uninstall":
        clink.configure_clink("install", scripts)
    run.reset_mock()
    # A prefix match is not evidence that this exact directory is registered.
    listing = str(scripts) + ("-other\n" if action == "install" else "\n")
    run.side_effect = [
        SimpleNamespace(returncode=1),
        SimpleNamespace(returncode=list_status, stdout=listing),
    ]

    with pytest.raises(OSError, match="Clink no pudo"):
        clink.configure_clink(action, scripts)

    assert clink._marker(scripts).exists() is (action == "uninstall")


def test_registry_verification_timeout_preserves_error_cause(integration):
    scripts, run = integration
    timeout = clink.subprocess.TimeoutExpired(["clink", "installscripts", "--list"], 10)
    run.side_effect = [SimpleNamespace(returncode=1), timeout]

    with pytest.raises(TimeoutError) as raised:
        clink.configure_clink("install", scripts)

    assert raised.value.__cause__ is timeout
    assert not clink._marker(scripts).exists()


def test_utf8_registration_path_ignores_windows_ansi_code_page(tmp_path, monkeypatch):
    scripts = tmp_path / "completado con acento é"
    scripts.mkdir()
    (scripts / "lanctl.lua").write_text("--test")
    producer = tmp_path / "fake_clink.py"
    producer.write_text(
        "import sys\n"
        f"path = {str(scripts)!r}\n"
        "if '--list' in sys.argv:\n"
        "    sys.stdout.buffer.write((path + '\\n').encode('utf-8'))\n"
        "else:\n"
        "    sys.exit(1)\n",
        encoding="utf-8",
    )
    run = subprocess.run

    def native_output(command, **kwargs):
        return run([sys.executable, str(producer), *command[1:]], **kwargs)

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setattr(clink, "principal_id", lambda: "actual-user")
    monkeypatch.setattr(clink, "elevated", lambda: False)
    monkeypatch.setattr(clink, "_find_clink", lambda **kw: "clink.exe")
    monkeypatch.setattr(locale, "getpreferredencoding", lambda *args: "cp1252")
    if hasattr(subprocess, "_text_encoding"):
        monkeypatch.setattr(subprocess, "_text_encoding", lambda: "cp1252")
    monkeypatch.setattr(subprocess, "run", native_output)

    assert clink.configure_clink("install", scripts)["status"] == "registered"
    assert clink._marker(scripts).exists()
