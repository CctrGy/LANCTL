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
el foco en una segunda apertura. La selección de proyecto es compartida por
LANCTL y sus launchers: las ventanas abiertas reconcilian la configuración y
renuevan sus datos, rutas y nombre de proyecto. El contexto versionado del
lanzamiento sigue siendo compatible, pero no fija una selección independiente
durante toda la vida de la ventana.

Cada operación trabaja con una instantánea consistente. Un escaneo ya iniciado
termina sobre su inventario original; un servicio de monitorización conserva el
proyecto de su trabajo hasta que se detenga. Los formularios antiguos no se
aplican al proyecto nuevo: se conserva su contenido y se pide cerrar y actualizar.
El sobre RPC aditivo `project_call` valida `projectContext` para las acciones
publicadas en `projectActions`; los métodos RPC anteriores conservan sus firmas.

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

La selección de proyecto se realiza desde LANCTL, según P88; LANWIRE conserva
el acceso a esa ventana y muestra el contexto activo. Una apertura fallida
conserva el contexto anterior. Cada proyecto contiene su inventario físico,
con cambios pendientes y guardado/verificación en la entrada opcional y
versionada `devices/physical.json` del VLF. Guardar y reabrir en otra instalación
recupera racks, equipos, cables, puertos y CPD. Un VLF anterior sin esa entrada
abre un inventario físico vacío. La base histórica se conserva aparte y puede
importarse explícitamente en un proyecto vacío mediante
`project import-physical ARCHIVO`; después se guarda con `project save`.
Las rutas configuradas se vuelven a enlazar al atender la siguiente operación.
Los overrides explícitos de arranque como `--database` siguen siendo respetados.

LANWIRE ofrece Nuevo elemento, Nuevo cable, Nuevo rack y Nuevo CPD. Los cables
pueden crearse con extremos compatibles en una sola operación; un puerto
inexistente, incompatible u ocupado rechaza el alta sin dejar un cable parcial.
También permite editar CPD y cambiar la pertenencia de un rack.
El doble clic abre los datos del elemento; el menú contextual de un rack
conserva «Ver interior del rack». El botón de nombres de cables solo oculta sus
etiquetas, manteniendo trazado, posiciones y nombres de equipos. Las tomas
genéricas de hasta dos puertos ocupan aproximadamente el 27 % del área anterior.


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

### Frentes visuales de equipos (skins)

La elevación del armario muestra frentes SVG genéricos sobre las unidades
ocupadas, con orejas de montaje o bandeja para equipos de sobremesa. Incluye
30 plantillas: automático, switches de 12/24/48 RJ45 y combinaciones con SFP
(24+2, 24+4, 48+2, 50+2, 48+4, 48+6 y 48+8), switches de sobremesa de
5/8/12/16/24 puertos, paneles de 12/24/48, servidores de 1/2/4 U, SAI de
2/3/4 U, router/cortafuegos, bandejas y paneles ciegos. Son representaciones
genéricas y no un catálogo de modelos comerciales.

Pulsa un equipo y elige «Personalizar frente» para seleccionar una plantilla,
verla previamente o ajustar el tipo, número de RJ45/SFP, montaje y altura.
La altura admite de 1 a 52 U, siempre que el equipo quepa en el rack sin
solaparse; un equipo de más de 8 U conserva su altura al editar el frente.
El modo automático deduce el frontal de los puertos y tipo del inventario.
Los puertos del frente son decorativos: no reciben clics, foco ni acciones de
conexión, ni muestran respuestas al pasar el ratón. La unidad completa conserva
el acceso a sus datos.
El número representado no añade ni renumera puertos; los conectores adicionales
se identifican como representación sin registro. Solo se resaltan conexiones
realmente registradas. El SAI no presenta porcentajes o estados de batería
inventados. Las unidades se numeran de abajo hacia arriba; una altura de 2 U
partiendo de U5 ocupa U5–U6, con validación de espacio y límite del armario.

La apariencia se guarda en `data.rackAppearance` con `schemaVersion: 1` en la
base compartida, y conserva equipos, CPD, ubicación, puertos y cables. Las
revisiones impiden sobrescribir cambios de otra ventana. El traslado desde la
GUI de LANWIRE y la reducción de altura del rack respetan el espacio ocupado.
Los equipos anteriores conservan 1 U y un frente automático hasta configurarlos.
La cabecera del rack reúne «Volver a la sala» y «Ver unidades simples» junto
al nombre y la ocupación. La descripción completa sigue disponible en la ficha.
Se conservan «Actualizar», «Nuevo CPD», «Nuevo rack» y «Nuevo elemento».
La navegación entre aplicaciones parte del acceso LANCTL del pie.

