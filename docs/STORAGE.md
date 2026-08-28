# Persistencia, concurrencia y recuperación

LANCTL separa programa, datos de usuario/servicio y proyectos. En una
instalación Windows estándar, el programa reside en `Program Files` y los datos
mutables en `C:\ProgramData\LANCTL`. Los secretos usan el ámbito de usuario o
servicio configurado. Los proyectos VLF solo cambian cuando se seleccionan de
forma explícita.

Los almacenes JSON usan locks de proceso e hilo, escritura temporal, `fsync` y
reemplazo atómico. `config/storage-schema.json` identifica la versión del
esquema. Una migración ascendente crea antes una copia en
`config/migration-backups`; una versión futura se rechaza para impedir que un
ejecutable antiguo modifique datos incompatibles.

Comandos operativos:

```powershell
lanctl database --diagnose
lanctl database --diagnose --json
lanctl database --export LANCTL-data.zip
lanctl database --verify LANCTL-data.zip
```

La exportación contiene un manifiesto y un SHA-256 por archivo. Verificar no
importa ni modifica datos. Antes de una reparación manual, detén otras
instancias y conserva la carpeta completa de datos.
