# Comprobación del backlog

## P69 — separación de preferencias por interfaz y launcher (22/10/2026)

Validación y planificación antes de implementar:

- Dependencias resueltas: REF-P69-settings (validación y autorización atómica)
  y REF-P69-remote-lifecycle (recuperación de backend). Se conservan ambas.
- Objetivo: una lista explícita de preferencias de usuario, filtrada por
  interfaz y launcher tanto al consultar como al guardar. Ocultar datos internos
  y campos automáticos sin eliminarlos de la configuración persistente.
- Módulos/archivos: `core/settings_policy.py`, catálogo declarativo compartido,
  `apps/suite/settings.py`, adaptadores CLI/TUI de settings y filtro técnico del
  formulario `apps/ip/interfaces/gui/desktop.py`; pruebas de regresión y docs.
- Riesgo alto: bloquear por error opciones CLI históricas, perder preferencias
  ocultas o permitir escribir desde un adaptador con un ámbito falso. Las opciones
  explícitas `--tui-*`/`--close-gui-on-launch` conservan su finalidad administrativa
  local; el catálogo genérico y las llamadas remotas no reciben esa excepción.
- Impacto: listas de preferencias más limitadas; mismos formatos, firmas públicas,
  permisos, transacciones y proyecto compartido. El contexto lo fija el adaptador.
  Sin cambios en `gui/*`, estilos, composición visual, localStorage ni temas de
  GUI-DESIGN. Adaptadores GUI: solamente filtrado de campos con la política común.
- Verificación prevista: matriz GUI/TUI/CLI y launchers, guardado atómico y rechazo
  directo, compatibilidad CLI, proyecto compartido, autorización remota, conservación
  de valores ocultos; suite completa aislada, contratos, referencias y controles CI.

Implementación y efectos revisados:

- `core/settings_policy.py`: registro explícito por interfaz y dominio de launcher;
  una nueva clave del esquema no se convierte automáticamente en preferencia.
  `preference_visible` y `restriction` comparten la misma regla; el guardado sigue
  validando el lote completo y conserva los permisos administrativos del backend.
- `apps/suite/settings.py`: filtra programa y proyecto, incluidos objetos agregados
  de acceso remoto para no divulgar campos desconocidos futuros. Mantiene los valores
  ocultos, los snapshots de proyecto y las transacciones. La conversión de formulario
  comparte nombres canónicos y admite las columnas CLI/TUI separadas por comas.
- Adaptadores CLI/TUI: el catálogo y las consultas se limitan a preferencias propias
  y comunes; las opciones locales explícitas mantienen la administración compatible
  de TUI/GUI. Las llamadas remotas rechazan estas rutas y las administrativas incluso
  cuando el valor solicitado ya coincide: no pueden entrar en la transacción remota
  como un supuesto lote vacío. La consola integrada conserva su contexto CLI.
- `desktop.py` y la inicialización de su adaptador privado en `suite/gui.py`:
  contexto GUI/launcher fijado en servidor y filtrado de campos. No cambian firmas
  ni envoltorios RPC. Se excluye `cliCommandChaining`; solo el formulario de LANCTL
  ofrece `closeGuiOnLaunch`. Los recursos visuales y localStorage no se modifican.
- `apps/wire/tui/settings.py`: mantiene su archivo propio; valida claves, tipos,
  límites y columnas antes del guardado bajo lock, conservando anchuras no enviadas.
  No incorpora preferencias LANIP ni escribe la configuración general.
- `tests/test_interface_preferences.py` y ajustes de expectativas antiguas en
  `test_settings_policy.py`, `test_settings_catalog.py` y `test_suite_gui.py`: el catálogo ya no muestra
  IDs/rutas internos y el menú prueba la categoría por nombre, no por posición.
  El catálogo de esquema de bajo nivel y `set_program_value` conservan su API;
  el filtrado corresponde a los adaptadores de preferencias de usuario.

Resultado focalizado: **272 pruebas y 379 subpruebas correctas** (19,32 s).
Incluye los servicios de autorización anteriores y ambos TUI. La primera integral
registró 1.690 aprobadas y un fallo de expectativa en `test_suite_gui.py`: exigía
exponer todo el esquema en la GUI, incluidas rutas internas y opciones TUI. Se
sustituye por comprobaciones de preferencias GUI/comunes y rechazo de escritura
de campos ajenos, conservando la validación existente. Esa regresión pasa por
separado. No se cambia código de producción tras la primera integral; se vuelve
a congelar y ejecutar la suite completa con la expectativa corregida. Evidencia
del intento anterior: `.tool-reports/p69-interface-complete.log` y `.xml`.

**Resultado final local — P69 completada en fuentes:** **1.691 pruebas y 1.008
subpruebas aprobadas, una omisión POSIX en Windows, cero fallos**, en **463,94 s**.
Incluye las 56 regresiones nuevas, 360 subcasos de matriz, `legacy_gui` y navegador
Edge real. Cobertura combinada **72,4941 %**, líneas **75,9751 %**, ramas
**62,0901 %**; umbral del proyecto 60 %. El XML cuenta también las subpruebas
como casos: 2.700 entradas, de las cuales una corresponde a la omisión.

Las fuentes y pruebas permanecen idénticas al corte final congelado. **1.243 firmas
públicas previas idénticas**, dos funciones aditivas; ningún ID ni formato persistente
modificado. Opciones CLI, permisos y envoltorios RPC conservados. Los recursos
`gui/*` y el archivo real de configuración local permanecen idénticos por hash.
Ruff, formato (528 archivos), Bandit según CI, pip check/pip-audit, referencias,
catálogo de 1.623 puntos, higiene y `git diff --check` correctos.

Evidencia local: `.tool-reports/p69-interface-final.log`, `p69-interface-final.xml`,
`p69-interface-final.coverage`, `p69-interface-coverage.json`,
`p69-interface-contracts.json`, `p69-interface-final-frozen.json` y
`p69-interface-verification.json`. Se actualiza también el contrato de coordinación
`gui-auditor-sync.json`. Rama `codex/p69-interface-preferences`, versión
`0.3.4-alpha.1`, sin commit, publicación, instalación ni compilación nueva.

Dependencias: P71 puede reutilizar la política de preferencias junto con el ciclo
remoto ya resuelto; sus páginas siguen pendientes. Siguiente prioridad:
**REF-P34-migration** (adopción del runtime y estado global de plugins). Siguen
abiertos REF-P47-interface, REF-P50-session, P71/P72 y las certificaciones nativas
y CI remoto de estas fuentes. P40/P42 conservan el bloqueo externo por ausencia
de editor oficial y paquetes firmados autorizados. Este cierre no certifica una
versión estable ni sustituye el trabajo visual de GUI-DESIGN.

## REF-P69-remote-lifecycle: validación y plan — 22/10/2026

Objetivo: recuperar cambios incompletos del backend remoto y confirmar el
propietario/revisión que está escuchando antes de guardar preferencias.
Riesgo **Alto**: procesos, claves y dos ámbitos de almacenamiento. Dependencias
disponibles: política REF-P69-settings, bloqueo interproceso, escritura atómica,
identidad de procesos y supervisor AccessRuntime. Sin dependencia de GUI-DESIGN.

Conflictos identificados: el supervisor no publica confirmación; los procesos
independientes conservan el endpoint antiguo; la parada descarta al propietario
antes de comprobar su fin; el guardado del programa ocurre después del backend.
Los ámbitos user/service pueden resolver al mismo archivo (portable/desarrollo).

Plan previo a código: añadir estado privado de ejecución con revisión e identidad,
parada/arranque confirmados y registro duradero de recuperación. Coordinar el
guardado final de preferencias con ese registro; compensar solamente los campos
propios y conservar cambios concurrentes en HTTPS, usuarios y sesiones. No copiar
credenciales al registro ni regenerar una clave existente. Recuperar un intento
interrumpido antes de aceptar otro y conservar evidencia si la reparación falla.

Archivos previstos: `apps/access/settings.py`, nuevos auxiliares de ciclo de vida,
`processes.py`, `runtime.py`, `service.py`, servidor SSH y adaptadores
`apps/suite/settings.py`, `commands/settings.py`, `commands/access.py`. Mantener
firmas públicas, permisos, argumentos y formatos existentes mediante metadatos
aditivos privados. Pruebas: fallos de escritura, arranque, confirmación, parada,
cambio de ámbito, PID reutilizado, concurrencia y recuperación tras interrupción;
después suite completa aislada, referencias, catálogo e higiene.

**Resultado final local — 22/10/2026:** 1.635 pruebas y 648 subpruebas correctas,
una omisión POSIX en Windows, cero fallos; **445,73 s**. Incluye `legacy_gui` y
navegador real (`LANCTL_GUI_BROWSER_TESTS=1`). Cobertura combinada con ramas
**72,3180 %**; sentencias **75,8396 %** y ramas **61,7641 %**, umbral del proyecto
60 %. Fuentes congeladas durante esta ejecución, datos aislados y configuración
local del usuario idéntica por hash antes/después.

Ruff, formato completo (527 archivos), Bandit con el umbral de CI, pip check,
pip-audit (sin vulnerabilidades conocidas), catálogo de **1.619 puntos**,
referencias CLI/web, higiene y `git diff --check` correctos. Se contrastaron los
controles con el workflow local de GitHub; no se ha ejecutado CI remoto de estas
fuentes. Las **1.241 firmas públicas anteriores son idénticas**; dos funciones
aditivas de ciclo de vida. Sin cambios en JS/CSS/HTML, IDs públicos ni opciones CLI.

Artefactos locales: `.tool-reports/p69-remote-complete.log`,
`p69-remote-complete.xml`, `p69-remote-complete.coverage`,
`p69-remote-coverage.json`, `p69-remote-contracts.json` y
`p69-remote-verification.json`. **REF-P69-remote-lifecycle y REF-P69-settings
completadas en fuentes.** Siguiente tarea recomendada: P69, preferencias por
interfaz/launcher, respetando la coordinación con GUI-DESIGN.

Dependencia encontrada durante la implementación: un lector de `users.json`
podía perder el almacén cuando otro componente lo migraba a `users.dc`. Se añade
`apps/access/store.py` al alcance para bloquear conjuntamente ambas rutas y
conservar el lector/escritor compatible después del renombrado. La transacción
de preferencias no migra ni copia credenciales. El arranque privado del hijo en
`bootstrap/lanip.py` evita inicializar la configuración de programa mientras su
padre mantiene el bloqueo esperando confirmación; `bootstrap/lanctl.py` reintenta
la reparación al abrir el programa interactivamente y conserva el diagnóstico
si requiere elevación o no puede terminarla.

### Implementación de REF-P69-remote-lifecycle

- Transacción de aplicación alrededor del guardado final CLI y del servicio
  común GUI/TUI. El registro privado v1 guarda intención antes de cada escritura,
  distingue persistencia confirmada de fallo previo y permite reintentar tras
  una interrupción. La comparación del área de acceso conserva también cambios
  posteriores ajenos, como el proyecto seleccionado. Una revisión ajena bloquea
  la reparación en lugar de sobrescribirla.
- Compensación de campos SSH/vista forzada y claves creadas por esta operación;
  no copia credenciales ni restaura snapshots de usuarios/sesiones/HTTPS.
  No rota claves preexistentes. Los permisos POSIX anteriores se restauran al
  reemplazar la configuración; los archivos nuevos del servicio usan su grupo.
  Windows conserva la política de ACL del directorio instalado.
- Arranque con registro del PID real del hijo, identidad y token antes de abrir
  el socket, más confirmación de revisión después del bind. Se contempla el
  wrapper de Python de Windows, cuyo PID puede diferir del intérprete hijo.
  Un fallo de registro o confirmación termina al hijo identificado.
- Parada mediante handle/identidad en Windows y pidfd en Linux; no confunde
  denegación con proceso ausente. El supervisor conserva un hilo que no termina,
  confirma revisiones y distingue propietarios incluso dentro del mismo proceso.
  Cambios de endpoint/ámbito detienen el listener anterior antes del siguiente.
  El ámbito de archivos se conserva separado del tipo de proceso antiguo.
- El servidor SSH cierra sus transportes al detenerse. HTTPS puede cerrarse
  antes de arrancar su bucle sin quedar bloqueado. El estado consultable incluye
  listeners confirmados del servicio y excluye los tokens privados nuevos.
- Recuperación al abrir LANCTL interactivamente y antes de otra modificación
  remota, manteniendo elevación y denegaciones del catálogo remoto. Si falla,
  conserva registro/origen y permite abrir la interfaz para resolverlo; no
  anuncia éxito ni acepta un cambio remoto que oculte ese estado pendiente.

Regresiones nuevas: **43**, con procesos SSH reales, inyección antes/después de
escrituras atómicas, fallo de clave/permisos, confirmación ausente, parada fallida,
interrupción abrupta en otro proceso, ámbito compartido/separado, supervisor
duplicado, PID reutilizado, migración de almacén abierto y conflicto concurrente.
Las expectativas de adaptadores anteriores se actualizan para interceptar el
límite transaccional real, sin eliminar pruebas de autorización. La pasada
integral final se ejecuta después de corregir el caso de proceso independiente
con archivos del ámbito de servicio; las pasadas interrumpidas no son evidencia
de aprobación.

Límites de certificación: falta CI remoto sobre estas fuentes e instalación
Windows/portable y Linux con cuenta de servicio real, ACL/grupo y SSH externo.
El supervisor probado aquí es el mismo código embebido, no una certificación
del gestor de servicios del sistema. Los backends antiguos sin confirmación de
propietario requieren actualización/reinicio. No se publica una versión estable
ni se cambia `0.3.4-alpha.1`. Se desbloquea continuar P69/P71; permanecen abiertos
sus alcances de interfaz y distribución, REF-P34-migration, REF-P47-interface,
REF-P50-session y el editor/firma oficial de P40/P42.

## REF-P69-settings: validación y plan — 22/10/2026

Objetivo: validar y autorizar el lote completo antes de guardar preferencias,
sin depender del parser CLI desde GUI/TUI. Riesgo **Alto** por almacenamiento
compartido, administración remota y compatibilidad de adaptadores.
Dependencias disponibles: configuración v2, bloqueo interproceso, contexto de
proyecto y validadores de dominio. No requiere cambios visuales GUI-DESIGN.

Archivos previstos: `core/settings_catalog.py`, nueva política compartida,
servicio de aplicación en `apps/suite`, adaptador remoto en `apps/access`,
`commands/settings.py`, `settings_menu.py`, GUI suite/desktop y editor TUI.
Conservar firmas RPC/CLI, IDs públicos y formato persistente. Las rutas
internas se conservan en almacenamiento y opciones CLI locales explícitas;
el catálogo de preferencias no concede administración por categoría.

