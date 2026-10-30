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
          "description": "Show the common suite version and exit.",
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
          "description": "Open the main console.",
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
          "description": "Open the main TUI.",
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
          "description": "Open the LANCTL graphical hub.",
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
          "description": "Show and open the official website.",
          "flags": [
            "-web",
            "--web"
          ],
          "label": "-web, --web",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Show and open the official GitHub.",
          "flags": [
            "-github",
            "--github"
          ],
          "label": "-github, --github",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Show and open the official reference.",
          "flags": [
            "-reference",
            "--reference"
          ],
          "label": "-reference, --reference",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Explicitly request UAC for an installed launcher on Windows.",
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
        "language",
        "backend",
        "setup-defaults",
        "completions",
        "post-install"
      ],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Root orchestrator for the LANCTL suite applications.",
      "details": "Usage: LANCTL [-h] [--version] [--cli | -tui | --gui] [-web | -github | -reference] [--admin]\n              LAUNCHER ...\n\nRoot orchestrator for the LANCTL suite applications.\n\nArguments:\n  LAUNCHER\n    lanip (ip)             Logical inventory, discovery, IP, MAC and services.\n    lanwire (wire)         Wiring, ports, panels and physical topology.\n    lanrack (rack)         Technical rooms, racks, rack units and equipment.\n    lanaccess (access)     Users, credentials and remote access.\n    lanmon (monitor)       Monitoring, events, incidents and history.\n    plugin                 Shared suite administration.\n    settings               Shared suite administration.\n    language               Shared suite administration.\n    backend                Shared suite administration.\n    setup-defaults         Initialize installation preferences without overwriting existing ones.\n    completions            Register or remove Clink completion for the current user.\n    post-install           Open LANIP as the normal user after installation.\n\nOptions:\n  -h, --help               Show this help and exit.\n  --version                Show the common suite version and exit.\n  --cli, -cli              Open the main console.\n  -tui, --tui              Open the main TUI.\n  --gui                    Open the LANCTL graphical hub.\n  -web, --web              Show and open the official website.\n  -github, --github        Show and open the official GitHub.\n  -reference, --reference  Show and open the official reference.\n  --admin                  Explicitly request UAC for an installed launcher on Windows.",
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
      "usage": "LANCTL [-h] [--version] [--cli | -tui | --gui] [-web | -github | -reference] [--admin]\n              LAUNCHER ..."
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
          "description": "Show the version and exit.",
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
          "description": "Suppress successful output; preserve errors.",
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
          "description": "Add execution diagnostics to stderr.",
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
          "description": "Open the LANIP graphical interface.",
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
          "description": "Request first scan confirmation when opening the GUI; do not scan automatically.",
          "flags": [
            "--first-scan"
          ],
          "label": "--first-scan",
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
          "description": "Open the advanced full-screen terminal interface. Can open PLUGINS, PROJECTS or SETTINGS directly.",
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
          "description": "Select a VLF project before opening the TUI or running a command.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Logical control of LAN devices and infrastructure.",
      "details": "Usage: LANIP [-h] [--version] [--quiet | --verbose] [--gui] [--first-scan] [--cli]\n             [-tui [VENTANA]] [-project ARCHIVO.vlf]\n             COMANDO ...\n\nLogical control of LAN devices and infrastructure.\n\nArguments:\n  COMANDO\n    ephemeral (-e)            Scan active hosts without reading or saving any inventory.\n    list                      Scan the LAN and show active and historical devices.\n    recurrent                 Query recurring elements known to LANCTL.\n    ping                      Check once whether an element responds to PING or ARP.\n    open (connect)            Open an element with a protocol-appropriate client.\n    settings                  Query or change LANCTL's persistent configuration.\n    call                      Resolve an alias, IP or MAC to device data.\n    search                    Search devices by alias, name, IP or MAC.\n    scan                      Inspect a single LAN element in depth.\n    cnf                       Assign an element's CNF state by IP, MAC or alias.\n    credential (credentials, auth)\n                              Associate encrypted credentials with an element and protocol.\n    GATEWAY (gateway)         Query and configure the gateway through TR-064.\n    downloadSettings (downloadsettings, download-settings)\n                              Legacy alias for “GATEWAY downloadSettings”.\n    protocol                  Query or configure an element's protocol.\n    ssh                       Open SSH or run a read-only show query.\n    radmin                    Configure, check or open Radmin Viewer.\n    wol                       Wake devices through Wake-on-LAN and run safe sequences.\n    history                   Query structured events from the active VLF project.\n    monitor                   Operate LAN monitor sessions and checks.\n    access                    Configure secure LAN remote access through SSH and HTTPS.\n    smb                       Discover and open Windows SMB resources.\n    terminal (cli)            Open an element's terminal according to its protocol.\n    switch                    Plan filtered, remapped and classified Cisco commands.\n    group                     Create, edit and query element groups.\n    element                   Edit one or more fields of an element identified by IP, MAC or\n                              alias.\n    project (projects)        Create, update and inspect LANCTL .vlf projects.\n    plugin (plugins, addon, addons)\n                              Manage unified LANCTL .lcp plugins.\n    language (languages, lang)\n                              Manage LANCTL interface languages.\n    error (errors)            Query the catalog by identifier 0eXXXXXXXX.\n    database (db)             Diagnose and export data.\n    demo                      Generate a reproducible walkthrough without depending on a real\n                              network.\n    lanwire (wire)            Open LANWIRE or run one of its commands on the shared physical\n                              database.\n    lab                       Manage simulated LANs without real traffic.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --version                   Show the version and exit.\n  --quiet                     Suppress successful output; preserve errors.\n  --verbose                   Add execution diagnostics to stderr.\n  --gui                       Open the LANIP graphical interface.\n  --first-scan                Request first scan confirmation when opening the GUI; do not scan\n                              automatically.\n  --cli, -cli                 Open the persistent interactive LANCTL terminal.\n  -tui, --tui [VENTANA]       Open the advanced full-screen terminal interface. Can open PLUGINS,\n                              PROJECTS or SETTINGS directly.\n  -project, --project ARCHIVO.vlf\n                              Select a VLF project before opening the TUI or running a command.",
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
      "usage": "LANIP [-h] [--version] [--quiet | --verbose] [--gui] [--first-scan] [--cli]\n             [-tui [VENTANA]] [-project ARCHIVO.vlf]\n             COMANDO ..."
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
          "description": "CIDR range to explore only during this execution.",
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
          "description": "Resolve names without storing them.",
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
          "description": "Optional TCP ports, for example 22,80,443.",
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
          "description": "Return the session as JSON.",
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
          "description": "Concurrent probes.",
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
          "description": "Base timeout per probe, in seconds.",
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
          "description": "Defensive limit on authorized addresses.",
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
          "description": "Address exploration order.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Perform actual discovery in an isolated in-memory session. Does not open, modify or save projects or device databases.",
      "details": "Usage: LANIP ephemeral [-h] [--fast | --normal | --accurate] [--range NETWORK] [--resolve-names]\n                       [--ports PORTS] [--json] [--workers WORKERS] [--timeout TIMEOUT]\n                       [--max-hosts MAX_HOSTS] [--scan-order {ascending,descending,random}]\n\nPerform actual discovery in an isolated in-memory session. Does not open, modify or save projects or device databases.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --fast                      Prioriza un barrido ARP rápido.\n  --normal                    Combina ICMP, ARP y descubrimiento de servicios.\n  --accurate                  Añade reintentos y reconocimiento más profundo.\n  --range NETWORK             CIDR range to explore only during this execution.\n  --resolve-names             Resolve names without storing them.\n  --ports PORTS               Optional TCP ports, for example 22,80,443.\n  --json                      Return the session as JSON.\n  --workers WORKERS           Concurrent probes.\n  --timeout TIMEOUT           Base timeout per probe, in seconds.\n  --max-hosts MAX_HOSTS       Defensive limit on authorized addresses.\n  --scan-order {ascending,descending,random}\n                              Address exploration order.",
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
          "description": "CIDR network. Detects the LAN as /24 by default.",
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
          "description": "Local IPv4 source or interface ID; uses its actual mask. ICMP/ARP only, without DNS or external discovery.",
          "flags": [
            "--interface"
          ],
          "label": "--interface",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Element JSON file.",
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
          "description": "Group JSON file.",
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
          "description": "Output format (default: table).",
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
          "description": "Save output to a file.",
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
          "description": "List recurring elements without scanning the LAN or showing IP.",
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
          "description": "Composable query, for example: \"active and group=IOT and vendor~Amazon\".",
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
          "description": "Concurrent checks.",
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
          "description": "Base timeout in seconds per operation and host; the profile may adjust it.",
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
          "description": "IP probe order: ascending, descending or random.",
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
          "description": "Include active hosts even if their MAC is not yet known.",
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
          "description": "Resolve and save DNS names of detected elements.",
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
          "description": "Maximum hosts allowed in a scan.",
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
          "description": "Method: icmp, active arp or hybrid (default from settings).",
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
          "description": "Complete scan profile: fast, normal or accurate.",
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
          "description": "Fast ARP scan.",
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
          "description": "Balanced hybrid scan.",
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
          "description": "Deep scan using multiple methods.",
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
          "description": "Show interactive progress.",
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
          "description": "Hide progress.",
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
          "description": "Add a column with ICMP, ARP, LOCAL, BASIC or CACHE.",
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
          "description": "Import cached ARP neighbors as unverified CACHE; they do not count as active.",
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
          "description": "Add historical methods and last-seen date.",
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
          "description": "Show only devices active in the current scan.",
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
          "description": "Show only devices not currently detected.",
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
          "description": "Compact view: IP, alias and description.",
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
          "description": "Filter by CNF state: O, X, -, S or F.",
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
          "description": "Show only elements in a group.",
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
          "description": "Show only IPs within the configured DHCP range.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Perform a basic IP/MAC scan, update the database by MAC and also show undetected devices.",
      "details": "Usage: LANIP list [-h] [--network NETWORK] [--interface INTERFACE] [--database DATABASE]\n                  [--groups GROUPS] [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT] [-recurrent]\n                  [--where WHERE] [-w WORKERS] [-t TIMEOUT]\n                  [--scan-order {ascending,descending,random}] [--include-unknown]\n                  [--resolve-names] [--max-hosts MAX_HOSTS] [--discovery {icmp,arp,hybrid}]\n                  [--profile {fast,normal,accurate} | --fast | --normal | --accurate]\n                  [--progress | --no-progress] [--show-discovery] [--include-arp-cache]\n                  [--show-detection] [--active | -disconnected] [-basic] [-cnf {O,X,-,S,F}]\n                  [-group GRUPO] [-dhcp]\n\nPerform a basic IP/MAC scan, update the database by MAC and also show undetected devices.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --network NETWORK           CIDR network. Detects the LAN as /24 by default.\n  --interface INTERFACE       Local IPv4 source or interface ID; uses its actual mask. ICMP/ARP\n                              only, without DNS or external discovery.\n  --database DATABASE         Element JSON file.\n  --groups GROUPS             Group JSON file.\n  -f, --format {table,json,csv,html,xml,yaml}\n                              Output format (default: table).\n  -o, --output OUTPUT         Save output to a file.\n  -recurrent, --recurrent     List recurring elements without scanning the LAN or showing IP.\n  --where WHERE               Composable query, for example: \"active and group=IOT and\n                              vendor~Amazon\".\n  -w, --workers WORKERS       Concurrent checks.\n  -t, --timeout TIMEOUT       Base timeout in seconds per operation and host; the profile may\n                              adjust it.\n  --scan-order {ascending,descending,random}\n                              IP probe order: ascending, descending or random.\n  --include-unknown           Include active hosts even if their MAC is not yet known.\n  --resolve-names             Resolve and save DNS names of detected elements.\n  --max-hosts MAX_HOSTS       Maximum hosts allowed in a scan.\n  --discovery {icmp,arp,hybrid}\n                              Method: icmp, active arp or hybrid (default from settings).\n  --profile {fast,normal,accurate}\n                              Complete scan profile: fast, normal or accurate.\n  --fast                      Fast ARP scan.\n  --normal                    Balanced hybrid scan.\n  --accurate                  Deep scan using multiple methods.\n  --progress                  Show interactive progress.\n  --no-progress               Hide progress.\n  --show-discovery            Add a column with ICMP, ARP, LOCAL, BASIC or CACHE.\n  --include-arp-cache         Import cached ARP neighbors as unverified CACHE; they do not count\n                              as active.\n  --show-detection            Add historical methods and last-seen date.\n  --active, -active, -connected, --connected, -conected\n                              Show only devices active in the current scan.\n  -disconnected, --disconnected, -offline\n                              Show only devices not currently detected.\n  -basic, --basic             Compact view: IP, alias and description.\n  -cnf, --cnf-state {O,X,-,S,F}\n                              Filter by CNF state: O, X, -, S or F.\n  -group, --group GRUPO       Show only elements in a group.\n  -dhcp, --dhcp-only          Show only IPs within the configured DHCP range.",
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
      "usage": "LANIP list [-h] [--network NETWORK] [--interface INTERFACE] [--database DATABASE]\n                  [--groups GROUPS] [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT] [-recurrent]\n                  [--where WHERE] [-w WORKERS] [-t TIMEOUT]\n                  [--scan-order {ascending,descending,random}] [--include-unknown]\n                  [--resolve-names] [--max-hosts MAX_HOSTS] [--discovery {icmp,arp,hybrid}]\n                  [--profile {fast,normal,accurate} | --fast | --normal | --accurate]\n                  [--progress | --no-progress] [--show-discovery] [--include-arp-cache]\n                  [--show-detection] [--active | -disconnected] [-basic] [-cnf {O,X,-,S,F}]\n                  [-group GRUPO] [-dhcp]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "List all recurring elements without their IPs.",
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
          "description": "Output format (default: table).",
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
          "description": "Save output to a file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Show recurring identities by MAC. Does not include IP because it can change on each LAN.",
      "details": "Usage: LANIP recurrent [-h] -list [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT]\n\nShow recurring identities by MAC. Does not include IP because it can change on each LAN.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -list, --list               List all recurring elements without their IPs.\n  -f, --format {table,json,csv,html,xml,yaml}\n                              Output format (default: table).\n  -o, --output OUTPUT         Save output to a file.",
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
          "description": "IP, MAC, alias or registered name.",
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
          "description": "Lookup method: auto, ping or arp (default: auto).",
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
          "description": "Use only one ICMP request.",
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
          "description": "Use only one active ARP request.",
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
          "description": "Maximum timeout per check, in seconds.",
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
          "description": "Return diagnostics as JSON.",
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
          "description": "Element JSON file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Diagnose a single element without changing the database. PING tests ICMP; ARP performs an active LAN query; AUTO combines both methods.",
      "details": "Usage: LANIP ping [-h] [--method {auto,ping,arp} | --ping | --arp] [--timeout TIMEOUT] [--json]\n                  [--database DATABASE]\n                  selector\n\nDiagnose a single element without changing the database. PING tests ICMP; ARP performs an active LAN query; AUTO combines both methods.\n\nArguments:\n  selector                  IP, MAC, alias or registered name.\n\nOptions:\n  -h, --help                Show this help and exit.\n  --method {auto,ping,arp}  Lookup method: auto, ping or arp (default: auto).\n  --ping                    Use only one ICMP request.\n  --arp                     Use only one active ARP request.\n  --timeout TIMEOUT         Maximum timeout per check, in seconds.\n  --json                    Return diagnostics as JSON.\n  --database DATABASE       Element JSON file.",
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
          "description": "Element IP, MAC or alias.",
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
          "description": "Protocol or automatic detection.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Alternative port.",
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
          "description": "HTTP/FTP/RTSP path or SMB resource.",
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
          "description": "Radmin connection mode.",
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
          "description": "Intermediate Radmin server HOST:PORT.",
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
          "description": "Open full-screen control or view.",
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
          "description": "Radmin color depth (1, 2, 4, 8, 16 or 24 bits).",
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
          "description": "Maximum screen updates per second (1-120).",
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
          "description": "Radmin .rpb phonebook path.",
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
          "description": "Entry identifier within the Radmin phonebook.",
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
          "description": "Show the target without opening it.",
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
          "description": "Element JSON file.",
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
          "description": "Encrypted credential store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP open [-h] [--port PORT] [--path PATH]\n                  [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                  [--through THROUGH] [--fullscreen] [--color-depth {24,16,8,4,2,1}]\n                  [--updates UPDATES] [--phonebook PHONEBOOK] [--phonebook-id PHONEBOOK_ID]\n                  [--dry-run] [--database DATABASE] [--store STORE]\n                  selector [{auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}]",
      "details": "Usage: LANIP open [-h] [--port PORT] [--path PATH]\n                  [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                  [--through THROUGH] [--fullscreen] [--color-depth {24,16,8,4,2,1}]\n                  [--updates UPDATES] [--phonebook PHONEBOOK] [--phonebook-id PHONEBOOK_ID]\n                  [--dry-run] [--database DATABASE] [--store STORE]\n                  selector [{auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}]\n\nArguments:\n  selector                    Element IP, MAC or alias.\n  {auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}\n                              Protocol or automatic detection.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --port PORT                 Alternative port.\n  --path PATH                 HTTP/FTP/RTSP path or SMB resource.\n  --mode {control,view,file,shutdown,chat,voice,message,telnet}\n                              Radmin connection mode.\n  --through THROUGH           Intermediate Radmin server HOST:PORT.\n  --fullscreen                Open full-screen control or view.\n  --color-depth {24,16,8,4,2,1}\n                              Radmin color depth (1, 2, 4, 8, 16 or 24 bits).\n  --updates UPDATES           Maximum screen updates per second (1-120).\n  --phonebook PHONEBOOK       Radmin .rpb phonebook path.\n  --phonebook-id PHONEBOOK_ID\n                              Entry identifier within the Radmin phonebook.\n  --dry-run                   Show the target without opening it.\n  --database DATABASE         Element JSON file.\n  --store STORE               Encrypted credential store.",
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
          "choices": [
            "cli",
            "tui",
            "gui"
          ],
          "default": null,
          "description": "Preferred interface when opening LANCTL without arguments.",
          "flags": [
            "--startup-interface"
          ],
          "label": "--startup-interface",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "on",
            "off"
          ],
          "default": null,
          "description": "Close the main GUI when the requested launcher is available.",
          "flags": [
            "--close-gui-on-launch"
          ],
          "label": "--close-gui-on-launch",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Default LAN range, for example 192.168.1.1/24.",
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
          "description": "Columns displayed by list, separated by spaces or commas.",
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
          "description": "Manual DHCP range. Use 'off' to leave it unconfigured.",
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
          "description": "Path to the encrypted credential store.",
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
          "description": "Default method used by list.",
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
          "description": "Default list profile: fast, normal or accurate.",
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
          "description": "Enable or disable interactive progress.",
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
          "description": "Enable or disable service recognition in scan.",
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
          "description": "Disconnected device persistence: permanent, session or forget.",
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
          "description": "Apply retention only to CNF=X (unconfirmed) or to all (all).",
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
          "description": "Apply the rule to the entire LAN (all) or only the DHCP range (dhcp).",
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
          "description": "Default scan concurrency.",
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
          "description": "Default timeout per network operation.",
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
          "description": "Default probe order: ascending, descending or random.",
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
          "description": "Maximum hosts authorized per scan.",
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
          "description": "Path to the element inventory.",
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
          "description": "Path to the physical SQLite database managed exclusively by LANWIRE.",
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
          "description": "Path to the group database.",
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
          "description": "Log directory.",
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
          "description": "Minimum ErrorEvent level written to the log (1 includes detailed diagnostics).",
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
          "description": "Default folder for relative VLF project names.",
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
          "description": "VLF save policy. Use 'list' to query built-in and plugin-provided options.",
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
          "description": "Interval for automatic.timeToSave in minutes (minimum 0.1).",
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
          "description": "Ask whether to save after each individual console command.",
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
          "description": "Allow command chaining with ; in the interactive CLI.",
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
          "description": "Enable or disable automatic cleanup of old logs.",
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
          "description": "Number of days to retain log files.",
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
          "description": "Enable restricted SSH access.",
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
          "description": "Local IPv4 address for SSH listening.",
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
          "description": "Authorized source network.",
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
          "description": "Remote SSH server port.",
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
          "description": "Allow or block SSH password authentication.",
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
          "description": "Run the backend as a persistent service or user process.",
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
          "description": "Default view for root forced-view.",
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
          "description": "Assign a key to a TUI action. May be repeated.",
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
          "description": "Place the CLI at the top (cli.top) or bottom (cli.bottom).",
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
          "description": "Vertical percentage reserved for CLI; ListElement retains at least 25%%.",
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
          "description": "Column weight (GROUP=15%%); IP=15ch and MAC=17ch are fixed.",
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
          "description": "Visible bottom-bar actions, comma-separated; use all for all actions.",
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
          "description": "Show or hide a specific bottom-bar action. May be repeated.",
          "flags": [
            "--tui-footer-button"
          ],
          "label": "--tui-footer-button",
          "metavar": "ACCIÓN=on|off",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Interactive program and project editor organized by category.",
          "flags": [
            "--menu"
          ],
          "label": "--menu",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "List common and CLI preferences by category, with values and editability.",
          "flags": [
            "--catalog"
          ],
          "label": "--catalog",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Query a setting by path, for example ip.workers.",
          "flags": [
            "--get"
          ],
          "label": "--get",
          "metavar": "RUTA",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Change a common or CLI preference; lists and booleans use JSON.",
          "flags": [
            "--set"
          ],
          "label": "--set",
          "metavar": "('RUTA', 'VALOR')",
          "required": false
        },
        {
          "choices": [
            "program",
            "project"
          ],
          "default": "program",
          "description": "Configuration scope (default: program).",
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
          "description": "Filter the catalog by category, for example network or monitor.",
          "flags": [
            "--category"
          ],
          "label": "--category",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Configuración",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP settings [-h] [--startup-interface {cli,tui,gui}] [--close-gui-on-launch {on,off}]\n                      [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]\n                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]\n                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]\n                      [--service-identification {on,off}]\n                      [--disconnected-retention {permanent,session,forget}]\n                      [--disconnected-target {unconfirmed,all}] [--disconnected-scope {all,dhcp}]\n                      [--workers WORKERS] [--timeout TIMEOUT]\n                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]\n                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]\n                      [--log DIRECTORIO] [--error-log-level 1-59]\n                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]\n                      [--cli-exit-save-prompt {on,off}] [--cli-command-chaining {on,off}]\n                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]\n                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]\n                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]\n                      [--remote-backend {service,user}]\n                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]\n                      [--tui-key ACCIÓN=TECLA] [--tui-layout {cli.bottom,cli.top}]\n                      [--tui-cli-percent 15-75] [--tui-column COLUMNA=TAMAÑO]\n                      [--tui-footer-buttons ACCIONES] [--tui-footer-button ACCIÓN=on|off]\n                      [--menu | --catalog | --get RUTA | --set RUTA VALOR]\n                      [--scope {program,project}] [--category CATEGORY]",
      "details": "Usage: LANIP settings [-h] [--startup-interface {cli,tui,gui}] [--close-gui-on-launch {on,off}]\n                      [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]\n                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]\n                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]\n                      [--service-identification {on,off}]\n                      [--disconnected-retention {permanent,session,forget}]\n                      [--disconnected-target {unconfirmed,all}] [--disconnected-scope {all,dhcp}]\n                      [--workers WORKERS] [--timeout TIMEOUT]\n                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]\n                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]\n                      [--log DIRECTORIO] [--error-log-level 1-59]\n                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]\n                      [--cli-exit-save-prompt {on,off}] [--cli-command-chaining {on,off}]\n                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]\n                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]\n                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]\n                      [--remote-backend {service,user}]\n                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]\n                      [--tui-key ACCIÓN=TECLA] [--tui-layout {cli.bottom,cli.top}]\n                      [--tui-cli-percent 15-75] [--tui-column COLUMNA=TAMAÑO]\n                      [--tui-footer-buttons ACCIONES] [--tui-footer-button ACCIÓN=on|off]\n                      [--menu | --catalog | --get RUTA | --set RUTA VALOR]\n                      [--scope {program,project}] [--category CATEGORY]\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --startup-interface {cli,tui,gui}\n                              Preferred interface when opening LANCTL without arguments.\n  --close-gui-on-launch {on,off}\n                              Close the main GUI when the requested launcher is available.\n  -range CIDR                 Default LAN range, for example 192.168.1.1/24.\n  -list-fields, --list-fields, -list CAMPO [CAMPO ...]\n                              Columns displayed by list, separated by spaces or commas.\n  -dhcp-range, --dhcp-range, -dhcp INICIO-FIN\n                              Manual DHCP range. Use 'off' to leave it unconfigured.\n  -credentials, --credentials ARCHIVO\n                              Path to the encrypted credential store.\n  -discovery, --discovery {icmp,arp,hybrid}\n                              Default method used by list.\n  --scan-profile {fast,normal,accurate}\n                              Default list profile: fast, normal or accurate.\n  --progress {on,off}         Enable or disable interactive progress.\n  --service-identification {on,off}\n                              Enable or disable service recognition in scan.\n  --disconnected-retention {permanent,session,forget}\n                              Disconnected device persistence: permanent, session or forget.\n  --disconnected-target {unconfirmed,all}\n                              Apply retention only to CNF=X (unconfirmed) or to all (all).\n  --disconnected-scope {all,dhcp}\n                              Apply the rule to the entire LAN (all) or only the DHCP range\n                              (dhcp).\n  --workers WORKERS           Default scan concurrency.\n  --timeout TIMEOUT           Default timeout per network operation.\n  --scan-order {ascending,descending,random}\n                              Default probe order: ascending, descending or random.\n  --max-hosts MAX_HOSTS       Maximum hosts authorized per scan.\n  --database ARCHIVO          Path to the element inventory.\n  --physical-database ARCHIVO\n                              Path to the physical SQLite database managed exclusively by LANWIRE.\n  --groups ARCHIVO            Path to the group database.\n  --log DIRECTORIO            Log directory.\n  --error-log-level 1-59      Minimum ErrorEvent level written to the log (1 includes detailed\n                              diagnostics).\n  --projects-directory DIRECTORIO\n                              Default folder for relative VLF project names.\n  -save-mode, --save-mode MODO\n                              VLF save policy. Use 'list' to query built-in and plugin-provided\n                              options.\n  -save-interval, --save-interval MINUTOS\n                              Interval for automatic.timeToSave in minutes (minimum 0.1).\n  --cli-exit-save-prompt {on,off}\n                              Ask whether to save after each individual console command.\n  --cli-command-chaining {on,off}\n                              Allow command chaining with ; in the interactive CLI.\n  -log-cleanup, --log-cleanup {on,off}\n                              Enable or disable automatic cleanup of old logs.\n  -log-retention-days, --log-retention-days DÍAS\n                              Number of days to retain log files.\n  --remote-access {on,off}    Enable restricted SSH access.\n  --remote-bind IP            Local IPv4 address for SSH listening.\n  --remote-cidr CIDR          Authorized source network.\n  --remote-port REMOTE_PORT   Remote SSH server port.\n  --remote-password-auth {on,off}\n                              Allow or block SSH password authentication.\n  --remote-backend {service,user}\n                              Run the backend as a persistent service or user process.\n  --remote-forced-view {off,gui,tui,plugins,projects,settings}\n                              Default view for root forced-view.\n  --tui-key ACCIÓN=TECLA      Assign a key to a TUI action. May be repeated.\n  --tui-layout {cli.bottom,cli.top}\n                              Place the CLI at the top (cli.top) or bottom (cli.bottom).\n  --tui-cli-percent 15-75     Vertical percentage reserved for CLI; ListElement retains at least\n                              25%.\n  --tui-column COLUMNA=TAMAÑO\n                              Column weight (GROUP=15%); IP=15ch and MAC=17ch are fixed.\n  --tui-footer-buttons ACCIONES\n                              Visible bottom-bar actions, comma-separated; use all for all\n                              actions.\n  --tui-footer-button ACCIÓN=on|off\n                              Show or hide a specific bottom-bar action. May be repeated.\n  --menu                      Interactive program and project editor organized by category.\n  --catalog                   List common and CLI preferences by category, with values and\n                              editability.\n  --get RUTA                  Query a setting by path, for example ip.workers.\n  --set RUTA VALOR            Change a common or CLI preference; lists and booleans use JSON.\n  --scope {program,project}   Configuration scope (default: program).\n  --category CATEGORY         Filter the catalog by category, for example network or monitor.",
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
      "usage": "LANIP settings [-h] [--startup-interface {cli,tui,gui}] [--close-gui-on-launch {on,off}]\n                      [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]\n                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]\n                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]\n                      [--service-identification {on,off}]\n                      [--disconnected-retention {permanent,session,forget}]\n                      [--disconnected-target {unconfirmed,all}] [--disconnected-scope {all,dhcp}]\n                      [--workers WORKERS] [--timeout TIMEOUT]\n                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]\n                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]\n                      [--log DIRECTORIO] [--error-log-level 1-59]\n                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]\n                      [--cli-exit-save-prompt {on,off}] [--cli-command-chaining {on,off}]\n                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]\n                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]\n                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]\n                      [--remote-backend {service,user}]\n                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]\n                      [--tui-key ACCIÓN=TECLA] [--tui-layout {cli.bottom,cli.top}]\n                      [--tui-cli-percent 15-75] [--tui-column COLUMNA=TAMAÑO]\n                      [--tui-footer-buttons ACCIONES] [--tui-footer-button ACCIÓN=on|off]\n                      [--menu | --catalog | --get RUTA | --set RUTA VALOR]\n                      [--scope {program,project}] [--category CATEGORY]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Device alias, IP or MAC.",
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
          "description": "Returned field (default: ip).",
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
          "description": "Return the complete record as JSON.",
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
          "description": "Element JSON file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP call [-h]\n                  [-f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}]\n                  [--json] [--database DATABASE]\n                  selector",
      "details": "Usage: LANIP call [-h]\n                  [-f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}]\n                  [--json] [--database DATABASE]\n                  selector\n\nArguments:\n  selector                    Device alias, IP or MAC.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -f, --field {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}\n                              Returned field (default: ip).\n  --json                      Return the complete record as JSON.\n  --database DATABASE         Element JSON file.",
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
          "description": "Exact alias, name, IP or MAC.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Return the complete record as JSON for scripts.",
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
          "description": "Element JSON file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP search [-h] [--json] [--database DATABASE] selector",
      "details": "Usage: LANIP search [-h] [--json] [--database DATABASE] selector\n\nArguments:\n  selector             Exact alias, name, IP or MAC.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --json               Return the complete record as JSON for scripts.\n  --database DATABASE  Element JSON file.",
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
          "description": "IP, MAC or alias registered in LANCTL.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "common",
          "description": "Ports or ranges: 22,80,443,8000-8100 (default: common).",
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
          "description": "Explicitly authorize a TCP 1-65535 scan.",
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
          "description": "Maximum timeout per connection, in seconds.",
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
          "description": "Maximum number of concurrent connections.",
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
          "description": "Read passive banners; do not send protocol-specific probes.",
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
          "description": "Recognize services and infer device type from evidence.",
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
          "description": "JSON output.",
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
          "description": "Element JSON file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Resolve an element by IP, MAC or alias and check identity, availability and TCP ports. Does not modify the device.",
      "details": "Usage: LANIP scan [-h] [--ports LISTA] [--all-ports] [--timeout TIMEOUT] [--workers WORKERS]\n                  [--banners] [--identify] [--json] [--database DATABASE]\n                  selector\n\nResolve an element by IP, MAC or alias and check identity, availability and TCP ports. Does not modify the device.\n\nArguments:\n  selector             IP, MAC or alias registered in LANCTL.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --ports LISTA        Ports or ranges: 22,80,443,8000-8100 (default: common).\n  --all-ports          Explicitly authorize a TCP 1-65535 scan.\n  --timeout TIMEOUT    Maximum timeout per connection, in seconds.\n  --workers WORKERS    Maximum number of concurrent connections.\n  --banners            Read passive banners; do not send protocol-specific probes.\n  --identify           Recognize services and infer device type from evidence.\n  --json               JSON output.\n  --database DATABASE  Element JSON file.",
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
          "description": "Element IP, MAC or alias.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) or F (FIXED). Without a value, release F and restore O.",
          "flags": [],
          "label": "value",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Element JSON file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP cnf [-h] [--database DATABASE] selector [value]",
      "details": "Usage: LANIP cnf [-h] [--database DATABASE] selector [value]\n\nArguments:\n  selector             Element IP, MAC or alias.\n  value                O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) or F (FIXED). Without a\n                       value, release F and restore O.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --database DATABASE  Element JSON file.",
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
          "description": "Element IP, MAC or alias.",
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
          "description": "Credential operation.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Protocol, for example tr-064.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Remote username.",
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
          "description": "Element JSON file.",
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
          "description": "Encrypted credential store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP credential [-h] [-user USERNAME] [--database DATABASE] [--store STORE]\n                        selector [{set,list,delete}] [protocol]",
      "details": "Usage: LANIP credential [-h] [-user USERNAME] [--database DATABASE] [--store STORE]\n                        selector [{set,list,delete}] [protocol]\n\nArguments:\n  selector                    Element IP, MAC or alias.\n  {set,list,delete}           Credential operation.\n  protocol                    Protocol, for example tr-064.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -user, --username USERNAME  Remote username.\n  --database DATABASE         Element JSON file.\n  --store STORE               Encrypted credential store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP GATEWAY [-h] ACCIÓN ...",
      "details": "Usage: LANIP GATEWAY [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    downloadSettings (downloadsettings, download-settings)\n                              Download relevant LAN and DHCP settings for configuration.\n\nOptions:\n  -h, --help                  Show this help and exit.",
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
          "description": "Router TR-064 port.",
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
          "description": "Maximum timeout in seconds.",
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
          "description": "Element JSON file.",
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
          "description": "Encrypted credential store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP GATEWAY downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                                      [--store STORE]",
      "details": "Usage: LANIP GATEWAY downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                                      [--store STORE]\n\nOptions:\n  -h, --help           Show this help and exit.\n  --port PORT          Router TR-064 port.\n  --timeout TIMEOUT    Maximum timeout in seconds.\n  --database DATABASE  Element JSON file.\n  --store STORE        Encrypted credential store.",
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
          "description": "Router IP, MAC or alias.",
          "flags": [],
          "label": "gateway",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "49000",
          "description": "Router TR-064 port.",
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
          "description": "Maximum timeout in seconds.",
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
          "description": "Element JSON file.",
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
          "description": "Encrypted credential store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                              [--store STORE]\n                              [gateway]",
      "details": "Usage: LANIP downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]\n                              [--store STORE]\n                              [gateway]\n\nArguments:\n  gateway              Router IP, MAC or alias.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --port PORT          Router TR-064 port.\n  --timeout TIMEOUT    Maximum timeout in seconds.\n  --database DATABASE  Element JSON file.\n  --store STORE        Encrypted credential store.",
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
          "description": "IP, MAC or alias.",
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
          "description": "Query or change the protocol.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Protocol to configure.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "22",
          "description": "Remote port.",
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
          "description": "Device driver.",
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
          "description": "Allowed host-key algorithm; may be repeated.",
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
          "description": "Key-exchange algorithm; may be repeated.",
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
          "description": "Reusable SSH profile.",
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
          "description": "Element JSON file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP protocol [-h] [--port PORT] [--driver DRIVER] [--host-key HOST_KEY] [--kex KEX]\n                      [--profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}]\n                      [--database DATABASE]\n                      selector {show,configure} protocol",
      "details": "Usage: LANIP protocol [-h] [--port PORT] [--driver DRIVER] [--host-key HOST_KEY] [--kex KEX]\n                      [--profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}]\n                      [--database DATABASE]\n                      selector {show,configure} protocol\n\nArguments:\n  selector                    IP, MAC or alias.\n  {show,configure}            Query or change the protocol.\n  protocol                    Protocol to configure.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --port PORT                 Remote port.\n  --driver DRIVER             Device driver.\n  --host-key HOST_KEY         Allowed host-key algorithm; may be repeated.\n  --kex KEX                   Key-exchange algorithm; may be repeated.\n  --profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}\n                              Reusable SSH profile.\n  --database DATABASE         Element JSON file.",
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
          "description": "IP, MAC or alias.",
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
          "description": "SSH operation.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Fingerprint or remote command, depending on the operation.",
          "flags": [],
          "label": "remote_command",
          "metavar": "COMANDO",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/database/devices.json",
          "description": "Element JSON file.",
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
          "description": "Encrypted credential store.",
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
          "description": "Candidate IP for probe/fingerprint, without changing the database.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP ssh [-h] [--database DATABASE] [--store STORE] [--host HOST]\n                 selector {probe,fingerprint,trust,open,show} [COMANDO ...]",
      "details": "Usage: LANIP ssh [-h] [--database DATABASE] [--store STORE] [--host HOST]\n                 selector {probe,fingerprint,trust,open,show} [COMANDO ...]\n\nArguments:\n  selector                    IP, MAC or alias.\n  {probe,fingerprint,trust,open,show}\n                              SSH operation.\n  COMANDO                     Fingerprint or remote command, depending on the operation.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --database DATABASE         Element JSON file.\n  --store STORE               Encrypted credential store.\n  --host HOST                 Candidate IP for probe/fingerprint, without changing the database.",
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
          "description": "Element IP, MAC or alias.",
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
          "description": "Per-device path; use 'auto' for automatic detection.",
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
          "description": "Intermediate server HOST:PORT.",
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
          "description": "Open full-screen control or view.",
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
          "description": "Radmin color depth (1, 2, 4, 8, 16 or 24 bits).",
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
          "description": "Maximum screen updates per second (1-120).",
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
          "description": "Radmin-managed .rpb phonebook.",
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
          "description": "Entry identifier within the Radmin phonebook.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP radmin [-h] [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                    [--port PORT] [--executable EXECUTABLE] [--through THROUGH] [--fullscreen]\n                    [--color-depth {24,16,8,4,2,1}] [--updates UPDATES] [--phonebook PHONEBOOK]\n                    [--phonebook-id PHONEBOOK_ID] [--database DATABASE] [--store STORE]\n                    selector {probe,configure,open}",
      "details": "Usage: LANIP radmin [-h] [--mode {control,view,file,shutdown,chat,voice,message,telnet}]\n                    [--port PORT] [--executable EXECUTABLE] [--through THROUGH] [--fullscreen]\n                    [--color-depth {24,16,8,4,2,1}] [--updates UPDATES] [--phonebook PHONEBOOK]\n                    [--phonebook-id PHONEBOOK_ID] [--database DATABASE] [--store STORE]\n                    selector {probe,configure,open}\n\nArguments:\n  selector                    Element IP, MAC or alias.\n  {probe,configure,open}      Opción de configuración de Radmin Viewer.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --mode {control,view,file,shutdown,chat,voice,message,telnet}\n                              Opción de configuración de Radmin Viewer.\n  --port PORT                 Opción de configuración de Radmin Viewer.\n  --executable EXECUTABLE     Per-device path; use 'auto' for automatic detection.\n  --through THROUGH           Intermediate server HOST:PORT.\n  --fullscreen                Open full-screen control or view.\n  --color-depth {24,16,8,4,2,1}\n                              Radmin color depth (1, 2, 4, 8, 16 or 24 bits).\n  --updates UPDATES           Maximum screen updates per second (1-120).\n  --phonebook PHONEBOOK       Radmin-managed .rpb phonebook.\n  --phonebook-id PHONEBOOK_ID\n                              Entry identifier within the Radmin phonebook.\n  --database DATABASE         Opción de configuración de Radmin Viewer.\n  --store STORE               Opción de configuración de Radmin Viewer.",
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
          "description": "NAME [wakeup|status|shutdown|restart|sleep|hibernate|configure] or sequence ...",
          "flags": [],
          "label": "words",
          "metavar": "",
          "required": false
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
          "description": "Element JSON file.",
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
          "description": "Encrypted credential store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP wol [-h] [-if CONDICIÓN] [--if-all CONDICIÓN] [--if-any CONDICIÓN]\n                 [--if-not CONDICIÓN] [-t SCHEDULE] [--message MESSAGE] [--force] [--cancel]\n                 [--broadcast BROADCAST] [--port PORT] [--repeat REPEAT] [--interval INTERVAL]\n                 [--wait WAIT] [--method {auto,arp,ping,port}] [--check-port CHECK_PORT]\n                 [--interface INTERFACE] [--retry RETRY] [--dry-run] [--json] [--quiet]\n                 [--group GROUP] [--all] [--yes] [--after AFTER] [--delay DELAY]\n                 [--timeout TIMEOUT] [--on-failure {stop,continue,retry}] [--cooldown COOLDOWN]\n                 [--max-attempts MAX_ATTEMPTS] [--power-transport {ssh,disabled}]\n                 [--power-platform {windows,linux}] [--power-command ACCIÓN=COMANDO]\n                 [--database DATABASE] [--store STORE] [--sequences SEQUENCES]\n                 [words ...]",
      "details": "Usage: LANIP wol [-h] [-if CONDICIÓN] [--if-all CONDICIÓN] [--if-any CONDICIÓN]\n                 [--if-not CONDICIÓN] [-t SCHEDULE] [--message MESSAGE] [--force] [--cancel]\n                 [--broadcast BROADCAST] [--port PORT] [--repeat REPEAT] [--interval INTERVAL]\n                 [--wait WAIT] [--method {auto,arp,ping,port}] [--check-port CHECK_PORT]\n                 [--interface INTERFACE] [--retry RETRY] [--dry-run] [--json] [--quiet]\n                 [--group GROUP] [--all] [--yes] [--after AFTER] [--delay DELAY]\n                 [--timeout TIMEOUT] [--on-failure {stop,continue,retry}] [--cooldown COOLDOWN]\n                 [--max-attempts MAX_ATTEMPTS] [--power-transport {ssh,disabled}]\n                 [--power-platform {windows,linux}] [--power-command ACCIÓN=COMANDO]\n                 [--database DATABASE] [--store STORE] [--sequences SEQUENCES]\n                 [words ...]\n\nArguments:\n  words                       NAME [wakeup|status|shutdown|restart|sleep|hibernate|configure] or\n                              sequence ...\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -if, --if CONDICIÓN         Condición AND adicional (repetible).\n  --if-all CONDICIÓN          Condición AND adicional.\n  --if-any CONDICIÓN          Condición OR adicional.\n  --if-not CONDICIÓN          Condición negada.\n  -t, --time SCHEDULE         Momento del apagado programado.\n  --message MESSAGE           Mensaje remoto, si el transporte lo admite.\n  --force                     Solicita cierre forzado al transporte.\n  --cancel                    Cancela una programación, si el transporte lo admite.\n  --broadcast BROADCAST       IPv4 de broadcast.\n  --port PORT                 Puerto UDP WOL.\n  --repeat REPEAT             Número de paquetes mágicos.\n  --interval INTERVAL         Intervalo entre paquetes.\n  --wait WAIT                 Segundos máximos de verificación.\n  --method {auto,arp,ping,port}\n                              Método de verificación.\n  --check-port CHECK_PORT     Puerto TCP de comprobación.\n  --interface INTERFACE       IPv4 local de salida.\n  --retry RETRY               Reintentos completos.\n  --dry-run                   Valida sin enviar.\n  --json                      Salida JSON estructurada.\n  --quiet                     Omite salida humana.\n  --group GROUP               Actúa sobre un grupo.\n  --all                       Actúa sobre todo el inventario.\n  --yes                       Confirma explícitamente --all.\n  --after AFTER               Dependencia de paso.\n  --delay DELAY               Espera previa del paso.\n  --timeout TIMEOUT           Timeout de paso.\n  --on-failure {stop,continue,retry}\n                              Política ante fallo.\n  --cooldown COOLDOWN         Espera mínima entre ejecuciones.\n  --max-attempts MAX_ATTEMPTS\n                              Máximo de intentos.\n  --power-transport {ssh,disabled}\n                              Transporte autorizado para apagar o reiniciar.\n  --power-platform {windows,linux}\n                              Sistema operativo remoto.\n  --power-command ACCIÓN=COMANDO\n                              Plantilla administrada ACCIÓN=COMANDO.\n  --database DATABASE         Element JSON file.\n  --store STORE               Encrypted credential store.\n  --sequences SEQUENCES       Archivo transaccional de secuencias.",
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
          "description": "DeviceId, alias, name, MAC, current or historical IP.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Include general events from the entire LAN.",
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
          "description": "In the interactive CLI, show session commands.",
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
          "description": "Limit the query to the current local day.",
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
          "description": "Start date YYYY-MM-DD.",
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
          "description": "End date YYYY-MM-DD.",
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
          "description": "Canonical type; may be repeated.",
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
          "description": "Filter by source.",
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
          "description": "Filter by result.",
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
          "description": "Show errors only.",
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
          "description": "Search safe text.",
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
          "description": "Maximum number of events (1..10000).",
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
          "description": "Descending order.",
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
          "description": "Output format.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP history [-h] [--all] [--commands] [--today] [--from FECHA] [--to FECHA]\n                     [--type TYPES] [--source SOURCE] [--result RESULT] [--errors]\n                     [--search SEARCH] [--limit LIMIT] [--reverse] [--format {table,json,csv}]\n                     [selector]",
      "details": "Usage: LANIP history [-h] [--all] [--commands] [--today] [--from FECHA] [--to FECHA]\n                     [--type TYPES] [--source SOURCE] [--result RESULT] [--errors]\n                     [--search SEARCH] [--limit LIMIT] [--reverse] [--format {table,json,csv}]\n                     [selector]\n\nArguments:\n  selector                   DeviceId, alias, name, MAC, current or historical IP.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --all                      Include general events from the entire LAN.\n  --commands                 In the interactive CLI, show session commands.\n  --today                    Limit the query to the current local day.\n  --from FECHA               Start date YYYY-MM-DD.\n  --to FECHA                 End date YYYY-MM-DD.\n  --type TYPES               Canonical type; may be repeated.\n  --source SOURCE            Filter by source.\n  --result RESULT            Filter by result.\n  --errors                   Show errors only.\n  --search SEARCH            Search safe text.\n  --limit LIMIT              Maximum number of events (1..10000).\n  --reverse                  Descending order.\n  --format {table,json,csv}  Output format.",
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
          "description": "attach, detach, status, once, session, incidents, incident, service or foreground.",
          "flags": [],
          "label": "words",
          "metavar": "",
          "required": false
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
          "description": "Runtime session state.",
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
          "description": "Runtime incident state.",
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
          "description": "Monitor singleton lock.",
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
          "description": "Monitor SQLite repository.",
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
          "description": "Custom profiles.",
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
          "description": "Persistent assignments.",
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
          "description": "Monitor profile.",
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
          "description": "Assignment priority.",
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
          "description": "Check ping, arp or port:NN.",
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
          "description": "Presence interval.",
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
          "description": "Discovery interval.",
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
          "description": "Service interval.",
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
          "description": "Deep scan interval.",
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
          "description": "Profile workers.",
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
          "description": "Profile timeout.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP monitor [-h] [--project PROJECT] [--permanent] [--duration DURATION]\n                     [--mode {permanent,temporary,diagnostic,once}]\n                     [--authority {observe,operate,administer}] [--json] [--yes]\n                     [--interval INTERVAL] [--every EVERY] [--group GROUP]\n                     [--type {presence,services,ports,identity,smb,full}] [--fast] [--unknown]\n                     [--follow] [--sessions SESSIONS] [--incidents-store INCIDENTS_STORE]\n                     [--lock LOCK] [--monitor-db MONITOR_DB] [--profiles PROFILES]\n                     [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n                     [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n                     [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP]\n                     [--workers WORKERS] [--timeout TIMEOUT]\n                     [words ...]",
      "details": "Usage: LANIP monitor [-h] [--project PROJECT] [--permanent] [--duration DURATION]\n                     [--mode {permanent,temporary,diagnostic,once}]\n                     [--authority {observe,operate,administer}] [--json] [--yes]\n                     [--interval INTERVAL] [--every EVERY] [--group GROUP]\n                     [--type {presence,services,ports,identity,smb,full}] [--fast] [--unknown]\n                     [--follow] [--sessions SESSIONS] [--incidents-store INCIDENTS_STORE]\n                     [--lock LOCK] [--monitor-db MONITOR_DB] [--profiles PROFILES]\n                     [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n                     [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n                     [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP]\n                     [--workers WORKERS] [--timeout TIMEOUT]\n                     [words ...]\n\nArguments:\n  words                       attach, detach, status, once, session, incidents, incident, service\n                              or foreground.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --project PROJECT           Opción operativa del monitor.\n  --permanent                 Opción operativa del monitor.\n  --duration DURATION         Opción operativa del monitor.\n  --mode {permanent,temporary,diagnostic,once}\n                              Opción operativa del monitor.\n  --authority {observe,operate,administer}\n                              Opción operativa del monitor.\n  --json                      Opción operativa del monitor.\n  --yes                       Opción operativa del monitor.\n  --interval INTERVAL         Opción operativa del monitor.\n  --every EVERY               Opción operativa del monitor.\n  --group GROUP               Opción operativa del monitor.\n  --type {presence,services,ports,identity,smb,full}\n                              Opción operativa del monitor.\n  --fast                      Opción operativa del monitor.\n  --unknown                   Opción operativa del monitor.\n  --follow                    Opción operativa del monitor.\n  --sessions SESSIONS         Runtime session state.\n  --incidents-store INCIDENTS_STORE\n                              Runtime incident state.\n  --lock LOCK                 Monitor singleton lock.\n  --monitor-db MONITOR_DB     Monitor SQLite repository.\n  --profiles PROFILES         Custom profiles.\n  --assignments-store ASSIGNMENTS_STORE\n                              Persistent assignments.\n  --profile PROFILE           Monitor profile.\n  --priority {low,normal,high,critical}\n                              Assignment priority.\n  --check CHECK               Check ping, arp or port:NN.\n  --presence PRESENCE         Presence interval.\n  --discovery DISCOVERY       Discovery interval.\n  --services SERVICES         Service interval.\n  --deep DEEP                 Deep scan interval.\n  --workers WORKERS           Profile workers.\n  --timeout TIMEOUT           Profile timeout.",
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
          "description": "init, status, enable, disable, configure, user, role, session, web or certificate.",
          "flags": [],
          "label": "words",
          "metavar": "",
          "required": false
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
          "description": "Separate user credentials from the persistent service credentials.",
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
          "description": "Separate remote configuration.",
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
          "description": "Remote user store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP access [-h] [--bind BIND] [--cidr CIDR] [--port PORT] [--password-auth {on,off}]\n                    [--role ROLE] [--ssh-key SSH_KEY] [--expires EXPIRES]\n                    [--permission PERMISSION] [--certificate CERTIFICATE]\n                    [--private-key PRIVATE_KEY] [--common-name COMMON_NAME] [--yes] [--json]\n                    [--scope {user,service}] [--config CONFIG] [--users USERS]\n                    [words ...]",
      "details": "Usage: LANIP access [-h] [--bind BIND] [--cidr CIDR] [--port PORT] [--password-auth {on,off}]\n                    [--role ROLE] [--ssh-key SSH_KEY] [--expires EXPIRES]\n                    [--permission PERMISSION] [--certificate CERTIFICATE]\n                    [--private-key PRIVATE_KEY] [--common-name COMMON_NAME] [--yes] [--json]\n                    [--scope {user,service}] [--config CONFIG] [--users USERS]\n                    [words ...]\n\nArguments:\n  words                      init, status, enable, disable, configure, user, role, session, web or\n                             certificate.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --bind BIND                Opción de acceso remoto.\n  --cidr CIDR                Opción de acceso remoto.\n  --port PORT                Opción de acceso remoto.\n  --password-auth {on,off}   Opción de acceso remoto.\n  --role ROLE                Opción de acceso remoto.\n  --ssh-key SSH_KEY          Opción de acceso remoto.\n  --expires EXPIRES          Opción de acceso remoto.\n  --permission PERMISSION    Opción de acceso remoto.\n  --certificate CERTIFICATE  Opción de acceso remoto.\n  --private-key PRIVATE_KEY  Opción de acceso remoto.\n  --common-name COMMON_NAME  Opción de acceso remoto.\n  --yes                      Opción de acceso remoto.\n  --json                     Opción de acceso remoto.\n  --scope {user,service}     Separate user credentials from the persistent service credentials.\n  --config CONFIG            Separate remote configuration.\n  --users USERS              Remote user store.",
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
          "description": "Server/device (no action defaults to info).",
          "flags": [],
          "label": "name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "scan, info, shares, open, printers, workgroups, connect, disconnect, status or printer.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Shared folder or printer.",
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
          "description": "Printer action.",
          "flags": [],
          "label": "resource_action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Examine the entire LANCTL inventory.",
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
          "description": "Limit the scan to a LANCTL group.",
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
          "description": "TCP probe timeout.",
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
          "description": "Maximum number of concurrent probes.",
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
          "description": "Do not load associated credentials.",
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
          "description": "Include administrative and special resources.",
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
          "description": "Show the plan without authenticating, opening or changing anything.",
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
          "description": "Confirm a printer connection.",
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
          "description": "Output structured JSON.",
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
          "description": "Inventory JSON file.",
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
          "description": "DPAPI credential store.",
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
          "description": "Plugin observations directory.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP smb [-h] [--network] [--group GROUP] [--timeout TIMEOUT] [--workers WORKERS]\n                 [--anonymous] [--include-system] [--dry-run] [--yes] [--json]\n                 [--database DATABASE] [--store STORE] [--storage STORAGE]\n                 [name] [action] [resource] [{open,queue,connect}]",
      "details": "Usage: LANIP smb [-h] [--network] [--group GROUP] [--timeout TIMEOUT] [--workers WORKERS]\n                 [--anonymous] [--include-system] [--dry-run] [--yes] [--json]\n                 [--database DATABASE] [--store STORE] [--storage STORAGE]\n                 [name] [action] [resource] [{open,queue,connect}]\n\nArguments:\n  name                  Server/device (no action defaults to info).\n  action                scan, info, shares, open, printers, workgroups, connect, disconnect,\n                        status or printer.\n  resource              Shared folder or printer.\n  {open,queue,connect}  Printer action.\n\nOptions:\n  -h, --help            Show this help and exit.\n  --network             Examine the entire LANCTL inventory.\n  --group GROUP         Limit the scan to a LANCTL group.\n  --timeout TIMEOUT     TCP probe timeout.\n  --workers WORKERS     Maximum number of concurrent probes.\n  --anonymous           Do not load associated credentials.\n  --include-system      Include administrative and special resources.\n  --dry-run             Show the plan without authenticating, opening or changing anything.\n  --yes                 Confirm a printer connection.\n  --json                Output structured JSON.\n  --database DATABASE   Inventory JSON file.\n  --store STORE         DPAPI credential store.\n  --storage STORAGE     Plugin observations directory.",
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
          "description": "Element IP, MAC or alias.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Protocol when multiple terminals are available.",
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
          "description": "Use the native SSH client without LANCTL's color layer.",
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
          "description": "Element JSON file.",
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
          "description": "Encrypted credential store.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP terminal [-h] [-p PROTOCOL] [--native] [--database DATABASE] [--store STORE] selector",
      "details": "Usage: LANIP terminal [-h] [-p PROTOCOL] [--native] [--database DATABASE] [--store STORE] selector\n\nArguments:\n  selector                 Element IP, MAC or alias.\n\nOptions:\n  -h, --help               Show this help and exit.\n  -p, --protocol PROTOCOL  Protocol when multiple terminals are available.\n  --native                 Use the native SSH client without LANCTL's color layer.\n  --database DATABASE      Element JSON file.\n  --store STORE            Encrypted credential store.",
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
          "description": "Switch IP, MAC or alias.",
          "flags": [],
          "label": "selector",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Cisco profile that remaps ports.",
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
          "description": "JSON file containing Cisco profiles.",
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
          "description": "Element JSON file.",
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
          "description": "Show the plan only.",
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
          "description": "Confirm changes without asking.",
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
          "description": "Managed Cisco action to plan.",
          "flags": [],
          "label": "arguments",
          "metavar": "COMANDO",
          "required": false
        }
      ],
      "category": "Infraestructura de red",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Managed Cisco commands:\n  show COMMAND\n  port list\n  port label PORT NAME\n  port unlabel PORT\n  port show [PORT] status|description|config|errors|vlan\n  port set [PORT] description|speed|duplex VALUE\n  port enable|disable|reset [PORT]\n  start|stop|reset [PORT]\n  save-config\n  terminal\n\nGlobal options: --profile PROFILE --dry-run --yes\nThis phase uses a simulated adapter and does not connect to the switch.",
      "details": "Usage: LANIP switch [-h] [--profile PROFILE] [--profiles PROFILES] [--database DATABASE]\n                    [--dry-run] [--yes]\n                    selector ...\n\nManaged Cisco commands:\n  show COMMAND\n  port list\n  port label PORT NAME\n  port unlabel PORT\n  port show [PORT] status|description|config|errors|vlan\n  port set [PORT] description|speed|duplex VALUE\n  port enable|disable|reset [PORT]\n  start|stop|reset [PORT]\n  save-config\n  terminal\n\nGlobal options: --profile PROFILE --dry-run --yes\nThis phase uses a simulated adapter and does not connect to the switch.\n\nArguments:\n  selector             Switch IP, MAC or alias.\n  COMANDO              Managed Cisco action to plan.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --profile PROFILE    Cisco profile that remaps ports.\n  --profiles PROFILES  JSON file containing Cisco profiles.\n  --database DATABASE  Element JSON file.\n  --dry-run            Show the plan only.\n  --yes                Confirm changes without asking.",
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
          "description": "Group name.",
          "flags": [],
          "label": "name",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Create the group.",
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
          "description": "Delete the group.",
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
          "description": "Rename the group.",
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
          "description": "Edit its description.",
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
          "description": "Add IP, MAC or alias.",
          "flags": [
            "-add"
          ],
          "label": "-add",
          "metavar": "ELEMENT",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Remove IP, MAC or alias.",
          "flags": [
            "-remove"
          ],
          "label": "-remove",
          "metavar": "ELEMENT",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "List elements belonging to the group.",
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
          "description": "Element JSON file.",
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
          "description": "Group JSON file.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP group [-h] [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENT |\n                   -remove ELEMENT | -list] [--database DATABASE] [--groups GROUPS]\n                   [name]",
      "details": "Usage: LANIP group [-h] [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENT |\n                   -remove ELEMENT | -list] [--database DATABASE] [--groups GROUPS]\n                   [name]\n\nArguments:\n  name                 Group name.\n\nOptions:\n  -h, --help           Show this help and exit.\n  -new                 Create the group.\n  -del                 Delete the group.\n  -rename NUEVO        Rename the group.\n  -description TEXTO   Edit its description.\n  -add ELEMENT         Add IP, MAC or alias.\n  -remove ELEMENT      Remove IP, MAC or alias.\n  -list                List elements belonging to the group.\n  --database DATABASE  Element JSON file.\n  --groups GROUPS      Group JSON file.",
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
      "usage": "LANIP group [-h] [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENT |\n                   -remove ELEMENT | -list] [--database DATABASE] [--groups GROUPS]\n                   [name]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "IP, MAC or alias.",
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
          "description": "Field or action to edit.",
          "flags": [],
          "label": "action",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "New value.",
          "flags": [],
          "label": "values",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Add a new element using its MAC address.",
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
          "description": "Assign NAME to the specified element.",
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
          "description": "Assign an IPv4 address.",
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
          "description": "Assign ALIAS to the specified element.",
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
          "description": "Assign DESCRIPTION to the specified element.",
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
          "description": "Assign the CNF state.",
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
          "description": "Assign a unique IDF (2-5 letters and 2-5 digits).",
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
          "description": "Add the element to the group.",
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
          "description": "Enable a protocol.",
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
          "description": "Completely delete the specified element.",
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
          "description": "Element JSON file.",
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
          "description": "Group JSON file.",
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
          "description": "Delete without requesting confirmation.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP element [-h] [-add MAC] [-name NEW_NAME] [-ip NEW_IP] [-alias NEW_ALIAS]\n                     [-description NEW_DESCRIPTION] [-cnf NEW_CNF] [-idf NEW_IDF]\n                     [-group NEW_GROUP] [-protocol NEW_PROTOCOL] [-delete] [--database DATABASE]\n                     [--groups GROUPS] [--yes]\n                     [selector]\n                     [{edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}]\n                     [values ...]",
      "details": "Usage: LANIP element [-h] [-add MAC] [-name NEW_NAME] [-ip NEW_IP] [-alias NEW_ALIAS]\n                     [-description NEW_DESCRIPTION] [-cnf NEW_CNF] [-idf NEW_IDF]\n                     [-group NEW_GROUP] [-protocol NEW_PROTOCOL] [-delete] [--database DATABASE]\n                     [--groups GROUPS] [--yes]\n                     [selector]\n                     [{edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}]\n                     [values ...]\n\nArguments:\n  selector                    IP, MAC or alias.\n  {edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}\n                              Field or action to edit.\n  values                      New value.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -add MAC                    Add a new element using its MAC address.\n  -name, --name NEW_NAME      Assign NAME to the specified element.\n  -ip, --ip NEW_IP            Assign an IPv4 address.\n  -alias, --alias NEW_ALIAS   Assign ALIAS to the specified element.\n  -description, --description NEW_DESCRIPTION\n                              Assign DESCRIPTION to the specified element.\n  -cnf, --cnf NEW_CNF         Assign the CNF state.\n  -idf, --idf NEW_IDF         Assign a unique IDF (2-5 letters and 2-5 digits).\n  -group, --group NEW_GROUP   Add the element to the group.\n  -protocol, --protocol NEW_PROTOCOL\n                              Enable a protocol.\n  -delete, --delete           Completely delete the specified element.\n  --database DATABASE         Element JSON file.\n  --groups GROUPS             Group JSON file.\n  --yes                       Delete without requesting confirmation.",
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
        "import-physical",
        "info",
        "verify",
        "use",
        "list"
      ],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project [-h] ACCIÓN ...",
      "details": "Usage: LANIP project [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    status           Show the active project.\n    create           Create an empty VLF project by default.\n    update           Update active data while preserving supplementary information.\n    save             Manually save the active VLF project.\n    import-physical  Copy a historical IDF database into the active empty physical project.\n    info             Show project metadata.\n    verify           Check hashes, structure and SQLite.\n    use              Select the VLF project that receives the audit.\n    list             List internal contents without extracting them.\n\nOptions:\n  -h, --help         Show this help and exit.",
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
          "description": "Return JSON.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project status [-h] [--json]",
      "details": "Usage: LANIP project status [-h] [--json]\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Return JSON.",
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
          "description": "Output file; .vlf is appended if missing.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Human-readable project name.",
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
          "description": "General description.",
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
          "description": "Project author.",
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
          "description": "Human-readable LAN name.",
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
          "description": "Physical location.",
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
          "description": "Company or organization.",
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
          "description": "Person responsible for the LAN.",
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
          "description": "Create the project by explicitly copying the active inventory and groups.",
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
          "description": "Overwrite an existing VLF.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project create [-h] [--name NAME] [--description DESCRIPTION] [--author AUTHOR]\n                            [--lan-name LAN_NAME] [--location LOCATION] [--company COMPANY]\n                            [--responsible RESPONSIBLE] [--clone-current] [--force]\n                            file",
      "details": "Usage: LANIP project create [-h] [--name NAME] [--description DESCRIPTION] [--author AUTHOR]\n                            [--lan-name LAN_NAME] [--location LOCATION] [--company COMPANY]\n                            [--responsible RESPONSIBLE] [--clone-current] [--force]\n                            file\n\nArguments:\n  file                       Output file; .vlf is appended if missing.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --name NAME                Human-readable project name.\n  --description DESCRIPTION  General description.\n  --author AUTHOR            Project author.\n  --lan-name LAN_NAME        Human-readable LAN name.\n  --location LOCATION        Physical location.\n  --company COMPANY          Company or organization.\n  --responsible RESPONSIBLE  Person responsible for the LAN.\n  --clone-current            Create the project by explicitly copying the active inventory and\n                             groups.\n  --force                    Overwrite an existing VLF.",
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
          "description": "Existing VLF project.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project update [-h] file",
      "details": "Usage: LANIP project update [-h] file\n\nArguments:\n  file        Existing VLF project.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Source IDF .db database; preserved unchanged.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project import-physical [-h] file",
      "details": "Usage: LANIP project import-physical [-h] file\n\nArguments:\n  file        Source IDF .db database; preserved unchanged.\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "VLF.md",
        "STORAGE.md",
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanip project import-physical --help"
      ],
      "group": "LANIP project",
      "id": "command-lanip-project-import-physical",
      "kind": "command",
      "launcher": "LANIP",
      "name": "import-physical",
      "path": [
        "LANIP",
        "project",
        "import-physical"
      ],
      "title": "LANIP project import-physical",
      "usage": "LANIP project import-physical [-h] file"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "VLF project.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Return JSON.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project info [-h] [--json] file",
      "details": "Usage: LANIP project info [-h] [--json] file\n\nArguments:\n  file        VLF project.\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Return JSON.",
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
          "description": "VLF project.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Return JSON.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project verify [-h] [--json] file",
      "details": "Usage: LANIP project verify [-h] [--json] file\n\nArguments:\n  file        VLF project.\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Return JSON.",
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
          "description": "Existing VLF project.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project use [-h] file",
      "details": "Usage: LANIP project use [-h] file\n\nArguments:\n  file        Existing VLF project.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "VLF project.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Proyectos",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP project list [-h] file",
      "details": "Usage: LANIP project list [-h] file\n\nArguments:\n  file        VLF project.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin [-h] ACCIÓN ...",
      "details": "Usage: LANIP plugin [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    list         List installed plugins.\n    catalog      Show the bundled official catalog.\n    info         Show manifest, permissions and state.\n    install      Verify and install a disabled .lcp package.\n    enable       Grant permissions and enable a plugin.\n    disable      Desactiva el complemento.\n    reload       Recarga un complemento activo.\n    uninstall    Desinstala el complemento.\n    verify       Verify a .lcp or installed plugin.\n    permissions  Show requested and granted permissions.\n    revoke       Revoke a plugin's permissions and trust.\n    publisher    Manage Ed25519 fingerprints of trusted LCP publishers.\n    extensions   List extensions for CLI, TUI and the future GUI.\n    pack         Build a .lcp package from a directory.\n\nOptions:\n  -h, --help     Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Stable plugin identifier.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin info [-h] plugin_id",
      "details": "Usage: LANIP plugin info [-h] plugin_id\n\nArguments:\n  plugin_id   Stable plugin identifier.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Package file with the .lcp extension.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin install [-h] file",
      "details": "Usage: LANIP plugin install [-h] file\n\nArguments:\n  file        Package file with the .lcp extension.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Installed plugin identifier.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Specific permissions to grant.",
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
          "description": "Grant all requested permissions.",
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
          "description": "Authorize trusted code within the process.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin enable [-h] [--grant [PERMISO ...]] [--grant-all] [--trust] plugin_id",
      "details": "Usage: LANIP plugin enable [-h] [--grant [PERMISO ...]] [--grant-all] [--trust] plugin_id\n\nArguments:\n  plugin_id              Installed plugin identifier.\n\nOptions:\n  -h, --help             Show this help and exit.\n  --grant [PERMISO ...]  Specific permissions to grant.\n  --grant-all            Grant all requested permissions.\n  --trust                Authorize trusted code within the process.",
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
          "description": "Installed plugin identifier.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin disable [-h] plugin_id",
      "details": "Usage: LANIP plugin disable [-h] plugin_id\n\nArguments:\n  plugin_id   Installed plugin identifier.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Installed plugin identifier.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin reload [-h] plugin_id",
      "details": "Usage: LANIP plugin reload [-h] plugin_id\n\nArguments:\n  plugin_id   Installed plugin identifier.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Installed plugin identifier.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin uninstall [-h] plugin_id",
      "details": "Usage: LANIP plugin uninstall [-h] plugin_id\n\nArguments:\n  plugin_id   Installed plugin identifier.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Installed identifier or path to a .lcp file.",
          "flags": [],
          "label": "target",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin verify [-h] target",
      "details": "Usage: LANIP plugin verify [-h] target\n\nArguments:\n  target      Installed identifier or path to a .lcp file.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Installed plugin identifier.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin permissions [-h] plugin_id",
      "details": "Usage: LANIP plugin permissions [-h] plugin_id\n\nArguments:\n  plugin_id   Installed plugin identifier.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Installed plugin identifier.",
          "flags": [],
          "label": "plugin_id",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Leave empty to revoke all permissions.",
          "flags": [],
          "label": "permissions",
          "metavar": "PERMISO",
          "required": false
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin revoke [-h] plugin_id [PERMISO ...]",
      "details": "Usage: LANIP plugin revoke [-h] plugin_id [PERMISO ...]\n\nArguments:\n  plugin_id   Installed plugin identifier.\n  PERMISO     Leave empty to revoke all permissions.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin publisher [-h] ACCIÓN ...",
      "details": "Usage: LANIP plugin publisher [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    list      List trusted publishers.\n    trust     Trust the signature contained in an LCP package.\n    revoke    Revoke a publisher fingerprint.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Signed and verified .lcp package.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Descriptive publisher name.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin publisher trust [-h] [--name NAME] file",
      "details": "Usage: LANIP plugin publisher trust [-h] [--name NAME] file\n\nArguments:\n  file         Signed and verified .lcp package.\n\nOptions:\n  -h, --help   Show this help and exit.\n  --name NAME  Descriptive publisher name.",
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
          "description": "Full Ed25519 SHA-256 fingerprint.",
          "flags": [],
          "label": "fingerprint",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Plugins y expansiones",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin publisher revoke [-h] fingerprint",
      "details": "Usage: LANIP plugin publisher revoke [-h] fingerprint\n\nArguments:\n  fingerprint  Full Ed25519 SHA-256 fingerprint.\n\nOptions:\n  -h, --help   Show this help and exit.",
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
          "description": "Filter by unified extension type.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin extensions [-h] [--type TYPE]",
      "details": "Usage: LANIP plugin extensions [-h] [--type TYPE]\n\nOptions:\n  -h, --help   Show this help and exit.\n  --type TYPE  Filter by unified extension type.",
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
          "description": "Source directory containing plugin.info.",
          "flags": [],
          "label": "directory",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Output .lcp file.",
          "flags": [],
          "label": "output",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Overwrite the existing output package.",
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
          "description": "Ed25519 PEM private key for signing the LCP.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP plugin pack [-h] [--force] [--signing-key SIGNING_KEY] directory output",
      "details": "Usage: LANIP plugin pack [-h] [--force] [--signing-key SIGNING_KEY] directory output\n\nArguments:\n  directory                  Source directory containing plugin.info.\n  output                     Output .lcp file.\n\nOptions:\n  -h, --help                 Show this help and exit.\n  --force                    Overwrite the existing output package.\n  --signing-key SIGNING_KEY  Ed25519 PEM private key for signing the LCP.",
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Stable error identifier.",
          "flags": [],
          "label": "error_id",
          "metavar": "0eXXXXXXXX",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Output the result as JSON.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP error [-h] [--json] 0eXXXXXXXX",
      "details": "Usage: LANIP error [-h] [--json] 0eXXXXXXXX\n\nArguments:\n  0eXXXXXXXX  Stable error identifier.\n\nOptions:\n  -h, --help  Show this help and exit.\n  --json      Output the result as JSON.",
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
          "description": "Validate configured stores.",
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
          "description": "Export data with verifiable hashes.",
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
          "description": "Verify an export without importing it.",
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
          "description": "Import verified data.",
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
          "description": "Restore a validated store backup.",
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
          "description": "Store to restore.",
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
          "description": "Confirm data replacement.",
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
          "description": "Output diagnostics as JSON.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP database [-h] (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip |\n                      --import ARCHIVO.zip | --restore ARCHIVO.bak)\n                      [--target {database,groups,physical}] [--yes] [--json]",
      "details": "Usage: LANIP database [-h] (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip |\n                      --import ARCHIVO.zip | --restore ARCHIVO.bak)\n                      [--target {database,groups,physical}] [--yes] [--json]\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --diagnose                  Validate configured stores.\n  --export ARCHIVO.zip        Export data with verifiable hashes.\n  --verify ARCHIVO.zip        Verify an export without importing it.\n  --import ARCHIVO.zip        Import verified data.\n  --restore ARCHIVO.bak       Restore a validated store backup.\n  --target {database,groups,physical}\n                              Store to restore.\n  --yes                       Confirm data replacement.\n  --json                      Output diagnostics as JSON.",
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
      "usage": "LANIP database [-h] (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip |\n                      --import ARCHIVO.zip | --restore ARCHIVO.bak)\n                      [--target {database,groups,physical}] [--yes] [--json]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": "LANCTL-demo",
          "description": "Directory for the project and report.",
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
          "description": "Replace a previous demo.",
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
          "description": "Exported report format.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Create inventory, VLF project, evidence, monitoring and a demonstration report isolated from user data.",
      "details": "Usage: LANIP demo [-h] [--output DIRECTORIO] [--force] [--format {json,html,all}]\n\nCreate inventory, VLF project, evidence, monitoring and a demonstration report isolated from user data.\n\nOptions:\n  -h, --help                Show this help and exit.\n  --output DIRECTORIO       Directory for the project and report.\n  --force                   Replace a previous demo.\n  --format {json,html,all}  Exported report format.",
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
          "description": "Open LANWIRE in a separate console even when arguments are provided.",
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
          "description": "Show the common LANWIRE version and exit.",
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
          "description": "Select an alternative physical IDF database.",
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
          "description": "Open the LANWIRE TUI.",
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
          "description": "Open the LANWIRE interactive console.",
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
          "description": "Arguments forwarded to LANWIRE, for example: list.",
          "flags": [],
          "label": "arguments",
          "metavar": "ARGUMENTO",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lanwire [-h] [--new-window] [--version] [--database ARCHIVO.db] [-tui | --cli] ...",
      "details": "Usage: LANIP lanwire [-h] [--new-window] [--version] [--database ARCHIVO.db] [-tui | --cli] ...\n\nArguments:\n  ARGUMENTO              Arguments forwarded to LANWIRE, for example: list.\n\nOptions:\n  -h, --help             Show this help and exit.\n  --new-window           Open LANWIRE in a separate console even when arguments are provided.\n  --version              Show the common LANWIRE version and exit.\n  --database ARCHIVO.db  Select an alternative physical IDF database.\n  -tui, --tui            Open the LANWIRE TUI.\n  --cli                  Open the LANWIRE interactive console.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab [-h] ACCIÓN ...",
      "details": "Usage: LANIP lab [-h] ACCIÓN ...\n\nArguments:\n  ACCIÓN\n    generate  Generate a reproducible scenario.\n    list      Lista escenarios.\n    status    Muestra el escenario activo.\n    stop      Desactiva el proveedor simulado.\n    start     Explicitly activate a virtual scenario.\n    validate  Validate a scenario.\n    export    Export a scenario.\n    import    Import a JSON scenario.\n    network   Manually create a virtual network.\n    device    Edit simulated devices.\n    evolve    Advance the clock and apply pending events.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Scenario name.",
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
          "description": "Virtual IPv4 network.",
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
          "description": "Device profile.",
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
          "description": "Number of devices.",
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
          "description": "Reproducible seed.",
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
          "description": "Active percentage.",
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
          "description": "DHCP percentage.",
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
          "description": "Scenario evolution.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab generate [-h] [--name NAME] [--cidr CIDR]\n                          [--profile {home,office,datacenter,industrial,chaotic}]\n                          [--devices DEVICES] [--seed SEED] [--active-percent ACTIVE_PERCENT]\n                          [--dhcp-percent DHCP_PERCENT] [--type {snapshot,timeline,chaos}]",
      "details": "Usage: LANIP lab generate [-h] [--name NAME] [--cidr CIDR]\n                          [--profile {home,office,datacenter,industrial,chaotic}]\n                          [--devices DEVICES] [--seed SEED] [--active-percent ACTIVE_PERCENT]\n                          [--dhcp-percent DHCP_PERCENT] [--type {snapshot,timeline,chaos}]\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --name NAME                 Scenario name.\n  --cidr CIDR                 Virtual IPv4 network.\n  --profile {home,office,datacenter,industrial,chaotic}\n                              Device profile.\n  --devices DEVICES           Number of devices.\n  --seed SEED                 Reproducible seed.\n  --active-percent ACTIVE_PERCENT\n                              Active percentage.\n  --dhcp-percent DHCP_PERCENT\n                              DHCP percentage.\n  --type {snapshot,timeline,chaos}\n                              Scenario evolution.",
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Scenario name.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab start [-h] scenario",
      "details": "Usage: LANIP lab start [-h] scenario\n\nArguments:\n  scenario    Scenario name.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Scenario name.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab validate [-h] scenario",
      "details": "Usage: LANIP lab validate [-h] scenario\n\nArguments:\n  scenario    Scenario name.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Scenario name.",
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
          "description": "Output format.",
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
          "description": "Destination file; stdout if omitted.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab export [-h] [--format {json,csv}] [--output OUTPUT] scenario",
      "details": "Usage: LANIP lab export [-h] [--format {json,csv}] [--output OUTPUT] scenario\n\nArguments:\n  scenario             Scenario name.\n\nOptions:\n  -h, --help           Show this help and exit.\n  --format {json,csv}  Output format.\n  --output OUTPUT      Destination file; stdout if omitted.",
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
          "description": "JSON file.",
          "flags": [],
          "label": "file",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab import [-h] file",
      "details": "Usage: LANIP lab import [-h] file\n\nArguments:\n  file        JSON file.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab network [-h] {create} ...",
      "details": "Usage: LANIP lab network [-h] {create} ...\n\nArguments:\n  {create}\n    create    Create an empty scenario.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Scenario name.",
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
          "description": "Virtual CIDR.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab network create [-h] --name NAME [--cidr CIDR]",
      "details": "Usage: LANIP lab network create [-h] --name NAME [--cidr CIDR]\n\nOptions:\n  -h, --help   Show this help and exit.\n  --name NAME  Scenario name.\n  --cidr CIDR  Virtual CIDR.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab device [-h] {add,delete} ...",
      "details": "Usage: LANIP lab device [-h] {add,delete} ...\n\nArguments:\n  {add,delete}\n    add         Add a device.\n    delete      Delete a device.\n\nOptions:\n  -h, --help    Show this help and exit.",
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
          "description": "Scenario.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Simulated IPv4.",
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
          "description": "Simulated MAC.",
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
          "description": "Name.",
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
          "description": "Create it inactive.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab device add [-h] --ip IP --mac MAC [--alias ALIAS] [--name NAME] [--inactive]\n                            scenario",
      "details": "Usage: LANIP lab device add [-h] --ip IP --mac MAC [--alias ALIAS] [--name NAME] [--inactive]\n                            scenario\n\nArguments:\n  scenario       Scenario.\n\nOptions:\n  -h, --help     Show this help and exit.\n  --ip IP        Simulated IPv4.\n  --mac MAC      Simulated MAC.\n  --alias ALIAS  Alias.\n  --name NAME    Name.\n  --inactive     Create it inactive.",
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
          "description": "Scenario.",
          "flags": [],
          "label": "scenario",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "ID, IP, MAC or alias.",
          "flags": [],
          "label": "device",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Laboratorio virtual",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab device delete [-h] scenario device",
      "details": "Usage: LANIP lab device delete [-h] scenario device\n\nArguments:\n  scenario    Scenario.\n  device      ID, IP, MAC or alias.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Virtual seconds.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANIP lab evolve [-h] --seconds SECONDS",
      "details": "Usage: LANIP lab evolve [-h] --seconds SECONDS\n\nOptions:\n  -h, --help         Show this help and exit.\n  --seconds SECONDS  Virtual seconds.",
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
          "description": "Show the common suite version and exit.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/physical/idf.db",
          "description": "Physical IDF database; defaults to physical/idf.db in the shared root.",
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
          "description": "Open the desktop graphical interface.",
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
          "description": "Open the full-screen interface.",
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
          "description": "Open the LANWIRE interactive console.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Physical management, IDF, wiring and topology for the LANCTL suite.",
      "details": "Usage: LANWIRE [-h] [--version] [--database ARCHIVO.db] [--gui | -tui | --cli] COMANDO ...\n\nPhysical management, IDF, wiring and topology for the LANCTL suite.\n\nArguments:\n  COMANDO\n    tui                  Open the full-screen interface.\n    cli                  Open the interactive console.\n    help                 Show LANWIRE command help.\n    list (ls)            List identifiers.\n    seed                 Load the initial test topology.\n    show                 Show an identifier.\n    add                  Generate the next IDF.\n    idf                  Create identifiers with a complete physical profile.\n    reserve              Reserve an IDF.\n    element              Query or update an element's data and ports.\n    delete (del)         Delete an IDF.\n    graph (map)          Show the physical topology.\n    prefix               Manage letter sets.\n\nOptions:\n  -h, --help             Show this help and exit.\n  --version              Show the common suite version and exit.\n  --database ARCHIVO.db  Physical IDF database; defaults to physical/idf.db in the shared root.\n  --gui                  Open the desktop graphical interface.\n  -tui, --tui            Open the full-screen interface.\n  --cli, -cli            Open the LANWIRE interactive console.",
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
      "usage": "LANWIRE [-h] [--version] [--database ARCHIVO.db] [--gui | -tui | --cli] COMANDO ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Filter by IDF prefix.",
          "flags": [],
          "label": "prefix",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE list [-h] [prefix]",
      "details": "Usage: LANWIRE list [-h] [prefix]\n\nArguments:\n  prefix      Filter by IDF prefix.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Physical identifier to query.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE show [-h] idf",
      "details": "Usage: LANWIRE show [-h] idf\n\nArguments:\n  idf         Physical identifier to query.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Physical element type prefix.",
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
          "description": "Number of counter digits (2 to 5).",
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
          "description": "Create N consecutive IDFs.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE add [-h] [--digits {2,3,4,5}] [-more N] prefix",
      "details": "Usage: LANWIRE add [-h] [--digits {2,3,4,5}] [-more N] prefix\n\nArguments:\n  prefix              Physical element type prefix.\n\nOptions:\n  -h, --help          Show this help and exit.\n  --digits {2,3,4,5}  Number of counter digits (2 to 5).\n  -more, --more N     Create N consecutive IDFs.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE idf [-h] {list,types,show,edit,delete,del,new,add} ...",
      "details": "Usage: LANWIRE idf [-h] {list,types,show,edit,delete,del,new,add} ...\n\nArguments:\n  {list,types,show,edit,delete,del,new,add}\n    list                      List prefixes or the IDFs of a prefix.\n    types                     List available physical profiles.\n    show                      Query a prefix or IDF.\n    edit                      Edit a prefix or IDF data.\n    delete (del)              Delete an IDF.\n    new                       Assign a physical profile to a prefix.\n    add                       Create an IDF using the assigned prefix profile.\n\nOptions:\n  -h, --help                  Show this help and exit.",
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
          "description": "Prefix whose elements are listed.",
          "flags": [],
          "label": "prefix",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE idf list [-h] [prefix]",
      "details": "Usage: LANWIRE idf list [-h] [prefix]\n\nArguments:\n  prefix      Prefix whose elements are listed.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Specific prefix or IDF.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE idf show [-h] code",
      "details": "Usage: LANWIRE idf show [-h] code\n\nArguments:\n  code        Specific prefix or IDF.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Specific prefix or IDF.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "IDF data.",
          "flags": [],
          "label": "data",
          "metavar": "CAMPO=VALOR",
          "required": false
        },
        {
          "choices": [],
          "default": "",
          "description": "New prefix profile.",
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
          "description": "Prefix name.",
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
          "description": "Prefix alias.",
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
          "description": "Prefix description.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE idf edit [-h] [-type ELEMENT_TYPE] [-name NAME] [-alias ALIAS]\n                        [-description DESCRIPTION]\n                        code [CAMPO=VALOR ...]",
      "details": "Usage: LANWIRE idf edit [-h] [-type ELEMENT_TYPE] [-name NAME] [-alias ALIAS]\n                        [-description DESCRIPTION]\n                        code [CAMPO=VALOR ...]\n\nArguments:\n  code                      Specific prefix or IDF.\n  CAMPO=VALOR               IDF data.\n\nOptions:\n  -h, --help                Show this help and exit.\n  -type ELEMENT_TYPE        New prefix profile.\n  -name NAME                Prefix name.\n  -alias ALIAS              Prefix alias.\n  -description DESCRIPTION  Prefix description.",
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
          "description": "Specific IDF; does not delete prefixes.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE idf delete [-h] code",
      "details": "Usage: LANWIRE idf delete [-h] code\n\nArguments:\n  code        Specific IDF; does not delete prefixes.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Prefix for new or exact IDF for add.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Record name.",
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
          "description": "Optional alias.",
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
          "description": "Optional description.",
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
          "description": "Physical profile.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE idf new [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION]\n                       -type ELEMENT_TYPE\n                       code",
      "details": "Usage: LANWIRE idf new [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION]\n                       -type ELEMENT_TYPE\n                       code\n\nArguments:\n  code                        Prefix for new or exact IDF for add.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -name NAME                  Record name.\n  -alias ALIAS                Optional alias.\n  -description, -descriptionn DESCRIPTION\n                              Optional description.\n  -type ELEMENT_TYPE          Physical profile.",
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
      "usage": "LANWIRE idf new [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION]\n                       -type ELEMENT_TYPE\n                       code"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Prefix for new or exact IDF for add.",
          "flags": [],
          "label": "code",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Record name.",
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
          "description": "Optional alias.",
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
          "description": "Optional description.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE idf add [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] code",
      "details": "Usage: LANWIRE idf add [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] code\n\nArguments:\n  code                        Prefix for new or exact IDF for add.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  -name NAME                  Record name.\n  -alias ALIAS                Optional alias.\n  -description, -descriptionn DESCRIPTION\n                              Optional description.",
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
          "description": "Exact IDF to reserve.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Optional initial data.",
          "flags": [],
          "label": "data",
          "metavar": "CLAVE=VALOR",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE reserve [-h] idf [CLAVE=VALOR ...]",
      "details": "Usage: LANWIRE reserve [-h] idf [CLAVE=VALOR ...]\n\nArguments:\n  idf          Exact IDF to reserve.\n  CLAVE=VALOR  Optional initial data.\n\nOptions:\n  -h, --help   Show this help and exit.",
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
          "description": "IDF to query or update.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Physical fields to modify.",
          "flags": [],
          "label": "data",
          "metavar": "CAMPO=VALOR",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE element [-h] idf [CAMPO=VALOR ...]",
      "details": "Usage: LANWIRE element [-h] idf [CAMPO=VALOR ...]\n\nArguments:\n  idf          IDF to query or update.\n  CAMPO=VALOR  Physical fields to modify.\n\nOptions:\n  -h, --help   Show this help and exit.",
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
          "description": "IDF to delete.",
          "flags": [],
          "label": "idf",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE delete [-h] idf",
      "details": "Usage: LANWIRE delete [-h] idf\n\nArguments:\n  idf         IDF to delete.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE prefix [-h] {list,ls,show,set,delete,del} ...",
      "details": "Usage: LANWIRE prefix [-h] {list,ls,show,set,delete,del} ...\n\nArguments:\n  {list,ls,show,set,delete,del}\n    list (ls)                 List definitions.\n    show                      Show a definition.\n    set                       Create or update a definition.\n    delete (del)              Delete a definition.\n\nOptions:\n  -h, --help                  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Prefix letters.",
          "flags": [],
          "label": "letters",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE prefix show [-h] letters",
      "details": "Usage: LANWIRE prefix show [-h] letters\n\nArguments:\n  letters     Prefix letters.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Prefix letters.",
          "flags": [],
          "label": "letters",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Descriptive type name.",
          "flags": [],
          "label": "name",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Optional description.",
          "flags": [],
          "label": "description",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE prefix set [-h] letters name [description]",
      "details": "Usage: LANWIRE prefix set [-h] letters name [description]\n\nArguments:\n  letters      Prefix letters.\n  name         Descriptive type name.\n  description  Optional description.\n\nOptions:\n  -h, --help   Show this help and exit.",
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
          "description": "Prefix letters to delete.",
          "flags": [],
          "label": "letters",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Cableado y topología",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANWIRE prefix delete [-h] letters",
      "details": "Usage: LANWIRE prefix delete [-h] letters\n\nArguments:\n  letters     Prefix letters to delete.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
          "description": "Show the common suite version and exit.",
          "flags": [
            "--version"
          ],
          "label": "--version",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "data/lc/projects/workspaces/default/physical/idf.db",
          "description": "Shared physical IDF database.",
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
          "description": "Open the desktop graphical interface.",
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
          "description": "Open the full-screen interface.",
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
          "description": "Open the interactive console.",
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
        "dimensions",
        "elements",
        "add-element",
        "element"
      ],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Display racks and their equipment.",
      "details": "Usage: LANRACK [-h] [--version] [--database ARCHIVO.db] [--gui | -tui | --cli]\n               {list,ls,show,dimensions,elements,add-element,element} ...\n\nDisplay racks and their equipment.\n\nArguments:\n  {list,ls,show,dimensions,elements,add-element,element}\n    list (ls)                 List available racks.\n    show                      Show a rack and its occupants.\n    dimensions                Edit the rack height and mounting width.\n    elements                  List all elements, locations and trays.\n    add-element               Create a shared physical element.\n    element                   Edit or relocate an element without changing its links.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --version                   Show the common suite version and exit.\n  --database ARCHIVO.db       Shared physical IDF database.\n  --gui                       Open the desktop graphical interface.\n  -tui, --tui                 Open the full-screen interface.\n  --cli, -cli                 Open the interactive console.",
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
      "usage": "LANRACK [-h] [--version] [--database ARCHIVO.db] [--gui | -tui | --cli]\n               {list,ls,show,dimensions,elements,add-element,element} ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
          "description": "Rack ID or name.",
          "flags": [],
          "label": "rack",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANRACK show [-h] rack",
      "details": "Usage: LANRACK show [-h] rack\n\nArguments:\n  rack        Rack ID or name.\n\nOptions:\n  -h, --help  Show this help and exit.",
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
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Rack ID.",
          "flags": [],
          "label": "rack",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Height from 4 to 52 U.",
          "flags": [
            "--units"
          ],
          "label": "--units",
          "metavar": "",
          "required": true
        },
        {
          "choices": [
            "10",
            "19",
            "21",
            "23"
          ],
          "default": null,
          "description": "Mounting width in inches.",
          "flags": [
            "--width-inches"
          ],
          "label": "--width-inches",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANRACK dimensions [-h] --units UNITS --width-inches {10,19,21,23} rack",
      "details": "Usage: LANRACK dimensions [-h] --units UNITS --width-inches {10,19,21,23} rack\n\nArguments:\n  rack                        Rack ID.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --units UNITS               Height from 4 to 52 U.\n  --width-inches {10,19,21,23}\n                              Mounting width in inches.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanrack dimensions --help"
      ],
      "group": "LANRACK",
      "id": "command-lanrack-dimensions",
      "kind": "command",
      "launcher": "LANRACK",
      "name": "dimensions",
      "path": [
        "LANRACK",
        "dimensions"
      ],
      "title": "LANRACK dimensions",
      "usage": "LANRACK dimensions [-h] --units UNITS --width-inches {10,19,21,23} rack"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANRACK elements [-h]",
      "details": "Usage: LANRACK elements [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanrack elements --help"
      ],
      "group": "LANRACK",
      "id": "command-lanrack-elements",
      "kind": "command",
      "launcher": "LANRACK",
      "name": "elements",
      "path": [
        "LANRACK",
        "elements"
      ],
      "title": "LANRACK elements",
      "usage": "LANRACK elements [-h]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Equipment, panel, outlet or tray profile.",
          "flags": [
            "--kind"
          ],
          "label": "--kind",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "IDF prefix.",
          "flags": [
            "--prefix"
          ],
          "label": "--prefix",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": "",
          "description": "Element name.",
          "flags": [
            "--name"
          ],
          "label": "--name",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANRACK add-element [-h] --kind KIND --prefix PREFIX [--name NAME]",
      "details": "Usage: LANRACK add-element [-h] --kind KIND --prefix PREFIX [--name NAME]\n\nOptions:\n  -h, --help       Show this help and exit.\n  --kind KIND      Equipment, panel, outlet or tray profile.\n  --prefix PREFIX  IDF prefix.\n  --name NAME      Element name.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanrack add-element --help"
      ],
      "group": "LANRACK",
      "id": "command-lanrack-add-element",
      "kind": "command",
      "launcher": "LANRACK",
      "name": "add-element",
      "path": [
        "LANRACK",
        "add-element"
      ],
      "title": "LANRACK add-element",
      "usage": "LANRACK add-element [-h] --kind KIND --prefix PREFIX [--name NAME]"
    },
    {
      "aliases": [],
      "arguments": [
        {
          "choices": [],
          "default": null,
          "description": "Element ID.",
          "flags": [],
          "label": "element",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Element name.",
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
          "description": "Element description.",
          "flags": [
            "--description"
          ],
          "label": "--description",
          "metavar": "",
          "required": false
        },
        {
          "choices": [
            "inside",
            "environment",
            "independent",
            "hosted"
          ],
          "default": null,
          "description": "Physical classification.",
          "flags": [
            "--placement"
          ],
          "label": "--placement",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Destination rack ID.",
          "flags": [
            "--rack"
          ],
          "label": "--rack",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Starting mounting unit.",
          "flags": [
            "--unit"
          ],
          "label": "--unit",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Height occupied by the element.",
          "flags": [
            "--height-u"
          ],
          "label": "--height-u",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": null,
          "description": "Tray housing the device.",
          "flags": [
            "--tray"
          ],
          "label": "--tray",
          "metavar": "",
          "required": false
        }
      ],
      "category": "Racks y salas técnicas",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANRACK element [-h] [--name NAME] [--description DESCRIPTION]\n                       [--placement {inside,environment,independent,hosted}] [--rack RACK]\n                       [--unit UNIT] [--height-u HEIGHT_U] [--tray TRAY]\n                       element",
      "details": "Usage: LANRACK element [-h] [--name NAME] [--description DESCRIPTION]\n                       [--placement {inside,environment,independent,hosted}] [--rack RACK]\n                       [--unit UNIT] [--height-u HEIGHT_U] [--tray TRAY]\n                       element\n\nArguments:\n  element                     Element ID.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --name NAME                 Element name.\n  --description DESCRIPTION   Element description.\n  --placement {inside,environment,independent,hosted}\n                              Physical classification.\n  --rack RACK                 Destination rack ID.\n  --unit UNIT                 Starting mounting unit.\n  --height-u HEIGHT_U         Height occupied by the element.\n  --tray TRAY                 Tray housing the device.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanrack element --help"
      ],
      "group": "LANRACK",
      "id": "command-lanrack-element",
      "kind": "command",
      "launcher": "LANRACK",
      "name": "element",
      "path": [
        "LANRACK",
        "element"
      ],
      "title": "LANRACK element",
      "usage": "LANRACK element [-h] [--name NAME] [--description DESCRIPTION]\n                       [--placement {inside,environment,independent,hosted}] [--rack RACK]\n                       [--unit UNIT] [--height-u HEIGHT_U] [--tray TRAY]\n                       element"
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
          "description": "Show the common suite version and exit.",
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
          "description": "LANCTL element database.",
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
          "description": "Encrypted credential store.",
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
          "description": "Encryption provider; portable prompts for a password.",
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
          "description": "Location; does not change permissions or copy secrets automatically.",
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
          "description": "Project directory for its independent store.",
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
          "description": "Open the desktop graphical interface.",
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
          "description": "Open the full-screen interface.",
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
          "description": "Open the interactive console.",
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
        "remote-setup",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Manage encrypted credentials in the LANCTL environment.",
      "details": "Usage: LANACCESS [-h] [--version] [--database DATABASE] [--store STORE]\n                 [--cipher {auto,dpapi,portable}] [--scope {program,windows,project}]\n                 [--project-dir PROJECT_DIR] [--gui | -tui | --cli]\n                 {remote-setup,list,ls,show,set,delete,del,credential,doctor,settings,protocol,user} ...\n\nManage encrypted credentials in the LANCTL environment.\n\nArguments:\n  {remote-setup,list,ls,show,set,delete,del,credential,doctor,settings,protocol,user}\n    remote-setup              Create the first remote service account on Windows (administrator\n                              required).\n    list (ls)                 List metadata; never secrets.\n    show                      Show credential metadata.\n    set                       Create or update a credential.\n    delete (del)              Delete a credential.\n    credential                Credential management, transport and recovery.\n    doctor                    Check links and permissions without changing data.\n    settings                  Show or select the shared store.\n    protocol                  Store protocol summary.\n    user                      Remote access users; not Windows accounts.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --version                   Show the common suite version and exit.\n  --database DATABASE         LANCTL element database.\n  --store STORE               Encrypted credential store.\n  --cipher {auto,dpapi,portable}\n                              Encryption provider; portable prompts for a password.\n  --scope {program,windows,project}\n                              Location; does not change permissions or copy secrets automatically.\n  --project-dir PROJECT_DIR   Project directory for its independent store.\n  --gui                       Open the desktop graphical interface.\n  -tui, --tui                 Open the full-screen interface.\n  --cli, -cli                 Open the interactive console.",
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
      "usage": "LANACCESS [-h] [--version] [--database DATABASE] [--store STORE]\n                 [--cipher {auto,dpapi,portable}] [--scope {program,windows,project}]\n                 [--project-dir PROJECT_DIR] [--gui | -tui | --cli]\n                 {remote-setup,list,ls,show,set,delete,del,credential,doctor,settings,protocol,user} ..."
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS remote-setup [-h]",
      "details": "Usage: LANACCESS remote-setup [-h]\n\nOptions:\n  -h, --help  Show this help and exit.",
      "docs": [
        "CLI-REFERENCE.md",
        "CLI.md"
      ],
      "examples": [
        "lanaccess remote-setup --help"
      ],
      "group": "LANACCESS",
      "id": "command-lanaccess-remote-setup",
      "kind": "command",
      "launcher": "LANACCESS",
      "name": "remote-setup",
      "path": [
        "LANACCESS",
        "remote-setup"
      ],
      "title": "LANACCESS remote-setup",
      "usage": "LANACCESS remote-setup [-h]"
    },
    {
      "aliases": [],
      "arguments": [],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
          "description": "Credential identifier.",
          "flags": [],
          "label": "credential_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS show [-h] credential_id",
      "details": "Usage: LANACCESS show [-h] credential_id\n\nArguments:\n  credential_id  Credential identifier.\n\nOptions:\n  -h, --help     Show this help and exit.",
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
          "description": "Device IP, MAC, alias or ID.",
          "flags": [],
          "label": "element",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Associated protocol, for example ssh.",
          "flags": [],
          "label": "protocol",
          "metavar": "",
          "required": true
        },
        {
          "choices": [],
          "default": null,
          "description": "Remote username.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS set [-h] --username USERNAME element protocol",
      "details": "Usage: LANACCESS set [-h] --username USERNAME element protocol\n\nArguments:\n  element                     Device IP, MAC, alias or ID.\n  protocol                    Associated protocol, for example ssh.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --username, -user USERNAME  Remote username.",
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
          "description": "Credential identifier.",
          "flags": [],
          "label": "credential_id",
          "metavar": "",
          "required": true
        }
      ],
      "category": "Credenciales y acceso",
      "children": [],
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS delete [-h] credential_id",
      "details": "Usage: LANACCESS delete [-h] credential_id\n\nArguments:\n  credential_id  Credential identifier.\n\nOptions:\n  -h, --help     Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS credential [-h] {list,show,delete,set,export,import,copy,recover} ...",
      "details": "Usage: LANACCESS credential [-h] {list,show,delete,set,export,import,copy,recover} ...\n\nArguments:\n  {list,show,delete,set,export,import,copy,recover}\n    list                      List metadata.\n    show                      show by identifier.\n    delete                    delete by identifier.\n    set                       Save and link a credential.\n    export                    Transport an encrypted store; never plaintext.\n    import                    Transport an encrypted store; never plaintext.\n    copy                      Copy to another store and verify; preserve the source.\n    recover                   Repair missing references; do not delete or overwrite secrets.\n\nOptions:\n  -h, --help                  Show this help and exit.",
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Apply repairs; diagnose only by default.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS credential recover [-h] [--yes]",
      "details": "Usage: LANACCESS credential recover [-h] [--yes]\n\nOptions:\n  -h, --help  Show this help and exit.\n  --yes       Apply repairs; diagnose only by default.",
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
        "verified": "0.3.4-alpha.2"
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
          "description": "Confirm changing the configured store without moving secrets.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS settings [-h] [--yes] [{show,use-store}] [file]",
      "details": "Usage: LANACCESS settings [-h] [--yes] [{show,use-store}] [file]\n\nArguments:\n  {show,use-store}\n  file\n\nOptions:\n  -h, --help        Show this help and exit.\n  --yes             Confirm changing the configured store without moving secrets.",
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
          "description": "Port 1-65535.",
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
          "description": "Protocol driver.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS protocol [-h] [--port PORT] [--driver DRIVER]\n                          [{list,configure}] [element] [protocol]",
      "details": "Usage: LANACCESS protocol [-h] [--port PORT] [--driver DRIVER]\n                          [{list,configure}] [element] [protocol]\n\nArguments:\n  {list,configure}\n  element\n  protocol\n\nOptions:\n  -h, --help        Show this help and exit.\n  --port PORT       Port 1-65535.\n  --driver DRIVER   Protocol driver.",
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
          "description": "Confirm deletion.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "usage: LANACCESS user [-h] [--role {viewer,operator,manager,administrator}] [--yes]\n                      {list,add,enable,disable,delete} [username]",
      "details": "Usage: LANACCESS user [-h] [--role {viewer,operator,manager,administrator}] [--yes]\n                      {list,add,enable,disable,delete} [username]\n\nArguments:\n  {list,add,enable,disable,delete}\n  username\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --role {viewer,operator,manager,administrator}\n  --yes                       Confirm deletion.",
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
          "description": "Show the common suite version and exit.",
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
          "required": false
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
          "description": "Runtime session state.",
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
          "description": "Runtime incident state.",
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
          "description": "Monitor singleton lock.",
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
          "description": "Monitor SQLite repository.",
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
          "description": "Custom profiles.",
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
          "description": "Persistent assignments.",
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
          "description": "Monitor profile.",
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
          "description": "Assignment priority.",
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
          "description": "Check ping, arp or port:NN.",
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
          "description": "Presence interval.",
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
          "description": "Discovery interval.",
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
          "description": "Service interval.",
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
          "description": "Deep scan interval.",
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
          "description": "Profile workers.",
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
          "description": "Profile timeout.",
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
          "description": "Open the desktop graphical interface.",
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
          "description": "Open the command console.",
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
          "description": "Open the tabular event viewer.",
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
          "description": "Log source.",
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
          "description": "Maximum number of events (1-1000).",
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
          "description": "Open logs in another terminal and follow the common log.",
          "flags": [
            "--window"
          ],
          "label": "--window",
          "metavar": "",
          "required": false
        },
        {
          "choices": [],
          "default": "1",
          "description": "Minimum level (1-59); preserve lines without a level.",
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Monitoring, events and incidents for the LANCTL suite.",
      "details": "Usage: LANMON [-h] [--version] [--project PROJECT] [--permanent] [--duration DURATION]\n              [--mode {permanent,temporary,diagnostic,once}]\n              [--authority {observe,operate,administer}] [--json] [--yes] [--interval INTERVAL]\n              [--every EVERY] [--group GROUP] [--type {presence,services,ports,identity,smb,full}]\n              [--fast] [--unknown] [--follow] [--sessions SESSIONS]\n              [--incidents-store INCIDENTS_STORE] [--lock LOCK] [--monitor-db MONITOR_DB]\n              [--profiles PROFILES] [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n              [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n              [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP] [--workers WORKERS]\n              [--timeout TIMEOUT] [--gui | --cli | --tui] [--source {all,program,project}]\n              [--limit LIMIT] [--window] [--level LEVEL]\n              [words ...]\n\nMonitoring, events and incidents for the LANCTL suite.\n\nArguments:\n  words                       logs, events, status, attach, detach, once, session, incidents,\n                              service o foreground.\n\nOptions:\n  -h, --help                  Show this help and exit.\n  --version                   Show the common suite version and exit.\n  --project PROJECT           Opción operativa del monitor.\n  --permanent                 Opción operativa del monitor.\n  --duration DURATION         Opción operativa del monitor.\n  --mode {permanent,temporary,diagnostic,once}\n                              Opción operativa del monitor.\n  --authority {observe,operate,administer}\n                              Opción operativa del monitor.\n  --json                      Opción operativa del monitor.\n  --yes                       Opción operativa del monitor.\n  --interval INTERVAL         Opción operativa del monitor.\n  --every EVERY               Opción operativa del monitor.\n  --group GROUP               Opción operativa del monitor.\n  --type {presence,services,ports,identity,smb,full}\n                              Opción operativa del monitor.\n  --fast                      Opción operativa del monitor.\n  --unknown                   Opción operativa del monitor.\n  --follow                    Opción operativa del monitor.\n  --sessions SESSIONS         Runtime session state.\n  --incidents-store INCIDENTS_STORE\n                              Runtime incident state.\n  --lock LOCK                 Monitor singleton lock.\n  --monitor-db MONITOR_DB     Monitor SQLite repository.\n  --profiles PROFILES         Custom profiles.\n  --assignments-store ASSIGNMENTS_STORE\n                              Persistent assignments.\n  --profile PROFILE           Monitor profile.\n  --priority {low,normal,high,critical}\n                              Assignment priority.\n  --check CHECK               Check ping, arp or port:NN.\n  --presence PRESENCE         Presence interval.\n  --discovery DISCOVERY       Discovery interval.\n  --services SERVICES         Service interval.\n  --deep DEEP                 Deep scan interval.\n  --workers WORKERS           Profile workers.\n  --timeout TIMEOUT           Profile timeout.\n  --gui                       Open the desktop graphical interface.\n  --cli, -cli                 Open the command console.\n  --tui, -tui                 Open the tabular event viewer.\n  --source {all,program,project}\n                              Log source.\n  --limit LIMIT               Maximum number of events (1-1000).\n  --window                    Open logs in another terminal and follow the common log.\n  --level LEVEL               Minimum level (1-59); preserve lines without a level.",
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
      "usage": "LANMON [-h] [--version] [--project PROJECT] [--permanent] [--duration DURATION]\n              [--mode {permanent,temporary,diagnostic,once}]\n              [--authority {observe,operate,administer}] [--json] [--yes] [--interval INTERVAL]\n              [--every EVERY] [--group GROUP] [--type {presence,services,ports,identity,smb,full}]\n              [--fast] [--unknown] [--follow] [--sessions SESSIONS]\n              [--incidents-store INCIDENTS_STORE] [--lock LOCK] [--monitor-db MONITOR_DB]\n              [--profiles PROFILES] [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]\n              [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]\n              [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP] [--workers WORKERS]\n              [--timeout TIMEOUT] [--gui | --cli | --tui] [--source {all,program,project}]\n              [--limit LIMIT] [--window] [--level LEVEL]\n              [words ...]"
    },
    {
      "category": "Proyectos",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Base auditada: `d6b0e7d382a643789942314fd0ea18a103f19a98`, versión `0.3.2-beta.4`. Las correcciones se desarrollan en `codex/audit-corrections` para revisión e integración posterior en `main`. Ninguna rama estable se modifica.",
      "details": "Documento mantenido en docs/AUDIT-CORRECTIONS-2026-10.md.",
      "docs": [
        "AUDIT-CORRECTIONS-2026-10.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-audit-corrections-2026-10",
      "kind": "document",
      "name": "AUDIT-CORRECTIONS-2026-10.md",
      "title": "Correcciones de la auditoría de octubre de 2026",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/AUDIT-CORRECTIONS-2026-10.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Validación y planificación antes de implementar:",
      "details": "Documento mantenido en docs/BACKLOG-VERIFICATION.md.",
      "docs": [
        "BACKLOG-VERIFICATION.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-backlog-verification",
      "kind": "document",
      "name": "BACKLOG-VERIFICATION.md",
      "title": "Comprobación del backlog",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/BACKLOG-VERIFICATION.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "**Preselección solicitada:** tomar el idioma elegido para el asistente en **P105** y preseleccionar automáticamente su equivalente para el programa, cuando esté disponible. Por ejemplo, instalador en inglés → programa en inglés de forma inicial. El usuario puede cambiar esa selección; los dos idiomas son preferencias independientes. Si el equivalente no está disponible, ofrecer inglés como alternativa e indicarlo de forma comprensible.",
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "`lanctl settings` abre el editor por categorías cuando se ejecuta en una terminal interactiva. `lanctl settings --menu` lo abre explícitamente. Con entrada/salida redirigida se conserva la consulta JSON anterior sin preguntas interactivas.",
      "details": "Documento mantenido en docs/CLI-SETTINGS.md.",
      "docs": [
        "CLI-SETTINGS.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-cli-settings",
      "kind": "document",
      "name": "CLI-SETTINGS.md",
      "title": "Configuración completa desde el CLI",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/CLI-SETTINGS.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "LANCTL, LANIP, LANWIRE, LANRACK, LANACCESS y LANMON registran sus ejecuciones en `runtime/coordinator.db`, dentro de la raíz de datos resuelta por el programa. Es un almacén SQLite transaccional con `user_version=1`, no una base de inventario ni un almacén de credenciales. No se versiona en Git.",
      "details": "Documento mantenido en docs/COORDINATION.md.",
      "docs": [
        "COORDINATION.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-coordination",
      "kind": "document",
      "name": "COORDINATION.md",
      "title": "Coordinación local entre launchers",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/COORDINATION.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "El usuario solicita completar los pendientes de interfaz y encarga a AUDITOR los cambios internos. El trabajo continúa en la rama existente experimental-gui, sin publicar, instalar ni modificar la versión durante la integración.",
      "details": "Documento mantenido en docs/GUI-AUDITOR-COORDINATION.md.",
      "docs": [
        "GUI-AUDITOR-COORDINATION.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-gui-auditor-coordination",
      "kind": "document",
      "name": "GUI-AUDITOR-COORDINATION.md",
      "title": "Integración de pendientes GUI y AUDITOR — 17/10/2026",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/GUI-AUDITOR-COORDINATION.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Abrir `gui/launcher-prototypes.html` en el navegador. No requiere servidor ni dependencias externas. Las cuatro vistas se seleccionan en la barra superior; también admiten los fragmentos `#wire`, `#rack`, `#access` y `#mon`.",
      "details": "Documento mantenido en docs/GUI-PROTOTYPES.md.",
      "docs": [
        "GUI-PROTOTYPES.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-gui-prototypes",
      "kind": "document",
      "name": "GUI-PROTOTYPES.md",
      "title": "Prototipos de los launchers pendientes",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/GUI-PROTOTYPES.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
      "title": "Limitaciones conocidas",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/KNOWN-ISSUES.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Inicia `lanctl --gui` (desde fuentes: `python -m lanctl --gui`). La consola habitual `lanctl --cli` y el TUI siguen disponibles. Desde fuentes se necesita el extra `gui`: `pip install -e \".[gui]\"`.",
      "details": "Documento mantenido en docs/LANCTL-GUI.md.",
      "docs": [
        "LANCTL-GUI.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-lanctl-gui",
      "kind": "document",
      "name": "LANCTL-GUI.md",
      "title": "Centro gráfico de LANCTL",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LANCTL-GUI.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Interfaz de escritorio sobre pywebview, HTML/CSS/JavaScript local y los servicios existentes de LANIP. No instala un servidor web ni abre un puerto de acceso remoto. La API remota anterior conserva `GuiApi`; el escritorio utiliza `DesktopApi`.",
      "details": "Documento mantenido en docs/LANIP-GUI.md.",
      "docs": [
        "LANIP-GUI.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-lanip-gui",
      "kind": "document",
      "name": "LANIP-GUI.md",
      "title": "GUI de LANIP",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LANIP-GUI.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Desde LANCTL, pulsa la tarjeta de la aplicación. También se abren directamente:",
      "details": "Documento mantenido en docs/LAUNCHER-GUI.md.",
      "docs": [
        "LAUNCHER-GUI.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-launcher-gui",
      "kind": "document",
      "name": "LAUNCHER-GUI.md",
      "title": "GUI de LANWIRE, LANRACK, LANACCESS y LANMON",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/LAUNCHER-GUI.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Fecha: 27/10/2026. Autorización: ejecutar el plan y las modificaciones sin consultas intermedias; revisar estética después. Las tareas se verifican por comportamiento y contratos, sin certificar exhaustividad por recuento de claves. Se trabaja sobre los cambios locales existentes sin descartarlos.",
      "details": "Documento mantenido en docs/P100-ACTION-PLAN.md.",
      "docs": [
        "P100-ACTION-PLAN.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-p100-action-plan",
      "kind": "document",
      "name": "P100-ACTION-PLAN.md",
      "title": "P100 — Plan de implantación del sistema de idiomas",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/P100-ACTION-PLAN.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "27/10/2026. Se ha ampliado la migración funcional de los seis launchers, sus interfaces existentes y los componentes compartidos. Los catálogos inglés y español tienen **2.470 claves cada uno**. La estética se revisará después. P100 conserva pendiente la certificación de recorridos e instalables nativos Windows/Linux; la auditoría estática no demuestra por sí sola todos los estados posibles del programa ni los textos de plugins externos.",
      "details": "Documento mantenido en docs/P100-PRELIMINARY-REVIEW.md.",
      "docs": [
        "P100-PRELIMINARY-REVIEW.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-p100-preliminary-review",
      "kind": "document",
      "name": "P100-PRELIMINARY-REVIEW.md",
      "title": "P100 — Revisión preliminar de la migración de idiomas",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/P100-PRELIMINARY-REVIEW.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Revisión de fuentes locales del 27/10/2026. No es una migración de idiomas ni una certificación de los ejecutables instalados. Incluye cambios locales existentes; no se han modificado interfaces, catálogos ni datos del usuario.",
      "details": "Documento mantenido en docs/P100-STRING-SCOPE.md.",
      "docs": [
        "P100-STRING-SCOPE.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-p100-string-scope",
      "kind": "document",
      "name": "P100-STRING-SCOPE.md",
      "title": "P100 — Alcance del inventario de internacionalización",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/P100-STRING-SCOPE.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Generado con `python3 tools/generate_string_inventory.py`. No importa ni ejecuta LANCTL.",
      "details": "Documento mantenido en docs/P100-STRING-SUMMARY.md.",
      "docs": [
        "P100-STRING-SUMMARY.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-p100-string-summary",
      "kind": "document",
      "name": "P100-STRING-SUMMARY.md",
      "title": "P100 — Inventario estático de cadenas",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/P100-STRING-SUMMARY.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Nueva versión del canal estable, posterior a 0.3.2-beta.4. Integra el desarrollo experimental y las correcciones de auditoría de octubre en la rama `main`. Las ramas y los instaladores de versiones anteriores se conservan.",
      "details": "Documento mantenido en docs/RELEASE-0.3.3.md.",
      "docs": [
        "RELEASE-0.3.3.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-3",
      "kind": "document",
      "name": "RELEASE-0.3.3.md",
      "title": "LANCTL 0.3.3",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.3.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Prototipo de la rama `experimental-gui`, publicado como **pre-release** para probar las interfaces gráficas en otro ordenador. No es una versión estable y no sustituye a la Release estable 0.3.3. No se necesita instalar Python.",
      "details": "Documento mantenido en docs/RELEASE-0.3.4-alpha.1.md.",
      "docs": [
        "RELEASE-0.3.4-alpha.1.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-4-alpha-1",
      "kind": "document",
      "name": "RELEASE-0.3.4-alpha.1.md",
      "title": "LANCTL 0.3.4-alpha.1 — GUI EXPERIMENTAL (NO ESTABLE)",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.4-alpha.1.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
      },
      "description": "Nueva revisión de desarrollo posterior a `0.3.4-alpha.1`. Incluye mejoras de configuración GUI, navegación TUI, diagnóstico, idiomas e instaladores. No declara una versión estable ni modifica los identificadores públicos del Core.",
      "details": "Documento mantenido en docs/RELEASE-0.3.4-alpha.2.md.",
      "docs": [
        "RELEASE-0.3.4-alpha.2.md"
      ],
      "examples": [],
      "group": "docs/",
      "id": "doc-release-0-3-4-alpha-2",
      "kind": "document",
      "name": "RELEASE-0.3.4-alpha.2.md",
      "title": "LANCTL 0.3.4-alpha.2 — Experimental (no estable)",
      "url": "https://github.com/CctrGy/LANCTL/blob/main/docs/RELEASE-0.3.4-alpha.2.md"
    },
    {
      "category": "Archivos de documentación",
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Documento histórico: recoge la revisión anterior a la publicación de 0.3.2-beta.4. El estado siguiente corresponde a ese momento y no al estado actual del repositorio; consulta las notas de cada Release.",
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
      },
      "description": "Inicia el anfitrión de la suite con `lanctl --tui`. Dentro, `help` y `help settings` muestran ayuda en una vista del propio TUI, sin salir a la consola. Usa `↑/↓`, `RePág/AvPág` e `Inicio/Fin` para desplazarte y `Esc` o `Enter` para volver al panel. `commands`, `pwd` y `version` usan la misma vista.",
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
        "verified": "0.3.4-alpha.2"
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
    "entryCount": 192,
    "name": "LANCTL Reference",
    "repository": "https://github.com/CctrGy/LANCTL",
    "version": "0.3.4-alpha.2"
  },
  "workflows": [
    {
      "compatibility": {
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
        "verified": "0.3.4-alpha.2"
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
