# Integración de LANCTL con Clink

`lanctl.lua`, compatible con LANCTL 0.3.4-alpha.1, registra completado contextual
para `lanctl`, `lanip`, el alias histórico `als` y los ejecutables especializados
`lanwire`, `lanrack`, `lanaccess` y `lanmon`, incluidas sus variantes `.exe`.
El orquestador completa además cada launcher y su alias corto.

El completado incluye las acciones y opciones de `history`, `monitor`,
`radmin`, `smb` y `wol`, además de árboles detallados para LANWIRE, LANRACK,
LANACCESS y LANMON. La prueba de integración compara todos los parsers
publicados con este script para detectar argumentos o comandos nuevos que
todavía no tengan completado.

Antes de congelar una rama `stable/VERSION` debe ejecutarse
`python -m pytest tests/test_clink.py`. El Lua validado queda asociado a esa
versión estable y se distribuye con el instalador de Windows. Clink no se usa
en Linux y no forma parte del alcance actual de sistemas Apple.

Instala la carpeta de scripts una vez:

```bat
clink installscripts "C:\Program Files\LANCTL\clink"
```

Durante el desarrollo puede apuntarse directamente al repositorio:

```bat
clink installscripts "C:\ruta\a\LANCTL\packaging\clink"
```

Comprueba las rutas activas con `clink info`. Para recargar scripts en una
sesión abierta usa `Ctrl-X`, `Ctrl-R`, o abre una consola nueva.

El instalador copia `lanctl.lua` y estas instrucciones a
`C:\Program Files\LANCTL\clink\`. Ejecuta `lanctl completions install` con
el usuario original; el adaptador detecta Clink y usa `clink installscripts`
con argumentos separados, sin shell. Repetir la instalación no añade otra ruta.
Una instalación iniciada ya elevada omite el registro para evitar asociarlo
a la cuenta administrativa: ejecuta el comando desde tu sesión normal.

El desinstalador usa `lanctl completions uninstall`: únicamente retira la
carpeta registrada por esta instalación y usuario. Si otro administrador
desinstala la aplicación, o Clink solo existe en una ubicación privada no
disponible al desinstalador elevado, el propietario debe ejecutar antes
`lanctl completions uninstall` o `clink uninstallscripts RUTA`. No se recorren
ni alteran perfiles de otros usuarios. La certificación con CMD/Clink real
sigue pendiente de un entorno con Clink instalado.

El ZIP portable incluye `clink/` y `prepare.ps1`. Ejecuta `prepare.ps1` para
registrar o `prepare.ps1 -RemoveClink` antes de mover/borrar el portable.
Los demás launchers y Linux conservan su comportamiento previo.
