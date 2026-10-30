# P100 — Plan de implantación del sistema de idiomas

Fecha: 27/10/2026. Autorización: ejecutar el plan y las modificaciones sin
consultas intermedias; revisar estética después. Las tareas se verifican por
comportamiento y contratos, sin certificar exhaustividad por recuento de claves.
Se trabaja sobre los cambios locales existentes sin descartarlos.

## Secuencia y entregables

1. **Contrato y compatibilidad.** Lector estricto de JSON, versiones 1/2,
   catálogos v2 `LAUNCHERS.<launcher>.CLI/TUI/GUI` y `SHARED`, índice interno
   plano con claves públicas conservadas. Rechazar esquemas desconocidos,
   claves duplicadas, árboles ambiguos e inventarios sin idioma. Validar
   campos de formato, preservar traducciones instaladas y actualizar plantillas.
2. **Fuente bilingüe y distribución.** Una fuente reproducible de mensajes,
   inglés y español con paridad de claves, ubicación y parámetros. Catálogos
   `.lang` estructurados, manifiesto/hash actualizado, actualización compatible
   sin sobrescribir personalizaciones. No traducir datos técnicos ni logs.
3. **Presentación Python.** Migrar ayudas y texto visible de launchers,
   componentes comunes CLI/TUI y formularios/mensajes GUI a claves explícitas.
   Resolver al presentar, evitando congelar el idioma al importar módulos.
   Conservar comandos, opciones, IDs, formato persistente y salidas técnicas.
4. **Presentación web.** Servicio común de cadenas por el puente existente,
   traducción explícita de elementos HTML y texto JavaScript, respetando
   atributos técnicos, nodos de datos y salida de la terminal. Sin reemplazos
   globales de texto, sin traducir arbitrariamente nodos generados ni código.
   Mantener el funcionamiento remoto y la inicialización antes del renderizado.
5. **Migración por aplicaciones.** LANCTL, LANIP/als, LANWIRE/lanwre,
   LANRACK, LANACCESS y LANMON; plantillas y ajustes compartidos, errores
   presentados, plugins con propietario independiente. La matriz del inventario
   es la base de comprobación. Identificar explícitamente pendientes residuales.
6. **Revisión preliminar de código.** Pruebas de presentación, claves usadas,
   compatibilidad v1/v2, fallback, argumentos, datos técnicos, GUI y catálogos
   personalizados; barrido de literales residuales con contexto. No confundir
   un barrido estático con el recorrido completo de todas las pantallas.
7. **Revisión preliminar de archivos.** Cargar ambos `.lang`, comparar claves,
   secciones, parámetros y valores; comprobar esquema, exportación, integridad
   del bundle y ausencia de IDs de inventario como claves de producción.
8. **Controles y entrega.** Pruebas relacionadas y suite según alcance, Ruff,
   catálogo de errores y referencias CLI/web, higiene y diff. Documentar
   evidencia y límites; la estética y certificación de instalables Windows/Linux
   quedan diferenciadas de la revisión funcional preliminar local.

## Criterios de implementación

- IDs `P100.STRING.*` identifican ocurrencias de auditoría, nunca se convierten
  automáticamente en las claves públicas definitivas.
- Una ocurrencia técnica o dato del usuario no se incorpora como traducción.
- Claves compartidas se definen una sola vez, aunque tengan varios consumidores.
- Los catálogos v1 siguen siendo aceptados; los v2 no son reinterpretados como v1.
- La fuente de inglés es fallback, no prueba de completitud de toda la interfaz.
- No ejecutar escaneos de red, modificar credenciales/proyectos ni reemplazar
  idiomas locales al probar; usar datos temporales.

## Seguimiento

El informe `P100-PRELIMINARY-REVIEW.md` registrará lo implementado, las pruebas
reales y los pendientes. P100 solo se cierra al completar la matriz funcional;
esta actuación no declara automáticamente terminada la certificación nativa.

## Estado tras la primera implantación

- [x] Contrato v2, compatibilidad v1, validadores y exportación.
- [x] Generación reproducible de inglés/español y recursos GUI/instalador.
- [x] Infraestructura de presentación común Python y frontend, con pruebas.
- [x] Primera migración transversal y revisión preliminar de consumidores/catálogos.
- [x] Completar migración semántica de los literales y flujos residuales identificados en la auditoría local.
- [ ] Completar recorridos funcionales de las seis aplicaciones en Windows/Linux.
- [ ] Revisar estética después de completar la migración funcional.
- [ ] Compilar y certificar instalables; no se ha publicado una distribución.

Resultados y límites detallados: `P100-PRELIMINARY-REVIEW.md`. La continuación incorpora 2.470 claves por idioma. La revisión distingue
consumidores explícitos, metadatos traducidos al presentar, comandos, datos y
diagnósticos originales. La evidencia actual se registra en la revisión preliminar;
la paridad de claves no sustituye los recorridos nativos de todos los flujos.
