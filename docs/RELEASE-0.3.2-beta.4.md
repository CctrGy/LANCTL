# LANCTL 0.3.2-beta.4

Publicación solicitada en el canal estable, conservando el sufijo beta por
decisión del propietario. La etiqueta de canal no implica ausencia de defectos.

- CLI/TUI propios del orquestador y modos coherentes en los seis launchers.
- Consola de comandos LANMON y panel LANRACK renovados.
- Guardado de proyectos vacíos sin insertar dispositivos reservados.
- Resolución de la carpeta configurada en project update.
- Recuperación de las consolas ante errores de carga y cancelación.
- Preparación de integración ProjectDock, sin reemplazo obligatorio de wrappers.

Validación local: 761 pruebas principales, 635 subpruebas y 21 pruebas GUI;
cobertura con ramas del 65.59%. Las dependencias auditadas no presentaban
vulnerabilidades conocidas en la fecha de revisión.

Los artefactos solo se publican si finaliza correctamente el workflow de release.
No se ha completado una validación manual exhaustiva de Fn/Ctrl, redimensionado
y prompts de todos los TUI, ni las pruebas prolongadas con proyectos concurrentes.
Consulta docs/STABILITY-REVIEW-2026-09-26.md para el alcance y límites de la revisión.
Conserva copias de seguridad antes de actualizar.
