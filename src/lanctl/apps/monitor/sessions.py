from __future__ import annotations

import uuid
from concurrent.futures import CancelledError
from contextlib import nullcontext
from datetime import datetime, timedelta

from .models import MonitorSession


class SessionManager:
    def __init__(self, repository, clock=lambda: datetime.now().astimezone()):
        self.repository = repository
        self.clock = clock

    def _transaction(self):
        transaction = getattr(self.repository, "transaction", None)
        if callable(transaction):
            return transaction()
        database = getattr(self.repository, "db", None)
        return database.transaction() if database is not None else nullcontext()

    def activate(self, session, *, require_existing=False):
        """Publish only the intended live session, ordered against stop requests."""
        from lanctl.shared.i18n import t

        with self._transaction():
            active = self.repository.active()
            if (
                session.status not in {"pending", "active"}
                or (require_existing and active is None)
                or (
                    active is not None
                    and (
                        active.sessionId != session.sessionId
                        or active.status not in {"pending", "active"}
                    )
                )
            ):
                raise CancelledError(t("LANCTL.MONITOR.EXECUTION.CANCELLED"))
            session.status = "active"
            self.repository.save(session)
        return session

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
        with self._transaction():
            return self._start(
                manager_id, project_id, network, interface, local_ip, mode, authority, duration
            )

    def _start(
        self, manager_id, project_id, network, interface, local_ip, mode, authority, duration
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

    def stop(self, status="completed", *, expected_session_id=None):
        with self._transaction():
            session = self.repository.active()
            if not session or (
                expected_session_id is not None and session.sessionId != expected_session_id
            ):
                raise RuntimeError("no hay una sesión monitor activa")
            session.status = status
            self.repository.save(session)
            return session

    def request_stop(self):
        with self._transaction():
            session = self.repository.active()
            if not session:
                raise RuntimeError("no hay una sesión monitor activa")
            session.status = "stopping"
            self.repository.save(session)
            return session

    def expire(self, *, mark=True):
        with self._transaction():
            return self._expire(mark=mark)

    def _expire(self, *, mark):
        session = self.repository.active()
        if (
            session
            and session.expiresAt
            and self.clock() >= datetime.fromisoformat(session.expiresAt)
        ):
            if mark:
                session.status = "expired"
                self.repository.save(session)
            return session
        return None
