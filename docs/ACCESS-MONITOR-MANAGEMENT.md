# LANACCESS y LANMON: administración separada

## LANACCESS

CLI directa, consola interactiva `lanaccess --cli` y TUI `lanaccess --tui`
comparten servicios. En el TUI, N/B cambia de página, A crea, E elimina,
D diagnostica y C permite ejecutar los mismos comandos sin salir.
Los controles se confirman con Intro; no son todavía modales como LANIP.

```text
lanaccess list
lanaccess credential set NAS ssh --username operador
lanaccess credential show cred_IDENTIFICADOR
lanaccess credential delete cred_IDENTIFICADOR
lanaccess protocol list
lanaccess protocol configure NAS ssh --port 22 --driver ssh_generico
lanaccess doctor
lanaccess credential recover
lanaccess credential recover --yes
lanaccess settings
lanaccess settings use-store "otro-almacen.vault" --yes
lanaccess user list
lanaccess user add operador --role operator
lanaccess user disable operador
lanaccess user enable operador
lanaccess user delete operador --yes
```

`user` administra usuarios **remotos de LANCTL**, no usuarios de Windows.
Requiere elevación del sistema operativo. Las contraseñas no se aceptan como
argumentos ni se imprimen; se solicitan interactivamente. Los roles remotos
existentes se reutilizan, no se crea otra base de identidades.

### Almacenes y transporte

Las opciones globales preceden al comando. `--scope program` usa el almacén
configurado; `--scope windows` usa LocalAppData del usuario actual;
`--scope project --project-dir DIRECTORIO` utiliza `access/credentials.vault`
como archivo independiente. No se introduce automáticamente dentro del VLF.
`--database` selecciona el inventario contra el que se resuelven los elementos;
  seleccionar una carpeta de almacén **no cambia el inventario**.

```text
lanaccess --cipher portable --store "mi-almacen.vault" credential set NAS ssh --username operador
lanaccess credential export "copia-cifrada.vault"
lanaccess --cipher portable --store "otro-almacen.vault" credential import "copia-cifrada.vault"
lanaccess --store "otro-almacen.vault" credential recover --yes
lanaccess credential copy "almacen-local.dat" --target-cipher dpapi
```

- `dpapi`: protección ligada al usuario de Windows; no es un proveedor TPM.
- `portable`: AES-256-GCM y Scrypt con parámetros fijos; requiere contraseña
  de al menos 12 caracteres. Disponible también en Linux.
- `auto`: reconoce almacenes existentes. Para crear uno portable se indica
  explícitamente `--cipher portable`. No modifica ni convierte archivos existentes.
- La exportación portable sirve también como copia de recuperación cifrada.
  La contraseña no puede recuperarse si se pierde. No existe contraseña maestra oculta.
- Copiar/importar conserva el origen y verifica el destino. Los conflictos con
  secretos distintos se rechazan. No hay eliminación automática del origen.
- Los IDs se conservan. Al importar entre inventarios distintos no se reasignan
  dispositivos por IP ni alias. `recover --yes` sólo vincula IDs coincidentes
  sin referencia previa, no sobrescribe asociaciones ni elimina entradas.
- Guardar y vincular revierte el almacén ante errores ordinarios del inventario.
  Un corte de proceso entre archivos puede dejar una entrada sin vínculo: `doctor`
  lo detecta. No se promete atomicidad multiarquivo frente a cortes eléctricos.
- Los launchers que utilizan `CredentialStore` reconocen el formato portable,
  pero un servicio sin terminal no puede desbloquearlo interactivamente. No se
  añade una clave en disco ni una variable de entorno para eludir esa protección.
- TPM, desbloqueo hardware y rotación de claves no están implementados.
  La personalización consiste en ámbito y proveedor, no en algoritmos arbitrarios.

Evento nuevo: `LANCTL.Access.Vault.Completed` versión 1, con `operation` y
`count`. Nunca transmite claves, contraseñas, usuarios ni contenido descifrado.
Los eventos y contratos anteriores no se renombran.

## LANMON

```text
lanmon status
lanmon logs --source all --limit 100 --level 20
lanmon logs --project "C:\Proyectos\home.vlf" --source project
lanmon --cli
lanmon --tui
```

La implementación de comandos pertenece ahora a `apps/monitor/commands.py`.
`events` y `events --follow` conservan su comportamiento histórico de monitor;
`logs` es la consulta nueva de registros combinados.
La ruta anterior en LANIP es un adaptador compatible. El motor reutiliza los
servicios de escaneo de LANIP, pero no importa su interfaz CLI para arrancar.

El visor es de lectura: combina logs operativos y auditorías del VLF activo,
etiqueta origen, filtra por nivel y limita lectura/memoria. Las líneas históricas
sin nivel se conservan. R recarga; P/J/A selecciona programa/proyecto/ambos;
N/B pagina en TUI; `level N` cambia el filtro. No realiza seguimiento automático.
Consulta hasta los cinco archivos más recientes por origen, hasta 1 MiB por
archivo; avisa si omite un miembro VLF mayor. No es un buscador histórico completo.

La lectura respeta permisos del sistema de archivos; no concede elevación.
Las órdenes de servicios siguen pasando por el proveedor de plataforma. Los
roles de acceso remoto no equivalen a permisos administrativos del sistema.

## Orquestador e instalador

`lanctl plugin ...` y `lanctl settings ...` son las entradas comunes recomendadas;
las entradas históricas de LANIP permanecen compatibles. Su implementación
todavía se adapta desde LANIP: no se duplica el estado por launcher.

El Setup ofrece accesos opcionales al visor LANMON y a LANACCESS administrativo.
Este último ejecuta `lanctl --admin lanaccess --tui` y solicita UAC explícitamente.
No cambia las ACL existentes, no activa servidores remotos, no crea usuarios,
no configura contraseñas y no eleva todos los launchers por defecto.

LANBACK sigue pendiente. Estos cambios no publican un instalador ni reemplazan
automáticamente la instalación existente.

Referencias del diseño criptográfico: [AES-GCM autenticado](https://cryptography.io/en/latest/hazmat/primitives/aead/)
y [ámbito de protección DPAPI](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata).
