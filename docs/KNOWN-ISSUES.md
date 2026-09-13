# Limitaciones conocidas de la beta

- Los binarios de una arquitectura no funcionan en otra. Raspberry Pi OS debe
  ser de 64 bits para usar el artefacto `arm64`.
- El descubrimiento depende de la interfaz, los permisos, el firewall y las
  herramientas disponibles. ICMP o ARP pueden estar bloqueados aunque el equipo
  esté conectado.
- `smbclient`, `arping` y `xdg-open` son integraciones opcionales en Linux.
- El tarball Linux no instala ni administra servicios systemd.
- El servicio systemd usa datos en `/var/lib/lanctl` y secretos en
  `/etc/lanctl/access`; no comparte automáticamente el proyecto del usuario.
- El acceso remoto SSH/HTTPS permanece desactivado hasta configurarlo de forma
  local y explícita.
- Los instaladores conservan los datos al desinstalar. Su eliminación requiere
  una acción administrativa independiente.
- La beta no debe ser la única copia de proyectos o inventarios importantes.
- Los plugins Python aislados aplican límites y auditoría, pero no constituyen
  una frontera de seguridad contra código deliberadamente hostil. Instala solo
  paquetes firmados y de confianza.
- `root forced-view` no puede mostrar una ventana en el escritorio interactivo
  cuando el backend se ejecuta como servicio Windows (Session 0).

Las limitaciones resueltas deben retirarse de esta lista en la misma revisión
que incorpore y pruebe la corrección.
