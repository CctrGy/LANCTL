# Referencia completa del CLI LANCTL

Documento generado automáticamente desde los parsers de la aplicación.
No lo edites manualmente; ejecuta `python tools/generate_cli_reference.py`.

## `LANCTL`

```text
Usage: LANCTL [-h] [--version] [--cli] [-tui] LAUNCHER ...

Orquestador raíz de las aplicaciones de la suite LANCTL.

Arguments:
  LAUNCHER
    lanip (ip)        Inventario lógico, descubrimiento, IP, MAC y servicios.
    lanwire (wire)    Cableado, puertos, paneles y topología física.
    lanrack (rack)    Salas técnicas, racks, unidades U y equipos.
    lanaccess (access)
                      Usuarios, credenciales y accesos remotos.
    lanmon (monitor)  Monitorización, eventos, incidencias e historial.

Options:
  -h, --help          Show this help and exit.
  --version           Muestra la versión común de la suite y termina.
  --cli               Abre la consola principal.
  -tui, --tui         Abre el TUI principal.
```

## `LANIP`

```text
Usage: LANIP [-h] [--version] [--quiet | --verbose] [--gui] [--cli] [-tui [VENTANA]]
             [-project ARCHIVO.vlf]
             COMANDO ...

Logical control of LAN devices and infrastructure.

Arguments:
  COMANDO
    ephemeral (-e)            Escanea activos sin leer ni guardar ningún inventario.
    list                      Escanea la LAN y muestra dispositivos activos e históricos.
    recurrent                 Consulta los elementos recurrentes conocidos por LANCTL.
    ping                      Comprueba puntualmente si un elemento responde por PING o ARP.
    open (connect)            Abre un elemento con un cliente acorde al protocolo.
    settings                  Consulta o modifica la configuración persistente de LANCTL.
    call                      Resuelve un alias, una IP o una MAC a los datos del dispositivo.
    search                    Busca dispositivos por alias, nombre, IP o MAC.
    scan                      Inspecciona en profundidad un único elemento de la LAN.
    cnf                       Asigna el estado CNF de un elemento por IP, MAC o alias.
    credential (credentials, auth)
                              Asocia credenciales cifradas a un elemento y protocolo.
    GATEWAY (gateway)         Consulta y configura el gateway mediante TR-064.
    downloadSettings (downloadsettings, download-settings)
                              Alias heredado de «GATEWAY downloadSettings».
    protocol                  Consulta o configura un protocolo de un elemento.
    ssh                       Abre SSH o ejecuta una consulta show de solo lectura.
    radmin                    Configura, comprueba o abre Radmin Viewer.
    wol                       Enciende equipos mediante Wake-on-LAN y ejecuta secuencias seguras.
    history                   Consulta eventos estructurados del proyecto VLF activo.
    monitor                   Opera sesiones y checks del monitor LAN.
    access                    Configura acceso remoto LAN seguro por SSH y HTTPS.
    smb                       Descubre y abre recursos SMB de Windows.
    terminal (cli)            Abre la terminal propia de un elemento según su protocolo.
    switch                    Planifica comandos Cisco filtrados, remapeados y clasificados.
    group                     Crea, edita y consulta grupos de elementos.
    element                   Edita uno o varios campos de un elemento identificado por IP, MAC o
                              alias.
    project (projects)        Crea, actualiza e inspecciona proyectos LANCTL .vlf.
    plugin (plugins, addon, addons)
                              Gestiona complementos unificados LANCTL .lcp.
    language (languages, lang)
                              Manage LANCTL interface languages.
    error (errors)            Consulta el catálogo por identificador 0eXXXXXXXX.
    database (db)             Diagnostica y exporta datos.
    demo                      Genera un recorrido reproducible sin depender de una red real.
    lanwire (wire)            Abre LANWIRE o ejecuta uno de sus comandos sobre la base física
                              compartida.
    lab                       Gestiona redes LAN simuladas sin tráfico real.

Options:
  -h, --help                  Show this help and exit.
  --version                   Muestra la versión y termina.
  --quiet                     Omite la salida correcta; conserva errores.
  --verbose                   Añade diagnóstico de ejecución a stderr.
  --gui                       Abre la GUI heredada (solo código fuente y con
                              LANCTL_ENABLE_LEGACY_GUI=1).
  --cli                       Open the persistent interactive LANCTL terminal.
  -tui [VENTANA], --tui [VENTANA]
                              Open the advanced full-screen terminal interface. Puede abrir
                              directamente PLUGINS, PROJECTS o SETTINGS.
  -project ARCHIVO.vlf, --project ARCHIVO.vlf
                              Selecciona un proyecto VLF antes de abrir el TUI o ejecutar un
                              comando.
```

## `LANIP ephemeral`

```text
Usage: LANIP ephemeral [-h] [--fast | --normal | --accurate] [--range NETWORK] [--resolve-names]
                       [--ports PORTS] [--json] [--workers WORKERS] [--timeout TIMEOUT]
                       [--max-hosts MAX_HOSTS] [--scan-order {ascending,descending,random}]

Ejecuta el descubrimiento real en una sesión aislada en memoria. No abre, modifica ni guarda proyectos o bases de dispositivos.

Options:
  -h, --help                  Show this help and exit.
  --fast                      Prioriza un barrido ARP rápido.
  --normal                    Combina ICMP, ARP y descubrimiento de servicios.
  --accurate                  Añade reintentos y reconocimiento más profundo.
  --range NETWORK             Rango CIDR que se explorará solo durante esta ejecución.
  --resolve-names             Resuelve nombres sin almacenarlos.
  --ports PORTS               Puertos TCP opcionales, por ejemplo 22,80,443.
  --json                      Devuelve la sesión como JSON.
  --workers WORKERS           Sondeos simultáneos.
  --timeout TIMEOUT           Tiempo máximo base por sondeo, en segundos.
  --max-hosts MAX_HOSTS       Límite defensivo de direcciones autorizadas.
  --scan-order {ascending,descending,random}
                              Orden de exploración de las direcciones.
```

## `LANIP list`

