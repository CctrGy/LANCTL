"""Shared desktop adapters; domain validation belongs to the shared services."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from threading import Lock, Thread

_STATE_LOCK = Lock()
_PROJECT_ACTIONS = frozenset(
    {
        "use_project",
        "create_project",
        "save_project",
        "project_state",
        "request_close",
        "update_device",
        "delete_device",
        "undo_edit",
        "redo_edit",
        "scan_network",
        "diagnose_device",
        "get_device_details",
        "plugin_action",
        "wake_device",
        "open_device",
        "open_service",
        "open_terminal",
        "group_action",
        "create_group",
        "save_settings",
        "save_setting",
        "save_catalog_setting",
        "save_launcher_setting",
        "wire_create",
        "wire_organization",
        "wire_update",
        "wire_connect",
        "wire_port",
        "wire_delete",
        "rack_appearance",
        "rack_dimensions",
        "rack_create",
        "rack_element",
        "rack_destinations",
        "rack_organization",
        "access_unlock",
        "access_lock",
        "access_set",
        "access_update",
        "access_delete",
        "access_open",
        "monitor_action",
        "monitor_samples",
        "monitor_incident",
        "monitor_device",
        "monitor_update",
        "monitor_group",
    }
)


class GuiSupportMixin:
    """Explicit RPC surface used by all six native GUI windows."""

    def project_call(self, expected, method, arguments):
        """Version 1 additive RPC envelope for actions from a displayed project.

        Existing RPC methods remain callable by legacy clients. The native GUI
        sends the identity rendered with its data, never a backend-only cache.
        """

        def operation():
            from lanctl.core.project_context import project_operation, require_project

            if (
                not isinstance(method, str)
                or method not in _PROJECT_ACTIONS
                or not isinstance(arguments, list)
            ):
                raise ValueError("Operación de proyecto no permitida")
            target = getattr(self, method, None)
            if not callable(target):
                raise ValueError("Operación no disponible en este launcher")
            # Do not wait behind a scan and then apply an obsolete queued edit.
            if not self._lock.acquire(blocking=False):
                raise RuntimeError("Hay una operación en curso; espera o cancela el escaneo.")
            try:
                with project_operation():
                    require_project(expected)
                    return target(*arguments)
            finally:
                self._lock.release()

        return self._support_reply(operation)

    def _project_actions(self):
        return sorted(name for name in _PROJECT_ACTIONS if callable(getattr(self, name, None)))

    def _support_state(self):
        with _STATE_LOCK:
            if not hasattr(self, "_gui_session"):
                from lanctl.core.session import current_session

                session = current_session()
                self._gui_session = session.id if session else ""
                self._gui_update_lock = Lock()
                self._gui_update = {"status": "idle"}
        return self._gui_session

    def _support_reply(self, operation):
        try:
            self._support_state()
            return {"ok": True, **(operation() or {})}
        except Exception as exc:  # noqa: BLE001 - native RPC preserves originating exception
            from lanctl.core.errors import errors

            name = getattr(operation, "__qualname__", "Support").split(".")
            action = name[1] if name[0] == "GuiSupportMixin" and len(name) > 1 else name[0]
            event = errors.from_exception(
                exc,
                origin=f"LANCTL.GUI.{action}",
                code="GUI.SUPPORT.FAILED",
                level=43,
                print_output=False,
            )
            return {
                "ok": False,
                "error": event.message,
                "errorId": event.error_id,
                "errorDetails": event.to_dict(),
            }

    def gui_preferences(self):
        from lanctl.core.gui_preferences import preferences_payload

        return self._support_reply(preferences_payload)

    def save_gui_preferences(self, values):
        from lanctl.core.gui_preferences import save_preferences

        return self._support_reply(lambda: save_preferences(values))

    def open_official_link(self, key):
        from lanctl.core.official_links import open_official_link

        return self._support_reply(lambda: open_official_link(key))

    def check_updates(self, manual=False):
        self._support_state()
        with self._gui_update_lock:
            if self._gui_update.get("status") == "checking":
                return {"ok": True, **self._gui_update}
            self._gui_update = {"status": "checking"}

        def check():
            from lanctl.core.updates import UpdateService

            result = self._support_reply(lambda: UpdateService().check(manual=bool(manual)))
            with self._gui_update_lock:
                self._gui_update = result

        Thread(target=check, daemon=True, name="gui-update-check").start()
        return {"ok": True, "status": "checking"}

    def update_status(self):
        self._support_state()
        with self._gui_update_lock:
            return {"ok": True, **self._gui_update}

    def remind_update_later(self, version):
        from lanctl.core.updates import UpdateService

        return self._support_reply(lambda: UpdateService().remind_later(version))

    def open_update_release(self):
        def open_release():
            import re
            import webbrowser

            url = self._gui_update.get("url", "")
            if not re.fullmatch(r"https://github\.com/CctrGy/LANCTL/releases/[^\s]+", url, re.I):
                raise ValueError("No hay un enlace de versión oficial disponible")
            return {"opened": webbrowser.open(url), "url": url}

        return self._support_reply(open_release)

    def record_activity(self, message, level=20, error_details=None):
        def append():
            from lanctl.core.activity import ActivityStore
            from lanctl.core.config import load_config
            from lanctl.core.session import current_session

            session = current_session()
            if session is None:
                raise ValueError("No hay sesión GUI registrada para conservar la actividad")
            self._gui_session = session.id
            if not isinstance(message, str) or not message.strip() or len(message) > 4096:
                raise ValueError("Mensaje de actividad no válido")
            stored_message = message
            if error_details is not None:
                if not isinstance(error_details, dict):
                    raise ValueError("Detalle de error no válido")
                details = {
                    k: str(error_details[k])[:128]
                    for k in ("origin", "code", "errorId", "timestamp", "correlationId")
                    if k in error_details
                }
                stored_message = json.dumps(
                    {"message": message[:1000], "error": details}, ensure_ascii=False
                )
            row = ActivityStore().append(
                stored_message,
                launcher=session.launcher,
                session=self._gui_session,
                project=load_config().get("activeProject"),
                level=43 if level == 43 else 20,
            )
            from lanctl.core.errors import redact_text
            from lanctl.core.logger import write_log

            warning = ""
            try:
                write_log(
                    "GUI_ACTIVITY "
                    + json.dumps(
                        {
                            "schemaVersion": 1,
                            "level": row["level"],
                            "message": redact_text(message),
                            "origin": f"LANCTL.{session.launcher}.GUI",
                        },
                        ensure_ascii=False,
                    )
                )
            except OSError as exc:
                from lanctl.core.errors import errors

                event = errors.from_exception(
                    exc,
                    origin="LANCTL.GUI.Activity.Log",
                    code="GUI.ACTIVITY.LOG.FAILED",
                    level=34,
                    print_output=False,
                    once_key="gui.activity.log",
                )
                warning = f"Actividad conservada; no se pudo escribir el registro operativo: {event.message}"
            return {"activity": row, "loggingWarning": warning}

        return self._support_reply(append)

    def open_monitor(self, view="activity"):
        def launch():
            from lanctl.apps.suite.processes import launcher_command, process_options

            if view not in {"activity", "report", "logs"}:
                raise ValueError("Vista de LANMON desconocida")
            options = process_options(context_launcher="lanmon")
            options["env"]["LANCTL_GUI_VIEW"] = view
            options["env"]["LANCTL_GUI_SOURCE_SESSION"] = self._gui_session
            subprocess.Popen(
                launcher_command("lanmon", "--gui"),
                **options,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return {"message": "LANMON abierto", "session": self._gui_session}

        return self._support_reply(launch)

    def monitor_view(self):
        if getattr(self, "_launcher", None) != "lanmon":
            return {"ok": True, "view": "", "sourceSession": ""}
        return {
            "ok": True,
            "view": os.environ.get("LANCTL_GUI_VIEW", ""),
            "sourceSession": os.environ.get("LANCTL_GUI_SOURCE_SESSION", ""),
        }

    def open_live_logs(self):
        def launch():
            from lanctl.apps.monitor.log_stream import open_log_window

            open_log_window(tui=True)
            return {"message": "Visor de registros de LANMON abierto"}

        return self._support_reply(launch)

    def _require_monitor_view(self):
        if getattr(self, "_launcher", None) != "lanmon":
            raise ValueError("Esta operación pertenece a LANMON")

    def monitor_activity(self, session=None, all_projects=False):
        def read():
            from lanctl.core.activity import ActivityStore
            from lanctl.core.config import load_config

            self._require_monitor_view()
            project = None if all_projects else load_config().get("activeProject") or ""
            rows = ActivityStore().query(limit=500, project=project, latest=True)
            for row in rows:
                try:
                    envelope = json.loads(row["message"])
                except (ValueError, TypeError):
                    continue
                if isinstance(envelope, dict) and isinstance(envelope.get("error"), dict):
                    row["message"] = envelope.get("message", "")
                    row["error"] = envelope["error"]
            sessions = sorted({row["session"] for row in rows})
            return {
                "records": [r for r in rows if not session or r["session"] == session],
                "sessions": sessions,
                "project": project,
            }

        return self._support_reply(read)

    def monitor_logs(self):
        def read():
            from collections import deque

            from lanctl.apps.monitor.log_stream import LogFollower
            from lanctl.core.config import load_config
            from lanctl.core.paths import application_path

            self._require_monitor_view()
            if not hasattr(self, "_gui_log_follower"):
                self._gui_log_follower = LogFollower(
                    application_path(load_config()["programLog"]), 300
                )
                self._gui_log_rows = deque(maxlen=500)
            self._gui_log_rows.extend(self._gui_log_follower.poll())
            return {"records": list(self._gui_log_rows)}

        return self._support_reply(read)

    def prepare_report(self, values):
        def prepare():
            from lanctl.core.diagnostics import diagnostic_markdown, prepare_diagnostic

            self._require_monitor_view()
            if not isinstance(values, dict):
                raise ValueError("Borrador de reporte no válido")
            activity = self.monitor_activity(values.get("session") or None)
            if not activity["ok"]:
                raise ValueError(activity["error"])
            logs = self.monitor_logs() if values.get("includeLogs") else {"records": []}
            plugins = []
            if values.get("includePlugins"):
                from lanctl.core.plugins.manager import get_plugin_manager

                plugins = [
                    {"id": p.manifest.plugin_id, "version": p.manifest.version}
                    for p in get_plugin_manager().list()
                ]
            report = prepare_diagnostic(
                description=str(values.get("description", ""))[:16000],
                steps=str(values.get("steps", ""))[:16000],
                expected=str(values.get("expected", ""))[:16000],
                application=activity["records"][-1]["launcher"]
                if values.get("session") and activity["records"]
                else "lanmon",
                interface="gui",
                errors=[
                    {
                        **r.get("error", {}),
                        "message": r["message"],
                        "level": r["level"],
                        "timestamp": r["created"],
                    }
                    for r in activity["records"]
                    if r["level"] >= 40
                ]
                if values.get("includeErrors", True)
                else [],
                logs=logs["records"][-100:]
                + (
                    [{"source": "gui-activity", **r} for r in activity["records"][-100:]]
                    if values.get("includeActivity")
                    else []
                ),
                plugins=plugins,
                context={
                    "session": values.get("session", ""),
                },
                anonymize=values.get("anonymize", True) is not False,
            )
            self._gui_report = report
            return {"report": report, "markdown": diagnostic_markdown(report)}

        return self._support_reply(prepare)

    def open_report_form(self):
        def open_form():
            import webbrowser

            from lanctl.apps.monitor.bug_reports import bug_report_url

            self._require_monitor_view()
            if not getattr(self, "_gui_report", None):
                raise ValueError("Prepara y revisa el reporte primero")
            url = bug_report_url(self._gui_report)
            return {"opened": webbrowser.open(url), "url": url}

        return self._support_reply(open_form)

    def export_report(self):
        def export():
            import webview

            from lanctl.core.diagnostics import export_diagnostic

            self._require_monitor_view()
            if not getattr(self, "_gui_report", None):
                raise ValueError("Prepara y revisa el reporte primero")
            if self._window is None:
                raise ValueError("No hay ventana para seleccionar el archivo")
            path = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename="lanctl-diagnostic.md",
                file_types=("Diagnóstico Markdown (*.md)",),
            )
            if not path:
                return {"cancelled": True}
            if isinstance(path, (tuple, list)):
                path = path[0]
            return {"path": export_diagnostic(self._gui_report, path)}

        return self._support_reply(export)
