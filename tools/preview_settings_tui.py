"""Standalone SETTINGS design preview. All values are fictional and in memory."""

from __future__ import annotations

import os
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from lanctl.apps.ip.interfaces.tui.keyboard import (
    posix_terminal_mode,
    read_posix_key,
    read_windows_key,
)
from lanctl.core.terminal_ui import ManagementScreen

ACCENT = "bright_green"


@dataclass
class Field:
    label: str
    value: str | bool
    hint: str
    choices: tuple[str, ...] = ()


def sample():
    return {
        "General": [
            Field(
                "Nombre del entorno",
                "Mi red local",
                "Nombre descriptivo para identificar este entorno.",
            ),
            Field(
                "Carpeta de proyectos",
                "~/Documentos/LanCTL",
                "Campo de texto de ejemplo; no se crean carpetas.",
            ),
            Field(
                "Interfaz al iniciar",
                "TUI",
                "Selecciona la interfaz de inicio.",
                ("TUI", "GUI", "CLI"),
            ),
            Field(
                "Consultar antes de cerrar",
                True,
                "Casilla: pulsa Espacio para activar o desactivar.",
            ),
        ],
        "Red": [
            Field(
                "Rango de red",
                "192.168.1.0/24",
                "Ejemplo de campo de texto para una red en formato CIDR.",
            ),
            Field(
                "Perfil de escaneo",
                "Normal",
                "Elige una opción de la lista.",
                ("Rápido", "Normal", "Preciso"),
            ),
            Field(
                "Tiempo de espera (s)",
                "1.5",
                "Ejemplo de campo numérico; esta maqueta no ejecuta escaneos.",
            ),
            Field("Resolver nombres DNS", True, "Activa o desactiva la consulta de nombres."),
        ],
        "Apariencia": [
            Field(
                "Tema",
                "Oscuro",
                "Selector de ejemplo; no cambia el tema del programa.",
                ("Oscuro", "Claro", "Sistema"),
            ),
            Field("Densidad", "Cómoda", "Espaciado de los controles.", ("Cómoda", "Compacta")),
            Field("Mostrar ayudas", True, "Ejemplo de preferencia de presentación."),
            Field("Animaciones", False, "Casilla de ejemplo para opciones visuales."),
        ],
    }


class SettingsPreview:
    def __init__(self):
        self.groups = sample()
        self.tab = self.focus = 0
        self.mode = ""
        self.draft = ""
        self.fresh = True
        self.choice = 0
        self.running = True
        self.status = "PROTOTIPO · Datos de ejemplo. No lee ni modifica tu configuración."

    @property
    def fields(self):
        return list(self.groups.values())[self.tab]

    def view(self):
        tabs = Text()
        for index, title in enumerate(self.groups):
            tabs.append(
                f"  {title}  ", style=f"bold black on {ACCENT}" if index == self.tab else "dim"
            )
            tabs.append("  ")
        controls = Text()
        for index, field in enumerate(self.fields):
            focused = index == self.focus
            controls.append("\n  > " if focused else "\n    ", style=ACCENT)
            controls.append(field.label + "\n      ", style="bold" if focused else "dim")
            if isinstance(field.value, bool):
                value = "[x] Activado" if field.value else "[ ] Desactivado"
            elif self.mode == "text" and focused:
                value = "[ " + self.draft + "▏ ]"
            elif field.choices:
                value = "[ " + str(field.value) + "  ▾ ]"
            else:
                value = "[ " + str(field.value) + " ]"
            controls.append(value + "\n", style=ACCENT if focused else "white")
        hint = (
            self.fields[self.focus].hint
            if self.focus < len(self.fields)
            else "Guardar solo simula la acción; Cancelar cierra el prototipo."
        )
        actions = Text("\n  ")
        for index, label in enumerate(
            ("Guardar ejemplo", "Restablecer", "Cancelar"), len(self.fields)
        ):
            actions.append(
                f" [ {label} ] ", style=f"bold black on {ACCENT}" if self.focus == index else ACCENT
            )
            actions.append("  ")
        content = Group(tabs, controls, Text("\n  " + hint, style="dim"), actions)
        if self.mode == "pick":
            picker = Text()
            for index, label in enumerate(self.fields[self.focus].choices):
                picker.append(
                    ("> " if index == self.choice else "  ") + label + "\n",
                    style=ACCENT if index == self.choice else "white",
                )
            content = Group(
                content,
                Panel(
                    picker,
                    title="Seleccionar opción",
                    subtitle="↑↓ elegir · Enter aceptar · Esc cancelar",
                    border_style=ACCENT,
                ),
            )
        return Group(
            Panel(content, title="LANCTL · SETTINGS · Vista de ejemplo", border_style=ACCENT),
            Text(self.status, style="dim"),
            Text(
                "←→ pestaña · Tab/↑↓ control · Enter editar · Espacio casilla · Ctrl+S simular guardado · Esc salir",
                style=ACCENT,
            ),
        )

    def handle(self, key):
        if self.mode == "text":
            if key == "ESC":
                self.mode = ""
            elif key == "ENTER":
                self.fields[self.focus].value = self.draft
                self.mode = ""
            elif key == "BACKSPACE":
                self.draft = self.draft[:-1]
                self.fresh = False
            elif key == "DELETE":
                self.draft = ""
                self.fresh = False
            elif len(key) == 1 and key.isprintable():
                self.draft = key if self.fresh else self.draft + key
                self.fresh = False
            return
        if self.mode == "pick":
            options = self.fields[self.focus].choices
            if key in ("UP", "DOWN"):
                self.choice = (self.choice + (-1 if key == "UP" else 1)) % len(options)
            elif key == "ENTER":
                self.fields[self.focus].value = options[self.choice]
                self.mode = ""
            elif key == "ESC":
                self.mode = ""
            return
        if key in ("ESC", "CTRL_Q"):
            self.running = False
        elif key in ("LEFT", "RIGHT"):
            self.tab = (self.tab + (-1 if key == "LEFT" else 1)) % len(self.groups)
            self.focus = 0
        elif key in ("UP", "DOWN", "TAB", "SHIFT_TAB"):
            self.focus = (self.focus + (-1 if key in ("UP", "SHIFT_TAB") else 1)) % (
                len(self.fields) + 3
            )
        elif key == "CTRL_S":
            self.status = "Guardado simulado. No se ha escrito ningún archivo."
        elif key in ("ENTER", " ", "SPACE"):
            if self.focus == len(self.fields):
                self.status = "Guardado simulado. No se ha escrito ningún archivo."
            elif self.focus == len(self.fields) + 1:
                self.groups = sample()
                self.status = "Valores de ejemplo restablecidos."
            elif self.focus == len(self.fields) + 2:
                self.running = False
            else:
                field = self.fields[self.focus]
                if isinstance(field.value, bool):
                    field.value = not field.value
                elif field.choices:
                    self.choice = field.choices.index(field.value)
                    self.mode = "pick"
                else:
                    self.draft = str(field.value)
                    self.fresh = True
                    self.mode = "text"


def main():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Abre este prototipo en una terminal interactiva.")
        return 2
    if os.name == "nt":
        from msvcrt import getwch

        def read():
            return read_windows_key(getwch)

        mode = nullcontext()
    else:

        def read():
            return read_posix_key(sys.stdin)

        mode = posix_terminal_mode(sys.stdin)
    preview = SettingsPreview()
    with ManagementScreen() as screen, mode:
        while preview.running:
            screen.draw(preview.view())
            preview.handle(read())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
