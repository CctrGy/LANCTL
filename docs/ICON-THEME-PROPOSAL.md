# P92 — propuesta de iconos por tema

Fecha: 04/11/2026. Estado: propuesta preparada; decisión visual e implementación
pendientes. Alcance de esta entrega: revisión de fuentes y contraste de colores,
sin modificar recursos gráficos, preferencias, instaladores ni asociaciones.

## Recomendación

Conservar las siluetas que identifican cada aplicación. Adaptar al tema los
símbolos internos mediante los tokens existentes y mantener la placa oscura con
verde de los iconos de aplicación que ve el sistema operativo. Esta opción
aprovecha el comportamiento ya presente en parte de la GUI, reduce recursos
adicionales y conserva una identidad reconocible entre ventanas y escritorio.

No hace falta añadir una preferencia de iconos: la selección de tema existente
basta para los símbolos internos. Los colores de estado (error, aviso, selección)
deben mantener su significado y no convertirse en color de marca.

## Evidencia en las fuentes

- `assets/launcher-icons/` contiene SVG, PNG e ICO de los launchers. Los SVG
  examinados de LANCTL y LANIP tienen placa `#151b1f`, borde `#3b4940` y trazo
  `#b2ef26`; sus colores son literales, independientes de los tokens CSS.
- Las tarjetas `.launch svg` de `gui/suite.css` utilizan `stroke:currentColor`
  y `color:var(--lime)`. `gui/app-preferences.js` asigna `--color-accent` a
  `--lime` y restaura el tema al cancelar la vista previa. Esto permite conservar
  el mecanismo compartido; no demuestra que todos los iconos internos lo usen.
- Los favicons de `gui/suite.html`, `gui/index.html` y `gui/launcher.js` apuntan a
  los SVG de aplicación. Un SVG cargado como recurso externo no hereda
  automáticamente los tokens CSS de su documento consumidor.
- Los puntos de entrada de GUI llaman a `webview_icon_path` al iniciar.
  `core/window_icons.py` dispone además de un adaptador Windows para iconos
  nativos. La revisión no acredita actualización dinámica de iconos de ventana.
- `LANCTL.spec` incorpora los recursos y fija un ICO por ejecutable; el
  instalador Inno referencia ICO en sus accesos. Cambiar el tema de la GUI no
  cambia esos recursos instalados ni garantiza invalidar las cachés del sistema.
- El catálogo `shared/assets/icons.py` gestiona imágenes JPEG de dispositivos:
  tiene otro contrato y no es el destino de variantes de marca por tema.

## Variantes propuestas

| Superficie | A · Recomendada | B · Alternativa para valorar |
| --- | --- | --- |
| Símbolo interno sin placa | Misma silueta, acento del tema mediante `currentColor` | Misma silueta, color de texto del tema; acento solo al seleccionar |
| Marca en cabecera/tarjeta | Símbolo adaptable y nombre legible | Placa de marca fija, sin recolorear |
| Favicon | Placa oscura y verde actuales | Igual que A en esta fase |
| Ventana/barra de tareas | Recurso actual por aplicación | Estudiar variantes nativas después, por backend |
| Ejecutable y acceso directo | Identidad fija distribuida con el programa | Igual que A en esta fase |

A integra mejor la marca con los temas actuales y aprovecha los tokens existentes.
B evita que un acento personalizado de poco contraste reduzca la legibilidad;
puede servir como fallback si la implementación futura detecta contraste
insuficiente. No introducir ambas como opciones configurables sin necesidad.

## Contraste de los temas actuales

Cálculo local sobre los cinco presets de `core/gui_preferences.py`, leído con
`ast.literal_eval` sin cargar configuración del usuario. Luminancia relativa
sRGB linealizada, razón `(Lmayor + 0.05) / (Lmenor + 0.05)`. Valores redondeados;
son comprobaciones de colores planos, no certificación visual o de accesibilidad.

| Tema | Acento/fondo | Acento/superficie | Verde fijo `#b2ef26`/fondo |
| --- | ---: | ---: | ---: |
| Grafito | 12,95 | 11,00 | 12,95 |
| Azul noche | 6,95 | 6,25 | 13,40 |
| Bosque | 10,54 | 8,86 | 12,81 |
| Violeta | 7,92 | 6,81 | 12,95 |
| Claro | 5,16 | 5,64 | 1,26 |

El verde fijo sobre la placa actual obtiene 12,63. Por eso se recomienda mantener
la placa en el icono externo y utilizar el acento verde oscuro `#477300` del tema
Claro para símbolos internos sin placa. Como objetivo de diseño, exigir al menos
3:1 para símbolos funcionales contra su fondo inmediato. Comprobar también hover,
selección y fondos de componentes: la tabla no cubre esos estados ni tokens
aportados por plugins. La legibilidad a 16 px requiere revisión de trazos real.

## Coordinación con P116, P71/P72 y distribución

P116 puede continuar sin implementar P92: diseñar `.vlf` como documento con
motivo de proyecto/red y `.lcp` como paquete/módulo, compartiendo el lenguaje de
trazos de los launchers. Distinguirlos por silueta, además del color, a 16, 24,
32, 48 y 256 px. Mantener fuentes vectoriales y generar PNG/ICO de forma
reproducible. Estas son direcciones propuestas, no diseños gráficos aprobados.

P71/P72 deben integrar y retirar solo los registros de asociación propios.
Usar recursos de archivo fijos que funcionen con el tema del explorador del
sistema, independiente del tema elegido dentro de LANCTL. El icono de un `.lcp`
no expresa firma, confianza ni autorización de ejecución. El alcance portable
necesita una decisión específica antes de registrar asociaciones persistentes.

Un cambio interno puede funcionar en una compilación si usa CSS/SVG o variantes
incluidas en ella. Cambiar el icono incrustado requiere una nueva distribución y
la firma autorizada que proceda; nunca modificar un ejecutable firmado instalado.
El tratamiento de iconos de ventana, escritorio y cachés debe validarse en cada
backend Windows/Linux antes de prometer un cambio en ejecución.

## Verificación necesaria antes de implementar o cerrar

1. Elegir A o B y revisar una muestra visual representativa de los seis launchers.
2. Inventariar símbolos internos restantes: distinguir marca, dispositivos y
   estados; conservar formas y nombres accesibles. Reutilizar tokens existentes.
3. Revisar tamaños 16/24/32/48, escalas 100/150/200 %, los cinco temas, estados
   interactivos y un tema de plugin con poco contraste. Fallback al color de
   texto si el acento no alcanza el objetivo contra el fondo real.
4. Comprobar vista previa, cancelar, aplicar y reiniciar; que no aparezcan mezclas
   de tema al refrescar o abrir otro launcher. Mantener los controles de idioma.
5. Para recursos del sistema, comprobar Windows y Linux instalados/portables,
   empaquetado, accesos y cachés. Las pruebas simuladas de backend no certifican
   esas plataformas ni un instalador.

P92 permanece abierta. Esta entrega completa la propuesta escrita y el análisis
de alcance; no autoriza por sí sola un recoloreado general ni cierra P116.