Orden: política y validación del lote; preautorización remota; adaptadores
GUI/TUI/CLI; regresiones y suite integral; catálogo/referencias y backlog.
Verificar valores no finitos, tipos, claves internas, ámbito/launcher, llamadas
directas, CLI integrado, permisos remotos, fallos previos al guardado y proyecto
compartido. Se mantiene separada la certificación nativa y CI publicada.

Hallazgo estructural adicional: el backend remoto inicializa varios archivos,
genera claves y arranca/detiene procesos. Una excepción posterior no equivale
a una transacción reversible. Registrar **REF-P69-remote-lifecycle** antes de
ampliar ese ciclo: preparación sin efectos, compensación y confirmación del
proceso propietario (riesgo Alto). Esta corrección garantiza rechazo de
validación/autorización antes de escribir y elimina el éxito falso tras una
denegación; no certifica recuperación transaccional ante caída del proceso.

### Implementación y comprobación de REF-P69-settings

**Resultado final local — 22/10/2026:** 1.592 pruebas y 648 subpruebas correctas,
una omisión POSIX en Windows, cero errores/fallos, 443,38 s. Incluye
`legacy_gui` y navegador real (`LANCTL_GUI_BROWSER_TESTS=1`). Cobertura combinada
con ramas **72,1686 %**; sentencias 75,7235 %, ramas 61,4837 %; umbral 60 %.
Ruff y formato completos, Bandit con el umbral de CI, pip check, pip-audit
(sin vulnerabilidades conocidas), catálogo **1.578 puntos**, referencias CLI/web,
higiene y `git diff --check` correctos. No se alteraron fuentes durante esta
última ejecución, ni la configuración local restaurada (`workers=64`).

Artefactos locales: `.tool-reports/p69-complete.log`, `p69-complete.xml`,
`p69-complete.coverage`, `p69-coverage.json`, `p69-contracts.json` y
`p69-verification.json`. La primera integral terminada registró cuatro fallos
(una expectativa del parser TUI y tres pruebas dependientes del entorno);
las 56 pruebas relacionadas pasan tras corregir sus fixtures y expectativas.
La repetición completa anterior es la evidencia final, no ese primer intento.


- Servicio `apps/suite/settings.py` con contexto de interfaz/launcher/ámbito
  construido por cada adaptador. Política en `core/settings_policy.py` y
  validadores compartidos; las denegaciones se aplican también al guardar.
- GUI/TUI dejan de construir el parser para guardar. Las opciones y firmas
  CLI continúan; las rutas administrativas clásicas quedan en CLI local.
  El catálogo local conserva metadatos de solo lectura para compatibilidad;
  el remoto excluye rutas internas. La separación completa de preferencias
  entre interfaces sigue perteneciendo a P69.
- Validación del lote completo: tipos, números finitos, enum, direcciones en
  texto, consistencia del teclado y monitor. Una denegación o validación fallida
  no modifica el archivo de configuración. Los formularios TUI obsoletos se
  rechazan cuando cambia el proyecto; los adaptadores mantienen `project_call`.
- El servicio remoto valida endpoint, colisiones, clave existente y puerto
  antes de inicializar almacenes. El backend de servicio exige elevación
  real; el backend de usuario conserva su operación sin UAC. No se concede
  administración local por tener un rol remoto. Los cambios de proyecto
  remotos exigen también `project.manage`, sin sustituir `system.configure`.
- `ContextVar` fija las rutas de usuario/servicio sin modificar el entorno
  global. El arranque recibe ámbito y entorno explícitos. Una revisión durante
  la primera suite detectó esa transmisión pendiente: ejecución interrumpida,
  corrección y regresión añadidas antes de repetir la suite completa.

Pruebas enfocadas finales: **258 correctas, 19 subpruebas y una omisión POSIX**,
incluidas **47 regresiones nuevas**. La suite integral se ejecutó sobre fuentes congeladas.
Contratos: **1.226 firmas públicas anteriores idénticas**, ninguna retirada;
15 adiciones. Sin modificación de JS/CSS/HTML ni de la versión `0.3.4-alpha.1`.
La restricción del catálogo genérico es deliberada: rutas internas se gestionan
por los comandos locales existentes, no por un editor de preferencias.

Incidencia de verificación: una prueba antigua simulaba `_capture` del TUI;
al retirarse la dependencia del parser, dejó de interceptar el guardado y
cambió `workers` local a 128. Se restauró **64**, valor indicado por el usuario,
conservando el resto del documento. La prueba ahora intercepta el servicio y
las ejecuciones posteriores usan una raíz de datos aislada. Cinco pruebas de
rutas por defecto/heredadas ahora limpian explícitamente las variables de entorno.
Las expectativas antiguas de éxito tras denegación y edición de rutas por
catálogo se sustituyen por rechazo o por su opción CLI local compatible;
no se omiten ni se marcan xfail.

Límite histórico de aquella pasada, resuelto por REF-P69-remote-lifecycle en
la sección inicial de este documento: un fallo de disco/arranque después de la preautorización
puede dejar efectos en el backend aunque la configuración de programa no se
guarde. REF-P69-remote-lifecycle queda como próxima prioridad; el cierre total
de REF-P69-settings y la ampliación administrativa de P69/P71 esperan esa
refactorización. No se han ejecutado una instalación ni CI remoto de estas
fuentes, ni se ha publicado una versión estable.

## REF-P84-session: validación y plan — 22/10/2026

Objetivo: conectar cierre, temporizador y selección compartida a las consolas
LANWIRE/LANRACK. Dependencias satisfechas: REF-P84-save-modes y P88;
el límite de mutación ya fija el proyecto y guarda después de liberar locks.
Riesgo **Alto**: una selección concurrente puede desviar una edición o un
guardado. Las rutas explícitas deben permanecer fijas aunque coincidan con
el proyecto inicial. No se modifica el ciclo de vida GUI.

Plan: propietario compartido en `core/projects/console_session.py`, adaptadores
`apps/wire/cli/main.py`, `apps/rack/cli.py`, `apps/wire/tui/app.py` y un callback
opcional compatible en `core/interactive_console.py`. Un temporizador por
consola persistente, contexto explícito por operación/guardado, renovación de
servicios e invalidación de formularios antiguos. El cierre permite guardar,
salir conservando el workspace o cancelar; un error de guardado mantiene abierta
la consola. Los comandos aislados no preguntan ni crean temporizadores.

Verificación prevista: regresiones con VLF real para cierre, todos los modos,
cancelación, errores, temporizador/reintento/limpieza, cambios entre proyectos,
bases externas, edición concurrente y permisos/contratos. Después, suite
completa, catálogo, referencias, análisis estático e higiene. Solo se implementa
esta tarea; REF-P69-settings será la siguiente prioridad disponible.

### Resultado funcional REF-P84-session

- Reproducción previa: tres regresiones fallidas, cierre sin VLF en LANWIRE
  y escrituras dirigidas al proyecto anterior en ambas consolas. Evidencia:
  `.tool-reports/p84-session-before-tests.log`.
- `core/projects/console_session.py`: propietario por consola, reutilizado
  entre entrada/adaptador, sin duplicarlo en llamadas anidadas a la misma base.
  Un destino explícito diferente recibe su propio propietario. Un único hilo
  mantiene los plazos de los proyectos observados; cada guardado lleva su
  contexto y la política común. No adopta un proyecto nuevo solo porque cambie
  la selección mientras espera. Los errores de temporizador/configuración se
  registran con origen y permiten reintento; el aviso pendiente está acotado.
- CLI LANWIRE y CLI/TUI LANRACK renuevan el procesador/servicio solo al cambiar
  la base. Las rutas explícitas permanecen fijas. Los contextos de preferencias
  conservan su baseline para que guardar ajustes desde una base fijada no
  vuelva a seleccionar accidentalmente el proyecto anterior.
- TUI LANWIRE: renueva inventario y procesador; invalida formularios, selección,
  navegación, confirmaciones y comandos pendientes de otro proyecto. La tecla
  que provocó el refresco no se aplica al nuevo inventario. El cierre con
  confirmación suspende/restaura la pantalla, permite cancelación y conserva
  la consola si falla el guardado. Se restaura el manejador de coordinación.
- `core/interactive_console.py`: callbacks opcionales de cierre y avisos,
  compatibles con las invocaciones anteriores. EOF/interrupción de entrada
  principal cierra sin preguntar; interrumpir una confirmación la cancela.
  Los comandos aislados no arrancan hilo ni preguntan y devuelven error si
  falla el guardado de cierre. `n` no borra datos del workspace.
- La parada espera a la escritura en curso; no queda un hilo escribiendo tras
  la salida. Un cierre aceptado bloquea nuevas ejecuciones del temporizador.
  Las excepciones de interfaz también liberan el propietario y la terminal.

Regresiones nuevas: **48 casos** en `tests/test_physical_console_session.py`;
VLF reales y temporizadores reales más comprobaciones deterministas de plazos.
Incluyen los seis modos, cambio concurrente durante edición/confirmación,
bases explícitas y externas, cancelación, disco lleno, EOF, errores de
configuración, limpieza y rutas GUI independientes. Verificación relacionada
anterior a los dos últimos casos: 183 correctas y una omisión de navegador;
la suite integral se ejecuta con navegador habilitado.

Contratos: 1.220 firmas anteriores cotejadas, 1.219 idénticas y una ampliación
compatible (`command_console`: `on_close=None`, `notifications=None`, solo por
nombre). Seis adiciones; ninguna retirada ni incompatibilidad. Los parsers,
IDs públicos, permisos, API de plugins y recursos `gui/*` permanecen iguales.
Catálogo: 1.560 puntos. Referencias CLI/web verificadas; Ruff y formato (519
archivos), Bandit, `pip check`, compilación e higiene correctos.

La primera suite integral detectó cuatro fallos (1.540 correctas, 648
subpruebas y una omisión). Se corrigió una suspensión innecesaria de la pantalla
al salir sin callback; los avisos vacíos tampoco suspenden la TUI. El doble de
RackService en `tests/test_interactive_launchers.py` recibe una ruta temporal
válida y conserva las aserciones sobre reutilización del servicio. La prueba
de recuperación tras fallo de revocación en `tests/test_plugin_process_runtime.py`
espera, con límite de cinco segundos, a que termine la limpieza anterior antes
de reintentar: `cleanupError` podía aparecer mientras `cleanupPending` seguía
activo. Conserva las comprobaciones de denegación de nueva generación y muerte
real del proceso. No se cambia el runtime de plugins ni su contrato asíncrono.
La salida inicial se conserva en `p84-session-first-complete.log`/`.xml`.

### Verificación integral final de REF-P84-session — 22/10/2026

- **1.545 pruebas y 648 subpruebas correctas**, cero fallos y errores;
  **458,42 segundos**. Una omisión específica de pipes POSIX en Windows:
  `test_partial_ipc_frame_cannot_bypass_activation_timeout`. JUnit: 2.194 casos
  contando las subpruebas. Incluye pruebas heredadas y navegador Edge.
- **Cobertura combinada con ramas: 71,8304 %**, umbral 60 % superado.
  Sentencias: 75,3891 %; ramas: 61,1088 %. Informe:
  `.tool-reports/p84-session-complete-coverage.json`.
- **124 pruebas enfocadas correctas** tras reparar los cuatro fallos iniciales;
  evidencia en `p84-session-repair-regressions.log`. Incluye las 48 nuevas,
  las consolas existentes y procesos reales de plugins.
- Ruff/formato, Bandit al nivel exigido, dependencias, catálogo, referencias,
  compilación, higiene y diff correctos. Sin cambios de fuentes durante esta
  última ejecución completa; después se cierra la documentación.

REF-P84-session completada. Se resuelve la dependencia del ciclo de vida físico
de P84/P88 y se puede pasar a su certificación integrada. La siguiente tarea
recomendada es **REF-P69-settings**; REF-P34-migration, P40/P42, REF-P47-interface,
REF-P50-session y las certificaciones externas conservan su estado pendiente.

Comando integral de este ciclo (PowerShell):

```powershell
$env:LANCTL_GUI_BROWSER_TESTS='1'
$env:COVERAGE_FILE='.tool-reports/p84-session-complete.coverage'
.venv/Scripts/python.exe -m coverage run --branch --source=src -m pytest -p no:cacheprovider -m 'legacy_gui or not legacy_gui' --junitxml=.tool-reports/p84-session-complete.xml -v *> .tool-reports/p84-session-complete.log
```

Evidencias locales: `p84-session-regressions.log`, `p84-session-related.log`,
`p84-session-complete.log`/`.xml` y `p84-session-contracts.json` dentro de
`.tool-reports/` (no versionado). Se conserva `0.3.4-alpha.1`; las fuentes se
trabajan en `codex/ref-p84-session` sobre los cambios locales anteriores,
que se han conservado. No se construye, instala ni publica una distribución.
Las pruebas de terminal utilizan streams simulados y entrada controlada;
la certificación manual de terminales nativas y la matriz remota de GitHub
sobre estas fuentes siguen pendientes. P40/P42 mantiene su bloqueo de editor
oficial. No se presenta este resultado como una versión estable.

## REF-P84-save-modes: validación y plan — 22/10/2026

Objetivo: aplicar el disparador `change` a las ediciones físicas confirmadas
de CLI/TUI y reutilizar el mismo límite de operación en los servicios GUI.
Dependencias satisfechas: inventario físico por proyecto/VLF (REF-P84), política
central de guardado y contexto de operación que fija el proyecto durante una
mutación. Riesgo **Alto** por locks, errores posteriores al commit y selección
compartida. Los permisos, parsers y firmas públicas anteriores se conservan.

Archivos previstos: nuevo límite en `core/projects/physical_mutations.py`,
notificación de escrituras de `core/session.py`, procesador y TUI LANWIRE,
servicios `wire/gui_service.py` y `rack/service.py`, adaptación no visual de
`suite/launcher_gui.py`, importación física y regresiones. No guardar dentro
de `update_json`: marcar escrituras en el contexto local y vaciarlo una vez
terminada la operación exterior, con sus locks ya liberados. Las lecturas y
operaciones rechazadas sin escrituras no deben guardar ni exportar otra base.

Hallazgo adicional: las consolas físicas no conectan el temporizador ni la
política de cierre a su ciclo de vida, y retienen su servicio al cambiar de
proyecto. Se separa **REF-P84-session** para diseñar ese ciclo sin reutilizar
un proyecto distinto al de la edición. Este hallazgo no bloquea el disparador
por mutación; los demás modos se verificarán con sus disparadores explícitos,
sin presentar las consolas como conectadas al temporizador/cierre.

