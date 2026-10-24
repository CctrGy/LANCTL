"""P82: shared edits, concurrency, project boundaries and credential secrecy."""

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier
from unittest.mock import patch

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase
from lanctl.apps.monitor.models import CheckResult
from lanctl.core import config
from lanctl.core.database import DeviceDatabase
from lanctl.core.group_database import GroupDatabase
from lanctl.core.projects.workspace import activate_project_workspace


def inventory(workspace):
    database = DeviceDatabase(workspace["database"])
    device = database.upsert([{"IP": "192.0.2.10", "MAC": "02:00:00:00:00:10"}])[0]
    groups = GroupDatabase(workspace["groups"], database)
    groups.create("LAB")
    with MonitorDatabase(workspace["monitorDatabase"]) as db:
        MetricsStore(db).write(CheckResult("ping", device.device_id, True, latencyMs=4.2), "saved")
    return database, device, groups


def credential(workspace):
    database, device, _ = inventory(workspace)
    access = api("lanaccess", cipher="portable")
    assert access.access_unlock("Vault-test-12345", "Vault-test-12345")["ok"]
    identifier = access.access_set(device.device_id, "ssh", "operator", "old-secret", "old-secret")[
        "id"
    ]
    return access, database, device, identifier


def row(access):
    return access.bootstrap()["records"][0]


def test_monitor_edits_use_the_lanip_rules_and_preserve_observations(workspace):
    database, device, _ = inventory(workspace)
    monitor = api("lanmon")
    before_samples = monitor.monitor_samples(device.device_id)["samples"]
    before = deepcopy(database.resolve(device.device_id).to_dict())
    record = monitor.monitor_device(device.device_id)["device"]
    assert set(record["editable"]) == {"name", "alias", "description", "ip"}
    assert monitor.monitor_update(
        device.device_id,
        record["revision"],
        {"alias": "Renamed", "description": "Stored", "ip": "192.0.2.11"},
    )["ok"]
    after = database.resolve(device.device_id)
    assert (after.alias, after.description, after.ip) == ("Renamed", "Stored", "192.0.2.11")
    assert after.device_id == device.device_id
    assert after.to_dict()["MAC"] == before["MAC"]
    assert monitor.monitor_samples(device.device_id)["samples"] == before_samples
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop = DesktopApi()
    assert desktop.device_record(device.device_id)["editable"]["alias"] == "Renamed"
    assert not monitor.monitor_update(device.device_id, record["revision"], {"alias": "stale"})[
        "ok"
    ]
    record = monitor.monitor_device(device.device_id)["device"]
    desktop_revision = desktop.device_record(device.device_id)["device"]["editRevision"]
    assert desktop.update_device(device.device_id, {"name": "Edited in LANIP"}, desktop_revision)[
        "ok"
    ]
    assert not monitor.monitor_update(device.device_id, record["revision"], {"name": "lost"})["ok"]
    current = monitor.monitor_device(device.device_id)["device"]
    saved = database.path.read_bytes()
    assert not monitor.monitor_update(
        device.device_id, current["revision"], {"alias": "partial", "ip": "not-an-ip"}
    )["ok"]
    assert database.path.read_bytes() == saved


@pytest.mark.parametrize(
    "field", ["id", "mac", "presence", "health", "latency", "groups", "credentials"]
)
def test_monitor_rejects_derived_internal_and_unknown_fields(workspace, field):
    database, device, _ = inventory(workspace)
    monitor = api("lanmon")
    record = monitor.monitor_device(device.device_id)["device"]
    saved = database.path.read_bytes()
    assert not monitor.monitor_update(device.device_id, record["revision"], {field: "tampered"})[
        "ok"
    ]
    assert not monitor.monitor_update(device.device_id, None, {"alias": "unguarded"})["ok"]
    assert database.path.read_bytes() == saved


def test_monitor_groups_keep_protection_and_detect_obsolete_memberships(workspace):
    database, device, groups = inventory(workspace)
    monitor = api("lanmon")
    record = monitor.monitor_device(device.device_id)["device"]
    assert not monitor.monitor_group(device.device_id, record["revision"], "add", "BASIC")["ok"]
    assert not monitor.monitor_group(device.device_id, record["revision"], "create", "INJECTED")[
        "ok"
    ]
    updated = monitor.monitor_group(device.device_id, record["revision"], "add", "LAB")
    assert updated["ok"], updated
    assert "LAB" in updated["device"]["groups"]
    assert not monitor.monitor_update(device.device_id, record["revision"], {"alias": "old"})["ok"]
    assert not monitor.monitor_group(device.device_id, record["revision"], "remove", "LAB")["ok"]
    assert monitor.monitor_group(device.device_id, updated["device"]["revision"], "remove", "LAB")[
        "ok"
    ]
    assert not database.resolve(device.device_id).groups
    assert not next(g for g in groups.load() if g.name == "LAB").members


