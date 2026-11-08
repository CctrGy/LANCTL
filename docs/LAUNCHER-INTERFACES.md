# Interfaces de los launchers

Todos los launchers admiten `--cli` (también `-cli`) y `--tui` (también `-tui`).
Los comandos directos y `/?` siguen disponibles. No cambia el formato de los
proyectos, credenciales ni contratos de plugins.

Todos los launchers incorporan `--gui`. LANIP: [interfaz de escritorio](LANIP-GUI.md).
LANWIRE, LANRACK, LANACCESS y LANMON: [interfaces gráficas](LAUNCHER-GUI.md).
LANCTL incorpora `--gui` para proyectos, plugins, preferencias y terminales:
véase [centro gráfico de LANCTL](LANCTL-GUI.md).

Sin argumentos, los seis launchers usan la preferencia global `startup.interface` (`cli` por
defecto). Se configura con `lanctl settings --startup-interface cli|tui|gui`.
Un comando o interfaz explícitos siempre tienen prioridad. La preferencia no
se aplica a comandos internos ni a la reentrada en una sesión del mismo launcher.
`lanctl lanip` y los demás enrutamientos sin opciones respetan la misma selección
que el ejecutable directo. Los accesos con `--cli`, `--tui` o `--gui` fuerzan
su modo; el host gráfico `lanctl-window.exe` fuerza GUI.

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
Con la preferencia predeterminada `cli`, LANCTL sin argumentos abre su consola
propia; las preferencias `tui` y `gui` abren la interfaz correspondiente.
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

### Creación de accesos Linux desde CLI (P118, entrega parcial)

`lanctl shortcut --mode tui --name "LANCTL TUI"` muestra un plan JSON sin
escribir. Repetir con `--create` crea el `.desktop`, sin reemplazar archivos
existentes. `--launcher lanip` permite elegir otra aplicación. `--destination`
selecciona dónde guardar el acceso; `--working-directory` es independiente y no
selecciona un proyecto. `--icon` admite un archivo de icono opcional.

En distribuciones compiladas, la carpeta predeterminada es la del ejecutable
real (`sys.executable`), nunca el directorio de extracción. Desde fuentes debe
indicarse `--distribution /ruta/a/los/ejecutables`; no se crean accesos al Python
del entorno virtual. Por defecto el archivo se guarda junto a esos ejecutables;
si la carpeta está protegida, elegir un destino del usuario: no hay elevación ni
redirección silenciosa. CLI/TUI solicitan terminal; GUI no solicita consola.
La disponibilidad de GUI se comprueba por su módulo de escritorio; la futura
separación de componentes P117 necesitará integrar su inventario definitivo.

No hay preguntas que bloqueen SSH o scripts: la vista previa es el paso de
revisión; omitir `--create` cancela sin cambios. Se devuelve 0 al completar la
vista previa o creación y 2 ante un fallo. No se aceptan argumentos libres,
credenciales, reemplazo ni reparación. Las rutas ejecutables con `%` se rechazan
por incompatibilidad comprobada con Gio; `=` no es válido según Desktop Entry.
Según el escritorio puede ser necesario permitir el lanzamiento manualmente.
La certificación nativa y de instalables permanece pendiente; esta entrega
no modifica instaladores ni certifica su comportamiento.

La GUI de LANCTL incluye **Crear acceso directo** en su barra de opciones.
El formulario permite elegir aplicación, modo, nombre, carpetas e icono;
**Revisar acceso** muestra los valores resueltos antes de confirmar **Crear**.
Cancelar la confirmación no escribe; una creación consume la vista previa y
los errores requieren revisar de nuevo antes de reintentar. En otras plataformas se indica que la función no está disponible. No exige un proyecto seleccionado.
El formulario y sus RPC tienen pruebas automatizadas ligeras; queda pendiente
la revisión visual y de navegación en ventanas nativas Windows/Linux.

El adaptador Windows está implementado en fuentes y usa el mismo comando y
formulario para generar `.lnk`. Los modos CLI/TUI apuntan al launcher `.exe`
con `--cli`/`--tui`; GUI usa `lanctl-window.exe` y el identificador del launcher.
Se reutilizan los iconos de terminal o del launcher cuando existen; se admite
icono elegido por el usuario. Windows valida nombres reservados y rechaza `%`
en las rutas que WSH podría interpretar como variables de entorno.

La creación requiere Windows PowerShell del sistema y WScript.Shell disponibles;
si una política corporativa los bloquea, devuelve el diagnóstico sin intentar
eludirla. Los datos se pasan como JSON por stdin, separados del código fijo.
Se crea primero un archivo privado, se verifican sus propiedades y se publica
sin sustituir archivos existentes. Esta implementación todavía requiere pruebas
nativas de Windows y validación en distribuciones instaladas y portables.

### Confirmación del cierre GUI (P90, fuentes del 05/11/2026)

Los seis hosts instalan `NativeClose`. El frontend utiliza
`requestNativeClose`, que prepara un recibo mediante `prepare_native_close`
(envoltorio `project_call`) y lo devuelve por el canal público de estado de
pywebview (`lanctl_close_receipt`). Ese canal no espera una respuesta RPC de
la ventana que se está destruyendo. El receptor espera de forma acotada a que
termine el hilo del RPC de preparación y revalida el contexto del proyecto
antes de llamar al servicio de cierre existente. No añade retardos arbitrarios
ni fuerza la terminación del intérprete. Una preparación pendiente es de un
solo uso y tiene caducidad; los recibos antiguos o desconocidos no cierran nada.

Los fallos conservan origen, errorId y errorDetails; se devuelven a la ventana
abierta mediante `lanctl_close_error`. Los métodos Python `request_close`
mantienen sus firmas anteriores. Los clientes sin el canal de estado conservan
su adaptación anterior; esta compatibilidad no certifica el cierre de clientes
GUI antiguos que destruyan directamente su WebView desde un RPC.

Comprobados 13 recorridos Qt offscreen con proyecto temporal: guardar y cancelar
para cada launcher y descartar en LANIP. El arnés verifica el evento closed,
los datos al reabrir y la ausencia de nuevos hilos no daemon antes de anunciar
éxito. El cierre con varios propietarios y el entorno provisional P98/P99,
Windows y los instalables requieren validación adicional. No equivale a una
revisión visual ni a probar el gesto X del gestor de ventanas real.
