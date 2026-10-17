# GUI de LANWIRE, LANRACK, LANACCESS y LANMON

Desde LANCTL, pulsa la tarjeta de la aplicación. También se abren directamente:

```text
lanwire --gui
lanrack --gui
lanaccess --gui
lanmon --gui
lanctl lanwire --gui
```

Se requiere el extra `gui` en desarrollo y WebView2 en Windows, igual que LANIP.
Se conserva el arranque CLI/TUI predeterminado de cada launcher. Cada aplicación
tiene icono, sesión coordinada y ventana propios; la instancia existente recibe
el foco en una segunda apertura. El lanzamiento transporta una instantánea
versionada de las rutas del proyecto, sin credenciales, para conservar el
contexto aunque otra ventana seleccione un proyecto distinto. No persiste esta
selección sobre la de otra sesión.

## LANWIRE

LANWIRE ofrece dos vistas independientes a pantalla completa: **Lista** y
**Topología**. Las barras superior e inferior permanecen visibles. La lista
permite ordenar, redimensionar y elegir columnas, buscar por nombre, alias,
identificador o IP y combinar filtros de tipo, prefijo, grupos del TUI, rack,
medio, conexión cableada/Wi-Fi y disponibilidad de puertos.

El lienzo de Topología muestra cables reales, sus puertos y suministros externos.
Admite zoom centrado en el cursor, arrastre del fondo y de equipos, minimapa,
encuadre completo, reorganización automática, historial de navegación, menú
contextual y enfoque de un elemento con profundidad configurable. Las posiciones
manuales se conservan localmente por almacén. Los equipos marcados solo Wi-Fi
quedan excluidos por defecto; los mixtos conservan sus conexiones físicas.
Pulsar un puerto en el lienzo selecciona el equipo; conectar cables es una
acción explícita de las pestañas Puertos/Conexiones de su ventana de datos.
Seleccionar un cable permite consultar o editar sus extremos. La topología representa también enlaces
cruzados: no presupone que la red sea un árbol sin bucles.

El doble clic en Lista o Topología abre un detalle con pestañas General,
Ubicación, Puertos, Conexiones, Datos técnicos y JSON copiable. Los campos de
nombre, alias, descripción, grupos, conexión, IP, velocidades, ubicación, medio,
PoE y altura de rack son editables según el tipo. Renombrar un puerto actualiza
sus referencias. «Centrar en Topología» conserva la selección y ofrece limpiar
filtros si impiden mostrarla. Una revisión de contenido impide sobrescribir
cambios de otra ventana; medio, ocupación, unidad y extremos se validan antes
de persistir. Los identificadores y fechas generadas son de consulta.

Configuración agrupa General, Lista y búsqueda, Topología, Puertos y conexiones,
Almacenamiento, Proyecto y Avanzado, con controles tipados, buscador y aviso de
solo lectura. Las preferencias visuales se guardan localmente con versión de
formato; los ajustes compartidos pasan por el catálogo y validación del programa.
Restaurar preferencias visuales no altera rutas ni opciones del proyecto.

«Cambiar proyecto» lista los VLF disponibles y permite abrir otro archivo. Los
cambios pendientes se guardan antes de cambiar; una apertura fallida conserva
el contexto anterior. **El inventario físico sigue siendo compartido**, mediante
`physicalDatabase` (o `--database` al arrancar); no está contenido en el VLF. El
selector cambia el contexto del proyecto y vuelve a enlazar el servicio físico
a la ruta configurada. No se simula una exportación VLF del inventario físico.
Las rutas modificadas en Configuración requieren volver a abrir la interfaz.


## LANRACK

LANRACK gestiona CPD (salas con nombre, descripción y ubicación) que agrupan
armarios del mismo almacén físico. Permite crear y editar CPD, asignar o trasladar
racks y eliminar una sala conservando sus armarios sin asignación o trasladándolos
a otra. Los identificadores internos distinguen salas con el mismo nombre.

Incluye vista de salas, lista filtrable/buscable por CPD o rack y detalle del
armario con unidades numeradas y equipos. Se navega de sala a rack y a los datos
del equipo; el detalle del armario conserva también los ocupantes sin unidad.
«Cambiar CPD» modifica la pertenencia física. La edición de equipos y cables
sigue en LANWIRE, accesible con «Abrir LANWIRE».

La organización se persiste en el propio `physicalDatabase` mediante la extensión
`cpdOrganization` con `schemaVersion: 1`; cada rack referencia su sala mediante
`data.location.cpd`. Las bases anteriores se leen sin CPD y guardan la extensión
al realizar la primera operación, sin reescribir identificadores ni conexiones.
Un esquema desconocido o datos inválidos se rechazan sin sobrescribirlos.
Las operaciones son atómicas bajo el lock común y requieren la revisión actual
del inventario, para no sobrescribir cambios de otra ventana.

