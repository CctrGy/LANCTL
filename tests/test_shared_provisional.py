"""Shared draft discovery preserves user data and serializes launcher joins."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.core.coordination import Coordinator
from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.provisional import (
    cancel_provisional_close,
    claim_provisional_close,
    complete_provisional_close,
    prepare_provisional_close,
    provisional_operation,
    shared_provisional_workspace,
)


def setup(tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owners = [coordinator.register(name, "gui") for name in ("lanip", "lanwire")]
    return coordinator, owners, tmp_path / "drafts"


def test_concurrent_launchers_share_one_draft_and_existing_inventory(tmp_path):
    coordinator, owners, root = setup(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        drafts = list(
            pool.map(
                lambda owner: shared_provisional_workspace(
                    owner, coordinator=coordinator, root=root
                ),
                owners,
            )
        )
    assert drafts[0] == drafts[1]
    assert len(list(root.glob("*/workspace.json"))) == 1
    metadata = json.loads((drafts[0].root / "workspace.json").read_text())
    assert set(metadata["owners"]) == set(owners)
    with provisional_operation(drafts[0], owners[0], coordinator=coordinator, base={}) as settings:
        DeviceDatabase(settings["database"]).add_manual_device(alias="Preserved")
    reopened = shared_provisional_workspace(owners[1], coordinator=coordinator, root=root)
    assert reopened == drafts[0]
    assert DeviceDatabase(reopened.settings({})["database"]).load()[0].alias == "Preserved"


def test_close_lease_blocks_join_and_closed_draft_is_retained(tmp_path):
    coordinator, owners, root = setup(tmp_path)
    draft = shared_provisional_workspace(owners[0], coordinator=coordinator, root=root)
    claim = claim_provisional_close(draft, owners[0], coordinator=coordinator)
    with pytest.raises(RuntimeError):
        shared_provisional_workspace(owners[1], coordinator=coordinator, root=root)
    cancel_provisional_close(draft, owners[0], claim["token"], coordinator=coordinator)
    claim = claim_provisional_close(draft, owners[0], coordinator=coordinator)
    assert prepare_provisional_close(draft, owners[0], claim["token"], coordinator=coordinator)[
        "ready"
    ]
    complete_provisional_close(draft, owners[0], claim["token"], coordinator=coordinator)
    old_files = {p.name: p.read_bytes() for p in draft.root.iterdir() if p.is_file()}
    new = shared_provisional_workspace(owners[1], coordinator=coordinator, root=root)
    assert new.identifier != draft.identifier
    assert old_files == {p.name: p.read_bytes() for p in draft.root.iterdir() if p.is_file()}


def test_dead_owner_draft_is_recovered_without_reset(tmp_path):
    coordinator, owners, root = setup(tmp_path)
    draft = shared_provisional_workspace(owners[0], coordinator=coordinator, root=root)
    DeviceDatabase(draft.settings({})["database"]).add_manual_device(alias="Recover me")
    coordinator.close(owners[0])
    recovered = shared_provisional_workspace(owners[1], coordinator=coordinator, root=root)
    assert recovered == draft
    assert DeviceDatabase(recovered.settings({})["database"]).load()[0].alias == "Recover me"


@pytest.mark.parametrize("damage", ["index", "metadata", "missing"])
def test_invalid_shared_state_never_replaces_inventory(tmp_path, damage):
    coordinator, owners, root = setup(tmp_path)
    draft = shared_provisional_workspace(owners[0], coordinator=coordinator, root=root)
    database = draft.root / "devices.json"
    DeviceDatabase(database).add_manual_device(alias="Do not erase")
    index = next(root.glob("shared-*.json"))
    if damage == "index":
        index.write_text('{"schemaVersion":true}', encoding="utf-8")
    elif damage == "metadata":
        (draft.root / "workspace.json").write_text("broken", encoding="utf-8")
    else:
        (draft.root / "workspace.json").unlink()
    before = database.read_bytes()
    index_before = index.read_bytes()
    with pytest.raises(ValueError):
        shared_provisional_workspace(owners[1], coordinator=coordinator, root=root)
    assert database.read_bytes() == before
    assert index.read_bytes() == index_before
    assert len([p for p in root.iterdir() if p.is_dir()]) == 1


def test_unknown_or_cli_session_cannot_allocate_shared_draft(tmp_path):
    coordinator, _, root = setup(tmp_path)
    cli = coordinator.register("lanip", "cli")
    for owner in ("unknown", cli):
        with pytest.raises(ValueError):
            shared_provisional_workspace(owner, coordinator=coordinator, root=root)
    assert not root.exists()


def test_separate_processes_discover_the_same_shared_draft(tmp_path):
    script = """
