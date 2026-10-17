# Comprobación del backlog — 15/10/2026

Evidencia de los 33 puntos de [BACKLOG.md](BACKLOG.md), sobre la versión de
desarrollo 0.3.3. «Verificado» identifica el alcance local indicado, con datos de
prueba aislados. No implica certificación de instalaciones ni plataformas no
ejecutadas. Los cambios permanecen en la rama de trabajo, sin publicación.

## Resultado por punto

| Punto | Resultado y alcance comprobado | Evidencia reproducible |
| --- | --- | --- |
| P01 | Corregido: Ctrl+S guarda SETTINGS y formularios de proyectos; POSIX desactiva IXON/IXOFF y restaura el TTY al salir. | `test_backlog_projects.py`, `test_tui.py` |
| P02 | Verificado: detección de cambios, escritura atómica, bloqueo, error de disco, recarga y conservación semántica del inventario. | `test_project_save_policy.py`, `test_file_transaction.py`, `gui_native_smoke.py` |
| P03 | Verificado: guardado activo/sin proyecto, atajo reasignado en gestores y con escaneo activo; los formularios guardan sus propios datos. Los modales de acceso/cierre conservan sus acciones locales. | `test_backlog_projects.py`, `test_tui.py` |
| P04 | Verificado: descubrimiento, paquetes, dependencias, permisos, activación, revocación y error; esquema de configuración inválido no oculta todos los plugins. | `test_plugins.py`, `test_backlog_plugins.py`, `test_suite_gui.py` |
| P05 | Corregido el flujo GUI de confianza: distingue falta de firma y falta de autorización del editor. Un LCP firmado coincidente puede autorizarse; cancelar, otra versión o paquete sin firma no concede confianza. | `test_backlog_plugins.py`, `test_suite_browser.py` |
| P06 | Corregido: Configurar depende de campos disponibles, incluidos valores por defecto sin archivo guardado; se recalcula al cargar el catálogo. | `test_backlog_plugins.py`, `test_suite_browser.py` |
| P07 | Verificado: guardado manual del proyecto activo. Editar otro proyecto modifica sus metadatos directamente, sin copiarle el inventario activo. | `test_tui.py`, `test_project_save_policy.py`, `gui_native_smoke.py` |
| P08 | Implementados los siete campos: nombre, descripción, autor, LAN, ubicación, empresa y responsable. Se mantienen UUID, inventario y hashes válidos. | `test_backlog_projects.py`, `test_settings_catalog.py` |
| P09 | Formularios TUI/GUI de creación y edición; vista compacta y desplazamiento hasta el campo seleccionado. | `test_tui.py`, `test_backlog_projects.py`, `test_suite_browser.py` |
| P10 | Validación antes de escribir; cancelación de cambios requiere confirmación. Una revisión obsoleta o un fallo de disco conserva el VLF anterior. | `test_backlog_projects.py`, `test_suite_browser.py` |
| P11 | Catálogo e información se recargan tras operaciones; la edición de un proyecto no activo notifica al proyecto correcto sin cambiar las sesiones. | `test_project_catalog.py`, `test_backlog_projects.py`, `test_tui.py` |
| P12 | Preferencia persistente CLI/TUI/GUI sin argumentos y prioridad de argumentos explícitos. Probada selección en código y ejecutables; GUI nativa sin argumentos. CLI/TUI empaquetados probados con entrada redirigida, no con clic manual en Explorer. | `test_backlog_startup.py`, `gui_coordination_smoke.py`, `portable_smoke.py` |
| P13 | Cierre opcional de LANCTL solo tras confirmar disponibilidad del launcher. Fallo conserva ventana; prueba nativa confirma que el hijo sobrevive al padre. | `test_backlog_startup.py`, `gui_coordination_smoke.py` |
| P14 | Exclusión real entre procesos, recuperación después de terminar el propietario, restauración y primer plano en Windows. Aperturas simultáneas del ejecutable portable dejan una sola GUI. | `test_backlog_startup.py`, `gui_coordination_smoke.py`, `portable_smoke.py` |
| P15 | LANCTL/LANIP simultáneos, feedback de apertura/cierre, eventos dirigidos al proyecto correcto y aislamiento entre proyectos. Las demás aplicaciones tienen coordinación CLI/TUI, no una GUI nueva. | `test_coordination.py`, `test_backlog_projects.py`, ambos smokes de coordinación/portable |
| P16 | Flecha independiente → con fondo de tecla en Plugins. | `test_tui_render.py::RichTuiRendererTests::test_plugin_footer_styles_standalone_arrow_as_keycap` |
| P17 | Estilo común de flechas, funciones, Supr, Enter, Esc, Ctrl y Shift+Tab; pies actualizados para guardar y editar proyectos. | `test_tui_render.py`, `controllers.py`, `managers.py` |
| P18 | Conflictos y teclas reservadas rechazados sin escritura; None desactiva, reasignar el valor inicial persiste; Esc restaura la edición del campo. | `test_backlog_projects.py`, `test_settings.py`, `test_tui.py` |
| P19 | Visibilidad del botón y asignación del atajo se verifican por separado; ocultar no desactiva. | `test_settings.py`, `test_tui.py` |
| P20 | Atajos del gestor consumidos dentro del modal; crear/editar no se despachan como acciones de inventario. | `test_tui.py`, `test_backlog_projects.py` |
| P21 | Inicio/cancelación/fallo/final de escaneo, guardado con/sin cambios, recarga y errores recuperables quedan visibles. | `test_tui.py`, `test_backlog_projects.py` |
| P22 | Mensaje final junto al prompt; selección anterior de salida se limpia. Errores nuevos conservan origen y catálogo. | `test_tui.py`, `test_error_catalog.py`, `test_errors.py` |
| P23 | Salida retenida: 2.000 líneas; historial: 500 comandos. Ajuste al ancho y navegación de salida/historial verificados. | `test_backlog_projects.py`, `test_tui.py`, `test_tui_components.py` |
| P24 | Revisados componentes compartidos de overlays: bordes, pestaña seleccionada, separación, ancho Unicode y fondos. Es verificación automatizada del renderizador; no una revisión física de todas las terminales. | `test_tui_render.py`, `test_tui_components.py` |
| P25 | Tamaños 40×12, 80×24, 160×50 y 240×70; el formulario mantiene visible su último campo. | `test_backlog_projects.py`, `test_tui_components.py` |
| P26 | Cobertura del rectángulo modal, captura de fondo y limpieza al redimensionar; no se borra toda la pantalla en cada frame. El parpadeo perceptible depende del terminal. | `test_tui_render.py`, `test_tui_components.py` |
| P27 | Selección, edición activa, asterisco de cambios y controles deshabilitados usan los estilos comunes; confirmación antes de descartar. | `test_tui_components.py`, `test_backlog_projects.py`, `test_suite_browser.py` |
| P28 | Validada la corrección de interfaz que ya estaba en curso: listas de 50 elementos, búsqueda, scroll y barra accesible en 790×570, 660×460 y 375×650. | `test_suite_browser.py::test_suite_footer_stays_visible_when_lists_scroll` |
| P29 | Procesos simultáneos, exclusión de archivo, escrituras atómicas, instantáneas obsoletas y contexto de sesiones. | `test_file_transaction.py`, `test_coordination.py`, `test_audit_regressions.py`, `test_backlog_projects.py` |
| P30 | No se solapan escaneos; cancelación, recuperación tras fallo, cierre de CLI integrado y liberación del bloqueo GUI después de una caída. | `test_tui.py`, `test_suite_gui.py`, `test_backlog_startup.py`, smokes nativos |
| P31 | Catálogo regenerado, orígenes conservados, contratos de eventos/funciones sin renombrar y comunicación por proyecto. | `test_error_catalog.py`, `test_errors.py`, `test_plugins.py`, `test_coordination.py` |
| P32 | **Parcial**: Windows desde fuentes y seis ejecutables portable comprobados. Pendientes Windows instalado limpio, Linux ARM64 y sesión SSH real desde otro equipo. | Comandos abajo; `.github/workflows/release.yml` contiene la matriz de distribución |
| P33 | Hallazgos, reproducción, gravedad, correcciones y límites registrados en este documento. | Tabla siguiente |

## Hallazgos corregidos

| Gravedad | Reproducción / problema | Impacto y aceptación |
| --- | --- | --- |
| Alta | Editar metadatos desde dos ventanas y guardar la antigua después. | Evita pérdida silenciosa: revisión optimista rechaza el segundo guardado y conserva inventario/UUID. |
| Alta | Abrir simultáneamente dos GUI del mismo launcher. | Evita duplicados y estados divergentes: bloqueo de vida del proceso, foco de instancia existente y recuperación tras caída. |
| Media | Ctrl+S en SETTINGS o en formulario de proyecto; terminal POSIX con IXON. | Antes no confirmaba el formulario o podía pausar la salida. Guarda el destino local y conserva/restaura los atributos TTY. |
| Media | Seleccionar y editar proyecto B desde una sesión cuyo activo es A. | Los observadores de B no recibían el aviso. Ahora se publica sobre B y A conserva su contexto. |
| Media | Activar WOL sin firma marcando todos los permisos. | La GUI explicaba el fallo demasiado tarde y remitía solo al CLI. Distingue firma/confianza y ofrece autorización verificable de un LCP firmado. |
| Media | Cancelar/cerrar un formulario GUI/TUI con cambios. | Evita perder la edición sin una decisión explícita. |
| Media | Cambiar continuamente de comandos con salidas grandes. | Retención acotada de historial y salida; conserva las entradas más recientes. |
| Baja | Plugin sin campos que ofrece Configurar. | Elimina paneles vacíos sin ocultar ajustes predeterminados disponibles. |
| Baja | Redimensionar un formulario largo o mostrar categorías con texto mal codificado. | Campo seleccionado visible, filas ajustadas al ancho y etiquetas corregidas. |

