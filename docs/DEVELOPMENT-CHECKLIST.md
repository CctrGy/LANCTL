# Lista de verificaciones al crear o modificar código

Esta lista desarrolla las [reglas de desarrollo](DEVELOPMENT-RULES.md).
Se utiliza para funciones nuevas, correcciones, refactorizaciones e interfaces,
incluidos scripts e instaladores. Una tarea no se declara verificada solo por
haber escrito el código o generado un catálogo.

Marcar lo comprobado y anotar la evidencia. Cuando un apartado no corresponda,
indicar «No aplica» y su motivo. Un requisito aplicable sin comprobar queda
pendiente: no equivale a una verificación correcta. Esta lista no certifica
retroactivamente el código existente ni cierra las tareas abiertas del backlog.

## 1. Antes de implementar

- [ ] Leer las reglas y la documentación del componente afectado.
- [ ] Definir el problema, el comportamiento esperado y cómo comprobarlo.
- [ ] Revisar llamadas, dependencias y contratos públicos afectados; localizar
  servicios existentes antes de duplicar lógica.
- [ ] Trabajar en una rama de desarrollo apropiada. Respetar la rama de destino
  indicada por el usuario y las ramas estables inmutables.
- [ ] Identificar cambios locales ajenos a la tarea y conservarlos.
- [ ] Prever si el cambio afecta a idiomas, errores, permisos, proyectos,
  persistencia, comandos o distribución y aplicar los apartados correspondientes.

## 2. Textos visibles e idiomas

- [ ] Revisar todos los textos introducidos o modificados: botones, etiquetas,
  títulos, pestañas, menús, ayudas CLI/TUI, placeholders, accesibilidad, estados,
  validaciones, confirmaciones, errores y pantallas del instalador.
- [ ] Buscar una clave existente con el mismo significado. Si no existe, crear
  una clave estable en la fuente bilingüe correspondiente de
  `src/lanctl/shared/ui_messages*.py`, conforme a [LANG.md](LANG.md).
- [ ] Resolver el texto mediante `t(...)` en Python o los bindings de
  `LanctlI18n` en la GUI. Almacenar claves en los metadatos y traducir al
  presentar, evitando fijar el idioma al importar un módulo.
- [ ] Mantener inglés y español con las mismas claves y parámetros. Interpolar
  valores mediante placeholders con nombre; evitar concatenar fragmentos que
  impidan cambiar el orden de una frase en otro idioma.
- [ ] Regenerar los `.lang`, el fallback JavaScript y el manifiesto del bundle
  desde sus fuentes. No editar manualmente los archivos generados ni las
  traducciones personalizadas del usuario.
- [ ] En instaladores, usar recursos de idioma separados del código y documentar
  cualquier formato específico de plataforma. Mantener independiente la elección
  del idioma del instalador y la del programa.
- [ ] Mantener sin traducir IDs, comandos, claves técnicas, rutas y valores
  persistidos, datos del usuario, trazas, salida externa y registros canónicos.
  Una explicación traducida no sustituye ni altera la evidencia técnica.
- [ ] Escapar las traducciones y los valores al insertarlos en HTML. No evaluar
  traducciones como código ni sustituir arbitrariamente textos del documento.
- [ ] Comprobar inglés/español, fallback, parámetros y textos dinámicos en las
  pantallas afectadas. Revisar tamaños, atajos y accesibilidad cuando cambie el
  texto. La paridad de claves no demuestra cobertura visual completa.

Comandos cuando cambien los recursos de idioma:

```bash
python tools/generate_language_catalogs.py
python tools/generate_installer_languages.py
python tools/generate_language_catalogs.py --check
python tools/generate_installer_languages.py --check
python tools/audit_language_usage.py --check
```

La auditoría ayuda a localizar referencias y candidatos; revisar sus resultados
y el flujo real. No convierte automáticamente todos los literales detectados en
textos traducibles ni demuestra por sí sola que no falte ninguna traducción.

## 3. Errores y diagnóstico

