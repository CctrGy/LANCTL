# Integración de LANCTL con Clink

`lanctl.lua`, compatible con LANCTL 0.3.2-beta.1, registra completado contextual
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

El instalador de LANCTL deberá copiar `lanctl.lua` a
`C:\Program Files\LANCTL\clink\` y ejecutar `clink installscripts` solamente
si detecta Clink. Al desinstalar deberá usar `clink uninstallscripts` con la
misma ruta.
