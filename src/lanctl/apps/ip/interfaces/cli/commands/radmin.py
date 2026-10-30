from __future__ import annotations

import argparse
import json

from lanctl.apps.ip.infrastructure.protocols.radmin import (
    COLOR_DEPTHS,
    DEFAULT_PORT,
    MODES,
    find_viewer,
    tcp_probe,
    validate_mode,
    validate_port,
)
from lanctl.apps.ip.interfaces.cli.commands.open import run_open
from lanctl.core.config import load_config
from lanctl.core.database import DeviceDatabase
from lanctl.shared.i18n import t


def register_radmin_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "radmin", help=t("LANCTL.UI.HELP.CONFIGURE_CHECK_OR_OPEN_RADMIN_VIEWER")
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.ELEMENT_IP_MAC_OR_ALIAS"))
    command.add_argument("action", choices=("probe", "configure", "open"))
    command.add_argument("--mode", choices=MODES)
    command.add_argument("--port", type=int)
    command.add_argument(
        "--executable", help=t("LANCTL.UI.HELP.PER_DEVICE_PATH_USE_AUTO_FOR_AUTOMATIC_DETECTION")
    )
    command.add_argument("--through", help=t("LANCTL.UI.HELP.INTERMEDIATE_SERVER_HOST_PORT"))
    command.add_argument(
        "--fullscreen",
        action="store_true",
        help=t("LANCTL.UI.HELP.OPEN_FULL_SCREEN_CONTROL_OR_VIEW"),
    )
    command.add_argument(
        "--color-depth",
        type=int,
        choices=COLOR_DEPTHS,
        help=t("LANCTL.UI.HELP.RADMIN_COLOR_DEPTH_1_2_4_8_16_OR_24_BITS"),
    )
    command.add_argument(
        "--updates",
        type=int,
        help=t("LANCTL.UI.HELP.MAXIMUM_SCREEN_UPDATES_PER_SECOND_1_120"),
    )
    command.add_argument("--phonebook", help=t("LANCTL.UI.HELP.RADMIN_MANAGED_RPB_PHONEBOOK"))
    command.add_argument(
        "--phonebook-id",
        type=int,
        help=t("LANCTL.UI.HELP.ENTRY_IDENTIFIER_WITHIN_THE_RADMIN_PHONEBOOK"),
    )
    command.add_argument("--database", default=config["database"])
    command.add_argument("--store", default=config["credentials"])
    for parser_action in command._actions:
        if parser_action.help is None:
            parser_action.help = "Opción de configuración de Radmin Viewer."
    command.set_defaults(handler=run_radmin)


def run_radmin(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    device = database.resolve(args.selector)
    from lanctl.apps.ip.domain.discovery import require_real_target

    require_real_target(device)
    options = dict(device.protocol_options.get("radmin", {}))
    if args.action == "configure":
        options["port"] = validate_port(
            args.port if args.port is not None else options.get("port", DEFAULT_PORT)
        )
        options["mode"] = validate_mode(args.mode or options.get("mode", "control"))
        if args.executable is not None:
            if args.executable.casefold() == "auto":
                options.pop("executable", None)
            else:
                options["executable"] = str(find_viewer(args.executable))
        for argument, key in (
            (args.through, "through"),
            (args.color_depth, "colorDepth"),
            (args.updates, "updates"),
            (args.phonebook, "phonebookPath"),
            (args.phonebook_id, "phonebookId"),
        ):
            if argument is not None:
                options[key] = argument
        if args.fullscreen:
            options["fullscreen"] = True
        database.configure_protocol(args.selector, "radmin", options)
        print(json.dumps(options, ensure_ascii=False))
        return 0
    if args.action == "probe":
        port = validate_port(
            args.port if args.port is not None else options.get("port", DEFAULT_PORT)
        )
        opened = tcp_probe(device.ip, port, float(load_config().get("timeout", 0.8)))
        print(
            json.dumps(
                {
                    "protocol": "radmin",
                    "ip": device.ip,
                    "port": port,
                    "open": opened,
                    "assessment": "probable/configurado" if opened else "no disponible",
                }
            )
        )
        return 0 if opened else 1
    return run_open(
        argparse.Namespace(
            selector=args.selector,
            protocol="radmin",
            port=args.port,
            mode=args.mode,
            path="",
            dry_run=False,
            database=args.database,
            store=args.store,
            through=args.through,
            fullscreen=args.fullscreen,
            color_depth=args.color_depth,
            updates=args.updates,
            phonebook=args.phonebook,
            phonebook_id=args.phonebook_id,
        )
    )