def test_credential_update_preserves_secret_identity_and_noop_revision(workspace):
    access, database, device, identifier = credential(workspace)
    first = row(access)
    references = dict(database.resolve(device.device_id).credentials)
    assert access.access_update(identifier, first["revision"], {"username": "new-user"})["ok"]
    current = row(access)
    assert current["credentialId"] == identifier
    assert current["username"] == "new-user"
    assert access._service.manager.store.get(identifier)["password"] == "old-secret"
    assert database.resolve(device.device_id).credentials == references
    assert "old-secret" not in json.dumps(access.bootstrap())
    assert b"old-secret" not in access._service.manager.store.path.read_bytes()
    assert access.access_update(identifier, current["revision"], {"username": "new-user"})["ok"]
    assert row(access)["revision"] == current["revision"]
    assert not access.access_update(identifier, first["revision"], {"username": "stale"})["ok"]
    assert access.access_update(
        identifier,
        current["revision"],
        {"username": "new-user", "password": "rotated-secret", "confirmation": "rotated-secret"},
    )["ok"]
    assert access._service.manager.store.get(identifier)["password"] == "rotated-secret"
    assert not access.access_update(identifier, current["revision"], {"username": "stale"})["ok"]
    fresh = api("lanaccess", cipher="portable")
    assert fresh.access_unlock("Vault-test-12345")["ok"]
    assert row(fresh) == row(access)
    assert not fresh.access_update(
        identifier,
        row(fresh)["revision"],
        {"username": "partial", "password": "mismatch", "confirmation": "different"},
    )["ok"]
    assert row(fresh) == row(access)
    access.access_lock()
    assert not access.access_update(identifier, row(fresh)["revision"], {"username": "locked"})[
        "ok"
    ]
    assert access.bootstrap()["records"] == []


@pytest.mark.parametrize("field", ["credentialId", "deviceId", "protocol", "revision", "path"])
def test_credential_edit_cannot_rebind_or_change_internal_fields(workspace, field):
    access, _, _, identifier = credential(workspace)
    previous = row(access)
    saved = access._service.manager.store.path.read_bytes()
    assert not access.access_update(
        identifier, previous["revision"], {"username": "partial", field: "injected"}
    )["ok"]
    assert access._service.manager.store.path.read_bytes() == saved


def test_new_edit_rpcs_reject_other_launchers_and_changed_projects(workspace, tmp_path):
    first, second = projects(workspace, tmp_path)
    active = config.load_config()
    access, _, device, identifier = credential(active)
    monitor = api("lanmon")
    context = monitor.bootstrap()["projectContext"]
    record = monitor.monitor_device(device.device_id)["device"]
    credential_revision = row(access)["revision"]
    wire = api("lanwire")
    assert not wire.monitor_update(device.device_id, record["revision"], {"alias": "wrong"})["ok"]
    assert not wire.access_update(identifier, credential_revision, {"username": "wrong"})["ok"]
    assert monitor.save_project()["ok"]
    old_database = DeviceDatabase(active["database"]).path.read_bytes()
    old_store = access._service.manager.store.path.read_bytes()
    activate_project_workspace(second)
    assert not monitor.project_call(
        context, "monitor_update", [device.device_id, record["revision"], {"alias": "old"}]
    )["ok"]
    assert not monitor.project_call(
        context, "monitor_group", [device.device_id, record["revision"], "add", "LAB"]
    )["ok"]
    assert not access.project_call(
        context, "access_update", [identifier, credential_revision, {"username": "old"}]
    )["ok"]
    assert DeviceDatabase(active["database"]).path.read_bytes() == old_database
    assert access._service.manager.store.path.read_bytes() == old_store
    assert monitor.bootstrap()["project"] == second
    assert first != second


def test_remote_viewer_permissions_and_rpc_allowlist_are_preserved(workspace, tmp_path):
    from lanctl.apps.access.auth import AuthenticationService, AuthorizationService
    from lanctl.apps.access.remote import RemoteGuiApi
    from lanctl.apps.access.store import AccessStore

    store = AccessStore(tmp_path / "users.json")
    viewer = AuthenticationService(store).add_user("viewer", ["viewer"], "viewer-test-password")
    remote = RemoteGuiApi(AuthorizationService(store), api("lanmon"))
    for method in (
        "monitor_update",
        "monitor_group",
        "access_update",
        "project_call",
        "update_device",
    ):
        with pytest.raises(PermissionError):
            remote.call(viewer, method, [])


@pytest.mark.parametrize("kind", ["monitor", "credential"])
def test_two_editors_cannot_overwrite_each_other(workspace, kind):
    if kind == "credential":
        first, database, device, identifier = credential(workspace)
        second = api("lanaccess", cipher="portable")
        assert second.access_unlock("Vault-test-12345")["ok"]
        revision = row(first)["revision"]

        def write(window, value):
            return window.access_update(identifier, revision, {"username": value})
    else:
        database, device, _ = inventory(workspace)
        first, second = api("lanmon"), api("lanmon")
        revision = first.monitor_device(device.device_id)["device"]["revision"]

        def write(window, value):
            return window.monitor_update(device.device_id, revision, {"alias": value})

    barrier = Barrier(2)

    def edit(index):
        barrier.wait(timeout=5)
        return write((first, second)[index], f"Window{index}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(edit, (0, 1)))
    assert sum(result["ok"] for result in outcomes) == 1
    winner = next(index for index, result in enumerate(outcomes) if result["ok"])
    if kind == "credential":
        assert row(first)["username"] == f"Window{winner}"
        assert first._service.manager.store.get(identifier)["password"] == "old-secret"
    else:
        assert database.resolve(device.device_id).alias == f"Window{winner}"


def test_monitor_changes_survive_project_save_and_reopen(workspace, tmp_path):
    first, second = projects(workspace, tmp_path)
    active = config.load_config()
    _, device, _ = inventory(active)
    monitor = api("lanmon")
    record = monitor.monitor_device(device.device_id)["device"]
    assert monitor.monitor_update(
        device.device_id, record["revision"], {"alias": "Persisted", "description": "Saved in VLF"}
    )["ok"]
    record = monitor.monitor_device(device.device_id)["device"]
    assert monitor.monitor_group(device.device_id, record["revision"], "add", "LAB")["ok"]
    assert monitor.save_project()["ok"]
    activate_project_workspace(second)
    activate_project_workspace(first, refresh=True)
    restored = api("lanmon").monitor_device(device.device_id)["device"]
    assert restored["editable"]["alias"] == "Persisted"
    assert restored["editable"]["description"] == "Saved in VLF"
    assert restored["groups"] == ["LAB"]
