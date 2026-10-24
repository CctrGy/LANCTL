"""Native desktop host for the four specialized applications."""

import subprocess
import sys
from pathlib import Path
from threading import Event, RLock, Thread

from lanctl import __version__
from lanctl.apps.suite.gui_support import GuiSupportMixin
from lanctl.apps.suite.processes import launcher_command, open_system_cli, process_options
from lanctl.core.config import load_config
from lanctl.core.project_context import project_identity, project_operation
from lanctl.core.resources import bundled_path

LAUNCHERS = {"lanwire", "lanrack", "lanaccess", "lanmon"}


class LauncherApi(GuiSupportMixin):
    def __init__(self, launcher, *, database=None, store=None, cipher="auto"):
        if launcher not in LAUNCHERS:
            raise ValueError("Launcher gráfico desconocido")
        from lanctl.apps.suite.gui import SuiteApi

        self._launcher = launcher
        self._suite = SuiteApi()
        self._window = None
        self._closing = False
        self._lock = RLock()
        self._options = (database, store, cipher)
        self._service = None
        self._binding = None
        self._bind_service(load_config())

    def _bind_service(self, config):
        database, store, cipher = self._options
        launcher = self._launcher
        binding = (
            *project_identity(config),
            config.get("physicalDatabase"),
            config.get("credentials"),
        )
        if binding == self._binding:
            return
        previous = self._service
        if launcher == "lanwire":
            from lanctl.apps.wire.gui_service import WireGuiService

            self._service = WireGuiService(database or config["physicalDatabase"])
        elif launcher == "lanrack":
            from lanctl.apps.rack.service import RackService

            self._service = RackService(database or config["physicalDatabase"])
        elif launcher == "lanaccess":
            from lanctl.apps.access.gui_service import AccessGuiService

            self._service = AccessGuiService(
                database or config["database"], store or config["credentials"], cipher
            )
        else:
            from lanctl.apps.monitor.gui_service import MonitorGuiService

            self._service = MonitorGuiService()
        if previous is not None and launcher == "lanaccess":
            previous.lock()
        self._binding = binding

    def _respond(self, operation, action):
        try:
            with self._lock, project_operation():
                self._bind_service(load_config())
                result = operation() or {}
                return {"ok": True, **result}
        except Exception as exc:  # noqa: BLE001 - native RPC boundary, preserve real origin
            from lanctl.core.errors import errors

            event = errors.from_exception(
                exc,
                origin=f"LANCTL.{self._launcher}.GUI.{action}",
                code="LAUNCHER.GUI.FAILED",
                level=43,
                print_output=False,
            )
            return {
                "ok": False,
                "error": event.message,
                "errorId": event.error_id,
                "errorDetails": event.to_dict(),
            }

    def _require(self, launcher):
        if self._launcher != launcher:
            raise ValueError("Esta operación no pertenece a la aplicación abierta")

    def bootstrap(self):
        def operation():
            config = load_config()
            payload = self._service.snapshot()
            return {
                **payload,
                "launcher": self._launcher,
                "version": __version__,
                "project": config.get("activeProject") or "",
                "projectContext": project_identity(config),
                "projectActions": self._project_actions(),
                "projectName": Path(config["activeProject"]).stem
                if config.get("activeProject")
                else "Sin proyecto",
            }

        return self._respond(operation, "Read")

    def rack_appearance(self, expected, identifier, values):
        def apply():
            self._require("lanrack")
            return self._service.set_appearance(expected, identifier, values)

        return self._respond(apply, "Appearance")

    def rack_element(self, expected, operation, identifier, values):
        def apply():
            self._require("lanrack")
            return self._service.edit_element(expected, operation, identifier, values)

        return self._respond(apply, "Element")

    def rack_destinations(self, identifier, height):
        def query():
            self._require("lanrack")
            return self._service.destinations(identifier, height)

        return self._respond(query, "Destinations")

    def rack_dimensions(self, expected, identifier, values):
        def apply():
            self._require("lanrack")
            return self._service.set_dimensions(expected, identifier, values)

        return self._respond(apply, "Dimensions")

    def rack_create(self, values):
        def create():
            from lanctl.apps.wire.gui_service import WireGuiService

            self._require("lanrack")
            if not isinstance(values, dict):
                raise ValueError("Datos de armario no válidos")
            return WireGuiService(self._service.database.path).create({**values, "kind": "rack"})

        return self._respond(create, "CreateRack")

    def rack_organization(self, expected, operation, values):
        def apply():
            self._require("lanrack")
            return self._service.organize(expected, operation, values)

        return self._respond(apply, "Organization")

    def wire_create(self, values):
        def operation():
            self._require("lanwire")
            return self._service.create(values)

        return self._respond(operation, "Create")

    def wire_organization(self, expected, operation, values):
        def apply():
            from lanctl.apps.rack.organization import mutate
            from lanctl.core.projects.physical_mutations import physical_mutation

            self._require("lanwire")
            with physical_mutation(self._service.database.path):
                return mutate(self._service.database, expected, operation, values)

        return self._respond(apply, "Organization")

    def wire_update(self, identifier, revision, values):
        def operation():
            self._require("lanwire")
            return self._service.update(identifier, revision, values)

        return self._respond(operation, "Edit")

    def wire_connect(self, identifier, revision, endpoints):
        def operation():
            self._require("lanwire")
            return self._service.connect(identifier, revision, endpoints)

        return self._respond(operation, "Connect")

    def wire_port(self, identifier, revision, port, name, position):
        def operation():
            self._require("lanwire")
            return self._service.port(identifier, revision, port, name, position)

        return self._respond(operation, "Port")

    def wire_delete(self, identifier, revision):
        def operation():
            self._require("lanwire")
            return self._service.delete(identifier, revision)

        return self._respond(operation, "Delete")

    def access_unlock(self, password, confirmation=""):
        def operation():
            self._require("lanaccess")
            return self._service.unlock(password, confirmation)

        return self._respond(operation, "Unlock")

    def access_lock(self):
        def operation():
            self._require("lanaccess")
            return self._service.lock()

        return self._respond(operation, "Lock")

    def access_set(self, selector, protocol, username, password, confirmation):
        def operation():
            self._require("lanaccess")
            return self._service.set(selector, protocol, username, password, confirmation)

        return self._respond(operation, "CredentialSave")

    def access_delete(self, identifier):
        def operation():
            self._require("lanaccess")
            return self._service.delete(identifier)

        return self._respond(operation, "CredentialDelete")

    def access_update(self, identifier, expected, values):
        def operation():
            self._require("lanaccess")
            return self._service.update(identifier, expected, values)

        return self._respond(operation, "CredentialEdit")

    def access_open(self, identifier):
        def operation():
            self._require("lanaccess")
            return self._service.open(identifier)

        return self._respond(operation, "Open")

    def monitor_action(self, action):
        def operation():
            self._require("lanmon")
            return {"result": self._service.action(action)}

        return self._respond(operation, "MonitorAction")

    def monitor_samples(self, identifier):
        def operation():
            self._require("lanmon")
            return {"samples": self._service.samples(identifier)}

        return self._respond(operation, "Metrics")

    def monitor_incident(self, identifier, action):
        def operation():
            self._require("lanmon")
            return {"incident": self._service.incident(identifier, action)}

        return self._respond(operation, "Incident")

    def monitor_device(self, identifier):
        def operation():
            self._require("lanmon")
            return {"device": self._service.device_record(identifier)}

        return self._respond(operation, "DeviceRead")

    def monitor_update(self, identifier, expected, values):
        def operation():
            self._require("lanmon")
            return {"device": self._service.update_device(identifier, expected, values)}

        return self._respond(operation, "DeviceEdit")

    def monitor_group(self, identifier, expected, action, name):
        def operation():
            self._require("lanmon")
            return {"device": self._service.edit_group(identifier, expected, action, name)}

        return self._respond(operation, "DeviceGroup")

    def settings(self):
        return self._suite.launcher_settings(self._launcher)

    def projects(self):
        return self._respond(self._suite._desktop._projects_payload, "Projects")

    def select_project_file(self):
        return self._suite.select_project_file()

    def select_project_directory(self):
        return self._suite.select_project_directory()

    def use_project(self, path):
        def operation():
            self._require("lanwire")
            result = self._suite.use_project(path)
            if result.get("ok"):
                self._bind_service(load_config())
            return result

        return self._respond(operation, "ProjectSwitch")

    def save_setting(self, path, value):
        return self._suite.save_launcher_setting(self._launcher, path, value)

    def project_state(self):
        return self._suite._desktop.project_state()

    def save_project(self):
        return self._suite.save_project()

    def open_cli(self):
        return self._respond(
            lambda: open_system_cli(self._launcher) or {"message": "CLI abierto"}, "CLI"
        )

    def open_gui(self, launcher="lanctl"):
        def operation():
            if launcher not in {"lanctl", "lanwire", "lanrack", "lanmon"}:
                raise ValueError("Destino no permitido")
            subprocess.Popen(
                launcher_command(launcher, "--gui"),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                **process_options(context_launcher=launcher),
            )
            return {"message": launcher.upper() + " GUI abierta"}

        return self._respond(operation, "Launcher")

    def request_close(self):
        def operation():
            if self._launcher == "lanaccess":
                self._service.lock()
            self._closing = True
            self._window.destroy()
            return {"closed": True}

        return self._respond(operation, "Close")


