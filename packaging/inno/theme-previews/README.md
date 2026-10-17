# Vistas previas de apariencia

Los cinco BMP muestran la pantalla Inicio real de LANCTL, renderizada con los
presets del Core y sin proyectos, plugins ni datos de usuario. Inno los incluye
con `dontcopy`, los extrae en su directorio temporal y carga la imagen de la
opción seleccionada en `TBitmapImage`.

Para regenerarlos en Windows, con Edge y Playwright instalados en el entorno
de desarrollo:

```text
python tools/generate_installer_theme_previews.py
python -m pytest tests/test_installer_theme_previews.py
```

El generador usa el navegador para redimensionar la captura y la biblioteca
estándar de Python para escribir BMP RGB de 24 bits. No necesita Pillow. La
compilación del instalador y las pruebas de recursos usan los archivos
versionados; no requieren un navegador ni generan capturas durante CI.

Además de esas pruebas, revisar las cinco opciones en la página Apariencia
inicial del Setup compilado, sin continuar con la instalación. Verificar que
cambia la imagen, conserva su proporción y no queda cortada por el formulario.
