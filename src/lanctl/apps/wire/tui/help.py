"""Ayuda navegable de LANWIRE, con la jerarquía visual de LANIP."""

from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text


@dataclass(frozen=True)
class HelpEntry:
    name: str
    arguments: str
    description: str
    usage: str


COMMANDS = (
    HelpEntry("help", "", "Muestra esta ayuda.", "help"),
    HelpEntry(
        "list", "[PREFIJO|@GRUPO]", "Lista y filtra los IDF físicos.", "list [PREFIJO|@GRUPO]"
    ),
    HelpEntry("idf list", "[PREFIJO]", "Lista prefijos o los IDF de uno.", "idf list [PREFIJO]"),
    HelpEntry("idf types", "", "Enumera los perfiles físicos disponibles.", "idf types"),
    HelpEntry("idf show", "PREFIJO|IDF", "Consulta un perfil o un IDF.", "idf show RT-00"),
    HelpEntry(
        "idf new",
        "PREFIJO -type TIPO",
        "Asigna un perfil físico al prefijo.",
        "idf new FB -type wire.fiber",
    ),
    HelpEntry(
        "idf add",
        "IDF [-name NOMBRE]",
        "Crea un IDF con el perfil del prefijo.",
        "idf add FB-00 -name Fibra",
    ),
    HelpEntry(
        "idf edit",
        "IDF CAMPO=VALOR",
        "Edita datos o el perfil de un prefijo.",
        "idf edit RT-00 alias=Central",
    ),
    HelpEntry("idf delete", "IDF", "Elimina un IDF sin borrar su prefijo.", "idf delete FB-00"),
    HelpEntry("prefix", "list|show|set|delete", "Gestiona los juegos de letras.", "prefix list"),
    HelpEntry("add", "PREFIJO [-more N]", "Genera uno o varios IDF libres.", "add FB -more 3"),
    HelpEntry("reserve", "IDF [CLAVE=VALOR]", "Reserva un identificador exacto.", "reserve FB-09"),
    HelpEntry("show", "[IDF]", "Abre los datos de un elemento.", "show FB-00"),
    HelpEntry(
        "element", "IDF [CAMPO=VALOR]", "Consulta o edita datos y puertos.", "element RT-00 ports=2"
    ),
    HelpEntry("graph", "(map)", "Dibuja la topología física.", "graph"),
    HelpEntry("delete", "IDF", "Elimina un IDF y limpia sus enlaces.", "delete FB-00"),
    HelpEntry("seed", "", "Carga la topología de demostración.", "seed"),
    HelpEntry("clear", "", "Limpia la salida del CLI del TUI.", "clear"),
    HelpEntry("exit", "(quit)", "Cierra LANWIRE.", "exit"),
)

KEYS = (
    "←/→       Cambiar entre Comandos, Detalle y Teclas",
    "↑/↓       Seleccionar comando o desplazar contenido",
    "PgUp/PgDn Avanzar por la lista o el contenido",
    "Home/End   Ir al primer o último comando",
    "Enter      Abrir el detalle del comando seleccionado",
    "Tab        Preparar el comando seleccionado en el prompt",
    "F1 / Esc   Cerrar esta ventana",
    "",
    "EN EL INVENTARIO",
    "Tab        Cambiar ELEMENTS → WIRE → ALL",
    "Enter      Abrir el elemento seleccionado",
    "F3         Seguir el cable o el extremo seleccionado",
    "Delete     Eliminar el elemento con confirmación",
    "F7         Extensiones",
    "F9         Base física activa",
    "F12        Configuración de LANWIRE",
    "Ctrl+S     Guardar preferencias",
    "Ctrl+C     Copiar IDF",
    "Ctrl+J     Copiar JSON",
    "Ctrl+H     Historial",
    "Ctrl+Q     Salir",
)


def help_view(width: int, height: int, tab: int, selected: int, scroll: int) -> Text:
    """Compone la zona interior del modal, ajustada a la terminal actual."""
    width = max(20, width)
    height = max(2, height)
    text = Text(no_wrap=True, overflow="crop")
    for index, label in enumerate(("Comandos", "Detalle", "Teclas")):
        if index:
            text.append("   ")
        text.append(f" {label} ", style="black on bright_cyan" if tab == index else "bright_cyan")
    text.append("\n" + "─" * width, style="grey50")

    if tab == 0:
        visible = max(0, height - 2)
        start = max(0, min(scroll, max(0, len(COMMANDS) - visible)))
        name_width = min(22, max(12, width // 5))
        args_width = min(28, max(12, width // 4))
        for index in range(start, min(len(COMMANDS), start + visible)):
            entry = COMMANDS[index]
            text.append("\n")
            text.append("▸ " if index == selected else "  ", style="bright_cyan")
            text.append(
                f"{entry.name:<{name_width}}",
                style="bright_cyan" if index == selected else "bright_white",
            )
            text.append(f"{entry.arguments:<{args_width}}", style="bright_white")
            text.append(
                entry.description, style="bright_cyan" if index == selected else "bright_white"
            )
    else:
        entry = COMMANDS[selected]
        lines = (
            (
                f"COMANDO  lanwire {entry.name}",
                "",
                entry.description,
                "",
                "USO",
                f"  lanwire {entry.usage}",
                "",
                "El mismo comando está disponible en el prompt de LANWIRE.",
                "Tab lo prepara en el prompt.",
            )
            if tab == 1
            else KEYS
        )
        for line in lines[scroll : scroll + max(0, height - 2)]:
            text.append("\n")
            text.append(
                line, style="bright_cyan" if line in {"USO", "EN EL INVENTARIO"} else "bright_white"
            )
    return text