def run_gui(launcher, **options):
    import webview

    from lanctl.apps.access.root_control import RootInterfaceAgent
    from lanctl.apps.suite.window_style import apply_dark_caption, webview_icon_path

    project = options.pop("project", None)
    if project:
        from lanctl.core.projects.workspace import activate_project_workspace

        activate_project_workspace(project)
    api = LauncherApi(launcher, **options)
    window = webview.create_window(
        launcher.upper() + " · LANCTL",
        bundled_path("gui/launcher.html").as_uri(),
        js_api=api,
        width=1100,
        height=780,
        min_size=(780, 560),
        background_color="#15181c",
    )
    api._window = window
    api._suite._desktop.attach_window(window)
    loaded = Event()
    window.events.loaded += loaded.set
    window.events.shown += lambda: apply_dark_caption(window, launcher)

    def closing():
        if api._closing or not loaded.is_set():
            return True
        Thread(target=lambda: window.evaluate_js("launcherClose()"), daemon=True).start()
        return False

    def remote_action(command):
        if not loaded.wait(10):
            raise TimeoutError("La GUI todavía no está disponible")
        if command.get("action") in {"data-changed", "refresh"}:
            window.evaluate_js("window.launcherDataChanged=true")
        elif command.get("action") == "view" and command.get("value") == "gui":
            window.restore()
            window.show()

    window.events.closing += closing
    agent = RootInterfaceAgent("gui", remote_action)
    window.events.loaded += agent.start
    try:
        webview.start(icon=webview_icon_path(launcher))
    finally:
        agent.stop()
        if launcher == "lanaccess":
            api._service.lock()
    return 0
