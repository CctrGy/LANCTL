-- Autocompletado de LANCTL para Clink 1.3.23 o posterior.
-- Compatible con LANCTL 0.3.2-beta.4.
-- Desarrollo: clink installscripts <ruta>\packaging\clink
-- Instalación: <directorio-de-instalación>\clink\lanctl.lua

local function values(items)
    return clink.argmatcher():addarg(items):nofiles()
end

local function history_value(hint)
    return clink.argmatcher():addarg({ fromhistory = true, hint = hint }):nofiles()
end

local function integer_range(first, last)
    local items = {}
    for value = first, last do
        table.insert(items, tostring(value))
    end
    return values(items)
end

local help_flags = { "-h", "--help", "/?" }
local formats = values({ "table", "json", "csv", "html", "xml", "yaml" })
local discovery = values({ "icmp", "arp", "hybrid" })
local profiles = values({ "fast", "normal", "accurate" })
local scan_orders = values({ "ascending", "descending", "random" })
local on_off = values({ "on", "off" })
local error_log_levels = integer_range(1, 59)
local cnf_states = values({ "O", "X", "-", "S", "F" })
local protocols = values({
    "auto", "ssh", "tr-064", "telnet", "http", "https", "ftp",
    "rdp", "rtsp", "smb", "radmin", "wol"
})
local selector = history_value("IP, MAC, alias o nombre")
local file_arg = clink.argmatcher():addarg(clink.filematches)
local dir_arg = clink.argmatcher():addarg(clink.dirmatches)

local list = clink.argmatcher()
    :addflags({
        "-h", "--help", "/?",
        "--network" .. history_value("Red CIDR"),
        "--database" .. file_arg,
        "--groups" .. file_arg,
        "-f" .. formats, "--format" .. formats,
        "-o" .. file_arg, "--output" .. file_arg,
        "-recurrent", "--recurrent",
        "--where" .. history_value("Consulta de filtrado"),
        "-w" .. history_value("Workers"), "--workers" .. history_value("Workers"),
        "-t" .. history_value("Segundos"), "--timeout" .. history_value("Segundos"),
        "--scan-order" .. scan_orders,
        "--include-unknown", "--resolve-names", "--max-hosts" .. history_value("Máximo"),
        "--discovery" .. discovery, "--profile" .. profiles,
        "--fast", "--normal", "--accurate", "--progress", "--no-progress",
        "--show-discovery", "--include-arp-cache", "--show-detection",
        "--active", "-active", "--connected", "-connected", "-conected",
        "--disconnected", "-disconnected", "-offline", "--basic", "-basic",
        "-cnf" .. cnf_states, "--cnf-state" .. cnf_states,
        "-group" .. history_value("Grupo"), "--group" .. history_value("Grupo"),
        "-dhcp", "--dhcp-only"
    }):nofiles()

local ephemeral = clink.argmatcher()
    :addflags({
        "-h", "--help", "/?", "--fast", "--normal", "--accurate",
        "--range" .. history_value("Red CIDR"), "--resolve-names",
        "--ports" .. history_value("22,80,443"), "--json",
        "--workers" .. history_value("Workers"),
        "--timeout" .. history_value("Segundos"),
        "--max-hosts" .. history_value("Máximo"),
        "--scan-order" .. scan_orders
    }):nofiles()

local recurrent = clink.argmatcher()
    :addflags({
        "-h", "--help", "/?", "-list", "--list",
        "-f" .. formats, "--format" .. formats,
        "-o" .. file_arg, "--output" .. file_arg
    }):nofiles()

local ping = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addflags({
        "-h", "--help", "/?",
        "--method" .. values({ "auto", "ping", "arp" }),
        "--ping", "--arp", "--timeout" .. history_value("Segundos"),
        "--json", "--database" .. file_arg
    }):nofiles()

local open = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addarg({ "auto", "ssh", "tr-064", "telnet", "http", "https", "ftp", "rdp", "rtsp", "smb", "radmin" })
    :addflags({
        "-h", "--help", "/?", "--port" .. history_value("Puerto"),
        "--path" .. history_value("Ruta remota"),
        "--mode" .. values({ "control", "view", "file", "shutdown", "chat", "voice", "message", "telnet" }),
        "--through" .. history_value("Servidor HOST:PUERTO"), "--fullscreen",
        "--color-depth" .. values({ "1", "2", "4", "8", "16", "24" }),
        "--updates" .. history_value("Actualizaciones/segundo"),
        "--phonebook" .. file_arg, "--phonebook-id" .. history_value("ID"),
        "--dry-run",
        "--database" .. file_arg, "--store" .. file_arg
    }):nofiles()

