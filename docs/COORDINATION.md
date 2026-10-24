# Coordinación local entre launchers

LANCTL, LANIP, LANWIRE, LANRACK, LANACCESS y LANMON registran sus ejecuciones
en `runtime/coordinator.db`, dentro de la raíz de datos resuelta por el programa.
Es un almacén SQLite transaccional con `user_version=1`, no una base de inventario
ni un almacén de credenciales. No se versiona en Git.

## Arquitectura y alcance

El coordinador es **embebido**: los procesos comparten el registro SQLite y cada
sesión mantiene un hilo de recepción/heartbeat. No requiere un nuevo daemon ni
un puerto TCP, y no añade un launcher LANBACK. Los servicios SSH/HTTPS y de
monitorización existentes conservan su ciclo de vida independiente de las
ventanas. Esta integración no instala ni activa servicios automáticamente.

Una sesión contiene UUID, PID, usuario del SO, launcher, interfaz, proyecto,
sesión padre y heartbeat. Cada invocación anidada de otro launcher tiene identidad
propia; los comandos de una consola reutilizan su sesión. Ayuda, versión y el
modo efímero no crean sesiones. Las tareas tienen origen de cuatro segmentos,
UUID de correlación, inicio, final y estado. Los logs operativos incluyen la
sesión, launcher, interfaz y tarea cuando existe ese contexto.

El estado no depende de un único `root-interface.json`. El adaptador antiguo
sigue disponible para consumidores anteriores, pero las interfaces coordinadas
se registran individualmente. Si hay varias ventanas, las órdenes requieren
un ID de sesión; nunca se escoge arbitrariamente la última ventana abierta.

Las GUI de LANCTL y LANIP añaden exclusión por launcher, usuario y raíz de datos
mediante un bloqueo del SO mantenido durante la vida del proceso. Una segunda
apertura espera a que la interfaz esté disponible y le envía `view gui`; restaura
la ventana y solicita el primer plano. Al morir el proceso se libera el bloqueo.
Un timeout informa del fallo sin crear una ventana duplicada. Launchers distintos
conservan bloqueos independientes. Las órdenes explícitas de backend mantienen
su requisito de destinatario; la apertura GUI resuelve su única instancia.

## Uso

```text
lanctl backend status
lanctl backend sessions
lanctl backend tasks
lanctl backend events --after 0 --limit 100
lanmon backend events --follow
lanctl backend refresh --session ID
```

Dentro de LANMON CLI/TUI también se admite `backend sessions`, `backend tasks`
y `backend events --follow`. Ctrl+C termina el seguimiento sin cerrar la consola
padre. El seguimiento de texto sigue disponible mediante `lanmon logs --window`.
La cola confirma recepción con `accepted`, no finalización del repintado.

El control remoto autorizado conserva `root status` y añade destinatarios:

```text
root refresh --session ID
root forced-view settings --session ID
```

## Proyectos, escrituras y refresco

- La configuración compartida es la autoridad sobre el proyecto seleccionado.
  Las sesiones interactivas la reconcilian al leer y durante el heartbeat, aun
  si se perdió un evento o el escritor no tenía sesión. Las ventanas abiertas
  actualizan contexto, datos y nombre de proyecto; no conservan una selección
  independiente indefinidamente.
- Las opciones generales continúan compartidas. Guardar opciones desde una
  sesión antigua no restaura su proyecto sobre el último proyecto seleccionado.
- Cada operación GUI y comando de inventario conserva una instantánea durante
  su ejecución, para que un cambio concurrente no redirija sus escrituras.
  Los trabajos backend ya iniciados conservan el proyecto original hasta
  terminar; el cambio de ventana no inicia ni redirige sondas de monitorización.
  Los temporizadores de guardado siguen a su interfaz propietaria.
- Dos sesiones sobre el mismo proyecto ven el mismo workspace. Los locks del SO,
  escrituras atómicas y journal devices/groups siguen protegiendo los datos;
  el registro de eventos no los sustituye.
