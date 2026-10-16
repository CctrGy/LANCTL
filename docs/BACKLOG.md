# Trabajo pendiente de LANCTL

Estado revisado el **15/10/2026**. Los puntos marcados tienen corrección o
verificación local con evidencia en [la matriz de comprobación](BACKLOG-VERIFICATION.md).
La validación de plataformas externas sigue separada; las marcas no equivalen
a certificar instaladores ni sistemas que no se han ejecutado.

## Prioridad alta: persistencia y fiabilidad

- [x] **P01.** Reproducir el fallo de `Ctrl+S` en el TUI y determinar qué cambios no se
  guardan: configuración, proyecto, inventario o estado de los gestores.
- [x] **P02.** Verificar el flujo completo de guardado: detección de cambios, validación,
  escritura transaccional, bloqueo, confirmación visual y recarga posterior.
- [x] **P03.** Comprobar el comportamiento de `Ctrl+S` con proyecto activo, sin proyecto,
  en cada ventana modal y durante tareas de segundo plano.
- [x] **P04.** Revisar la carga de plugins: descubrimiento, dependencias, permisos,
  estados pendiente/activo/fallido, recarga y presentación de errores.

## Incidencia reportada: activación de Wake-on-LAN en la GUI

- [x] **P05.** Investigar y corregir el flujo de activación de Wake-on-LAN cuando se
  conceden los permisos y se autoriza la ejecución `trusted`, pero la GUI
  devuelve un error de confianza del editor.

Estado: **flujo corregido y verificado**. Gravedad: media. El LCP WOL incluido
no lleva firma; se conserva el bloqueo de seguridad y la GUI explica el requisito.
Un LCP firmado permite autorizar al editor seleccionando el paquete original.
Evidencia: captura aportada por el usuario del diálogo «Activar Wake-on-LAN».
La versión instalada y la procedencia/firma del LCP no se pueden determinar
a partir de la captura.

Secuencia a reproducir: abrir la activación de Wake-on-LAN, marcar
`network.udp`, `functions.register`, `ui-action.register` y «Autorizar ejecución
trusted (requiere editor autorizado)», y pulsar «Activar plugin».

Mensaje mostrado, con su identificador tal como aparece en la captura:

```text
el runtime trusted requiere un LCP firmado por un editor confiable; usa plugin publisher trust (0e94E1E397)
```

Impacto observado: la activación queda bloqueada y el diálogo remite a un comando
CLI sin completar el flujo de autorización del editor desde esa pantalla.
Referencia para investigar: `PluginManager.enable()` en
`src/lanctl/core/plugins/manager.py`, verificación de firma y almacén de editores
confiables. Se confirmó el bloqueo para paquetes sin firma y para editores no autorizados.
La GUI distingue ambos casos; no se concede confianza al marcar permisos.

Criterio de aceptación: un paquete firmado por un editor autorizado se activa con
los permisos concedidos; si falta esa confianza o la firma no es válida, la GUI
explica el requisito concreto y los pasos necesarios. La corrección debe conservar
la validación de firmas y añadir regresiones para ambos casos.

## Plugins: disponibilidad del botón de configuración

- [x] **P06.** Mostrar el botón de configuración únicamente en los plugins que ofrezcan
  opciones configurables. Si el plugin no dispone de ninguna, ocultar el botón
  para evitar abrir un panel vacío.

Criterio de aceptación: comprobar plugins sin opciones y plugins configurables,
incluidos los que todavía usan valores predeterminados y no tienen configuración
guardada. La visibilidad debe depender de las opciones disponibles, no de haber
guardado ajustes previamente, y actualizarse al recargar o actualizar el plugin.

## Project Manager

- [x] **P07.** Permitir guardar manualmente el proyecto seleccionado o activo.
- [x] **P08.** Añadir edición de nombre, descripción, autor, LAN, ubicación, empresa y
  responsable.
- [x] **P09.** Crear formularios modales con cuadros de texto para crear y editar los
  metadatos del proyecto.
- [x] **P10.** Validar los datos antes de escribir y pedir confirmación si existen
  modificaciones sin guardar.
- [x] **P11.** Refrescar el catálogo y la pestaña de información inmediatamente después
  de crear, editar, guardar, activar o eliminar un proyecto.

## Arranque de LANCTL y coordinación de launchers

Pendientes de revisión incorporados el 15/10/2026:

- [x] **P12.** Añadir una opción de configuración global y persistente para elegir
  **CLI, TUI o GUI como interfaz preferida al iniciar LANCTL sin argumentos**.
  Debe aplicarse tanto al doble clic sobre el ejecutable principal como a su
  invocación desde una terminal. Los argumentos explícitos deben conservar su
  prioridad sobre esta preferencia. Verificar los tres modos en ambos arranques.