local settings = clink.argmatcher()
    :addflags({
        "-h", "--help", "/?",
        "-range" .. history_value("Red CIDR"),
        "-list-fields" .. history_value("Columnas"), "--list-fields" .. history_value("Columnas"),
        "-dhcp-range" .. history_value("IP-INICIO-IP-FIN"), "--dhcp-range" .. history_value("IP-INICIO-IP-FIN"),
        "-credentials" .. file_arg, "--credentials" .. file_arg,
        "-discovery" .. discovery, "--discovery" .. discovery,
        "--scan-profile" .. profiles, "--progress" .. on_off,
        "--service-identification" .. on_off,
        "--disconnected-retention" .. values({ "permanent", "session", "forget" }),
        "--disconnected-target" .. values({ "unconfirmed", "all" }),
        "--disconnected-scope" .. values({ "all", "dhcp" }),
        "--workers" .. history_value("Workers"), "--timeout" .. history_value("Segundos"),
        "--scan-order" .. scan_orders,
        "--max-hosts" .. history_value("Máximo"), "--database" .. file_arg,
        "--physical-database" .. file_arg,
        "--groups" .. file_arg, "--log" .. dir_arg,
        "--error-log-level" .. error_log_levels,
        "--projects-directory" .. dir_arg,
        "-save-mode" .. values({ "list", "manual", "manual.inCloseConsult", "automatic.toClose", "automatic.toScan", "automatic.timeToSave", "automatic.allChanges" }),
        "--save-mode" .. values({ "list", "manual", "manual.inCloseConsult", "automatic.toClose", "automatic.toScan", "automatic.timeToSave", "automatic.allChanges" }),
        "-save-interval" .. history_value("Minutos"),
        "--save-interval" .. history_value("Minutos"),
        "--cli-exit-save-prompt" .. on_off,
        "--cli-command-chaining" .. on_off,
        "-log-cleanup" .. on_off, "--log-cleanup" .. on_off,
        "-log-retention-days" .. history_value("Días"),
        "--log-retention-days" .. history_value("Días"),
        "--remote-access" .. on_off,
        "--remote-bind" .. history_value("IPv4 local"),
        "--remote-cidr" .. history_value("Red CIDR"),
        "--remote-port" .. history_value("Puerto SSH"),
        "--remote-password-auth" .. on_off,
        "--remote-backend" .. values({ "service", "user" }),
        "--remote-forced-view" .. values({ "off", "gui", "tui", "plugins", "projects", "settings" }),
        "--tui-key" .. history_value("ACCIÓN=TECLA"),
        "--tui-layout" .. values({ "cli.bottom", "cli.top" }),
        "--tui-cli-percent" .. history_value("15-75"),
        "--tui-column" .. history_value("COLUMNA=TAMAÑO"),
        "--tui-footer-buttons" .. history_value("ACCIONES"),
        "--tui-footer-button" .. history_value("ACCIÓN=on|off")
    }):nofiles()

local call = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addflags({
        "-h", "--help", "/?",
        "-f" .. values({ "ip", "cnf", "mac", "alias", "name", "group", "description", "manufacturer", "default-name", "device-id", "protocols" }),
        "--field" .. values({ "ip", "cnf", "mac", "alias", "name", "group", "description", "manufacturer", "default-name", "device-id", "protocols" }),
        "--json", "--database" .. file_arg
    }):nofiles()

local search = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC, alias o nombre" })
    :addflags({ "-h", "--help", "/?", "--json", "--database" .. file_arg })
    :nofiles()

local scan = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addflags({
        "-h", "--help", "/?", "--ports" .. history_value("Puertos o rangos"),
        "--all-ports", "--timeout" .. history_value("Segundos"),
        "--workers" .. history_value("Workers"), "--banners", "--identify",
        "--json", "--database" .. file_arg
    }):nofiles()

