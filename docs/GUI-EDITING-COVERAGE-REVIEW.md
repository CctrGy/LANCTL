# Revisión de estructura y cobertura de edición de la GUI

Fecha: 10/11/2026. Revisión del checkout local, incluidos cambios pendientes.
No representa una certificación de instalables ni autoriza modificaciones de
proyectos reales. No se han cambiado datos personales ni código operativo.

## Resultado

La GUI dispone de una base amplia de edición, pero no puede declararse que
estén todas las opciones requeridas: hay funciones pendientes identificadas,
diferencias respecto a CLI y recorridos cuya organización resulta ambigua.
No se recomienda añadir un editor libre de todos los campos JSON: identificadores,
versiones, revisiones, métricas y relaciones protegidas tienen restricciones.

La referencia de esta revisión son los servicios editables actuales, sus rutas
GUI y los requisitos abiertos del backlog. Una opción presente en CLI no se
considera automáticamente obligatoria en todos los launchers. Cuando no hay un
requisito de paridad aprobado, se indica como diferencia de alcance.

## Estructura observada

| Capa | Fuentes principales | Responsabilidad |
| --- | --- | --- |
| Centro de aplicaciones | `gui/suite.html`, `suite.js`, `suite-settings.js`; `SuiteApi` | Proyectos, plugins, preferencias y apertura de launchers |
| Inventario lógico | `gui/index.html`, `desktop.js`, `device-sheet.js`; `DesktopApi`/`GuiApi` | Elementos LANIP, ficha, grupos, diagnóstico y acceso |
| Contenedor de cuatro launchers | `gui/launcher.html`, `launcher.js`; `LauncherApi` | Cabecera, acciones, ficha modal, refresco, proyecto y guardado |
| Edición física | `wire-gui.js`, `physical-gui.js`, `physical-editor.js`, `rack-dimensions.js`, `rack-skins.js` | Elementos, puertos, cableado, ubicación, racks, CPD y frentes |
| Edición lógica especializada | `record-editors.js`, `monitor-support.js` | Credenciales, equipo monitorizado, grupos, incidencias y reportes |
| Servicios | `WireGuiService`, `RackService`, `AccessGuiService`, `MonitorGuiService`, `core/inventory_editing.py` | Validación, revisiones y persistencia |
| Contexto y guardado | `GuiSupportMixin.project_call`, `core/project_context.py`, `core/projects/*` | Rechazo de contexto obsoleto, workspace, VLF y política de guardado |

`launcher.html` carga extensiones que reasignan funciones globales como `render`,
`fullDetails`, `call` y `refresh`. Esto permite reutilizar la edición de LANWIRE
en LANRACK, pero obliga a revisar el orden de carga y la implementación final:
leer solo `launcher.js` o la primera definición de una ficha da una imagen
incompleta. Por ejemplo, `physical-editor.js` reemplaza la antigua consulta del
ocupante por una ficha editable y adapta los RPC `wire_*` a `rack_element`.

La reutilización de servicios es adecuada y debe conservarse. Como mejora
incremental, conviene registrar acciones y editores por entidad/launcher de
forma explícita, manteniendo los RPC compatibles. No hace falta una reescritura
para corregir los huecos funcionales identificados.

## Matriz de opciones

