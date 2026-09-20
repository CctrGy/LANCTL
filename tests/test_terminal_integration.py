import importlib.machinery
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from lanctl.core.plugins.contracts import FunctionResult
from lanctl.core.terminal_integration import FUNCTION, OWNER, route_tui


@pytest.fixture
def plugin(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "plugins-src/lanctl.integration.terminal/main.exec"
    loader = importlib.machinery.SourceFileLoader("terminal_plugin_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("ProgramData", str(tmp_path / "shared"))
    monkeypatch.setattr(module, "directory", lambda: tmp_path / "preferences")
    monkeypatch.setattr(module, "executable", lambda mode: "C:/Program Files/LANCTL/lanip.exe")
    return module


def test_profiles_preserve_personal_and_remove_recoverably(plugin):
    plugin.create("cli")
    assert json.loads(plugin.fragment("cli").read_text())["profiles"][0]["name"] == "LANCTL"
    plugin.create("cli")
    plugin.remove("cli")
    assert plugin.fragment("cli").with_suffix(".json.removed").exists()
    personal = plugin.fragment("cli").parents[2] / "settings.json"
    personal.write_text('{"profiles":{"list":[{"name":"LANCTL"}]}}')
    with pytest.raises(ValueError, match="perfil personal"):
        plugin.create("cli")


def test_bridge_absent_or_wrong_owner():
    manager = Mock()
    manager.functions.owner.side_effect = ValueError("missing")
    assert not route_tui(manager, [])
    manager.functions.owner.side_effect = None
    manager.functions.owner.return_value = "other"
    assert not route_tui(manager, [])
    manager.functions.call.assert_not_called()


def test_bridge_preserves_arguments():
    manager = Mock()
    manager.functions.owner.return_value = OWNER
    manager.functions.call.return_value = FunctionResult(True, data={"relaunched": True})
    args = ["--tui", "-project", "home.vlf"]
    assert route_tui(manager, args)
    manager.functions.call.assert_called_once_with(FUNCTION, args, caller="LANCTL")


def test_launch_no_shell_and_blocks_wt_separators(plugin, monkeypatch):
    monkeypatch.setattr(plugin.shutil, "which", lambda name: "wt.exe")
    run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(plugin.subprocess, "run", run)
    plugin.launch("tui", ["--tui", "-project", "home project.vlf"])
    assert run.call_args.args[0][-1] == "home project.vlf"
    assert run.call_args.kwargs["env"]["LANCTL_TERMINAL_RELAUNCHED"] == "1"
    with pytest.raises(ValueError):
        plugin.launch("tui", ["bad;new-tab"])


def test_activation_and_loop_guards(plugin, monkeypatch):
    api = Mock()
    plugin.activate(api)
    functions = {call.args[0]: call.args[1] for call in api.functions.register.call_args_list}
    assert FUNCTION in functions
    command = functions["TerminalIntegration.Profile.Command.Run"]
    assert command(["help"]).success
    assert command(["configure", "windows-terminal"]).success
    assert plugin.preferences()["terminal"] == "windows-terminal"
    launch = Mock()
    monkeypatch.setattr(plugin, "launch", launch)
    monkeypatch.setenv("LANCTL_TERMINAL_RELAUNCHED", "1")
    assert not functions[FUNCTION](["--tui"]).data["relaunched"]
    launch.assert_not_called()
