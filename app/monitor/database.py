from __future__ import annotations

import json
import os
import platform
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.paths import application_path

from .configuration import parse_duration
from .models import CheckResult, Incident, MonitorSession

SCHEMA_VERSION = 2


def utc(value=None):
    return (
        (value or datetime.now(timezone.utc))
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def monitor_database_path(override=None, *, environment=None, platform_name=None):
    if override:
        return Path(override).expanduser().resolve()
    env = environment or os.environ
    system = (platform_name or platform.system()).casefold()
    if system == "windows":
        return application_path("data/lc/monitor.db")
    state = env.get("XDG_STATE_HOME")
    return (
        Path(state).expanduser()
        if state
        else Path(env.get("HOME", str(Path.home()))) / ".local/state"
    ) / "lanctl/monitor.db"


class MonitorDatabase:
    def __init__(self, path=None):
        self.path = monitor_database_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.connection = sqlite3.connect(self.path, timeout=5, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        try:
            self._migrate()
        except Exception:
            self.connection.close()
            raise

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def transaction(self):
        with self.lock, self.connection:
            yield self.connection

    def _migrate(self):
        current = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if current > SCHEMA_VERSION:
            raise ValueError(f"monitor.db versión futura {current}")
        if current == 0:
            self.connection.executescript("""
            CREATE TABLE manager_identity(manager_id TEXT PRIMARY KEY,name TEXT,platform TEXT,installation_id TEXT UNIQUE,metadata TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE network_identity(network_id TEXT PRIMARY KEY,project_id TEXT,cidr TEXT,gateway_ip TEXT,gateway_mac TEXT,ssid TEXT,dns_suffix TEXT,evidence TEXT NOT NULL,confidence REAL NOT NULL,last_validated TEXT NOT NULL);
            CREATE TABLE sessions(session_id TEXT PRIMARY KEY,run_id TEXT,manager_id TEXT,project_id TEXT,network TEXT,interface TEXT,local_ip TEXT,mode TEXT,authority TEXT,started_at TEXT,expires_at TEXT,finished_at TEXT,status TEXT,error TEXT,report TEXT);
            CREATE TABLE device_state(device_id TEXT PRIMARY KEY,presence TEXT,health TEXT,latency_ms REAL,updated_at TEXT,session_id TEXT,consecutive_failures INTEGER NOT NULL DEFAULT 0,consecutive_recoveries INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE samples(sample_id INTEGER PRIMARY KEY AUTOINCREMENT,device_id TEXT NOT NULL,timestamp TEXT NOT NULL,presence INTEGER NOT NULL,latency_ms REAL,check_type TEXT NOT NULL,result TEXT NOT NULL,session_id TEXT,correlation_id TEXT,details TEXT NOT NULL DEFAULT '{}');
            CREATE INDEX samples_device_time ON samples(device_id,timestamp); CREATE INDEX samples_time ON samples(timestamp);
            CREATE TABLE metric_aggregates(device_id TEXT NOT NULL,bucket TEXT NOT NULL,resolution INTEGER NOT NULL,availability REAL,latency_min REAL,latency_avg REAL,latency_max REAL,packet_loss REAL,sample_count INTEGER,outage_count INTEGER,outage_duration REAL,PRIMARY KEY(device_id,bucket,resolution));
            CREATE INDEX aggregate_time ON metric_aggregates(bucket,resolution);
            CREATE TABLE incidents(incident_id TEXT PRIMARY KEY,device_id TEXT,severity TEXT,cause TEXT,origin TEXT,opened_at TEXT,resolved_at TEXT,closed_at TEXT,status TEXT,correlation_id TEXT,session_id TEXT,acknowledged_at TEXT,transitions TEXT NOT NULL);
            CREATE INDEX incidents_device_status ON incidents(device_id,status,opened_at);
            CREATE TABLE assignments(assignment_id TEXT PRIMARY KEY,payload TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE custom_profiles(profile_id TEXT PRIMARY KEY,payload TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE runtime_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);
            PRAGMA user_version=2;
            """)
            self.connection.commit()
        elif current == 1:
            self.connection.executescript("""
            ALTER TABLE device_state ADD COLUMN consecutive_failures INTEGER NOT NULL DEFAULT 0;
            ALTER TABLE device_state ADD COLUMN consecutive_recoveries INTEGER NOT NULL DEFAULT 0;
            ALTER TABLE samples ADD COLUMN details TEXT NOT NULL DEFAULT '{}';
            PRAGMA user_version=2;
            """)
            self.connection.commit()

    def execute(self, sql, values=()):
        return self.connection.execute(sql, values)


class MetricsStore:
    def __init__(self, database: MonitorDatabase):
        self.db = database

    def write(self, result: CheckResult, session_id: str) -> None:
        timestamp = _normalize(result.timestamp)
        presence = 1 if result.success else 0
        details = json.dumps(
            {"evidence": list(result.evidence), "metrics": result.metrics, "error": result.error},
            ensure_ascii=False,
        )
        with self.db.transaction():
            self.db.execute(
                "INSERT INTO samples(device_id,timestamp,presence,latency_ms,check_type,result,session_id,correlation_id,details) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    result.target,
                    timestamp,
                    presence,
                    result.latencyMs,
                    result.checkId,
                    "success" if result.success else "failure",
                    session_id,
                    result.metrics.get("correlationId"),
                    details,
                ),
            )

    def aggregate(self, *, now=None, resolutions=(300, 3600)):
        written = 0
        for resolution in resolutions:
            rows = self.db.execute(
                "SELECT device_id,CAST(strftime('%s',timestamp)/? AS INTEGER)*? bucket_epoch,AVG(presence)*100 availability,MIN(latency_ms) lmin,AVG(latency_ms) lavg,MAX(latency_ms) lmax,COUNT(*) count,SUM(CASE WHEN presence=0 THEN 1 ELSE 0 END) losses FROM samples WHERE check_type IN ('availability','ping','arp') GROUP BY device_id,bucket_epoch",
                (resolution, resolution),
            ).fetchall()
            with self.db.transaction():
                for row in rows:
                    bucket = (
                        datetime.fromtimestamp(row["bucket_epoch"], timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z")
                    )
                    self.db.execute(
                        "INSERT OR REPLACE INTO metric_aggregates VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            row["device_id"],
                            bucket,
                            resolution,
                            row["availability"],
                            row["lmin"],
                            row["lavg"],
                            row["lmax"],
                            row["losses"] * 100 / row["count"],
                            row["count"],
                            row["losses"],
                            row["losses"] * resolution,
                        ),
                    )
                    written += 1
        return written

    def cleanup(self, retention, *, now=None, batch=10000):
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        raw = utc(current - timedelta(seconds=parse_duration(retention.get("rawSamples", "24h"))))
        with self.db.transaction():
            deleted = self.db.execute(
                "DELETE FROM samples WHERE sample_id IN (SELECT sample_id FROM samples WHERE timestamp<? LIMIT ?)",
                (raw, batch),
            ).rowcount
            for resolution, key in ((300, "fiveMinuteAggregates"), (3600, "hourlyAggregates")):
                cutoff = utc(
                    current
                    - timedelta(
                        seconds=parse_duration(
                            retention.get(key, "30d" if resolution == 300 else "365d")
                        )
                    )
                )
                self.db.execute(
                    "DELETE FROM metric_aggregates WHERE resolution=? AND bucket<?",
                    (resolution, cutoff),
                )
        return deleted

    def summary(self):
        row = self.db.execute(
            "SELECT COUNT(DISTINCT device_id) devices,AVG(presence)*100 availability,AVG(latency_ms) latency FROM samples WHERE check_type IN ('availability','ping','arp')"
        ).fetchone()
        return dict(row)


class SessionRepository:
    def __init__(self, database):
        self.db = database

    def save(self, s):
        with self.db.transaction():
            self.db.execute(
                "INSERT INTO sessions(session_id,run_id,manager_id,project_id,network,interface,local_ip,mode,authority,started_at,expires_at,status,error) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET status=excluded.status,expires_at=excluded.expires_at,error=excluded.error",
                (
                    s.sessionId,
                    s.runId,
                    s.managerId,
                    s.projectId,
                    s.network,
                    s.interface,
                    s.localIp,
                    s.mode,
                    s.authority,
                    _normalize(s.startedAt),
                    _normalize(s.expiresAt) if s.expiresAt else None,
                    s.status,
                    json.dumps(s.error) if s.error else None,
                ),
            )

    def active(self):
        row = self.db.execute(
            "SELECT * FROM sessions WHERE status IN ('pending','active','stopping') ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return _session(row) if row else None

    def list(self):
        return [
            _session(x) for x in self.db.execute("SELECT * FROM sessions ORDER BY started_at DESC")
        ]

    def get(self, session_id):
        row = self.db.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if not row:
            raise ValueError("sesión monitor no encontrada")
        return _session(row)

    def save_report(self, session_id, report):
        with self.db.transaction():
            self.db.execute(
                "UPDATE sessions SET report=? WHERE session_id=?",
                (json.dumps(report, ensure_ascii=False), session_id),
            )


class IncidentRepository:
    def __init__(self, database):
        self.db = database

    def save(self, item):
        old = self.db.execute(
            "SELECT transitions FROM incidents WHERE incident_id=?", (item.incidentId,)
        ).fetchone()
        transitions = json.loads(old[0]) if old else []
        if not transitions or transitions[-1]["status"] != item.status:
            transitions.append({"status": item.status, "at": utc()})
        with self.db.transaction():
            self.db.execute(
                "INSERT INTO incidents(incident_id,device_id,severity,cause,origin,opened_at,resolved_at,status,correlation_id,session_id,transitions) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(incident_id) DO UPDATE SET severity=excluded.severity,resolved_at=excluded.resolved_at,status=excluded.status,transitions=excluded.transitions",
                (
                    item.incidentId,
                    item.deviceId,
                    item.severity,
                    item.cause,
                    item.origin,
                    _normalize(item.openedAt),
                    _normalize(item.resolvedAt) if item.resolvedAt else None,
                    item.status,
                    item.correlationId,
                    item.sessionId,
                    json.dumps(transitions),
                ),
            )

    def list(self):
        return [
            _incident(x) for x in self.db.execute("SELECT * FROM incidents ORDER BY opened_at DESC")
        ]


class IdentityRepository:
    def __init__(self, database):
        self.db = database

    def manager(self, name="LANCTL Manager", metadata=None):
        row = self.db.execute("SELECT * FROM manager_identity LIMIT 1").fetchone()
        if row:
            return dict(row)
        identity = {
            "manager_id": "manager_" + uuid.uuid4().hex,
            "name": name,
            "platform": platform.platform(),
            "installation_id": str(uuid.uuid4()),
            "metadata": json.dumps(metadata or {}),
            "updated_at": utc(),
        }
        with self.db.transaction():
            self.db.execute(
                "INSERT INTO manager_identity VALUES(:manager_id,:name,:platform,:installation_id,:metadata,:updated_at)",
                identity,
            )
        return identity

    def save_network(
        self,
        network_id,
        *,
        project_id="",
        cidr="",
        gateway_ip="",
        gateway_mac="",
        ssid="",
        dns_suffix="",
        evidence=(),
        confidence=0,
    ):
        payload = (
            network_id,
            project_id,
            cidr,
            gateway_ip,
            gateway_mac,
            ssid,
            dns_suffix,
            json.dumps(list(evidence)),
            float(confidence),
            utc(),
        )
        with self.db.transaction():
            self.db.execute(
                "INSERT OR REPLACE INTO network_identity VALUES(?,?,?,?,?,?,?,?,?,?)", payload
            )

    def compare(self, network_id, evidence):
        row = self.db.execute(
            "SELECT * FROM network_identity WHERE network_id=?", (network_id,)
        ).fetchone()
        if not row:
            return {"match": False, "reason": "unknown-network", "evidence": list(evidence)}
        stored = set(json.loads(row["evidence"]))
        actual = set(evidence)
        return {
            "match": bool(stored & actual),
            "confidence": row["confidence"],
            "storedEvidence": sorted(stored),
            "actualEvidence": sorted(actual),
        }


def _normalize(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp monitor requiere zona horaria")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _session(r):
    return MonitorSession(
        r["session_id"],
        r["run_id"],
        r["manager_id"],
        r["project_id"],
        r["network"],
        r["interface"],
        r["local_ip"],
        r["mode"],
        r["authority"],
        r["started_at"],
        r["expires_at"],
        r["status"],
        json.loads(r["error"]) if r["error"] else None,
    )


def _incident(r):
    return Incident(
        r["incident_id"],
        r["device_id"],
        r["severity"],
        r["cause"],
        r["origin"],
        r["opened_at"],
        r["status"],
        r["resolved_at"],
        r["correlation_id"],
        r["session_id"],
    )
