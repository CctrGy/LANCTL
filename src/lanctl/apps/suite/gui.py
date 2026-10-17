"""Local-only desktop entry point for the suite's shared administration."""

from __future__ import annotations

import platform
import subprocess
import sys
from threading import Event, RLock, Thread

from lanctl import __version__
from lanctl.apps.suite.gui_support import GuiSupportMixin
from lanctl.apps.suite.processes import (
    EmbeddedCli,
    launcher_command,
    open_system_cli,
    process_options,
)
from lanctl.core.config import load_config
from lanctl.core.plugins.manager import get_plugin_manager
from lanctl.core.plugins.settings import PluginSettings
from lanctl.core.resources import bundled_path


class SuiteApi(GuiSupportMixin):
    def __init__(self):
        # Compatibility adapter until shared desktop project/settings UI moves out of LANIP.
        # Only explicitly forwarded methods are exported through this WebView.
        from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi

        self._desktop = DesktopApi()
        self._cli = EmbeddedCli()
        self._lock = RLock()

    def _respond(self, action, operation):
        try:
            with self._lock:
                return {"ok": True, **operation()}
        except Exception as exc:  # noqa: BLE001 - local desktop RPC boundary
            from lanctl.core.errors import errors

            event = errors.from_exception(
                exc,
                origin=f"LANCTL.Suite.GUI.{action}",
                code="SUITE.GUI.FAILED",
                level=43,
                print_output=False,
            )
            return {
                "ok": False,
                "error": event.message,
                "errorId": event.error_id,
                "errorDetails": event.to_dict(),
            }

    def bootstrap(self):
        def operation():
            from lanctl.core.coordination import Coordinator

            return {
                "version": __version__,
                "system": platform.system(),
                "architecture": platform.machine(),
                "sessions": Coordinator().sessions(),
                **self._desktop._projects_payload(),
                **self._plugin_payload(),
            }

        return self._respond("Bootstrap", operation)

    def runtime_status(self):
        from lanctl.core.coordination import Coordinator

        return self._respond("RuntimeStatus", lambda: {"sessions": Coordinator().sessions()})

    def _plugin_payload(self):
        manager = get_plugin_manager()
        return {
            "plugins": [
                {
                    "id": p.manifest.plugin_id,
                    "name": p.manifest.name,
                    "description": p.manifest.description,
                    "version": p.manifest.version,
                    "author": p.manifest.author,
                    "minimumLanctl": p.manifest.minimum_lanctl,
                    "maximumLanctl": p.manifest.maximum_lanctl,
                    "capabilities": list(p.manifest.capabilities),
                    "signature": p.signature,
                    "state": p.state.value,
                    "permissions": list(p.manifest.permissions),
                    "granted": sorted(p.granted),
                    "trusted": p.trusted,
                    "runtime": p.manifest.runtime,
                    "error": p.error,
                    "publisherTrusted": manager.publishers.is_trusted(p.signature),
                    **self._configuration_status(p),
                }
                for p in manager.list()
            ]
        }

    @staticmethod
    def _configuration_status(plugin):
        try:
            return {"hasSettings": bool(PluginSettings(plugin).fields()), "settingsError": ""}
        except (OSError, ValueError, TypeError, KeyError) as exc:
            from lanctl.core.errors import errors

            errors.from_exception(
                exc,
                origin="LANCTL.Suite.GUI.PluginSettingsRead",
                code="SUITE.GUI.PLUGIN_SETTINGS.INVALID",
                level=34,
                print_output=False,
            )
            return {"hasSettings": False, "settingsError": str(exc)}

    def trust_plugin_publisher(self, plugin_id):
        def operation():
            import webview

            from lanctl.core.plugins.package import verify_package

            manager = get_plugin_manager()
            plugin = manager.get(plugin_id)
            if self._desktop._window is None:
                raise RuntimeError("No hay ventana disponible para seleccionar el LCP firmado")
            selected = self._desktop._window.create_file_dialog(
                webview.OPEN_DIALOG, allow_multiple=False, file_types=("Plugin firmado (*.lcp)",)
            )
            if not selected:
                return {"cancelled": True}
            result = verify_package(selected[0])
            if (
                result["manifest"].plugin_id != plugin_id
                or result["checksum"] != plugin.checksum
                or result["signature"] != plugin.signature
            ):
                raise ValueError("Selecciona el LCP firmado que corresponde a la versión instalada")
            manager.publishers.trust_package(selected[0])
            manager.audit(plugin_id, "PUBLISHER TRUST", plugin.signature, "OK")
            return self._plugin_payload()

        return self._respond("PublisherTrust", operation)

    def install_signed_plugin(self, plugin_id):
        def operation():
            import webview

            from lanctl.core.plugins.package import verify_package

            manager = get_plugin_manager()
            manager.get(plugin_id)
            if self._desktop._window is None:
                raise RuntimeError("No hay ventana disponible para seleccionar el LCP firmado")
            selected = self._desktop._window.create_file_dialog(
                webview.OPEN_DIALOG, allow_multiple=False, file_types=("Plugin firmado (*.lcp)",)
            )
            if not selected:
                return {"cancelled": True}
            result = verify_package(selected[0])
            if result["manifest"].plugin_id != plugin_id:
                raise ValueError("El paquete no corresponde al plugin seleccionado")
            if not result["signature"].startswith("VALID_ED25519:"):
                raise ValueError("El paquete necesita una firma Ed25519 válida")
            manager.install(selected[0])
            return self._plugin_payload()

        return self._respond("PluginSignedInstall", operation)

    def create_project(self, name, directory="", metadata=None):
        # The existing adapter writes/validates a real VLF before returning success.
        with self._lock:
            return self._desktop.create_project(name, directory, metadata=metadata)

    def project_metadata(self, path):
        from lanctl.core.projects.metadata import read_metadata

        return self._respond("ProjectMetadataRead", lambda: read_metadata(path))

    def save_project_metadata(self, path, values, revision):
        def operation():
            from lanctl.core.projects.metadata import update_metadata

            update_metadata(path, values, revision)
            return {
                **self._desktop._projects_payload(),
                "message": "Metadatos del proyecto guardados.",
            }

        return self._respond("ProjectMetadataSave", operation)

    def project_state(self):
        return self._desktop.project_state()

    def request_close(self):
        return self._desktop.request_close("save")

    def use_project(self, path):
        with self._lock:
            return self._desktop.use_project(path)

    def save_project(self):
        with self._lock:
            return self._desktop.save_project()

    def select_project_file(self):
        return self._desktop.select_project_file()

    def select_project_directory(self):
        return self._desktop.select_project_directory()

    def get_settings(self):
        return self._desktop.get_settings()

    def project_defaults(self):
        def operation():
            from lanctl.core.projects.paths import resolve_project_path

            return {
                "directory": str(
                    resolve_project_path(
                        "Nuevo proyecto.vlf", load_config().get("projectsDirectory")
                    ).parent
                ),
                "lan": "LAN principal",
            }

        return self._respond("ProjectDefaults", operation)

    def settings_catalog(self, scope="program"):
        def operation():
            # Compatibility adapter: preserves the CLI service validation and
            # remote backend side effects until this adapter moves to core.
            from lanctl.apps.ip.interfaces.cli.commands.settings_menu import _entries
            from lanctl.core.settings_catalog import CATEGORIES

            if scope not in {"program", "project"}:
                raise ValueError("Ámbito de configuración desconocido")
            return {
                "entries": _entries(scope),
                "categories": {
                    **CATEGORIES,
                    "identity": "Identidad del proyecto",
                    "lan": "Identidad LAN",
                    "vlan": "VLAN del proyecto",
                },
            }

        return self._respond("SettingsCatalog", operation)

    def save_catalog_setting(self, scope, path, value):
        def operation():
            import json

            from lanctl.apps.ip.interfaces.cli.commands.settings_menu import _set

            if scope not in {"program", "project"}:
                raise ValueError("Ámbito de configuración desconocido")
            _set(scope, path, json.dumps(value, ensure_ascii=False))
            return {"message": "Configuración guardada"}

        return self._respond("SettingsCatalogSave", operation)

    @staticmethod
    def _launcher_categories(launcher):
        return {
            "lanip": ("ip", "network", "wol"),
            "lanwire": ("projects", "storage"),
            "lanrack": ("projects", "storage"),
            "lanaccess": ("access", "storage"),
            "lanmon": ("monitor", "logging"),
        }[launcher]

    def launcher_settings(self, launcher):
        def operation():
            from lanctl.apps.ip.interfaces.cli.commands.settings_menu import _entries
            from lanctl.core.settings_catalog import CATEGORIES

            categories = self._launcher_categories(launcher)
            entries = [e for e in _entries("program") if e["category"] in categories]
            return {"entries": entries, "categories": CATEGORIES}

        return self._respond("LauncherSettings", operation)

    def save_launcher_setting(self, launcher, path, value):
        def operation():
            import json

            from lanctl.apps.ip.interfaces.cli.commands.settings_menu import _set

            if path.split(".")[0] not in self._launcher_categories(launcher):
                raise ValueError("El ajuste no pertenece a este launcher")
            _set("program", path, json.dumps(value, ensure_ascii=False))
            return {"message": "Configuración guardada"}

        return self._respond("LauncherSettingSave", operation)

    def save_settings(self, values):
        with self._lock:
            return self._desktop.save_settings(values)

    def plugin_settings(self, plugin_id):
        def operation():
            plugin = get_plugin_manager().get(plugin_id)
            settings = PluginSettings(plugin)
            return {"fields": settings.fields(), "values": settings.load()}

        return self._respond("PluginSettingsRead", operation)

    def save_plugin_settings(self, plugin_id, values):
        def operation():
            plugin = get_plugin_manager().get(plugin_id)
            PluginSettings(plugin).save(values)
            return {"message": "Opciones guardadas; se aplicarán al próximo inicio del plugin."}

        return self._respond("PluginSettingsSave", operation)

    def set_plugin_enabled(self, plugin_id, enabled, grants=None, trusted=False):
        def operation():
            if type(enabled) is not bool or type(trusted) is not bool:
                raise ValueError("estado de plugin no válido")
            manager = get_plugin_manager()
            plugin = manager.get(plugin_id)
            if enabled:
                if grants is not None and (
                    not isinstance(grants, list)
                    or not all(isinstance(item, str) for item in grants)
                    or set(grants) - set(plugin.manifest.permissions)
                ):
                    raise ValueError("permisos de plugin no válidos")
                manager.enable(
                    plugin_id, grant=None if grants is None else set(grants), trusted=trusted
                )
            else:
                manager.disable(plugin_id)
            return self._plugin_payload()

        return self._respond("PluginActivation", operation)

    def open_cli(self):
        return self._respond(
            "ExternalCLI",
            lambda: open_system_cli() or {"message": "CLI abierto en la terminal del sistema."},
        )

    def start_terminal(self):
        return self._respond("TerminalStart", lambda: self._cli.start() or {})

    def terminal_send(self, line):
        return self._respond("TerminalInput", lambda: self._cli.send(line) or {})

    def terminal_output(self):
        return self._respond("TerminalOutput", self._cli.output)

    def launch_gui(self, launcher):
        def operation():
            # Launch only registered graphical applications.
            if launcher not in {"lanip", "lanwire", "lanrack", "lanaccess", "lanmon"}:
                raise ValueError("Este launcher todavía no dispone de interfaz GUI.")
            config = load_config()
            arguments = ["--gui"]
            if launcher == "lanip" and config.get("activeProject"):
                arguments.extend(["-project", config["activeProject"]])
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.Popen(
                launcher_command(launcher, *arguments),
                creationflags=flags,
                **process_options(context_launcher=launcher),
            )
            from lanctl.core.coordination import Coordinator
            from lanctl.core.gui_instance import focus_gui

            focus_gui(Coordinator(), launcher)
            close = config.get("closeGuiOnLaunch") is True
            if close and self._desktop._window is not None:
                self.record_activity(f"GUI de {launcher.upper()} abierta.")
                self._desktop._closing = True
                self._desktop._window.destroy()
            return {"message": f"GUI de {launcher.upper()} abierta.", "closed": close}

        return self._respond("Launcher", operation)


