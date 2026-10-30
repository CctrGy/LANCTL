"""Reviewed bilingual help messages for advanced commands and shared services."""

BLOCK_MESSAGES = {
    "LANCTL.UI.BLOCK.TR_064_COMMANDS_SERVICES_CALL_SERVICE_ACTION_NAME_VALUE_HELP_EXIT_FOR_SAFETY_ACTION_MUST_BEGIN_": (
        "TR-064 commands:\n  services\n  call SERVICE ACTION [Name=Value ...]\n  help\n  exit\n\nFor safety, ACTION must begin with Get. This terminal is read-only.",
        "Comandos TR-064:\n  services\n  call SERVICIO ACCION [Nombre=Valor ...]\n  help\n  exit\n\nPor seguridad, ACCION debe comenzar por Get. Esta terminal es de solo lectura.",
    ),
    "LANCTL.UI.BLOCK.LANCTL_SETTINGS_1_ENTIRE_PROGRAM_2_ACTIVE_PROJECT_0_BACK": (
        "\nLANCTL settings\n1. Entire program\n2. Active project\n0. Back",
        "\nConfiguración LANCTL\n1. Programa completo\n2. Proyecto activo\n0. Volver",
    ),
    "LANCTL.UI.BLOCK.SETTINGS_CLOSED": ("\nSettings closed.", "\nConfiguración cerrada."),
    "LANCTL.UI.BLOCK.MANAGED_CISCO_COMMANDS_SHOW_COMMAND_PORT_LIST_PORT_LABEL_PORT_NAME_PORT_UNLABEL_PORT_PORT_SHOW_": (
        "Managed Cisco commands:\n  show COMMAND\n  port list\n  port label PORT NAME\n  port unlabel PORT\n  port show [PORT] status|description|config|errors|vlan\n  port set [PORT] description|speed|duplex VALUE\n  port enable|disable|reset [PORT]\n  start|stop|reset [PORT]\n  save-config\n  terminal\n\nGlobal options: --profile PROFILE --dry-run --yes\nThis phase uses a simulated adapter and does not connect to the switch.",
        "Comandos Cisco gestionados:\n  show COMANDO\n  port list\n  port label PUERTO NOMBRE\n  port unlabel PUERTO\n  port show [PUERTO] status|description|config|errors|vlan\n  port set [PUERTO] description|speed|duplex VALOR\n  port enable|disable|reset [PUERTO]\n  start|stop|reset [PUERTO]\n  save-config\n  terminal\n\nOpciones globales: --profile PERFIL --dry-run --yes\nEsta fase utiliza un adaptador simulado y no conecta con el switch.",
    ),
    "LANCTL.UI.BLOCK.RESULTS_EXIST_ONLY_DURING_THIS_EXECUTION_AND_WILL_NOT_BE_STORED": (
        "Results exist only during this execution and will not be stored.\n",
        "Los resultados existen únicamente durante esta ejecución y no se almacenarán.\n",
    ),
    "LANCTL.UI.BLOCK.LANCTL_INTERACTIVE_CLI_CONTEXT_COMMANDS_SELECT_ELEMENT_SELECT_AN_ELEMENT_BY_IP_MAC_ALIAS_OR_NAM": (
        "LANCTL interactive CLI\n\nContext commands:\n  select ELEMENT       Select an element by IP, MAC, alias or name.\n  info | selected      Show selected element information.\n  deselect             Clear the current selection.\n  clear | cls          Clear the screen and preserve context.\n  history              Show commands entered during the session.\n  version              Show the LANCTL version.\n  help [COMMAND]       Show general or command help.\n  exit                 Close the CLI.\n\nYou can chain commands with ; when the advanced option is enabled:\n  select JL1 ; element -cnf O ; info\n\nWhen an element is selected, you can omit it, for example:\n  select SW\n  element\n  scan --ports 22,80,443\n  ssh probe\n  switch port list\n",
        "CLI interactiva de LANCTL\n\nComandos de contexto:\n  select ELEMENTO       Selecciona un elemento por IP, MAC, alias o nombre.\n  info | selected       Muestra la información del elemento seleccionado.\n  deselect              Limpia la selección actual.\n  clear | cls           Limpia la pantalla y conserva el contexto.\n  history               Muestra los comandos escritos durante la sesión.\n  version               Muestra la versión de LANCTL.\n  help [COMANDO]        Muestra ayuda general o la ayuda de un comando.\n  exit                  Cierra la CLI.\n\nPuedes encadenar órdenes con ; cuando la opción avanzada está activada:\n  select JL1 ; element -cnf O ; info\n\nCuando hay un elemento seleccionado puedes omitirlo, por ejemplo:\n  select SW\n  element\n  scan --ports 22,80,443\n  ssh probe\n  switch port list\n",
    ),
    "LANCTL.UI.BLOCK.SELECT_ENTER_CONNECT_ESC_BACK": (
        "\n↑/↓ select · Enter connect · Esc back",
        "\n↑/↓ seleccionar · Enter conectar · Esc volver",
    ),
    "LANCTL.UI.BLOCK.OPTION_ENTER_OPEN_F3_FOLLOW_ESC_BACK": (
        "\n↑/↓ option · Enter open · F3 follow · Esc back",
        "\n↑/↓ opción · Enter abrir · F3 seguir · Esc volver",
    ),
    "LANCTL.UI.BLOCK.PORT_F3_FOLLOW_CABLE_TAB_ENTER_OPTIONS_ESC_CLOSE": (
        "\n↑/↓ port · F3 follow cable · Tab/Enter options · Esc close",
        "\n↑/↓ puerto · F3 seguir cable · Tab/Enter opciones · Esc cerrar",
    ),
    "LANCTL.UI.BLOCK.SELECT_CHANGE_CTRL_S_SAVE_ESC_CLOSE": (
        "\n\n  ↑/↓ select   ←/→ change   Ctrl+S save   Esc close",
        "\n\n  ↑/↓ seleccionar   ←/→ cambiar   Ctrl+S guardar   Esc cerrar",
    ),
    "LANCTL.UI.BLOCK.LANWIRE_DOES_NOT_LOAD_LCP_PLUGINS_THE_PHYSICAL_EDITOR_USES_ONLY_ITS_LOCAL_IDF_DATABASE_SO_THAT_": (
        "  LANWIRE does not load LCP plugins.\n\n  The physical editor uses only its local IDF database so that\n  topology and connections remain deterministic.",
        "  LANWIRE no carga plugins LCP.\n\n  El editor físico usa únicamente su base IDF local para que\n  la topología y sus conexiones sigan siendo deterministas.",
    ),
}

