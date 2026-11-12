"""Authenticated web adapters for the same GUI APIs used by native launchers."""

from __future__ import annotations

import inspect
import os
import time
from collections import OrderedDict
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit

from lanctl.core.config import load_config
from lanctl.core.gui_preferences import preferences_payload
from lanctl.core.paths import data_root
from lanctl.core.project_context import project_operation, require_project
from lanctl.shared.i18n import initialize_language, t

PAGES = {
    "panel": "lanctl",
    "ip": "lanip",
    "wire": "lanwire",
    "access": "lanaccess",
    "rack": "lanrack",
    "mon": "lanmon",
}
PAGE_PERMISSION = {"access": "device.connect", "mon": "monitor.read"}
READ = "inventory.read"
COMMON = {
    "bootstrap": READ,
    "project_state": READ,
    "projects": READ,
    "list_projects": READ,
    "project_defaults": READ,
    "gui_preferences": READ,
    "project_selection": READ,
    "sync_project": READ,
    "use_project": "project.manage",
    "create_project": "project.manage",
    "save_project": "project.manage",
    "save_gui_preferences": "system.configure",
    "settings": "system.configure",
    "get_settings": "system.configure",
    "settings_catalog": "system.configure",
    "launcher_settings": "system.configure",
    "save_catalog_setting": "system.configure",
    "save_catalog_settings": "system.configure",
    "save_launcher_setting": "system.configure",
    "save_setting": "system.configure",
}
METHODS = {
    "panel": {
        "runtime_status": "monitor.read",
        "project_metadata": "project.manage",
        "save_project_metadata": "project.manage",
        "plugin_settings": "system.configure",
        "save_plugin_settings": "system.configure",
        "set_plugin_enabled": "system.configure",
    },
    "ip": {
        "list_devices": READ,
        "get_device": READ,
        "device_record": READ,
        "get_history": "history.read",
        "monitor_data": "monitor.read",
        "scan_network": "scan.run",
        "scan_status": "scan.run",
        "scan_targets": "scan.run",
        "cancel_scan": "scan.run",
        "first_scan_options": READ,
        "dismiss_first_scan": "scan.run",
        "diagnose_device": "scan.run",
        "get_device_details": "scan.run",
        "wake_device": "wol.send",
        "create_device": "system.configure",
        "update_device": "system.configure",
        "delete_device": "system.destructive",
        "undo_edit": "system.configure",
        "redo_edit": "system.configure",
        "create_group": "system.configure",
        "group_action": "system.configure",
    },
    "wire": {
        "wire_create": "system.configure",
        "wire_diagram": "system.configure",
        "wire_organization": "system.configure",
        "wire_update": "system.configure",
        "wire_connect": "system.configure",
        "wire_port": "system.configure",
        "wire_delete": "system.destructive",
    },
    "rack": {
        "rack_appearance": "system.configure",
        "rack_element": "system.configure",
        "rack_destinations": READ,
        "rack_dimensions": "system.configure",
        "rack_create": "system.configure",
        "rack_organization": "system.configure",
    },
    "access": {
        "access_unlock": "device.connect",
        "access_lock": "device.connect",
        "access_set": "device.connect",
        "access_update": "device.connect",
        "access_delete": "system.destructive",
    },
    "mon": {
        "monitor_action": "monitor.control",
        "monitor_samples": "monitor.read",
        "monitor_incident": "monitor.control",
        "monitor_device": "monitor.read",
        "monitor_update": "system.configure",
        "monitor_group": "system.configure",
    },
}
PROJECT_METHODS = frozenset(
    {
        "use_project",
        "create_project",
        "save_project",
        "save_project_metadata",
        "scan_network",
        "diagnose_device",
        "get_device_details",
        "wake_device",
        "create_device",
        "update_device",
        "delete_device",
        "undo_edit",
        "redo_edit",
        "create_group",
        "group_action",
        "save_catalog_setting",
        "save_catalog_settings",
        "save_launcher_setting",
        "save_setting",
        *METHODS["wire"],
        *METHODS["rack"],
        *METHODS["access"],
        *METHODS["mon"],
    }
)


