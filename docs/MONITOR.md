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

Los perfiles integrados están protegidos. Las asignaciones resueltas guardan `deviceId`, por lo que cambiar alias o IP no rompe la referencia.

## Datos y retención

`monitor.db` contiene identidad del gestor/LAN, sesiones, estado actual, muestras limitadas, agregados, incidencias y metadatos runtime. No contiene credenciales ni payloads remotos arbitrarios. Los timestamps se normalizan a UTC. El mantenimiento agrega mediante claves idempotentes y elimina por lotes las muestras caducadas.

El VLF no incorpora la base SQLite. Los informes portables se escriben bajo `monitoring/` renovando hashes con el mismo bloqueo de escritura que HistoryService.

En Linux la ruta predeterminada respeta `XDG_STATE_HOME` o `~/.local/state/lanctl`; un servicio puede proporcionar un override hacia `/var/lib/lanctl`. En Windows portable se usa `application_path`.
