from __future__ import annotations


class InMemoryMetricsStore:
    def __init__(self):
        self.rows = []

    def write(self, result, session_id):
        self.rows.append((session_id, result))


class InMemorySessionRepository:
    def __init__(self):
        self.rows = {}

    def save(self, session):
        self.rows[session.sessionId] = session

    def active(self):
        return next(
            (
                x
                for x in reversed(list(self.rows.values()))
                if x.status in {"pending", "active", "stopping"}
            ),
            None,
        )


class InMemoryIncidentRepository:
    def __init__(self):
        self.rows = {}

    def list(self):
        return list(self.rows.values())

    def save(self, incident):
        self.rows[incident.incidentId] = incident


class NullReportBuilder:
    def completed(self, session):
        pass
