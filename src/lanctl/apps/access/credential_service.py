"""Shared metadata and encrypted credential transactions for CLI, TUI and GUI."""

from lanctl.apps.ip.domain.models import normalize_protocol
from lanctl.core.credentials import CredentialStore
from lanctl.core.database import DeviceDatabase
from lanctl.core.file_transaction import locked_files


class CredentialService:
    def __init__(self, database_path: str, store_path: str) -> None:
        self.database = DeviceDatabase(database_path)
        self.store = CredentialStore(store_path)

    def list(self) -> list[dict[str, str]]:
        devices = {device.device_id: device for device in self.database.load()}
        rows = self.store.metadata()
        for row in rows:
            device = devices.get(row["deviceId"])
            row["element"] = (
                device.alias or device.name or device.ip or device.mac
                if device
                else row["deviceId"]
            )
        return rows

    def set_secret(self, selector: str, protocol: str, username: str, password: str) -> str:
        """Shared credential transaction; interactive callers obtain the secret separately."""
        device = self.database.resolve(selector)
        normalized = normalize_protocol(protocol)
        if not password or not username.strip():
            raise ValueError("usuario y contraseña son obligatorios")
        with locked_files([self.store.path, self.database.path]):
            previous = self.store._load()
            identifier = self.store.set(device.device_id, normalized, username, password)
            try:
                self.database.bind_credential(selector, normalized, identifier)
            except (OSError, ValueError):
                self.store._save(previous)
                raise
        return identifier

    def delete(self, identifier: str) -> bool:
        metadata = next(
            (row for row in self.store.metadata() if row["credentialId"] == identifier), None
        )
        if metadata is None:
            return False
        for device in self.database.load():
            for protocol, reference in tuple(device.credentials.items()):
                if reference == identifier:
                    self.database.unbind_credential(device.device_id, protocol)
        return self.store.delete(identifier)
