# Idiomas de LANCTL

LANCTL utiliza catálogos JSON con extensión `.lang`. Las claves son contratos
estables, por ejemplo `LANCTL.CORE.APP.CANCELLED`, y no el texto original.

```json
{
  "schemaVersion": 1,
  "meta": {"code":"es","name":"Spanish","nativeName":"Español","region":"España","version":"1.0","author":"LANCTL"},
  "strings": {
    "LANCTL.CORE.APP.CANCELLED": "Operación cancelada.",
    "LANCTL.LANGUAGE.ERROR.NOT_FOUND": "Idioma no instalado: {language}"
  }
}
```

Los placeholders deben coincidir con el catálogo inglés. Una instalación nueva
genera únicamente `english.lang`; otros idiomas se instalan aparte.

```text
./data/lc/languajes/
├── english.lang
├── español.lang
└── languajes.json
```

Se conserva el nombre histórico `languajes`. `languajes.json` es un índice
generado por LANCTL y no debe editarse manualmente.

```bat
lanctl language list
lanctl language use es
lanctl language info es
lanctl language validate español.lang
lanctl language install español.lang
lanctl language export plantilla.lang
```

Las claves ausentes siempre usan inglés como fallback. Un LCP puede aportar un
catálogo declarando una extensión `language` cuyo `specification.file` apunte a
su `.lang`; requiere el permiso `language.register`.

Los módulos nuevos deben usar `t("CLAVE")` para todo texto visible.
