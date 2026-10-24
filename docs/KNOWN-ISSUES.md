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
- La base física histórica no se asigna automáticamente a un proyecto: debe
  importarse explícitamente con `project import-physical ARCHIVO` y guardar
  el proyecto. El original se conserva. Los proyectos actuales sí incluyen
  racks, equipos, cables y CPD en el VLF.
- Las ediciones físicas CLI/TUI/GUI ya aplican `automatic.allChanges` al VLF.
  Las consolas LANWIRE/LANRACK también aplican cierre y temporizador y renuevan
  sus servicios al cambiar de proyecto compartido (`REF-P84-session`). Un
  formulario TUI anterior se cierra sin aplicar su edición al nuevo proyecto.
  Los comandos aislados no tienen temporizador ni preguntan al salir: con
  modo manual/consulta se conserva el workspace y hace falta `project save`.
  Una operación en curso conserva su proyecto original; una base externa
  explícita nunca se incorpora automáticamente al proyecto activo.
- Los plugins Python aislados aplican límites y auditoría, pero no constituyen
  una frontera de seguridad contra código deliberadamente hostil. Instala solo
  paquetes firmados y de confianza.
- Revocar un plugin `trusted` heredado retira su acceso al Core, pero no puede
  detener de forma segura los hilos nativos que ya ejecuta dentro del proceso.
  Si aparece `restartRequired`, es necesario reiniciar ese proceso para retirar
  su código. `REF-P34-runtime` añade ejecución cancelable con API de proceso
  v2; los paquetes heredados no se migran automáticamente. Sus adaptadores y
  certificación quedan en `REF-P34-migration`.
- El estado de terminación de plugins corresponde al proceso propietario que
  lo informa. La revocación se comprueba en cada llamada y los otros propietarios
  reconcilian el registro, pero no existe todavía un resumen global de sus
  confirmaciones. La API v2 tiene un catálogo acotado de tipos y operaciones;
  no sustituye automáticamente toda la API `trusted`.
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
