"""Local, privileged first-account wizard for an installed Windows service."""

from __future__ import annotations

import ctypes
import os
import stat
import sys
from pathlib import Path
from threading import Event, RLock, Thread

from lanctl.apps.access.auth import AuthenticationService
from lanctl.apps.access.store import AccessStore
from lanctl.core.file_transaction import locked_file
from lanctl.core.local_permissions import require_admin


def _program_data():
    # Ask Windows rather than accepting an inherited environment override.
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    query = shell.SHGetFolderPathW
    query.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_wchar_p,
    ]
    query.restype = ctypes.c_long
    buffer = ctypes.create_unicode_buffer(260)
    if query(None, 0x0023, None, 0, buffer) != 0 or not buffer.value:
        raise OSError("Windows no pudo resolver el directorio de datos del servicio")
    return Path(buffer.value)


def _reject_redirected_paths(paths):
    for path in paths:
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
        ):
            raise ValueError("El asistente no admite rutas de servicio redirigidas")


def _installed_store_path():
    require_admin()
    from lanctl.core.config import CONFIG_PATH, load_config
    from lanctl.core.paths import is_portable_install

    if os.name != "nt" or not getattr(sys, "frozen", False) or is_portable_install():
        raise ValueError("Este asistente requiere LANCTL instalado en Windows")
    root = _program_data() / "LANCTL"
    target = root / "access" / "users.dc"
    _reject_redirected_paths(
        [
            root,
            root / "config",
            root / "config/config.json",
            target.parent,
            target,
            target.with_name("users.json"),
            target.with_name("users.dc.lock"),
        ]
    )
    if not target.parent.is_dir():
        raise ValueError("Ejecuta Setup para preparar el directorio protegido del servicio")
    if CONFIG_PATH.resolve() != (root / "config/config.json").resolve():
        raise ValueError(
            "La configuración personalizada requiere el administrador de acceso existente"
        )
    configured = str(load_config()["accessUsers"]).replace("\\", "/")
    if configured not in {"data/lc/access/users.dc", "data/lc/access/users.json"} and (
        not Path(configured).is_absolute() or Path(configured).resolve() != target.resolve()
    ):
        raise ValueError("El almacén personalizado requiere el administrador de acceso existente")
    if os.environ.get("LANCTL_SECRET_DIR") or os.environ.get("LANCTL_DATA_DIR"):
        raise ValueError("El asistente requiere las rutas de servicio de la instalación")
    return target


class InitialRemoteAccount:
    """Never expose this service as a remote endpoint or grant OS privileges."""

    def __init__(self, path):
        self.path = Path(path)

    def status(self):
        require_admin()
        with locked_file(self.path):
            has_users = bool(AccessStore(self.path).users())
        return {
            "scope": "service",
            "storage": str(self.path),
            "hasUsers": has_users,
            "canCreate": not has_users,
            "roleLabel": "Administrador de LANACCESS",
            "message": "Ya existen cuentas; se conservan sin cambios."
            if has_users
            else "Crea la primera cuenta remota del servicio. Este paso no activa SSH ni HTTPS.",
        }

    def create(self, username, password, confirmation):
        require_admin()
        if not isinstance(username, str) or not 3 <= len(username.strip()) <= 64:
            raise ValueError("Indica un usuario remoto de entre 3 y 64 caracteres")
        if not isinstance(password, str) or not 12 <= len(password) <= 1024:
            raise ValueError("La contraseña debe tener entre 12 y 1024 caracteres")
        if not isinstance(confirmation, str) or password != confirmation:
            raise ValueError("Las contraseñas no coinciden")
        with locked_file(self.path):
            store = AccessStore(self.path)
            if store.users():
                raise ValueError(
                    "Ya existen cuentas; usa el administrador de acceso para modificarlas"
                )
            user = AuthenticationService(store).add_user(
                username, roles=("administrator",), password=password
            )
        return {
            "created": True,
            "username": user.username,
            "scope": "service",
            "message": "Cuenta creada. Configura el acceso remoto antes de habilitar SSH o HTTPS.",
        }


class _InstalledRemoteAccount:
    """Resolve scope on each RPC so setup errors remain visible in the wizard."""

    def status(self):
        return InitialRemoteAccount(_installed_store_path()).status()

    def create(self, username, password, confirmation):
        return InitialRemoteAccount(_installed_store_path()).create(
            username, password, confirmation
        )


class RemoteSetupApi:
    def __init__(self, service):
        self._service = service
        self._window = None
        self._lock = RLock()
        self._closing = False

    def _respond(self, operation, action):
        try:
            with self._lock:
                if self._closing:
                    raise ValueError("El asistente ya se está cerrando")
                return {"ok": True, **operation()}
        except Exception as exc:  # noqa: BLE001 - local RPC boundary retains error origin
            from lanctl.core.errors import errors

            event = errors.from_exception(
                exc,
                origin=f"LANCTL.Access.Setup.{action}",
                code="ACCESS.SETUP.FAILED",
                level=43,
                print_output=False,
            )
            return {
                "ok": False,
                "error": event.message,
                "message": event.message,
                "errorId": event.error_id,
            }

    def setup_status(self):
        return self._respond(self._service.status, "Read")

    def create_initial_user(self, username, password, confirmation):
        return self._respond(
            lambda: self._service.create(username, password, confirmation), "Create"
        )

    def request_close(self):
        with self._lock:
            self._closing = True
            if self._window is not None:
                self._window.destroy()
        return {"ok": True, "closed": True}


def run_remote_setup():
    import webview

    from lanctl.apps.suite.window_style import webview_icon_path
    from lanctl.core.resources import bundled_path

    api = RemoteSetupApi(_InstalledRemoteAccount())
    api._window = webview.create_window(
        "LANACCESS · Cuenta remota inicial",
        bundled_path("gui/remote-setup.html").as_uri(),
        js_api=api,
        width=760,
        height=680,
        min_size=(640, 600),
        background_color="#15181c",
    )
    loaded = Event()
    api._window.events.loaded += loaded.set

    def closing():
        if api._closing or not loaded.is_set():
            return True
        Thread(
            target=lambda: api._window.evaluate_js("window.remoteSetupClose()"), daemon=True
        ).start()
        return False

    api._window.events.closing += closing
    webview.start(icon=webview_icon_path("lanaccess"))
    return 0
