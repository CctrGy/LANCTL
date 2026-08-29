# Recorrido de presentación de LANCTL

## Preparación reproducible

La demostración aislada no modifica el inventario normal ni envía paquetes a la
red. Genera un proyecto VLF verificable y dos informes:

```powershell
lanctl demo --output .\LANCTL-demo --format all --force
```

En la distribución instalada se puede usar directamente el ejecutable dedicado:

```powershell
landemo.exe --output .\LANCTL-demo --format all --force
```

`lanmon.exe` abre directamente las funciones de monitorización; sin argumentos
muestra el estado (`lanctl monitor status`).

Archivos creados:

- `LANCTL-Presentation-Demo.vlf`: proyecto con tres identidades de muestra.
- `demo-report.html`: informe visual para abrir durante la presentación.
- `demo-report.json`: evidencia estructurada y reutilizable.
- `devices.json`: inventario aislado usado para construir el proyecto.

El recorrido muestra descubrimiento, fusión de evidencias, confianza de
identidad, monitorización, historial y un diagnóstico WOL simulado. El modo de
muestra nunca envía un paquete WOL real.

## Ensayo con una red real

1. Abrir LANCTL y seleccionar el proyecto preparado.
2. Ejecutar un escaneo `normal`; usar `accurate` solo si el tiempo lo permite.
3. Mostrar fabricante, hostname, protocolos, métodos y confianza.
4. Abrir monitorización e historial.
5. Ejecutar un diagnóstico sobre un dispositivo autorizado.
6. Enviar WOL únicamente a un equipo de prueba previamente acordado.
7. Abrir el informe HTML de respaldo si la red de la sala no responde.

## Puertas para `0.3.0-rc.1`

- Árbol Git limpio y todas las pruebas aprobadas dos veces.
- Versión interna, paquete, instalador y metadatos idénticos.
- Ejecutables e instalador con firma Authenticode válida y timestamp.
- Instalación, actualización, demo y desinstalación en un Windows limpio.
- Datos de usuario conservados tras actualizar y desinstalar.
- Proyecto VLF e informes de demostración verificados.
- Ningún plugin en cuarentena y registro de seguridad sin incumplimientos.

El workflow oficial de release ejecuta estas pruebas sobre un runner Windows
limpio. La publicación se detiene si falta el certificado o falla cualquiera de
las comprobaciones.