local element = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addarg({ "edit", "ip", "cnf", "name", "description", "alias", "idf", "group", "protocol", "delete", "del", "remove" })
    :addarg({ fromhistory = true, hint = "Valor" })
    :addflags({
        "-h", "--help", "/?", "-add" .. history_value("MAC"),
        "-ip" .. history_value("IPv4"), "--ip" .. history_value("IPv4"),
        "-name" .. history_value("Nombre"), "--name" .. history_value("Nombre"),
        "-alias" .. history_value("Alias"), "--alias" .. history_value("Alias"),
        "-description" .. history_value("Descripción"), "--description" .. history_value("Descripción"),
        "-cnf" .. cnf_states, "--cnf" .. cnf_states,
        "-idf" .. history_value("AB-12"), "--idf" .. history_value("AB-12"),
        "-group" .. history_value("Grupo"), "--group" .. history_value("Grupo"),
        "-protocol" .. protocols, "--protocol" .. protocols,
        "-delete", "--delete", "--database" .. file_arg, "--groups" .. file_arg, "--yes"
    }):loop(3)

local group = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Grupo" })
    :addflags({
        "-h", "--help", "/?", "-new", "-del", "-list",
        "-rename" .. history_value("Nuevo nombre"),
        "-description" .. history_value("Descripción"),
        "-add" .. selector, "-remove" .. selector,
        "--database" .. file_arg, "--groups" .. file_arg
    }):nofiles()

local credential = clink.argmatcher()
    :addarg({ fromhistory = true, "list", hint = "Elemento o list" })
    :addarg({ "set", "list", "delete" })
    :addarg({ fromhistory = true, hint = "Protocolo" })
    :addflags({
        "-h", "--help", "/?", "-user" .. history_value("Usuario"),
        "--username" .. history_value("Usuario"),
        "--database" .. file_arg, "--store" .. file_arg
    }):nofiles()

local protocol = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Elemento" })
    :addarg({ "show", "configure" })
    :addarg({ "ssh", "tr-064", "telnet", "http", "https", "ftp", "rdp", "rtsp", "smb", "radmin", "wol" })
    :addflags({
        "-h", "--help", "/?", "--port" .. history_value("Puerto"),
        "--driver" .. history_value("Driver"), "--host-key" .. history_value("Algoritmo"),
        "--kex" .. history_value("Algoritmo"), "--profile" .. history_value("Perfil"),
        "--database" .. file_arg
    }):nofiles()

local simple_selector = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addflags({ "-h", "--help", "/?", "--database" .. file_arg }):nofiles()

local terminal = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addflags({
        "-h", "--help", "/?", "-p" .. history_value("Protocolo"),
        "--protocol" .. history_value("Protocolo"), "--native",
        "--database" .. file_arg, "--store" .. file_arg
    }):nofiles()

local ssh = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addarg({ "probe", "fingerprint", "trust", "open", "show" })
    :addarg({ fromhistory = true, hint = "Huella o comando remoto" })
    :addflags({
        "-h", "--help", "/?", "--database" .. file_arg,
        "--store" .. file_arg, "--host" .. history_value("IP candidata")
    }):loop(3)

local radmin = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addarg({ "probe", "configure", "open" })
    :addflags({
        "-h", "--help", "/?",
        "--mode" .. values({ "control", "view", "file", "shutdown", "chat", "voice", "message", "telnet" }),
        "--port" .. history_value("Puerto"), "--executable" .. file_arg,
        "--through" .. history_value("Servidor HOST:PUERTO"), "--fullscreen",
        "--color-depth" .. values({ "1", "2", "4", "8", "16", "24" }),
        "--updates" .. history_value("Actualizaciones/segundo"),
        "--phonebook" .. file_arg, "--phonebook-id" .. history_value("ID"),
        "--database" .. file_arg, "--store" .. file_arg
    }):nofiles()

local history = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Elemento" })
    :addflags({
        "-h", "--help", "/?", "--all", "--commands", "--today",
        "--from" .. history_value("AAAA-MM-DD"), "--to" .. history_value("AAAA-MM-DD"),
        "--type" .. history_value("Tipo de evento"), "--source" .. history_value("Origen"),
        "--result" .. history_value("Resultado"), "--errors",
        "--search" .. history_value("Texto"), "--limit" .. history_value("Cantidad"),
        "--reverse", "--format" .. values({ "table", "json", "csv" })
    }):nofiles()

