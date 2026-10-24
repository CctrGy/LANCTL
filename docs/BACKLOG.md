# Trabajo pendiente de LANCTL

## Estado vigente — 22/10/2026, cierre de P69

Esta sección prevalece sobre los resultados históricos de ciclos anteriores.
No se ha publicado ni instalado una versión estable nueva.

| Estado | Entradas | Verificación / dependencia pendiente |
| --- | --- | --- |
| Corregidas en fuentes | REF-P84, P84, P79, P80, P86, P87 | Inventario físico por proyecto y VLF; creación LANWIRE; historial IDF/IP; cierre compartido; etiquetas y tomas. Regresiones de servicios y navegador real. |
| Implementada y verificada | REF-P34-runtime | API de proceso v2 optativa, revocación por generación, terminación confirmada y bloqueo ante cierre fallido. Pruebas con procesos reales y ejecutable de comprobación. Mantiene la compatibilidad v1/trusted. |
| Implementadas y verificadas | REF-P84-save-modes; REF-P84-session | Cambios físicos y ciclo de vida CLI/TUI: cierre, cancelación, temporizador y renovación de servicios. VLF guardado en su contexto de origen; base explícita fija; errores y commits parciales conservados. GUI mantiene su propietario independiente. |
| Implementadas; falta certificación nativa/entrega | P70, P73, P85, P75, P88 | Texto/selección del servicio y host GUI sin consola compilados; doble clic y selección compartida verificados en fuentes. El instalable anterior no se ha sustituido. |
| Implementadas y verificadas | REF-P69-settings; REF-P69-remote-lifecycle | Validación/autorización común y recuperación duradera del backend remoto, confirmación de propietario/revisión, parada y cambio de ámbito. Fallos persistentes conservan una reparación pendiente explícita, sin éxito falso. |
| Implementada y verificada | P69 | Preferencias filtradas por interfaz y launcher en consulta y guardado; campos internos ocultos, valores persistentes conservados, CLI compatible y LANWIRE TUI independiente. Sin cambios visuales de GUI-DESIGN. |
| Refactorización previa necesaria | REF-P34-migration → P34 | Adaptar plugins heredados y consolidar confirmaciones entre propietarios. El nuevo runtime no migra ni firma los paquetes existentes. |
| Desarrollo pendiente tras dependencias | REF-P47-interface/P47; REF-P50-session/P50; P71; P72 | Origen TCP/descubridores; snapshot de sesión viva y MCP; cinco páginas; inventario seguro de recursos y desinstalación completa. P71 tiene resueltos el ciclo remoto y la política de preferencias P69. |
| Bloqueo externo confirmado | P40/P42 | No hay editor oficial configurado ni paquetes firmados autorizados. Se mantiene el rechazo de trusted sin firma/confianza. |
| Certificación externa pendiente | P32, parte de P47/P48 y revisión visual nativa | CI de estas fuentes, Windows instalado/portable, Linux, SSH externo, varias NIC y desinstalación con otra cuenta. No equivale a pruebas unitarias ni a compilación. |

Verificación integral de este corte: **1.691 pruebas y 1.008 subpruebas correctas,
una omisión específica POSIX en Windows, cero fallos**. Cobertura con ramas:
**72,4941 %**, superior al umbral de 60 %. **56 regresiones nuevas** de P69,
con 360 subcasos de matriz, incluidas en la integral de 463,94 s. Ruff/formato,
Bandit según CI, pip check/pip-audit, catálogo de 1.623 puntos, referencias e higiene correctos.
Las **1.243 firmas públicas anteriores se conservan idénticas**; dos adiciones,
ninguna retirada. Se mantienen IDs y formatos públicos, opciones CLI y controles
de autorización. No cambia ningún recurso visual de GUI-DESIGN ni la configuración
local del usuario. Los catálogos de usuario omiten los campos ajenos/internos;
los valores almacenados y las rutas locales CLI explícitas se conservan. Evidencia y límites en
[BACKLOG-VERIFICATION.md](BACKLOG-VERIFICATION.md). La versión continúa siendo
`0.3.4-alpha.1`; esto no certifica una nueva entrega estable.

Siguiente prioridad disponible: **REF-P34-migration**, adaptación de los plugins
heredados y consolidación de su estado entre propietarios. P69, REF-P69-settings y
REF-P69-remote-lifecycle quedan cerradas en fuentes; falta certificar el servicio
instalado/portable, Linux con su cuenta real y SSH externo, además de CI remoto.
La recuperación conserva el diagnóstico y bloquea otra modificación remota si
no consigue compensar un fallo persistente. REF-P84-session
cierra la dependencia de ciclo de vida de las consolas físicas y permite su
validación integrada de distribución con P84/P88; esa certificación sigue pendiente.
REF-P34-runtime satisface la dependencia técnica
de REF-P34-migration; P34 permanece abierto hasta adaptar los paquetes y
consolidar su estado global. P50 conserva su dependencia REF-P50-session.
Los planes pendientes están en la lista de refactorizaciones; requieren
implementación, no solo certificación.
La base física histórica se conserva aparte e importa solo por acción explícita,
conforme a la respuesta del usuario; no se han migrado datos reales.

## Revisión de pendientes solicitada — 17/10/2026, segundo ciclo

Se vuelve a comprobar toda la lista, incluidas las entradas implementadas que
esperan el cierre de GUI-DESIGN. No se inicia una segunda compilación durante
su validación. El usuario confirma que **todavía no existe un editor oficial
configurado**: P40/P42 siguen requiriendo identidad y firma autorizadas.

| Orden | Objetivo / alcance | Archivos previstos | Dependencias e impacto | Riesgo |
| --- | --- | --- | --- | --- |
| 1 | P34: comprobar autorización vigente en cada acceso al Core, invalidar referencias antiguas, propagar revocaciones y separar limpieza de locks. Exponer los límites del runtime trusted heredado. | `core/plugins/manager.py`, `api.py`, nuevo servicio de autorización y regresiones de plugins. | Esperar cierre del build en curso; conservar firmas públicas y autorización explícita. Hilos nativos heredados requieren una migración de runtime, nunca declarar su terminación por quitar callbacks. | Crítico |
| 2 | REF-P47-interface/P47: enumerar redes reales y vincular las sondas a un origen seleccionado. | Servicios de descubrimiento, `core/first_scan.py`, CLI de escaneo y regresiones; adaptador visual coordinado. | Contrato de selección explícita, máscara real, rechazo de interfaz desaparecida; ninguna sonda previa a confirmar. | Alto |
| 3 | P50: contrato de consulta de sesión viva, revisión y datos sin guardar antes del transporte externo. | `core/session.py`, servicios de consulta y adaptador MCP; pruebas de contexto y redacción. | Contexto explícito, revocación y autenticación. La disponibilidad en ChatGPT exige conexión externa real; no se confunde una prueba local con esa certificación. | Alto |
| 4 | P67/P68: comparar Coverage 7.10.6/7.16.2 y Ruff 0.16.2/0.17.0 con Python 3.10 y umbral 60 %. | `pyproject.toml`, documentación de herramientas; entornos de evaluación locales. | Evaluación aislada durante build; suite con ambas versiones sobre las mismas fuentes cuando quede libre. No fusionar PR ni publicar ramas estables. | Medio |
| 5 | P45/P46/P48/P32: contrastar instalación, portable, completado y plataformas con evidencia real. | Empaquetado y pruebas de distribución. | Artefactos de GUI-DESIGN, CMD/Clink y entornos disponibles. Firmas, Linux ARM64 o SSH no disponibles no se certifican. | Alto |

P35/P49/P51/P52/P53/P54 y P66 «Dimensiones» tienen implementación compartida;
su cierre se contrastará con el resultado integral y los artefactos del primer
ciclo. Las decisiones y resultados de este segundo ciclo se añaden a la matriz
de verificación, conservando el historial anterior.

Resultado del segundo ciclo (fuentes): mitigaciones de P34 aplicadas y verificadas
con 119 pruebas; P47 incorpora máscara real y origen ICMP/ARP, con 132 pruebas
y 10 subpruebas. Integración visual P34/P47 aplicada por GUI-DESIGN. P68 revisada:
Ruff 0.17.0 pasa lint/formato y queda fijado en `pyproject.toml`; P67 supera la
comparación integral y fija Coverage 7.16.2. No cambian IDs públicos
ni versión de LANCTL. Los detalles y límites figuran en la matriz de verificación.
P69–P73 fueron incorporadas desde HELP durante este ciclo por peticiones de
anotación. La creación inicial de cuentas de P71.4 se adelanta por nueva petición
humana; el resto sigue pendiente y no se presenta como implementado.

### Estabilización y comprobaciones GitHub — 17/10/2026

El usuario solicita corregir fallos persistentes/intermitentes y preparar la
próxima estable. Se anteponen los fallos reproducibles de seguridad y CI a las
nuevas opciones del instalador. No se cambia la versión ni se publica una estable
durante esta validación.

- [x] Resolver el fallo repetido de `dependency-review`: grafo de dependencias
  desactivado, activado y verificado mediante reintentos reales de las PR 23/25.
- [x] Igualar dependencias de CI y Release (`dev,gui`), conservar JUnit/logs
  incluso al fallar y añadir regresiones Windows Python 3.10/3.11 a CI. Las nuevas
  definiciones pasan en CI 39071429147 sobre `7a60daa`.
- [x] Endurecer cabeceras HTTPS: tipos MIME fijos para recursos publicados y
  validación de identificadores de sesión; pruebas TLS contra inyección.
- [x] Sustituir confianza SSH automática en dos pruebas por la clave efímera
  conocida; verificar salidas de metadatos/TUI/higiene sin contraseñas.
- [x] Corregir fuga del hash de contraseña al crear un usuario remoto desde
  CLI: proyección explícita de metadatos, clave `passwordHash` vacía por
  compatibilidad y nueva señal `passwordConfigured`; autenticación conservada.
- [x] Corregir nombre y selección de última versión del workflow estable,
  manteniendo el canal experimental. No se ha publicado ni movido ningún tag.
- [x] Comparación integral Coverage 7.10.6/7.16.2 sobre fuentes idénticas:
  ambas pasan 1.208 pruebas y 645 subpruebas, con cobertura idéntica 69,3568 %
  y umbral conservado del 60 %. Se adopta 7.16.2 (P67).
- [x] Verificación local final tras corregir el reintento del primer escaneo:
  1.270 pruebas (incluidas heredadas y navegador) y 645 subpruebas pasan;
  un caso POSIX omitido en Windows. Cobertura 69,9160 %, umbral 60 %.
  Este corte incluye P45/P48/P71.4 y rechazo previo de plataforma no compatible.
- [x] Reejecutar CodeQL sobre el candidato e inspeccionar el SARIF: el resultado
  de la PR 26 conserva #6 sobre `passwordRotatedAt`, una fecha, no el hash.
  El análisis completo de la rama registra diez resultados sobre rutas,
  fechas y metadatos; los tres de SSH/cabecera ya no aparecen.
  No se ocultan alertas; los avisos de `main` no se consideran cerrados antes
  de integrar y analizar esa rama.
- [x] Corregir el fallo exclusivo de CI Linux en la simulación de Windows:
  la prueba de interfaces ahora suministra `CREATE_NO_WINDOW` y verifica flags.
- [x] Corregir seis expectativas de rutas que fallaban en Windows CI con
  alias 8.3 (`RUNNER~1`). Reproducidas localmente con una ruta corta real:
  seis fallos antes, 16 pruebas correctas después; contrato canónico conservado.
- [x] Completar CI de la PR 26 sobre `7a60daa`: Linux y Windows Python
  3.10/3.11 correctos en 39071429147, con navegador en Windows.
- [x] Completar paquetes 39071434470 sobre ese mismo código: Windows instalado
  y portable, Linux amd64/arm64; instalación, actualización y desinstalación
  correctas. El job de publicación se omite; no se crean releases ni tags.
- [x] Compilar los seis launchers y Setup actualizado: 398 entradas,
  recursos/módulos y parser comprobados; Inno termina con código 0.
- [ ] Completar la revisión visual nativa final: interrumpida con Escape por
  el usuario en GUI-DESIGN; no se reanuda ni se marca como aprobada.
  Firmas oficiales y REF-P34-runtime conservan sus bloqueos explícitos.

Estado consolidado el **17/10/2026**; se conserva debajo el historial del 16/10. Los puntos marcados tienen corrección o
verificación local con evidencia en [la matriz de comprobación](BACKLOG-VERIFICATION.md).
La validación de plataformas externas sigue separada; las marcas no equivalen
a certificar instaladores ni sistemas que no se han ejecutado.

## Coordinación no visual AUDITOR — 17/10/2026

Esta revisión complementa el orden histórico del 16/10. El usuario ha encargado
continuar los pendientes disponibles en coordinación con GUI-DESIGN. Se conserva
`experimental-gui` y la versión existente; no se publican ni instalan artefactos.
GUI-DESIGN conserva los archivos `gui/*`, SuiteApi/LauncherApi, `gui_support.py`
y `desktop.py`; AUDITOR desarrolla servicios, datos, CLI/TUI e instalación.

| Tarea | Objetivo y archivos de AUDITOR | Dependencias / impacto | Riesgo | Resultado en fuentes |
| --- | --- | --- | --- | --- |
| P54 | Enlaces compartidos en `core/official_links.py`, `bootstrap/lanctl.py`, Clink y referencias. | Opciones aditivas; sin shell ni destino arbitrario. Desbloquea botones GUI y catálogo de P48. | Bajo | Backend y CLI/TUI verificados; integración visual a cargo de GUI-DESIGN. |
| P35 | Cinco presets y preferencias en `core/gui_preferences.py`, `config.py`, `settings_catalog.py`; lectura de temas activos en `plugins/manager.py`. | Base elegida + tokens/componentes explícitos de plugins; no cambia preferencias guardadas. P34 sigue pendiente para revocación completa entre procesos. | Medio | Persistencia, validación y catálogo comprobados; corregida categoría GUI ausente. |
| P49 | TUI incremental en `apps/monitor/log_tui.py`, `log_stream.py`, `bootstrap/lanmon.py`. | Reutiliza lector, limita lotes y memoria, conserva `--follow`; cierre sin parar tareas. | Medio | Pausa, navegación, filtros y terminal independiente verificados en pruebas enfocadas. |
| P53 | Transporte en `core/activity.py`. | SQLite por propietario, sesión/proyecto explícitos, cursor y últimos registros; conserva mensajes tras cerrar el emisor. | Alto | Verificada escritura desde proceso independiente y lectura desde otro; GUI puede retirar buffer local. |
| P52 | Preparador `core/diagnostics.py` y adaptador `apps/monitor/bug_reports.py`. | Selección acotada, anonimización, agrupación de errores y nueva redacción al exportar; sin proyectos completos ni publicación automática. | Alto | Backend comprobado. Separa el preparador sin red del formulario GitHub; desbloquea esa parte de P50. |
| P51 | Consulta `core/updates.py`. | REST oficial, comparación semántica y canal publicado; caché y reserva entre procesos; tolera fallos. GUI debe invocarlo en worker. | Medio | Verificadas versiones, fallos, recordatorio, concurrencia y validación de enlaces de caché. No instala ni descarga. |
| P66 «Dimensiones» | `core/rack_dimensions.py`, servicios rack/wire, base IDF, modelo NetworkRack y CLI/TUI de LANRACK. | 4–52 U y 10/19/21/23 pulgadas; conserva datos antiguos con advertencias y bloquea reducciones que excluyan equipos. | Alto | Validación y persistencia compartidas comprobadas. La otra entrada P66 «Frentes» conserva su ID y estado. |
| P46 | `plugins/selection.py`, `builtin.py`, `core/installation.py`, instalador. | Selección inicial all/none/individual persistente; tema base obligatorio; actualización conserva elección y permisos. P40 impide certificar uso de trusted oficiales. | Alto | Backend verificado; fuente del instalador preparada, pendiente empaquetado/certificación. |
| P45 | Cinco temas con preview en `packaging/inno/LANCTL.iss`; `setup-defaults` consume el mismo validador. | P35/P46 implementadas en fuentes; actualización no sobrescribe configuración existente. | Medio | Implementación preparada; la compilación/prueba visual del instalador corresponde a integración final. |
| P47 | `core/first_scan.py`, enumeración de interfaces, CLI `list --interface` y transporte ICMP/ARP con origen explícito. | Selección de NIC/rango real, usuario normal y confirmación antes de sondas; adaptador visual en integración. | Alto | 132 pruebas y 10 subpruebas pasan. REF-P47-interface conserva TCP/descubridores y certificación nativa varias NIC/Linux. |
| P48 | `core/clink_integration.py`, Lua, instalador, `portable/prepare.ps1`, script de build. | Solo carpeta de esta distribución/usuario; no ejecutar PATH de usuario al desinstalar elevado. Falta desinstalación desde otra cuenta. | Medio | CMD/Clink 1.9.34 real: completado de los seis launchers, registro repetido y retirada verificados. Corregido código 1 de operación ya aplicada; registro original restaurado. |
| P34 | Concesiones por activación, comprobación de autoridad, retirada de referencias y limpieza fuera de locks implementadas; 119 pruebas pasan. | REF-P34-runtime sigue necesaria: hilos y efectos nativos del trusted heredado no son cancelables desde la API. | Crítico | `runtime_status` distingue acceso al Core, limpieza pendiente y reinicio requerido. No se declara revocación nativa completa. |
| P40/P42 | Artefactos LCP oficiales y confianza real. | Requiere editor/clave y paquetes firmados autorizados; no crear identidad ficticia. | Alto | Bloqueo externo mantenido. |
| P50 | Puente MCP de consulta y diagnóstico. | REF-P34-runtime, contrato de snapshots de sesión viva/revisión y transporte autenticado verificable; el coordinador actual solo comparte metadatos. | Alto | Preparador P52 disponible; puente no implementado ni certificado. No sustituir cambios sin guardar por lectura del VLF. |
| P32 | Certificación de distribución. | Windows instalado/portable y Linux amd64/arm64 pasan en GitHub sobre `7a60daa` (39071434470). SSH externo y varias NIC siguen pendientes. | Alto | Evidencia por commit y plataforma; no se confunde compilación o SSH de loopback con certificación de red externa. |

