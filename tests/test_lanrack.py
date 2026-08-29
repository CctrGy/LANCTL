import json
from unittest.mock import patch

from lanctl.apps.rack.cli import main
from lanctl.apps.rack.service import RackService
from lanctl.apps.wire.idf.database import IDFDatabaseManager


def test_rack_service_only_returns_racks_and_their_occupants(tmp_path):
    path = tmp_path / "idf.db"
    database = IDFDatabaseManager(path)
    database.add("RK-01", {"type": "rack", "name": "Principal", "size_units": 24})
    database.add(
        "SW-01",
        {"type": "device.switch", "name": "Core", "location": {"rack": "RK-01", "unit": 20}},
    )
    database.add("CB-01", {"type": "wire", "name": "Cable"})
    rack = RackService(str(path)).get("rk-01")
    assert rack["units"] == 24
    assert [item["id"] for item in rack["occupants"]] == ["SW-01"]


def test_lanrack_cli_outputs_structured_rack(tmp_path, capsys):
    path = tmp_path / "idf.db"
    IDFDatabaseManager(path).add("RK-01", {"type": "rack", "units": 12})
    assert main(["--database", str(path), "show", "RK-01"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "RK-01"


def test_lanrack_tui_can_exit(tmp_path):
    with patch("builtins.input", return_value="q"):
        assert main(["--database", str(tmp_path / "idf.db"), "--tui"]) == 0
