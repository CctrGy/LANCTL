# Reglas de desarrollo, ramas y distribución

Estas reglas son el contrato de trabajo del repositorio. Se aplican a código,
documentación, plugins, automatizaciones, empaquetado y publicaciones.

## Modelo de ramas

- **`main` es exclusivamente la rama de trabajo.** Recibe el desarrollo
  integrado y puede contener una versión todavía no declarada estable.
- **`stable/VERSION` representa una versión estable concreta e inmutable.** Se
  crea desde un commit validado de `main`, por ejemplo `stable/0.3.2`. Después
  de publicarla no se añaden commits, no se fuerza su historial y no se mueve.
- **Las ramas adicionales son temporales.** Correcciones, funciones,
  experimentos, documentación y mantenimiento se realizan en ramas con un
  propósito identificable y se integran en `main` mediante revisión.
- Una corrección de una versión estable se desarrolla fuera de su rama
  estática. El resultado usa un número de versión nuevo y, cuando se declare
  estable, una rama `stable/NUEVA_VERSION` nueva.
- Nunca se mezcla `main` dentro de una rama estable ya publicada.

## Publicación automática de versiones estables

Al subir por primera vez una rama `stable/VERSION`, el workflow de Release:

1. exige que `VERSION` coincida con `lanctl.__version__`;
2. ejecuta pruebas, cobertura, formato, seguridad, referencias y catálogo de
   errores;
3. valida que `packaging/clink/lanctl.lua` cubra todos los launchers, comandos,
   alias y opciones publicados por los parsers de esa versión mediante
   `tests/test_clink.py`; el archivo queda congelado con la rama estable y se
   incluye en el instalador de Windows, mientras Linux conserva su completado
   nativo y sus launchers sin depender de Clink;
4. compila el Setup y ZIP portable de Windows;
5. compila DEB y tarballs para Linux `amd64` y `arm64`;
6. prueba instalación, actualización y desinstalación del Setup;
7. genera metadatos y sumas SHA-256;
8. crea el tag `vVERSION` y la GitHub Release con todos los instaladores.

El soporte estable se valida en Windows y Linux. Los sistemas Apple quedan
fuera del alcance hasta que una decisión futura cambie expresamente esta regla.

Una rama estable se publica como Release estable incluso si se conserva un
sufijo histórico en su nombre. Los tags creados directamente desde `main`
siguen el canal de prueba y los sufijos `alpha`, `beta` o `rc` se publican como
pre-release.

## Errores y origen

- Cada error debe conservar el punto y el origen real donde se produce.
- `errorList.txt` es generado, no se edita manualmente.
- Tras añadir, retirar o mover un punto de error se ejecutan:

```text
python tools/generate_error_catalog.py
python tools/generate_error_catalog.py --check
```

- Un manejador genérico no debe hacer que errores distintos pierdan su origen
  o compartan de forma accidental una identidad pública.

## Identificadores y retrocompatibilidad

- Los IDs públicos del Core, eventos, funciones y tareas siguen cuatro
  segmentos `a.b.c.d`.
- El namespace `LANCTL` está reservado al núcleo; cada plugin utiliza su propio
  namespace.
- Un ID publicado no se renombra, reutiliza ni cambia de significado.
- Los contratos versionados conservan las versiones anteriores mientras sean
  compatibles. Un cambio incompatible crea una versión nueva y documenta la
  migración.
- Los plugins deben declarar su rango de versiones LANCTL y su versión de
  esquema; no se relaja esa validación para aceptar datos ambiguos.

## Distribución del código

- `src/lanctl/core/` contiene contratos y servicios compartidos y no debe
  depender de una interfaz concreta salvo mediante adaptadores de
  compatibilidad documentados.
- `src/lanctl/apps/` contiene cada aplicación y sus capas de dominio,
  infraestructura e interfaces.
- CLI, TUI y GUI llaman a servicios compartidos; no duplican reglas de negocio
  incompatibles.
- Los formatos persistentes llevan `schemaVersion`, validación y migraciones
  explícitas. Nunca se interpreta corrupción como una colección vacía.
- Al mover un contrato público se mantienen importaciones compatibles durante
  la transición y se añaden pruebas de regresión.

## Archivos versionados, generados y locales

- Se versionan fuentes, pruebas, documentación, scripts reproducibles,
  manifiestos y referencias generadas requeridas por CI.
- No se versionan ejecutables, `dist/`, `build/`, bases de datos, proyectos VLF,
  registros, credenciales, claves, configuración privada ni estado de usuario.
- Los instalables pertenecen a GitHub Releases, no al historial Git.
- Antes de preparar un commit se ejecuta:

```text
python tools/check_repository_hygiene.py
python tools/generate_cli_reference.py --check
python tools/generate_web_reference.py --check
```

## Condiciones mínimas para integrar

- Pruebas relacionadas y suite completa cuando el alcance lo permita.
- Ruff, catálogo de errores, referencias, higiene y `git diff --check` limpios.
- Documentación y compatibilidad por versión actualizadas.
- Ninguna modificación accidental de datos del usuario o ramas estables.