```text
Usage: LANIP list [-h] [--network NETWORK] [--database DATABASE] [--groups GROUPS]
                  [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT] [-recurrent] [--where WHERE]
                  [-w WORKERS] [-t TIMEOUT] [--scan-order {ascending,descending,random}]
                  [--include-unknown] [--resolve-names] [--max-hosts MAX_HOSTS]
                  [--discovery {icmp,arp,hybrid}]
                  [--profile {fast,normal,accurate} | --fast | --normal | --accurate]
                  [--progress | --no-progress] [--show-discovery] [--include-arp-cache]
                  [--show-detection] [--active | -disconnected] [-basic] [-cnf {O,X,-,S,F}]
                  [-group GRUPO] [-dhcp]

Realiza un escaneo básico de IP/MAC, actualiza la base de datos por MAC y muestra también los equipos no detectados.

Options:
  -h, --help                  Show this help and exit.
  --network NETWORK           Red CIDR. Por defecto detecta la LAN como /24.
  --database DATABASE         Archivo JSON de elementos.
  --groups GROUPS             Archivo JSON de grupos.
  -f {table,json,csv,html,xml,yaml}, --format {table,json,csv,html,xml,yaml}
                              Formato de salida (por defecto: table).
  -o OUTPUT, --output OUTPUT  Guarda la salida en un archivo.
  -recurrent, --recurrent     Lista los elementos recurrentes sin escanear la LAN ni mostrar IP.
  --where WHERE               Consulta combinable, por ejemplo: "active and group=IOT and
                              vendor~Amazon".
  -w WORKERS, --workers WORKERS
                              Comprobaciones simultáneas.
  -t TIMEOUT, --timeout TIMEOUT
                              Timeout base en segundos por operación y host; el perfil puede
                              ajustarlo.
  --scan-order {ascending,descending,random}
                              Orden de sondeo de IP: ascending, descending o random.
  --include-unknown           Incluye hosts activos aunque todavía no tengan MAC.
  --resolve-names             Resuelve y guarda nombres DNS de los elementos detectados.
  --max-hosts MAX_HOSTS       Máximo de hosts permitido en un escaneo.
  --discovery {icmp,arp,hybrid}
                              Método: icmp, arp activo o hybrid (por defecto según settings).
  --profile {fast,normal,accurate}
                              Perfil completo de escaneo: fast, normal o accurate.
  --fast                      Escaneo ARP rápido.
  --normal                    Escaneo híbrido equilibrado.
  --accurate                  Escaneo profundo con varios métodos.
  --progress                  Muestra el progreso interactivo.
  --no-progress               Oculta el progreso.
  --show-discovery            Añade una columna con ICMP, ARP, LOCAL, BASIC o CACHE.
  --include-arp-cache         Importa vecinos ARP en caché como CACHE no verificada; no cuentan
                              como activos.
  --show-detection            Añade los métodos históricos y la fecha de última detección.
  --active, -active, -connected, --connected, -conected
                              Muestra solo los dispositivos activos en el escaneo actual.
  -disconnected, --disconnected, -offline
                              Muestra solo los dispositivos no detectados actualmente.
  -basic, --basic             Vista reducida: IP, alias y descripción.
  -cnf {O,X,-,S,F}, --cnf-state {O,X,-,S,F}
                              Filtra por estado CNF: O, X, -, S o F.
  -group GRUPO, --group GRUPO
                              Muestra solo los elementos de un grupo.
  -dhcp, --dhcp-only          Muestra solo IP incluidas en el rango DHCP configurado.
```

## `LANIP recurrent`

```text
Usage: LANIP recurrent [-h] -list [-f {table,json,csv,html,xml,yaml}] [-o OUTPUT]

Muestra identidades recurrentes por MAC. No incluye IP porque puede cambiar en cada LAN.

Options:
  -h, --help                  Show this help and exit.
  -list, --list               Lista todos los elementos recurrentes sin sus IP.
  -f {table,json,csv,html,xml,yaml}, --format {table,json,csv,html,xml,yaml}
                              Formato de salida (por defecto: table).
  -o OUTPUT, --output OUTPUT  Guarda la salida en un archivo.
```

## `LANIP ping`

```text
Usage: LANIP ping [-h] [--method {auto,ping,arp} | --ping | --arp] [--timeout TIMEOUT] [--json]
                  [--database DATABASE]
                  selector

Diagnostica un único elemento sin modificar la base de datos. PING prueba ICMP; ARP realiza una consulta activa en la LAN; AUTO combina ambos métodos.

Arguments:
  selector                  IP, MAC, alias o nombre registrado.

Options:
  -h, --help                Show this help and exit.
  --method {auto,ping,arp}  Buscador utilizado: auto, ping o arp (por defecto: auto).
  --ping                    Usa únicamente una solicitud ICMP.
  --arp                     Usa únicamente una solicitud ARP activa.
  --timeout TIMEOUT         Tiempo máximo de cada comprobación, en segundos.
  --json                    Devuelve el diagnóstico como JSON.
  --database DATABASE       Archivo JSON de elementos.
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
  selector                    IP, MAC o alias del elemento.
  {auto,ssh,tr-064,telnet,http,https,ftp,rdp,rtsp,smb,radmin}
                              Protocolo o detección automática.

Options:
  -h, --help                  Show this help and exit.
  --port PORT                 Puerto alternativo.
  --path PATH                 Ruta HTTP/FTP/RTSP o recurso SMB.
  --mode {control,view,file,shutdown,chat,voice,message,telnet}
                              Modo de conexión Radmin.
  --through THROUGH           Servidor Radmin intermedio HOST:PUERTO.
  --fullscreen                Abre control o vista a pantalla completa.
  --color-depth {24,16,8,4,2,1}
                              Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).
  --updates UPDATES           Máximo de actualizaciones de pantalla por segundo (1-120).
  --phonebook PHONEBOOK       Ruta de phonebook Radmin .rpb.
  --phonebook-id PHONEBOOK_ID
                              Identificador de entrada dentro del phonebook de Radmin.
  --dry-run                   Muestra el destino sin abrirlo.
  --database DATABASE         Archivo JSON de elementos.
  --store STORE               Almacén cifrado de credenciales.
```

## `LANIP settings`

