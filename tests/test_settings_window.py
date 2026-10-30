"""Complete GUI settings metadata and atomic program form submissions."""

from unittest.mock import patch

from test_launcher_gui import workspace as workspace

from lanctl.apps.suite.gui import SuiteApi
from lanctl.apps.suite.settings import settings_entries
from lanctl.core import config
from lanctl.core.project_context import project_identity
from lanctl.core.settings_policy import SettingsContext


def suite():
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        return SuiteApi()


def test_form_describes_every_visible_preference_without_exposing_internal_paths(workspace):
    window = suite()
    payload = window.settings_catalog()
    assert payload["ok"], payload
    entries = {item["path"]: item for item in payload["entries"]}
    assert set(entries) == {item["path"] for item in settings_entries(SettingsContext("gui"))}
    assert len(entries) > 50
    assert "cli.commandChaining" not in entries
    assert "storage.credentials" not in entries
    assert entries["startup.closeGuiOnLaunch"]["control"] == "boolean"
    assert entries["ip.workers"]["control"] == "number"
    assert entries["projects.directory"]["nullable"]
    assert entries["network.dnsServers"]["control"] == "lines"
    assert {choice["value"] for choice in entries["gui.theme"]["choices"]} >= {"graphite", "light"}
    assert "manual" in {choice["value"] for choice in entries["projects.saveMode"]["choices"]}


def test_form_batch_validates_before_writing_and_preserves_unrelated_settings(workspace):
    window = suite()
    before = config.CONFIG_PATH.read_bytes()
    rejected = window.save_catalog_settings({"logging.retentionDays": 15, "gui.fontScale": -9})
    assert not rejected["ok"]
    assert config.CONFIG_PATH.read_bytes() == before
    accepted = window.save_catalog_settings({"logging.retentionDays": 15, "gui.density": "compact"})
    assert accepted["ok"], accepted
    current = config.load_config()
    assert current["logRetentionDays"] == 15
    assert current["guiPreferences"]["density"] == "compact"
    assert current["database"] == workspace["database"]
    before = config.CONFIG_PATH.read_bytes()
    for changes, launcher in (
        ({"storage.credentials": "secret"}, "lanctl"),
        ({"ip.workers": 12}, "lanmon"),
        ({"cli.commandChaining": True}, "lanctl"),
    ):
        assert not window.save_catalog_settings(changes, launcher)["ok"]
        assert config.CONFIG_PATH.read_bytes() == before


def test_form_batch_rejects_stale_project_context(workspace):
    window = suite()
    assert "save_catalog_settings" in window.bootstrap()["projectActions"]
    old = project_identity(config.load_config())
    before = config.CONFIG_PATH.read_bytes()
    rejected = window.project_call(
        ["different-project"], "save_catalog_settings", [{"gui.density": "compact"}]
    )
    assert not rejected["ok"]
    assert config.CONFIG_PATH.read_bytes() == before
    assert window.project_call(old, "save_catalog_settings", [{"gui.density": "compact"}])["ok"]