local wol = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Elemento o sequence" })
    :addarg({ "wakeup", "status", "shutdown", "restart", "sleep", "hibernate", "create", "add", "run" })
    :addarg({ fromhistory = true, hint = "Elemento, secuencia o valor" })
    :addflags({
        "-h", "--help", "/?", "-if" .. history_value("Condición"),
        "--if" .. history_value("Condición"), "--if-all" .. history_value("Condición"),
        "--if-any" .. history_value("Condición"), "--if-not" .. history_value("Condición"),
        "-t" .. history_value("Tiempo"), "--time" .. history_value("Tiempo"),
        "--message" .. history_value("Mensaje"), "--force", "--cancel",
        "--broadcast" .. history_value("IPv4 broadcast"), "--port" .. history_value("Puerto UDP"),
        "--power-transport" .. values({ "ssh", "disabled" }),
        "--power-platform" .. values({ "windows", "linux" }),
        "--power-command" .. history_value("ACCION=COMANDO"),
        "--repeat" .. history_value("Repeticiones"), "--interval" .. history_value("Segundos"),
        "--wait" .. history_value("Segundos"), "--method" .. values({ "auto", "arp", "ping", "port" }),
        "--check-port" .. history_value("Puerto TCP"), "--interface" .. history_value("Interfaz/IP"),
        "--retry" .. history_value("Intentos"), "--dry-run", "--json", "--quiet",
        "--group" .. history_value("Grupo"), "--all", "--yes",
        "--after" .. history_value("Dependencia"), "--delay" .. history_value("Duración"),
        "--timeout" .. history_value("Segundos"),
        "--on-failure" .. values({ "stop", "continue", "retry" }),
        "--cooldown" .. history_value("Duración"), "--max-attempts" .. history_value("Intentos"),
        "--database" .. file_arg, "--sequences" .. file_arg
    }):loop(3)

local smb = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Servidor o scan/workgroups/printers" })
    :addarg({ "scan", "info", "shares", "open", "printers", "workgroups", "connect", "disconnect", "status", "printer" })
    :addarg({ fromhistory = true, hint = "Recurso compartido" })
    :addarg({ "open", "queue", "connect" })
    :addflags({
        "-h", "--help", "/?", "--network", "--group" .. history_value("Grupo"),
        "--timeout" .. history_value("Segundos"), "--workers" .. history_value("Workers"),
        "--anonymous", "--include-system", "--dry-run", "--yes", "--json",
        "--database" .. file_arg, "--store" .. file_arg, "--storage" .. dir_arg
    }):loop(4)

local monitor = clink.argmatcher()
    :addarg({
        "attach", "start", "detach", "stop", "restart", "status", "once",
        "session", "incidents", "incident", "service", "foreground", "configure",
        "profile", "assign", "unassign", "assignments", "report", "ping", "scan",
        "identify", "health", "events"
    })
    :addarg({
        "start", "stop", "list", "report", "acknowledge", "close", "install",
        "uninstall", "create", "update", "delete", "show", "latest", "permanent", "temporary"
    })
    :addarg({ fromhistory = true, hint = "Proyecto, elemento, perfil o ID" })
    :addflags({
        "-h", "--help", "/?", "--project" .. file_arg, "--permanent",
        "--duration" .. history_value("Duración"),
        "--mode" .. values({ "permanent", "temporary", "diagnostic", "once" }),
        "--authority" .. values({ "observe", "operate", "administer" }),
        "--json", "--yes", "--interval" .. history_value("Duración"),
        "--every" .. history_value("Duración"), "--group" .. history_value("Grupo"),
        "--type" .. values({ "presence", "services", "ports", "identity", "smb", "full" }),
        "--fast", "--unknown", "--follow", "--sessions" .. file_arg,
        "--incidents-store" .. file_arg, "--lock" .. file_arg, "--monitor-db" .. file_arg,
        "--profiles" .. file_arg, "--assignments-store" .. file_arg,
        "--profile" .. history_value("Perfil"),
        "--priority" .. values({ "low", "normal", "high", "critical" }),
        "--check" .. history_value("ping, arp o port:NN"),
        "--presence" .. history_value("Duración"), "--discovery" .. history_value("Duración"),
        "--services" .. history_value("Duración"), "--deep" .. history_value("Duración"),
        "--workers" .. history_value("Workers"), "--timeout" .. history_value("Segundos")
    }):loop(3)