```text
Usage: LANIP settings [-h] [-range CIDR] [-list-fields CAMPO [CAMPO ...]] [-dhcp-range INICIO-FIN]
                      [-credentials ARCHIVO] [-discovery {icmp,arp,hybrid}]
                      [--scan-profile {fast,normal,accurate}] [--progress {on,off}]
                      [--service-identification {on,off}] [--workers WORKERS] [--timeout TIMEOUT]
                      [--scan-order {ascending,descending,random}] [--max-hosts MAX_HOSTS]
                      [--database ARCHIVO] [--physical-database ARCHIVO] [--groups ARCHIVO]
                      [--log DIRECTORIO] [--error-log-level 1-59]
                      [--projects-directory DIRECTORIO] [-save-mode MODO] [-save-interval MINUTOS]
                      [-log-cleanup {on,off}] [-log-retention-days DÍAS]
                      [--remote-access {on,off}] [--remote-bind IP] [--remote-cidr CIDR]
                      [--remote-port REMOTE_PORT] [--remote-password-auth {on,off}]
                      [--remote-backend {service,user}]
                      [--remote-forced-view {off,gui,tui,plugins,projects,settings}]
                      [--tui-key ACCIÓN=TECLA] [--tui-footer-buttons ACCIONES]
                      [--tui-footer-button ACCIÓN=on|off]

Options:
  -h, --help                  Show this help and exit.
  -range CIDR                 Rango LAN predeterminado, por ejemplo 192.168.1.1/24.
  -list-fields CAMPO [CAMPO ...], --list-fields CAMPO [CAMPO ...], -list CAMPO [CAMPO ...]
                              Columnas mostradas por list, separadas por espacios o comas.
  -dhcp-range INICIO-FIN, --dhcp-range INICIO-FIN, -dhcp INICIO-FIN
                              Rango DHCP manual. Usa 'off' para dejarlo sin configurar.
  -credentials ARCHIVO, --credentials ARCHIVO
                              Ruta del almacén de credenciales cifradas.
  -discovery {icmp,arp,hybrid}, --discovery {icmp,arp,hybrid}
                              Método predeterminado utilizado por list.
  --scan-profile {fast,normal,accurate}
                              Perfil predeterminado de list: fast, normal o accurate.
  --progress {on,off}         Activa o desactiva el progreso interactivo.
  --service-identification {on,off}
                              Activa o desactiva el reconocimiento de servicios en scan.
  --workers WORKERS           Concurrencia predeterminada de los escaneos.
  --timeout TIMEOUT           Timeout predeterminado por operación de red.
  --scan-order {ascending,descending,random}
                              Orden predeterminado de sondeo: ascending, descending o random.
  --max-hosts MAX_HOSTS       Máximo de hosts autorizado por escaneo.
  --database ARCHIVO          Ruta del inventario de elementos.
  --physical-database ARCHIVO
                              Ruta de la base física SQLite administrada exclusivamente por
                              LANWIRE.
  --groups ARCHIVO            Ruta de la base de grupos.
  --log DIRECTORIO            Directorio de registros.
  --error-log-level 1-59      Nivel mínimo de ErrorEvent escrito en el log (1 incluye diagnóstico
                              detallado).
  --projects-directory DIRECTORIO
                              Carpeta predeterminada para nombres de proyecto VLF relativos.
  -save-mode MODO, --save-mode MODO
                              Política de guardado VLF. Usa 'list' para consultar las opciones
                              integradas y las aportadas por plugins.
  -save-interval MINUTOS, --save-interval MINUTOS
                              Intervalo de automatic.timeToSave en minutos (mínimo 0.1).
  -log-cleanup {on,off}, --log-cleanup {on,off}
                              Activa o desactiva la limpieza automática de logs antiguos.
  -log-retention-days DÍAS, --log-retention-days DÍAS
                              Días durante los que se conservan los archivos de log.
  --remote-access {on,off}    Activa el acceso SSH restringido.
  --remote-bind IP            IPv4 local de escucha SSH.
  --remote-cidr CIDR          Red de origen autorizada.
  --remote-port REMOTE_PORT   Puerto del servidor SSH remoto.
  --remote-password-auth {on,off}
                              Permite o bloquea autenticación SSH mediante contraseña.
  --remote-backend {service,user}
                              Ejecuta el backend como servicio persistente o proceso de usuario.
  --remote-forced-view {off,gui,tui,plugins,projects,settings}
                              Vista predeterminada para root forced-view.
  --tui-key ACCIÓN=TECLA      Asigna una tecla a una acción del TUI. Puede repetirse.
  --tui-footer-buttons ACCIONES
                              Acciones visibles en la barra inferior, separadas por comas; usa all
                              para todas.
  --tui-footer-button ACCIÓN=on|off
                              Muestra u oculta una acción concreta de la barra inferior. Puede
                              repetirse.
```

## `LANIP call`

```text
Usage: LANIP call [-h]
                  [-f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}]
                  [--json] [--database DATABASE]
                  selector

Arguments:
  selector                    Alias, IP o MAC del dispositivo.

Options:
  -h, --help                  Show this help and exit.
  -f {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}, --field {ip,cnf,mac,alias,name,group,description,manufacturer,default-name,device-id,protocols}
                              Dato devuelto (por defecto: ip).
  --json                      Devuelve el registro completo como JSON.
  --database DATABASE         Archivo JSON de elementos.
```

## `LANIP search`

```text
Usage: LANIP search [-h] [--json] [--database DATABASE] selector

Arguments:
  selector             Alias, nombre, IP o MAC exactos.

Options:
  -h, --help           Show this help and exit.
  --json               Devuelve el registro completo como JSON para scripts.
  --database DATABASE  Archivo JSON de elementos.
```

## `LANIP scan`

```text
Usage: LANIP scan [-h] [--ports LISTA] [--all-ports] [--timeout TIMEOUT] [--workers WORKERS]
                  [--banners] [--identify] [--json] [--database DATABASE]
                  selector

Resuelve un elemento por IP, MAC o alias y comprueba identidad, disponibilidad y puertos TCP. No modifica el dispositivo.

Arguments:
  selector             IP, MAC o alias registrado en LANCTL.

Options:
  -h, --help           Show this help and exit.
  --ports LISTA        Puertos o rangos: 22,80,443,8000-8100 (por defecto: common).
  --all-ports          Autoriza explícitamente el escaneo TCP 1-65535.
  --timeout TIMEOUT    Tiempo máximo por conexión, en segundos.
  --workers WORKERS    Número máximo de conexiones simultáneas.
  --banners            Lee banners pasivos; no envía sondas específicas de protocolo.
  --identify           Reconoce servicios y deduce el tipo de dispositivo con evidencias.
  --json               Salida JSON.
  --database DATABASE  Archivo JSON de elementos.
```

## `LANIP cnf`

