# 1. Registrar las decisiones de arquitectura

Fecha: 2026-09-25

## Estado

Aceptada

## Contexto

LANCTL tiene contratos públicos para plugins, formatos persistentes, varios
launchers e interfaces diferentes. Algunas decisiones afectan a la
retrocompatibilidad y no pueden reconstruirse únicamente leyendo el código.

## Decisión

Las decisiones arquitectónicas relevantes se documentarán en `docs/adr/` como
archivos Markdown numerados. Cada ADR incluirá contexto, decisión,
consecuencias y estado. Una decisión posterior no borrará la anterior: la
marcará como sustituida y enlazará el nuevo ADR.

## Consecuencias

- El razonamiento técnico queda versionado junto al código.
- Los cambios de contratos, ramas, persistencia y distribución requieren un
  ADR cuando introduzcan una política nueva o incompatible.
- Los ADR forman parte del proyecto y no deben añadirse a `.gitignore`.