El tamaño visual se ajusta automáticamente al ancho y alto disponibles, sin
deslizador y sin modificar la altura U ni las dimensiones físicas. En racks
altos o ventanas pequeñas se conserva un mínimo legible y se usa desplazamiento
vertical para acceder a todas las unidades. Redimensionar no cierra la ficha ni
pierde cambios pendientes. La preferencia local de vista simple o frentes
mantiene su esquema 1; el antiguo tamaño manual deja de aplicarse.

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
argumentos de procesos. La ficha permite editar el usuario sin reintroducir la
contraseña guardada. «Cambiar contraseña» habilita una contraseña nueva y su
confirmación; los campos empiezan vacíos. El equipo, protocolo e identificador
de una credencial existente son de lectura. Una revisión opaca del archivo
cifrado impide sobrescribir cambios de otra sesión. DPAPI mantiene su protección
de usuario de Windows. Un almacén
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

La ficha de un equipo permite editar nombre, alias, descripción e IP mediante
el mismo servicio de inventario que LANIP. La pestaña «Grupos» añade o retira
pertenencias a grupos existentes; respeta los grupos protegidos. Estas acciones
se aplican al pulsar «Añadir» o «Retirar» y requieren guardar o descartar antes
los cambios pendientes en «Datos». Los identificadores, las observaciones,
muestras, métricas y eventos son de lectura. La revisión incluye datos y
pertenencias y rechaza formularios obsoletos antes de escribir.

El proceso de monitorización continúa al cerrar la ventana. Sus reglas y
perfiles avanzados permanecen disponibles en configuración y CLI. Las acciones
remotas con mayor autoridad mantienen sus comprobaciones existentes.

## Interacción compartida y comprobación

Cabecera, filtros, barra de acciones y pie permanecen visibles; el contenido
central se desplaza. Cada GUI incluye configuración por categorías, CLI propio,
acceso a LANCTL, errores con su origen y confirmaciones con la temática de la
aplicación. La actualización de datos no reemplaza formularios abiertos.
Las barras inferiores de LANCTL, LANIP, LANWIRE, LANRACK, LANACCESS y LANMON
no muestran un reloj de hora actual. Se conservan proyecto, versión y navegación,
el refresco de datos y las fechas/horas de actividad, incidencias, eventos y
registros. Los prototipos siguen el mismo criterio para sus pies.
LANMON y LANACCESS conservan la selección y los filtros después de editar;
si el registro deja de coincidir con el filtro, permanece visible con un aviso
hasta cambiar filtro, selección o proyecto. Cancelar los datos de una ficha no
los guarda. Las respuestas tardías de fichas cerradas no sustituyen otros
diálogos. Las nuevas operaciones nativas `monitor_device`, `monitor_update`,
`monitor_group` y `access_update` respetan la guarda de proyecto y el launcher
correspondiente; no amplían la lista de operaciones ni los permisos remotos.

Pruebas reproducibles:

```text
python -m pytest tests/test_launcher_gui.py -q
python -m pytest tests/test_view_editing.py tests/test_view_editing_gui.py -q
python -m pytest tests/test_launcher_footers.py -q
python tests/launcher_gui_native_smoke.py lanwire
python tests/launcher_gui_native_smoke.py lanrack
python tests/launcher_gui_native_smoke.py lanaccess
python tests/launcher_gui_native_smoke.py lanmon
python tests/launcher_suite_native_smoke.py
```

Los smokes nativos Windows utilizan directorios temporales y cierran solamente
sus propias ventanas y procesos. La revisión local no certifica otras plataformas.
Las regresiones de navegador requieren `LANCTL_GUI_BROWSER_TESTS=1` y el
runtime de Playwright con Edge, igual que las demás pruebas GUI del proyecto.

Las rutas de almacén están vinculadas a la instancia abierta: después de
cambiarlas en configuración, cierra y vuelve a abrir el launcher. Los cambios
de parámetros del monitor se aplican al reiniciar su sesión de ejecución.
# Controles compartidos de escritorio — 17/10/2026

Las seis ventanas nativas comparten un editor de apariencia con cinco paletas
(Grafito, Azul noche, Bosque, Violeta y Claro), densidad, tamaño de texto y
reducción de animaciones. La vista previa se cancela sin guardar; Aplicar usa
las preferencias validadas del Core y las demás ventanas las reciben en vivo.
Los temas de plugins amplían únicamente sus tokens declarados, sin reemplazar
la preferencia base. Al retirarlos se limpian sus estilos de componente.

El pie incluye `Report a bug`. Los errores conservan código, origen e identidad
y se agrupan para evitar ventanas repetidas. LANMON permite elegir sesión y
evidencias, editar descripción/pasos/resultado esperado, anonimizar y revisar
el borrador antes de exportarlo o abrir el formulario oficial. Abrir GitHub no
publica una incidencia. Las credenciales se excluyen incluso si se desactiva
la anonimización de datos identificativos.

