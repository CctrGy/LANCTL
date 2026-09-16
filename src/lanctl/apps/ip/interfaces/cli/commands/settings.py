from __future__ import annotations

import argparse
import ipaddress
import json

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
from lanctl.core.config import (
    CONFIG_PATH,
    canonical_config,
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
from lanctl.core.file_transaction import transactional_file
from lanctl.core.output import normalize_columns


def register_settings_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "settings",
        help="Consulta o modifica la configuración persistente de LANCTL.",
    )
    command.add_argument(
        "-range",
        dest="network_range",
        metavar="CIDR",
        help="Rango LAN predeterminado, por ejemplo 192.168.1.1/24.",
    )
    command.add_argument(
        "-list-fields",
        "--list-fields",
        "-list",
        nargs="+",
        metavar="CAMPO",
        help="Columnas mostradas por list, separadas por espacios o comas.",
    )
    command.add_argument(
        "-dhcp-range",
        "--dhcp-range",
        "-dhcp",
        metavar="INICIO-FIN",
        help=("Rango DHCP manual. Usa 'off' para dejarlo sin configurar."),
    )
    command.add_argument(
        "-credentials",
        "--credentials",
        metavar="ARCHIVO",
        help="Ruta del almacén de credenciales cifradas.",
    )
    command.add_argument(
        "-discovery",
        "--discovery",
        choices=("icmp", "arp", "hybrid"),
        help="Método predeterminado utilizado por list.",
    )
    command.add_argument(
        "--scan-profile",
        choices=tuple(SCAN_PROFILES),
        help="Perfil predeterminado de list: fast, normal o accurate.",
    )
    command.add_argument(
        "--progress", choices=("on", "off"), help="Activa o desactiva el progreso interactivo."
    )
    command.add_argument(
        "--service-identification",
        choices=("on", "off"),
        help="Activa o desactiva el reconocimiento de servicios en scan.",
    )
    command.add_argument(
        "--disconnected-retention",
        choices=RETENTION_MODES,
        help="Persistencia de desconectados: permanent, session o forget.",
    )
    command.add_argument(
        "--disconnected-target",
        choices=RETENTION_TARGETS,
        help="Aplica la retención solo a CNF=X (unconfirmed) o a todos (all).",
    )
    command.add_argument(
        "--disconnected-scope",
        choices=RETENTION_SCOPES,
        help="Aplica la regla a toda la LAN (all) o solo al rango DHCP (dhcp).",
    )
    command.add_argument("--workers", type=int, help="Concurrencia predeterminada de los escaneos.")
    command.add_argument(
        "--timeout", type=float, help="Timeout predeterminado por operación de red."
    )
    command.add_argument(
        "--scan-order",
        choices=SCAN_ORDERS,
        help="Orden predeterminado de sondeo: ascending, descending o random.",
    )
    command.add_argument("--max-hosts", type=int, help="Máximo de hosts autorizado por escaneo.")
    command.add_argument("--database", metavar="ARCHIVO", help="Ruta del inventario de elementos.")
    command.add_argument(
        "--physical-database",
        metavar="ARCHIVO",
        help="Ruta de la base física SQLite administrada exclusivamente por LANWIRE.",
    )
    command.add_argument("--groups", metavar="ARCHIVO", help="Ruta de la base de grupos.")
    command.add_argument("--log", metavar="DIRECTORIO", help="Directorio de registros.")
    command.add_argument(
        "--error-log-level",
        type=int,
        metavar="1-59",
        help="Nivel mínimo de ErrorEvent escrito en el log (1 incluye diagnóstico detallado).",
    )
    command.add_argument(
        "--projects-directory",
        metavar="DIRECTORIO",
        help="Carpeta predeterminada para nombres de proyecto VLF relativos.",
    )
    command.add_argument(
        "-save-mode",
        "--save-mode",
        metavar="MODO",
        help=(
            "Política de guardado VLF. Usa 'list' para consultar las opciones integradas "
            "y las aportadas por plugins."
        ),
    )
    command.add_argument(
        "-save-interval",
        "--save-interval",
        type=float,
        metavar="MINUTOS",
        help="Intervalo de automatic.timeToSave en minutos (mínimo 0.1).",
    )
    command.add_argument(
        "-log-cleanup",
        "--log-cleanup",
        choices=("on", "off"),
        help="Activa o desactiva la limpieza automática de logs antiguos.",
    )
    command.add_argument(
        "-log-retention-days",
        "--log-retention-days",
        type=int,
        metavar="DÍAS",
        help="Días durante los que se conservan los archivos de log.",
    )
    command.add_argument(
        "--remote-access", choices=("on", "off"), help="Activa el acceso SSH restringido."
    )
    command.add_argument("--remote-bind", metavar="IP", help="IPv4 local de escucha SSH.")
    command.add_argument("--remote-cidr", metavar="CIDR", help="Red de origen autorizada.")
    command.add_argument("--remote-port", type=int, help="Puerto del servidor SSH remoto.")
    command.add_argument(
        "--remote-password-auth",
        choices=("on", "off"),
        help="Permite o bloquea autenticación SSH mediante contraseña.",
    )
    command.add_argument(
        "--remote-backend",
        choices=("service", "user"),
        help="Ejecuta el backend como servicio persistente o proceso de usuario.",
    )
    command.add_argument(
        "--remote-forced-view",
        choices=("off", "gui", "tui", "plugins", "projects", "settings"),
        help="Vista predeterminada para root forced-view.",
    )
    command.add_argument(
        "--tui-key",
        action="append",
        metavar="ACCIÓN=TECLA",
        help="Asigna una tecla a una acción del TUI. Puede repetirse.",
    )
    command.add_argument(
        "--tui-layout",
        choices=PANEL_LAYOUTS,
        help="Coloca el CLI arriba (cli.top) o abajo (cli.bottom).",
    )
    command.add_argument(
        "--tui-cli-percent",
        metavar="15-75",
        help="Porcentaje vertical reservado al CLI; ListElement conserva al menos 25%%.",
    )
    command.add_argument(
        "--tui-column",
        action="append",
        metavar="COLUMNA=TAMAÑO",
        help="Peso de columna (GROUP=15%%); IP=15ch y MAC=17ch son fijas.",
    )
    command.add_argument(
        "--tui-footer-buttons",
        metavar="ACCIONES",
        help="Acciones visibles en la barra inferior, separadas por comas; usa all para todas.",
    )
    command.add_argument(
        "--tui-footer-button",
        action="append",
        metavar="ACCIÓN=on|off",
        help="Muestra u oculta una acción concreta de la barra inferior. Puede repetirse.",
    )
    command.set_defaults(handler=run_settings)


