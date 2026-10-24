# LANCTL VLF 1.0

## Política de compatibilidad 0.3

- Toda la serie LANCTL `0.3.x` escribe VLF `1.0` y puede abrir proyectos `1.0`
  creados por versiones alpha, beta o estables de la serie.
- Los campos JSON desconocidos son aditivos. Los namespaces de plugins y los
  recursos no regenerados se conservan al actualizar un proyecto.
- Una versión de formato distinta de `1.0` se rechaza antes de modificar el
  archivo. No se realizan migraciones implícitas sobre formatos futuros.
- `project update` verifica primero el archivo, conserva su UUID y fecha de
  creación, genera una copia `.vlf.bak` y sustituye el original de forma
  transaccional. La base anterior queda además como `devices/backup.db`.
- No se garantiza compatibilidad descendente desde un futuro VLF 2.x hacia
  ejecutables LANCTL antiguos.

Un archivo `.vlf` es un contenedor ZIP con nombres internos POSIX y una
estructura fija. No debe confundirse la compresión ZIP con cifrado.

## Comandos

```text
project create ARCHIVO.vlf [metadatos]
project update ARCHIVO.vlf
project save
project import-physical ARCHIVO.db
project info ARCHIVO.vlf [--json]
project verify ARCHIVO.vlf [--json]
project list ARCHIVO.vlf
```

## Inventario físico por proyecto

El contenedor admite la entrada opcional `devices/physical.json` con
`{"schemaVersion":1,"inventory":{...}}`. `inventory` conserva el documento IDF
versionado completo, incluidos CPD, prefijos, registros y relaciones. Se valida
antes de materializar y guardar, y queda cubierto por los hashes del VLF.
Los proyectos antiguos sin esa entrada abren una base física vacía. El
workspace coloca su copia en `physical/idf.db`; guardar/reabrir restaura esa
copia independientemente de la instalación original.

La base física histórica permanece separada. `project import-physical` exige
un proyecto activo con inventario físico vacío, valida y copia el archivo sin
modificar el original. La importación y las ediciones CLI/TUI/GUI de
LANWIRE/LANRACK aplican el disparador `change` de la política compartida:
`automatic.allChanges` guarda el VLF; los otros modos conservan los cambios
pendientes hasta su disparador correspondiente o `project save` explícito.
La operación fija el proyecto y guarda una sola vez después de liberar los
locks físicos. Las consultas, ediciones rechazadas sin escritura y bases
externas seleccionadas explícitamente no disparan el guardado del proyecto.
Si falla el guardado del VLF, el cambio permanece en la base de trabajo y se
informa del error; se debe reintentar `project save`, sin repetir la edición.
Si desaparece la base materializada no se recrea vacía:
hay que recuperar una copia o recargar explícitamente el proyecto.

Los lectores VLF 1.0 anteriores pueden abrir el inventario lógico, pero sus
escritores anteriores a esta extensión no garantizan conservar la nueva
entrada física al volver a guardar. La compatibilidad de lectura no implica
esa conservación por ejecutables antiguos.

## SaveMode

`project save` sincroniza explícitamente el proyecto activo. La opción global
`settings --save-mode MODO` permite elegir:

- `manual`: solo `project save` o `project update`.
- `manual.inCloseConsult` (también acepta `manual.consultToClose`): si el
  workspace tiene cambios, el TUI abre una ventana para guardar, descartar o
  cancelar el cierre.
- `automatic.toClose`: al cerrar la invocación principal, CLI, TUI o GUI.
- `automatic.toScan`: después de cada escaneo de red.
- `automatic.timeToSave`: guardado periódico; el intervalo se configura con
  `settings --save-interval MINUTOS` y vale 5 minutos por defecto.
- `automatic.allChanges`: después de cualquier cambio confirmado.

La variante histórica `automatic..allChanges` se acepta y se normaliza a un
solo punto. Todos los modos comprueban el hash del workspace antes de escribir.
Un plugin puede aportar opciones mediante `project-save-mode`, declarando los
disparadores `change`, `scan`, `close` o `timer`.

Las consolas físicas LANWIRE/LANRACK conectan `change`, `close` y `timer` a
la misma política. Cada consola persistente tiene un temporizador, que se
detiene al salir y reintenta tras errores de guardado. La consulta de cierre
ofrece `S` (guardar), `n` (salir conservando el workspace) y `c` (cancelar).
Un fallo al guardar mantiene abierta la consola para reintentar sin repetir
la edición. EOF o interrupción de la entrada principal cierra sin preguntar;
EOF/interrupción durante la confirmación cancela ese intento de cierre.

