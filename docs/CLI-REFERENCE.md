# Referencia completa del CLI LANCTL

Documento generado automáticamente desde los parsers de la aplicación.
No lo edites manualmente; ejecuta `python tools/generate_cli_reference.py`.

## `LANCTL`

```text
Usage: LANCTL [-h] [--version] [--cli | -tui | --gui] [-web | -github | -reference] [--admin]
              LAUNCHER ...

Root orchestrator for the LANCTL suite applications.

Arguments:
  LAUNCHER
    lanip (ip)             Logical inventory, discovery, IP, MAC and services.
    lanwire (wire)         Wiring, ports, panels and physical topology.
    lanrack (rack)         Technical rooms, racks, rack units and equipment.
    lanaccess (access)     Users, credentials and remote access.
    lanmon (monitor)       Monitoring, events, incidents and history.
    plugin                 Shared suite administration.
    settings               Shared suite administration.
    language               Shared suite administration.
    backend                Shared suite administration.
    setup-defaults         Initialize installation preferences without overwriting existing ones.
    completions            Register or remove Clink completion for the current user.
    post-install           Open LANIP as the normal user after installation.

Options:
  -h, --help               Show this help and exit.
  --version                Show the common suite version and exit.
  --cli, -cli              Open the main console.
  -tui, --tui              Open the main TUI.
  --gui                    Open the LANCTL graphical hub.
  -web, --web              Show and open the official website.
  -github, --github        Show and open the official GitHub.
  -reference, --reference  Show and open the official reference.
  --admin                  Explicitly request UAC for an installed launcher on Windows.
```

## `LANIP`

```text
Usage: LANIP [-h] [--version] [--quiet | --verbose] [--gui] [--first-scan] [--cli]
             [-tui [VENTANA]] [-project ARCHIVO.vlf]
             COMANDO ...

Logical control of LAN devices and infrastructure.

Arguments:
  COMANDO
    ephemeral (-e)            Scan active hosts without reading or saving any inventory.
    list                      Scan the LAN and show active and historical devices.
    recurrent                 Query recurring elements known to LANCTL.
    ping                      Check once whether an element responds to PING or ARP.
    open (connect)            Open an element with a protocol-appropriate client.
    settings                  Query or change LANCTL's persistent configuration.
    call                      Resolve an alias, IP or MAC to device data.
    search                    Search devices by alias, name, IP or MAC.
    scan                      Inspect a single LAN element in depth.
    cnf                       Assign an element's CNF state by IP, MAC or alias.
    credential (credentials, auth)
                              Associate encrypted credentials with an element and protocol.
    GATEWAY (gateway)         Query and configure the gateway through TR-064.
    downloadSettings (downloadsettings, download-settings)
                              Legacy alias for “GATEWAY downloadSettings”.
    protocol                  Query or configure an element's protocol.
    ssh                       Open SSH or run a read-only show query.
    radmin                    Configure, check or open Radmin Viewer.
    wol                       Wake devices through Wake-on-LAN and run safe sequences.
    history                   Query structured events from the active VLF project.
    monitor                   Operate LAN monitor sessions and checks.
    access                    Configure secure LAN remote access through SSH and HTTPS.
    smb                       Discover and open Windows SMB resources.
    terminal (cli)            Open an element's terminal according to its protocol.
    switch                    Plan filtered, remapped and classified Cisco commands.
    group                     Create, edit and query element groups.
    element                   Edit one or more fields of an element identified by IP, MAC or
                              alias.
    project (projects)        Create, update and inspect LANCTL .vlf projects.
    plugin (plugins, addon, addons)
                              Manage unified LANCTL .lcp plugins.
    language (languages, lang)
                              Manage LANCTL interface languages.
    error (errors)            Query the catalog by identifier 0eXXXXXXXX.
    database (db)             Diagnose and export data.
    demo                      Generate a reproducible walkthrough without depending on a real
                              network.
    lanwire (wire)            Open LANWIRE or run one of its commands on the shared physical
                              database.
    lab                       Manage simulated LANs without real traffic.

Options:
  -h, --help                  Show this help and exit.
  --version                   Show the version and exit.
  --quiet                     Suppress successful output; preserve errors.
  --verbose                   Add execution diagnostics to stderr.
  --gui                       Open the LANIP graphical interface.
  --first-scan                Request first scan confirmation when opening the GUI; do not scan
                              automatically.
  --cli, -cli                 Open the persistent interactive LANCTL terminal.
  -tui, --tui [VENTANA]       Open the advanced full-screen terminal interface. Can open PLUGINS,
                              PROJECTS or SETTINGS directly.
  -project, --project ARCHIVO.vlf
                              Select a VLF project before opening the TUI or running a command.
```

## `LANIP ephemeral`

```text
Usage: LANIP ephemeral [-h] [--fast | --normal | --accurate] [--range NETWORK] [--resolve-names]
                       [--ports PORTS] [--json] [--workers WORKERS] [--timeout TIMEOUT]
                       [--max-hosts MAX_HOSTS] [--scan-order {ascending,descending,random}]

Perform actual discovery in an isolated in-memory session. Does not open, modify or save projects or device databases.

Options:
  -h, --help                  Show this help and exit.
  --fast                      Prioriza un barrido ARP rápido.
  --normal                    Combina ICMP, ARP y descubrimiento de servicios.
  --accurate                  Añade reintentos y reconocimiento más profundo.
  --range NETWORK             CIDR range to explore only during this execution.
  --resolve-names             Resolve names without storing them.
  --ports PORTS               Optional TCP ports, for example 22,80,443.
  --json                      Return the session as JSON.
  --workers WORKERS           Concurrent probes.
  --timeout TIMEOUT           Base timeout per probe, in seconds.
  --max-hosts MAX_HOSTS       Defensive limit on authorized addresses.
  --scan-order {ascending,descending,random}
                              Address exploration order.
```

## `LANIP list`

```text
Usage: LANIP list [-h] [--network NETWORK] [--interface INTERFACE] [--database DATABASE]
                  [--groups GROUPS] [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT] [-recurrent]
                  [--where WHERE] [-w WORKERS] [-t TIMEOUT]
                  [--scan-order {ascending,descending,random}] [--include-unknown]
                  [--resolve-names] [--max-hosts MAX_HOSTS] [--discovery {icmp,arp,hybrid}]
                  [--profile {fast,normal,accurate} | --fast | --normal | --accurate]
                  [--progress | --no-progress] [--show-discovery] [--include-arp-cache]
                  [--show-detection] [--active | -disconnected] [-basic] [-cnf {O,X,-,S,F}]
                  [-group GRUPO] [-dhcp]

Perform a basic IP/MAC scan, update the database by MAC and also show undetected devices.

Options:
  -h, --help                  Show this help and exit.
  --network NETWORK           CIDR network. Detects the LAN as /24 by default.
  --interface INTERFACE       Local IPv4 source or interface ID; uses its actual mask. ICMP/ARP
                              only, without DNS or external discovery.
  --database DATABASE         Element JSON file.
  --groups GROUPS             Group JSON file.
  -f, --format {table,json,csv,html,xml,yaml}
                              Output format (default: table).
  -o, --output OUTPUT         Save output to a file.
  -recurrent, --recurrent     List recurring elements without scanning the LAN or showing IP.
  --where WHERE               Composable query, for example: "active and group=IOT and
                              vendor~Amazon".
  -w, --workers WORKERS       Concurrent checks.
  -t, --timeout TIMEOUT       Base timeout in seconds per operation and host; the profile may
                              adjust it.
  --scan-order {ascending,descending,random}
                              IP probe order: ascending, descending or random.
  --include-unknown           Include active hosts even if their MAC is not yet known.
  --resolve-names             Resolve and save DNS names of detected elements.
  --max-hosts MAX_HOSTS       Maximum hosts allowed in a scan.
  --discovery {icmp,arp,hybrid}
                              Method: icmp, active arp or hybrid (default from settings).
  --profile {fast,normal,accurate}
                              Complete scan profile: fast, normal or accurate.
  --fast                      Fast ARP scan.
  --normal                    Balanced hybrid scan.
  --accurate                  Deep scan using multiple methods.
  --progress                  Show interactive progress.
  --no-progress               Hide progress.
  --show-discovery            Add a column with ICMP, ARP, LOCAL, BASIC or CACHE.
  --include-arp-cache         Import cached ARP neighbors as unverified CACHE; they do not count
                              as active.
  --show-detection            Add historical methods and last-seen date.
  --active, -active, -connected, --connected, -conected
                              Show only devices active in the current scan.
  -disconnected, --disconnected, -offline
                              Show only devices not currently detected.
  -basic, --basic             Compact view: IP, alias and description.
  -cnf, --cnf-state {O,X,-,S,F}
                              Filter by CNF state: O, X, -, S or F.
  -group, --group GRUPO       Show only elements in a group.
  -dhcp, --dhcp-only          Show only IPs within the configured DHCP range.
```

