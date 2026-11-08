"""Native close handshake, using pywebview's response-free state event channel.

Never destroy a WebView while its close RPC thread is still returning JavaScript.
The original request_close methods remain available to direct Python callers.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from threading import Lock, current_thread

from lanctl.core.project_context import project_identity, project_operation, require_project
from lanctl.shared.i18n import t


@dataclass(frozen=True)
class ProvisionalClose:
    """A resolved draft decision, owned by the native host, never an RPC input."""

    workspace: object
    session_id: str
    token: str
    coordinator: object
    decision: str

    def validate(self):
        from lanctl.core.projects.provisional import validate_provisional_close

        return validate_provisional_close(
            self.workspace, self.session_id, self.token, coordinator=self.coordinator
        )

    def complete(self):
        from lanctl.core.projects.provisional import complete_provisional_close

        return complete_provisional_close(
            self.workspace, self.session_id, self.token, coordinator=self.coordinator
        )

    def cancel(self):
        from lanctl.core.projects.provisional import cancel_provisional_close

        cancel_provisional_close(
            self.workspace, self.session_id, self.token, coordinator=self.coordinator
        )


class NativeClose:
    def __init__(self, window, api, close, *, decisions=frozenset({"save", "discard"})):
        self.window = window
        self.api = api
        self.close = close
        self.decisions = decisions
        self.lock = Lock()
        self.ticket = None
        self.provisional = None
        window.state += self.receive
        window.events.closed += self.closed

    def prepare(self, decision="save"):
        if not isinstance(decision, str) or decision not in self.decisions:
            raise ValueError(t("LANCTL.GUI.CLOSE.INVALID"))
        if self.provisional is not None and decision != self.provisional.decision:
            raise ValueError(t("LANCTL.GUI.CLOSE.INVALID"))
        from lanctl.core.config import load_config

        with self.lock:
            if self.ticket and time.monotonic() - self.ticket["created"] < 15:
                raise RuntimeError(t("LANCTL.GUI.CLOSE.BUSY"))
            token = secrets.token_urlsafe(24)
            self.ticket = {
                "token": token,
                "decision": decision,
                "thread": current_thread(),
                "created": time.monotonic(),
                "context": project_identity(load_config()),
                "provisional": self.provisional,
            }
            return {"token": token}

    def closed(self):
        with self.lock:
            self.ticket = None
        self.window.state -= self.receive

    def receive(self, event, key, value):
        if event != "change" or key != "lanctl_close_receipt":
            return
        with self.lock:
            ticket = self.ticket
            if (
                not ticket
                or not isinstance(value, str)
                or len(value) != len(ticket["token"])
                or not value.isascii()
                or not secrets.compare_digest(value, ticket["token"])
            ):
                return
            self.ticket = None  # one use, including failure
            if self.provisional is ticket["provisional"]:
                self.provisional = None  # a retry needs a newly resolved decision
        try:
            if time.monotonic() - ticket["created"] >= 15:
                raise TimeoutError(t("LANCTL.GUI.CLOSE.EXPIRED"))
            # The JS receipt can arrive before Qt has returned its evaluate_js
            # result. Wait for that exact RPC thread to finish before destruction.
            ticket["thread"].join(5)
            if ticket["thread"].is_alive():
                raise TimeoutError(t("LANCTL.GUI.CLOSE.BUSY"))
            if not self.api._lock.acquire(blocking=False):
                raise RuntimeError(t("LANCTL.GUI.CLOSE.BUSY"))
            try:
                with project_operation():
                    require_project(ticket["context"])
                    if ticket["provisional"] is not None:
                        ticket["provisional"].validate()
                    result = self.close(ticket["decision"])
            finally:
                self.api._lock.release()
            if not result.get("ok") or not result.get("closed"):
                if ticket["provisional"] is not None and not self.window.events.closed.is_set():
                    ticket["provisional"].cancel()
                if not self.window.events.closed.is_set():
                    self.window.state.lanctl_close_error = {"token": value, **result}
                return
            if not self.window.events.closed.wait(5):
                raise TimeoutError(t("LANCTL.GUI.CLOSE.BUSY"))
            if ticket["provisional"] is not None:
                ticket["provisional"].complete()
        except Exception as exc:  # noqa: BLE001 - native event preserves original cause
            from lanctl.core.errors import errors

            error = errors.from_exception(
                exc,
                origin="LANCTL.GUI.NativeClose.Commit",
                code="GUI.CLOSE.FAILED",
                level=43,
                print_output=False,
            )
            if ticket["provisional"] is not None and not self.window.events.closed.is_set():
                try:
                    ticket["provisional"].cancel()
                except Exception as cancel_error:  # noqa: BLE001 - preserve both origins
                    errors.from_exception(
                        cancel_error,
                        origin="LANCTL.GUI.NativeClose.Cancel",
                        code="GUI.CLOSE.FAILED",
                        level=43,
                        print_output=False,
                    )
            if not self.window.events.closed.is_set():
                self.window.state.lanctl_close_error = {
                    "token": value,
                    "ok": False,
                    "error": error.message,
                    "errorId": error.error_id,
                    "errorDetails": error.to_dict(),
                }


def install_native_close(window, api, *, launcher):
    close = api.request_close if launcher == "lanip" else lambda decision: api.request_close()
    api._native_close = NativeClose(
        window,
        api,
        close,
        decisions=frozenset({"save", "discard"}) if launcher == "lanip" else frozenset({"save"}),
    )