local download_settings = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Gateway opcional" })
    :addflags({
        "-h", "--help", "/?", "--port" .. history_value("Puerto TR-064"),
        "--timeout" .. history_value("Segundos"),
        "--database" .. file_arg, "--store" .. file_arg
    }):nofiles()

local gateway_download = clink.argmatcher()
    :addflags({
        "-h", "--help", "/?", "--port" .. history_value("Puerto TR-064"),
        "--timeout" .. history_value("Segundos"),
        "--database" .. file_arg, "--store" .. file_arg
    }):nofiles()

local gateway = clink.argmatcher()
    :addarg({
        "downloadSettings" .. gateway_download,
        "downloadsettings" .. gateway_download,
        "download-settings" .. gateway_download
    }):addflags(help_flags):nofiles()

local switch = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Switch" })
    :addarg({ "show", "port", "start", "stop", "reset", "save-config", "terminal" })
    :addarg({ "list", "label", "unlabel", "show", "set", "enable", "disable", "reset" })
    :addarg({ fromhistory = true, hint = "Puerto, alias o comando" })
    :addflags({
        "-h", "--help", "/?", "--profile" .. history_value("Perfil"),
        "--profiles" .. file_arg, "--database" .. file_arg, "--dry-run", "--yes"
    }):loop(4)

local function project_action(flags, second_file)
    local matcher = clink.argmatcher():addarg(clink.filematches)
    if second_file then matcher:addarg(clink.filematches) end
    matcher:addflags(flags or help_flags)
    return matcher
end

local project = clink.argmatcher():addarg({
    "status" .. clink.argmatcher():addflags({ "-h", "--help", "/?", "--json" }):nofiles(),
    "create" .. project_action({
        "-h", "--help", "/?", "--name" .. history_value("Nombre"),
        "--description" .. history_value("Descripción"), "--author" .. history_value("Autor"),
        "--lan-name" .. history_value("LAN"), "--location" .. history_value("Ubicación"),
        "--company" .. history_value("Empresa"), "--responsible" .. history_value("Responsable"),
        "--empty", "--clone-current", "--force"
    }),
    "update" .. project_action(), "info" .. project_action({ "-h", "--help", "/?", "--json" }),
    "verify" .. project_action({ "-h", "--help", "/?", "--json" }),
    "use" .. project_action(), "list" .. project_action(),
    "save" .. clink.argmatcher():addflags(help_flags):nofiles()
}):addflags(help_flags):nofiles()

local plugin_id = history_value("ID del plugin")
local plugin = clink.argmatcher():addarg({
    "list" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "catalog" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "info" .. clink.argmatcher():addarg({ fromhistory = true }):addflags(help_flags):nofiles(),
    "install" .. project_action(),
    "enable" .. clink.argmatcher():addarg({ fromhistory = true }):addflags({ "-h", "--help", "/?", "--grant" .. history_value("Permiso"), "--grant-all", "--trust" }):nofiles(),
    "disable" .. plugin_id, "reload" .. plugin_id, "uninstall" .. plugin_id,
    "verify" .. project_action(), "permissions" .. plugin_id, "revoke" .. plugin_id,
    "publisher" .. clink.argmatcher():addarg({ "list", "trust", "revoke" }):addflags({ "-h", "--help", "/?", "--name" .. history_value("Editor") }),
    "extensions" .. clink.argmatcher():addflags({ "-h", "--help", "/?", "--type" .. history_value("Tipo") }):nofiles(),
    "pack" .. project_action({ "-h", "--help", "/?", "--force", "--signing-key" .. file_arg }, true)
}):addflags(help_flags):nofiles()

local language = clink.argmatcher():addarg({
    "list" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "use" .. history_value("Idioma"), "info" .. history_value("Idioma"),
    "install" .. project_action(), "validate" .. project_action(), "export" .. project_action()
}):addflags(help_flags):nofiles()

local access = clink.argmatcher()
    :addarg({ "status", "configure", "enable", "disable", "user", "session", "certificate", "host-key" })
    :addflags({ "-h", "--help", "/?", "--bind", "--cidr", "--port", "--password-auth", "--role", "--ssh-key", "--expires", "--permission", "--certificate", "--private-key", "--common-name", "--yes", "--json", "--scope", "--config", "--users" })
    :nofiles()