```text
Usage: LANIP cnf [-h] [--database DATABASE] selector [value]

Arguments:
  selector             IP, MAC o alias del elemento.
  value                O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) o F (FIXED). Sin valor
                       libera F y restaura O.

Options:
  -h, --help           Show this help and exit.
  --database DATABASE  Archivo JSON de elementos.
```

## `LANIP credential`

```text
Usage: LANIP credential [-h] [-user USERNAME] [--database DATABASE] [--store STORE]
                        selector [{set,list,delete}] [protocol]

Arguments:
  selector                    IP, MAC o alias del elemento.
  {set,list,delete}           Operación sobre la credencial.
  protocol                    Protocolo, por ejemplo tr-064.

Options:
  -h, --help                  Show this help and exit.
  -user USERNAME, --username USERNAME
                              Nombre de usuario remoto.
  --database DATABASE         Archivo JSON de elementos.
  --store STORE               Almacén cifrado de credenciales.
```

## `LANIP GATEWAY`

```text
Usage: LANIP GATEWAY [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    downloadSettings (downloadsettings, download-settings)
                              Descarga las opciones LAN y DHCP interesantes para configuración.

Options:
  -h, --help                  Show this help and exit.
```

## `LANIP GATEWAY downloadSettings`

```text
Usage: LANIP GATEWAY downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]
                                      [--store STORE]

Options:
  -h, --help           Show this help and exit.
  --port PORT          Puerto TR-064 del router.
  --timeout TIMEOUT    Tiempo máximo de espera en segundos.
  --database DATABASE  Archivo JSON de elementos.
  --store STORE        Almacén cifrado de credenciales.
```

## `LANIP downloadSettings`

```text
Usage: LANIP downloadSettings [-h] [--port PORT] [--timeout TIMEOUT] [--database DATABASE]
                              [--store STORE]
                              [gateway]

Arguments:
  gateway              IP, MAC o alias del router.

Options:
  -h, --help           Show this help and exit.
  --port PORT          Puerto TR-064 del router.
  --timeout TIMEOUT    Tiempo máximo de espera en segundos.
  --database DATABASE  Archivo JSON de elementos.
  --store STORE        Almacén cifrado de credenciales.
```

## `LANIP protocol`

```text
Usage: LANIP protocol [-h] [--port PORT] [--driver DRIVER] [--host-key HOST_KEY] [--kex KEX]
                      [--profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}]
                      [--database DATABASE]
                      selector {show,configure} protocol

Arguments:
  selector                    IP, MAC o alias.
  {show,configure}            Consulta o modifica el protocolo.
  protocol                    Protocolo que se configura.

Options:
  -h, --help                  Show this help and exit.
  --port PORT                 Puerto remoto.
  --driver DRIVER             Controlador del dispositivo.
  --host-key HOST_KEY         Algoritmo de clave de host permitido; se puede repetir.
  --kex KEX                   Algoritmo de intercambio de claves; se puede repetir.
  --profile {ssh_legacy_cisco_s300,ssh_esp32_rack_monitor}
                              Perfil SSH reutilizable.
  --database DATABASE         Archivo JSON de elementos.
```

## `LANIP ssh`

```text
Usage: LANIP ssh [-h] [--database DATABASE] [--store STORE] [--host HOST]
                 selector {probe,fingerprint,trust,open,show} [COMANDO ...]

Arguments:
  selector                    IP, MAC o alias.
  {probe,fingerprint,trust,open,show}
                              Operación SSH.
  COMANDO                     Huella o comando remoto, según la operación.

Options:
  -h, --help                  Show this help and exit.
  --database DATABASE         Archivo JSON de elementos.
  --store STORE               Almacén cifrado de credenciales.
  --host HOST                 IP candidata para probe/fingerprint, sin modificar la base de datos.
```

## `LANIP radmin`

```text
Usage: LANIP radmin [-h] [--mode {control,view,file,shutdown,chat,voice,message,telnet}]
                    [--port PORT] [--executable EXECUTABLE] [--through THROUGH] [--fullscreen]
                    [--color-depth {24,16,8,4,2,1}] [--updates UPDATES] [--phonebook PHONEBOOK]
                    [--phonebook-id PHONEBOOK_ID] [--database DATABASE] [--store STORE]
                    selector {probe,configure,open}

Arguments:
  selector                    IP, MAC o alias del elemento.
  {probe,configure,open}      Opción de configuración de Radmin Viewer.

Options:
  -h, --help                  Show this help and exit.
  --mode {control,view,file,shutdown,chat,voice,message,telnet}
                              Opción de configuración de Radmin Viewer.
  --port PORT                 Opción de configuración de Radmin Viewer.
  --executable EXECUTABLE     Ruta por dispositivo; usa 'auto' para detección automática.
  --through THROUGH           Servidor intermedio HOST:PUERTO.
  --fullscreen                Abre control o vista a pantalla completa.
  --color-depth {24,16,8,4,2,1}
                              Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).
  --updates UPDATES           Máximo de actualizaciones de pantalla por segundo (1-120).
  --phonebook PHONEBOOK       Phonebook .rpb administrado por Radmin.
  --phonebook-id PHONEBOOK_ID
                              Identificador de entrada dentro del phonebook de Radmin.
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
  words                       NAME [wakeup|status|shutdown|restart|sleep|hibernate|configure] o
                              sequence ...

Options:
  -h, --help                  Show this help and exit.
  -if CONDICIÓN, --if CONDICIÓN
                              Condición AND adicional (repetible).
  --if-all CONDICIÓN          Condición AND adicional.
  --if-any CONDICIÓN          Condición OR adicional.
  --if-not CONDICIÓN          Condición negada.
  -t SCHEDULE, --time SCHEDULE
                              Momento del apagado programado.
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
  --database DATABASE         Archivo JSON de elementos.
  --store STORE               Almacén cifrado de credenciales.
  --sequences SEQUENCES       Archivo transaccional de secuencias.
```

## `LANIP history`

