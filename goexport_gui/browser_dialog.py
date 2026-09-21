"""Embedded browser used to select a video or user ID."""

from __future__ import annotations

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from goexport_gui.browser_picker import (
    BrowserMatch,
    BrowserPickerConfig,
    normalize_browser_url,
)


class BrowserPage(QWebEnginePage):
    """Keep links requesting a new window inside the picker."""

    def createWindow(
        self, _window_type: QWebEnginePage.WebWindowType
    ) -> QWebEnginePage:
        return self


class BrowserDialog(QDialog):
    """Browse a configured site and return an ID from a matching URL."""

    def __init__(self, config: BrowserPickerConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.selected_match: BrowserMatch | None = None
        self._current_match: BrowserMatch | None = None

        self.setWindowTitle("Browse for a GoExport ID")
        self.resize(1040, 760)
        self.setMinimumSize(720, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        navigation = QHBoxLayout()
        navigation.setSpacing(8)
        self.back_button = QPushButton("Back")
        self.forward_button = QPushButton("Forward")
        self.reload_button = QPushButton("Reload")
        self.url_field = QLineEdit()
        self.url_field.setObjectName("browserUrl")
        self.url_field.setPlaceholderText("Enter a web address")
        navigation.addWidget(self.back_button)
        navigation.addWidget(self.forward_button)
        navigation.addWidget(self.reload_button)
        navigation.addWidget(self.url_field, 1)
        layout.addLayout(navigation)

        self.browser = QWebEngineView()
        self.browser_profile = QWebEngineProfile(self)
        self.browser.setPage(BrowserPage(self.browser_profile, self.browser))
        layout.addWidget(self.browser, 1)

        footer = QHBoxLayout()
        self.match_status = QLabel("Open a configured video or user page.")
        self.match_status.setObjectName("browserStatus")
        self.match_status.setWordWrap(True)
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("OK")
        self.ok_button.setObjectName("primaryButton")
        self.ok_button.setDefault(True)
        self.ok_button.setEnabled(False)
        footer.addWidget(self.match_status, 1)
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.ok_button)
        layout.addLayout(footer)

        self.back_button.clicked.connect(self.browser.back)
        self.forward_button.clicked.connect(self.browser.forward)
        self.reload_button.clicked.connect(self.browser.reload)
        self.url_field.returnPressed.connect(self._navigate)
        self.browser.urlChanged.connect(self._url_changed)
        self.browser.loadFinished.connect(self._update_navigation_buttons)
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self._accept_match)

        self._update_navigation_buttons()
        self.browser.setUrl(QUrl(config.start_url))

    def _navigate(self) -> None:
        address = self.url_field.text().strip()
        normalized_url = normalize_browser_url(address)
        if normalized_url is None:
            self._show_no_match("Only HTTP and HTTPS addresses can be opened.")
            return
        self.browser.setUrl(QUrl(normalized_url))

    def _url_changed(self, url: QUrl) -> None:
        address = url.toString()
        self.url_field.setText(address)
        self._update_navigation_buttons()
        if url.scheme().lower() not in {"http", "https"}:
            self._show_no_match("Open a configured video or user page.")
            return

        matches = self.config.matches(address)
        if len(matches) == 1:
            self._current_match = matches[0]
            label = "Video ID" if matches[0].field == "video" else "User ID"
            self.match_status.setText(f"{label}: {matches[0].value}")
            self.ok_button.setEnabled(True)
        elif len(matches) > 1:
            self._show_no_match(
                "This address matches both video and user rules. Update the preset regexes."
            )
        else:
            self._show_no_match("This page is not a configured video or user page.")

    def _show_no_match(self, message: str) -> None:
        self._current_match = None
        self.match_status.setText(message)
        self.ok_button.setEnabled(False)

    def _update_navigation_buttons(self, _loaded: bool | None = None) -> None:
        history = self.browser.history()
        self.back_button.setEnabled(history.canGoBack())
        self.forward_button.setEnabled(history.canGoForward())

    def _accept_match(self) -> None:
        if self._current_match is None:
            return
        self.selected_match = self._current_match
        self.accept()
