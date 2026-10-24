"""Physical project isolation and VLF persistence through real shared APIs."""

import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.core import config
from lanctl.core.projects.workspace import activate_project_workspace


def physical_inventory():
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "name": "Rack First"})
    assert cabinet["ok"], cabinet
    room = rack.rack_organization(
        rack.bootstrap()["organizationRevision"], "create", {"name": "CPD First"}
    )
    assert room["ok"], room
    assert rack.rack_organization(
        rack.bootstrap()["organizationRevision"],
        "assign",
        {"rack": cabinet["id"], "id": room["id"]},
    )["ok"]
    pc = wire.wire_create({"kind": "pc.1port", "prefix": "PC", "name": "PC First"})
    cable = wire.wire_create({"kind": "wire.copper", "prefix": "WL", "name": "Cable First"})
    assert pc["ok"] and cable["ok"]
    record = next(r for r in wire.bootstrap()["records"] if r["id"] == cable["id"])
    assert wire.wire_connect(
        cable["id"], record["revision"], [{"device": pc["id"], "port": "LAN1"}]
    )["ok"]
    return wire, rack


def test_physical_edits_mark_active_project_dirty(workspace, tmp_path):
    projects(workspace, tmp_path)
    assert not api("lanwire").project_state()["dirty"]
    wire, _ = physical_inventory()
    assert wire.project_state()["dirty"]


def test_switching_projects_isolates_racks_cables_and_cpds(workspace, tmp_path):
    _, second = projects(workspace, tmp_path)
    wire, rack = physical_inventory()
    assert wire.save_project()["ok"]
    activate_project_workspace(second)
    snapshot = wire.bootstrap()
    assert snapshot["project"] == second
    assert snapshot["records"] == []
    assert snapshot["cpds"] == []
    assert rack.bootstrap()["records"] == []


