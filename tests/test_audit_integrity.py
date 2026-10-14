import ipaddress
import json
import threading
import uuid
import zipfile
from unittest.mock import Mock

import pytest

from lanctl.apps.ip.domain.models import Device
from lanctl.apps.ip.infrastructure.services.lan_scanner import LanScanner
from lanctl.core import config
from lanctl.core.database import DeviceDatabase
from lanctl.core.file_transaction import InterProcessLock
from lanctl.core.group_database import GroupDatabase
from lanctl.core.persistence import create_backup
from lanctl.core.projects import vlf
from lanctl.core.projects.workspace import prepare_project_workspace


@pytest.fixture
def inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(DeviceDatabase, "_audit_changes", lambda *_: None)
    database = DeviceDatabase(str(tmp_path / "devices.json"))
    return database, GroupDatabase(str(tmp_path / "groups.json"), database)


def test_deleting_provisional_device_preserves_other_identities(inventory):
    database, groups = inventory
    devices = [
        Device(ip="192.0.2.10"),
        Device(ip="192.0.2.11"),
        Device(ip="192.0.2.1", default_alias="GATEWAY"),
    ]
    database.save_devices(devices)
    groups.delete_device(devices[0].device_id)
    assert {x.device_id for x in database.load()} == {x.device_id for x in devices[1:]}


def test_ensure_basic_does_not_replace_concurrent_edit(inventory):
    database, groups = inventory
    database.save_devices([Device(ip="192.0.2.10", mac="00:11:22:33:44:55", alias="before")])
    stale = database.load()
    database.set_alias("192.0.2.10", "concurrent")
    groups.ensure_basic(stale)
    assert database.load()[0].alias == "concurrent"


def test_discovered_mac_promotes_provisional_identity(inventory):
    database, _ = inventory
    provisional = Device(ip="192.0.2.10", alias="keep", credentials={"ssh": "credential-id"})
    merged = database.preview(
        [{"IP": provisional.ip, "MAC": "00:11:22:33:44:55"}], _devices=[provisional]
    )
    assert len(merged) == 1
    assert merged[0].device_id == provisional.device_id
    assert merged[0].credentials == provisional.credentials
    assert merged[0].alias == "keep"
    distinct = database.preview(
        [{"IP": provisional.ip, "MAC": "00:11:22:33:44:66"}], _devices=merged
    )
    assert len(distinct) == 2


@pytest.mark.parametrize("version", [999, -1, "2", None, True])
def test_invalid_or_future_config_is_rejected_without_rewriting(tmp_path, monkeypatch, version):
    document = {"schemaVersion": version, "futureOnly": "preserve"}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    original = path.read_bytes()
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    monkeypatch.delenv("LANCTL_CANONICAL_HELP", raising=False)
    with pytest.raises(ValueError, match="versión"):
        config._load_config()
    with pytest.raises(ValueError, match="versión"):
        config.canonical_config(document)
    assert path.read_bytes() == original


def test_lock_deadline_applies_between_threads_and_can_be_retried(tmp_path):
    path = tmp_path / "data.lock"
    ready, release = threading.Event(), threading.Event()

    def holder():
        with InterProcessLock(path):
            ready.set()
            release.wait(3)

    thread = threading.Thread(target=holder)
    thread.start()
    assert ready.wait(2)
    lock = InterProcessLock(path, timeout=0.03)
    try:
        with pytest.raises(TimeoutError):
            lock.acquire()
    finally:
        release.set()
        thread.join(2)
    with lock, InterProcessLock(path, timeout=0):
        pass


def test_backups_with_same_timestamp_remain_distinct(tmp_path, monkeypatch):
    clock = Mock()
    clock.now.return_value.strftime.return_value = "20261014T100000Z"
    monkeypatch.setattr("lanctl.core.persistence.datetime", clock)
    source = tmp_path / "sample.json"
    source.write_text("first", encoding="utf-8")
    first = create_backup(source)
    source.write_text("second", encoding="utf-8")
    second = create_backup(source)
    assert first != second
    assert first.read_text() == "first"
    assert second.read_text() == "second"


def test_host_limit_rejects_large_network_before_enumeration(monkeypatch):
    def forbidden(_network):
        raise AssertionError("network was enumerated")

    monkeypatch.setattr(ipaddress.IPv4Network, "hosts", forbidden)
    scanner = LanScanner(ipaddress.ip_network("10.0.0.0/8"), 2, 0.1, 256)
    with pytest.raises(ValueError, match="max-hosts"):
        scanner.scan()


@pytest.mark.parametrize("cidr, expected", [("192.0.2.0/31", 2), ("192.0.2.1/32", 1)])
def test_host_limit_includes_point_to_point_and_single_host(cidr, expected):
    scanner = LanScanner(ipaddress.ip_network(cidr), 1, 0.1, expected)
    assert len(scanner._ordered_hosts()) == expected


@pytest.mark.parametrize("identity", ["../escape", "C:/outside", "Z:relative", "", "not-a-uuid"])
def test_vlf_rejects_path_identifiers(identity):
    with pytest.raises(ValueError, match="UUID"):
        vlf.validate_project_id(identity)


def test_validly_checksummed_vlf_cannot_select_workspace_path(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lanctl.core.plugins.get_plugin_manager",
        lambda: Mock(project_registry=lambda: {"schemaVersion": 1, "plugins": []}),
    )
    settings = {
        "database": str(tmp_path / "devices.json"),
        "groups": str(tmp_path / "groups.json"),
        "credentials": str(tmp_path / "credentials"),
        "range": "192.0.2.0/24",
    }
    path = tmp_path / "hostile.vlf"
    vlf.create_project(path, config=settings, initialize_reserved=False)
    with zipfile.ZipFile(path) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    info = json.loads(entries["project.info"])
    info["id"] = str(tmp_path / "outside")
    entries["project.info"] = json.dumps(info).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in entries.items():
            if name != "meta/checksum":
                archive.writestr(name, value)
    with zipfile.ZipFile(path) as archive:
        checksum = vlf._hash_archive(archive, {"meta/checksum"})
    manifest = json.loads(entries["meta/checksum"])
    manifest["hash"] = checksum
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("meta/checksum", json.dumps(manifest))
    with pytest.raises(ValueError, match="UUID"):
        prepare_project_workspace(path, root=tmp_path / "workspaces")
    assert not (tmp_path / "outside").exists()
    assert vlf.validate_project_id(str(uuid.uuid4()))


def test_scanner_submission_window_is_bounded():
    from concurrent.futures import Future

    submitted = []

    class Executor:
        def submit(self, function, value):
            submitted.append(value)
            future = Future()
            future.set_result(function(value))
            return future

    scanner = LanScanner(ipaddress.ip_network("192.0.2.0/24"), 2, 0.1, 254)
    stream = scanner._bounded_futures(Executor(), ((i, str, (i,)) for i in range(100)), {})
    next(stream)
    assert len(submitted) == 4
    assert len(list(stream)) == 99
