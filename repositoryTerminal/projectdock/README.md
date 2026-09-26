# Gestión del repositorio con ProjectDock

Integración de desarrollo en transición, compatible con LANCTL 0.3.2-beta.1.
No forma parte de los seis ejecutables distribuidos. Los proyectos de código
de ProjectDock y los proyectos de red VLF son conceptos independientes.

## Preparar sin ejecutar

Desde la raíz del repositorio:

~~~powershell
python tools/setup_projectdock.py
python tools/setup_projectdock.py --apply --python "RUTA/AL/python.exe"
~~~

El primer comando solo muestra las recetas propuestas. El segundo crea
.project/ si no existe; rechaza una configuración existente, sin sobrescribir
recetas. No instala dependencias, no registra un catálogo personal, no autoriza
comandos y no genera run.exe. El intérprete se elige explícitamente. Los datos
de desarrollo quedan en .project/lanctl-data, separados de Home y producción.

Requiere el motor ProjectDock de desarrollo con soporte io: inherit y
resources (commit 66502c9 o descendiente). El instalador público 0.1.1 no
incluye todavía esa compatibilidad. No reemplaces el runtime por el de ese
instalador al probar la TUI.

Después de revisar la configuración, desde un motor compatible puede generarse
el lanzador con "projectdock launcher RUTA" y autorizarse explícitamente con
"projectdock trust RUTA". No se han hecho estos pasos sobre LANCTL durante esta
migración: run.cmd sigue siendo el acceso operativo. run.exe tiene precedencia
en CMD cuando se genere; PowerShell requiere .\run.exe. Para pasar argumentos
al programa se usa .\run.exe RECETA -- ARGUMENTOS.

## Mapa de equivalencia y estado

| Acceso anterior | Receta o acceso ProjectDock | Estado |
| --- | --- | --- |
| run.cmd ARGUMENTOS | start -- ARGUMENTOS | Mismo script; falta validar TUI real |
| run.cmd --cli / --tui | cli / lanctl-tui | Consola heredada; fallback conservado |
| project run APP ARGUMENTOS | lanip, lanwire, lanrack, lanaccess, lanmon | Argumentos individuales tras -- |
| build.cmd | build-legacy | Mismo módulo PyInstaller y spec; no ejecutado |
| helper.cmd | help-full | Mismo fullHelp.py; Python explícito, sin búsqueda automática |
| install.cmd build | repository-build | Conserva detección de versión y AllowDirty del script original |
| install.cmd | repository-install | Conserva asistente y elevación; no ejecutado |
| install.cmd remote | repository-remote | Conserva instalador público; no ejecutado |
| install.cmd help | repository-help | Ayuda del orquestador original |
| terminal-profile.cmd | terminal-profile | Conserva PS1 y protección de perfiles existentes |
| sign-terminal-plugin.py | terminal-sign | Conserva firma especializada; no ejecutado ni accedido a claves |
| project tree | tree | Archivos Git; no reproduce dibujo del árbol |
| project version | version | Revisión y rama Git; no reproduce versión LANCTL |
| project environment | python-info | Solo intérprete; inventario completo pendiente |
| project tools | GUI de ProjectDock / conectores futuros | Monitor privado sin migrar |

Las recetas repository-*-plan usan -DryRun; permiten revisar el plan.
terminal-profile-plan también usa -DryRun, pero puede leer configuración
de Terminal: las pruebas deben redirigir LOCALAPPDATA y ProgramData.
repository-build admite árboles sucios porque conserva el comportamiento
local anterior; no debe confundirse con una compilación de release limpia.
resources coordina recetas dentro de este proyecto; no bloquea herramientas
ejecutadas directamente desde fuera.

Los comandos de instalación, firma y creación de perfiles producen cambios al
ejecutarlos. Solo se han preparado sus definiciones. No hay receta de push.
No se ha ejecutado el build, ninguna instalación LANCTL ni firma.

## Retirada pendiente

No se retira ningún envoltorio todavía. Se conservan run.cmd, build.cmd,
helper.cmd, install.cmd, el project.cmd local ignorado y
terminal-profile.cmd. Se conservan todas las implementaciones PS1/Python,
scripts de generación/validación/compilación e install.ps1 / install.sh.
CI y las referencias CLI/web mantienen sus rutas.

Antes de retirarlos hay que validar la TUI real: teclas Fn/Ctrl, redimensionado,
pantalla alternativa, prompts, Ctrl+C, código de salida y datos sin guardar.
Los argumentos con comillas/Unicode/símbolos deben compararse con el envoltorio
antiguo desde CMD y PowerShell. ProjectDock stop puede forzar el cierre.
Las pruebas actuales no justifican eliminar ese fallback ni declarar completa
la sustitución del monitor local.

## Validación realizada

28 recetas/grupos validados por el Core de ProjectDock. En una fixture temporal,
el lanzador compilado conserva espacios, comillas, Unicode y metacaracteres,
devuelve el código 7 del programa de prueba y recibe una consola real.
LANCTL_DATA_DIR apunta al espacio temporal, sin cargar datos reales.

La receta test ejecuta dos pasos: test-isolated mantiene LANCTL_DATA_DIR;
test-paths lo vacía solo para cinco pruebas de rutas que usan mocks/directorios
temporales o calculan rutas sin leerlas. Esas cinco comprueban precisamente el
comportamiento sin override. Resultado de validación: 736 pruebas pasan bajo
el override y las cinco restantes pasan separadamente; 21 pruebas legacy_gui
quedan excluidas por la configuración del repositorio. También pasan las ocho
pruebas focalizadas de integración y scripts, Ruff, formato, referencias,
catálogo de errores e higiene.
