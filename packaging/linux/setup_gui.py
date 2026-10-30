"""Unprivileged Qt wizard for the Linux DEB distribution."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QProcessEnvironment, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)
from setup_account import validate_request
from setup_model import (
    PLUGINS,
    THEMES,
    Selection,
    clean_environment,
    install_command,
    load_distribution,
    write_shortcuts,
)


def account_command():
    command = ["/usr/bin/pkexec", sys.executable]
    if not getattr(sys, "frozen", False):
        command.append(str(Path(__file__).resolve()))
    return [*command, "--create-account"]


# Installer translations are intentionally separate from the program language catalogs.
TEXT = {
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


class Installer(QWizard):
    def __init__(self, distribution: Path, metadata: dict):
        super().__init__()
        self.distribution, self.metadata = distribution, metadata
        self.running = False
        self.completed = False
        self.language = "es" if os.environ.get("LANG", "").startswith("es") else "en"
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(740, 600)
        self.resize(850, 690)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage)
        self.pages_by_key = {}
        self.labels = []
        self.checks = {}
        self.queue = []
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        environment = QProcessEnvironment()
        for key, value in clean_environment().items():
            environment.insert(key, value)
        self.process.setProcessEnvironment(environment)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.command_finished)
        self.process.started.connect(self.process_started)
        self.account_input = None
        self.account_output = ""
        self.process.errorOccurred.connect(self.process_error)
        self.make_pages()
        self.retranslate()

    def tr_text(self, key):
        return TEXT[key][self.language == "es"]

    def add_section(self, key):
        page = QWizardPage()
        page.setLayout(QVBoxLayout())
        self.pages_by_key[key] = page
        self.addPage(page)
        return page

    def label(self, page, key):
        label = QLabel()
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.labels.append((label, key))
        page.layout().addWidget(label)
        return label

    def check(self, page, key, checked=False):
        box = QCheckBox()
        box.setChecked(checked)
        self.checks[key] = box
        self.labels.append((box, key))
        page.layout().addWidget(box)
        return box

    def make_pages(self):
        page = self.add_section("welcome")
        self.label(page, "intro")
        self.label(page, "installer_language")
        self.installer_language = QComboBox()
        self.installer_language.addItem("English", "en")
        self.installer_language.addItem("Español", "es")
        self.installer_language.setCurrentIndex(self.language == "es")
        page.layout().addWidget(self.installer_language)
        self.installer_language.currentIndexChanged.connect(self.language_changed)
        page.layout().addStretch()
        page = self.add_section("components")
        for key in ("core", "path"):
            self.check(page, key, True).setEnabled(False)
        self.check(page, "monitor")
        self.check(page, "tools", True)
        self.plugin_group = QGroupBox()
        self.plugin_group.setLayout(QVBoxLayout())
        self.plugin_checks = {}
        for plugin in PLUGINS:
            box = QCheckBox()
            box.setChecked(True)
            self.plugin_checks[plugin] = box
            self.plugin_group.layout().addWidget(box)
        page.layout().addWidget(self.plugin_group)
        self.label(page, "components_help")
        page = self.add_section("preferences")
        self.label(page, "program_language")
        self.program_language = QComboBox()
        for entry in self.metadata["languages"]:
            self.program_language.addItem(entry["nativeName"], entry["code"])
        self.program_language.setCurrentIndex(max(0, self.program_language.findData(self.language)))
        page.layout().addWidget(self.program_language)
        self.fallback = self.label(page, "language_fallback")
        self.fallback.hide()
        self.check(page, "change_language")
        self.label(page, "theme")
        self.theme = QComboBox()
        self.theme.addItems(THEMES)
        page.layout().addWidget(self.theme)
        self.swatch = QLabel("LANCTL    ·    192.168.1.1    ·    ● Online")
        self.swatch.setMinimumHeight(95)
        self.swatch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page.layout().addWidget(self.swatch)
        self.theme.currentIndexChanged.connect(self.theme_changed)
        self.theme_changed()
        self.label(page, "preserve")
        page.layout().addStretch()
        page = self.add_section("integration")
        self.check(page, "completion", True)
        self.label(page, "completion_help")
        for key in ("desktop", "ipgui", "events", "access_admin", "remote_account", "first_scan"):
            self.check(page, key)
        self.check(page, "open_gui", True)
        page.layout().addStretch()
        page = self.add_section("account")
        self.label(page, "account_help")
        self.account_fields = {}
        for key in ("username", "password", "confirmation"):
            self.label(page, key)
            field = QLineEdit()
            field.setMaxLength(64 if key == "username" else 1024)
            if key != "username":
                field.setEchoMode(QLineEdit.EchoMode.Password)
            self.account_fields[key] = field
            page.layout().addWidget(field)
        page.layout().addStretch()
        page = self.add_section("review")
        self.label(page, "review_help")
        self.summary = QPlainTextEdit()
        self.summary.setReadOnly(True)
        page.layout().addWidget(self.summary)
        page = self.add_section("install")
        self.status = QLabel()
        self.status.setWordWrap(True)
        page.layout().addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        page.layout().addWidget(self.progress)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(5000)
        page.layout().addWidget(self.log)
        page.isComplete = lambda: self.completed
        self.currentIdChanged.connect(self.page_changed)

    def theme_changed(self):
        colors = {
            "graphite": ("#20292e", "#b6f22d"),
            "midnight": ("#111b34", "#7fb6ff"),
            "forest": ("#142b23", "#86d99e"),
            "violet": ("#2a203b", "#d7a0ff"),
            "light": ("#f1f4f7", "#345a0a"),
        }
        bg, fg = colors[self.theme.currentText()]
        self.swatch.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;font-size:20px")

    def language_changed(self):
        self.language = self.installer_language.currentData()
        index = self.program_language.findData(self.language)
        self.fallback.setVisible(index < 0)
        self.program_language.setCurrentIndex(
            index if index >= 0 else self.program_language.findData("en")
        )
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(f"{self.tr_text('title')} · {self.metadata['version']}")
        for key, page in self.pages_by_key.items():
            page.setTitle(self.tr_text(key))
        for label, key in self.labels:
            label.setText(self.tr_text(key))
        self.plugin_group.setTitle(self.tr_text("plugins"))
        for plugin, box in self.plugin_checks.items():
            box.setText(PLUGINS[plugin][self.language == "es"])
        for button, key in (
            (QWizard.WizardButton.NextButton, "next"),
            (QWizard.WizardButton.BackButton, "back"),
            (QWizard.WizardButton.CancelButton, "cancel"),
            (QWizard.WizardButton.FinishButton, "finish"),
        ):
            self.setButtonText(button, self.tr_text(key))

    def selection(self):
        values = {
            key: box.isChecked()
            for key, box in self.checks.items()
            if key not in {"core", "path", "tools"}
        }
        return Selection(
            language=self.program_language.currentData(),
            theme=self.theme.currentText(),
            plugins=[plugin for plugin, box in self.plugin_checks.items() if box.isChecked()],
            network_tools=self.checks["tools"].isChecked(),
            **values,
        )

    def page_changed(self, _page_id):
        if self.currentPage() == self.pages_by_key["account"]:
            for field in self.account_fields.values():
                field.setEnabled(self.checks["remote_account"].isChecked())
        if self.currentPage() == self.pages_by_key["review"]:
            selection = self.selection()
            lines = [
                f"{self.tr_text('version')}: {self.metadata['version']} ({self.metadata['arch']})",
                f"{self.tr_text('location')}: /opt/lanctl",
                f"{self.tr_text('program_language')}: {self.program_language.currentText()}",
                f"{self.tr_text('theme')}: {selection.theme}",
                f"{self.tr_text('plugins')}: {len(selection.plugins)} / {len(PLUGINS)}",
            ]
            lines += [
                f"{self.tr_text(key)}: {self.tr_text('yes' if box.isChecked() else 'no')}"
                for key, box in self.checks.items()
                if key not in {"core", "path"}
            ]
            self.summary.setPlainText("\n".join(lines))
        elif self.currentPage() == self.pages_by_key["install"] and not self.running:
            self.start_installation()

    def start_installation(self):
        self.completed = False
        self.running = True
        self.log.clear()
        self.progress.setRange(0, 0)
        self.selected = self.selection()
        if self.selected.remote_account and not self.valid_account():
            self.fail(self.tr_text("invalid_account"))
            return
        self.button(QWizard.WizardButton.BackButton).setEnabled(False)
        self.button(QWizard.WizardButton.CancelButton).setEnabled(False)
        self.pages_by_key["install"].completeChanged.emit()
        package = self.distribution / self.metadata["package"]
        self.queue = [
            ("installing", install_command(package, self.selected)),
            ("configuring", self.selected.defaults_command()),
        ]
        if self.selected.monitor:
            self.queue.append(
                (
                    "service",
                    [
                        "/usr/bin/pkexec",
                        "/usr/bin/systemctl",
                        "enable",
                        "--now",
                        "lanctl-monitor.service",
                    ],
                )
            )
        if self.selected.remote_account:
            self.account_input = json.dumps(
                {key: field.text() for key, field in self.account_fields.items()},
                ensure_ascii=False,
            ).encode()
            self.queue.append(("remote", account_command()))
        self.next_command()

    def next_command(self):
        if not self.queue:
            try:
                write_shortcuts(self.selected, Path.home())
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                self.fail(str(error))
                return
            self.running = False
            self.completed = True
            self.status.setText(self.tr_text("done"))
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
            self.pages_by_key["install"].completeChanged.emit()
            return
        key, command = self.queue.pop(0)
        self.current_operation = key
        self.account_output = ""
        self.status.setText(self.tr_text(key))
        self.log.appendPlainText("\n" + self.tr_text(key))
        self.process.start(command[0], command[1:])

    def valid_account(self):
        try:
            validate_request({key: field.text() for key, field in self.account_fields.items()})
        except ValueError as error:
            self.account_validation_error = getattr(error, "code", "invalid_account")
            return False
        return True

    def validateCurrentPage(self):
        if (
            self.currentPage() == self.pages_by_key["account"]
            and self.checks["remote_account"].isChecked()
            and not self.valid_account()
        ):
            QMessageBox.warning(
                self, self.tr_text("error"), self.tr_text(self.account_validation_error)
            )
            return False
        return True

    def process_started(self):
        if self.current_operation == "remote" and self.account_input is not None:
            self.process.write(self.account_input)
            self.process.closeWriteChannel()
            self.account_input = None
            for field in self.account_fields.values():
                if field.echoMode() == QLineEdit.EchoMode.Password:
                    field.clear()

    def read_output(self):
        text = bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        if self.current_operation == "remote":
            self.account_output = (self.account_output + text)[-16384:]
            return
        self.log.insertPlainText(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def command_finished(self, code, status):
        self.read_output()
        if not self.running:
            return
        if code != 0 or status != QProcess.ExitStatus.NormalExit:
            if self.current_operation == "remote":
                try:
                    result = json.loads(self.account_output)
                    reason = result.get("error", "account-error")
                except (ValueError, AttributeError):
                    reason = (
                        "account-cancelled"
                        if code == 126
                        else "account-denied"
                        if code == 127
                        else "account-error"
                    )
                if reason not in TEXT:
                    reason = "account-error"
                self.fail(self.tr_text(reason) + f" (Exit: {code})")
            else:
                self.fail(f"Exit: {code}")
        else:
            if self.current_operation == "remote":
                try:
                    result = json.loads(self.account_output)
                except ValueError:
                    result = {}
                if result.get("created") is True:
                    self.log.appendPlainText(self.tr_text("account-created"))
                elif result.get("preservedExistingUsers") is True:
                    self.log.appendPlainText(self.tr_text("account-preserved"))
                else:
                    self.fail(self.tr_text("account-error"))
                    return
            self.next_command()

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.fail(self.process.errorString())

    def fail(self, detail):
        self.running = False
        self.queue.clear()
        self.account_input = None
        self.status.setText(self.tr_text("failed"))
        self.log.appendPlainText(detail)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.button(QWizard.WizardButton.BackButton).setEnabled(True)
        self.button(QWizard.WizardButton.CancelButton).setEnabled(True)

    def reject(self):
        if self.running:
            QMessageBox.information(self, self.tr_text("title"), self.tr_text("busy"))
            return
        super().reject()

    def accept(self):
        if not self.completed:
            return
        command = None
        if self.selected.first_scan:
            command = ["/opt/lanctl/lanctl", "post-install", "--first-scan"]
        elif self.selected.open_gui:
            command = ["/opt/lanctl/lanctl", "--gui"]
        if command:
            try:
                subprocess.Popen(
                    command,
                    env=clean_environment(),
                    start_new_session=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError as error:
                QMessageBox.warning(self, self.tr_text("error"), str(error))
                return
        super().accept()


def main():
    parser = argparse.ArgumentParser(description="LANCTL Linux setup")
    parser.add_argument("--distribution", type=Path)
    parser.add_argument("--create-account", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--check", action="store_true", help="Validate package without installing")
    args = parser.parse_args()
    if args.create_account:
        from setup_account import main as create_account

        return create_account()
    if args.distribution is None:
        parser.error("--distribution is required")
    try:
        metadata = load_distribution(args.distribution.resolve())
        if args.check:
            print(f"LANCTL {metadata['version']} {metadata['arch']}: package verified")
            return 0
        app = QApplication(sys.argv[:1])
        if os.geteuid() == 0:
            QMessageBox.critical(
                None,
                "LANCTL",
                "Run setup as your normal desktop user, without sudo.\nEjecuta el instalador con tu usuario normal, sin sudo.",
            )
            return 2
        for required in ("apt-get", "dpkg-deb", "pkexec", "xdg-user-dir"):
            if not shutil.which(required):
                QMessageBox.critical(
                    None, "LANCTL", f"Missing dependency / Dependencia ausente: {required}"
                )
                return 2
        app.setStyle("Fusion")
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#648d16"))
        app.setPalette(palette)
        wizard = Installer(args.distribution.resolve(), metadata)
        wizard.show()
        return app.exec()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"LANCTL Linux setup: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