import json, sys
from pathlib import Path
from lanctl.core.coordination import Coordinator
from lanctl.core.projects.provisional import shared_provisional_workspace
coordinator = Coordinator(Path(sys.argv[1]) / 'coordinator.db')
owner = coordinator.register(sys.argv[2], 'gui')
draft = shared_provisional_workspace(owner, coordinator=coordinator, root=Path(sys.argv[1]) / 'drafts')
print(json.dumps(draft.identifier))
"""

    def launch(name):
        result = subprocess.run(
            [sys.executable, "-c", script, str(tmp_path), name],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        return json.loads(result.stdout)

    # Two small Python workers, no GUI/browser or network scan.
    with ThreadPoolExecutor(max_workers=2) as pool:
        identifiers = list(pool.map(launch, ("lanip", "lanwire")))
    assert identifiers[0] == identifiers[1]
    assert len(list((tmp_path / "drafts").glob("*/workspace.json"))) == 1


def test_gui_operations_use_draft_context_and_preserve_local_inventory(workspace, tmp_path):
    from unittest.mock import patch

    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.apps.suite.launcher_gui import LauncherApi
    from lanctl.core.config import CONFIG_PATH, load_config

    coordinator, owners, root = setup(tmp_path)
    draft = shared_provisional_workspace(owners[0], coordinator=coordinator, root=root)
    shared_provisional_workspace(owners[1], coordinator=coordinator, root=root)
    historical = DeviceDatabase(workspace["database"])
    historical.add_manual_device(alias="Historical")
    historical_bytes = historical.path.read_bytes()
    config_bytes = CONFIG_PATH.read_bytes()
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop = DesktopApi()
        wire = LauncherApi("lanwire")
    with provisional_operation(draft, owners[0], coordinator=coordinator, base=workspace):
        created = desktop.create_device({"alias": "Draft only", "idf": "AB-12"})
        assert created["ok"], created
        records = DeviceDatabase(load_config()["database"]).load()
        assert [item.alias for item in records] == ["Draft only"]
        device_id = records[0].device_id
        assert desktop.update_device(device_id, {"alias": "Updated draft"})["ok"]
    with provisional_operation(draft, owners[1], coordinator=coordinator, base=workspace):
        created = wire.wire_create({"kind": "pc.1port", "prefix": "PC", "name": "Draft PC"})
        assert created["ok"], created
        assert any(row["id"] == created["id"] for row in wire.bootstrap()["records"])
        assert desktop.delete_device(device_id, confirmed=True)["ok"]
        assert DeviceDatabase(load_config()["database"]).load() == []
    assert load_config()["database"] == workspace["database"]
    assert historical.path.read_bytes() == historical_bytes
    assert CONFIG_PATH.read_bytes() == config_bytes


def test_provisional_context_rejects_other_project_and_restores_after_failure(tmp_path):
    from lanctl.core.project_context import operation_config, project_operation

    coordinator, owners, root = setup(tmp_path)
    draft = shared_provisional_workspace(owners[0], coordinator=coordinator, root=root)
    with project_operation({"activeProject": "other.vlf", "database": "other.json"}):
        with (
            pytest.raises(ValueError),
            provisional_operation(draft, owners[0], coordinator=coordinator, base={}),
        ):
            pytest.fail("A different in-flight project must not be redirected")
        assert operation_config()["activeProject"] == "other.vlf"
    with (
        pytest.raises(RuntimeError, match="controlled failure"),
        provisional_operation(draft, owners[0], coordinator=coordinator, base={}),
    ):
        assert operation_config()["database"] == str(draft.root / "devices.json")
        raise RuntimeError("controlled failure")
    assert operation_config() is None
    with (
        provisional_operation(draft, owners[0], coordinator=coordinator, base={}) as settings,
        provisional_operation(draft, owners[0], coordinator=coordinator, base={}),
    ):
        assert operation_config()["database"] == settings["database"]


def test_saving_preferences_does_not_persist_draft_private_paths(workspace, tmp_path):
    from lanctl.core import config

    coordinator, owners, root = setup(tmp_path)
    draft = shared_provisional_workspace(owners[0], coordinator=coordinator, root=root)
    original = config.load_config()
    with provisional_operation(draft, owners[0], coordinator=coordinator, base=original):
        for timeout in (2.0, 3.0):
            settings = config.load_config()
            settings["timeout"] = timeout
            config.save_config(settings)
            stored = config._load_config()
            assert stored["timeout"] == timeout
            for key in ("credentials", "log", "programLog", "database", "projectWorkspace"):
                assert stored[key] == original[key], key
            # Saving preferences must not redirect the ongoing draft operation.
            assert config.load_config()["credentials"] == str(draft.root / "private/credentials")
            assert config.load_config()["database"] == str(draft.root / "devices.json")
    assert config.load_config()["credentials"] == original["credentials"]


def test_draft_preference_save_preserves_new_global_paths(workspace, tmp_path):
    from lanctl.core import config

    coordinator, owners, root = setup(tmp_path)
    draft = shared_provisional_workspace(owners[0], coordinator=coordinator, root=root)
    original = config.load_config()
    with provisional_operation(draft, owners[0], coordinator=coordinator, base=original):
        changed = config._load_config()
        for key in ("credentials", "log", "programLog"):
            changed[key] = str(tmp_path / "new-global" / key)
        config.CONFIG_PATH.write_text(
            json.dumps(config.canonical_config(changed)), encoding="utf-8"
        )
        settings = config.load_config()
        settings["timeout"] = 2.0
        config.save_config(settings)
        for key in ("credentials", "log", "programLog"):
            assert config._load_config()[key] == changed[key]
        # A deliberate edit of a global preference is still supported.
        settings = config.load_config()
        settings["log"] = str(tmp_path / "explicit-logs")
        config.save_config(settings)
        assert config._load_config()["log"] == settings["log"]
        assert config._load_config()["credentials"] == changed["credentials"]
