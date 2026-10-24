"""Windowed Windows host; console launchers keep their existing contracts."""

from __future__ import annotations

import importlib
import sys

_APPLICATIONS = {
    "lanctl": "lanctl.bootstrap.lanctl",
    "lanip": "lanctl.bootstrap.lanip",
    "lanwire": "lanctl.apps.wire.cli.main",
    "lanrack": "lanctl.apps.rack.cli",
    "lanaccess": "lanctl.apps.access.manager_cli",
    "lanmon": "lanctl.bootstrap.lanmon",
}


def _notify_failure(message):
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, "LANCTL: no se pudo abrir la GUI", 0x10)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    launcher = arguments.pop(0).casefold() if arguments else "lanctl"
    try:
        if launcher not in _APPLICATIONS:
            raise ValueError("Launcher gráfico no válido")
        if arguments and not (launcher == "lanip" and arguments == ["--first-scan"]):
            raise ValueError("El host gráfico solo admite un launcher y --first-scan para LANIP")
        application = importlib.import_module(_APPLICATIONS[launcher])
        result = application.main(["--gui", *arguments])
        if result:
            _notify_failure(
                f"{launcher.upper()} no pudo abrirse (código {result}). "
                "Consulta los registros de LANCTL en LANMON para ver el origen del error."
            )
        return int(result or 0)
    except Exception as error:  # noqa: BLE001 - no console in this bootstrap boundary
        from lanctl.core.errors import errors

        event = errors.from_exception(
            error,
            origin="LANCTL.GUI.Bootstrap.Start",
            code="GUI.BOOTSTRAP.FAILED",
            print_output=False,
        )
        _notify_failure(f"No se pudo iniciar la GUI. {event.message}\nID: {event.error_id}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
