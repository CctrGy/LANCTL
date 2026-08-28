from __future__ import annotations

import uuid

from .models import Incident, now_iso


class IncidentManager:
    def __init__(self, repository):
        self.repository = repository

    def open(self, device_id, severity, cause, origin, correlation_id=None, session_id=None):
        existing = next(
            (
                x
                for x in self.repository.list()
                if x.deviceId == device_id
                and x.cause == cause
                and x.status in {"open", "acknowledged"}
            ),
            None,
        )
        if existing:
            return existing
        incident = Incident(
            str(uuid.uuid4()),
            device_id,
            severity,
            cause,
            origin,
            now_iso(),
            correlationId=correlation_id,
            sessionId=session_id,
        )
        self.repository.save(incident)
        return incident

    def acknowledge(self, incident_id):
        return self._set(incident_id, "acknowledged")

    def resolve(self, device_id, cause):
        item = next(
            (
                x
                for x in self.repository.list()
                if x.deviceId == device_id
                and x.cause == cause
                and x.status in {"open", "acknowledged"}
            ),
            None,
        )
        if item:
            item.status = "resolved"
            item.resolvedAt = now_iso()
            self.repository.save(item)
        return item

    def close(self, incident_id):
        return self._set(incident_id, "closed")

    def _set(self, incident_id, status):
        item = next((x for x in self.repository.list() if x.incidentId == incident_id), None)
        if not item:
            raise ValueError("incidencia no encontrada")
        item.status = status
        if status in {"resolved", "closed"}:
            item.resolvedAt = now_iso()
        self.repository.save(item)
        return item
