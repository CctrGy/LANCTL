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
from setup_messages import TEXT
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
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        environment = QProcessEnvironment()
        for key, value in clean_environment().items():
            environment.insert(key, value)
        self.process.setProcessEnvironment(environment)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
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
        self.check(page, "advanced").toggled.connect(self.advanced_changed)
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
        self.checks["remote_account"].setVisible(False)
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
            if key not in {"core", "path", "tools", "advanced"}
        }
        values["remote_account"] = values["remote_account"] and self.checks["advanced"].isChecked()
        return Selection(
            language=self.program_language.currentData(),
            theme=self.theme.currentText(),
            plugins=[plugin for plugin, box in self.plugin_checks.items() if box.isChecked()],
            network_tools=self.checks["tools"].isChecked(),
            **values,
        )

    def advanced_changed(self, enabled):
        self.checks["remote_account"].setVisible(enabled)
        if not enabled:
            self.account_input = None
            for field in self.account_fields.values():
                if field.echoMode() == QLineEdit.EchoMode.Password:
                    field.clear()

    def nextId(self):
        if (
            self.pages_by_key.get("integration") is not None
            and self.currentPage() is self.pages_by_key["integration"]
            and (
                not self.checks["advanced"].isChecked()
                or not self.checks["remote_account"].isChecked()
            )
        ):
            return next(
                page_id
                for page_id in self.pageIds()
                if self.page(page_id) is self.pages_by_key["review"]
            )
        return super().nextId()

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
                f"{self.tr_text(key)}: {self.tr_text('yes' if (selection.remote_account if key == 'remote_account' else box.isChecked()) else 'no')}"
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

    def read_error(self):
        text = bytes(self.process.readAllStandardError()).decode("utf-8", "replace")
        if self.current_operation == "remote":
            # The account protocol is JSON on stdout only. Authentication/Qt
            # diagnostics must neither corrupt it nor enter the installer log.
            return
        self.log.insertPlainText(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def command_finished(self, code, status):
        self.read_output()
        self.read_error()
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
