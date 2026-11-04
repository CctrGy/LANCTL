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
lanctl database --import LANCTL-data.zip --yes
lanctl database --restore devices.json.FECHA.bak --target database --yes
```

La exportación contiene un manifiesto y un SHA-256 por archivo. Verificar no
importa ni modifica datos. La importación vuelve a verificar, rechaza rutas que
salgan de la raíz, crea backups y revierte todos los destinos si una escritura
falla. Antes de importar, detén otras instancias y conserva una copia externa.

## Contratos de restauración y destinos de exportación

La restauración valida y escribe los mismos bytes de la copia, leídos una sola
vez bajo bloqueo conjunto de origen y destino. Para las rutas configuradas se
comprueban los contratos de dispositivos, grupos, inventario físico IDF,
configuración y registro de plugins, reutilizando los validadores de sus lectores.
Se admiten los formatos históricos que dichos lectores soportan. Una copia
inválida no reemplaza el destino. Los consumidores Python pueden proporcionar
`contract` a `restore_backup` o un mapa `contracts` a diagnóstico/importación
para rutas arbitrarias; no se deduce el contenido por el nombre del archivo.

El diagnóstico JSON añade `validation`: `functional` indica contrato comprobado;
`syntax-only`, únicamente JSON bien formado; `not-checked`, contenido sin contrato
comprobado; `failed`, validación fallida. `valid: true` con `syntax-only` no
certifica que una aplicación pueda abrir el archivo. Este límite también se
explica en el diagnóstico textual de JSON desconocido.

Las nuevas exportaciones CLI usan manifiesto `schemaVersion: 2` y
`layout: logical`, con destinos `devices`, `groups`, `physical`, `config` y
`plugins` presentes en la exportación. La importación los resuelve mediante un
mapa explícito de rutas locales configuradas, capturado antes de escribir:
ninguna ruta absoluta del equipo de origen se obtiene del ZIP. Esto conserva
los destinos aunque falten archivos opcionales o el workspace esté fuera de la
raíz de datos. Se rechazan destinos duplicados y mapas incompletos.

Para consumidores Python, `export_storage(..., source_root=raiz)` produce v2
con `layout: relative` y conserva los directorios respecto a esa raíz fija.
`destinations={nombre_logico: ruta}` selecciona el formato lógico; no puede
combinarse con `source_root`. Su importación exige un mapa `destinations`
explícito. La API sin estas opciones conserva el formato v1 por compatibilidad.
Los archivos v1 mantienen su disposición relativa original al importarse; no se
inventa una carpeta `database/` que no conste en su manifiesto. Los consumidores
antiguos que solo conocen v1 rechazarán las exportaciones v2; se necesita una
versión con soporte v2 para leerlas.

## Recuperación durable de importaciones múltiples

La importación publica un journal `.lanctl-import.transaction` versionado y
sincronizado antes de sustituir datos, con las instantáneas anteriores y sus
checksums. Cada destino tiene un marcador `.lanctl-import.pending` que lo vincula
al mismo journal y transacción. Los nombres son metadatos internos; no deben
editarse, trasladarse ni eliminarse para forzar una apertura.

Hasta confirmar de forma durable la fase `committed`, una recuperación restaura
la generación anterior completa. Después de esa confirmación conserva la nueva
generación y termina la limpieza. Si se interrumpe la recuperación, se puede
repetir; los destinos inicialmente ausentes vuelven a estar ausentes al revertir.
Los backups se conservan y se sincronizan antes de reemplazar los almacenes.

Los lectores de dispositivos, grupos, configuración, registro de plugins e
inventario físico consultan los marcadores antes de exponer datos. Los escritores
que usan el bloqueo compartido también recuperan antes de modificar un destino,
incluso si esperaban el lock cuando murió el importador. La transacción previa de
dispositivos/grupos se recupera antes de capturar la instantánea de importación
cuando esas rutas forman parte del mapa de almacenes. El cálculo de cambios del
proyecto no puede sustituir una recuperación fallida por una lectura sin validar.

Se comprueban esquema, checksums, rutas canónicas y correspondencia entre destino,
marcador y transacción. Un journal o marcador corrupto bloquea el acceso y conserva
la evidencia; un fallo del rollback registra `STORAGE.IMPORT.RECOVERY_FAILED`
con origen `LANCTL.Storage.Import.Recovery`. No se presenta como un almacén vacío
ni como una importación correcta. No se escriben snapshots en los logs.

Un cierre anterior a la publicación de todos los marcadores todavía no ha
sustituido datos: conserva la generación anterior; el journal de esa raíz se
recupera al volver a importar o mediante `recover_journal`. Una vez publicados los
marcadores, la apertura de cualquiera de los destinos vinculados recupera el
conjunto, sin requerir repetir el comando de importación. Los locks auxiliares
persistentes siguen la política de los demás almacenes.

Estas rutas se prueban con procesos terminados abruptamente en Linux, también
durante la recuperación. La prueba no certifica cortes de alimentación reales
ni distribución Windows: allí se conserva el límite documentado de `fsync` de
directorios del adaptador compartido. Mantén una copia externa y detén otros
escritores antes de importar; los lectores/escritores externos que omitan los
servicios y locks de LANCTL no participan en esta coordinación.
