# LANCTL 0.3.1-beta.3

Versión de prueba publicada desde `main` como **pre-release**. Puede contener
funciones todavía no sometidas a un ciclo completo de validación. La versión
conservada como estable sigue siendo `0.3.1-beta.1` en la rama
`stable/0.3.1-beta.1`, su tag y su GitHub Release.

## Cambios destacados

- Reference usa la exploración por categorías como portada y abre el catálogo
  completo al seleccionar una categoría o realizar una búsqueda.
- Nueva exploración por acciones con procedimientos completos para proyectos,
  plugins, configuración LAN, SSH, acceso remoto, monitorización, copias de
  seguridad e inventario de dispositivos.
- Las entradas y guías de Reference muestran la versión contra la que fueron
  verificadas. El formato admite también versiones de incorporación, retirada
  o compatibilidad exclusiva cuando ese historial esté confirmado.
- Mejoras acumuladas en CLI, TUI y GUI para configuración, inventario y manejo
  de dispositivos recurrentes.
- Autocompletado Lua de Clink actualizado para distinguir `lanctl`, `lanip` y
  `als`, registrar todos los ejecutables de la suite y completar sus launchers.

## Canal y estabilidad

GitHub debe mostrar esta versión como **pre-release**, no como Latest estable.
Los instaladores del release `v0.3.1-beta.1` permanecen disponibles y no se
reemplazan. Los usuarios que prueben esta versión deberían conservar una copia
de seguridad independiente de sus proyectos y datos.
