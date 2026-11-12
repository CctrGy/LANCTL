# Acceso remoto LANCTL

Para nodos permanentes, políticas de mínimo privilegio, PKI, actualización y
recuperación, consulta la [guía de despliegue empresarial](ENTERPRISE.md).

SSH y HTTPS están desactivados inicialmente y son independientes de MONITOR.
Ambos comparten usuarios y RBAC, pero SSH autentica claves públicas y la web
usa hashes Scrypt; una clave SSH nunca se transforma en contraseña web.

```text
lanctl access init
lanctl access configure ssh --bind 192.168.1.5 --cidr 192.168.1.0/24 --port 2222
lanctl access rotate-host-key --yes
lanctl access user add alice --role operator --ssh-key alice.pub
lanctl access enable ssh

lanctl access configure https --bind 192.168.1.5 --cidr 192.168.1.0/24 --port 8443
lanctl access certificate --common-name lanctl.local
lanctl access user add webadmin --role administrator --password-auth on
lanctl access enable https
```

Nunca se usa `0.0.0.0` por defecto. Cada petición/conexión se valida contra el
CIDR gestionado. No hay UPnP, NAT automático, CORS wildcard, shell del sistema,
SFTP/SCP ni forwarding SSH. Las reglas de firewall no se modifican por defecto.

`lanctl access setup-wizard --scope user` configura ambos autenticadores para
una ejecución interactiva. En un nodo MONITOR permanente se usa
`--scope service`: Windows conserva los secretos en
`ProgramData\LANCTL\access` y Linux en `/etc/lanctl/access`. El supervisor del
backend activa o detiene los listeners habilitados y los recupera tras un
reinicio. Puede crear reglas `netsh`/`ufw` únicamente tras confirmación; cada regla
queda limitada a la IP LAN, puerto TCP y CIDR indicados. Si una etapa falla, se
detienen los procesos iniciados, se eliminan las reglas creadas y SSH/HTTPS
vuelven a quedar apagados.

Los certificados autogenerados son autofirmados: distribuye su huella mediante
un canal confiable. `access status` distingue configuración habilitada de
proceso realmente activo. La recuperación se ejecuta localmente y no existen
cuentas o contraseñas predeterminadas.

## Cuenta inicial desde el instalador de Windows

Setup ofrece **Crear la primera cuenta de acceso remoto del servicio**. Después
de copiar los ejecutables y proteger el directorio de acceso, abre el asistente
`lanaccess remote-setup` con los privilegios de la instalación. Solicita usuario,
contraseña (al menos 12 caracteres) y confirmación directamente en su ventana.
No recibe contraseñas por línea de comandos ni las guarda en archivos temporales.

La cuenta tiene el rol `administrator` de LANACCESS y pertenece al ámbito
`service`, en `ProgramData\LANCTL\access\users.dc`; no crea usuarios de Windows
ni credenciales para dispositivos del inventario. El almacén conserva únicamente
el hash Scrypt. Si ya existen cuentas, las conserva y bloquea una nueva creación
inicial; para administrarlas usa los comandos `access user` con `--scope service`.
Las rutas personalizadas requieren esa administración existente, sin sobrescribir
su configuración desde este asistente.

Crear la cuenta no habilita SSH/HTTPS ni modifica el firewall. Configura después
los endpoints y autenticadores necesarios siguiendo los pasos anteriores. Es
posible omitir o cerrar el asistente; una instalación silenciosa no lo abre.

## Remote Access desde SETTINGS

La pestaña `REMOTE ACCESS` de F12 reúne la IP de escucha, CIDR autorizado,
puerto, autenticación, tipo de backend y vista forzada predeterminada. El modo
`service` usa el servicio MONITOR y continúa funcionando sin TUI/GUI ni sesión
interactiva; el modo `user` inicia un backend oculto en la sesión actual y sí
puede abrir ventanas visibles. Para hacer persistente el primero:

```text
lanctl monitor service install --yes
lanctl monitor service start
```