## `LANIP recurrent`

```text
Usage: LANIP recurrent [-h] -list [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT]

Show recurring identities by MAC. Does not include IP because it can change on each LAN.

Options:
  -h, --help                  Show this help and exit.
  -list, --list               List all recurring elements without their IPs.
  -f, --format {table,json,csv,html,xml,yaml}
                              Output format (default: table).
  -o, --output OUTPUT         Save output to a file.
```

## `LANIP ping`

```text
Usage: LANIP ping [-h] [--method {auto,ping,arp} | --ping | --arp] [--timeout TIMEOUT] [--json]
                  [--database DATABASE]
                  selector

Diagnose a single element without changing the database. PING tests ICMP; ARP performs an active LAN query; AUTO combines both methods.

Arguments:
  selector                  IP, MAC, alias or registered name.

Options:
  -h, --help                Show this help and exit.
  --method {auto,ping,arp}  Lookup method: auto, ping or arp (default: auto).
  --ping                    Use only one ICMP request.
  --arp                     Use only one active ARP request.
  --timeout TIMEOUT         Maximum timeout per check, in seconds.
  --json                    Return diagnostics as JSON.
  --database DATABASE       Element JSON file.
```

## `LANIP open`

```text
Usage: LANIP open [-h] [--port PORT] [--path PATH]
                  [--mode {control,view,file,shutdown,chat,voice,message,telnet}]
                  [--through THROUGH] [--fullscreen] [--color-depth {24,16,8,4,2,1}]
                  [--updates UPDATES] [--phonebook PHONEBOOK] [--phonebook-id PHONEBOOK_ID]
                  [--dry-run] [--database DATABASE] [--store STORE]
                  selector [{auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}]

Arguments:
  selector                    Element IP, MAC or alias.
  {auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}
                              Protocol or automatic detection.

Options:
  -h, --help                  Show this help and exit.
  --port PORT                 Alternative port.
  --path PATH                 HTTP/FTP/RTSP path or SMB resource.
  --mode {control,view,file,shutdown,chat,voice,message,telnet}
                              Radmin connection mode.
  --through THROUGH           Intermediate Radmin server HOST:PORT.
  --fullscreen                Open full-screen control or view.
  --color-depth {24,16,8,4,2,1}
                              Radmin color depth (1, 2, 4, 8, 16 or 24 bits).
  --updates UPDATES           Maximum screen updates per second (1-120).
  --phonebook PHONEBOOK       Radmin .rpb phonebook path.
  --phonebook-id PHONEBOOK_ID
                              Entry identifier within the Radmin phonebook.
  --dry-run                   Show the target without opening it.
  --database DATABASE         Element JSON file.
  --store STORE               Encrypted credential store.
```

## `LANIP settings`

```text
Usage: LANIP settings [-h] [--startup-interface {cli,tui,gui}] [--close-gui-on-launch {on,off}]
                      [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]
                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]
                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]
                      [--service-identification {on,off}]
                      [--disconnected-retention {permanent,session,forget}]
                      [--disconnected-target {unconfirmed,all}] [--disconnected-scope {all,dhcp}]
                      [--workers WORKERS] [--timeout TIMEOUT]
                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]
                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]
                      [--log DIRECTORIO] [--error-log-level 1-59]
                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]
                      [--cli-exit-save-prompt {on,off}] [--cli-command-chaining {on,off}]
                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]
                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]
                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]
                      [--remote-backend {service,user}]
                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]
                      [--tui-key ACCIÓN=TECLA] [--tui-layout {cli.bottom,cli.top}]
                      [--tui-cli-percent 15-75] [--tui-column COLUMNA=TAMAÑO]
                      [--tui-footer-buttons ACCIONES] [--tui-footer-button ACCIÓN=on|off]
                      [--menu | --catalog | --get RUTA | --set RUTA VALOR]
                      [--scope {program,project}] [--category CATEGORY]

Options:
  -h, --help                  Show this help and exit.
  --startup-interface {cli,tui,gui}
                              Preferred interface when opening LANCTL without arguments.
  --close-gui-on-launch {on,off}
                              Close the main GUI when the requested launcher is available.
  -range CIDR                 Default LAN range, for example 192.168.1.1/24.
  -list-fields, --list-fields, -list CAMPO [CAMPO ...]
                              Columns displayed by list, separated by spaces or commas.
  -dhcp-range, --dhcp-range, -dhcp INICIO-FIN
                              Manual DHCP range. Use 'off' to leave it unconfigured.
  -credentials, --credentials ARCHIVO
                              Path to the encrypted credential store.
  -discovery, --discovery {icmp,arp,hybrid}
                              Default method used by list.
  --scan-profile {fast,normal,accurate}
                              Default list profile: fast, normal or accurate.
  --progress {on,off}         Enable or disable interactive progress.
  --service-identification {on,off}
                              Enable or disable service recognition in scan.
  --disconnected-retention {permanent,session,forget}
                              Disconnected device persistence: permanent, session or forget.
  --disconnected-target {unconfirmed,all}
                              Apply retention only to CNF=X (unconfirmed) or to all (all).
  --disconnected-scope {all,dhcp}
                              Apply the rule to the entire LAN (all) or only the DHCP range
                              (dhcp).
  --workers WORKERS           Default scan concurrency.
  --timeout TIMEOUT           Default timeout per network operation.
  --scan-order {ascending,descending,random}
                              Default probe order: ascending, descending or random.
  --max-hosts MAX_HOSTS       Maximum hosts authorized per scan.
  --database ARCHIVO          Path to the element inventory.
  --physical-database ARCHIVO
                              Path to the physical SQLite database managed exclusively by LANWIRE.
  --groups ARCHIVO            Path to the group database.
  --log DIRECTORIO            Log directory.
  --error-log-level 1-59      Minimum ErrorEvent level written to the log (1 includes detailed
                              diagnostics).
  --projects-directory DIRECTORIO
                              Default folder for relative VLF project names.
  -save-mode, --save-mode MODO
                              VLF save policy. Use 'list' to query built-in and plugin-provided
                              options.
  -save-interval, --save-interval MINUTOS
                              Interval for automatic.timeToSave in minutes (minimum 0.1).
  --cli-exit-save-prompt {on,off}
                              Ask whether to save after each individual console command.
  --cli-command-chaining {on,off}
                              Allow command chaining with ; in the interactive CLI.
  -log-cleanup, --log-cleanup {on,off}
                              Enable or disable automatic cleanup of old logs.
  -log-retention-days, --log-retention-days DÍAS
                              Number of days to retain log files.
  --remote-access {on,off}    Enable restricted SSH access.
  --remote-bind IP            Local IPv4 address for SSH listening.
  --remote-cidr CIDR          Authorized source network.
  --remote-port REMOTE_PORT   Remote SSH server port.
  --remote-password-auth {on,off}
                              Allow or block SSH password authentication.
  --remote-backend {service,user}
                              Run the backend as a persistent service or user process.
  --remote-forced-view {off,gui,tui,plugins,projects,settings}
                              Default view for root forced-view.
  --tui-key ACCIÓN=TECLA      Assign a key to a TUI action. May be repeated.
  --tui-layout {cli.bottom,cli.top}
                              Place the CLI at the top (cli.top) or bottom (cli.bottom).
  --tui-cli-percent 15-75     Vertical percentage reserved for CLI; ListElement retains at least
                              25%.
  --tui-column COLUMNA=TAMAÑO
                              Column weight (GROUP=15%); IP=15ch and MAC=17ch are fixed.
  --tui-footer-buttons ACCIONES
                              Visible bottom-bar actions, comma-separated; use all for all
                              actions.
  --tui-footer-button ACCIÓN=on|off
                              Show or hide a specific bottom-bar action. May be repeated.
  --menu                      Interactive program and project editor organized by category.
  --catalog                   List common and CLI preferences by category, with values and
                              editability.
  --get RUTA                  Query a setting by path, for example ip.workers.
  --set RUTA VALOR            Change a common or CLI preference; lists and booleans use JSON.
  --scope {program,project}   Configuration scope (default: program).
  --category CATEGORY         Filter the catalog by category, for example network or monitor.
```