## Contratos y alcance

- Se conservan IDs públicos de cuatro segmentos, contratos de eventos y funciones,
  formatos VLF/LCP y rutas de importación. No se mueve ni renombra un contrato.
- `startup` es una ampliación aditiva del esquema de configuración. Los archivos
  previos mantienen CLI y ventana principal abierta. Se conservan aliases planos
  para consumidores existentes.
- `DesktopApi.create_project` conserva sus argumentos anteriores; los metadatos
  son un argumento opcional. La edición usa un servicio común para TUI/GUI.
- La cola de coordinación mantiene versión 1, propietarios y acciones permitidas;
  `view gui` se admite también para la GUI raíz. No se habilita ejecución de shell.
- La validación de editores, firmas y permisos no se relaja. Para activar el WOL
  distribuido sin firma aún hace falta publicar/obtener un LCP firmado por su editor.

## Ejecución reproducible

Resultado de la suite completa, incluidas GUI legacy y pruebas de navegador:
**964 pruebas y 643 subpruebas aprobadas; 1 prueba POSIX omitida en Windows**.
Cobertura combinada de líneas/ramas: **67,55 %**, superior al mínimo del 60 %.
Ruff, formato, Bandit (perfil de release), catálogos, referencias, higiene y
comprobación de espacios de Git pasan. Los smokes nativos de Windows también
confirman restauración/primer plano y supervivencia del launcher al cerrar LANCTL.

En Windows, desde el entorno `.venv` del proyecto:

```powershell
$env:LANCTL_GUI_BROWSER_TESTS='1'
python -m coverage run --branch --source=src -m pytest -m 'legacy_gui or not legacy_gui' -q
python -m coverage report --precision=2 --fail-under=60
python tests/gui_native_smoke.py
python tests/gui_coordination_smoke.py
python tests/portable_smoke.py RUTA_BUILD_AISLADO
python -m ruff check .
python -m ruff format --check .
python -m bandit -q -r src -ll -s B104
python tools/generate_error_catalog.py --check
python tools/generate_cli_reference.py --check
python tools/generate_web_reference.py --check
python tools/check_repository_hygiene.py
git diff --check
```

El smoke portable utiliza el marcador portable y datos exclusivos de su build.
Prueba los seis launchers, preferencia sin argumentos, prioridad de `--cli`,
dos aperturas simultáneas, restauración y cierre independiente. No instala el
programa ni publica los ejecutables generados.

La prueba de IPC parcialmente recibido es específica de pipes POSIX y se omite
en Windows; debe ejecutarse en Linux. La suite de acceso remoto cubre validación,
autorización y encaminamiento, pero no sustituye conectar por SSH desde otra
máquina ni verificar un instalador con servicios y permisos reales.

## Pendientes externos concretos

1. Windows limpio: instalar, actualizar y desinstalar Setup; repetir el arranque
   con doble clic en Explorer y terminal interactiva para CLI/TUI/GUI. No se
   altera la instalación del usuario para simular una máquina de pruebas.
2. Linux ARM64: suite completa, prueba POSIX omitida aquí, paquete y terminal
   real. Este equipo no tiene una distribución WSL instalada ni un runner ARM64.
3. Acceso remoto: sesión SSH real, persistencia/cancelación y desconexión desde
   otro equipo autorizado; aquí solo se verifican sus regresiones locales.
4. Distribución de WOL: obtener/publicar el LCP firmado y su huella de editor;
   el arreglo de interfaz no convierte el paquete sin firma en uno autorizado.

## Revisión de backend de plugins — 16/10/2026 (P34, P40/P42)

Alcance de AUDITOR: `core/plugins/manager.py`, `package.py`, `publishers.py`,
regresiones nuevas en `tests/test_plugin_security_review.py` y documentación.
GUI-DESIGN conserva las ventanas, formularios, diálogos, estilos y empaquetado.
Las correcciones se realizan en la rama de trabajo existente, sin modificar
los paquetes instalados ni conceder permisos o confianza en los datos del usuario.

### Hallazgos reproducidos y correcciones

Antes de corregir se ejecutaron 20 casos nuevos: los 20 fallaron y reprodujeron
los problemas descritos. Se amplió después la cobertura a concurrencia,
dependencias, reinstalación y recuperación.

| Gravedad | Problema confirmado | Corrección y efecto futuro |
| --- | --- | --- |
| Alta | `verify ID` devolvía válido sin leer los archivos; activar/recargar podía ejecutar código modificado después del descubrimiento. | Verificación del directorio, checksum y firma antes de publicar la instalación y antes de cargar código o extensiones. El contenido alterado queda bloqueado. |
| Alta | La firma se recuperaba del texto guardado en el registro; borrar o alterar `meta/signature` no invalidaba esa confianza. Los paquetes preinstalados firmados podían aparecer como `UNSIGNED`. | Verificación criptográfica Ed25519 de los bytes instalados y cotejo con la identidad previamente registrada. Descubrimiento recupera la firma real sin autorizar al editor automáticamente. |
| Alta | El arranque omitía permisos, compatibilidad y dependencias; una activación fallida podía dejar el runtime anterior funcionando. | Mismas precondiciones al activar y restaurar; descarga de módulos, procesos y registros al fallar. |
| Alta | Dos gestores podían sobrescribir cambios ajenos y restaurar permisos revocados. Autorizar un editor concurrentemente también podía deshacer una revocación. | Bloqueo de lectura/modificación/escritura, actualización por plugin y rechazo de revisiones antiguas antes de reemplazar o activar; transacción completa del almacén de editores. |
| Media | El orden de arranque dependía del nombre visible y se ignoraban versiones de dependencias. | Orden por dependencias, restricciones de versión, rechazo de ciclos y fallos; descarga de consumidores locales al desactivar su dependencia. |
| Media | Repetir activación, descubrir de nuevo o reinstalar perdía referencias al runtime anterior. | Activación idempotente y limpieza antes de redescubrir/reemplazar. |
| Alta | Un fallo de disco al persistir la activación dejaba el código cargado aunque la operación devolviese error. | Tanto activación manual como arranque descargan sus runtimes si no pueden guardar el estado; el registro anterior permanece intacto. |
| Media | El motivo de bloqueo no siempre persistía; la cuarentena desaparecía del catálogo tras otro reinicio. | Motivo de fallo persistente y conservación de la cuarentena visible, sin que su historial haga reaparecer plugins desinstalados. |
| Media | Registros corruptos se interpretaban como vacíos o causaban excepciones de estructura sin contexto. | Validación de esquema y tipos; error contextual sin sobrescribir el documento dañado. |

### Estado observado y límites

Lectura de los paquetes incluidos y del registro local de desarrollo: MAC
Vendor, mDNS/SSDP, Windows SMB y WOL usan `trusted`, carecen de firma y figuran
desactivados. El tema y Network Summary Example figuran activados y usan
`isolated`; el emulador de red también es `isolated` y figura desactivado.
Esta lectura no certifica el estado de otro directorio de datos o instalación.

El bloqueo de mDNS/SSDP y WOL mostrado en las capturas es correcto para los LCP
actuales. Las pruebas positivas firman paquetes con claves efímeras en carpetas
temporales, autorizan explícitamente al editor de prueba y verifican activación
y revocación. No sustituyen la entrega de paquetes firmados por el editor real.

P34 sigue parcial: falta notificar y aplicar inmediatamente las revocaciones
en otros procesos ya activos y actualizar sus vistas. La protección añadida
evita sobrescribir el estado nuevo y bloquea operaciones posteriores con copias
antiguas; no detiene por sí sola código `trusted` que ya esté ejecutándose en
otro proceso. La publicación de LCP oficiales y las plataformas de P32 siguen
pendientes. P40/P42 describen la misma incidencia, con alcance técnico y visual.

Se conservan métodos públicos, valores de `PluginState`, esquemas de registro 1,
formatos LCP/VLF e IDs de eventos/funciones del Core. La salida de `verify ID`
añade checksum y firma comprobados a sus campos anteriores. Las entradas de
dependencias existentes con `*` siguen siendo válidas. Un registro corrupto
ahora exige reparación explícita en lugar de activar valores por defecto.

### Validación de esta revisión

Suite completa final, incluidas GUI legacy y pruebas de navegador:
**1.013 pruebas y 643 subpruebas aprobadas; 1 prueba POSIX omitida en Windows**,
en 113,72 segundos. Cobertura combinada: **67,83 %**, por encima del mínimo
del 60 %. Las fuentes comprobadas no cambiaron durante la ejecución.
Los resultados del 15/10/2026 de la sección anterior son históricos.

Comparación con HEAD: conservadas las **28 firmas públicas/estructuras** de
los tres módulos modificados y el catálogo de eventos del Core. Los comandos
reproducibles de suite/cobertura son los indicados en la sección anterior;
las regresiones específicas se ejecutan con:

```text
python -m pytest tests/test_plugin_security_review.py -q
```

