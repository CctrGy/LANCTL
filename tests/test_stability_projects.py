from types import SimpleNamespace
from unittest.mock import patch

from lanctl.core.file_transaction import atomic_write_json
from lanctl.core.projects.save_policy import save_active_project
from lanctl.core.projects.vlf import create_project, inspect_project


def test_empty_project_can_be_saved_without_inventing_reserved_devices(tmp_path):
    database = tmp_path / "devices.json"
    groups = tmp_path / "groups.json"
    atomic_write_json(database, [])
    atomic_write_json(groups, [])
    project = tmp_path / "empty.vlf"
    settings = {
        "database": str(database),
        "groups": str(groups),
        "activeProject": str(project),
        "projectSaveMode": "manual",
        "projectWorkspace": {
            "database": str(database),
            "groups": str(groups),
            "metadata": str(tmp_path / "workspace.json"),
        },
    }
    manager = SimpleNamespace(
        events=SimpleNamespace(emit=lambda *args: None), project_registry=dict
    )
    with (
        patch("lanctl.core.plugins.get_plugin_manager", return_value=manager),
        patch("lanctl.core.projects.save_policy.write_log"),
    ):
        create_project(project, config=settings, initialize_reserved=False)
        assert save_active_project(force=True, config=settings).saved
    assert inspect_project(project)["devices"] == 0


def test_update_resolves_configured_project_directory(tmp_path):
    from lanctl.apps.ip.interfaces.cli.commands import project as cli

    project = tmp_path / "home.vlf"
    settings = {"activeProject": str(project), "projectsDirectory": str(tmp_path)}
    with (
        patch.object(cli, "load_config", return_value=settings),
        patch(
            "lanctl.core.projects.save_policy.save_active_project",
            return_value=SimpleNamespace(saved=True, path=str(project)),
        ) as save,
        patch.object(cli, "_set_active_project"),
        patch.object(cli, "verify_project", return_value={"checksum": "test"}),
        patch.object(cli, "write_log"),
    ):
        assert cli._update(SimpleNamespace(file="home.vlf")) == 0
    save.assert_called_once_with(force=True, config=settings)
