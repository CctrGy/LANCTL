# Prototipos de los launchers pendientes

Abrir `gui/launcher-prototypes.html` en el navegador. No requiere servidor ni
dependencias externas. Las cuatro vistas se seleccionan en la barra superior;
también admiten los fragmentos `#wire`, `#rack`, `#access` y `#mon`.

- LANWIRE: topología, lista de enlaces, extremos y medio de conexión.
- LANRACK: selector de racks, vista frontal numerada y selección de ocupantes.
- LANACCESS: perfiles agrupados, destinos, protocolos y detalle sin secretos.
- LANMON: indicadores, lista de equipos, gráfico ilustrativo y eventos.

Mantienen los colores y los iconos SVG del centro LANCTL, con cabecera,
controles y barra inferior fuera del área desplazable. La búsqueda y el filtro
actúan sobre los datos de ejemplo. Se pueden seleccionar elementos, abrir sus
detalles con doble clic y modificar datos temporalmente. Al recargar se restaura
la demostración. «Nuevo» crea un registro visual a partir de un ejemplo.

Son propuestas de interfaz, no nuevas implementaciones de los servicios.
Configuración muestra el formulario propuesto; LANCTL y CLI explican su destino
previsto. No ejecutan procesos, sondeos ni conexiones, ni leen/escriben VLF o
credenciales. LANRACK propone edición futura, aunque su servicio actual es de
solo lectura. Los accesos de producción de LANCTL mantienen su comportamiento.
