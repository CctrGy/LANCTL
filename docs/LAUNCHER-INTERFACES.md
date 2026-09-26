# Interfaces de los launchers

Todos los launchers admiten `--cli` (también `-cli`) y `--tui` (también `-tui`).
Los comandos directos y `/?` siguen disponibles. No cambia el formato de los
proyectos, credenciales ni contratos de plugins.

| Launcher | CLI interactivo | TUI |
| --- | --- | --- |
| LANCTL | Consola de orquestación propia | Panel de aplicaciones y comandos |
| LANIP | Consola de inventario existente | Inventario interactivo existente |
| LANWIRE | Consola de cableado existente | Topología y edición existentes |
| LANRACK | list, show y ayuda | Panel de racks y los mismos comandos |
| LANACCESS | Gestión de credenciales existente | Gestión de accesos existente |
| LANMON | Todos los comandos del monitor | Panel de comandos de monitorización |

Ejemplos:

```text
lanctl --cli
lanctl --tui
lanctl lanip --tui
lanwire --cli
lanrack --tui
lanaccess --cli
lanmon --tui
```

En la consola raíz se escribe `lanip --tui`, `lanwire --cli`, `settings`,
`plugin list` o `language list`. `help settings` muestra las opciones compartidas.
Los números 1–5 abren las aplicaciones en TUI. `exit` vuelve al llamador.
LANCTL sin argumentos abre su CLI propio: ya no abre el inventario de LANIP.
La entrada raíz no escanea ni inicia servicios al abrirse.

La aplicación raíz vive en `apps/suite/interfaces.py`; el anfitrión común de
consolas está en `core/interactive_console.py` y recibe un despachador sin
importar aplicaciones. Cada aplicación conserva sus servicios y comandos.

Los paneles nuevos LANCTL/LANMON/LANRACK son interfaces de comandos con Enter,
no editores con navegación inmediata por flechas. Suspenden el alternate buffer
durante las operaciones para que los prompts y los TUI anidados conserven sus
flujos de terminal. La salida se muestra directamente, sin capturar contraseñas
ni convertir pantallas interactivas en logs. Enter devuelve al panel.
El tamaño se recalcula al dibujar; no hay repintado autónomo durante `input()`.
Los TUI especializados de LANIP/LANWIRE conservan sus controles actuales.

LANRACK continúa siendo visor; LANBACK no se añade como aplicación ficticia.
Las configuraciones compartidas todavía usan el adaptador compatible de LANIP.
ProjectDock es una herramienta de desarrollo, no una dependencia de ejecución.