def run_gui():
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError('Instala la interfaz gráfica con: pip install -e ".[gui]"') from exc
    api = SuiteApi()
    window = webview.create_window(
        "LANCTL · Network Control Suite",
        bundled_path("gui/suite.html").as_uri(),
        js_api=api,
        width=790,
        height=570,
        min_size=(660, 460),
        background_color="#15181c",
    )
    api._desktop.attach_window(window)
    loaded = Event()
    window.events.loaded += loaded.set

    def closing():
        if api._desktop._closing or not loaded.is_set():
            return True
        Thread(target=lambda: window.evaluate_js("suiteClose()"), daemon=True).start()
        return False

    window.events.closing += closing
    from lanctl.apps.suite.window_style import apply_dark_caption, webview_icon_path

    window.events.shown += lambda: apply_dark_caption(window)
    from lanctl.apps.access.root_control import RootInterfaceAgent
    from lanctl.core.session import current_session

    def remote_action(command):
        if not loaded.wait(10):
            raise TimeoutError("La interfaz LANCTL todavía no está disponible")
        if command.get("action") in {"data-changed", "refresh"}:
            window.evaluate_js("window.suiteDataChanged = true")
        elif command.get("action") == "view" and command.get("value") == "gui":
            window.restore()
            window.show()

    def observe(event):
        if loaded.is_set():
            window.evaluate_js("window.suiteDataChanged = true")

    agent = RootInterfaceAgent("gui", remote_action)
    window.events.loaded += agent.start
    session = current_session()
    if session:
        session.subscribers.append(observe)
    try:
        webview.start(icon=webview_icon_path("lanctl"))
    finally:
        agent.stop()
        if session:
            session.subscribers.remove(observe)
        api._cli.close()
    return 0
