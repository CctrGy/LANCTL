# Correcciones de la auditoría de octubre de 2026

Base auditada: `d6b0e7d382a643789942314fd0ea18a103f19a98`, versión
`0.3.2-beta.4`. Las correcciones se desarrollan en `codex/audit-corrections`
para revisión e integración posterior en `main`. Ninguna rama estable se modifica.

## Errores corregidos y pruebas de regresión

| ID | Gravedad | Corrección | Pruebas |
| --- | --- | --- | --- |
| F01 | Crítica | IPC JSON acotado, validación y presupuesto en el padre; recepción independiente del timeout. No se usa pickle para recibir datos del plugin. | `test_audit_regressions.py`: payload pickle real, frames inválidos, presupuesto, desactivación y frame parcial POSIX. |
| F02 | Alta | Validación UUID al crear/verificar VLF; confinamiento del workspace resuelto. | `test_audit_integrity.py`: VLF con checksums válidos e ID de ruta externa. |
| F03 | Alta | `list` requiere `scan.run`; se bloquean destinos de salida remotos. | `test_audit_access.py`: viewer/operator y variantes de `--output`/`-o`. |
| F04 | Alta | Cada autorización relee cuenta, roles y autenticadores. | `test_audit_access.py`: desactivación, eliminación, roles, caducidad y rotaciones. |
| F05 | Alta | Handshake TLS dentro del pool limitado con timeout, después del filtro de red. | `test_audit_access.py`: cliente TCP inmóvil mientras otro cliente HTTPS responde. |
| F06 | Alta | Política de huella en la misma conexión Netmiko, antes de autenticar. | `test_audit_access.py`: clave correcta/incorrecta y orden frente a credenciales. |
| F07 | Media | Cabecera CSRF ausente o vacía se rechaza en POST autenticado. | `test_audit_access.py`: peticiones HTTPS reales sin token, vacío, incorrecto y válido. |
| F08 | Alta | Borrado por `device_id`, sin eliminar otras MAC vacías. | `test_audit_integrity.py`: registros provisionales y gateway sin MAC. |
| F09 | Alta | `ensure_basic` aplica su cambio sobre una lectura bajo lock, conservando la firma pública. | `test_audit_integrity.py`: alias concurrente entre guardado y actualización de BASIC. |
| F10 | Alta | Se rechazan esquemas futuros o inválidos antes de migrar o serializar. | `test_audit_integrity.py`: rechazo y bytes originales intactos. |
| F11 | Alta | Target vigente por tarea y eliminación tras redescubrimiento. | `test_audit_runtime.py`: DHCP conserva ID y cambia IP; retirada de dispositivo. |
| F12 | Media | Intervalos de caída compartidos por agregados e informes; duración acotada al bucket. | `test_audit_runtime.py`: fallos consecutivos, recuperación cruzando buckets y conteo de incidentes. |
| F13 | Media | Salud derivada por check/servicio/puerto, con precedencia de mantenimiento. | `test_audit_runtime.py`: recuperación de latencia y fallos de otros servicios pendientes. |
| F14 | Media | Registro de tareas activas y cancelación de la generación en vuelo. | `test_audit_runtime.py`: cancelar, reemplazar con el mismo ID y completar la ejecución anterior. |
| F15 | Alta | Plazo compartido para lock local y lock del sistema operativo. | `test_audit_integrity.py`: timeout entre hilos y reutilización/reentrada posterior. |
| F16 | Media | Constructor común de launcher LANIP, checkout y ejecución como módulo. | `test_audit_access.py`: `--help` real desde otra carpeta y selección de binarios congelados. |
| F17 | Media | Backups con creación exclusiva y nombre único. | `test_audit_integrity.py`: dos snapshots con el mismo timestamp conservan ambos contenidos. |
| F18 | Media | Promoción de IP provisional a MAC conservando ID y asociaciones. | `test_audit_integrity.py`: identidad promovida y separación de dos MAC conocidas. |
| F19 | Alta | Límite anterior a enumerar CIDR y ventana acotada de Futures. | `test_audit_integrity.py`: red /8 rechazada sin enumerar, /31, /32 y cola limitada. |
| F20 | Media | Instalación completa en staging y reemplazo con recuperación de la anterior. | `test_audit_runtime.py`: fallo de extracción, fallo de publicación y reintento correcto. |

Las pruebas citadas están en `tests/`. También se endurecen los nombres de archivo
LCP y `entryPoint` contra unidades Windows y streams alternativos (riesgo R09).

## Compatibilidad y alcance

Se conservan los IDs públicos existentes de eventos, funciones y tareas y los
formatos persistentes. No se cambia la versión de una rama estable. Los rechazos
nuevos aplican las validaciones del contrato ya documentado: no se convierten
datos de esquema futuro en legacy ni se autorizan escrituras con permisos de lectura.

