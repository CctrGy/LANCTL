# LANCTL 0.3.4-alpha.2 — Experimental (no estable)

Nueva revisión de desarrollo posterior a `0.3.4-alpha.1`. Incluye mejoras de
configuración GUI, navegación TUI, diagnóstico, idiomas e instaladores.
No declara una versión estable ni modifica los identificadores públicos del Core.

Los scripts de compilación de Linux y Windows usan `0.3.4-alpha.2` por defecto
y comprueban que coincida con la versión declarada por la aplicación.

Artefactos previstos:

- `LANCTL-0.3.4-alpha.2-linux-amd64-setup.run` (asistente gráfico Linux)
- `lanctl_0.3.4-alpha.2_amd64.deb`
- `LANCTL-0.3.4-alpha.2-linux-amd64.tar.gz`
- `LANCTL-0.3.4-alpha.2-windows-x64-setup.exe`
- `LANCTL-0.3.4-alpha.2-windows-x64-portable.zip`

Este cambio de versión no recompila ni renombra los binarios anteriores: los
artefactos `0.3.4-alpha.1` conservan su versión original. La disponibilidad de
cada instalador requiere una compilación en su plataforma correspondiente.