```text
Usage: LANIP history [-h] [--all] [--commands] [--today] [--from FECHA] [--to FECHA]
                     [--type TYPES] [--source SOURCE] [--result RESULT] [--errors]
                     [--search SEARCH] [--limit LIMIT] [--reverse] [--format {table,json,csv}]
                     [selector]

Arguments:
  selector                   DeviceId, alias, nombre, MAC, IP actual o histórica.

Options:
  -h, --help                 Show this help and exit.
  --all                      Incluye eventos generales de toda la LAN.
  --commands                 En CLI interactiva muestra los comandos de la sesión.
  --today                    Limita la consulta al día local actual.
  --from FECHA               Fecha inicial YYYY-MM-DD.
  --to FECHA                 Fecha final YYYY-MM-DD.
  --type TYPES               Tipo canónico; se puede repetir.
  --source SOURCE            Filtra por origen.
  --result RESULT            Filtra por resultado.
  --errors                   Muestra únicamente errores.
  --search SEARCH            Busca texto seguro.
  --limit LIMIT              Máximo de eventos (1..10000).
  --reverse                  Orden descendente.
  --format {table,json,csv}  Formato de salida.
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
                              o foreground.

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
  --sessions SESSIONS         Estado runtime de sesiones.
  --incidents-store INCIDENTS_STORE
                              Estado runtime de incidencias.
  --lock LOCK                 Lock singleton del monitor.
  --monitor-db MONITOR_DB     Repositorio SQLite del monitor.
  --profiles PROFILES         Perfiles personalizados.
  --assignments-store ASSIGNMENTS_STORE
                              Asignaciones persistentes.
  --profile PROFILE           Perfil monitor.
  --priority {low,normal,high,critical}
                              Prioridad de asignación.
  --check CHECK               Check ping, arp o port:NN.
  --presence PRESENCE         Intervalo de presencia.
  --discovery DISCOVERY       Intervalo de descubrimiento.
  --services SERVICES         Intervalo de servicios.
  --deep DEEP                 Intervalo profundo.
  --workers WORKERS           Workers del perfil.
  --timeout TIMEOUT           Timeout del perfil.
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
  words                      init, status, enable, disable, configure, user, role, session, web o
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
  --scope {user,service}     Separa credenciales del usuario y del servicio permanente.
  --config CONFIG            Configuración remota separada.
  --users USERS              Almacén de usuarios remotos.
```

## `LANIP smb`

```text
Usage: LANIP smb [-h] [--network] [--group GROUP] [--timeout TIMEOUT] [--workers WORKERS]
                 [--anonymous] [--include-system] [--dry-run] [--yes] [--json]
                 [--database DATABASE] [--store STORE] [--storage STORAGE]
                 [name] [action] [resource] [{open,queue,connect}]

Arguments:
  name                  Servidor/dispositivo (sin acción equivale a info).
  action                scan, info, shares, open, printers, workgroups, connect, disconnect,
                        status o printer.
  resource              Carpeta o impresora compartida.
  {open,queue,connect}  Acción sobre la impresora.

Options:
  -h, --help            Show this help and exit.
  --network             Examina todo el inventario LANCTL.
  --group GROUP         Limita el escaneo a un grupo LANCTL.
  --timeout TIMEOUT     Tiempo máximo del probe TCP.
  --workers WORKERS     Número máximo de probes concurrentes.
  --anonymous           No carga credenciales asociadas.
  --include-system      Incluye recursos administrativos y especiales.
  --dry-run             Muestra el plan sin autenticar, abrir ni mutar.
  --yes                 Confirma una conexión de impresora.
  --json                Emite JSON estructurado.
  --database DATABASE   Archivo JSON del inventario.
  --store STORE         Almacén DPAPI de credenciales.
  --storage STORAGE     Directorio de observaciones de plugins.
```

## `LANIP terminal`

```text
Usage: LANIP terminal [-h] [-p PROTOCOL] [--native] [--database DATABASE] [--store STORE] selector

Arguments:
  selector                    IP, MAC o alias del elemento.

Options:
  -h, --help                  Show this help and exit.
  -p PROTOCOL, --protocol PROTOCOL
                              Protocolo si hay varias terminales.
  --native                    Usa el cliente SSH nativo sin la capa de color de LANCTL.
  --database DATABASE         Archivo JSON de elementos.
  --store STORE               Almacén cifrado de credenciales.
```

## `LANIP switch`

```text
Usage: LANIP switch [-h] [--profile PROFILE] [--profiles PROFILES] [--database DATABASE]
                    [--dry-run] [--yes]
                    selector ...

Comandos Cisco gestionados:
  show COMANDO
  port list
  port label PUERTO NOMBRE
  port unlabel PUERTO
  port show [PUERTO] status|description|config|errors|vlan
  port set [PUERTO] description|speed|duplex VALOR
  port enable|disable|reset [PUERTO]
  start|stop|reset [PUERTO]
  save-config
  terminal

Opciones globales: --profile PERFIL --dry-run --yes
Esta fase utiliza un adaptador simulado y no conecta con el switch.

Arguments:
  selector             IP, MAC o alias del switch.
  COMANDO              Acción Cisco gestionada que se quiere planificar.

Options:
  -h, --help           Show this help and exit.
  --profile PROFILE    Perfil Cisco que remapea los puertos.
  --profiles PROFILES  Archivo JSON que contiene los perfiles Cisco.
  --database DATABASE  Archivo JSON de elementos.
  --dry-run            Solo muestra el plan.
  --yes                Confirma cambios sin preguntar.
```

## `LANIP group`

```text
Usage: LANIP group [-h]
                   [-new | -del | -rename NUEVO | -description TEXTO | -add ELEMENTO | -remove ELEMENTO | -list]
                   [--database DATABASE] [--groups GROUPS]
                   [name]

Arguments:
  name                 Nombre del grupo.

Options:
  -h, --help           Show this help and exit.
  -new                 Crea el grupo.
  -del                 Elimina el grupo.
  -rename NUEVO        Renombra el grupo.
  -description TEXTO   Edita su descripción.
  -add ELEMENTO        Añade IP, MAC o alias.
  -remove ELEMENTO     Retira IP, MAC o alias.
  -list                Lista los elementos que pertenecen al grupo.
  --database DATABASE  Archivo JSON de elementos.
  --groups GROUPS      Archivo JSON de grupos.
```

## `LANIP element`

