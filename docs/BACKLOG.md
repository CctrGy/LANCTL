# Trabajo pendiente de LANCTL

Lista de asuntos acordados para revisar en una sesión futura. Este documento no
indica que las tareas estén implementadas.

## Prioridad alta: persistencia y fiabilidad

- [ ] Reproducir el fallo de `Ctrl+S` en el TUI y determinar qué cambios no se
  guardan: configuración, proyecto, inventario o estado de los gestores.
- [ ] Verificar el flujo completo de guardado: detección de cambios, validación,
  escritura transaccional, bloqueo, confirmación visual y recarga posterior.
- [ ] Comprobar el comportamiento de `Ctrl+S` con proyecto activo, sin proyecto,
  en cada ventana modal y durante tareas de segundo plano.
- [ ] Revisar la carga de plugins: descubrimiento, dependencias, permisos,
  estados pendiente/activo/fallido, recarga y presentación de errores.

## Project Manager

- [ ] Permitir guardar manualmente el proyecto seleccionado o activo.
- [ ] Añadir edición de nombre, descripción, autor, LAN, ubicación, empresa y
  responsable.
- [ ] Crear formularios modales con cuadros de texto para crear y editar los
  metadatos del proyecto.
- [ ] Validar los datos antes de escribir y pedir confirmación si existen
  modificaciones sin guardar.
- [ ] Refrescar el catálogo y la pestaña de información inmediatamente después
  de crear, editar, guardar, activar o eliminar un proyecto.

## Teclado y ayudas visuales

- [ ] Remarcar `→` con fondo blanco en el pie del menú Plugins.
- [ ] Auditar todos los pies de ventanas para encontrar teclas sin el fondo de
  tecla correcto, incluyendo flechas, teclas de función, `Supr`, `Enter`,
  `Esc` y combinaciones `Ctrl+…`.
- [ ] Revisar el editor de asignaciones: conflictos, teclas reservadas,
  desactivación con `None`, persistencia y restauración de valores iniciales.
- [ ] Verificar por separado qué atajos están activos y cuáles son visibles en
  la barra inferior.
- [ ] Comprobar que los atajos locales de una ventana no se ejecuten fuera de
  ella.

## Consola integrada del TUI

- [ ] Añadir más mensajes útiles sobre inicio y final de tareas, resultados,
  guardado, recarga, cambios pendientes y errores recuperables.
- [ ] Mantener los mensajes breves, con nivel y origen coherentes y sin desplazar
  innecesariamente la tabla principal.
- [ ] Revisar el historial, el límite de líneas y el ajuste al ancho disponible.

## Revisión estética general

- [ ] Auditar bordes, títulos, pestañas, separadores, colores de fondo,
  alineación y recorte en todos los overlays.
- [ ] Probar tamaños de terminal pequeños, medios y muy grandes, además de
  cambios de tamaño mientras el TUI está abierto.
- [ ] Verificar que las ventanas modales oculten correctamente las líneas del
  fondo y que el renderizado diferencial no deje residuos ni produzca parpadeo.
- [ ] Unificar el estilo de selección, campos editables, cambios pendientes,
  estados deshabilitados y mensajes de confirmación.

## Auditoría técnica

- [ ] Revisar concurrencia, bloqueos de archivos y escrituras simultáneas entre
  TUI, CLI, backend y plugins.
- [ ] Revisar tareas de segundo plano, cancelación, cierre seguro y liberación
  de recursos.
- [ ] Confirmar que errores, eventos, logs y puntos de extensión del core se
  emitan de forma coherente en todos los flujos anteriores.
- [ ] Ejecutar pruebas de regresión en Windows instalado, Windows portable,
  Linux ARM64 y acceso remoto.
- [ ] Registrar durante la revisión cualquier hallazgo técnico adicional con
  pasos de reproducción, impacto y prueba de aceptación.