## `LANIP call`

```text
Usage: LANIP call [-h]
                  [-f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}]
                  [--json] [--database DATABASE]
                  selector

Arguments:
  selector                    Device alias, IP or MAC.

Options:
  -h, --help                  Show this help and exit.
  -f, --field {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}
                              Returned field (default: ip).
  --json                      Return the complete record as JSON.
  --database DATABASE         Element JSON file.
```

## `LANIP search`

```text
Usage: LANIP search [-h] [--json] [--database DATABASE] selector

Arguments:
  selector             Exact alias, name, IP or MAC.

Options:
  -h, --help           Show this help and exit.
  --json               Return the complete record as JSON for scripts.
  --database DATABASE  Element JSON file.
```

## `LANIP scan`

```text
Usage: LANIP scan [-h] [--ports LISTA] [--all-ports] [--timeout TIMEOUT] [--workers WORKERS]
                  [--banners] [--identify] [--json] [--database DATABASE]
                  selector

Resolve an element by IP, MAC or alias and check identity, availability and TCP ports. Does not modify the device.

Arguments:
  selector             IP, MAC or alias registered in LANCTL.

Options:
  -h, --help           Show this help and exit.
  --ports LISTA        Ports or ranges: 22,80,443,8000-8100 (default: common).
  --all-ports          Explicitly authorize a TCP 1-65535 scan.
  --timeout TIMEOUT    Maximum timeout per connection, in seconds.
  --workers WORKERS    Maximum number of concurrent connections.
  --banners            Read passive banners; do not send protocol-specific probes.
  --identify           Recognize services and infer device type from evidence.
  --json               JSON output.
  --database DATABASE  Element JSON file.
```

## `LANIP cnf`

```text
Usage: LANIP cnf [-h] [--database DATABASE] selector [value]

Arguments:
  selector             Element IP, MAC or alias.
  value                O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) or F (FIXED). Without a
                       value, release F and restore O.

Options:
  -h, --help           Show this help and exit.
  --database DATABASE  Element JSON file.
```

## `LANIP credential`

```text
Usage: LANIP credential [-h] [-user USERNAME] [--database DATABASE] [--store STORE]
                        selector [{set,list,delete}] [protocol]

Arguments:
  selector                    Element IP, MAC or alias.
  {set,list,delete}           Credential operation.
  protocol                    Protocol, for example tr-064.

Options:
  -h, --help                  Show this help and exit.
  -user, --username USERNAME  Remote username.
  --database DATABASE         Element JSON file.
  --store STORE               Encrypted credential store.
```

## `LANIP GATEWAY`

```text
Usage: LANIP GATEWAY [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    downloadSettings (downloadsettings, download-settings)
                              Download relevant LAN and DHCP settings for configuration.

Options:
  -h, --help                  Show this help and exit.
```

## `LANIP GATEWAY downloadSettings`

```text
Usage: LANIP GATEWAY downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]
                                      [--store STORE]

Options:
  -h, --help           Show this help and exit.
  --port PORT          Router TR-064 port.
  --timeout TIMEOUT    Maximum timeout in seconds.
  --database DATABASE  Element JSON file.
  --store STORE        Encrypted credential store.
```

## `LANIP downloadSettings`

```text
Usage: LANIP downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]
                              [--store STORE]
                              [gateway]

Arguments:
  gateway              Router IP, MAC or alias.

Options:
  -h, --help           Show this help and exit.
  --port PORT          Router TR-064 port.
  --timeout TIMEOUT    Maximum timeout in seconds.
  --database DATABASE  Element JSON file.
  --store STORE        Encrypted credential store.
```

## `LANIP protocol`

```text
Usage: LANIP protocol [-h] [--port PORT] [--driver DRIVER] [--host-key HOST_KEY] [--kex KEX]
                      [--profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}]
                      [--database DATABASE]
                      selector {show,configure} protocol

Arguments:
  selector                    IP, MAC or alias.
  {show,configure}            Query or change the protocol.
  protocol                    Protocol to configure.

Options:
  -h, --help                  Show this help and exit.
  --port PORT                 Remote port.
  --driver DRIVER             Device driver.
  --host-key HOST_KEY         Allowed host-key algorithm; may be repeated.
  --kex KEX                   Key-exchange algorithm; may be repeated.
  --profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}
                              Reusable SSH profile.
  --database DATABASE         Element JSON file.
```

## `LANIP ssh`

```text
Usage: LANIP ssh [-h] [--database DATABASE] [--store STORE] [--host HOST]
                 selector {probe,fingerprint,trust,open,show} [COMANDO ...]

Arguments:
  selector                    IP, MAC or alias.
  {probe,fingerprint,trust,open,show}
                              SSH operation.
  COMANDO                     Fingerprint or remote command, depending on the operation.

Options:
  -h, --help                  Show this help and exit.
  --database DATABASE         Element JSON file.
  --store STORE               Encrypted credential store.
  --host HOST                 Candidate IP for probe/fingerprint, without changing the database.
```

## `LANIP radmin`

```text
Usage: LANIP radmin [-h] [--mode {control,view,file,shutdown,chat,voice,message,telnet}]
                    [--port PORT] [--executable EXECUTABLE] [--through THROUGH] [--fullscreen]
                    [--color-depth {24,16,8,4,2,1}] [--updates UPDATES] [--phonebook PHONEBOOK]
                    [--phonebook-id PHONEBOOK_ID] [--database DATABASE] [--store STORE]
                    selector {probe,configure,open}

Arguments:
  selector                    Element IP, MAC or alias.
  {probe,configure,open}      Opción de configuración de Radmin Viewer.

Options:
  -h, --help                  Show this help and exit.
  --mode {control,view,file,shutdown,chat,voice,message,telnet}
                              Opción de configuración de Radmin Viewer.
  --port PORT                 Opción de configuración de Radmin Viewer.
  --executable EXECUTABLE     Per-device path; use 'auto' for automatic detection.
  --through THROUGH           Intermediate server HOST:PORT.
  --fullscreen                Open full-screen control or view.
  --color-depth {24,16,8,4,2,1}
                              Radmin color depth (1, 2, 4, 8, 16 or 24 bits).
  --updates UPDATES           Maximum screen updates per second (1-120).
  --phonebook PHONEBOOK       Radmin-managed .rpb phonebook.
  --phonebook-id PHONEBOOK_ID
                              Entry identifier within the Radmin phonebook.
  --database DATABASE         Opción de configuración de Radmin Viewer.
  --store STORE               Opción de configuración de Radmin Viewer.
```

## `LANIP wol`

```text
Usage: LANIP wol [-h] [-if CONDICIÓN] [--if-all CONDICIÓN] [--if-any CONDICIÓN]
                 [--if-not CONDICIÓN] [-t SCHEDULE] [--message MESSAGE] [--force] [--cancel]
                 [--broadcast BROADCAST] [--port PORT] [--repeat REPEAT] [--interval INTERVAL]
                 [--wait WAIT] [--method {auto,arp,ping,port}] [--check-port CHECK_PORT]
                 [--interface INTERFACE] [--retry RETRY] [--dry-run] [--json] [--quiet]
                 [--group GROUP] [--all] [--yes] [--after AFTER] [--delay DELAY]
                 [--timeout TIMEOUT] [--on-failure {stop,continue,retry}] [--cooldown COOLDOWN]
                 [--max-attempts MAX_ATTEMPTS] [--power-transport {ssh,disabled}]
                 [--power-platform {windows,linux}] [--power-command ACCIÓN=COMANDO]
                 [--database DATABASE] [--store STORE] [--sequences SEQUENCES]
                 [words ...]

Arguments:
  words                       NAME [wakeup|status|shutdown|restart|sleep|hibernate|configure] or
                              sequence ...

Options:
  -h, --help                  Show this help and exit.
  -if, --if CONDICIÓN         Condición AND adicional (repetible).
  --if-all CONDICIÓN          Condición AND adicional.
  --if-any CONDICIÓN          Condición OR adicional.
  --if-not CONDICIÓN          Condición negada.
  -t, --time SCHEDULE         Momento del apagado programado.
  --message MESSAGE           Mensaje remoto, si el transporte lo admite.
  --force                     Solicita cierre forzado al transporte.
  --cancel                    Cancela una programación, si el transporte lo admite.
  --broadcast BROADCAST       IPv4 de broadcast.
  --port PORT                 Puerto UDP WOL.
  --repeat REPEAT             Número de paquetes mágicos.
  --interval INTERVAL         Intervalo entre paquetes.
  --wait WAIT                 Segundos máximos de verificación.
  --method {auto,arp,ping,port}
                              Método de verificación.
  --check-port CHECK_PORT     Puerto TCP de comprobación.
  --interface INTERFACE       IPv4 local de salida.
  --retry RETRY               Reintentos completos.
  --dry-run                   Valida sin enviar.
  --json                      Salida JSON estructurada.
  --quiet                     Omite salida humana.
  --group GROUP               Actúa sobre un grupo.
  --all                       Actúa sobre todo el inventario.
  --yes                       Confirma explícitamente --all.
  --after AFTER               Dependencia de paso.
  --delay DELAY               Espera previa del paso.
  --timeout TIMEOUT           Timeout de paso.
  --on-failure {stop,continue,retry}
                              Política ante fallo.
  --cooldown COOLDOWN         Espera mínima entre ejecuciones.
  --max-attempts MAX_ATTEMPTS
                              Máximo de intentos.
  --power-transport {ssh,disabled}
                              Transporte autorizado para apagar o reiniciar.
  --power-platform {windows,linux}
                              Sistema operativo remoto.
  --power-command ACCIÓN=COMANDO
                              Plantilla administrada ACCIÓN=COMANDO.
  --database DATABASE         Element JSON file.
  --store STORE               Encrypted credential store.
  --sequences SEQUENCES       Archivo transaccional de secuencias.
```

