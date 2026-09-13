LANCTL portable para Linux
==========================

Este paquete contiene los launchers autocontenidos `lanctl`, `lanip`,
`lanwire`, `lanrack`, `lanaccess` y `lanmon`; no necesita una instalación de
Python. Ejecútalos desde el directorio LANCTL, por ejemplo:

    ./lanctl --version
    ./lanip -tui

El marcador `LANCTL.portable` hace que los datos modificables se almacenen en
`data/lanctl` junto a los ejecutables. Conserva ese directorio al actualizar.
El paquete portable no modifica PATH, `/etc`, `/var/lib`, systemd, el firewall
ni la configuración SSH/HTTPS del equipo.

Algunas funciones opcionales usan programas del sistema:

* `iputils-ping` para ICMP;
* `arping` para descubrimiento ARP activo;
* `smbclient` para enumerar recursos SMB;
* `xdg-utils` para abrir recursos mediante el escritorio.

Estos programas no son necesarios para iniciar la CLI/TUI. La disponibilidad
de ciertas técnicas de descubrimiento depende también de permisos y de la
configuración de la distribución Linux.

La compilación `amd64` sirve para equipos Linux Intel/AMD de 64 bits. La
compilación `arm64` sirve para Linux AArch64, incluida Raspberry Pi OS de
64 bits en Raspberry Pi 5. Los binarios no son intercambiables.

No ejecutes simultáneamente dos copias que utilicen el mismo directorio de
datos. Para un servicio permanente usa el paquete DEB y su cuenta dedicada en
lugar del tarball portable.
