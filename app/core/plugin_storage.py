from __future__ import annotations

import json
import re
from pathlib import Path
from threading import RLock


_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9.-]+$")


class PluginStorage:
    """JSON transportable, transaccional y separado del inventario Device."""

    def __init__(self, root: str | Path, plugin_id: str):
        if not _PLUGIN_ID.fullmatch(plugin_id):
            raise ValueError("id de plugin no válido")
        self.path = Path(root) / f"{plugin_id}.json"
        self._lock = RLock()

    def load(self) -> dict:
        with self._lock:
            if not self.path.exists():
                return {"schemaVersion": 1, "observations": {}}
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("observations", {}), dict):
                raise ValueError("almacén de plugin no válido")
            value.setdefault("schemaVersion", 1); value.setdefault("observations", {})
            return value

    def put_observation(self, device_id: str, observation: dict) -> None:
        if not device_id or not isinstance(observation, dict):
            raise ValueError("observación no válida")
        with self._lock:
            value = self.load(); value["observations"][device_id] = dict(observation)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            temporary.replace(self.path)