Las **43 regresiones nuevas** pasan. Bandit con el perfil de release, Ruff lint,
referencias CLI/web, catálogo de errores (1.237 puntos) e higiene pasan. El
formato de los cuatro archivos Python de esta revisión también pasa.

El formato global aún señala cinco archivos del trabajo paralelo de GUI-DESIGN:
`src/lanctl/apps/ip/interfaces/gui/desktop.py`, `src/lanctl/apps/suite/gui.py`,
`src/lanctl/core/session.py`, `tests/test_distribution.py` y
`tests/test_suite_browser.py`. AUDITOR no los modifica para evitar solaparse.
Queda pendiente ese ajuste antes de integrar. Los binarios/instaladores generados
en paralelo tampoco se consideran certificados por estas pruebas de fuentes;
deberán incorporar las correcciones finales del backend y validarse después.

## GUI: comprobación local del 16/10/2026

- P36/P41: `test_project_defaults_do_not_require_a_folder_picker` y navegador
  comprueban carpeta predeterminada editable y LAN inicial sin selector obligatorio.
- P37/P39: `test_home_terminal_and_project_defaults_fit_client_area` comprueba
  Inicio sin scroll y salida de terminal desplazable con entrada visible a
  790×570, 660×460 y 1440×900.
- P38: `test_complete_settings_catalog_and_edit_use_shared_validation` compara
  el catálogo completo y comprueba guardado y rechazo de un valor inválido.
- Confirmaciones: `test_project_edit_form_discard_confirmation_and_preserved_revision`
  comprueba el diálogo de aplicación y la conservación de cambios al cancelar.
- Plugins GUI: `test_signed_plugin_replacement_checks_identity_and_signature`
  verifica ID/firma antes de instalar y que no se concede confianza implícita.
- Smoke nativo local: LANCTL verifica catálogo, valores iniciales, icono HICON
  y cierre; LANIP verifica crear/editar/grupos/guardar/cambiar/restaurar/cerrar.
- Pasada completa local: 961 pruebas, 643 subtests; seis omitidas y 21 excluidas.
  Las pruebas de navegador se ejecutaron por separado con su opción habilitada.

Estas verificaciones no certifican Linux ni una instalación limpia de Windows.
La auditoría de distribución de firmas de plugins se mantiene en AUDITOR.

## P43: carga de iconos en Windows — 16/10/2026

Causa reproducida: `run_gui()` de LANCTL y LANIP entregaba respectivamente
`lanctl.png` y `lanip.png` a `webview.start`. El backend WinForms de pywebview
invoca `System.Drawing.Icon` sin convertir la imagen. Ambos PNG generan la
misma `ArgumentException` de la traza original; los ICO incluidos cargan como
iconos nativos de 32×32. La selección del recurso queda centralizada en
`apps/suite/window_style.py`: ICO en Windows, PNG en las otras plataformas.
No se modifica la dependencia instalada ni se oculta la excepción con un
manejador genérico. No cambian imágenes, estilos, parsers ni contratos del Core.

`tests/test_gui_window_icons.py` ejecuta los dos puntos de entrada con WebView
simulado, comprueba plataforma y contenido del recurso, y repite con una ruta
de extracción PyInstaller con espacios. Cuatro casos adicionales usan el
constructor real de .NET en Windows y liberan sus recursos. Resultado antes
de corregir: ocho fallos y ocho aprobados; después: **16 aprobados**. Con las
pruebas relacionadas de GUI y distribución: **69 aprobados**.

GUI-DESIGN comenzó otros cambios durante esta revisión. Para verificar P43 sin
incorporar trabajo incompleto, se exportó `a6fadc8e88cd0ac3fcd41e882cec57ff74c489b2`
y se aplicaron únicamente los tres módulos de la corrección y su nueva prueba.
Sobre esa copia se ejecutó la suite completa, incluidas GUI legacy y navegador:
**1.029 pruebas y 643 subpruebas aprobadas, una omisión POSIX, 90,94 segundos**.
Comparación AST: conservadas las **101 firmas de funciones y métodos existentes**
de esos tres módulos. Ruff, catálogo de errores (1.237 puntos) y referencias
CLI/web de esa copia pasan. El árbol compartido no se considera certificado
por este resultado: una ejecución anterior coincidió con cambios de GUI-DESIGN
y falló en tres pruebas de sus parsers, distribución y apertura de launchers.

Se compilaron los seis ejecutables desde la copia aislada en `dist/p43-verified`.
Los seis responden correctamente a `--version`. LANCTL y LANIP abren ventanas
nativas con HICON desde fuentes y desde esos ejecutables, sin la excepción de
P43. Se generó `dist/p43-verified/LANCTL-0.3.3-p43-setup.exe`; no se ejecutó el
instalador ni se modificó la instalación del usuario. Los resultados y scripts
de diagnóstico locales están en `.tool-reports/p43/`, incluido
`full-suite-verified.xml`, `snapshot.json` y `contracts.json`.

Límite descubierto en la comprobación nativa: con datos nuevos el registro de
plugins contiene `{}` y el validador lo rechaza. Esto impide el bootstrap de
LANIP, incluso después de corregir el icono; queda registrado como **P44**.
La prueba empaquetada de P43 se repite con un registro de prueba explícitamente
válido (`schemaVersion: 1`, `plugins: {}`). No constituye una validación de
instalación limpia ni resuelve P44. No se alteraron datos reales del usuario.

Comprobación final del adaptador especializado añadido durante el trabajo de
GUI-DESIGN: `suite/launcher_gui.py` repetía el PNG incompatible. Se modificaron
solo la importación del selector y el argumento `icon` de `webview.start`.
Ocho casos nuevos invocan ese punto de entrada con LANWIRE, LANRACK, LANACCESS
y LANMON y cargan el recurso resultante con .NET, desde fuentes y rutas de
extracción. Los ocho reproducen la excepción antes del ajuste y pasan después:
**24 regresiones P43 aprobadas** en el árbol compartido. Esta comprobación no
certifica las nuevas interfaces completas de GUI-DESIGN ni las incorpora al
instalador aislado descrito arriba. La última prueba de los ejecutables aislados
también verifica el cierre normal de LANCTL y LANIP una vez termina su bootstrap.

## Integración de la plantilla de plugins — P44, 16/10/2026

GUI-DESIGN cambió únicamente el documento inicial de `data_migration.py` a
`{"schemaVersion": 1, "plugins": {}}`. AUDITOR verificó el cambio en una carpeta
temporal independiente: `ensure_data_layout()` genera exactamente ese esquema
y el constructor real de `PluginManager` completa el descubrimiento sin el
error del registro. No se cambian el gestor ni sus comprobaciones de permisos,
firmas o confianza de editores durante esta integración.

También se comprobó el caso previo: con `registry.json` igual a `{}`, repetir
`ensure_data_layout()` conserva el archivo y el gestor sigue rechazándolo.
P44 permanece parcial hasta resolver explícitamente esa compatibilidad y
verificar el recorrido de arranque correspondiente. La compilación aislada
`dist/p43-verified` se generó antes del ajuste de la plantilla y no lo contiene.

Validación relacionada: **50 pruebas y 17 subpruebas aprobadas** al ejecutar
`tests/test_data_migration.py` y `tests/test_plugin_security_review.py`.

## Launchers con GUI real: verificación del 16/10/2026

- Suite completa: **1022 pruebas superadas**, 643 subtests; seis omitidas y 21
  excluidas. Navegador: seis pruebas adicionales con la opción habilitada.
- `tests/test_launcher_gui.py`: persistencia IDF, conexiones incompatibles y
  ocupadas, revisión frente a ediciones antiguas, renombrado de puertos y
  actualización de referencias; visor LANRACK; cifrado portable y enlace de
  credenciales; métricas reales guardadas; contexto de proceso; modos directos
  y enrutados; registro inicial de plugins con esquema válido.
- `tests/launcher_gui_native_smoke.py`: cuatro ventanas nativas, API real,
  operaciones con datos temporales, contexto y cierre.
- `tests/launcher_suite_native_smoke.py`: los cuatro botones de LANCTL abren
  simultáneamente sus aplicaciones, reciben IPC y cierran sin dejar sesiones.
- Los cuatro ejecutables compilados se han abierto con `--gui` en este Windows;
  se han comprobado sus recursos frente a las fuentes, iconos HICON, IPC,
  reconocimiento de `--gui` y cierre con código cero.
- Instalador local reconstruido en `dist/gui-current`, incluyendo accesos de
  menú a las seis GUI. No se ha publicado una versión ni ejecutado la matriz de
  instalación limpia/Linux/acceso remoto de P32.

## LANWIRE GUI: lista y topología interactivas (16/10/2026)

- Vistas independientes a pantalla completa; detalle por pestañas con JSON
  copiable, edición validada, grupos del TUI y clasificación cable/Wi-Fi/mixta.
- Lienzo con zoom, desplazamiento, posiciones manuales, distribución por
  componentes, enfoque por niveles, minimapa, navegación y enlaces por puerto.
- Filtros combinables, columnas configurables y redimensionables, selector de
  proyecto VLF y configuración agrupada con etiquetas legibles.
- Almacén físico compartido explícito; fallo de apertura de proyecto conserva
  el contexto. Las revisiones evitan sobrescribir ediciones concurrentes.
