"""Asynchronous launcher for a separately packaged GoExport executable."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, QProcess, pyqtSignal


def application_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def find_goexport_executable() -> Path:
    """Find GoExport in supported source and published layouts."""
    override = os.environ.get("GOEXPORT_EXECUTABLE")
    if override:
        candidate = Path(override).expanduser().resolve()
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"GOEXPORT_EXECUTABLE does not exist: {candidate}")

    # Go binaries have no extension on Linux and macOS, while the Windows
    # release is named ``GoExport.exe``.
    executable_name = "GoExport.exe" if sys.platform == "win32" else "GoExport"
    app_dir = application_directory()
    candidates = (
        app_dir / executable_name,
        app_dir / "GoExport" / executable_name,
        app_dir / "dist" / "GoExport-GUI" / executable_name,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    locations = "\n".join(f"  • {candidate}" for candidate in candidates)
    raise FileNotFoundError(
        f"{executable_name} could not be found. Checked:\n" + locations
    )


class GoExportService(QObject):
    """Translate GoExport V2's documented JSON events into Qt signals."""

    progress = pyqtSignal(float, str)
    completed = pyqtSignal(str)
    failed = pyqtSignal(str, str)
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, options: dict[str, Any], parent: QObject | None = None):
        super().__init__(parent)
        self.options = options
        self._buffer = b""
        self._completed = False
        self._failure_reported = False
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read_events)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.errorOccurred.connect(self._process_error)
        self.process.finished.connect(self._process_finished)

    def start(self) -> None:
        executable = find_goexport_executable()
        self.process.setWorkingDirectory(str(executable.parent))
        self.process.start(str(executable), self._arguments())

    def _arguments(self) -> list[str]:
        option = self.options
        arguments = [
            "--json", "record", "-id", option["movie_id"],
            "-f", option["format"], "-out", option["output"],
            "-r", option["resolution"], "-u", option["url"],
            "-api", option["api_url"], "-swf", option["swf_url"],
            "-store", option["store_path"],
            "-theme", option["client_theme_path"],
        ]
        if option["user_id"]:
            arguments.extend(["-uid", option["user_id"]])
        if option["no_outro"]:
            arguments.append("--no-outro")
        elif option["use_outro"]:
            arguments.extend(["--use-outro", option["use_outro"]])
        return arguments

    def _read_events(self) -> None:
        self._buffer += bytes(self.process.readAllStandardOutput())
        lines = self._buffer.split(b"\n")
        self._buffer = lines.pop()
        for line in lines:
            self._handle_event(line.decode("utf-8", errors="replace").strip())

    def _handle_event(self, line: str) -> None:
        if not line:
            return
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            self.log.emit(line)
            return
        event_name = event.get("event")
        if event_name == "progress":
            self.progress.emit(float(event["progress"]), str(event["stage"]))
        elif event_name == "complete":
            self._completed = True
            self.completed.emit(str(event["output"]))
        elif event_name == "error":
            self._report_failure(str(event.get("message", "GoExport failed.")), line)

    def _read_stderr(self) -> None:
        text = bytes(self.process.readAllStandardError()).decode(
            "utf-8", errors="replace"
        ).strip()
        if text:
            self.log.emit(text)

    def _report_failure(self, message: str, detail: str) -> None:
        if not self._failure_reported:
            self._failure_reported = True
            self.failed.emit(message, detail)

    def _process_error(self, _error: QProcess.ProcessError) -> None:
        if not self._completed:
            self._report_failure("Unable to start GoExport.", self.process.errorString())

    def _process_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        self._read_events()
        self._read_stderr()
        if exit_code and not self._completed:
            self._report_failure(
                f"GoExport exited with code {exit_code}.",
                "See details for GoExport output.",
            )
        self.finished.emit()
