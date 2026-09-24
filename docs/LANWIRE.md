# Integración LANWIRE

LANWIRE es el gestor de infraestructura física complementario de LANCTL. En
Windows se distribuye como `lanwire.exe` en el mismo directorio que
`LANCTL.exe`. La GUI heredada no forma parte de la distribución.

## Ejecución

```powershell
lanctl lanwire
lanctl lanwire list
lanctl wire list
lanwire idf list
lanwire idf list FB
```

La creación tiene dos pasos diferenciados, tanto en la CLI como en el prompt
del TUI:

```text
idf new BR -type wire.fiber
idf add BR-00 -name fiber -description "Fibra de compañía"

idf new RT -type router.otg
idf add RT-00 -name OTG
idf list
idf list BR
idf types
idf show BR
idf show BR-00
idf edit BR-00 alias=Entrada
idf edit BR -type wire.copper
idf delete BR-00
```

`idf new` registra únicamente un prefijo de 2–5 letras y le asigna un perfil;
no crea ningún elemento. `idf add` exige un IDF completo con número de 2–5
dígitos y crea el elemento usando el perfil guardado. Acepta `-name`, `-alias`
y `-description`; `idf list` muestra los prefijos definidos y los que ya
aparecen en IDF existentes, con su perfil y cantidad de IDF. `idf list BR`
lista los elementos de ese prefijo, igual que `list BR`.
`idf types` enumera perfiles disponibles. `idf show` consulta tanto el perfil
de un prefijo como un IDF concreto; `idf edit` modifica el perfil para futuros
IDF o los datos de un registro existente. `idf delete` solo elimina un IDF;
para borrar una definición de prefijo se usa `prefix delete BR`.
Por compatibilidad, también se acepta `-descriptionn`. Los perfiles
incluyen `wire.copper` (también
`wire.coper`), `wire.fiber`, `wire.dac`, `router.otg`, `router.gateway` y
`switch.5Ports`, `switch.12Ports`, `switch.24Ports`, `switch.48Ports`. También
hay perfiles básicos `pc.1Port`, `pc.2Ports` y `server.2Ports`. `router.otg`
genera exactamente dos puertos, en orden: `FIBER` (1) y `WLAN` (2).

Sin argumentos se abre una consola independiente. Con argumentos, LANCTL espera
el resultado y devuelve el mismo código de salida. `--new-window` fuerza una
consola separada.

En desarrollo, el lanzador utiliza `lanwire.py` en la misma raíz que
`lanctl.py`. Las instalaciones finales buscan `lanwire.exe` junto a
`sys.executable`. Ambos son entradas independientes de un único proyecto.

## Edición en la TUI

En la lista, `Tab` recorre `ELEMENTS → WIRE → ALL` y `Enter` abre la ficha. Dentro
de un elemento, `↑/↓` selecciona el puerto; `Tab` o `Enter` activa el menú
lateral. `F3` sigue la conexión: desde un puerto abre su cable y selecciona el
extremo opuesto; desde ese cable abre el equipo y puerto de destino. En un
cable de un solo extremo, sigue el extremo conectado. `Backspace` vuelve al
paso anterior sin perder la selección. Las opciones principales del menú son
**Datos generales del elemento** (incluye
la cantidad y plantilla de puertos), **Datos del puerto** (excepciones de ese
puerto), **Conectar al puerto** (selector de cables compatibles con un extremo
libre) y **Eliminar elemento** (con confirmación). Si ya hay un cable, el menú
también permite abrirlo, desconectarlo o
moverlo. `Esc` vuelve al nivel anterior. Los cambios se guardan y la ficha se
actualiza al confirmar, sin cerrarla.

Los IDF nuevos con prefijo `FB` se crean como cables de fibra; `WL` y `WE`
se crean como cables de cobre. Al abrir una base existente, los registros de
esos prefijos que todavía no tenían tipo se clasifican igual sin cambiar los
que tengan un tipo diferente asignado expresamente.

La plantilla `portNaming` admite una serie simple (`LAN{n}`), varias series
numeradas de forma independiente (`X{n}:24,XG{a}:4`) y nombres fijos
(`LAN{n}:4,FIBER`). El número después de `:` indica cuántos puertos genera esa
serie; todas empiezan en 1. `FIBER` crea un puerto de fibra genérica y conserva
ese nombre reservado. Al editar
`portCount` en una plantilla mixta, se ajustan primero las series del final;
solo se pueden retirar puertos sin cable. En **Datos del puerto** se pueden
editar el nombre y la posición (comenzando en 1). Renombrar un puerto conectado
actualiza también la referencia en el cable.

## Contrato de datos

Antes de iniciar LANWIRE, LANCTL exporta su raíz resuelta en
`LANCTL_DATA_DIR`. También se conserva `LANCTL_DATA_SCOPE`. El marcador portable
debe contener exactamente `LANCTL-PORTABLE-V1`.

```text
<raíz compartida>/
├── database/devices.json       # inventario lógico LANCTL
├── monitoring/monitor.db       # monitorización LANCTL
└── physical/idf.db             # infraestructura física LANWIRE
```

La clave `physicalDatabase` de la configuración apunta por defecto a
`data/lc/physical/idf.db`. LANCTL solo conserva y muestra esta ruta; no abre la
base con `DeviceDatabase` ni mezcla sus tablas con otros almacenes.

## Compilación

`LANCTL.spec` analiza las dos entradas raíz, `lanctl.py` y `lanwire.py`, y
produce ambos ejecutables en una sola ejecución de PyInstaller. El script
`scripts/build-windows.ps1` exige los dos resultados y los incorpora al
instalador y al ZIP portable. Inno Setup lo
instala como parte del componente principal y lo elimina junto con los binarios,
pero conserva `%PROGRAMDATA%\LANCTL\physical` durante la desinstalación.
