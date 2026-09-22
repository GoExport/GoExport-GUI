"""Main window for GoExport GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from goexport_gui.browser_dialog import BrowserDialog
from goexport_gui.browser_picker import BrowserMatch, PickerField
from goexport_gui.presets import load_presets
from goexport_gui.service import GoExportService
from ansi2html import Ansi2HTMLConverter

STAGE_NAMES = {
    "preparing": "Preparing dependencies…",
    "recording": "Recording video…",
    "muxing": "Exporting video…",
    "outro": "Appending outro…",
    "finalizing": "Finalizing…",
}

ASSET_DIR = Path(__file__).resolve().parent / "resources"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._presets = load_presets()
        self._service: GoExportService | None = None
        self._ansi_converter = Ansi2HTMLConverter(inline=True)
        self.setWindowTitle("GoExport")
        self.resize(680, 660)
        self.setMinimumSize(600, 540)
        self._build_ui()
        self._apply_preset(0)

    def _build_ui(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        self.setCentralWidget(scroll)

        title = QLabel()
        title.setObjectName("brandLogo")
        logo = QPixmap(str(ASSET_DIR / "goexport-logo.svg"))
        if logo.isNull():
            title.setText("GoExport")
        else:
            title.setPixmap(
                logo.scaled(
                    330,
                    60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        title.setAccessibleName("GoExport")
        title.setFixedHeight(60)
        subtitle = QLabel(
            "Export a GoAnimate video through your local Wrapper-compatible server."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        primary = QFrame()
        primary.setObjectName("card")
        form = QFormLayout(primary)
        form.setContentsMargins(18, 18, 18, 18)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        self.preset = QComboBox()
        self.preset.addItems([preset.name for preset in self._presets])
        self._configure_combo_popup(self.preset)
        self.preset.currentIndexChanged.connect(self._apply_preset)
        self.movie_id = QLineEdit()
        self.movie_id.setPlaceholderText("Enter the video ID")
        self.browse_video = QPushButton("Browse\u2026")
        self.browse_video.clicked.connect(
            lambda _checked=False: self._browse_for_id("video")
        )
        movie_row = QHBoxLayout()
        movie_row.setContentsMargins(0, 0, 0, 0)
        movie_row.addWidget(self.movie_id, 1)
        movie_row.addWidget(self.browse_video)
        self.user_id = QLineEdit()
        self.user_id.setPlaceholderText("Enter the user ID")
        self.browse_user = QPushButton("Browse\u2026")
        self.browse_user.clicked.connect(
            lambda _checked=False: self._browse_for_id("user")
        )
        user_row = QHBoxLayout()
        user_row.setContentsMargins(0, 0, 0, 0)
        user_row.addWidget(self.user_id, 1)
        user_row.addWidget(self.browse_user)
        form.addRow("Preset", self.preset)
        form.addRow("Video ID", movie_row)
        form.addRow("User ID", user_row)
        layout.addWidget(primary)

        self.advanced_toggle = self._section_button("Advanced")
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        layout.addWidget(self.advanced_toggle)
        self.advanced_panel = self._build_advanced_panel()
        self.advanced_panel.setVisible(False)
        layout.addWidget(self.advanced_panel)

        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 16, 18, 16)
        status_layout.setSpacing(10)
        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        status_layout.addWidget(self.status)
        status_layout.addWidget(self.progress)
        layout.addWidget(status_card)

        self.export_button = QPushButton("Export Video")
        self.export_button.setObjectName("primaryButton")
        self.export_button.setDefault(True)
        self.export_button.setMinimumHeight(42)
        self.export_button.clicked.connect(self._start_export)
        self.cancel_export_button = QPushButton("Cancel")
        self.cancel_export_button.setMinimumHeight(42)
        self.cancel_export_button.setEnabled(False)
        self.cancel_export_button.clicked.connect(self._cancel_export)
        export_actions = QHBoxLayout()
        export_actions.setContentsMargins(0, 0, 0, 0)
        export_actions.setSpacing(10)
        export_actions.addWidget(self.export_button, 1)
        export_actions.addWidget(self.cancel_export_button)
        layout.addLayout(export_actions)

        self.log_toggle = self._section_button("Show details")
        self.log_toggle.toggled.connect(self._toggle_log)
        layout.addWidget(self.log_toggle)
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.document().setMaximumBlockCount(500)
        self.log_panel.setMinimumHeight(150)
        self.log_panel.setVisible(False)
        layout.addWidget(self.log_panel)
        layout.addStretch(1)

    def _section_button(self, text: str) -> QToolButton:
        button = QToolButton(text=text)
        button.setCheckable(True)
        button.setArrowType(Qt.ArrowType.RightArrow)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return button

    def _configure_combo_popup(self, combo: QComboBox) -> None:
        """Remove the dark native frame around Qt's separate popup window."""
        popup = combo.view().window()
        popup.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        popup.setObjectName("comboPopup")

    def _build_advanced_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("card")
        form = QFormLayout(panel)
        form.setContentsMargins(18, 18, 18, 18)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        self.output = QLineEdit(str(Path.cwd() / "final_output"))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._choose_output)
        output_row = QHBoxLayout()
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.addWidget(self.output)
        output_row.addWidget(browse)
        self.video_format = QComboBox()
        self.video_format.addItems(["mp4", "mov", "mkv"])
        self._configure_combo_popup(self.video_format)
        self.resolution = QLineEdit()
        self.url = QLineEdit()
        self.api_url = QLineEdit()
        self.swf_url = QLineEdit()
        self.store_path = QLineEdit()
        self.client_theme_path = QLineEdit()
        self.additional_flashvars = QLineEdit()
        self.additional_flashvars.setPlaceholderText("name=value&another=value")
        self.replacements = QPlainTextEdit()
        self.replacements.setPlaceholderText("owner_id={user_id}\nname=value")
        self.replacements.setMaximumHeight(90)
        self.use_outro = QLineEdit()
        self.chrome_path = QLineEdit()
        self.chromedriver_path = QLineEdit()
        self.flash_plugin_path = QLineEdit()
        self.flash_plugin_version = QLineEdit()
        self.ffmpeg_path = QLineEdit()
        self.no_outro = QComboBox()
        self.no_outro.addItems(["Include outro", "No outro"])
        self._configure_combo_popup(self.no_outro)
        self.no_wide = QCheckBox("Disable widescreen mode")
        self.no_wide.setToolTip(
            "Pass --no-wide to use GoAnimate's standard aspect mode."
        )
        self.electron = QCheckBox("Connect to an Electron browser")
        self.electron.setToolTip(
            "Pass --electron to hook into an Electron browser on remote debugging port 9222."
        )
        self.no_flash_timeout = QCheckBox("Wait indefinitely for Flash")
        self.no_flash_timeout.setToolTip(
            "Pass --no-flash-timeout instead of stopping when the Flash player takes too long to load."
        )
        self.verbose = QCheckBox("Enable verbose logging")
        self.verbose.setToolTip("Include GoExport debug messages in the details log.")
        form.addRow("Output", output_row)
        form.addRow("Format", self.video_format)
        form.addRow("Resolution", self.resolution)
        form.addRow("Server URL", self.url)
        form.addRow("API URL", self.api_url)
        form.addRow("SWF URL", self.swf_url)
        form.addRow("Store path", self.store_path)
        form.addRow("Theme path", self.client_theme_path)
        form.addRow("Additional Flashvars", self.additional_flashvars)
        form.addRow("Replacements", self.replacements)
        form.addRow("Outro file", self.use_outro)
        form.addRow("Outro", self.no_outro)
        form.addRow("Display mode", self.no_wide)
        form.addRow("Browser integration", self.electron)
        form.addRow("Flash timeout", self.no_flash_timeout)
        form.addRow("Logging", self.verbose)
        form.addRow("Chromium executable", self.chrome_path)
        form.addRow("ChromeDriver executable", self.chromedriver_path)
        form.addRow("Flash plugin", self.flash_plugin_path)
        form.addRow("Flash plugin version", self.flash_plugin_version)
        form.addRow("FFmpeg executable", self.ffmpeg_path)
        return panel

    def _toggle_advanced(self, shown: bool) -> None:
        self.advanced_panel.setVisible(shown)
        self.advanced_toggle.setArrowType(
            Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow
        )

    def _toggle_log(self, shown: bool) -> None:
        self.log_panel.setVisible(shown)
        self.log_toggle.setArrowType(
            Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow
        )

    def _apply_preset(self, index: int) -> None:
        if index < 0:
            return
        values = self._presets[index].values
        fields = (
            (self.resolution, "resolution", "1280x720"),
            (self.url, "url", ""),
            (self.api_url, "api_url", ""),
            (self.swf_url, "swf_url", ""),
            (self.store_path, "store_path", ""),
            (self.client_theme_path, "client_theme_path", ""),
            (self.use_outro, "use_outro", ""),
        )
        for widget, name, default in fields:
            widget.setText(str(values.get(name, default)))
        self.additional_flashvars.setText(str(values.get("additional_flashvars", "")))
        replacements = values.get("replacements", {})
        if isinstance(replacements, dict):
            self.replacements.setPlainText(
                "\n".join(f"{name}={value}" for name, value in replacements.items())
            )
        else:
            self.replacements.setPlainText(str(replacements))
        self.video_format.setCurrentText(str(values.get("format", "mp4")))
        self.no_outro.setCurrentIndex(1 if values.get("no_outro", False) else 0)
        self.no_wide.setChecked(bool(values.get("no_wide", False)))
        self.electron.setChecked(bool(values.get("electron", False)))
        self.no_flash_timeout.setChecked(bool(values.get("no_flash_timeout", False)))
        self.verbose.setChecked(bool(values.get("verbose", False)))
        picker_config = self._presets[index].browser_picker
        for field_name, button in (
            ("video", self.browse_video),
            ("user", self.browse_user),
        ):
            enabled = picker_config is not None and picker_config.supports(field_name)
            button.setEnabled(enabled)
            button.setToolTip(
                f"Browse this preset's site and select a {field_name}."
                if enabled
                else f"This preset has no {field_name} URL rule configured."
            )

    def _browse_for_id(self, field_name: PickerField) -> None:
        index = self.preset.currentIndex()
        if index < 0:
            return
        config = self._presets[index].browser_picker
        if config is None or not config.supports(field_name):
            return
        dialog = BrowserDialog(config, field_name, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        match = dialog.selected_match
        if match is None:
            return
        self._apply_browser_match(match)

    def _apply_browser_match(self, match: BrowserMatch) -> None:
        if match.field == "video":
            self.movie_id.setText(match.value)
            self.movie_id.setFocus()
        else:
            self.user_id.setText(match.value)
            self.user_id.setFocus()

    def _choose_output(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Choose output filename",
            self.output.text(),
            "Videos (*.mp4 *.mov *.mkv)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if filename:
            self.output.setText(filename)

    def _options(self) -> dict[str, Any] | None:
        movie_id = self.movie_id.text().strip()
        if not movie_id:
            QMessageBox.warning(
                self, "Video ID required", "Enter the video ID to export."
            )
            self.movie_id.setFocus()
            return None
        resolution = self.resolution.text().strip().lower()
        try:
            width, height = (int(value) for value in resolution.split("x"))
            if width <= 0 or height <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self, "Invalid resolution", "Use a resolution such as 1280x720."
            )
            self.resolution.setFocus()
            return None
        replacements = []
        for line_number, line in enumerate(
            self.replacements.toPlainText().splitlines(), start=1
        ):
            entry = line.strip()
            if not entry:
                continue
            if "=" not in entry:
                QMessageBox.warning(
                    self,
                    "Invalid replacement",
                    f"Replacement line {line_number} must use NAME=VALUE.",
                )
                self.replacements.setFocus()
                return None
            replacements.append(entry)
        return {
            "movie_id": movie_id,
            "user_id": self.user_id.text().strip() or None,
            "format": self.video_format.currentText(),
            "output": self.output.text().strip() or "final_output",
            "resolution": f"{width}x{height}",
            "url": self.url.text().strip(),
            "api_url": self.api_url.text().strip(),
            "swf_url": self.swf_url.text().strip(),
            "store_path": self.store_path.text().strip(),
            "client_theme_path": self.client_theme_path.text().strip(),
            "additional_flashvars": self.additional_flashvars.text().strip(),
            "replacements": replacements,
            "no_outro": self.no_outro.currentIndex() == 1,
            "use_outro": self.use_outro.text().strip(),
            "no_wide": self.no_wide.isChecked(),
            "electron": self.electron.isChecked(),
            "no_flash_timeout": self.no_flash_timeout.isChecked(),
            "verbose": self.verbose.isChecked(),
            "chrome_path": self.chrome_path.text().strip(),
            "chromedriver_path": self.chromedriver_path.text().strip(),
            "flash_plugin_path": self.flash_plugin_path.text().strip(),
            "flash_plugin_version": self.flash_plugin_version.text().strip(),
            "ffmpeg_path": self.ffmpeg_path.text().strip(),
        }

    def _start_export(self) -> None:
        options = self._options()
        if options is None:
            return
        self.log_panel.clear()
        self.progress.setValue(0)
        self.status.setText(STAGE_NAMES["preparing"])
        self.export_button.setEnabled(False)
        self._service = GoExportService(options, self)
        self._service.started.connect(self._export_started)
        self._service.progress.connect(self._on_progress)
        self._service.log.connect(self._append_log)
        self._service.completed.connect(self._on_complete)
        self._service.cancelled.connect(self._on_cancelled)
        self._service.failed.connect(self._on_failed)
        self._service.finished.connect(self._export_finished)
        try:
            self._service.start()
        except Exception as error:
            self._on_failed(str(error), repr(error))
            self._export_finished()

    def _append_log(self, text: str) -> None:
        """Append terminal output while preserving ANSI colors in the details pane."""
        html = self._ansi_converter.convert(text, full=False)
        cursor = self.log_panel.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        # Do not let the last ANSI span bleed into the following log line.
        cursor.setCharFormat(QTextCharFormat())
        cursor.insertBlock()
        self.log_panel.setTextCursor(cursor)
        self.log_panel.ensureCursorVisible()

    def _export_started(self) -> None:
        self.cancel_export_button.setEnabled(True)

    def _cancel_export(self) -> None:
        if self._service is None or not self._service.cancel():
            return
        self.cancel_export_button.setEnabled(False)
        self.status.setText("Cancelling export...")

    def _on_progress(self, value: float, stage: str) -> None:
        self.progress.setValue(round(value))
        self.status.setText(
            STAGE_NAMES.get(stage, stage.replace("_", " ").title() + "…")
        )

    def _on_complete(self, output: str) -> None:
        self.progress.setValue(100)
        self.status.setText(f"Complete — {output}")

    def _on_cancelled(self) -> None:
        self.status.setText("Export cancelled")

    def _on_failed(self, message: str, detail: str) -> None:
        self.status.setText("Export failed")
        self._append_log(detail)
        QMessageBox.critical(
            self,
            "Export failed",
            message + "\n\nOpen details for troubleshooting information.",
        )

    def _export_finished(self) -> None:
        self.export_button.setEnabled(True)
        self.cancel_export_button.setEnabled(False)
        if self._service is not None:
            self._service.deleteLater()
        self._service = None
