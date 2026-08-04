from __future__ import annotations
import json
from dataclasses import asdict
from datetime import datetime,timezone
from app.projects.vlf import append_monitor_document

class ReportBuilder:
    def __init__(self,database,session_repository,incident_repository,project=None):self.db=database;self.sessions=session_repository;self.incidents=incident_repository;self.project=project
    def build(self,session):
        samples=self.db.execute("SELECT device_id,COUNT(*) samples,SUM(CASE WHEN presence=1 THEN 1 ELSE 0 END) online,AVG(latency_ms) latency,SUM(CASE WHEN presence=0 THEN 1 ELSE 0 END) outages FROM samples WHERE session_id=? GROUP BY device_id",(session.sessionId,)).fetchall()
        incidents=[asdict(x) for x in self.incidents.list() if x.sessionId==session.sessionId]
        report={"schemaVersion":1,"session":asdict(session),"generatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"summary":{"devicesObserved":len(samples),"samples":sum(x["samples"] for x in samples),"disconnects":sum(x["outages"] for x in samples),"incidents":len(incidents)},"devices":[dict(x) for x in samples],"incidents":incidents,"pendingObservations":[]}
        self.sessions.save_report(session.sessionId,report);return report
    def completed(self,session):
        report=self.build(session)
        if self.project:append_monitor_document(self.project,f"monitoring/sessions/{session.sessionId}.json",report)
        return report
    @staticmethod
    def human(report):
        s=report["summary"];return f"Sesión {report['session']['sessionId']}\nDispositivos observados: {s['devicesObserved']}\nMuestras: {s['samples']}\nDesconexiones: {s['disconnects']}\nIncidencias: {s['incidents']}"

def monitor_view(database):
    metrics=database.execute("SELECT COUNT(*) devices,SUM(CASE WHEN presence='online' THEN 1 ELSE 0 END) connected,AVG(latency_ms) latency FROM device_state").fetchone()
    incidents=database.execute("SELECT * FROM incidents WHERE status IN ('open','acknowledged') ORDER BY opened_at DESC").fetchall()
    sessions=database.execute("SELECT session_id,mode,authority,started_at,status FROM sessions ORDER BY started_at DESC LIMIT 20").fetchall()
    devices=database.execute("SELECT device_id,presence,health,latency_ms,updated_at FROM device_state ORDER BY device_id").fetchall()
    if not devices:
        devices=database.execute("SELECT s.device_id,CASE s.presence WHEN 1 THEN 'online' ELSE 'offline' END presence,CASE s.result WHEN 'success' THEN 'healthy' ELSE 'warning' END health,s.latency_ms,s.timestamp updated_at FROM samples s JOIN (SELECT device_id,MAX(timestamp) timestamp FROM samples GROUP BY device_id) latest ON latest.device_id=s.device_id AND latest.timestamp=s.timestamp ORDER BY s.device_id").fetchall()
        metrics={"devices":len(devices),"connected":sum(x["presence"]=="online" for x in devices),"latency":sum((x["latency_ms"] or 0) for x in devices)/len(devices) if devices else None}
    return {"metrics":{**dict(metrics),"incidents":len(incidents)},"items":[dict(x) for x in devices],"devices":[dict(x) for x in devices],"incidents":[dict(x) for x in incidents],"sessions":[dict(x) for x in sessions]}