local lanwire = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "Comando o argumento de LANWIRE" })
    :addflags({ "-h", "--help", "/?", "--new-window" })
    :loop()

local error_lookup = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "0eXXXXXXXX" })
    :addflags({ "-h", "--help", "/?", "--json" })
    :nofiles()

local database = clink.argmatcher()
    :addflags({
        "-h", "--help", "/?", "--diagnose",
        "--export" .. file_arg, "--verify" .. file_arg,
        "--import" .. file_arg, "--restore" .. file_arg,
        "--target" .. values({ "database", "groups", "physical" }), "--yes", "--json"
    })

local demo = clink.argmatcher()
    :addflags({
        "-h", "--help", "/?", "--output" .. file_arg, "--force",
        "--format" .. values({ "json", "html", "all" })
    })

local lab = clink.argmatcher()
    :addarg({ "generate", "network", "device", "list", "validate", "start", "stop", "status", "evolve", "export", "import" })
    :addflags({
        "-h", "--help", "/?", "--name", "--cidr", "--profile", "--devices", "--seed",
        "--active-percent", "--dhcp-percent", "--type", "--ip", "--mac", "--alias",
        "--inactive", "--seconds", "--format", "--output"
    }):loop()

-- Árbol completo de los ejecutables especializados.  Se mantiene aquí, en vez
-- de usar passthrough, para que una versión estable congele también su contrato
-- de terminal y no sólo el parser de Python.
local wire_idf = clink.argmatcher():addarg({
    "list" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Prefijo opcional" }):addflags(help_flags):nofiles(),
    "types" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "show" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Prefijo o IDF" }):addflags(help_flags):nofiles(),
    "edit" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Prefijo o IDF" }):addarg({ fromhistory = true, hint = "CAMPO=VALOR" }):addflags({
        "-h", "--help", "/?", "-type" .. history_value("Perfil físico"),
        "-name" .. history_value("Nombre"), "-alias" .. history_value("Alias"),
        "-description" .. history_value("Descripción")
    }):loop(),
    "delete" .. clink.argmatcher():addarg({ fromhistory = true, hint = "IDF" }):addflags(help_flags):nofiles(),
    "del" .. clink.argmatcher():addarg({ fromhistory = true, hint = "IDF" }):addflags(help_flags):nofiles(),
    "new" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Prefijo" }):addflags({
        "-h", "--help", "/?", "-type" .. history_value("Perfil físico"),
        "-name" .. history_value("Nombre"), "-alias" .. history_value("Alias"),
        "-description" .. history_value("Descripción"), "-descriptionn" .. history_value("Descripción")
    }):nofiles(),
    "add" .. clink.argmatcher():addarg({ fromhistory = true, hint = "IDF exacto" }):addflags({
        "-h", "--help", "/?", "-name" .. history_value("Nombre"),
        "-alias" .. history_value("Alias"), "-description" .. history_value("Descripción"),
        "-descriptionn" .. history_value("Descripción")
    }):nofiles()
}):addflags(help_flags):nofiles()

local wire_prefix = clink.argmatcher():addarg({
    "list" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "ls" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "show" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Letras" }):addflags(help_flags):nofiles(),
    "set" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Letras" }):addarg({ fromhistory = true, hint = "Nombre" }):addarg({ fromhistory = true, hint = "Descripción opcional" }):addflags(help_flags):nofiles(),
    "delete" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Letras" }):addflags(help_flags):nofiles(),
    "del" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Letras" }):addflags(help_flags):nofiles()
}):addflags(help_flags):nofiles()

local function configure_lanwire(matcher)
    return matcher:addarg({
        "tui", "cli", "help",
        "list" .. history_value("Prefijo opcional"), "ls" .. history_value("Prefijo opcional"),
        "seed", "show" .. history_value("IDF"),
        "add" .. clink.argmatcher():addarg({ fromhistory = true, hint = "Prefijo" }):addflags({
            "-h", "--help", "/?", "--digits" .. values({ "2", "3", "4", "5" }),
            "-more" .. history_value("Cantidad"), "--more" .. history_value("Cantidad")
        }):nofiles(),
        "idf" .. wire_idf,
        "reserve" .. clink.argmatcher():addarg({ fromhistory = true, hint = "IDF" }):addarg({ fromhistory = true, hint = "CLAVE=VALOR" }):addflags(help_flags):loop(),
        "element" .. clink.argmatcher():addarg({ fromhistory = true, hint = "IDF" }):addarg({ fromhistory = true, hint = "CAMPO=VALOR" }):addflags(help_flags):loop(),
        "delete" .. history_value("IDF"), "del" .. history_value("IDF"),
        "graph", "map", "prefix" .. wire_prefix
    }):addflags({
        "-h", "--help", "/?", "--version", "--database" .. file_arg,
        "-tui", "--tui", "--cli", "-cli"
    }):nofiles()