def test_saved_vlf_restores_physical_inventory_without_original_database(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    wire, _ = physical_inventory()
    original = wire.bootstrap()
    saved = wire.save_project()
    assert saved["ok"], saved
    assert Path(first).is_file()
    # Simulate reopening on another installation: no original physical file.
    # Only the test configuration is changed; the original file is preserved.
    fresh = config.load_config()
    fresh["physicalDatabase"] = str(tmp_path / "fresh-installation" / "idf.db")
    config.save_config(fresh)
    activate_project_workspace(first, root=tmp_path / "fresh-workspaces", refresh=True)
    reopened = api("lanwire").bootstrap()
    assert reopened["project"] == first
    assert reopened["records"] == original["records"]
    assert reopened["cpds"] == original["cpds"]


def test_legacy_global_is_preserved_and_import_requires_empty_explicit_project(workspace, tmp_path):
    from lanctl.core.project_context import project_identity
    from lanctl.core.projects.physical import import_inventory

    legacy, _ = physical_inventory()
    source = Path(legacy._service.database.path)
    original = source.read_bytes()
    first, second = projects(workspace, tmp_path)
    assert api("lanwire").bootstrap()["records"] == []
    assert config.load_config()["legacyPhysicalDatabase"] == str(source)
    expected = project_identity(config.load_config())
    assert import_inventory(source, expected)["records"] == 3
    assert source.read_bytes() == original
    with pytest.raises(ValueError, match="ya tiene"):
        import_inventory(source, expected)
    assert api("lanwire").save_project()["ok"]
    activate_project_workspace(second)
    with pytest.raises(ValueError, match="proyecto cambió"):
        import_inventory(source, expected)
    assert api("lanwire").bootstrap()["records"] == []
    activate_project_workspace(first, root=tmp_path / "restored")
    assert len(api("lanwire").bootstrap()["records"]) == 3


@pytest.mark.parametrize(
    "envelope",
    [
        {},
        {"schemaVersion": 2},
        {"schemaVersion": True},
        {"schemaVersion": 1, "inventory": None},
        {"schemaVersion": 1, "inventory": {"format": "OTHER"}},
    ],
)
def test_physical_archive_rejects_invalid_schema(envelope):
    from lanctl.core.projects.physical import decode_archive

    with pytest.raises(ValueError):
        decode_archive(json.dumps(envelope).encode())


def test_corrupt_working_inventory_cannot_replace_saved_vlf(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    wire, _ = physical_inventory()
    assert wire.save_project()["ok"]
    before = Path(first).read_bytes()
    Path(wire._service.database.path).write_text('{"records":', encoding="utf-8")
    assert not wire.save_project()["ok"]
    assert Path(first).read_bytes() == before


def test_empty_creation_does_not_clone_physical_working_copy(workspace, tmp_path):
    from lanctl.core.projects.physical import ARCHIVE_ENTRY
    from lanctl.core.projects.vlf import create_project

    projects(workspace, tmp_path)
    physical_inventory()
    settings = config.load_config()
    settings.update(
        database=str(tmp_path / "empty-devices.json"), groups=str(tmp_path / "empty-groups.json")
    )
    output = tmp_path / "Empty.vlf"
    create_project(output, config=settings, initialize_reserved=False)
    with ZipFile(output) as archive:
        assert ARCHIVE_ENTRY not in archive.namelist()


def test_physical_import_cli_is_local_and_keeps_legacy_source(workspace, tmp_path):
    from lanctl.apps.access.remote import required_permission
    from lanctl.apps.ip.interfaces.cli.main import build_parser

    wire, _ = physical_inventory()
    source = Path(wire._service.database.path)
    before = source.read_bytes()
    projects(workspace, tmp_path)
    args = build_parser().parse_args(["project", "import-physical", str(source)])
    assert args.handler(args) == 0
    assert len(api("lanwire").bootstrap()["records"]) == 3
    assert source.read_bytes() == before
    with pytest.raises(PermissionError, match="remoto"):
        required_permission(["project", "import-physical", str(source)])


def test_old_dirty_workspace_upgrade_preserves_unsaved_logical_changes(workspace, tmp_path):
    from lanctl.apps.ip.domain.models import Device
    from lanctl.core.database import DeviceDatabase

    first, _ = projects(workspace, tmp_path)
    current = config.load_config()["projectWorkspace"]
    DeviceDatabase(current["database"]).upsert([Device(ip="192.0.2.7", alias="Unsaved")])
    physical = Path(current["physicalDatabase"])
    physical.unlink()  # Disposable fixture: emulate a workspace from before REF-P84.
    metadata = Path(current["metadata"])
    document = json.loads(metadata.read_text(encoding="utf-8"))
    document.pop("physicalSchemaVersion")
    metadata.write_text(json.dumps(document), encoding="utf-8")
    activate_project_workspace(first)
    assert DeviceDatabase(current["database"]).load()[0].alias == "Unsaved"
    assert physical.is_file()
    assert api("lanwire").project_state()["dirty"]


def test_concurrent_physical_edit_is_not_falsely_marked_saved(workspace, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from lanctl.apps.wire.gui_service import WireGuiService
    from lanctl.core.projects import vlf
    from lanctl.core.projects.physical import ARCHIVE_ENTRY, decode_archive
    from lanctl.core.projects.save_policy import save_active_project

    first, _ = projects(workspace, tmp_path)
    wire, _ = physical_inventory()
    row = next(r for r in wire.bootstrap()["records"] if r["data"]["type"] == "wire")
    service = WireGuiService(wire._service.database.path)
    attempted, completed = Event(), Event()

    def edit():
        attempted.set()
        service.update(row["id"], row["revision"], {"name": "After snapshot"})
        completed.set()

    original = vlf.update_project
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []

        def save(*args, **kwargs):
            result = original(*args, **kwargs)
            futures.append(executor.submit(edit))
            assert attempted.wait(2)
            assert not completed.wait(0.1), "Writer escaped the save snapshot lock"
            return result

        monkeypatch.setattr(vlf, "update_project", save)
        assert save_active_project(force=True).saved
        futures[0].result(timeout=5)
    assert wire.project_state()["dirty"]
    with ZipFile(first) as archive:
        saved = decode_archive(archive.read(ARCHIVE_ENTRY))
    assert saved["records"][row["id"]]["data"]["name"] == "Cable First"


@pytest.mark.parametrize("already_open", [False, True])
def test_missing_project_physical_inventory_is_not_recreated(workspace, tmp_path, already_open):
    from test_project_sync import projects

    from lanctl.apps.wire.idf.database import IDFDatabaseManager
    from lanctl.core import config
    from lanctl.core.projects.workspace import activate_project_workspace

    first, _ = projects(workspace, tmp_path)
    path = Path(config.load_config()["physicalDatabase"])
    manager = IDFDatabaseManager(path) if already_open else None
    path.unlink()
    with pytest.raises(FileNotFoundError, match="inventario físico"):
        manager.create("PC") if manager else IDFDatabaseManager(path)
    assert not path.exists()
    # Recovery remains explicit; an old VLF without physical data is valid.
    activate_project_workspace(first, refresh=True, discard_changes=True)
    assert IDFDatabaseManager(path).all() == []


def test_gui_physical_changes_obey_automatic_all_changes(workspace, tmp_path):
    from test_launcher_gui import api
    from test_project_sync import projects

    from lanctl.core import config
    from lanctl.core.projects.save_policy import workspace_is_dirty
    from lanctl.core.projects.workspace import prepare_project_workspace

    first, _ = projects(workspace, tmp_path)
    cfg = config.load_config()
    cfg["projectSaveMode"] = "automatic.allChanges"
    config.save_config(cfg)
    wire = api("lanwire")
    assert wire.wire_create({"kind": "rack", "prefix": "RK", "name": "Automatic"})["ok"]
    assert not workspace_is_dirty(config.load_config())
    fresh = prepare_project_workspace(first, root=tmp_path / "new-installation")
    from lanctl.apps.wire.idf.database import IDFDatabaseManager

    assert IDFDatabaseManager(fresh.physical).all()[0]["data"]["name"] == "Automatic"
