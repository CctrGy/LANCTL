# Monitorización LAN

El backend separa el motor de ejecución de la configuración y los datos. `MonitorService` consume `ConfigProvider`, `AssignmentProvider`, `MetricsStore`, `SessionRepository`, `IncidentRepository` y `ReportBuilder`. Las implementaciones persistentes usan SQLite con WAL, timeout de bloqueo, transacciones e índices por dispositivo y tiempo.

## Configuración y CLI

La clave `monitor` conserva claves desconocidas y completa de forma aditiva `intervals` y `retention`. Las duraciones aceptan `s`, `m`, `h` y `d`, sin evaluar expresiones.

```text
monitor profile list
monitor profile show normal
monitor profile create storage --presence 30s --discovery 5m --services 10m --deep 6h
monitor assign NAS --profile storage
monitor assign ROUTER --priority critical
monitor assign SERVER --check port:22 --check port:443 --every 30s
monitor assign --group SWITCHES --profile infrastructure
monitor unassign NAS
monitor assignments --json
monitor session list --json
monitor session report SESSION --json
monitor report latest
```

## Servicio permanente en Windows

La instalación completa puede registrar `LANCTLMonitor` automáticamente. También
se puede administrar de forma explícita desde una consola elevada:

```text
monitor service install --yes
monitor service status
monitor service start
monitor service stop
monitor service restart
monitor service uninstall --yes
```

El servicio ejecuta el mismo motor `foreground` mediante el protocolo nativo del
Service Control Manager; no es un proceso de consola simulado. Se ejecuta con la
cuenta restringida `LocalService` y conserva inventario, perfiles, asignaciones,
métricas e incidencias bajo el directorio común de datos de LANCTL.

Los perfiles integrados están protegidos. Las asignaciones resueltas guardan `deviceId`, por lo que cambiar alias o IP no rompe la referencia.

## Datos y retención

### Presupuesto, cancelación y parada

Cada ejecución recibe un presupuesto monotónico desde su admisión en la cola.
El argumento sigue siendo compatible con el timeout numérico de cada sonda;
los checks compuestos comparten además un plazo total. Las sondas integradas
comprueban cancelación entre fases y limitan nuevas operaciones al tiempo
restante. Un resultado caducado no se persiste. La generación y sesión se
capturan al programar: las escrituras vuelven a comprobar su vigencia bajo la
exclusión de publicación. Las métricas, estados e incidencias que comparten
SQLite se aceptan en una transacción; los eventos VLF se emiten después.

Una parada invalida nuevas escrituras, cancela presupuestos y deja la sesión en
`stopping` hasta drenar tareas y callbacks admitidos. El cierre espera por defecto
hasta cinco segundos por intento. Si un handler heredado no coopera, devuelve
`MonitorShutdownPending` y conserva la propiedad del trabajo y los recursos;
no anuncia parada ni permite reutilizar el servicio para otra sesión. No puede
forzar la terminación segura de un hilo nativo arbitrario. Una escritura ya
aceptada puede terminar su commit; la parada posterior queda ordenada tras ella.

Los nuevos procesos foreground anuncian `session-request-v1` en el lock verificado.
`monitor stop` y el primer paso de reinicio solicitan `stopping` en la base sin
enviar una señal de terminación (especialmente relevante en Windows). El dueño
detecta la petición en su ciclo y sale cuando confirma el drenado. Reinicio sigue
esperando la salida real del dueño antes de crear su sustituto. Los procesos
anteriores sin este protocolo conservan el mecanismo de señal heredado.

El hijo de arranque recibe internamente el ID previsto y no adopta sesiones
sustitutas ni recrea una sesión cancelada. Activación y solicitud de parada se
ordenan en la misma transacción. Estas garantías cubren las rutas integradas y
sus adaptadores cooperativos; un plugin que escriba por su cuenta fuera de esos
adaptadores requiere su propio aislamiento/contrato.

`monitor.db` contiene identidad del gestor/LAN, sesiones, estado actual, muestras limitadas, agregados, incidencias y metadatos runtime. No contiene credenciales ni payloads remotos arbitrarios. Los timestamps se normalizan a UTC. El mantenimiento agrega mediante claves idempotentes y elimina por lotes las muestras caducadas.

El VLF no incorpora la base SQLite. Los informes portables se escriben bajo `monitoring/` renovando hashes con el mismo bloqueo de escritura que HistoryService.

### Identidad, salud y significado de las métricas

Las tareas conservan su identificador público, pero resuelven el target vigente
al ejecutarse. Un redescubrimiento actualiza la IP del mismo `deviceId` y retira
las tareas de dispositivos ausentes. Cancelar una tarea también invalida su
ejecución en vuelo: su finalización no vuelve a introducirla en la cola.

La salud se deriva del resultado vigente de cada check (incluido servicio/puerto)
durante la ejecución del motor. Una latencia normal recupera su propio check,
pero un éxito en otro servicio no borra un fallo pendiente. El estado de
mantenimiento tiene precedencia. Los contadores de presencia conservan sus
umbrales de fallo y recuperación.

`packet_loss` y `availability` describen proporciones de muestras. En cambio,
`outage_count` y las desconexiones del informe cuentan intervalos consecutivos
de observaciones fallidas, incluida una primera observación ya fallida; no son
el número de paquetes perdidos ni el número de incidencias del gestor. Las
observaciones simultáneas se consideran presentes si alguna tiene éxito.

`outage_duration` estima segundos entre la primera observación fallida y la
siguiente recuperación; si no hay recuperación, termina en la última muestra
observada. No extrapola más allá de esa muestra ni entre sesiones. Dentro de
una sesión se supone continuidad entre observaciones, por lo que los huecos
largos reducen la precisión de la estimación. Los intervalos solapados se unen
y la duración se recorta a cada bucket; nunca supera su resolución. El inicio
se cuenta solo en el bucket donde ocurrió. Solo se materializan buckets con
muestras. Los agregados existentes se recalculan cuando aún existen sus crudos;
los informes históricos ya guardados no se reescriben automáticamente.

En Linux la ruta predeterminada respeta `XDG_STATE_HOME` o `~/.local/state/lanctl`; un servicio puede proporcionar un override hacia `/var/lib/lanctl`. En Windows portable se usa `application_path`.
