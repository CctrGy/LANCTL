# Guía para beta testers

LANCTL se distribuye como beta técnica. Utilízalo únicamente en redes propias
o donde tengas autorización y conserva una copia independiente de los proyectos
`.vlf`. No uses todavía LANCTL como única fuente del inventario de una red.

## Artefactos

| Plataforma | Instalador | Portable |
|---|---|---|
| Windows x64 | `LANCTL-VERSION-windows-x64-setup.exe` | `LANCTL-VERSION-windows-x64-portable.zip` |
| Linux amd64 | `lanctl_VERSION_amd64.deb` | `LANCTL-VERSION-linux-amd64.tar.gz` |
| Linux arm64 | `lanctl_VERSION_arm64.deb` | `LANCTL-VERSION-linux-arm64.tar.gz` |

Verifica primero el archivo descargado contra `SHA256SUMS.txt`. No mezcles
artefactos de versiones o arquitecturas diferentes.

## Recorrido mínimo de prueba

1. Instala o descomprime en un equipo de prueba y ejecuta `lanctl --version`.
2. Comprueba `lanctl /?` y la versión de los seis launchers.
3. Crea un proyecto vacío y confirma que no hereda dispositivos.
4. Escanea una red pequeña autorizada y edita dos elementos.
5. Guarda, cierra completamente y vuelve a abrir el proyecto.
6. Crea un segundo proyecto y confirma que los inventarios no se mezclan.
7. Cambia de proyecto con modificaciones pendientes y comprueba el aviso.
8. Prueba hardware relevante: Raspberry Pi, ESP, impresora, cámara o NAS.
9. En Linux prueba la CLI/TUI como usuario normal; prueba systemd solamente con
   el DEB y un proyecto de servicio preparado expresamente.
10. Desinstala y confirma que proyectos, configuración y datos permanecen.

Al informar de un problema incluye plataforma, arquitectura, versión exacta,
comando, resultado esperado y observado. Adjunta los registros después de
revisar que no contienen direcciones, nombres o credenciales que no quieras
compartir.

## Puerta de publicación

Un artefacto solo se considera verificado si se ha instalado o ejecutado en su
plataforma y arquitectura reales. Una revisión estática o una compilación
cruzada no sustituye esa prueba. Los resultados de Windows, Linux amd64 y Linux
arm64 deben registrarse por separado.