BLOCK_LOCATIONS = {
    "LANCTL.UI.BLOCK.LANCTL_SETTINGS_1_ENTIRE_PROGRAM_2_ACTIVE_PROJECT_0_BACK": ("LANIP", "CLI"),
    "LANCTL.UI.BLOCK.SETTINGS_CLOSED": ("LANIP", "CLI"),
    "LANCTL.UI.BLOCK.RESULTS_EXIST_ONLY_DURING_THIS_EXECUTION_AND_WILL_NOT_BE_STORED": (
        "LANIP",
        "CLI",
    ),
    "LANCTL.UI.BLOCK.SELECT_ENTER_CONNECT_ESC_BACK": ("LANWIRE", "TUI"),
    "LANCTL.UI.BLOCK.OPTION_ENTER_OPEN_F3_FOLLOW_ESC_BACK": ("LANWIRE", "TUI"),
    "LANCTL.UI.BLOCK.PORT_F3_FOLLOW_CABLE_TAB_ENTER_OPTIONS_ESC_CLOSE": ("LANWIRE", "TUI"),
    "LANCTL.UI.BLOCK.SELECT_CHANGE_CTRL_S_SAVE_ESC_CLOSE": ("LANWIRE", "TUI"),
    "LANCTL.UI.BLOCK.LANWIRE_DOES_NOT_LOAD_LCP_PLUGINS_THE_PHYSICAL_EDITOR_USES_ONLY_ITS_LOCAL_IDF_DATABASE_SO_THAT_": (
        "LANWIRE",
        "TUI",
    ),
}