El IPC es interno entre dos procesos de la misma instalación; su codificación
no es un contrato público de plugins. La API declarada sigue siendo compatible.
La semántica corregida de las métricas se detalla en `MONITOR.md`; no se reescriben
informes históricos que ya fueron guardados.

Estos cambios cierran los errores F01–F20. No sustituyen las refactorizaciones
estructurales R01–R12: orden global de locks, separación Core/apps, unidad de
trabajo entre almacenes, historial VLF por lotes, retención incremental, validación
uniforme de contratos y gates de plataforma/publicación requieren trabajo específico.
El runtime aislado sigue sin ser un sandbox del sistema operativo para código hostil.

La validación local se realiza en Windows; las pruebas POSIX se conservan para
Linux. El arranque congelado se verifica con dobles de ruta; la auditoría de esta
corrección no construye ni publica instaladores.

## Verificación final del 14 de octubre de 2026

Entorno: Windows, Python 3.10.11 del entorno `.venv`, sobre la rama de corrección.

| Comprobación | Resultado |
| --- | --- |
| Suite completa, incluyendo `legacy_gui`, con cobertura de ramas | 865 pruebas y 635 subpruebas aprobadas; 2 omisiones iniciales. |
| Navegador opcional, habilitado después con `LANCTL_GUI_BROWSER_TESTS=1` | 1 prueba adicional aprobada en Edge headless; cubre filtros, ajustes, guardado, edición pendiente y nuevo proyecto. |
| Regresiones nuevas de auditoría | 56 casos aprobados; 1 caso específico POSIX pendiente de Linux. |
| Cobertura combinada de líneas y ramas | 66,6027 %, superior al mínimo del 60 %. |
| Ruff y formato | Sin errores; 409 archivos con formato correcto. |
| Catálogo de errores | Actualizado y comprobado: 1.129 puntos catalogados. |
| Referencias CLI y web | Comprobadas; `reference/catalog.js` regenerado. |
| Bandit, umbral medio/alto | Sin hallazgos; dos avisos preexistentes de comentarios `nosec` sin incidencia asociada. |
| Dependencias instaladas y compilación Python | `pip check` y `compileall` correctos. |
| Higiene y espacios del diff | `check_repository_hygiene.py` y `git diff --check` correctos. |

Resultado conjunto: **866 pruebas y 635 subpruebas aprobadas**, sin fallos. La
única prueba sin ejecutar en este entorno es el frame parcial de pipes POSIX.
La prueba de navegador usa el puente API simulado del repositorio; no sustituye
una prueba del instalador o del motor nativo de pywebview.

La comparación AST de los 244 módulos existentes con el commit auditado conserva
los 134 literales de ID `LANCTL.a.b.c`, incluidos los orígenes, y los campos de las
74 dataclasses. Se conservan los 1.051 símbolos invocables públicos comparados;
la única firma ampliada es `AuthorizationService(store, clock=now)`, cuyo nuevo
argumento es opcional. No se retiran módulos ni rutas de importación existentes.
Los registros de eventos y funciones, contratos de plugins y UI, API de plugins,
tareas, errores, coordinación, sesión y adaptadores de parser no cambian. Se
mantienen los 19 eventos del Core, sus versiones y contratos; los tests de
plugins, entrypoints, persistencia y completado Clink pasan en la suite.

Para reproducir la validación funcional en el entorno de desarrollo:

```text
python -m coverage run --branch --source=src -m pytest -m "legacy_gui or not legacy_gui" -q --tb=short
python -m coverage report --precision=4 --fail-under=60
```

La prueba opcional de navegador se ejecuta con `LANCTL_GUI_BROWSER_TESTS=1` y
`python -m pytest tests/test_desktop_browser.py -q`. En esta verificación, los
informes de cobertura, JUnit y comparación de contratos se guardan fuera del
repositorio, sin versionar bases, credenciales o resultados de pruebas.

## Trabajo pendiente

- Validar en Linux la suite y el caso de IPC POSIX; construir y probar los
  instaladores y los launchers congelados en ambas plataformas antes de publicar.
- Priorizar los riesgos altos restantes: orden global de locks (R01), separación
  Core/aplicaciones/interfaces (R02), historial VLF por lotes (R03), fuente canónica
  de relaciones (R04), transacciones entre almacenes (R05) y singleton del monitor
  (R10). Sus impactos son bloqueos, coste creciente y estados parciales o divergentes.
- Tratar la retención incremental (R06), validación uniforme de contratos y origen
  de errores (R07), consultas sin efectos persistentes (R08) y controles continuos
  de pruebas/publicación (R11–R12). El endurecimiento de rutas de R09 está incluido;
  no se ha ejecutado una matriz de integración entre unidades Windows distintas.
- Revisar e integrar esta rama en `main`. Esta validación no implica una publicación
  estable ni elimina la necesidad de aislamiento del sistema operativo para plugins
  hostiles. Los informes históricos guardados conservan sus valores anteriores.
