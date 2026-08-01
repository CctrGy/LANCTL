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
project info ARCHIVO.vlf [--json]
project verify ARCHIVO.vlf [--json]
project list ARCHIVO.vlf
```

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
