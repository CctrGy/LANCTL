from __future__ import annotations

import argparse
import ipaddress
import json
from copy import deepcopy

from lanctl.apps.ip.infrastructure.services.lan_scanner import SCAN_ORDERS
from lanctl.apps.ip.infrastructure.services.scan_profiles import SCAN_PROFILES
from lanctl.apps.ip.interfaces.tui.keyboard import (
    CONFIGURABLE_TUI_KEYS,
    FOOTER_ACTIONS,
    normalize_footer_actions,
    normalize_key_bindings,
    validate_key_bindings,
)
from lanctl.apps.ip.interfaces.tui.layout import (
    DEFAULT_COLUMN_SPECS,
    PANEL_LAYOUTS,
    normalize_cli_percent,
    normalize_column_spec,
    normalize_column_specs,
    normalize_panel_layout,
)
from lanctl.core.config import CONFIG_PATH as CONFIG_PATH  # Compatibility export.
from lanctl.core.config import (
    load_config,
    normalize_dhcp_range,
    save_config,
)
from lanctl.core.console import ok
from lanctl.core.device_retention import (
    RETENTION_MODES,
    RETENTION_SCOPES,
    RETENTION_TARGETS,
    normalize_retention_mode,
    normalize_retention_scope,
    normalize_retention_target,
)
from lanctl.core.output import normalize_columns
from lanctl.shared.i18n import t, translate_label


