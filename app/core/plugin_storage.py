from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path

from app.core.file_transaction import update_json

_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9.-]+$")


class PluginStorage:
    """JSON transportable, transaccional y separado del inventario Device."""

    def __init__(self, root: str | Path, plugin_id: str):
        if not _PLUGIN_ID.fullmatch(plugin_id):
            raise ValueError("id de plugin no válido")
        self.path = Path(root) / f"{plugin_id}.json"

    def load(self) -> dict:
        if not self.path.exists():
            return {"schemaVersion": 1, "observations": {}}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("observations", {}), dict):
            raise ValueError("almacén de plugin no válido")
        value.setdefault("schemaVersion", 1)
        value.setdefault("observations", {})
        return value

    def put_observation(self, device_id: str, observation: dict) -> None:
        self.put_observations({device_id: observation})

    def put_observations(self, observations: Mapping[str, dict]) -> None:
        """Guarda un lote con una sola lectura y una sola escritura del JSON."""

        batch: dict[str, dict] = {}
        for device_id, observation in observations.items():
            if not device_id or not isinstance(observation, dict):
                raise ValueError("observación no válida")
            batch[str(device_id)] = dict(observation)
        if not batch:
            return

        def replace(value):
            if not isinstance(value, dict) or not isinstance(value.get("observations", {}), dict):
                raise ValueError("almacén de plugin no válido")
            value.setdefault("schemaVersion", 1)
            value.setdefault("observations", {}).update(batch)

        update_json(
            self.path,
            lambda: {"schemaVersion": 1, "observations": {}},
            replace,
        )
