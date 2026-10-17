"""Bounded, principal-scoped GUI activity transport, independent of project files."""

from __future__ import annotations

import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path

from lanctl.core.coordination import Coordinator, principal_id
from lanctl.core.paths import data_root

RETENTION = 10000


class ActivityStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else data_root() / "runtime" / "activity.db"
        self.owner = principal_id()

    @contextmanager
    def _connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.row_factory = sqlite3.Row
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("versión del transporte de actividad no compatible")
            db.execute(
                "CREATE TABLE IF NOT EXISTS activity (seq INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL, created REAL NOT NULL, message TEXT NOT NULL, launcher TEXT NOT NULL, session TEXT NOT NULL, project TEXT, level INTEGER NOT NULL, task TEXT)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS activity_owner_seq ON activity(owner,seq)")
            db.execute("PRAGMA user_version=1")
            yield db

    def append(self, message, *, launcher, session, project=None, level=20, task=None) -> dict:
        if not isinstance(message, str) or not message.strip() or len(message) > 4096:
            raise ValueError("mensaje de actividad vacío o mayor de 4096 caracteres")
        if type(level) is not int or not 1 <= level <= 59:
            raise ValueError("nivel de actividad fuera de 1-59")
        if task is not None and (not isinstance(task, str) or len(task) > 128):
            raise ValueError("tarea de actividad no válida")
        if not isinstance(session, str) or not isinstance(launcher, str):
            raise ValueError("sesión y launcher de actividad requeridos")
        # The adapter supplies its actual session, not arbitrary JS origin fields.
        live = next((s for s in Coordinator().sessions() if s["id"] == session), None)
        if live is None or live["launcher"] != launcher or live["project"] != project:
            raise ValueError("sesión, launcher o proyecto de actividad no vigentes")
        clean = " ".join("".join(c for c in message if c.isprintable() or c in "\n\t").splitlines())
        created = time.time()
        with self._connection() as db:
            cursor = db.execute(
                "INSERT INTO activity(owner,created,message,launcher,session,project,level,task) VALUES (?,?,?,?,?,?,?,?)",
                (self.owner, created, clean, launcher, session, project, level, task),
            )
            seq = cursor.lastrowid
            db.execute(
                "DELETE FROM activity WHERE owner=? AND seq NOT IN (SELECT seq FROM activity WHERE owner=? ORDER BY seq DESC LIMIT ?)",
                (self.owner, self.owner, RETENTION),
            )
        return {
            "schemaVersion": 1,
            "seq": seq,
            "created": created,
            "message": clean,
            "launcher": launcher,
            "session": session,
            "project": project,
            "level": level,
            "task": task,
        }

    def query(self, *, after=0, limit=100, session=None, project=None, latest=False) -> list[dict]:
        if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("cursor o límite de actividad no válido")
        if any(value is not None and not isinstance(value, str) for value in (session, project)):
            raise ValueError("filtro de actividad no válido")
        if type(latest) is not bool:
            raise ValueError("latest debe ser booleano")
        if not self.path.exists():
            return []
        with self._connection() as db:
            rows = db.execute(
                "SELECT seq,created,message,launcher,session,project,level,task FROM activity WHERE owner=? AND seq>? AND (? IS NULL OR session=?) AND (? IS NULL OR COALESCE(project,'')=?) ORDER BY CASE WHEN ? THEN -seq ELSE seq END LIMIT ?",
                (self.owner, after, session, session, project, project, latest, limit),
            )
            result = [{"schemaVersion": 1, **dict(row)} for row in rows]
            return list(reversed(result)) if latest else result
