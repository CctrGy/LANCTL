"""Reviewed dynamic presentation templates. Values preserve their original formatting."""

DYNAMIC_MESSAGES = {
    "LANCTL.UI.MESSAGE.LAST_OPERATION_VALUE_CODE_VALUE": (
        "Last operation: {value0} (code {value1}).",
        "Última operación: {value0} (código {value1}).",
    ),
    "LANCTL.UI.MESSAGE.VALUE_VALUE_VALUE_PGUP_PGDN_HOME_END_ESC_ENTER_BACK": (
        "{value0}-{value1} / {value2} · ↑↓ PgUp/PgDn Home/End · Esc/Enter back",
        "{value0}-{value1} / {value2} · ↑↓ PgUp/PgDn Inicio/Fin · Esc/Enter volver",
    ),
    "LANCTL.UI.MESSAGE.PAGE_VALUE_VALUE_N_B_PAGES_L_REFRESH_A_ADD_E_DELETE_C_COMMAND_D_DIAGNOSTICS_Q_QUIT": (
        "Page {value0}/{value1} · N/B pages | L Refresh | A Add | E Delete | C Command | D Diagnostics | Q Quit",
        "Página {value0}/{value1} · N/B páginas | L Refrescar | A Añadir | E Eliminar | C Comando | D Diagnóstico | Q Salir",
    ),
    "LANCTL.UI.MESSAGE.VALUE_CAN_OPEN_PLUGINS_PROJECTS_OR_SETTINGS_DIRECTLY": (
        "{value0} Can open PLUGINS, PROJECTS or SETTINGS directly.",
        "{value0} Puede abrir directamente PLUGINS, PROJECTS o SETTINGS.",
    ),
    "LANCTL.UI.MESSAGE.GROUP_CREATED_VALUE": ("Group created: {value0}", "Grupo creado: {value0}"),
    "LANCTL.UI.MESSAGE.PROJECT_LOADED_VALUE": (
        "Project loaded: {value0}",
        "Proyecto cargado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.EMPTY_PROJECT_CREATED_VALUE": (
        "Empty project created: {value0}",
        "Proyecto vacío creado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.ELEMENT_DELETED_VALUE": (
        "Element deleted: {value0}",
        "Elemento eliminado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PROJECT_SAVED_VALUE": (
        "Project saved: {value0}",
        "Proyecto guardado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PROJECT_CREATED_VALUE": (
        "Project created: {value0}",
        "Proyecto creado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.VALUE_IS_AVAILABLE": ("{value0} is available", "{value0} está disponible"),
    "LANCTL.UI.MESSAGE.WAKE_SIGNAL_SENT_TO_VALUE": (
        "Wake signal sent to {value0}",
        "Señal de encendido enviada a {value0}",
    ),
    "LANCTL.UI.MESSAGE.KEY_VALUE_CLI_OPTION_VALUE_STATE_VALUE": (
        "  Key: {value0}  ·  CLI option: {value1}  ·  State: {value2}",
        "  Clave: {value0}  ·  Opción CLI: {value1}  ·  Estado: {value2}",
    ),
    "LANCTL.UI.MESSAGE.VERSION_VALUE": ("Version      : {value0}", "Versión      : {value0}"),
    "LANCTL.UI.MESSAGE.DESCRIPTION_VALUE": ("Description  : {value0}", "Descripción  : {value0}"),
    "LANCTL.UI.MESSAGE.LOCATION_VALUE": ("Location     : {value0}", "Ubicación    : {value0}"),
    "LANCTL.UI.MESSAGE.NO_PROJECTS_IN_VALUE": (
        "(No projects in {value0})",
        "(No hay proyectos en {value0})",
    ),
    "LANCTL.UI.MESSAGE.VALUE_SAVED_SECTION_FIELD_TAB_EDIT_F2_ESC_CLOSE": (
        "{value0} saved · ←/→ section  ↑/↓ field  Tab edit  F2/Esc close",
        "{value0} guardado · ←/→ sección  ↑/↓ campo  Tab editar  F2/Esc cerrar",
    ),
    "LANCTL.UI.MESSAGE.LIST_FILTER_VALUE_VALUE_ELEMENTS": (
        "List filter: {value0} | {value1} elements",
        "Filtro de lista: {value0} | {value1} elementos",
    ),
    "LANCTL.UI.MESSAGE.PENDING_CHANGES_VALUE": (
        "  Pending changes: {value0}",
        "  Cambios pendientes: {value0}",
    ),
    "LANCTL.UI.MESSAGE.DETECTED_ALIAS_VALUE": (
        "  Detected alias: {value0}",
        "  Alias detectado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.DETECTED_HOSTNAME_VALUE": (
        "  Detected hostname: {value0}",
        "  Hostname detectado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PROBABLE_TYPE_VALUE": (
        "  Probable type: {value0}",
        "  Tipo probable: {value0}",
    ),
    "LANCTL.UI.MESSAGE.DETECTED_BY_VALUE": ("  Detected by: {value0}", "  Detectado por: {value0}"),
    "LANCTL.UI.MESSAGE.LAST_DETECTION_VALUE": (
        "  Last detection: {value0}",
        "  Ultima deteccion: {value0}",
    ),
    "LANCTL.UI.MESSAGE.LAST_SEEN_VALUE": ("  Last seen: {value0}", "  Ultima vez visto: {value0}"),
    "LANCTL.UI.MESSAGE.REFERENCED_CREDENTIALS_VALUE": (
        "  Referenced credentials: {value0}",
        "  Credenciales referenciadas: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PROTOCOL_OPTIONS_VALUE": (
        "  Protocol options: {value0}",
        "  Opciones de protocolo: {value0}",
    ),
    "LANCTL.UI.MESSAGE.OPEN_PORTS_VALUE": (
        "  Open ports: {value0}",
        "  Puertos abiertos: {value0}",
    ),
    "LANCTL.UI.MESSAGE.EXAMINED_PORTS_VALUE": (
        "  Examined ports: {value0}",
        "  Puertos examinados: {value0}",
    ),
    "LANCTL.UI.MESSAGE.ANALYSIS_DURATION_VALUE_S": (
        "  Analysis duration: {value0} s",
        "  Duracion del analisis: {value0} s",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_EDIT_METADATA_VALUE": (
        "Could not edit metadata: {value0}",
        "No se pudieron editar los metadatos: {value0}",
    ),
    "LANCTL.UI.MESSAGE.COMMAND_PREPARED_VALUE_COMPLETE_ITS_ARGUMENTS_AND_PRESS_ENTER": (
        "Command prepared: {value0}. Complete its arguments and press Enter.",
        "Comando preparado: {value0}. Completa sus argumentos y pulsa Enter.",
    ),
    "LANCTL.UI.MESSAGE.SELECTION_PINNED_TO_VALUE_USE_CNF_OR_CNF_STATE_TO_RELEASE_IT": (
        "Selection pinned to {value0}. Use 'cnf' or 'cnf STATE' to release it.",
        "Selección fijada en {value0}. Usa 'cnf' o 'cnf ESTADO' para liberarla.",
    ),
    "LANCTL.UI.MESSAGE.VALUEVALUE_SCANNING_VALUE_VALUEELEMENTS_FOUND_VALUEVALUE": (
        "{value0}{value1} SCANNING {value2} {value3}Elements found: {value4}{value5}",
        "{value0}{value1} ESCANEANDO {value2} {value3}Elementos encontrados: {value4}{value5}",
    ),
    "LANCTL.UI.MESSAGE.VALUETHE_LIST_FILLS_IN_REAL_TIME_VALUE": (
        "{value0}The list fills in real time.{value1}",
        "{value0}La lista se completa en tiempo real.{value1}",
    ),
    "LANCTL.UI.MESSAGE.VALUETHE_LAST_VALID_STATE_IS_PRESERVED_DATA_IS_NOT_UP_TO_DATE_VALUE": (
        "{value0}The last valid state is preserved; data is not up to date.{value1}",
        "{value0}Se conserva el último estado válido; los datos no están actualizados.{value1}",
    ),
    "LANCTL.UI.MESSAGE.VALUEVALUE_NETWORK_VALUE_NO_SCAN_IN_THIS_SESSION": (
        "{value0}{value1} NETWORK {value2} No scan in this session",
        "{value0}{value1} RED {value2} Sin escaneo en esta sesión",
    ),
    "LANCTL.UI.MESSAGE.HISTORY_VALUE_EVENTS_ENTER_DETAILS_ESC_INVENTORY": (
        "History: {value0} events | Enter details | Esc inventory",
        "Historial: {value0} eventos | Enter detalle | Esc inventario",
    ),
    "LANCTL.UI.MESSAGE.EXIT_CODE_VALUE": ("Exit code: {value0}", "Código de salida: {value0}"),
    "LANCTL.UI.MESSAGE.INVENTORY_RELOADED_VALUE_ELEMENTS_NO_NETWORK_SCAN": (
        "Inventory reloaded | {value0} elements | no network scan.",
        "Inventario recargado | {value0} elementos | sin escaneo de red.",
    ),
    "LANCTL.UI.MESSAGE.PROJECT_SAVED_SUCCESSFULLY_VALUE_VALUE": (
        "Project saved successfully: {value0} ({value1}).",
        "Proyecto guardado correctamente: {value0} ({value1}).",
    ),
    "LANCTL.UI.MESSAGE.THE_SELECTED_ELEMENT_DOES_NOT_HAVE_VALUE_AVAILABLE": (
        "The selected element does not have {value0} available.",
        "El elemento seleccionado no tiene {value0} disponible.",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_SAVE_VALUE_TAB_EDIT_F2_ESC_CLOSE": (
        "Could not save: {value0} · Tab edit · F2/Esc close",
        "No se pudo guardar: {value0} · Tab editar · F2/Esc cerrar",
    ),
    "LANCTL.UI.MESSAGE.PROJECT_CREATED_AND_ACTIVATED_VALUE": (
        "Project created and activated: {value0}",
        "Proyecto creado y activado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PROJECT_DELETED_VALUE": (
        "Project deleted: {value0}",
        "Proyecto eliminado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PROJECT_ACTIVATED_VALUE": (
        "Project activated: {value0}",
        "Proyecto activado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.ERROR_VALUE_ESC_BACK": (
        "ERROR: {value0} · Esc back",
        "ERROR: {value0} · Esc volver",
    ),
    "LANCTL.UI.MESSAGE.ERROR_VALUE_VALUE_ENTER_RETRY_ESC_BACK": (
        "ERROR: {value0} [{value1}] · Enter retry · Esc back",
        "ERROR: {value0} [{value1}] · Enter reintentar · Esc volver",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_LOAD_THE_PLUGIN_MANAGER_VALUE": (
        "Could not load the plugin manager: {value0}",
        "No se pudo cargar el gestor de plugins: {value0}",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_UPDATE_PROJECTS_DB_VALUE": (
        "Could not update projects.db: {value0}",
        "No se pudo actualizar projects.db: {value0}",
    ),
    "LANCTL.UI.MESSAGE.COMPLETELY_DELETE_VALUE": (
        "Completely delete {value0}?",
        "Eliminar completamente {value0}?",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_SAVE_THE_PROJECT_VALUE": (
        "Could not save the project: {value0}",
        "No se pudo guardar el proyecto: {value0}",
    ),
    "LANCTL.UI.MESSAGE.THE_PROJECT_DID_NOT_NEED_SAVING_VALUE": (
        "The project did not need saving: {value0}.",
        "El proyecto no necesitó guardarse: {value0}.",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_COPY_TO_CLIPBOARD_VALUE": (
        "Could not copy to clipboard: {value0}",
        "No se pudo copiar al portapapeles: {value0}",
    ),
    "LANCTL.UI.MESSAGE.VALUE_ESC_CLOSE": ("{value0} · Esc close", "{value0} · Esc cerrar"),
    "LANCTL.UI.MESSAGE.COULD_NOT_CREATE_THE_PROJECT_VALUE": (
        "Could not create the project: {value0}",
        "No se pudo crear el proyecto: {value0}",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_DELETE_THE_PROJECT_VALUE": (
        "Could not delete the project: {value0}",
        "No se pudo eliminar el proyecto: {value0}",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_CHANGE_PROJECTS_VALUE": (
        "Could not change projects: {value0}",
        "No se pudo cambiar de proyecto: {value0}",
    ),
    "LANCTL.UI.MESSAGE.ERROR_VALUE_ESC_CLOSE": (
        "ERROR: {value0} · Esc close",
        "ERROR: {value0} · Esc cerrar",
    ),
    "LANCTL.UI.MESSAGE.ERROR_SAVING_VALUE_ESC_CANCEL": (
        "ERROR saving: {value0} · Esc cancel",
        "ERROR al guardar: {value0} · Esc cancelar",
    ),
    "LANCTL.UI.MESSAGE.FIXED_WIDTH_OF_VALUE_THIS_COLUMN_RETAINS_ALL_ITS_CHARACTERS": (
        "Fixed width of {value0}; this column retains all its characters.",
        "Anchura fija de {value0}; esta columna conserva todos sus caracteres.",
    ),
    "LANCTL.UI.MESSAGE.RELATIVE_WEIGHT_OF_VALUE_LANCTL_APPLIES_ITS_MINIMUM_AND_MAXIMUM_BOUNDS_AUTOMATICALLY": (
        "Relative weight of {value0}. LANCTL applies its minimum and maximum bounds automatically.",
        "Peso relativo de {value0}. LANCTL aplica automáticamente sus límites mínimo y máximo.",
    ),
    "LANCTL.UI.MESSAGE.THE_PROJECT_IS_NO_LONGER_AVAILABLE_VALUE": (
        "The project is no longer available: {value0}",
        "El proyecto ya no está disponible: {value0}",
    ),
    "LANCTL.UI.MESSAGE.FINGERPRINT_PINNED_FOR_VALUE_VALUE": (
        "Fingerprint pinned for {value0}: {value1}",
        "Huella fijada para {value0}: {value1}",
    ),
    "LANCTL.UI.MESSAGE.IDENTITY_MATCH_VALUE": (
        "Identity match: {value0}",
        "Coincidencia de identidad: {value0}",
    ),
    "LANCTL.UI.MESSAGE.CISCO_IDENTITY_BY_OUI_VALUE": (
        "Cisco identity by OUI: {value0}",
        "Identidad Cisco por OUI: {value0}",
    ),
    "LANCTL.UI.MESSAGE.COMPLETELY_DELETE_VALUE_VALUE_S_N": (
        "Completely delete {value0} ({value1})? [s/N]: ",
        "Eliminar completamente {value0} ({value1})? [s/N]: ",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_SAVE_VALUE": (
        "Could not save: {value0}",
        "No se ha podido guardar: {value0}",
    ),
    "LANCTL.UI.MESSAGE.STARTUP_INTERFACE_VALUE": (
        "Startup interface: {value0}",
        "Interfaz de inicio: {value0}",
    ),
    "LANCTL.UI.MESSAGE.SAVE_INTERVAL_VALUE_MINUTES": (
        "Save interval: {value0} minutes",
        "Intervalo de guardado: {value0} minutos",
    ),
    "LANCTL.UI.MESSAGE.ASK_TO_SAVE_AFTER_COMMAND_VALUE": (
        "Ask to save after command: {value0}",
        "Consulta de guardado al terminar comando: {value0}",
    ),
    "LANCTL.UI.MESSAGE.CHAINED_CLI_COMMANDS_VALUE": (
        "Chained CLI commands: {value0}",
        "Comandos encadenados en CLI: {value0}",
    ),
    "LANCTL.UI.MESSAGE.LIST_COLUMNS_VALUE": ("List columns: {value0}", "Columnas list: {value0}"),
    "LANCTL.UI.MESSAGE.SCAN_PROFILE_VALUE": (
        "Scan profile: {value0}",
        "Perfil de escaneo: {value0}",
    ),
    "LANCTL.UI.MESSAGE.SERVICE_IDENTIFICATION_VALUE": (
        "Service identification: {value0}",
        "Identificación de servicios: {value0}",
    ),
    "LANCTL.UI.MESSAGE.DISCONNECTED_RETENTION_VALUE": (
        "Disconnected retention: {value0}",
        "Retención de desconectados: {value0}",
    ),
    "LANCTL.UI.MESSAGE.RETENTION_TARGET_VALUE": (
        "Retention target: {value0}",
        "Objetivo de retención: {value0}",
    ),
    "LANCTL.UI.MESSAGE.RETENTION_RANGE_VALUE": (
        "Retention range: {value0}",
        "Alcance de retención: {value0}",
    ),
    "LANCTL.UI.MESSAGE.SCAN_ORDER_VALUE": ("Scan order: {value0}", "Orden de escaneo: {value0}"),
    "LANCTL.UI.MESSAGE.MAXIMUM_HOSTS_VALUE": (
        "Maximum hosts: {value0}",
        "Máximo de hosts: {value0}",
    ),
    "LANCTL.UI.MESSAGE.AUTOMATIC_LOG_CLEANUP_VALUE": (
        "Automatic log cleanup: {value0}",
        "Limpieza automática de logs: {value0}",
    ),
    "LANCTL.UI.MESSAGE.LOG_RETENTION_VALUE_DAYS": (
        "Log retention: {value0} days",
        "Retención de logs: {value0} días",
    ),
    "LANCTL.UI.MESSAGE.MINIMUM_LOGGED_ERROR_LEVEL_VALUE": (
        "Minimum logged error level: {value0}",
        "Nivel mínimo de errores en log: {value0}",
    ),
    "LANCTL.UI.MESSAGE.TUI_LAYOUT_VALUE": ("TUI layout: {value0}", "Distribución TUI: {value0}"),
    "LANCTL.UI.MESSAGE.CLI_HEIGHT_VALUE": ("CLI height: {value0}%", "Altura del CLI: {value0}%"),
    "LANCTL.UI.MESSAGE.GROUP_RENAMED_TO_VALUE": (
        "Group renamed to {value0}",
        "Grupo renombrado a {value0}",
    ),
    "LANCTL.UI.MESSAGE.SIZE_VALUE_BYTES": (
        " Size    : {value0} bytes",
        " Tamaño  : {value0} bytes",
    ),
    "LANCTL.UI.MESSAGE.CONFIRM_VALUE_ON_VALUE_S_N": (
        "Confirm {value0} on {value1}? [s/N]: ",
        "Confirmar {value0} sobre {value1}? [s/N]: ",
    ),
    "LANCTL.UI.MESSAGE.DELETED_FROM_VALUE_VALUE": (
        "Deleted from {value0} ({value1})",
        "Eliminada de {value0} ({value1})",
    ),
    "LANCTL.UI.MESSAGE.DEMO_PREPARED_VALUE": (
        "Demo prepared: {value0}",
        "Demo preparada: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PROJECT_VERIFIED_VALUE": (
        "Project verified: {value0}",
        "Proyecto verificado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.EXAMINED_VALUE_OPEN_VALUE_DURATION_VALUE_S": (
        "Examined: {value0} | Open: {value1} | Duration: {value2} s",
        "Examinados: {value0} | Abiertos: {value1} | Duración: {value2} s",
    ),
    "LANCTL.UI.MESSAGE.PROBABLE_TYPE_VALUE_1B275E0A": (
        "  Probable type  : {value0}",
        "  Tipo probable  : {value0}",
    ),
    "LANCTL.UI.MESSAGE.ACTIVE_VALUE_SAVED_0_DURATION_VALUE_S": (
        "Active: {value0} | Saved: 0 | Duration: {value1} s",
        "Activos: {value0} | Guardados: 0 | Duración: {value1} s",
    ),
    "LANCTL.UI.MESSAGE.IMPORTED_AND_VERIFIED_VALUE_FILES": (
        "Imported and verified: {value0} files",
        "Importados y verificados: {value0} archivos",
    ),
    "LANCTL.UI.MESSAGE.RESTORED_AND_VALIDATED_VALUE": (
        "Restored and validated: {value0}",
        "Restaurado y validado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.VIRTUAL_NETWORK_CREATED_VALUE_VALUE": (
        "Virtual network created: {value0} | {value1}",
        "Red virtual creada: {value0} | {value1}",
    ),
    "LANCTL.UI.MESSAGE.DEVICE_DELETED_VALUE": (
        "Device deleted: {value0}",
        "Dispositivo eliminado: {value0}",
    ),
    "LANCTL.UI.MESSAGE.VIRTUAL_CLOCK_VALUES": (
        "Virtual clock: {value0}s",
        "Reloj virtual: {value0}s",
    ),
    "LANCTL.UI.MESSAGE.DEVICE_ADDED_VALUE": (
        "Device added: {value0}",
        "Dispositivo añadido: {value0}",
    ),
    "LANCTL.UI.MESSAGE.SHOWN_VALUE_ACTIVE_VALUE_UNDETECTED_VALUE_TOTAL_RECORDED_VALUE_PROFILE_VALUE_DISCOVERY_VALUE_OR": (
        "Shown: {value0} | Active: {value1} | Undetected: {value2} | Total recorded: {value3}\nProfile: {value4} | Discovery: {value5} | Order: {value6} | Timeout: {value7}s | ICMP: {value8} | ARP: {value9} | Unverified cache: {value10}",
        "Mostrados: {value0} | Activos: {value1} | No detectados: {value2} | Total registrados: {value3}\nPerfil: {value4} | Descubrimiento: {value5} | Orden: {value6} | Timeout: {value7}s | ICMP: {value8} | ARP: {value9} | Cache no verificada: {value10}",
    ),
    "LANCTL.UI.MESSAGE.INITIAL_TOPOLOGY_CREATED_VALUE_ELEMENTS": (
        "Initial topology created: {value0} elements",
        "Topología inicial creada: {value0} elementos",
    ),
    "LANCTL.UI.MESSAGE.NO_ELEMENTS_IN_GROUP_VALUE": (
        "No elements in group {value0}.",
        "No hay elementos con grupo {value0}.",
    ),
    "LANCTL.UI.MESSAGE.UNKNOWN_COMMAND_VALUE": (
        "Unknown command: {value0}",
        "Comando desconocido: {value0}",
    ),
    "LANCTL.UI.MESSAGE.PREFIX_VALUE_UPDATED_TO_VALUE": (
        "Prefix {value0} updated to {value1}",
        "Prefijo {value0} actualizado a {value1}",
    ),
    "LANCTL.UI.MESSAGE.PREFIX_VALUE_DEFINED_AS_VALUE": (
        "Prefix {value0} defined as {value1}",
        "Prefijo {value0} definido como {value1}",
    ),
    "LANCTL.UI.MESSAGE.DEFINITION_DELETED_VALUE": (
        "Definition deleted: {value0}",
        "Definición eliminada: {value0}",
    ),
    "LANCTL.UI.MESSAGE.SYNTAX_ERROR_VALUE": (
        "Syntax error: {value0}",
        "Error de sintaxis: {value0}",
    ),
    "LANCTL.UI.MESSAGE.NO_ELEMENTS_WITH_PREFIX_VALUE": (
        "No elements with prefix {value0}.",
        "No hay elementos con prefijo {value0}.",
    ),
    "LANCTL.UI.MESSAGE.UNDEFINED_PREFIX_VALUE": (
        "Undefined prefix: {value0}",
        "Prefijo no definido: {value0}",
    ),
    "LANCTL.UI.MESSAGE.EDIT_CABLE_VALUE": ("Edit cable {value0}", "Editar cable {value0}"),
    "LANCTL.UI.MESSAGE.CONNECTED_VALUE_TO_VALUE_VALUE": (
        "Connected {value0} to {value1}.{value2}",
        "Conectado {value0} a {value1}.{value2}",
    ),
    "LANCTL.UI.MESSAGE.DELETED_PORT_VALUE_VALUE": (
        "Deleted port {value0}.{value1}.",
        "Eliminado puerto {value0}.{value1}.",
    ),
    "LANCTL.UI.MESSAGE.DISCONNECTED_VALUE_FROM_VALUE_VALUE": (
        "Disconnected {value0} from {value1}.{value2}",
        "Desconectado {value0} de {value1}.{value2}",
    ),
    "LANCTL.UI.MESSAGE.VALUE_LINES": ("{value0} lines", "{value0} líneas"),
    "LANCTL.UI.MESSAGE.DISCONNECTED_SIDE_VALUE_OF_VALUE": (
        "Disconnected side {value0} of {value1}",
        "Desconectado el lado {value0} de {value1}",
    ),
    "LANCTL.UI.MESSAGE.CONNECTED_VALUE_TO_VALUE": (
        "Connected {value0} to {value1}",
        "Conectado {value0} a {value1}",
    ),
    "LANCTL.UI.MESSAGE.DISCONNECT_VALUE_BEFORE_DELETING_VALUE_VALUE": (
        "Disconnect {value0} before deleting {value1}.{value2}.",
        "Desconecta {value0} antes de eliminar {value1}.{value2}.",
    ),
    "LANCTL.UI.MESSAGE.ACTIVE_IDF_DATABASE_VALUE_TOPOLOGY_CHANGES_ARE_SAVED_ATOMICALLY_WHEN_EACH_EDIT_IS_CONFIRMED_LAN": (
        "  ACTIVE IDF DATABASE\n\n  {value0}\n\n  Topology changes are saved atomically when each edit\n  is confirmed. LANWIRE does not show projects, networks\n  or preferences from other launchers in this window.",
        "  BASE IDF ACTIVA\n\n  {value0}\n\n  Los cambios de topología se guardan de forma atómica al\n  confirmar cada edición. LANWIRE no muestra proyectos, redes\n  ni preferencias de otros launchers en esta ventana.",
    ),
    "LANCTL.UI.MESSAGE.YOU_WILL_DELETE_VALUE_ITS_CABLE_ENDPOINTS_WILL_BE_DISCONNECTED_AND_ASSOCIATED_RACK_REFERENCES_R": (
        "  You will delete {value0}.\n\n  Its cable endpoints will be disconnected and associated\n  rack references removed. Cables will remain\n  as free endpoints.\n\n  Enter confirm   Esc cancel",
        "  Vas a eliminar {value0}.\n\n  Se desconectarán sus extremos de cable y se eliminarán\n  referencias de rack asociadas. Los cables permanecerán\n  como extremos libres.\n\n  Enter confirmar   Esc cancelar",
    ),
    "LANCTL.UI.MESSAGE.VIEWING_VALUE_PRESS_ESC_TO_RETURN_TO_THE_LIST": (
        "Viewing {value0}. Press Esc to return to the list.",
        "Visualizando {value0}. Pulsa Esc para volver a la lista.",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_VALUE_VALUE": (
        "Could not {value0}: {value1}",
        "No se pudo {value0}: {value1}",
    ),
    "LANCTL.UI.MESSAGE.COULD_NOT_CONNECT_VALUE": (
        "Could not connect: {value0}",
        "No se pudo conectar: {value0}",
    ),
    "LANCTL.UI.MESSAGE.ACTIVE_LIST_VALUE": ("Active list: {value0}", "Lista activa: {value0}"),
    "LANCTL.UI.MESSAGE.DELETED_VALUE_PHYSICAL_LINKS_CLEARED": (
        "Deleted {value0}; physical links cleared.",
        "Eliminado {value0}; enlaces físicos limpiados.",
    ),
    "LANCTL.UI.MESSAGE.VALUE_DOES_NOT_EXIST": ("{value0} does not exist.", "No existe {value0}."),
    "LANCTL.UI.MESSAGE.VALUE_VIEW_ACTIVE": ("{value0} view active.", "Vista de {value0} activa."),
    "LANCTL.UI.MESSAGE.LOCATION_VALUE_RACK_VALUE_UVALUE_TRAY_VALUE": (
        "location: {value0} · rack: {value1} · U{value2} · tray: {value3}",
        "ubicación: {value0} · rack: {value1} · U{value2} · bandeja: {value3}",
    ),
}