Verificación prevista: reproducción previa en CLI/TUI, VLF real, todos los
modos y extensiones de política, errores de escritura, operaciones parciales,
lecturas, guardado único, locks liberados, proyecto fijado, base externa y
concurrencia. Después: suite completa, contratos, catálogo, referencias e higiene.

### Resultado funcional REF-P84-save-modes

- Reproducción anterior a la corrección: creación CLI ausente en el VLF y
  elemento eliminado desde TUI todavía presente en el archivo guardado; dos
  regresiones fallidas en `p84-save-before-tests.log`.
- `core/projects/physical_mutations.py` y `core/session.py`: las escrituras
  confirmadas marcan únicamente la operación local y el inventario esperado.
  Se fija la selección durante la operación, se agrupan llamadas anidadas y
  se llama a la política después de liberar los locks. Las escrituras de otro
  hilo no convierten una consulta local en un guardado.
- `apps/wire/cli/commands.py`, `apps/wire/tui/app.py`, `apps/rack/cli.py`:
  creación, edición, puertos, conexiones, eliminación y comandos por lotes
  aplican el límite compartido. Un error de guardado conserva los cambios,
  devuelve error al CLI y mantiene la TUI operativa. Si un lote anterior a esta
  corrección admite commits parciales, se conservan y se refresca la vista,
  manteniendo el error original; no se presenta el lote como transaccional.
- `apps/wire/gui_service.py`, `apps/rack/service.py` y el adaptador no visual
  `apps/suite/launcher_gui.py`: sustituyen el guardado específico del RPC por
  el mismo límite de los servicios. CPD de LANWIRE conserva explícitamente su
  ruta de mutación. No se alteran recursos `gui/*` ni contratos RPC/permisos.
- `core/projects/physical.py`: la importación explícita utiliza la política
  del proyecto elegido y conserva el archivo de origen.
- Un fallo de VLF conserva el origen real en
  `LANCTL.Project.Physical.Autosave`, registra que la base ya fue modificada y
  pide reintentar el guardado. Si además falló la operación, su excepción
  original no se sustituye por el error del guardado.

Regresiones en `tests/test_physical_save_modes.py`: 32 casos nuevos. Incluyen
los seis modos, una política de plugin, CLI real, acciones TUI, CPD/GUI,
lecturas sin escritura, bases externas, importación, fallo de disco, lotes
parciales, cambio de selección antes del commit y dos comandos concurrentes.
La toma de todos los locks desde otro hilo durante el guardado comprueba que
el editor ya los ha liberado. La selección posterior a un commit pendiente
es rechazada correctamente por la protección existente; la prueba de cambio
concurrente sitúa la selección antes del commit, sin desactivar esa protección.

Verificación relacionada: 202 casos correctos y dos pruebas de navegador
omitidas en esa ejecución enfocada. Comprobación final enfocada con navegador
habilitado: **66 casos correctos**, sin omisiones (32 nuevos más sincronización
de proyecto y adaptador de launchers). Evidencias en
`.tool-reports/p84-save-related.log` y `p84-save-final-focused.log`.

### Verificación integral final — 22/10/2026

Fuentes finales de `codex/ref-p84-save-modes`, versión `0.3.4-alpha.1`,
conservando las modificaciones locales de los ciclos anteriores. Se mantuvieron
sin cambios durante la ejecución completa; solo se cerró la documentación después.

- **1.497 pruebas y 648 subpruebas correctas**, cero fallos/errores y una
  omisión de pipes POSIX en Windows:
  `test_partial_ipc_frame_cannot_bypass_activation_timeout`.
  Duración: 397,32 segundos; JUnit registra 2.146 casos con las subpruebas.
  Incluye pruebas heredadas y navegador Edge sin interfaz visible.
- **Cobertura combinada con ramas: 71,4203 %**, umbral 60 % superado.
  Sentencias: 75,0052 %; ramas: 60,6347 %.
- Ruff y formato correctos (517 archivos), Bandit sin hallazgos en el nivel
  exigido y `pip check` correcto. No cambian dependencias.
- Catálogo actualizado: **1.556 puntos**; referencias CLI/web, higiene y
  `git diff --check` correctos. No cambian comandos, opciones ni IDs públicos.
- **1.217 firmas de funciones/métodos públicos conservadas**, tres adiciones,
  ninguna retirada o modificada. El cotejo AST de este ciclo excluye funciones
  locales y clases privadas. Los contratos de plugins no se han modificado;
  las regresiones de permisos, RPC, contexto, VLF y concurrencia pasan.
- Los recursos `gui/*` conservan sus hashes iniciales. El cambio del adaptador
  `launcher_gui.py` reutiliza la política común sin modificar controles visuales
  ni firmas RPC. No se compilaron, instalaron o publicaron distribuciones.

Comando integral reproducible (PowerShell):

```powershell
$env:LANCTL_GUI_BROWSER_TESTS='1'
$env:COVERAGE_FILE='.tool-reports/p84-save-complete.coverage'
.venv/Scripts/python.exe -m coverage run --branch --source=src -m pytest -p no:cacheprovider -m 'legacy_gui or not legacy_gui' --junitxml=.tool-reports/p84-save-complete.xml -v
.venv/Scripts/python.exe -m coverage json -o .tool-reports/p84-save-complete-coverage.json --fail-under=60
```

Evidencias locales ignoradas: `p84-save-complete.log`, `p84-save-complete.xml`,
`p84-save-complete-coverage.json`, `p84-save-contracts.json` y
`p84-save-bandit.log`, dentro de `.tool-reports/`. La suite final y el umbral
de cobertura terminaron con código 0.

REF-P84-save-modes queda completada para el disparador de mutación. Desbloquea
el diseño de sesión de **REF-P84-session**, siguiente tarea recomendada antes
de REF-P69-settings. Cierre/temporizador y renovación de los servicios de
consola continúan pendientes; no se declaran cubiertos por estas pruebas de
disparadores explícitos. Siguen pendientes las adaptaciones de plugins,
editor oficial, CI de estas fuentes y certificación de distribuciones.

## REF-P34-runtime: validación y plan — 21/10/2026

Dependencias comprobadas: concesiones por generación de `authorization.py`,
registro compartido y confianza del editor, limpieza diferida fuera de locks,
contratos tipados de funciones/eventos y proceso aislado existente. No depende
de crear un editor oficial: las firmas reales de P40/P42 siguen pendientes.
El runtime `trusted` anterior conserva su contrato en proceso y su aviso de
reinicio; no se migran paquetes ni permisos automáticamente.

Objetivo: una ejecución cancelable con contrato explícito para nuevos paquetes
aislados (`runtimeApiVersion: 2`), RPC JSON versionado ligado a la generación,
validación de permisos en el host y callbacks retirados al revocar. El cierre
debe confirmar la muerte del proceso; una limpieza fallida no habilita otra
generación. El RPC permite únicamente operaciones y tipos declarados, nunca
objetos pickle, imports elegidos por el emisor ni acceso al gestor del host.

Archivos previstos: protocolo y adaptador de proceso nuevos en `core/plugins`,
`isolated_runtime.py`, `authorization.py`, `manager.py`, `models.py`, pruebas
de runtime/revocación y documentación de plugins. Riesgo **Crítico** por
concurrencia y permisos. Se mantiene la API pública anterior y el protocolo
aislado v1; el v2 tiene un catálogo de operaciones acotado y documentado.
Verificar revocación durante llamadas, procesos/hilos que no cooperan,
dependencias, cambio de generación, firma/confianza, límites y mensajes
inválidos, además de toda la suite. No modificar GUI-DESIGN ni publicar builds.

### Resultado funcional y revisión de dependencias REF-P34-runtime

- Nuevos `runtime_protocol.py`, `process_api.py` y `process_runtime.py`: JSON
  acotado por versión/generación, catálogo explícito, callbacks y permisos por
  llamada. Un contexto RPC evita volver a ejecutar callbacks `trusted` dentro
  del host. Los contratos anteriores y sus IDs no cambian.
- `authorization.py`, `api.py` y `manager.py`: registro y revocación comparten
  una transacción; ninguna inserción tardía sobrevive a la revocación. La
  limpieza se ejecuta fuera de locks. Se conserva el proceso si falla el
  cierre, se bloquea la nueva generación y se exponen diagnóstico y confirmación
  local. Sustitución/desinstalación comprueban el cierre antes de cambiar archivos;
  la instalación usa una copia temporal verificada del LCP para ambas fases.
- `isolated_runtime.py`: v1 también tiene plazo de cierre independiente del
  manifiesto, conserva referencias ante fallo y vigila la muerte del propietario.
  Corregidas firmas HANDLE de Win32 y completada la denegación de creación,
  sustitución y señalización de procesos mediante eventos de auditoría Python.
  Se usan canales exclusivos por generación; no hay locks de datos compartidos
  con el worker que puedan quedar abandonados al terminarlo.
- `models.py`, manual generado y `LCP.md`: selección explícita de API v2 y
  compatibilidad v1/trusted. El catálogo v2 no promete operaciones sin adaptador
  ni un sandbox del sistema operativo. La firma/editor de los paquetes oficiales
  sigue pendiente; no se crea confianza nueva.
