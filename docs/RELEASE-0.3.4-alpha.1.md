# LANCTL 0.3.4-alpha.1 — GUI EXPERIMENTAL (NO ESTABLE)

Prototipo de la rama `experimental-gui`, publicado como **pre-release** para
probar las interfaces gráficas en otro ordenador. No es una versión estable y
no sustituye a la Release estable 0.3.3. No se necesita instalar Python.

## Descargas de Windows x64

- **Setup**: `LANCTL-0.3.4-alpha.1-windows-x64-setup.exe`.
- **Portable**: `LANCTL-0.3.4-alpha.1-windows-x64-portable.zip`.
- Comprueba el SHA-256 de la descarga con `SHA256SUMS.txt`.

Requisito de las interfaces gráficas: Microsoft Edge WebView2 Runtime.
El instalador no incorpora ese runtime; debe estar instalado en el ordenador
de prueba. Sin certificado Authenticode, Windows puede mostrar editor desconocido.

## Cómo probar la GUI

1. Instala el Setup o extrae todo el ZIP en una carpeta con permiso de escritura.
2. Abre el acceso «LANCTL GUI» del menú Inicio o ejecuta `LANCTL.exe --gui`.
3. Desde el centro gráfico abre LANIP, LANWIRE, LANRACK, LANACCESS y LANMON.
   También puedes ejecutar cada launcher con `--gui`.
4. Crea un proyecto de prueba o abre una copia de un VLF. Prueba creación,
   edición, guardado, ajustes, ventanas simultáneas y cierre con cambios pendientes.
5. Informa de la versión, Windows/WebView2 utilizados, pasos y error observado.
   No publiques credenciales ni proyectos privados al comunicar un problema.

El Setup utiliza la identidad y carpeta de instalación habituales de LANCTL:
actualiza una instalación existente. Para probar sin sustituirla, usa el ZIP
portable; guarda su estado en `data/lanctl` junto a los ejecutables, salvo que
hayas configurado variables de entorno que seleccionen otra raíz de datos.
Conserva copias de proyectos, configuración y credenciales antes de probar.

## Prototipo incluido

- Centro gráfico LANCTL con proyectos, metadatos, ajustes y gestión de plugins.
- Interfaces reales para LANIP, LANWIRE, LANRACK, LANACCESS y LANMON.
- Iconos por launcher, ventanas coordinadas, preferencias de arranque y terminal
  integrada. CLI y TUI permanecen disponibles.
- Mejoras de configuración de proyectos y plugins, topología física y controles
  de integridad y seguridad desarrollados desde la versión 0.3.3.

## Alcance y límites

Es software experimental, con flujos y controles todavía sujetos a cambios.
Las pruebas automáticas y el smoke de ejecutables no equivalen a una validación
manual completa de todas las pantallas o de un entorno de producción.
Los prototipos visuales de `GUI-PROTOTYPES.md` no se presentan como funciones terminadas.
Las distribuciones Linux conservan su alcance CLI/TUI; esta pre-release no declara
soporte gráfico Linux. El acceso remoto no se habilita automáticamente.

La Release incluye los scripts de instalación, metadatos de versión/revisión y
sumas SHA-256. Para fijar la versión experimental en Windows:

```powershell
.\install.ps1 -Version 0.3.4-alpha.1
```

Documentación: [centro gráfico](LANCTL-GUI.md), [LANIP](LANIP-GUI.md),
[otras aplicaciones](LAUNCHER-GUI.md) y [limitaciones pendientes](BACKLOG.md).
