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


class GoExportOBSOptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _options(self):
        return {
            "verbose": False,
            "movie_id": "movie",
            "format": "mp4",
            "output": "output",
            "resolution": "1280x720",
            "url": "http://wrapper/",
            "api_url": "http://wrapper/",
            "swf_url": "http://assets/player.swf",
            "store_path": "http://assets/store/<store>",
            "client_theme_path": "http://assets/<client_theme>",
            "user_id": None,
            "additional_flashvars": "",
            "replacements": [],
            "no_outro": True,
            "use_outro": "",
            "no_wide": False,
            "electron": False,
            "no_flash_timeout": False,
            "chrome_path": "",
            "chromedriver_path": "",
            "flash_plugin_path": "",
            "flash_plugin_version": "",
            "ffmpeg_path": "",
            "capture_backend": "obs",
            "obs_host": "obs.example",
            "obs_port": 4456,
            "obs_profile": "Export Profile",
            "obs_scene_collection": "Export Scenes",
            "obs_password": "secret",
        }

    def test_obs_arguments_are_forwarded(self):
        service = GoExportService(self._options())

        arguments = service._arguments()

        self.assertIn("--capture-backend", arguments)
        self.assertEqual(arguments[arguments.index("--capture-backend") + 1], "obs")
        self.assertEqual(arguments[arguments.index("--obs-host") + 1], "obs.example")
        self.assertEqual(arguments[arguments.index("--obs-port") + 1], "4456")
        self.assertEqual(
            arguments[arguments.index("--obs-scene-collection") + 1],
            "Export Scenes",
        )

    def test_password_is_passed_in_child_environment(self):
        service = GoExportService(self._options())
        service.process = MagicMock()

        with patch(
            "goexport_gui.service.find_goexport_executable",
            return_value=Path("C:/GoExport/GoExport.exe"),
        ):
            service.start()

        environment = service.process.setProcessEnvironment.call_args.args[0]
        self.assertEqual(environment.value("GOEXPORT_OBS_PASSWORD"), "secret")


if __name__ == "__main__":
    unittest.main()
