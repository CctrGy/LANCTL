import json
from unittest.mock import Mock

import pytest

from lanctl.core import first_scan


def test_request_consumed_once_without_network_or_inventory_actions(tmp_path, monkeypatch):
    path = tmp_path / "request.json"
    monkeypatch.setattr(first_scan, "_path", lambda: path)
    monkeypatch.setattr(first_scan, "load_config", lambda: {"range": "10.0.0.0/24"})
    monkeypatch.setattr("lanctl.core.network_interfaces.ipv4_interfaces", list)
    assert not first_scan.scan_choices()["requested"]
    first_scan.request_first_scan()
    assert first_scan.scan_choices()["range"] == "10.0.0.0/24"
    assert not first_scan.scan_choices()["interfaceSelectionAvailable"]
    assert first_scan.consume_request()
    assert not first_scan.consume_request()
    assert not first_scan.scan_choices()["requested"]


def test_invalid_request_not_interpreted_as_scan_authorization(tmp_path, monkeypatch):
    path = tmp_path / "request.json"
    monkeypatch.setattr(first_scan, "_path", lambda: path)
    path.write_text(json.dumps({"schemaVersion": 1, "requested": "yes", "created": 0}))
    with pytest.raises(ValueError):
        first_scan.consume_request()


def test_installer_gui_launch_requires_normal_identity_and_never_scans(monkeypatch):
    launch = Mock()
    request = Mock()
    monkeypatch.setattr(first_scan.subprocess, "Popen", launch)
    monkeypatch.setattr(first_scan, "request_first_scan", request)
    monkeypatch.setattr("lanctl.core.local_permissions.elevated", lambda: True)
    with pytest.raises(PermissionError):
        first_scan.launch_installed_gui(first_scan=True)
    launch.assert_not_called()
    request.assert_not_called()
    monkeypatch.setattr("lanctl.core.local_permissions.elevated", lambda: False)
    result = first_scan.launch_installed_gui(first_scan=True)
    assert result["scanRequested"] and not result["scanStarted"]
    assert launch.call_args.args[0][-1] == "--gui"
    assert not launch.call_args.kwargs.get("shell")
