# LANCTL 0.3.2-beta.1

Beta de desarrollo integrada en `main`; no es una versión estable.

## Cambios

- Integración de LANWIRE experimental: topología, paneles, puertos e interconexiones.
- Gestión CLI/TUI de LANACCESS y almacenes cifrados portables.
- Separación de comandos de LANMON y consulta combinada de logs.
- Corrección de la comparación del inventario al guardar proyectos: el orden de
  pertenencia a grupos no debe provocar una restauración falsa del backup.
- Actualización de documentación, referencias, completado y reglas del repositorio.

## Alcance

Conserva copias de los proyectos antes de probar esta beta. TPM y LANBACK siguen
pendientes. La GUI antigua permanece fuera de la suite predeterminada.
La publicación del código en `main` no implica que los nuevos instaladores estén
compilados, verificados o disponibles en Releases. La instalación existente no se
actualiza con un push del repositorio.