- Validación: suite general 1.027 passed, 8 skipped, 21 deselected; prueba de
  navegador contra WireGuiService real (edición, filtros, puertos, desconexión,
  JSON, doble clic y navegación); regresiones visuales de los otros launchers;
  arranque/puente/cierre nativo de LANWIRE en Windows. Los datos usados son
  temporales, sin modificar proyectos ni inventario del usuario.

## P44: migración del registro vacío histórico — 16/10/2026

### Validación y planificación previas

Se revisaron las reglas del proyecto, el estado del árbol compartido y todas
las tareas abiertas. El plan de objetivos, módulos/archivos, dependencias,
conflictos, riesgos e impacto está en «Orden de ejecución validado» del backlog.
P44 se adelantó por bloquear el arranque con datos antiguos; P40/P42 conservan
un seguimiento único. Los cambios visuales siguen asignados a GUI-DESIGN.

La plantilla de datos nuevos ya estaba corregida por GUI-DESIGN. El problema
restante era `{}` persistido por versiones anteriores. `ensure_data_layout()`
se invoca desde LANIP, mientras otras entradas acceden directamente al gestor:
corregir solo ese inicializador no cubría todos los consumidores. Se eligió el
lector compartido y se reutilizó el lock reentrante y la escritura atómica
existentes. Riesgo estimado de la intervención: **Alto**, por afectar al registro
de autorizaciones. No se requirieron dependencias nuevas ni una refactorización
estructural adicional durante la implementación.

### Cambio y efectos comprobados

`PluginManager._read_registry()` reconoce únicamente el objeto JSON vacío
histórico y lo sustituye por `{"schemaVersion": 1, "plugins": {}}`. La lectura y
migración comparten el lock de los escritores. Un documento ya versionado se
conserva sin reescritura; datos corruptos, tipos incorrectos y esquemas
desconocidos mantienen su rechazo. La migración no recupera permisos, confianza
de editor ni estado activo. Un fallo de escritura conserva el documento original
y el origen `LANCTL.Plugin.Registry.Load` con la excepción causante.

Archivos modificados en este ciclo:

- `src/lanctl/core/plugins/manager.py`: migración acotada en el lector privado.
- `tests/test_plugin_registry_migration.py`: 18 casos de regresión nuevos.
- `errorList.txt`: regenerado sobre el árbol actual, con 1.285 puntos.
- `docs/BACKLOG.md`: planificación, prioridades, dependencias y cierre de P44.
- `docs/BACKLOG-VERIFICATION.md`: este informe y sus límites.

`data_migration.py` se verificó sin volver a modificarlo. Los cambios previos de
GUI-DESIGN y los de P43 se conservaron; no se añadieron funcionalidades de GUI.

### Verificación

- Antes del cambio: **6 fallos y 12 aprobados** en las regresiones de P44.
- Después: **87 pruebas y 17 subpruebas aprobadas** entre migración del registro,
  revisión de seguridad de plugins, migración de datos y pruebas de plugins.
  Incluyen idempotencia, documentos inválidos intactos, error de disco con causa,
  espera del escritor concurrente, conservación de su autorización y ausencia
  de ejecución de un plugin `trusted` instalado sin permisos.
- Arranque LANIP con datos nuevos y antiguos en procesos aislados: API real de
  bootstrap, sustituyendo únicamente la creación de la ventana en esas pruebas.
- Smoke nativo Windows adicional con registro `{}` y datos/secretos temporales:
  puente real, crear proyecto, editar dispositivo, grupos, guardar, cambiar,
  restaurar y cerrar correctamente. No se modifican datos del usuario.
- Suite completa con navegador y GUI legacy: **1.073 pruebas y 643 subpruebas
  aprobadas; una prueba POSIX omitida en Windows**, en 130,95 segundos. Cobertura
  de ramas combinada: **68,0842 %**, superior al umbral del 60 %.
- Los hashes de **418 archivos** de fuentes, pruebas, herramientas, recursos y
  empaquetado coinciden antes/después de la suite: no hubo cambios concurrentes.
- Comparación AST con HEAD: se conservan las **37 firmas de funciones/métodos**
  del gestor; el resto del módulo es idéntico salvo el cuerpo de `_read_registry`.
  Por tanto se conservan registro de eventos y contratos públicos existentes.
  También coinciden los **51 IDs y orígenes de error** del gestor, salvo líneas.
- Ruff lint global, Bandit con el perfil de release, referencias CLI/web,
  catálogo, higiene y `git diff --check`: aprobados. Formato de los dos archivos
  Python de P44: aprobado.

Reproducción de la suite en PowerShell:

```powershell
$env:LANCTL_GUI_BROWSER_TESTS='1'
$env:COVERAGE_FILE='.tool-reports/p44/.coverage'
python -m coverage run --branch --source=src -m pytest -m 'legacy_gui or not legacy_gui' -q --tb=short --junitxml .tool-reports/p44/full-suite.xml
python -m coverage report --precision=4 --fail-under=60
```

Evidencia local: `.tool-reports/p44/full-suite.xml`, `full-suite.log`,
`coverage.xml`, `native-legacy.log`, `contracts.json`, `source-snapshot.json`,
`snapshot-check.json` y `format-check.json`. Son artefactos ignorados por Git.

### Dependencias y trabajo pendiente

**P44 queda completada en fuentes**, sustituyendo el estado parcial de la
sección anterior. Se pueden verificar P34/P32 con registros antiguos y queda
satisfecha la dependencia de arranque de P46/P47; sus otros requisitos siguen
vigentes. **La siguiente tarea es P34**, empezando por validar revocación entre
procesos, limpieza de consumidores, límites del runtime `trusted` y orden de
locks. No se implementó esa segunda tarea en este ciclo.

El formato global sigue pendiente en seis archivos de cambios anteriores:
`src/lanctl/apps/access/manager_cli.py`, `src/lanctl/bootstrap/lanmon.py`,
`src/lanctl/core/data_migration.py`, `tests/launcher_gui_native_smoke.py`,
`tests/test_suite_browser.py` y `tests/test_suite_gui.py`. Debe corregirse antes
de integrar; no se alteraron esos archivos al resolver P44.

Los instaladores ya existentes no incorporan esta migración; quedan su
reconstrucción y las comprobaciones externas de P32. Tampoco se cierra P40/P42:
la distribución de LCP oficiales firmados requiere la identidad y los paquetes
autorizados del editor. El resto de pendientes conserva su orden y responsable
en el backlog. No se cambió la versión del programa ni se publicó una entrega.

## LANWIRE P55–P63 y CPD LANRACK P64–P65 — 17/10/2026

Implementadas las correcciones en fuentes manteniendo grafito y lima. LANWIRE
separa Interior de racks y Vista general, con contenedores por rack/CPD, filtros,
contexto de extremos externos y agrupación desplegable de enlaces paralelos.
La distribución determinista usa fuerzas de conexiones y separación de tarjetas;
solo los conjuntos sin enlaces se ordenan en cuadrícula. También considera los
enlaces salientes al organizar los equipos dentro de cada rack. Los puertos se
distribuyen por medio, ocupación y posición del destino, conservando sus nombres.
Los cables usan coordenadas DOM de sus puertos, etiquetas con fondo y guías,
abrevian con poco zoom y permiten consultar nombre, medio y extremos completos.
Pulsar un puerto del lienzo selecciona el equipo; conectar sigue siendo una acción
explícita de su ventana de datos. El doble clic desde Lista conserva el acceso
para centrarlo en Topología.

LANRACK permite crear/editar CPD con nombre, descripción y ubicación, trasladar
racks y eliminar salas conservando los armarios sin asignación o en otra sala.
Incluye vistas de salas, lista y detalle de rack/equipo, búsqueda y filtro CPD.
La extensión aditiva `cpdOrganization` lleva `schemaVersion: 1` dentro del mismo
inventario IDF; `data.location.cpd` contiene la pertenencia única del rack.
No hay duplicación de inventarios ni cambio de identidad de equipos o cables.
Las bases anteriores se leen sin CPD y se extienden en la primera escritura.
Lectura coherente y escritura atómica usan el lock común del almacén; la revisión
del documento rechaza actualizaciones obsoletas. Corrupción o versiones
incompatibles se conservan y se notifican con su origen.

### Comprobaciones de esta entrega

- 22 pruebas dirigidas aprobadas con navegador Edge: servicios reales y dos
  ventanas sobre la misma base temporal; creación de CPD desde LANRACK visible
  en LANWIRE, traslado de racks, conservación de equipos/puertos/cables,
  eliminación con y sin traslado, nombres duplicados con IDs distintos,
  actualización obsoleta rechazada y documento inválido sin sobrescritura.
- Topología real con siete racks, ciclo y enlaces paralelos; prueba adicional
  con 24 racks, tres CPD y 25 cables. Se comprueban recuentos, agrupación de
  enlaces, salidas de filtros, ausencia de solapamientos, contención de racks,
  anclaje de puertos tras zoom, 48 puertos sin scroll interno y ausencia de
  errores JavaScript. Cabecera/pie y ancho comprobados también a 960×650.
- Arranque/cierre nativo de LANWIRE y LANRACK aprobados con puente real y datos
  temporales, también tras el cambio de versión a 0.3.4-alpha.1.
- Ruff y formato de los archivos Python de este cambio, sintaxis JavaScript,
  higiene, referencias CLI/web y catálogo de 1.300 puntos comprobados.

