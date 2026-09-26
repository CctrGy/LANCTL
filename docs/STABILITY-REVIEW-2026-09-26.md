# Revisión de estabilidad — 2026-09-26

Estado: preparación local; no declarada estable, sin publicación ni actualización
de la instalación. Versión mantenida: 0.3.2-beta.1.

## Correcciones de esta revisión

- Guardar un proyecto vacío no vuelve a generar GATEWAY/BRODCAST durante update.
  Se verifica el round-trip del VLF con inventario vacío.
- `project update home.vlf` resuelve la carpeta de proyectos configurada igual
  que las demás operaciones, no exclusivamente el directorio actual.
- Un fallo de carga del panel no derriba la consola de administración.
- Ctrl+C durante una operación vuelve a la consola padre con resultado 130.
- La entrada raíz no devuelve un Namespace de argparse como código de salida.

## Evidencia local en Windows

- Suite principal: 761 pruebas y 635 subpruebas correctas; 21 legacy GUI excluidas.
- GUI heredada por separado: 21 pruebas correctas.
- Coverage con ramas, source=src: 65.59%, supera el umbral CI del 60%.
- 18 invocaciones en procesos separados: seis launchers por --version, --help y /?.
  Datos y secretos aislados en un directorio temporal.
- Ruff, formato, compileall, referencias, catálogo, higiene y diff-check correctos.
- pip check correcto. Bandit sin hallazgos de severidad media/alta.
- `pip_audit . --strict`: sin vulnerabilidades conocidas en dependencias resueltas.
  La auditoría inicial del entorno editable falló por metadatos locales antiguos;
  no equivale a haber auditado todos los paquetes ajenos del entorno.

## Puertas pendientes para publicar estable

1. Validación interactiva real de los TUI: resize, Fn/Ctrl, prompts, buffers,
   navegación entre aplicaciones y cierre con datos pendientes.
2. Build de los seis ejecutables, Setup y portable desde la revisión final.
3. Instalación limpia, actualización y desinstalación con datos de prueba y
   usuario sin privilegios; confirmar conservación de proyectos/credenciales.
4. Pruebas nativas Linux amd64/arm64 y paquetes. No hay distribución WSL
   disponible en este equipo; las pruebas Windows no sustituyen las de Linux.
5. Validación de uso prolongado/concurrencia con dos procesos y copias de proyectos.
6. Consolidar cambios, ejecutar CI sobre el commit final y verificar hashes de
   artefactos antes de crear la rama estable inmutable.

La cobertura deja rutas sin ejercitar: ni las pruebas ni el análisis estático
demuestran ausencia total de defectos. La migración ProjectDock continúa siendo
preparación de desarrollo, no reemplazo completamente validado.