end

local function configure_lanrack(matcher)
    return matcher:addarg({
        "list", "ls", "show" .. history_value("ID o nombre del rack")
    }):addflags({
        "-h", "--help", "/?", "--version", "--database" .. file_arg,
        "-tui", "--tui", "--cli", "-cli"
    }):nofiles()
end

local access_credential = clink.argmatcher():addarg({
    "list", "show" .. history_value("ID de credencial"),
    "delete" .. history_value("ID de credencial"),
    "set" .. clink.argmatcher():addarg(selector):addarg(protocols):addflags({
        "-h", "--help", "/?", "--username" .. history_value("Usuario")
    }):nofiles(),
    "export" .. file_arg, "import" .. file_arg,
    "copy" .. clink.argmatcher():addarg(clink.filematches):addflags({
        "-h", "--help", "/?", "--target-cipher" .. values({ "dpapi", "portable" })
    }):nofiles(),
    "recover" .. clink.argmatcher():addflags({ "-h", "--help", "/?", "--yes" }):nofiles()
}):addflags(help_flags):nofiles()

local function configure_lanaccess(matcher)
    return matcher:addarg({
        "list", "ls", "show" .. history_value("ID de credencial"),
        "set" .. clink.argmatcher():addarg(selector):addarg(protocols):addflags({
            "-h", "--help", "/?", "--username" .. history_value("Usuario"),
            "-user" .. history_value("Usuario")
        }):nofiles(),
        "delete" .. history_value("ID de credencial"), "del" .. history_value("ID de credencial"),
        "credential" .. access_credential, "doctor",
        "settings" .. clink.argmatcher():addarg({ "show", "use-store" }):addarg(clink.filematches):addflags({ "-h", "--help", "/?", "--yes" }):nofiles(),
        "protocol" .. clink.argmatcher():addarg({ "list", "configure" }):addarg(selector):addarg(protocols):addflags({
            "-h", "--help", "/?", "--port" .. history_value("Puerto"),
            "--driver" .. history_value("Driver")
        }):nofiles(),
        "user" .. clink.argmatcher():addarg({ "list", "add", "enable", "disable", "delete" }):addarg({ fromhistory = true, hint = "Usuario" }):addflags({
            "-h", "--help", "/?", "--role" .. values({ "viewer", "operator", "manager", "administrator" }), "--yes"
        }):nofiles()
    }):addflags({
        "-h", "--help", "/?", "--version", "--database" .. file_arg,
        "--store" .. file_arg, "--cipher" .. values({ "auto", "dpapi", "portable" }),
        "--scope" .. values({ "program", "windows", "project" }),
        "--project-dir" .. dir_arg, "-tui", "--tui", "--cli", "-cli"
    }):nofiles()
end

local function configure_lanmon(matcher)
    return matcher:addarg({
        "logs", "events", "status", "attach", "detach", "once", "session",
        "incidents", "incident", "service", "foreground", "configure", "profile",
        "assign", "unassign", "assignments", "report", "ping", "scan", "identify", "health"
    }):addflags({
        "-h", "--help", "/?", "--version", "--cli", "-cli", "--tui", "-tui",
        "--source" .. values({ "all", "program", "project" }),
        "--limit" .. history_value("1-1000"), "--level" .. error_log_levels,
        "--project" .. file_arg, "--permanent", "--duration" .. history_value("Duración"),
        "--mode" .. values({ "permanent", "temporary", "diagnostic", "once" }),
        "--authority" .. values({ "observe", "operate", "administer" }),
        "--json", "--yes", "--interval" .. history_value("Duración"),
        "--every" .. history_value("Duración"), "--group" .. history_value("Grupo"),
        "--type" .. values({ "presence", "services", "ports", "identity", "smb", "full" }),
        "--fast", "--unknown", "--follow", "--sessions" .. file_arg,
        "--incidents-store" .. file_arg, "--lock" .. file_arg, "--monitor-db" .. file_arg,
        "--profiles" .. file_arg, "--assignments-store" .. file_arg,
        "--profile" .. history_value("Perfil"),
        "--priority" .. values({ "low", "normal", "high", "critical" }),
        "--check" .. history_value("ping, arp o port:NN"),
        "--presence" .. history_value("Duración"), "--discovery" .. history_value("Duración"),
        "--services" .. history_value("Duración"), "--deep" .. history_value("Duración"),
        "--workers" .. history_value("Workers"), "--timeout" .. history_value("Segundos")
    }):loop()