| Launcher | Elementos y opciones presentes en fuentes | Límites y pendientes |
| --- | --- | --- |
| LANCTL | Crear, abrir y guardar proyectos; nombre, descripción, autor y metadatos LAN; preferencias de programa/proyecto; plugins, permisos y configuración | Eliminar proyectos no está expuesto: P125. Firma autorizada de plugins sigue siendo P40/P42. No sustituye a los editores de inventario |
| LANIP | Alta manual; nombre, alias, descripción, IP, IDF, icono y confirmación; crear grupos y añadir/retirar pertenencias; borrar equipo, deshacer/rehacer y acciones de diagnóstico/acceso | No hay gestión gráfica completa del grupo: renombrar, editar descripción y eliminar. Incidencia P127 de asignación requiere reproducción específica; la existencia del control no demuestra que ese caso esté resuelto |
| LANWIRE | Equipos, cables, racks, CPD; nombre/alias/descripción, grupos, conexión cable/Wi-Fi/mixta, IP, velocidades; ubicación; medio/PoE de puertos, renombrado/orden; extremos de cables; dimensiones de rack; edición/borrado | Ver detalles y Editar convergen a la misma ficha: P129. Topología y lista requieren una presentación de acciones coherente. Ancho de columnas transversal sigue en P126 |
| LANRACK | CPD y asignación de racks; alta de rack, altura/ancho; ficha editable del elemento con ubicación interior/entorno/independiente/bandeja, altura U, mover, alojar, puertos/conexiones, borrar y personalizar frente | Menú contextual por unidad ocupada/vacía y alta/asignación preseleccionadas siguen en P130. No afirmar que solo permite consultar o que toda edición exige abrir LANWIRE |
| LANACCESS | Crear credencial por equipo/protocolo, usuario y contraseña; cambiar usuario conservando secreto; rotar contraseña con confirmación; borrar, conectar, bloquear/desbloquear | Equipo/protocolo/ID de una credencial existente son de lectura por contrato. No es un editor de ubicación física; no debe devolver secretos actuales al frontend |
| LANMON | Editar nombre, alias, descripción e IP; añadir/retirar grupos existentes; iniciar/detener/comprobar; reconocer/cerrar incidencias; actividad, logs y reportes | No hay editor dedicado de perfiles/asignaciones avanzadas. Sus métricas, estados observados y muestras son de lectura. La ficha de equipo no tiene por qué duplicar todos los campos LANIP |

### Campos físicos cubiertos

`WireGuiService._fields` admite nombre, alias, descripción, colocación,
connectionMode, groups, speeds, IP, medio de cable y dimensiones de rack.
`wire-gui.js` construye los campos correspondientes y envía `portChanges` para
medio/PoE. Los cambios de nombre/orden de puerto y de extremos tienen operaciones
separadas. `physical-editor.js` añade rack, unidad, altura U, bandeja y clase de
ubicación. `RackService.edit_element` reutiliza esas operaciones con revisión
completa del inventario. La forma SVG de un frente no crea ni renumera puertos.

### Campos lógicos cubiertos

`core/inventory_editing.py` limita edición a alias, nombre, descripción, icono,
confirmación, IP e IDF. LANIP dispone de controles para ellos; MAC se ofrece en
el alta y no aparece como edición ordinaria en ese contrato. No se registra esa
restricción como un simple botón ausente. LANMON reduce intencionadamente la
ficha a nombre, alias, descripción e IP y publica pertenencias por separado.

## Hallazgos concretos y acciones recomendadas

1. **P130 — interacción por unidad de rack pendiente.** Existen edición, movimiento,
   ocupación y validaciones de ubicación, pero no el menú solicitado por unidad.
   Añadir acciones vinculadas al ocupante o al destino U, tanto con ratón como
   con teclado. Reutilizar los servicios existentes; no generar otra identidad
   al asignar ni mover equipos implícitamente al crear.
2. **P129 — consulta/edición ambiguas en LANWIRE.** `launcher.js:action` envía
   detalles a `fullDetails`; `wire-gui.js:wireEdit` también llama a `fullDetails`
   para LANWIRE. La convergencia queda confirmada en fuentes. Unificar la entrada
   o distinguir consulta y edición de forma real; probar cancelación y guardado.
3. **LANIP — falta CRUD gráfico del catálogo de grupos.** `DesktopApi.group_action`
   admite create/add/remove y `create_group` permite descripción al crear. Core
   y CLI también ofrecen rename/delete/set_description, sin ruta GUI equivalente
   localizada. Completar el gestor con confirmaciones y protección de BASIC,
   conservando pertenencias. Esta carencia es distinta del fallo comunicado P127.
4. **P125 — eliminación de proyectos no ofrecida en LANCTL.** Mantenerla como
   tarea independiente, con confirmación, identificación de VLF/workspace y
   guardas de proyecto abierto. Esta revisión no elimina proyectos.
