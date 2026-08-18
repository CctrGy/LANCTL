# LANCTL 0.3.0-beta.20

Versión beta para evaluación en Windows x64. Incluye ejecutables autocontenidos:
no requiere una instalación de Python en el equipo de destino.

## Artefactos Windows

- `LANCTL-0.3.0-beta.20-windows-x64-setup.exe`: instalador con desinstalador,
  integración opcional con PATH y accesos directos separados para TUI, CLI y GUI.
- `LANCTL-0.3.0-beta.20-windows-x64-portable.zip`: distribución extraíble que
  conserva sus datos bajo su propia carpeta y no modifica el sistema.
- `SHA256SUMS.txt`: hashes de todos los archivos publicados.

## Cambios destacados

- TUI basada en Rich con ventanas modales adaptables y gestores de proyectos,
  plugins y configuración.
- Acceso SSH restringido y backend remoto con estado, refresco y apertura de vistas.
- Políticas de guardado de proyectos VLF y contratos ampliados para plugins.
- Mejoras de descubrimiento, presentación del inventario y entrada segura de secretos.

## Advertencias beta

- Los binarios no están firmados con un certificado comercial; Windows puede mostrar
  SmartScreen. Verifica siempre `SHA256SUMS.txt` antes de ejecutarlos.
- El acceso remoto permanece desactivado hasta que un administrador lo configura.
- Una desinstalación normal conserva los datos y proyectos bajo `ProgramData\\LANCTL`.
