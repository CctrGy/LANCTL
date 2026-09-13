# LANCTL 0.3.0-beta.22

Beta técnica dirigida a evaluación controlada. Los launchers son
autocontenidos y no requieren que Python esté instalado en el equipo destino.

## Artefactos previstos

- `LANCTL-0.3.0-beta.22-windows-x64-setup.exe`
- `LANCTL-0.3.0-beta.22-windows-x64-portable.zip`
- `lanctl_0.3.0-beta.22_amd64.deb`
- `LANCTL-0.3.0-beta.22-linux-amd64.tar.gz`
- `lanctl_0.3.0-beta.22_arm64.deb`
- `LANCTL-0.3.0-beta.22-linux-arm64.tar.gz`
- `SHA256SUMS.txt`

La presencia de un nombre en esta lista no acredita por sí sola que el artefacto
haya sido publicado o probado. La publicación definitiva debe adjuntar los
resultados independientes de Windows x64, Linux amd64 y Linux arm64.

## Launchers

La distribución incluye `lanctl`, `lanip`, `lanwire`, `lanrack`, `lanaccess` y
`lanmon`. En Windows llevan la extensión `.exe`; en Linux no.

## Advertencias

- Verifica siempre el hash SHA-256 antes de instalar.
- Conserva una copia externa de los proyectos `.vlf` durante la beta.
- El acceso remoto permanece desactivado hasta su configuración local expresa.
- El DEB conserva `/var/lib/lanctl` y `/etc/lanctl` al desinstalar o purgar.
- El portable Linux no instala servicios ni modifica PATH.
- Consulta `BETA-TESTING.md` y `KNOWN-ISSUES.md` antes de distribuirlo.