## `LANIP history`

```text
Usage: LANIP history [-h] [--all] [--commands] [--today] [--from FECHA] [--to FECHA]
                     [--type TYPES] [--source SOURCE] [--result RESULT] [--errors]
                     [--search SEARCH] [--limit LIMIT] [--reverse] [--format {table,json,csv}]
                     [selector]

Arguments:
  selector                   DeviceId, alias, name, MAC, current or historical IP.

Options:
  -h, --help                 Show this help and exit.
  --all                      Include general events from the entire LAN.
  --commands                 In the interactive CLI, show session commands.
  --today                    Limit the query to the current local day.
  --from FECHA               Start date YYYY-MM-DD.
  --to FECHA                 End date YYYY-MM-DD.
  --type TYPES               Canonical type; may be repeated.
  --source SOURCE            Filter by source.
  --result RESULT            Filter by result.
  --errors                   Show errors only.
  --search SEARCH            Search safe text.
  --limit LIMIT              Maximum number of events (1..10000).
  --reverse                  Descending order.
  --format {table,json,csv}  Output format.
```

## `LANIP monitor`

```text
Usage: LANIP monitor [-h] [--project PROJECT] [--permanent] [--duration DURATION]
                     [--mode {permanent,temporary,diagnostic,once}]
                     [--authority {observe,operate,administer}] [--json] [--yes]
                     [--interval INTERVAL] [--every EVERY] [--group GROUP]
                     [--type {presence,services,ports,identity,smb,full}] [--fast] [--unknown]
                     [--follow] [--sessions SESSIONS] [--incidents-store INCIDENTS_STORE]
                     [--lock LOCK] [--monitor-db MONITOR_DB] [--profiles PROFILES]
                     [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]
                     [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]
                     [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP]
                     [--workers WORKERS] [--timeout TIMEOUT]
                     [words ...]

Arguments:
  words                       attach, detach, status, once, session, incidents, incident, service
                              or foreground.

Options:
  -h, --help                  Show this help and exit.
  --project PROJECT           Opción operativa del monitor.
  --permanent                 Opción operativa del monitor.
  --duration DURATION         Opción operativa del monitor.
  --mode {permanent,temporary,diagnostic,once}
                              Opción operativa del monitor.
  --authority {observe,operate,administer}
                              Opción operativa del monitor.
  --json                      Opción operativa del monitor.
  --yes                       Opción operativa del monitor.
  --interval INTERVAL         Opción operativa del monitor.
  --every EVERY               Opción operativa del monitor.
  --group GROUP               Opción operativa del monitor.
  --type {presence,services,ports,identity,smb,full}
                              Opción operativa del monitor.
  --fast                      Opción operativa del monitor.
  --unknown                   Opción operativa del monitor.
  --follow                    Opción operativa del monitor.
  --sessions SESSIONS         Runtime session state.
  --incidents-store INCIDENTS_STORE
                              Runtime incident state.
  --lock LOCK                 Monitor singleton lock.
  --monitor-db MONITOR_DB     Monitor SQLite repository.
  --profiles PROFILES         Custom profiles.
  --assignments-store ASSIGNMENTS_STORE
                              Persistent assignments.
  --profile PROFILE           Monitor profile.
  --priority {low,normal,high,critical}
                              Assignment priority.
  --check CHECK               Check ping, arp or port:NN.
  --presence PRESENCE         Presence interval.
  --discovery DISCOVERY       Discovery interval.
  --services SERVICES         Service interval.
  --deep DEEP                 Deep scan interval.
  --workers WORKERS           Profile workers.
  --timeout TIMEOUT           Profile timeout.
```

## `LANIP access`

```text
Usage: LANIP access [-h] [--bind BIND] [--cidr CIDR] [--port PORT] [--password-auth {on,off}]
                    [--role ROLE] [--ssh-key SSH_KEY] [--expires EXPIRES]
                    [--permission PERMISSION] [--certificate CERTIFICATE]
                    [--private-key PRIVATE_KEY] [--common-name COMMON_NAME] [--yes] [--json]
                    [--scope {user,service}] [--config CONFIG] [--users USERS]
                    [words ...]

Arguments:
  words                      init, status, enable, disable, configure, user, role, session, web or
                             certificate.

Options:
  -h, --help                 Show this help and exit.
  --bind BIND                Opción de acceso remoto.
  --cidr CIDR                Opción de acceso remoto.
  --port PORT                Opción de acceso remoto.
  --password-auth {on,off}   Opción de acceso remoto.
  --role ROLE                Opción de acceso remoto.
  --ssh-key SSH_KEY          Opción de acceso remoto.
  --expires EXPIRES          Opción de acceso remoto.
  --permission PERMISSION    Opción de acceso remoto.
  --certificate CERTIFICATE  Opción de acceso remoto.
  --private-key PRIVATE_KEY  Opción de acceso remoto.
  --common-name COMMON_NAME  Opción de acceso remoto.
  --yes                      Opción de acceso remoto.
  --json                     Opción de acceso remoto.
  --scope {user,service}     Separate user credentials from the persistent service credentials.
  --config CONFIG            Separate remote configuration.
  --users USERS              Remote user store.
```

## `LANIP smb`

```text
Usage: LANIP smb [-h] [--network] [--group GROUP] [--timeout TIMEOUT] [--workers WORKERS]
                 [--anonymous] [--include-system] [--dry-run] [--yes] [--json]
                 [--database DATABASE] [--store STORE] [--storage STORAGE]
                 [name] [action] [resource] [{open,queue,connect}]

Arguments:
  name                  Server/device (no action defaults to info).
  action                scan, info, shares, open, printers, workgroups, connect, disconnect,
                        status or printer.
  resource              Shared folder or printer.
  {open,queue,connect}  Printer action.

Options:
  -h, --help            Show this help and exit.
  --network             Examine the entire LANCTL inventory.
  --group GROUP         Limit the scan to a LANCTL group.
  --timeout TIMEOUT     TCP probe timeout.
  --workers WORKERS     Maximum number of concurrent probes.
  --anonymous           Do not load associated credentials.
  --include-system      Include administrative and special resources.
  --dry-run             Show the plan without authenticating, opening or changing anything.
  --yes                 Confirm a printer connection.
  --json                Output structured JSON.
  --database DATABASE   Inventory JSON file.
  --store STORE         DPAPI credential store.
  --storage STORAGE     Plugin observations directory.
```

## `LANIP terminal`

```text
Usage: LANIP terminal [-h] [-p PROTOCOL] [--native] [--database DATABASE] [--store STORE] selector

Arguments:
  selector                 Element IP, MAC or alias.

Options:
  -h, --help               Show this help and exit.
  -p, --protocol PROTOCOL  Protocol when multiple terminals are available.
  --native                 Use the native SSH client without LANCTL's color layer.
  --database DATABASE      Element JSON file.
  --store STORE            Encrypted credential store.
```

