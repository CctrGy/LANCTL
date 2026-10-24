"""Orquestador principal de las aplicaciones de la suite."""

from __future__ import annotations

import argparse
import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.core.parser import (
    LANCTLArgumentParser,
    has_help_argument,
    normalize_help_arguments,
)
from lanctl.core.session import coordinated_launcher

_LAUNCHERS = {
    "lanip": ("ip", "Inventario lógico, descubrimiento, IP, MAC y servicios."),
    "lanwire": ("wire", "Cableado, puertos, paneles y topología física."),
    "lanrack": ("rack", "Salas técnicas, racks, unidades U y equipos."),
    "lanaccess": ("access", "Usuarios, credenciales y accesos remotos."),
    "lanmon": ("monitor", "Monitorización, eventos, incidencias e historial."),
}


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> LANCTLArgumentParser:
    parser = LANCTLArgumentParser(
        prog="LANCTL",
        description="Orquestador raíz de las aplicaciones de la suite LANCTL.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión común de la suite y termina.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", "-cli", action="store_true", help="Abre la consola principal.")
    mode.add_argument("-tui", "--tui", action="store_true", help="Abre el TUI principal.")
    mode.add_argument("--gui", action="store_true", help="Abre el centro gráfico de LANCTL.")
    links = parser.add_mutually_exclusive_group()
    for key, label in (("web", "la web"), ("github", "GitHub"), ("reference", "la referencia")):
        links.add_argument(
            f"-{key}", f"--{key}", action="store_true", help=f"Muestra y abre {label} oficial."
        )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Solicita UAC explícitamente para un launcher instalado en Windows.",
    )
    launchers = parser.add_subparsers(dest="launcher", metavar="LAUNCHER")
    for name, (alias, description) in _LAUNCHERS.items():
        child = launchers.add_parser(name, aliases=[alias], help=description, add_help=False)
        child.add_argument("arguments", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    for name in ("plugin", "settings", "language", "backend"):
        child = launchers.add_parser(
            name, help="Administración compartida de la suite.", add_help=False
        )
        child.add_argument("arguments", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    setup = launchers.add_parser(
        "setup-defaults",
        help="Inicializa preferencias de instalación sin sobrescribir las existentes.",
    )
    setup.add_argument(
        "--theme",
        choices=("graphite", "midnight", "forest", "violet", "light"),
        default="graphite",
        help="Tema inicial.",
    )
    setup.add_argument(
        "--plugins",
        default="all",
        help="all, none o IDs de plugins opcionales separados por comas.",
    )
    completions = launchers.add_parser(
        "completions", help="Registra o retira el completado Clink del usuario actual."
    )
    completions.add_argument("action", choices=("install", "uninstall"))
    post_install = launchers.add_parser(
        "post-install", help="Abre LANIP con el usuario normal al finalizar la instalación."
    )
    post_install.add_argument(
        "--first-scan",
        action="store_true",
        help="Prepara confirmación del rango; no inicia sondas.",
    )
    return parser


def _run_launcher(name: str, arguments: list[str]) -> int:
    canonical = (
        "lanmon"
        if name == "monitor"
        else f"lan{name}"
        if name in {"ip", "wire", "rack", "access"}
        else name
    )
    if canonical == "lanip":
        from lanctl.bootstrap.lanip import main as application
    elif canonical == "lanwire":
        from lanctl.apps.wire.cli.main import main as application
    elif canonical == "lanrack":
        from lanctl.apps.rack.cli import main as application
    elif canonical == "lanaccess":
        from lanctl.apps.access.manager_cli import main as application
    else:
        from lanctl.bootstrap.lanmon import main as application
    return application(arguments)


@coordinated_launcher("lanctl")
def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    if arguments and arguments[0] == "backend":
        from lanctl.core.coordination_cli import run

        return run(arguments[1:])
    if arguments and arguments[0] == "--admin" and not has_help_argument(arguments):
        from lanctl.core.errors import errors
        from lanctl.core.local_permissions import launch_elevated

        try:
            return launch_elevated(arguments[1:])
        except OSError as exc:
            errors.from_exception(
                exc, origin="LANCTL.Suite.Access.Elevate", code="SUITE.ELEVATION.DENIED", level=46
            )
            return 2
    if arguments and arguments[0] in {"plugin", "settings", "language"}:
        # Compatibility adapter; shared services remain the single source of state.
        from lanctl.bootstrap.lanip import main as ip_main

        return ip_main(arguments)
    if arguments and arguments[0] in {"setup-defaults", "completions", "post-install"}:
        import json

        args = build_parser().parse_args(arguments)
        try:
            if args.launcher == "setup-defaults":
                from lanctl.core.installation import initialize_defaults

                result = initialize_defaults(theme=args.theme, plugins=args.plugins)
            elif args.launcher == "completions":
                from lanctl.core.clink_integration import configure_clink

                result = configure_clink(args.action)
            else:
                from lanctl.core.first_scan import launch_installed_gui

                result = launch_installed_gui(first_scan=args.first_scan)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        except (OSError, ValueError) as exc:
            from lanctl.core.errors import errors

            errors.from_exception(
                exc,
                origin="LANCTL.Suite.Install.Configure",
                code="INSTALL.CONFIGURE.FAILED",
                level=43,
            )
            return 2
    launcher_names = {*_LAUNCHERS, "ip", "wire", "rack", "access", "monitor"}
    if has_help_argument(arguments):
        if arguments and arguments[0].casefold() in launcher_names:
            return _run_launcher(arguments[0].casefold(), arguments[1:])
        return build_parser().parse_args(arguments)
    if arguments and arguments[0].casefold() in launcher_names:
        return _run_launcher(arguments[0].casefold(), arguments[1:])
    if any(
        word in {"-web", "--web", "-github", "--github", "-reference", "--reference"}
        for word in arguments
    ):
        import webbrowser

        from lanctl.core.official_links import get_official_links, open_official_link

        parser = build_parser()
        args = parser.parse_args(arguments)
        if args.launcher or args.gui or args.cli or args.tui or args.admin:
            parser.error("usa el enlace oficial sin otros modos ni comandos")
        key = next(key for key in get_official_links() if getattr(args, key))
        # Plain complete URLs are clickable in capable terminals and remain useful
        # when redirected; no escape sequences or shell interpolation are needed.
        print(get_official_links()[key])
        try:
            open_official_link(key)
        except (OSError, webbrowser.Error) as exc:
            from lanctl.core.errors import errors

            errors.from_exception(
                exc, origin="LANCTL.Suite.Links.Open", code="SUITE.LINK.OPEN.FAILED", level=24
            )
            return 2
        return 0
    if not arguments or arguments[0] in {"--cli", "-cli", "--tui", "-tui", "--gui"}:
        from lanctl.apps.suite.interfaces import run_console

        args = build_parser().parse_args(arguments)
        if args.launcher:
            build_parser().error("usa lanctl LAUNCHER --cli o --tui")
        from lanctl.apps.access.settings_lifecycle import _recover_on_startup

        _recover_on_startup()
        if args.gui:
            from lanctl.apps.suite.gui import run_gui

            try:
                return run_gui()
            except (ImportError, OSError, RuntimeError) as exc:
                from lanctl.core.errors import errors

                errors.from_exception(
                    exc, origin="LANCTL.Suite.GUI.Start", code="SUITE.GUI.START.FAILED", level=43
                )
                return 2
        return run_console(tui=args.tui)
    parser = build_parser()
    parser.parse_args(arguments)
    parser.error("indica un launcher o utiliza --cli / --tui")
