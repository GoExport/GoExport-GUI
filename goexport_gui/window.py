"""Main window for GoExport GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QProgressBar, QPlainTextEdit,
    QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)

from goexport_gui.presets import load_presets
from goexport_gui.service import GoExportService

STAGE_NAMES = {
    "preparing": "Preparing dependencies…", "recording": "Recording video…",
    "muxing": "Exporting video…", "outro": "Appending outro…",
    "finalizing": "Finalizing…",
}

ASSET_DIR = Path(__file__).resolve().parent / "resources"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._presets = load_presets()
        self._service: GoExportService | None = None
        self.setWindowTitle("GoExport GUI")
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
                    330, 60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        title.setAccessibleName("GoExport")
        title.setFixedHeight(60)
        subtitle = QLabel("Export a GoAnimate video through your local Wrapper-compatible server.")
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
        self.user_id = QLineEdit()
        self.user_id.setPlaceholderText("Enter the user ID")
        form.addRow("Preset", self.preset)
        form.addRow("Video ID", self.movie_id)
        form.addRow("User ID", self.user_id)
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
        layout.addWidget(self.export_button)

        self.log_toggle = self._section_button("Show details")
        self.log_toggle.toggled.connect(self._toggle_log)
        layout.addWidget(self.log_toggle)
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setMaximumBlockCount(500)
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
        self.use_outro = QLineEdit()
        self.chrome_path = QLineEdit()
        self.chromedriver_path = QLineEdit()
        self.flash_plugin_path = QLineEdit()
        self.ffmpeg_path = QLineEdit()
        self.no_outro = QComboBox()
        self.no_outro.addItems(["Include outro", "No outro"])
        self._configure_combo_popup(self.no_outro)
        form.addRow("Output", output_row)
        form.addRow("Format", self.video_format)
        form.addRow("Resolution", self.resolution)
        form.addRow("Server URL", self.url)
        form.addRow("API URL", self.api_url)
        form.addRow("SWF URL", self.swf_url)
        form.addRow("Store path", self.store_path)
        form.addRow("Theme path", self.client_theme_path)
        form.addRow("Outro file", self.use_outro)
        form.addRow("Outro", self.no_outro)
        form.addRow("Chromium executable", self.chrome_path)
        form.addRow("ChromeDriver executable", self.chromedriver_path)
        form.addRow("Flash plugin", self.flash_plugin_path)
        form.addRow("FFmpeg executable", self.ffmpeg_path)
        return panel

    def _toggle_advanced(self, shown: bool) -> None:
        self.advanced_panel.setVisible(shown)
        self.advanced_toggle.setArrowType(Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow)

    def _toggle_log(self, shown: bool) -> None:
        self.log_panel.setVisible(shown)
        self.log_toggle.setArrowType(Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow)

    def _apply_preset(self, index: int) -> None:
        if index < 0:
            return
        values = self._presets[index].values
        fields = (
            (self.resolution, "resolution", "1280x720"), (self.url, "url", ""),
            (self.api_url, "api_url", ""), (self.swf_url, "swf_url", ""),
            (self.store_path, "store_path", ""),
            (self.client_theme_path, "client_theme_path", ""),
            (self.use_outro, "use_outro", ""),
        )
        for widget, name, default in fields:
            widget.setText(str(values.get(name, default)))
        self.video_format.setCurrentText(str(values.get("format", "mp4")))
        self.no_outro.setCurrentIndex(1 if values.get("no_outro", False) else 0)

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
            QMessageBox.warning(self, "Video ID required", "Enter the video ID to export.")
            self.movie_id.setFocus()
            return None
        resolution = self.resolution.text().strip().lower()
        try:
            width, height = (int(value) for value in resolution.split("x"))
            if width <= 0 or height <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid resolution", "Use a resolution such as 1280x720.")
            self.resolution.setFocus()
            return None
        return {
            "movie_id": movie_id, "user_id": self.user_id.text().strip() or None,
            "format": self.video_format.currentText(),
            "output": self.output.text().strip() or "final_output",
            "resolution": f"{width}x{height}", "url": self.url.text().strip(),
            "api_url": self.api_url.text().strip(), "swf_url": self.swf_url.text().strip(),
            "store_path": self.store_path.text().strip(),
            "client_theme_path": self.client_theme_path.text().strip(),
            "no_outro": self.no_outro.currentIndex() == 1,
            "use_outro": self.use_outro.text().strip(),
            "chrome_path": self.chrome_path.text().strip(),
            "chromedriver_path": self.chromedriver_path.text().strip(),
            "flash_plugin_path": self.flash_plugin_path.text().strip(),
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
        self._service.progress.connect(self._on_progress)
        self._service.log.connect(self.log_panel.appendPlainText)
        self._service.completed.connect(self._on_complete)
        self._service.failed.connect(self._on_failed)
        self._service.finished.connect(self._export_finished)
        try:
            self._service.start()
        except Exception as error:
            self._on_failed(str(error), repr(error))
            self._export_finished()

    def _on_progress(self, value: float, stage: str) -> None:
        self.progress.setValue(round(value))
        self.status.setText(STAGE_NAMES.get(stage, stage.replace("_", " ").title() + "…"))

    def _on_complete(self, output: str) -> None:
        self.progress.setValue(100)
        self.status.setText(f"Complete — {output}")

    def _on_failed(self, message: str, detail: str) -> None:
        self.status.setText("Export failed")
        self.log_panel.appendPlainText(detail)
        QMessageBox.critical(self, "Export failed", message + "\n\nOpen details for troubleshooting information.")

    def _export_finished(self) -> None:
        self.export_button.setEnabled(True)
        if self._service is not None:
            self._service.deleteLater()
        self._service = None