## `LANIP switch`

```text
Usage: LANIP switch [-h] [--profile PROFILE] [--profiles PROFILES] [--database DATABASE]
                    [--dry-run] [--yes]
                    selector ...

Managed Cisco commands:
  show COMMAND
  port list
  port label PORT NAME
  port unlabel PORT
  port show [PORT] status|description|config|errors|vlan
  port set [PORT] description|speed|duplex VALUE
  port enable|disable|reset [PORT]
  start|stop|reset [PORT]
  save-config
  terminal

Global options: --profile PROFILE --dry-run --yes
This phase uses a simulated adapter and does not connect to the switch.

Arguments:
  selector             Switch IP, MAC or alias.
  COMANDO              Managed Cisco action to plan.

Options:
  -h, --help           Show this help and exit.
  --profile PROFILE    Cisco profile that remaps ports.
  --profiles PROFILES  JSON file containing Cisco profiles.
  --database DATABASE  Element JSON file.
  --dry-run            Show the plan only.
  --yes                Confirm changes without asking.
```

## `LANIP group`

```text
Usage: LANIP group [-h] [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENT |
                   -remove ELEMENT | -list] [--database DATABASE] [--groups GROUPS]
                   [name]

Arguments:
  name                 Group name.

Options:
  -h, --help           Show this help and exit.
  -new                 Create the group.
  -del                 Delete the group.
  -rename NUEVO        Rename the group.
  -description TEXTO   Edit its description.
  -add ELEMENT         Add IP, MAC or alias.
  -remove ELEMENT      Remove IP, MAC or alias.
  -list                List elements belonging to the group.
  --database DATABASE  Element JSON file.
  --groups GROUPS      Group JSON file.
```

## `LANIP element`

```text
Usage: LANIP element [-h] [-add MAC] [-name NEW_NAME] [-ip NEW_IP] [-alias NEW_ALIAS]
                     [-description NEW_DESCRIPTION] [-cnf NEW_CNF] [-idf NEW_IDF]
                     [-group NEW_GROUP] [-protocol NEW_PROTOCOL] [-delete] [--database DATABASE]
                     [--groups GROUPS] [--yes]
                     [selector]
                     [{edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}]
                     [values ...]

Arguments:
  selector                    IP, MAC or alias.
  {edit,ip,cnf,name,description,alias,idf,group,protocol,delete,del,remove}
                              Field or action to edit.
  values                      New value.

Options:
  -h, --help                  Show this help and exit.
  -add MAC                    Add a new element using its MAC address.
  -name, --name NEW_NAME      Assign NAME to the specified element.
  -ip, --ip NEW_IP            Assign an IPv4 address.
  -alias, --alias NEW_ALIAS   Assign ALIAS to the specified element.
  -description, --description NEW_DESCRIPTION
                              Assign DESCRIPTION to the specified element.
  -cnf, --cnf NEW_CNF         Assign the CNF state.
  -idf, --idf NEW_IDF         Assign a unique IDF (2-5 letters and 2-5 digits).
  -group, --group NEW_GROUP   Add the element to the group.
  -protocol, --protocol NEW_PROTOCOL
                              Enable a protocol.
  -delete, --delete           Completely delete the specified element.
  --database DATABASE         Element JSON file.
  --groups GROUPS             Group JSON file.
  --yes                       Delete without requesting confirmation.
```

## `LANIP project`

```text
Usage: LANIP project [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    status           Show the active project.
    create           Create an empty VLF project by default.
    update           Update active data while preserving supplementary information.
    save             Manually save the active VLF project.
    import-physical  Copy a historical IDF database into the active empty physical project.
    info             Show project metadata.
    verify           Check hashes, structure and SQLite.
    use              Select the VLF project that receives the audit.
    list             List internal contents without extracting them.

Options:
  -h, --help         Show this help and exit.
```

## `LANIP project status`

```text
Usage: LANIP project status [-h] [--json]

Options:
  -h, --help  Show this help and exit.
  --json      Return JSON.
```

## `LANIP project create`

```text
Usage: LANIP project create [-h] [--name NAME] [--description DESCRIPTION] [--author AUTHOR]
                            [--lan-name LAN_NAME] [--location LOCATION] [--company COMPANY]
                            [--responsible RESPONSIBLE] [--clone-current] [--force]
                            file

Arguments:
  file                       Output file; .vlf is appended if missing.

Options:
  -h, --help                 Show this help and exit.
  --name NAME                Human-readable project name.
  --description DESCRIPTION  General description.
  --author AUTHOR            Project author.
  --lan-name LAN_NAME        Human-readable LAN name.
  --location LOCATION        Physical location.
  --company COMPANY          Company or organization.
  --responsible RESPONSIBLE  Person responsible for the LAN.
  --clone-current            Create the project by explicitly copying the active inventory and
                             groups.
  --force                    Overwrite an existing VLF.
```

## `LANIP project update`

```text
Usage: LANIP project update [-h] file

Arguments:
  file        Existing VLF project.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project save`

```text
Usage: LANIP project save [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project import-physical`

```text
Usage: LANIP project import-physical [-h] file

Arguments:
  file        Source IDF .db database; preserved unchanged.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project info`

```text
Usage: LANIP project info [-h] [--json] file

Arguments:
  file        VLF project.

Options:
  -h, --help  Show this help and exit.
  --json      Return JSON.
```

## `LANIP project verify`

```text
Usage: LANIP project verify [-h] [--json] file

Arguments:
  file        VLF project.

Options:
  -h, --help  Show this help and exit.
  --json      Return JSON.
```

## `LANIP project use`

```text
Usage: LANIP project use [-h] file

Arguments:
  file        Existing VLF project.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project list`

```text
Usage: LANIP project list [-h] file

Arguments:
  file        VLF project.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin`

```text
Usage: LANIP plugin [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    list         List installed plugins.
    catalog      Show the bundled official catalog.
    info         Show manifest, permissions and state.
    install      Verify and install a disabled .lcp package.
    enable       Grant permissions and enable a plugin.
    disable      Desactiva el complemento.
    reload       Recarga un complemento activo.
    uninstall    Desinstala el complemento.
    verify       Verify a .lcp or installed plugin.
    permissions  Show requested and granted permissions.
    revoke       Revoke a plugin's permissions and trust.
    publisher    Manage Ed25519 fingerprints of trusted LCP publishers.
    extensions   List extensions for CLI, TUI and the future GUI.
    pack         Build a .lcp package from a directory.

Options:
  -h, --help     Show this help and exit.
```

## `LANIP plugin list`

```text
Usage: LANIP plugin list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin catalog`

```text
Usage: LANIP plugin catalog [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin info`

```text
Usage: LANIP plugin info [-h] plugin_id

Arguments:
  plugin_id   Stable plugin identifier.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin install`

```text
Usage: LANIP plugin install [-h] file

Arguments:
  file        Package file with the .lcp extension.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin enable`

```text
Usage: LANIP plugin enable [-h] [--grant [PERMISO ...]] [--grant-all] [--trust] plugin_id

Arguments:
  plugin_id              Installed plugin identifier.

Options:
  -h, --help             Show this help and exit.
  --grant [PERMISO ...]  Specific permissions to grant.
  --grant-all            Grant all requested permissions.
  --trust                Authorize trusted code within the process.
```

## `LANIP plugin disable`

```text
Usage: LANIP plugin disable [-h] plugin_id

Arguments:
  plugin_id   Installed plugin identifier.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin reload`

```text
Usage: LANIP plugin reload [-h] plugin_id

Arguments:
  plugin_id   Installed plugin identifier.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin uninstall`

```text
Usage: LANIP plugin uninstall [-h] plugin_id

Arguments:
  plugin_id   Installed plugin identifier.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin verify`

```text
Usage: LANIP plugin verify [-h] target

Arguments:
  target      Installed identifier or path to a .lcp file.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin permissions`

```text
Usage: LANIP plugin permissions [-h] plugin_id

Arguments:
  plugin_id   Installed plugin identifier.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin revoke`

```text
Usage: LANIP plugin revoke [-h] plugin_id [PERMISO ...]

Arguments:
  plugin_id   Installed plugin identifier.
  PERMISO     Leave empty to revoke all permissions.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin publisher`

```text
Usage: LANIP plugin publisher [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    list      List trusted publishers.
    trust     Trust the signature contained in an LCP package.
    revoke    Revoke a publisher fingerprint.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin publisher list`

