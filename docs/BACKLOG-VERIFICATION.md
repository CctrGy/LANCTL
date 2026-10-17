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