5. **LANMON — paridad avanzada por decidir.** `monitor/commands.py` y
   `monitor/configuration.py` permiten perfiles, checks, prioridades y asignaciones;
   `MonitorGuiService.action` publica solo start/stop/once y arranca con opciones
   predeterminadas. Configuración genérica/CLI no equivalen a un editor dedicado.
   Definir si el alcance requerido incluye administrar estas entidades desde GUI.
6. **Descripción desactualizada de LANRACK.** `LAUNCHER-GUI.md` todavía indica
   que la edición de equipos/cables sigue en LANWIRE; las extensiones actuales
   sí la implementan dentro de LANRACK. La definición de launcher en
   `gui/launcher.js` también utiliza el subtítulo
   `VIEW_RACKS_AND_OCCUPANTS_EDITING_IS_AVAILABLE_IN_LANWIRE`, que no explica
   la edición local actual. Actualizar documentación y recursos de idioma junto
   a una prueba de ficha final para evitar anunciar capacidades equivocadas.
7. **Coherencia y descubribilidad transversal.** P128 ya aporta Guardar proyecto
   en los dos launchers físicos; P98/P99 conserva trabajo pendiente sin proyecto.
   Proponer una estructura estable: acciones de colección (Nuevo/filtrar), acciones
   del seleccionado (Ficha/Editar/Mover/Eliminar) y acciones de proyecto (Guardar).
   Diferenciar Guardar ficha —workspace— de Guardar proyecto —VLF—. No cambiar
   automáticamente una política de autoguardado elegida por el usuario.

## Distinciones que deben quedar claras

- LANIP/LANMON editan inventario lógico. LANWIRE/LANRACK comparten inventario
  físico. El campo IDF permite relacionarlos, pero no se ha acreditado un editor
  único que sincronice automáticamente cualquier propiedad entre ambas entidades.
  Diseñar ese enlace antes de prometer que editar un nombre en una vista cambia
  el de todas las demás.
- Posición manual del lienzo, zoom y columnas son preferencias visuales; rack,
  unidad, altura y extremos de cable son datos del proyecto. Guardar el VLF no
  debe presentarse como prueba de exportación de todas las preferencias locales.
- ID público, revisión, historial, versión de esquema, métricas y contraseñas
  actuales no se vuelven editables por buscar una interfaz «completa».
- Un control presente en las fuentes no demuestra accesibilidad, permisos,
  persistencia ni disponibilidad en el ejecutable instalado. Tampoco basta una
  prueba de servicio para cerrar un requisito de menú o disposición visual.

## Evidencia y límites de esta revisión

Se inspeccionaron las páginas productivas, su orden de scripts, los adaptadores
RPC, los validadores/servicios editables y las entradas P125–P130, P94/P100 y
P98/P99. Las pruebas usan datos temporales, sin sondeos de la red doméstica.

- Servicios y formularios: `test_launcher_gui.py`, `test_physical_placement_gui.py`,
  `test_rack_dimensions.py`, `test_rack_skins.py`, `test_manual_device.py` y
  `test_settings_window.py`: **58 correctas, 7 omitidas** (navegador opcional).
- Edición lógica compartida: `test_view_editing.py`: **20 correctas**.
- Chromium local con RPC real: `test_launcher_save.py`,
  `test_manual_device_browser.py`, `test_settings_window_browser.py`:
  **12 correctas**. Incluyen teclado, edición, contexto, guardado y temas.

Además pasan dos recorridos de edición LANMON/LANIP y credenciales, y uno de
ubicación/bandejas LANRACK con feedback LANWIRE. Se ejecutaron con español
instalado explícitamente en los directorios temporales y adaptando solo el
lanzamiento de msedge a Chromium en el proceso de revisión. El intento previo
sin fijar idioma tuvo fallos por selectores de texto españoles; detalle en
`BACKLOG-VERIFICATION.md`. Ningún test histórico se ha modificado.
No se certifican Windows, Qt, instaladores ni todas las combinaciones posibles
de tipo de elemento, tema, idioma, escala y tamaño. El inventario anterior es
una revisión trazable de cobertura, no una afirmación de ausencia total de fallos.
