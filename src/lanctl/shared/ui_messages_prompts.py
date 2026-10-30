"""Reviewed bilingual help messages for advanced commands and shared services."""

PROMPT_MESSAGES = {
    "LANCTL.UI.PROMPT.THE_COMMAND_RETURNED_NO_CONTENT": (
        "The command returned no content.",
        "El comando no devolvió contenido.",
    ),
    "LANCTL.UI.PROMPT.PASSWORD_NOT_DISPLAYED": (
        "Password (not displayed): ",
        "Contraseña (no se mostrará): ",
    ),
    "LANCTL.UI.PROMPT.REPEAT_PASSWORD": ("Repeat password: ", "Repite la contraseña: "),
    "LANCTL.UI.PROMPT.NO_SAVED_CREDENTIALS": (
        "No saved credentials.",
        "No hay credenciales guardadas.",
    ),
    "LANCTL.UI.PROMPT.REMOTE_USER_PASSWORD": (
        "Remote user password: ",
        "Contraseña del usuario remoto: ",
    ),
    "LANCTL.UI.PROMPT.DESTINATION_PASSWORD_AT_LEAST_12_CHARACTERS": (
        "Destination password (at least 12 characters): ",
        "Contraseña del destino (mínimo 12 caracteres): ",
    ),
    "LANCTL.UI.PROMPT.PRESS_ENTER_TO_CONTINUE": (
        "Press Enter to continue…",
        "Pulsa Intro para continuar…",
    ),
    "LANCTL.UI.PROMPT.INVALID_COMMAND_SEE_HELP": (
        "Invalid command; see --help",
        "Comando no válido; consulta --help",
    ),
    "LANCTL.UI.PROMPT.OPTION": ("Option: ", "Opción: "),
    "LANCTL.UI.PROMPT.NOT_FOUND": ("Not found.", "No encontrada."),
    "LANCTL.UI.PROMPT.LANCTL_COLOR_LAYER_ACTIVE_USE_NATIVE_FOR_DIRECT_OPENSSH": (
        "LANCTL color layer active | use --native for direct OpenSSH",
        "Capa de color LANCTL activa | usa --native para OpenSSH directo",
    ),
    "LANCTL.UI.PROMPT.MAIN_COMMANDS_INFO_SENS_READ_FAN_ALL_READ_LAN_SHOW_HELP": (
        "Main commands: info, sens read, fan all read, lan show, help",
        "Comandos principales: info, sens read, fan all read, lan show, help",
    ),
    "LANCTL.UI.PROMPT.UNKNOWN_COMMAND_TYPE_HELP": (
        "Unknown command. Type 'help'.",
        "Comando desconocido. Escribe 'help'.",
    ),
    "LANCTL.UI.PROMPT.LANIP_NETWORK_INVENTORY": (
        "LANIP · Network inventory",
        "LANIP · Inventario de red",
    ),
    "LANCTL.UI.PROMPT.UNKNOWN_SERVICE": ("Unknown service", "Servicio desconocido"),
    "LANCTL.UI.PROMPT.THE_FINGERPRINT_WAS_ONLY_QUERIED_IT_HAS_NOT_BEEN_SAVED_YET": (
        "The fingerprint was only queried; it has not been saved yet.",
        "La huella solo se ha consultado; todavía no está guardada.",
    ),
    "LANCTL.UI.PROMPT.REGISTERED_FUNCTION_ESP32_RACK_MANAGER_MONITOR": (
        "Registered function: ESP32 rack manager/monitor",
        "Función registrada: gestor/monitor del rack ESP32",
    ),
    "LANCTL.UI.PROMPT.REQUESTED_PERMISSIONS_BEFORE_INSTALLATION": (
        "Requested permissions before installation:",
        "Permisos solicitados antes de instalar:",
    ),
    "LANCTL.UI.PROMPT.ENABLE_IT_WITH_LANCTL_PLUGIN_ENABLE_ID_GRANT_ALL": (
        " Enable it with: lanctl plugin enable ID --grant-all",
        " Actívalo con: lanctl plugin enable ID --grant-all",
    ),
    "LANCTL.UI.PROMPT.NO_PLUGINS_INSTALLED": (
        "No plugins installed.",
        "No hay complementos instalados.",
    ),
    "LANCTL.UI.PROMPT.NO_ELEMENTS_WERE_DELETED": (
        "No elements were deleted.",
        "No se ha eliminado ningún elemento.",
    ),
    "LANCTL.UI.PROMPT.SETTINGS_SAVED": ("Settings saved.", "Configuración guardada."),
    "LANCTL.UI.PROMPT.NEW_VALUE_JSON_FOR_LISTS_BOOLEANS_EMPTY_CANCEL": (
        "New value (JSON for lists/booleans; empty: cancel): ",
        "Nuevo valor (JSON para listas/booleanos; vacío: cancelar): ",
    ),
    "LANCTL.UI.PROMPT.CATEGORY_0_BACK": ("Category (0: back): ", "Categoría (0: volver): "),
    "LANCTL.UI.PROMPT.TUI_COLUMN_PROPORTIONS_UPDATED": (
        "TUI column proportions updated",
        "Proporciones de columnas TUI actualizadas",
    ),
    "LANCTL.UI.PROMPT.VISIBLE_TUI_BUTTONS_UPDATED": (
        "Visible TUI buttons updated",
        "Botones visibles del TUI actualizados",
    ),
    "LANCTL.UI.PROMPT.TUI_BUTTON_VISIBILITY_UPDATED": (
        "TUI button visibility updated",
        "Visibilidad de botones del TUI actualizada",
    ),
    "LANCTL.UI.PROMPT.NEW_REMOTE_PASSWORD": ("New remote password: ", "Nueva contraseña remota: "),
    "LANCTL.UI.PROMPT.REPEAT_REMOTE_PASSWORD": (
        "Repeat remote password: ",
        "Repite la contraseña remota: ",
    ),
    "LANCTL.UI.PROMPT.LANCTL_REMOTE_ACCESS_SSH_HTTPS_REMAIN_OFF_UNTIL_FINAL_CONFIRMATION": (
        "LANCTL REMOTE ACCESS (SSH/HTTPS remain off until final confirmation)",
        "ACCESO REMOTO LANCTL (SSH/HTTPS permanecen apagados hasta la confirmación final)",
    ),
    "LANCTL.UI.PROMPT.REMOTE_PASSWORD": ("Remote password: ", "Contraseña remota: "),
    "LANCTL.UI.PROMPT.ADMINISTRATOR_ACCOUNT": (
        "Administrator account: ",
        "Cuenta administradora: ",
    ),
    "LANCTL.UI.PROMPT.SSH_PUBLIC_KEY_PATH_OPTIONAL": (
        "SSH public key (path, optional): ",
        "Clave pública SSH (ruta, opcional): ",
    ),
    "LANCTL.UI.PROMPT.INVALID_SESSION_ACTION": (
        "invalid session action",
        "acción de sesión no válida",
    ),
    "LANCTL.UI.PROMPT.NO_PROJECT_SELECTED": (
        "No project selected",
        "No hay ningún proyecto seleccionado",
    ),
    "LANCTL.UI.PROMPT.PLAN_ACCEPTED_BY_FAKECISCOADAPTER_NO_NETWORK_CONNECTION_EXISTS": (
        "Plan accepted by FakeCiscoAdapter; no network connection exists.",
        "Plan aceptado por FakeCiscoAdapter; no existe conexión de red.",
    ),
    "LANCTL.UI.PROMPT.MANAGED_CISCO_TERMINAL_SIMULATED_ADAPTER_TYPE_HELP_OR_EXIT": (
        "Managed Cisco terminal (simulated adapter). Type help or exit.",
        "Terminal Cisco gestionada (adaptador simulado). Escribe help o exit.",
    ),
    "LANCTL.UI.PROMPT.PLAN_VALIDATED_NO_COMMAND_WAS_EXECUTED": (
        "Plan validated; no command was executed.",
        "Plan validado; no se ha ejecutado ningún comando.",
    ),
    "LANCTL.UI.PROMPT.THE_PLAN_WAS_NOT_SENT_TO_THE_ADAPTER": (
        "The plan was not sent to the adapter.",
        "El plan no se ha enviado al adaptador.",
    ),
    "LANCTL.UI.PROMPT.NO_PORT_SELECTED": ("No port selected.", "Ningún puerto seleccionado."),
    "LANCTL.UI.PROMPT.NONE_DETECTED_IN_THE_EXAMINED_SET": (
        "  None detected in the examined set.",
        "  Ninguno detectado en el conjunto examinado.",
    ),
    "LANCTL.UI.PROMPT.WAKE_ON_LAN_OPTION": ("Wake-on-LAN option.", "Opción Wake-on-LAN."),
    "LANCTL.UI.PROMPT.THE_DEVICE_WAS_NOT_DETECTED_SENDING_THE_PACKET_DOES_NOT_GUARANTEE_WAKE_UP": (
        "The device was not detected; sending the packet does not guarantee wake-up",
        "El dispositivo no fue detectado; el paquete enviado no garantiza el encendido",
    ),
    "LANCTL.UI.PROMPT.CONFIGURE_SSH_TRANSPORT_WITH_WOL_NAME_CONFIGURE": (
        "Configure SSH transport with 'wol NAME configure'",
        "Configura el transporte SSH con 'wol NAME configure'",
    ),
    "LANCTL.UI.PROMPT.DEPENDENCY_NOT_COMPLETED": (
        "Dependency not completed",
        "Dependencia no completada",
    ),
    "LANCTL.UI.PROMPT.COMMAND_CHAINING_IS_DISABLED_IN_SETTINGS_ADVANCED": (
        "command chaining is disabled in SETTINGS/ADVANCED",
        "el encadenamiento de comandos está desactivado en SETTINGS/AVANZADO",
    ),
    "LANCTL.UI.PROMPT.SIMULATED_PROVIDER_DISABLED": (
        "Simulated provider disabled",
        "Proveedor simulado desactivado",
    ),
    "LANCTL.UI.PROMPT.NO_IDF_PREFIXES": ("No IDF prefixes.", "No hay prefijos IDF."),
    "LANCTL.UI.PROMPT.NO_PREFIXES_DEFINED": ("No prefixes defined.", "No hay prefijos definidos."),
}