- [ ] Localizar los puntos donde puede fallar la operación, incluidos entradas
  inválidas, permisos, red, archivos, dependencias y procesos externos.
- [ ] Utilizar los servicios y adaptadores de errores existentes. Conservar el
  origen real, la excepción o causa y el código/nivel pertinente según el
  contrato del componente. No inventar un sistema paralelo de códigos.
- [ ] Mantener los IDs públicos existentes. No renombrarlos, reutilizarlos ni
  agrupar fallos distintos bajo una identidad que pierda su significado.
- [ ] Presentar un mensaje comprensible y traducible, asociado al diagnóstico
  original. No revelar contraseñas, tokens ni información privada en mensajes,
  trazas, registros o informes exportados.
- [ ] No ocultar un fallo con un `except` vacío, un resultado de éxito o una
  colección vacía. Distinguir cancelación, ausencia esperada y error real.
- [ ] Verificar el estado que queda tras un fallo: datos conservados, recursos
  liberados, interfaz recuperable y posibilidad de reintento cuando corresponda.
- [ ] Tras añadir, modificar, retirar o mover puntos de error, regenerar
  `errorList.txt` y comprobar el diff. Nunca editarlo a mano. Si un nuevo tipo de
  fuente queda fuera del generador, documentar la carencia y ampliar su cobertura;
  no declarar ese origen catalogado sin comprobarlo.

```bash
python tools/generate_error_catalog.py
python tools/generate_error_catalog.py --check
```

## 4. Arquitectura, contratos y proyectos

- [ ] Respetar la separación entre Core, aplicaciones e interfaces. CLI, TUI y
  GUI utilizan servicios compartidos para las mismas reglas de negocio.
- [ ] Mantener el significado de IDs públicos `a.b.c.d`, namespaces y contratos
  versionados. Un cambio incompatible requiere una versión de contrato nueva;
  conservar adaptadores o rutas compatibles cuando corresponda.
- [ ] Validar tipos, rangos y valores en el servicio, además de los controles de
  interfaz. Respetar el catálogo y las políticas de configuración existentes.
- [ ] Distinguir configuración global, de usuario, de servicio y de proyecto.
  No guardar una opción en otro ámbito ni cambiar preferencias implícitamente.
- [ ] En operaciones de proyecto, comprobar el contexto y los permisos en el
  servicio; no depender solo de la selección visual ni aceptar contextos obsoletos.
- [ ] Si afecta a varios launchers, verificar que comparten el proyecto y la
  configuración esperados sin mezclar datos entre proyectos o sesiones.

## 5. Persistencia, permisos y recursos

- [ ] Utilizar las rutas y servicios de almacenamiento existentes; no introducir
  rutas personales absolutas ni usar el directorio del código para datos locales.
- [ ] Conservar `schemaVersion`, validación y migraciones explícitas. No tratar
  datos corruptos como una instalación vacía ni sobrescribirlos silenciosamente.
- [ ] Aplicar transacciones, bloqueo y escritura atómica cuando corresponda;
  comprobar que un error no deja cambios parciales no documentados.
- [ ] Preservar proyectos, credenciales y preferencias al actualizar o cancelar.
  Preparar las pruebas en directorios temporales, sin migrar datos reales.
- [ ] Mantener la comprobación de permisos en el backend. Elevar solo las
  operaciones que lo necesitan y conservar la identidad del usuario para sus datos.
- [ ] Evitar secretos en argumentos, archivos temporales, registros o el historial
  del shell. Pasar argumentos a procesos de forma estructurada, sin interpolar
  entradas arbitrarias en comandos de shell.
- [ ] Cerrar archivos, conexiones, hilos y procesos propios. Evitar bloquear la
  interfaz con operaciones largas y conservar cancelación o recuperación segura.

## 6. Interfaces, comandos e instaladores — según el alcance

- [ ] GUI: controles adecuados al tipo de dato, etiquetas traducibles, foco y
  navegación por teclado, estado de operación y errores visibles y recuperables.
- [ ] TUI: conservar navegación y ayudas dentro de la interfaz; restaurar el
  estado de la terminal al salir o fallar.
