# Configuración completa desde el CLI

`lanctl settings` abre el editor por categorías cuando se ejecuta en una terminal
interactiva. `lanctl settings --menu` lo abre explícitamente. Con entrada/salida
redirigida se conserva la consulta JSON anterior sin preguntas interactivas.

El menú separa **Programa completo** y **Proyecto activo**. Cada categoría muestra
los ajustes, su valor actual y los campos de solo lectura. Selecciona un número
para editar, introduce el nuevo valor y pulsa Intro para guardarlo. `0` vuelve al
nivel anterior; una entrada vacía cancela la edición. Las cadenas se pueden
introducir directamente; para vaciarlas usa `""`. Booleanos, listas y objetos
usan JSON (`true`, `false`, `["1.1.1.1"]`). `null` elimina un valor opcional.

## Categorías del programa

- Almacenamiento y rutas de credenciales e iconos.
- Registros, limpieza, retención y nivel de diagnóstico.
- Proyectos: directorio, guardado, intervalos, bases y espacio de trabajo.
- Plugins: directorios, registro, almacenamiento y modo seguro.
- Idioma y directorio de traducciones.
- CLI: confirmación al salir y encadenamiento de comandos.
- Inicio: interfaz preferida de LANCTL y cierre de la GUI al abrir un launcher.
- Red: rango, DHCP, DNS, gateway, máscara, dominio, reservas y TR-064.
- LANIP: perfiles, descubrimiento, concurrencia, tiempos, límites, retención,
  columnas, perfiles Cisco y visor Radmin.
- TUI: distribución, proporciones, columnas, todos los atajos y botones.
- Wake on LAN: puerto, repeticiones, intervalos, espera, método y secuencias.
- LANACCESS: almacenes y configuración del acceso remoto.
- LANMON: activación, perfil, modo, autoridad, interfaz, CIDR, duración, ejecución, intervalos y retención.
- Información del formato.

El catálogo se deriva del esquema canónico: incluye todas sus opciones sin
mantener una segunda lista reducida. Los campos de versión, selección del
proyecto y fecha de descarga se muestran como automáticos y explican cómo se
gestionan. El catálogo muestra rutas de almacenes, nunca descifra sus secretos.
La configuración propia declarada por cada plugin sigue utilizando su servicio
`PluginSettings`; las cuentas, claves y permisos conservan los comandos LANACCESS.

## Categorías del proyecto

Selecciona primero el proyecto mediante `project use`. Las categorías son:

- `identity`: nombre, descripción y autor; UUID, fechas, versiones, hashes y
  contadores se muestran como datos automáticos.
- `lan`: nombre de la LAN, descripción, ubicación, empresa y responsable.
- `network`: CIDR, gateway, DNS, DHCP, descubrimiento, perfil y orden de escaneo,
  modo e intervalo de guardado. Dirección de red, máscara y prefijo se derivan
  del CIDR.
- `vlan`: definición de VLANs, VLAN nativa y VLAN de gestión.

Cada modificación del proyecto escribe el VLF inmediatamente, guarda una copia
en `.lanctl-backups` y actualiza sus hashes. Conserva el inventario y el espacio
de trabajo con cambios pendientes. Las preferencias de red explícitas quedan
versionadas en `lan/settings.override.json` (schemaVersion 1), se mantienen en
los siguientes guardados y se aplican al activar el proyecto. También se aplican
a la sesión que modifica el proyecto activo. Otros procesos ya abiertos pueden
necesitar volver a seleccionar el proyecto para recargar sus preferencias.

## Acceso directo y automatización

```text
lanctl settings --catalog
lanctl settings --catalog --category monitor
lanctl settings --get ip.workers
lanctl settings --set ip.workers 32
lanctl settings --set cli.commandChaining false
lanctl settings --startup-interface gui --close-gui-on-launch off
lanctl settings --set startup.interface tui
lanctl settings --set startup.closeGuiOnLaunch true
lanctl settings --scope project --catalog
lanctl settings --scope project --set identity.name "Oficina principal"
lanctl settings --scope project --set lan.company "Mi empresa"
lanctl settings --scope project --set network.cidr 192.168.20.0/24
```

Para modificar conjuntamente el enlace y la red permitida de acceso remoto,
selecciona el ajuste `access.remote` e introduce un objeto JSON con `bind`,
`cidr` y, opcionalmente, `enabled`, `port`, `passwordAuthentication`, `backend`
o `forcedView`. Esta operación reutiliza la validación y aplicación del backend
remoto existente. Los flags clásicos de `settings` siguen disponibles; no se
mezclan con `--menu`, `--catalog`, `--get` o `--set` en una misma llamada.

La preferencia de inicio solo se aplica sin argumentos. `lanctl --cli`,
`lanctl --tui`, `lanctl --gui` y los comandos explícitos conservan prioridad.
Los valores anteriores sin sección `startup` conservan el inicio CLI y la GUI
principal abierta. Son campos aditivos del esquema de configuración existente.

En SETTINGS del TUI, `Ctrl+S` guarda el formulario mediante el mismo comando
validado que el menú de salida. En Project Manager, `Ctrl+E` edita el proyecto
seleccionado y el atajo de guardado del inventario guarda el proyecto activo.
En los formularios de creación/edición, `Ctrl+S` confirma el formulario local.
`Esc` solicita confirmación antes de descartar cambios. Los atajos locales no
modifican las asignaciones globales del inventario.