Refactorizaciones necesarias antes de reanudar las tareas bloqueadas:

- [x] **REF-P84-session · Alta.** Completada el **22/10/2026**, sobre
  REF-P84-save-modes y P88. CLI/TUI LANWIRE/LANRACK aplican cierre, consulta,
  cancelación y temporizador mediante un propietario común. Las siguientes
  operaciones renuevan el servicio según la selección; las ediciones/guardados
  en curso conservan el proyecto de origen. `--database` permanece fija incluso
  si coincidía con el proyecto inicial. La TUI invalida formularios antiguos.
  Un fallo de cierre permite reintentar; EOF y comandos aislados no preguntan.
  Un temporizador por consola persistente, reintentos y parada sin dejar un
  escritor activo. Archivos: `core/projects/console_session.py`, entradas wire/rack,
  TUI físico y callbacks opcionales del anfitrión común; tres archivos de pruebas.
  48 regresiones nuevas, 124 pruebas enfocadas finales y suite completa correcta.
  Permisos, formatos y contratos compatibles; recursos y ciclo GUI conservados.
  Resuelta la dependencia técnica de ciclo de vida; queda certificación nativa
  y distribución, no una segunda implementación. Evidencia:
  [BACKLOG-VERIFICATION.md](BACKLOG-VERIFICATION.md).

- [ ] **REF-P34-migration · Alta.** Adoptar la API de proceso versionada en los
  paquetes que aún requieren `trusted`. Inventariar sus contratos y desarrollar
  adaptadores de red/almacenamiento/monitorización/credenciales únicamente con
  permisos y contexto explícitos. Archivos: `plugins-src/`, adaptadores RPC,
  contratos y pruebas de cada paquete; no cambiar firmas ni permisos de los
  LCP publicados. REF-P34-runtime ya satisface la dependencia técnica; los artefactos oficiales dependen
  además del editor autorizado P40/P42. Consolidar en P34 las confirmaciones
  de cada propietario antes de anunciar una terminación global en las vistas.
  Riesgo alto por efectos nativos y datos sensibles; mantener el aviso de
  reinicio para runtimes heredados. La infraestructura v2 no completa por sí
  sola P34/P50 ni entrega plugins oficiales nuevos.

- [x] **REF-P84-save-modes · Alta.** Unificar el disparador de cambio físico
  CLI/TUI con GUI. Completada el **22/10/2026**: límite compartido de mutación,
  proyecto/contexto fijados, escrituras detectadas por operación y guardado
  después de liberar locks. `automatic.allChanges` ya llega al VLF desde
  comandos, editores, servicios e importación explícita. Los demás modos no
  se fuerzan; consultas y bases externas no guardan el proyecto. El fallo de
  VLF conserva el cambio y su diagnóstico, pide reintentar el guardado y no
  sustituye una excepción anterior. Archivos: `core/projects/physical_mutations.py`,
  notificación de sesión, servicios físicos, procesador, TUI y adaptador GUI
  no visual. 32 regresiones nuevas; 66 pruebas enfocadas finales y suite
  completa correcta. La validación separó el ciclo de cierre/temporizador y
  renovación de servicios en **REF-P84-session**, completada después. Evidencia:
  [BACKLOG-VERIFICATION.md](BACKLOG-VERIFICATION.md).

- [x] **REF-P69-settings · Alta · Completada en fuentes.** Aplicada el **22/10/2026**
  la separación de preferencias respecto al parser CLI, el contexto fijado por
  adaptador y la validación/autorización del lote antes de escribir. Rechaza
  rutas internas en los editores, valores no finitos, tipos incorrectos y
  ajustes ajenos al launcher. Conserva las opciones clásicas de rutas en CLI
  local; el acceso remoto no hereda esa capacidad. Las ediciones remotas de
  proyecto requieren además `project.manage`. GUI/TUI usan el servicio común;
  se conserva selección compartida, formato y firmas públicas. El backend de
  servicio pide elevación antes de crear almacenes o claves; una denegación ya
  no guarda preferencias ni se anuncia como éxito. El ámbito de datos es local
  a la operación y se transmite explícitamente al proceso hijo.
  Archivos: `core/settings_policy.py`, `settings_catalog.py`, `paths.py`,
  `apps/suite/settings.py`, `apps/access/settings.py`, `processes.py`, `remote.py`
  y adaptadores CLI/TUI/GUI. Verificación y límites en
  [BACKLOG-VERIFICATION.md](BACKLOG-VERIFICATION.md).
  La dependencia de recuperación operativa se cierra con REF-P69-remote-lifecycle:
  compensación comprobada o estado pendiente explícito ante un fallo persistente.
  P69 se completa en su entrada propia; las páginas restantes de P71 siguen pendientes.

- [x] **REF-P69-remote-lifecycle · Alta · Completada el 22/10/2026.** Registro
  privado de intención/recuperación, revisión del propietario, confirmación del
  listener y compensación alrededor del guardado final de preferencias. Los
  cambios `service`/`user` y de endpoint detienen el propietario anterior;
  se conservan por separado ámbito de archivos y tipo de proceso heredado.
  Una parada no confirmada o reparación fallida mantiene identidad y registro,
  impide ocultar el fallo con otro cambio y se reintenta al abrir LANCTL o al
  volver a modificar el backend. No copia usuarios/sesiones ni rota claves
  preexistentes; preserva cambios ajenos y los lectores de almacenes migrados.
  Archivos: `apps/access/settings_lifecycle.py`, `runtime_state.py`, `settings.py`,
  `processes.py`, `runtime.py`, `service.py`, `store.py`, servidores SSH/HTTPS,
  adaptadores de preferencias y bootstrap. Riesgo **Alto**, dependencia previa
  satisfecha por la política REF-P69-settings. **43 regresiones nuevas**, procesos
  reales y suite completa correctos. Desbloquea P69/P71; la certificación con
  cuentas de servicio instaladas, Linux/Windows/SSH externo y CI sigue pendiente.
  Evidencia detallada en [BACKLOG-VERIFICATION.md](BACKLOG-VERIFICATION.md).

- [x] **REF-P34-runtime.** Contrato de ejecución con revocación comprobable.
  Separar los plugins con ejecución cancelable en procesos propiedad del host;
  versionar el RPC, permisos por llamada y concesión/revisión de autorización.
  Definir suspensión de nuevas llamadas, retirada de callbacks/funciones,
  cancelación y terminación con plazo, dependencias y confirmación por proceso.
  Nunca mantener locks de registro mientras se invoca `deactivate` de código
  externo. Conservar runtime/API anteriores como compatibilidad explícita con
  sus límites; no anunciar aislamiento para `trusted` en proceso. Impacto alto
  en plugins y contratos, riesgo crítico; condición previa de cierre P34/P50.
  **Completada el 21/10/2026:** API v2 optativa y acotada, terminación con plazo,
  conservación del propietario ante fallo, permisos por llamada y registro
  atómico frente a revocación. 71 regresiones enfocadas y suite integral de
  1.465 pruebas + 648 subpruebas correctas; comprobación real del ejecutable
  empaquetado. Confirmación local por propietario; la migración de paquetes
  y la consolidación global quedan en REF-P34-migration/P34. No se modifican
  GUI-DESIGN, firmas, confianza ni contratos anteriores. Evidencia en
  [BACKLOG-VERIFICATION.md](BACKLOG-VERIFICATION.md).
- [ ] **REF-P47-interface.** Completar el origen explícito de TCP y de los
  descubridores mDNS/SSDP/WSD, y certificar varias NIC en Windows/Linux.
  La enumeración con máscara real y la vinculación ICMP/ARP ya están
  implementadas; el modo explícito omite los mecanismos que aún no garantizan
  ese origen. No introducir escaneos fuera del rango confirmado. Impacto
  transversal en descubrimiento, riesgo alto; requisito para completar P47.

- [ ] **REF-P50-session.** Antes del puente MCP, definir un proveedor de snapshot
  del proceso propietario con revisión, contexto de sesión/proyecto explícito,
  caducidad al cerrar/cambiar de proyecto y datos temporales aún no guardados.
  Seleccionar campos por capacidad y excluir credenciales. El coordinador solo
  contiene metadatos y `_SESSION_DEVICES` es memoria de proceso: leer un VLF
  desde el servidor no cumple ese contrato. Riesgo alto, impacto en sesión e
  inventario; REF-P34-runtime ya aporta el transporte y la revocación, pero no
  sustituye este contrato de sesión ni aporta por sí solo el adaptador MCP.

Orden vigente tras esta revisión: P69, REF-P69-settings y
REF-P69-remote-lifecycle completadas; continuar con los adaptadores de REF-P34-migration sin cambiar
contratos de paquetes existentes; completar REF-P47-interface y la
certificación externa P32/P48; configurar el
editor autorizado antes de cerrar P40/P42. P50 requiere además el contrato de
sesión viva REF-P50-session. P45 está comprobada por el usuario; P67/P68 están
aplicadas y verificadas. Las nuevas páginas y opciones P70–P73 conservan su
planificación separada, salvo la creación inicial de cuentas de P71.4.

Las marcas históricas de las tareas con alcance GUI/instalador no se adelantan
a la validación final. Evidencia y límites: sección AUDITOR del 17/10 en
`docs/BACKLOG-VERIFICATION.md`; contratos de integración en el informe local
`.tool-reports/gui-auditor-sync.json`.

## Orden de ejecución validado — 16/10/2026

Este orden gobierna las tareas abiertas; los IDs y el historial de las secciones
posteriores se conservan. En cada ciclo se valida y planifica antes de escribir
código, se implementa una sola tarea disponible y se actualiza su evidencia.
Los riesgos de la tabla describen el riesgo de introducir el cambio. Una tarea
bloqueada no impide avanzar otra independiente. GUI-DESIGN estaba inactivo al
comprobar esta planificación; sus archivos conservan cambios sin integrar.

Hallazgos de validación: P40/P42 son una sola incidencia; P44 impedía comprobar
el arranque con datos antiguos; la inicialización completa del layout solo se
invoca en la entrada LANIP, mientras otras GUI usan el gestor directamente.
Por ello la compatibilidad del registro debe resolverse en su límite de lectura
compartido, sin añadir inicializadores a cada interfaz. P34 conserva autorización
y runtimes en memoria por proceso: notificar cambios visuales no basta para
revocar ejecución. Su siguiente revisión debe definir el alcance del cierre de
un plugin `trusted` dentro del proceso y el orden de locks antes de implementar.