def register_settings_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "settings",
        help=t("LANCTL.UI.HELP.QUERY_OR_CHANGE_LANCTL_S_PERSISTENT_CONFIGURATION"),
    )
    command.add_argument(
        "--startup-interface",
        choices=("cli", "tui", "gui"),
        help=t("LANCTL.UI.HELP.PREFERRED_INTERFACE_WHEN_OPENING_LANCTL_WITHOUT_ARGUMENTS"),
    )
    command.add_argument(
        "--close-gui-on-launch",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.CLOSE_THE_MAIN_GUI_WHEN_THE_REQUESTED_LAUNCHER_IS_AVAILABLE"),
    )
    command.add_argument(
        "-range",
        dest="network_range",
        metavar="CIDR",
        help=t("LANCTL.UI.HELP.DEFAULT_LAN_RANGE_FOR_EXAMPLE_192_168_1_1_24"),
    )
    command.add_argument(
        "-list-fields",
        "--list-fields",
        "-list",
        nargs="+",
        metavar="CAMPO",
        help=t("LANCTL.UI.HELP.COLUMNS_DISPLAYED_BY_LIST_SEPARATED_BY_SPACES_OR_COMMAS"),
    )
    command.add_argument(
        "-dhcp-range",
        "--dhcp-range",
        "-dhcp",
        metavar="INICIO-FIN",
        help=(t("LANCTL.UI.HELP.MANUAL_DHCP_RANGE_USE_OFF_TO_LEAVE_IT_UNCONFIGURED")),
    )
    command.add_argument(
        "-credentials",
        "--credentials",
        metavar="ARCHIVO",
        help=t("LANCTL.UI.HELP.PATH_TO_THE_ENCRYPTED_CREDENTIAL_STORE"),
    )
    command.add_argument(
        "-discovery",
        "--discovery",
        choices=("icmp", "arp", "hybrid"),
        help=t("LANCTL.UI.HELP.DEFAULT_METHOD_USED_BY_LIST"),
    )
    command.add_argument(
        "--scan-profile",
        choices=tuple(SCAN_PROFILES),
        help=t("LANCTL.UI.HELP.DEFAULT_LIST_PROFILE_FAST_NORMAL_OR_ACCURATE"),
    )
    command.add_argument(
        "--progress",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.ENABLE_OR_DISABLE_INTERACTIVE_PROGRESS"),
    )
    command.add_argument(
        "--service-identification",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.ENABLE_OR_DISABLE_SERVICE_RECOGNITION_IN_SCAN"),
    )
    command.add_argument(
        "--disconnected-retention",
        choices=RETENTION_MODES,
        help=t("LANCTL.UI.HELP.DISCONNECTED_DEVICE_PERSISTENCE_PERMANENT_SESSION_OR_FORGET"),
    )
    command.add_argument(
        "--disconnected-target",
        choices=RETENTION_TARGETS,
        help=t("LANCTL.UI.HELP.APPLY_RETENTION_ONLY_TO_CNF_X_UNCONFIRMED_OR_TO_ALL_ALL"),
    )
    command.add_argument(
        "--disconnected-scope",
        choices=RETENTION_SCOPES,
        help=t("LANCTL.UI.HELP.APPLY_THE_RULE_TO_THE_ENTIRE_LAN_ALL_OR_ONLY_THE_DHCP_RANGE_DHCP"),
    )
    command.add_argument("--workers", type=int, help=t("LANCTL.UI.HELP.DEFAULT_SCAN_CONCURRENCY"))
    command.add_argument(
        "--timeout", type=float, help=t("LANCTL.UI.HELP.DEFAULT_TIMEOUT_PER_NETWORK_OPERATION")
    )
    command.add_argument(
        "--scan-order",
        choices=SCAN_ORDERS,
        help=t("LANCTL.UI.HELP.DEFAULT_PROBE_ORDER_ASCENDING_DESCENDING_OR_RANDOM"),
    )
    command.add_argument(
        "--max-hosts", type=int, help=t("LANCTL.UI.HELP.MAXIMUM_HOSTS_AUTHORIZED_PER_SCAN")
    )
    command.add_argument(
        "--database", metavar="ARCHIVO", help=t("LANCTL.UI.HELP.PATH_TO_THE_ELEMENT_INVENTORY")
    )
    command.add_argument(
        "--physical-database",
        metavar="ARCHIVO",
        help=t(
            "LANCTL.UI.HELP.PATH_TO_THE_PHYSICAL_SQLITE_DATABASE_MANAGED_EXCLUSIVELY_BY_LANWIRE"
        ),
    )
    command.add_argument(
        "--groups", metavar="ARCHIVO", help=t("LANCTL.UI.HELP.PATH_TO_THE_GROUP_DATABASE")
    )
    command.add_argument("--log", metavar="DIRECTORIO", help=t("LANCTL.UI.HELP.LOG_DIRECTORY"))
    command.add_argument(
        "--error-log-level",
        type=int,
        metavar="1-59",
        help=t(
            "LANCTL.UI.HELP.MINIMUM_ERROREVENT_LEVEL_WRITTEN_TO_THE_LOG_1_INCLUDES_DETAILED_DIAGNOSTICS"
        ),
    )
    command.add_argument(
        "--projects-directory",
        metavar="DIRECTORIO",
        help=t("LANCTL.UI.HELP.DEFAULT_FOLDER_FOR_RELATIVE_VLF_PROJECT_NAMES"),
    )
    command.add_argument(
        "-save-mode",
        "--save-mode",
        metavar="MODO",
        help=(
            t(
                "LANCTL.UI.HELP.VLF_SAVE_POLICY_USE_LIST_TO_QUERY_BUILT_IN_AND_PLUGIN_PROVIDED_OPTIONS"
            )
        ),
    )
    command.add_argument(
        "-save-interval",
        "--save-interval",
        type=float,
        metavar="MINUTOS",
        help=t("LANCTL.UI.HELP.INTERVAL_FOR_AUTOMATIC_TIMETOSAVE_IN_MINUTES_MINIMUM_0_1"),
    )
    command.add_argument(
        "--cli-exit-save-prompt",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.ASK_WHETHER_TO_SAVE_AFTER_EACH_INDIVIDUAL_CONSOLE_COMMAND"),
    )
    command.add_argument(
        "--cli-command-chaining",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.ALLOW_COMMAND_CHAINING_WITH_IN_THE_INTERACTIVE_CLI"),
    )
    command.add_argument(
        "-log-cleanup",
        "--log-cleanup",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.ENABLE_OR_DISABLE_AUTOMATIC_CLEANUP_OF_OLD_LOGS"),
    )
    command.add_argument(
        "-log-retention-days",
        "--log-retention-days",
        type=int,
        metavar="DÍAS",
        help=t("LANCTL.UI.HELP.NUMBER_OF_DAYS_TO_RETAIN_LOG_FILES"),
    )
    command.add_argument(
        "--remote-access",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.ENABLE_RESTRICTED_SSH_ACCESS"),
    )
    command.add_argument(
        "--remote-bind", metavar="IP", help=t("LANCTL.UI.HELP.LOCAL_IPV4_ADDRESS_FOR_SSH_LISTENING")
    )
    command.add_argument(
        "--remote-cidr", metavar="CIDR", help=t("LANCTL.UI.HELP.AUTHORIZED_SOURCE_NETWORK")
    )
    command.add_argument("--remote-port", type=int, help=t("LANCTL.UI.HELP.REMOTE_SSH_SERVER_PORT"))
    command.add_argument(
        "--remote-password-auth",
        choices=("on", "off"),
        help=t("LANCTL.UI.HELP.ALLOW_OR_BLOCK_SSH_PASSWORD_AUTHENTICATION"),
    )
    command.add_argument(
        "--remote-backend",
        choices=("service", "user"),
        help=t("LANCTL.UI.HELP.RUN_THE_BACKEND_AS_A_PERSISTENT_SERVICE_OR_USER_PROCESS"),
    )
    command.add_argument(
        "--remote-forced-view",
        choices=("off", "gui", "tui", "plugins", "projects", "settings"),
        help=t("LANCTL.UI.HELP.DEFAULT_VIEW_FOR_ROOT_FORCED_VIEW"),
    )
    command.add_argument(
        "--tui-key",
        action="append",
        metavar="ACCIÓN=TECLA",
        help=t("LANCTL.UI.HELP.ASSIGN_A_KEY_TO_A_TUI_ACTION_MAY_BE_REPEATED"),
    )
    command.add_argument(
        "--tui-layout",
        choices=PANEL_LAYOUTS,
        help=t("LANCTL.UI.HELP.PLACE_THE_CLI_AT_THE_TOP_CLI_TOP_OR_BOTTOM_CLI_BOTTOM"),
    )
    command.add_argument(
        "--tui-cli-percent",
        metavar="15-75",
        help=t(
            "LANCTL.UI.HELP.VERTICAL_PERCENTAGE_RESERVED_FOR_CLI_LISTELEMENT_RETAINS_AT_LEAST_25"
        ),
    )
    command.add_argument(
        "--tui-column",
        action="append",
        metavar="COLUMNA=TAMAÑO",
        help=t("LANCTL.UI.HELP.COLUMN_WEIGHT_GROUP_15_IP_15CH_AND_MAC_17CH_ARE_FIXED"),
    )
    command.add_argument(
        "--tui-footer-buttons",
        metavar="ACCIONES",
        help=t("LANCTL.UI.HELP.VISIBLE_BOTTOM_BAR_ACTIONS_COMMA_SEPARATED_USE_ALL_FOR_ALL_ACTIONS"),
    )
    command.add_argument(
        "--tui-footer-button",
        action="append",
        metavar="ACCIÓN=on|off",
        help=t("LANCTL.UI.HELP.SHOW_OR_HIDE_A_SPECIFIC_BOTTOM_BAR_ACTION_MAY_BE_REPEATED"),
    )
    from .settings_menu import dispatch_settings, register_catalog_options

    register_catalog_options(command)
    command.set_defaults(handler=dispatch_settings)


