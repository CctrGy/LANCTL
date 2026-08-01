# LANCTL mDNS + SSDP Discovery

Extrae del núcleo de LANCTL los descubridores mDNS/DNS-SD y SSDP/UPnP.
El paquete usa runtime `trusted` porque abre sockets UDP multicast.

```bat
lanctl plugin install plugins\lanctl.discovery.mdns-ssdp.lcp
lanctl plugin enable lanctl.discovery.mdns-ssdp --grant-all --trust
```

Una vez activo, los perfiles `normal` y `accurate` de `list` consumen sus
resultados automáticamente. Al desactivarlo, ICMP, ARP y WSD siguen operativos.