| Orden / tarea | Objetivo | Módulos y archivos afectados | Dependencias y conflictos detectados | Riesgo | Impacto / estado actual |
| --- | --- | --- | --- | --- | --- |
| Completada · P44 | Recuperar exclusivamente el registro vacío histórico y conservar rechazos de corrupción. | Plugins/persistencia: `src/lanctl/core/plugins/manager.py`, `src/lanctl/core/data_migration.py` (plantilla ya corregida), `src/lanctl/core/file_transaction.py` (reutilizar); nueva prueba `tests/test_plugin_registry_migration.py`; `errorList.txt`. | Sin bloqueo externo. No duplicar la migración en GUI ni relajar el validador. Compartir el lock de los escritores. | Alto | Arranque antiguo recuperado y verificado. Dependencia satisfecha para P34/P46/P47/P32. |
| 1 · P34 | Aplicar cambios de autorización a gestores/runtimes activos y reflejar estado real. | `core/plugins/manager.py`, `publishers.py`, `api.py`, `events.py`, `functions.py`, `isolated_runtime.py`; `core/session.py`, `coordination.py`; adaptadores GUI y pruebas de plugins/coordinación bajo `src/lanctl/` y `tests/`. | P44 completada permite reproducir actualizaciones desde datos previos. Concretar cancelación de `trusted`, propagación entre procesos, dependencia de consumidores y revocación durante llamadas; las vistas se coordinan con GUI-DESIGN. | Crítico | Seguridad transversal; no basta invalidar una caché ni emitir un evento. Pendiente de validación específica del ciclo de vida. |
| 2 · P40 | Distribuir y verificar los LCP oficiales firmados. | `core/plugins/package.py`, `publishers.py`, `builtin.py`, `bundled/*.lcp`, `bundled/plugin-catalog.json`, herramientas de empaquetado y pruebas de instalación. | Requiere identidad/clave del editor y artefactos autorizados. P34 para certificar revocación en caliente; la firma del paquete puede prepararse en paralelo. No generar una identidad oficial ficticia. | Alto | Desbloquea uso de los cuatro plugins `trusted` y la entrega de P46. Bloqueada externamente para publicar firmas reales. |
| 2 · P42 | Conservar evidencia y seguimiento del bloqueo de mDNS/SSDP. | `docs/BACKLOG.md`, `docs/BACKLOG-VERIFICATION.md`; mismos módulos de P40. | Alias de seguimiento de P40, no una segunda implementación. | Bajo | Se cerrará junto a P40 cuando exista evidencia de instalación real. |
| 3 · P35 | Definir opciones básicas y verificar persistencia/feedback de temas. | `core/plugins/theme.py`, `settings.py`, `core/config.py`; `apps/ip/interfaces/gui/theme.py`; `gui/suite.js`, `suite.css`, `launcher.js`; pruebas de configuración/navegador. | P34 para estado de plugins consistente entre procesos. Acordar catálogo de opciones antes de añadir campos; propiedad visual de GUI-DESIGN. | Medio | Establece el contrato de temas que consumirá P45; evita un estado visual distinto del guardado. Pendiente de diseño acotado. |
| 4 · P46 | Respetar selección de plugins opcionales durante instalación y actualización. | `core/plugins/builtin.py`, `core/data_migration.py`, `LANCTL.spec`, `packaging/inno/LANCTL.iss`, `scripts/build-windows.ps1`, pruebas de distribución. | P44 completada; P40 para entregar plugins `trusted` utilizables. Definir exclusión persistente para que el bootstrap no reinstale lo omitido y preservar el tema base. | Alto | Cambia instalación/primer arranque sin conceder permisos. Antes de P45 y de certificar P47. |
| 5 · P45 | Elegir cinco temas con vista previa sin sobrescribir preferencias al actualizar. | `core/plugins/theme.py`, `core/config.py`, recursos de temas, `packaging/inno/LANCTL.iss`, pruebas de instalación/configuración. | P35 define preferencias y los cinco temas; P46 define qué recursos son obligatorios. Comparte instalador con P46/P47/P48: cambios secuenciales. | Medio | Afecta primer inicio y actualización; no escribir configuraciones con un formato paralelo. |
| 6 · P47 | Abrir LANIP y ofrecer el primer escaneo elegido por el usuario. | `packaging/inno/LANCTL.iss`, `bootstrap/lanip.py`, `apps/ip/interfaces/gui/desktop.py`, `core/config.py`; pruebas nativas/distribución. | P44 completada; contrato de selección de P46; revisar sesión normal frente a instalador elevado y selección de red antes del escaneo. | Alto | Puede iniciar tráfico de red: consentimiento explícito y límites/progreso compartidos. Pendiente. |
| 7 · P54 | Compartir enlaces oficiales entre GUI y comandos CLI/TUI. | `bootstrap/lanctl.py`, `apps/suite/interfaces.py`, `apps/suite/gui.py`, `gui/suite.html`, `suite.js`; servicio de enlaces propuesto; generadores de referencias, `packaging/clink/lanctl.lua` y tests. | No depende de la migración. URLs proporcionadas; no usar shell. Coordinar barra inferior con P53/P52. Antes de la comprobación final de Clink de P48. | Bajo | Añade opciones públicas; conservar las anteriores y salida legible sin soporte de hipervínculos. Pendiente. |
| 8 · P48 | Empaquetar y registrar Clink para el usuario correcto, con desinstalación acotada. | `packaging/clink/lanctl.lua`, `README.md`, `packaging/inno/LANCTL.iss`, `scripts/build-windows.ps1`, `packaging/portable/`, `tests/test_clink.py`, `test_distribution.py`. | P54 para certificar el catálogo final de opciones; instalación puede prepararse antes. Requiere CMD con Clink real y pruebas de actualización, sin registrar en la cuenta administrativa equivocada. | Medio | Afecta PATH/completado y paquetes; no retirar scripts ajenos ni duplicar registros. Pendiente. |
| 9 · P49 | Visor TUI de logs operativo, incremental y acotado, independiente de LANIP. | `apps/monitor/log_stream.py`, `event_view.py`, `interfaces.py`, `bootstrap/lanmon.py`; `core/logger.py`; `apps/ip/interfaces/gui/desktop.py`; pruebas de logs, launcher y terminal. | Reutilizar `LogFollower`, no crear un segundo lector. Definir contrato de origen/sesión que P53 amplía con actividad GUI. Coordinar botón con GUI-DESIGN. | Medio | Debe soportar rotación, pausa, filtros y cierre sin detener tareas; no confundir auditoría VLF con log operativo. Pendiente. |
| 10 · P53 | Trasladar actividad a LANMON preservando origen y retirar el reloj visual. | `gui/suite.js`, `suite.html`; `core/session.py`, `coordination.py`, `logger.py`; `apps/monitor/event_view.py`, `gui_service.py`; pruebas entre procesos. | P49 ofrece visor común. El buffer local de hasta 100 mensajes necesita transporte explícito; no eliminarlo antes de que LANMON reciba esos mensajes. | Alto | Riesgo de perder mensajes o mezclar proyectos. No elimina timestamps ni comandos CLI/TUI. Pendiente, ámbito visual de GUI-DESIGN. |
| 11 · P52 | Preparar reportes revisables y anonimizados desde LANMON. | `core/errors.py`, `logger.py`, `history.py`; servicio de diagnóstico propuesto; `apps/monitor/reports.py`, `gui_service.py`; barra GUI y pruebas de redacción/exportación. | P49/P53 para fuentes/origen compartidos. Servicio de preparación independiente de abrir GitHub; no usarlo como dependencia de red de P50. Agrupar errores sin recursión de notificaciones. | Alto | Maneja datos potencialmente privados; excluir secretos y publicar solo mediante revisión humana. Pendiente. |
| 12 · P51 | Avisar de versiones estables superiores con consultas limitadas y tolerantes a fallos. | `infrastructure/distribution/release.py`, `core/config.py`, `core/session.py`, GUI de ajustes; servicio de consulta propuesto y pruebas de versiones/red/caché. | Reglas de canal existentes; un sufijo histórico no determina por sí solo estabilidad. Separar comparación semántica del nombre del artefacto y del orden de publicación. No requiere P50. | Medio | Arranque, red y preferencias; ningún instalador se descarga ni ejecuta. Sincronizar la versión de la futura entrega antes de publicarla. Pendiente. |
| 13 · P50 | Puente MCP externo de consulta y diagnóstico con contexto explícito. | `core/plugins/api.py`, `contracts.py`, `core/session.py`, `coordination.py`, `session_context.py`, proyectos; plugin/adaptador MCP nuevos; diagnóstico de P52 y pruebas de permisos. | P34 y contrato de sesión/revisión; reutilizar el preparador de P52 sin su navegación GitHub. Definir transporte/autenticación con documentación vigente de los clientes antes de implementar. Control con escrituras queda para una fase posterior. | Alto | Frontera externa: no exponer secretos, confundir datos guardados con cambios en memoria ni elegir arbitrariamente una sesión. Pendiente de diseño de conexión. |
| Cierre de candidato · P32 | Certificar instalación, actualización, portable, Linux ARM64 y acceso remoto. | `.github/workflows/release.yml`, `scripts/build-windows.ps1`, `build-linux.sh`, `tests/portable_smoke.py`, smokes nativos y documentación de validación. | P44 completada; P34 y todos los cambios incluidos en el candidato; identidad de versión/artefactos congelada. Requiere Windows limpio, Linux ARM64 y otro equipo SSH. No exige implementar todas las funciones futuras del backlog. | Alto | Evidencia reproducible por plataforma. Las pruebas locales pueden adelantarse; la certificación externa sigue bloqueada por entornos pendientes. |

Plan acotado de P44, previo a implementación: reconocer únicamente el objeto
JSON vacío histórico en el lector compartido del registro; migrarlo a esquema 1
bajo el mismo lock que usan los escritores, mediante sustitución atómica.
Mantener intactos los registros versionados, permisos, firmas y editores. JSON
roto, esquemas desconocidos y documentos no vacíos inválidos seguirán fallando
con su origen. Probar datos nuevos/antiguos, idempotencia, errores de escritura,
concurrencia y arranque LANIP; ejecutar después la suite completa. Si aparece
un bloqueo estructural que exija ampliar el alcance, detener este cambio y
registrar una refactorización con dependencia y estimación antes de continuar.

Resultado del ciclo: **P44 completada y verificada en fuentes**, sin ampliar el
alcance ni modificar interfaces de GUI-DESIGN. Su dependencia de arranque queda
satisfecha para P34, P46, P47 y P32; estas tareas conservan sus otros requisitos.
No apareció un problema estructural nuevo que obligara a detener P44 y crear
una refactorización. **Siguiente tarea recomendada: P34**, comenzando por validar
revocación, ciclo de vida de runtimes y orden de locks antes de implementar.

La suite completa pasa con 1.073 pruebas, 643 subpruebas, una omisión POSIX y
cobertura del 68,0842 %. Sigue pendiente el formato de seis archivos de cambios
anteriores, enumerados en la matriz de verificación; debe resolverse antes de
integrar. Los instaladores existentes todavía no incluyen esta migración.

## Prioridad alta: persistencia y fiabilidad

- [x] **P01.** Reproducir el fallo de `Ctrl+S` en el TUI y determinar qué cambios no se
  guardan: configuración, proyecto, inventario o estado de los gestores.
- [x] **P02.** Verificar el flujo completo de guardado: detección de cambios, validación,
  escritura transaccional, bloqueo, confirmación visual y recarga posterior.
- [x] **P03.** Comprobar el comportamiento de `Ctrl+S` con proyecto activo, sin proyecto,
  en cada ventana modal y durante tareas de segundo plano.
- [x] **P04.** Revisar la carga de plugins: descubrimiento, dependencias, permisos,
  estados pendiente/activo/fallido, recarga y presentación de errores.

## Incidencia reportada: activación de Wake-on-LAN en la GUI

- [x] **P05.** Investigar y corregir el flujo de activación de Wake-on-LAN cuando se
  conceden los permisos y se autoriza la ejecución `trusted`, pero la GUI
  devuelve un error de confianza del editor.

Estado: **flujo corregido y verificado**. Gravedad: media. El LCP WOL incluido
no lleva firma; se conserva el bloqueo de seguridad y la GUI explica el requisito.
Un LCP firmado permite autorizar al editor seleccionando el paquete original.
Evidencia: captura aportada por el usuario del diálogo «Activar Wake-on-LAN».
La versión instalada y la procedencia/firma del LCP no se pueden determinar
a partir de la captura.

Secuencia a reproducir: abrir la activación de Wake-on-LAN, marcar
`network.udp`, `functions.register`, `ui-action.register` y «Autorizar ejecución
trusted (requiere editor autorizado)», y pulsar «Activar plugin».

Mensaje mostrado, con su identificador tal como aparece en la captura:

```text
el runtime trusted requiere un LCP firmado por un editor confiable; usa plugin publisher trust (0e94E1E397)
```

Impacto observado: la activación queda bloqueada y el diálogo remite a un comando
CLI sin completar el flujo de autorización del editor desde esa pantalla.
Referencia para investigar: `PluginManager.enable()` en
`src/lanctl/core/plugins/manager.py`, verificación de firma y almacén de editores
confiables. Se confirmó el bloqueo para paquetes sin firma y para editores no autorizados.
La GUI distingue ambos casos; no se concede confianza al marcar permisos.

Criterio de aceptación: un paquete firmado por un editor autorizado se activa con
los permisos concedidos; si falta esa confianza o la firma no es válida, la GUI
explica el requisito concreto y los pasos necesarios. La corrección debe conservar
la validación de firmas y añadir regresiones para ambos casos.

## Plugins: disponibilidad del botón de configuración

- [x] **P06.** Mostrar el botón de configuración únicamente en los plugins que ofrezcan
  opciones configurables. Si el plugin no dispone de ninguna, ocultar el botón
  para evitar abrir un panel vacío.

Criterio de aceptación: comprobar plugins sin opciones y plugins configurables,
incluidos los que todavía usan valores predeterminados y no tienen configuración
guardada. La visibilidad debe depender de las opciones disponibles, no de haber
guardado ajustes previamente, y actualizarse al recargar o actualizar el plugin.

## Project Manager

- [x] **P07.** Permitir guardar manualmente el proyecto seleccionado o activo.
- [x] **P08.** Añadir edición de nombre, descripción, autor, LAN, ubicación, empresa y
  responsable.
- [x] **P09.** Crear formularios modales con cuadros de texto para crear y editar los
  metadatos del proyecto.
- [x] **P10.** Validar los datos antes de escribir y pedir confirmación si existen
  modificaciones sin guardar.
- [x] **P11.** Refrescar el catálogo y la pestaña de información inmediatamente después
  de crear, editar, guardar, activar o eliminar un proyecto.

## Arranque de LANCTL y coordinación de launchers

Pendientes de revisión incorporados el 15/10/2026:

- [x] **P12.** Añadir una opción de configuración global y persistente para elegir
  **CLI, TUI o GUI como interfaz preferida al iniciar LANCTL sin argumentos**.
  Debe aplicarse tanto al doble clic sobre el ejecutable principal como a su
  invocación desde una terminal. Los argumentos explícitos deben conservar su
  prioridad sobre esta preferencia. Verificar los tres modos en ambos arranques.
- [x] **P13.** Permitir configurar el comportamiento de la GUI principal al abrir un
  launcher: **cerrar la GUI de LANCTL** o **mantenerla abierta**. Comprobar que
  cerrar la ventana principal no cierre el launcher y que un fallo al abrirlo
  mantenga visible el error, sin cerrar prematuramente LANCTL.
- [x] **P14.** Impedir que se abran dos ventanas GUI del mismo launcher. Detectar la
  ventana existente, restaurarla si está minimizada y traerla al frente al
  solicitar otra apertura. Revisar este comportamiento desde LANCTL, terminal
  y doble clic, incluyendo aperturas simultáneas y recuperación después de un
  cierre inesperado, para evitar duplicados o bloqueos por instancias obsoletas.
- [x] **P15.** Verificar que **launchers distintos puedan permanecer abiertos al mismo
  tiempo** y mantengan comunicación y feedback entre ellos: estado de apertura,
  cierre y errores, eventos y actualización de los datos compartidos que les
  correspondan. Confirmar que cada interfaz refleje los cambios relevantes sin
  reiniciarse, respete el contexto de su proyecto y que cerrar un launcher no
  interrumpa los demás. Incluir la GUI de LANCTL cuando se configure para seguir
  abierta y probar la coordinación cuando se cierre.

## Teclado y ayudas visuales

- [x] **P16.** Remarcar `→` con fondo blanco en el pie del menú Plugins.
- [x] **P17.** Auditar todos los pies de ventanas para encontrar teclas sin el fondo de
  tecla correcto, incluyendo flechas, teclas de función, `Supr`, `Enter`,
  `Esc` y combinaciones `Ctrl+…`.
- [x] **P18.** Revisar el editor de asignaciones: conflictos, teclas reservadas,
  desactivación con `None`, persistencia y restauración de valores iniciales.
- [x] **P19.** Verificar por separado qué atajos están activos y cuáles son visibles en
  la barra inferior.
- [x] **P20.** Comprobar que los atajos locales de una ventana no se ejecuten fuera de
  ella.

## Consola integrada del TUI

- [x] **P21.** Añadir más mensajes útiles sobre inicio y final de tareas, resultados,
  guardado, recarga, cambios pendientes y errores recuperables.
- [x] **P22.** Mantener los mensajes breves, con nivel y origen coherentes y sin desplazar
  innecesariamente la tabla principal.
- [x] **P23.** Revisar el historial, el límite de líneas y el ajuste al ancho disponible.

## Revisión estética general

- [x] **P24.** Auditar bordes, títulos, pestañas, separadores, colores de fondo,
  alineación y recorte en todos los overlays.
- [x] **P25.** Probar tamaños de terminal pequeños, medios y muy grandes, además de
  cambios de tamaño mientras el TUI está abierto.
- [x] **P26.** Verificar que las ventanas modales oculten correctamente las líneas del
  fondo y que el renderizado diferencial no deje residuos ni produzca parpadeo.
- [x] **P27.** Unificar el estilo de selección, campos editables, cambios pendientes,
  estados deshabilitados y mensajes de confirmación.

### GUI: disposición y recorte de la barra inferior

