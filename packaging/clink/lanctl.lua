-- LANCTL completion for Clink 1.3.23+
-- Development: clink installscripts <path>\packaging\clink
-- Installed layout: <install-dir>\clink\lanctl.lua

local function values(items)
    return clink.argmatcher():addarg(items):nofiles()
end

local function history_value(hint)
    return clink.argmatcher():addarg({ fromhistory = true, hint = hint }):nofiles()
end

local help_flags = { "-h", "--help", "/?" }
local formats = values({ "table", "json", "csv", "html", "xml" })
local discovery = values({ "icmp", "arp", "hybrid" })
local profiles = values({ "fast", "normal", "accurate" })
local scan_orders = values({ "ascending", "descending", "random" })
local on_off = values({ "on", "off" })
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
        "--mode" .. values({ "control", "view" }), "--dry-run",
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
        "--workers" .. history_value("Workers"), "--timeout" .. history_value("Segundos"),
        "--scan-order" .. scan_orders,
        "--max-hosts" .. history_value("Máximo"), "--database" .. file_arg,
        "--groups" .. file_arg, "--log" .. dir_arg,
        "--projects-directory" .. dir_arg,
        "-log-cleanup" .. on_off, "--log-cleanup" .. on_off,
        "-log-retention-days" .. history_value("Días"),
        "--log-retention-days" .. history_value("Días")
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
    :addarg({ "edit", "cnf", "name", "description", "alias", "group", "protocol", "delete", "del", "remove" })
    :addarg({ fromhistory = true, hint = "Valor" })
    :addflags({
        "-h", "--help", "/?", "-add" .. history_value("MAC"),
        "-name" .. history_value("Nombre"), "-alias" .. history_value("Alias"),
        "-description" .. history_value("Descripción"),
        "--database" .. file_arg, "--groups" .. file_arg, "--yes"
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

local name_alias = clink.argmatcher()
    :addarg({ fromhistory = true, hint = "IP, MAC o alias" })
    :addarg({ fromhistory = true, hint = "Nuevo valor" })
    :addflags({ "-h", "--help", "/?", "-def", "-del", "--database" .. file_arg })
    :nofiles()

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
        "-h", "--help", "/?", "--mode" .. values({ "control", "view" }),
        "--port" .. history_value("Puerto"), "--executable" .. file_arg,
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
        "-h", "--help", "/?", "-if" .. history_value("CondiciÃ³n"),
        "--if" .. history_value("CondiciÃ³n"), "--if-all" .. history_value("CondiciÃ³n"),
        "--if-any" .. history_value("CondiciÃ³n"), "--if-not" .. history_value("CondiciÃ³n"),
        "-t" .. history_value("Tiempo"), "--time" .. history_value("Tiempo"),
        "--message" .. history_value("Mensaje"), "--force", "--cancel",
        "--broadcast" .. history_value("IPv4 broadcast"), "--port" .. history_value("Puerto UDP"),
        "--repeat" .. history_value("Repeticiones"), "--interval" .. history_value("Segundos"),
        "--wait" .. history_value("Segundos"), "--method" .. values({ "auto", "arp", "ping", "port" }),
        "--check-port" .. history_value("Puerto TCP"), "--interface" .. history_value("Interfaz/IP"),
        "--retry" .. history_value("Intentos"), "--dry-run", "--json", "--quiet",
        "--group" .. history_value("Grupo"), "--all", "--yes",
        "--after" .. history_value("Dependencia"), "--delay" .. history_value("DuraciÃ³n"),
        "--timeout" .. history_value("Segundos"),
        "--on-failure" .. values({ "stop", "continue", "retry" }),
        "--cooldown" .. history_value("DuraciÃ³n"), "--max-attempts" .. history_value("Intentos"),
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
        "--duration" .. history_value("DuraciÃ³n"),
        "--mode" .. values({ "permanent", "temporary", "diagnostic", "once" }),
        "--authority" .. values({ "observe", "operate", "administer" }),
        "--json", "--yes", "--interval" .. history_value("DuraciÃ³n"),
        "--every" .. history_value("DuraciÃ³n"), "--group" .. history_value("Grupo"),
        "--type" .. values({ "presence", "services", "ports", "identity", "smb", "full" }),
        "--fast", "--unknown", "--follow", "--sessions" .. file_arg,
        "--incidents-store" .. file_arg, "--lock" .. file_arg, "--monitor-db" .. file_arg,
        "--profiles" .. file_arg, "--assignments-store" .. file_arg,
        "--profile" .. history_value("Perfil"),
        "--priority" .. values({ "low", "normal", "high", "critical" }),
        "--check" .. history_value("ping, arp o port:NN"),
        "--presence" .. history_value("DuraciÃ³n"), "--discovery" .. history_value("DuraciÃ³n"),
        "--services" .. history_value("DuraciÃ³n"), "--deep" .. history_value("DuraciÃ³n"),
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
    "create" .. project_action({
        "-h", "--help", "/?", "--name" .. history_value("Nombre"),
        "--description" .. history_value("Descripción"), "--author" .. history_value("Autor"),
        "--lan-name" .. history_value("LAN"), "--location" .. history_value("Ubicación"),
        "--company" .. history_value("Empresa"), "--responsible" .. history_value("Responsable"),
        "--force"
    }),
    "update" .. project_action(), "info" .. project_action({ "-h", "--help", "/?", "--json" }),
    "verify" .. project_action({ "-h", "--help", "/?", "--json" }),
    "use" .. project_action(), "list" .. project_action()
}):addflags(help_flags):nofiles()

