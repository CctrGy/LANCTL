"""Bilingual Linux installer messages, independent of program language selection."""

TEXT = {
    "advanced": (
        "Advanced installation (remote service account options)",
        "Instalación avanzada (opciones de cuenta remota del servicio)",
    ),
    "title": ("LANCTL · Linux setup", "LANCTL · Instalador Linux"),
    "welcome": ("Welcome", "Bienvenido"),
    "intro": (
        (
            "Install LANCTL for this computer. Administrator authentication is requested only "
            "for packages and the optional monitor service. Personal settings belong to your user."
        ),
        (
            "Instala LANCTL en este equipo. Solo se pedirán permisos de administrador para los "
            "paquetes y el servicio opcional del monitor. La configuración personal será de tu usuario."
        ),
    ),
    "installer_language": ("Installer language", "Idioma del instalador"),
    "components": ("Components", "Componentes"),
    "core": (
        "LANCTL and its six launchers (required)",
        "LANCTL y sus seis launchers (obligatorio)",
    ),
    "path": (
        "Terminal commands in /usr/bin (included by DEB)",
        "Comandos en /usr/bin (incluidos por el DEB)",
    ),
    "monitor": ("Enable LANMON as a system service", "Activar LANMON como servicio del sistema"),
    "tools": (
        "Install network tools (ping, ARP, SMB, SSH)",
        "Instalar herramientas de red (ping, ARP, SMB, SSH)",
    ),
    "plugins": ("Optional plugins", "Plugins opcionales"),
    "components_help": (
        (
            "The application files are installed together. Plugin selection initializes new "
            "installations without activating permissions. Existing selections are preserved. "
            "An unselected monitor leaves any existing service unchanged."
        ),
        (
            "Los archivos de la aplicación se instalan juntos. La selección de plugins inicializa "
            "instalaciones nuevas sin activar permisos. Se conserva la selección existente. "
            "Si no marcas el monitor, un servicio existente no se modifica."
        ),
    ),
    "preferences": ("Initial configuration", "Configuración inicial"),
    "program_language": ("Program language", "Idioma del programa"),
    "change_language": (
        "Also change the language of an existing installation",
        "Cambiar también el idioma de una instalación existente",
    ),
    "theme": ("Initial theme", "Tema inicial"),
    "preserve": (
        "Existing themes and plugin selections are preserved during upgrades.",
        "Se conservan los temas y las selecciones de plugins existentes al actualizar.",
    ),
    "integration": ("Desktop and terminal", "Escritorio y terminal"),
    "completion": (
        "Enable native Bash completion for lanctl",
        "Activar autocompletado nativo de Bash para lanctl",
    ),
    "completion_help": (
        "Linux uses Bash completion; the .lua / Clink integration is Windows-only.",
        "Linux usa autocompletado de Bash; la integración .lua / Clink es exclusiva de Windows.",
    ),
    "desktop": ("Create a desktop shortcut", "Crear acceso directo en el escritorio"),
    "ipgui": ("Create a LANIP GUI menu shortcut", "Crear acceso a LANIP GUI en el menú"),
    "events": ("Create a LANMON event viewer shortcut", "Crear acceso al visor de eventos LANMON"),
    "access_admin": (
        "Create a LANACCESS administration shortcut",
        "Crear acceso a administración LANACCESS",
    ),
    "remote_account": (
        "Create the first remote service account",
        "Crear la primera cuenta remota del servicio",
    ),
    "first_scan": (
        "Open LANIP to confirm a first scan (no automatic probes)",
        "Abrir LANIP para confirmar el primer escaneo (sin sondeos automáticos)",
    ),
    "open_gui": ("Open LANCTL when finished", "Abrir LANCTL al terminar"),
    "review": ("Ready to install", "Preparado para instalar"),
    "review_help": (
        "Review your selection. The next step installs the DEB and any missing dependencies using APT.",
        "Revisa tu selección. El siguiente paso instala el DEB y las dependencias que falten mediante APT.",
    ),
    "install": ("Installation", "Instalación"),
    "installing": ("Installing packages…", "Instalando paquetes…"),
    "configuring": ("Saving your initial preferences…", "Guardando tus preferencias iniciales…"),
    "service": ("Enabling the monitor service…", "Activando el servicio del monitor…"),
    "remote": ("Creating the first service account…", "Creando la primera cuenta del servicio…"),
    "account": ("Remote service account", "Cuenta remota del servicio"),
    "account_help": (
        "Optional LANACCESS administrator account, separate from your Linux login. Existing accounts are preserved. This does not enable SSH or HTTPS.",
        "Cuenta opcional de administrador LANACCESS, independiente de tu usuario Linux. Las cuentas existentes se conservan. No activa SSH ni HTTPS.",
    ),
    "username": ("Username (3-64 characters)", "Usuario (3-64 caracteres)"),
    "invalid-username": (
        "Use 3-64 characters: start with a letter, then letters, digits, dot, underscore or hyphen.",
        "Usa 3-64 caracteres: empieza por una letra y continúa con letras sin acentos, números, punto, guion o guion bajo.",
    ),
    "password-length": (
        "The password must contain 12-1024 characters.",
        "La contraseña debe tener entre 12 y 1024 caracteres.",
    ),
    "password-mismatch": ("The passwords do not match.", "Las contraseñas no coinciden."),
    "invalid-request": (
        "The account request is invalid. Enter the account details again.",
        "La solicitud de cuenta no es válida. Introduce los datos de nuevo.",
    ),
    "service-account-missing": (
        "The LANCTL service user is missing. Check that the package was installed correctly.",
        "Falta el usuario de servicio LANCTL. Comprueba que el paquete se haya instalado correctamente.",
    ),
    "service-files-missing": (
        "Service files are missing. Check the LANCTL package installation.",
        "Faltan archivos del servicio. Comprueba la instalación del paquete LANCTL.",
    ),
    "service-permission": (
        "Cannot access the service account store. Check its installation and permissions.",
        "No se puede acceder al almacén de cuentas del servicio. Comprueba su instalación y permisos.",
    ),
    "account-error": (
        "The account could not be created. The service store may be unavailable or invalid.",
        "No se ha podido crear la cuenta. El almacén del servicio puede no estar disponible o no ser válido.",
    ),
    "account-cancelled": (
        "Administrator authentication was cancelled. Enter the password again to retry.",
        "Se ha cancelado la autorización administrativa. Introduce la contraseña de nuevo para reintentar.",
    ),
    "account-denied": (
        "Administrator authorization was denied. The account was not created.",
        "Se ha denegado la autorización administrativa. No se ha creado la cuenta.",
    ),
    "account-created": ("Initial service account created.", "Cuenta inicial del servicio creada."),
    "account-preserved": (
        "Existing service accounts were preserved; the password entered here has not replaced them.",
        "Se han conservado las cuentas existentes del servicio; la contraseña introducida aquí no las ha sustituido.",
    ),
    "password": ("Password (12-1024 characters)", "Contraseña (12-1024 caracteres)"),
    "confirmation": ("Confirm password", "Repetir contraseña"),
    "invalid_account": (
        "Check the username, password length and confirmation.",
        "Revisa el usuario, la longitud de la contraseña y su confirmación.",
    ),
    "done": (
        "Installation completed. Click Finish to open the selected interfaces.",
        "Instalación completada. Pulsa Finalizar para abrir las interfaces seleccionadas.",
    ),
    "failed": (
        "Installation did not complete. Details are shown below. You may go back and retry. Packages already installed remain installed.",
        "La instalación no se ha completado. Consulta los detalles. Puedes volver atrás y reintentar. Los paquetes ya instalados permanecen instalados.",
    ),
    "busy": (
        "Wait for the current operation to finish before closing.",
        "Espera a que termine la operación antes de cerrar.",
    ),
    "error": ("Setup error", "Error de instalación"),
    "next": ("Next →", "Siguiente →"),
    "back": ("← Back", "← Atrás"),
    "cancel": ("Cancel", "Cancelar"),
    "finish": ("Finish", "Finalizar"),
    "yes": ("Yes", "Sí"),
    "no": ("No", "No"),
    "location": ("System location", "Ubicación del sistema"),
    "version": ("Version", "Versión"),
    "language_fallback": (
        "Installer language unavailable for the program; English was selected.",
        "El idioma del instalador no está disponible para el programa; se ha seleccionado inglés.",
    ),
}