Estado: **corrección validada en navegador** el 15/10/2026. Se conserva la
corrección de interfaz que el usuario indicó en curso el 14/10/2026: pruebas con
50 proyectos/plugins, desplazamiento y ventanas de 790×570, 660×460 y 375×650.

Evidencia: dos capturas de la vista de proyectos; la primera muestra la barra
inferior con plugins, CLI, Actividad y Sistema, y en la segunda esa barra no
queda visible dentro de la ventana. La primera captura muestra la versión 0.3.3.

- [x] **P28.** Validar la corrección que ya está en marcha: la barra y sus controles
  deben permanecer visibles y accesibles al redimensionar la ventana y desplazar
  la lista de proyectos, sin recortes ni superposiciones.

## Auditoría técnica

- [x] **P29.** Revisar concurrencia, bloqueos de archivos y escrituras simultáneas entre
  TUI, CLI, backend y plugins.
- [x] **P30.** Revisar tareas de segundo plano, cancelación, cierre seguro y liberación
  de recursos.
- [x] **P31.** Confirmar que errores, eventos, logs y puntos de extensión del core se
  emitan de forma coherente en todos los flujos anteriores.
- [ ] **P32.** Ejecutar pruebas de regresión en Windows instalado, Windows portable,
  Linux ARM64 y acceso remoto.
  Windows instalado/portable y Linux amd64/arm64 verificados por el workflow
  manual 39071434470 (`7a60daa`), incluyendo P45/P48/P71.4 y el rechazo de
  plataforma no compatible. Queda certificar acceso desde otro equipo, sin
  confundirlo con las pruebas TLS/SSH locales.
- [x] **P33.** Registrar durante la revisión cualquier hallazgo técnico adicional con
  pasos de reproducción, impacto y prueba de aceptación.

## Validación que sigue pendiente

P32 permanece abierto: instalación/actualización/desinstalación en Windows
limpio, Linux ARM64 y acceso SSH desde otra máquina. Las pruebas locales y los
smokes de GUI no sustituyen esas comprobaciones. La matriz registra el alcance
exacto de cada prueba y los hallazgos corregidos.

## Próxima revisión: pendientes añadidos el 16/10/2026

Estado actualizado el **16/10/2026**. Los avances de GUI-DESIGN y AUDITOR se
indican por separado; las comprobaciones de backend se amplían en
[la matriz de verificación](BACKLOG-VERIFICATION.md).

- [ ] **P34.** Revisar el estado actual de los plugins y comprobar que su estado
  real se corresponda con el que muestra la interfaz. Esta nueva revisión
  complementa las comprobaciones anteriores de P04, P05 y P06.
  **Parcial — AUDITOR:** corregidas integridad y firma al activar/verificar,
  restauración segura al arrancar, dependencias, limpieza de runtimes,
  cuarentena persistente y escrituras concurrentes. Falta la propagación
  inmediata de cambios y revocaciones a todos los runtimes e interfaces ya
  abiertos; las operaciones con una revisión antigua se rechazan y piden recarga.
  Verificación final: 43 regresiones nuevas; suite completa con 1.013 pruebas y
  643 subpruebas aprobadas, 1 omisión POSIX y cobertura del 67,83 %.
  **Actualización 21/10/2026:** REF-P34-runtime completada; la API de proceso v2
  permite revocar generaciones activas y dependientes, detener código no
  cooperativo y comprobar el cierre local. La suite actual y los límites están
  al inicio del documento. Los paquetes `trusted` heredados siguen requiriendo
  adaptación/reinicio y falta consolidar las confirmaciones de todos los
  propietarios en las vistas; P34 permanece abierto mediante REF-P34-migration.
- [x] **P35.** Revisar el feedback del sistema de temas y paletas de colores:
  comprobar cómo se reflejan los cambios seleccionados en la interfaz y en los
  ajustes guardados. Definir y añadir opciones básicas de configuración de la
  GUI; las opciones concretas quedan por determinar en esa revisión.
- [x] **P36.** Al crear un proyecto, rellenar automáticamente el campo de carpeta
  de guardado con la ruta predeterminada. Permitir que el usuario la edite o
  seleccione otra carpeta si lo desea, sin exigir una selección manual para
  aceptar la ubicación predeterminada.

## Observaciones de GUI del 16/10/2026

- [x] **P37.** Ajustar Inicio al área útil inicial, incluyendo escalado de Windows,
  para mostrar los cinco launchers completos sin scroll. Mantener cabecera y pie
  visibles al redimensionar.
- [x] **P38.** Completar Configuración GUI con las opciones de programa y proyecto
  agrupadas por temas, reutilizando el catálogo y las validaciones compartidas
  del CLI. Diferenciar campos editables y automáticos y comprobar persistencia.
- [x] **P39.** Hacer que la terminal integrada ocupe el espacio disponible al
  redimensionar; solo la salida debe desplazarse, con entrada y pie visibles.
- [ ] **P40.** Revisar con AUDITOR el diálogo de permisos de plugins y el bloqueo
  por firma no válida (mDNS + SSDP Discovery). Distinguir permisos, firma y
  confianza del editor; relacionado con P34/P05. No asumir fallo del backend
  ni retirar validaciones de seguridad. Anotación enviada a AUDITOR.
  **Parcial — AUDITOR:** confirmado que los LCP incluidos de mDNS/SSDP y WOL
  carecen de firma; el bloqueo es correcto. Corregidos fallos independientes del
  backend de validación, estado y persistencia, con regresiones. Sigue pendiente
  distribuir LCP firmados por el editor del proyecto y verificar su instalación
  real. P42 conserva la evidencia del mismo caso; no es una incidencia adicional.
- [x] **P41.** Ampliar P36: proponer valores iniciales editables para metadatos
  técnicos de proyectos, especialmente LAN, sin copiar datos privados del
  proyecto anterior ni sobrescribir VLF existentes.

La confirmación de cambios sin guardar de LANCTL utiliza ahora un diálogo
propio con botón principal verde lima, en lugar del aviso «Esta página dice».
- [ ] **P42.** Seguimiento de P40: revisar permisos y firmas de plugins a partir del
  bloqueo reportado al activar **LANCTL mDNS + SSDP Discovery**. Relacionado con
  P34 y con el antecedente de Wake-on-LAN de P05.

  Evidencia reportada: captura del 16/10/2026 del diálogo «Activar LANCTL mDNS +
  SSDP Discovery», que muestra los permisos `scanner.register`,
  `functions.register` y `network.scan`. El diálogo informa de que el paquete
  no tiene una firma válida, solicita un LCP firmado y no permite activarlo.
  La captura por sí sola no demuestra un fallo del backend: el bloqueo de este
  paquete sin firma es correcto. La auditoría posterior encontró y corrigió
  otros fallos de integridad, activación y persistencia, registrados en la matriz.

  Revisión técnica realizada: permisos solicitados/concedidos, autorización
  del runtime `trusted`, validez de la firma y confianza del editor. La firma de
  los cuatro plugins `trusted` del catálogo sigue pendiente de distribución;
  no se ha generado ni autorizado una identidad oficial durante la auditoría.


Implementación GUI del 16/10/2026: P36/P37/P38/P39/P41 completados con
validación local de catálogo compartido, persistencia y distribución a tamaños
790×570, 960×590, 660×460 y 1440×900. P40/P42: el flujo gráfico ahora permite
instalar una versión firmada verificada sin recurrir a comandos; la auditoría
de la distribución/firma de los paquetes sigue separada. No se autoriza un
paquete sin firma por marcar sus permisos.

## Errores reportados en el chat — 16/10/2026

- [x] **P43.** Corregir la excepción no controlada al inicializar un icono
  mediante `System.Drawing.Icon.Initialize(Int32 width, Int32 height)`.
  **Corregido y verificado localmente — AUDITOR, 16/10/2026. Gravedad alta:**
  LANCTL y LANIP pasaban un PNG a `webview.start(icon=...)`; el backend WinForms
  lo entregaba directamente a `System.Drawing.Icon`, que exige un ICO. Los dos
  PNG reproducen exactamente la excepción reportada. Se selecciona ahora el
  ICO incluido en Windows y se conserva el PNG en las otras plataformas.

  Evidencia aportada por el usuario (traza íntegra):

  ```text
  Excepción no controlada: System.ArgumentException: El argumento 'picture' debe ser una imagen que puede utilizarse como Icon.
     en System.Drawing.Icon.Initialize(Int32 width, Int32 height)
  --- Fin del seguimiento de la pila de la ubicación anterior donde se produjo la excepción ---
     en System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()
     en Python.Runtime.PythonException.ThrowLastAsClrException()
     en Python.Runtime.Dispatcher.TrueDispatch(Object[] args)
     en Python.Runtime.Dispatcher.Dispatch(Object[] args)
     en __System_Threading_ThreadStartDispatcher.Invoke()
     en System.Threading.ExecutionContext.RunInternal(ExecutionContext executionContext, ContextCallback callback, Object state, Boolean preserveSyncCtx)
     en System.Threading.ExecutionContext.Run(ExecutionContext executionContext, ContextCallback callback, Object state, Boolean preserveSyncCtx)
     en System.Threading.ExecutionContext.Run(ExecutionContext executionContext, ContextCallback callback, Object state)
     en System.Threading.ThreadHelper.ThreadStart()
  ```

  Verificación inicial: 16 regresiones (ocho fallaban antes de la corrección), constructor
  real de .NET, rutas de fuentes y extracción PyInstaller, ventanas nativas y
  ejecutables nuevos de LANCTL/LANIP con HICON. Suite completa sobre una copia
  de `a6fadc8` más la corrección: 1.029 pruebas y 643 subpruebas aprobadas;
  una prueba POSIX omitida en Windows. Se conservan las firmas existentes y
  los contratos del Core. Catálogo de errores regenerado y comprobado.

  Durante la revisión, el adaptador nuevo `suite/launcher_gui.py` de GUI-DESIGN
  introdujo la misma llamada con PNG. Corregidos únicamente su importación y
  selección de icono. Ocho regresiones adicionales reproducen la excepción y
  pasan después para LANWIRE/LANRACK/LANACCESS/LANMON: **24 regresiones de P43
  aprobadas** en el árbol compartido. Sus nuevas interfaces siguen bajo
  GUI-DESIGN y no forman parte de los ejecutables aislados de esta revisión.

  Los artefactos de prueba están en `dist/p43-verified/`, incluido
  `LANCTL-0.3.3-p43-setup.exe`. Se han separado del desarrollo concurrente de
  GUI-DESIGN; no se ha actualizado la instalación del usuario. La prueba de
  arranque empaquetado de LANIP requiere un registro de plugins válido por P44.
  Detalle y límites en `docs/BACKLOG-VERIFICATION.md`.

- [x] **P44.** Corregir la inicialización del registro de plugins y migrar el vacío histórico.
  **Completada y verificada en fuentes — 16/10/2026. Gravedad alta.** Detectado al verificar P43:
  `ensure_data_layout()` creaba `plugins/registry.json` con `{}`, pero
  `PluginManager._read_registry()` exige `schemaVersion: 1` y un objeto `plugins`.
  La GUI de LANIP muestra «registro de plugins no válido»; el ejecutable puede
  terminar con código 2 antes de abrirla. Es independiente del formato del icono.
  GUI-DESIGN corrigió la plantilla de creación a `{"schemaVersion": 1, "plugins": {}}`.
  AUDITOR comprobó con datos temporales nuevos que ese documento se crea y
  `PluginManager` inicia correctamente. La validación de permisos y firmas no
  se ha relajado. El instalador aislado de P43 es anterior a este ajuste.

  El lector compartido migra ahora exclusivamente el objeto JSON vacío `{}`
  al esquema 1 mediante escritura atómica y bajo el lock del registro. No
  reescribe documentos versionados ni concede permisos, confianza o ejecución.
  Los documentos corruptos, no vacíos sin esquema o de versión desconocida
  siguen fallando con su origen; un fallo de escritura conserva el original.

  Verificación: 18 regresiones nuevas (seis fallaban antes), 87 pruebas
  relacionadas y 17 subpruebas aprobadas; arranque y recorrido nativo completo
  de LANIP con `{}` en datos temporales. Suite completa: 1.073 pruebas y 643
  subpruebas aprobadas, una omisión POSIX, cobertura del 68,0842 %. Conservadas
  las 37 firmas de funciones/métodos del gestor, sus eventos y 51 IDs/orígenes
  de error. Desbloqueadas las comprobaciones con datos antiguos de P34/P32 y
  satisfecha la dependencia de arranque de P46/P47. La reconstrucción y
  certificación de instaladores sigue dentro de la entrega/P32.

## Configuración inicial del instalador — 16/10/2026

- [x] **P45.** Añadir una selección de cinco temas durante la instalación, con
  nombre y vista previa. Guardar la elección mediante la configuración compartida
  del programa y conservar el tema existente en actualizaciones, salvo cambio
  explícito del usuario.
  **Reabierta por reporte visual — 17/10/2026.** En el instalador
  «LANCTL GUI experimental (NO ESTABLE) version 0.3.4-alpha.1», página
  «Apariencia inicial», no se ven las imágenes de ejemplo de los temas.
  La captura aportada muestra las cinco opciones y «Bosque» seleccionado,
  pero el área de vista previa aparece vacía, con el texto «LANCTL · Vista
  previa de fondo y acento» apenas legible. Resultado esperado: mostrar una
  imagen representativa del aspecto del programa y actualizarla al cambiar
  de tema. Pendiente de diagnóstico: comprobar generación, inclusión y carga
  de los recursos en el instalador compilado, así como contraste y renderizado
  del control. Validar visualmente las cinco opciones en el Setup distribuido;
  la implementación en fuentes no cierra este fallo observado en el instalador.
  **Corregida y comprobada — 17/10/2026.** El instalador usa cinco capturas
  reales del GUI con las paletas del Core, incluidas y extraídas como BMP,
  en lugar de paneles de color. Pasan 16 pruebas de recursos/distribución.
  El usuario abrió el Setup actualizado y confirmó que las cinco imágenes
  son distintas y se ven completas: «Sí, las cinco se ven bien». La captura
  automatizada de la ventana elevada no estuvo disponible; la evidencia visual
  corresponde a esa comprobación humana. Se conserva el contrato de preferencias.
- [x] **P46.** Permitir elegir si se instalan los plugins predeterminados del
  programa, con selección individual opcional. Adaptar el empaquetado y el primer
  inicio para respetar la elección, distinguir los recursos necesarios (como el
  tema base) de los plugins opcionales y conservar permisos, firmas y confianza
  del editor. Mantener las elecciones existentes al actualizar.
- [ ] **P47.** Ofrecer al finalizar la instalación las opciones «Abrir LANIP» y
  «Realizar un primer escaneo». Arrancar la GUI con el usuario normal, mostrar la
  red detectada y permitir seleccionar interfaz/rango cuando haya varias redes;
  mostrar el progreso del escaneo en la GUI y ejecutarlo solo si se ha elegido.
  **Implementado y probado:** selector con máscara real, origen ICMP/ARP,
  progreso y reintento conservando la petición tras fallo. Queda completar
  REF-P47-interface y verificar varias NIC reales.
- [ ] **P48.** Corregir la distribución del completado Clink: incluir
  `packaging/clink/lanctl.lua` y sus instrucciones en el instalador Windows y en
  el ZIP portable. Detectar Clink y registrar automáticamente la carpeta de
  scripts con `clink installscripts` para el usuario correspondiente, tanto en
  la instalación como en el flujo de preparación del portable. Evitar registros
  duplicados al actualizar y retirar el registro de la instalación al
  desinstalar, sin afectar otras carpetas de Clink. Verificar el contenido de
  ambos paquetes y el completado real de los seis ejecutables en CMD con Clink;
  mantener la validación del Lua frente a los parsers de la versión distribuida.
  **Implementado y probado:** CMD/Clink 1.9.34 real, seis launchers, registro
  repetido, retirada y rutas con espacios/acentos; corregida decodificación UTF-8.
  Resta la desinstalación elevada realizada desde otra cuenta.

