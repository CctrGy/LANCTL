# Interfaces de los launchers

Todos los launchers admiten `--cli` (también `-cli`) y `--tui` (también `-tui`).
Los comandos directos y `/?` siguen disponibles. No cambia el formato de los
proyectos, credenciales ni contratos de plugins.

Todos los launchers incorporan `--gui`. LANIP: [interfaz de escritorio](LANIP-GUI.md).
LANWIRE, LANRACK, LANACCESS y LANMON: [interfaces gráficas](LAUNCHER-GUI.md).
LANCTL incorpora `--gui` para proyectos, plugins, preferencias y terminales:
véase [centro gráfico de LANCTL](LANCTL-GUI.md).

Sin argumentos, LANCTL usa la preferencia global `startup.interface` (`cli` por
defecto). Se configura con `lanctl settings --startup-interface cli|tui|gui`.
Un comando o interfaz explícitos siempre tienen prioridad. La preferencia no
cambia el arranque predeterminado de los launchers especializados.

Las instancias comparten [coordinación local](COORDINATION.md): sesiones,
una selección de proyecto común, tareas, eventos y órdenes de refresco dirigidas.
Las operaciones y servicios ya iniciados conservan su contexto hasta terminar;
las siguientes operaciones de las interfaces usan el proyecto seleccionado.
`lanctl backend sessions` lista instancias y `lanmon backend events --follow`
muestra los eventos en vivo, además del seguimiento de logs descrito abajo.

Las consolas LANWIRE/LANRACK aplican la [política de guardado del VLF](VLF.md)
al editar, al cerrar y mediante un temporizador por consola persistente.
`manual.inCloseConsult` permite guardar, salir conservando el workspace o
cancelar. Un error de guardado mantiene la consola abierta para reintentar.
Los comandos aislados y la salida por EOF no preguntan; no crean temporizador.
`--database` fija la base durante toda la invocación. Sin esa opción siguen
el proyecto compartido entre operaciones; la TUI LANWIRE descarta el formulario
pendiente al cambiar de proyecto para no aplicarlo a otro inventario.

## Log operativo unificado en vivo

`lanmon logs --window` abre otra ventana de terminal, muestra las últimas 100
líneas del `programLog` compartido y sigue los nuevos registros de los launchers.
También se puede usar `lanctl lanmon logs --window`. No inicia el backend ni escaneos.
Para verlo en la misma ventana: `lanmon logs --follow`. `Ctrl+C` termina el visor.
`--limit 200 --level 30` ajusta el historial inicial y filtra niveles numéricos;
las líneas sin nivel se conservan. El visor no recupera eventos que el nivel de
registro configurado impidió escribir y no captura stdout ajeno al log.
El seguimiento usa el log operativo común, no las auditorías archivadas dentro
del VLF. `lanmon logs --source project` sigue ofreciendo esa consulta puntual.
La ruta queda fijada al abrir el visor; si se cambia `programLog`, vuelve a abrirlo.
Windows utiliza una consola independiente; Linux requiere x-terminal-emulator o xterm.

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

Comandos básicos dentro de la consola raíz:

| Comando | Acción |
| --- | --- |
| `clear` / `cls` | Limpia la pantalla sin borrar datos ni logs |
| `pwd` | Muestra el directorio de trabajo |
| `commands` | Lista los comandos básicos de consola |
| `help [comando]` | Ayuda general o específica |
| `version` | Versión del programa |
| `exit` / `quit` / `q` | Sale o vuelve al llamador |

Estos comandos pertenecen a la sesión interactiva, no al shell de Windows.
`clear` no emite secuencias de control cuando la salida está redirigida.
En los paneles de comandos compartidos, limpia el estado y redibuja el panel.

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

LANRACK conserva sus consultas CLI/TUI y añade gestión de agrupaciones CPD
en la GUI sobre el inventario compartido. LANBACK no se añade como aplicación ficticia.
Las configuraciones compartidas todavía usan el adaptador compatible de LANIP.
ProjectDock es una herramienta de desarrollo, no una dependencia de ejecución.

## Preferencias por interfaz y launcher — P69, 22/10/2026

El catálogo de usuario usa una lista explícita compartida en
`core/settings_policy.py`. GUI, TUI y CLI consultan y guardan solamente sus
preferencias y los ajustes funcionales comunes. `startup.interface` es común;
`startup.closeGuiOnLaunch` corresponde a LANCTL GUI; `gui.*` a las GUI,
`tui.*` a LANIP TUI, `cli.*` e `ip.progress` a CLI, e `ip.listColumns` a CLI/TUI.
El catálogo general LANCTL administra todos los dominios; el editor específico
de cada launcher añade sus ajustes de dominio a los comunes. LANWIRE TUI mantiene
sus preferencias en su archivo propio, con validación de claves y valores.

El adaptador fija el contexto. Los nombres enviados por WebView no pueden
convertir una llamada GUI en CLI. Un terminal integrado sigue siendo CLI.
Rutas de bases, locks, secretos, esquemas, identificadores y estado automático
no aparecen como preferencias. Ocultar un campo no borra su valor persistente.
El proyecto conserva su editor compartido, sus IDs y sus verificaciones VLF.

`settings --menu`, `--catalog`, `--get` y `--set` ofrecen preferencias comunes
y CLI. La consulta sin opciones conserva un objeto JSON agrupado, filtrado;
deja de ser un volcado de la configuración interna. Los campos omitidos siguen
almacenados y consumidos por su interfaz. Las opciones locales explícitas
`--tui-*` y `--close-gui-on-launch` conservan su contrato de administración de
otra interfaz; las opciones históricas de rutas conservan su ruta administrativa.
Estas excepciones no se aplican a `--set`, formularios ni sesiones remotas.
Los permisos LANACCESS y la transacción de recuperación se conservan; incluso
una solicitud remota sin cambios de valor debe superar la autorización.