- `save_devices` rechaza una instantánea previamente leída si el archivo cambió.
  Las operaciones de edición releen dentro de sus transacciones existentes.
- Una recarga destructiva no descarta cambios pendientes cuando otra sesión
  mantiene abierto ese proyecto. Tampoco se materializa un archivo que cambió
  durante su lectura.
- LANIP GUI/TUI y LANWIRE TUI reciben notificaciones. LANIP difiere la recarga
  durante escaneos, formularios y ediciones; LANWIRE mientras edita un detalle.
  No se inicia un escaneo al recibir una notificación.
- Las GUI nativas envían la identidad del proyecto y de sus almacenes con las
  acciones de edición (`project_call`, sobre aditivo v1). Un formulario antiguo
  se rechaza sin aplicar cambios; actualizar una vista no autoriza una edición
  preparada en otro proyecto. LANACCESS vuelve a bloquear el almacén al renovar
  su servicio. Los métodos RPC existentes conservan sus firmas.
- Las consolas de comandos leen datos al ejecutar sus consultas; no se imprime
  salida asíncrona sobre el texto que el usuario está escribiendo.

## Eventos y plugins

Los contratos públicos existentes no cambian. El bus local sigue ejecutando los
hooks de plugins, especialmente los cancelables, una sola vez en su proceso.
Se publica un sobre de observación con ID original, versión, sesión, proyecto,
correlación, fecha y cursor incremental. **No se replica el payload del plugin**
ni se ejecutan hooks remotos como si fueran locales.

Observadores pueden leer `Coordinator.events(after, limit)` o suscribirse a
`current_session().subscribers` con un callback de metadatos. Los callbacks se
ejecutan en el hilo de coordinación y deben encolar trabajo en su interfaz;
no deben modificar widgets ni bloquear. Retirar el callback cancela la escucha.

Nuevos IDs de observación, contrato v1:

```text
LANCTL.Core.Session.Started
LANCTL.Core.Session.Stopped
LANCTL.Core.Session.Project
LANCTL.Core.Task.Started
LANCTL.Core.Task.Finished
LANCTL.Core.Storage.Changed
LANCTL.Core.Config.Changed
```

Orígenes de tareas: `LANCTL.Core.Command.Execute`,
`LANCTL.Core.Storage.Transaction`, `LANCTL.GUI.Desktop.Operation`.

## Seguridad y recuperación

Solo se transportan metadatos permitidos; no contraseñas, comandos arbitrarios,
argumentos de comandos ni contenidos de bases. Las órdenes admitidas son
`refresh` y `view`. Las sesiones ordinarias se filtran por usuario del SO; el
control remoto administrativo puede dirigirse a otros usuarios únicamente con
privilegios del SO, además de la autorización SSH/HTTPS existente.

La frontera de seguridad local sigue siendo la ACL/permisos de la raíz de datos.
El usuario almacenado en SQLite no sustituye esa protección. No se debe situar
el archivo del coordinador en una carpeta modificable por usuarios no confiables
ni en una unidad de red compartida entre máquinas. No es un coordinador distribuido.

Heartbeats cada segundo; una sesión deja de estar disponible tras 15 segundos.
Las tareas huérfanas pasan a `interrupted` durante el mantenimiento. Una sesión
que se reanuda tras una pausa recupera su heartbeat. Las órdenes caducan a los
30 segundos y se reclaman una sola vez; una orden entregada antes de un fallo no
se reproduce automáticamente. El historial de eventos retiene unos 10.000
registros y tareas/órdenes terminadas un día; no reemplaza el log de auditoría.
Una discontinuidad de eventos provoca reconciliación del estado desde disco.

Una versión de esquema desconocida o corrupción produce un error; no se borra
el registro para simular una base vacía. El fallo de transporte se registra con
origen propio. Esta entrega se prueba en Windows; Linux necesita validación
equivalente antes de publicar sus instaladores.