```text
Usage: LANIP element [-h] [-add MAC] [-name NEW_NAME] [-alias NEW_ALIAS]
                     [-description NEW_DESCRIPTION] [-cnf NEW_CNF] [-group NEW_GROUP]
                     [-protocol NEW_PROTOCOL] [-delete] [--database DATABASE] [--groups GROUPS]
                     [--yes]
                     [selector]
                     [{edit,cnf,name,description,alias,group,protocol,delete,del,remove}]
                     [values ...]

Arguments:
  selector                    IP, MAC o alias.
  {edit,cnf,name,description,alias,group,protocol,delete,del,remove}
                              Campo o acción que se quiere editar.
  values                      Nuevo valor.

Options:
  -h, --help                  Show this help and exit.
  -add MAC                    Añade un elemento nuevo utilizando su dirección MAC.
  -name NEW_NAME, --name NEW_NAME
                              Asigna NAME al elemento indicado.
  -alias NEW_ALIAS, --alias NEW_ALIAS
                              Asigna ALIAS al elemento indicado.
  -description NEW_DESCRIPTION, --description NEW_DESCRIPTION
                              Asigna DESCRIPTION al elemento indicado (máximo 42 caracteres).
  -cnf NEW_CNF, --cnf NEW_CNF
                              Asigna el estado CNF.
  -group NEW_GROUP, --group NEW_GROUP
                              Añade el elemento al grupo.
  -protocol NEW_PROTOCOL, --protocol NEW_PROTOCOL
                              Activa un protocolo.
  -delete, --delete           Elimina completamente el elemento indicado.
  --database DATABASE         Archivo JSON de elementos.
  --groups GROUPS             Archivo JSON de grupos.
  --yes                       Elimina sin solicitar confirmación.
```

## `LANIP project`

```text
Usage: LANIP project [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    status    Muestra el proyecto activo.
    create    Crea un proyecto VLF vacío por defecto.
    update    Actualiza datos activos conservando información complementaria.
    save      Guarda manualmente el proyecto VLF activo.
    info      Muestra los metadatos del proyecto.
    verify    Comprueba hashes, estructura y SQLite.
    use       Selecciona el proyecto VLF que recibirá la auditoría.
    list      Lista el contenido interno sin extraerlo.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project status`

```text
Usage: LANIP project status [-h] [--json]

Options:
  -h, --help  Show this help and exit.
  --json      Devuelve JSON.
```

## `LANIP project create`

```text
Usage: LANIP project create [-h] [--name NAME] [--description DESCRIPTION] [--author AUTHOR]
                            [--lan-name LAN_NAME] [--location LOCATION] [--company COMPANY]
                            [--responsible RESPONSIBLE] [--clone-current] [--force]
                            file

Arguments:
  file                       Archivo de salida; se añade .vlf si falta.

Options:
  -h, --help                 Show this help and exit.
  --name NAME                Nombre humano del proyecto.
  --description DESCRIPTION  Descripción general.
  --author AUTHOR            Autor del proyecto.
  --lan-name LAN_NAME        Nombre humano de la LAN.
  --location LOCATION        Ubicación física.
  --company COMPANY          Empresa u organización.
  --responsible RESPONSIBLE  Responsable de la LAN.
  --clone-current            Crea el proyecto copiando explícitamente el inventario y grupos
                             activos.
  --force                    Sobrescribe un VLF existente.
```

## `LANIP project update`

```text
Usage: LANIP project update [-h] file

Arguments:
  file        Proyecto VLF existente.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project save`

```text
Usage: LANIP project save [-h]

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project info`

```text
Usage: LANIP project info [-h] [--json] file

Arguments:
  file        Proyecto VLF.

Options:
  -h, --help  Show this help and exit.
  --json      Devuelve JSON.
```

## `LANIP project verify`

```text
Usage: LANIP project verify [-h] [--json] file

Arguments:
  file        Proyecto VLF.

Options:
  -h, --help  Show this help and exit.
  --json      Devuelve JSON.
```

## `LANIP project use`

```text
Usage: LANIP project use [-h] file

Arguments:
  file        Proyecto VLF existente.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP project list`

```text
Usage: LANIP project list [-h] file

Arguments:
  file        Proyecto VLF.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin`

```text
Usage: LANIP plugin [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    list       Lista complementos instalados.
    catalog    Muestra el catálogo oficial incluido.
    info       Muestra manifiesto, permisos y estado.
    install    Verifica e instala un paquete .lcp desactivado.
    enable     Concede permisos y activa un complemento.
    disable    Desactiva el complemento.
    reload     Recarga un complemento activo.
    uninstall  Desinstala el complemento.
    verify     Verifica un .lcp o plugin instalado.
    permissions
               Muestra permisos solicitados y concedidos.
    revoke     Revoca permisos y confianza de un complemento.
    publisher  Gestiona huellas Ed25519 de editores LCP confiables.
    extensions
               Lista extensiones para CLI, TUI y futura GUI.
    pack       Construye un paquete .lcp desde un directorio.

Options:
  -h, --help   Show this help and exit.
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
  plugin_id   Identificador estable del complemento.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin install`

```text
Usage: LANIP plugin install [-h] file

Arguments:
  file        Archivo de paquete con extensión .lcp.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin enable`

```text
Usage: LANIP plugin enable [-h] [--grant [PERMISO ...]] [--grant-all] [--trust] plugin_id

Arguments:
  plugin_id              Identificador del complemento instalado.

Options:
  -h, --help             Show this help and exit.
  --grant [PERMISO ...]  Permisos concretos que se conceden.
  --grant-all            Concede todos los permisos solicitados.
  --trust                Autoriza código trusted dentro del proceso.
```

## `LANIP plugin disable`

```text
Usage: LANIP plugin disable [-h] plugin_id

Arguments:
  plugin_id   Identificador del complemento instalado.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin reload`

```text
Usage: LANIP plugin reload [-h] plugin_id

Arguments:
  plugin_id   Identificador del complemento instalado.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin uninstall`

```text
Usage: LANIP plugin uninstall [-h] plugin_id

Arguments:
  plugin_id   Identificador del complemento instalado.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin verify`

```text
Usage: LANIP plugin verify [-h] target

Arguments:
  target      Identificador instalado o ruta de un archivo .lcp.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin permissions`

```text
Usage: LANIP plugin permissions [-h] plugin_id

Arguments:
  plugin_id   Identificador del complemento instalado.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin revoke`

```text
Usage: LANIP plugin revoke [-h] plugin_id [PERMISO ...]

Arguments:
  plugin_id   Identificador del complemento instalado.
  PERMISO     Vacío revoca todos los permisos.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP plugin publisher`

```text
Usage: LANIP plugin publisher [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    list      Lista editores confiables.
    trust     Confía en la firma que contiene un paquete LCP.
    revoke    Revoca una huella de editor.

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
  file         Paquete .lcp firmado y verificado.

Options:
  -h, --help   Show this help and exit.
  --name NAME  Nombre descriptivo del editor.
```

