# Acceso remoto LANCTL

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

Antes de entrar hay que crear al menos una identidad. Se recomiendan claves
públicas y el ámbito debe coincidir con el backend:

```text
lanctl access init --scope service
lanctl access user add administrador --role administrator --ssh-key C:\Users\Victor\.ssh\id_ed25519.pub --scope service
ssh -p 2222 administrador@192.168.1.5
```

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
