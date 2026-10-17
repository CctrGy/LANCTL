"""Live monitor view and bounded command adapter; opening never starts probes."""

from dataclasses import asdict
from pathlib import Path

from lanctl.apps.monitor.database import IncidentRepository, MonitorDatabase, SessionRepository
from lanctl.apps.monitor.lifecycle import SingletonLock
from lanctl.core.config import load_config
from lanctl.core.database import DeviceDatabase
from lanctl.core.history import HistoryService
from lanctl.core.paths import application_path


class MonitorGuiService:
    def snapshot(self):
        config = load_config()
        with MonitorDatabase(application_path(config["monitorDatabase"])) as db:
            states = {r["device_id"]: dict(r) for r in db.execute("SELECT * FROM device_state")}
            latest = {
                row["device_id"]: dict(row)
                for row in db.execute(
                    "SELECT s.* FROM samples s JOIN (SELECT device_id,MAX(sample_id) AS last_id FROM samples "
                    "WHERE check_type IN ('availability','ping','arp') GROUP BY device_id) q ON q.last_id=s.sample_id"
                )
            }
            rows = []
            for device in DeviceDatabase(config["database"]).load():
                last = latest.get(device.device_id, {})
                state = states.get(device.device_id) or {
                    "presence": "online"
                    if last.get("presence")
                    else "offline"
                    if last
                    else "unknown",
                    "latency_ms": last.get("latency_ms"),
                    "updated_at": last.get("timestamp"),
                }
                rows.append(
                    {
                        "id": device.device_id,
                        "name": device.alias or device.name or device.ip,
                        "ip": device.ip,
                        "groups": list(device.groups),
                        "presence": state.get("presence", "unknown"),
                        "health": state.get("health", "unknown"),
                        "latency": state.get("latency_ms"),
                        "updated": state.get("updated_at"),
                    }
                )
            session = SessionRepository(db).active()
            return {
                "records": rows,
                "incidents": [
                    asdict(i)
                    for i in IncidentRepository(db).list()
                    if i.deviceId in {r["id"] for r in rows}
                ],
                "events": [
                    event.to_dict()
                    for event in HistoryService(config.get("activeProject")).query(
                        source="lanctl.monitor", limit=30, reverse=True
                    )
                ]
                if config.get("activeProject")
                else [],
                "session": asdict(session) if session else None,
                "process": SingletonLock(application_path(config["monitorLock"])).status(),
                "storage": str(db.path),
            }

    def samples(self, identifier):
        config = load_config()
        DeviceDatabase(config["database"]).resolve(identifier)
        with MonitorDatabase(application_path(config["monitorDatabase"])) as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT timestamp,latency_ms,presence FROM samples WHERE device_id=? "
                    "AND check_type IN ('availability','ping','arp') ORDER BY sample_id DESC LIMIT 60",
                    (identifier,),
                )
            ][::-1]

    def incident(self, identifier, action):
        from lanctl.apps.monitor.incidents import IncidentManager

        if action not in {"acknowledge", "close"}:
            raise ValueError("Acción de incidencia no permitida")
        if not any(i["incidentId"] == identifier for i in self.snapshot()["incidents"]):
            raise ValueError("La incidencia no pertenece al inventario mostrado")
        with MonitorDatabase(application_path(load_config()["monitorDatabase"])) as db:
            manager = IncidentManager(IncidentRepository(db))
            return asdict(getattr(manager, action)(identifier))

    def action(self, action):
        if action not in {"start", "stop", "once"}:
            raise ValueError("Operación de monitor no permitida")
        config = load_config()
        project = config.get("activeProject")
        if not project:
            raise ValueError("Selecciona un proyecto antes de operar el monitor")
        snapshot = self.snapshot()
        session = snapshot["session"]
        if session and Path(session["projectId"]).resolve() != Path(project).resolve():
            raise ValueError("El monitor está asociado a otro proyecto")
        if action != "stop" and (session or snapshot["process"].get("running")):
            raise ValueError("Ya existe una sesión de monitor; detenla antes de iniciar otra")
        from lanctl.apps.monitor.commands import execute_monitor
        from lanctl.bootstrap.lanmon import build_parser

        words = [action, "--project", project, "--json"]
        if action == "start":
            words.extend(["--permanent"])
        return execute_monitor(build_parser().parse_args(words))