## Monitorización simultánea con LANIP — 16/10/2026

- [x] **P49.** Añadir a LANMON una TUI de logs en tiempo real que pueda
  permanecer abierta en una terminal mientras se controla y modifica el
  inventario desde la GUI de LANIP. Reutilizar el seguimiento incremental del
  log común, con actualización automática, colores por nivel, filtros, pausa
  y navegación del historial; conservar el origen de los eventos y limitar el
  uso de memoria. Añadir un botón en la GUI de LANIP para abrir este visor en
  otra terminal, tanto desde fuentes como desde los ejecutables instalados y
  portables. Cerrar el visor no debe cerrar LANIP ni interrumpir sus tareas.
  Distinguir el log operativo de las auditorías VLF y explicitar su cobertura;
  verificar que las operaciones registradas desde la GUI aparecen en directo.

## Puente externo MCP con ChatGPT y Codex — 16/10/2026

- [ ] **P50.** Diseñar e implementar un plugin puente externo MCP usable desde
  ChatGPT y Codex, sin incorporar un chat dentro de LANCTL. Exponer herramientas
  estructuradas para consultar proyectos, inventario, tareas y errores mediante
  lenguaje natural. Detectar las sesiones y el proyecto abierto; si hay varias
  sesiones o proyectos, permitir seleccionar explícitamente el contexto.
  Consultar el estado de trabajo de la sesión, incluidos los cambios sin guardar,
  distinguiéndolos de los datos persistidos en el VLF sin forzar su guardado.
  Contemplar cambios de proyecto, cierre de sesión y revisiones del estado para
  evitar presentar datos obsoletos como actuales. Definir y verificar la conexión
  externa y autenticación correspondientes para ChatGPT y Codex.
  La primera fase será de consulta
  y diagnóstico, incluyendo la preparación de borradores de incidencias con
  versión, origen, contexto y evidencia seleccionada, revisables y exportables
  por el usuario. No incluir conexión, sincronización ni publicación en GitHub.
  Definir contratos versionados y permisos por capacidad. Excluir
  credenciales de las respuestas y permitir seleccionar o anonimizar los datos
  incluidos en informes. Ampliar después el control por lenguaje natural con
  operaciones validadas por los servicios compartidos del Core, respetando
  transacciones, bloqueos, auditoría y coordinación con las interfaces abiertas.

## Avisos de actualizaciones estables — 16/10/2026

- [x] **P51.** Añadir una comprobación de actualizaciones en las Releases del
  repositorio oficial de GitHub, con aviso automático en segundo plano y botón
  «Buscar actualizaciones» en ajustes. Ofrecer únicamente versiones estables
  publicadas superiores a la instalada; excluir borradores y prereleases y
  determinar la estabilidad por el canal de publicación, respetando las reglas
  de `stable/VERSION` incluso cuando exista un sufijo histórico. Comparar
  versiones semánticamente, sin confundir orden de publicación con versión
  superior. Mostrar versión instalada/disponible, novedades y enlace de descarga,
  con opción de recordar más tarde. Limitar las comprobaciones automáticas
  (como máximo una al día), sin bloquear el arranque ni el uso si falla la red.
  No descargar, ejecutar instaladores ni instalar actualizaciones automáticamente.

## Reportes de errores desde LANMON — 16/10/2026

- [x] **P52.** Centralizar en LANMON la recopilación y preparación de reportes
  de errores. Al detectar un error, mostrar una ventana emergente con resumen
  y acciones para ver detalles, preparar el reporte o cerrar; agrupar errores
  repetidos para evitar una sucesión de ventanas. Añadir en la barra inferior
  de información de las GUI un botón de texto «Report a bug», con el mismo
  estilo y comportamiento visual que el botón «CLI», que permita informar
  también de problemas sin error registrado. Ambas entradas abrirán el mismo
  flujo de reporte gestionado por LANMON.
  Preparar un borrador editable con descripción, pasos de reproducción,
  resultado esperado, versión de LANCTL y del sistema, aplicación/interfaz,
  código y origen del error, fecha, sesión/tarea relacionada, versiones de
  plugins y fragmentos de logs pertinentes. Mostrar una vista previa de los
  datos y logs antes de abrir el formulario de incidencias del repositorio
  oficial en GitHub, con selección/exclusión de datos y anonimización de
  información privada; excluir credenciales y no adjuntar proyectos completos
  por defecto. Abrir el formulario con el resumen rellenado y permitir exportar
  un diagnóstico adjuntable para logs extensos; el usuario revisará y publicará
  la incidencia en GitHub. Mantener esta función independiente del puente MCP
  de P50, que continúa sin conexión con GitHub.

## Barra inferior y actividad centralizada en LANMON — 16/10/2026

- [x] **P53.** Retirar la fecha y hora (TIME/DATE) de la barra inferior de
  información de la GUI de LANCTL mostrada por el usuario. Trasladar el visor
  «Actividad» de esa barra al launcher LANMON, conservando el acceso a los
  mensajes de actividad de LANCTL. Actualmente son mensajes locales en memoria
  de la GUI (hasta 100), distintos del historial compartido y de los eventos de
  monitorización que ya muestra LANMON: definir su transporte y conservación
  para que el traslado no pierda información ni mezcle sus orígenes.
  Coordinar el visor con P49. Revisar el impacto en las interfaces CLI/TUI y
  conservar sus comandos, consultas de logs e historial y contratos públicos;
  retirar el reloj visual no elimina las marcas de tiempo de los registros.
  Verificar actividad entre procesos, selección de proyecto/sesión y cierre de
  ventanas, además de las regresiones relacionadas de GUI, CLI y TUI.

- [x] **P54.** Añadir accesos de texto «Web», «GitHub» y «Referencia» a la
  barra inferior de información de LANCTL, con estilo coherente con «CLI»,
  apertura en el navegador del sistema y distribución adaptable al ancho.
  Exponer también `lanctl -web`, `lanctl -github` y `lanctl -reference`,
  utilizables desde terminal y las consolas CLI/TUI, para abrir respectivamente
  `https://cctrgy.github.io/lanctl/`, `https://github.com/CctrGy/LANCTL` y
  `https://cctrgy.github.io/lanctl/reference/`. Mostrar asimismo la URL completa
  en la salida, clicable con el ratón en terminales compatibles mediante
  hipervínculos de terminal y/o su detección nativa de URLs; mantener texto
  legible en terminales sin soporte y en salida redirigida. Compartir las rutas
  entre GUI y CLI/TUI, verificar el comportamiento desde los ejecutables
  instalados y portables y actualizar ayuda, referencias CLI/web y completado
  Clink al incorporar estas opciones.

## Correcciones visuales de Topología LANWIRE — 17/10/2026

Implementadas en fuentes el 17/10/2026. La evidencia de comprobación y
sus límites se documentan en `docs/BACKLOG-VERIFICATION.md`.

- [x] **P55.** Sustituir la distribución en cuadrícula de los elementos
  conectados por una organización automática basada en sus conexiones reales.
  Evaluar un trazado jerárquico o de grafos por componentes que reduzca cruces,
  solapamientos y recorridos innecesarios, respete tamaños y puertos de cada
  equipo y maneje ramificaciones y ciclos. Reservar la cuadrícula para los
  elementos sin conexiones establecidas, separados del conjunto conectado.
  Conservar el movimiento manual y permitir reorganizar explícitamente.
  Validar con router, switches, paneles, tomas y suministro externo, además de
  componentes independientes: ningún equipo debe quedar tapado y las
  conexiones deben poder seguirse visualmente. No prometer un óptimo global:
  priorizar una distribución legible y reproducible.

- [x] **P56.** Corregir el anclaje visual de los cables a los elementos y sus
  puertos. En la captura del «Switch Rack» la línea termina fuera de la tarjeta,
  dejando un hueco en lugar de llegar a la conexión correspondiente. Revisar
  coordenadas, dimensiones y capas al desplazar nodos, aplicar zoom, redimensionar
  la ventana o desplazar la lista interna de puertos. Cuando el puerto quede
  oculto, mostrar un anclaje de borde identificable sin dejar extremos flotantes.
  Verificar también varios cables por equipo y enlaces seleccionados.

- [x] **P57.** Mejorar las etiquetas de los cables en Topología: el trazado
  no debe atravesar el nombre ni los extremos mostrados. Separar texto y línea,
  usar fondo/contraste acorde con grafito y lima y evitar colisiones con nodos
  y otras etiquetas. Mantener legibilidad según el zoom; si se abrevia el texto,
  permitir consultar el nombre y los extremos completos al señalar o seleccionar
  el cable. Comprobar nombres largos, cables próximos y distintos niveles de zoom.

- [x] **P58.** Optimizar automáticamente la distribución visual de los puertos
  de los switches. Adaptar filas, columnas, separación y tamaño de la tarjeta
  al número de puertos y a sus conexiones, coordinándolo con P55/P56 para
  facilitar el seguimiento de los cables y reducir cruces. Mantener etiquetas
  legibles y distinguir puertos libres y ocupados, sin cambiar sus nombres,
  numeración, identidad ni conexiones almacenadas por reorganizar su dibujo.
  Comprobar switches de 5, 12, 24 y 48 puertos, con distintas ocupaciones,
  tamaños de ventana y niveles de zoom; evitar recortes y scroll interno que
  oculte los puntos de conexión cuando sea posible.

- [x] **P59.** Trasladar la acción de conectar cables a la ventana de datos del
  propio elemento, en la pestaña de puertos/conexiones. Pulsar un puerto en el
  lienzo de Topología no debe sugerir ni iniciar una conexión: debe conservar
  la interacción de selección del elemento, y el doble clic abrir sus datos.
  Desde esa ventana se elegirá explícitamente el puerto y el cable compatible,
  mostrando ocupación y extremos existentes. Mantener las validaciones reales
  de compatibilidad y disponibilidad. Verificar que seleccionar, arrastrar y
  abrir un elemento desde el área de sus puertos no abra formularios de conexión
  inesperados ni cambie enlaces; comprobar el flujo de conexión desde sus datos.

- [x] **P60.** Representar los racks como contenedores de ubicación y filtros
  de Topología, sin dibujarlos como equipos de red independientes. Agrupar
  visualmente dentro de cada rack los elementos que ya tengan esa ubicación;
  distinguir los equipos sin rack asignado. Ofrecer «Todos los racks», selección
  de un rack y «Sin rack», manteniendo su registro editable en el inventario.
  Coordinar la distribución automática de P55 con las fronteras visuales de
  los contenedores para que no coloque fuera de ellos los equipos que contienen.

- [x] **P61.** Conservar y representar las conexiones entre equipos de distintos
  racks: la pertenencia física no limita la conectividad ni convierte el rack
  en extremo del cable. En la vista global, dibujar los enlaces cruzando los
  límites de sus contenedores y anclados a los puertos reales. Al filtrar un rack,
  señalar las conexiones salientes y su destino externo, con acceso para
  centrar/ver el equipo o rack de destino; no ocultarlas silenciosamente ni
  presentar un enlace existente como desconectado. Comprobar dos o más racks,
  equipos sin rack, enlaces internos y entre racks, filtros y zoom, sin alterar
  ubicaciones o conexiones almacenadas. Coordinar con P55, P56 y P60.

- [x] **P62.** Añadir dos niveles de visualización de Topología: «Interior del
  rack» y «Vista general de racks». La vista interior muestra los equipos,
  puertos y cables del rack elegido, conservando sus conexiones salientes (P61).
  La exterior representa cada rack como un contenedor contraído con su nombre
  o identificador (A, B, C…), y muestra sus enlaces hacia otros racks, equipos
  externos o suministros, siguiendo el esquema aportado por el usuario.
  Los puntos de entrada/salida del contenedor resumen extremos reales de sus
  equipos: no crean puertos físicos ni conexiones propias del rack. Los enlaces
  internos quedan disponibles al entrar en él. Permitir entrar mediante doble
  clic o acción explícita y volver a la vista general conservando posición,
  zoom y filtros; mostrar claramente el nivel y rack actuales. Ambas vistas
  deben representar el mismo inventario cargado, sin duplicar registros.

- [x] **P63.** Hacer legible la vista general con numerosos racks y conexiones
  en malla. El trazado debe admitir ciclos, enlaces paralelos y múltiples
  destinos, sin imponer una estructura de árbol ni reducirla a cinco líneas.
  Ofrecer agrupación visual desplegable de cables entre los mismos contenedores,
  indicando su cantidad y permitiendo consultar cada cable y sus extremos.
  Distinguir medios como fibra y cobre mediante etiquetas/leyenda además del
  color, y permitir filtrar, buscar, enfocar un rack y resaltar sus conexiones.
  Coordinar distribución, rutas y etiquetas con P55/P57/P60/P61/P62; mantener
  zoom, desplazamiento y minimapa para instalaciones grandes. Verificar racks
  A–G y escenarios de mayor tamaño, conexiones cruzadas, paralelas y salidas
  externas, sin perder ni inventar enlaces al agrupar, filtrar o cambiar de nivel.

Ámbito implementado: `gui/wire-gui.js`, `gui/physical-gui.js`,
`gui/launcher.css` y pruebas de interacción de LANWIRE/LANRACK. Mantener la estética actual y los datos y contratos del inventario.

## Agrupación de armarios por CPD en LANRACK — 17/10/2026

Implementado en fuentes el 17/10/2026; comparte el inventario físico con LANWIRE.

- [x] **P64.** Incorporar en LANRACK la entidad CPD, como sala o conjunto con
  nombre propio que contiene uno o varios armarios rack. Permitir crear,
  consultar y editar el nombre, descripción y ubicación del CPD, asignar o
  retirar racks y trasladarlos entre CPD. Distinguir los racks sin CPD asignado.
  Cada rack tendrá como máximo un CPD físico; conservar su identidad, equipos,
  unidades y conexiones al cambiar la agrupación. Retirar un rack del grupo o
  eliminar el CPD no debe borrar armarios ni su contenido; ofrecer conservarlos
  sin asignación o trasladarlos. La creación puede prepararse sin racks, pero
  debe mostrar expresamente que el CPD está vacío.

- [x] **P65.** Utilizar la agrupación por CPD en las visualizaciones de LANRACK:
  lista de armarios agrupable y filtrable por CPD, vista general de la sala con
  sus armarios y vista detallada de cada rack con sus unidades y equipos.
  Permitir navegar CPD → rack → equipo y volver conservando el contexto, con
  búsqueda por nombre de CPD o rack y resumen de armarios, capacidad y ocupación
  calculado desde los datos reales. Mantener nombres naturales y la estética
  actual. Acordar los formatos visuales adicionales antes de implementarlos.

LANRACK será responsable de gestionar esta organización física; reutilizar el
inventario y los servicios compartidos para que LANWIRE pueda reflejarla sin
mantener grupos duplicados. Coordinar con P60–P63, conservando las conexiones
entre racks y entre CPD. Antes de persistir el nuevo modelo, definir esquema
versionado, validación y migración compatible de los racks existentes, que
seguirán disponibles sin CPD asignado. Comprobar CPD con uno y varios racks,
nombres repetidos con identificadores distintos, cambios de pertenencia y
conservación de equipos y enlaces. La migración conserva los registros existentes y no modifica conexiones.

## Dimensiones de armarios rack — 17/10/2026

