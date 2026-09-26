"""CLI and TUI adapters for the root launcher."""

from lanctl.core.interactive_console import command_console


def run_console(*, tui=False):
    from lanctl.bootstrap.lanctl import main

    return command_console(
        "LANCTL",
        main,
        tui=tui,
        overview=(
            "1  LANIP       Inventario lógico y descubrimiento\n"
            "2  LANWIRE     Cableado y topología física\n"
            "3  LANRACK     Visualización de racks\n"
            "4  LANACCESS   Credenciales y accesos\n"
            "5  LANMON      Monitorización y eventos\n\n"
            "Número: abrir TUI · lanip --cli: abrir CLI\n"
            "settings: configuración · plugin: plugins · language: idioma\n"
            "help settings: opciones de configuración\n"
            "Las aplicaciones vuelven aquí al cerrarse. No se escanea al abrir la suite."
        ),
        shortcuts={
            str(i): [app, "--tui"]
            for i, app in enumerate(("lanip", "lanwire", "lanrack", "lanaccess", "lanmon"), 1)
        },
    )
