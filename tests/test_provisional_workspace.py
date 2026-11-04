"""Provisional data is explicit, isolated and never silently reinitialized."""

import json

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.provisional import prepare_provisional_workspace
from lanctl.core.projects.save_policy import workspace_is_dirty


def test_fresh_provisional_does_not_copy_or_change_existing_data(tmp_path):
    historical = tmp_path / "historical.json"
    historical.write_text('[{"private":"existing"}]')
    base = {"database": str(historical), "activeProject": None, "credentials": "private-vault"}
    workspace = prepare_provisional_workspace(root=tmp_path / "provisional")
    settings = workspace.settings(base)
    assert settings["activeProject"] is None
    assert settings["database"] != str(historical)
    assert DeviceDatabase(settings["database"]).load() == []
    assert not workspace_is_dirty(settings)
    assert historical.read_text() == '[{"private":"existing"}]'
    assert base["credentials"] == "private-vault"
    assert settings["credentials"] != base["credentials"]


def test_explicit_reopen_preserves_shared_changes_and_detects_dirty(tmp_path):
    root = tmp_path / "provisional"
    first = prepare_provisional_workspace(root=root)
    settings = first.settings({})
    device = DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001", ip="192.0.2.1")
    second = prepare_provisional_workspace(root=root, identifier=first.identifier)
    assert second == first
    assert DeviceDatabase(second.settings({})["database"]).resolve(device.device_id).idf == "PC-001"
    assert workspace_is_dirty(settings)
    third = prepare_provisional_workspace(root=root)
    assert third.identifier != first.identifier
    assert not workspace_is_dirty(third.settings({}))


def test_failed_save_preserves_source_and_existing_destination(workspace, tmp_path):
    from lanctl.core.projects.provisional import save_provisional_project

    provisional = prepare_provisional_workspace(root=tmp_path / "provisional")
    settings = provisional.settings(workspace)
    DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001")
    original = (provisional.root / "devices.json").read_bytes()
    destination = tmp_path / "Existing.vlf"
    destination.write_bytes(b"existing-file-must-remain")
    with pytest.raises(ValueError):
        save_provisional_project(provisional, destination, name="Existing", base=workspace)
    assert destination.read_bytes() == b"existing-file-must-remain"
    assert (provisional.root / "devices.json").read_bytes() == original
    assert workspace_is_dirty(settings)


def test_incomplete_or_unknown_workspace_is_not_recreated(tmp_path):
    root = tmp_path / "provisional"
    workspace = prepare_provisional_workspace(root=root)
    database = workspace.root / "devices.json"
    original = database.read_bytes()
    metadata = workspace.root / "workspace.json"
    document = json.loads(metadata.read_text())
    document["schemaVersion"] = 999
    metadata.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        prepare_provisional_workspace(root=root, identifier=workspace.identifier)
    assert database.read_bytes() == original
    database.unlink()
    with pytest.raises(ValueError):
        prepare_provisional_workspace(root=root, identifier=workspace.identifier)
    assert not database.exists()


def test_save_reopens_network_groups_and_physical_without_private_data(workspace, tmp_path):
    from pathlib import Path
    from zipfile import ZipFile

    from lanctl.apps.wire.idf.database import IDFDatabaseManager
    from lanctl.core.group_database import GroupDatabase
    from lanctl.core.projects.provisional import save_provisional_project
    from lanctl.core.projects.workspace import prepare_project_workspace

    provisional = prepare_provisional_workspace(root=tmp_path / "provisional")
    settings = provisional.settings(workspace)
    devices = DeviceDatabase(settings["database"])
    device = devices.add_manual_device(idf="PC-001", ip="192.0.2.1")
    GroupDatabase(settings["groups"], devices).create("Office")
    physical = IDFDatabaseManager(settings["physicalDatabase"])
    record = physical.create("SW", data={"kind": "switch.5ports", "name": "Shared switch"})
    credentials = Path(settings["credentials"])
    credentials.parent.mkdir()
    credentials.write_bytes(b"PRIVATE-CREDENTIAL-SENTINEL")
    destination = tmp_path / "Saved.vlf"
    result = save_provisional_project(provisional, destination, name="Saved", base=workspace)
    reopened = prepare_project_workspace(result["path"], root=tmp_path / "reopened")
    assert DeviceDatabase(str(reopened.database)).resolve(device.device_id).idf == "PC-001"
    assert "OFFICE" in [
        g.name
        for g in GroupDatabase(str(reopened.groups), DeviceDatabase(str(reopened.database))).load()
    ]
    assert (
        IDFDatabaseManager(reopened.physical).get(record["id"])["data"]["name"] == "Shared switch"
    )
    with ZipFile(destination) as archive:
        assert archive.read("auth/logins.lgn") == b""
        assert all(
            b"PRIVATE-CREDENTIAL-SENTINEL" not in archive.read(name) for name in archive.namelist()
        )
    assert credentials.read_bytes() == b"PRIVATE-CREDENTIAL-SENTINEL"
    assert workspace_is_dirty(settings)