```text
Usage: LANIP plugin publisher list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin publisher trust`

```text
Usage: LANIP plugin publisher trust [-h] [--name NAME] file

Arguments:
  file         Signed and verified .lcp package.

Options:
  -h, --help   Show this help and exit.
  --name NAME  Descriptive publisher name.
```

## `LANIP plugin publisher revoke`

```text
Usage: LANIP plugin publisher revoke [-h] fingerprint

Arguments:
  fingerprint  Full Ed25519 SHA-256 fingerprint.

Options:
  -h, --help   Show this help and exit.
```

## `LANIP plugin extensions`

```text
Usage: LANIP plugin extensions [-h] [--type TYPE]

Options:
  -h, --help   Show this help and exit.
  --type TYPE  Filter by unified extension type.
```

## `LANIP plugin pack`

```text
Usage: LANIP plugin pack [-h] [--force] [--signing-key SIGNING_KEY] directory output

Arguments:
  directory                  Source directory containing plugin.info.
  output                     Output .lcp file.

Options:
  -h, --help                 Show this help and exit.
  --force                    Overwrite the existing output package.
  --signing-key SIGNING_KEY  Ed25519 PEM private key for signing the LCP.
```

## `LANIP language`

```text
Usage: LANIP language [-h] ACTION ...

Arguments:
  ACTION
    list      List installed languages.
    use       Select the interface language.
    info      Show language metadata and coverage.
    install   Install or update a .lang JSON catalog.
    validate  Validate a .lang catalog.
    export    Export the English template for translation.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP language list`

```text
Usage: LANIP language list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP language use`

```text
Usage: LANIP language use [-h] language

Arguments:
  language    Language code or name, for example en or Español.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP language info`

```text
Usage: LANIP language info [-h] [language]

Arguments:
  language    Language code or name; active language by default.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP language install`

```text
Usage: LANIP language install [-h] file

Arguments:
  file        Language catalog with .lang extension.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP language validate`

```text
Usage: LANIP language validate [-h] file

Arguments:
  file        Language catalog with .lang extension.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP language export`

```text
Usage: LANIP language export [-h] file

Arguments:
  file        Destination .lang file.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP error`

```text
Usage: LANIP error [-h] [--json] 0eXXXXXXXX

Arguments:
  0eXXXXXXXX  Stable error identifier.

Options:
  -h, --help  Show this help and exit.
  --json      Output the result as JSON.
```

## `LANIP database`

```text
Usage: LANIP database [-h] (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip |
                      --import ARCHIVO.zip | --restore ARCHIVO.bak)
                      [--target {database,groups,physical}] [--yes] [--json]

Options:
  -h, --help                  Show this help and exit.
  --diagnose                  Validate configured stores.
  --export ARCHIVO.zip        Export data with verifiable hashes.
  --verify ARCHIVO.zip        Verify an export without importing it.
  --import ARCHIVO.zip        Import verified data.
  --restore ARCHIVO.bak       Restore a validated store backup.
  --target {database,groups,physical}
                              Store to restore.
  --yes                       Confirm data replacement.
  --json                      Output diagnostics as JSON.
```

## `LANIP demo`

```text
Usage: LANIP demo [-h] [--output DIRECTORIO] [--force] [--format {json,html,all}]

Create inventory, VLF project, evidence, monitoring and a demonstration report isolated from user data.

Options:
  -h, --help                Show this help and exit.
  --output DIRECTORIO       Directory for the project and report.
  --force                   Replace a previous demo.
  --format {json,html,all}  Exported report format.
```

## `LANIP lanwire`

```text
Usage: LANIP lanwire [-h] [--new-window] [--version] [--database ARCHIVO.db] [-tui | --cli] ...

Arguments:
  ARGUMENTO              Arguments forwarded to LANWIRE, for example: list.

Options:
  -h, --help             Show this help and exit.
  --new-window           Open LANWIRE in a separate console even when arguments are provided.
  --version              Show the common LANWIRE version and exit.
  --database ARCHIVO.db  Select an alternative physical IDF database.
  -tui, --tui            Open the LANWIRE TUI.
  --cli                  Open the LANWIRE interactive console.
```

## `LANIP lab`

```text
Usage: LANIP lab [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    generate  Generate a reproducible scenario.
    list      Lista escenarios.
    status    Muestra el escenario activo.
    stop      Desactiva el proveedor simulado.
    start     Explicitly activate a virtual scenario.
    validate  Validate a scenario.
    export    Export a scenario.
    import    Import a JSON scenario.
    network   Manually create a virtual network.
    device    Edit simulated devices.
    evolve    Advance the clock and apply pending events.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab generate`

```text
Usage: LANIP lab generate [-h] [--name NAME] [--cidr CIDR]
                          [--profile {home,office,datacenter,industrial,chaotic}]
                          [--devices DEVICES] [--seed SEED] [--active-percent ACTIVE_PERCENT]
                          [--dhcp-percent DHCP_PERCENT] [--type {snapshot,timeline,chaos}]

Options:
  -h, --help                  Show this help and exit.
  --name NAME                 Scenario name.
  --cidr CIDR                 Virtual IPv4 network.
  --profile {home,office,datacenter,industrial,chaotic}
                              Device profile.
  --devices DEVICES           Number of devices.
  --seed SEED                 Reproducible seed.
  --active-percent ACTIVE_PERCENT
                              Active percentage.
  --dhcp-percent DHCP_PERCENT
                              DHCP percentage.
  --type {snapshot,timeline,chaos}
                              Scenario evolution.
```

## `LANIP lab list`

```text
Usage: LANIP lab list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab status`

```text
Usage: LANIP lab status [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab stop`

```text
Usage: LANIP lab stop [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab start`

```text
Usage: LANIP lab start [-h] scenario

Arguments:
  scenario    Scenario name.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab validate`

```text
Usage: LANIP lab validate [-h] scenario

Arguments:
  scenario    Scenario name.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab export`

```text
Usage: LANIP lab export [-h] [--format {json,csv}] [--output OUTPUT] scenario

Arguments:
  scenario             Scenario name.

Options:
  -h, --help           Show this help and exit.
  --format {json,csv}  Output format.
  --output OUTPUT      Destination file; stdout if omitted.
```

## `LANIP lab import`

```text
Usage: LANIP lab import [-h] file

Arguments:
  file        JSON file.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab network`

```text
Usage: LANIP lab network [-h] {create} ...

Arguments:
  {create}
    create    Create an empty scenario.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab network create`

```text
Usage: LANIP lab network create [-h] --name NAME [--cidr CIDR]

Options:
  -h, --help   Show this help and exit.
  --name NAME  Scenario name.
  --cidr CIDR  Virtual CIDR.
```

## `LANIP lab device`

```text
Usage: LANIP lab device [-h] {add,delete} ...

Arguments:
  {add,delete}
    add         Add a device.
    delete      Delete a device.

Options:
  -h, --help    Show this help and exit.
```

## `LANIP lab device add`

```text
Usage: LANIP lab device add [-h] --ip IP --mac MAC [--alias ALIAS] [--name NAME] [--inactive]
                            scenario

Arguments:
  scenario       Scenario.

Options:
  -h, --help     Show this help and exit.
  --ip IP        Simulated IPv4.
  --mac MAC      Simulated MAC.
  --alias ALIAS  Alias.
  --name NAME    Name.
  --inactive     Create it inactive.
```

## `LANIP lab device delete`

```text
Usage: LANIP lab device delete [-h] scenario device

Arguments:
  scenario    Scenario.
  device      ID, IP, MAC or alias.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab evolve`

```text
Usage: LANIP lab evolve [-h] --seconds SECONDS

Options:
  -h, --help         Show this help and exit.
  --seconds SECONDS  Virtual seconds.
```

## `LANWIRE`

```text
Usage: LANWIRE [-h] [--version] [--database ARCHIVO.db] [--gui | -tui | --cli] COMANDO ...

Physical management, IDF, wiring and topology for the LANCTL suite.

Arguments:
  COMANDO
    tui                  Open the full-screen interface.
    cli                  Open the interactive console.
    help                 Show LANWIRE command help.
    list (ls)            List identifiers.
    seed                 Load the initial test topology.
    show                 Show an identifier.
    add                  Generate the next IDF.
    idf                  Create identifiers with a complete physical profile.
    reserve              Reserve an IDF.
    element              Query or update an element's data and ports.
    delete (del)         Delete an IDF.
    graph (map)          Show the physical topology.
    prefix               Manage letter sets.

Options:
  -h, --help             Show this help and exit.
  --version              Show the common suite version and exit.
  --database ARCHIVO.db  Physical IDF database; defaults to physical/idf.db in the shared root.
  --gui                  Open the desktop graphical interface.
  -tui, --tui            Open the full-screen interface.
  --cli, -cli            Open the LANWIRE interactive console.
```

