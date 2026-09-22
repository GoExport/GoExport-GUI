from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

GUI_ROOT = Path(__file__).resolve().parent.parent
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

from goexport_gui.service import GoExportService  # noqa: E402
from PyQt6.QtCore import QProcess  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402


class GoExportCancellationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _service(self, state: QProcess.ProcessState):
        process = MagicMock()
        process.state.return_value = state
        process.readAllStandardOutput.return_value = b""
        process.readAllStandardError.return_value = b""
        with patch("goexport_gui.service.QProcess", return_value=process):
            service = GoExportService({})
        return service, process

    def test_cancel_terminates_running_process_and_reports_cancelled(self):
        service, process = self._service(QProcess.ProcessState.Running)
        cancelled: list[bool] = []
        failures: list[str] = []
        service.cancelled.connect(lambda: cancelled.append(True))
        service.failed.connect(lambda message, _detail: failures.append(message))

        self.assertTrue(service.cancel())
        process.terminate.assert_called_once_with()
        service._process_finished(1, QProcess.ExitStatus.CrashExit)

        self.assertEqual(cancelled, [True])
        self.assertEqual(failures, [])

    def test_cancel_is_ignored_when_process_is_not_running(self):
        service, process = self._service(QProcess.ProcessState.NotRunning)

        self.assertFalse(service.cancel())
        process.terminate.assert_not_called()

    def test_cancel_forces_process_to_close_after_timeout(self):
        service, process = self._service(QProcess.ProcessState.Running)
        service._cancel_requested = True

        service._force_cancel()

        process.kill.assert_called_once_with()

    def test_subprocess_keeps_rich_terminal_formatting_enabled(self):
        _service, process = self._service(QProcess.ProcessState.NotRunning)

        environment = process.setProcessEnvironment.call_args.args[0]
        self.assertEqual(environment.value("FORCE_COLOR"), "1")
        self.assertEqual(environment.value("CLICOLOR_FORCE"), "1")
        self.assertEqual(environment.value("TERM"), "xterm-256color")
        self.assertFalse(environment.contains("NO_COLOR"))


if __name__ == "__main__":
    unittest.main()