Un comando aislado aplica `close`, no crea temporizador ni solicita entrada.
Con `manual.inCloseConsult` conserva los cambios pendientes sin guardar el
VLF; se pueden guardar después con `project save`. Un fallo de guardado al
cerrar devuelve un código de error.

Sin `--database`, los servicios físicos siguen la selección compartida entre
operaciones. La TUI invalida el formulario/comando pendiente al cambiar de
proyecto. Una operación en curso y sus guardados mantienen el workspace de
origen. `--database` fija el destino incluso si coincide inicialmente con
el proyecto activo; una base externa nunca se exporta a ese VLF. La GUI
mantiene su ciclo de vida independiente.

## Carpeta predeterminada

Un nombre relativo se guarda en la carpeta de proyectos del usuario:

`%USERPROFILE%` es la variable estándar de Windows para el perfil actual
(`C:\Users\<usuario>`). Se conserva literalmente en `.config` y solo se
expande al abrir o guardar, evitando nombres de usuario fijos.

```text
%USERPROFILE%\Documents\LanCTL\
```

Por ejemplo, `project create Hogar.vlf` crea
`%USERPROFILE%\Documents\LanCTL\Hogar.vlf`. La carpeta se crea automáticamente.
Una ruta absoluta permite utilizar cualquier otra ubicación:

```bat
lanctl project create D:\Redes\Oficina.vlf
```

La ubicación predeterminada también puede cambiarse:

```bat
lanctl settings --projects-directory D:\ProyectosLANCTL
```

Usa `lanctl settings --projects-directory default` para recuperar la ruta
portable predeterminada.

`update` conserva UUID, fecha de creación, identidad de la LAN, VLAN,
topología complementaria, claves ya incluidas y logs históricos. La base
anterior pasa a `devices/backup.db`, y el VLF anterior queda como `.vlf.bak`.

## Estructura

```text
project.info
lan/lanIdentifier.info
lan/network.config
lan/vlan.config
lan/topology.map
auth/logins.lgn
auth/keys/ssh/
auth/keys/api/
auth/keys/device/
auth/keys/logon/access.info
logs/dd-mm-yyyy.log
devices/elements.db
devices/backup.db
meta/version
meta/created
meta/checksum
```

Los archivos `.info`, `.config`, `.map` y `meta/checksum` usan JSON UTF-8.
`elements.db` y `backup.db` son SQLite. `logins.lgn` conserva el almacén de
credenciales cifrado de LANCTL como datos opacos.

## Integridad

- `project.info.contentHash` cubre el contenido funcional, excluyendo
  `project.info` y `meta/checksum` para evitar autorreferencia.
- `meta/checksum.hash` cubre todos los archivos salvo el propio checksum.
- Los hashes usan SHA-256 sobre nombre, tamaño y contenido de cada entrada en
  orden estable.
- `project verify` comprueba ambos hashes, entradas obligatorias y
  `PRAGMA integrity_check` en las dos bases SQLite.

## Seguridad

- El ZIP no cifra el proyecto completo.
- Las contraseñas nunca se convierten a texto plano al crear el VLF.
- Las claves SSH, API o de dispositivo no se importan automáticamente; solo se
  conservan durante una actualización si ya estaban dentro del proyecto.
- El lector rechaza rutas absolutas, `..`, barras invertidas, nombres
  duplicados, entradas mayores de 256 MiB y proyectos expandidos mayores de
  512 MiB.
- Compartir un VLF puede revelar inventario, topología y logs incluso cuando
  las credenciales permanezcan cifradas.
# Eventos estructurados

VLF 1.0 admite de forma aditiva `logs/events/YYYY-MM-DD.jsonl`, con un objeto
`HistoryEvent` por línea. Cada append renueva `project.info.contentHash` y
`meta/checksum`; `project update` preserva el directorio completo. Las líneas
corruptas o truncadas se omiten en lectura normal y producen error en modo
estricto. `logs/dd-mm-yyyy.log` permanece disponible para auditoría legacy.

### Preferencias explícitas del proyecto

El editor `lanctl settings --scope project` conserva las preferencias de red
editadas en `lan/settings.override.json`, un documento opcional con
`schemaVersion: 1` y un objeto `network`. Sus campos corresponden a
`lan/network.config`; `network`, `netmask` y `prefixLength` se derivan de `cidr`.
El guardado conserva este documento y aplica sus valores sobre los valores
generados. Forma parte del cálculo de hashes del VLF. La activación carga las
preferencias explícitas sin reemplazar el inventario del espacio de trabajo.
