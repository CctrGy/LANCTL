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

`lanctl access setup-wizard` configura ambos autenticadores desde una consola
local. Puede crear reglas `netsh`/`ufw` únicamente tras confirmación; cada regla
queda limitada a la IP LAN, puerto TCP y CIDR indicados. Si una etapa falla, se
detienen los procesos iniciados, se eliminan las reglas creadas y SSH/HTTPS
vuelven a quedar apagados.

Los certificados autogenerados son autofirmados: distribuye su huella mediante
un canal confiable. `access status` distingue configuración habilitada de
proceso realmente activo. La recuperación se ejecuta localmente y no existen
cuentas o contraseñas predeterminadas.
