# Reglas de desarrollo de LANCTL

Antes de crear o modificar código, lee y aplica
[`docs/DEVELOPMENT-RULES.md`](docs/DEVELOPMENT-RULES.md).

Reglas obligatorias resumidas:

- `main` es la rama activa de desarrollo; no se presenta como estable.
- `stable/VERSION` es una fotografía inmutable de una versión estable.
- Las correcciones se desarrollan en ramas separadas y se integran en `main`;
  una versión estable corregida obtiene una rama estable nueva.
- No se reescriben ni reutilizan IDs públicos `a.b.c.d` de eventos, funciones o
  tareas del Core. Los cambios incompatibles requieren una versión de contrato.
- Todo punto de error debe conservar origen y aparecer en `errorList.txt`; tras
  modificar errores se ejecuta `python tools/generate_error_catalog.py`.
- Respeta los límites entre `core`, aplicaciones e interfaces y conserva rutas
  o adaptadores compatibles cuando un contrato público deba trasladarse.
- Datos, credenciales, proyectos, bases, builds y configuración local no se
  versionan. Ejecuta `python tools/check_repository_hygiene.py` antes de Git.
- Actualiza y comprueba las referencias CLI/web cuando cambien parsers,
  comandos, opciones o compatibilidad por versión.
- Una rama `stable/VERSION` debe coincidir con la versión del código. GitHub
  Actions construye y publica automáticamente sus instaladores.