- [ ] CLI: mantener ayuda, argumentos, alias, códigos de salida y separación entre
  salida útil y diagnóstico. Comprobar que las opciones documentadas funcionan.
- [ ] Si cambian parsers, comandos u opciones, actualizar las referencias CLI/web
  y los completados de terminal afectados, incluida la validación Clink aplicable.
- [ ] Instaladores: incluir recursos y dependencias reales, idiomas, componentes
  seleccionados, permisos y comportamiento de actualización/desinstalación.
- [ ] Versiones: mantener coherentes aplicación, metadatos y scripts de build.
  Comprobar la arquitectura y plataforma objetivo; modificar fuentes o renombrar
  archivos no equivale a recompilar ni a validar un instalador nuevo.

## 7. Verificaciones automáticas y funcionales

- [ ] Ejecutar las pruebas relacionadas y añadir regresiones cuando sean útiles
  para comprobar el comportamiento o un contrato. Ajustar el alcance al cambio;
  una edición documental no exige ejecutar toda la aplicación.
- [ ] En cambios transversales, ejecutar la suite completa cuando sea viable y
  los recorridos manuales necesarios de CLI/TUI/GUI y plataformas afectadas.
- [ ] Comprobar el caso correcto y los errores relevantes; incluir persistencia,
  permisos, contexto de proyecto, compatibilidad y recuperación cuando proceda.
- [ ] Ejecutar las comprobaciones de formato, catálogo, referencias e higiene.
  Si un generado queda obsoleto por el cambio, regenerarlo y revisar el diff.
- [ ] Registrar comando, resultado y limitaciones reales. No omitir o debilitar
  pruebas para presentar un fallo como éxito; distinguir comprobaciones locales,
  pruebas omitidas y certificación pendiente en otra plataforma.

Comprobaciones comunes, con el Python del entorno del proyecto:

```bash
python -m ruff check .
python -m ruff format --check .
python tools/generate_error_catalog.py --check
python tools/generate_cli_reference.py --check
python tools/generate_web_reference.py --check
python tools/check_repository_hygiene.py
git diff --check
```

Para código, seleccionar las pruebas pertinentes y ampliar cuando el alcance lo
requiera; por ejemplo, `python -m pytest -q tests/ARCHIVO_AFECTADO.py`. La suite
general se ejecuta con `python -m pytest -q`. Los comandos de idiomas del apartado
2 se añaden cuando cambie su fuente o consumo.

## 8. Documentación, Git y entrega

- [ ] Actualizar la documentación del comportamiento modificado, la compatibilidad
  y el backlog cuando la tarea corresponda a un pendiente existente.
- [ ] Ejecutar la higiene antes de preparar el commit y revisar el conjunto exacto
  que se va a subir, incluidos archivos nuevos y eliminaciones.
- [ ] Excluir datos, proyectos, credenciales, registros, configuración local,
  entornos, builds e instaladores. Mantener los artefactos en el canal de
  distribución previsto, fuera del historial Git.
- [ ] Comprobar también `git diff --cached --check` sobre los cambios preparados.
- [ ] Cuando se solicite subir, comprobar la rama remota de destino, conservar
  cambios ajenos y verificar el resultado de la subida sin sobrescribir historial.
- [ ] Entregar un resumen de qué cambió, qué se verificó y qué queda pendiente.
  No declarar estable o completamente validado un cambio con fallos pendientes.

Registro breve para cada entrega:

```text
Cambio y comportamiento esperado:
Idiomas: comprobado / pendiente / no aplica (motivo)
Errores y catálogo: comprobado / pendiente / no aplica (motivo)
Contratos, permisos, datos y proyecto: resultado y apartados aplicables
Pruebas y recorridos: comandos, plataforma y resultados
Generados, referencias, formato e higiene: resultado
Documentación y pendientes: rutas o tareas afectadas
Git e instalables: rama/commit o artefactos, solo si se solicitaron y realizaron
Limitaciones y fallos sin resolver:
```