LANCTL conserva su buffer local de actividad y envía los mensajes al transporte
compartido antes de abrir el visor de LANMON. Allí se filtra por proyecto,
sesión, nivel y texto. Los registros operativos tienen una vista independiente,
historial acotado y pausa. LANIP ofrece además Registros para abrir la TUI en
otra terminal. Cerrar el visor no detiene el monitor.

La barra de LANCTL ya no muestra reloj. Web, GitHub y Referencia usan el servicio
de enlaces oficiales compartido con CLI/TUI. Configuración ofrece la búsqueda
manual de actualizaciones; la consulta automática corre en segundo plano y el
Core la limita a una diaria. El usuario puede recordar después o abrir la
Release; no se descargan ni ejecutan instaladores automáticamente.

LANRACK crea armarios y edita altura (4–52 U) y ancho de montaje
(10/19/21/23 pulgadas). LANWIRE muestra esas dimensiones desde el mismo registro
y remite su edición a LANRACK. Los datos heredados incompletos se identifican
para revisión; una altura inválida no se convierte en una elevación inventada.
Los puertos de las skins siguen siendo exclusivamente decorativos.

La solicitud de primer escaneo del instalador abre una confirmación editable
en LANIP con las interfaces IPv4 disponibles y su máscara real. Se confirma
adaptador, CIDR y perfil antes de sondear. El modo de origen seleccionado usa
ICMP/ARP y omite DNS y descubridores externos con un aviso; no atribuye ese
enlace a transportes todavía no adaptados. Sin interfaz válida no inicia ni
descarta la solicitud. Un escaneo fallido conserva la petición para reintentar.
El botón Red de escaneo permite cambiar la selección o recuperar las rutas
habituales del sistema. La selección se conserva solo en la ventana abierta.

Estos adaptadores son exclusivos del escritorio local. El frontend remoto
conserva su superficie restringida y no obtiene métodos nativos adicionales.


## Edición física desde LANRACK y LANWIRE

LANRACK permite crear elementos (incluidas bandejas), editar sus datos, puertos
y conexiones y abrir la acción **Mover elemento** desde el equipo seleccionado.
La acción muestra su posición actual y destinos disponibles para la altura
indicada. La transacción vuelve a comprobar ocupación y revisión al guardar.
La pestaña **Ubicación** permite escoger interior, entorno, independiente o
alojado en bandeja. En una bandeja montada también aparece **Alojar dispositivo**;
para retirarlo se edita su ubicación y se elige un destino explícito.

El rack conserva su altura de 4–52 U y ancho de 10/19/21/23 pulgadas. Un equipo
puede ocupar de 1 a 52 U, limitado por el armario y sus vecinos. Su única altura
persistida sigue siendo `rackAppearance.units`; cambiar el frente usa la misma
validación. LANWIRE puede editar las dimensiones en la ficha del rack.

El inventario distingue montaje directo, entorno y elementos independientes.
La relación de pertenencia no modifica el cableado: las tomas mantienen el
puerto concreto de su panel y un equipo independiente puede enlazar con un rack.
Los dispositivos alojados conservan registros, puertos e IDs propios, y solo la
bandeja reserva U. Su rack y unidad efectivos se calculan a partir de ella.

Las ubicaciones nuevas llevan `location.schemaVersion: 1`. Una ubicación antigua
con rack y posición válida se interpreta como interior sin reescribir el archivo;
las asociaciones ambiguas se muestran para revisión. La edición explícita migra
la ubicación. Las bandejas antiguas dibujadas en `layout` pueden convertirse desde
**Convertir bandeja heredada**: se crea un ID libre y se retira solo ese dibujo,
en una transacción. No se asignan dispositivos automáticamente. Los otros muebles
heredados conservan su espacio reservado. La TUI da prioridad a la ubicación real
de un equipo sobre un dibujo anterior que apuntase a su ID.

CLI y TUI de LANRACK comparten estas reglas:

```text
LANRACK elements
LANRACK add-element --kind tray --prefix TR --name Bandeja
LANRACK element TR-00 --placement inside --rack RK-00 --unit 3 --height-u 2
LANRACK element RT-01 --placement hosted --tray TR-00
LANRACK element RT-01 --placement independent
```

Los nombres de proyecto de los cinco launchers son informativos y aparecen en
el pie. La selección gráfica se realiza desde LANCTL; el botón LANCTL del pie
usa la coordinación de ventanas existente. Las APIs y comandos históricos de
proyecto siguen disponibles. Un formulario abierto conserva su contenido y
rechaza la escritura si cambió el proyecto o el inventario mientras estaba abierto.