- [x] **P13.** Permitir configurar el comportamiento de la GUI principal al abrir un
  launcher: **cerrar la GUI de LANCTL** o **mantenerla abierta**. Comprobar que
  cerrar la ventana principal no cierre el launcher y que un fallo al abrirlo
  mantenga visible el error, sin cerrar prematuramente LANCTL.
- [x] **P14.** Impedir que se abran dos ventanas GUI del mismo launcher. Detectar la
  ventana existente, restaurarla si está minimizada y traerla al frente al
  solicitar otra apertura. Revisar este comportamiento desde LANCTL, terminal
  y doble clic, incluyendo aperturas simultáneas y recuperación después de un
  cierre inesperado, para evitar duplicados o bloqueos por instancias obsoletas.
- [x] **P15.** Verificar que **launchers distintos puedan permanecer abiertos al mismo
  tiempo** y mantengan comunicación y feedback entre ellos: estado de apertura,
  cierre y errores, eventos y actualización de los datos compartidos que les
  correspondan. Confirmar que cada interfaz refleje los cambios relevantes sin
  reiniciarse, respete el contexto de su proyecto y que cerrar un launcher no
  interrumpa los demás. Incluir la GUI de LANCTL cuando se configure para seguir
  abierta y probar la coordinación cuando se cierre.

## Teclado y ayudas visuales

- [x] **P16.** Remarcar `→` con fondo blanco en el pie del menú Plugins.
- [x] **P17.** Auditar todos los pies de ventanas para encontrar teclas sin el fondo de
  tecla correcto, incluyendo flechas, teclas de función, `Supr`, `Enter`,
  `Esc` y combinaciones `Ctrl+…`.
- [x] **P18.** Revisar el editor de asignaciones: conflictos, teclas reservadas,
  desactivación con `None`, persistencia y restauración de valores iniciales.
- [x] **P19.** Verificar por separado qué atajos están activos y cuáles son visibles en
  la barra inferior.
- [x] **P20.** Comprobar que los atajos locales de una ventana no se ejecuten fuera de
  ella.

## Consola integrada del TUI

- [x] **P21.** Añadir más mensajes útiles sobre inicio y final de tareas, resultados,
  guardado, recarga, cambios pendientes y errores recuperables.
- [x] **P22.** Mantener los mensajes breves, con nivel y origen coherentes y sin desplazar
  innecesariamente la tabla principal.
- [x] **P23.** Revisar el historial, el límite de líneas y el ajuste al ancho disponible.

## Revisión estética general

- [x] **P24.** Auditar bordes, títulos, pestañas, separadores, colores de fondo,
  alineación y recorte en todos los overlays.
- [x] **P25.** Probar tamaños de terminal pequeños, medios y muy grandes, además de
  cambios de tamaño mientras el TUI está abierto.
- [x] **P26.** Verificar que las ventanas modales oculten correctamente las líneas del
  fondo y que el renderizado diferencial no deje residuos ni produzca parpadeo.
- [x] **P27.** Unificar el estilo de selección, campos editables, cambios pendientes,
  estados deshabilitados y mensajes de confirmación.

### GUI: disposición y recorte de la barra inferior

Estado: **corrección validada en navegador** el 15/10/2026. Se conserva la
corrección de interfaz que el usuario indicó en curso el 14/10/2026: pruebas con
50 proyectos/plugins, desplazamiento y ventanas de 790×570, 660×460 y 375×650.

Evidencia: dos capturas de la vista de proyectos; la primera muestra la barra
inferior con plugins, CLI, Actividad y Sistema, y en la segunda esa barra no
queda visible dentro de la ventana. La primera captura muestra la versión 0.3.3.

- [x] **P28.** Validar la corrección que ya está en marcha: la barra y sus controles
  deben permanecer visibles y accesibles al redimensionar la ventana y desplazar
  la lista de proyectos, sin recortes ni superposiciones.

## Auditoría técnica

- [x] **P29.** Revisar concurrencia, bloqueos de archivos y escrituras simultáneas entre
  TUI, CLI, backend y plugins.
- [x] **P30.** Revisar tareas de segundo plano, cancelación, cierre seguro y liberación
  de recursos.
- [x] **P31.** Confirmar que errores, eventos, logs y puntos de extensión del core se
  emitan de forma coherente en todos los flujos anteriores.
- [ ] **P32.** Ejecutar pruebas de regresión en Windows instalado, Windows portable,
  Linux ARM64 y acceso remoto.
- [x] **P33.** Registrar durante la revisión cualquier hallazgo técnico adicional con
  pasos de reproducción, impacto y prueba de aceptación.

## Validación que sigue pendiente

P32 permanece abierto: instalación/actualización/desinstalación en Windows
limpio, Linux ARM64 y acceso SSH desde otra máquina. Las pruebas locales y los
smokes de GUI no sustituyen esas comprobaciones. La matriz registra el alcance
exacto de cada prueba y los hallazgos corregidos.

## Próxima revisión: pendientes añadidos el 16/10/2026

