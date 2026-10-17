import os
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