PROMPT_LOCATIONS = {
    "LANCTL.UI.PROMPT.NO_SAVED_CREDENTIALS": ("LANACCESS", "SHARED"),
    "LANCTL.UI.PROMPT.REMOTE_USER_PASSWORD": ("LANACCESS", "SHARED"),
    "LANCTL.UI.PROMPT.DESTINATION_PASSWORD_AT_LEAST_12_CHARACTERS": ("LANACCESS", "SHARED"),
    "LANCTL.UI.PROMPT.PRESS_ENTER_TO_CONTINUE": ("LANACCESS", "SHARED"),
    "LANCTL.UI.PROMPT.INVALID_COMMAND_SEE_HELP": ("LANACCESS", "SHARED"),
    "LANCTL.UI.PROMPT.OPTION": ("LANACCESS", "SHARED"),
    "LANCTL.UI.PROMPT.NOT_FOUND": ("LANACCESS", "SHARED"),
    "LANCTL.UI.PROMPT.LANCTL_COLOR_LAYER_ACTIVE_USE_NATIVE_FOR_DIRECT_OPENSSH": ("LANIP", "SHARED"),
    "LANCTL.UI.PROMPT.MAIN_COMMANDS_INFO_SENS_READ_FAN_ALL_READ_LAN_SHOW_HELP": ("LANIP", "SHARED"),
    "LANCTL.UI.PROMPT.UNKNOWN_COMMAND_TYPE_HELP": ("LANIP", "SHARED"),
    "LANCTL.UI.PROMPT.LANIP_NETWORK_INVENTORY": ("LANIP", "GUI"),
    "LANCTL.UI.PROMPT.UNKNOWN_SERVICE": ("LANIP", "GUI"),
    "LANCTL.UI.PROMPT.THE_FINGERPRINT_WAS_ONLY_QUERIED_IT_HAS_NOT_BEEN_SAVED_YET": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.REGISTERED_FUNCTION_ESP32_RACK_MANAGER_MONITOR": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.REQUESTED_PERMISSIONS_BEFORE_INSTALLATION": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.ENABLE_IT_WITH_LANCTL_PLUGIN_ENABLE_ID_GRANT_ALL": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NO_PLUGINS_INSTALLED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NO_ELEMENTS_WERE_DELETED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.SETTINGS_SAVED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NEW_VALUE_JSON_FOR_LISTS_BOOLEANS_EMPTY_CANCEL": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.CATEGORY_0_BACK": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.TUI_COLUMN_PROPORTIONS_UPDATED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.VISIBLE_TUI_BUTTONS_UPDATED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.TUI_BUTTON_VISIBILITY_UPDATED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NEW_REMOTE_PASSWORD": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.REPEAT_REMOTE_PASSWORD": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.LANCTL_REMOTE_ACCESS_SSH_HTTPS_REMAIN_OFF_UNTIL_FINAL_CONFIRMATION": (
        "LANIP",
        "CLI",
    ),
    "LANCTL.UI.PROMPT.REMOTE_PASSWORD": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.ADMINISTRATOR_ACCOUNT": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.SSH_PUBLIC_KEY_PATH_OPTIONAL": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.INVALID_SESSION_ACTION": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NO_PROJECT_SELECTED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.PLAN_ACCEPTED_BY_FAKECISCOADAPTER_NO_NETWORK_CONNECTION_EXISTS": (
        "LANIP",
        "CLI",
    ),
    "LANCTL.UI.PROMPT.MANAGED_CISCO_TERMINAL_SIMULATED_ADAPTER_TYPE_HELP_OR_EXIT": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.PLAN_VALIDATED_NO_COMMAND_WAS_EXECUTED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.THE_PLAN_WAS_NOT_SENT_TO_THE_ADAPTER": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NO_PORT_SELECTED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NONE_DETECTED_IN_THE_EXAMINED_SET": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.WAKE_ON_LAN_OPTION": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.THE_DEVICE_WAS_NOT_DETECTED_SENDING_THE_PACKET_DOES_NOT_GUARANTEE_WAKE_UP": (
        "LANIP",
        "CLI",
    ),
    "LANCTL.UI.PROMPT.CONFIGURE_SSH_TRANSPORT_WITH_WOL_NAME_CONFIGURE": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.DEPENDENCY_NOT_COMPLETED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.COMMAND_CHAINING_IS_DISABLED_IN_SETTINGS_ADVANCED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.SIMULATED_PROVIDER_DISABLED": ("LANIP", "CLI"),
    "LANCTL.UI.PROMPT.NO_IDF_PREFIXES": ("LANWIRE", "CLI"),
    "LANCTL.UI.PROMPT.NO_PREFIXES_DEFINED": ("LANWIRE", "CLI"),
}