La primera suite completa se cruzó con un cambio concurrente de versión:
1.074 pruebas aprobadas y dos fallos por comparar el 0.3.3 ya cargado con procesos
0.3.4-alpha.1 y con su referencia nueva. No se alteró la versión para ocultarlos;
se regeneraron las referencias y se repitió la suite con el árbol actualizado.
La reconstrucción y sus resultados finales se consignan a continuación.

Evidencia local ignorada: `tmp/cpd-browser-last.log`, `tmp/cpd-full-current.log`,
`tmp/cpd-build-current.log`, `tmp/cpd-lanwire-general.png` y `tmp/cpd-lanrack.png`.
Los escenarios no escanean redes ni modifican inventarios del usuario. El trazado
busca legibilidad y no garantiza un óptimo matemático global. La agrupación física
sigue en `physicalDatabase`, compartida por las dos interfaces; no se añade una
copia del inventario dentro del VLF.

Resultado de la repetición con versión coherente: **1.076 pruebas y 643
subpruebas aprobadas; una prueba POSIX omitida en Windows**, en 143,84 segundos.
El escenario adicional de 24 racks se ejecutó después junto con las regresiones
dirigidas: **22 aprobadas**, en 43,54 segundos. No se cambió código de ejecución
después de esa comprobación. Las referencias y la higiene permanecen correctas.

La comprobación de versiones de los ejecutables detectó que el empaquetado
incremental había retenido bytecode 0.3.3 en LANIP, aunque los recursos gráficos
ya coincidían. Esa entrega se descartó y se reconstruyó con caché limpia y
carpeta de trabajo nueva; se exige comprobar recursos y versión de los seis
binarios antes de considerar válida la entrega.

Verificación dirigida final: **22 aprobadas en 32,00 segundos** después del
ajuste de conservación de contexto al cambiar el filtro CPD. La regresión
adicional de volver de un CPD a la vista global recuperando la cámara también
pasó (24 racks, 3,80 segundos). Registros: `tmp/cpd-browser-delivery.log` y
`tmp/cpd-navigation-final.log`. Se reconstruyen los recursos finales desde
`build/cpd-final-alpha`; no se usa el instalador incremental descartado.

Entrega final verificada: los seis ejecutables contienen el servicio CPD, los
recursos gráficos idénticos a las fuentes finales y la versión 0.3.4-alpha.1.
LANWIRE, LANRACK, LANACCESS y LANMON compilados abren y cierran correctamente,
con ventana, icono, coordinación IPC y recursos válidos. El instalador local
`dist/gui-current/LANCTL-0.3.4-alpha.1-gui-setup.exe` se generó correctamente
(135.025.921 bytes). Evidencia: `tmp/cpd-frozen-resources.log`,
`tmp/cpd-frozen-windows.log`, `tmp/cpd-build-delivery.log` y
`tmp/cpd-installer-final.log`. No se instaló ni publicó automáticamente.
P55–P65 quedan completadas para esta entrega; las certificaciones externas de
P32 y las tareas de plugins ajenas a este cambio mantienen su estado propio.

## P66: skins de equipos en LANRACK — 17/10/2026

Se añaden frentes SVG genéricos superpuestos a las unidades ocupadas: 30
plantillas y ajustes personalizados, RJ45/SFP, montaje rack o bandeja, servidores,
SAI, paneles, routers y tapas. El editor ofrece vista previa y guarda únicamente
`data.rackAppearance` (`schemaVersion: 1`). Los conectores dibujados sin registro
son representaciones; la apariencia no crea puertos ni altera cables. El modo
automático usa tipo y puertos reales, sin inventar telemetría del SAI. Las
preferencias de visibilidad y tamaño de U también tienen esquema local versionado.

Se comprueba que una skin 48 RJ45 + 4 SFP no cambia los 24 puertos originales del
equipo de prueba. Las alturas se validan contra los límites del rack y el espacio
ocupado; un servidor desde U5 de 2 U ocupa U5–U6. LANWIRE respeta esa ocupación al
trasladar equipos y reducir la altura del armario. Las filas libres y ocupadas
mantienen la misma altura por U; los frentes de varias U abarcan el espacio real.

Validación:

- Suite completa: **1.080 pruebas y 643 subpruebas aprobadas**, una prueba POSIX
  omitida en Windows, en 144,74 segundos.
- 25 pruebas dirigidas de skins, CPD y launchers aprobadas. Regresión gráfica
  final adicional: 3 aprobadas, incluyendo las 30 plantillas en vista previa,
  guardar y volver a leer desde LANWIRE, vista simple/gráfica, altura por U y
  tamaño ajustable con preferencias versionadas. Sin errores JavaScript.
- Guardado obsoleto, cantidades inválidas, altura fuera del armario y solapamiento
  rechazados, preservando el inventario anterior. Acceso de escritura restringido
  a LANRACK; se mantienen los servicios de inventario compartidos.
- Arranque y cierre nativo de LANRACK aprobados. Ruff/formato de Python, sintaxis
  JavaScript, higiene y catálogo de **1.310 puntos** comprobados.

Fuentes principales: `apps/rack/skins.py`, `rack/service.py`,
`suite/launcher_gui.py`, validación de ubicación en `wire/gui_service.py`,
`gui/rack-skins.js`, `gui/physical-gui.js`, HTML/CSS compartidos y
`tests/test_rack_skins.py`. No se modifican proyectos ni inventarios del usuario.
Evidencia local: `tmp/rack-skins-full.log`, `tmp/rack-skins-final-browser.log`,
`tmp/rack-skins-targeted.log`, `tmp/lanrack-skins.png` y logs de empaquetado.

Empaquetado final de P66: los seis ejecutables tienen versión 0.3.4-alpha.1,
servicio de skins incluido y recursos HTML/CSS/JS idénticos a las fuentes.
LANWIRE, LANRACK, LANACCESS y LANMON compilados abren y cierran correctamente
con ventana, icono e IPC. El instalador actualizado
`dist/gui-current/LANCTL-0.3.4-alpha.1-gui-setup.exe` se generó con éxito
(135.076.670 bytes), sin instalarlo ni publicarlo automáticamente. Evidencia:
`tmp/rack-skins-frozen-resources.log`, `tmp/rack-skins-frozen-windows.log`,
`tmp/rack-skins-build.log`, `tmp/rack-skins-root-ip.log` y
`tmp/rack-skins-installer.log`.

### Aclaración P66: puertos decorativos — 17/10/2026

Los puertos de las skins quedan explícitamente sin eventos de puntero, foco ni
acciones propias. No abren conexiones ni muestran respuestas individuales al
pasar el ratón. El acceso a los datos se conserva en la unidad completa del rack.
Las tres regresiones existentes de skins pasan con el cambio; no se añaden
pruebas que solo dupliquen las reglas CSS. No hay cambios de datos ni de contratos.
Las futuras ampliaciones mencionadas por el usuario quedan por concretar.

El ajuste decorativo queda también incluido en los seis ejecutables y en el
instalador local actualizado. Recursos finales comprobados contra las fuentes,
versión 0.3.4-alpha.1 y compilación del Setup correctas. Evidencia:
`tmp/rack-skins-passive-build.log`, `tmp/rack-skins-passive-resources.log` y
`tmp/rack-skins-passive-installer.log`. No se instaló automáticamente.

## Servicios, datos e instalación — AUDITOR, 17/10/2026

Se validaron dependencias antes de implementar y se comunicaron firmas y
payloads mediante `.tool-reports/gui-auditor-sync.json`. GUI-DESIGN conserva
los adaptadores y recursos visuales. AUDITOR no cambió rama ni versión
(`experimental-gui`, `0.3.4-alpha.1`), no publicó, no instaló y no ejecutó builds
ni la suite completa mientras la integración visual estaba en curso.

### Cambios y archivos

- **P54:** `core/official_links.py`, `bootstrap/lanctl.py`, Lua y referencias
  generadas. Opciones `-web/-github/-reference` y alias largos; URL completa
  legible en terminal y salida redirigida; únicamente destinos oficiales.
- **P35:** `core/gui_preferences.py`, `config.py`, `settings_catalog.py` y
  función aditiva `active_theme_extensions` en `plugins/manager.py`. Presets
  graphite/midnight/forest/violet/light; density, fontScale y reducedMotion.
  La configuración canónica v2 guarda un bloque `gui` de esquema 1. Un plugin
  de tema explícito añade solo sus tokens/componentes declarados; se informa
  `effectivePlugin`, `pluginTokens` y `pluginComponents`. La paleta incluida
  `lanctl.theme.default.palette` es base sustituible por el preset, pues
  aplicarla como overlay anulaba las cinco elecciones. No se modifican las
  preferencias guardadas al aplicar un plugin. Se corrigió el error de catálogo
  `'gui' is not in list` registrando la categoría y el mismo validador.
- **P49:** `apps/monitor/log_tui.py`, `log_stream.py`, `bootstrap/lanmon.py`.
  `lanmon logs --tui` y `open_log_window(tui=True)` usan el mismo lector
  incremental. Pausa de vista sin perder el seguimiento, historial acotado,
  navegación, filtro de texto y nivel. Lotes de hasta 1.000 líneas dejan los
  bytes restantes en disco para la siguiente consulta; se conserva UTF-8
  parcial, rotación y el seguimiento de texto existente.
