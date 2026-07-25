from __future__ import annotations

from app.cisco.models import CommandSpec, Risk


def _show(path: str, help_text: str) -> CommandSpec:
    parts = tuple(path.split())
    return CommandSpec(
        id="switch." + ".".join(parts), path=parts, aliases=(),
        context=("switch",), risk=Risk.READ_ONLY, help=help_text,
        templates=(path,),
    )


ROOT_COMMANDS = tuple(
    _show(command, help_text)
    for command, help_text in (
        ("show running-config", "Muestra la configuración activa."),
        ("show startup-config", "Muestra la configuración de arranque."),
        ("show version", "Muestra versión y modelo."),
        ("show system", "Muestra información del sistema."),
        ("show clock", "Muestra el reloj del switch."),
        ("show users", "Muestra usuarios conectados."),
        ("show interfaces status", "Resume el estado de interfaces."),
        ("show interfaces counters", "Muestra contadores de interfaces."),
        ("show interfaces description", "Muestra descripciones de interfaces."),
        ("show interfaces switchport", "Muestra configuración switchport."),
        ("show vlan brief", "Resume las VLAN."),
        ("show mac address-table", "Muestra la tabla MAC."),
        ("show arp", "Muestra la tabla ARP."),
        ("show spanning-tree detail", "Muestra Spanning Tree."),
        ("show etherchannel summary", "Resume EtherChannel."),
        ("show ip route", "Muestra rutas IP."),
        ("show ip interface", "Muestra interfaces IP."),
        ("show ip arp", "Muestra ARP IP."),
        ("show logging", "Muestra el registro del equipo."),
        ("show processes", "Muestra procesos."),
        ("show memory", "Muestra uso de memoria."),
        ("show cpu", "Muestra uso de CPU."),
    )
)


PORT_COMMANDS = (
    CommandSpec("switch.port.show.status", ("port", "show", "status"), (), ("switch", "port"), Risk.READ_ONLY, "Estado del puerto.", ("show interfaces status {native_port}",), True),
    CommandSpec("switch.port.show.description", ("port", "show", "description"), (), ("switch", "port"), Risk.READ_ONLY, "Descripción del puerto.", ("show interfaces description {native_port}",), True),
    CommandSpec("switch.port.show.config", ("port", "show", "config"), (("port", "show", "configuration"),), ("switch", "port"), Risk.READ_ONLY, "Configuración del puerto.", ("show interfaces configuration {native_port}",), True),
    CommandSpec("switch.port.show.errors", ("port", "show", "errors"), (), ("switch", "port"), Risk.READ_ONLY, "Errores del puerto.", ("show interfaces errors {native_port}",), True),
    CommandSpec("switch.port.show.vlan", ("port", "show", "vlan"), (), ("switch", "port"), Risk.READ_ONLY, "VLAN del puerto.", ("show interfaces switchport {native_port}",), True),
    CommandSpec("switch.port.set.description", ("port", "set", "description"), (), ("switch", "port"), Risk.CONFIG_CHANGE, "Cambia la descripción.", ("configure terminal", "interface {native_port}", "description {value}"), True, "description"),
    CommandSpec("switch.port.set.speed", ("port", "set", "speed"), (), ("switch", "port"), Risk.CONFIG_CHANGE, "Cambia la velocidad.", ("configure terminal", "interface {native_port}", "speed {value}"), True, "speed"),
    CommandSpec("switch.port.set.duplex", ("port", "set", "duplex"), (), ("switch", "port"), Risk.CONFIG_CHANGE, "Cambia el dúplex.", ("configure terminal", "interface {native_port}", "duplex {value}"), True, "duplex"),
    CommandSpec("switch.port.enable", ("port", "enable"), (("start",),), ("switch", "port"), Risk.CONFIG_CHANGE, "Habilita el puerto.", ("configure terminal", "interface {native_port}", "no shutdown"), True),
    CommandSpec("switch.port.disable", ("port", "disable"), (("stop",),), ("switch", "port"), Risk.CONFIG_CHANGE, "Deshabilita el puerto.", ("configure terminal", "interface {native_port}", "shutdown"), True),
    CommandSpec("switch.port.reset", ("port", "reset"), (("reset",),), ("switch", "port"), Risk.DISRUPTIVE, "Restaura el puerto.", ("configure terminal", "default interface {native_port}"), True),
    CommandSpec("switch.save-config", ("save-config",), (("write",),), ("switch",), Risk.PERSIST_CONFIG, "Guarda running-config.", ("copy running-config startup-config",)),
)


CATALOG = (*ROOT_COMMANDS, *PORT_COMMANDS)


def find_spec(path: tuple[str, ...]) -> CommandSpec:
    normalized = tuple(part.casefold() for part in path)
    for spec in CATALOG:
        if normalized == spec.path or normalized in spec.aliases:
            return spec
    raise ValueError("comando Cisco no permitido: " + " ".join(path))