Al guardar ajustes remotos, LANCTL confirma la parada del listener anterior y
el arranque de la revisión nueva antes de guardar las preferencias. Cambiar
backend, IP, puerto, CIDR o autenticación reinicia el listener correspondiente;
las conexiones SSH abiertas se cierran. El servicio MONITOR debe estar activo
y actualizado para confirmar los cambios del backend `service`. Un timeout,
una denegación o un fallo de disco no se presentan como guardado correcto.

La operación mantiene un registro local `config.json.remote-transaction.json`
junto a la configuración del programa. Contiene revisiones, rutas e identidad
del proceso, sin contraseñas, hashes de usuarios ni claves privadas. Si falla
antes del guardado del programa, se intenta restaurar el endpoint anterior;
si el programa ya se guardó, se conserva el backend confirmado. Los cambios
concurrentes de HTTPS, usuarios y sesiones se preservan. Los archivos de usuario
y las claves preexistentes no se regeneran ni se copian para compensar.

Si la recuperación falla, el registro se conserva y bloquea otra modificación
remota. Se reintenta al abrir LANCTL de forma interactiva y antes del siguiente
cambio remoto. Las operaciones del ámbito `service` vuelven a exigir elevación;
no se solicita ni concede automáticamente. Un conflicto de revisión se informa
sin sobrescribir la modificación ajena. La parada independiente verifica la
identidad mediante un handle nativo en Windows y requiere `pidfd` en Linux.
No se termina un PID cuya identidad no pueda comprobarse. Las instalaciones
anteriores sin confirmación de propietario requieren actualizar/reiniciar su
backend antes de administrarlo mediante este ciclo.

Antes de entrar hay que crear al menos una identidad. Se recomiendan claves
públicas y el ámbito debe coincidir con el backend:

```text
lanctl access init --scope service
lanctl access user add administrador --role administrator --ssh-key C:\Users\Victor\.ssh\id_ed25519.pub --scope service
ssh -p 2222 administrador@192.168.1.5
```

Desde `F12 > REMOTE ACCESS > Usuarios remotos` se abre el administrador de
cuentas. La tabla muestra usuario, nivel de acceso, estado y si existe una
contraseña, pero nunca revela hashes ni secretos. Sus controles son `N` para
crear, `P` para cambiar contraseña, `R` para cambiar rol, `E` para
activar/desactivar y `Supr` para eliminar. Los niveles integrados son `viewer`,
`operator`, `manager` y `administrator`.

Las cuentas se almacenan en `users.dc`. Aunque el archivo sea estructurado, las
contraseñas solo aparecen como hashes Scrypt con sal individual. Al abrir por
primera vez esta versión, un `users.json` anterior se migra automáticamente sin
perder las cuentas existentes.

La sesión resultante es la consola restringida de LANCTL, no una shell de
Windows. Además de los comandos autorizados dispone de controles exclusivos
para el ordenador raíz:

```text
root status
root refresh
root forced-view gui
root forced-view tui
root forced-view plugins
root forced-view projects
root forced-view settings
```

`root status` diferencia `BACKEND`, `TUI`, `GUI`, `TUI+BACKEND`,
`GUI+BACKEND` y `STOPPED`. `root refresh` actualiza la lista ya visible sin
iniciar un escaneo nuevo. `root forced-view` abre o enfoca la vista solicitada.
Por aislamiento de Windows, un servicio que corre en Session 0 no puede dibujar
una ventana sobre el escritorio del usuario: para esa acción usa backend
`user`, o mantén una TUI/GUI agente abierta. Las operaciones de consulta,
inventario y escaneo siguen disponibles desde el backend `service`.

Las eliminaciones remotas de elementos, grupos y proyectos requieren el permiso
adicional `system.destructive`, reservado al rol `administrator`. Los roles
`operator` y `manager` no reciben ese permiso aunque puedan modificar otros
datos de su ámbito.

## Límites de salida de comandos

Los subcomandos autorizados se ejecutan sin shell y con stdin cerrado. La captura
por defecto drena stdout y stderr incrementalmente, reteniendo como máximo 1 MiB
agregado. El exceso se descarta hasta que el comando termina o vence su timeout;
no se crea un archivo temporal ni un hilo lector por stream. La respuesta final
incluye el marcador de truncamiento traducido dentro del límite de 1 MiB UTF-8.
Se conserva stdout seguido de stderr; no se garantiza su orden cronológico mutuo.