end

local root_commands = {
    "ephemeral" .. ephemeral, "-e" .. ephemeral,
    "list" .. list, "recurrent" .. recurrent, "ping" .. ping,
    "open" .. open, "connect" .. open,
    "settings" .. settings, "call" .. call, "search" .. search, "scan" .. scan,
    "element" .. element, "group" .. group, "credential" .. credential,
    "credentials" .. credential, "auth" .. credential, "protocol" .. protocol,
    "switch" .. switch, "cnf" .. simple_selector, "ssh" .. ssh,
    "radmin" .. radmin, "wol" .. wol, "history" .. history,
    "monitor" .. monitor, "smb" .. smb, "access" .. access,
    "terminal" .. terminal, "cli" .. terminal,
    "GATEWAY" .. gateway, "gateway" .. gateway,
    "downloadSettings" .. download_settings,
    "downloadsettings" .. download_settings,
    "download-settings" .. download_settings,
    "project" .. project, "projects" .. project, "plugin" .. plugin,
    "plugins" .. plugin, "addon" .. plugin, "addons" .. plugin,
    "language" .. language, "languages" .. language, "lang" .. language,
    "error" .. error_lookup, "errors" .. error_lookup,
    "database" .. database, "db" .. database, "demo" .. demo,
    "lanwire" .. lanwire, "wire" .. lanwire, "lab" .. lab
}

local function configure_lanip(matcher)
    return matcher
        :addarg(root_commands)
        :addflags({
            "-h", "--help", "/?", "--version", "--quiet", "--verbose", "--gui", "--cli", "-cli", "-tui", "--tui",
            "-project" .. file_arg, "--project" .. file_arg
        })
        :nofiles()
end

local function passthrough(hint)
    return clink.argmatcher()
        :addarg({ fromhistory = true, hint = hint })
        :addflags(help_flags)
        :loop()
end

-- `lanip` y el alias histórico `als` comparten el árbol completo de LANIP.
configure_lanip(clink.argmatcher("lanip", "lanip.exe", "als", "als.exe"))

configure_lanwire(clink.argmatcher("lanwire", "lanwire.exe"))
configure_lanrack(clink.argmatcher("lanrack", "lanrack.exe"))
configure_lanaccess(clink.argmatcher("lanaccess", "lanaccess.exe"))
configure_lanmon(clink.argmatcher("lanmon", "lanmon.exe"))

local suite_commands = {}
for _, command in ipairs(root_commands) do
    table.insert(suite_commands, command)
end
local suite_launchers = {
    "lanip" .. configure_lanip(clink.argmatcher()),
    "ip" .. configure_lanip(clink.argmatcher()),
    "lanwire" .. configure_lanwire(clink.argmatcher()), "wire" .. configure_lanwire(clink.argmatcher()),
    "lanrack" .. configure_lanrack(clink.argmatcher()), "rack" .. configure_lanrack(clink.argmatcher()),
    "lanaccess" .. configure_lanaccess(clink.argmatcher()), "access" .. configure_lanaccess(clink.argmatcher()),
    "lanmon" .. configure_lanmon(clink.argmatcher()), "monitor" .. configure_lanmon(clink.argmatcher())
}
for _, launcher in ipairs(suite_launchers) do
    table.insert(suite_commands, launcher)
end

clink.argmatcher("lanctl", "lanctl.exe", "LANCTL.exe")
    :addarg(suite_commands)
    :addflags({
        "-h", "--help", "/?", "--version", "--cli", "-cli", "-tui", "--tui", "--admin"
    })
    :nofiles()
