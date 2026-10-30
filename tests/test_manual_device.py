"""Manual LANIP creation preserves identity and rejects unsafe collisions."""

from datetime import datetime, timedelta

import pytest
from test_desktop_gui import api
from test_launcher_gui import workspace as workspace

from lanctl.core.database import DeviceDatabase


def test_manual_optional_mac_and_scan_promotion(workspace):
    database = DeviceDatabase(workspace["database"])
    created = database.add_manual_device(ip="192.0.2.10", name="Manual")
    assert not created.mac
    database.upsert([{"IP": "192.0.2.10", "MAC": "02:00:00:00:00:10"}])
    rows = database.load()
    assert len(rows) == 1
    assert rows[0].device_id == created.device_id
    assert rows[0].name == "Manual"
    assert rows[0].mac == "02:00:00:00:00:10"


def test_manual_ip_collision_depends_on_activity_and_legacy_stays_strict(workspace):
    database = DeviceDatabase(workspace["database"])
    first = database.add_manual_device(ip="192.0.2.10", name="First")
    rows = database.load()
    rows[0].last_seen = datetime.now().astimezone().isoformat()
    database.save_devices(rows)
    with pytest.raises(ValueError, match="IP"):
        database.add_manual_device(ip=first.ip, name="Second")
    rows[0].last_seen = (datetime.now().astimezone() - timedelta(hours=1)).isoformat()
    database.save_devices(rows)
    second = database.add_manual_device(ip=first.ip, name="Second")
    assert second.device_id != first.device_id
    with pytest.raises(ValueError, match="IP"):
        database.add_device("02:00:00:00:00:20", ip=first.ip)
    database.upsert([{"IP": first.ip, "MAC": "02:00:00:00:00:30"}])
    rows = database.load()
    # Ambiguous address cannot select one of the manual identities to overwrite.
    assert len(rows) == 3
    assert all(not row.mac for row in rows if row.device_id in {first.device_id, second.device_id})


@pytest.mark.parametrize(
    "fields",
    [
        {"mac": "invalid"},
        {"ip": "999.1.1.1"},
        {"idf": "invalid"},
    ],
)
def test_manual_invalid_fields_leave_database_untouched(workspace, fields):
    database = DeviceDatabase(workspace["database"])
    with pytest.raises(ValueError):
        database.add_manual_device(**fields)
    assert database.load() == []


def test_manual_uniqueness_and_blank_ips(workspace):
    database = DeviceDatabase(workspace["database"])
    first = database.add_manual_device(mac="02:00:00:00:00:10", alias="one", idf="AB-12")
    database.add_manual_device(name="without address")
    with pytest.raises(ValueError):
        database.add_manual_device(mac=first.mac)
    with pytest.raises(ValueError):
        database.add_manual_device(alias="ONE")
    with pytest.raises(ValueError, match="IDF"):
        database.add_manual_device(idf="ab-12")


def test_desktop_create_through_project_bridge_without_project(workspace):
    window = api()
    snapshot = window.bootstrap()
    assert snapshot["ok"] and not snapshot["projectContext"][0]
    result = window.project_call(
        snapshot["projectContext"], "create_device", [{"name": "Manual", "ip": "192.0.2.10"}]
    )
    assert result["ok"], result
    assert any(row["id"] == result["createdId"] for row in result["devices"])
    stale = list(snapshot["projectContext"])
    stale[0] = "different.vlf"
    rejected = window.project_call(stale, "create_device", [{"name": "Wrong project"}])
    assert not rejected["ok"]
    assert len(DeviceDatabase(workspace["database"]).load()) == 1


def test_old_english_catalog_falls_back_to_new_builtin_labels(tmp_path):
    import json

    from lanctl.shared.i18n import LanguageManager

    (tmp_path / "english.lang").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "meta": {"code": "en", "name": "English"},
                "strings": {"LANCTL.COMMON.STATUS.OK": "Custom OK"},
            }
        )
    )
    manager = LanguageManager(tmp_path)
    manager.initialize("en")
    assert manager.translate("LANCTL.INVENTORY.MANUAL.ADD") == "Add"
    assert manager.translate("LANCTL.COMMON.STATUS.OK") == "Custom OK"