local plugin_id = history_value("ID del plugin")
local plugin = clink.argmatcher():addarg({
    "list" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "info" .. clink.argmatcher():addarg({ fromhistory = true }):addflags(help_flags):nofiles(),
    "install" .. project_action(),
    "enable" .. clink.argmatcher():addarg({ fromhistory = true }):addflags({ "-h", "--help", "/?", "--grant" .. history_value("Permiso"), "--grant-all", "--trust" }):nofiles(),
    "disable" .. plugin_id, "reload" .. plugin_id, "uninstall" .. plugin_id,
    "verify" .. project_action(), "permissions" .. plugin_id,
    "extensions" .. clink.argmatcher():addflags({ "-h", "--help", "/?", "--type" .. history_value("Tipo") }):nofiles(),
    "pack" .. project_action({ "-h", "--help", "/?", "--force" }, true)
}):addflags(help_flags):nofiles()

local language = clink.argmatcher():addarg({
    "list" .. clink.argmatcher():addflags(help_flags):nofiles(),
    "use" .. history_value("Idioma"), "info" .. history_value("Idioma"),
    "install" .. project_action(), "validate" .. project_action(), "export" .. project_action()
}):addflags(help_flags):nofiles()

local virtual_commands = {
    "list" .. list, "recurrent" .. recurrent, "ping" .. ping,
    "open" .. open, "connect" .. open,
    "settings" .. settings, "call" .. call, "search" .. search, "scan" .. scan,
    "element" .. element, "group" .. group, "credential" .. credential,
    "credentials" .. credential, "auth" .. credential, "protocol" .. protocol,
    "switch" .. switch, "name" .. name_alias, "alias" .. name_alias,
    "cnf" .. simple_selector, "ssh" .. ssh,
    "radmin" .. radmin, "wol" .. wol, "history" .. history,
    "monitor" .. monitor, "smb" .. smb,
    "terminal" .. terminal, "cli" .. terminal,
    "GATEWAY" .. gateway, "gateway" .. gateway,
    "downloadSettings" .. download_settings,
    "downloadsettings" .. download_settings,
    "download-settings" .. download_settings,
    "project" .. project, "projects" .. project, "plugin" .. plugin,
    "plugins" .. plugin, "addon" .. plugin, "addons" .. plugin,
    "language" .. language, "languages" .. language, "lang" .. language
}

local virtual = clink.argmatcher()
    :addarg(virtual_commands)
    :addflags({ "-h", "--help", "/?", "--cli" })
    :nofiles()

local root_commands = { "virtual" .. virtual }
for _, command in ipairs(virtual_commands) do
    table.insert(root_commands, command)
end

clink.argmatcher("lanctl", "lanctl.exe", "als", "als.exe")
    :addarg(root_commands)
    :addflags({
        "-h", "--help", "/?", "--version", "--gui", "--cli", "-tui", "--tui"
    })
    :nofiles()
