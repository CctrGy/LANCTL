# Despliegue empresarial de acceso remoto

Esta guía describe un nodo LANCTL administrado dentro de una LAN confiable.
SSH y HTTPS permanecen desactivados hasta completar la configuración y no se
publican directamente en Internet.

## Preparación y cuentas

1. Reserva una IP para el nodo y limita el CIDR al segmento administrado.
2. Instala LANCTL como administrador y conserva `ProgramData\LANCTL` en la
   política de copias de seguridad.
3. Inicializa el ámbito de servicio y crea primero un administrador con clave
   SSH Ed25519:

```text
lanctl access init --scope service
lanctl access user add administrador --role administrator --ssh-key administrador.pub --scope service
lanctl access configure ssh --bind 192.168.10.5 --cidr 192.168.10.0/24 --port 2222 --scope service
lanctl access certificate --common-name lanctl.intranet --scope service
```

Los perfiles de mínimo privilegio son `viewer` (observador), `operator`
(operador) y `administrator` (administrador). `manager` añade gestión de
proyectos y automatizaciones, pero no recibe `system.destructive`. Usa
`--expires FECHA_ISO_CON_ZONA` para contratistas y sesiones de mantenimiento.

## Servicio, firewall y certificados

```text
lanctl monitor service install --yes
lanctl access setup-wizard --scope service
lanctl monitor service start
lanctl access status --scope service --json
```

El asistente solicita confirmación antes de crear reglas de firewall. Sustituye
el certificado autofirmado por uno de la PKI de la organización cuando exista,
distribuye la huella por un canal independiente y conserva la clave privada con
ACL exclusiva de administradores y SYSTEM. Nunca habilites autenticación por
contraseña SSH salvo que la política local lo exija.

## Operación y auditoría

- Revisa periódicamente cuentas caducadas, bloqueos, conexiones y cierres de
  sesión en el historial.
- Revoca sesiones de mantenimiento con `lanctl access session revoke ID`.
- Usa `root status` para comprobar backend y vista; `root forced-view` requiere
  administrador y una sesión de usuario capaz de mostrar ventanas.
- Prueba varios clientes contra un nodo de preproducción antes de ampliar el
  CIDR o desplegar una actualización.
- Ejecuta `lanctl database --diagnose --json` y exporta una copia verificada
  antes de actualizar.

## Actualización y recuperación

El Setup reemplaza binarios, pero no elimina datos de `ProgramData\LANCTL`.
Tras actualizar, comprueba versión, servicio, autenticación por clave y una
consulta de inventario. Si el servicio no arranca, deshabilita temporalmente el
acceso, restaura la copia conforme a [STORAGE.md](STORAGE.md) y consulta
[TROUBLESHOOTING.md](TROUBLESHOOTING.md). La desinstalación tampoco elimina los
datos de usuario; su borrado debe ser una decisión administrativa separada.