### Racks y CPD en Topología LANWIRE

«Interior de racks» agrupa los equipos dentro de contenedores por rack.
«Vista general de racks» contrae cada armario y muestra los cables que salen a
otros racks, equipos externos y suministros. Un rack es un contenedor visual,
nunca un extremo físico nuevo. El doble clic entra en el rack; los controles
permiten volver a la vista general y conservar cámara y posiciones por contexto.
Las conexiones salientes permanecen visibles con sus equipos/racks de destino
como contexto, aunque pertenezcan a otra sala.

Se puede filtrar por CPD, rack o elementos sin asignación, y agrupar/desplegar
los enlaces paralelos. Un grupo de cables permite abrir los registros reales
que lo componen. Los medios se identifican por texto, sin depender solo del color.
Las ventanas refrescan el almacén cada cinco segundos cuando no se edita ni
arrastra; «Actualizar» permite consultar antes los cambios de la otra interfaz.

La distribución usa fuerzas deterministas por componentes y separación de
rectángulos, tanto para equipos como para contenedores conectados. Solo los
componentes sin conexiones se colocan en cuadrícula. No garantiza un óptimo
matemático global. Los puertos se ordenan por medio y número, con filas/columnas
adaptadas a su cantidad; su numeración e identidad no se modifican. Se muestran
libres/ocupados sin scroll interno y las posiciones manuales respetan el rack.
«Reorganizar» recalcula el dibujo sin alterar los datos físicos.

Los cables se anclan a coordenadas de puertos reales recalculadas con cada zoom
o movimiento. Sus etiquetas llevan fondo y se separan de equipos y otras
etiquetas; una guía discontinua identifica el enlace si el texto se desplaza.
Con poco zoom se abrevia a identificador/cantidad; señalar la etiqueta muestra
el nombre, medio y extremos completos. El minimapa y «Ver todo» incluyen los
tamaños variables de las tarjetas y contenedores.

## LANACCESS

Lista metadatos de credenciales con equipos, protocolo y usuario. Permite crear
o actualizar la combinación equipo/protocolo, eliminar y abrir el cliente de
conexión disponible. El almacén y el enlace con el inventario utilizan el mismo
servicio transaccional que CLI/TUI; `AccessManager` conserva su ruta compatible
como adaptador de entrada de secretos de consola.

Los secretos no se devuelven a JavaScript en listas o detalles, ni se colocan en
argumentos de procesos. La edición solicita una contraseña nueva y su
confirmación. DPAPI mantiene su protección de usuario de Windows. Un almacén
portable se desbloquea explícitamente; uno nuevo requiere al menos 12 caracteres
y confirmación. Bloquear o cerrar elimina la contraseña de desbloqueo de la
instancia. Se respetan `--database`, `--store`, `--cipher` y las opciones de scope.
Las conexiones interactivas usan una terminal del sistema para autenticarse.

## LANMON

Lee el inventario, las últimas observaciones, latencia y hasta 60 muestras
reales por equipo, incidencias y eventos del proyecto. La ventana no inicia
sondeos ni un servicio al abrirse. «Iniciar monitor», «Detener» y «Comprobar una
vez» requieren una decisión explícita y llaman a las mismas operaciones que
el CLI, con autoridad observe. Los resultados se escriben en la base del monitor.
No permite detener desde la GUI la sesión de otro proyecto ni iniciar una
segunda sesión si ya existe una activa. Las incidencias del inventario mostrado
se pueden reconocer y cerrar mediante su servicio.

El proceso de monitorización continúa al cerrar la ventana. Sus reglas y
perfiles avanzados permanecen disponibles en configuración y CLI. Las acciones
remotas con mayor autoridad mantienen sus comprobaciones existentes.

## Interacción compartida y comprobación

Cabecera, filtros, barra de acciones y pie permanecen visibles; el contenido
central se desplaza. Cada GUI incluye configuración por categorías, CLI propio,
acceso a LANCTL, errores con su origen y confirmaciones con la temática de la
aplicación. La actualización de datos no reemplaza formularios abiertos.

Pruebas reproducibles:

```text
python -m pytest tests/test_launcher_gui.py -q
python tests/launcher_gui_native_smoke.py lanwire
python tests/launcher_gui_native_smoke.py lanrack
python tests/launcher_gui_native_smoke.py lanaccess
python tests/launcher_gui_native_smoke.py lanmon
python tests/launcher_suite_native_smoke.py
```

Los smokes nativos Windows utilizan directorios temporales y cierran solamente
sus propias ventanas y procesos. La revisión local no certifica otras plataformas.

Las rutas de almacén están vinculadas a la instancia abierta: después de
cambiarlas en configuración, cierra y vuelve a abrir el launcher. Los cambios
de parámetros del monitor se aplican al reiniciar su sesión de ejecución.
