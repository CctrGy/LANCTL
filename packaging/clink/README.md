# Integración de LANCTL con Clink

`lanctl.lua` registra completado contextual para `lanctl`, `LANCTL.exe`, `als`
y `als.exe`. Todos los comandos se completan directamente desde la raíz.

El completado incluye las acciones y opciones de `history`, `monitor`,
`radmin`, `smb` y `wol`, además de los comandos clásicos. La prueba de
integración compara las opciones publicadas por el parser de LANCTL con este
script para detectar argumentos nuevos que todavía no tengan completado.

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
