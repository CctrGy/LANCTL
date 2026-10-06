"""Local, transactional coordination shared by independent launcher processes.

SQLite is the coordinator (not a TCP server). Existing services keep running
independently of windows. Only metadata is transported: never argv or secrets.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import uuid4

from lanctl.core.paths import data_root

SCHEMA_VERSION = 1
SESSION_TTL = 15
EVENT_LIMIT = 10000
EVENT_ID = re.compile(r"^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){3}$")


def coordinator_path():
    return data_root() / "runtime" / "coordinator.db"


def principal_id():
    """Use the OS token, never spoofable USER/USERNAME environment variables."""
    if os.name != "nt":
        return f"uid:{os.geteuid()}"
    import ctypes
    from ctypes import wintypes

    size = wintypes.ULONG(1024)
    buffer = ctypes.create_unicode_buffer(size.value)
    if not ctypes.windll.secur32.GetUserNameExW(2, buffer, ctypes.byref(size)):
        raise OSError("no se pudo determinar la identidad de la sesión del sistema")
    return buffer.value.casefold()


class Coordinator:
    def __init__(self, path=None, *, administrative=False):
        if administrative:
            from lanctl.core.local_permissions import require_admin

            require_admin()
        self.path = Path(path) if path is not None else coordinator_path()
        self.owner = principal_id()
        self.administrative = administrative

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.row_factory = sqlite3.Row
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise ValueError(f"versión del coordinador no compatible: {version}")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, pid INTEGER NOT NULL,
                    launcher TEXT NOT NULL, mode TEXT NOT NULL, project TEXT,
                    heartbeat REAL NOT NULL, started REAL NOT NULL, parent TEXT,
                    controls INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL,
                    session TEXT NOT NULL, event TEXT NOT NULL, project TEXT,
                    correlation TEXT NOT NULL, created REAL NOT NULL, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, session TEXT NOT NULL, owner TEXT NOT NULL,
                    origin TEXT NOT NULL, state TEXT NOT NULL, started REAL NOT NULL,
                    finished REAL);
                CREATE TABLE IF NOT EXISTS commands (
                    id TEXT PRIMARY KEY, target TEXT NOT NULL, owner TEXT NOT NULL,
                    action TEXT NOT NULL, value TEXT, state TEXT NOT NULL,
                    created REAL NOT NULL, finished REAL);
            """)
            db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            yield db

    def register(self, launcher, mode, project=None, parent=None):
        identifier = uuid4().hex
        now = time.time()
        with self.connection() as db:
            db.execute(
                "INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,0)",
                (identifier, self.owner, os.getpid(), launcher, mode, project, now, now, parent),
            )
        self.maintain()
        return identifier

    def heartbeat(self, identifier, project=None, controls=False):
        with self.connection() as db:
            db.execute(
                "UPDATE sessions SET heartbeat=?, project=?, controls=? WHERE id=? AND owner=?",
                (time.time(), project, int(controls), identifier, self.owner),
            )

    def close(self, identifier):
        with self.connection() as db:
            db.execute("DELETE FROM sessions WHERE id=? AND owner=?", (identifier, self.owner))
            db.execute(
                "UPDATE tasks SET state='interrupted',finished=? WHERE session=? AND state='running' AND owner=?",
                (time.time(), identifier, self.owner),
            )
            db.execute(
                "UPDATE commands SET state='expired',finished=? WHERE target=? AND state='queued' AND owner=?",
                (time.time(), identifier, self.owner),
            )

    def maintain(self):
        now = time.time()
        with self.connection() as db:
            db.execute("DELETE FROM sessions WHERE heartbeat<?", (now - 86400,))
            db.execute(
                "UPDATE tasks SET state='interrupted',finished=? WHERE state='running' AND session NOT IN (SELECT id FROM sessions WHERE heartbeat>=?)",
                (now, now - SESSION_TTL),
            )
            db.execute(
                "UPDATE commands SET state='expired',finished=? WHERE state='queued' AND (created<? OR target NOT IN (SELECT id FROM sessions WHERE heartbeat>=?))",
                (now, now - 30, now - SESSION_TTL),
            )
            db.execute(
                "DELETE FROM events WHERE seq <= (SELECT COALESCE(MAX(seq),0)-? FROM events)",
                (EVENT_LIMIT,),
            )
            db.execute("DELETE FROM tasks WHERE finished<?", (now - 86400,))
            db.execute("DELETE FROM commands WHERE finished<?", (now - 86400,))

    def sessions(self):
        if not self.path.exists():
            return []
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM sessions WHERE (? OR owner=?) AND heartbeat>=? ORDER BY started",
                    (self.administrative, self.owner, time.time() - SESSION_TTL),
                )
            ]

    def publish(self, session, event, *, project=None, correlation=None, metadata=None):
        if not EVENT_ID.fullmatch(event):
            raise ValueError("el ID de evento debe tener cuatro segmentos")
        # Explicit allow-list prevents plugin payloads, credentials and command
        # arguments from entering a shared diagnostics database.
        metadata = {"version": 1, **(metadata or {})}
        if set(metadata) - {"path", "version", "state", "launcher", "mode"}:
            raise ValueError("metadatos no permitidos en el canal de coordinación")
        payload = json.dumps(metadata, ensure_ascii=False)
        if len(payload) > 8192:
            raise ValueError("metadatos de evento demasiado grandes")
        with self.connection() as db:
            cursor = db.execute(
                "INSERT INTO events(owner,session,event,project,correlation,created,metadata) VALUES (?,?,?,?,?,?,?)",
                (
                    self.owner,
                    session,
                    event,
                    project,
                    correlation or uuid4().hex,
                    time.time(),
                    payload,
                ),
            )
            return cursor.lastrowid

    def events(self, after=0, limit=200):
        if not 1 <= limit <= 1000:
            raise ValueError("limit debe estar entre 1 y 1000")
        if not self.path.exists():
            return []
        with self.connection() as db:
            rows = [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM events WHERE owner=? AND seq>? ORDER BY seq LIMIT ?",
                    (self.owner, after, limit),
                )
            ]
        for row in rows:
            row["metadata"] = json.loads(row["metadata"])
        return rows

    def latest(self):
        with self.connection() as db:
            return db.execute(
                "SELECT COALESCE(MAX(seq),0) FROM events WHERE owner=?", (self.owner,)
            ).fetchone()[0]

    def task(self, session, origin, identifier, state="running"):
        if not EVENT_ID.fullmatch(origin):
            raise ValueError("el origen de tarea debe tener cuatro segmentos")
        with self.connection() as db:
            if state == "running":
                db.execute(
                    "INSERT INTO tasks VALUES (?,?,?,?,?,?,NULL)",
                    (identifier, session, self.owner, origin, state, time.time()),
                )
            else:
                db.execute(
                    "UPDATE tasks SET state=?,finished=? WHERE id=? AND owner=?",
                    (state, time.time(), identifier, self.owner),
                )

    def tasks(self):
        if not self.path.exists():
            return []
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM tasks WHERE owner=? ORDER BY started DESC LIMIT 200",
                    (self.owner,),
                )
            ]

    def enqueue(self, target, action, value=None):
        if action not in {"refresh", "view"} or (action == "refresh" and value is not None):
            raise ValueError("acción de interfaz no permitida")
        if action == "view" and value not in {"gui", "tui", "plugins", "projects", "settings"}:
            raise ValueError("vista no válida")
        identifier = uuid4().hex
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT controls,owner,launcher,mode FROM sessions WHERE id=? AND (? OR owner=?) AND heartbeat>=?",
                (target, self.administrative, self.owner, time.time() - SESSION_TTL),
            ).fetchone()
            if not row or not row[0]:
                raise ValueError("la sesión no está disponible para recibir órdenes")
            if action == "view" and (
                row[2] != "lanip"
                or (row[3] == "gui" and value != "gui")
                or (row[3] == "tui" and value == "gui")
                or row[3] not in {"gui", "tui"}
            ):
                raise ValueError("esa vista no es compatible con la interfaz destinataria")
            db.execute(
                "INSERT INTO commands VALUES (?,?,?,?,?,'queued',?,NULL)",
                (identifier, target, row[1], action, value, time.time()),
            )
        return identifier

    def claim(self, target):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM commands WHERE target=? AND owner=? AND state='queued' AND created>=? ORDER BY created",
                    (target, self.owner, time.time() - 30),
                )
            ]
            for row in rows:
                db.execute(
                    "UPDATE commands SET state='delivered',finished=? WHERE id=?",
                    (time.time(), row["id"]),
                )
        return rows

    def acknowledge(self, identifier, success):
        with self.connection() as db:
            db.execute(
                "UPDATE commands SET state=?,finished=? WHERE id=? AND owner=?",
                ("accepted" if success else "failed", time.time(), identifier, self.owner),
            )