def presentation():
    return {
        "ok": True,
        "languageCatalog": initialize_language().presentation_payload(),
        **preferences_payload(),
    }


class WebSuiteGateway:
    """Explicit allowlists and session-local GUI state, including vault unlock state."""

    def __init__(self, authorization, factory=None):
        self.authorization = authorization
        self.factory = factory or self._factory
        self._sessions = OrderedDict()
        self._lock = RLock()

    @staticmethod
    def _factory(page):
        if page == "panel":
            from lanctl.apps.suite.gui import SuiteApi

            return SuiteApi()
        if page == "ip":
            from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi

            return DesktopApi()
        from lanctl.apps.suite.launcher_gui import LauncherApi

        return LauncherApi(PAGES[page])

    def forget(self, session):
        with self._lock:
            self._sessions.pop(session, None)

    def _api(self, session, user, page):
        now = time.monotonic()
        with self._lock:
            for key in list(self._sessions):
                if now - self._sessions[key]["seen"] > 1800:
                    self._sessions.pop(key)
            record = self._sessions.setdefault(
                session, {"user": user.userId, "seen": now, "apis": {}}
            )
            if record["user"] != user.userId:
                raise PermissionError(t("LANCTL.WEB.DENIED"))
            record["seen"] = now
            self._sessions.move_to_end(session)
            while len(self._sessions) > 64:
                self._sessions.popitem(last=False)
            if page not in record["apis"]:
                record["apis"][page] = self.factory(page)
            return record["apis"][page]

    def capabilities(self, user, page, api):
        allowed = self.authorization.permissions(user)
        return sorted(
            method
            for method, permission in {**COMMON, **METHODS[page]}.items()
            if permission in allowed and callable(getattr(api, method, None))
        )

    @staticmethod
    def _projects(result):
        if not isinstance(result, dict) or "projects" not in result:
            return result
        from lanctl.core.projects import inspect_project

        directory = Path(load_config().get("projectsDirectory") or data_root() / "projects")
        projects = {item["path"]: item for item in result["projects"]}
        for path in sorted(directory.glob("*.vlf")):
            try:
                info = inspect_project(path)
                projects[str(path)] = {
                    "path": str(path),
                    "name": info.get("name") or path.stem,
                    "id": info.get("id", ""),
                }
            except (OSError, ValueError) as error:
                from lanctl.core.errors import errors

                errors.from_exception(
                    error,
                    origin="LANCTL.Access.Web.Projects.Discover",
                    code="ACCESS.WEB.PROJECT.INVALID",
                    level=23,
                    print_output=False,
                )
        return {
            **result,
            "projects": sorted(projects.values(), key=lambda item: item["name"].casefold()),
        }

    @staticmethod
    def services():
        """Deployment-owned links; never infer a web port from a VPN socket."""
        services = []
        for identifier, name in (
            ("hardware", "Hardware"),
            ("dns", "DNS"),
            ("vpn", "WireGuard VPN"),
        ):
            url = os.environ.get("LANCTL_WEB_" + identifier.upper() + "_URL", "").strip()
            if url:
                parsed = urlsplit(url)
                if (
                    parsed.scheme not in {"http", "https"}
                    or not parsed.hostname
                    or parsed.username is not None
                    or parsed.password is not None
                    or any(character.isspace() for character in url)
                ):
                    raise ValueError(t("LANCTL.WEB.INVALID_REQUEST"))
                _ = parsed.port
            services.append({"id": identifier, "name": name, "url": url})
        return services

    def shell(self, user, session):
        self.authorization.require(user, READ)
        api = self._api(session, user, "panel")
        result = self._projects(api.bootstrap())
        allowed = self.authorization.permissions(user)
        return {
            **result,
            **presentation(),
            "username": user.username,
            "services": self.services(),
            "pages": [page for page in PAGES if PAGE_PERMISSION.get(page, READ) in allowed],
            "permissions": sorted(allowed),
        }

    @staticmethod
    def _check_settings(method, args):
        from lanctl.core.settings_policy import SettingsContext, restriction

        scope, paths = "program", []
        if method == "save_catalog_settings":
            if not args or not isinstance(args[0], dict):
                raise ValueError(t("LANCTL.WEB.INVALID_REQUEST"))
            paths = list(args[0])
        elif method == "save_catalog_setting":
            scope, paths = args[0], [args[1]]
        elif method == "save_launcher_setting":
            paths = [args[1]]
        elif method == "save_setting":
            paths = [args[0]]
        for path in paths:
            if not isinstance(path, str) or not isinstance(scope, str):
                raise ValueError(t("LANCTL.WEB.INVALID_REQUEST"))
            reason = restriction(SettingsContext(scope=scope, interface="remote"), path)
            if reason:
                raise PermissionError(reason)

    def call(self, user, session, page, method, args, expected=None):
        if (
            not isinstance(page, str)
            or page not in PAGES
            or not isinstance(method, str)
            or not isinstance(args, list)
            or len(args) > 8
        ):
            raise ValueError(t("LANCTL.WEB.INVALID_REQUEST"))
        self.authorization.require(user, PAGE_PERMISSION.get(page, READ))
        if method == "project_call":
            if len(args) != 3:
                raise ValueError(t("LANCTL.WEB.INVALID_REQUEST"))
            expected, method, args = args
            if not isinstance(method, str) or not isinstance(args, list) or len(args) > 8:
                raise ValueError(t("LANCTL.WEB.INVALID_REQUEST"))
        permission = {**COMMON, **METHODS[page]}.get(method)
        if permission is None:
            raise PermissionError(t("LANCTL.WEB.DENIED"))
        self.authorization.require(user, permission)
        if (
            method in {"rack_element", "wire_organization", "rack_organization"}
            and len(args) > 1
            and args[1] == "delete"
        ):
            self.authorization.require(user, "system.destructive")
        api = self._api(session, user, page)
        target = getattr(api, method, None)
        if not callable(target):
            raise PermissionError(t("LANCTL.WEB.DENIED"))
        try:
            inspect.signature(target).bind(*args)
        except TypeError as error:
            raise ValueError(t("LANCTL.WEB.INVALID_REQUEST")) from error
        self._check_settings(method, args)
        with api._lock, project_operation():
            if method in PROJECT_METHODS:
                require_project(expected)
            if method in {"use_project", "project_metadata", "save_project_metadata"}:
                path = args[0] if args else None
                choices = self._projects(self._api(session, user, "panel").bootstrap()).get(
                    "projects", []
                )
                if path not in {item["path"] for item in choices}:
                    raise PermissionError(t("LANCTL.WEB.PROJECT_PATH"))
            if method == "project_defaults":
                config = load_config()
                directory = config.get("projectsDirectory") or str(data_root() / "projects")
                return {
                    "ok": True,
                    "directory": directory,
                    "configuredDirectory": directory,
                    "lan": "LAN",
                }
            if method == "create_project":
                directory = Path(
                    load_config().get("projectsDirectory") or data_root() / "projects"
                ).resolve()
                if len(args) > 1 and args[1] and Path(args[1]).resolve() != directory:
                    raise PermissionError(t("LANCTL.WEB.PROJECT_PATH"))
                directory.mkdir(parents=True, exist_ok=True)
                args = list(args)
                if len(args) < 2:
                    args.append(str(directory))
                else:
                    args[1] = str(directory)
            result = target(*args)
        result = self._projects(result)
        if method == "bootstrap" and result.get("ok"):
            result = {
                **result,
                **presentation(),
                "remote": True,
                "webMethods": self.capabilities(user, page, api),
                "projectActions": [
                    item
                    for item in result.get("projectActions", [])
                    if item in self.capabilities(user, page, api)
                ],
            }
        return result
