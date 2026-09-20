from __future__ import annotations

import json
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from lanctl.apps.ip.domain.models import Device, Group
from lanctl.core.database import DeviceDatabase
from lanctl.core.file_transaction import atomic_write_json
from lanctl.core.group_database import GroupDatabase, _encoded_snapshot, _journal_path


def stores(tmp_path: Path) -> tuple[DeviceDatabase, GroupDatabase]:
    devices_path = tmp_path / "devices.json"
    groups_path = tmp_path / "groups.json"
    devices_path.write_text(
        json.dumps(
            [
                Device(
                    ip="192.168.1.10",
                    mac="10:20:30:40:50:60",
                    alias="OLD",
                    name="Old name",
                ).to_dict()
            ]
        ),
        encoding="utf-8",
    )
    groups_path.write_text(json.dumps([Group("LAB", editable=True).to_dict()]), encoding="utf-8")
    database = DeviceDatabase(str(devices_path))
    return database, GroupDatabase(str(groups_path), database)


def test_chained_element_validation_is_all_or_nothing(tmp_path: Path) -> None:
    database, groups = stores(tmp_path)

    with pytest.raises(ValueError, match="42 caracteres"):
        groups.edit_device_fields(
            "OLD", [("name", "Nuevo"), ("description", "x" * 43), ("group", "LAB")]
        )

    device = database.resolve("OLD")
    assert device.name == "Old name"
    assert device.groups == []
    assert groups.load()[0].members == []


def test_manual_element_can_be_created_with_an_ip(tmp_path: Path) -> None:
    database, _groups = stores(tmp_path)

    device = database.add_device(
        "AA-BB-CC-DD-EE-FF",
        ip="192.168.1.44",
        alias="SENSOR",
    )

    assert device.ip == "192.168.1.44"
    assert database.resolve("SENSOR").mac == "AA:BB:CC:DD:EE:FF"


def test_element_ip_can_be_corrected_atomically(tmp_path: Path) -> None:
    database, groups = stores(tmp_path)

    updated = groups.edit_device_fields("OLD", [("ip", "192.168.1.99")])

    assert updated.ip == "192.168.1.99"
    assert database.resolve("OLD").ip == "192.168.1.99"


def test_element_ip_rejects_invalid_and_duplicate_addresses(tmp_path: Path) -> None:
    database, groups = stores(tmp_path)
    database.add_device("AA:BB:CC:DD:EE:FF", ip="192.168.1.44")

    with pytest.raises(ValueError, match="IPv4 no válida"):
        groups.edit_device_fields("OLD", [("ip", "192.168.1.999")])
    with pytest.raises(ValueError, match="ya pertenece"):
        groups.edit_device_fields("OLD", [("ip", "192.168.1.44")])

    assert database.resolve("OLD").ip == "192.168.1.10"


def test_pair_commit_restores_both_files_when_second_write_fails(tmp_path: Path) -> None:
    database, groups = stores(tmp_path)
    before_devices = database.path.read_bytes()
    before_groups = groups.path.read_bytes()

    with (
        patch.object(groups, "_write", side_effect=OSError("fallo inyectado")),
        pytest.raises(OSError, match="fallo inyectado"),
    ):
        groups.edit_device_fields("OLD", [("name", "Nuevo"), ("group", "LAB")])

    assert database.path.read_bytes() == before_devices
    assert groups.path.read_bytes() == before_groups


def test_concurrent_chained_edits_do_not_lose_fields(tmp_path: Path) -> None:
    database, groups = stores(tmp_path)
    barrier = threading.Barrier(3)
    failures: list[BaseException] = []

    def edit(field: str, value: str) -> None:
        try:
            barrier.wait()
            groups.edit_device_fields("OLD", [(field, value)])
        except BaseException as error:  # pragma: no cover - asserted below
            failures.append(error)

    first = threading.Thread(target=edit, args=("name", "Nuevo"))
    second = threading.Thread(target=edit, args=("description", "Descripción"))
    first.start()
    second.start()
    barrier.wait()
    first.join()
    second.join()

    assert failures == []
    device = database.resolve("OLD")
    assert device.name == "Nuevo"
    assert device.description == "Descripción"


def test_pending_journal_is_recovered_before_database_is_read(tmp_path: Path) -> None:
    database, groups = stores(tmp_path)
    original_devices = database.path.read_bytes()
    original_groups = groups.path.read_bytes()
    journal = _journal_path(database.path)
    atomic_write_json(
        journal,
        {
            "schemaVersion": 1,
            "devicesPath": str(database.path.resolve()),
            "groupsPath": str(groups.path.resolve()),
            "before": {
                "devices": _encoded_snapshot(original_devices),
                "groups": _encoded_snapshot(original_groups),
            },
        },
    )
    # Simula la caída después de escribir devices pero antes de groups.
    database.path.write_text("[]", encoding="utf-8")

    recovered = DeviceDatabase(str(database.path)).load()

    assert recovered[0].alias == "OLD"
    assert database.path.read_bytes() == original_devices
    assert groups.path.read_bytes() == original_groups
    assert not journal.exists()
