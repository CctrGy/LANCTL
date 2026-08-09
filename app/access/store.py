from __future__ import annotations

import json
from pathlib import Path

from app.core.file_transaction import atomic_write_json, locked_file

from .models import AccessSession, RemoteUser


class AccessStore:
    def __init__(self, path):
        self.path = Path(path)

    @staticmethod
    def _empty():
        return {"schemaVersion": 1, "users": [], "sessions": [], "pairings": [], "roles": {}}

    def _load_unlocked(self):
        if not self.path.exists():
            return self._empty()
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if value.get("schemaVersion") != 1:
            raise ValueError("version de almacen de acceso no compatible")
        return value

    def load(self):
        # El escritor usa `os.replace`: una lectura observa la versión anterior
        # o la nueva sin bloquear autenticaciones concurrentes entre sí.
        return self._load_unlocked()

    def _save_unlocked(self, value):
        atomic_write_json(self.path, value)

    @staticmethod
    def _upsert(items, key, replacement):
        """Reemplaza conservando orden o añade al final si aún no existe."""
        identity = replacement[key]
        for index, item in enumerate(items):
            if item[key] == identity:
                items[index] = replacement
                return
        items.append(replacement)

    def save(self, value):
        with locked_file(self.path):
            self._save_unlocked(value)

    def update(self, mutator):
        """Agrupa lectura, modificacion y escritura en una transaccion de hilos."""
        with locked_file(self.path):
            value = self._load_unlocked()
            result = mutator(value)
            self._save_unlocked(value)
            return result

    def users(self):
        return [RemoteUser(**x) for x in self.load()["users"]]

    def save_user(self, user):
        def operation(value):
            self._upsert(value["users"], "userId", vars(user))

        self.update(operation)

    def create_user(self, user):
        def operation(value):
            if any(
                item["username"].casefold() == user.username.casefold() for item in value["users"]
            ):
                raise ValueError("usuario remoto no valido o duplicado")
            value["users"].append(vars(user))

        self.update(operation)

    def update_user(self, user_id, mutator):
        def operation(value):
            index = next(
                (i for i, item in enumerate(value["users"]) if item["userId"] == user_id), None
            )
            if index is None:
                raise ValueError("usuario remoto no encontrado")
            user = mutator(RemoteUser(**value["users"][index]))
            value["users"][index] = vars(user)
            return user

        return self.update(operation)

    def delete_user(self, user_id):
        def operation(value):
            before = len(value["users"])
            value["users"] = [x for x in value["users"] if x["userId"] != user_id]
            if len(value["users"]) == before:
                raise ValueError("usuario remoto no encontrado")
            value["sessions"] = [x for x in value["sessions"] if x["userId"] != user_id]

        self.update(operation)

    def sessions(self):
        return [AccessSession(**x) for x in self.load()["sessions"]]

    def save_session(self, session):
        def operation(value):
            self._upsert(value["sessions"], "sessionId", vars(session))

        self.update(operation)
