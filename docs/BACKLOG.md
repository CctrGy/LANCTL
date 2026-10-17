# Trabajo pendiente de LANCTL

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
y 10 subpruebas. Integración visual P34/P47 en curso en GUI-DESIGN. P68 revisada:
Ruff 0.17.0 pasa lint/formato y queda fijado en `pyproject.toml`; P67 supera la
comparación integral y fija Coverage 7.16.2. No cambian IDs públicos
ni versión de LANCTL. Los detalles y límites figuran en la matriz de verificación.
P69–P73 fueron incorporadas desde HELP durante este ciclo por peticiones de
anotación; se conservan como tareas nuevas, todavía sin implementación.

### Estabilización y comprobaciones GitHub — 17/10/2026

El usuario solicita corregir fallos persistentes/intermitentes y preparar la
próxima estable. Se anteponen los fallos reproducibles de seguridad y CI a las
nuevas opciones del instalador. No se cambia la versión ni se publica una estable
durante esta validación.

- [x] Resolver el fallo repetido de `dependency-review`: grafo de dependencias
  desactivado, activado y verificado mediante reintentos reales de las PR 23/25.
- [x] Igualar dependencias de CI y Release (`dev,gui`), conservar JUnit/logs
  incluso al fallar y añadir regresiones Windows Python 3.10/3.11 a CI. Las nuevas
  definiciones requieren ejecución remota tras integrar estas fuentes.
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
  1.212 pruebas activas, 21 de compatibilidad heredada y 645 subpruebas pasan;
  un caso POSIX omitido en Windows. Cobertura 69,4720 %, umbral 60 %.
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
- [ ] Completar CI y validación remota de paquetes del candidato de la PR 26;
  el primer job Linux detectó el fixture anterior. Sin publicación automática
  durante la validación manual del workflow de distribución.
- [ ] Compilar/certificar el candidato actualizado con GUI-DESIGN. El Release
  GitHub 39052546460 demuestra Windows/Linux amd64/arm64 para `4ca563d`, no
  para las modificaciones posteriores. Firmas oficiales y REF-P34-runtime
  conservan sus bloqueos explícitos.

Estado revisado el **16/10/2026**. Los puntos marcados tienen corrección o
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
| P48 | `core/clink_integration.py`, Lua, instalador, `portable/prepare.ps1`, script de build. | Solo carpeta de esta distribución/usuario; no ejecutar PATH de usuario al desinstalar elevado. Falta CMD/Clink real y caso de desinstalación por otra cuenta. | Medio | Registro y retirada comprobados con ejecutor simulado; paquetes preparados en fuentes. No certificada. |
| P34 | Concesiones por activación, comprobación de autoridad, retirada de referencias y limpieza fuera de locks implementadas; 119 pruebas pasan. | REF-P34-runtime sigue necesaria: hilos y efectos nativos del trusted heredado no son cancelables desde la API. | Crítico | `runtime_status` distingue acceso al Core, limpieza pendiente y reinicio requerido. No se declara revocación nativa completa. |
| P40/P42 | Artefactos LCP oficiales y confianza real. | Requiere editor/clave y paquetes firmados autorizados; no crear identidad ficticia. | Alto | Bloqueo externo mantenido. |
| P50 | Puente MCP de consulta y diagnóstico. | REF-P34-runtime, contrato de snapshots de sesión viva/revisión y transporte autenticado verificable; el coordinador actual solo comparte metadatos. | Alto | Preparador P52 disponible; puente no implementado ni certificado. No sustituir cambios sin guardar por lectura del VLF. |
| P32 | Certificación de distribución. | GUI-DESIGN ejecutará suite integral y único build; Windows limpio, ARM64 y SSH externo siguen sin evidencia. | Alto | No se confunden regresiones de fuente con certificación de paquetes. |

Refactorizaciones necesarias antes de reanudar las tareas bloqueadas:

- [ ] **REF-P34-runtime.** Contrato de ejecución con revocación comprobable.
  Separar los plugins con ejecución cancelable en procesos propiedad del host;
  versionar el RPC, permisos por llamada y concesión/revisión de autorización.
  Definir suspensión de nuevas llamadas, retirada de callbacks/funciones,
  cancelación y terminación con plazo, dependencias y confirmación por proceso.
  Nunca mantener locks de registro mientras se invoca `deactivate` de código
  externo. Conservar runtime/API anteriores como compatibilidad explícita con
  sus límites; no anunciar aislamiento para `trusted` en proceso. Impacto alto
  en plugins y contratos, riesgo crítico; condición previa de cierre P34/P50.