## `LANIP plugin publisher revoke`

```text
Usage: LANIP plugin publisher revoke [-h] fingerprint

Arguments:
  fingerprint  Huella SHA-256 Ed25519 completa.

Options:
  -h, --help   Show this help and exit.
```

## `LANIP plugin extensions`

```text
Usage: LANIP plugin extensions [-h] [--type TYPE]

Options:
  -h, --help   Show this help and exit.
  --type TYPE  Filtra por tipo de extensión unificada.
```

## `LANIP plugin pack`

```text
Usage: LANIP plugin pack [-h] [--force] [--signing-key SIGNING_KEY] directory output

Arguments:
  directory                  Directorio fuente que contiene plugin.info.
  output                     Archivo .lcp de salida.

Options:
  -h, --help                 Show this help and exit.
  --force                    Sobrescribe el paquete de salida existente.
  --signing-key SIGNING_KEY  Clave privada Ed25519 PEM para firmar el LCP.
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
  0eXXXXXXXX  Identificador estable del error.

Options:
  -h, --help  Show this help and exit.
  --json      Emite el resultado como JSON.
```

## `LANIP database`

```text
Usage: LANIP database [-h]
                      (--diagnose | --export ARCHIVO.zip | --verify ARCHIVO.zip | --import ARCHIVO.zip | --restore ARCHIVO.bak)
                      [--target {database,groups,physical}] [--yes] [--json]

Options:
  -h, --help                  Show this help and exit.
  --diagnose                  Valida los almacenes configurados.
  --export ARCHIVO.zip        Exporta datos con hashes verificables.
  --verify ARCHIVO.zip        Verifica una exportación sin importarla.
  --import ARCHIVO.zip        Importa datos verificados.
  --restore ARCHIVO.bak       Restaura un backup validado del almacén.
  --target {database,groups,physical}
                              Almacén que se restaura.
  --yes                       Confirma la sustitución de datos.
  --json                      Emite el diagnóstico como JSON.
```

## `LANIP demo`

```text
Usage: LANIP demo [-h] [--output DIRECTORIO] [--force] [--format {json,html,all}]

Crea inventario, proyecto VLF, evidencias, monitorización y un informe de demostración aislados de los datos del usuario.

Options:
  -h, --help                Show this help and exit.
  --output DIRECTORIO       Directorio donde se guardará el proyecto y el informe.
  --force                   Reemplaza una demo anterior.
  --format {json,html,all}  Formato del informe exportado.
```

## `LANIP lanwire`

```text
Usage: LANIP lanwire [-h] [--new-window] [--version] [--database ARCHIVO.db] [-tui | --cli] ...

Arguments:
  ARGUMENTO              Argumentos enviados a LANWIRE, por ejemplo: list.

Options:
  -h, --help             Show this help and exit.
  --new-window           Abre LANWIRE en una consola independiente incluso si se indican
                         argumentos.
  --version              Muestra la versión común de LANWIRE y termina.
  --database ARCHIVO.db  Selecciona una base física IDF alternativa.
  -tui, --tui            Abre la interfaz TUI de LANWIRE.
  --cli                  Abre la consola interactiva de LANWIRE.
```

## `LANIP lab`

```text
Usage: LANIP lab [-h] ACCIÓN ...

Arguments:
  ACCIÓN
    generate  Genera un escenario reproducible.
    list      Lista escenarios.
    status    Muestra el escenario activo.
    stop      Desactiva el proveedor simulado.
    start     Activa explícitamente un escenario virtual.
    validate  Valida un escenario.
    export    Exporta un escenario.
    import    Importa un escenario JSON.
    network   Crea manualmente una red virtual.
    device    Edita dispositivos simulados.
    evolve    Avanza el reloj y aplica eventos pendientes.

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
  --name NAME                 Nombre del escenario.
  --cidr CIDR                 Red IPv4 virtual.
  --profile {home,office,datacenter,industrial,chaotic}
                              Perfil de dispositivos.
  --devices DEVICES           Cantidad de dispositivos.
  --seed SEED                 Semilla reproducible.
  --active-percent ACTIVE_PERCENT
                              Porcentaje activo.
  --dhcp-percent DHCP_PERCENT
                              Porcentaje DHCP.
  --type {snapshot,timeline,chaos}
                              Evolución del escenario.
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
  scenario    Nombre del escenario.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab validate`

```text
Usage: LANIP lab validate [-h] scenario

Arguments:
  scenario    Nombre del escenario.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab export`

```text
Usage: LANIP lab export [-h] [--format {json,csv}] [--output OUTPUT] scenario

Arguments:
  scenario             Nombre del escenario.

Options:
  -h, --help           Show this help and exit.
  --format {json,csv}  Formato de salida.
  --output OUTPUT      Archivo de destino; stdout si se omite.
```

## `LANIP lab import`

```text
Usage: LANIP lab import [-h] file

Arguments:
  file        Archivo JSON.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab network`

```text
Usage: LANIP lab network [-h] {create} ...

Arguments:
  {create}
    create    Crea un escenario vacío.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab network create`

```text
Usage: LANIP lab network create [-h] --name NAME [--cidr CIDR]

Options:
  -h, --help   Show this help and exit.
  --name NAME  Nombre del escenario.
  --cidr CIDR  CIDR virtual.
```

## `LANIP lab device`

```text
Usage: LANIP lab device [-h] {add,delete} ...

Arguments:
  {add,delete}
    add         Añade un dispositivo.
    delete      Elimina un dispositivo.

Options:
  -h, --help    Show this help and exit.
```

## `LANIP lab device add`

```text
Usage: LANIP lab device add [-h] --ip IP --mac MAC [--alias ALIAS] [--name NAME] [--inactive]
                            scenario

Arguments:
  scenario       Escenario.

Options:
  -h, --help     Show this help and exit.
  --ip IP        IPv4 simulada.
  --mac MAC      MAC simulada.
  --alias ALIAS  Alias.
  --name NAME    Nombre.
  --inactive     Lo crea inactivo.
```

## `LANIP lab device delete`

```text
Usage: LANIP lab device delete [-h] scenario device

Arguments:
  scenario    Escenario.
  device      ID, IP, MAC o alias.

Options:
  -h, --help  Show this help and exit.
```

## `LANIP lab evolve`

```text
Usage: LANIP lab evolve [-h] --seconds SECONDS

Options:
  -h, --help         Show this help and exit.
  --seconds SECONDS  Segundos virtuales.
```