El timeout devuelve 124 y conserva el ID del diagnóstico. El adaptador admite
un evento de cancelación opcional y devuelve 130; no presupone que desconectar
un cliente proporcione ese evento. Al cancelar/expirar se cierran pipes y se
recoge el proceso directo. En POSIX se limpia además el grupo de procesos creado
para esa invocación, incluidos hijos que heredaron los pipes. La limpieza de
árboles de procesos Windows requiere certificación nativa y no se afirma aquí.
Los runners personalizados inyectados mantienen su contrato anterior: deben
proporcionar sus propios límites de captura; el límite de respuesta sí se aplica.

## Web común de los launchers

La raíz HTTPS y `/lanctl` abren la navegación común. La barra lateral puede
ocultarse y reaparecer con el botón de menú; permanece al cambiar de aplicación.

| Ruta | Interfaz reutilizada |
| --- | --- |
| `/lanctl/panel` | LANCTL: proyectos, plugins y configuración |
| `/lanctl/ip` | LANIP |
| `/lanctl/wire` | LANWIRE |
| `/lanctl/access` | LANACCESS |
| `/lanctl/rack` | LANRACK |
| `/lanctl/mon` | LANMON |

Cada vista carga el HTML, CSS y JavaScript de la GUI instalada dentro de un
marco del mismo origen. `web-bridge.js` adapta el contrato pywebview a una API
HTTP autenticada; no se mantiene una segunda implementación del dominio.
El contenedor comparte la selección de proyecto y las preferencias de idioma y
tema del servicio. Estas preferencias pertenecen al usuario del servicio; no se
copian automáticamente desde otro ordenador.

El backend valida una lista explícita de métodos por aplicación, permisos RBAC,
CSRF y contexto de proyecto antes de llamar a las API GUI existentes. Las
instancias de API se separan por sesión: desbloquear la bóveda en un navegador
no desbloquea la de otro. Abrir otro launcher navega a su ruta en la misma web.
Las operaciones exclusivas del escritorio, como abrir una terminal del servidor
o elegir carpetas nativas, no se exponen. El selector web de proyectos ofrece
los proyectos registrados y los creados en la carpeta gestionada del servicio.
Las rutas anteriores `/index.html` y `/api/rpc` se conservan por compatibilidad.

Para publicar `https://core.lan/lanctl/`, el proxy debe conservar el prefijo y el
origen externo debe coincidir con el origen permitido del servicio. Esta
función no configura DNS, certificados ni el proxy inverso y no modifica los
puertos de otros servicios. En la RPi de prueba se utiliza temporalmente
`https://192.168.1.9:8443/lanctl/panel`.

### Menú compacto y enlaces a otros servicios

El menú común distribuye los seis launchers sin scroll, seguido de
Configuración general, el proyecto activo y un bloque inferior de servicios.
En pantallas bajas reduce separaciones y descripciones, conservando el orden
vertical de los launchers. Al plegarse, desaparece por completo
y deja el ancho disponible al contenido. Configuración abre la ventana de
ajustes existente de LANCTL y respeta `system.configure`.

Las direcciones de los otros servicios se definen en el entorno del proceso:
`LANCTL_WEB_HARDWARE_URL`, `LANCTL_WEB_DNS_URL` y `LANCTL_WEB_VPN_URL`.
Aceptan enlaces HTTP/HTTPS sin credenciales. Si no se configura una dirección,
se conserva su espacio como etiqueta inactiva. Se abren en otra pestaña sin
acceso a la ventana de LANCTL. Cada servicio conserva su propia autenticación.
Estas variables son propias del despliegue; no se fijan IP o puertos personales
en los fuentes ni se adivina una web a partir del puerto UDP de WireGuard.

En la RPi5 se localizaron Hardware en `/hardware/`, Pi-hole en `/admin/` y
WireGuard VPN en `/vpn/`, servidos por el acceso común `https://core.lan`.
El proxy Caddy de ese acceso ya existía al revisar esta modificación; no se
cambió su configuración ni la de los otros servicios.
