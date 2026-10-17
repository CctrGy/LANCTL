# Limitaciones conocidas

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
- La versión experimental no debe ser la única copia de proyectos o inventarios importantes.
- Los plugins Python aislados aplican límites y auditoría, pero no constituyen
  una frontera de seguridad contra código deliberadamente hostil. Instala solo
  paquetes firmados y de confianza.
- Revocar un plugin `trusted` heredado retira su acceso al Core, pero no puede
  detener de forma segura los hilos nativos que ya ejecuta dentro del proceso.
  Si aparece `restartRequired`, es necesario reiniciar ese proceso para retirar
  su código. El aislamiento cancelable completo sigue en `REF-P34-runtime`.
- Todavía no existe un editor oficial de plugins configurado. Los complementos
  que requieren firma y confianza no se habilitan automáticamente por estar
  incluidos en la distribución; P40/P42 requieren identidad y paquetes firmados.
- La selección explícita de interfaz vincula ICMP y ARP al origen elegido.
  En ese modo se omiten los descubridores adicionales y la resolución de nombres
  que todavía no garantizan ese origen. La certificación con varias NIC en
  Windows/Linux y el resto de protocolos siguen en `REF-P47-interface`.
- `root forced-view` no puede mostrar una ventana en el escritorio interactivo
  cuando el backend se ejecuta como servicio Windows (Session 0).

Las limitaciones resueltas deben retirarse de esta lista en la misma revisión
que incorpore y pruebe la corrección.
