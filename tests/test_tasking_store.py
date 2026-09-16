import json
import tempfile
from pathlib import Path

from lanctl.core.tasking import JsonStore


def test_wol_store_upgrades_legacy_shape_when_saved() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "wol.json"
        path.write_text(json.dumps({"sequences": {"boot": []}, "runs": {}}), encoding="utf-8")
        store = JsonStore(path)
        value = store.load()
        assert value["schemaVersion"] == 1
        assert value["documentType"] == "lanctl.wol-sequences"
        store.save(value)
        stored = json.loads(path.read_text(encoding="utf-8"))
        assert stored["sequences"] == {"boot": []}
        assert stored["documentType"] == "lanctl.wol-sequences"