- **P53:** `core/activity.py`. Almacén SQLite versionado, máximo 10.000
  mensajes por propietario, validación del emisor contra la sesión viva y
  filtros explícitos. `project=None` consulta todos los proyectos del usuario;
  `project=''` solo mensajes sin proyecto. `latest=True` entrega los últimos
  registros en orden ascendente; `after` permite seguimiento incremental.
  Las filas sobreviven al cierre del emisor. No se relaja el canal de
  coordinación de metadatos ni se reutilizan sus IDs públicos.
- **P52:** `core/diagnostics.py`, `apps/monitor/bug_reports.py`. Preparación
  pura con evidencia seleccionada, límites, origen/código/versiones y errores
  repetidos agrupados. Se filtran credenciales incluso al desactivar la
  anonimización de identidad; esta última oculta rutas, IP, MAC y correos.
  Exportación Markdown y URL de formulario, con nueva redacción tras editar
  el borrador. Sin inventario completo ni publicación automática. La revisión
  humana sigue siendo necesaria para datos privados no reconocibles por sus
  claves o patrones; no se afirma una anonimización universal.
- **P51:** `core/updates.py`. Comparación SemVer y filtro por `draft=false`,
  `prerelease=false` y publicación efectiva, incluso con sufijos históricos.
  Se consulta un máximo acotado de páginas del repositorio oficial; reserva
  diaria persistente antes de red, también en fallos o consultas simultáneas.
  Recordatorio por versión y validación de enlaces incluso al leer caché.
  El adaptador GUI debe usar worker. Se contrastaron los campos y paginación
  con [GitHub REST](https://docs.github.com/en/rest/releases/releases#list-releases)
  y la comparación con [SemVer](https://semver.org/). No se descarga ni instala.
- **P66 «Dimensiones»:** `core/rack_dimensions.py`, `apps/rack/service.py`,
  `apps/rack/cli.py`, `apps/wire/gui_service.py`, `apps/wire/idf/database.py`
  y `apps/wire/models/rack.py`. Enteros 4–52 U y anchos 10/19/21/23. Altura
  canónica `data.units`, ancho en `data.rackDimensions` esquema 1. Las bases
  antiguas conservan valores inválidos o desconocidos con advertencias; solo
  una edición explícita los corrige, manteniendo alias heredados coherentes.
  La transacción compartida impide reducir por debajo de los equipos y sus
  frentes de varias U. LANRACK añade `dimensions ID --units U --width-inches W`.
- **P45/P46:** `core/installation.py`, `plugins/selection.py`, `builtin.py` y
  `packaging/inno/LANCTL.iss`. `setup-defaults` guarda una vez la elección de
  tema/plugins; una actualización conserva selección, configuración y registro
  de permisos. Los plugins omitidos no reaparecen por bootstrap; el tema base
  sigue obligatorio. El ejemplo incluido ya no reescribe manifiestos idénticos
  en cada inicio. El instalador ofrece selección individual y cinco previews;
  su compilación/certificación corresponde a la fase de integración.
- **P47, alcance seguro:** `core/first_scan.py`, entrada CLI LANIP, orquestador
  e instalador. `post-install [--first-scan]` exige usuario normal, deja una
  petición de confirmación antes de abrir LANIP y nunca inicia sondas. La
  petición caduca tras 24 horas y se consume una vez. `scan_choices` no inventa
  interfaces ni máscaras; el escáner usa las rutas del sistema. Falta enlazar
  realmente una interfaz a todas las sondas: REF-P47-interface.
- **P48:** `core/clink_integration.py`, `packaging/clink/*`, instalador,
  `packaging/portable/prepare.ps1`, README y `scripts/build-windows.ps1`.
  Distribución del Lua y registro/retirada de una carpeta mediante argumentos
  nativos. Instalación de registro con usuario normal; desinstalación elevada
  solo busca binarios en Program Files consultado en HKLM, sin usar PATH de
  usuario. Se conserva marcador por usuario/directorio. Clink registra rutas
  en el perfil del usuario según su [documentación](https://chrisant996.github.io/clink/clink.html#command-line-options).
  Inno no recupera siempre la identidad original y no admite ExecAsOriginalUser
  al desinstalar, según [su contrato](https://jrsoftware.org/ishelp/topic_isxfunc_execasoriginaluser.htm).
  Por ello otra cuenta administrativa no se presenta como limpieza completa
  del registro del propietario; se documenta retirada manual previa.

### Verificación de AUDITOR

Resultado consolidado de 23 módulos de pruebas relacionados: **281 pruebas y
11 subpruebas aprobadas en 36,91 s**. Incluye regresiones de los diez archivos
nuevos `test_official_links`, `test_gui_preferences`, `test_activity`,
`test_log_tui`, `test_diagnostics`, `test_updates`, `test_rack_dimensions`,
`test_installation_preferences`, `test_first_scan`, `test_clink_integration`,
además de plugins, permisos/firmas, migración, configuración, coordinación,
IDF/modelos, launchers, distribución, Clink y errores existentes.

Después de ajustar la fixture sintética de redacción para respetar la higiene
y cubrir la paleta base que anulaba presets: **20 pruebas adicionales pasan**
(preferencias/diagnósticos). No se modificó el detector de secretos.

Evidencia local no versionada:
`.tool-reports/auditor-20261017/focused.log`, `focused.xml` y `contracts.json`.
La prueba de actividad ejecuta un proceso Python separado, escribe con una
sesión real, la cierra y comprueba recepción y conservación desde el padre.
Las pruebas de actualizaciones no consultan la red y las de Clink no alteran
el registro real del equipo.

- Ruff global `check src tests`: correcto; formato de los 35 archivos Python
  propios revisados: correcto.
- Bandit `-q -r src -ll`: sin hallazgos de nivel exigido; conserva dos avisos
  previos de `nosec B104` sin incidencia coincidente.
- Referencias CLI/web actualizadas y comprobadas; catálogo de errores
  regenerado y comprobado (**1.388 puntos** al cierre de AUDITOR).
- Higiene correcta y `git diff --check` sin errores; Git solo advierte sobre
  normalización CRLF/LF de archivos compartidos.
- Comparación AST contra HEAD: **29 métodos existentes de PluginManager
  idénticos**, además de preservar los archivos públicos de contratos,
  eventos y funciones. Se añadieron interfaces/keywords compatibles; las
  nuevas restricciones de dimensiones responden expresamente al requisito.

### Dependencias abiertas y siguiente paso

**Fuentes de AUDITOR listas para integración**; GUI-DESIGN ejecuta la suite
completa con cobertura, pruebas visuales/nativas, recursos y un único build.
No se atribuyen aquí resultados finales que aún no hayan terminado.

P34 requiere REF-P34-runtime: el host no puede detener de forma segura hilos
arbitrarios de un plugin trusted ya cargado en su propio proceso. El diseño
previo a implementarlo debe introducir runtime cancelable propiedad del host,
RPC versionado, concesiones por revisión, validación antes de cada operación,
retirada de callbacks y cierre con plazo, sin mantener locks durante callbacks
externos. Implica cambios de arquitectura y compatibilidad, no una notificación
de GUI. P34 permanece crítica y abierta.

P50 depende además de un contrato de snapshot vivo: enumeración por propietario,
selección explícita de sesión/proyecto, revisión solicitada/observada, estado
guardado frente a cambios en memoria y errores de sesión caducada o revisión
desfasada. El coordinador actual no ofrece ese snapshot y el VLF no lo sustituye.
El transporte/autenticación externos deben verificarse antes de exponerlo. El
preparador de P52 queda reutilizable sin introducir GitHub en ese futuro puente.

P40/P42 requieren firmas e identidad reales autorizadas. P47 no certifica
selección de interfaz hasta REF-P47-interface. P48 requiere CMD/Clink real y
resolver/probar los escenarios de usuario administrador distinto. P32 conserva
la matriz externa Windows limpio/Linux ARM64/SSH. Estos puntos no se marcan
completados ni se rebaja su prioridad.
## Integración coordinada de pendientes GUI — 17/10/2026

GUI-DESIGN implementa la presentación y los adaptadores de escritorio; AUDITOR
entrega servicios, modelos, CLI/TUI e instalador. El reparto y las dependencias
se registran en `docs/GUI-AUDITOR-COORDINATION.md`.

- P35: cinco temas, vista previa/cancelación, persistencia, sincronización entre
  ventanas, densidad, escala de texto y reducción de animaciones. Los overrides
  de plugins conservan el tema base y se retiran sus estilos de componente.
- P49/P53: botón Registros en LANIP para la TUI, actividad y registros en LANMON
  con pausa, filtros y límites. Transporte con sesión/proyecto/origen reales;
  se conserva el buffer local hasta transmitir y el historial tras cerrar la
  sesión. Reloj retirado solo del pie de LANCTL.
- P51/P54: consulta de actualizaciones fuera del hilo de interfaz, revisión
  manual, versión/novedades, recordar después y navegador explícito. Web,
  GitHub y Referencia comparten destinos con los comandos CLI/TUI.
- P52: Report a bug en las seis ventanas nativas; errores agrupados con
  origen/código/ID; borrador en LANMON con sesión, selección de evidencias,
  campos editables, anonimización y vista previa antes de abrir GitHub o
  exportar Markdown. No se publican incidencias automáticamente.
- P66 «Dimensiones»: creación y edición en LANRACK, lectura en LANWIRE desde
  el mismo inventario. Altura estricta 4–52 U y ancho 10/19/21/23 pulgadas;
  advertencias sobre datos heredados sin normalizarlos a escondidas. Las skins
  y sus puertos decorativos se conservan.
- P47: confirmación de interfaz IPv4, CIDR con máscara real y perfil antes de
  sondear. Se valida el origen con el Core y se comunica el alcance ICMP/ARP;
  DNS y descubridores externos se omiten con aviso. Sin interfaces o tras un
  error de escaneo, la solicitud sigue pendiente y permite reintentar. El
  selector habitual también permite recuperar las rutas del sistema.

Verificación de fuentes: trece regresiones nuevas con servicios reales y
navegador Edge aprobadas en 18,25 s tras las últimas correcciones; además pasan
las regresiones combinadas de interfaces, topología/CPD y skins
aprobadas. También pasan el arranque/cierre nativo de LANIP y de los cuatro
launchers y la coordinación nativa de los cuatro botones de LANCTL.

La suite integral y el paquete final se registran al concluir esta integración.
Estas pruebas no certifican P34, P40/P42, P50, los transportes restantes de P47 ni
P32 en plataformas externas. Esos pendientes mantienen su estado explícito.

### Correcciones tras la primera suite integral — AUDITOR

La primera ejecución integral de GUI-DESIGN terminó con 1.166 pruebas y 644
subpruebas aprobadas, un caso omitido y seis fallos. Tres pertenecían a la
interfaz y los corrige GUI-DESIGN; los tres no visuales quedan resueltos:

- La plantilla RK-00 ahora declara las mismas dimensiones que persiste la
  creación (18 U, 19 pulgadas). `sample_topology.py` conserva la idempotencia
  con muestras antiguas sin añadir dimensiones a sus datos; sigue rechazando
  modificaciones reales. Pruebas de repetición, conservación y conflicto.
- `settings_catalog.py` añade GUI al final de las categorías para conservar
  la numeración previa: la opción 8 sigue siendo LANIP. La prueba original de
  navegación pasa sin cambiar su secuencia.
- La prueba de expansión de variables usa un directorio personalizado y ya
  no lo confunde con el valor histórico que Windows redirige a Documentos.
  `test_project_paths.py` cubre también la falta de Known Folder; el código de
  producción y el contrato de redirección permanecen iguales.

Además, `event_view.py` reconoce `GUI_ACTIVITY` esquema 1 emitido por la GUI
con nivel entero 1–59, manteniendo el mensaje y su origen. Los éxitos no se
convierten en ErrorEvent. La regresión escribe mediante el logger real y
comprueba lectura incremental, filtrado TUI e histórico; un marcador incluido
en el texto del mensaje no sustituye al marcador externo. Los datos malformados
siguen visibles, sin asignarles un nivel inventado.

Evaluación de impacto: medio para la comparación de muestras y navegación,
bajo para el lector y aislamiento de pruebas. No se cambian IDs públicos,
firmas de métodos ni rutas de producción. Verificación enfocada ampliada:
**147 pruebas aprobadas en 14,95 s**, incluyendo TUI física, dimensiones,
configuración, rutas y seguimiento de registros. Evidencia local:
`.tool-reports/auditor-20261017/integration-followup.xml`.
Ruff, referencias CLI/web e higiene correctos; catálogo regenerado y comprobado
con **1.390 puntos**. Fuentes no visuales congeladas de nuevo para repetir la
suite integral y el build bajo responsabilidad de GUI-DESIGN.

## Segundo ciclo AUDITOR — 17/10/2026

Validación y orden: primero el acceso de plugins al Core y la limpieza de runtimes
(P34, riesgo crítico); después origen del primer escaneo (P47, alto); herramientas
de desarrollo P67/P68 cuando las fuentes estén congeladas. GUI-DESIGN conserva
la propiedad de las vistas y sus adaptadores. Se mantienen IDs y versión
0.3.4-alpha.1; no se fusionan PR ni se publican ramas o instaladores.

### P34: revocación de accesos y ciclo de limpieza

Cambios en `core/plugins/authorization.py`, `manager.py`, `api.py` y
`core/plugin_storage.py`. Cada activación recibe una concesión distinta. Las
operaciones del API comprueban la autoridad persistida y el editor; referencias
antiguas de funciones, eventos, monitor y almacenes dejan de autorizar llamadas.
Los callbacks comprueban además la concesión al retornar. Un observador del
gestor global reconcilia cambios cada 0,5 s; las llamadas no esperan ese sondeo.
La corrupción de la autoridad retira accesos y conserva el archivo averiado.

Se retiran también los checks del monitor, los consumidores dependientes y los
runtimes aislados que han terminado. La limpieza externa se reserva bajo lock,
pero se ejecuta después de liberarlo y se espera como máximo 0,5 s por plugin.
Una limpieza pendiente impide activar la generación siguiente. `reload` espera
esa fase antes de reactivar. El método aditivo `runtime_status(id)` devuelve
esquema 1, `active`, `coreAccess`, `restartRequired`, `cleanupPending` y `execution`.

Pruebas: las tres regresiones principales fallaban antes del cambio. Las dieciséis
nuevas incluyen un segundo proceso, revocación de editor, referencias retenidas,
llamada en curso, limpieza colgada, carrera antes de arrancar la limpieza,
dependencias transitivas y terminación de un proceso aislado. El conjunto
ampliado de plugins pasó 119 pruebas en 42,56 s sobre las fuentes aplicadas.
Se añade un lock de inicialización global: ocho accesos simultáneos crean un
solo gestor y un solo observador (regresión específica aprobada).
La comparación AST conserva las firmas de 13 métodos públicos del gestor y
30 del API. Los contratos de eventos y funciones no se modifican.

Límite explícito: un plugin `trusted` ya cargado puede haber creado hilos y
efectos nativos fuera del API; no se garantiza su terminación ni se deshacen
efectos anteriores o de operaciones ya iniciadas. `restartRequired` persiste
durante la vida del gestor. P34/REF-P34-runtime siguen abiertos hasta disponer
del host de ejecución cancelable y RPC versionado, conservando el runtime
heredado como compatibilidad explícita. No se presenta esta mitigación como
aislamiento del SO.

### P47: inventario de interfaces y sondeo con origen

Cambios en `core/network_interfaces.py`, `core/first_scan.py`, servicios
`lan_scanner.py`/`source_binding.py` y comando CLI `list.py`. La enumeración es
local, con máscara real; Windows incluye interfaces virtuales conectadas y
Linux consume `ip -j`. Se valida índice, dirección, prefijo y selección única.
El origen se vuelve a comprobar antes del escaneo: una interfaz desaparecida,
una dirección repetida o un CIDR ajeno no provocan fallback a otra ruta.

`list --interface ID_O_IPV4` conserva las invocaciones anteriores. Sin un
`--network` explícito usa la máscara de la interfaz; con rango explícito exige
que pertenezca a ella. Rechaza su combinación con un laboratorio activo.
Windows usa IcmpSendEcho2Ex y SendARP con dirección de origen; Linux pasa
interfaz y dirección a ping/arping. La caché ARP se consulta por interfaz.
Los límites de hosts siguen vigentes antes de sondear.

La modalidad seleccionada es ICMP/ARP: DNS y descubridores externos se omiten
con aviso porque todavía carecen del contrato de origen. No se afirma que
TCP, mDNS, SSDP, WSD o plugins estén vinculados. REF-P47-interface conserva ese
alcance restante y la certificación nativa con varias NIC/Linux. Enumeración
Windows real comprobada sin tráfico; conjunto de 132 pruebas y 10 subpruebas
aprobado en 3,18 s. Dieciséis regresiones nuevas cubren
validación, comandos/llamadas nativas, ausencia de fallback y confirmación.

Fuentes técnicas consultadas:
[Get-NetIPConfiguration](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netipconfiguration),
[IcmpSendEcho2Ex](https://learn.microsoft.com/en-us/windows/win32/api/icmpapi/nf-icmpapi-icmpsendecho2ex),
[SendARP](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-sendarp),
[implementación de ping de iputils](https://github.com/iputils/iputils/blob/master/ping/ping.c).

### Bloqueos y prioridades restantes

P40/P42: el usuario confirma que aún no existe editor oficial configurado.
Faltan identidad autorizada y artefactos LCP firmados; no se crea una identidad
oficial ficticia ni se desactiva la verificación. Las claves generadas por las
pruebas son efímeras y solo se usan en directorios temporales.

P50: el coordinador actual comparte metadatos y avisos, no un snapshot coherente
del estado de trabajo. `_SESSION_DEVICES` vive dentro de cada proceso; leer el
VLF desde un servidor externo perdería esos datos y cambios sin guardar.
Se antepone REF-P50-session: proveedor de snapshot del proceso propietario,
revisión, sesión/proyecto explícitos, caducidad/cierre y lista permitida de datos
sin credenciales. Impacto alto sobre sesión/inventario; no añadir transporte
externo que finja un estado vivo antes de ese contrato y REF-P34-runtime.

La documentación oficial confirma transportes STDIO y Streamable HTTP para
Codex; ChatGPT web no toma la configuración local de Codex. Para el transporte
remoto autenticado se requiere identidad de usuario y validación de permisos
por petición. No hay conexión externa certificada ni proveedor de identidad
del proyecto definido. Referencias:
[MCP y clientes](https://learn.chatgpt.com/docs/extend/mcp?surface=cli),
[autenticación de servidores MCP](https://developers.openai.com/plugins/build/auth).

P48 conserva la verificación real de Clink en CMD y el caso de desinstalación
con otra identidad. P32 conserva Windows limpio, Linux ARM64 y SSH remoto.
Las pruebas locales de fuentes no sustituyen esas certificaciones.

## Estabilización con evidencia de GitHub — 17/10/2026

Validación previa: se revisaron los workflows y los jobs/logs reales de las
últimas ejecuciones fallidas y correctas. Objetivo: corregir causas vigentes,
separar fallos de fixtures de fallos del producto y conservar los contratos.

| Trabajo | Archivos / dependencias | Riesgo e impacto | Resultado |
| --- | --- | --- | --- |
| Dependencias GUI ausentes en CI | `.github/workflows/ci.yml`, `tests/test_distribution.py`; extra `gui` ya usado por Release | Medio; evita que pruebas de confianza fallen por `webview` ausente | CI instala `dev,gui`; regresión de distribución pasa |
| Diagnóstico y plataforma | CI/Release; JUnit/logs y job Windows 3.10/3.11 | Medio; evidencia descargable tras un fallo, sin bajar cobertura Linux del 60 % | Definiciones preparadas; ejecución nueva remota pendiente de integración |
| Cabeceras HTTP | `apps/access/https_server.py`, `tests/test_http_session_headers.py` | Alto; impide valores de cookie/cabecera inyectados por adaptadores o MIME del sistema | Seis IDs malformados rechazados por HTTPS real; tres recursos conservan MIME seguro |
| Pruebas SSH | `tests/test_access.py`; claves Ed25519 efímeras del servidor de prueba | Medio; cliente rechaza servidores con una clave distinta | Dos `AutoAddPolicy` retiradas; pruebas de acceso pasan |
| Salidas de metadatos | `tests/test_lanaccess_manager.py`, `tests/test_hygiene_output.py` | Alto por sensibilidad del almacén; no cambia el contrato de salida | List/show/doctor/settings/protocol y diagnóstico TUI no imprimen contraseña; higiene no imprime el token detectado |
| Fuga real en alta de usuario remoto | `apps/ip/interfaces/cli/commands/access.py`, `tests/test_access_cli_output.py` | Alto; el `asdict` anterior imprimía `passwordHash` en stdout | Proyección explícita conserva metadatos y clave/tipo `passwordHash`, ahora vacía; `passwordConfigured` es aditivo. Pruebas con contraseña y SSH, autenticación persistida y campo privado futuro |
| Canal estable | `.github/workflows/release.yml`, regresión de distribución | Medio; el nombre «experimental» y `make_latest:false` eran incondicionales | Solo el canal experimental conserva esa etiqueta; estable tiene nombre propio y puede ser última versión |
| Herramientas P67/P68 | `pyproject.toml`; Python 3.10.11, Coverage 7.10.6/7.16.2, Ruff 0.17.0 | Medio; comparación sobre fuentes idénticas, sin relajar reglas | Ambas suites: 1.208 pruebas y 645 subpruebas correctas; cobertura idéntica 69,3568 %, umbral 60 % |

La comparación completa termina en 182,07 s con Coverage 7.10.6 y 189,55 s con
7.16.2. Ambas registran 19.740 líneas cubiertas de 27.055 y 5.243 ramas cubiertas
de 8.966, sin diferencias de cómputo. Un caso de framing IPC POSIX se omite en
Windows y 21 pruebas `legacy_gui` se excluyen según la configuración existente.
Se adopta Coverage 7.16.2; Ruff 0.17.0 comprueba 483 archivos. El entorno no
presenta dependencias rotas. Los XML JUnit, JSON de cobertura y huellas de fuentes
se conservan localmente en `.tool-reports/tool-upgrades/`.

El nuevo job Windows activa también `LANCTL_GUI_BROWSER_TESTS=1`, instala
Playwright 1.63.0 (la misma versión verificada localmente, compatible con Python
3.10) y usa Microsoft Edge incluido en la
[imagen oficial Windows 2022](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md).
Así esas regresiones no quedan omitidas en todas las plataformas de CI.

Se reprodujo el comportamiento anterior de cookies en el nuevo caso de prueba:
respondía 200 ante un identificador con CRLF; con el validador responde 400 y no
emite la cabecera inyectada ni la cookie. El contrato normal usa UUID y sigue
funcionando. La API pública de HTTPS y los IDs de eventos no se modifican.
Regresiones enfocadas: 59 pruebas de acceso/distribución/credenciales y otras
9 de salidas/higiene pasan. `pip-audit . --strict`: ninguna vulnerabilidad conocida.

### Resultados remotos comprobados

- [Release 39052546460](https://github.com/CctrGy/LANCTL/actions/runs/39052546460):
  éxito de validación, Windows y Linux amd64/arm64 sobre `4ca563d`.
  Los fallos anteriores de dependencia GUI, fixture de plataforma, arranque
  frío y comprobación de permisos del sentinel ya tienen una ejecución posterior
  correcta. No equivale a validar el candidato local posterior.
- [Seguridad PR 25](https://github.com/CctrGy/LANCTL/actions/runs/38596122454) y
  [seguridad PR 23](https://github.com/CctrGy/LANCTL/actions/runs/37421942821):
  fallaban repetidamente porque **Dependency graph estaba Off**. Se activó en
  el repositorio público y se relanzaron los jobs fallidos desde la sesión del
  propietario. Ambos intentos 2 finalizan correctamente. No se cambió el umbral
  `moderate`, no se deshabilitó el control ni se fusionaron las PR.
- Documentación contrastada:
  [revisión de dependencias de GitHub](https://docs.github.com/en/code-security/getting-started/quickstart-for-securing-your-repository)
  y [acción oficial](https://github.com/actions/dependency-review-action).

### Avisos CodeQL y límites de la comprobación

Se inventariaron los 13 avisos abiertos de `main`: 6/7/8/10/12/14/15/16/17/18
de salida de datos, 5/13 sobre `AutoAddPolicy` en pruebas y 9 sobre
`Content-Type`. El flujo completo de #18 identifica `secret_root()` como
origen sensible y termina mostrando **la ruta**, sin leer el secreto: falso
positivo comprobado. #7/#8/#15 muestran rutas; #14 muestra nombre de archivo y
clase del hallazgo, probado sin volcar el valor. Los listados del almacén usan
proyecciones explícitas de metadatos, verificadas con contraseñas centinela.

#9 deja de depender de MIME obtenido del sistema; 5/13 ahora usan host keys
conocidas. La revisión de las ramas del comando `access` detectó una
fuga real: `user add` serializaba el hash de contraseña. La regresión reproduce
el fallo anterior y verifica la proyección segura. El código de emparejamiento
solo se emite bajo su petición explícita.

Se creó la [PR 26 en borrador](https://github.com/CctrGy/LANCTL/pull/26), desde
`codex/stable-readiness-20261017`, con copia aislada y comprobada de las fuentes;
`main`, `experimental-gui`, tags y ramas estables no se modificaron. El
[análisis de seguridad del candidato](https://github.com/CctrGy/LANCTL/actions/runs/39068885618)
completa dependency-review y CodeQL correctamente. Se inspeccionaron los SARIF
de `main` (1952995019) y de la PR (1973832502): en el candidato figura #6 con
origen `user.passwordRotatedAt`, una fecha opcional de metadatos. El hash real
ya no sale; el JSON conserva su clave como string vacío. No se cambia el
contrato de fechas ni se renombra código para esquivar el analizador.

El SARIF histórico confirma que #10/#12/#16/#17 siguen IDs públicos y campos
de metadatos desde el documento descifrado, no `password`; #14 sigue las
etiquetas de patrones del detector, no los tokens encontrados; #6/#7/#8/#15/#18
seguían rutas devueltas por `secret_root`. Las regresiones con secretos centinela
comprueban la separación. No se han descartado alertas remotamente: los 13 de
`main` conservan el estado correspondiente a su propio código hasta integración.

### Verificación final local y primer CI del candidato

Con Coverage 7.16.2 y navegador Edge: **1.212 pruebas, 645 subpruebas correctas**
en 185,61 s, una omisión POSIX en Windows y 21 heredadas excluidas por defecto.
Estas últimas se ejecutaron también explícitamente: **21/21 correctas** en
1,82 s. Total: **1.233 pruebas correctas**. Cobertura 69,4720 %, umbral 60 %.
Ruff/formato (484 archivos), catálogo (1.420 puntos), referencias e higiene
correctos. No cambian los archivos de contratos/IDs Core ni las firmas públicas
revisadas de acceso y HTTPS frente a `main` (`ccd728b`).

El primer [CI remoto](https://github.com/CctrGy/LANCTL/actions/runs/39068885619)
detectó un fallo de fixture exclusivo de Linux: la prueba simulaba Windows sin
proporcionar `subprocess.CREATE_NO_WINDOW`. Se corrige únicamente
`tests/test_network_interfaces.py`, manteniendo la implementación nativa. Sus
16 pruebas pasan también al eliminar esa constante del módulo local antes de
ejecutarlas; ahora se comprueba el flag Windows y el cero Linux. No requiere
recompilar los binarios. La validación remota posterior queda registrada al
terminar; no se equipara el resultado local a un CI Linux correcto.

El supuesto bloqueo de cierre LANIP fue un fallo del harness: usaba proyectos
reales y pipes sin consumir. GUI-DESIGN comprobó cierre nativo y código de salida
0 con directorio temporal y salida a archivo; no necesitó cambiar la aplicación
por esa observación. P34/P47 están integrándose con sus avisos y selector real.
