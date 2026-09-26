// Generado por tools/generate_web_reference.py. No editar.
window.LANCTL_REFERENCE = {
  "categories": [
    "Launchers",
    "Descubrimiento de red",
    "Inventario y búsqueda",
    "Comandos",
    "Diagnóstico de red",
    "Configuración",
    "Acceso remoto",
    "Automatización",
    "Datos y exportación",
    "Monitorización",
    "Infraestructura de red",
    "Grupos de comandos",
    "Inventario y edición",
    "Proyectos",
    "Plugins y expansiones",
    "Laboratorio virtual",
    "Cableado y topología",
    "Racks y salas técnicas",
    "Credenciales y acceso",
    "Archivos de documentación"
  ],
  "entries": [
    {
      "aliases": [
        "ip",
        "wire",
        "rack",
        "access",
        "monitor"
      ],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Muestra la versión común de la suite y termina.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la consola principal.",
          "flags": [
            "--cli",
            "-cli"
          ],
          "label": "--cli, -cli",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre el TUI principal.",
          "flags": [
            "-tui",
            "--tui"
          ],
          "label": "-tui, --tui",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Solicita UAC explícitamente para un launcher instalado en Windows.",
          "flags": [
            "--admin"
          ],
          "label": "--admin",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Launchers",
      "children": [
        "lanip",
        "lanwire",
        "lanrack",
        "lanaccess",
        "lanmon",
        "plugin",
        "settings",
        "language"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Orquestador raíz de las aplicaciones de la suite LANCTL.",
      "details": "Usage: LANCTL [-h] [--version] [--cli | -tui] [--admin] LAUNCHER ...\n\nOrquestador raíz de las aplicaciones de la suite LANCTL.\n\nArguments:\n  LAUNCHER\n    lanip (ip)        Inventario lógico, descubrimiento, IP, MAC y servicios.\n    lanwire (wire)    Cableado, puertos, paneles y topología física.\n    lanrack (rack)    Salas técnicas, racks, unidades U y equipos.\n    lanaccess (access)\n                      Usuarios, credenciales y accesos remotos.\n    lanmon (monitor)  Monitorización, eventos, incidencias e historial.\n    plugin            Administración compartida de la suite.\n    settings          Administración compartida de la suite.\n    language          Administración compartida de la suite.\n\nOptions:\n  -h, --help          Show this help and exit.\n  --version           Muestra la versión común de la suite y termina.\n  --cli, -cli         Abre la consola principal.\n  -tui, --tui         Abre el TUI principal.\n  --admin             Solicita UAC explícitamente para un launcher instalado en Windows.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanctl --tui",
        "lanctl lanip --help"
      ],
      "group": "LANCTL",
      "id": "command-lanctl",
      "kind": "launcher",
      "launcher": "LANCTL",
      "name": "LANCTL",
      "path": [
        "LANCTL"
      ],
      "title": "LANCTL",
      "usage": "LANCTL [-h] [--version] [--cli | -tui] [--admin] LAUNCHER ..."
    },
    {
      "aliases": [
        "-e",
        "connect",
        "credentials",
        "auth",
        "gateway",
        "downloadsettings",
        "download-settings",
        "cli",
        "projects",
        "plugins",
        "addon",
        "addons",
        "languages",
        "lang",
        "errors",
        "db",
        "wire"
      ],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Muestra la versión y termina.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Omite la salida correcta; conserva errores.",
          "flags": [
            "--quiet"
          ],
          "label": "--quiet",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Añade diagnóstico de ejecución a stderr.",
          "flags": [
            "--verbose"
          ],
          "label": "--verbose",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la GUI heredada (solo código fuente y con LANCTL_ENABLE_LEGACY_GUI=1).",
          "flags": [
            "--gui"
          ],
          "label": "--gui",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Open the persistent interactive LANCTL terminal.",
          "flags": [
            "--cli",
            "-cli"
          ],
          "label": "--cli, -cli",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "inventory",
            "plugins",
            "projects",
            "settings"
          ],
          "default": null,
          "description": "Open the advanced full-screen terminal interface. Puede abrir directamente PLUGINS, PROJECTS o SETTINGS.",
          "flags": [
            "-tui",
            "--tui"
          ],
          "label": "-tui, --tui",
          "metavar": "VENTANA",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Selecciona un proyecto VLF antes de abrir el TUI o ejecutar un comando.",
          "flags": [
            "-project",
            "--project"
          ],
          "label": "-project, --project",
          "metavar": "ARCHIVO.vlf",
          "required": false
        }
      ],
      "category": "Launchers",
      "children": [
        "ephemeral",
        "list",
        "recurrent",
        "ping",
        "open",
        "settings",
        "call",
        "search",
        "scan",
        "cnf",
        "credential",
        "GATEWAY",
        "downloadSettings",
        "protocol",
        "ssh",
        "radmin",
        "wol",
        "history",
        "monitor",
        "access",
        "smb",
        "terminal",
        "switch",
        "group",
        "element",
        "project",
        "plugin",
        "language",
        "error",
        "database",
        "demo",
        "lanwire",
        "lab"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Logical control of LAN devices and infrastructure.",
      "details": "Usage: LANIP [-h] [--version] [--quiet | --verbose] [--gui] [--cli] [-tui [VENTANA]]\n             [-project ARCHIVO.vlf]\n             COMANDO ...\n\nLogical control of LAN devices and infrastructure.\n\nArguments:\n  COMANDO\n    ephemeral (-e)            Escanea activos sin leer ni guardar ningún inventario.\n    list                      Escanea la LAN y muestra dispositivos activos e históricos.\n    recurrent                 Consulta los elementos recurrentes conocidos por LANCTL.\n    ping                      Comprueba puntualmente si un elemento responde por PING o ARP.\n    open (connect)            Abre un elemento con un cliente acorde al protocolo.\n    settings                  Consulta o modifica la configuración persistente de LANCTL.\n    call                      Resuelve un alias, una IP o una MAC a los datos del dispositivo.\n    search                    Busca dispositivos por alias, nombre, IP o MAC.\n    scan                      Inspecciona en profundidad un único elemento de la LAN.\n    cnf                       Asigna el estado CNF de un elemento por IP, MAC o alias.\n    credential (credentials, auth)\n                              Asocia credenciales cifradas a un elemento y protocolo.\n    GATEWAY (gateway)         Consulta y configura el gateway mediante TR-064.\n    downloadSettings (downloadsettings, download-settings)\n                              Alias heredado de «GATEWAY downloadSettings».\n    protocol                  Consulta o configura un protocolo de un elemento.\n    ssh                       Abre SSH o ejecuta una consulta show de solo lectura.\n    radmin                    Configura, comprueba o abre Radmin Viewer.\n    wol                       Enciende equipos mediante Wake-on-LAN y ejecuta secuencias seguras.\n    history                   Consulta eventos estructurados del proyecto VLF activo.\n    monitor                   Opera sesiones y checks del monitor LAN.\n    access                    Configura acceso remoto LAN seguro por SSH y HTTPS.\n    smb                       Descubre y abre recursos SMB de Windows.\n    terminal (cli)            Abre la terminal propia de un elemento según su protocolo.\n    switch                    Planifica comandos Cisco filtrados, remapeados y clasificados.\n    group                     Crea, edita y consulta grupos de elementos.\n    element                   Edita uno o varios campos de un elemento identificado por IP, MAC o\n                              alias.\n    project (projects)        Crea, actualiza e inspecciona proyectos LANCTL .vlf.\n    plugin (plugins, addon, addons)\n                              Gestiona complementos unificados LANCTL .lcp.\n    language (languages, lang)\n                              Manage LANCTL interface languages.\n    error (errors)            Consulta el catálogo por identificador 0eXXXXXXXX.\n    database (db)             Diagnostica y exporta datos.\n    demo                      Genera un recorrido reproducible sin depender de una red real.\n    lanwire (wire)            Abre LANWIRE o ejecuta uno de sus comandos sobre la base física\n                              compartida.\n    lab                       Gestiona redes LAN simuladas sin tráfico real.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --version                   Muestra la versión y termina.\n  --quiet                     Omite la salida correcta; conserva errores.\n  --verbose                   Añade diagnóstico de ejecución a stderr.\n  --gui                       Abre la GUI heredada (solo código fuente y con\n                              LANCTL_ENABLE_LEGACY_GUI=1).\n  --cli, -cli                 Open the persistent interactive LANCTL terminal.\n  -tui [VENTANA], --tui [VENTANA]\n                              Open the advanced full-screen terminal interface. Puede abrir\n                              directamente PLUGINS, PROJECTS o SETTINGS.\n  -project ARCHIVO.vlf, --project ARCHIVO.vlf\n                              Selecciona un proyecto VLF antes de abrir el TUI o ejecutar un\n                              comando.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip --tui",
        "lanip --help"
      ],
      "group": "LANIP",
      "id": "command-lanip",
      "kind": "launcher",
      "launcher": "LANIP",
      "name": "LANIP",
      "path": [
        "LANIP"
      ],
      "title": "LANIP",
      "usage": "LANIP [-h] [--version] [--quiet | --verbose] [--gui] [--cli] [-tui [VENTANA]]\n             [-project ARCHIVO.vlf]\n             COMANDO ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": "normal",
          "description": "Prioriza un barrido ARP rápido.",
          "flags": [
            "--fast"
          ],
          "label": "--fast",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "normal",
          "description": "Combina ICMP, ARP y descubrimiento de servicios.",
          "flags": [
            "--normal"
          ],
          "label": "--normal",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "normal",
          "description": "Añade reintentos y reconocimiento más profundo.",
          "flags": [
            "--accurate"
          ],
          "label": "--accurate",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Rango CIDR que se explorará solo durante esta ejecución.",
          "flags": [
            "--range"
          ],
          "label": "--range",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Resuelve nombres sin almacenarlos.",
          "flags": [
            "--resolve-names"
          ],
          "label": "--resolve-names",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Puertos TCP opcionales, por ejemplo 22,80,443.",
          "flags": [
            "--ports"
          ],
          "label": "--ports",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Devuelve la sesión como JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "64",
          "description": "Sondeos simultáneos.",
          "flags": [
            "--workers"
          ],
          "label": "--workers",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "0.8",
          "description": "Tiempo máximo base por sondeo, en segundos.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "4096",
          "description": "Límite defensivo de direcciones autorizadas.",
          "flags": [
            "--max-hosts"
          ],
          "label": "--max-hosts",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "ascending",
            "descending",
            "random"
          ],
          "default": "ascending",
          "description": "Orden de exploración de las direcciones.",
          "flags": [
            "--scan-order"
          ],
          "label": "--scan-order",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Descubrimiento de red",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Ejecuta el descubrimiento real en una sesión aislada en memoria. No abre, modifica ni guarda proyectos o bases de dispositivos.",
      "details": "Usage: LANIP ephemeral [-h] [--fast | --normal | --accurate] [--range NETWORK] [--resolve-names]\n                       [--ports PORTS] [--json] [--workers WORKERS] [--timeout TIMEOUT]\n                       [--max-hosts MAX_HOSTS] [--scan-order {ascending,descending,random}]\n\nEjecuta el descubrimiento real en una sesión aislada en memoria. No abre, modifica ni guarda proyectos o bases de dispositivos.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --fast                      Prioriza un barrido ARP rápido.\n  --normal                    Combina ICMP, ARP y descubrimiento de servicios.\n  --accurate                  Añade reintentos y reconocimiento más profundo.\n  --range NETWORK             Rango CIDR que se explorará solo durante esta ejecución.\n  --resolve-names             Resuelve nombres sin almacenarlos.\n  --ports PORTS               Puertos TCP opcionales, por ejemplo 22,80,443.\n  --json                      Devuelve la sesión como JSON.\n  --workers WORKERS           Sondeos simultáneos.\n  --timeout TIMEOUT           Tiempo máximo base por sondeo, en segundos.\n  --max-hosts MAX_HOSTS       Límite defensivo de direcciones autorizadas.\n  --scan-order {ascending,descending,random}\n                              Orden de exploración de las direcciones.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip ephemeral --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-ephemeral",
      "kind": "command",
      "launcher": "LANIP",
      "name": "ephemeral",
      "path": [
        "LANIP",
        "ephemeral"
      ],
      "title": "LANIP ephemeral",
      "usage": "LANIP ephemeral [-h] [--fast | --normal | --accurate] [--range NETWORK] [--resolve-names]\n                       [--ports PORTS] [--json] [--workers WORKERS] [--timeout TIMEOUT]\n                       [--max-hosts MAX_HOSTS] [--scan-order {ascending,descending,random}]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Red CIDR. Por defecto detecta la LAN como /24.",
          "flags": [
            "--network"
          ],
          "label": "--network",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/groups.json",
          "description": "Archivo JSON de grupos.",
          "flags": [
            "--groups"
          ],
          "label": "--groups",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "table",
            "json",
            "csv",
            "html",
            "xml",
            "yaml"
          ],
          "default": "table",
          "description": "Formato de salida (por defecto: table).",
          "flags": [
            "-f",
            "--format"
          ],
          "label": "-f, --format",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Guarda la salida en un archivo.",
          "flags": [
            "-o",
            "--output"
          ],
          "label": "-o, --output",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Lista los elementos recurrentes sin escanear la LAN ni mostrar IP.",
          "flags": [
            "-recurrent",
            "--recurrent"
          ],
          "label": "-recurrent, --recurrent",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Consulta combinable, por ejemplo: \"active and group=IOT and vendor~Amazon\".",
          "flags": [
            "--where"
          ],
          "label": "--where",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "64",
          "description": "Comprobaciones simultáneas.",
          "flags": [
            "-w",
            "--workers"
          ],
          "label": "-w, --workers",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "0.8",
          "description": "Timeout base en segundos por operación y host; el perfil puede ajustarlo.",
          "flags": [
            "-t",
            "--timeout"
          ],
          "label": "-t, --timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "ascending",
            "descending",
            "random"
          ],
          "default": "ascending",
          "description": "Orden de sondeo de IP: ascending, descending o random.",
          "flags": [
            "--scan-order"
          ],
          "label": "--scan-order",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Incluye hosts activos aunque todavía no tengan MAC.",
          "flags": [
            "--include-unknown"
          ],
          "label": "--include-unknown",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Resuelve y guarda nombres DNS de los elementos detectados.",
          "flags": [
            "--resolve-names"
          ],
          "label": "--resolve-names",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "4096",
          "description": "Máximo de hosts permitido en un escaneo.",
          "flags": [
            "--max-hosts"
          ],
          "label": "--max-hosts",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "icmp",
            "arp",
            "hybrid"
          ],
          "default": null,
          "description": "Método: icmp, arp activo o hybrid (por defecto según settings).",
          "flags": [
            "--discovery"
          ],
          "label": "--discovery",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "fast",
            "normal",
            "accurate"
          ],
          "default": null,
          "description": "Perfil completo de escaneo: fast, normal o accurate.",
          "flags": [
            "--profile"
          ],
          "label": "--profile",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Escaneo ARP rápido.",
          "flags": [
            "--fast"
          ],
          "label": "--fast",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Escaneo híbrido equilibrado.",
          "flags": [
            "--normal"
          ],
          "label": "--normal",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Escaneo profundo con varios métodos.",
          "flags": [
            "--accurate"
          ],
          "label": "--accurate",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "True",
          "description": "Muestra el progreso interactivo.",
          "flags": [
            "--progress"
          ],
          "label": "--progress",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "True",
          "description": "Oculta el progreso.",
          "flags": [
            "--no-progress"
          ],
          "label": "--no-progress",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Añade una columna con ICMP, ARP, LOCAL, BASIC o CACHE.",
          "flags": [
            "--show-discovery"
          ],
          "label": "--show-discovery",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Importa vecinos ARP en caché como CACHE no verificada; no cuentan como activos.",
          "flags": [
            "--include-arp-cache"
          ],
          "label": "--include-arp-cache",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Añade los métodos históricos y la fecha de última detección.",
          "flags": [
            "--show-detection"
          ],
          "label": "--show-detection",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra solo los dispositivos activos en el escaneo actual.",
          "flags": [
            "--active",
            "-active",
            "-connected",
            "--connected",
            "-conected"
          ],
          "label": "--active, -active, -connected, --connected, -conected",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra solo los dispositivos no detectados actualmente.",
          "flags": [
            "-disconnected",
            "--disconnected",
            "-offline"
          ],
          "label": "-disconnected, --disconnected, -offline",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Vista reducida: IP, alias y descripción.",
          "flags": [
            "-basic",
            "--basic"
          ],
          "label": "-basic, --basic",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "O",
            "X",
            "-",
            "S",
            "F"
          ],
          "default": null,
          "description": "Filtra por estado CNF: O, X, -, S o F.",
          "flags": [
            "-cnf",
            "--cnf-state"
          ],
          "label": "-cnf, --cnf-state",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra solo los elementos de un grupo.",
          "flags": [
            "-group",
            "--group"
          ],
          "label": "-group, --group",
          "metavar": "GRUPO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra solo IP incluidas en el rango DHCP configurado.",
          "flags": [
            "-dhcp",
            "--dhcp-only"
          ],
          "label": "-dhcp, --dhcp-only",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Inventario y búsqueda",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Realiza un escaneo básico de IP/MAC, actualiza la base de datos por MAC y muestra también los equipos no detectados.",
      "details": "Usage: LANIP list [-h] [--network NETWORK] [--database DATABASE] [--groups GROUPS]\n                  [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT] [-recurrent] [--where WHERE]\n                  [-w WORKERS] [-t TIMEOUT] [--scan-order {ascending,descending,random}]\n                  [--include-unknown] [--resolve-names] [--max-hosts MAX_HOSTS]\n                  [--discovery {icmp,arp,hybrid}]\n                  [--profile {fast,normal,accurate} | --fast | --normal | --accurate]\n                  [--progress | --no-progress] [--show-discovery] [--include-arp-cache]\n                  [--show-detection] [--active | -disconnected] [-basic] [-cnf {O,X,-,S,F}]\n                  [-group GRUPO] [-dhcp]\n\nRealiza un escaneo básico de IP/MAC, actualiza la base de datos por MAC y muestra también los equipos no detectados.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --network NETWORK           Red CIDR. Por defecto detecta la LAN como /24.\n  --database DATABASE         Archivo JSON de elementos.\n  --groups GROUPS             Archivo JSON de grupos.\n  -f {table,json,csv,html,xml,yaml}, --format {table,json,csv,html,xml,yaml}\n                              Formato de salida (por defecto: table).\n  -o OUTPUT, --output OUTPUT  Guarda la salida en un archivo.\n  -recurrent, --recurrent     Lista los elementos recurrentes sin escanear la LAN ni mostrar IP.\n  --where WHERE               Consulta combinable, por ejemplo: \"active and group=IOT and\n                              vendor~Amazon\".\n  -w WORKERS, --workers WORKERS\n                              Comprobaciones simultáneas.\n  -t TIMEOUT, --timeout TIMEOUT\n                              Timeout base en segundos por operación y host; el perfil puede\n                              ajustarlo.\n  --scan-order {ascending,descending,random}\n                              Orden de sondeo de IP: ascending, descending o random.\n  --include-unknown           Incluye hosts activos aunque todavía no tengan MAC.\n  --resolve-names             Resuelve y guarda nombres DNS de los elementos detectados.\n  --max-hosts MAX_HOSTS       Máximo de hosts permitido en un escaneo.\n  --discovery {icmp,arp,hybrid}\n                              Método: icmp, arp activo o hybrid (por defecto según settings).\n  --profile {fast,normal,accurate}\n                              Perfil completo de escaneo: fast, normal o accurate.\n  --fast                      Escaneo ARP rápido.\n  --normal                    Escaneo híbrido equilibrado.\n  --accurate                  Escaneo profundo con varios métodos.\n  --progress                  Muestra el progreso interactivo.\n  --no-progress               Oculta el progreso.\n  --show-discovery            Añade una columna con ICMP, ARP, LOCAL, BASIC o CACHE.\n  --include-arp-cache         Importa vecinos ARP en caché como CACHE no verificada; no cuentan\n                              como activos.\n  --show-detection            Añade los métodos históricos y la fecha de última detección.\n  --active, -active, -connected, --connected, -conected\n                              Muestra solo los dispositivos activos en el escaneo actual.\n  -disconnected, --disconnected, -offline\n                              Muestra solo los dispositivos no detectados actualmente.\n  -basic, --basic             Vista reducida: IP, alias y descripción.\n  -cnf {O,X,-,S,F}, --cnf-state {O,X,-,S,F}\n                              Filtra por estado CNF: O, X, -, S o F.\n  -group GRUPO, --group GRUPO\n                              Muestra solo los elementos de un grupo.\n  -dhcp, --dhcp-only          Muestra solo IP incluidas en el rango DHCP configurado.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip list --active",
        "lanip list --format json"
      ],
      "group": "LANIP",
      "id": "command-lanip-list",
      "kind": "command",
      "launcher": "LANIP",
      "name": "list",
      "path": [
        "LANIP",
        "list"
      ],
      "title": "LANIP list",
      "usage": "LANIP list [-h] [--network NETWORK] [--database DATABASE] [--groups GROUPS]\n                  [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT] [-recurrent] [--where WHERE]\n                  [-w WORKERS] [-t TIMEOUT] [--scan-order {ascending,descending,random}]\n                  [--include-unknown] [--resolve-names] [--max-hosts MAX_HOSTS]\n                  [--discovery {icmp,arp,hybrid}]\n                  [--profile {fast,normal,accurate} | --fast | --normal | --accurate]\n                  [--progress | --no-progress] [--show-discovery] [--include-arp-cache]\n                  [--show-detection] [--active | -disconnected] [-basic] [-cnf {O,X,-,S,F}]\n                  [-group GRUPO] [-dhcp]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Lista todos los elementos recurrentes sin sus IP.",
          "flags": [
            "-list",
            "--list"
          ],
          "label": "-list, --list",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "table",
            "json",
            "csv",
            "html",
            "xml",
            "yaml"
          ],
          "default": "table",
          "description": "Formato de salida (por defecto: table).",
          "flags": [
            "-f",
            "--format"
          ],
          "label": "-f, --format",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Guarda la salida en un archivo.",
          "flags": [
            "-o",
            "--output"
          ],
          "label": "-o, --output",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Muestra identidades recurrentes por MAC. No incluye IP porque puede cambiar en cada LAN.",
      "details": "Usage: LANIP recurrent [-h] -list [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT]\n\nMuestra identidades recurrentes por MAC. No incluye IP porque puede cambiar en cada LAN.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -list, --list               Lista todos los elementos recurrentes sin sus IP.\n  -f {table,json,csv,html,xml,yaml}, --format {table,json,csv,html,xml,yaml}\n                              Formato de salida (por defecto: table).\n  -o OUTPUT, --output OUTPUT  Guarda la salida en un archivo.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip recurrent --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-recurrent",
      "kind": "command",
      "launcher": "LANIP",
      "name": "recurrent",
      "path": [
        "LANIP",
        "recurrent"
      ],
      "title": "LANIP recurrent",
      "usage": "LANIP recurrent [-h] -list [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC, alias o nombre registrado.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "auto",
            "ping",
            "arp"
          ],
          "default": "auto",
          "description": "Buscador utilizado: auto, ping o arp (por defecto: auto).",
          "flags": [
            "--method"
          ],
          "label": "--method",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Usa únicamente una solicitud ICMP.",
          "flags": [
            "--ping"
          ],
          "label": "--ping",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Usa únicamente una solicitud ARP activa.",
          "flags": [
            "--arp"
          ],
          "label": "--arp",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "0.8",
          "description": "Tiempo máximo de cada comprobación, en segundos.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Devuelve el diagnóstico como JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Diagnóstico de red",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Diagnostica un único elemento sin modificar la base de datos. PING prueba ICMP; ARP realiza una consulta activa en la LAN; AUTO combina ambos métodos.",
      "details": "Usage: LANIP ping [-h] [--method {auto,ping,arp} | --ping | --arp] [--timeout TIMEOUT] [--json]\n                  [--database DATABASE]\n                  selector\n\nDiagnostica un único elemento sin modificar la base de datos. PING prueba ICMP; ARP realiza una consulta activa en la LAN; AUTO combina ambos métodos.\n\nArguments:\n  selector                  IP, MAC, alias o nombre registrado.\n\nOptions:\n  -h, --help                Show this help and exit.\n  --method {auto,ping,arp}  Buscador utilizado: auto, ping o arp (por defecto: auto).\n  --ping                    Usa únicamente una solicitud ICMP.\n  --arp                     Usa únicamente una solicitud ARP activa.\n  --timeout TIMEOUT         Tiempo máximo de cada comprobación, en segundos.\n  --json                    Devuelve el diagnóstico como JSON.\n  --database DATABASE       Archivo JSON de elementos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip ping --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-ping",
      "kind": "command",
      "launcher": "LANIP",
      "name": "ping",
      "path": [
        "LANIP",
        "ping"
      ],
      "title": "LANIP ping",
      "usage": "LANIP ping [-h] [--method {auto,ping,arp} | --ping | --arp] [--timeout TIMEOUT] [--json]\n                  [--database DATABASE]\n                  selector"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias del elemento.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "auto",
            "ssh",
            "tr-064",
            "telnet",
            "http",
            "https",
            "ftp",
            "rdp",
            "rtsp",
            "smb",
            "radmin"
          ],
          "default": "auto",
          "description": "Protocolo o detección automática.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Puerto alternativo.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Ruta HTTP/FTP/RTSP o recurso SMB.",
          "flags": [
            "--path"
          ],
          "label": "--path",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "control",
            "view",
            "file",
            "shutdown",
            "chat",
            "voice",
            "message",
            "telnet"
          ],
          "default": null,
          "description": "Modo de conexión Radmin.",
          "flags": [
            "--mode"
          ],
          "label": "--mode",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Servidor Radmin intermedio HOST:PUERTO.",
          "flags": [
            "--through"
          ],
          "label": "--through",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre control o vista a pantalla completa.",
          "flags": [
            "--fullscreen"
          ],
          "label": "--fullscreen",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "24",
            "16",
            "8",
            "4",
            "2",
            "1"
          ],
          "default": null,
          "description": "Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).",
          "flags": [
            "--color-depth"
          ],
          "label": "--color-depth",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Máximo de actualizaciones de pantalla por segundo (1-120).",
          "flags": [
            "--updates"
          ],
          "label": "--updates",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Ruta de phonebook Radmin .rpb.",
          "flags": [
            "--phonebook"
          ],
          "label": "--phonebook",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Identificador de entrada dentro del phonebook de Radmin.",
          "flags": [
            "--phonebook-id"
          ],
          "label": "--phonebook-id",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra el destino sin abrirlo.",
          "flags": [
            "--dry-run"
          ],
          "label": "--dry-run",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP open [-h] [--port PORT] [--path PATH]\n                  [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                  [--through THROUGH] [--fullscreen] [--color-depth {24,16,8,4,2,1}]\n                  [--updates UPDATES] [--phonebook PHONEBOOK] [--phonebook-id PHONEBOOK_ID]\n                  [--dry-run] [--database DATABASE] [--store STORE]\n                  selector [{auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}]",
      "details": "Usage: LANIP open [-h] [--port PORT] [--path PATH]\n                  [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                  [--through THROUGH] [--fullscreen] [--color-depth {24,16,8,4,2,1}]\n                  [--updates UPDATES] [--phonebook PHONEBOOK] [--phonebook-id PHONEBOOK_ID]\n                  [--dry-run] [--database DATABASE] [--store STORE]\n                  selector [{auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}]\n\nArguments:\n  selector                    IP, MAC o alias del elemento.\n  {auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}\n                              Protocolo o detección automática.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --port PORT                 Puerto alternativo.\n  --path PATH                 Ruta HTTP/FTP/RTSP o recurso SMB.\n  --mode {control,view,file,shutdown,chat,voice,message,telnet}\n                              Modo de conexión Radmin.\n  --through THROUGH           Servidor Radmin intermedio HOST:PUERTO.\n  --fullscreen                Abre control o vista a pantalla completa.\n  --color-depth {24,16,8,4,2,1}\n                              Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).\n  --updates UPDATES           Máximo de actualizaciones de pantalla por segundo (1-120).\n  --phonebook PHONEBOOK       Ruta de phonebook Radmin .rpb.\n  --phonebook-id PHONEBOOK_ID\n                              Identificador de entrada dentro del phonebook de Radmin.\n  --dry-run                   Muestra el destino sin abrirlo.\n  --database DATABASE         Archivo JSON de elementos.\n  --store STORE               Almacén cifrado de credenciales.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip open --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-open",
      "kind": "command",
      "launcher": "LANIP",
      "name": "open",
      "path": [
        "LANIP",
        "open"
      ],
      "title": "LANIP open",
      "usage": "LANIP open [-h] [--port PORT] [--path PATH]\n                  [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                  [--through THROUGH] [--fullscreen] [--color-depth {24,16,8,4,2,1}]\n                  [--updates UPDATES] [--phonebook PHONEBOOK] [--phonebook-id PHONEBOOK_ID]\n                  [--dry-run] [--database DATABASE] [--store STORE]\n                  selector [{auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Rango LAN predeterminado, por ejemplo 192.168.1.1/24.",
          "flags": [
            "-range"
          ],
          "label": "-range",
          "metavar": "CIDR",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Columnas mostradas por list, separadas por espacios o comas.",
          "flags": [
            "-list-fields",
            "--list-fields",
            "-list"
          ],
          "label": "-list-fields, --list-fields, -list",
          "metavar": "CAMPO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Rango DHCP manual. Usa 'off' para dejarlo sin configurar.",
          "flags": [
            "-dhcp-range",
            "--dhcp-range",
            "-dhcp"
          ],
          "label": "-dhcp-range, --dhcp-range, -dhcp",
          "metavar": "INICIO-FIN",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Ruta del almacén de credenciales cifradas.",
          "flags": [
            "-credentials",
            "--credentials"
          ],
          "label": "-credentials, --credentials",
          "metavar": "ARCHIVO",
          "required": false
        },
        {
          "choices": [
            "icmp",
            "arp",
            "hybrid"
          ],
          "default": null,
          "description": "Método predeterminado utilizado por list.",
          "flags": [
            "-discovery",
            "--discovery"
          ],
          "label": "-discovery, --discovery",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "fast",
            "normal",
            "accurate"
          ],
          "default": null,
          "description": "Perfil predeterminado de list: fast, normal o accurate.",
          "flags": [
            "--scan-profile"
          ],
          "label": "--scan-profile",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Activa o desactiva el progreso interactivo.",
          "flags": [
            "--progress"
          ],
          "label": "--progress",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Activa o desactiva el reconocimiento de servicios en scan.",
          "flags": [
            "--service-identification"
          ],
          "label": "--service-identification",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "permanent",
            "session",
            "forget"
          ],
          "default": null,
          "description": "Persistencia de desconectados: permanent, session o forget.",
          "flags": [
            "--disconnected-retention"
          ],
          "label": "--disconnected-retention",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "unconfirmed",
            "all"
          ],
          "default": null,
          "description": "Aplica la retención solo a CNF=X (unconfirmed) o a todos (all).",
          "flags": [
            "--disconnected-target"
          ],
          "label": "--disconnected-target",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "all",
            "dhcp"
          ],
          "default": null,
          "description": "Aplica la regla a toda la LAN (all) o solo al rango DHCP (dhcp).",
          "flags": [
            "--disconnected-scope"
          ],
          "label": "--disconnected-scope",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Concurrencia predeterminada de los escaneos.",
          "flags": [
            "--workers"
          ],
          "label": "--workers",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Timeout predeterminado por operación de red.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "ascending",
            "descending",
            "random"
          ],
          "default": null,
          "description": "Orden predeterminado de sondeo: ascending, descending o random.",
          "flags": [
            "--scan-order"
          ],
          "label": "--scan-order",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Máximo de hosts autorizado por escaneo.",
          "flags": [
            "--max-hosts"
          ],
          "label": "--max-hosts",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Ruta del inventario de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "ARCHIVO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Ruta de la base física SQLite administrada exclusivamente por LANWIRE.",
          "flags": [
            "--physical-database"
          ],
          "label": "--physical-database",
          "metavar": "ARCHIVO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Ruta de la base de grupos.",
          "flags": [
            "--groups"
          ],
          "label": "--groups",
          "metavar": "ARCHIVO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Directorio de registros.",
          "flags": [
            "--log"
          ],
          "label": "--log",
          "metavar": "DIRECTORIO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Nivel mínimo de ErrorEvent escrito en el log (1 incluye diagnóstico detallado).",
          "flags": [
            "--error-log-level"
          ],
          "label": "--error-log-level",
          "metavar": "1-59",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Carpeta predeterminada para nombres de proyecto VLF relativos.",
          "flags": [
            "--projects-directory"
          ],
          "label": "--projects-directory",
          "metavar": "DIRECTORIO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Política de guardado VLF. Usa 'list' para consultar las opciones integradas y las aportadas por plugins.",
          "flags": [
            "-save-mode",
            "--save-mode"
          ],
          "label": "-save-mode, --save-mode",
          "metavar": "MODO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo de automatic.timeToSave en minutos (mínimo 0.1).",
          "flags": [
            "-save-interval",
            "--save-interval"
          ],
          "label": "-save-interval, --save-interval",
          "metavar": "MINUTOS",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Consulta si se guarda al terminar cada comando individual de consola.",
          "flags": [
            "--cli-exit-save-prompt"
          ],
          "label": "--cli-exit-save-prompt",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Permite encadenar órdenes con ; dentro de la CLI interactiva.",
          "flags": [
            "--cli-command-chaining"
          ],
          "label": "--cli-command-chaining",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Activa o desactiva la limpieza automática de logs antiguos.",
          "flags": [
            "-log-cleanup",
            "--log-cleanup"
          ],
          "label": "-log-cleanup, --log-cleanup",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Días durante los que se conservan los archivos de log.",
          "flags": [
            "-log-retention-days",
            "--log-retention-days"
          ],
          "label": "-log-retention-days, --log-retention-days",
          "metavar": "DÍAS",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Activa el acceso SSH restringido.",
          "flags": [
            "--remote-access"
          ],
          "label": "--remote-access",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "IPv4 local de escucha SSH.",
          "flags": [
            "--remote-bind"
          ],
          "label": "--remote-bind",
          "metavar": "IP",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Red de origen autorizada.",
          "flags": [
            "--remote-cidr"
          ],
          "label": "--remote-cidr",
          "metavar": "CIDR",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Puerto del servidor SSH remoto.",
          "flags": [
            "--remote-port"
          ],
          "label": "--remote-port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Permite o bloquea autenticación SSH mediante contraseña.",
          "flags": [
            "--remote-password-auth"
          ],
          "label": "--remote-password-auth",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "service",
            "user"
          ],
          "default": null,
          "description": "Ejecuta el backend como servicio persistente o proceso de usuario.",
          "flags": [
            "--remote-backend"
          ],
          "label": "--remote-backend",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "off",
            "gui",
            "tui",
            "plugins",
            "projects",
            "settings"
          ],
          "default": null,
          "description": "Vista predeterminada para root forced-view.",
          "flags": [
            "--remote-forced-view"
          ],
          "label": "--remote-forced-view",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Asigna una tecla a una acción del TUI. Puede repetirse.",
          "flags": [
            "--tui-key"
          ],
          "label": "--tui-key",
          "metavar": "ACCIÓN=TECLA",
          "required": false
        },
        {
          "choices": [
            "cli.bottom",
            "cli.top"
          ],
          "default": null,
          "description": "Coloca el CLI arriba (cli.top) o abajo (cli.bottom).",
          "flags": [
            "--tui-layout"
          ],
          "label": "--tui-layout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Porcentaje vertical reservado al CLI; ListElement conserva al menos 25%%.",
          "flags": [
            "--tui-cli-percent"
          ],
          "label": "--tui-cli-percent",
          "metavar": "15-75",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Peso de columna (GROUP=15%%); IP=15ch y MAC=17ch son fijas.",
          "flags": [
            "--tui-column"
          ],
          "label": "--tui-column",
          "metavar": "COLUMNA=TAMAÑO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Acciones visibles en la barra inferior, separadas por comas; usa all para todas.",
          "flags": [
            "--tui-footer-buttons"
          ],
          "label": "--tui-footer-buttons",
          "metavar": "ACCIONES",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra u oculta una acción concreta de la barra inferior. Puede repetirse.",
          "flags": [
            "--tui-footer-button"
          ],
          "label": "--tui-footer-button",
          "metavar": "ACCIÓN=on|off",
          "required": false
        }
      ],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP settings [-h] [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]\n                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]\n                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]\n                      [--service-identification {on,off}]\n                      [--disconnected-retention {permanent,session,forget}]\n                      [--disconnected-target {unconfirmed,all}] [--disconnected-scope {all,dhcp}]\n                      [--workers WORKERS] [--timeout TIMEOUT]\n                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]\n                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]\n                      [--log DIRECTORIO] [--error-log-level 1-59]\n                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]\n                      [--cli-exit-save-prompt {on,off}] [--cli-command-chaining {on,off}]\n                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]\n                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]\n                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]\n                      [--remote-backend {service,user}]\n                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]\n                      [--tui-key ACCIÓN=TECLA] [--tui-layout {cli.bottom,cli.top}]\n                      [--tui-cli-percent 15-75] [--tui-column COLUMNA=TAMAÑO]\n                      [--tui-footer-buttons ACCIONES] [--tui-footer-button ACCIÓN=on|off]",
      "details": "Usage: LANIP settings [-h] [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]\n                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]\n                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]\n                      [--service-identification {on,off}]\n                      [--disconnected-retention {permanent,session,forget}]\n                      [--disconnected-target {unconfirmed,all}] [--disconnected-scope {all,dhcp}]\n                      [--workers WORKERS] [--timeout TIMEOUT]\n                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]\n                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]\n                      [--log DIRECTORIO] [--error-log-level 1-59]\n                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]\n                      [--cli-exit-save-prompt {on,off}] [--cli-command-chaining {on,off}]\n                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]\n                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]\n                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]\n                      [--remote-backend {service,user}]\n                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]\n                      [--tui-key ACCIÓN=TECLA] [--tui-layout {cli.bottom,cli.top}]\n                      [--tui-cli-percent 15-75] [--tui-column COLUMNA=TAMAÑO]\n                      [--tui-footer-buttons ACCIONES] [--tui-footer-button ACCIÓN=on|off]\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -range CIDR                 Rango LAN predeterminado, por ejemplo 192.168.1.1/24.\n  -list-fields CAMPO [CAMPO ...], --list-fields CAMPO [CAMPO ...], -list CAMPO [CAMPO ...]\n                              Columnas mostradas por list, separadas por espacios o comas.\n  -dhcp-range INICIO-FIN, --dhcp-range INICIO-FIN, -dhcp INICIO-FIN\n                              Rango DHCP manual. Usa 'off' para dejarlo sin configurar.\n  -credentials ARCHIVO, --credentials ARCHIVO\n                              Ruta del almacén de credenciales cifradas.\n  -discovery {icmp,arp,hybrid}, --discovery {icmp,arp,hybrid}\n                              Método predeterminado utilizado por list.\n  --scan-profile {fast,normal,accurate}\n                              Perfil predeterminado de list: fast, normal o accurate.\n  --progress {on,off}         Activa o desactiva el progreso interactivo.\n  --service-identification {on,off}\n                              Activa o desactiva el reconocimiento de servicios en scan.\n  --disconnected-retention {permanent,session,forget}\n                              Persistencia de desconectados: permanent, session o forget.\n  --disconnected-target {unconfirmed,all}\n                              Aplica la retención solo a CNF=X (unconfirmed) o a todos (all).\n  --disconnected-scope {all,dhcp}\n                              Aplica la regla a toda la LAN (all) o solo al rango DHCP (dhcp).\n  --workers WORKERS           Concurrencia predeterminada de los escaneos.\n  --timeout TIMEOUT           Timeout predeterminado por operación de red.\n  --scan-order {ascending,descending,random}\n                              Orden predeterminado de sondeo: ascending, descending o random.\n  --max-hosts MAX_HOSTS       Máximo de hosts autorizado por escaneo.\n  --database ARCHIVO          Ruta del inventario de elementos.\n  --physical-database ARCHIVO\n                              Ruta de la base física SQLite administrada exclusivamente por\n                              LANWIRE.\n  --groups ARCHIVO            Ruta de la base de grupos.\n  --log DIRECTORIO            Directorio de registros.\n  --error-log-level 1-59      Nivel mínimo de ErrorEvent escrito en el log (1 incluye diagnóstico\n                              detallado).\n  --projects-directory DIRECTORIO\n                              Carpeta predeterminada para nombres de proyecto VLF relativos.\n  -save-mode MODO, --save-mode MODO\n                              Política de guardado VLF. Usa 'list' para consultar las opciones\n                              integradas y las aportadas por plugins.\n  -save-interval MINUTOS, --save-interval MINUTOS\n                              Intervalo de automatic.timeToSave en minutos (mínimo 0.1).\n  --cli-exit-save-prompt {on,off}\n                              Consulta si se guarda al terminar cada comando individual de\n                              consola.\n  --cli-command-chaining {on,off}\n                              Permite encadenar órdenes con ; dentro de la CLI interactiva.\n  -log-cleanup {on,off}, --log-cleanup {on,off}\n                              Activa o desactiva la limpieza automática de logs antiguos.\n  -log-retention-days DÍAS, --log-retention-days DÍAS\n                              Días durante los que se conservan los archivos de log.\n  --remote-access {on,off}    Activa el acceso SSH restringido.\n  --remote-bind IP            IPv4 local de escucha SSH.\n  --remote-cidr CIDR          Red de origen autorizada.\n  --remote-port REMOTE_PORT   Puerto del servidor SSH remoto.\n  --remote-password-auth {on,off}\n                              Permite o bloquea autenticación SSH mediante contraseña.\n  --remote-backend {service,user}\n                              Ejecuta el backend como servicio persistente o proceso de usuario.\n  --remote-forced-view {off,gui,tui,plugins,projects,settings}\n                              Vista predeterminada para root forced-view.\n  --tui-key ACCIÓN=TECLA      Asigna una tecla a una acción del TUI. Puede repetirse.\n  --tui-layout {cli.bottom,cli.top}\n                              Coloca el CLI arriba (cli.top) o abajo (cli.bottom).\n  --tui-cli-percent 15-75     Porcentaje vertical reservado al CLI; ListElement conserva al menos\n                              25%.\n  --tui-column COLUMNA=TAMAÑO\n                              Peso de columna (GROUP=15%); IP=15ch y MAC=17ch son fijas.\n  --tui-footer-buttons ACCIONES\n                              Acciones visibles en la barra inferior, separadas por comas; usa all\n                              para todas.\n  --tui-footer-button ACCIÓN=on|off\n                              Muestra u oculta una acción concreta de la barra inferior. Puede\n                              repetirse.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip settings --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-settings",
      "kind": "command",
      "launcher": "LANIP",
      "name": "settings",
      "path": [
        "LANIP",
        "settings"
      ],
      "title": "LANIP settings",
      "usage": "LANIP settings [-h] [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]\n                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]\n                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]\n                      [--service-identification {on,off}]\n                      [--disconnected-retention {permanent,session,forget}]\n                      [--disconnected-target {unconfirmed,all}] [--disconnected-scope {all,dhcp}]\n                      [--workers WORKERS] [--timeout TIMEOUT]\n                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]\n                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]\n                      [--log DIRECTORIO] [--error-log-level 1-59]\n                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]\n                      [--cli-exit-save-prompt {on,off}] [--cli-command-chaining {on,off}]\n                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]\n                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]\n                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]\n                      [--remote-backend {service,user}]\n                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]\n                      [--tui-key ACCIÓN=TECLA] [--tui-layout {cli.bottom,cli.top}]\n                      [--tui-cli-percent 15-75] [--tui-column COLUMNA=TAMAÑO]\n                      [--tui-footer-buttons ACCIONES] [--tui-footer-button ACCIÓN=on|off]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Alias, IP o MAC del dispositivo.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "ip",
            "cnf",
            "mac",
            "alias",
            "name",
            "group",
            "description",
            "manufacturer",
            "default-name",
            "device-id",
            "protocols"
          ],
          "default": "ip",
          "description": "Dato devuelto (por defecto: ip).",
          "flags": [
            "-f",
            "--field"
          ],
          "label": "-f, --field",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Devuelve el registro completo como JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP call [-h]\n                  [-f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}]\n                  [--json] [--database DATABASE]\n                  selector",
      "details": "Usage: LANIP call [-h]\n                  [-f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}]\n                  [--json] [--database DATABASE]\n                  selector\n\nArguments:\n  selector                    Alias, IP o MAC del dispositivo.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}, --field {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}\n                              Dato devuelto (por defecto: ip).\n  --json                      Devuelve el registro completo como JSON.\n  --database DATABASE         Archivo JSON de elementos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip call --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-call",
      "kind": "command",
      "launcher": "LANIP",
      "name": "call",
      "path": [
        "LANIP",
        "call"
      ],
      "title": "LANIP call",
      "usage": "LANIP call [-h]\n                  [-f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}]\n                  [--json] [--database DATABASE]\n                  selector"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Alias, nombre, IP o MAC exactos.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Devuelve el registro completo como JSON para scripts.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Inventario y búsqueda",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP search [-h] [--json] [--database DATABASE] selector",
      "details": "Usage: LANIP search [-h] [--json] [--database DATABASE] selector\n\nArguments:\n  selector             Alias, nombre, IP o MAC exactos.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --json               Devuelve el registro completo como JSON para scripts.\n  --database DATABASE  Archivo JSON de elementos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip search --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-search",
      "kind": "command",
      "launcher": "LANIP",
      "name": "search",
      "path": [
        "LANIP",
        "search"
      ],
      "title": "LANIP search",
      "usage": "LANIP search [-h] [--json] [--database DATABASE] selector"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias registrado en LANCTL.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "common",
          "description": "Puertos o rangos: 22,80,443,8000-8100 (por defecto: common).",
          "flags": [
            "--ports"
          ],
          "label": "--ports",
          "metavar": "LISTA",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Autoriza explícitamente el escaneo TCP 1-65535.",
          "flags": [
            "--all-ports"
          ],
          "label": "--all-ports",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "0.5",
          "description": "Tiempo máximo por conexión, en segundos.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "128",
          "description": "Número máximo de conexiones simultáneas.",
          "flags": [
            "--workers"
          ],
          "label": "--workers",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Lee banners pasivos; no envía sondas específicas de protocolo.",
          "flags": [
            "--banners"
          ],
          "label": "--banners",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "True",
          "description": "Reconoce servicios y deduce el tipo de dispositivo con evidencias.",
          "flags": [
            "--identify"
          ],
          "label": "--identify",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Salida JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Descubrimiento de red",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Resuelve un elemento por IP, MAC o alias y comprueba identidad, disponibilidad y puertos TCP. No modifica el dispositivo.",
      "details": "Usage: LANIP scan [-h] [--ports LISTA] [--all-ports] [--timeout TIMEOUT] [--workers WORKERS]\n                  [--banners] [--identify] [--json] [--database DATABASE]\n                  selector\n\nResuelve un elemento por IP, MAC o alias y comprueba identidad, disponibilidad y puertos TCP. No modifica el dispositivo.\n\nArguments:\n  selector             IP, MAC o alias registrado en LANCTL.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --ports LISTA        Puertos o rangos: 22,80,443,8000-8100 (por defecto: common).\n  --all-ports          Autoriza explícitamente el escaneo TCP 1-65535.\n  --timeout TIMEOUT    Tiempo máximo por conexión, en segundos.\n  --workers WORKERS    Número máximo de conexiones simultáneas.\n  --banners            Lee banners pasivos; no envía sondas específicas de protocolo.\n  --identify           Reconoce servicios y deduce el tipo de dispositivo con evidencias.\n  --json               Salida JSON.\n  --database DATABASE  Archivo JSON de elementos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip scan NAS --identify --banners"
      ],
      "group": "LANIP",
      "id": "command-lanip-scan",
      "kind": "command",
      "launcher": "LANIP",
      "name": "scan",
      "path": [
        "LANIP",
        "scan"
      ],
      "title": "LANIP scan",
      "usage": "LANIP scan [-h] [--ports LISTA] [--all-ports] [--timeout TIMEOUT] [--workers WORKERS]\n                  [--banners] [--identify] [--json] [--database DATABASE]\n                  selector"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias del elemento.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) o F (FIXED). Sin valor libera F y restaura O.",
          "flags": [],
          "label": "value",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP cnf [-h] [--database DATABASE] selector [value]",
      "details": "Usage: LANIP cnf [-h] [--database DATABASE] selector [value]\n\nArguments:\n  selector             IP, MAC o alias del elemento.\n  value                O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) o F (FIXED). Sin valor\n                       libera F y restaura O.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --database DATABASE  Archivo JSON de elementos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip cnf --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-cnf",
      "kind": "command",
      "launcher": "LANIP",
      "name": "cnf",
      "path": [
        "LANIP",
        "cnf"
      ],
      "title": "LANIP cnf",
      "usage": "LANIP cnf [-h] [--database DATABASE] selector [value]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias del elemento.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "set",
            "list",
            "delete"
          ],
          "default": null,
          "description": "Operación sobre la credencial.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Protocolo, por ejemplo tr-064.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Nombre de usuario remoto.",
          "flags": [
            "-user",
            "--username"
          ],
          "label": "-user, --username",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Acceso remoto",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP credential [-h] [-user USERNAME] [--database DATABASE] [--store STORE]\n                        selector [{set,list,delete}] [protocol]",
      "details": "Usage: LANIP credential [-h] [-user USERNAME] [--database DATABASE] [--store STORE]\n                        selector [{set,list,delete}] [protocol]\n\nArguments:\n  selector                    IP, MAC o alias del elemento.\n  {set,list,delete}           Operación sobre la credencial.\n  protocol                    Protocolo, por ejemplo tr-064.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -user USERNAME, --username USERNAME\n                              Nombre de usuario remoto.\n  --database DATABASE         Archivo JSON de elementos.\n  --store STORE               Almacén cifrado de credenciales.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip credential --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-credential",
      "kind": "command",
      "launcher": "LANIP",
      "name": "credential",
      "path": [
        "LANIP",
        "credential"
      ],
      "title": "LANIP credential",
      "usage": "LANIP credential [-h] [-user USERNAME] [--database DATABASE] [--store STORE]\n                        selector [{set,list,delete}] [protocol]"
    },
    {
      "aliases": [
        "downloadsettings",
        "download-settings"
      ],
      "arguments": [],
      "category": "Comandos",
      "children": [
        "downloadSettings"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP GATEWAY [-h] ACCIÓN ...",
      "details": "Usage: LANIP GATEWAY [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    downloadSettings (downloadsettings, download-settings)\n                              Descarga las opciones LAN y DHCP interesantes para configuración.\n\nOptions:\n  -h, --help                  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip gateway --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-gateway",
      "kind": "command",
      "launcher": "LANIP",
      "name": "GATEWAY",
      "path": [
        "LANIP",
        "GATEWAY"
      ],
      "title": "LANIP GATEWAY",
      "usage": "LANIP GATEWAY [-h] ACCIÓN ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": "49000",
          "description": "Puerto TR-064 del router.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "5.0",
          "description": "Tiempo máximo de espera en segundos.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP GATEWAY downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                                      [--store STORE]",
      "details": "Usage: LANIP GATEWAY downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                                      [--store STORE]\n\nOptions:\n  -h, --help           Show this help and exit.\n  --port PORT          Puerto TR-064 del router.\n  --timeout TIMEOUT    Tiempo máximo de espera en segundos.\n  --database DATABASE  Archivo JSON de elementos.\n  --store STORE        Almacén cifrado de credenciales.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip gateway downloadsettings --help"
      ],
      "group": "LANIP GATEWAY",
      "id": "command-lanip-gateway-downloadsettings",
      "kind": "command",
      "launcher": "LANIP",
      "name": "downloadSettings",
      "path": [
        "LANIP",
        "GATEWAY",
        "downloadSettings"
      ],
      "title": "LANIP GATEWAY downloadSettings",
      "usage": "LANIP GATEWAY downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                                      [--store STORE]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": "GATEWAY",
          "description": "IP, MAC o alias del router.",
          "flags": [],
          "label": "gateway",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "49000",
          "description": "Puerto TR-064 del router.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "5.0",
          "description": "Tiempo máximo de espera en segundos.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                              [--store STORE]\n                              [gateway]",
      "details": "Usage: LANIP downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                              [--store STORE]\n                              [gateway]\n\nArguments:\n  gateway              IP, MAC o alias del router.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --port PORT          Puerto TR-064 del router.\n  --timeout TIMEOUT    Tiempo máximo de espera en segundos.\n  --database DATABASE  Archivo JSON de elementos.\n  --store STORE        Almacén cifrado de credenciales.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip downloadsettings --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-downloadsettings",
      "kind": "command",
      "launcher": "LANIP",
      "name": "downloadSettings",
      "path": [
        "LANIP",
        "downloadSettings"
      ],
      "title": "LANIP downloadSettings",
      "usage": "LANIP downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                              [--store STORE]\n                              [gateway]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "show",
            "configure"
          ],
          "default": null,
          "description": "Consulta o modifica el protocolo.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Protocolo que se configura.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "22",
          "description": "Puerto remoto.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "autodetect",
          "description": "Controlador del dispositivo.",
          "flags": [
            "--driver"
          ],
          "label": "--driver",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Algoritmo de clave de host permitido; se puede repetir.",
          "flags": [
            "--host-key"
          ],
          "label": "--host-key",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Algoritmo de intercambio de claves; se puede repetir.",
          "flags": [
            "--kex"
          ],
          "label": "--kex",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "ssh_legacy_cisco_s300",
            "ssh_esp32_rack_monitor"
          ],
          "default": null,
          "description": "Perfil SSH reutilizable.",
          "flags": [
            "--profile"
          ],
          "label": "--profile",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Acceso remoto",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP protocol [-h] [--port PORT] [--driver DRIVER] [--host-key HOST_KEY] [--kex KEX]\n                      [--profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}]\n                      [--database DATABASE]\n                      selector {show,configure} protocol",
      "details": "Usage: LANIP protocol [-h] [--port PORT] [--driver DRIVER] [--host-key HOST_KEY] [--kex KEX]\n                      [--profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}]\n                      [--database DATABASE]\n                      selector {show,configure} protocol\n\nArguments:\n  selector                    IP, MAC o alias.\n  {show,configure}            Consulta o modifica el protocolo.\n  protocol                    Protocolo que se configura.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --port PORT                 Puerto remoto.\n  --driver DRIVER             Controlador del dispositivo.\n  --host-key HOST_KEY         Algoritmo de clave de host permitido; se puede repetir.\n  --kex KEX                   Algoritmo de intercambio de claves; se puede repetir.\n  --profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}\n                              Perfil SSH reutilizable.\n  --database DATABASE         Archivo JSON de elementos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip protocol --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-protocol",
      "kind": "command",
      "launcher": "LANIP",
      "name": "protocol",
      "path": [
        "LANIP",
        "protocol"
      ],
      "title": "LANIP protocol",
      "usage": "LANIP protocol [-h] [--port PORT] [--driver DRIVER] [--host-key HOST_KEY] [--kex KEX]\n                      [--profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}]\n                      [--database DATABASE]\n                      selector {show,configure} protocol"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "probe",
            "fingerprint",
            "trust",
            "open",
            "show"
          ],
          "default": null,
          "description": "Operación SSH.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Huella o comando remoto, según la operación.",
          "flags": [],
          "label": "remote_command",
          "metavar": "COMANDO",
          "required": true
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "IP candidata para probe/fingerprint, sin modificar la base de datos.",
          "flags": [
            "--host"
          ],
          "label": "--host",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Acceso remoto",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP ssh [-h] [--database DATABASE] [--store STORE] [--host HOST]\n                 selector {probe,fingerprint,trust,open,show} [COMANDO ...]",
      "details": "Usage: LANIP ssh [-h] [--database DATABASE] [--store STORE] [--host HOST]\n                 selector {probe,fingerprint,trust,open,show} [COMANDO ...]\n\nArguments:\n  selector                    IP, MAC o alias.\n  {probe,fingerprint,trust,open,show}\n                              Operación SSH.\n  COMANDO                     Huella o comando remoto, según la operación.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --database DATABASE         Archivo JSON de elementos.\n  --store STORE               Almacén cifrado de credenciales.\n  --host HOST                 IP candidata para probe/fingerprint, sin modificar la base de datos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip ssh --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-ssh",
      "kind": "command",
      "launcher": "LANIP",
      "name": "ssh",
      "path": [
        "LANIP",
        "ssh"
      ],
      "title": "LANIP ssh",
      "usage": "LANIP ssh [-h] [--database DATABASE] [--store STORE] [--host HOST]\n                 selector {probe,fingerprint,trust,open,show} [COMANDO ...]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias del elemento.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "probe",
            "configure",
            "open"
          ],
          "default": null,
          "description": "Opción de configuración de Radmin Viewer.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "control",
            "view",
            "file",
            "shutdown",
            "chat",
            "voice",
            "message",
            "telnet"
          ],
          "default": null,
          "description": "Opción de configuración de Radmin Viewer.",
          "flags": [
            "--mode"
          ],
          "label": "--mode",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de configuración de Radmin Viewer.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Ruta por dispositivo; usa 'auto' para detección automática.",
          "flags": [
            "--executable"
          ],
          "label": "--executable",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Servidor intermedio HOST:PUERTO.",
          "flags": [
            "--through"
          ],
          "label": "--through",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre control o vista a pantalla completa.",
          "flags": [
            "--fullscreen"
          ],
          "label": "--fullscreen",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "24",
            "16",
            "8",
            "4",
            "2",
            "1"
          ],
          "default": null,
          "description": "Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).",
          "flags": [
            "--color-depth"
          ],
          "label": "--color-depth",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Máximo de actualizaciones de pantalla por segundo (1-120).",
          "flags": [
            "--updates"
          ],
          "label": "--updates",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Phonebook .rpb administrado por Radmin.",
          "flags": [
            "--phonebook"
          ],
          "label": "--phonebook",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Identificador de entrada dentro del phonebook de Radmin.",
          "flags": [
            "--phonebook-id"
          ],
          "label": "--phonebook-id",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Opción de configuración de Radmin Viewer.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Opción de configuración de Radmin Viewer.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Acceso remoto",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP radmin [-h] [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                    [--port PORT] [--executable EXECUTABLE] [--through THROUGH] [--fullscreen]\n                    [--color-depth {24,16,8,4,2,1}] [--updates UPDATES] [--phonebook PHONEBOOK]\n                    [--phonebook-id PHONEBOOK_ID] [--database DATABASE] [--store STORE]\n                    selector {probe,configure,open}",
      "details": "Usage: LANIP radmin [-h] [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                    [--port PORT] [--executable EXECUTABLE] [--through THROUGH] [--fullscreen]\n                    [--color-depth {24,16,8,4,2,1}] [--updates UPDATES] [--phonebook PHONEBOOK]\n                    [--phonebook-id PHONEBOOK_ID] [--database DATABASE] [--store STORE]\n                    selector {probe,configure,open}\n\nArguments:\n  selector                    IP, MAC o alias del elemento.\n  {probe,configure,open}      Opción de configuración de Radmin Viewer.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --mode {control,view,file,shutdown,chat,voice,message,telnet}\n                              Opción de configuración de Radmin Viewer.\n  --port PORT                 Opción de configuración de Radmin Viewer.\n  --executable EXECUTABLE     Ruta por dispositivo; usa 'auto' para detección automática.\n  --through THROUGH           Servidor intermedio HOST:PUERTO.\n  --fullscreen                Abre control o vista a pantalla completa.\n  --color-depth {24,16,8,4,2,1}\n                              Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).\n  --updates UPDATES           Máximo de actualizaciones de pantalla por segundo (1-120).\n  --phonebook PHONEBOOK       Phonebook .rpb administrado por Radmin.\n  --phonebook-id PHONEBOOK_ID\n                              Identificador de entrada dentro del phonebook de Radmin.\n  --database DATABASE         Opción de configuración de Radmin Viewer.\n  --store STORE               Opción de configuración de Radmin Viewer.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip radmin --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-radmin",
      "kind": "command",
      "launcher": "LANIP",
      "name": "radmin",
      "path": [
        "LANIP",
        "radmin"
      ],
      "title": "LANIP radmin",
      "usage": "LANIP radmin [-h] [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                    [--port PORT] [--executable EXECUTABLE] [--through THROUGH] [--fullscreen]\n                    [--color-depth {24,16,8,4,2,1}] [--updates UPDATES] [--phonebook PHONEBOOK]\n                    [--phonebook-id PHONEBOOK_ID] [--database DATABASE] [--store STORE]\n                    selector {probe,configure,open}"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "NAME [wakeup|status|shutdown|restart|sleep|hibernate|configure] o sequence ...",
          "flags": [],
          "label": "words",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Condición AND adicional (repetible).",
          "flags": [
            "-if",
            "--if"
          ],
          "label": "-if, --if",
          "metavar": "CONDICIÓN",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Condición AND adicional.",
          "flags": [
            "--if-all"
          ],
          "label": "--if-all",
          "metavar": "CONDICIÓN",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Condición OR adicional.",
          "flags": [
            "--if-any"
          ],
          "label": "--if-any",
          "metavar": "CONDICIÓN",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Condición negada.",
          "flags": [
            "--if-not"
          ],
          "label": "--if-not",
          "metavar": "CONDICIÓN",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Momento del apagado programado.",
          "flags": [
            "-t",
            "--time"
          ],
          "label": "-t, --time",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Mensaje remoto, si el transporte lo admite.",
          "flags": [
            "--message"
          ],
          "label": "--message",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Solicita cierre forzado al transporte.",
          "flags": [
            "--force"
          ],
          "label": "--force",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Cancela una programación, si el transporte lo admite.",
          "flags": [
            "--cancel"
          ],
          "label": "--cancel",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "IPv4 de broadcast.",
          "flags": [
            "--broadcast"
          ],
          "label": "--broadcast",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Puerto UDP WOL.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Número de paquetes mágicos.",
          "flags": [
            "--repeat"
          ],
          "label": "--repeat",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo entre paquetes.",
          "flags": [
            "--interval"
          ],
          "label": "--interval",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Segundos máximos de verificación.",
          "flags": [
            "--wait"
          ],
          "label": "--wait",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "auto",
            "arp",
            "ping",
            "port"
          ],
          "default": null,
          "description": "Método de verificación.",
          "flags": [
            "--method"
          ],
          "label": "--method",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Puerto TCP de comprobación.",
          "flags": [
            "--check-port"
          ],
          "label": "--check-port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "IPv4 local de salida.",
          "flags": [
            "--interface"
          ],
          "label": "--interface",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Reintentos completos.",
          "flags": [
            "--retry"
          ],
          "label": "--retry",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Valida sin enviar.",
          "flags": [
            "--dry-run"
          ],
          "label": "--dry-run",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Salida JSON estructurada.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Omite salida humana.",
          "flags": [
            "--quiet"
          ],
          "label": "--quiet",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Actúa sobre un grupo.",
          "flags": [
            "--group"
          ],
          "label": "--group",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Actúa sobre todo el inventario.",
          "flags": [
            "--all"
          ],
          "label": "--all",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Confirma explícitamente --all.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Dependencia de paso.",
          "flags": [
            "--after"
          ],
          "label": "--after",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Espera previa del paso.",
          "flags": [
            "--delay"
          ],
          "label": "--delay",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "60",
          "description": "Timeout de paso.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "stop",
            "continue",
            "retry"
          ],
          "default": "stop",
          "description": "Política ante fallo.",
          "flags": [
            "--on-failure"
          ],
          "label": "--on-failure",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Espera mínima entre ejecuciones.",
          "flags": [
            "--cooldown"
          ],
          "label": "--cooldown",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "1",
          "description": "Máximo de intentos.",
          "flags": [
            "--max-attempts"
          ],
          "label": "--max-attempts",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "ssh",
            "disabled"
          ],
          "default": null,
          "description": "Transporte autorizado para apagar o reiniciar.",
          "flags": [
            "--power-transport"
          ],
          "label": "--power-transport",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "windows",
            "linux"
          ],
          "default": null,
          "description": "Sistema operativo remoto.",
          "flags": [
            "--power-platform"
          ],
          "label": "--power-platform",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Plantilla administrada ACCIÓN=COMANDO.",
          "flags": [
            "--power-command"
          ],
          "label": "--power-command",
          "metavar": "ACCIÓN=COMANDO",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/wol-sequences.json",
          "description": "Archivo transaccional de secuencias.",
          "flags": [
            "--sequences"
          ],
          "label": "--sequences",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Automatización",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP wol [-h] [-if CONDICIÓN] [--if-all CONDICIÓN] [--if-any CONDICIÓN]\n                 [--if-not CONDICIÓN] [-t SCHEDULE] [--message MESSAGE] [--force] [--cancel]\n                 [--broadcast BROADCAST] [--port PORT] [--repeat REPEAT] [--interval INTERVAL]\n                 [--wait WAIT] [--method {auto,arp,ping,port}] [--check-port CHECK_PORT]\n                 [--interface INTERFACE] [--retry RETRY] [--dry-run] [--json] [--quiet]\n                 [--group GROUP] [--all] [--yes] [--after AFTER] [--delay DELAY]\n                 [--timeout TIMEOUT] [--on-failure {stop,continue,retry}] [--cooldown COOLDOWN]\n                 [--max-attempts MAX_ATTEMPTS] [--power-transport {ssh,disabled}]\n                 [--power-platform {windows,linux}] [--power-command ACCIÓN=COMANDO]\n                 [--database DATABASE] [--store STORE] [--sequences SEQUENCES]\n                 [words ...]",
      "details": "Usage: LANIP wol [-h] [-if CONDICIÓN] [--if-all CONDICIÓN] [--if-any CONDICIÓN]\n                 [--if-not CONDICIÓN] [-t SCHEDULE] [--message MESSAGE] [--force] [--cancel]\n                 [--broadcast BROADCAST] [--port PORT] [--repeat REPEAT] [--interval INTERVAL]\n                 [--wait WAIT] [--method {auto,arp,ping,port}] [--check-port CHECK_PORT]\n                 [--interface INTERFACE] [--retry RETRY] [--dry-run] [--json] [--quiet]\n                 [--group GROUP] [--all] [--yes] [--after AFTER] [--delay DELAY]\n                 [--timeout TIMEOUT] [--on-failure {stop,continue,retry}] [--cooldown COOLDOWN]\n                 [--max-attempts MAX_ATTEMPTS] [--power-transport {ssh,disabled}]\n                 [--power-platform {windows,linux}] [--power-command ACCIÓN=COMANDO]\n                 [--database DATABASE] [--store STORE] [--sequences SEQUENCES]\n                 [words ...]\n\nArguments:\n  words                       NAME [wakeup|status|shutdown|restart|sleep|hibernate|configure] o\n                              sequence ...\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -if CONDICIÓN, --if CONDICIÓN\n                              Condición AND adicional (repetible).\n  --if-all CONDICIÓN          Condición AND adicional.\n  --if-any CONDICIÓN          Condición OR adicional.\n  --if-not CONDICIÓN          Condición negada.\n  -t SCHEDULE, --time SCHEDULE\n                              Momento del apagado programado.\n  --message MESSAGE           Mensaje remoto, si el transporte lo admite.\n  --force                     Solicita cierre forzado al transporte.\n  --cancel                    Cancela una programación, si el transporte lo admite.\n  --broadcast BROADCAST       IPv4 de broadcast.\n  --port PORT                 Puerto UDP WOL.\n  --repeat REPEAT             Número de paquetes mágicos.\n  --interval INTERVAL         Intervalo entre paquetes.\n  --wait WAIT                 Segundos máximos de verificación.\n  --method {auto,arp,ping,port}\n                              Método de verificación.\n  --check-port CHECK_PORT     Puerto TCP de comprobación.\n  --interface INTERFACE       IPv4 local de salida.\n  --retry RETRY               Reintentos completos.\n  --dry-run                   Valida sin enviar.\n  --json                      Salida JSON estructurada.\n  --quiet                     Omite salida humana.\n  --group GROUP               Actúa sobre un grupo.\n  --all                       Actúa sobre todo el inventario.\n  --yes                       Confirma explícitamente --all.\n  --after AFTER               Dependencia de paso.\n  --delay DELAY               Espera previa del paso.\n  --timeout TIMEOUT           Timeout de paso.\n  --on-failure {stop,continue,retry}\n                              Política ante fallo.\n  --cooldown COOLDOWN         Espera mínima entre ejecuciones.\n  --max-attempts MAX_ATTEMPTS\n                              Máximo de intentos.\n  --power-transport {ssh,disabled}\n                              Transporte autorizado para apagar o reiniciar.\n  --power-platform {windows,linux}\n                              Sistema operativo remoto.\n  --power-command ACCIÓN=COMANDO\n                              Plantilla administrada ACCIÓN=COMANDO.\n  --database DATABASE         Archivo JSON de elementos.\n  --store STORE               Almacén cifrado de credenciales.\n  --sequences SEQUENCES       Archivo transaccional de secuencias.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip wol --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-wol",
      "kind": "command",
      "launcher": "LANIP",
      "name": "wol",
      "path": [
        "LANIP",
        "wol"
      ],
      "title": "LANIP wol",
      "usage": "LANIP wol [-h] [-if CONDICIÓN] [--if-all CONDICIÓN] [--if-any CONDICIÓN]\n                 [--if-not CONDICIÓN] [-t SCHEDULE] [--message MESSAGE] [--force] [--cancel]\n                 [--broadcast BROADCAST] [--port PORT] [--repeat REPEAT] [--interval INTERVAL]\n                 [--wait WAIT] [--method {auto,arp,ping,port}] [--check-port CHECK_PORT]\n                 [--interface INTERFACE] [--retry RETRY] [--dry-run] [--json] [--quiet]\n                 [--group GROUP] [--all] [--yes] [--after AFTER] [--delay DELAY]\n                 [--timeout TIMEOUT] [--on-failure {stop,continue,retry}] [--cooldown COOLDOWN]\n                 [--max-attempts MAX_ATTEMPTS] [--power-transport {ssh,disabled}]\n                 [--power-platform {windows,linux}] [--power-command ACCIÓN=COMANDO]\n                 [--database DATABASE] [--store STORE] [--sequences SEQUENCES]\n                 [words ...]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "DeviceId, alias, nombre, MAC, IP actual o histórica.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Incluye eventos generales de toda la LAN.",
          "flags": [
            "--all"
          ],
          "label": "--all",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "En CLI interactiva muestra los comandos de la sesión.",
          "flags": [
            "--commands"
          ],
          "label": "--commands",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Limita la consulta al día local actual.",
          "flags": [
            "--today"
          ],
          "label": "--today",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Fecha inicial YYYY-MM-DD.",
          "flags": [
            "--from"
          ],
          "label": "--from",
          "metavar": "FECHA",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Fecha final YYYY-MM-DD.",
          "flags": [
            "--to"
          ],
          "label": "--to",
          "metavar": "FECHA",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Tipo canónico; se puede repetir.",
          "flags": [
            "--type"
          ],
          "label": "--type",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Filtra por origen.",
          "flags": [
            "--source"
          ],
          "label": "--source",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Filtra por resultado.",
          "flags": [
            "--result"
          ],
          "label": "--result",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra únicamente errores.",
          "flags": [
            "--errors"
          ],
          "label": "--errors",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Busca texto seguro.",
          "flags": [
            "--search"
          ],
          "label": "--search",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "100",
          "description": "Máximo de eventos (1..10000).",
          "flags": [
            "--limit"
          ],
          "label": "--limit",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Orden descendente.",
          "flags": [
            "--reverse"
          ],
          "label": "--reverse",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "table",
            "json",
            "csv"
          ],
          "default": "table",
          "description": "Formato de salida.",
          "flags": [
            "--format"
          ],
          "label": "--format",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Datos y exportación",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP history [-h] [--all] [--commands] [--today] [--from FECHA] [--to FECHA]\n                     [--type TYPES] [--source SOURCE] [--result RESULT] [--errors]\n                     [--search SEARCH] [--limit LIMIT] [--reverse] [--format {table,json,csv}]\n                     [selector]",
      "details": "Usage: LANIP history [-h] [--all] [--commands] [--today] [--from FECHA] [--to FECHA]\n                     [--type TYPES] [--source SOURCE] [--result RESULT] [--errors]\n                     [--search SEARCH] [--limit LIMIT] [--reverse] [--format {table,json,csv}]\n                     [selector]\n\nArguments:\n  selector                   DeviceId, alias, nombre, MAC, IP actual o histórica.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --all                      Incluye eventos generales de toda la LAN.\n  --commands                 En CLI interactiva muestra los comandos de la sesión.\n  --today                    Limita la consulta al día local actual.\n  --from FECHA               Fecha inicial YYYY-MM-DD.\n  --to FECHA                 Fecha final YYYY-MM-DD.\n  --type TYPES               Tipo canónico; se puede repetir.\n  --source SOURCE            Filtra por origen.\n  --result RESULT            Filtra por resultado.\n  --errors                   Muestra únicamente errores.\n  --search SEARCH            Busca texto seguro.\n  --limit LIMIT              Máximo de eventos (1..10000).\n  --reverse                  Orden descendente.\n  --format {table,json,csv}  Formato de salida.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip history --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-history",
      "kind": "command",
      "launcher": "LANIP",
      "name": "history",
      "path": [
        "LANIP",
        "history"
      ],
      "title": "LANIP history",
      "usage": "LANIP history [-h] [--all] [--commands] [--today] [--from FECHA] [--to FECHA]\n                     [--type TYPES] [--source SOURCE] [--result RESULT] [--errors]\n                     [--search SEARCH] [--limit LIMIT] [--reverse] [--format {table,json,csv}]\n                     [selector]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "attach, detach, status, once, session, incidents, incident, service o foreground.",
          "flags": [],
          "label": "words",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--project"
          ],
          "label": "--project",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--permanent"
          ],
          "label": "--permanent",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--duration"
          ],
          "label": "--duration",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "permanent",
            "temporary",
            "diagnostic",
            "once"
          ],
          "default": "temporary",
          "description": "Opción operativa del monitor.",
          "flags": [
            "--mode"
          ],
          "label": "--mode",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "observe",
            "operate",
            "administer"
          ],
          "default": "observe",
          "description": "Opción operativa del monitor.",
          "flags": [
            "--authority"
          ],
          "label": "--authority",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--interval"
          ],
          "label": "--interval",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--every"
          ],
          "label": "--every",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--group"
          ],
          "label": "--group",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "presence",
            "services",
            "ports",
            "identity",
            "smb",
            "full"
          ],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--type"
          ],
          "label": "--type",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--fast"
          ],
          "label": "--fast",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--unknown"
          ],
          "label": "--unknown",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--follow"
          ],
          "label": "--follow",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/sessions.json",
          "description": "Estado runtime de sesiones.",
          "flags": [
            "--sessions"
          ],
          "label": "--sessions",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/incidents.json",
          "description": "Estado runtime de incidencias.",
          "flags": [
            "--incidents-store"
          ],
          "label": "--incidents-store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/monitor.lock",
          "description": "Lock singleton del monitor.",
          "flags": [
            "--lock"
          ],
          "label": "--lock",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/monitor.db",
          "description": "Repositorio SQLite del monitor.",
          "flags": [
            "--monitor-db"
          ],
          "label": "--monitor-db",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/profiles.json",
          "description": "Perfiles personalizados.",
          "flags": [
            "--profiles"
          ],
          "label": "--profiles",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/assignments.json",
          "description": "Asignaciones persistentes.",
          "flags": [
            "--assignments-store"
          ],
          "label": "--assignments-store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Perfil monitor.",
          "flags": [
            "--profile"
          ],
          "label": "--profile",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "low",
            "normal",
            "high",
            "critical"
          ],
          "default": "normal",
          "description": "Prioridad de asignación.",
          "flags": [
            "--priority"
          ],
          "label": "--priority",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Check ping, arp o port:NN.",
          "flags": [
            "--check"
          ],
          "label": "--check",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo de presencia.",
          "flags": [
            "--presence"
          ],
          "label": "--presence",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo de descubrimiento.",
          "flags": [
            "--discovery"
          ],
          "label": "--discovery",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo de servicios.",
          "flags": [
            "--services"
          ],
          "label": "--services",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo profundo.",
          "flags": [
            "--deep"
          ],
          "label": "--deep",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Workers del perfil.",
          "flags": [
            "--workers"
          ],
          "label": "--workers",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Timeout del perfil.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Monitorización",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP monitor [-h] [--project PROJECT] [--permanent] [--duration DURATION]\n                     [--mode {permanent,temporary,diagnostic,once}]\n                     [--authority {observe,operate,administer}] [--json] [--yes]\n                     [--interval INTERVAL] [--every EVERY] [--group GROUP]\n                     [--type {presence,services,ports,identity,smb,full}] [--fast] [--unknown]\n                     [--follow] [--sessions SESSIONS] [--incidents-store INCIDENTS_STORE]\n                     [--lock LOCK] [--monitor-db MONITOR_DB] [--profiles PROFILES]\n                     [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n                     [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n                     [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP]\n                     [--workers WORKERS] [--timeout TIMEOUT]\n                     [words ...]",
      "details": "Usage: LANIP monitor [-h] [--project PROJECT] [--permanent] [--duration DURATION]\n                     [--mode {permanent,temporary,diagnostic,once}]\n                     [--authority {observe,operate,administer}] [--json] [--yes]\n                     [--interval INTERVAL] [--every EVERY] [--group GROUP]\n                     [--type {presence,services,ports,identity,smb,full}] [--fast] [--unknown]\n                     [--follow] [--sessions SESSIONS] [--incidents-store INCIDENTS_STORE]\n                     [--lock LOCK] [--monitor-db MONITOR_DB] [--profiles PROFILES]\n                     [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n                     [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n                     [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP]\n                     [--workers WORKERS] [--timeout TIMEOUT]\n                     [words ...]\n\nArguments:\n  words                       attach, detach, status, once, session, incidents, incident, service\n                              o foreground.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --project PROJECT           Opción operativa del monitor.\n  --permanent                 Opción operativa del monitor.\n  --duration DURATION         Opción operativa del monitor.\n  --mode {permanent,temporary,diagnostic,once}\n                              Opción operativa del monitor.\n  --authority {observe,operate,administer}\n                              Opción operativa del monitor.\n  --json                      Opción operativa del monitor.\n  --yes                       Opción operativa del monitor.\n  --interval INTERVAL         Opción operativa del monitor.\n  --every EVERY               Opción operativa del monitor.\n  --group GROUP               Opción operativa del monitor.\n  --type {presence,services,ports,identity,smb,full}\n                              Opción operativa del monitor.\n  --fast                      Opción operativa del monitor.\n  --unknown                   Opción operativa del monitor.\n  --follow                    Opción operativa del monitor.\n  --sessions SESSIONS         Estado runtime de sesiones.\n  --incidents-store INCIDENTS_STORE\n                              Estado runtime de incidencias.\n  --lock LOCK                 Lock singleton del monitor.\n  --monitor-db MONITOR_DB     Repositorio SQLite del monitor.\n  --profiles PROFILES         Perfiles personalizados.\n  --assignments-store ASSIGNMENTS_STORE\n                              Asignaciones persistentes.\n  --profile PROFILE           Perfil monitor.\n  --priority {low,normal,high,critical}\n                              Prioridad de asignación.\n  --check CHECK               Check ping, arp o port:NN.\n  --presence PRESENCE         Intervalo de presencia.\n  --discovery DISCOVERY       Intervalo de descubrimiento.\n  --services SERVICES         Intervalo de servicios.\n  --deep DEEP                 Intervalo profundo.\n  --workers WORKERS           Workers del perfil.\n  --timeout TIMEOUT           Timeout del perfil.",
      "docs": [
        "MONITOR.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip monitor --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-monitor",
      "kind": "command",
      "launcher": "LANIP",
      "name": "monitor",
      "path": [
        "LANIP",
        "monitor"
      ],
      "title": "LANIP monitor",
      "usage": "LANIP monitor [-h] [--project PROJECT] [--permanent] [--duration DURATION]\n                     [--mode {permanent,temporary,diagnostic,once}]\n                     [--authority {observe,operate,administer}] [--json] [--yes]\n                     [--interval INTERVAL] [--every EVERY] [--group GROUP]\n                     [--type {presence,services,ports,identity,smb,full}] [--fast] [--unknown]\n                     [--follow] [--sessions SESSIONS] [--incidents-store INCIDENTS_STORE]\n                     [--lock LOCK] [--monitor-db MONITOR_DB] [--profiles PROFILES]\n                     [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n                     [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n                     [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP]\n                     [--workers WORKERS] [--timeout TIMEOUT]\n                     [words ...]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "init, status, enable, disable, configure, user, role, session, web o certificate.",
          "flags": [],
          "label": "words",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--bind"
          ],
          "label": "--bind",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--cidr"
          ],
          "label": "--cidr",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--password-auth"
          ],
          "label": "--password-auth",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Opción de acceso remoto.",
          "flags": [
            "--role"
          ],
          "label": "--role",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Opción de acceso remoto.",
          "flags": [
            "--ssh-key"
          ],
          "label": "--ssh-key",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--expires"
          ],
          "label": "--expires",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Opción de acceso remoto.",
          "flags": [
            "--permission"
          ],
          "label": "--permission",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--certificate"
          ],
          "label": "--certificate",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--private-key"
          ],
          "label": "--private-key",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--common-name"
          ],
          "label": "--common-name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción de acceso remoto.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "user",
            "service"
          ],
          "default": "user",
          "description": "Separa credenciales del usuario y del servicio permanente.",
          "flags": [
            "--scope"
          ],
          "label": "--scope",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/access/config.json",
          "description": "Configuración remota separada.",
          "flags": [
            "--config"
          ],
          "label": "--config",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/access/users.dc",
          "description": "Almacén de usuarios remotos.",
          "flags": [
            "--users"
          ],
          "label": "--users",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Acceso remoto",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP access [-h] [--bind BIND] [--cidr CIDR] [--port PORT] [--password-auth {on,off}]\n                    [--role ROLE] [--ssh-key SSH_KEY] [--expires EXPIRES]\n                    [--permission PERMISSION] [--certificate CERTIFICATE]\n                    [--private-key PRIVATE_KEY] [--common-name COMMON_NAME] [--yes] [--json]\n                    [--scope {user,service}] [--config CONFIG] [--users USERS]\n                    [words ...]",
      "details": "Usage: LANIP access [-h] [--bind BIND] [--cidr CIDR] [--port PORT] [--password-auth {on,off}]\n                    [--role ROLE] [--ssh-key SSH_KEY] [--expires EXPIRES]\n                    [--permission PERMISSION] [--certificate CERTIFICATE]\n                    [--private-key PRIVATE_KEY] [--common-name COMMON_NAME] [--yes] [--json]\n                    [--scope {user,service}] [--config CONFIG] [--users USERS]\n                    [words ...]\n\nArguments:\n  words                      init, status, enable, disable, configure, user, role, session, web o\n                             certificate.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --bind BIND                Opción de acceso remoto.\n  --cidr CIDR                Opción de acceso remoto.\n  --port PORT                Opción de acceso remoto.\n  --password-auth {on,off}   Opción de acceso remoto.\n  --role ROLE                Opción de acceso remoto.\n  --ssh-key SSH_KEY          Opción de acceso remoto.\n  --expires EXPIRES          Opción de acceso remoto.\n  --permission PERMISSION    Opción de acceso remoto.\n  --certificate CERTIFICATE  Opción de acceso remoto.\n  --private-key PRIVATE_KEY  Opción de acceso remoto.\n  --common-name COMMON_NAME  Opción de acceso remoto.\n  --yes                      Opción de acceso remoto.\n  --json                     Opción de acceso remoto.\n  --scope {user,service}     Separa credenciales del usuario y del servicio permanente.\n  --config CONFIG            Configuración remota separada.\n  --users USERS              Almacén de usuarios remotos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip access --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-access",
      "kind": "command",
      "launcher": "LANIP",
      "name": "access",
      "path": [
        "LANIP",
        "access"
      ],
      "title": "LANIP access",
      "usage": "LANIP access [-h] [--bind BIND] [--cidr CIDR] [--port PORT] [--password-auth {on,off}]\n                    [--role ROLE] [--ssh-key SSH_KEY] [--expires EXPIRES]\n                    [--permission PERMISSION] [--certificate CERTIFICATE]\n                    [--private-key PRIVATE_KEY] [--common-name COMMON_NAME] [--yes] [--json]\n                    [--scope {user,service}] [--config CONFIG] [--users USERS]\n                    [words ...]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Servidor/dispositivo (sin acción equivale a info).",
          "flags": [],
          "label": "name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "scan, info, shares, open, printers, workgroups, connect, disconnect, status o printer.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Carpeta o impresora compartida.",
          "flags": [],
          "label": "resource",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "open",
            "queue",
            "connect"
          ],
          "default": null,
          "description": "Acción sobre la impresora.",
          "flags": [],
          "label": "resource_action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Examina todo el inventario LANCTL.",
          "flags": [
            "--network"
          ],
          "label": "--network",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Limita el escaneo a un grupo LANCTL.",
          "flags": [
            "--group"
          ],
          "label": "--group",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "0.8",
          "description": "Tiempo máximo del probe TCP.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "32",
          "description": "Número máximo de probes concurrentes.",
          "flags": [
            "--workers"
          ],
          "label": "--workers",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "No carga credenciales asociadas.",
          "flags": [
            "--anonymous"
          ],
          "label": "--anonymous",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Incluye recursos administrativos y especiales.",
          "flags": [
            "--include-system"
          ],
          "label": "--include-system",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra el plan sin autenticar, abrir ni mutar.",
          "flags": [
            "--dry-run"
          ],
          "label": "--dry-run",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Confirma una conexión de impresora.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Emite JSON estructurado.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON del inventario.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén DPAPI de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/plugin-storage",
          "description": "Directorio de observaciones de plugins.",
          "flags": [
            "--storage"
          ],
          "label": "--storage",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Acceso remoto",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP smb [-h] [--network] [--group GROUP] [--timeout TIMEOUT] [--workers WORKERS]\n                 [--anonymous] [--include-system] [--dry-run] [--yes] [--json]\n                 [--database DATABASE] [--store STORE] [--storage STORAGE]\n                 [name] [action] [resource] [{open,queue,connect}]",
      "details": "Usage: LANIP smb [-h] [--network] [--group GROUP] [--timeout TIMEOUT] [--workers WORKERS]\n                 [--anonymous] [--include-system] [--dry-run] [--yes] [--json]\n                 [--database DATABASE] [--store STORE] [--storage STORAGE]\n                 [name] [action] [resource] [{open,queue,connect}]\n\nArguments:\n  name                  Servidor/dispositivo (sin acción equivale a info).\n  action                scan, info, shares, open, printers, workgroups, connect, disconnect,\n                        status o printer.\n  resource              Carpeta o impresora compartida.\n  {open,queue,connect}  Acción sobre la impresora.\n\nOptions:\n  -h, --help            Show this help and exit.\n  --network             Examina todo el inventario LANCTL.\n  --group GROUP         Limita el escaneo a un grupo LANCTL.\n  --timeout TIMEOUT     Tiempo máximo del probe TCP.\n  --workers WORKERS     Número máximo de probes concurrentes.\n  --anonymous           No carga credenciales asociadas.\n  --include-system      Incluye recursos administrativos y especiales.\n  --dry-run             Muestra el plan sin autenticar, abrir ni mutar.\n  --yes                 Confirma una conexión de impresora.\n  --json                Emite JSON estructurado.\n  --database DATABASE   Archivo JSON del inventario.\n  --store STORE         Almacén DPAPI de credenciales.\n  --storage STORAGE     Directorio de observaciones de plugins.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip smb --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-smb",
      "kind": "command",
      "launcher": "LANIP",
      "name": "smb",
      "path": [
        "LANIP",
        "smb"
      ],
      "title": "LANIP smb",
      "usage": "LANIP smb [-h] [--network] [--group GROUP] [--timeout TIMEOUT] [--workers WORKERS]\n                 [--anonymous] [--include-system] [--dry-run] [--yes] [--json]\n                 [--database DATABASE] [--store STORE] [--storage STORAGE]\n                 [name] [action] [resource] [{open,queue,connect}]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias del elemento.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Protocolo si hay varias terminales.",
          "flags": [
            "-p",
            "--protocol"
          ],
          "label": "-p, --protocol",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Usa el cliente SSH nativo sin la capa de color de LANCTL.",
          "flags": [
            "--native"
          ],
          "label": "--native",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Acceso remoto",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP terminal [-h] [-p PROTOCOL] [--native] [--database DATABASE] [--store STORE] selector",
      "details": "Usage: LANIP terminal [-h] [-p PROTOCOL] [--native] [--database DATABASE] [--store STORE] selector\n\nArguments:\n  selector                    IP, MAC o alias del elemento.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -p PROTOCOL, --protocol PROTOCOL\n                              Protocolo si hay varias terminales.\n  --native                    Usa el cliente SSH nativo sin la capa de color de LANCTL.\n  --database DATABASE         Archivo JSON de elementos.\n  --store STORE               Almacén cifrado de credenciales.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip terminal --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-terminal",
      "kind": "command",
      "launcher": "LANIP",
      "name": "terminal",
      "path": [
        "LANIP",
        "terminal"
      ],
      "title": "LANIP terminal",
      "usage": "LANIP terminal [-h] [-p PROTOCOL] [--native] [--database DATABASE] [--store STORE] selector"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias del switch.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Perfil Cisco que remapea los puertos.",
          "flags": [
            "--profile"
          ],
          "label": "--profile",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/cisco_profiles.json",
          "description": "Archivo JSON que contiene los perfiles Cisco.",
          "flags": [
            "--profiles"
          ],
          "label": "--profiles",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Solo muestra el plan.",
          "flags": [
            "--dry-run"
          ],
          "label": "--dry-run",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Confirma cambios sin preguntar.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Acción Cisco gestionada que se quiere planificar.",
          "flags": [],
          "label": "arguments",
          "metavar": "COMANDO",
          "required": true
        }
      ],
      "category": "Infraestructura de red",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Comandos Cisco gestionados:\n  show COMANDO\n  port list\n  port label PUERTO NOMBRE\n  port unlabel PUERTO\n  port show [PUERTO] status|description|config|errors|vlan\n  port set [PUERTO] description|speed|duplex VALOR\n  port enable|disable|reset [PUERTO]\n  start|stop|reset [PUERTO]\n  save-config\n  terminal\n\nOpciones globales: --profile PERFIL --dry-run --yes\nEsta fase utiliza un adaptador simulado y no conecta con el switch.",
      "details": "Usage: LANIP switch [-h] [--profile PROFILE] [--profiles PROFILES] [--database DATABASE]\n                    [--dry-run] [--yes]\n                    selector ...\n\nComandos Cisco gestionados:\n  show COMANDO\n  port list\n  port label PUERTO NOMBRE\n  port unlabel PUERTO\n  port show [PUERTO] status|description|config|errors|vlan\n  port set [PUERTO] description|speed|duplex VALOR\n  port enable|disable|reset [PUERTO]\n  start|stop|reset [PUERTO]\n  save-config\n  terminal\n\nOpciones globales: --profile PERFIL --dry-run --yes\nEsta fase utiliza un adaptador simulado y no conecta con el switch.\n\nArguments:\n  selector             IP, MAC o alias del switch.\n  COMANDO              Acción Cisco gestionada que se quiere planificar.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --profile PROFILE    Perfil Cisco que remapea los puertos.\n  --profiles PROFILES  Archivo JSON que contiene los perfiles Cisco.\n  --database DATABASE  Archivo JSON de elementos.\n  --dry-run            Solo muestra el plan.\n  --yes                Confirma cambios sin preguntar.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip switch --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-switch",
      "kind": "command",
      "launcher": "LANIP",
      "name": "switch",
      "path": [
        "LANIP",
        "switch"
      ],
      "title": "LANIP switch",
      "usage": "LANIP switch [-h] [--profile PROFILE] [--profiles PROFILES] [--database DATABASE]\n                    [--dry-run] [--yes]\n                    selector ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Nombre del grupo.",
          "flags": [],
          "label": "name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Crea el grupo.",
          "flags": [
            "-new"
          ],
          "label": "-new",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Elimina el grupo.",
          "flags": [
            "-del"
          ],
          "label": "-del",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Renombra el grupo.",
          "flags": [
            "-rename"
          ],
          "label": "-rename",
          "metavar": "NUEVO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Edita su descripción.",
          "flags": [
            "-description"
          ],
          "label": "-description",
          "metavar": "TEXTO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Añade IP, MAC o alias.",
          "flags": [
            "-add"
          ],
          "label": "-add",
          "metavar": "ELEMENTO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Retira IP, MAC o alias.",
          "flags": [
            "-remove"
          ],
          "label": "-remove",
          "metavar": "ELEMENTO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Lista los elementos que pertenecen al grupo.",
          "flags": [
            "-list"
          ],
          "label": "-list",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/groups.json",
          "description": "Archivo JSON de grupos.",
          "flags": [
            "--groups"
          ],
          "label": "--groups",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Grupos de comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP group [-h]\n                   [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENTO | -remove ELEMENTO | -list]\n                   [--database DATABASE] [--groups GROUPS]\n                   [name]",
      "details": "Usage: LANIP group [-h]\n                   [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENTO | -remove ELEMENTO | -list]\n                   [--database DATABASE] [--groups GROUPS]\n                   [name]\n\nArguments:\n  name                 Nombre del grupo.\n\nOptions:\n  -h, --help           Show this help and exit.\n  -new                 Crea el grupo.\n  -del                 Elimina el grupo.\n  -rename NUEVO        Renombra el grupo.\n  -description TEXTO   Edita su descripción.\n  -add ELEMENTO        Añade IP, MAC o alias.\n  -remove ELEMENTO     Retira IP, MAC o alias.\n  -list                Lista los elementos que pertenecen al grupo.\n  --database DATABASE  Archivo JSON de elementos.\n  --groups GROUPS      Archivo JSON de grupos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip group --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-group",
      "kind": "command",
      "launcher": "LANIP",
      "name": "group",
      "path": [
        "LANIP",
        "group"
      ],
      "title": "LANIP group",
      "usage": "LANIP group [-h]\n                   [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENTO | -remove ELEMENTO | -list]\n                   [--database DATABASE] [--groups GROUPS]\n                   [name]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC o alias.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "edit",
            "ip",
            "cnf",
            "name",
            "description",
            "alias",
            "idf",
            "group",
            "protocol",
            "delete",
            "del",
            "remove"
          ],
          "default": null,
          "description": "Campo o acción que se quiere editar.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Nuevo valor.",
          "flags": [],
          "label": "values",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Añade un elemento nuevo utilizando su dirección MAC.",
          "flags": [
            "-add"
          ],
          "label": "-add",
          "metavar": "MAC",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Asigna NAME al elemento indicado.",
          "flags": [
            "-name",
            "--name"
          ],
          "label": "-name, --name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Asigna una dirección IPv4.",
          "flags": [
            "-ip",
            "--ip"
          ],
          "label": "-ip, --ip",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Asigna ALIAS al elemento indicado.",
          "flags": [
            "-alias",
            "--alias"
          ],
          "label": "-alias, --alias",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Asigna DESCRIPTION al elemento indicado (máximo 42 caracteres).",
          "flags": [
            "-description",
            "--description"
          ],
          "label": "-description, --description",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Asigna el estado CNF.",
          "flags": [
            "-cnf",
            "--cnf"
          ],
          "label": "-cnf, --cnf",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Asigna un IDF único (2-5 letras y 2-5 dígitos).",
          "flags": [
            "-idf",
            "--idf"
          ],
          "label": "-idf, --idf",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Añade el elemento al grupo.",
          "flags": [
            "-group",
            "--group"
          ],
          "label": "-group, --group",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Activa un protocolo.",
          "flags": [
            "-protocol",
            "--protocol"
          ],
          "label": "-protocol, --protocol",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Elimina completamente el elemento indicado.",
          "flags": [
            "-delete",
            "--delete"
          ],
          "label": "-delete, --delete",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Archivo JSON de elementos.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/groups.json",
          "description": "Archivo JSON de grupos.",
          "flags": [
            "--groups"
          ],
          "label": "--groups",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Elimina sin solicitar confirmación.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Inventario y edición",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP element [-h] [-add MAC] [-name NEW_NAME] [-ip NEW_IP] [-alias NEW_ALIAS]\n                     [-description NEW_DESCRIPTION] [-cnf NEW_CNF] [-idf NEW_IDF]\n                     [-group NEW_GROUP] [-protocol NEW_PROTOCOL] [-delete] [--database DATABASE]\n                     [--groups GROUPS] [--yes]\n                     [selector]\n                     [{edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}]\n                     [values ...]",
      "details": "Usage: LANIP element [-h] [-add MAC] [-name NEW_NAME] [-ip NEW_IP] [-alias NEW_ALIAS]\n                     [-description NEW_DESCRIPTION] [-cnf NEW_CNF] [-idf NEW_IDF]\n                     [-group NEW_GROUP] [-protocol NEW_PROTOCOL] [-delete] [--database DATABASE]\n                     [--groups GROUPS] [--yes]\n                     [selector]\n                     [{edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}]\n                     [values ...]\n\nArguments:\n  selector                    IP, MAC o alias.\n  {edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}\n                              Campo o acción que se quiere editar.\n  values                      Nuevo valor.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -add MAC                    Añade un elemento nuevo utilizando su dirección MAC.\n  -name NEW_NAME, --name NEW_NAME\n                              Asigna NAME al elemento indicado.\n  -ip NEW_IP, --ip NEW_IP     Asigna una dirección IPv4.\n  -alias NEW_ALIAS, --alias NEW_ALIAS\n                              Asigna ALIAS al elemento indicado.\n  -description NEW_DESCRIPTION, --description NEW_DESCRIPTION\n                              Asigna DESCRIPTION al elemento indicado (máximo 42 caracteres).\n  -cnf NEW_CNF, --cnf NEW_CNF\n                              Asigna el estado CNF.\n  -idf NEW_IDF, --idf NEW_IDF\n                              Asigna un IDF único (2-5 letras y 2-5 dígitos).\n  -group NEW_GROUP, --group NEW_GROUP\n                              Añade el elemento al grupo.\n  -protocol NEW_PROTOCOL, --protocol NEW_PROTOCOL\n                              Activa un protocolo.\n  -delete, --delete           Elimina completamente el elemento indicado.\n  --database DATABASE         Archivo JSON de elementos.\n  --groups GROUPS             Archivo JSON de grupos.\n  --yes                       Elimina sin solicitar confirmación.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip element --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-element",
      "kind": "command",
      "launcher": "LANIP",
      "name": "element",
      "path": [
        "LANIP",
        "element"
      ],
      "title": "LANIP element",
      "usage": "LANIP element [-h] [-add MAC] [-name NEW_NAME] [-ip NEW_IP] [-alias NEW_ALIAS]\n                     [-description NEW_DESCRIPTION] [-cnf NEW_CNF] [-idf NEW_IDF]\n                     [-group NEW_GROUP] [-protocol NEW_PROTOCOL] [-delete] [--database DATABASE]\n                     [--groups GROUPS] [--yes]\n                     [selector]\n                     [{edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}]\n                     [values ...]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Proyectos",
      "children": [
        "status",
        "create",
        "update",
        "save",
        "info",
        "verify",
        "use",
        "list"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project [-h] ACCIÓN ...",
      "details": "Usage: LANIP project [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    status    Muestra el proyecto activo.\n    create    Crea un proyecto VLF vacío por defecto.\n    update    Actualiza datos activos conservando información complementaria.\n    save      Guarda manualmente el proyecto VLF activo.\n    info      Muestra los metadatos del proyecto.\n    verify    Comprueba hashes, estructura y SQLite.\n    use       Selecciona el proyecto VLF que recibirá la auditoría.\n    list      Lista el contenido interno sin extraerlo.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project status",
        "lanip project list MiRed.vlf"
      ],
      "group": "LANIP",
      "id": "command-lanip-project",
      "kind": "command",
      "launcher": "LANIP",
      "name": "project",
      "path": [
        "LANIP",
        "project"
      ],
      "title": "LANIP project",
      "usage": "LANIP project [-h] ACCIÓN ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Devuelve JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project status [-h] [--json]",
      "details": "Usage: LANIP project status [-h] [--json]\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Devuelve JSON.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project status --help"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-status",
      "kind": "command",
      "launcher": "LANIP",
      "name": "status",
      "path": [
        "LANIP",
        "project",
        "status"
      ],
      "title": "LANIP project status",
      "usage": "LANIP project status [-h] [--json]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Archivo de salida; se añade .vlf si falta.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Nombre humano del proyecto.",
          "flags": [
            "--name"
          ],
          "label": "--name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Descripción general.",
          "flags": [
            "--description"
          ],
          "label": "--description",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "user",
          "description": "Autor del proyecto.",
          "flags": [
            "--author"
          ],
          "label": "--author",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Nombre humano de la LAN.",
          "flags": [
            "--lan-name"
          ],
          "label": "--lan-name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Ubicación física.",
          "flags": [
            "--location"
          ],
          "label": "--location",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Empresa u organización.",
          "flags": [
            "--company"
          ],
          "label": "--company",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Responsable de la LAN.",
          "flags": [
            "--responsible"
          ],
          "label": "--responsible",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "==SUPPRESS==",
          "flags": [
            "--empty"
          ],
          "label": "--empty",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Crea el proyecto copiando explícitamente el inventario y grupos activos.",
          "flags": [
            "--clone-current"
          ],
          "label": "--clone-current",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Sobrescribe un VLF existente.",
          "flags": [
            "--force"
          ],
          "label": "--force",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project create [-h] [--name NAME] [--description DESCRIPTION] [--author AUTHOR]\n                            [--lan-name LAN_NAME] [--location LOCATION] [--company COMPANY]\n                            [--responsible RESPONSIBLE] [--clone-current] [--force]\n                            file",
      "details": "Usage: LANIP project create [-h] [--name NAME] [--description DESCRIPTION] [--author AUTHOR]\n                            [--lan-name LAN_NAME] [--location LOCATION] [--company COMPANY]\n                            [--responsible RESPONSIBLE] [--clone-current] [--force]\n                            file\n\nArguments:\n  file                       Archivo de salida; se añade .vlf si falta.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --name NAME                Nombre humano del proyecto.\n  --description DESCRIPTION  Descripción general.\n  --author AUTHOR            Autor del proyecto.\n  --lan-name LAN_NAME        Nombre humano de la LAN.\n  --location LOCATION        Ubicación física.\n  --company COMPANY          Empresa u organización.\n  --responsible RESPONSIBLE  Responsable de la LAN.\n  --clone-current            Crea el proyecto copiando explícitamente el inventario y grupos\n                             activos.\n  --force                    Sobrescribe un VLF existente.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project create Casa.vlf --name \"Red de casa\""
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-create",
      "kind": "command",
      "launcher": "LANIP",
      "name": "create",
      "path": [
        "LANIP",
        "project",
        "create"
      ],
      "title": "LANIP project create",
      "usage": "LANIP project create [-h] [--name NAME] [--description DESCRIPTION] [--author AUTHOR]\n                            [--lan-name LAN_NAME] [--location LOCATION] [--company COMPANY]\n                            [--responsible RESPONSIBLE] [--clone-current] [--force]\n                            file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Proyecto VLF existente.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project update [-h] file",
      "details": "Usage: LANIP project update [-h] file\n\nArguments:\n  file        Proyecto VLF existente.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project update --help"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-update",
      "kind": "command",
      "launcher": "LANIP",
      "name": "update",
      "path": [
        "LANIP",
        "project",
        "update"
      ],
      "title": "LANIP project update",
      "usage": "LANIP project update [-h] file"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project save [-h]",
      "details": "Usage: LANIP project save [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project save --help"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-save",
      "kind": "command",
      "launcher": "LANIP",
      "name": "save",
      "path": [
        "LANIP",
        "project",
        "save"
      ],
      "title": "LANIP project save",
      "usage": "LANIP project save [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Proyecto VLF.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Devuelve JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project info [-h] [--json] file",
      "details": "Usage: LANIP project info [-h] [--json] file\n\nArguments:\n  file        Proyecto VLF.\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Devuelve JSON.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project info --help"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-info",
      "kind": "command",
      "launcher": "LANIP",
      "name": "info",
      "path": [
        "LANIP",
        "project",
        "info"
      ],
      "title": "LANIP project info",
      "usage": "LANIP project info [-h] [--json] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Proyecto VLF.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Devuelve JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project verify [-h] [--json] file",
      "details": "Usage: LANIP project verify [-h] [--json] file\n\nArguments:\n  file        Proyecto VLF.\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Devuelve JSON.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project verify Casa.vlf"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-verify",
      "kind": "command",
      "launcher": "LANIP",
      "name": "verify",
      "path": [
        "LANIP",
        "project",
        "verify"
      ],
      "title": "LANIP project verify",
      "usage": "LANIP project verify [-h] [--json] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Proyecto VLF existente.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project use [-h] file",
      "details": "Usage: LANIP project use [-h] file\n\nArguments:\n  file        Proyecto VLF existente.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project use --help"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-use",
      "kind": "command",
      "launcher": "LANIP",
      "name": "use",
      "path": [
        "LANIP",
        "project",
        "use"
      ],
      "title": "LANIP project use",
      "usage": "LANIP project use [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Proyecto VLF.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP project list [-h] file",
      "details": "Usage: LANIP project list [-h] file\n\nArguments:\n  file        Proyecto VLF.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project list --help"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-list",
      "kind": "command",
      "launcher": "LANIP",
      "name": "list",
      "path": [
        "LANIP",
        "project",
        "list"
      ],
      "title": "LANIP project list",
      "usage": "LANIP project list [-h] file"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Plugins y expansiones",
      "children": [
        "list",
        "catalog",
        "info",
        "install",
        "enable",
        "disable",
        "reload",
        "uninstall",
        "verify",
        "permissions",
        "revoke",
        "publisher",
        "extensions",
        "pack"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin [-h] ACCIÓN ...",
      "details": "Usage: LANIP plugin [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    list       Lista complementos instalados.\n    catalog    Muestra el catálogo oficial incluido.\n    info       Muestra manifiesto, permisos y estado.\n    install    Verifica e instala un paquete .lcp desactivado.\n    enable     Concede permisos y activa un complemento.\n    disable    Desactiva el complemento.\n    reload     Recarga un complemento activo.\n    uninstall  Desinstala el complemento.\n    verify     Verifica un .lcp o plugin instalado.\n    permissions\n               Muestra permisos solicitados y concedidos.\n    revoke     Revoca permisos y confianza de un complemento.\n    publisher  Gestiona huellas Ed25519 de editores LCP confiables.\n    extensions\n               Lista extensiones para CLI, TUI y futura GUI.\n    pack       Construye un paquete .lcp desde un directorio.\n\nOptions:\n  -h, --help   Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin list",
        "lanip plugin verify extension.lcp"
      ],
      "group": "LANIP",
      "id": "command-lanip-plugin",
      "kind": "command",
      "launcher": "LANIP",
      "name": "plugin",
      "path": [
        "LANIP",
        "plugin"
      ],
      "title": "LANIP plugin",
      "usage": "LANIP plugin [-h] ACCIÓN ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin list [-h]",
      "details": "Usage: LANIP plugin list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin list --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-list",
      "kind": "command",
      "launcher": "LANIP",
      "name": "list",
      "path": [
        "LANIP",
        "plugin",
        "list"
      ],
      "title": "LANIP plugin list",
      "usage": "LANIP plugin list [-h]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin catalog [-h]",
      "details": "Usage: LANIP plugin catalog [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin catalog --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-catalog",
      "kind": "command",
      "launcher": "LANIP",
      "name": "catalog",
      "path": [
        "LANIP",
        "plugin",
        "catalog"
      ],
      "title": "LANIP plugin catalog",
      "usage": "LANIP plugin catalog [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador estable del complemento.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin info [-h] plugin_id",
      "details": "Usage: LANIP plugin info [-h] plugin_id\n\nArguments:\n  plugin_id   Identificador estable del complemento.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin info --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-info",
      "kind": "command",
      "launcher": "LANIP",
      "name": "info",
      "path": [
        "LANIP",
        "plugin",
        "info"
      ],
      "title": "LANIP plugin info",
      "usage": "LANIP plugin info [-h] plugin_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Archivo de paquete con extensión .lcp.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin install [-h] file",
      "details": "Usage: LANIP plugin install [-h] file\n\nArguments:\n  file        Archivo de paquete con extensión .lcp.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin install extension.lcp"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-install",
      "kind": "command",
      "launcher": "LANIP",
      "name": "install",
      "path": [
        "LANIP",
        "plugin",
        "install"
      ],
      "title": "LANIP plugin install",
      "usage": "LANIP plugin install [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador del complemento instalado.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Permisos concretos que se conceden.",
          "flags": [
            "--grant"
          ],
          "label": "--grant",
          "metavar": "PERMISO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Concede todos los permisos solicitados.",
          "flags": [
            "--grant-all"
          ],
          "label": "--grant-all",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Autoriza código trusted dentro del proceso.",
          "flags": [
            "--trust"
          ],
          "label": "--trust",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin enable [-h] [--grant [PERMISO ...]] [--grant-all] [--trust] plugin_id",
      "details": "Usage: LANIP plugin enable [-h] [--grant [PERMISO ...]] [--grant-all] [--trust] plugin_id\n\nArguments:\n  plugin_id              Identificador del complemento instalado.\n\nOptions:\n  -h, --help             Show this help and exit.\n  --grant [PERMISO ...]  Permisos concretos que se conceden.\n  --grant-all            Concede todos los permisos solicitados.\n  --trust                Autoriza código trusted dentro del proceso.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin enable extension-id --grant-all"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-enable",
      "kind": "command",
      "launcher": "LANIP",
      "name": "enable",
      "path": [
        "LANIP",
        "plugin",
        "enable"
      ],
      "title": "LANIP plugin enable",
      "usage": "LANIP plugin enable [-h] [--grant [PERMISO ...]] [--grant-all] [--trust] plugin_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador del complemento instalado.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin disable [-h] plugin_id",
      "details": "Usage: LANIP plugin disable [-h] plugin_id\n\nArguments:\n  plugin_id   Identificador del complemento instalado.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin disable --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-disable",
      "kind": "command",
      "launcher": "LANIP",
      "name": "disable",
      "path": [
        "LANIP",
        "plugin",
        "disable"
      ],
      "title": "LANIP plugin disable",
      "usage": "LANIP plugin disable [-h] plugin_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador del complemento instalado.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin reload [-h] plugin_id",
      "details": "Usage: LANIP plugin reload [-h] plugin_id\n\nArguments:\n  plugin_id   Identificador del complemento instalado.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin reload --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-reload",
      "kind": "command",
      "launcher": "LANIP",
      "name": "reload",
      "path": [
        "LANIP",
        "plugin",
        "reload"
      ],
      "title": "LANIP plugin reload",
      "usage": "LANIP plugin reload [-h] plugin_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador del complemento instalado.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin uninstall [-h] plugin_id",
      "details": "Usage: LANIP plugin uninstall [-h] plugin_id\n\nArguments:\n  plugin_id   Identificador del complemento instalado.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin uninstall --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-uninstall",
      "kind": "command",
      "launcher": "LANIP",
      "name": "uninstall",
      "path": [
        "LANIP",
        "plugin",
        "uninstall"
      ],
      "title": "LANIP plugin uninstall",
      "usage": "LANIP plugin uninstall [-h] plugin_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador instalado o ruta de un archivo .lcp.",
          "flags": [],
          "label": "target",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin verify [-h] target",
      "details": "Usage: LANIP plugin verify [-h] target\n\nArguments:\n  target      Identificador instalado o ruta de un archivo .lcp.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin verify --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-verify",
      "kind": "command",
      "launcher": "LANIP",
      "name": "verify",
      "path": [
        "LANIP",
        "plugin",
        "verify"
      ],
      "title": "LANIP plugin verify",
      "usage": "LANIP plugin verify [-h] target"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador del complemento instalado.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin permissions [-h] plugin_id",
      "details": "Usage: LANIP plugin permissions [-h] plugin_id\n\nArguments:\n  plugin_id   Identificador del complemento instalado.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin permissions --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-permissions",
      "kind": "command",
      "launcher": "LANIP",
      "name": "permissions",
      "path": [
        "LANIP",
        "plugin",
        "permissions"
      ],
      "title": "LANIP plugin permissions",
      "usage": "LANIP plugin permissions [-h] plugin_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador del complemento instalado.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Vacío revoca todos los permisos.",
          "flags": [],
          "label": "permissions",
          "metavar": "PERMISO",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin revoke [-h] plugin_id [PERMISO ...]",
      "details": "Usage: LANIP plugin revoke [-h] plugin_id [PERMISO ...]\n\nArguments:\n  plugin_id   Identificador del complemento instalado.\n  PERMISO     Vacío revoca todos los permisos.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin revoke --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-revoke",
      "kind": "command",
      "launcher": "LANIP",
      "name": "revoke",
      "path": [
        "LANIP",
        "plugin",
        "revoke"
      ],
      "title": "LANIP plugin revoke",
      "usage": "LANIP plugin revoke [-h] plugin_id [PERMISO ...]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Plugins y expansiones",
      "children": [
        "list",
        "trust",
        "revoke"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin publisher [-h] ACCIÓN ...",
      "details": "Usage: LANIP plugin publisher [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    list      Lista editores confiables.\n    trust     Confía en la firma que contiene un paquete LCP.\n    revoke    Revoca una huella de editor.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin publisher --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-publisher",
      "kind": "command",
      "launcher": "LANIP",
      "name": "publisher",
      "path": [
        "LANIP",
        "plugin",
        "publisher"
      ],
      "title": "LANIP plugin publisher",
      "usage": "LANIP plugin publisher [-h] ACCIÓN ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin publisher list [-h]",
      "details": "Usage: LANIP plugin publisher list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin publisher list --help"
      ],
      "group": "LANIP plugin publisher",
      "id": "command-lanip-plugin-publisher-list",
      "kind": "command",
      "launcher": "LANIP",
      "name": "list",
      "path": [
        "LANIP",
        "plugin",
        "publisher",
        "list"
      ],
      "title": "LANIP plugin publisher list",
      "usage": "LANIP plugin publisher list [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Paquete .lcp firmado y verificado.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Nombre descriptivo del editor.",
          "flags": [
            "--name"
          ],
          "label": "--name",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin publisher trust [-h] [--name NAME] file",
      "details": "Usage: LANIP plugin publisher trust [-h] [--name NAME] file\n\nArguments:\n  file         Paquete .lcp firmado y verificado.\n\nOptions:\n  -h, --help   Show this help and exit.\n  --name NAME  Nombre descriptivo del editor.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin publisher trust --help"
      ],
      "group": "LANIP plugin publisher",
      "id": "command-lanip-plugin-publisher-trust",
      "kind": "command",
      "launcher": "LANIP",
      "name": "trust",
      "path": [
        "LANIP",
        "plugin",
        "publisher",
        "trust"
      ],
      "title": "LANIP plugin publisher trust",
      "usage": "LANIP plugin publisher trust [-h] [--name NAME] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Huella SHA-256 Ed25519 completa.",
          "flags": [],
          "label": "fingerprint",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin publisher revoke [-h] fingerprint",
      "details": "Usage: LANIP plugin publisher revoke [-h] fingerprint\n\nArguments:\n  fingerprint  Huella SHA-256 Ed25519 completa.\n\nOptions:\n  -h, --help   Show this help and exit.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin publisher revoke --help"
      ],
      "group": "LANIP plugin publisher",
      "id": "command-lanip-plugin-publisher-revoke",
      "kind": "command",
      "launcher": "LANIP",
      "name": "revoke",
      "path": [
        "LANIP",
        "plugin",
        "publisher",
        "revoke"
      ],
      "title": "LANIP plugin publisher revoke",
      "usage": "LANIP plugin publisher revoke [-h] fingerprint"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Filtra por tipo de extensión unificada.",
          "flags": [
            "--type"
          ],
          "label": "--type",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin extensions [-h] [--type TYPE]",
      "details": "Usage: LANIP plugin extensions [-h] [--type TYPE]\n\nOptions:\n  -h, --help   Show this help and exit.\n  --type TYPE  Filtra por tipo de extensión unificada.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin extensions --help"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-extensions",
      "kind": "command",
      "launcher": "LANIP",
      "name": "extensions",
      "path": [
        "LANIP",
        "plugin",
        "extensions"
      ],
      "title": "LANIP plugin extensions",
      "usage": "LANIP plugin extensions [-h] [--type TYPE]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Directorio fuente que contiene plugin.info.",
          "flags": [],
          "label": "directory",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Archivo .lcp de salida.",
          "flags": [],
          "label": "output",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Sobrescribe el paquete de salida existente.",
          "flags": [
            "--force"
          ],
          "label": "--force",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Clave privada Ed25519 PEM para firmar el LCP.",
          "flags": [
            "--signing-key"
          ],
          "label": "--signing-key",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP plugin pack [-h] [--force] [--signing-key SIGNING_KEY] directory output",
      "details": "Usage: LANIP plugin pack [-h] [--force] [--signing-key SIGNING_KEY] directory output\n\nArguments:\n  directory                  Directorio fuente que contiene plugin.info.\n  output                     Archivo .lcp de salida.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --force                    Sobrescribe el paquete de salida existente.\n  --signing-key SIGNING_KEY  Clave privada Ed25519 PEM para firmar el LCP.",
      "docs": [
        "LCP.md",
        "SECURITY.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip plugin pack mi-plugin extension.lcp"
      ],
      "group": "LANIP plugin",
      "id": "command-lanip-plugin-pack",
      "kind": "command",
      "launcher": "LANIP",
      "name": "pack",
      "path": [
        "LANIP",
        "plugin",
        "pack"
      ],
      "title": "LANIP plugin pack",
      "usage": "LANIP plugin pack [-h] [--force] [--signing-key SIGNING_KEY] directory output"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Configuración",
      "children": [
        "list",
        "use",
        "info",
        "install",
        "validate",
        "export"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP language [-h] ACTION ...",
      "details": "Usage: LANIP language [-h] ACTION ...\n\nArguments:\n  ACTION\n    list      List installed languages.\n    use       Select the interface language.\n    info      Show language metadata and coverage.\n    install   Install or update a .lang JSON catalog.\n    validate  Validate a .lang catalog.\n    export    Export the English template for translation.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip language --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-language",
      "kind": "command",
      "launcher": "LANIP",
      "name": "language",
      "path": [
        "LANIP",
        "language"
      ],
      "title": "LANIP language",
      "usage": "LANIP language [-h] ACTION ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP language list [-h]",
      "details": "Usage: LANIP language list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip language list --help"
      ],
      "group": "LANIP language",
      "id": "command-lanip-language-list",
      "kind": "command",
      "launcher": "LANIP",
      "name": "list",
      "path": [
        "LANIP",
        "language",
        "list"
      ],
      "title": "LANIP language list",
      "usage": "LANIP language list [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Language code or name, for example en or Español.",
          "flags": [],
          "label": "language",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP language use [-h] language",
      "details": "Usage: LANIP language use [-h] language\n\nArguments:\n  language    Language code or name, for example en or Español.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip language use --help"
      ],
      "group": "LANIP language",
      "id": "command-lanip-language-use",
      "kind": "command",
      "launcher": "LANIP",
      "name": "use",
      "path": [
        "LANIP",
        "language",
        "use"
      ],
      "title": "LANIP language use",
      "usage": "LANIP language use [-h] language"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Language code or name; active language by default.",
          "flags": [],
          "label": "language",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP language info [-h] [language]",
      "details": "Usage: LANIP language info [-h] [language]\n\nArguments:\n  language    Language code or name; active language by default.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip language info --help"
      ],
      "group": "LANIP language",
      "id": "command-lanip-language-info",
      "kind": "command",
      "launcher": "LANIP",
      "name": "info",
      "path": [
        "LANIP",
        "language",
        "info"
      ],
      "title": "LANIP language info",
      "usage": "LANIP language info [-h] [language]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Language catalog with .lang extension.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP language install [-h] file",
      "details": "Usage: LANIP language install [-h] file\n\nArguments:\n  file        Language catalog with .lang extension.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip language install --help"
      ],
      "group": "LANIP language",
      "id": "command-lanip-language-install",
      "kind": "command",
      "launcher": "LANIP",
      "name": "install",
      "path": [
        "LANIP",
        "language",
        "install"
      ],
      "title": "LANIP language install",
      "usage": "LANIP language install [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Language catalog with .lang extension.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP language validate [-h] file",
      "details": "Usage: LANIP language validate [-h] file\n\nArguments:\n  file        Language catalog with .lang extension.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip language validate --help"
      ],
      "group": "LANIP language",
      "id": "command-lanip-language-validate",
      "kind": "command",
      "launcher": "LANIP",
      "name": "validate",
      "path": [
        "LANIP",
        "language",
        "validate"
      ],
      "title": "LANIP language validate",
      "usage": "LANIP language validate [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Destination .lang file.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP language export [-h] file",
      "details": "Usage: LANIP language export [-h] file\n\nArguments:\n  file        Destination .lang file.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip language export --help"
      ],
      "group": "LANIP language",
      "id": "command-lanip-language-export",
      "kind": "command",
      "launcher": "LANIP",
      "name": "export",
      "path": [
        "LANIP",
        "language",
        "export"
      ],
      "title": "LANIP language export",
      "usage": "LANIP language export [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador estable del error.",
          "flags": [],
          "label": "error_id",
          "metavar": "0eXXXXXXXX",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Emite el resultado como JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Comandos",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP error [-h] [--json] 0eXXXXXXXX",
      "details": "Usage: LANIP error [-h] [--json] 0eXXXXXXXX\n\nArguments:\n  0eXXXXXXXX  Identificador estable del error.\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Emite el resultado como JSON.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip error --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-error",
      "kind": "command",
      "launcher": "LANIP",
      "name": "error",
      "path": [
        "LANIP",
        "error"
      ],
      "title": "LANIP error",
      "usage": "LANIP error [-h] [--json] 0eXXXXXXXX"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Valida los almacenes configurados.",
          "flags": [
            "--diagnose"
          ],
          "label": "--diagnose",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Exporta datos con hashes verificables.",
          "flags": [
            "--export"
          ],
          "label": "--export",
          "metavar": "ARCHIVO.zip",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Verifica una exportación sin importarla.",
          "flags": [
            "--verify"
          ],
          "label": "--verify",
          "metavar": "ARCHIVO.zip",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Importa datos verificados.",
          "flags": [
            "--import"
          ],
          "label": "--import",
          "metavar": "ARCHIVO.zip",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Restaura un backup validado del almacén.",
          "flags": [
            "--restore"
          ],
          "label": "--restore",
          "metavar": "ARCHIVO.bak",
          "required": false
        },
        {
          "choices": [
            "database",
            "groups",
            "physical"
          ],
          "default": null,
          "description": "Almacén que se restaura.",
          "flags": [
            "--target"
          ],
          "label": "--target",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Confirma la sustitución de datos.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Emite el diagnóstico como JSON.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Datos y exportación",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP database [-h]\n                      (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip | --import ARCHIVO.zip | --restore ARCHIVO.bak)\n                      [--target {database,groups,physical}] [--yes] [--json]",
      "details": "Usage: LANIP database [-h]\n                      (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip | --import ARCHIVO.zip | --restore ARCHIVO.bak)\n                      [--target {database,groups,physical}] [--yes] [--json]\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --diagnose                  Valida los almacenes configurados.\n  --export ARCHIVO.zip        Exporta datos con hashes verificables.\n  --verify ARCHIVO.zip        Verifica una exportación sin importarla.\n  --import ARCHIVO.zip        Importa datos verificados.\n  --restore ARCHIVO.bak       Restaura un backup validado del almacén.\n  --target {database,groups,physical}\n                              Almacén que se restaura.\n  --yes                       Confirma la sustitución de datos.\n  --json                      Emite el diagnóstico como JSON.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip database --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-database",
      "kind": "command",
      "launcher": "LANIP",
      "name": "database",
      "path": [
        "LANIP",
        "database"
      ],
      "title": "LANIP database",
      "usage": "LANIP database [-h]\n                      (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip | --import ARCHIVO.zip | --restore ARCHIVO.bak)\n                      [--target {database,groups,physical}] [--yes] [--json]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": "LANCTL-demo",
          "description": "Directorio donde se guardará el proyecto y el informe.",
          "flags": [
            "--output"
          ],
          "label": "--output",
          "metavar": "DIRECTORIO",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Reemplaza una demo anterior.",
          "flags": [
            "--force"
          ],
          "label": "--force",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "json",
            "html",
            "all"
          ],
          "default": "all",
          "description": "Formato del informe exportado.",
          "flags": [
            "--format"
          ],
          "label": "--format",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Crea inventario, proyecto VLF, evidencias, monitorización y un informe de demostración aislados de los datos del usuario.",
      "details": "Usage: LANIP demo [-h] [--output DIRECTORIO] [--force] [--format {json,html,all}]\n\nCrea inventario, proyecto VLF, evidencias, monitorización y un informe de demostración aislados de los datos del usuario.\n\nOptions:\n  -h, --help                Show this help and exit.\n  --output DIRECTORIO       Directorio donde se guardará el proyecto y el informe.\n  --force                   Reemplaza una demo anterior.\n  --format {json,html,all}  Formato del informe exportado.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip demo --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-demo",
      "kind": "command",
      "launcher": "LANIP",
      "name": "demo",
      "path": [
        "LANIP",
        "demo"
      ],
      "title": "LANIP demo",
      "usage": "LANIP demo [-h] [--output DIRECTORIO] [--force] [--format {json,html,all}]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Abre LANWIRE en una consola independiente incluso si se indican argumentos.",
          "flags": [
            "--new-window"
          ],
          "label": "--new-window",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Muestra la versión común de LANWIRE y termina.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Selecciona una base física IDF alternativa.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "ARCHIVO.db",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la interfaz TUI de LANWIRE.",
          "flags": [
            "-tui",
            "--tui"
          ],
          "label": "-tui, --tui",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la consola interactiva de LANWIRE.",
          "flags": [
            "--cli"
          ],
          "label": "--cli",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Argumentos enviados a LANWIRE, por ejemplo: list.",
          "flags": [],
          "label": "arguments",
          "metavar": "ARGUMENTO",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lanwire [-h] [--new-window] [--version] [--database ARCHIVO.db] [-tui | --cli] ...",
      "details": "Usage: LANIP lanwire [-h] [--new-window] [--version] [--database ARCHIVO.db] [-tui | --cli] ...\n\nArguments:\n  ARGUMENTO              Argumentos enviados a LANWIRE, por ejemplo: list.\n\nOptions:\n  -h, --help             Show this help and exit.\n  --new-window           Abre LANWIRE en una consola independiente incluso si se indican\n                         argumentos.\n  --version              Muestra la versión común de LANWIRE y termina.\n  --database ARCHIVO.db  Selecciona una base física IDF alternativa.\n  -tui, --tui            Abre la interfaz TUI de LANWIRE.\n  --cli                  Abre la consola interactiva de LANWIRE.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lanwire --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-lanwire",
      "kind": "command",
      "launcher": "LANIP",
      "name": "lanwire",
      "path": [
        "LANIP",
        "lanwire"
      ],
      "title": "LANIP lanwire",
      "usage": "LANIP lanwire [-h] [--new-window] [--version] [--database ARCHIVO.db] [-tui | --cli] ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Laboratorio virtual",
      "children": [
        "generate",
        "list",
        "status",
        "stop",
        "start",
        "validate",
        "export",
        "import",
        "network",
        "device",
        "evolve"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab [-h] ACCIÓN ...",
      "details": "Usage: LANIP lab [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    generate  Genera un escenario reproducible.\n    list      Lista escenarios.\n    status    Muestra el escenario activo.\n    stop      Desactiva el proveedor simulado.\n    start     Activa explícitamente un escenario virtual.\n    validate  Valida un escenario.\n    export    Exporta un escenario.\n    import    Importa un escenario JSON.\n    network   Crea manualmente una red virtual.\n    device    Edita dispositivos simulados.\n    evolve    Avanza el reloj y aplica eventos pendientes.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab --help"
      ],
      "group": "LANIP",
      "id": "command-lanip-lab",
      "kind": "command",
      "launcher": "LANIP",
      "name": "lab",
      "path": [
        "LANIP",
        "lab"
      ],
      "title": "LANIP lab",
      "usage": "LANIP lab [-h] ACCIÓN ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": "lab",
          "description": "Nombre del escenario.",
          "flags": [
            "--name"
          ],
          "label": "--name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "192.0.2.0/24",
          "description": "Red IPv4 virtual.",
          "flags": [
            "--cidr"
          ],
          "label": "--cidr",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "home",
            "office",
            "datacenter",
            "industrial",
            "chaotic"
          ],
          "default": "home",
          "description": "Perfil de dispositivos.",
          "flags": [
            "--profile"
          ],
          "label": "--profile",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "20",
          "description": "Cantidad de dispositivos.",
          "flags": [
            "--devices"
          ],
          "label": "--devices",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "1",
          "description": "Semilla reproducible.",
          "flags": [
            "--seed"
          ],
          "label": "--seed",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "80",
          "description": "Porcentaje activo.",
          "flags": [
            "--active-percent"
          ],
          "label": "--active-percent",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "70",
          "description": "Porcentaje DHCP.",
          "flags": [
            "--dhcp-percent"
          ],
          "label": "--dhcp-percent",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "snapshot",
            "timeline",
            "chaos"
          ],
          "default": "snapshot",
          "description": "Evolución del escenario.",
          "flags": [
            "--type"
          ],
          "label": "--type",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab generate [-h] [--name NAME] [--cidr CIDR]\n                          [--profile {home,office,datacenter,industrial,chaotic}]\n                          [--devices DEVICES] [--seed SEED] [--active-percent ACTIVE_PERCENT]\n                          [--dhcp-percent DHCP_PERCENT] [--type {snapshot,timeline,chaos}]",
      "details": "Usage: LANIP lab generate [-h] [--name NAME] [--cidr CIDR]\n                          [--profile {home,office,datacenter,industrial,chaotic}]\n                          [--devices DEVICES] [--seed SEED] [--active-percent ACTIVE_PERCENT]\n                          [--dhcp-percent DHCP_PERCENT] [--type {snapshot,timeline,chaos}]\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --name NAME                 Nombre del escenario.\n  --cidr CIDR                 Red IPv4 virtual.\n  --profile {home,office,datacenter,industrial,chaotic}\n                              Perfil de dispositivos.\n  --devices DEVICES           Cantidad de dispositivos.\n  --seed SEED                 Semilla reproducible.\n  --active-percent ACTIVE_PERCENT\n                              Porcentaje activo.\n  --dhcp-percent DHCP_PERCENT\n                              Porcentaje DHCP.\n  --type {snapshot,timeline,chaos}\n                              Evolución del escenario.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab generate --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-generate",
      "kind": "command",
      "launcher": "LANIP",
      "name": "generate",
      "path": [
        "LANIP",
        "lab",
        "generate"
      ],
      "title": "LANIP lab generate",
      "usage": "LANIP lab generate [-h] [--name NAME] [--cidr CIDR]\n                          [--profile {home,office,datacenter,industrial,chaotic}]\n                          [--devices DEVICES] [--seed SEED] [--active-percent ACTIVE_PERCENT]\n                          [--dhcp-percent DHCP_PERCENT] [--type {snapshot,timeline,chaos}]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab list [-h]",
      "details": "Usage: LANIP lab list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab list --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-list",
      "kind": "command",
      "launcher": "LANIP",
      "name": "list",
      "path": [
        "LANIP",
        "lab",
        "list"
      ],
      "title": "LANIP lab list",
      "usage": "LANIP lab list [-h]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab status [-h]",
      "details": "Usage: LANIP lab status [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab status --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-status",
      "kind": "command",
      "launcher": "LANIP",
      "name": "status",
      "path": [
        "LANIP",
        "lab",
        "status"
      ],
      "title": "LANIP lab status",
      "usage": "LANIP lab status [-h]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab stop [-h]",
      "details": "Usage: LANIP lab stop [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab stop --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-stop",
      "kind": "command",
      "launcher": "LANIP",
      "name": "stop",
      "path": [
        "LANIP",
        "lab",
        "stop"
      ],
      "title": "LANIP lab stop",
      "usage": "LANIP lab stop [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Nombre del escenario.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab start [-h] scenario",
      "details": "Usage: LANIP lab start [-h] scenario\n\nArguments:\n  scenario    Nombre del escenario.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab start --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-start",
      "kind": "command",
      "launcher": "LANIP",
      "name": "start",
      "path": [
        "LANIP",
        "lab",
        "start"
      ],
      "title": "LANIP lab start",
      "usage": "LANIP lab start [-h] scenario"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Nombre del escenario.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab validate [-h] scenario",
      "details": "Usage: LANIP lab validate [-h] scenario\n\nArguments:\n  scenario    Nombre del escenario.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab validate --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-validate",
      "kind": "command",
      "launcher": "LANIP",
      "name": "validate",
      "path": [
        "LANIP",
        "lab",
        "validate"
      ],
      "title": "LANIP lab validate",
      "usage": "LANIP lab validate [-h] scenario"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Nombre del escenario.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "json",
            "csv"
          ],
          "default": "json",
          "description": "Formato de salida.",
          "flags": [
            "--format"
          ],
          "label": "--format",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Archivo de destino; stdout si se omite.",
          "flags": [
            "--output"
          ],
          "label": "--output",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab export [-h] [--format {json,csv}] [--output OUTPUT] scenario",
      "details": "Usage: LANIP lab export [-h] [--format {json,csv}] [--output OUTPUT] scenario\n\nArguments:\n  scenario             Nombre del escenario.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --format {json,csv}  Formato de salida.\n  --output OUTPUT      Archivo de destino; stdout si se omite.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab export --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-export",
      "kind": "command",
      "launcher": "LANIP",
      "name": "export",
      "path": [
        "LANIP",
        "lab",
        "export"
      ],
      "title": "LANIP lab export",
      "usage": "LANIP lab export [-h] [--format {json,csv}] [--output OUTPUT] scenario"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Archivo JSON.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab import [-h] file",
      "details": "Usage: LANIP lab import [-h] file\n\nArguments:\n  file        Archivo JSON.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab import --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-import",
      "kind": "command",
      "launcher": "LANIP",
      "name": "import",
      "path": [
        "LANIP",
        "lab",
        "import"
      ],
      "title": "LANIP lab import",
      "usage": "LANIP lab import [-h] file"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Laboratorio virtual",
      "children": [
        "create"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab network [-h] {create} ...",
      "details": "Usage: LANIP lab network [-h] {create} ...\n\nArguments:\n  {create}\n    create    Crea un escenario vacío.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab network --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-network",
      "kind": "command",
      "launcher": "LANIP",
      "name": "network",
      "path": [
        "LANIP",
        "lab",
        "network"
      ],
      "title": "LANIP lab network",
      "usage": "LANIP lab network [-h] {create} ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Nombre del escenario.",
          "flags": [
            "--name"
          ],
          "label": "--name",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "192.0.2.0/24",
          "description": "CIDR virtual.",
          "flags": [
            "--cidr"
          ],
          "label": "--cidr",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab network create [-h] --name NAME [--cidr CIDR]",
      "details": "Usage: LANIP lab network create [-h] --name NAME [--cidr CIDR]\n\nOptions:\n  -h, --help   Show this help and exit.\n  --name NAME  Nombre del escenario.\n  --cidr CIDR  CIDR virtual.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab network create --help"
      ],
      "group": "LANIP lab network",
      "id": "command-lanip-lab-network-create",
      "kind": "command",
      "launcher": "LANIP",
      "name": "create",
      "path": [
        "LANIP",
        "lab",
        "network",
        "create"
      ],
      "title": "LANIP lab network create",
      "usage": "LANIP lab network create [-h] --name NAME [--cidr CIDR]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Laboratorio virtual",
      "children": [
        "add",
        "delete"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab device [-h] {add,delete} ...",
      "details": "Usage: LANIP lab device [-h] {add,delete} ...\n\nArguments:\n  {add,delete}\n    add         Añade un dispositivo.\n    delete      Elimina un dispositivo.\n\nOptions:\n  -h, --help    Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab device --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-device",
      "kind": "command",
      "launcher": "LANIP",
      "name": "device",
      "path": [
        "LANIP",
        "lab",
        "device"
      ],
      "title": "LANIP lab device",
      "usage": "LANIP lab device [-h] {add,delete} ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Escenario.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "IPv4 simulada.",
          "flags": [
            "--ip"
          ],
          "label": "--ip",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "MAC simulada.",
          "flags": [
            "--mac"
          ],
          "label": "--mac",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Alias.",
          "flags": [
            "--alias"
          ],
          "label": "--alias",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Nombre.",
          "flags": [
            "--name"
          ],
          "label": "--name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Lo crea inactivo.",
          "flags": [
            "--inactive"
          ],
          "label": "--inactive",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab device add [-h] --ip IP --mac MAC [--alias ALIAS] [--name NAME] [--inactive]\n                            scenario",
      "details": "Usage: LANIP lab device add [-h] --ip IP --mac MAC [--alias ALIAS] [--name NAME] [--inactive]\n                            scenario\n\nArguments:\n  scenario       Escenario.\n\nOptions:\n  -h, --help     Show this help and exit.\n  --ip IP        IPv4 simulada.\n  --mac MAC      MAC simulada.\n  --alias ALIAS  Alias.\n  --name NAME    Nombre.\n  --inactive     Lo crea inactivo.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab device add --help"
      ],
      "group": "LANIP lab device",
      "id": "command-lanip-lab-device-add",
      "kind": "command",
      "launcher": "LANIP",
      "name": "add",
      "path": [
        "LANIP",
        "lab",
        "device",
        "add"
      ],
      "title": "LANIP lab device add",
      "usage": "LANIP lab device add [-h] --ip IP --mac MAC [--alias ALIAS] [--name NAME] [--inactive]\n                            scenario"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Escenario.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "ID, IP, MAC o alias.",
          "flags": [],
          "label": "device",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab device delete [-h] scenario device",
      "details": "Usage: LANIP lab device delete [-h] scenario device\n\nArguments:\n  scenario    Escenario.\n  device      ID, IP, MAC o alias.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab device delete --help"
      ],
      "group": "LANIP lab device",
      "id": "command-lanip-lab-device-delete",
      "kind": "command",
      "launcher": "LANIP",
      "name": "delete",
      "path": [
        "LANIP",
        "lab",
        "device",
        "delete"
      ],
      "title": "LANIP lab device delete",
      "usage": "LANIP lab device delete [-h] scenario device"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Segundos virtuales.",
          "flags": [
            "--seconds"
          ],
          "label": "--seconds",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANIP lab evolve [-h] --seconds SECONDS",
      "details": "Usage: LANIP lab evolve [-h] --seconds SECONDS\n\nOptions:\n  -h, --help         Show this help and exit.\n  --seconds SECONDS  Segundos virtuales.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip lab evolve --help"
      ],
      "group": "LANIP lab",
      "id": "command-lanip-lab-evolve",
      "kind": "command",
      "launcher": "LANIP",
      "name": "evolve",
      "path": [
        "LANIP",
        "lab",
        "evolve"
      ],
      "title": "LANIP lab evolve",
      "usage": "LANIP lab evolve [-h] --seconds SECONDS"
    },
    {
      "aliases": [
        "ls",
        "del",
        "map"
      ],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Muestra la versión común de la suite y termina.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/physical/idf.db",
          "description": "Base física IDF; por defecto usa physical/idf.db en la raíz compartida.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "ARCHIVO.db",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la interfaz de pantalla completa.",
          "flags": [
            "-tui",
            "--tui"
          ],
          "label": "-tui, --tui",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la consola interactiva de LANWIRE.",
          "flags": [
            "--cli",
            "-cli"
          ],
          "label": "--cli, -cli",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Launchers",
      "children": [
        "tui",
        "cli",
        "help",
        "list",
        "seed",
        "show",
        "add",
        "idf",
        "reserve",
        "element",
        "delete",
        "graph",
        "prefix"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Gestión física, IDF, cableado y topología de la suite LANCTL.",
      "details": "Usage: LANWIRE [-h] [--version] [--database ARCHIVO.db] [-tui | --cli] COMANDO ...\n\nGestión física, IDF, cableado y topología de la suite LANCTL.\n\nArguments:\n  COMANDO\n    tui                  Abre la interfaz de pantalla completa.\n    cli                  Abre la consola interactiva.\n    help                 Muestra la ayuda de comandos de LANWIRE.\n    list (ls)            Lista los identificadores.\n    seed                 Carga la topología inicial de pruebas.\n    show                 Muestra un identificador.\n    add                  Genera el siguiente IDF.\n    idf                  Crea identificadores con perfil físico completo.\n    reserve              Reserva un IDF.\n    element              Consulta o actualiza los datos y puertos de un elemento.\n    delete (del)         Elimina un IDF.\n    graph (map)          Muestra la topología física.\n    prefix               Gestiona juegos de letras.\n\nOptions:\n  -h, --help             Show this help and exit.\n  --version              Muestra la versión común de la suite y termina.\n  --database ARCHIVO.db  Base física IDF; por defecto usa physical/idf.db en la raíz compartida.\n  -tui, --tui            Abre la interfaz de pantalla completa.\n  --cli, -cli            Abre la consola interactiva de LANWIRE.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire list",
        "lanwire --tui"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire",
      "kind": "launcher",
      "launcher": "LANWIRE",
      "name": "LANWIRE",
      "path": [
        "LANWIRE"
      ],
      "title": "LANWIRE",
      "usage": "LANWIRE [-h] [--version] [--database ARCHIVO.db] [-tui | --cli] COMANDO ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE tui [-h]",
      "details": "Usage: LANWIRE tui [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire tui --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-tui",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "tui",
      "path": [
        "LANWIRE",
        "tui"
      ],
      "title": "LANWIRE tui",
      "usage": "LANWIRE tui [-h]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE cli [-h]",
      "details": "Usage: LANWIRE cli [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire cli --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-cli",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "cli",
      "path": [
        "LANWIRE",
        "cli"
      ],
      "title": "LANWIRE cli",
      "usage": "LANWIRE cli [-h]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE help [-h]",
      "details": "Usage: LANWIRE help [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire help --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-help",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "help",
      "path": [
        "LANWIRE",
        "help"
      ],
      "title": "LANWIRE help",
      "usage": "LANWIRE help [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Filtra por prefijo IDF.",
          "flags": [],
          "label": "prefix",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE list [-h] [prefix]",
      "details": "Usage: LANWIRE list [-h] [prefix]\n\nArguments:\n  prefix      Filtra por prefijo IDF.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire list --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-list",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "list",
      "path": [
        "LANWIRE",
        "list"
      ],
      "title": "LANWIRE list",
      "usage": "LANWIRE list [-h] [prefix]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE seed [-h]",
      "details": "Usage: LANWIRE seed [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire seed --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-seed",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "seed",
      "path": [
        "LANWIRE",
        "seed"
      ],
      "title": "LANWIRE seed",
      "usage": "LANWIRE seed [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador físico que se desea consultar.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE show [-h] idf",
      "details": "Usage: LANWIRE show [-h] idf\n\nArguments:\n  idf         Identificador físico que se desea consultar.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire show --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-show",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "show",
      "path": [
        "LANWIRE",
        "show"
      ],
      "title": "LANWIRE show",
      "usage": "LANWIRE show [-h] idf"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Prefijo del tipo de elemento físico.",
          "flags": [],
          "label": "prefix",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "2",
            "3",
            "4",
            "5"
          ],
          "default": null,
          "description": "Cantidad de dígitos del contador (2 a 5).",
          "flags": [
            "--digits"
          ],
          "label": "--digits",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "1",
          "description": "Crea N IDF consecutivos.",
          "flags": [
            "-more",
            "--more"
          ],
          "label": "-more, --more",
          "metavar": "N",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE add [-h] [--digits {2,3,4,5}] [-more N] prefix",
      "details": "Usage: LANWIRE add [-h] [--digits {2,3,4,5}] [-more N] prefix\n\nArguments:\n  prefix              Prefijo del tipo de elemento físico.\n\nOptions:\n  -h, --help          Show this help and exit.\n  --digits {2,3,4,5}  Cantidad de dígitos del contador (2 a 5).\n  -more N, --more N   Crea N IDF consecutivos.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire add --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-add",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "add",
      "path": [
        "LANWIRE",
        "add"
      ],
      "title": "LANWIRE add",
      "usage": "LANWIRE add [-h] [--digits {2,3,4,5}] [-more N] prefix"
    },
    {
      "aliases": [
        "del"
      ],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [
        "list",
        "types",
        "show",
        "edit",
        "delete",
        "new",
        "add"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf [-h] {list,types,show,edit,delete,del,new,add} ...",
      "details": "Usage: LANWIRE idf [-h] {list,types,show,edit,delete,del,new,add} ...\n\nArguments:\n  {list,types,show,edit,delete,del,new,add}\n    list                      Lista prefijos o los IDF de uno de ellos.\n    types                     Lista los perfiles físicos disponibles.\n    show                      Consulta un prefijo o IDF.\n    edit                      Edita un prefijo o los datos de un IDF.\n    delete (del)              Elimina un IDF.\n    new                       Asigna un perfil físico a un prefijo.\n    add                       Crea un IDF del perfil asignado al prefijo.\n\nOptions:\n  -h, --help                  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-idf",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "idf",
      "path": [
        "LANWIRE",
        "idf"
      ],
      "title": "LANWIRE idf",
      "usage": "LANWIRE idf [-h] {list,types,show,edit,delete,del,new,add} ..."
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Prefijo cuyos elementos se listan.",
          "flags": [],
          "label": "prefix",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf list [-h] [prefix]",
      "details": "Usage: LANWIRE idf list [-h] [prefix]\n\nArguments:\n  prefix      Prefijo cuyos elementos se listan.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf list --help"
      ],
      "group": "LANWIRE idf",
      "id": "command-lanwire-idf-list",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "list",
      "path": [
        "LANWIRE",
        "idf",
        "list"
      ],
      "title": "LANWIRE idf list",
      "usage": "LANWIRE idf list [-h] [prefix]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf types [-h]",
      "details": "Usage: LANWIRE idf types [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf types --help"
      ],
      "group": "LANWIRE idf",
      "id": "command-lanwire-idf-types",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "types",
      "path": [
        "LANWIRE",
        "idf",
        "types"
      ],
      "title": "LANWIRE idf types",
      "usage": "LANWIRE idf types [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Prefijo o IDF concreto.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf show [-h] code",
      "details": "Usage: LANWIRE idf show [-h] code\n\nArguments:\n  code        Prefijo o IDF concreto.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf show --help"
      ],
      "group": "LANWIRE idf",
      "id": "command-lanwire-idf-show",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "show",
      "path": [
        "LANWIRE",
        "idf",
        "show"
      ],
      "title": "LANWIRE idf show",
      "usage": "LANWIRE idf show [-h] code"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Prefijo o IDF concreto.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Datos del IDF.",
          "flags": [],
          "label": "data",
          "metavar": "CAMPO=VALOR",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Nuevo perfil del prefijo.",
          "flags": [
            "-type"
          ],
          "label": "-type",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Nombre del prefijo.",
          "flags": [
            "-name"
          ],
          "label": "-name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Alias del prefijo.",
          "flags": [
            "-alias"
          ],
          "label": "-alias",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Descripción del prefijo.",
          "flags": [
            "-description"
          ],
          "label": "-description",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf edit [-h] [-type ELEMENT_TYPE] [-name NAME] [-alias ALIAS]\n                        [-description DESCRIPTION]\n                        code [CAMPO=VALOR ...]",
      "details": "Usage: LANWIRE idf edit [-h] [-type ELEMENT_TYPE] [-name NAME] [-alias ALIAS]\n                        [-description DESCRIPTION]\n                        code [CAMPO=VALOR ...]\n\nArguments:\n  code                      Prefijo o IDF concreto.\n  CAMPO=VALOR               Datos del IDF.\n\nOptions:\n  -h, --help                Show this help and exit.\n  -type ELEMENT_TYPE        Nuevo perfil del prefijo.\n  -name NAME                Nombre del prefijo.\n  -alias ALIAS              Alias del prefijo.\n  -description DESCRIPTION  Descripción del prefijo.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf edit --help"
      ],
      "group": "LANWIRE idf",
      "id": "command-lanwire-idf-edit",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "edit",
      "path": [
        "LANWIRE",
        "idf",
        "edit"
      ],
      "title": "LANWIRE idf edit",
      "usage": "LANWIRE idf edit [-h] [-type ELEMENT_TYPE] [-name NAME] [-alias ALIAS]\n                        [-description DESCRIPTION]\n                        code [CAMPO=VALOR ...]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IDF concreto; no elimina prefijos.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf delete [-h] code",
      "details": "Usage: LANWIRE idf delete [-h] code\n\nArguments:\n  code        IDF concreto; no elimina prefijos.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf delete --help"
      ],
      "group": "LANWIRE idf",
      "id": "command-lanwire-idf-delete",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "delete",
      "path": [
        "LANWIRE",
        "idf",
        "delete"
      ],
      "title": "LANWIRE idf delete",
      "usage": "LANWIRE idf delete [-h] code"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Prefijo para new o IDF exacto para add.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Nombre del registro.",
          "flags": [
            "-name"
          ],
          "label": "-name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Alias opcional.",
          "flags": [
            "-alias"
          ],
          "label": "-alias",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Descripción opcional.",
          "flags": [
            "-description",
            "-descriptionn"
          ],
          "label": "-description, -descriptionn",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Perfil físico.",
          "flags": [
            "-type"
          ],
          "label": "-type",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf new [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] -type\n                       ELEMENT_TYPE\n                       code",
      "details": "Usage: LANWIRE idf new [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] -type\n                       ELEMENT_TYPE\n                       code\n\nArguments:\n  code                        Prefijo para new o IDF exacto para add.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -name NAME                  Nombre del registro.\n  -alias ALIAS                Alias opcional.\n  -description DESCRIPTION, -descriptionn DESCRIPTION\n                              Descripción opcional.\n  -type ELEMENT_TYPE          Perfil físico.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf new --help"
      ],
      "group": "LANWIRE idf",
      "id": "command-lanwire-idf-new",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "new",
      "path": [
        "LANWIRE",
        "idf",
        "new"
      ],
      "title": "LANWIRE idf new",
      "usage": "LANWIRE idf new [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] -type\n                       ELEMENT_TYPE\n                       code"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Prefijo para new o IDF exacto para add.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Nombre del registro.",
          "flags": [
            "-name"
          ],
          "label": "-name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Alias opcional.",
          "flags": [
            "-alias"
          ],
          "label": "-alias",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "Descripción opcional.",
          "flags": [
            "-description",
            "-descriptionn"
          ],
          "label": "-description, -descriptionn",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE idf add [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] code",
      "details": "Usage: LANWIRE idf add [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] code\n\nArguments:\n  code                        Prefijo para new o IDF exacto para add.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -name NAME                  Nombre del registro.\n  -alias ALIAS                Alias opcional.\n  -description DESCRIPTION, -descriptionn DESCRIPTION\n                              Descripción opcional.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire idf add --help"
      ],
      "group": "LANWIRE idf",
      "id": "command-lanwire-idf-add",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "add",
      "path": [
        "LANWIRE",
        "idf",
        "add"
      ],
      "title": "LANWIRE idf add",
      "usage": "LANWIRE idf add [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] code"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IDF exacto que se desea reservar.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Datos iniciales opcionales.",
          "flags": [],
          "label": "data",
          "metavar": "CLAVE=VALOR",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE reserve [-h] idf [CLAVE=VALOR ...]",
      "details": "Usage: LANWIRE reserve [-h] idf [CLAVE=VALOR ...]\n\nArguments:\n  idf          IDF exacto que se desea reservar.\n  CLAVE=VALOR  Datos iniciales opcionales.\n\nOptions:\n  -h, --help   Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire reserve --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-reserve",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "reserve",
      "path": [
        "LANWIRE",
        "reserve"
      ],
      "title": "LANWIRE reserve",
      "usage": "LANWIRE reserve [-h] idf [CLAVE=VALOR ...]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IDF que se desea consultar o actualizar.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Campos físicos que se desean modificar.",
          "flags": [],
          "label": "data",
          "metavar": "CAMPO=VALOR",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE element [-h] idf [CAMPO=VALOR ...]",
      "details": "Usage: LANWIRE element [-h] idf [CAMPO=VALOR ...]\n\nArguments:\n  idf          IDF que se desea consultar o actualizar.\n  CAMPO=VALOR  Campos físicos que se desean modificar.\n\nOptions:\n  -h, --help   Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire element --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-element",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "element",
      "path": [
        "LANWIRE",
        "element"
      ],
      "title": "LANWIRE element",
      "usage": "LANWIRE element [-h] idf [CAMPO=VALOR ...]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IDF que se desea eliminar.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE delete [-h] idf",
      "details": "Usage: LANWIRE delete [-h] idf\n\nArguments:\n  idf         IDF que se desea eliminar.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire delete --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-delete",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "delete",
      "path": [
        "LANWIRE",
        "delete"
      ],
      "title": "LANWIRE delete",
      "usage": "LANWIRE delete [-h] idf"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE graph [-h]",
      "details": "Usage: LANWIRE graph [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire graph --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-graph",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "graph",
      "path": [
        "LANWIRE",
        "graph"
      ],
      "title": "LANWIRE graph",
      "usage": "LANWIRE graph [-h]"
    },
    {
      "aliases": [
        "ls",
        "del"
      ],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [
        "list",
        "show",
        "set",
        "delete"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE prefix [-h] {list,ls,show,set,delete,del} ...",
      "details": "Usage: LANWIRE prefix [-h] {list,ls,show,set,delete,del} ...\n\nArguments:\n  {list,ls,show,set,delete,del}\n    list (ls)                 Lista las definiciones.\n    show                      Muestra una definición.\n    set                       Crea o actualiza una definición.\n    delete (del)              Elimina una definición.\n\nOptions:\n  -h, --help                  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire prefix --help"
      ],
      "group": "LANWIRE",
      "id": "command-lanwire-prefix",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "prefix",
      "path": [
        "LANWIRE",
        "prefix"
      ],
      "title": "LANWIRE prefix",
      "usage": "LANWIRE prefix [-h] {list,ls,show,set,delete,del} ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE prefix list [-h]",
      "details": "Usage: LANWIRE prefix list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire prefix list --help"
      ],
      "group": "LANWIRE prefix",
      "id": "command-lanwire-prefix-list",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "list",
      "path": [
        "LANWIRE",
        "prefix",
        "list"
      ],
      "title": "LANWIRE prefix list",
      "usage": "LANWIRE prefix list [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Letras del prefijo.",
          "flags": [],
          "label": "letters",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE prefix show [-h] letters",
      "details": "Usage: LANWIRE prefix show [-h] letters\n\nArguments:\n  letters     Letras del prefijo.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire prefix show --help"
      ],
      "group": "LANWIRE prefix",
      "id": "command-lanwire-prefix-show",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "show",
      "path": [
        "LANWIRE",
        "prefix",
        "show"
      ],
      "title": "LANWIRE prefix show",
      "usage": "LANWIRE prefix show [-h] letters"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Letras del prefijo.",
          "flags": [],
          "label": "letters",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Nombre descriptivo del tipo.",
          "flags": [],
          "label": "name",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Descripción opcional.",
          "flags": [],
          "label": "description",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE prefix set [-h] letters name [description]",
      "details": "Usage: LANWIRE prefix set [-h] letters name [description]\n\nArguments:\n  letters      Letras del prefijo.\n  name         Nombre descriptivo del tipo.\n  description  Descripción opcional.\n\nOptions:\n  -h, --help   Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire prefix set --help"
      ],
      "group": "LANWIRE prefix",
      "id": "command-lanwire-prefix-set",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "set",
      "path": [
        "LANWIRE",
        "prefix",
        "set"
      ],
      "title": "LANWIRE prefix set",
      "usage": "LANWIRE prefix set [-h] letters name [description]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Letras del prefijo que se desea eliminar.",
          "flags": [],
          "label": "letters",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANWIRE prefix delete [-h] letters",
      "details": "Usage: LANWIRE prefix delete [-h] letters\n\nArguments:\n  letters     Letras del prefijo que se desea eliminar.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "LANWIRE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanwire prefix delete --help"
      ],
      "group": "LANWIRE prefix",
      "id": "command-lanwire-prefix-delete",
      "kind": "command",
      "launcher": "LANWIRE",
      "name": "delete",
      "path": [
        "LANWIRE",
        "prefix",
        "delete"
      ],
      "title": "LANWIRE prefix delete",
      "usage": "LANWIRE prefix delete [-h] letters"
    },
    {
      "aliases": [
        "ls"
      ],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Muestra la versión común de la suite y termina.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/physical/idf.db",
          "description": "Base física IDF compartida.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "ARCHIVO.db",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la interfaz de pantalla completa.",
          "flags": [
            "-tui",
            "--tui"
          ],
          "label": "-tui, --tui",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la consola interactiva.",
          "flags": [
            "--cli",
            "-cli"
          ],
          "label": "--cli, -cli",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Launchers",
      "children": [
        "list",
        "show"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Visualiza racks y sus equipos.",
      "details": "Usage: LANRACK [-h] [--version] [--database ARCHIVO.db] [-tui | --cli] {list,ls,show} ...\n\nVisualiza racks y sus equipos.\n\nArguments:\n  {list,ls,show}\n    list (ls)            Lista los racks disponibles.\n    show                 Muestra un rack y sus ocupantes.\n\nOptions:\n  -h, --help             Show this help and exit.\n  --version              Muestra la versión común de la suite y termina.\n  --database ARCHIVO.db  Base física IDF compartida.\n  -tui, --tui            Abre la interfaz de pantalla completa.\n  --cli, -cli            Abre la consola interactiva.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanrack list",
        "lanrack --tui"
      ],
      "group": "LANRACK",
      "id": "command-lanrack",
      "kind": "launcher",
      "launcher": "LANRACK",
      "name": "LANRACK",
      "path": [
        "LANRACK"
      ],
      "title": "LANRACK",
      "usage": "LANRACK [-h] [--version] [--database ARCHIVO.db] [-tui | --cli] {list,ls,show} ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANRACK list [-h]",
      "details": "Usage: LANRACK list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanrack list --help"
      ],
      "group": "LANRACK",
      "id": "command-lanrack-list",
      "kind": "command",
      "launcher": "LANRACK",
      "name": "list",
      "path": [
        "LANRACK",
        "list"
      ],
      "title": "LANRACK list",
      "usage": "LANRACK list [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "ID o nombre del rack.",
          "flags": [],
          "label": "rack",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANRACK show [-h] rack",
      "details": "Usage: LANRACK show [-h] rack\n\nArguments:\n  rack        ID o nombre del rack.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanrack show --help"
      ],
      "group": "LANRACK",
      "id": "command-lanrack-show",
      "kind": "command",
      "launcher": "LANRACK",
      "name": "show",
      "path": [
        "LANRACK",
        "show"
      ],
      "title": "LANRACK show",
      "usage": "LANRACK show [-h] rack"
    },
    {
      "aliases": [
        "ls",
        "del"
      ],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Muestra la versión común de la suite y termina.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Base de elementos LANCTL.",
          "flags": [
            "--database"
          ],
          "label": "--database",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/.credentials",
          "description": "Almacén cifrado de credenciales.",
          "flags": [
            "--store"
          ],
          "label": "--store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "auto",
            "dpapi",
            "portable"
          ],
          "default": "auto",
          "description": "Proveedor de cifrado; portable pide contraseña.",
          "flags": [
            "--cipher"
          ],
          "label": "--cipher",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "program",
            "windows",
            "project"
          ],
          "default": "program",
          "description": "Ubicación; no cambia permisos ni copia secretos automáticamente.",
          "flags": [
            "--scope"
          ],
          "label": "--scope",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Directorio del proyecto para su almacén independiente.",
          "flags": [
            "--project-dir"
          ],
          "label": "--project-dir",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la interfaz de pantalla completa.",
          "flags": [
            "-tui",
            "--tui"
          ],
          "label": "-tui, --tui",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la consola interactiva.",
          "flags": [
            "--cli",
            "-cli"
          ],
          "label": "--cli, -cli",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Launchers",
      "children": [
        "list",
        "show",
        "set",
        "delete",
        "credential",
        "doctor",
        "settings",
        "protocol",
        "user"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Gestiona credenciales cifradas del entorno LANCTL.",
      "details": "Usage: LANACCESS [-h] [--version] [--database DATABASE] [--store STORE]\n                 [--cipher {auto,dpapi,portable}] [--scope {program,windows,project}]\n                 [--project-dir PROJECT_DIR] [-tui | --cli]\n                 {list,ls,show,set,delete,del,credential,doctor,settings,protocol,user} ...\n\nGestiona credenciales cifradas del entorno LANCTL.\n\nArguments:\n  {list,ls,show,set,delete,del,credential,doctor,settings,protocol,user}\n    list (ls)                 Lista metadatos; nunca secretos.\n    show                      Muestra metadatos de una credencial.\n    set                       Crea o actualiza una credencial.\n    delete (del)              Elimina una credencial.\n    credential                Gestión, transporte y recuperación de credenciales.\n    doctor                    Comprueba vínculos y permisos sin cambiar datos.\n    settings                  Muestra o selecciona el almacén compartido.\n    protocol                  Resumen por protocolos del almacén.\n    user                      Usuarios del acceso remoto; no cuentas de Windows.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --version                   Muestra la versión común de la suite y termina.\n  --database DATABASE         Base de elementos LANCTL.\n  --store STORE               Almacén cifrado de credenciales.\n  --cipher {auto,dpapi,portable}\n                              Proveedor de cifrado; portable pide contraseña.\n  --scope {program,windows,project}\n                              Ubicación; no cambia permisos ni copia secretos automáticamente.\n  --project-dir PROJECT_DIR   Directorio del proyecto para su almacén independiente.\n  -tui, --tui                 Abre la interfaz de pantalla completa.\n  --cli, -cli                 Abre la consola interactiva.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess list",
        "lanaccess --tui"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess",
      "kind": "launcher",
      "launcher": "LANACCESS",
      "name": "LANACCESS",
      "path": [
        "LANACCESS"
      ],
      "title": "LANACCESS",
      "usage": "LANACCESS [-h] [--version] [--database DATABASE] [--store STORE]\n                 [--cipher {auto,dpapi,portable}] [--scope {program,windows,project}]\n                 [--project-dir PROJECT_DIR] [-tui | --cli]\n                 {list,ls,show,set,delete,del,credential,doctor,settings,protocol,user} ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS list [-h]",
      "details": "Usage: LANACCESS list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess list --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-list",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "list",
      "path": [
        "LANACCESS",
        "list"
      ],
      "title": "LANACCESS list",
      "usage": "LANACCESS list [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador de la credencial.",
          "flags": [],
          "label": "credential_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS show [-h] credential_id",
      "details": "Usage: LANACCESS show [-h] credential_id\n\nArguments:\n  credential_id  Identificador de la credencial.\n\nOptions:\n  -h, --help     Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess show --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-show",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "show",
      "path": [
        "LANACCESS",
        "show"
      ],
      "title": "LANACCESS show",
      "usage": "LANACCESS show [-h] credential_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC, alias o ID del dispositivo.",
          "flags": [],
          "label": "element",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Protocolo asociado, por ejemplo ssh.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Usuario remoto.",
          "flags": [
            "--username",
            "-user"
          ],
          "label": "--username, -user",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS set [-h] --username USERNAME element protocol",
      "details": "Usage: LANACCESS set [-h] --username USERNAME element protocol\n\nArguments:\n  element                     IP, MAC, alias o ID del dispositivo.\n  protocol                    Protocolo asociado, por ejemplo ssh.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --username USERNAME, -user USERNAME\n                              Usuario remoto.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess set --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-set",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "set",
      "path": [
        "LANACCESS",
        "set"
      ],
      "title": "LANACCESS set",
      "usage": "LANACCESS set [-h] --username USERNAME element protocol"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Identificador de la credencial.",
          "flags": [],
          "label": "credential_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS delete [-h] credential_id",
      "details": "Usage: LANACCESS delete [-h] credential_id\n\nArguments:\n  credential_id  Identificador de la credencial.\n\nOptions:\n  -h, --help     Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess delete --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-delete",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "delete",
      "path": [
        "LANACCESS",
        "delete"
      ],
      "title": "LANACCESS delete",
      "usage": "LANACCESS delete [-h] credential_id"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Credenciales y acceso",
      "children": [
        "list",
        "show",
        "delete",
        "set",
        "export",
        "import",
        "copy",
        "recover"
      ],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential [-h] {list,show,delete,set,export,import,copy,recover} ...",
      "details": "Usage: LANACCESS credential [-h] {list,show,delete,set,export,import,copy,recover} ...\n\nArguments:\n  {list,show,delete,set,export,import,copy,recover}\n    list                      Lista metadatos.\n    show                      show por identificador.\n    delete                    delete por identificador.\n    set                       Guarda y vincula una credencial.\n    export                    Transporta un almacén cifrado; nunca texto plano.\n    import                    Transporta un almacén cifrado; nunca texto plano.\n    copy                      Copia a otro almacén y verifica; origen conservado.\n    recover                   Repara referencias ausentes; no elimina ni sobrescribe secretos.\n\nOptions:\n  -h, --help                  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-credential",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "credential",
      "path": [
        "LANACCESS",
        "credential"
      ],
      "title": "LANACCESS credential",
      "usage": "LANACCESS credential [-h] {list,show,delete,set,export,import,copy,recover} ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential list [-h]",
      "details": "Usage: LANACCESS credential list [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential list --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-list",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "list",
      "path": [
        "LANACCESS",
        "credential",
        "list"
      ],
      "title": "LANACCESS credential list",
      "usage": "LANACCESS credential list [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "credential_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential show [-h] credential_id",
      "details": "Usage: LANACCESS credential show [-h] credential_id\n\nArguments:\n  credential_id\n\nOptions:\n  -h, --help     Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential show --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-show",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "show",
      "path": [
        "LANACCESS",
        "credential",
        "show"
      ],
      "title": "LANACCESS credential show",
      "usage": "LANACCESS credential show [-h] credential_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "credential_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential delete [-h] credential_id",
      "details": "Usage: LANACCESS credential delete [-h] credential_id\n\nArguments:\n  credential_id\n\nOptions:\n  -h, --help     Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential delete --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-delete",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "delete",
      "path": [
        "LANACCESS",
        "credential",
        "delete"
      ],
      "title": "LANACCESS credential delete",
      "usage": "LANACCESS credential delete [-h] credential_id"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "element",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [
            "--username"
          ],
          "label": "--username",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential set [-h] --username USERNAME element protocol",
      "details": "Usage: LANACCESS credential set [-h] --username USERNAME element protocol\n\nArguments:\n  element\n  protocol\n\nOptions:\n  -h, --help           Show this help and exit.\n  --username USERNAME",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential set --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-set",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "set",
      "path": [
        "LANACCESS",
        "credential",
        "set"
      ],
      "title": "LANACCESS credential set",
      "usage": "LANACCESS credential set [-h] --username USERNAME element protocol"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential export [-h] file",
      "details": "Usage: LANACCESS credential export [-h] file\n\nArguments:\n  file\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential export --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-export",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "export",
      "path": [
        "LANACCESS",
        "credential",
        "export"
      ],
      "title": "LANACCESS credential export",
      "usage": "LANACCESS credential export [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential import [-h] file",
      "details": "Usage: LANACCESS credential import [-h] file\n\nArguments:\n  file\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential import --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-import",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "import",
      "path": [
        "LANACCESS",
        "credential",
        "import"
      ],
      "title": "LANACCESS credential import",
      "usage": "LANACCESS credential import [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "dpapi",
            "portable"
          ],
          "default": "portable",
          "description": "",
          "flags": [
            "--target-cipher"
          ],
          "label": "--target-cipher",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential copy [-h] [--target-cipher {dpapi,portable}] file",
      "details": "Usage: LANACCESS credential copy [-h] [--target-cipher {dpapi,portable}] file\n\nArguments:\n  file\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --target-cipher {dpapi,portable}",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential copy --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-copy",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "copy",
      "path": [
        "LANACCESS",
        "credential",
        "copy"
      ],
      "title": "LANACCESS credential copy",
      "usage": "LANACCESS credential copy [-h] [--target-cipher {dpapi,portable}] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Aplica reparaciones; por defecto sólo diagnostica.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS credential recover [-h] [--yes]",
      "details": "Usage: LANACCESS credential recover [-h] [--yes]\n\nOptions:\n  -h, --help  Show this help and exit.\n  --yes       Aplica reparaciones; por defecto sólo diagnostica.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess credential recover --help"
      ],
      "group": "LANACCESS credential",
      "id": "command-lanaccess-credential-recover",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "recover",
      "path": [
        "LANACCESS",
        "credential",
        "recover"
      ],
      "title": "LANACCESS credential recover",
      "usage": "LANACCESS credential recover [-h] [--yes]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS doctor [-h]",
      "details": "Usage: LANACCESS doctor [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess doctor --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-doctor",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "doctor",
      "path": [
        "LANACCESS",
        "doctor"
      ],
      "title": "LANACCESS doctor",
      "usage": "LANACCESS doctor [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [
            "show",
            "use-store"
          ],
          "default": "show",
          "description": "",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Confirma cambiar el almacén configurado sin mover secretos.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS settings [-h] [--yes] [{show,use-store}] [file]",
      "details": "Usage: LANACCESS settings [-h] [--yes] [{show,use-store}] [file]\n\nArguments:\n  {show,use-store}\n  file\n\nOptions:\n  -h, --help        Show this help and exit.\n  --yes             Confirma cambiar el almacén configurado sin mover secretos.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess settings --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-settings",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "settings",
      "path": [
        "LANACCESS",
        "settings"
      ],
      "title": "LANACCESS settings",
      "usage": "LANACCESS settings [-h] [--yes] [{show,use-store}] [file]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [
            "list",
            "configure"
          ],
          "default": "list",
          "description": "",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "element",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Puerto 1-65535.",
          "flags": [
            "--port"
          ],
          "label": "--port",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Driver del protocolo.",
          "flags": [
            "--driver"
          ],
          "label": "--driver",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS protocol [-h] [--port PORT] [--driver DRIVER]\n                          [{list,configure}] [element] [protocol]",
      "details": "Usage: LANACCESS protocol [-h] [--port PORT] [--driver DRIVER]\n                          [{list,configure}] [element] [protocol]\n\nArguments:\n  {list,configure}\n  element\n  protocol\n\nOptions:\n  -h, --help        Show this help and exit.\n  --port PORT       Puerto 1-65535.\n  --driver DRIVER   Driver del protocolo.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess protocol --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-protocol",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "protocol",
      "path": [
        "LANACCESS",
        "protocol"
      ],
      "title": "LANACCESS protocol",
      "usage": "LANACCESS protocol [-h] [--port PORT] [--driver DRIVER]\n                          [{list,configure}] [element] [protocol]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [
            "list",
            "add",
            "enable",
            "disable",
            "delete"
          ],
          "default": null,
          "description": "",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "",
          "flags": [],
          "label": "username",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "viewer",
            "operator",
            "manager",
            "administrator"
          ],
          "default": "viewer",
          "description": "",
          "flags": [
            "--role"
          ],
          "label": "--role",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Confirma eliminación.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "usage: LANACCESS user [-h] [--role {viewer,operator,manager,administrator}] [--yes]\n                      {list,add,enable,disable,delete} [username]",
      "details": "Usage: LANACCESS user [-h] [--role {viewer,operator,manager,administrator}] [--yes]\n                      {list,add,enable,disable,delete} [username]\n\nArguments:\n  {list,add,enable,disable,delete}\n  username\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --role {viewer,operator,manager,administrator}\n  --yes                       Confirma eliminación.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess user --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-user",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "user",
      "path": [
        "LANACCESS",
        "user"
      ],
      "title": "LANACCESS user",
      "usage": "LANACCESS user [-h] [--role {viewer,operator,manager,administrator}] [--yes]\n                      {list,add,enable,disable,delete} [username]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Muestra la versión común de la suite y termina.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "logs, events, status, attach, detach, once, session, incidents, service o foreground.",
          "flags": [],
          "label": "words",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--project"
          ],
          "label": "--project",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--permanent"
          ],
          "label": "--permanent",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--duration"
          ],
          "label": "--duration",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "permanent",
            "temporary",
            "diagnostic",
            "once"
          ],
          "default": "temporary",
          "description": "Opción operativa del monitor.",
          "flags": [
            "--mode"
          ],
          "label": "--mode",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "observe",
            "operate",
            "administer"
          ],
          "default": "observe",
          "description": "Opción operativa del monitor.",
          "flags": [
            "--authority"
          ],
          "label": "--authority",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--json"
          ],
          "label": "--json",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--yes"
          ],
          "label": "--yes",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--interval"
          ],
          "label": "--interval",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--every"
          ],
          "label": "--every",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--group"
          ],
          "label": "--group",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "presence",
            "services",
            "ports",
            "identity",
            "smb",
            "full"
          ],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--type"
          ],
          "label": "--type",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--fast"
          ],
          "label": "--fast",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--unknown"
          ],
          "label": "--unknown",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Opción operativa del monitor.",
          "flags": [
            "--follow"
          ],
          "label": "--follow",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/sessions.json",
          "description": "Estado runtime de sesiones.",
          "flags": [
            "--sessions"
          ],
          "label": "--sessions",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/incidents.json",
          "description": "Estado runtime de incidencias.",
          "flags": [
            "--incidents-store"
          ],
          "label": "--incidents-store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/monitor.lock",
          "description": "Lock singleton del monitor.",
          "flags": [
            "--lock"
          ],
          "label": "--lock",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/monitor.db",
          "description": "Repositorio SQLite del monitor.",
          "flags": [
            "--monitor-db"
          ],
          "label": "--monitor-db",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/profiles.json",
          "description": "Perfiles personalizados.",
          "flags": [
            "--profiles"
          ],
          "label": "--profiles",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/monitoring/assignments.json",
          "description": "Asignaciones persistentes.",
          "flags": [
            "--assignments-store"
          ],
          "label": "--assignments-store",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Perfil monitor.",
          "flags": [
            "--profile"
          ],
          "label": "--profile",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "low",
            "normal",
            "high",
            "critical"
          ],
          "default": "normal",
          "description": "Prioridad de asignación.",
          "flags": [
            "--priority"
          ],
          "label": "--priority",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "[]",
          "description": "Check ping, arp o port:NN.",
          "flags": [
            "--check"
          ],
          "label": "--check",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo de presencia.",
          "flags": [
            "--presence"
          ],
          "label": "--presence",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo de descubrimiento.",
          "flags": [
            "--discovery"
          ],
          "label": "--discovery",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo de servicios.",
          "flags": [
            "--services"
          ],
          "label": "--services",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Intervalo profundo.",
          "flags": [
            "--deep"
          ],
          "label": "--deep",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Workers del perfil.",
          "flags": [
            "--workers"
          ],
          "label": "--workers",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Timeout del perfil.",
          "flags": [
            "--timeout"
          ],
          "label": "--timeout",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre la consola de comandos.",
          "flags": [
            "--cli",
            "-cli"
          ],
          "label": "--cli, -cli",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Abre el visor tabular de eventos.",
          "flags": [
            "--tui",
            "-tui"
          ],
          "label": "--tui, -tui",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "all",
            "program",
            "project"
          ],
          "default": "all",
          "description": "Origen para logs.",
          "flags": [
            "--source"
          ],
          "label": "--source",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "100",
          "description": "Máximo de eventos (1-1000).",
          "flags": [
            "--limit"
          ],
          "label": "--limit",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "1",
          "description": "Nivel mínimo (1-59); conserva líneas sin nivel.",
          "flags": [
            "--level"
          ],
          "label": "--level",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Launchers",
      "children": [],
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Monitorización, eventos e incidencias de la suite LANCTL.",
      "details": "Usage: LANMON [-h] [--version] [--project PROJECT] [--permanent] [--duration DURATION]\n              [--mode {permanent,temporary,diagnostic,once}]\n              [--authority {observe,operate,administer}] [--json] [--yes] [--interval INTERVAL]\n              [--every EVERY] [--group GROUP] [--type {presence,services,ports,identity,smb,full}]\n              [--fast] [--unknown] [--follow] [--sessions SESSIONS]\n              [--incidents-store INCIDENTS_STORE] [--lock LOCK] [--monitor-db MONITOR_DB]\n              [--profiles PROFILES] [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n              [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n              [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP] [--workers WORKERS]\n              [--timeout TIMEOUT] [--cli | --tui] [--source {all,program,project}] [--limit LIMIT]\n              [--level LEVEL]\n              [words ...]\n\nMonitorización, eventos e incidencias de la suite LANCTL.\n\nArguments:\n  words                       logs, events, status, attach, detach, once, session, incidents,\n                              service o foreground.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --version                   Muestra la versión común de la suite y termina.\n  --project PROJECT           Opción operativa del monitor.\n  --permanent                 Opción operativa del monitor.\n  --duration DURATION         Opción operativa del monitor.\n  --mode {permanent,temporary,diagnostic,once}\n                              Opción operativa del monitor.\n  --authority {observe,operate,administer}\n                              Opción operativa del monitor.\n  --json                      Opción operativa del monitor.\n  --yes                       Opción operativa del monitor.\n  --interval INTERVAL         Opción operativa del monitor.\n  --every EVERY               Opción operativa del monitor.\n  --group GROUP               Opción operativa del monitor.\n  --type {presence,services,ports,identity,smb,full}\n                              Opción operativa del monitor.\n  --fast                      Opción operativa del monitor.\n  --unknown                   Opción operativa del monitor.\n  --follow                    Opción operativa del monitor.\n  --sessions SESSIONS         Estado runtime de sesiones.\n  --incidents-store INCIDENTS_STORE\n                              Estado runtime de incidencias.\n  --lock LOCK                 Lock singleton del monitor.\n  --monitor-db MONITOR_DB     Repositorio SQLite del monitor.\n  --profiles PROFILES         Perfiles personalizados.\n  --assignments-store ASSIGNMENTS_STORE\n                              Asignaciones persistentes.\n  --profile PROFILE           Perfil monitor.\n  --priority {low,normal,high,critical}\n                              Prioridad de asignación.\n  --check CHECK               Check ping, arp o port:NN.\n  --presence PRESENCE         Intervalo de presencia.\n  --discovery DISCOVERY       Intervalo de descubrimiento.\n  --services SERVICES         Intervalo de servicios.\n  --deep DEEP                 Intervalo profundo.\n  --workers WORKERS           Workers del perfil.\n  --timeout TIMEOUT           Timeout del perfil.\n  --cli, -cli                 Abre la consola de comandos.\n  --tui, -tui                 Abre el visor tabular de eventos.\n  --source {all,program,project}\n                              Origen para logs.\n  --limit LIMIT               Máximo de eventos (1-1000).\n  --level LEVEL               Nivel mínimo (1-59); conserva líneas sin nivel.",
      "docs": [
        "MONITOR.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanmon status",
        "lanmon --help"
      ],
      "group": "LANMON",
      "id": "command-lanmon",
      "kind": "launcher",
      "launcher": "LANMON",
      "name": "LANMON",
      "path": [
        "LANMON"
      ],
      "title": "LANMON",
      "usage": "LANMON [-h] [--version] [--project PROJECT] [--permanent] [--duration DURATION]\n              [--mode {permanent,temporary,diagnostic,once}]\n              [--authority {observe,operate,administer}] [--json] [--yes] [--interval INTERVAL]\n              [--every EVERY] [--group GROUP] [--type {presence,services,ports,identity,smb,full}]\n              [--fast] [--unknown] [--follow] [--sessions SESSIONS]\n              [--incidents-store INCIDENTS_STORE] [--lock LOCK] [--monitor-db MONITOR_DB]\n              [--profiles PROFILES] [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n              [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n              [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP] [--workers WORKERS]\n              [--timeout TIMEOUT] [--cli | --tui] [--source {all,program,project}] [--limit LIMIT]\n              [--level LEVEL]\n              [words ...]"
    },
    {
      "category": "Proyectos",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Contenedor portable de inventario, configuración, auditoría y hashes.",
      "details": "Los proyectos .vlf permiten guardar, verificar, clonar y trasladar un entorno LANCTL completo.",
      "docs": [
        "VLF.md",
        "STORAGE.md"
      ],
      "examples": [
        "lanip project create Casa.vlf --name \"Red de casa\"",
        "lanip project verify Casa.vlf"
      ],
      "group": "Formato de proyecto",
      "id": "concept-project-vlf",
      "kind": "concept",
      "name": "Proyecto VLF"
    },
    {
      "category": "Plugins y expansiones",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Paquete verificable de extensión con manifiesto, permisos y runtimes controlados.",
      "details": "Los paquetes .lcp se validan antes de instalarse y permanecen desactivados hasta conceder sus permisos.",
      "docs": [
        "LCP.md",
        "SECURITY.md"
      ],
      "examples": [
        "lanip plugin install extension.lcp",
        "lanip plugin permissions extension-id"
      ],
      "group": "Formato de extensión",
      "id": "concept-plugin-lcp",
      "kind": "concept",
      "name": "Plugin LCP"
    },
    {
      "category": "Grupos de comandos",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Árboles de subcomandos que agrupan acciones relacionadas bajo una raíz común.",
      "details": "Usa --help en cualquier nivel para consultar sus acciones, argumentos y opciones disponibles.",
      "docs": [
        "CLI.md",
        "CLI-REFERENCE.md"
      ],
      "examples": [
        "lanip project --help",
        "lanip plugin publisher --help"
      ],
      "group": "Organización del CLI",
      "id": "concept-command-groups",
      "kind": "concept",
      "name": "Grupos de comandos"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "CLI directa, consola interactiva `lanaccess --cli` y TUI `lanaccess --tui` comparten servicios. En el TUI, N/B cambia de página, A crea, E elimina, D diagnostica y C permite ejecutar los mismos comandos sin salir. Los controles se confirman con Intro; no son todavía modales como LANIP.",
      "details": "Documento mantenido en docs/ACCESS-MONITOR-MANAGEMENT.md.",
      "docs": [
        "ACCESS-MONITOR-MANAGEMENT.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-access-monitor-management",
      "kind": "document",
      "name": "ACCESS-MONITOR-MANAGEMENT.md",
      "title": "LANACCESS y LANMON: administración separada",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/ACCESS-MONITOR-MANAGEMENT.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Para nodos permanentes, políticas de mínimo privilegio, PKI, actualización y recuperación, consulta la [guía de despliegue empresarial](ENTERPRISE.md).",
      "details": "Documento mantenido en docs/ACCESS.md.",
      "docs": [
        "ACCESS.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-access",
      "kind": "document",
      "name": "ACCESS.md",
      "title": "Acceso remoto LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/ACCESS.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "`LANCTL` es el orquestador común. Permite abrir las aplicaciones con `lanctl ip`, `lanctl wire`, `lanctl rack` y `lanctl access`; los ejecutables independientes usan los mismos datos y la misma versión de la suite.",
      "details": "Documento mantenido en docs/APPLICATIONS.md.",
      "docs": [
        "APPLICATIONS.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-applications",
      "kind": "document",
      "name": "APPLICATIONS.md",
      "title": "Aplicaciones paralelas de LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/APPLICATIONS.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Lista de asuntos acordados para revisar en una sesión futura. Este documento no indica que las tareas estén implementadas.",
      "details": "Documento mantenido en docs/BACKLOG.md.",
      "docs": [
        "BACKLOG.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-backlog",
      "kind": "document",
      "name": "BACKLOG.md",
      "title": "Trabajo pendiente de LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/BACKLOG.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANCTL se distribuye como beta técnica. Utilízalo únicamente en redes propias o donde tengas autorización y conserva una copia independiente de los proyectos `.vlf`. No uses todavía LANCTL como única fuente del inventario de una red.",
      "details": "Documento mantenido en docs/BETA-TESTING.md.",
      "docs": [
        "BETA-TESTING.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-beta-testing",
      "kind": "document",
      "name": "BETA-TESTING.md",
      "title": "Guía para beta testers",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/BETA-TESTING.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "`CiscoPlanner` no conoce SSH ni Netmiko. `CommandPlan` contiene la identidad estable ALS, endpoint actual, puerto lógico y nativo, riesgo y comandos que un adaptador podría ejecutar. `FakeCiscoAdapter` es el único adaptador habilitado en esta fase.",
      "details": "Documento mantenido en docs/cisco-command-layer.md.",
      "docs": [
        "cisco-command-layer.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-cisco-command-layer",
      "kind": "document",
      "name": "cisco-command-layer.md",
      "title": "Capa gestionada de comandos Cisco",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/cisco-command-layer.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Documento generado automáticamente desde los parsers de la aplicación. No lo edites manualmente; ejecuta `python tools/generate_cli_reference.py`.",
      "details": "Documento mantenido en docs/CLI-REFERENCE.md.",
      "docs": [
        "CLI-REFERENCE.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-cli-reference",
      "kind": "document",
      "name": "CLI-REFERENCE.md",
      "title": "Referencia completa del CLI LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/CLI-REFERENCE.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Todos los comandos admiten `-h`, `--help` y `/?`. `list` y `recurrent` ofrecen `table`, `json`, `csv`, `html`, `xml` y `yaml`. Usa `--output` para escritura atómica a archivo.",
      "details": "Documento mantenido en docs/CLI.md.",
      "docs": [
        "CLI.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-cli",
      "kind": "document",
      "name": "CLI.md",
      "title": "Referencia operativa del CLI",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/CLI.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANCTL conserva una única configuración JSON con esquema versionado. Desde el esquema 2, las opciones se agrupan por responsabilidad en vez de compartir un espacio plano de claves.",
      "details": "Documento mantenido en docs/CONFIGURATION.md.",
      "docs": [
        "CONFIGURATION.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-configuration",
      "kind": "document",
      "name": "CONFIGURATION.md",
      "title": "Configuración de LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/CONFIGURATION.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Estas reglas son el contrato de trabajo del repositorio. Se aplican a código, documentación, plugins, automatizaciones, empaquetado y publicaciones.",
      "details": "Documento mantenido en docs/DEVELOPMENT-RULES.md.",
      "docs": [
        "DEVELOPMENT-RULES.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-development-rules",
      "kind": "document",
      "name": "DEVELOPMENT-RULES.md",
      "title": "Reglas de desarrollo, ramas y distribución",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/DEVELOPMENT-RULES.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Estas herramientas ayudan a revisar LANCTL, pero no forman parte del programa ni de sus instaladores. Se instalan fuera del repositorio. Sus configuraciones reproducibles y documentos de arquitectura sí se versionan.",
      "details": "Documento mantenido en docs/DEVELOPMENT-TOOLS.md.",
      "docs": [
        "DEVELOPMENT-TOOLS.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-development-tools",
      "kind": "document",
      "name": "DEVELOPMENT-TOOLS.md",
      "title": "Herramientas auxiliares de desarrollo",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/DEVELOPMENT-TOOLS.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Esta guía describe un nodo LANCTL administrado dentro de una LAN confiable. SSH y HTTPS permanecen desactivados hasta completar la configuración y no se publican directamente en Internet.",
      "details": "Documento mantenido en docs/ENTERPRISE.md.",
      "docs": [
        "ENTERPRISE.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-enterprise",
      "kind": "document",
      "name": "ENTERPRISE.md",
      "title": "Despliegue empresarial de acceso remoto",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/ENTERPRISE.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANCTL representa los fallos nuevos mediante `ErrorEvent`, con nivel, origen jerárquico, código estable, mensaje, recuperabilidad, contexto redactado y un identificador de correlación. `ErrorManager.emit()` permite decidir de forma independiente si el error se muestra (`print_output`) y si interrumpe la tarea (`break_execution`). Los errores que interrumpen se muestran mediante su `repr`, útil para soporte y diagnóstico.",
      "details": "Documento mantenido en docs/ERRORS.md.",
      "docs": [
        "ERRORS.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-errors",
      "kind": "document",
      "name": "ERRORS.md",
      "title": "Errores estructurados",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/ERRORS.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Este subsistema está destinado a la futura interfaz gráfica. No registra comandos en CLI ni TUI.",
      "details": "Documento mantenido en docs/ICONS.md.",
      "docs": [
        "ICONS.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-icons",
      "kind": "document",
      "name": "ICONS.md",
      "title": "Catálogo de iconos de LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/ICONS.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "GitHub Releases es el canal de distribución binaria de LANCTL. Los scripts de instalación no compilan código: seleccionan un artefacto exacto para la versión, SO y arquitectura, descargan `SHA256SUMS.txt` y fallan antes de instalar si la verificación no coincide.",
      "details": "Documento mantenido en docs/INSTALL.md.",
      "docs": [
        "INSTALL.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-install",
      "kind": "document",
      "name": "INSTALL.md",
      "title": "Instalación y actualización",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/INSTALL.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Las limitaciones resueltas deben retirarse de esta lista en la misma revisión que incorpore y pruebe la corrección.",
      "details": "Documento mantenido en docs/KNOWN-ISSUES.md.",
      "docs": [
        "KNOWN-ISSUES.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-known-issues",
      "kind": "document",
      "name": "KNOWN-ISSUES.md",
      "title": "Limitaciones conocidas de la beta",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/KNOWN-ISSUES.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANCTL utiliza catálogos JSON con extensión `.lang`. Las claves son contratos estables, por ejemplo `LANCTL.CORE.APP.CANCELLED`, y no el texto original.",
      "details": "Documento mantenido en docs/LANG.md.",
      "docs": [
        "LANG.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-lang",
      "kind": "document",
      "name": "LANG.md",
      "title": "Idiomas de LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LANG.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANLAB permite probar inventario, filtros, historial y presentación de LANIP sin depender de una LAN física. Su proveedor implementa el contrato común `DiscoveryProvider` y devuelve `DiscoveryResult` con `source=simulated`, proveedor, escenario y semilla.",
      "details": "Documento mantenido en docs/LANLAB.md.",
      "docs": [
        "LANLAB.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-lanlab",
      "kind": "document",
      "name": "LANLAB.md",
      "title": "LANLAB Network Emulator",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LANLAB.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANWIRE es el gestor de infraestructura física complementario de LANCTL. En Windows se distribuye como `lanwire.exe` en el mismo directorio que `LANCTL.exe`. La GUI heredada no forma parte de la distribución.",
      "details": "Documento mantenido en docs/LANWIRE.md.",
      "docs": [
        "LANWIRE.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-lanwire",
      "kind": "document",
      "name": "LANWIRE.md",
      "title": "Integración LANWIRE",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LANWIRE.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Todos los launchers admiten `--cli` (también `-cli`) y `--tui` (también `-tui`). Los comandos directos y `/?` siguen disponibles. No cambia el formato de los proyectos, credenciales ni contratos de plugins.",
      "details": "Documento mantenido en docs/LAUNCHER-INTERFACES.md.",
      "docs": [
        "LAUNCHER-INTERFACES.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-launcher-interfaces",
      "kind": "document",
      "name": "LAUNCHER-INTERFACES.md",
      "title": "Interfaces de los launchers",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LAUNCHER-INTERFACES.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANCTL utiliza `.lcp` como contenedor ZIP seguro para todos sus complementos. Un mismo paquete puede aportar capacidades `plugin`, `theme`, `language`, `settings`, `automation`, `network`, `analysis`, `ui`, `security`, `protocol`, `scanner`, `parser`, `exporter`, `project-handler` o `project-save-mode`. CLI, TUI y la futura GUI consumen el mismo registro de extensiones.",
      "details": "Documento mantenido en docs/LCP.md.",
      "docs": [
        "LCP.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-lcp",
      "kind": "document",
      "name": "LCP.md",
      "title": "LANCTL Complement Platform (LCP) 1.0",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LCP.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "La GUI se conserva únicamente como referencia mientras el desarrollo se centra en CLI y TUI. No recibe nuevas funciones, no participa en la batería ordinaria de pruebas y no se incluye en los ejecutables, el ZIP portable, el instalador ni los accesos directos de Windows.",
      "details": "Documento mantenido en docs/LEGACY-GUI.md.",
      "docs": [
        "LEGACY-GUI.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-legacy-gui",
      "kind": "document",
      "name": "LEGACY-GUI.md",
      "title": "GUI heredada congelada",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LEGACY-GUI.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "El backend separa el motor de ejecución de la configuración y los datos. `MonitorService` consume `ConfigProvider`, `AssignmentProvider`, `MetricsStore`, `SessionRepository`, `IncidentRepository` y `ReportBuilder`. Las implementaciones persistentes usan SQLite con WAL, timeout de bloqueo, transacciones e índices por dispositivo y tiempo.",
      "details": "Documento mantenido en docs/MONITOR.md.",
      "docs": [
        "MONITOR.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-monitor",
      "kind": "document",
      "name": "MONITOR.md",
      "title": "Monitorización LAN",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/MONITOR.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "La demostración aislada no modifica el inventario normal ni envía paquetes a la red. Genera un proyecto VLF verificable y dos informes:",
      "details": "Documento mantenido en docs/PRESENTATION.md.",
      "docs": [
        "PRESENTATION.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-presentation",
      "kind": "document",
      "name": "PRESENTATION.md",
      "title": "Recorrido de presentación de LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/PRESENTATION.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Fecha: 2026-08-01",
      "details": "Documento mantenido en docs/RELEASE-0.3.0-beta.1.md.",
      "docs": [
        "RELEASE-0.3.0-beta.1.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-0-beta-1",
      "kind": "document",
      "name": "RELEASE-0.3.0-beta.1.md",
      "title": "Verificación de LANCTL 0.3.0-beta.1",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.0-beta.1.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Versión beta para evaluación en Windows x64. Incluye ejecutables autocontenidos: no requiere una instalación de Python en el equipo de destino.",
      "details": "Documento mantenido en docs/RELEASE-0.3.0-beta.20.md.",
      "docs": [
        "RELEASE-0.3.0-beta.20.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-0-beta-20",
      "kind": "document",
      "name": "RELEASE-0.3.0-beta.20.md",
      "title": "LANCTL 0.3.0-beta.20",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.0-beta.20.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Beta técnica dirigida a evaluación controlada. Los launchers son autocontenidos y no requieren que Python esté instalado en el equipo destino.",
      "details": "Documento mantenido en docs/RELEASE-0.3.0-beta.22.md.",
      "docs": [
        "RELEASE-0.3.0-beta.22.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-0-beta-22",
      "kind": "document",
      "name": "RELEASE-0.3.0-beta.22.md",
      "title": "LANCTL 0.3.0-beta.22",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.0-beta.22.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Beta técnica dirigida a evaluación controlada. Los launchers son autocontenidos y no requieren que Python esté instalado en el equipo destino.",
      "details": "Documento mantenido en docs/RELEASE-0.3.1-beta.1.md.",
      "docs": [
        "RELEASE-0.3.1-beta.1.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-1-beta-1",
      "kind": "document",
      "name": "RELEASE-0.3.1-beta.1.md",
      "title": "LANCTL 0.3.1-beta.1",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.1-beta.1.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Beta técnica en desarrollo sobre la rama `main`. La versión estable anterior permanece congelada en `stable/0.3.1-beta.1`, en el tag `v0.3.1-beta.1` y en su GitHub Release con los instaladores originales.",
      "details": "Documento mantenido en docs/RELEASE-0.3.1-beta.2.md.",
      "docs": [
        "RELEASE-0.3.1-beta.2.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-1-beta-2",
      "kind": "document",
      "name": "RELEASE-0.3.1-beta.2.md",
      "title": "LANCTL 0.3.1-beta.2",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.1-beta.2.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Versión de prueba publicada desde `main` como **pre-release**. Puede contener funciones todavía no sometidas a un ciclo completo de validación. La versión conservada como estable sigue siendo `0.3.1-beta.1` en la rama `stable/0.3.1-beta.1`, su tag y su GitHub Release.",
      "details": "Documento mantenido en docs/RELEASE-0.3.1-beta.3.md.",
      "docs": [
        "RELEASE-0.3.1-beta.3.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-1-beta-3",
      "kind": "document",
      "name": "RELEASE-0.3.1-beta.3.md",
      "title": "LANCTL 0.3.1-beta.3",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.1-beta.3.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Beta de desarrollo integrada en `main`; no es una versión estable.",
      "details": "Documento mantenido en docs/RELEASE-0.3.2-beta.1.md.",
      "docs": [
        "RELEASE-0.3.2-beta.1.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-2-beta-1",
      "kind": "document",
      "name": "RELEASE-0.3.2-beta.1.md",
      "title": "LANCTL 0.3.2-beta.1",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.2-beta.1.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Publicación solicitada en el canal estable, conservando el sufijo beta por decisión del propietario. La etiqueta de canal no implica ausencia de defectos.",
      "details": "Documento mantenido en docs/RELEASE-0.3.2-beta.4.md.",
      "docs": [
        "RELEASE-0.3.2-beta.4.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-2-beta-4",
      "kind": "document",
      "name": "RELEASE-0.3.2-beta.4.md",
      "title": "LANCTL 0.3.2-beta.4",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.2-beta.4.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANWIRE añade perfiles de prefijos, creación explícita de IDF, identificadores de 2–5 letras/dígitos, plantillas mixtas de puertos, compatibilidad de medios, vista de topología, navegación entre cables/equipos y edición desde el TUI. La persistencia actualiza referencias al renombrar puertos y limpia conexiones al eliminar elementos, con escrituras transaccionales. La inicialización de LANWIRE puede clasificar registros antiguos FB/WL/WE: conviene respaldar bases reales antes de abrirlas con esta versión.",
      "details": "Documento mantenido en docs/REVIEW-EXPERIMENTAL-2026-09-25.md.",
      "docs": [
        "REVIEW-EXPERIMENTAL-2026-09-25.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-review-experimental-2026-09-25",
      "kind": "document",
      "name": "REVIEW-EXPERIMENTAL-2026-09-25.md",
      "title": "Integración de experimental — 2026-09-25",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/REVIEW-EXPERIMENTAL-2026-09-25.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Las comprobaciones de cada cambio a `main` incluyen pruebas de integración y cobertura de ramas, Ruff, Bandit, `pip check`, `pip-audit`, CodeQL y revisión de dependencias. Dependabot revisa semanalmente paquetes Python y GitHub Actions. Los workflows usan permisos mínimos y la publicación solo obtiene `contents: write` dentro del trabajo que crea una release desde un tag.",
      "details": "Documento mantenido en docs/SECURITY.md.",
      "docs": [
        "SECURITY.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-security",
      "kind": "document",
      "name": "SECURITY.md",
      "title": "Seguridad del proyecto",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/SECURITY.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Estado: preparación local; no declarada estable, sin publicación ni actualización de la instalación. Versión mantenida: 0.3.2-beta.1.",
      "details": "Documento mantenido en docs/STABILITY-REVIEW-2026-09-26.md.",
      "docs": [
        "STABILITY-REVIEW-2026-09-26.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-stability-review-2026-09-26",
      "kind": "document",
      "name": "STABILITY-REVIEW-2026-09-26.md",
      "title": "Revisión de estabilidad — 2026-09-26",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/STABILITY-REVIEW-2026-09-26.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "LANCTL separa programa, datos de usuario/servicio y proyectos. En una instalación Windows estándar, el programa reside en `Program Files` y los datos mutables en `C:\\ProgramData\\LANCTL`. Los secretos usan el ámbito de usuario o servicio configurado. Los proyectos VLF solo cambian cuando se seleccionan de forma explícita.",
      "details": "Documento mantenido en docs/STORAGE.md.",
      "docs": [
        "STORAGE.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-storage",
      "kind": "document",
      "name": "STORAGE.md",
      "title": "Persistencia, concurrencia y recuperación",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/STORAGE.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "1. Ejecuta `lanctl database --diagnose` y conserva la salida. 2. Consulta un identificador mostrado con `lanctl error 0eXXXXXXXX`. 3. Revisa `logs/` sin publicar credenciales ni la carpeta `access/`. 4. Si falla un plugin, inicia con `pluginSafeMode: true`, revoca permisos o desactívalo. 5. Verifica un LCP con `lanctl plugin verify ARCHIVO.lcp` antes de instalarlo. 6. Verifica una copia de datos con `lanctl database --verify ARCHIVO.zip`.",
      "details": "Documento mantenido en docs/TROUBLESHOOTING.md.",
      "docs": [
        "TROUBLESHOOTING.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-troubleshooting",
      "kind": "document",
      "name": "TROUBLESHOOTING.md",
      "title": "Recuperación y solución de problemas",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/TROUBLESHOOTING.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Inicia la interfaz con `lanctl --tui`. También puede abrir directamente `PLUGINS`, `PROJECTS` o `SETTINGS`. La pantalla se adapta automáticamente a terminales estrechas; se recomienda un mínimo de 80×24 para la demostración.",
      "details": "Documento mantenido en docs/TUI.md.",
      "docs": [
        "TUI.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-tui",
      "kind": "document",
      "name": "TUI.md",
      "title": "Manual del TUI",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/TUI.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "description": "Un archivo `.vlf` es un contenedor ZIP con nombres internos POSIX y una estructura fija. No debe confundirse la compresión ZIP con cifrado.",
      "details": "Documento mantenido en docs/VLF.md.",
      "docs": [
        "VLF.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-vlf",
      "kind": "document",
      "name": "VLF.md",
      "title": "LANCTL VLF 1.0",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/VLF.md"
    }
  ],
  "meta": {
    "entryCount": 170,
    "name": "LANCTL Reference",
    "repository": "https://github.com/CctrGy/LANCTL",
    "version": "0.3.2-beta.4"
  },
  "workflows": [
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "VLF.md",
        "STORAGE.md"
      ],
      "id": "workflow-project-create-save",
      "level": "Inicial",
      "related": [
        "command-lanip-project-create",
        "command-lanip-project-save",
        "command-lanip-project-verify"
      ],
      "steps": [
        {
          "commands": [
            "lanip settings --projects-directory D:\\ProyectosLANCTL"
          ],
          "description": "Opcionalmente define dónde se guardarán los proyectos.",
          "title": "Elegir el directorio"
        },
        {
          "commands": [
            "lanip project create Casa.vlf --name \"Red de casa\""
          ],
          "description": "Crea un VLF vacío con un nombre reconocible.",
          "title": "Crear el proyecto"
        },
        {
          "commands": [
            "lanip project use Casa.vlf",
            "lanip project status"
          ],
          "description": "Selecciona el proyecto como destino del inventario y la auditoría.",
          "title": "Activarlo"
        },
        {
          "commands": [
            "lanip list --normal",
            "lanip list --active"
          ],
          "description": "Escanea la LAN y revisa los dispositivos antes de guardar.",
          "title": "Descubrir e inventariar"
        },
        {
          "commands": [
            "lanip project save",
            "lanip project verify Casa.vlf"
          ],
          "description": "Persiste los cambios y comprueba estructura, hashes y SQLite.",
          "title": "Guardar y verificar"
        }
      ],
      "summary": "Prepara un proyecto aislado, añade el inventario y verifica el archivo antes de compartirlo.",
      "time": "5-10 min",
      "title": "Crear y guardar un proyecto VLF"
    },
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "LCP.md",
        "SECURITY.md"
      ],
      "id": "workflow-plugin-import",
      "level": "Intermedio",
      "related": [
        "command-lanip-plugin-verify",
        "command-lanip-plugin-install",
        "command-lanip-plugin-enable"
      ],
      "steps": [
        {
          "commands": [
            "lanip plugin verify MiPlugin.lcp"
          ],
          "description": "Comprueba estructura, manifiesto, firma y seguridad antes de instalar.",
          "title": "Verificar el paquete"
        },
        {
          "commands": [
            "lanip plugin install MiPlugin.lcp"
          ],
          "description": "Importa el LCP sin ejecutar todavía su código.",
          "title": "Instalar desactivado"
        },
        {
          "commands": [
            "lanip plugin info plugin-id",
            "lanip plugin permissions plugin-id"
          ],
          "description": "Consulta identidad, capacidades y permisos solicitados.",
          "title": "Revisar manifiesto y permisos"
        },
        {
          "commands": [
            "lanip plugin enable plugin-id --grant permiso.necesario"
          ],
          "description": "Concede solamente los permisos necesarios. --grant-all debe reservarse para paquetes confiables.",
          "title": "Conceder y activar"
        },
        {
          "commands": [
            "lanip plugin list",
            "lanip plugin extensions"
          ],
          "description": "Confirma que el plugin aparece activo y revisa sus extensiones registradas.",
          "title": "Comprobar el resultado"
        }
      ],
      "summary": "Verifica el paquete, inspecciona permisos y actívalo de forma explícita.",
      "time": "5 min",
      "title": "Importar y activar un plugin LCP"
    },
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "CONFIGURATION.md",
        "CLI.md"
      ],
      "id": "workflow-lan-environment",
      "level": "Inicial",
      "related": [
        "command-lanip-settings",
        "command-lanip-list",
        "command-lanip-ephemeral"
      ],
      "steps": [
        {
          "commands": [
            "ipconfig  # Windows",
            "ip address  # Linux"
          ],
          "description": "Obtén el CIDR y el rango DHCP desde tu router o administrador.",
          "title": "Identificar la red"
        },
        {
          "commands": [
            "lanip settings --range 192.168.1.0/24"
          ],
          "description": "Configura la red autorizada que LANCTL puede explorar.",
          "title": "Guardar el rango LAN"
        },
        {
          "commands": [
            "lanip settings --dhcp-range 192.168.1.100-192.168.1.200"
          ],
          "description": "Separa direcciones dinámicas de equipos con IP fija.",
          "title": "Definir DHCP"
        },
        {
          "commands": [
            "lanip settings --discovery hybrid --scan-profile normal --progress on"
          ],
          "description": "Hybrid combina ICMP y ARP; normal es el perfil equilibrado.",
          "title": "Elegir descubrimiento"
        },
        {
          "commands": [
            "lanip ephemeral --normal --range 192.168.1.0/24"
          ],
          "description": "Valida primero el alcance mediante una sesión efímera.",
          "title": "Probar sin persistencia"
        },
        {
          "commands": [
            "lanip list --normal --active"
          ],
          "description": "Cuando el resultado sea correcto, ejecuta el escaneo persistente.",
          "title": "Crear el inventario"
        }
      ],
      "summary": "Define red, DHCP, descubrimiento y perfil de escaneo antes de inventariar.",
      "time": "10 min",
      "title": "Configurar el entorno de la LAN"
    },
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "ACCESS.md",
        "SECURITY.md"
      ],
      "id": "workflow-ssh-credentials",
      "level": "Intermedio",
      "related": [
        "command-lanip-protocol",
        "command-lanip-credential",
        "command-lanip-ssh"
      ],
      "steps": [
        {
          "commands": [
            "lanip search NAS",
            "lanip call NAS --json"
          ],
          "description": "Usa alias, IP o MAC y confirma que se trata del equipo correcto.",
          "title": "Localizar el dispositivo"
        },
        {
          "commands": [
            "lanip protocol NAS configure ssh --port 22"
          ],
          "description": "Registra el puerto del servicio. Cambia 22 si el equipo utiliza otro.",
          "title": "Configurar SSH"
        },
        {
          "commands": [
            "lanip credential NAS set ssh --username administrador"
          ],
          "description": "LANCTL solicitará la contraseña mediante entrada segura y no la mostrará.",
          "title": "Guardar la credencial"
        },
        {
          "commands": [
            "lanip ssh NAS probe",
            "lanip ssh NAS fingerprint"
          ],
          "description": "Verifica conectividad y compara la huella con la indicada por el equipo.",
          "title": "Comprobar y leer la huella"
        },
        {
          "commands": [
            "lanip ssh NAS trust SHA256:HUELLA",
            "lanip ssh NAS open"
          ],
          "description": "Solo confía en la huella después de validarla por un canal independiente.",
          "title": "Confiar y conectar"
        }
      ],
      "summary": "Asocia el protocolo, guarda el secreto cifrado y valida la huella antes de abrir una sesión.",
      "time": "10 min",
      "title": "Configurar credenciales y conexión SSH"
    },
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "ACCESS.md",
        "ENTERPRISE.md"
      ],
      "id": "workflow-remote-access",
      "level": "Avanzado",
      "related": [
        "command-lanip-access",
        "command-lanip-settings"
      ],
      "steps": [
        {
          "commands": [
            "lanip access init"
          ],
          "description": "Crea la estructura local sin exponer todavía ningún servicio.",
          "title": "Inicializar"
        },
        {
          "commands": [
            "lanip access configure ssh --bind 192.168.1.31 --cidr 192.168.1.0/24 --port 2222"
          ],
          "description": "Usa una IP LAN concreta y nunca publiques directamente el servicio en Internet.",
          "title": "Configurar el enlace"
        },
        {
          "commands": [
            "lanip access user add operador --role operator"
          ],
          "description": "Asigna el rol mínimo necesario.",
          "title": "Crear un usuario"
        },
        {
          "commands": [
            "lanip access status --json"
          ],
          "description": "Revisa configuración y estado desde el propio nodo.",
          "title": "Validar antes de activar"
        },
        {
          "commands": [
            "ssh -p 2222 operador@192.168.1.31"
          ],
          "description": "Conecta desde un host dentro del CIDR permitido y conserva los logs de la prueba.",
          "title": "Probar desde otro equipo"
        }
      ],
      "summary": "Inicializa usuarios y limita SSH/HTTPS a una dirección y un CIDR autorizados.",
      "time": "15 min",
      "title": "Habilitar acceso remoto a LANCTL"
    },
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "MONITOR.md",
        "VLF.md"
      ],
      "id": "workflow-monitor-project",
      "level": "Intermedio",
      "related": [
        "command-lanip-monitor",
        "command-lanip-project-verify"
      ],
      "steps": [
        {
          "commands": [
            "lanip project verify Oficina.vlf"
          ],
          "description": "No monitorices un contenedor dañado o de procedencia desconocida.",
          "title": "Verificar el proyecto"
        },
        {
          "commands": [
            "lanip project use Oficina.vlf"
          ],
          "description": "Selecciona el inventario que se observará.",
          "title": "Activarlo"
        },
        {
          "commands": [
            "lanip monitor once --type presence"
          ],
          "description": "Empieza con una pasada única antes de crear una sesión prolongada.",
          "title": "Ejecutar una comprobación"
        },
        {
          "commands": [
            "lanip monitor start --mode temporary --duration 1h --interval 60"
          ],
          "description": "Ajusta duración e intervalo al tamaño de la red.",
          "title": "Iniciar una sesión temporal"
        },
        {
          "commands": [
            "lanip monitor session list",
            "lanip monitor incidents",
            "lanip monitor stop"
          ],
          "description": "Consulta sesiones e incidencias y detén la monitorización al terminar.",
          "title": "Revisar resultados"
        }
      ],
      "summary": "Comprueba el proyecto, inicia una sesión controlada y revisa sus incidencias.",
      "time": "10 min",
      "title": "Monitorizar un proyecto"
    },
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "STORAGE.md",
        "TROUBLESHOOTING.md"
      ],
      "id": "workflow-backup-restore",
      "level": "Inicial",
      "related": [
        "command-lanip-database"
      ],
      "steps": [
        {
          "commands": [
            "lanip database --diagnose"
          ],
          "description": "Resuelve problemas existentes antes de crear la copia.",
          "title": "Diagnosticar"
        },
        {
          "commands": [
            "lanip database --export LANCTL-backup.zip"
          ],
          "description": "Crea un archivo portable en una ubicación con espacio suficiente.",
          "title": "Exportar"
        },
        {
          "commands": [
            "lanip database --verify LANCTL-backup.zip"
          ],
          "description": "Comprueba estructura y hashes inmediatamente.",
          "title": "Verificar"
        },
        {
          "commands": [],
          "description": "Conserva otra copia en un medio o ubicación independiente.",
          "title": "Guardar fuera del equipo"
        },
        {
          "commands": [
            "lanip database --import LANCTL-backup.zip",
            "lanip database --restore ARCHIVO.bak --yes"
          ],
          "description": "Revisa el destino y conserva los datos actuales antes de confirmar.",
          "title": "Restaurar solo cuando sea necesario"
        }
      ],
      "summary": "Exporta los datos, verifica el ZIP y practica una restauración controlada.",
      "time": "5 min",
      "title": "Crear y verificar una copia de seguridad"
    },
    {
      "compatibility": {
        "verified": "0.3.2-beta.4"
      },
      "docs": [
        "CLI.md",
        "CONFIGURATION.md"
      ],
      "id": "workflow-new-device",
      "level": "Inicial",
      "related": [
        "command-lanip-scan",
        "command-lanip-element",
        "command-lanip-group"
      ],
      "steps": [
        {
          "commands": [
            "lanip scan 192.168.1.50 --identify --banners"
          ],
          "description": "Confirma disponibilidad, identidad y servicios sin modificarlo.",
          "title": "Escanear el objetivo"
        },
        {
          "commands": [
            "lanip call 192.168.1.50 --json"
          ],
          "description": "Consulta la información capturada antes de editar.",
          "title": "Revisar el registro"
        },
        {
          "commands": [
            "lanip element 192.168.1.50 -name Servidor -alias NAS -description \"Almacenamiento principal\""
          ],
          "description": "Añade nombre, alias y descripción en una operación validada.",
          "title": "Asignar identidad legible"
        },
        {
          "commands": [
            "lanip group SERVIDORES -new",
            "lanip group SERVIDORES -add NAS"
          ],
          "description": "Crea el grupo si no existe y añade el dispositivo.",
          "title": "Clasificar"
        },
        {
          "commands": [
            "lanip element NAS -protocol ssh"
          ],
          "description": "Añade únicamente servicios que hayas confirmado.",
          "title": "Registrar protocolos"
        }
      ],
      "summary": "Descubre un equipo, confirma su identidad y completa nombre, grupo y protocolos.",
      "time": "5 min",
      "title": "Añadir y documentar un dispositivo"
    }
  ]
};