@transactional_file(CONFIG_PATH)
def run_settings(args: argparse.Namespace) -> int:
    config = load_config()
    if (
        args.network_range is None
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
        and args.projects_directory is None
        and args.save_mode is None
        and args.save_interval is None
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
        print(json.dumps(canonical_config(config), indent=2, ensure_ascii=False))
        print(f"\nArchivo: {CONFIG_PATH.resolve()}")
        return 0

    changes: list[str] = []
    if args.save_mode is not None:
        from lanctl.core.projects.save_policy import available_save_modes, normalize_save_mode

        if args.save_mode.casefold() == "list":
            for definition in available_save_modes():
                triggers = ",".join(sorted(definition.triggers)) or "manual"
                if definition.mode == "manual.inCloseConsult":
                    triggers = "close?"
                print(
                    f"{definition.mode:<28} {triggers:<20} "
                    f"{definition.owner} {definition.description}"
                )
            return 0
        config["projectSaveMode"] = normalize_save_mode(args.save_mode)
        changes.append(f"SaveMode: {config['projectSaveMode']}")
    if args.save_interval is not None:
        if args.save_interval < 0.1:
            raise ValueError("save-interval debe ser de al menos 0.1 minutos")
        config["projectSaveIntervalMinutes"] = args.save_interval
        changes.append(f"Intervalo de guardado: {args.save_interval:g} minutos")
    if args.network_range is not None:
        try:
            network = ipaddress.ip_network(args.network_range, strict=False)
        except ValueError as error:
            raise ValueError(f"rango CIDR no válido: {args.network_range}") from error
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError("el rango de red debe ser IPv4")
        config["range"] = args.network_range
        changes.append(f"Rango: {args.network_range}")
    if args.list_fields is not None:
        config["listColumns"] = normalize_columns(args.list_fields)
        changes.append(f"Columnas list: {', '.join(config['listColumns'])}")
    if args.dhcp_range is not None:
        config["dhcpRange"] = normalize_dhcp_range(args.dhcp_range)
        shown = config["dhcpRange"] or "sin configurar"
        changes.append(f"Rango DHCP: {shown}")
    if args.credentials is not None:
        path = args.credentials.strip()
        if not path:
            raise ValueError("la ruta de credenciales no puede estar vacía")
        config["credentials"] = path
        changes.append(f"Credenciales: {path}")
    if args.discovery is not None:
        config["discovery"] = args.discovery
        changes.append(f"Descubrimiento: {args.discovery}")
    if args.scan_profile is not None:
        config["scanProfile"] = args.scan_profile
        changes.append(f"Perfil de escaneo: {args.scan_profile}")
    if args.progress is not None:
        config["progress"] = args.progress == "on"
        changes.append(f"Progreso: {args.progress}")
    if args.service_identification is not None:
        config["serviceIdentification"] = args.service_identification == "on"
        changes.append(f"Identificación de servicios: {args.service_identification}")
    if args.disconnected_retention is not None:
        config["disconnectedRetention"] = normalize_retention_mode(args.disconnected_retention)
        changes.append(f"Retención de desconectados: {config['disconnectedRetention']}")
    if args.disconnected_target is not None:
        config["disconnectedRetentionTarget"] = normalize_retention_target(args.disconnected_target)
        changes.append(f"Objetivo de retención: {config['disconnectedRetentionTarget']}")
    if args.disconnected_scope is not None:
        config["disconnectedRetentionScope"] = normalize_retention_scope(args.disconnected_scope)
        changes.append(f"Alcance de retención: {config['disconnectedRetentionScope']}")
    if args.workers is not None:
        if args.workers < 1:
            raise ValueError("workers debe ser mayor que cero")
        config["workers"] = args.workers
        changes.append(f"Workers: {args.workers}")
    if args.timeout is not None:
        if args.timeout <= 0:
            raise ValueError("timeout debe ser mayor que cero")
        config["timeout"] = args.timeout
        changes.append(f"Timeout: {args.timeout}")
    if args.scan_order is not None:
        config["scanOrder"] = args.scan_order
        changes.append(f"Orden de escaneo: {args.scan_order}")
    if args.max_hosts is not None:
        if args.max_hosts < 1:
            raise ValueError("max-hosts debe ser mayor que cero")
        config["maxHosts"] = args.max_hosts
        changes.append(f"Máximo de hosts: {args.max_hosts}")
    for argument, key, label in (
        (args.database, "database", "Base de elementos"),
        (args.physical_database, "physicalDatabase", "Base física LANWIRE"),
        (args.groups, "groups", "Base de grupos"),
        (args.log, "log", "Directorio de logs"),
        (args.projects_directory, "projectsDirectory", "Directorio de proyectos"),
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
        changes.append(f"Limpieza automática de logs: {state}")
    if args.log_retention_days is not None:
        if args.log_retention_days < 1:
            raise ValueError("la retención de logs debe ser de al menos 1 día")
        config["logRetentionDays"] = args.log_retention_days
        changes.append(f"Retención de logs: {args.log_retention_days} días")
    if args.error_log_level is not None:
        if not 1 <= args.error_log_level <= 59:
            raise ValueError("error-log-level debe estar entre 1 y 59")
        config["errorLogLevel"] = args.error_log_level
        changes.append(f"Nivel mínimo de errores en log: {args.error_log_level}")

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
        changes.append(f"Distribución TUI: {config['tuiPanelLayout']}")
    if args.tui_cli_percent is not None:
        config["tuiCliHeightPercent"] = normalize_cli_percent(args.tui_cli_percent)
        changes.append(f"Altura del CLI: {config['tuiCliHeightPercent']}%")
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
        changes.append("Proporciones de columnas TUI actualizadas")

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
        changes.append("Botones visibles del TUI actualizados")

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
        changes.append("Visibilidad de botones del TUI actualizada")

    path = save_config(config)
    if remote_changed:
        try:
            _configure_remote_access(config, bind, cidr, port)
        except PermissionError:
            changes.append(
                "Backend remoto: valores guardados; aplicación pendiente de permisos de administrador"
            )
    ok("CONFIGURADO", "\n".join((*changes, f"Archivo: {path}")))
    return 0


def _configure_remote_access(config: dict, bind: str, cidr: str, port: int) -> None:
    import os
    import signal
    from contextlib import suppress

    from lanctl.apps.access.keys import generate_host_key
    from lanctl.apps.access.service import AccessService, access_process_running
    from lanctl.core.paths import application_path

    previous_scope = os.environ.get("LANCTL_DATA_SCOPE")
    os.environ["LANCTL_DATA_SCOPE"] = config["remoteAccessBackend"]
    try:
        access = AccessService(
            application_path(config["accessConfig"]),
            application_path(config["accessUsers"]),
        )
        access.initialize()
        was_enabled = bool(access.config()["ssh"].get("enabled"))
        if bind and cidr:
            access.configure(
                "ssh",
                bind=bind,
                cidr=cidr,
                port=port,
                password_authentication=config["remoteAccessPasswordAuthentication"],
            )
        access_config = access.config()
        access_config["control"]["forcedView"] = config["remoteAccessForcedView"]
        if config["remoteAccessEnabled"] and not access_config["ssh"].get("hostKey"):
            access_config["ssh"]["hostKey"] = generate_host_key(
                application_path("data/lc/access/ssh_host_ed25519_key")
            )
        access.save_config(access_config)
        if config["remoteAccessEnabled"]:
            if not was_enabled:
                access.enable("ssh")
            if config["remoteAccessBackend"] == "user" and not access_process_running(
                access.config()["ssh"]
            ):
                from lanctl.apps.ip.interfaces.cli.commands.access import _start_service_process

                _start_service_process(access, "ssh")
        else:
            current = access.config()["ssh"]
            pid = current.get("processId")
            if pid and access_process_running(current):
                with suppress(OSError):
                    os.kill(int(pid), signal.SIGTERM)
            access.disable("ssh")
    finally:
        if previous_scope is None:
            os.environ.pop("LANCTL_DATA_SCOPE", None)
        else:
            os.environ["LANCTL_DATA_SCOPE"] = previous_scope
