# LANCTL 0.3.3

Nueva versión del canal estable, posterior a 0.3.2-beta.4. Integra el desarrollo
experimental y las correcciones de auditoría de octubre en la rama `main`.
Las ramas y los instaladores de versiones anteriores se conservan.

## Cambios

- GUI de escritorio de LANIP incluida en Windows: inventario editable, filtros,
  grupos, escaneo cancelable, diagnóstico, ajustes y apertura/guardado de proyectos.
- Sesiones y coordinación entre aplicaciones; consolas interactivas y seguimiento
  de registros de LANMON. Se mantienen los seis launchers CLI/TUI existentes.
- IPC de plugins con JSON acotado, límites de recepción y timeout; validación de
  rutas de paquetes LCP y publicación transaccional de plugins.
- Autorización remota actualizada en cada operación, protección de destinos de
  exportación, comprobación CSRF y handshake TLS limitado.
- Verificación de claves SSH antes de autenticar, en la misma conexión Netmiko.
- Integridad de proyectos VLF, confinamiento de workspaces, rechazo de esquemas
  futuros, backups únicos y correcciones de escrituras concurrentes.
- Identidad de dispositivos y límites de descubrimiento corregidos; tareas de
  monitorización actualizadas tras DHCP, cancelación y retirada de dispositivos.
- Cálculo de caídas y salud por servicio corregido. No se reescriben informes
  históricos ya guardados.
- Metadatos, referencias CLI/web y completado Clink actualizados para 0.3.3.
- Instalación remota desde el canal estable por defecto; beta sigue disponible.

## Distribución y validación

El workflow valida pruebas, cobertura, formato, seguridad, higiene, referencias y
catálogo de errores antes de construir Windows x64 y Linux amd64/arm64. Comprueba
instalación, actualización, launchers y desinstalación; genera metadatos y SHA-256
antes de publicar Setup, ZIP portable, DEB y tarballs junto a los scripts remotos.
La Release solo se publica si todas esas comprobaciones terminan correctamente.

La evidencia y las regresiones de las correcciones se documentan en
[AUDIT-CORRECTIONS-2026-10.md](AUDIT-CORRECTIONS-2026-10.md).

## Requisitos y límites

- Windows: la GUI necesita WebView2 Runtime. Linux se distribuye con CLI/TUI;
  el empaquetado gráfico Linux sigue fuera de esta versión.
- La prueba del navegador utiliza un puente API simulado; no sustituye la
  validación interactiva de todas las pantallas y motores nativos.
- La firma Authenticode y la firma detached dependen de los secretos configurados
  en GitHub. Sin ellos se publican artefactos sin firma, con SHA-256 obligatorio.
- El runtime de plugins aislados no constituye un sandbox del sistema operativo.
- Siguen pendientes los trabajos estructurales descritos en la auditoría, incluidas
  transacciones entre almacenes y orden global de locks.

Conserva copias de proyectos, configuración y credenciales antes de actualizar.