def run_settings(args: argparse.Namespace) -> int:
    from lanctl.core import config as config_module
    from lanctl.core.file_transaction import locked_file
    from lanctl.core.project_context import project_operation

    with locked_file(config_module.CONFIG_PATH), project_operation():
        return _run_settings(args)


def _run_settings(args: argparse.Namespace) -> int:
    # The public adapter is also called directly with Namespace instances.
    # argparse choices alone are not a validation boundary.
    for name in (
        "close_gui_on_launch",
        "progress",
        "service_identification",
        "cli_exit_save_prompt",
        "cli_command_chaining",
        "log_cleanup",
        "remote_access",
        "remote_password_auth",
    ):
        value = getattr(args, name, None)
        if value is not None and value not in {"on", "off"}:
            raise ValueError(f"{name}: usa on u off")
    config = load_config()
    original = deepcopy(config)
    from lanctl.apps.suite.settings import cli_context, settings_entries

    context = cli_context(legacy_paths=True)
    # Validate requested privileged routes even when their value is unchanged:
    # a no-op must not bypass the remote restriction and initialize a backend.
    if context.interface == "remote" and any(
        getattr(args, key, None) is not None
        for key in (
            "credentials",
            "database",
            "physical_database",
            "groups",
            "log",
            "projects_directory",
            "remote_access",
            "remote_bind",
            "remote_cidr",
            "remote_port",
            "remote_password_auth",
            "remote_backend",
            "remote_forced_view",
        )
    ):
        raise ValueError("Administración local: solo lectura desde la CLI remota")
    if context.interface == "remote" and any(
        getattr(args, key, None) is not None
        for key in (
            "close_gui_on_launch",
            "tui_key",
            "tui_layout",
            "tui_cli_percent",
            "tui_column",
            "tui_footer_buttons",
            "tui_footer_button",
        )
    ):
        raise ValueError("Preferencias de otra interfaz: solo lectura desde la CLI remota")
    if (
        args.network_range is None
        and getattr(args, "startup_interface", None) is None
        and getattr(args, "close_gui_on_launch", None) is None
        and args.list_fields is None
        and args.dhcp_range is None
        and args.credentials is None
        and args.discovery is None
        and args.scan_profile is None
        and args.progress is None
        and args.service_identification is None
        and args.disconnected_retention is None
        and args.disconnected_target is None
        and args.disconnected_scope is None
        and args.workers is None
        and args.timeout is None
        and args.scan_order is None
        and args.max_hosts is None
        and args.database is None
        and args.physical_database is None
        and args.groups is None
        and args.log is None
        and args.error_log_level is None
        and args.projects_directory is None
        and args.save_mode is None
        and args.save_interval is None
        and args.cli_exit_save_prompt is None
        and args.cli_command_chaining is None
        and args.log_cleanup is None
        and args.log_retention_days is None
        and args.remote_access is None
        and args.remote_bind is None
        and args.remote_cidr is None
        and args.remote_port is None
        and args.remote_password_auth is None
        and args.remote_backend is None
        and args.remote_forced_view is None
        and args.tui_key is None
        and args.tui_layout is None
        and args.tui_cli_percent is None
        and args.tui_column is None
        and args.tui_footer_buttons is None
        and args.tui_footer_button is None
    ):
        context = cli_context()
        if context.interface == "remote":
            print(
                json.dumps(
                    {entry["path"]: entry["value"] for entry in settings_entries(context)},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            document = {}
            for entry in settings_entries(context):
                target = document
                parts = entry["path"].split(".")
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = entry["value"]
            print(json.dumps(document, indent=2, ensure_ascii=False))
        return 0

    changes: list[str] = []
    if getattr(args, "startup_interface", None) is not None:
        config["startupInterface"] = args.startup_interface
        changes.append(
            t("LANCTL.UI.MESSAGE.STARTUP_INTERFACE_VALUE", value0=f"{args.startup_interface}")
        )
    if getattr(args, "close_gui_on_launch", None) is not None:
        config["closeGuiOnLaunch"] = args.close_gui_on_launch == "on"
        changes.append(
            t(
                "LANCTL.UI.DETAIL.CLOSE_GUI_WHEN_OPENING_A_LAUNCHER_VALUE",
                value0=f"{args.close_gui_on_launch}",
            )
        )
    if args.save_mode is not None:
        from lanctl.core.projects.save_policy import available_save_modes, normalize_save_mode

        if args.save_mode.casefold() == "list":
            for definition in available_save_modes():
                triggers = ",".join(sorted(definition.triggers)) or "manual"
                if definition.mode == "manual.inCloseConsult":
                    triggers = "close?"
                print(
                    f"{definition.mode:<28} {triggers:<20} "
                    f"{definition.owner} {translate_label(definition.description)}"
                )
            return 0
        config["projectSaveMode"] = normalize_save_mode(args.save_mode)
        changes.append(t("LANCTL.UI.DETAIL.SAVEMODE_VALUE", value0=f"{config['projectSaveMode']}"))
    if args.save_interval is not None:
        if args.save_interval < 0.1:
            raise ValueError("save-interval debe ser de al menos 0.1 minutos")
        config["projectSaveIntervalMinutes"] = args.save_interval
        changes.append(
            t("LANCTL.UI.MESSAGE.SAVE_INTERVAL_VALUE_MINUTES", value0=f"{args.save_interval:g}")
        )
    if args.cli_exit_save_prompt is not None:
        config["cliPromptSaveOnCommandExit"] = args.cli_exit_save_prompt == "on"
        changes.append(
            t(
                "LANCTL.UI.MESSAGE.ASK_TO_SAVE_AFTER_COMMAND_VALUE",
                value0=f"{args.cli_exit_save_prompt}",
            )
        )
    if args.cli_command_chaining is not None:
        config["cliCommandChaining"] = args.cli_command_chaining == "on"
        changes.append(
            t("LANCTL.UI.MESSAGE.CHAINED_CLI_COMMANDS_VALUE", value0=f"{args.cli_command_chaining}")
        )
    if args.network_range is not None:
        try:
            network = ipaddress.ip_network(args.network_range, strict=False)
        except ValueError as error:
            raise ValueError(f"rango CIDR no válido: {args.network_range}") from error
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError("el rango de red debe ser IPv4")
        config["range"] = args.network_range
        changes.append(t("LANCTL.UI.DETAIL.RANGE_VALUE", value0=f"{args.network_range}"))
    if args.list_fields is not None:
        config["listColumns"] = normalize_columns(args.list_fields)
        changes.append(
            t("LANCTL.UI.MESSAGE.LIST_COLUMNS_VALUE", value0=f"{', '.join(config['listColumns'])}")
        )
    if args.dhcp_range is not None:
        config["dhcpRange"] = normalize_dhcp_range(args.dhcp_range)
        shown = config["dhcpRange"] or "sin configurar"
        changes.append(t("LANCTL.UI.DETAIL.DHCP_RANGE_VALUE", value0=f"{shown}"))
    if args.credentials is not None:
        path = args.credentials.strip()
        if not path:
            raise ValueError("la ruta de credenciales no puede estar vacía")
        config["credentials"] = path
        changes.append(t("LANCTL.UI.DETAIL.CREDENTIALS_VALUE", value0=f"{path}"))
    if args.discovery is not None:
        config["discovery"] = args.discovery
        changes.append(t("LANCTL.UI.DETAIL.DISCOVERY_VALUE", value0=f"{args.discovery}"))
    if args.scan_profile is not None:
        config["scanProfile"] = args.scan_profile
        changes.append(t("LANCTL.UI.MESSAGE.SCAN_PROFILE_VALUE", value0=f"{args.scan_profile}"))
    if args.progress is not None:
        config["progress"] = args.progress == "on"
        changes.append(t("LANCTL.UI.DETAIL.PROGRESS_VALUE", value0=f"{args.progress}"))
    if args.service_identification is not None:
        config["serviceIdentification"] = args.service_identification == "on"
        changes.append(
            t(
                "LANCTL.UI.MESSAGE.SERVICE_IDENTIFICATION_VALUE",
                value0=f"{args.service_identification}",
            )
        )
    if args.disconnected_retention is not None:
        config["disconnectedRetention"] = normalize_retention_mode(args.disconnected_retention)
        changes.append(
            t(
                "LANCTL.UI.MESSAGE.DISCONNECTED_RETENTION_VALUE",
                value0=f"{config['disconnectedRetention']}",
            )
        )
    if args.disconnected_target is not None:
        config["disconnectedRetentionTarget"] = normalize_retention_target(args.disconnected_target)
        changes.append(
            t(
                "LANCTL.UI.MESSAGE.RETENTION_TARGET_VALUE",
                value0=f"{config['disconnectedRetentionTarget']}",
            )
        )
    if args.disconnected_scope is not None:
        config["disconnectedRetentionScope"] = normalize_retention_scope(args.disconnected_scope)
        changes.append(
            t(
                "LANCTL.UI.MESSAGE.RETENTION_RANGE_VALUE",
                value0=f"{config['disconnectedRetentionScope']}",
            )
        )
    if args.workers is not None:
        if args.workers < 1:
            raise ValueError("workers debe ser mayor que cero")
        config["workers"] = args.workers
        changes.append(t("LANCTL.UI.DETAIL.WORKERS_VALUE", value0=f"{args.workers}"))
    if args.timeout is not None:
        if args.timeout <= 0:
            raise ValueError("timeout debe ser mayor que cero")
        config["timeout"] = args.timeout
        changes.append(t("LANCTL.UI.DETAIL.TIMEOUT_VALUE", value0=f"{args.timeout}"))
    if args.scan_order is not None:
        config["scanOrder"] = args.scan_order
        changes.append(t("LANCTL.UI.MESSAGE.SCAN_ORDER_VALUE", value0=f"{args.scan_order}"))
    if args.max_hosts is not None:
        if args.max_hosts < 1:
            raise ValueError("max-hosts debe ser mayor que cero")
        config["maxHosts"] = args.max_hosts
        changes.append(t("LANCTL.UI.MESSAGE.MAXIMUM_HOSTS_VALUE", value0=f"{args.max_hosts}"))
    for argument, key, label in (
        (args.database, "database", t("LANCTL.UI.SCREEN.ELEMENT_DATABASE")),
        (
            args.physical_database,
            "physicalDatabase",
            t("LANCTL.UI.SCREEN.LANWIRE_PHYSICAL_DATABASE"),
        ),
        (args.groups, "groups", t("LANCTL.UI.SCREEN.GROUP_DATABASE")),
        (args.log, "log", t("LANCTL.UI.SCREEN.LOG_DIRECTORY")),
        (args.projects_directory, "projectsDirectory", t("LANCTL.UI.TEXT.PROJECT_DIRECTORY")),
    ):
        if argument is not None:
            value = argument.strip()
            if not value:
                raise ValueError(f"{label} no puede quedar vacío")
            if key == "projectsDirectory" and value.casefold() in ("default", "auto"):
                value = None
            config[key] = value
            changes.append(f"{label}: {value or 'auto (Documentos de Windows)'}")

    if args.log_cleanup is not None:
        config["logCleanupEnabled"] = args.log_cleanup == "on"
        state = "activada" if config["logCleanupEnabled"] else "desactivada"
        changes.append(t("LANCTL.UI.MESSAGE.AUTOMATIC_LOG_CLEANUP_VALUE", value0=f"{state}"))
    if args.log_retention_days is not None:
        if args.log_retention_days < 1:
            raise ValueError("la retención de logs debe ser de al menos 1 día")
        config["logRetentionDays"] = args.log_retention_days
        changes.append(
            t("LANCTL.UI.MESSAGE.LOG_RETENTION_VALUE_DAYS", value0=f"{args.log_retention_days}")
        )
    if args.error_log_level is not None:
        if not 1 <= args.error_log_level <= 59:
            raise ValueError("error-log-level debe estar entre 1 y 59")
        config["errorLogLevel"] = args.error_log_level
        changes.append(
            t(
                "LANCTL.UI.MESSAGE.MINIMUM_LOGGED_ERROR_LEVEL_VALUE",
                value0=f"{args.error_log_level}",
            )
        )

    remote_values = {
        "remoteAccessEnabled": args.remote_access == "on" if args.remote_access else None,
        "remoteAccessBind": args.remote_bind,
        "remoteAccessCidr": args.remote_cidr,
        "remoteAccessPort": args.remote_port,
        "remoteAccessPasswordAuthentication": (
            args.remote_password_auth == "on" if args.remote_password_auth else None
        ),
        "remoteAccessBackend": args.remote_backend,
        "remoteAccessForcedView": args.remote_forced_view,
    }
    remote_changed = any(value is not None for value in remote_values.values())
    if remote_changed:
        for key, value in remote_values.items():
            if value is not None:
                config[key] = value
        bind = str(config["remoteAccessBind"]).strip()
        cidr = str(config["remoteAccessCidr"]).strip()
        port = int(config["remoteAccessPort"])
        if not (1 <= port <= 65535):
            raise ValueError("remote-port debe estar entre 1 y 65535")
        if config["remoteAccessEnabled"] and (not bind or not cidr):
            raise ValueError("Remote Access requiere IP de enlace y CIDR permitido")
        if bind or cidr:
            if not bind or not cidr:
                raise ValueError("indica conjuntamente la IP de enlace y el CIDR permitido")
            from lanctl.apps.access.network import validate_endpoint

            validate_endpoint(bind, cidr, port)
        changes.append(
            "Remote Access: " + ("activado" if config["remoteAccessEnabled"] else "desactivado")
        )

    if args.tui_key:
        bindings = normalize_key_bindings(config.get("tuiKeyBindings"))
        valid_actions = {action.casefold(): action for action in bindings}
        for assignment in args.tui_key:
            action_text, separator, key_text = assignment.partition("=")
            action = valid_actions.get(action_text.strip().casefold())
            key = key_text.strip().upper().replace("+", "_")
            if not separator or not action:
                valid = ", ".join(bindings)
                raise ValueError(f"tui-key debe usar ACCIÓN=TECLA; acciones: {valid}")
            if key in {"NONE", "NULL", "OFF", "-"}:
                bindings[action] = None
                continue
            if key not in CONFIGURABLE_TUI_KEYS:
                valid = ", ".join(item.replace("_", "+") for item in CONFIGURABLE_TUI_KEYS)
                raise ValueError(f"tecla TUI no válida: {key_text}. Opciones: None, {valid}")
            bindings[action] = key
        config["tuiKeyBindings"] = validate_key_bindings(bindings)
        changes.append("Atajos TUI actualizados")

    if args.tui_layout is not None:
        config["tuiPanelLayout"] = normalize_panel_layout(args.tui_layout)
        changes.append(
            t("LANCTL.UI.MESSAGE.TUI_LAYOUT_VALUE", value0=f"{config['tuiPanelLayout']}")
        )
    if args.tui_cli_percent is not None:
        config["tuiCliHeightPercent"] = normalize_cli_percent(args.tui_cli_percent)
        changes.append(
            t("LANCTL.UI.MESSAGE.CLI_HEIGHT_VALUE", value0=f"{config['tuiCliHeightPercent']}")
        )
    if args.tui_column:
        columns = normalize_column_specs(config.get("tuiColumnWidths"))
        canonical = {name.casefold(): name for name in DEFAULT_COLUMN_SPECS}
        canonical["protocols"] = "users"
        for assignment in args.tui_column:
            raw_name, separator, raw_value = assignment.partition("=")
            name = canonical.get(raw_name.strip().casefold())
            if not separator or not name:
                choices = ", ".join(DEFAULT_COLUMN_SPECS)
                raise ValueError(f"tui-column debe usar COLUMNA=TAMAÑO; columnas: {choices}")
            columns[name] = normalize_column_spec(name, raw_value)
        config["tuiColumnWidths"] = columns
        changes.append(t("LANCTL.UI.PROMPT.TUI_COLUMN_PROPORTIONS_UPDATED"))

    if args.tui_footer_buttons is not None:
        requested = [part.strip() for part in args.tui_footer_buttons.split(",")]
        invalid = [
            part
            for part in requested
            if part
            and part.casefold() != "all"
            and part.casefold() not in {x.casefold() for x in FOOTER_ACTIONS}
        ]
        if invalid:
            raise ValueError(
                f"acciones de barra TUI no válidas: {', '.join(invalid)}; "
                f"opciones: {', '.join(FOOTER_ACTIONS)}"
            )
        config["tuiFooterButtons"] = normalize_footer_actions(requested)
        changes.append(t("LANCTL.UI.PROMPT.VISIBLE_TUI_BUTTONS_UPDATED"))

    if args.tui_footer_button:
        visible = normalize_footer_actions(config.get("tuiFooterButtons"))
        valid_actions = {action.casefold(): action for action in FOOTER_ACTIONS}
        for assignment in args.tui_footer_button:
            action_text, separator, state_text = assignment.partition("=")
            action = valid_actions.get(action_text.strip().casefold())
            state = state_text.strip().casefold()
            if not separator or not action or state not in {"on", "off"}:
                raise ValueError(
                    "tui-footer-button debe usar ACCIÓN=on|off; "
                    f"acciones: {', '.join(FOOTER_ACTIONS)}"
                )
            if state == "on" and action not in visible:
                visible.append(action)
            elif state == "off" and action in visible:
                visible.remove(action)
        config["tuiFooterButtons"] = [action for action in FOOTER_ACTIONS if action in visible]
        changes.append(t("LANCTL.UI.PROMPT.TUI_BUTTON_VISIBILITY_UPDATED"))

    config = _prepare_legacy_changes(original, config, context)
    if remote_changed:
        from lanctl.apps.access.settings_lifecycle import remote_settings_transaction

        with remote_settings_transaction(original, config):
            path = save_config(config)
    else:
        path = save_config(config)
    ok(
        t("LANCTL.UI.STATUS.CONFIGURED"),
        "\n".join((*changes, t("LANCTL.UI.DETAIL.FILE_VALUE", value0=f"{path}"))),
    )
    return 0


def _prepare_legacy_changes(original, candidate, context):
    # Explicit local --tui-* / --close-gui-on-launch options are compatibility
    # administration routes. Generic --set and remote commands never use them.
    from lanctl.core.settings_policy import SettingsContext, changed_values, prepare_program_changes

    groups = {"cli": {}, "gui": {}, "tui": {}}
    for path, value in changed_values(original, candidate).items():
        interface = (
            "tui"
            if path.startswith("tui.")
            else "gui"
            if path == "startup.closeGuiOnLaunch"
            else "cli"
        )
        groups[interface][path] = value
    result = original
    for interface, changes in groups.items():
        if changes:
            target = (
                context
                if interface == "cli" or context.interface == "remote"
                else SettingsContext(interface)
            )
            result = prepare_program_changes(result, changes, target)
    if result is not original:
        from lanctl.core.session import PROJECT_KEYS

        result.project_base = {key: deepcopy(original.get(key)) for key in PROJECT_KEYS}
        result.base_values = deepcopy(dict(original))
    return result


def _configure_remote_access(config: dict, bind: str, cidr: str, port: int) -> None:
    """Compatibility adapter; the application service owns remote configuration."""
    from lanctl.apps.access.settings import apply_remote_settings

    apply_remote_settings(config)
