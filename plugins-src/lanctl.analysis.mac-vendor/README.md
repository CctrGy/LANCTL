# MAC Vendor Resolver

Complemento LCP de LANCTL que resuelve fabricantes mediante el prefijo de una
dirección MAC. El escaneo usa siempre la caché local; Internet solo se utiliza
al ejecutar una actualización explícita desde los registros públicos oficiales
IEEE MA-L, MA-M y MA-S.

```bat
lanctl mac-vendor resolve 00:0C:29:AA:BB:CC
lanctl mac-vendor list
lanctl mac-vendor add 001122 "Fabricante local"
lanctl mac-vendor add FA758937BE52 "Móvil Yuyu" --force
lanctl mac-vendor remove 001122
lanctl mac-vendor update
```

Las reglas personalizadas pueden contener prefijos de 24, 28 o 36 bits, o una
MAC completa de 48 bits. Gana siempre la coincidencia más larga. `update`
descarga exclusivamente las listas oficiales configuradas en el complemento y
conserva las reglas locales que no colisionan con IEEE.

El runtime es `trusted` porque registra funciones Python, escribe su caché y
puede descargar la actualización. Debe habilitarse expresamente con confianza.