- [ ] **REF-P47-interface.** Enumeración de redes con máscara real y selección
  del origen de sondas ICMP/ARP/TCP. El escáner actual usa rutas del SO y puede
  inferir /24; una etiqueta de interfaz no altera ese comportamiento. Añadir
  adaptadores Windows/Linux con origen explícito, verificar varias NIC y no
  introducir escaneos fuera del rango confirmado. Impacto transversal en
  descubrimiento, riesgo alto; requisito para completar P47.

- [ ] **REF-P50-session.** Antes del puente MCP, definir un proveedor de snapshot
  del proceso propietario con revisión, contexto de sesión/proyecto explícito,
  caducidad al cerrar/cambiar de proyecto y datos temporales aún no guardados.
  Seleccionar campos por capacidad y excluir credenciales. El coordinador solo
  contiene metadatos y `_SESSION_DEVICES` es memoria de proceso: leer un VLF
  desde el servidor no cumple ese contrato. Riesgo alto, impacto en sesión e
  inventario; depende de REF-P34-runtime para exposición mediante plugin.

Orden recomendado tras la integración de fuentes: resolver REF-P34-runtime y
el contrato de sesión viva de P50; obtener las firmas de P40; verificar el
instalador P45/P46/P48 y luego P32 con su matriz externa; resolver
REF-P47-interface antes de certificar selección de red. P67/P68 (herramientas
de desarrollo) son propuestas separadas y no se mezclan en este cambio.

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

- [ ] **P45.** Añadir una selección de cinco temas durante la instalación, con
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
- [x] **P46.** Permitir elegir si se instalan los plugins predeterminados del
  programa, con selección individual opcional. Adaptar el empaquetado y el primer
  inicio para respetar la elección, distinguir los recursos necesarios (como el
  tema base) de los plugins opcionales y conservar permisos, firmas y confianza
  del editor. Mantener las elecciones existentes al actualizar.
- [ ] **P47.** Ofrecer al finalizar la instalación las opciones «Abrir LANIP» y
  «Realizar un primer escaneo». Arrancar la GUI con el usuario normal, mostrar la
  red detectada y permitir seleccionar interfaz/rango cuando haya varias redes;
  mostrar el progreso del escaneo en la GUI y ejecutarlo solo si se ha elegido.
- [ ] **P48.** Corregir la distribución del completado Clink: incluir
  `packaging/clink/lanctl.lua` y sus instrucciones en el instalador Windows y en
  el ZIP portable. Detectar Clink y registrar automáticamente la carpeta de
  scripts con `clink installscripts` para el usuario correspondiente, tanto en
  la instalación como en el flujo de preparación del portable. Evitar registros
  duplicados al actualizar y retirar el registro de la instalación al
  desinstalar, sin afectar otras carpetas de Clink. Verificar el contenido de
  ambos paquetes y el completado real de los seis ejecutables en CMD con Clink;
  mantener la validación del Lua frente a los parsers de la versión distribuida.

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

P35, P45, P46, P49, P51–P54 y P66 «Dimensiones» quedan implementados y
verificados localmente junto con sus adaptadores de escritorio. La evidencia
está en `docs/BACKLOG-VERIFICATION.md`. P47 incluye confirmación de CIDR y
progreso, pero mantiene pendiente el enlace real a una interfaz de red. P48
conserva la certificación con Clink real y el caso de desinstalación por otra
cuenta. La instalación limpia y las plataformas externas siguen en P32.
P34, P40/P42 y P50 no se consideran completados por estas mejoras visuales:
AUDITOR continúa su trabajo interno por separado tras el paquete comprobado.
Los puertos de las skins permanecen decorativos y los datos se comparten entre
LANRACK y LANWIRE sin duplicar inventarios.

## Configuración editable según interfaz — 17/10/2026

- [ ] **P69.** Corregir los cruces de configuración entre GUI, TUI y CLI:
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
