from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from .models import MonitorSession


class SessionManager:
    def __init__(self, repository, clock=lambda: datetime.now().astimezone()):
        self.repository = repository
        self.clock = clock

    def start(
        self,
        manager_id,
        project_id,
        network="",
        interface="",
        local_ip="",
        mode="temporary",
        authority="observe",
        duration=None,
    ):
        active = self.repository.active()
        if active:
            raise RuntimeError("ya existe una sesión monitor activa")
        now = self.clock()
        expires = (now + timedelta(seconds=duration)).isoformat() if duration else None
        session = MonitorSession(
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            manager_id,
            project_id,
            network,
            interface,
            local_ip,
            mode,
            authority,
            now.isoformat(),
            expires,
            "active",
        )
        self.repository.save(session)
        return session

    def stop(self, status="completed"):
        session = self.repository.active()
        if not session:
            raise RuntimeError("no hay una sesión monitor activa")
        session.status = status
        self.repository.save(session)
        return session

    def expire(self):
        session = self.repository.active()
        if (
            session
            and session.expiresAt
            and self.clock() >= datetime.fromisoformat(session.expiresAt)
        ):
            session.status = "expired"
            self.repository.save(session)
            return session
        return None
