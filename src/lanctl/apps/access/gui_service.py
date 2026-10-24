"""Credential GUI adapter; snapshots contain metadata, never passwords."""

import base64
import os

from lanctl.apps.access.credential_service import CredentialService
from lanctl.core.file_transaction import locked_files
from lanctl.core.vault_crypto import MAGIC


class AccessGuiService:
    def __init__(self, database, store, cipher="auto"):
        self.manager = CredentialService(database, store)
        self.manager.store.cipher = cipher
        self._unlocked = False

    def _portable(self):
        store = self.manager.store
        if store.path.exists():
            with store.path.open("rb") as stream:
                return base64.b64decode(stream.read(64), validate=True).startswith(MAGIC)
        return store.cipher == "portable" or (store.cipher == "auto" and os.name != "nt")

    def snapshot(self):
        with locked_files((self.manager.store.path, self.manager.database.path)):
            portable = self._portable()
            locked = portable and not self._unlocked
            rows = [] if locked else self.manager.list()
            if rows:
                revision = self.manager.revision()
                rows = [{**row, "revision": revision} for row in rows]
            return {
                "locked": locked,
                "portable": portable,
                "newVault": not self.manager.store.path.exists(),
                "records": rows,
                "devices": [
                    {
                        "id": d.device_id,
                        "name": d.alias or d.name or d.ip,
                        "protocols": list(d.protocols),
                    }
                    for d in self.manager.database.load()
                ],
                "storage": str(self.manager.store.path),
            }

    def unlock(self, password, confirmation=""):
        if not self.manager.store.path.exists() and (
            len(password) < 12 or password != confirmation
        ):
            raise ValueError("Usa una contraseña de almacén de al menos 12 caracteres y repítela")
        self.manager.store._password = password
        self.manager.store.cipher = "portable"
        try:
            self.manager.store.metadata()
        except Exception:
            self.manager.store._password = None
            raise
        self._unlocked = True

    def lock(self):
        self.manager.store._password = None
        self._unlocked = False

    def set(self, selector, protocol, username, password, confirmation):
        if self._portable() and not self._unlocked:
            raise ValueError("Desbloquea el almacén antes de editar")
        if password != confirmation:
            raise ValueError("Las contraseñas no coinciden")
        return {"id": self.manager.set_secret(selector, protocol, username, password)}

    def update(self, identifier, expected, values):
        with locked_files((self.manager.store.path,)):
            return self._update(identifier, expected, values)

    def _update(self, identifier, expected, values):
        if self._portable() and not self._unlocked:
            raise ValueError("Desbloquea el almacén antes de editar")
        if not isinstance(values, dict) or set(values) - {"username", "password", "confirmation"}:
            raise ValueError("Campos de credencial no editables.")
        if "password" in values or "confirmation" in values:
            password = values.get("password")
            if (
                not isinstance(password, str)
                or not password
                or password != values.get("confirmation")
            ):
                raise ValueError("Indica y repite la nueva contraseña.")
        else:
            password = None
        return {
            "id": self.manager.update_secret(identifier, expected, values.get("username"), password)
        }

    def delete(self, identifier):
        if self._portable() and not self._unlocked:
            raise ValueError("Desbloquea el almacén antes de editar")
        if not self.manager.delete(identifier):
            raise ValueError("La credencial ya no existe")

    def open(self, identifier):
        import argparse
        import subprocess
        import sys

        from lanctl.apps.ip.domain.discovery import require_real_target
        from lanctl.apps.ip.interfaces.cli.commands.open import OPEN_PROTOCOLS, run_open
        from lanctl.apps.suite.processes import launcher_command, process_options

        row = next((r for r in self.snapshot()["records"] if r["credentialId"] == identifier), None)
        if row is None:
            raise ValueError("La credencial no está disponible; desbloquea o actualiza el almacén")
        device = self.manager.database.resolve(row["deviceId"])
        require_real_target(device)
        protocol = row["protocol"]
        if protocol not in OPEN_PROTOCOLS:
            raise ValueError("Este protocolo no tiene cliente de conexión disponible")
        if protocol in {"http", "https", "ftp", "smb", "rdp", "rtsp", "radmin"}:
            run_open(
                argparse.Namespace(
                    selector=device.device_id,
                    protocol=protocol,
                    port=None,
                    path="",
                    dry_run=False,
                    database=str(self.manager.database.path),
                    store=str(self.manager.store.path),
                )
            )
        else:
            # Interactive authentication stays in a system terminal, never process arguments.
            command = launcher_command(
                "lanip",
                "open",
                device.device_id,
                "--protocol",
                protocol,
                "--database",
                str(self.manager.database.path),
                "--store",
                str(self.manager.store.path),
            )
            options = process_options(context_launcher="lanip")
            if sys.platform == "win32":
                subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE, **options)
            else:
                import shutil

                terminal = shutil.which("x-terminal-emulator") or shutil.which("xterm")
                if not terminal:
                    raise RuntimeError("No hay terminal disponible para la conexión interactiva")
                subprocess.Popen([terminal, "-e", *command], **options)
        return {"message": "Conexión abierta en su cliente"}
