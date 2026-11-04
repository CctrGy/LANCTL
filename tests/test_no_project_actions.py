"""Service-side matrix only: does not certify the native webview bridge."""

from unittest.mock import patch

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace

from lanctl.core import config
from lanctl.core.database import DeviceDatabase


@pytest.mark.parametrize(
    "launcher", ["lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"]
)
def test_no_project_common_actions_keep_valid_context(workspace, launcher):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.apps.suite.gui import SuiteApi

    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        window = (
            SuiteApi()
            if launcher == "lanctl"
            else DesktopApi()
            if launcher == "lanip"
            else api(launcher)
        )
    state = window.bootstrap()
    assert state["ok"], state
    assert state["projectContext"][0] == ""
    result = window.project_call(state["projectContext"], "project_state", [])
    assert result["ok"], result
    assert window.gui_preferences()["ok"]
    assert not config.load_config().get("activeProject")


def test_lanip_manual_crud_without_vlf_uses_context_guards(workspace):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi

    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        window = DesktopApi()
    expected = window.bootstrap()["projectContext"]
    created = window.project_call(
        expected, "create_device", [{"idf": "PC-001", "ip": "192.0.2.10", "name": "Manual"}]
    )
    assert created["ok"], created
    identifier = created["createdId"]
    updated = window.project_call(expected, "update_device", [identifier, {"alias": "Edited"}])
    assert updated["ok"], updated
    assert DeviceDatabase(config.load_config()["database"]).resolve(identifier).alias == "Edited"
    rejected = window.project_call(["stale", "", ""], "delete_device", [identifier, True])
    assert not rejected["ok"]
    assert DeviceDatabase(config.load_config()["database"]).resolve(identifier).alias == "Edited"
    deleted = window.project_call(expected, "delete_device", [identifier, True])
    assert deleted["ok"], deleted
    assert not DeviceDatabase(config.load_config()["database"]).load()
    assert not config.load_config().get("activeProject")