- [x] **P66.** Corregir la altura de los armarios rack para admitir únicamente
  valores enteros entre **4 y 52 U**, ambos incluidos; rechazar cualquier valor
  fuera del rango en creación y edición mediante validación compartida. Añadir
  como propiedad independiente de cada rack el **ancho de montaje en pulgadas**,
  limitado a **10, 19, 21 o 23**. Ambas dimensiones serán editables en **LANRACK**
  y visibles como datos en **LANWIRE**, con representación coherente en **GUI y
  TUI**. No confundir el ancho físico con la anchura visual de paneles o columnas.
  Persistirlas en el inventario físico compartido y el proyecto, sin duplicar
  datos por launcher; coordinar con P60–P65. Definir esquema versionado y
  tratamiento compatible de racks existentes sin ancho o con alturas fuera
  del nuevo rango: señalar los casos que requieran corrección, sin truncar,
  asignar dimensiones ni eliminar equipos silenciosamente. Impedir reducir
  la altura si deja equipos fuera del armario y conservar ubicaciones y enlaces.
  Verificar los límites 4/52 U, el rechazo de 3/53 U y valores no enteros, las
  cuatro anchuras admitidas y el rechazo de otras medidas; comprobar guardado,
  reapertura y consistencia entre launchers e interfaces.


## Frentes de equipos en LANRACK — 17/10/2026

- [x] **P66.** Superponer skins vectoriales genéricas en la elevación del rack:
  switches rackmount y de sobremesa, combinaciones RJ45/SFP, paneles,
  servidores, SAI, routers, bandejas y paneles ciegos. Catálogo de 30 plantillas
  y frente personalizado con vista previa, altura, montaje y conectores.
  Guardar apariencia versionada sin inventar puertos ni alterar conexiones;
  validar ocupación de varias U, traslados desde LANWIRE y límites del rack.
  Mantener vista simple, tamaño ajustable y estética grafito/lima.
  Implementado en fuentes; comprobaciones en `docs/BACKLOG-VERIFICATION.md`.


## Actualizaciones de herramientas propuestas por Dependabot — 17/10/2026

Estas ramas son propuestas automáticas de mantenimiento de dependencias Python
(`pip`), dirigidas a `main`. Los números corresponden a las herramientas, no a
versiones de LANCTL. En la revisión del 17/10/2026 ambas pull requests están
abiertas y pendientes de integración; cada una modifica únicamente su versión
fijada en el grupo opcional `dev` de `pyproject.toml`.