## `LANWIRE tui`

```text
Usage: LANWIRE tui [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE cli`

```text
Usage: LANWIRE cli [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE help`

```text
Usage: LANWIRE help [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE list`

```text
Usage: LANWIRE list [-h] [prefix]

Arguments:
  prefix      Filter by IDF prefix.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE seed`

```text
Usage: LANWIRE seed [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE show`

```text
Usage: LANWIRE show [-h] idf

Arguments:
  idf         Physical identifier to query.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE add`

```text
Usage: LANWIRE add [-h] [--digits {2,3,4,5}] [-more N] prefix

Arguments:
  prefix              Physical element type prefix.

Options:
  -h, --help          Show this help and exit.
  --digits {2,3,4,5}  Number of counter digits (2 to 5).
  -more, --more N     Create N consecutive IDFs.
```

## `LANWIRE idf`

```text
Usage: LANWIRE idf [-h] {list,types,show,edit,delete,del,new,add} ...

Arguments:
  {list,types,show,edit,delete,del,new,add}
    list                      List prefixes or the IDFs of a prefix.
    types                     List available physical profiles.
    show                      Query a prefix or IDF.
    edit                      Edit a prefix or IDF data.
    delete (del)              Delete an IDF.
    new                       Assign a physical profile to a prefix.
    add                       Create an IDF using the assigned prefix profile.

Options:
  -h, --help                  Show this help and exit.
```

## `LANWIRE idf list`

```text
Usage: LANWIRE idf list [-h] [prefix]

Arguments:
  prefix      Prefix whose elements are listed.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE idf types`

```text
Usage: LANWIRE idf types [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE idf show`

```text
Usage: LANWIRE idf show [-h] code

Arguments:
  code        Specific prefix or IDF.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE idf edit`

```text
Usage: LANWIRE idf edit [-h] [-type ELEMENT_TYPE] [-name NAME] [-alias ALIAS]
                        [-description DESCRIPTION]
                        code [CAMPO=VALOR ...]

Arguments:
  code                      Specific prefix or IDF.
  CAMPO=VALOR               IDF data.

Options:
  -h, --help                Show this help and exit.
  -type ELEMENT_TYPE        New prefix profile.
  -name NAME                Prefix name.
  -alias ALIAS              Prefix alias.
  -description DESCRIPTION  Prefix description.
```

## `LANWIRE idf delete`

```text
Usage: LANWIRE idf delete [-h] code

Arguments:
  code        Specific IDF; does not delete prefixes.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE idf new`

```text
Usage: LANWIRE idf new [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION]
                       -type ELEMENT_TYPE
                       code

Arguments:
  code                        Prefix for new or exact IDF for add.

Options:
  -h, --help                  Show this help and exit.
  -name NAME                  Record name.
  -alias ALIAS                Optional alias.
  -description, -descriptionn DESCRIPTION
                              Optional description.
  -type ELEMENT_TYPE          Physical profile.
```

## `LANWIRE idf add`

```text
Usage: LANWIRE idf add [-h] [-name NAME] [-alias ALIAS] [-description DESCRIPTION] code

Arguments:
  code                        Prefix for new or exact IDF for add.

Options:
  -h, --help                  Show this help and exit.
  -name NAME                  Record name.
  -alias ALIAS                Optional alias.
  -description, -descriptionn DESCRIPTION
                              Optional description.
```

## `LANWIRE reserve`

```text
Usage: LANWIRE reserve [-h] idf [CLAVE=VALOR ...]

Arguments:
  idf          Exact IDF to reserve.
  CLAVE=VALOR  Optional initial data.

Options:
  -h, --help   Show this help and exit.
```

## `LANWIRE element`

```text
Usage: LANWIRE element [-h] idf [CAMPO=VALOR ...]

Arguments:
  idf          IDF to query or update.
  CAMPO=VALOR  Physical fields to modify.

Options:
  -h, --help   Show this help and exit.
```

## `LANWIRE delete`

```text
Usage: LANWIRE delete [-h] idf

Arguments:
  idf         IDF to delete.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE graph`

```text
Usage: LANWIRE graph [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE prefix`

```text
Usage: LANWIRE prefix [-h] {list,ls,show,set,delete,del} ...

Arguments:
  {list,ls,show,set,delete,del}
    list (ls)                 List definitions.
    show                      Show a definition.
    set                       Create or update a definition.
    delete (del)              Delete a definition.

Options:
  -h, --help                  Show this help and exit.
```

## `LANWIRE prefix list`

```text
Usage: LANWIRE prefix list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE prefix show`

```text
Usage: LANWIRE prefix show [-h] letters

Arguments:
  letters     Prefix letters.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE prefix set`

```text
Usage: LANWIRE prefix set [-h] letters name [description]

Arguments:
  letters      Prefix letters.
  name         Descriptive type name.
  description  Optional description.

Options:
  -h, --help   Show this help and exit.
```

## `LANWIRE prefix delete`

```text
Usage: LANWIRE prefix delete [-h] letters

Arguments:
  letters     Prefix letters to delete.

Options:
  -h, --help  Show this help and exit.
```

## `LANRACK`

```text
Usage: LANRACK [-h] [--version] [--database ARCHIVO.db] [--gui | -tui | --cli]
               {list,ls,show,dimensions,elements,add-element,element} ...

Display racks and their equipment.

Arguments:
  {list,ls,show,dimensions,elements,add-element,element}
    list (ls)                 List available racks.
    show                      Show a rack and its occupants.
    dimensions                Edit the rack height and mounting width.
    elements                  List all elements, locations and trays.
    add-element               Create a shared physical element.
    element                   Edit or relocate an element without changing its links.

Options:
  -h, --help                  Show this help and exit.
  --version                   Show the common suite version and exit.
  --database ARCHIVO.db       Shared physical IDF database.
  --gui                       Open the desktop graphical interface.
  -tui, --tui                 Open the full-screen interface.
  --cli, -cli                 Open the interactive console.
```

## `LANRACK list`

```text
Usage: LANRACK list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANRACK show`

```text
Usage: LANRACK show [-h] rack

Arguments:
  rack        Rack ID or name.

Options:
  -h, --help  Show this help and exit.
```

## `LANRACK dimensions`

```text
Usage: LANRACK dimensions [-h] --units UNITS --width-inches {10,19,21,23} rack

Arguments:
  rack                        Rack ID.

Options:
  -h, --help                  Show this help and exit.
  --units UNITS               Height from 4 to 52 U.
  --width-inches {10,19,21,23}
                              Mounting width in inches.
```

## `LANRACK elements`

```text
Usage: LANRACK elements [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANRACK add-element`

```text
Usage: LANRACK add-element [-h] --kind KIND --prefix PREFIX [--name NAME]

Options:
  -h, --help       Show this help and exit.
  --kind KIND      Equipment, panel, outlet or tray profile.
  --prefix PREFIX  IDF prefix.
  --name NAME      Element name.
```

## `LANRACK element`

```text
Usage: LANRACK element [-h] [--name NAME] [--description DESCRIPTION]
                       [--placement {inside,environment,independent,hosted}] [--rack RACK]
                       [--unit UNIT] [--height-u HEIGHT_U] [--tray TRAY]
                       element

Arguments:
  element                     Element ID.

Options:
  -h, --help                  Show this help and exit.
  --name NAME                 Element name.
  --description DESCRIPTION   Element description.
  --placement {inside,environment,independent,hosted}
                              Physical classification.
  --rack RACK                 Destination rack ID.
  --unit UNIT                 Starting mounting unit.
  --height-u HEIGHT_U         Height occupied by the element.
  --tray TRAY                 Tray housing the device.
```

## `LANACCESS`