Estado actualizado el **16/10/2026**. Los avances de GUI-DESIGN y AUDITOR se
indican por separado; las comprobaciones de backend se amplían en
[la matriz de verificación](BACKLOG-VERIFICATION.md).

- [ ] **P34.** Revisar el estado actual de los plugins y comprobar que su estado
  real se corresponda con el que muestra la interfaz. Esta nueva revisión
  complementa las comprobaciones anteriores de P04, P05 y P06.
  **Parcial — AUDITOR:** corregidas integridad y firma al activar/verificar,
  restauración segura al arrancar, dependencias, limpieza de runtimes,
  cuarentena persistente y escrituras concurrentes. Falta la propagación
  inmediata de cambios y revocaciones a todos los runtimes e interfaces ya
  abiertos; las operaciones con una revisión antigua se rechazan y piden recarga.
  Verificación final: 43 regresiones nuevas; suite completa con 1.013 pruebas y
  643 subpruebas aprobadas, 1 omisión POSIX y cobertura del 67,83 %.
- [ ] **P35.** Revisar el feedback del sistema de temas y paletas de colores:
  comprobar cómo se reflejan los cambios seleccionados en la interfaz y en los
  ajustes guardados. Definir y añadir opciones básicas de configuración de la
  GUI; las opciones concretas quedan por determinar en esa revisión.
- [x] **P36.** Al crear un proyecto, rellenar automáticamente el campo de carpeta
  de guardado con la ruta predeterminada. Permitir que el usuario la edite o
  seleccione otra carpeta si lo desea, sin exigir una selección manual para
  aceptar la ubicación predeterminada.

## Observaciones de GUI del 16/10/2026

- [x] **P37.** Ajustar Inicio al área útil inicial, incluyendo escalado de Windows,
  para mostrar los cinco launchers completos sin scroll. Mantener cabecera y pie
  visibles al redimensionar.
- [x] **P38.** Completar Configuración GUI con las opciones de programa y proyecto
  agrupadas por temas, reutilizando el catálogo y las validaciones compartidas
  del CLI. Diferenciar campos editables y automáticos y comprobar persistencia.
- [x] **P39.** Hacer que la terminal integrada ocupe el espacio disponible al
  redimensionar; solo la salida debe desplazarse, con entrada y pie visibles.
- [ ] **P40.** Revisar con AUDITOR el diálogo de permisos de plugins y el bloqueo
  por firma no válida (mDNS + SSDP Discovery). Distinguir permisos, firma y
  confianza del editor; relacionado con P34/P05. No asumir fallo del backend
  ni retirar validaciones de seguridad. Anotación enviada a AUDITOR.
  **Parcial — AUDITOR:** confirmado que los LCP incluidos de mDNS/SSDP y WOL
  carecen de firma; el bloqueo es correcto. Corregidos fallos independientes del
  backend de validación, estado y persistencia, con regresiones. Sigue pendiente
  distribuir LCP firmados por el editor del proyecto y verificar su instalación
  real. P42 conserva la evidencia del mismo caso; no es una incidencia adicional.
- [x] **P41.** Ampliar P36: proponer valores iniciales editables para metadatos
  técnicos de proyectos, especialmente LAN, sin copiar datos privados del
  proyecto anterior ni sobrescribir VLF existentes.

La confirmación de cambios sin guardar de LANCTL utiliza ahora un diálogo
propio con botón principal verde lima, en lugar del aviso «Esta página dice».
- [ ] **P42.** Seguimiento de P40: revisar permisos y firmas de plugins a partir del
  bloqueo reportado al activar **LANCTL mDNS + SSDP Discovery**. Relacionado con
  P34 y con el antecedente de Wake-on-LAN de P05.

  Evidencia reportada: captura del 16/10/2026 del diálogo «Activar LANCTL mDNS +
  SSDP Discovery», que muestra los permisos `scanner.register`,
  `functions.register` y `network.scan`. El diálogo informa de que el paquete
  no tiene una firma válida, solicita un LCP firmado y no permite activarlo.
  La captura por sí sola no demuestra un fallo del backend: el bloqueo de este
  paquete sin firma es correcto. La auditoría posterior encontró y corrigió
  otros fallos de integridad, activación y persistencia, registrados en la matriz.

  Revisión técnica realizada: permisos solicitados/concedidos, autorización
  del runtime `trusted`, validez de la firma y confianza del editor. La firma de
  los cuatro plugins `trusted` del catálogo sigue pendiente de distribución;
  no se ha generado ni autorizado una identidad oficial durante la auditoría.


Implementación GUI del 16/10/2026: P36/P37/P38/P39/P41 completados con
validación local de catálogo compartido, persistencia y distribución a tamaños
790×570, 960×590, 660×460 y 1440×900. P40/P42: el flujo gráfico ahora permite
instalar una versión firmada verificada sin recurrir a comandos; la auditoría
de la distribución/firma de los paquetes sigue separada. No se autoriza un
paquete sin firma por marcar sus permisos.