## `LANWIRE`

```text
Usage: LANWIRE [-h] [--version] [--database ARCHIVO.db] [-tui | --cli] COMANDO ...

Gestión física, IDF, cableado y topología de la suite LANCTL.

Arguments:
  COMANDO
    tui                  Abre la interfaz de pantalla completa.
    cli                  Abre la consola interactiva.
    list (ls)            Lista los identificadores.
    seed                 Carga la topología inicial de pruebas.
    show                 Muestra un identificador.
    add                  Genera el siguiente IDF.
    reserve              Reserva un IDF.
    delete (del)         Elimina un IDF.
    prefix               Gestiona juegos de letras.

Options:
  -h, --help             Show this help and exit.
  --version              Muestra la versión común de la suite y termina.
  --database ARCHIVO.db  Base física IDF; por defecto usa physical/idf.db en la raíz compartida.
  -tui, --tui            Abre la interfaz de pantalla completa.
  --cli                  Abre la consola interactiva de LANWIRE.
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

## `LANWIRE list`

```text
Usage: LANWIRE list [-h] [prefix]

Arguments:
  prefix      Filtra por prefijo IDF.

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
  idf         Identificador físico que se desea consultar.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE add`

```text
Usage: LANWIRE add [-h] prefix [CLAVE=VALOR ...]

Arguments:
  prefix       Prefijo del tipo de elemento físico.
  CLAVE=VALOR  Datos iniciales opcionales.

Options:
  -h, --help   Show this help and exit.
```

## `LANWIRE reserve`

```text
Usage: LANWIRE reserve [-h] idf [CLAVE=VALOR ...]

Arguments:
  idf          IDF exacto que se desea reservar.
  CLAVE=VALOR  Datos iniciales opcionales.

Options:
  -h, --help   Show this help and exit.
```

## `LANWIRE delete`

```text
Usage: LANWIRE delete [-h] idf

Arguments:
  idf         IDF que se desea eliminar.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE prefix`

```text
Usage: LANWIRE prefix [-h] {list,ls,show,set,delete,del} ...

Arguments:
  {list,ls,show,set,delete,del}
    list (ls)                 Lista las definiciones.
    show                      Muestra una definición.
    set                       Crea o actualiza una definición.
    delete (del)              Elimina una definición.

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
  letters     Letras del prefijo.

Options:
  -h, --help  Show this help and exit.
```

## `LANWIRE prefix set`

```text
Usage: LANWIRE prefix set [-h] letters name [description]

Arguments:
  letters      Letras del prefijo.
  name         Nombre descriptivo del tipo.
  description  Descripción opcional.

Options:
  -h, --help   Show this help and exit.
```

## `LANWIRE prefix delete`

```text
Usage: LANWIRE prefix delete [-h] letters

Arguments:
  letters     Letras del prefijo que se desea eliminar.

Options:
  -h, --help  Show this help and exit.
```

## `LANRACK`

```text
Usage: LANRACK [-h] [--version] [--database ARCHIVO.db] [-tui | --cli] {list,ls,show} ...

Visualiza racks y sus equipos.

Arguments:
  {list,ls,show}
    list (ls)            Lista los racks disponibles.
    show                 Muestra un rack y sus ocupantes.

Options:
  -h, --help             Show this help and exit.
  --version              Muestra la versión común de la suite y termina.
  --database ARCHIVO.db  Base física IDF compartida.
  -tui, --tui            Abre la interfaz de pantalla completa.
  --cli                  Abre la consola interactiva.
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
  rack        ID o nombre del rack.

Options:
  -h, --help  Show this help and exit.
```

## `LANACCESS`

```text
Usage: LANACCESS [-h] [--version] [--database DATABASE] [--store STORE] [-tui | --cli]
                 {list,ls,show,set,delete,del} ...

Gestiona credenciales cifradas del entorno LANCTL.

Arguments:
  {list,ls,show,set,delete,del}
    list (ls)                 Lista metadatos; nunca secretos.
    show                      Muestra metadatos de una credencial.
    set                       Crea o actualiza una credencial.
    delete (del)              Elimina una credencial.

Options:
  -h, --help                  Show this help and exit.
  --version                   Muestra la versión común de la suite y termina.
  --database DATABASE         Base de elementos LANCTL.
  --store STORE               Almacén cifrado de credenciales.
  -tui, --tui                 Abre la interfaz de pantalla completa.
  --cli                       Abre la consola interactiva.
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
  credential_id  Identificador de la credencial.

Options:
  -h, --help     Show this help and exit.
```

## `LANACCESS set`

```text
Usage: LANACCESS set [-h] --username USERNAME element protocol

Arguments:
  element                     IP, MAC, alias o ID del dispositivo.
  protocol                    Protocolo asociado, por ejemplo ssh.

Options:
  -h, --help                  Show this help and exit.
  --username USERNAME, -user USERNAME
                              Usuario remoto.
```

## `LANACCESS delete`

```text
Usage: LANACCESS delete [-h] credential_id

Arguments:
  credential_id  Identificador de la credencial.

Options:
  -h, --help     Show this help and exit.
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
              [--timeout TIMEOUT]
              [words ...]

Monitorización, eventos e incidencias de la suite LANCTL.

Arguments:
  words                       attach, detach, status, once, session, incidents, incident, service
                              o foreground.

Options:
  -h, --help                  Show this help and exit.
  --version                   Muestra la versión común de la suite y termina.
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
  --sessions SESSIONS         Estado runtime de sesiones.
  --incidents-store INCIDENTS_STORE
                              Estado runtime de incidencias.
  --lock LOCK                 Lock singleton del monitor.
  --monitor-db MONITOR_DB     Repositorio SQLite del monitor.
  --profiles PROFILES         Perfiles personalizados.
  --assignments-store ASSIGNMENTS_STORE
                              Asignaciones persistentes.
  --profile PROFILE           Perfil monitor.
  --priority {low,normal,high,critical}
                              Prioridad de asignación.
  --check CHECK               Check ping, arp o port:NN.
  --presence PRESENCE         Intervalo de presencia.
  --discovery DISCOVERY       Intervalo de descubrimiento.
  --services SERVICES         Intervalo de servicios.
  --deep DEEP                 Intervalo profundo.
  --workers WORKERS           Workers del perfil.
  --timeout TIMEOUT           Timeout del perfil.
```