- Siete entradas de empaquetado: `freeze_support()` antes del arranque de la
  aplicación. Dependencia confirmada en la [documentación de PyInstaller](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#multi-processing).
  Límites/terminación contrastados con [multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
  y [Job Objects de Windows](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).
  Eventos de proceso contrastados con la [API os de Python](https://docs.python.org/3.11/library/os.html).

Pruebas nuevas en `test_plugin_process_runtime.py` y ampliadas en
`test_plugin_revocation.py`: callbacks reales, caída del host incluso sin Job,
hilos no cooperativos, dependencia revocada, firma/permisos conservados,
generaciones antiguas, presupuesto, frames corruptos, prohibiciones nativas,
cierre fallido, conservación de archivos y arranque de workers empaquetados.
La última ejecución enfocada pasa 71 casos. La primera ejecución ampliada
encontró un ID de parametrización de 64 KiB que excedía el límite de entorno
de Windows; se corrigió el nombre del caso sin omitir la prueba de frame grande.

La primera suite integral de este bloque se interrumpió al detectar las vías
de creación nativa no cubiertas; no se cuenta como validación final. Se añadió
la regresión para v1/v2 y se regeneraron catálogo y referencias antes de repetir.
Quedan como continuación REF-P34-migration y la consolidación del estado global
de P34; REF-P50-session sigue siendo necesaria para MCP. La revocación y la
confirmación locales no se extrapolan a la certificación de todos los paquetes
o plataformas.

### Verificación final de REF-P34-runtime — 21/10/2026

Fuentes finales de `codex/ref-p34-runtime`, versión `0.3.4-alpha.1`, conservando
los cambios locales anteriores. No se modificaron las vistas de GUI-DESIGN.

- **1.465 pruebas y 648 subpruebas correctas**, cero fallos/errores y una omisión
  POSIX en Windows: `test_partial_ipc_frame_cannot_bypass_activation_timeout`.
  Suite completa con heredadas y navegador Edge sin interfaz visible;
  duración 388,25 segundos. JUnit registra 2.114 casos contando subpruebas.
- **Cobertura combinada con ramas: 71,2457 %**, umbral de 60 % conservado.
  Cobertura de sentencias 74,8449 % y de ramas 60,4438 %.
- Ruff y formato correctos (515 archivos); Bandit sin hallazgos en el nivel
  exigido y `pip check` correcto. No cambian dependencias de producción.
- Catálogo regenerado y verificado: **1.552 puntos**. Referencias CLI/web,
  higiene y `git diff --check` correctos.
- **1.238 firmas públicas previas conservadas**, ninguna retirada/alterada,
  14 adiciones. `contracts.py`, `events.py`, `functions.py` y `extensions.py`
  conservan sus hashes iniciales; no se reescriben IDs públicos. Las regresiones
  de contratos, permisos, confianza, registros y extensiones complementan
  este cotejo estático.
- Ejecutable Windows de comprobación recompilado con las fuentes finales:
  `--version`, instalación y activación explícitas de un LCP aislado de prueba,
  callback RPC real, revocación y rechazo posterior del comando. Datos y
  permisos aislados en `.tool-reports`, sin instalar ni alterar plugins reales.
  La verificación no equivale a compilar/certificar los siete instalables,
  Linux ni una nueva distribución estable.

Comando integral reproducible (PowerShell):

```powershell
$env:LANCTL_GUI_BROWSER_TESTS='1'
$env:COVERAGE_FILE='.tool-reports/p34-verified.coverage'
.venv/Scripts/python.exe -m coverage run --branch --source=src -m pytest -p no:cacheprovider -m 'legacy_gui or not legacy_gui' --junitxml=.tool-reports/p34-verified.xml -v
.venv/Scripts/python.exe -m coverage json -o .tool-reports/p34-verified-coverage.json --fail-under=60
```

Evidencias locales ignoradas: `p34-verified.log`, `p34-verified.xml`,
`p34-verified-coverage.json`, `p34-contracts.json`, `p34-final-regressions.log`,
`p34-final-bandit.log`, `p34-frozen-build-final.log` y `p34-frozen-smoke.json`,
todas en `.tool-reports/`. La suite final terminó con código 0; no se han
repetido ni ocultado fallos de esa ejecución.

REF-P34-runtime queda completada en su alcance de infraestructura. Desbloquea
la adaptación explícita REF-P34-migration; P34 conserva la adopción de los
paquetes y la consolidación del estado entre propietarios. P40/P42 siguen sin
editor oficial y REF-P50-session sigue pendiente. Siguiente tarea disponible:
**REF-P84-save-modes**, seguida de REF-P69-settings. No se ha publicado una
versión estable ni se atribuyen a estas fuentes los resultados históricos de CI.

## Histórico del corte anterior — 21/10/2026

Fuentes de `experimental-gui`, versión `0.3.4-alpha.1`, incluidos los cambios
locales de este ciclo. La ejecución completa final incorpora pruebas heredadas
y navegador real de Edge sin interfaz visible (`LANCTL_GUI_BROWSER_TESTS=1`):

- **1.410 pruebas y 648 subpruebas correctas**, cero fallos y una omisión:
  `test_partial_ipc_frame_cannot_bypass_activation_timeout`, específica de pipes
  POSIX. Duración: 360,47 segundos. JUnit registra 2.059 casos contando subpruebas.
- **Cobertura con ramas: 71,1913 %**, umbral conservado del 60 %.
- Ruff y formato correctos (511 archivos); Bandit sin hallazgos en el nivel
  exigido, `pip check` correcto y `pip-audit` sin vulnerabilidades conocidas.
- Catálogo actualizado: 1.494 puntos; referencias CLI/web verificadas, sintaxis
  JavaScript/PowerShell, higiene y `git diff --check` correctos.
- Se conservan las 1.225 firmas cotejadas con el inicio del ciclo; 13 adiciones,
  ninguna firma retirada o alterada. Las pruebas de permisos, contexto,
  contratos y VLF complementan este cotejo estático.

Evidencia local ignorada por Git: `.tool-reports/backlog-20261021-complete.log`,
su JUnit `.xml`, `backlog-20261021-complete-coverage.json` y
`backlog-20261021-contracts.json`. La suite se ejecutó con Coverage, `--branch`,
`--source=src`, `-p no:cacheprovider` y `-m 'legacy_gui or not legacy_gui'`.

REF-P84 desbloqueó la persistencia de P84 y la comprobación de P85; P79 permitió
verificar el cierre con guardado P80. La base física histórica se conserva y
solo se importa mediante acción explícita; no se han migrado datos del usuario.
P70/P73 compilan como comprobación estructural, pendiente distribución completa
y prueba nativa. La lista vigente de desarrollo y bloqueos está al principio de
[BACKLOG.md](BACKLOG.md): REF-P34-runtime, REF-P84-save-modes, REF-P69-settings,
REF-P47-interface, REF-P50-session, P71/P72, firmas oficiales y certificaciones.
No se ha integrado, publicado ni instalado una nueva versión estable. Las
ejecuciones de GitHub citadas más abajo corresponden a sus commits indicados,
no a estas modificaciones locales.

## Histórico inicial — 15/10/2026

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

Para evitar confundir el análisis incremental de la PR con el repositorio
completo, se ejecutó también
[CodeQL manual sobre la rama candidata](https://github.com/CctrGy/LANCTL/actions/runs/39069160510).
El análisis completo 1973841429 de `2b8494a` termina sin errores ni advertencias
del analizador, con 43 reglas y **10 resultados**: #6/#7/#10/#12/#14/#15/#16/#17/
#18/#19. Se revisaron sus orígenes: fecha `passwordRotatedAt`, rutas de
`secret_root`, IDs/metadatos de credenciales y etiquetas del detector de higiene.
#19 corresponde a la ruta del archivo de configuración, antes registrada como
#8 en `main`. Los dos hallazgos de host keys y el de cabecera HTTP no aparecen
en este análisis completo. Los diez resultados de metadatos siguen visibles;
no se han añadido exclusiones ni se han descartado alertas para obtener un verde.

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

GUI-DESIGN completó la compilación y comprobación nativa de los seis launchers.
Se verifican independientemente las 386 entradas congeladas y la huella del
instalador local: 135.487.663 bytes, SHA-256
`5401cb5a085c4cf8fa2b86dbb9270e72f6a45ff0cfdfbdbf1c4ce113626bde3a`.
El resultado está en `dist/gui-current/LANCTL-0.3.4-alpha.1-gui-setup.exe`.
Los seis binarios incluyen los recursos/módulos actuales y pasan apertura,
icono, IPC y cierre; los datos de prueba están aislados. No se ha instalado ni
publicado ese instalador en el equipo del usuario. La certificación remota de
instalación y paquetes continúa mediante el workflow manual, que excluye el
job de publicación por exigir un evento `push`.

Los jobs Windows 3.10 y 3.11 del segundo CI detectaron **seis expectativas de
rutas incorrectas** en `test_paths.py`, `test_icons.py` y
`test_physical_core_libraries.py`. El directorio temporal del runner usa
`RUNNER~1`, mientras que los servicios devuelven rutas canónicas con
`runneradmin`. Se reprodujeron los mismos seis fallos localmente mediante un
alias 8.3 real obtenido con `GetShortPathNameW`. Las expectativas ahora resuelven
la ruta esperada, conservando los componentes/nombres y el contrato existente;
**16/16 pruebas correctas** con el alias. Solo cambian pruebas, sin modificar
servicios ni invalidar los binarios compilados. La matriz Windows se repite
sobre la corrección; no se normaliza el entorno del runner para ocultar el caso.

La siguiente [ejecución CI](https://github.com/CctrGy/LANCTL/actions/runs/39069631762)
de `4193664` completa correctamente Linux y Windows Python 3.10/3.11 con las
regresiones de navegador activadas en Windows. El
[workflow manual de distribución](https://github.com/CctrGy/LANCTL/actions/runs/39069158807)
de `2b8494a` también finaliza correctamente: Windows instalado/actualizado/
desinstalado conservando datos, portable con los seis launchers y exclusión de
GUI duplicada, paquetes nativos Linux amd64 y arm64 con instalación/actualización/
desinstalación. El job `release` se omite; no crea tags ni publicaciones.
Estos resultados preceden a la corrección nativa Clink y a los previews P45,
por lo que se repiten las comprobaciones pertinentes sobre el siguiente corte.

### P48: comprobación nativa y corrección de registro repetido

Se usa el ZIP oficial de [Clink 1.9.34](https://github.com/chrisant996/clink/releases/tag/v1.9.34),
contrastado con su SHA-256 publicado, en `.tool-reports/clink-native/`, sin
instalar autorun ni modificar PATH/perfil de forma permanente. CMD con Clink
completa `--version` para los seis launchers y el contexto `lanctl ip history`.

La prueba real detectó que `installscripts` devuelve 1 para una carpeta ya
registrada; `uninstallscripts` hace lo mismo si ya fue retirada. El adaptador
trataba esos casos como fallos. Se corrige `core/clink_integration.py`: ante
código 1 comprueba el listado real y exige coincidencia exacta normalizada de
la carpeta y el estado solicitado. No acepta prefijos ni un listado fallido.
Conserva bloqueo, propietario, protección ante elevación, plazo y origen de
errores; no cambia la API pública. Riesgo medio, sin impacto en Linux.

Las regresiones reproducen tres fallos anteriores; después pasan 22 pruebas
y seis subpruebas enfocadas. Con Clink real pasan registro, repetición, retirada,
repetición de retirada y retirada previa por otra herramienta. El registro
original del usuario se comprueba y restaura exactamente; los marcadores de
prueba permanecen en un directorio aislado. P48 solo conserva la comprobación
de desinstalación elevada por otra cuenta. No se atribuye esa certificación a
la prueba del usuario normal.

El supuesto bloqueo de cierre LANIP fue un fallo del harness: usaba proyectos
reales y pipes sin consumir. GUI-DESIGN comprobó cierre nativo y código de salida
0 con directorio temporal y salida a archivo; no necesitó cambiar la aplicación
por esa observación. P34/P47 están integrándose con sus avisos y selector real.

La regresión adicional de codificación reproduce el fallo con salida UTF-8 y
CP1252 como codificación predeterminada de Windows. Se declara UTF-8 en las
dos llamadas Clink. La prueba pasa tras fallar antes; Clink 1.9.34 real confirma
registro repetido y retirada de una ruta con espacios y «é», restaurando el
registro original. La suite completa anterior a este último ajuste pasó
1.241 pruebas, 645 subpruebas y una omisión, con cobertura 69,8801 %.

### P71.4: validación y plan de cuenta inicial en Setup

Solicitud humana nueva recibida mediante GUI-DESIGN: el instalador no pide
crear las credenciales de acceso remoto. Se adelanta exclusivamente ese punto
de P71, sin incorporar el resto de la reorganización del instalador.

- Objetivo: ofrecer un asistente local para la primera cuenta administrativa
  LANACCESS del servicio; preservar todas las cuentas de una actualización.
- Archivos: `apps/access/remote_setup.py`, parser `manager_cli.py`, regresiones,
  Clink y referencias. GUI-DESIGN posee `gui/remote-setup.{html,css,js}` e Inno.
- Dependencias: `AuthenticationService`, `AccessStore`, bloqueo entre procesos,
  privilegios del SO, WebView2 y ACL de la carpeta del servicio aplicadas antes
  del asistente. Ventana independiente después de copiar los ejecutables.
- Riesgo alto: confundir el perfil de quien acepta UAC con el almacén del
  servicio o filtrar secretos por argv/logs. La ruta procede de Windows y se
  rechazan redirecciones/configuraciones personalizadas incompatibles.
- Contrato: comando aditivo `lanaccess remote-setup`; puente local limitado a
  estado, creación inicial y cierre. Contraseña/confirmación solo en memoria;
  hash Scrypt mediante el servicio existente; ninguna contraseña predeterminada.
- Impacto: no modifica autenticación ni cuentas existentes, no abre listeners,
  no habilita SSH/HTTPS ni toca firewall. La creación concurrente se serializa.
  Cancelación/silencioso permiten instalar sin configurar acceso remoto.
- Verificación prevista: no administrador, validación, duplicado, concurrencia,
  actualización, rutas, ausencia de secretos, contrato parser, navegador y
  suite completa; repetir CI y distribución después de integrar GUI-DESIGN.

La implementación de P71.4 pasa las regresiones de permisos del SO, longitud y
confirmación de contraseña, creación concurrente, actualización sin reemplazar
cuentas, migración heredada, corrupción, rutas redirigidas/personalizadas,
cancelación y redacción de errores. La integración Edge llama al servicio real
con un almacén temporal: crea la cuenta y verifica después su autenticación
Scrypt y rol administrativo, sin modificar cuentas reales ni abrir listeners.
Los errores de inicio se muestran dentro del asistente, también con consola
oculta. El recorrido humano completo bajo UAC se comprobará con el instalador
reconstruido; no se da por verificado por la prueba de navegador.

La inspección final contrasta 89 firmas públicas con `main` (`ccd728b`) y, para
el adaptador Clink añadido después, con el checkpoint `581c5a3`: no se elimina
ni cambia ninguna. `AccessManager.__init__/list/delete` siguen disponibles con
las mismas firmas por herencia de `CredentialService`. Los tres archivos de
contratos/IDs Core permanecen idénticos. `remote-setup` es un comando aditivo;
se regeneran CLI, Clink y referencia web. La redacción de `passwordHash` en la
salida CLI es el cambio de seguridad intencionado ya descrito, manteniendo la
clave JSON y añadiendo `passwordConfigured`.

### Corte final local con P45, P48 y P71.4

Suite completa, incluidas las pruebas heredadas y navegador Edge:
**1.269 pruebas y 645 subpruebas correctas**, una omisión POSIX en Windows,
196,59 s. Cobertura de ramas/líneas combinada **69,9154 %**, umbral 60 %.
Ruff/formato: 490 archivos; Bandit con el mismo nivel `-ll` de CI, pip check,
pip-audit, compileall, catálogo (1.434 puntos), referencias CLI/web, higiene y
`git diff --check` correctos. Se congela este código para reconstrucción local
y CI/distribución de la PR 26; sus resultados remotos se añaden por commit.

El candidato `3a02230` supera el job Linux de
[CI 39070877629](https://github.com/CctrGy/LANCTL/actions/runs/39070877629):
1.195 pruebas, 54 omisiones de plataforma/navegador y 21 heredadas excluidas
por la configuración ordinaria; estas últimas sí están incluidas en la suite
local completa. Cobertura Linux 68,4067 %. Ruff, referencias, catálogo, Bandit,
higiene y dependencias pasan en el runner.

El análisis CodeQL completo de la rama,
[39070884827](https://github.com/CctrGy/LANCTL/actions/runs/39070884827), produce
el análisis 1973896053 sobre `3a02230`, 43 reglas, sin errores ni advertencias
del motor. Conserva exactamente los diez resultados previamente inspeccionados
sobre rutas, fechas y metadatos; no incorpora resultados nuevos con P48/P71.4.
No se han silenciado ni descartado alertas en GitHub. Esto no declara cerradas
las alertas de `main` antes de integrar la corrección y analizar esa rama.

La matriz completa de CI 39070877629 termina correctamente para `3a02230`:
Linux y Windows Python 3.10/3.11. Las regresiones de navegador están habilitadas
en ambos jobs Windows, incluidas las del asistente de cuenta remota.

El Setup local se reconstruye sin ejecutar el instalador: Inno retorna 0 y
produce `dist/gui-verified/LANCTL-0.3.4-alpha.1-gui-setup.exe`, 135.699.318 bytes,
SHA-256 `54b71767a472d4d0da8fb7fd64ba1ce289a749f5505dede980e0280e6fd936e5`.
Se verifican las 398 entradas del manifest congelado; los seis ejecutables
contienen los 32 recursos y 17 módulos esperados y el parser `remote-setup`.
La última prueba nativa de ventanas se interrumpe por Escape del usuario y
queda pendiente; no se declara éxito por el mero arranque. Las cuentas reales
y el control UAC no se modifican. El artefacto local es experimental y procede
del checkout compartido; los paquetes de certificación se generan desde el
commit limpio de la PR en los runners de GitHub.

### Último caso de plataforma del asistente

La revisión posterior encuentra un fallo en `remote-setup` fuera de Windows:
intentaba importar WebView antes de rechazar la plataforma, por lo que una
instalación Linux sin GUI terminaba con `ModuleNotFoundError`. Se reproduce
con una prueba que impide cargar WebView; después se rechaza con `ValueError`
antes de importar la interfaz, conservando el manejo CLI existente. Cambian
únicamente dos líneas del adaptador, una regresión y el catálogo (1.435 puntos).
Pasan 35 pruebas enfocadas, Ruff, formato, referencias e higiene. Se repiten
CI y distribución sobre esta corrección; los resultados de `3a02230` anteriores
se conservan como evidencia del corte previo, sin atribuirlos al nuevo commit.

La suite completa del código `7a60daa`, con navegador y compatibilidad heredada,
termina con **1.270 pruebas, 645 subpruebas correctas y una omisión POSIX**,
en 189,71 s; cobertura **69,9160 %**. CodeQL completo 39071435601 produce el
análisis 1973914868 (43 reglas, sin errores/advertencias del motor), con los
mismos diez resultados de metadatos inspeccionados y ninguna alerta nueva.
El instalador local documentado antes corresponde al corte `3a02230`; los
paquetes del código final se reconstruyen en 39071434470, sin publicación.

### Cierre de verificación del candidato 7a60daa

- [CI 39071429147](https://github.com/CctrGy/LANCTL/actions/runs/39071429147):
  **correcto** para Linux y Windows Python 3.10/3.11. Cada job Windows pasa
  1.249 pruebas y 645 subpruebas; una omisión y 21 heredadas excluidas por su
  configuración, ya incluidas en las 1.270 de la suite local.
- [Seguridad de la PR](https://github.com/CctrGy/LANCTL/actions/runs/39071428973)
  y [análisis completo](https://github.com/CctrGy/LANCTL/actions/runs/39071435601):
  **correctos**, sin nuevas alertas respecto al análisis inspeccionado.
- [Distribución 39071434470](https://github.com/CctrGy/LANCTL/actions/runs/39071434470):
  **correcta** en Windows x64, Linux amd64 y Linux arm64 nativos. Incluye
  instalación, actualización y desinstalación conservando datos. Windows pasa
  además seis launchers portables, preferencias CLI/TUI/GUI, override explícito
  CLI, bloqueo de GUI duplicada, restauración y cierre independiente.
- Los artefactos quedan guardados en ese workflow. `release` se omite por ser
  una ejecución manual; no se publica una versión ni se mueve una rama estable.
  No hay certificado Authenticode configurado: los paquetes llevan checksums,
  pero no se presentan como firmados.

La [PR 26](https://github.com/CctrGy/LANCTL/pull/26) permanece en borrador con el
código y la evidencia actualizados. El backlog local conserva el cierre de la
verificación y separa los límites pendientes: REF-P34-runtime (crítico), editor
oficial/firma P40/P42, varias NIC y acceso desde otra máquina, desinstalación
Clink con otra cuenta y revisión visual elevada de P71.4. El control local de
ventanas interrumpido por el usuario no se reanuda. P50 y las nuevas opciones
P69–P73 (salvo la cuenta inicial ya implementada) siguen su planificación.
La siguiente tarea técnica recomendada es REF-P34-runtime, previa a cerrar
P34 y a exponer operaciones mediante el puente P50. No se declara estable el
candidato `0.3.4-alpha.1` mientras permanezcan estos límites.


## P88 — Cambio global de proyecto y protección de vistas antiguas — 18/10/2026

La selección dejaba de propagarse porque cada proceso fijaba las rutas del
proyecto al iniciarse. Además, LANWIRE/LANRACK/LANACCESS conservaban servicios
ligados al almacén anterior. La configuración compartida pasa a ser la autoridad
entre operaciones; el heartbeat reconcilia incluso cambios sin evento. LANIP
actualiza selector e inventario en una respuesta coherente; los launchers
renuevan sus servicios y LANACCESS bloquea el almacén anterior.

Cada operación conserva una instantánea durante su ejecución. Los escaneos y
trabajos backend ya iniciados mantienen su proyecto original; las siguientes
operaciones interactivas usan el nuevo. Se limpian actividad y latencias al
cambiar de proyecto, incluso si se repiten identificadores de dispositivos.
Los formularios envían la identidad que se mostró con sus datos mediante el
sobre RPC aditivo `project_call`; se rechaza una edición antigua sin aplicarla
al proyecto nuevo ni borrar su borrador. No se expone un despachador arbitrario.

Guardar preferencias desde una instantánea antigua conserva la selección más
reciente y los campos que el usuario no modificó. Las actualizaciones mediante
el catálogo de configuración conservan el origen de su instantánea, y las
sustituciones explícitas de documentos siguen funcionando. La apertura detecta
una selección competidora antes de confirmar el cambio. Se mantienen las
protecciones existentes de proyectos inválidos y workspaces con cambios.

Archivos de ejecución: `core/config.py`, `core/session.py`, nuevo
`core/project_context.py`, `core/projects/workspace.py`; adaptadores
`suite/gui.py`, `suite/gui_support.py`, `suite/launcher_gui.py`; LANIP GUI,
CLI y TUI; integración de llamadas/refresco en `gui/app.js`, `desktop.js`,
`launcher.js` y `suite.js`. No cambia el esquema del inventario físico ni se
introduce una copia del IDF en el VLF. Se conservan overrides explícitos de
arranque y no se redirigen servicios del sistema a datos de otro usuario.

Pruebas añadidas/actualizadas en `tests/test_project_sync.py`,
`test_coordination.py`, `test_settings_catalog.py` y `test_backlog_projects.py`:
seis launchers en procesos separados, seis adaptadores GUI vivos, formulario
obsoleto de LANRACK en Edge, renovación de almacenes, bloqueo del vault,
cambio fallido, datos sin guardar, escritores concurrentes y sesión backend.
Las pruebas finales de TUI y sincronización pasan: 116 casos y 19 subpruebas.
Se conservan las 201 firmas públicas revisadas frente a `7a60daa`; los archivos
de contratos, eventos y funciones de plugins son idénticos a esa referencia.
Ruff, formato, higiene, referencias CLI/web, catálogo de 1.439 puntos y
`git diff --check` correctos. Bandit no encuentra resultados medios/altos ni
errores de análisis.

P88 continúa abierta para la centralización visual del selector en LANCTL,
las barras coordinadas con P75 y la entrega compilada. Este cambio está en
fuentes locales: los instaladores y los resultados de GitHub del candidato
anterior no certifican esta modificación. No se ha publicado una versión
estable ni reanudado el control nativo de ventanas interrumpido por el usuario.

Verificación final sobre las fuentes actuales: **1.289 pruebas aprobadas,
645 subpruebas y una omitida** (POSIX en Windows), incluidos navegador Edge
sin ventanas visibles y casos legacy. Cobertura de líneas y ramas con los
parámetros de GitHub (`--branch --source=src`): **70.2655 %**, supera el
umbral existente del 60 % sin modificarlo. La primera salida de cobertura
que incluía plugins temporales se descartó; estos son los resultados de la
repetición completa con el alcance de fuentes correcto.

Evidencia local ignorada: `.tool-reports/project-sync-ci.log`,
`project-sync-ci.xml`, `project-sync-coverage.json`,
`project-sync-tui-final.log`, `project-sync-contracts.json` y
`project-sync-bandit.json`. No se reutilizan resultados remotos anteriores
como si correspondieran a este cambio. Quedan desbloqueadas la integración
visual P88/P75 y su posterior compilación; P74 y P76–P78 siguen requiriendo
su validación y evolución del modelo de elementos físicos.


## Plan de ejecución LANRACK — 18/10/2026

Alcance autorizado: P74, P76, P77, P78, P82, P66 y P88. GUI-DESIGN estaba
inactivo al comprobarlo; se conservan sus modificaciones existentes.

| Orden | Objetivo | Módulos y archivos principales | Dependencias | Riesgo e impacto |
|---|---|---|---|---|
| 1 | P74/P77: ubicación versionada y ocupación única | Core `physical_placement.py`, IDF `database.py`, `wire/gui_service.py`, `rack/skins.py` | Dimensiones P66 existentes | Alto: compatibilidad de datos antiguos y todas las escrituras |
| 2 | P76/P78: mover y alojar equipos en bandejas | `rack/service.py`, `suite/launcher_gui.py`, pruebas de inventario | Paso 1; revisión transaccional existente | Alto: concurrencia, puertos y enlaces que deben conservarse |
| 3 | P82/P66: editar desde la vista y reflejar las ubicaciones | `gui/wire-gui.js`, `physical-gui.js`, editor físico compartido; CLI/TUI de rack y wire | Pasos 1–2 | Medio: formularios, selección, representación multi-U |
| 4 | P88: selección central y proyecto informativo | GUI principal existente; `desktop.js`, `launcher.html/js`, `wire-gui.js` | Sincronización Core y guardas por operación ya implementadas; acceso LANCTL existente | Alto: evitar que el nombre y los datos pertenezcan a proyectos diferentes |
| 5 | Verificar y actualizar referencias y backlog | Pruebas de regresión, suite, catálogos y documentación | Pasos anteriores | Medio: compatibilidad CLI y APIs públicas |

Decisión de esquema: `data.location.schemaVersion = 1`, con `rack`, `in_rack`,
`unit` y `tray`. Un dispositivo alojado guarda `tray` y usa `rack: null`,
`in_rack: false`, `unit: 0`; su rack/unidad efectivos se derivan de la bandeja.
Se conserva `rackAppearance.units` como única altura ocupada del equipo.
La migración es explícita al editar la ubicación: las lecturas antiguas no
reescriben el fichero; una asociación sin posición se muestra para revisión.
Los formatos IDF y VLF mantienen sus contratos. El almacén físico compartido
continúa en `physicalDatabase`; no se afirma que esté embebido en el VLF.


### Implementación y dependencias resueltas

- P74/P77: reglas puras en Core y validación en las transacciones de IDF;
  clasificación versionada, alturas enteras, capacidad y colisiones. Desbloquean
  P76/P78. Se conserva el import público de `rack.skins.appearance/span`.
- P76/P78: movimientos con revisión de inventario, destinos disponibles,
  dispositivos alojados sin reserva duplicada, rechazo de ciclos y de retirada
  de una bandeja/rack con contenido sin reubicar. Conversión explícita y atómica
  de bandejas dibujadas en el formato heredado. Desbloquean la edición P82.
- P82 (alcance LANRACK/LANWIRE): editor compartido de identidad, ubicación,
  puertos, conexiones y dimensiones; campos derivados y JSON siguen de lectura.
  Reflejo en ambas GUI y representación/edición de ocupación en TUI. La revisión
  transversal de las restantes interfaces de P82 queda separada de este alcance.
- P66: se conservan dimensiones y catálogo de frentes; ocupación unificada hasta
  52 U, sin permitir recortar equipos al reducir el armario.
- P88: selectores secundarios retirados de las GUI de los launchers; nombre
  informativo en el pie de los cinco y selección desde LANCTL. Se conserva la
  API anterior y el acceso coordinado a LANCTL. No se migra `physicalDatabase`
  al VLF. Falta reconstrucción/validación nativa de instalables para su entrega.

Conflicto estructural resuelto: el `layout` antiguo podía mantener un equipo en
su U anterior tras moverlo. La TUI usa ahora su ubicación real; los dibujos de
bandeja se convierten explícitamente, sin inventar identidades para dispositivos.

Pruebas nuevas: `test_physical_placement.py` y `test_physical_placement_gui.py`.
Verifican enlaces toma-panel, independencia, altura, solapamiento, concurrencia,
revisión obsoleta, bandejas, conversión, reapertura, CLI/TUI y las cinco GUI en
Edge sin ventanas visibles. Se actualiza una expectativa antigua que permitía
seleccionar proyecto en LANWIRE para reflejar el criterio actual de P88.


Revisión adicional de P88: los entrypoints de LANRACK, LANWIRE y LANACCESS
pasaban las rutas predeterminadas como overrides explícitos a la GUI. Esto
podía mantener un almacén anterior aunque cambiase el contexto. Se distingue
ahora un argumento explícito de un valor predeterminado, conservando los defaults
públicos de los parsers y el comportamiento CLI. Prueba de regresión por cada
entrypoint, con ruta predeterminada y explícita; LANACCESS incluye el almacén.

Se corrige también la actualización indiscriminada de `updated_at` al borrar un
registro físico: solo cambian las revisiones de los registros realmente afectados.
La regresión fuerza otra fecha para detectar el fallo sin depender del reloj.


Archivos de implementación de este bloque:

- `src/lanctl/core/physical_placement.py` (nuevo); `src/lanctl/apps/rack/service.py`,
  `skins.py`, `cli.py`; `src/lanctl/apps/wire/idf/database.py`, `gui_service.py`,
  `cli/main.py`, `tui/editor.py`, `tui/detail.py`.
- `src/lanctl/apps/suite/launcher_gui.py`, `gui_support.py` y
  `src/lanctl/apps/access/manager_cli.py` (arranque que sigue la selección global).
- `gui/physical-editor.js` (nuevo), `physical-gui.js`, `wire-gui.js`,
  `launcher.js`, `launcher.html`, `app.js`, `desktop.js`, `index.html`.
- `tests/test_physical_placement.py`, `test_physical_placement_gui.py` (nuevos);
  regresiones añadidas a `test_project_sync.py` y expectativas actualizadas en
  `test_launcher_gui.py` y `test_desktop_browser.py`.
- `packaging/clink/lanctl.lua`, referencias generadas CLI/web, `errorList.txt`,
  `docs/LAUNCHER-GUI.md`, este informe y `docs/BACKLOG.md`.

Se preservan los cambios previos del workspace. La validación corresponde a las
fuentes locales de `experimental-gui`; no implica una ejecución nueva de GitHub
Actions, integración en `main` ni actualización de los ejecutables instalados.


### Resultado final verificado — 18/10/2026

- Suite completa sobre el estado final, con navegador Edge habilitado y pruebas
  GUI históricas incluidas: **1.313 passed, 645 subtests passed, 1 skipped** en
  233,68 s. La omisión es `test_partial_ipc_frame_cannot_bypass_activation_timeout`,
  exclusiva de framing parcial de pipes POSIX; este host es Windows.
- Cobertura con `coverage run --branch --source=src`: **70,5093 %** combinada de
  líneas y ramas (74,1475 % de sentencias; 59,5925 % de ramas), supera el umbral
  existente del 60 % sin modificarlo.
- **283 firmas públicas conservadas**, sin firmas retiradas o cambiadas, frente a
  `7a60daac7ed4239d9202bd6a4b424a699fcd3a67`; se comprueban también los imports
  compatibles de las funciones trasladadas. Los archivos de contratos, eventos,
  funciones builtin y contratos UI de plugins del Core permanecen idénticos.
- Ruff y formato, sintaxis JavaScript, higiene, referencias CLI/web,
  `git diff --check` y catálogo de errores correctos; **1.467 puntos catalogados**.
  Bandit: cero hallazgos de gravedad media/alta y cero errores de análisis.
- Evidencia local ignorada por Git: `.tool-reports/rack-verified.log`,
  `rack-verified.xml`, `rack-verified.coverage`, `rack-verified-coverage.json`,
  `rack-verified-bandit.json`, `rack-contracts.json` y `physical-placement.png`.
  La ejecución `rack-verified` es la evidencia final; los intentos anteriores
  documentaron una expectativa GUI sustituida y el fallo de revisiones al borrar,
  ambos corregidos y comprobados en esta ejecución.

Pendiente: CI nueva de GitHub y reconstrucción/validación de los instalables;
P82 fuera de las vistas físicas conserva su revisión transversal. Siguiente tarea
GUI recomendada: P81. No se modifican los bloqueos de publicación estable ajenos
al alcance ni se publica una nueva versión desde estas pruebas locales.

## P81 · Validación y plan — 20/10/2026

Objetivo: simplificar el detalle de LANRACK y adaptar su escala visual al espacio
disponible, conservando las dimensiones físicas y la edición existente.
P66 y P74/P76–P78 ya aportan dimensiones, ocupación y bandejas; no hay una
dependencia de datos pendiente. GUI-DESIGN figura inactivo al comprobarlo.

- Archivos previstos: `gui/physical-gui.js`, `gui/rack-skins.js`,
  `gui/launcher.css`, pruebas de navegador de frentes y adaptación del rack.
- Dependencias directas: composición de `render`, detalle físico compartido y
  `rack-dimensions.js`. Indirectas: editor de bandejas, refresco de proyecto y
  estilos globales. Se conservarán los adaptadores y las acciones de edición.
- Riesgo **Medio**: altura disponible, solapamientos, frentes multi-U y controles
  en ventanas pequeñas. El ajuste tendrá un mínimo legible y desplazamiento
  vertical cuando todas las unidades no quepan; no alterará datos del inventario.
- Orden: cabecera compacta y navegación; escala automática sin deslizador;
  regresiones de redimensionado, preferencias anteriores y edición; suite
  completa y controles del repositorio; actualización del backlog.

Esta ejecución continúa en la rama de trabajo `experimental-gui`, conservando
los cambios previos. No modifica contratos Core, parsers ni formatos persistidos
de proyectos. P82 fuera de LANRACK/LANWIRE y la entrega compilada de P88 siguen
siendo tareas distintas.

### Implementación y regresiones P81

- Cabecera compacta con nombre, ocupación y navegación visible al desplazarse;
  la descripción completa permanece en la ficha. Retirado «Abrir LANWIRE»,
  conservados los controles de actualización, altas, dimensiones y edición.
- `ResizeObserver` ajusta la altura visual de las filas mediante CSS, sin
  reconstruir formularios ni tocar el inventario. Mínimo de 30 píxeles por U
  y desplazamiento vertical para racks altos; se conserva la proporción de
  los equipos multi-U y un rótulo de texto legible independiente del SVG.
- La preferencia anterior de vista simple/frentes sigue siendo válida. El
  tamaño manual anterior se ignora y deja de guardarse.
- Cambian `gui/physical-gui.js`, `gui/rack-skins.js`, `gui/launcher.css`,
  `tests/test_rack_skins.py`, el helper de `test_physical_placement_gui.py`,
  el nuevo `test_rack_responsive_gui.py` y la documentación de LANRACK.
- Nueve pruebas relacionadas pasan en Edge sin ventanas visibles. Después de
  fijar la cabecera se repiten las cuatro regresiones nuevas, también correctas:
  racks de 4/18/52 U, ventanas 800×600, 850×700, 1440×1000 y 1920×1080,
  extremos accesibles, varias U, vistas simple/frentes, datos sin cambios y
  edición con foco y valores pendientes conservados.
- Revisión visual local de `.tool-reports/p81-rack-small.png`, a 800×600:
  cabecera y controles accesibles, inventario desplazable y pie visible.

La simplificación elimina la dependencia del deslizador de P66. La revisión
transversal P82 requiere delimitar qué datos son editables en cada launcher y
coordinar sus ajustes con P69; no queda resuelta por la presentación del rack.

Hallazgo adicional registrado como P89: el editor de frentes conserva un máximo
de 8 U y una previsualización recortada a 8, frente a las 52 U válidas en Core.
Una reproducción independiente en Edge con inventario temporal confirma que
un equipo de 12 U abre con `value=12`, `max=8`, `rangeOverflow=true`.
Se antepone su corrección a la ampliación P82 porque afecta a datos existentes
válidos. Riesgo Medio; no es un cambio del esquema ni de la arquitectura.

### Cierre verificado P81

Suite completa con Edge y pruebas GUI históricas: **1.317 pruebas y 645
subpruebas correctas, una omisión POSIX en Windows**, en 245,10 s. Cobertura
combinada **70,5093 %**, sobre el umbral sin cambios del 60 %.
Ruff, formato de 496 archivos, sintaxis JS, higiene, referencias CLI/web,
catálogo de 1.467 errores y `git diff --check` correctos. Bandit sin hallazgos
medios/altos ni errores. Comparación AST frente a `7a60daa`: 260 funciones/métodos
públicos y 13 constructores conservados; tres imports compatibles y archivos
de contratos Core sin cambios. Evidencias: `.tool-reports/p81-verified.log`,
`p81-verified.xml`, `p81-verified.coverage`, `p81-coverage.json`,
`p81-contracts.json` y `p81-bandit.json`.

### P89 · Validación y plan

P81 terminado permite abordar el siguiente defecto comprobado. Objetivo:
editar frentes de equipos válidos de 9–52 U conservando la altura guardada.
Archivos: `gui/rack-skins.js` y `tests/test_rack_skins.py`. Dependencia directa:
`core.physical_placement.appearance`, cuyo rango 1–52 ya está validado y no se
modifica. Dependencias indirectas: capacidad del rack, colisiones y servicios
compartidos de guardado; no se duplicarán sus reglas en la GUI.
Riesgo **Medio**: alturas límite, SVG y datos existentes. Se comprobarán
previsualización, guardado/reapertura, límites y rechazo por falta de espacio,
conservando identidad, puertos y conexiones. Sin migraciones ni nuevas API.

### Implementación P89

El campo de altura y la previsualización de `gui/rack-skins.js` usan ahora el
rango existente 1–52 U. El guardado continúa pasando por el servicio compartido,
que valida espacio y ocupación; no se modifica ninguna regla ni API del Core.
Se añaden tres regresiones de navegador en `tests/test_rack_skins.py`, para
9, 12 y 52 U: frente completo, persistencia/reapertura, conservación de identidad,
puertos y cable real, rechazo de 0/53/1,5 U y de 19 U dentro de un rack de 18 U.
La prueba cierra el diálogo de error antes de corregir el dato y reintentar.

Pruebas relacionadas P81/P89 y ubicación compartida: **29 correctas** en
17,12 s (`.tool-reports/p89-targeted.log`). Los controles de formato, higiene,
referencias y catálogo siguen correctos.

### Resultado final combinado P81/P89 — 20/10/2026

- Suite completa, incluidas GUI históricas y Edge: **1.320 pruebas y 645
  subpruebas correctas**, una omisión, en **253,85 s**.
- Omisión: `test_partial_ipc_frame_cannot_bypass_activation_timeout`,
  «framing parcial de pipes POSIX», no aplicable a este host Windows.
- Cobertura combinada: **70,5093 %**, umbral del 60 % conservado.
- Ruff, formato (496 archivos), sintaxis JavaScript, higiene, referencias
  CLI/web, catálogo de 1.467 errores y `git diff --check` correctos.
  Bandit: cero hallazgos medios/altos y cero errores.
- Las firmas y los archivos de contratos Core revisados en P81 permanecen
  idénticos; P89 modifica únicamente dos límites de la GUI y sus regresiones.
  No se cambian parsers, IDs públicos ni formatos de datos.
- Evidencia final: `.tool-reports/p81-p89-final.log`, `p81-p89-final.xml`,
  `p81-p89-final.coverage`, `p81-p89-final-coverage.json` y
  `p81-p89-final-coverage.txt`. Sustituye los resultados intermedios para
  evaluar el estado combinado.

P81 y P89 quedan completados en fuentes. Siguiente tarea: validar y acotar P82
fuera de las vistas físicas, coordinando el ámbito de ajustes con P69.
Siguen pendientes CI de GitHub y reconstrucción/validación de instaladores;
este bloque no resuelve los bloqueos de plugins/firma ni declara una versión
estable. No se han actualizado los ejecutables instalados.

## P82 · Validación y plan — 20/10/2026

GUI-DESIGN sigue inactivo. Se conservan la rama y las modificaciones anteriores.
P76–P78, P81/P89 y la guarda de proyecto P88 están disponibles en fuentes.
P69 sigue abierto para el catálogo de preferencias: P82 no ampliará ese catálogo
ni concederá acceso a ajustes internos o administrativos.

| Orden | Objetivo y archivos | Dependencias | Riesgo e impacto |
|---|---|---|---|
| 1 · REF-P82-inventario | Extraer la operación de edición revisada de `ip/interfaces/gui/desktop.py` a `core/inventory_editing.py`, conservando el adaptador y el historial | `GroupDatabase.edit_device_fields`, locks y validación existentes | Alto: evitar dos reglas distintas en LANIP y LANMON |
| 2 | Ficha editable en LANMON: `monitor/gui_service.py`, `suite/launcher_gui.py`, `gui_support.py`, `gui/record-editors.js` y `launcher.html` | Paso 1 y guarda de proyecto P88 | Alto: rechazar revisiones obsoletas y grupos protegidos; conservar muestras, eventos e identidad |
| 3 | Ficha editable de LANACCESS: `access/credential_service.py`, `access/gui_service.py`, los mismos adaptadores y editor GUI | Locks/cifrado existentes y P88 | Alto: conservar contraseña al editar usuario; cambio de secreto explícito, revisión del almacén y bloqueo |
| 4 | Verificación transversal y backlog | Servicios reales, pruebas de navegador y suite completa | Medio: cancelación, guardado/reapertura, reflejo entre vistas y permisos remotos |

La extracción previa resuelve el acoplamiento de la edición a DesktopApi antes
de incorporarla a otra vista. No se traslada ni se elimina ninguna API pública.
Las nuevas operaciones serán aditivas, restringidas al launcher correspondiente
y al proyecto mostrado.

Matriz de alcance: LANRACK/LANWIRE ya tienen editor físico; LANIP tiene ficha de
datos y grupos; LANCTL tiene metadatos del proyecto y ajustes declarados de
plugins. LANACCESS carece de edición desde la ficha y exige reintroducir el
secreto incluso para cambiar usuario. LANMON muestra identidad/grupos sin editor.
Métricas, muestras, eventos, registros, JSON interno y recursos descubiertos de
plugins permanecen de lectura, salvo acciones expresamente declaradas.
Las CLI/TUI existentes de inventario y credenciales ya tienen comandos de
edición; la TUI de LANMON es una consola de eventos de lectura.

### Implementación y verificación relacionada P82

- REF-P82-inventario completado: `core/inventory_editing.py` centraliza la
  edición y revisión ya usadas por LANIP. `DesktopApi` mantiene firma, historial,
  revisión y respuesta; `GroupDatabase` conserva validación y transacción.
- LANMON incorpora ficha de nombre, alias, descripción, IP y pertenencia a
  grupos existentes. Rechaza campos internos, revisiones obsoletas y operaciones
  sobre grupos protegidos. Las observaciones y los datos del monitor conservan
  su condición de lectura; abrir la ficha no inicia sondeos.
- LANACCESS edita el usuario de la identidad existente conservando el secreto.
  La rotación exige contraseña y confirmación explícitas. El token de revisión
  se calcula sobre el cifrado; no se envía el secreto actual al navegador.
  Se mantienen bloqueo, identidad, enlace al inventario y métodos anteriores.
- Los RPC aditivos se restringen a su launcher y al contexto de proyecto P88.
  La lista de permisos remotos no cambia. `gui/record-editors.js` conserva
  selección y filtros, avisa si mantiene una fila fuera del filtro y descarta
  respuestas de fichas cerradas antes de actualizar otros diálogos.
- Archivos: `core/inventory_editing.py`, `apps/ip/interfaces/gui/desktop.py`,
  `apps/monitor/gui_service.py`, `apps/access/{credential_service,gui_service}.py`,
  `apps/suite/{launcher_gui,gui_support}.py`, `gui/record-editors.js`,
  `gui/launcher.{html,css}`, `tests/test_view_editing{,_gui}.py`,
  `tests/test_launcher_browser.py`, este informe, `BACKLOG.md`,
  `LAUNCHER-GUI.md` y catálogo de errores generado.
- **82 pruebas relacionadas correctas**, en 32,04 s:
  `.tool-reports/p82-targeted.log`. Incluyen servicios reales y navegador,
  edición LANMON↔LANIP, rechazo de escrituras parciales, dos editores simultáneos,
  guardado/reapertura del proyecto, grupos protegidos, bloqueo y rotación de
  credenciales, permisos remotos, cancelación, filtros, proyecto obsoleto y
  respuesta tardía después de cerrar la ficha.
- Revisión visual en Edge sin ventanas nativas: fichas de credencial y grupos
  legibles, sin secretos guardados ni campos internos editables. Evidencias
  `.tool-reports/p82-credential.png` y `p82-monitor-groups.png`.
- La primera suite completa detectó un doble de prueba antiguo que no ofrecía
  `monitor_device`: 1.343 pruebas correctas y un fallo en
  `test_real_launcher_views_and_action_arguments`. Se actualiza su respuesta
  simulada y se comprueban identidad, campos cargados y ausencia de diálogo de
  error, conservando las comprobaciones previas. El informe original queda en
  `.tool-reports/p82-first-suite.{log,xml}`; el cierre exige repetir la suite.

P69 conserva su alcance de preferencias y permisos de configuración. No bloquea
estas fichas de datos; el inventario y los permisos ya existen. P84/P85 pueden
reutilizar los editores compartidos, pero requieren sus propias validaciones de
altas y de interacción. La siguiente tarea visual disponible sigue siendo P83;
este cambio no declara una versión estable ni actualiza ejecutables instalados.

### Cierre verificado P82 — 20/10/2026

- Repetición focalizada tras actualizar el doble antiguo: **25 pruebas
  correctas**, 19,39 s (`.tool-reports/p82-browser-recheck.log`).
- Suite completa final, incluidas pruebas GUI históricas y Edge: **1.344 pruebas
  y 645 subpruebas correctas**, una omisión, **274,35 s**. Cero fallos/errores
  en JUnit. La omisión corresponde a
  `test_partial_ipc_frame_cannot_bypass_activation_timeout`, framing de pipes
  POSIX no aplicable al host Windows.
- Cobertura combinada **70,6906 %**; umbral del **60 %** conservado.
- Comparación AST con el árbol de trabajo anterior a P82: **1.292 firmas
  públicas** en **283 archivos**, sin cambios, eliminaciones ni archivos
  ausentes. Archivos de contratos, eventos, tareas del Core y permisos remotos
  sin cambios respecto a HEAD. Nuevas operaciones aditivas; sin cambios de
  parsers, IDs públicos o formatos persistentes.
- Ruff y formato de **499 archivos**, sintaxis de **20 scripts JavaScript**,
  compilación Python, dependencias instaladas, higiene, referencias CLI/web,
  catálogo de **1.476 errores** y `git diff --check` correctos. Bandit sin
  hallazgos medios/altos ni errores.
- Evidencias finales: `.tool-reports/p82-final.log`, `p82-final.xml`,
  `p82-final.coverage`, `p82-final-coverage.json`, `p82-final-coverage.txt`,
  `p82-contracts.json` y `p82-bandit.json`. Estos resultados sustituyen al primer
  intento para evaluar el estado final.

P82 y REF-P82-inventario completados en fuentes. Se actualiza el backlog:
P83 es la siguiente tarea visual disponible; P84/P85 pueden reutilizar la edición
compartida. P69 y los bloqueos de runtime/editor oficial conservan su alcance.
No se han generado ni instalado compilados ni ejecutado CI remoto sobre este
árbol; esa entrega sigue pendiente, al igual que la validación de Linux.

## P83 · Validación y plan — 21/10/2026

GUI-DESIGN permanece inactivo. Se conservan la rama `experimental-gui` y las
modificaciones previas. P82 y P88 están disponibles en fuentes; el pie ya
presenta proyecto y navegación. No hay dependencia pendiente que impida retirar
el reloj. P69 mantiene su revisión de preferencias fuera de este alcance.

| Orden | Objetivo y archivos | Dependencias | Riesgo e impacto |
|---|---|---|---|
| 1 | Retirar el reloj en `gui/launcher.html` y su actualización en `gui/launcher.js` | Plantilla común de LANWIRE/LANRACK/LANACCESS/LANMON y P88 | Bajo: conservar el refresco de datos de cinco segundos que comparte el temporizador |
| 2 | Alinear `gui/launcher-prototypes.{html,js}` | Presentación aislada, sin persistencia | Bajo: evitar relojes residuales; conservar horas ilustrativas de eventos |
| 3 | Verificar los seis launchers, arranques directos, refresco y pies adaptables; fechas de registros y eventos | LANCTL usa `suite.html`; LANIP usa `index.html`; servicios y navegación existentes P53/P75/P88 | Bajo: no cambiar permisos, contratos, datos ni relojes internos |
| 4 | Documentación y cierre P83 | Pruebas relacionadas, suite completa y controles del repositorio | Bajo: distinguir fuentes verificadas de entrega compilada |

LANCTL y LANIP ya carecen de reloj en el pie. Las marcas de tiempo de actividad,
incidencias, muestras y registros son datos de diagnóstico y se conservan.
No se modifican temporizadores del Core, parsers ni operaciones públicas.

### Implementación y pruebas relacionadas P83

- Se retira el elemento de reloj del pie de `launcher.html` y
  `launcher-prototypes.html`, y únicamente la asignación de hora actual en sus
  scripts. El refresco de datos de cinco segundos conserva su intervalo y
  guardas para no interrumpir formularios. No se modifican estilos ni navegación.
- LANCTL y LANIP ya cumplían la ausencia de reloj. Sus pies se verifican junto
  con los cuatro launchers que comparten plantilla, a 1440×900 y 800×600.
  LANIP conserva su desplazamiento vertical del documento en ventanas pequeñas.
- `tests/test_launcher_footers.py` añade ocho regresiones: seis aplicaciones
  con servicios reales, refresco posterior al antiguo intervalo del reloj,
  proyecto y accesos conservados; fechas de eventos, incidencias, actividad y
  logs, con persistencia intacta; cuatro arranques de los prototipos y horas de
  sus eventos ilustrativos conservadas.
- Reproducción previa: LANWIRE y el prototipo fallaban por encontrar el reloj
  en el pie (`.tool-reports/p83-before.log`). La validación ajusta dos supuestos
  del nuevo test: acceso por desplazamiento en LANIP y carga independiente de
  cada prototipo, sin introducir cambios adicionales de interfaz.
- **58 pruebas relacionadas correctas**, en **52,23 s**, incluidos arranques
  directos/enrutados, sincronización global de proyecto y controles compartidos.
  Evidencia: `.tool-reports/p83-targeted.log`.
- Comparación de **287 archivos**: todos los fuentes Python y los componentes
  de fechas de LANIP, LANCTL y registros de LANMON conservan sus bytes. No se
  modifican contratos, permisos, formatos persistentes ni puntos de error;
  el catálogo de **1.476 errores** sigue vigente. Evidencia:
  `.tool-reports/p83-contracts.json`.
- Capturas reproducibles de los seis pies:
  `.tool-reports/p83-{lanctl,lanip,lanwire,lanrack,lanaccess,lanmon}-footer.png`.
  La comprobación de sintaxis de los 20 scripts JavaScript, Ruff/formato de
  500 archivos, referencias CLI/web, higiene y diff pasa. Bandit sin hallazgos
  medios/altos ni errores.

P84 es la siguiente tarea de esta secuencia, con la edición P82 y la guarda P88
ya disponibles. La entrega compilada y la verificación remota siguen separadas.

La primera suite completa termina con 1.351 pruebas correctas y un falso
positivo en `test_error_event_redacts_secrets_embedded_in_messages_and_values`:
el UUID aleatorio de correlación contenía `abc`, igual que el secreto breve de
prueba. Mensaje y detalles estaban correctamente redactados. Se hace
determinista únicamente ese UUID en `tests/test_errors.py`, conservando todas
las aserciones sobre secretos y sin modificar el servicio de errores. Evidencia
original: `.tool-reports/p83-first-suite.{log,xml}`. Se repite la suite completa
antes del cierre; este resultado no se considera una verificación correcta.

### Cierre verificado P83 — 21/10/2026

- Pruebas de errores y pies tras fijar el UUID: **26 correctas**, 12,45 s
  (`.tool-reports/p83-security-recheck.log`).
- Suite completa final, incluidas GUI históricas y navegador Edge: **1.352
  pruebas y 645 subpruebas correctas**, **296,51 s**, una omisión POSIX en
  Windows (`test_partial_ipc_frame_cannot_bypass_activation_timeout`).
  JUnit confirma cero errores y cero fallos.
- Cobertura combinada **70,6906 %**, idéntica a P82; se conserva el umbral del
  **60 %**. No se excluyen pruebas ni se rebajan comprobaciones.
- Ruff y formato de **500 archivos**, sintaxis de **20 scripts JavaScript**,
  referencias CLI/web, higiene y `git diff --check` correctos. El catálogo de
  **1.476 errores** sigue vigente; no se han modificado puntos de error del
  programa. Bandit: cero hallazgos medios/altos y cero errores.
- Revisión visual de los seis pies a 800×600, con proyecto y navegación
  conservados. La comparación de **287 archivos** confirma que todos los
  fuentes Python y los componentes de fechas examinados permanecen intactos.
- Evidencia final: `.tool-reports/p83-final.log`, `p83-final.xml`,
  `p83-final.coverage`, `p83-final-coverage.json`, `p83-final-coverage.txt`,
  `p83-contracts.json`, `p83-bandit.json` y las seis capturas del pie.

P83 completado en fuentes y backlog actualizado. Siguiente tarea visual: P84.
P69 y los bloqueos previos conservan su estado. No se han ejecutado CI remoto ni
compilación/instalación; estas fuentes requieren una entrega nueva y validación
de las plataformas de distribución antes de declarar una versión estable.

## P84 — validación y plan previo, 21/10/2026

Objetivo: completar las altas de LANWIRE desde el proyecto activo, con acciones
visibles para cable, rack y CPD, y conservar los tipos físicos existentes.
P81/P89 aportan el formulario CPD y dimensiones; P82 aporta edición compartida;
P88 aporta el contexto de proyecto y rechazo de formularios obsoletos. Están
disponibles en fuentes. GUI-DESIGN está inactivo; no se modifica su asistente.

| Orden | Módulos y archivos | Dependencias e impacto | Riesgo |
| --- | --- | --- | --- |
| 1 | `apps/wire/gui_service.py`, `apps/suite/launcher_gui.py`, `gui_support.py` | Reutilizar organización CPD y validación de extremos. Alta y conexión del cable en una única escritura bajo el bloqueo compartido. RPC CPD aditiva, exclusiva de LANWIRE y con guarda P88; mantener RPC LANRACK y permisos remotos. | Medio |
| 2 | `gui/wire-gui.js`, `physical-gui.js`, `physical-editor.js` | Acciones explícitas y formulario CPD común; extremos opcionales en altas de cables; mantener edición P82, cancelación y refresco compartido. Sin selector de proyecto. | Medio |
| 3 | `tests/test_wire_creation.py`, `test_wire_creation_gui.py` | Servicios reales y Edge sin ventanas: proyecto vacío/con datos, medios y puertos, rechazo atómico, permisos, cambio de proyecto, cancelación, feedback y guardar/reabrir. | Bajo |
| 4 | `docs/LAUNCHER-GUI.md`, backlog y catálogo generado | Suite completa, compatibilidad pública, referencias e higiene; separar cierre en fuentes de entrega compilada. | Bajo |

En la inspección inicial no se detectó el bloqueo de persistencia que reveló
después la prueba de reapertura descrita abajo. Los perfiles
existentes cubren switches, routers/OTG, ordenadores, servidores, bandejas,
paneles, tomas, cables y racks; no se introducen tipos de inventario nuevos.
El alta antigua de cable sin extremos sigue siendo válida. No cambian parsers,
formatos persistentes ni identificadores públicos del Core.

## REF-P84 — bloqueo estructural confirmado, 21/10/2026

**P84 no completado.** La ampliación de la interfaz se detiene por la regla
del usuario: ante un problema estructural importante, detener la tarea,
crear la refactorización previa y reordenar prioridades. Se retiran únicamente
los cambios parciales de producción y sus pruebas experimentales introducidos
en esta sesión, conservando todos los cambios anteriores del workspace.

La prueba real de guardado y cambio de proyecto muestra que:

1. `activate_project_workspace` cambia dispositivos y grupos lógicos, pero
   deja `physicalDatabase` apuntando a la misma base global. El pie indica
   Second y las vistas físicas siguen mostrando los datos de First.
2. Los hashes del workspace y la política de guardado no contemplan la base
   física. Crear un rack, cable conectado y CPD mantiene `dirty=False`.
3. `create_project`/`update_project` guardan el inventario lógico y conservan
   el documento de topología previo, pero no incorporan la base IDF activa.
   Guardar y reabrir con una ruta física nueva devuelve un inventario vacío.
   El archivo global original no se elimina: la pérdida es de persistencia
   y recuperación **a través del VLF**, no un borrado demostrado de ese archivo.

**Gravedad Alta.** Puede atribuir datos físicos al proyecto equivocado, permitir
ediciones sobre ese inventario compartido accidentalmente y ofrecer un VLF
que no restaura todos los datos visibles. Afecta LANWIRE y LANRACK, además de
los flujos CLI/TUI que utilizan las mismas rutas. P88 sí protege la identidad
de una operación, pero esa guarda no sustituye al aislamiento de su almacén.

### Plan previo de la dependencia

| Orden | Objetivo y archivos a revisar | Dependencias / impacto | Riesgo |
| --- | --- | --- | --- |
| 1 | Definir persistencia física compatible: `core/projects/vlf.py`, adaptador IDF y documentación del formato | Decidir una representación versionada que conserve todos los registros, metadatos y CPD; validar VLF antiguos, corruptos y de versiones posteriores | Alto |
| 2 | Aislar rutas/materialización: `core/projects/workspace.py`, configuración y rutas | Depende del formato; preservar la base histórica y no importarla automáticamente en proyectos sin identidad de origen; conservar constructores y APIs públicas | Alto |
| 3 | Incluir estado físico en guardado: `fingerprint.py`, `save_policy.py` | Depende del aislamiento; bloqueo coherente entre snapshot/escritura/verificación, cambios pendientes, backups y reapertura sin pérdida | Alto |
| 4 | Verificar clientes compartidos: adaptadores suite, LANWIRE/LANRACK, CLI/TUI y pruebas de proyecto | Reutilizar P88 y permisos existentes; concurrencia entre ventanas, formularios obsoletos, proyecto vacío y con datos | Medio |
| 5 | Retomar P84 y después P85 | Solo tras pasar los tres invariantes y suite completa; creación explícita de cable/rack/CPD y alta atómica de extremos | Medio |

No se ha implementado esta refactorización ni cambiado el formato VLF en esta
sesión. Las decisiones de migración y compatibilidad deben quedar concretadas
antes de modificar el almacenamiento. P69 y los bloqueos previos de plugins
mantienen su alcance; esta dependencia precede a nuevas altas visuales.

### Evidencia reproducible

`tests/test_physical_project_persistence.py` usa proyectos temporales y APIs
existentes, con rack, CPD, equipo y cable conectado reales. Sus tres invariantes
se reproducen con:

```text
.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_physical_project_persistence.py --runxfail -q
```

Resultado inicial: **3 fallos reproducidos**, en las comprobaciones de cambios
pendientes, aislamiento y recuperación. Evidencia:
`.tool-reports/p84-storage-reproduction.log`. Se registran como `xfail(strict=True)`
con una excepción exclusiva del invariante conocido: fallos de preparación o
de APIs no quedan ocultos por la marca. Una corrección hará fallar la suite por
`XPASS` hasta retirar la marca; los tres casos **no cuentan como pruebas correctas**.

Se confirma por SHA-256 que los **284 archivos Python de producción** conservan
sus bytes previos a P84 tras retirar el cambio parcial. No se cambian permisos,
RPC, parsers ni identidades públicas. Los resultados experimentales
`p84-before.log` y `p84-services.log` no acreditan una implementación entregada.

Las pruebas relacionadas pasan: **49 correctas y 3 fallos conocidos**, 18,70 s
(`.tool-reports/p84-targeted.log`). La reproducción explícita con `--runxfail`
confirma los tres fallos en 2,42 s. Ruff/formato de 501 archivos, catálogo de
1.476 errores, referencias CLI/web, higiene y diff correctos.

La primera suite completa obtiene 1.351 pruebas y 645 subpruebas correctas,
una omisión POSIX, tres fallos conocidos REF-P84 y un fallo inesperado en
`test_secret_input_uses_the_tui_prompt_and_never_echoes_characters`. Esa prueba
simulaba caracteres Windows pero consultaba el estado real de Control: el
retroceso se interpretaba como `CTRL_H` según el teclado del escritorio.
Se fija únicamente `windows_control_pressed=False` dentro de esa prueba,
conservando todas las aserciones de edición y ausencia de eco. No se modifica
el lector de secretos ni el comportamiento del programa.

Evidencia inicial: `.tool-reports/p84-first-suite.{log,xml,coverage}`.
Verificación TUI posterior: **83 pruebas y 19 subpruebas correctas**, 3 fallos
conocidos REF-P84, 3,28 s (`p84-tui-recheck.log`). Se repite la suite completa;
la primera ejecución no se considera una validación correcta.

### Cierre de la revisión P84 — 21/10/2026

- Suite completa final, con GUI históricas y Edge: **1.352 pruebas y 645
  subpruebas correctas**, **315,35 s**, una omisión POSIX en Windows y **tres
  fallos conocidos REF-P84 (`xfail`)**. JUnit confirma cero fallos inesperados
  y cero errores. No se presentan esos tres casos como corregidos.
- Cobertura combinada **70,6798 %**, umbral del 60 % conservado. Evidencia:
  `.tool-reports/p84-final.{log,xml,coverage}`, `p84-final-coverage.json` y
  `p84-final-coverage.txt`.
- Ruff y formato de **501 archivos**, catálogo de **1.476 errores**, referencias
  CLI/web, higiene y diff correctos. Comparación SHA-256 final: los **284
  archivos Python de producción** conservan sus bytes. Se verifican **1.225
  firmas públicas** sin diferencias (`p84-contracts.json`).
- Cambios conservados de esta sesión: nuevo archivo de reproducciones
  `tests/test_physical_project_persistence.py`, aislamiento del estado del
  teclado en `tests/test_tui.py`, y actualización de `BACKLOG.md`, este informe,
  `KNOWN-ISSUES.md` y `LAUNCHER-GUI.md`. Ningún cambio de producción, permisos,
  contratos públicos, datos de usuario ni interfaz de GUI-DESIGN.

**Estado final: P84 bloqueado, no implementado. Siguiente tarea: REF-P84.**
Tras resolver y verificar esa dependencia se retoman las acciones de alta de
cables, racks y CPD en LANWIRE, seguidas por P85. No se ha compilado, instalado,
publicado ni ejecutado CI remoto, y no se declara una nueva versión estable.

## Reanudación del backlog — REF-P84, 21/10/2026

El usuario solicita continuar todas las correcciones pendientes. Se ejecutan
por dependencias, empezando por REF-P84; siguen P84–P87, diagnóstico P79/P80 y
los demás puntos disponibles. Las certificaciones de distribución y P40/P42
no se dan por resueltas sin entorno/evidencia o editor oficial autorizado.
GUI-DESIGN permanece inactivo; se conservan sus cambios existentes.

Plan concreto REF-P84 (riesgo Alto): añadir una entrada opcional versionada
`devices/physical.json` al VLF 1.0, manteniendo sus entradas obligatorias y APIs;
materializar `physical/idf.db` en cada workspace; incluir todo el documento IDF,
CPD y metadatos en huellas, locks, guardado y verificación posterior. VLF antiguos
sin entrada física abren un inventario vacío, sin adjudicarles la base global.
La base global histórica permanece intacta y su ruta se conserva para una
importación explícita. La migración no se ejecuta sobre datos reales durante
el desarrollo. Se pregunta al usuario por la preferencia de asociación.

Archivos previstos: nuevo adaptador `core/projects/physical.py`, `workspace.py`,
`save_policy.py`, `vlf.py`, configuración, pruebas de persistencia/compatibilidad
y documentación. Se reutilizan los validadores de dominio IDF/CPD; no se
introduce una segunda base ni reglas propias de GUI. Se comprueba aislamiento,
guardar/reabrir, corrupción, proyectos antiguos, inventario histórico intacto,
concurrencia y detección de cambios. Las tres regresiones REF-P84 deben pasar
sin `xfail` antes de desbloquear P84.

REF-P84 implementado en fuentes: las tres regresiones originales pasan sin
`xfail`; 14 pruebas específicas cubren además importación local explícita,
base histórica intacta, rechazo remoto, esquemas inválidos, corrupción sin
sobrescribir el VLF, proyecto nuevo vacío, migración de workspace antiguo con
cambios lógicos y escritura concurrente que continúa pendiente tras guardar.
El bloque previo de compatibilidad pasa 81 pruebas y 6 subpruebas (una omisión
POSIX y una GUI histórica deseleccionada en ese corte). Se realizará la suite
completa con navegador al cerrar este ciclo. P84 queda desbloqueado en fuentes.

La migración conservadora no importa automáticamente la base global. Su ruta
queda en `legacyPhysicalDatabase`; `project import-physical ARCHIVO.db` copia
solo a un proyecto vacío seleccionado explícitamente y deja el original intacto.
El comando se rechaza en remoto. CLI/web y Clink se actualizan para el comando
aditivo. Las firmas públicas existentes y el formato obligatorio VLF 1.0 se
conservan; `devices/physical.json` es una extensión opcional con esquema 1.

### Plan P85–P87 antes de modificar la topología

P85 depende de los editores P82, disponibles. El doble clic actual de equipos
ya abre datos en fuentes; se verificará con tipos reales y se homogeneizará
también para racks. Se conservan las acciones por clic derecho y la navegación
por controles de nivel. Archivos: `gui/physical-gui.js`, pruebas de navegador.
Riesgo Bajo; no cambia el inventario.

P86 reutiliza el dibujo de enlaces y añade `wirePrefs.cableLabels`, que hereda
la preferencia antigua hasta la primera elección explícita, sin ocultar los
identificadores de equipos. Añadir
alternancia explícita en la barra de topología con estado accesible, sin
relanzar layout ni cambiar datos. Archivos: `gui/physical-gui.js`, pruebas.
Riesgo Bajo; se conservan zoom, selección, posiciones y preferencias.

P87 depende de la interacción P85. Reducir el área de tomas de dos puertos
a aproximadamente una cuarta parte, manteniendo texto y puertos; usar una
única geometría para layout, hit-test, límites y anclajes DOM. Archivos:
`gui/physical-gui.js`, `gui/launcher.css`, pruebas de navegador. Riesgo Medio
por selección y cableado; verificar varias tomas, zoom y conexiones.

P84 pasa **28 pruebas** de servicios y navegador real (13,45 s): alta CPD/rack/
equipos/cable conectado, cancelación, edición CPD, feedback LANRACK y VLF reabierto;
ocho rechazos atómicos de extremos, contención por un puerto y guardas de launcher/
proyecto. Dos tests antiguos asumían base global al seleccionar un VLF: se
actualizan para exigir aislamiento y guardado antes del cambio, conservando
sus comprobaciones de edición/conexiones. Evidencia: `p84-creation.log`.
## P79/P80: validación y plan de corrección — 21/10/2026

Los registros locales confirman tres `KeyError('idf')` el 18/10 y el rechazo
de descarte compartido. No contienen traza de pila. La revisión localiza una
causa reproducible: el historial GUI acepta IP/IDF, pero `_edit_label` carece
de esas claves y deshacer/rehacer las omite. Esto afecta a edición, refresco,
finalización del escaneo y respuesta de guardado. P79 (riesgo medio) ampliará
las etiquetas y la restauración de campos, protegiendo lectura/verificación/
escritura con los locks existentes. Archivos: GUI `main.py`, pruebas de
regresión y catálogo. También se verificará la columna IDF inactiva en
`core/output.py`, cuya paleta está incompleta; es un defecto separado.

P80 (riesgo alto por datos compartidos) depende de P79 para verificar la
respuesta de guardado. El cierre con descarte debe conservar el workspace si
otra sesión lo utiliza, cerrar solo esta ventana y explicar ese alcance antes
de confirmar. Un descarte exclusivo restaura el VLF. Se reutilizarán el
coordinador, los locks y la protección existente contra recargas destructivas;
no se relajará el cambio de proyecto. Archivos: `projects/workspace.py`,
GUI `desktop.py`, `gui/desktop.js` y pruebas de sesiones/cierre. Guardar debe
persistir y verificar; cancelar o fallar no debe cerrar la ventana.

## P70: validación y plan — 21/10/2026

P70 no depende de la reorganización completa P71. La selección `monitor`
solo pertenece a `monitor custom`; el motor no necesita cambios. Riesgo bajo:
modificar exclusivamente `packaging/inno/LANCTL.iss`, ampliar el texto e
incluir Standard. La explicación se ajustará al ancho y reservará su altura
medida para evitar solaparse con componentes o espacio en disco. Referencia
de API: https://jrsoftware.org/ishelp/topic_scriptclasses.htm (`TNewStaticText`,
`WordWrap`, `AdjustHeight`). Comprobar selección declarada y compilar con Inno;
la comprobación visual nativa sigue separada del chequeo de compilación.

## P73: validación y plan — 21/10/2026

Los seis ejecutables Windows declaran `console=True`; ocultar su ventana una
vez arrancados no elimina el parpadeo. Mantenerlos conserva CLI/TUI, pipes y
códigos de salida. P73 añadirá un host gráfico Windows (`lanctl-window.exe`)
con lista cerrada de los seis launchers y primer escaneo opcional de LANIP.
Los accesos GUI de Setup y la apertura de GUI desde otra GUI usarán ese host.
No se cerrará ni ocultará una consola ya abierta. Riesgo medio, dependencias:
PyInstaller, bootstrap existentes, singleton/contexto P88 y empaquetado
Windows/portable. Archivos: nuevo adaptador `bootstrap/gui.py`, entrada
PyInstaller, `LANCTL.spec`, `suite/processes.py`, Setup/build y pruebas.
Los errores de arranque conservarán diagnóstico y notificación visible cuando
no exista consola. La certificación nativa de instalables sigue en P32/P73.

## Resultado del ciclo y revisión de dependencias — 21/10/2026

- REF-P84/P84: adaptador `projects/physical.py`, workspace/guardado/VLF y
  configuración, importación CLI y Clink, servicios LANWIRE y acciones GUI.
  17 regresiones físicas incluyen las tres reproducciones anteriores, migración
  explícita, corrupción, concurrencia, pérdida del archivo sin recreación vacía
  y `automatic.allChanges` desde GUI. La base antigua real no se ha tocado.
- P79: reproducción `KeyError('idf')` y `KeyError('ip')` al consultar historial;
  etiquetas y deshacer/rehacer corregidos en GUI `main.py`. La prueba conserva
  datos a través de escaneo/guardado/reapertura. Paleta inactiva IDF corregida
  en `core/output.py` con variantes de ancho y color. 42 pruebas relacionadas.
- P80: coordinación en `projects/workspace.py`, cierre GUI y decisión en
  `save_policy.py`; nueve combinaciones de cierre, fallo de guardado y aviso
  de alcance compartido en navegador. No se elimina la protección contra
  sustituir un workspace usado por otra sesión.
- P85/P86/P87: `physical-gui.js`, `physical-editor.js`, CSS y regresión con API
  real; doble clic directo, navegación explícita al interior, nombres de cables
  independientes y tomas de 120×64 con puertos/anclajes verificados a varios zoom.
- P70/P73: Setup, host `bootstrap/gui.py`, entrada de empaquetado, spec,
  `suite/processes.py` y script Windows. 47 pruebas relacionadas; PyInstaller
  compila el host, PE confirma subsistema GUI 2 frente a consola 3. Inno compila
  con código 0. Artefacto **solo de comprobación estructural**: contiene seis
  ejecutables anteriores y el host nuevo, no una entrega validada de las siete
  aplicaciones. No se ha instalado ni ejecutado el recorrido elevado.

La primera suite de este ciclo obtuvo 1.391 correctas, 648 subpruebas, una
omisión POSIX y dos expectativas antiguas: doble clic que navegaba al interior
y cambio de proyecto ignorando cambios físicos. Las pruebas se actualizan al
contrato pedido; la segunda incluso reutiliza el mismo ID en otro proyecto y
comprueba que el formulario viejo no cambia ninguno de los dos racks. Ambas
regresiones pasan. Un chequeo posterior detectó la referencia a la ruta física
omitida en README portable; restaurada su explicación, pasan las 15 pruebas de
distribución. No se omiten ni se marcan xfail estos casos.

Contratos: 1.225 firmas públicas anteriores conservadas, 13 firmas aditivas;
CLI y web regeneradas para `project import-physical`, catálogo 1.494 puntos.
Ruff/formato, sintaxis de todos los JS, Bandit, pip check e higiene correctos;
pip-audit no detecta vulnerabilidades. El cotejo de firmas no sustituye las
pruebas de comportamiento de permisos, proyecto compartido y formatos.

GitHub consultado el 21/10: el último workflow publicado de experimental-gui
es [39052546460](https://github.com/CctrGy/LANCTL/actions/runs/39052546460),
correcto sobre `4ca563d`; el fallo previo `39051944590` queda antes de ese
resultado correcto. El conector no devuelve ejecuciones de PR para el HEAD
local `581c5a3`. Esto no certifica los cambios locales sin publicar. Se
conserva por separado la evidencia multiplataforma `39071434470` del ciclo
anterior sobre `7a60daa`; no se atribuye a las fuentes de este ciclo.

P69 detenido antes de alterar el guardado tras detectar acoplamiento entre
adaptadores y parser CLI: creada REF-P69-settings con plan, riesgo y pruebas
requeridas. P34/P40/P42/P47/P50 y P71/P72 conservan las dependencias explícitas
del resumen vigente del backlog. La próxima versión estable sigue pendiente.

Revisión final de P80: también se prueba un workspace en raíz personalizada y
un fallo del cierre nativo, que conserva la siguiente confirmación. 27 pruebas
de cierre/desktop pasan. Tras añadir ese punto de error se regeneraron de nuevo
catálogo y referencia web; las 22 comprobaciones de referencias/distribución
pasan. Se inicia la suite integral definitiva con esas fuentes congeladas.

La revisión de políticas físicas descubre una integración todavía pendiente:
CLI/TUI de LANWIRE/LANRACK guardan el workspace pero no llaman a SavePolicy.
Se registra REF-P84-save-modes (Alta) para resolverlo en un límite compartido
de mutación, sin introducir inversión de locks desde callbacks de escritura.
El guardado explícito VLF y el automático de las GUI están comprobados; no se
extrapola esa garantía a todas las interfaces.

### Corrección de la responsabilidad del cierre P80

La revisión detectó una carrera adicional: después de que la GUI resolviera
guardar o descartar, el `finally` de CLI podía ejecutar de nuevo el guardado
sobre un proyecto diferente seleccionado entretanto. Se interrumpió la tercera
ejecución integral para corregirlo; ese intento no cuenta como suite superada.
`apps/ip/interfaces/cli/main.py` deja el cierre a la GUI cuando delega en ella,
pero mantiene la parada del temporizador. `desktop.py` no deja una respuesta
global pendiente para otra sesión. Se conservan los cierres CLI/TUI.

Las regresiones ejecutan `main(["--gui"])`, resuelven el cierre, activan un
segundo proyecto y dejan un cambio sin guardar en él. Ambas decisiones mantienen
ese cambio pendiente y el inventario guardado intacto. Con los casos de raíz
personalizada, errores nativos y políticas de guardado pasan 40 pruebas
relacionadas. Catálogo y referencias se regeneran después de esta corrección;
la siguiente ejecución completa utiliza esas fuentes sin modificaciones.