```text
Usage: LANACCESS [-h] [--version] [--database DATABASE] [--store STORE]
                 [--cipher {auto,dpapi,portable}] [--scope {program,windows,project}]
                 [--project-dir PROJECT_DIR] [--gui | -tui | --cli]
                 {remote-setup,list,ls,show,set,delete,del,credential,doctor,settings,protocol,user} ...

Manage encrypted credentials in the LANCTL environment.

Arguments:
  {remote-setup,list,ls,show,set,delete,del,credential,doctor,settings,protocol,user}
    remote-setup              Create the first remote service account on Windows (administrator
                              required).
    list (ls)                 List metadata; never secrets.
    show                      Show credential metadata.
    set                       Create or update a credential.
    delete (del)              Delete a credential.
    credential                Credential management, transport and recovery.
    doctor                    Check links and permissions without changing data.
    settings                  Show or select the shared store.
    protocol                  Store protocol summary.
    user                      Remote access users; not Windows accounts.

Options:
  -h, --help                  Show this help and exit.
  --version                   Show the common suite version and exit.
  --database DATABASE         LANCTL element database.
  --store STORE               Encrypted credential store.
  --cipher {auto,dpapi,portable}
                              Encryption provider; portable prompts for a password.
  --scope {program,windows,project}
                              Location; does not change permissions or copy secrets automatically.
  --project-dir PROJECT_DIR   Project directory for its independent store.
  --gui                       Open the desktop graphical interface.
  -tui, --tui                 Open the full-screen interface.
  --cli, -cli                 Open the interactive console.
```

## `LANACCESS remote-setup`

```text
Usage: LANACCESS remote-setup [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANACCESS list`

```text
Usage: LANACCESS list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANACCESS show`

```text
Usage: LANACCESS show [-h] credential_id

Arguments:
  credential_id  Credential identifier.

Options:
  -h, --help     Show this help and exit.
```

## `LANACCESS set`

```text
Usage: LANACCESS set [-h] --username USERNAME element protocol

Arguments:
  element                     Device IP, MAC, alias or ID.
  protocol                    Associated protocol, for example ssh.

Options:
  -h, --help                  Show this help and exit.
  --username, -user USERNAME  Remote username.
```

## `LANACCESS delete`

```text
Usage: LANACCESS delete [-h] credential_id

Arguments:
  credential_id  Credential identifier.

Options:
  -h, --help     Show this help and exit.
```

## `LANACCESS credential`

```text
Usage: LANACCESS credential [-h] {list,show,delete,set,export,import,copy,recover} ...

Arguments:
  {list,show,delete,set,export,import,copy,recover}
    list                      List metadata.
    show                      show by identifier.
    delete                    delete by identifier.
    set                       Save and link a credential.
    export                    Transport an encrypted store; never plaintext.
    import                    Transport an encrypted store; never plaintext.
    copy                      Copy to another store and verify; preserve the source.
    recover                   Repair missing references; do not delete or overwrite secrets.

Options:
  -h, --help                  Show this help and exit.
```

## `LANACCESS credential list`

```text
Usage: LANACCESS credential list [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANACCESS credential show`

```text
Usage: LANACCESS credential show [-h] credential_id

Arguments:
  credential_id

Options:
  -h, --help     Show this help and exit.
```

## `LANACCESS credential delete`

```text
Usage: LANACCESS credential delete [-h] credential_id

Arguments:
  credential_id

Options:
  -h, --help     Show this help and exit.
```

## `LANACCESS credential set`

```text
Usage: LANACCESS credential set [-h] --username USERNAME element protocol

Arguments:
  element
  protocol

Options:
  -h, --help           Show this help and exit.
  --username USERNAME
```

## `LANACCESS credential export`

```text
Usage: LANACCESS credential export [-h] file

Arguments:
  file

Options:
  -h, --help  Show this help and exit.
```

## `LANACCESS credential import`

```text
Usage: LANACCESS credential import [-h] file

Arguments:
  file

Options:
  -h, --help  Show this help and exit.
```

## `LANACCESS credential copy`

```text
Usage: LANACCESS credential copy [-h] [--target-cipher {dpapi,portable}] file

Arguments:
  file

Options:
  -h, --help                  Show this help and exit.
  --target-cipher {dpapi,portable}
```

## `LANACCESS credential recover`

```text
Usage: LANACCESS credential recover [-h] [--yes]

Options:
  -h, --help  Show this help and exit.
  --yes       Apply repairs; diagnose only by default.
```

## `LANACCESS doctor`

```text
Usage: LANACCESS doctor [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANACCESS settings`

```text
Usage: LANACCESS settings [-h] [--yes] [{show,use-store}] [file]

Arguments:
  {show,use-store}
  file

Options:
  -h, --help        Show this help and exit.
  --yes             Confirm changing the configured store without moving secrets.
```

## `LANACCESS protocol`

```text
Usage: LANACCESS protocol [-h] [--port PORT] [--driver DRIVER]
                          [{list,configure}] [element] [protocol]

Arguments:
  {list,configure}
  element
  protocol

Options:
  -h, --help        Show this help and exit.
  --port PORT       Port 1-65535.
  --driver DRIVER   Protocol driver.
```

## `LANACCESS user`

```text
Usage: LANACCESS user [-h] [--role {viewer,operator,manager,administrator}] [--yes]
                      {list,add,enable,disable,delete} [username]

Arguments:
  {list,add,enable,disable,delete}
  username

Options:
  -h, --help                  Show this help and exit.
  --role {viewer,operator,manager,administrator}
  --yes                       Confirm deletion.
```

## `LANMON`

```text
Usage: LANMON [-h] [--version] [--project PROJECT] [--permanent] [--duration DURATION]
              [--mode {permanent,temporary,diagnostic,once}]
              [--authority {observe,operate,administer}] [--json] [--yes] [--interval INTERVAL]
              [--every EVERY] [--group GROUP] [--type {presence,services,ports,identity,smb,full}]
              [--fast] [--unknown] [--follow] [--sessions SESSIONS]
              [--incidents-store INCIDENTS_STORE] [--lock LOCK] [--monitor-db MONITOR_DB]
              [--profiles PROFILES] [--assignments-store ASSIGNMENTS_STORE] [--profile PROFILE]
              [--priority {low,normal,high,critical}] [--check CHECK] [--presence PRESENCE]
              [--discovery DISCOVERY] [--services SERVICES] [--deep DEEP] [--workers WORKERS]
              [--timeout TIMEOUT] [--gui | --cli | --tui] [--source {all,program,project}]
              [--limit LIMIT] [--window] [--level LEVEL]
              [words ...]

Monitoring, events and incidents for the LANCTL suite.

Arguments:
  words                       logs, events, status, attach, detach, once, session, incidents,
                              service o foreground.

Options:
  -h, --help                  Show this help and exit.
  --version                   Show the common suite version and exit.
  --project PROJECT           Opción operativa del monitor.
  --permanent                 Opción operativa del monitor.
  --duration DURATION         Opción operativa del monitor.
  --mode {permanent,temporary,diagnostic,once}
                              Opción operativa del monitor.
  --authority {observe,operate,administer}
                              Opción operativa del monitor.
  --json                      Opción operativa del monitor.
  --yes                       Opción operativa del monitor.
  --interval INTERVAL         Opción operativa del monitor.
  --every EVERY               Opción operativa del monitor.
  --group GROUP               Opción operativa del monitor.
  --type {presence,services,ports,identity,smb,full}
                              Opción operativa del monitor.
  --fast                      Opción operativa del monitor.
  --unknown                   Opción operativa del monitor.
  --follow                    Opción operativa del monitor.
  --sessions SESSIONS         Runtime session state.
  --incidents-store INCIDENTS_STORE
                              Runtime incident state.
  --lock LOCK                 Monitor singleton lock.
  --monitor-db MONITOR_DB     Monitor SQLite repository.
  --profiles PROFILES         Custom profiles.
  --assignments-store ASSIGNMENTS_STORE
                              Persistent assignments.
  --profile PROFILE           Monitor profile.
  --priority {low,normal,high,critical}
                              Assignment priority.
  --check CHECK               Check ping, arp or port:NN.
  --presence PRESENCE         Presence interval.
  --discovery DISCOVERY       Discovery interval.
  --services SERVICES         Service interval.
  --deep DEEP                 Deep scan interval.
  --workers WORKERS           Profile workers.
  --timeout TIMEOUT           Profile timeout.
  --gui                       Open the desktop graphical interface.
  --cli, -cli                 Open the command console.
  --tui, -tui                 Open the tabular event viewer.
  --source {all,program,project}
                              Log source.
  --limit LIMIT               Maximum number of events (1-1000).
  --window                    Open logs in another terminal and follow the common log.
  --level LEVEL               Minimum level (1-59); preserve lines without a level.
```
