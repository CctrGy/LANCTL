# Centro gráfico de LANCTL

Inicia `lanctl --gui` (desde fuentes: `python -m lanctl --gui`). La consola
habitual `lanctl --cli` y el TUI siguen disponibles. Desde fuentes se necesita
el extra `gui`: `pip install -e ".[gui]"`.

El centro utiliza la distribución compacta Grafito y lima: LANIP/LANWIRE,
LANRACK/LANACCESS y LANMON a todo el ancho. Los accesos abren exclusivamente
interfaces gráficas. Actualmente LANIP dispone de GUI; los otros cuatro
launchers muestran que su GUI está pendiente, sin abrir una CLI/TUI en su lugar.

## Proyectos

«Nuevo proyecto» solicita una carpeta y un nombre. «Crear archivo VLF» escribe
un VLF real y vacío mediante el servicio existente, sin copiar dispositivos ni
credenciales del proyecto anterior. No sobrescribe archivos existentes.
La interfaz confirma el resultado y su ruta cuando la creación y activación han
terminado. Los cambios pendientes deben guardarse antes de cambiar de proyecto.
También permite abrir VLF existentes y guardar el proyecto activo. La creación
y «Editar» incluyen nombre, descripción, autor, LAN, ubicación, empresa y
responsable. Los cambios de metadatos se guardan conjuntamente, conservando UUID,
inventario y otros contenidos. Si otra ventana modificó esos datos, se pide
recargar antes de guardar. Cancelar o cerrar un formulario modificado pide
confirmación. La lista se actualiza al completar la operación.

Las operaciones de proyectos y preferencias reutilizan temporalmente el
adaptador compatible `DesktopApi` de LANIP. `SuiteApi` expone exclusivamente los
métodos de administración necesarios, sin publicar los RPC de inventario.

## Plugins

Cada plugin instalado ofrece activación y desactivación. «Configurar» aparece
únicamente si ofrece campos configurables, aunque todavía use valores
predeterminados y no exista un archivo de ajustes.
Los campos se leen del manifiesto actual al consultar la configuración, también
si el paquete instalado fue actualizado por otro proceso. Un manifiesto inválido
se muestra como error de configuración sin abrir un formulario vacío.
La activación muestra los permisos solicitados y requiere seleccionarlos;
no se concede confianza a código trusted sin un editor autorizado.
El diálogo de configuración muestra las opciones declaradas por el plugin.
Los plugins sin opciones propias no muestran un botón que abra un panel vacío.
Wake-on-LAN ofrece puerto UDP, repeticiones y espera de arranque, conectados
a los valores compartidos que ya utiliza el CLI de WOL.

Un paquete trusted sin firma válida muestra el requisito de obtener un LCP
firmado antes de intentar la activación. Para un paquete firmado cuyo editor
todavía no es confiable, el diálogo muestra su huella y permite seleccionar el
LCP original para autorizar al editor. Se verifica que ID, checksum y firma coincidan
con la versión instalada. Después se conceden permisos y ejecución trusted.
Cancelar o seleccionar otro paquete no concede confianza. El paquete WOL
incluido actualmente está sin firmar; este flujo no elimina ese requisito.

Contrato opcional y aditivo en `plugin.info`:

```json
{
  "settingsSchema": {
    "schemaVersion": 1,
    "fields": [
      {"name": "retries", "label": "Reintentos", "type": "integer", "minimum": 1, "maximum": 10, "default": 3},
      {"name": "enabled", "label": "Habilitar análisis", "type": "boolean", "default": true},
      {"name": "mode", "label": "Modo", "type": "select", "choices": ["fast", "normal"], "default": "normal"}
    ]
  }
}
```

Tipos admitidos: `text`, `integer`, `boolean`, `select`. Cada campo requiere un
valor predeterminado válido. No se admiten contraseñas ni secretos. Los valores
se guardan fuera del paquete, en `plugins/.settings/ID.json`, con `schemaVersion`
y escritura transaccional. Un archivo corrupto o de versión desconocida produce
un error; no se sustituye silenciosamente por valores vacíos.
Cada plugin puede consultar sus propios valores mediante `api.settings`.
Los procesos aislados reciben una instantánea al iniciarse; tras cambiar opciones
hay que desactivar y activar el plugin para que vuelva a leerlas.

## Terminales

«Terminal», junto a Configuración, ejecuta un CLI general real de LANCTL en un
proceso separado y muestra su salida dentro del programa. No interpreta HTML ni
ejecuta comandos de shell. La sesión continúa al cambiar de sección y se cierra
con el centro gráfico. Para SSH, contraseñas, TUI y otras sesiones que necesitan
una terminal nativa se utiliza el acceso inferior.

«CLI», en la barra inferior, abre `lanctl --cli` en la terminal del sistema:
Windows utiliza el host de terminal predeterminado; Linux utiliza
`x-terminal-emulator` (o `xterm` como alternativa). Si no hay terminal instalada,
se informa del error. Esta consola independiente permanece abierta al cerrar
la GUI. Ninguno de los dos accesos inicia un escaneo por sí mismo.

La barra inferior muestra versión, proyecto y número de plugins activos.
«Sistema» muestra SO, arquitectura e información de la interfaz local.
«Actividad» permite consultar los mensajes de las últimas operaciones de la sesión.

En Proyectos y Plugins, solo se desplaza la lista: cabecera, acciones,
buscador y barra inferior permanecen visibles. La búsqueda por nombre es local,
no distingue mayúsculas y muestra el número de resultados. Cada plugin muestra
versión, estado y autor; su información técnica desplegable incluye ID, runtime,
compatibilidad LANCTL, capacidades, permisos solicitados/concedidos y firma.

## Inicio y ventanas

En Configuración general, `startupInterface` elige `cli`, `tui` o `gui` cuando
LANCTL arranca sin argumentos, tanto desde terminal como desde su ejecutable.
El valor predeterminado sigue siendo `cli`; un argumento explícito tiene prioridad.
`closeGuiOnLaunch` permite cerrar LANCTL después de confirmar que LANIP está
disponible. Si la apertura falla, LANCTL conserva su ventana y muestra el error.

Solo hay una GUI por launcher, usuario y raíz de datos. Una nueva solicitud
restaura y enfoca la existente. LANCTL y LANIP sí pueden coexistir; cerrar una
no cierra la otra. La página inicial y Actividad reflejan apertura y cierre.
Los cambios compartidos se recargan cuando no hay un formulario abierto; no se
reemplaza una edición en curso. Cada sesión conserva su proyecto.