- [x] **P67.** Revisar e integrar, si supera las comprobaciones, la actualización
  de **Coverage 7.10.6 → 7.16.2**, propuesta en la rama
  `dependabot/pip/coverage-7.16.2` mediante la
  [PR #23](https://github.com/CctrGy/LANCTL/pull/23). Coverage mide las líneas y
  ramas de código ejercitadas por las pruebas. Ejecutar la suite con cobertura,
  comparar los resultados y revisar posibles diferencias en su cálculo, sin
  rebajar el umbral exigido para aceptar la actualización.

- [x] **P68.** Revisar e integrar, si supera las comprobaciones, la actualización
  de **Ruff 0.16.2 → 0.17.0**, propuesta en la rama
  `dependabot/pip/ruff-0.17.0` mediante la
  [PR #25](https://github.com/CctrGy/LANCTL/pull/25). Ruff realiza análisis
  estático y comprueba el formato de Python. Revisar sus cambios incompatibles,
  ejecutar `ruff check` y `ruff format --check` con la versión propuesta y
  evaluar cualquier modificación necesaria conservando la compatibilidad con
  las versiones Python admitidas por el proyecto.

P67/P68 validadas e incorporadas a las fuentes de la rama de trabajo: Python
3.10, reglas y umbral conservados; 483 archivos con formato correcto. Las dos
suites de Coverage pasan 1.208 pruebas y 645 subpruebas cada una, con un caso
POSIX omitido en Windows y 21 pruebas GUI heredadas excluidas por la política
existente. Ambas miden 69,3568 %: mismos contadores de líneas y ramas. Las PR
remotas permanecen sin fusionar y la integración en `main` sigue su revisión.

Son herramientas de desarrollo y CI: estas propuestas no añaden funciones al
programa, no representan versiones instalables alternativas y no cambian por sí
solas el número de versión de LANCTL. La integración se realizará en `main`
cuando se valide cada propuesta; las ramas estables, tags e instaladores ya
publicados conservarán su contenido original.


## Cierre de interfaz coordinado — 17/10/2026

P35, P46, P49, P51–P54 y P66 «Dimensiones» quedan implementados y
verificados localmente junto con sus adaptadores de escritorio. La evidencia
está en `docs/BACKLOG-VERIFICATION.md`. P45 tiene imágenes reales incorporadas;
el usuario comprobó las cinco opciones en Setup y confirmó que se ven completas
y distintas. La revisión visual es humana, sin captura automatizada. P47 enlaza
ICMP/ARP a interfaz/CIDR real y conserva el reintento; faltan otros transportes
y certificación con varias NIC. P48 ya pasa con CMD/Clink real y conserva la
certificación de desinstalación por otra cuenta. P32 registra la instalación
limpia de Windows y Linux amd64/arm64 por commit; el acceso externo sigue abierto.
P34, P40/P42 y P50 no se consideran completados por estas mejoras visuales:
AUDITOR continúa su trabajo interno por separado tras el paquete comprobado.
Los puertos de las skins permanecen decorativos y los datos se comparten entre
LANRACK y LANWIRE sin duplicar inventarios.

## Configuración editable según interfaz — 17/10/2026

- [x] **P69 · Completada en fuentes — 22/10/2026.** Corregir los cruces de configuración entre GUI, TUI y CLI:
  **Dependencia actualizada 22/10: REF-P69-settings y REF-P69-remote-lifecycle
  están completadas y verificadas en fuentes. Separación por interfaz y launcher
  implementada y verificada; los recursos visuales de GUI-DESIGN no se modifican.**
  cada interfaz solo podrá consultar y modificar sus preferencias específicas
  y los ajustes comunes del programa o proyecto. Definir en un catálogo
  compartido una lista explícita de ajustes editables, con ámbito de interfaz,
  launcher, programa/proyecto, validación y permisos administrativos cuando
  correspondan. No exponer variables internas, rutas de bases y locks,
  esquemas, identificadores, estado de ejecución ni secretos como ajustes.
  Usar `docs/CONFIGURATION-USER-REVIEW.txt` como referencia de revisión,
  contrastándolo con los consumidores y servicios actuales antes de implementar.
  Filtrar tanto los catálogos y menús como las operaciones de guardado en el
  backend: rechazar claves ajenas a la interfaz, internas o desconocidas aunque
  se invoque directamente el adaptador, sin cambios parciales. No confiar
  únicamente en controles ocultos ni en el nombre del launcher; el contexto
  de interfaz debe determinarlo el adaptador de entrada, no un valor arbitrario
  enviado por el cliente. Aplicar el criterio a los editores generales y por
  launcher, formularios específicos y rutas compatibles de configuración.
  Separar, por ejemplo, `startup.closeGuiOnLaunch` (GUI), las preferencias
  `tui.*` (TUI), el comportamiento CLI y `ip.listColumns` (CLI/TUI), conservando
  los ajustes funcionales comunes. Un CLI integrado conserva su contexto CLI.
  Mantener las preferencias existentes al ocultarlas de interfaces ajenas y
  conservar los servicios compartidos de validación, transacciones y permisos.
  Verificar la matriz de lectura/escritura GUI/TUI/CLI, los ajustes comunes,
  accesos directos al backend, permisos administrativos y ausencia de variables
  internas; actualizar ayuda y referencias si cambia el contrato de comandos.

  **Cierre:** lista explícita compartida; GUI/TUI/CLI y editores por launcher
  filtran lectura y rechazan escrituras ajenas sin cambios parciales. Proyecto
  compartido y valores ocultos conservados. LANWIRE TUI mantiene su archivo y
  valida claves/tipos antes de escribir. Las opciones locales explícitas
  `--tui-*`/`--close-gui-on-launch` conservan su contrato; no conceden excepciones
  al catálogo, formularios o sesiones remotas. Se impide también la autorización
  implícita de solicitudes remotas sin cambio de valor. **56 regresiones nuevas**;
  integral de **1.691 pruebas y 1.008 subpruebas**, una omisión POSIX, cero fallos;
  cobertura **72,4941 %**. Permisos, 1.243 firmas previas y configuración local
  conservados. Ayuda, referencias y catálogo actualizados. P71 puede reutilizar
  esta política; no se certifica todavía distribución nativa ni CI remoto.

## Explicación del servicio LANMON en el instalador — 17/10/2026

- [ ] **P70.** Sustituir el texto «Monitor service» por **«Servicio de
  monitorización en segundo plano (LANMON)»** en la selección de componentes
  del instalador. Añadir una explicación visible en esa pantalla: instala
  LANMON como servicio de Windows para ejecutar las comprobaciones de
  monitorización configuradas en segundo plano, sin mantener abierta la GUI
  ni una terminal. Aclarar que es opcional y que desmarcarlo no elimina LANMON
  ni impide utilizarlo de forma interactiva. Incluir el servicio LANMON entre
  los componentes marcados por defecto al seleccionar el tipo de instalación
  **Standard**, manteniendo la posibilidad de desmarcarlo en la selección
  personalizada. Actualmente el componente `monitor` solo declara los tipos
  `monitor custom`; corregir su pertenencia para incluir también `standard`
  y comprobar la selección inicial y los cambios del desplegable de tipos.
  Comprobar que el nombre completo
  y la explicación sean legibles sin recortes en el instalador; describir
  fielmente el comportamiento real del servicio. El cambio de selección
  predeterminada no modifica el funcionamiento del motor de monitorización.

  **Avance 21/10:** texto, explicación con altura calculada y selección Standard
  implementados; regresión de componentes correcta e Inno compila el Setup.
  Sigue pendiente revisar visualmente el recorrido nativo y cambios de tipo.

## Asistente de instalación por pasos — 17/10/2026

- [ ] **P71.** Reorganizar las opciones del instalador en cinco páginas de
  configuración, respetando este orden y coordinando P45–P47 y P70. Son pasos
  de opciones dentro del asistente; conservar las pantallas necesarias de
  destino, progreso y finalización sin repetir selecciones.

  1. **Integración y segundo plano:** casillas para añadir LANCTL al PATH y
     «Servicio de monitorización en segundo plano (LANMON)». Explicación breve
     del PATH y más detallada del servicio, su funcionamiento sin ventanas y
     su carácter opcional. Mantener LANMON seleccionado en Standard según P70.
  2. **Plugins incluidos:** selección individual de los complementos distribuidos
     por el autor de LANCTL, con selección de todos o ninguno y descripción
     breve. Instalar un plugin no debe omitir comprobaciones de firma, confianza
     ni permisos; reutilizar P46 sin volver a marcarlo como no implementado.
  3. **Tema general GUI:** elegir uno de los cinco temas de P45, con nombre y
     vista previa. Aplicar la selección a la estética general de todas las
     ventanas GUI de la suite mediante el contrato compartido, preservándola
     al actualizar. No trasladar preferencias visuales GUI a CLI/TUI.
  4. **Acceso remoto, solo en instalación avanzada:** permitir activar SSH y/o
     WEB-GUI y crear el usuario inicial y sus credenciales de acceso, con
     confirmación de contraseña y validación mediante servicios de LANACCESS.
     Mantener estos accesos desactivados salvo elección explícita. Permitir
     gestionar después varios usuarios con credenciales propias, no una única
     contraseña compartida. No guardar secretos en logs, argumentos de proceso
     ni respuestas persistentes del instalador; conservar usuarios existentes
     durante actualizaciones. No confundir estas cuentas con credenciales de
     dispositivos del inventario. Omitir la página en el recorrido normal.
  5. **Accesos directos:** cuadrícula con filas LANCTL, LANIP, LANWIRE, LANRACK,
     LANACCESS y LANMON, y columnas Escritorio y Barra de tareas de Windows.
     Selección independiente por aplicación y destino. Verificar los mecanismos
     oficiales de anclaje y su disponibilidad en las versiones de Windows
     admitidas; cuando requieran intervención del usuario, solicitar el anclaje
     o proporcionar la acción guiada, sin prometer un anclaje automático ni
     mostrar éxito si Windows no lo ha confirmado. Mantener separadas barra
     de tareas y menú Inicio.

  Al finalizar, conservar las opciones de abrir LANIP y realizar el primer
  escaneo de P47. Verificar avanzar/retroceder sin perder elecciones, recorrido
  estándar y avanzado, actualización conservando preferencias y correspondencia
  entre lo elegido y lo realmente instalado/configurado. Esta entrada define
  el flujo pendiente; no supone que las nuevas páginas estén implementadas.

  **Avance P71.4:** implementada la creación opcional de la primera cuenta
  administrativa del servicio mediante `lanaccess remote-setup`, ofrecida por
  Setup después de aplicar ACL. Formulario con confirmación, autenticación
  Scrypt existente, bloqueo entre procesos, rechazo de rutas incompatibles y
  conservación de cuentas al actualizar. Probada la integración navegador/API
  real en un almacén temporal. No activa listeners ni firewall y no completa
  las cinco páginas de P71. Falta la comprobación humana del recorrido elevado
  del instalador definitivo; la instalación silenciosa lo omite.

## Desinstalación completa de LANCTL — 17/10/2026

- [ ] **P72.** Hacer que la desinstalación elimine los componentes y datos
  propios de LANCTL, incluida la carpeta **Documentos/LanCTL** con sus proyectos
  y archivos, además de ejecutables, plugins, preferencias, configuración,
  bases, credenciales, registros, cachés, temporales y copias de seguridad
  gestionadas por la aplicación. Mostrar en el desinstalador que la eliminación
  completa incluye proyectos y credenciales y no conserva datos para reinstalar.
  Resolver Documentos mediante la carpeta conocida de Windows, contemplando
  redirección a OneDrive y ubicaciones heredadas. Inventariar también los datos
  de usuario y servicio en ProgramData, LocalAppData y otras rutas propias
  realmente utilizadas, sin asumir que todas pertenecen a la cuenta elevada.
  Detener y retirar servicios y procesos de LANCTL; eliminar sus accesos
  directos, entrada propia del PATH, registro Clink, reglas de firewall y
  registros del sistema creados por la instalación. Coordinar con P48 y P71.
  Utilizar un inventario de instalación y validar cada ruta absoluta antes de
  borrar recursivamente; no seguir enlaces o redirecciones fuera del destino
  previsto ni borrar carpetas compartidas o archivos ajenos por su nombre.
  Las ubicaciones personalizadas requieren identificar los recursos propios,
  sin vaciar indiscriminadamente el directorio elegido por el usuario.
  Contemplar errores de permisos y archivos bloqueados y comunicar cualquier
  resto que no se haya podido retirar. No prometer borrar copias externas,
  históricos de Windows/OneDrive o datos de otras cuentas sin acceso autorizado.
  Separar desinstalación definitiva de actualización: actualizar debe conservar
  los datos y preferencias existentes. Verificar instalación/desinstalación y
  reinstalación limpia, carpetas heredadas, servicio, cuenta distinta y rutas
  personalizadas, comprobando ausencia de restos propios y conservación de
  contenido ajeno.

## Sincronización global de proyecto — 18/10/2026

- [ ] **P88 · Alta · En curso.** Centralizar el cambio de proyecto de las GUI
  exclusivamente en la GUI principal de LANCTL y actualizar todos los launchers
  abiertos. **Criterio revisado por el usuario — 18/10/2026:** retirar los
  selectores y acciones de cambio de proyecto de las GUI de los launchers;
  sustituye la propuesta anterior de cambiar desde LANWIRE o cualquier selector.
  Mostrar el nombre del proyecto de trabajo en la barra inferior de LANIP,
  LANWIRE, LANRACK, LANACCESS y LANMON, como información sin selector. Coordinar
  el acceso a LANCTL con P75. Verificar que el nombre corresponde al contexto
  real de los datos y se actualiza al completar el cambio, sin anunciar un
  proyecto nuevo mientras se muestran datos del anterior. Esta restricción
  corresponde a las GUI y no retira contratos públicos CLI/TUI. Causa confirmada:
  `Session` fijaba la selección inicial y los servicios GUI mantenían rutas antiguas.
  Plan: reconciliar la configuración compartida en `core/session.py`, conservar
  una instantánea por operación en Core, renovar los servicios GUI y refrescar
  selector/inventario juntos. Rechazar formularios de otro proyecto sin perder
  sus datos y conservar las operaciones ya iniciadas en su workspace original.
  Archivos: Core de configuración/sesiones, adaptadores Suite/Launcher/LANIP,
  integración RPC en JS y pruebas de coordinación/GUI/TUI. Dependencias:
  coordinador y workspaces existentes; no depende del rediseño GUI-DESIGN.
  Riesgo alto: escrituras cruzadas, escaneos concurrentes y preferencias guardadas
  desde instantáneas antiguas. Verificar procesos reales, cambios sin guardar,
  APIs existentes y suite completa antes de cerrar.
  Se identifica como P88 para evitar reutilizar P74, que corresponde a la
  clasificación de elementos interiores, de entorno e independientes de racks.
  **Subestado técnico — 18/10/2026:** sincronización Core/adaptadores corregida
  en fuentes: selección compartida, renovación de servicios, protección de
  formularios antiguos y preferencias, y contexto estable para operaciones ya
  iniciadas. Conserva firmas públicas e IDs; detalle de pruebas en
  `BACKLOG-VERIFICATION.md`. El inventario físico sigue en su almacén compartido
  existente, sin migrarlo ni incorporarlo ficticiamente al VLF.
  **Actualización — 18/10/2026:** selección gráfica centralizada en LANCTL y
  nombre informativo en el pie de los cinco launchers, con sus accesos LANCTL.
  Pruebas de navegador con las seis ventanas y servicios reales. Los arranques
  de LANRACK, LANWIRE y LANACCESS ya no convierten rutas predeterminadas en
  overrides fijos: siguen los almacenes del proyecto; los argumentos explícitos
  siguen teniendo prioridad. Las APIs y los comandos anteriores se conservan.
  **Pendiente de entrega de P88:** reconstruir instalables y repetir la
  validación de las ventanas compiladas. No se considera publicado por estar
  corregido únicamente en las fuentes.

## Inicio gráfico sin consola adicional — 17/10/2026

- [ ] **P73.** Corregir el arranque de las GUI de LANCTL y sus launchers desde
  los accesos directos para que no aparezca una terminal adicional del backend,
  ni permanezca visible ni parpadee durante el inicio. Revisar el empaquetado
  Windows y los destinos de los accesos del menú Inicio, escritorio y barra
  de tareas, coordinándolo con P71. Conservar el funcionamiento de CLI/TUI,
  entrada/salida estándar, redirecciones y códigos de salida; no desactivar
  indiscriminadamente la consola de todos los ejecutables. Tampoco ocultar o
  cerrar una terminal existente del usuario al invocar un modo gráfico desde
  ella. Mantener el registro de errores y logs compartidos y su consulta en
  LANMON, incluidos los fallos de arranque gráfico; ofrecer información útil
  si la GUI no llega a abrirse. Verificar los seis launchers en instalación
  y portable, apertura desde accesos y desde terminal, lanzamiento de otras
  GUI desde LANCTL y apertura explícita de CLI/TUI y LANMON desde la GUI.

  **Avance 21/10:** host `lanctl-window.exe` con subsistema Windows GUI y lista
  cerrada de launchers, accesos GUI de Setup y apertura entre GUI actualizados.
  Los seis ejecutables de consola conservan su contrato. 47 pruebas de rutas,
  errores, distribución y suite GUI pasan. Host compilado: subsistema PE 2;
  LANCTL de consola conserva PE 3. Pendiente certificación nativa instalada y
  portable; el build de comprobación no es una entrega estable.

## Elementos interiores, de entorno e independientes de racks — 18/10/2026

- [x] **P74 · Implementado en fuentes y verificado.** Incorporar la clasificación de elementos físicos mediante
  `location.rack`, `location.in_rack` y `location.unit`, distinguiendo:
  **interior del armario** (`rack` con ID existente, `in_rack: true`, `unit`
  entero desde 1 hasta la altura del rack); **entorno dependiente del armario**
  (`rack` con ID existente, `in_rack: false`, `unit: 0`); e **independiente**
  (`rack: null`, `in_rack: false`, `unit: 0`), como CM-00 en el caso del usuario.
  Un switch rackmount o patchpanel pertenece al interior; las tomas de pared
  atendidas por ese rack pertenecen a su entorno, conservando su conexión al
  puerto concreto del patchpanel. La pertenencia y el cableado son relaciones
  independientes: asignar un rack no crea conexiones, y un elemento independiente
  puede conectarse a equipos de un rack sin pertenecer a su entorno.
  Editar esta clasificación mediante servicios compartidos y representarla
  coherentemente en LANRACK y LANWIRE, GUI y TUI: interiores en la elevación,
  elementos de entorno alrededor del armario e independientes fuera de los
  grupos de rack. Conservar identidades, puertos y conexiones al reclasificar,
  filtrar o cambiar de vista; mantener visibles o consultables los enlaces
  entre racks, entornos e independientes. Coordinar con P60–P66 y la agrupación
  por CPD, sin confundir dependencia de un rack con pertenencia a una sala.
  Validar combinaciones, existencia del rack, capacidad y solapamientos según
  la altura ocupada por cada elemento; las posiciones empiezan en U1 aunque
  la altura permitida del armario sea de 4–52 U. Persistir en el inventario y
  proyecto compartidos con esquema versionado y migración compatible: una
  posición antigua válida puede identificar montaje interior, pero una
  asociación sin posición definida requiere revisión y no debe convertirse
  silenciosamente en elemento de entorno. Verificar las tres situaciones,
  reclasificación y cambio de rack, guardado/reapertura y conservación de enlaces
  reales, incluidos toma-patchpanel y CM-00 conectado sin rack asignado.

## Acceso a LANCTL desde la barra de los launchers — 18/10/2026

- [ ] **P75.** Añadir un botón de texto **«LANCTL»** en la barra inferior de
  información de las GUI de LANIP, LANWIRE, LANRACK, LANACCESS y LANMON, con
  estilo coherente con los accesos de esa barra. Abrir desde él la interfaz
  principal de LANCTL para poder iniciar cualquier otro launcher, incluso
  cuando la aplicación actual se haya abierto directamente desde un acceso
  externo. Si LANCTL ya está abierto, enfocar su ventana cuando sea posible
  sin crear duplicados innecesarios. Conservar el contexto del proyecto al
  abrirlo y no guardar, descartar cambios ni cerrar el launcher de origen
  implícitamente; respetar las políticas explícitas de apertura/cierre del
  programa. Utilizar los mecanismos compartidos de lanzamiento y coordinación,
  manteniendo el arranque gráfico sin consola adicional de P73. Verificar los
  cinco launchers, LANCTL abierto y cerrado, proyectos distintos en varias
  sesiones, cambios sin guardar e instalación/portable. Esta entrada corresponde
  a las barras GUI; no introduce preferencias gráficas en CLI/TUI (P69).

## Colocación y bandejas en LANRACK — 18/10/2026

- [x] **P76 · Implementado en fuentes y verificado.** Permitir seleccionar un elemento en LANRACK y moverlo a otra
  posición U del armario mediante una acción explícita de reubicación. Mostrar
  la posición actual y los destinos disponibles y validar el movimiento antes
  de persistirlo, sin cambiar identidad, puertos ni conexiones. Gestionar las
  posiciones desde LANRACK y reflejarlas en LANWIRE, GUI y TUI; coordinar con
  P66 y P74 y utilizar servicios compartidos y actualización transaccional.

- [x] **P77 · Implementado en fuentes y verificado.** Completar la edición y representación de elementos que ocupan
  varias unidades U consecutivas. Conservar y unificar el cálculo de altura
  ocupada ya existente, evitando un segundo campo o cálculo incompatible.
  Permitir indicar la altura del elemento además de su unidad de inicio;
  representar toda su extensión y reservar esas posiciones. Rechazar alturas
  no enteras o menores que 1, solapamientos y colocaciones que excedan la
  altura del armario (4–52 U), tanto al crear como al mover o redimensionar.
  Verificar elementos de 1 U y varias U, límites y cambios concurrentes.

- [x] **P78 · Implementado en fuentes y verificado.** Incorporar las **bandejas** como elementos físicos identificables
  y editables en LANRACK, con posición y altura en U configurables, capaces
  de contener varios dispositivos pequeños; caso de referencia: **OTG y router
  neutro en una misma bandeja**. Reutilizar o evolucionar las representaciones
  `tray` existentes en lugar de crear tipos visuales incompatibles. Definir
  una relación explícita entre bandeja y dispositivos alojados: la bandeja
  reserva las U en el armario y sus dispositivos no vuelven a ocupar esas U
  como montajes independientes. Conservar los dispositivos como registros
  propios con sus puertos y enlaces, mostrar su pertenencia a la bandeja y
  permitir incorporarlos o retirarlos. Mover la bandeja debe trasladar su
  contenido de forma coherente; impedir ciclos de contención y no borrar sus
  dispositivos al retirar la bandeja: resolver explícitamente su reubicación.
  Coordinar `rack`, `in_rack` y `unit` con P74 y definir el esquema versionado
  y la migración antes de persistir la relación, sin inventar posiciones de
  montajes directos para los dispositivos alojados. Representar bandeja y
  contenido en LANRACK y LANWIRE, GUI/TUI, conservando todas sus conexiones.
  Verificar bandejas vacías y con varios equipos, cambio de tamaño, movimiento,
  retirada de contenido y guardado/reapertura. Depende del modelo de ocupación
  y movimiento de P76/P77; estas tareas amplían las capacidades existentes
  y se han implementado como relaciones de inventario, además de la skin.
  La conversión explícita de bandejas de `layout` conserva la descripción
  heredada y retira el dibujo duplicado en la misma transacción. Las bandejas
  montadas ofrecen «Alojar dispositivo»; su retirada requiere reubicación.

## Error al finalizar un escaneo de red — 18/10/2026

- [x] **P79 · Corregido en fuentes.** Investigar el error mostrado en la GUI al terminar de escanear
  una red. Reporte del usuario, pendiente de reproducción y diagnóstico:

  ```text
  'idf'
  Origen: LANCTL.GUI.Desktop.Response
  Código: GUI.DESKTOP.FAILED
  ID: 0e4FDE31E6
  ```

  No se ha aportado versión, traza completa ni confirmación de si los resultados
  del escaneo se conservaron. Correlacionar el ID con los registros y localizar
  el origen real antes de atribuir una causa al mensaje `'idf'`. Revisar la
  finalización del escaneo y la actualización de resultados en la GUI. Criterio
  de cierre: reproducir el caso, corregir su causa y verificar que el escaneo
  finaliza y muestra sus resultados sin este error, con regresión del caso
  identificado. Si se modifican puntos de error, regenerar y comprobar
  `errorList.txt` mediante `tools/generate_error_catalog.py`.

  **Cierre 21/10:** reproducido tras editar IDF/IP: el historial aceptaba esos
  campos pero no generaba sus etiquetas ni los restauraba al deshacer. Corregidas
  etiquetas, deshacer/rehacer y comprobación bajo locks. Regresión de edición,
  escaneo, guardado, reapertura y deshacer/rehacer. También corregida la paleta
  IDF de filas inactivas (fallo independiente). 42 pruebas relacionadas pasan.

## Errores al cerrar LANIP guardando o descartando cambios — 18/10/2026

- [x] **P80 · Corregido en fuentes.** Revisar el cierre de la ventana de LANIP al elegir descartar
  los cambios sin guardarlos. El usuario informa de este mensaje durante esa
  acción; pendiente de reproducción y diagnóstico:

  ```text
  no se puede reemplazar un workspace con cambios pendientes mientras otra sesión utiliza el proyecto; guarda o cierra esa sesión

  Origen: LANCTL.GUI.Desktop.Response
  Código: GUI.DESKTOP.FAILED
  ID: 0e4FDE31E6
  ```

  **Ampliación del reporte:** al intentar cerrar LANIP eligiendo guardar los
  cambios también aparece un error. En este caso el usuario aporta únicamente:

  ```text
  Origen: LANCTL.GUI.Desktop.Response
  Código: GUI.DESKTOP.FAILED
  ID: 0e4FDE31E6
  ```

  No se ha aportado un mensaje descriptivo para el caso de guardar ni confirmado
  si los cambios llegaron a persistirse o la ventana se cerró. Investigar ambas
  rutas por separado y comprobar guardado efectivo y reapertura del proyecto;
  el código e ID comunes no demuestran que tengan la misma causa.

  El mensaje indica otra sesión usando el proyecto, pero el reporte no confirma
  qué otras ventanas o sesiones estaban abiertas, ni si LANIP llegó a cerrarse.
  Revisar la coordinación de sesiones y el tratamiento del workspace al
  descartar durante el cierre. Definir el alcance del descarte cuando existen
  cambios compartidos y permitir un cierre coherente sin guardar implícitamente
  ni perder cambios de otras sesiones. Comprobar una y varias sesiones, cambios
  pendientes, guardar/descartar/cancelar y conservación del proyecto. Registrar
  por separado de P79: ambos reportes muestran el mismo origen, código e ID,
  pero mensajes y acciones distintos; revisar también la trazabilidad del
  origen real sin asumir que comparten causa. Si se modifican puntos de error,
  regenerar y comprobar el catálogo mediante `tools/generate_error_catalog.py`.

  **Cierre 21/10:** descartar cierra esta ventana y conserva cambios si otra
  sesión usa el proyecto; en exclusiva restaura el VLF. El diálogo explica
  ese alcance. La GUI resuelve el cierre; el envoltorio CLI no repite el
  guardado, evitando guardar otro proyecto seleccionado justo después desde
  otra sesión. Se comprueban las dos decisiones con esa carrera real simulada.
  Pasan nueve combinaciones guardar/descartar/cancelar y sesiones compartidas,
  además de fallo de guardado sin cierre y la prueba de diálogo en navegador.
  El caso de guardar tras editar IDF queda cubierto por la regresión P79;
  no se atribuyen a esa causa errores distintos sin su diagnóstico.

## Simplificación de LANRACK y edición desde las vistas — 18/10/2026

- [x] **P81 · Completado en fuentes — 20/10/2026.** Simplificar la GUI de
  LANRACK según la revisión del usuario.
  Eliminar el deslizador que ajusta el tamaño visual de las unidades: la escala
  de la interfaz debe adaptarse automáticamente al redimensionar la ventana,
  sin cambiar las dimensiones físicas ni la altura U de los equipos o racks.
  Reducir al mínimo el cuadro de datos y colocar «Volver a la sala» y
  «Ver unidades simples» como botones sencillos en la parte superior.
  Conservar las acciones «Actualizar», «Nuevo CPD» y «Nuevo rack». Retirar de
  esta vista el botón «Abrir LANWIRE»; coordinar la navegación general con P75.
  Esta petición sustituye el ajuste manual de tamaño visual contemplado en
  la tarea de frentes de equipos P66. Comprobar distintas dimensiones de ventana,
  legibilidad y acceso a todos los controles y unidades, sin solapamientos.
  **Verificado:** cabecera compacta fija al desplazar, escala automática con
  mínimo legible, vistas simple/frentes y equipos multi-U; edición y datos
  conservados. Suite completa: 1.317 pruebas, 645 subpruebas, una omisión POSIX
  en Windows; cobertura combinada 70,5093 %. Falta entregar un nuevo compilado.

- [x] **P82 · Completado en fuentes — 20/10/2026.** Hacer que todas las interfaces de visualización de datos permitan
  también editar los datos gestionables que presentan, para reducir la necesidad
  de abrir y alternar ventanas. Aplicar este criterio transversal al revisar
  las vistas existentes, incluidos LANRACK y LANWIRE; no depender de abrir otro
  launcher para editar un elemento mostrado. Reutilizar los servicios compartidos,
  validaciones y permisos, manteniendo como solo lectura los valores derivados
  o internos que no sean editables. Conservar selección y contexto al editar,
  reflejar los cambios en las demás vistas y verificar persistencia y reapertura.
  Coordinar con P69 y P76–P78, sin duplicar inventarios ni reglas de negocio.
  **Alcance LANRACK/LANWIRE completado — 18/10/2026:** edición desde la ficha,
  ubicación, altura, bandejas, puertos/conexiones y dimensiones del rack;
  refresco entre vistas y persistencia verificados. P76–P78 quedan resueltos.
  **Alcance transversal completado — 20/10/2026:** LANMON permite editar
  identidad e IP y pertenencias a grupos existentes; LANACCESS edita el usuario
  conservando el secreto, con rotación explícita y confirmación. La extracción
  previa REF-P82-inventario comparte las reglas de LANIP sin retirar su API.
  Se conservan selección y filtros; las revisiones y la guarda P88 rechazan
  formularios obsoletos o de otro proyecto. Grupos protegidos, datos derivados,
  registros internos y permisos remotos mantienen sus restricciones.
  LANIP, LANCTL y CLI/TUI se revisan con sus editores/acciones ya existentes.
  P69 sigue separado como revisión del catálogo de preferencias.
  **Verificado:** 1.344 pruebas y 645 subpruebas correctas, una omisión POSIX;
  cobertura 70,6906 % y 1.292 firmas públicas conservadas. Falta entrega compilada.

## Barras inferiores sin reloj — 18/10/2026

- [x] **P83 · Completado en fuentes — 21/10/2026.** Retirar el reloj de hora actual que el usuario sigue viendo en
  las barras inferiores de algunos launchers. Completar el alcance visual de
  P53 comprobando LANCTL, LANIP, LANWIRE, LANRACK, LANACCESS y LANMON, incluidos
  los arranques directos. Conservar las marcas de tiempo de logs y eventos.
  Coordinar la barra con P88 «Sincronización global de proyecto» y P75 para
  mostrar el nombre del proyecto y los accesos correspondientes sin reloj,
  con disposición legible al redimensionar la ventana.
  **Verificado:** reloj retirado de la plantilla común de LANWIRE/LANRACK/
  LANACCESS/LANMON y sus prototipos; LANCTL y LANIP ya no lo mostraban.
  Proyecto, navegación y refresco de datos conservados. Ocho regresiones nuevas
  comprueban los seis pies, tamaños 1440×900 y 800×600, y fechas/horas de logs,
  actividad, incidencias y eventos. Suite completa: 1.352 pruebas y 645 subpruebas
  correctas, una omisión POSIX; cobertura 70,6906 %. Falta entrega compilada.

## Acciones de creación en LANWIRE — 18/10/2026

- [x] **P84 · Implementado y verificado en fuentes.** Ampliar y organizar las opciones generales de LANWIRE para
  crear elementos desde su propia interfaz. Incluir una acción visible para
  crear cables o enlaces («wire») y revisar qué otros tipos de elementos
  gestionables carecen de acción de alta, exponiendo las operaciones compatibles
  con el modelo existente. Tomar como referencia la disponibilidad de acciones
  de creación de LANRACK, como «Nuevo rack», y mejorar la interfaz para ofrecer
  explícitamente «Nuevo CPD» («new CPD» en el reporte). Coordinar esta última
  acción entre LANWIRE y LANRACK con P81, manteniendo nombres y comportamiento
  coherentes. Permitir crear y editar sin abrir otro launcher, según P82;
  reutilizar el inventario y servicios compartidos, sus validaciones y permisos.
  Crear en el proyecto activo sin introducir selectores de proyecto en los
  launchers (P88). Verificar altas desde un proyecto vacío y con datos,
  validación de extremos y puertos para los cables/enlaces, cancelación,
  actualización de vistas y conservación tras guardar y reabrir el proyecto.
  **Cierre 21/10:** resuelta REF-P84. Acciones Nuevo cable/rack/CPD, edición
  y asignación de CPD, extremos opcionales validados atómicamente y selección
  del elemento creado. 28 pruebas de creación/launchers pasan, incluida GUI
  real en Edge sin ventanas nativas y reapertura en una instalación vacía.
  Los tres fallos conocidos anteriores son ahora regresiones normales que pasan.

- [x] **REF-P84 — Alta: aislamiento y persistencia del inventario físico.**
  Implementado en fuentes el 21/10/2026: base por proyecto, entrada VLF física
  versionada, cambios pendientes, guardado/verificación y migración explícita
  sin borrar la base global. Pasan las tres regresiones originales y 11 casos
  adicionales; desbloquea P84. Ampliado con rechazo de recreación silenciosa de
  bases físicas desaparecidas y guardado automático de cambios desde GUI.
  Decisión humana confirmada: conservar la base antigua e importar explícitamente.
  Se conserva debajo el diagnóstico que originó la tarea:
  Prioridad anterior a P84/P85. Al cambiar First → Second, racks, cables y CPD
  siguen apareciendo desde la base física global. Los cambios físicos no
  marcan el proyecto como pendiente y guardar el VLF no permite recuperarlos
  en una instalación limpia. No equivale a pérdida del archivo global original,
  que permanece en disco, pero sí impide transportar y restaurar esos datos
  con el proyecto y puede provocar modificaciones sobre la red equivocada.
  Revisar `core/projects/workspace.py`, `save_policy.py`, `fingerprint.py`,
  `vlf.py`, configuración/rutas y los adaptadores IDF y LANWIRE/LANRACK.
  Requiere formato físico versionado compatible, aislamiento por proyecto,
  detección de cambios, guardado/verificación/reapertura y una transición
  explícita del inventario global histórico sin asignarlo arbitrariamente
  a un proyecto. Conservar IDs, relaciones, CPD, puertos, frentes y ubicaciones.
  Riesgo de implementación **Alto**; impacto transversal en CLI/TUI/GUI y
  recuperación de proyectos. Plan detallado y tres reproducciones:
  `BACKLOG-VERIFICATION.md`, sección REF-P84.

## Doble clic sin datos del elemento en LANWIRE — 18/10/2026

- [ ] **P85 · Fuentes verificadas; pendiente distribución nativa.** Corregir la acción predeterminada del doble clic sobre un
  elemento de LANWIRE para mostrar directamente sus datos y permitir editarlos
  según P82. En la captura del usuario, el elemento «OTG de compañía» abre
  el diálogo «Acciones · OTG de compañía», que solo muestra botones como
  «Ver y editar datos», «Centrar» y opciones de conexiones/ramas, sin presentar
  los datos del elemento. Evitar ese paso intermedio para consultar la ficha;
  conservar las demás acciones accesibles por controles apropiados. Este reporte
  contradice el comportamiento esperado de doble clic ya descrito en las
  correcciones visuales de Topología: verificarlo en la GUI distribuida antes
  de darlo por resuelto. Comprobar distintos tipos de elementos, selección
  correcta, apertura de datos sin modificaciones implícitas, edición,
  cancelación y guardado sin perder el contexto de la topología.

  **21/10:** doble clic abre datos también en racks; «Ver interior del rack»
  queda como acción contextual explícita. Verificados OTG, switch, tomas y
  rack en navegador con API real. Falta contrastar el instalable que originó
  la captura y entregar el nuevo; no se confunde fuente actual con binario.

## Visibilidad de nombres de cables en LANWIRE — 18/10/2026

- [x] **P86 · Implementado y verificado.** Añadir al diagrama de flujo/topología de LANWIRE un botón
  para alternar entre «Ocultar nombres de cables» y «Mostrar nombres de cables».
  Aplicarlo a las etiquetas de los cables del diagrama, manteniendo visibles
  los enlaces y sin modificar nombres ni datos del inventario. Indicar claramente
  el estado y permitir recuperar los nombres con la misma acción. Conservar la
  elección al refrescar la vista durante la sesión y verificar la alternancia
  con distintos niveles de zoom, selección y edición de elementos, sin perder
  conexiones ni alterar la disposición del diagrama.

## Tamaño visual de las tomas de pared en LANWIRE — 18/10/2026

- [x] **P87 · Implementado y verificado.** Reducir las tarjetas de las tomas de red genéricas de pared en
  el diagrama de flujo/topología de LANWIRE a aproximadamente **una cuarta
  parte del tamaño visual actual**, para distinguir su escala de la de equipos
  como switches y routers. Usar como referencia una cuarta parte del área
  ocupada, sin reducir automáticamente ancho y alto al 25 % (lo que supondría
  un área de 1/16). Mantener identificador, puertos y conexiones legibles y
  seleccionables; adaptar anclajes de cables, distribución y límites de
  selección a las nuevas dimensiones. Conservar el doble clic para consultar
  los datos según P85 y verificar diferentes niveles de zoom y varias tomas
  próximas. El cambio afecta a su representación GUI, no a dimensiones físicas,
  identidad, pertenencia al rack ni conexiones del inventario.


## Estado de los cambios de elementos solicitados — 18/10/2026

P74, P76, P77 y P78 completados en fuentes; P66 conservado y ampliado con la
misma validación de ocupación. P82 completado también en su alcance transversal
el 20/10/2026. P88 completado en fuentes/GUI webview;
pendiente de entrega compilada. Las pruebas y contratos se detallan en
`BACKLOG-VERIFICATION.md`.

Actualización del orden — 22/10/2026: P81, P89, P82, P83, REF-P84, P84,
P79/P80 y P86/P87 completados en fuentes. P85, P70 y P73 tienen corrección
en fuentes y comprobación automatizada; conservan su verificación nativa pendiente.
REF-P34-runtime, REF-P84-save-modes y REF-P84-session también quedan completadas en fuentes.
REF-P69-settings, REF-P69-remote-lifecycle y P69 quedan completadas.
Sigue REF-P34-migration para la adopción del runtime y el estado
global de P34.
La publicación estable sigue su propia validación y no se declara completada
con estos cambios.

Validación del bloque del 18/10: 1.313 pruebas + 645 subpruebas correctas,
una prueba POSIX omitida en Windows, cobertura combinada 70,5093 %, 283 firmas
públicas conservadas y controles de calidad correctos. Pendientes de entrega:
CI de GitHub y compilación/validación de instalables con estas fuentes.

## Desajuste del editor de frentes — 20/10/2026

- [x] **P89 · Media · Completado en fuentes — 20/10/2026.** Alinear el límite
  de altura del editor de frentes con
  las 1–52 U ya admitidas por el inventario. `rack-skins.js` mantiene un máximo
  HTML de 8 y recorta la previsualización a 8; un equipo válido de 12 U abre
  su ficha con `rangeOverflow`, impidiendo guardar su frente.
  Reproducido en Edge con inventario temporal: valor 12, máximo 8, campo inválido.
  Afecta a `gui/rack-skins.js` y `tests/test_rack_skins.py`; depende de la
  ocupación compartida P77 ya resuelta. Riesgo **Medio** por alturas límite,
  previsualización y colisiones; conservar el límite de capacidad del rack
  validado en Core. Añadir regresiones para equipos de más de 8 U y rechazos
  fuera del rango o sin espacio, sin cambiar IDs, puertos ni conexiones.
  Se ha resuelto antes de la ampliación transversal de P82 por afectar a datos
  válidos que ya podían crearse. El campo y la previsualización admiten ahora
  1–52 U; el Core sigue rechazando falta de espacio o colisiones.
  Guardado/reapertura de 9/12/52 U y conservación de puertos y cables verificados.

## Cierre P81/P89 — 20/10/2026

Suite completa del estado final, con Edge y pruebas GUI históricas:
**1.320 pruebas y 645 subpruebas correctas, una omisión POSIX en Windows**.
Cobertura combinada **70,5093 %**; contratos revisados, formato, seguridad,
referencias y catálogo de errores correctos. Evidencia y archivos en
`BACKLOG-VERIFICATION.md`.

Pendientes tras P81/P89: P82 (cerrado en el bloque siguiente), restantes tareas abiertas del backlog,
CI nueva de GitHub y reconstrucción/validación de instalables. Los bloqueos
previos de ciclo de vida de plugins y editor/firma oficial se mantienen.
Las correcciones de este bloque están en las fuentes de `experimental-gui`;
el ejecutable instalado todavía requiere una entrega nueva.

## Cierre P82 — 20/10/2026

Dependencias revisadas: P76–P78 y P88 disponibles; extracción
REF-P82-inventario completada antes de ampliar LANMON. Se conservan contratos,
permisos y formatos persistentes. La edición desde las demás vistas queda
verificada con servicios reales, dos editores simultáneos, cambio de proyecto,
cancelación, selección/filtros, guardado/reapertura y navegador Edge.

Suite completa final: **1.344 pruebas y 645 subpruebas correctas**, una omisión
POSIX en Windows, **274,35 s**, cobertura **70,6906 %**. Sin cambios ni bajas
en **1.292 firmas públicas** de 283 archivos respecto al inicio de P82.
Ruff/formato, referencias CLI/web, catálogo de 1.476 errores, higiene y
comprobación del diff correctos; Bandit sin hallazgos medios/altos.
Informe y evidencias: `BACKLOG-VERIFICATION.md`, sección P82.

Al cerrar P82 quedaban pendientes P69 y las demás tareas abiertas, empezando
en esta secuencia visual por P83, completado en el bloque siguiente.
La verificación de CI de GitHub sobre estas fuentes y la
reconstrucción/validación de instalables son posteriores. Se mantienen los
bloqueos de runtime de plugins y editor/firma oficial; no se declara una estable.

## Cierre P83 — 21/10/2026

Las seis GUI quedan verificadas sin reloj en sus barras inferiores, conservando
fechas y horas de diagnóstico, proyecto, navegación y refresco automático.
Cambios de presentación limitados a `gui/launcher.{html,js}` y
`gui/launcher-prototypes.{html,js}`. Los 287 archivos comparados conservan sus
bytes: todos los fuentes Python y los componentes de fechas de LANIP, LANCTL
y registros de LANMON. Contratos públicos, permisos y datos no cambian.

Se añade `tests/test_launcher_footers.py` y se elimina una intermitencia de
`tests/test_errors.py`: un UUID aleatorio podía contener el secreto breve de
prueba `abc` y producir un falso positivo. Se fija el UUID de la prueba sin
debilitar sus aserciones ni cambiar el servicio de errores.

Suite completa final: **1.352 pruebas y 645 subpruebas correctas**, una omisión
POSIX en Windows, **296,51 s**, cobertura **70,6906 %**. Ruff/formato, sintaxis JS,
seguridad, higiene, referencias y catálogo de 1.476 errores correctos.
Detalles y evidencias en `BACKLOG-VERIFICATION.md`, sección P83.

Estado histórico anterior a la reanudación: **REF-P84** bloqueaba P84. P69 y los demás pendientes
mantienen su alcance. P88 conserva su verificación de selección y guardas de
contexto; no demuestra aislamiento ni persistencia del inventario físico.
Falta validar estas fuentes en CI remoto y reconstruir/probar los instaladores;
el ejecutable instalado no se ha actualizado. No se publica una versión estable.
