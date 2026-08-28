from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lanctl.core.file_transaction import atomic_write_json, locked_file
from lanctl.core.paths import application_path
from lanctl.core.plugins.package import verify_package

TRUSTED_PUBLISHERS = application_path("data/lc/trusted-publishers.json")


class TrustedPublisherStore:
    """Almacén explícito de huellas Ed25519 autorizadas para paquetes LCP."""

    def __init__(self, path: str | Path = TRUSTED_PUBLISHERS) -> None:
        self.path = Path(path)

    def list(self) -> list[dict]:
        return sorted(self._read().values(), key=lambda item: item["name"].casefold())

    def trust_package(self, package: str | Path, name: str = "") -> dict:
        result = verify_package(package)
        signature = str(result["signature"])
        if not signature.startswith("VALID_ED25519:"):
            raise ValueError("sólo se puede confiar en un editor con un LCP firmado válido")
        fingerprint = signature.split(":", 1)[1]
        manifest = result["manifest"]
        publishers = self._read()
        entry = {
            "fingerprint": fingerprint,
            "name": name.strip() or manifest.author.strip() or manifest.name,
            "sourcePlugin": manifest.plugin_id,
            "trustedAt": datetime.now(timezone.utc).isoformat(),
        }
        publishers[fingerprint] = entry
        self._write(publishers)
        return entry

    def revoke(self, fingerprint: str) -> bool:
        normalized = fingerprint.strip().casefold()
        publishers = self._read()
        removed = publishers.pop(normalized, None) is not None
        if removed:
            self._write(publishers)
        return removed

    def is_trusted(self, signature: str) -> bool:
        prefix = "VALID_ED25519:"
        return signature.startswith(prefix) and signature[len(prefix) :].casefold() in self._read()

    def _read(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
            values = document.get("publishers", {})
            if not isinstance(values, dict):
                raise ValueError("publishers debe ser un objeto")
            return {str(key).casefold(): dict(value) for key, value in values.items()}
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise ValueError(f"almacén de editores confiables no válido: {self.path}") from error

    def _write(self, publishers: dict[str, dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with locked_file(self.path):
            atomic_write_json(self.path, {"schemaVersion": 1, "publishers": publishers})
