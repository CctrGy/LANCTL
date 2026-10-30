"""Reviewed dynamic presentation templates. Values preserve their original formatting."""

SUMMARY_MESSAGES = {
    "LANCTL.UI.SUMMARY.VALUEVALUENETWORK_INVENTORY_SUMMARYVALUE": (
        "{value0}{value1}NETWORK INVENTORY SUMMARY{value2}",
        "{value0}{value1}NETWORK INVENTORY SUMMARY{value2}",
    ),
    "LANCTL.UI.SUMMARY.DEVICES_VALUE": (" Devices       : {value0}", " Devices       : {value0}"),
    "LANCTL.UI.SUMMARY.WITH_IP_MAC_VALUE_VALUE": (
        " With IP / MAC : {value0} / {value1}",
        " With IP / MAC : {value0} / {value1}",
    ),
    "LANCTL.UI.SUMMARY.GROUPS_VALUE": (" Groups        : {value0}", " Groups        : {value0}"),
    "LANCTL.UI.SUMMARY.PROTOCOLS_VALUE": (" Protocols     : {value0}", " Protocols     : {value0}"),
    "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUEU_VALUE_INCHES_VALUE_ELEMENTS": (
        "{value0} | {value1} | {value2}U | {value3} inches | {value4} elements",
        "{value0} | {value1} | {value2}U | {value3} pulgadas | {value4} elementos",
    ),
    "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUEU_VALUE_INCHES_VALUE_ELEMENTS_0F275CC5": (
        "{value0} {value1} · {value2}U · {value3} inches · {value4} elements",
        "{value0} {value1} · {value2}U · {value3} pulgadas · {value4} elementos",
    ),
    "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUE_USERNAME": (
        "{value0} {value1} {value2} USERNAME",
        "{value0} {value1} {value2} USUARIO",
    ),
    "LANCTL.UI.SUMMARY.LANCTL_UNIFIED_LOG_VALUE_CTRL_C_TO_STOP_FOLLOWING": (
        "LANCTL · Unified log · {value0}\nCtrl+C to stop following.",
        "LANCTL · Log unificado · {value0}\nCtrl+C para cerrar el seguimiento.",
    ),
    "LANCTL.UI.SUMMARY.REGISTERED_IP_VALUE": (
        "  Registered IP: {value0}",
        "  IP registrada: {value0}",
    ),
    "LANCTL.UI.SUMMARY.REGISTERED_MAC_VALUE": (
        "  Registered MAC: {value0}",
        "  MAC registrada: {value0}",
    ),
    "LANCTL.UI.SUMMARY.OBSERVED_MAC_VALUE": (
        "  Observed MAC: {value0}",
        "  MAC observada: {value0}",
    ),
    "LANCTL.UI.SUMMARY.REGISTERED_MAC_VALUE_7A1F0852": (
        "Registered MAC: {value0}",
        "MAC registrada: {value0}",
    ),
    "LANCTL.UI.SUMMARY.MAC_OBSERVED_IN_ARP_VALUE": (
        "MAC observed in ARP: {value0}",
        "MAC observada en ARP: {value0}",
    ),
    "LANCTL.UI.SUMMARY.PROBED_IP_VALUE": ("Probed IP: {value0}", "IP comprobada: {value0}"),
    "LANCTL.UI.SUMMARY.VALUE_VALUE_DISABLED": (
        "{value0} {value1} | disabled",
        "{value0} {value1} | desactivado",
    ),
    "LANCTL.UI.SUMMARY.VALUE_REMOVED_FROM_THE_DATABASE_AND_ALL_GROUPS": (
        "{value0} | removed from the database and all groups",
        "{value0} | retirado de la base y de todos los grupos",
    ),
    "LANCTL.UI.SUMMARY.VALUE_VALUE_DEVICES": (
        "{value0} | {value1} devices",
        "{value0} | {value1} dispositivos",
    ),
    "LANCTL.UI.SUMMARY.VALUE_ELEMENTS_IMPORTED_SAVE_THE_PROJECT_WITH_PROJECT_SAVE": (
        "{value0} elements imported; save the project with project save",
        "{value0} elementos importados; guarda el proyecto con project save",
    ),
    "LANCTL.UI.SUMMARY.VALUE_SSH_CONFIGURED_ONLY_FOR_THIS_ELEMENT": (
        "{value0} | ssh configured only for this element",
        "{value0} | ssh configurado solo para este elemento",
    ),
    "LANCTL.UI.SUMMARY.LANWIRE_STARTED_DATA_VALUE": (
        "LANWIRE started | data: {value0}",
        "LANWIRE iniciado | datos: {value0}",
    ),
    "LANCTL.UI.SUMMARY.HISTORY_VALUE": ("HISTORY — {value0}", "HISTORIAL — {value0}"),
    "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUE_PORTS": (
        "{value0} | {value1} | {value2} ports",
        "{value0} | {value1} | {value2} puertos",
    ),
    "LANCTL.UI.SUMMARY.OBSERVED_MAC_VALUE_8B6BBDFA": (
        "  Observed MAC : {value0}",
        "  MAC observada : {value0}",
    ),
    "LANCTL.UI.SUMMARY.VALUE_VALUE_DEVICES_SEED_VALUE": (
        "{value0} | {value1} devices | seed {value2}",
        "{value0} | {value1} dispositivos | seed {value2}",
    ),
    "LANCTL.UI.SUMMARY.VALUE_PURELY_VIRTUAL": (
        "{value0} | purely virtual",
        "{value0} | puramente virtual",
    ),
}

# These legacy source labels were already English; Spanish still needs a translation.
for _key, (_english, _spanish) in tuple(SUMMARY_MESSAGES.items()):
    if _spanish == "{value0}{value1}NETWORK INVENTORY SUMMARY{value2}":
        SUMMARY_MESSAGES[_key] = (_english, "{value0}{value1}RESUMEN DEL INVENTARIO DE RED{value2}")
    elif _spanish == " Devices       : {value0}":
        SUMMARY_MESSAGES[_key] = (_english, " Elementos     : {value0}")
    elif _spanish == " With IP / MAC : {value0} / {value1}":
        SUMMARY_MESSAGES[_key] = (_english, " Con IP / MAC : {value0} / {value1}")
    elif _spanish == " Groups        : {value0}":
        SUMMARY_MESSAGES[_key] = (_english, " Grupos        : {value0}")
    elif _spanish == " Protocols     : {value0}":
        SUMMARY_MESSAGES[_key] = (_english, " Protocolos    : {value0}")
