# LANCTL 0.3.1-beta.1

Beta técnica dirigida a evaluación controlada. Los launchers son
autocontenidos y no requieren que Python esté instalado en el equipo destino.

## Cambios destacados

- El instalador remoto de Windows usa `auto` como versión predeterminada.
- La versión solicitada se valida después de inicializar sus parámetros.
- La selección automática consulta GitHub Releases por canal `beta` o `stable`.
- Se mantiene la comprobación SHA-256 antes de instalar cualquier artefacto.

## Artefactos previstos

- `LANCTL-0.3.1-beta.1-windows-x64-setup.exe`
- `LANCTL-0.3.1-beta.1-windows-x64-portable.zip`
- `lanctl_0.3.1-beta.1_amd64.deb`
- `LANCTL-0.3.1-beta.1-linux-amd64.tar.gz`
- `lanctl_0.3.1-beta.1_arm64.deb`
- `LANCTL-0.3.1-beta.1-linux-arm64.tar.gz`
- `install.ps1`
- `install.sh`
- `SHA256SUMS.txt`

## Launchers

La distribución incluye `lanctl`, `lanip`, `lanwire`, `lanrack`, `lanaccess` y
`lanmon`. En Windows llevan la extensión `.exe`; en Linux no.

## Advertencias

- Verifica siempre el hash SHA-256 antes de instalar.
- Conserva una copia externa de los proyectos `.vlf` durante la beta.
- El acceso remoto permanece desactivado hasta su configuración local expresa.
- El DEB conserva `/var/lib/lanctl` y `/etc/lanctl` al desinstalar o purgar.
- El portable Linux no instala servicios ni modifica `PATH`.
- Consulta `BETA-TESTING.md` y `KNOWN-ISSUES.md` antes de distribuirlo.
