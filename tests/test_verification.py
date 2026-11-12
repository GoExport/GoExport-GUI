from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

GUI_ROOT = Path(__file__).resolve().parent.parent
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

from goexport_gui import service as service_module  # noqa: E402
from goexport_gui.service import (  # noqa: E402
    CANCEL_COMMAND,
    GoExportService,
    child_environment,
)
from goexport_gui.window import MainWindow  # noqa: E402
from PyQt6.QtCore import QProcess, QProcessEnvironment  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

REQUIRED = json.dumps(
    {
        "event": "verification_required",
        "reason": "cloudflare",
        "message": "Manual browser verification is required.",
        "presentation": "vnc",
        "timeout": 300,
    }
)


class ServiceVerificationEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.process = MagicMock()
        self.process.state.return_value = QProcess.ProcessState.Running
        self.process.readAllStandardOutput.return_value = b""
        self.process.readAllStandardError.return_value = b""
        with patch("goexport_gui.service.QProcess", return_value=self.process):
            self.service = GoExportService({})

    def test_verification_events_become_signals(self):
        required, completed, failed = [], [], []
        self.service.verification_required.connect(
            lambda message, kind: required.append((message, kind))
        )
        self.service.verification_completed.connect(lambda: completed.append(True))
        self.service.verification_failed.connect(failed.append)

        self.service._handle_event(REQUIRED)
        self.service._handle_event('{"event": "verification_complete"}')
        self.service._handle_event(
            '{"event": "verification_failed", "message": "Timed out", "reason": "timeout"}'
        )

        self.assertEqual(
            required, [("Manual browser verification is required.", "vnc")]
        )
        self.assertEqual(completed, [True])
        self.assertEqual(failed, ["Timed out"])

    def test_cancel_asks_goexport_to_stop_verification_before_terminating(self):
        self.assertTrue(self.service.cancel())
        self.process.write.assert_called_once_with(CANCEL_COMMAND)
        self.assertEqual(json.loads(CANCEL_COMMAND), {"command": "cancel"})
        self.process.terminate.assert_called_once_with()
        self.assertGreaterEqual(self.service._cancel_timer.interval(), 10000)

    def test_failed_verification_is_not_reported_after_cancellation(self):
        failed = []
        self.service.verification_failed.connect(failed.append)
        self.service.cancel()
        self.service._handle_event(
            '{"event": "verification_failed", "message": "cancelled", "reason": "cancelled"}'
        )
        self.assertEqual(failed, [])


class ChildEnvironmentTests(unittest.TestCase):
    def test_pyinstaller_library_path_is_restored(self):
        environment = QProcessEnvironment()
        environment.insert("LD_LIBRARY_PATH", "/tmp/.mount_GoExport/usr/lib:/opt/lib")
        environment.insert("LD_LIBRARY_PATH_ORIG", "/opt/lib")
        with patch.object(
            service_module.QProcessEnvironment,
            "systemEnvironment",
            return_value=environment,
        ):
            result = child_environment()
        self.assertEqual(result.value("LD_LIBRARY_PATH"), "/opt/lib")
        self.assertFalse(result.contains("LD_LIBRARY_PATH_ORIG"))

    def test_empty_original_library_path_is_removed(self):
        environment = QProcessEnvironment()
        environment.insert("LD_LIBRARY_PATH", "/tmp/.mount_GoExport/usr/lib")
        environment.insert("LD_LIBRARY_PATH_ORIG", "")
        with patch.object(
            service_module.QProcessEnvironment,
            "systemEnvironment",
            return_value=environment,
        ):
            result = child_environment()
        self.assertFalse(result.contains("LD_LIBRARY_PATH"))


class WindowVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()
        self.window.show()

    def tearDown(self) -> None:
        self.window.close()

    def test_vnc_verification_is_shown_and_cleared(self):
        self.window._on_progress(3, "preparing")
        self.window._on_verification_required("Manual verification.", "vnc")

        self.assertTrue(self.window.verification_notice.isVisible())
        self.assertIn("verification viewer", self.window.verification_notice.text())
        self.assertEqual(self.window.progress.maximum(), 0)
        self.assertIn("verification", self.window.status.text())

        self.window._on_verification_complete()

        self.assertFalse(self.window.verification_notice.isVisible())
        self.assertEqual(self.window.progress.maximum(), 100)
        self.assertEqual(self.window.progress.value(), 3)
        self.assertIn("resuming", self.window.status.text())

    def test_windows_verification_names_chromium_without_vnc_details(self):
        self.window._on_verification_required("Manual verification.", "window")
        text = self.window.verification_notice.text()
        self.assertIn("Chromium window", text)
        self.assertNotIn("viewer", text)
        self.assertNotIn("VNC", text)

    def test_cancel_stays_available_while_verifying(self):
        service = MagicMock()
        service.cancel.return_value = True
        self.window._service = service
        self.window._export_started()
        self.window._on_verification_required("Manual verification.", "window")
        self.assertTrue(self.window.cancel_export_button.isEnabled())
        self.window._cancel_export()
        service.cancel.assert_called_once_with()

    def test_failure_and_finish_return_to_normal_interface(self):
        self.window._on_verification_required("Manual verification.", "vnc")
        self.window._on_verification_failed("Timed out")
        self.assertFalse(self.window.verification_notice.isVisible())
        self.assertEqual(self.window.progress.maximum(), 100)
        self.assertEqual(self.window.status.text(), "Browser verification failed")

        self.window._on_verification_required("Manual verification.", "vnc")
        self.window._export_finished()
        self.assertFalse(self.window.verification_notice.isVisible())
        self.assertEqual(self.window.progress.maximum(), 100)


class AnubisServiceEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        process = MagicMock()
        process.state.return_value = QProcess.ProcessState.Running
        with patch("goexport_gui.service.QProcess", return_value=process):
            self.service = GoExportService({})

    def test_provider_and_interaction_are_forwarded(self):
        required, completed, failed = [], [], []
        self.service.verification_required.connect(
            lambda *values: required.append(values)
        )
        self.service.verification_completed.connect(completed.append)
        self.service.verification_failed.connect(
            lambda message, provider: failed.append((message, provider))
        )

        self.service._handle_event(
            json.dumps(
                {
                    "event": "verification_required",
                    "reason": "anubis",
                    "provider": "anubis",
                    "interaction": "automatic",
                    "message": "Anubis verification is in progress.",
                    "presentation": None,
                    "timeout": 300,
                }
            )
        )
        self.service._handle_event(
            '{"event": "verification_complete", "provider": "anubis"}'
        )
        self.service._handle_event(
            '{"event": "verification_failed", "message": "Timed out", '
            '"reason": "timeout", "provider": "anubis"}'
        )

        self.assertEqual(
            required,
            [("Anubis verification is in progress.", "", "anubis", "automatic")],
        )
        self.assertEqual(completed, ["anubis"])
        self.assertEqual(failed, [("Timed out", "anubis")])

    def test_events_from_older_goexport_default_to_manual_cloudflare(self):
        required, completed, failed = [], [], []
        self.service.verification_required.connect(
            lambda *values: required.append(values)
        )
        self.service.verification_completed.connect(completed.append)
        self.service.verification_failed.connect(
            lambda _message, provider: failed.append(provider)
        )
        self.service._handle_event(REQUIRED)  # no provider or interaction keys
        self.service._handle_event('{"event": "verification_complete"}')
        self.service._handle_event(
            '{"event": "verification_failed", "message": "x", "reason": "timeout"}'
        )
        self.assertEqual(required[0][2:], ("cloudflare", "manual"))
        self.assertEqual(completed, ["cloudflare"])
        self.assertEqual(failed, ["cloudflare"])


class AnubisWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()
        self.window.show()

    def tearDown(self) -> None:
        self.window.close()

    def test_automatic_anubis_shows_status_without_asking_the_user(self):
        self.window._on_progress(4, "preparing")
        self.window._on_verification_required(
            "Anubis verification is in progress.", "", "anubis", "automatic"
        )
        self.assertEqual(self.window.status.text(), "Completing Anubis verification…")
        self.assertFalse(self.window.verification_notice.isVisible())
        self.assertEqual(self.window.progress.maximum(), 0)

        self.window._on_verification_complete("anubis")
        self.assertEqual(
            self.window.status.text(),
            "Anubis verification completed — resuming export…",
        )
        self.assertEqual(self.window.progress.maximum(), 100)
        self.assertEqual(self.window.progress.value(), 4)

    def test_stalled_anubis_switches_to_manual_verification(self):
        self.window._on_progress(4, "preparing")
        self.window._on_verification_required(
            "Anubis verification is in progress.", "", "anubis", "automatic"
        )
        self.window._on_verification_required(
            "Anubis verification needs your help.", "vnc", "anubis", "manual"
        )
        self.assertEqual(self.window.status.text(), "Manual verification required.")
        self.assertTrue(self.window.verification_notice.isVisible())
        self.assertIn("Anubis", self.window.verification_notice.text())
        self.assertIn("verification viewer", self.window.verification_notice.text())

        self.window._on_verification_complete("anubis")
        self.assertFalse(self.window.verification_notice.isVisible())
        self.assertEqual(self.window.progress.value(), 4)

    def test_windows_anubis_prompt_names_chromium_without_vnc(self):
        self.window._on_verification_required("help", "window", "anubis", "manual")
        text = self.window.verification_notice.text()
        self.assertIn("Chromium window", text)
        self.assertNotIn("viewer", text)

    def test_anubis_failure_status(self):
        self.window._on_verification_required(
            "Anubis verification is in progress.", "", "anubis", "automatic"
        )
        self.window._on_verification_failed("Chromium 87 cannot run it", "anubis")
        self.assertEqual(
            self.window.status.text(), "Anubis verification failed or timed out."
        )
        self.assertEqual(self.window.progress.maximum(), 100)

    def test_cloudflare_texts_are_unchanged(self):
        self.window._on_verification_required(
            "Manual verification.", "window", "cloudflare", "manual"
        )
        self.assertEqual(self.window.status.text(), "Waiting for browser verification…")
        self.assertIn("Cloudflare", self.window.verification_notice.text())
        self.window._on_verification_complete("cloudflare")
        self.assertEqual(
            self.window.status.text(), "Verification complete — resuming export…"
        )


if __name__ == "__main__":
    unittest.main()
