# Integración de LANCTL con Clink

`lanctl.lua` registra completado contextual para `lanctl`, `LANCTL.exe`, `als`
y `als.exe`. Incluye comandos directos heredados y el ámbito explícito
`virtual`.

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
