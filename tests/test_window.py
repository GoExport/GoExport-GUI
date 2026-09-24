from __future__ import annotations

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

from goexport_gui.browser_picker import BrowserMatch  # noqa: E402
from goexport_gui.window import MainWindow  # noqa: E402
from PyQt6.QtWidgets import QApplication, QDialog  # noqa: E402


class MainWindowBrowserPickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()

    def test_version_is_shown_in_status_bar(self):
        self.assertEqual(self.window.version_status.text(), f"GoExport {self.window.windowTitle().removeprefix('GoExport ')}")
        self.assertIs(self.window.version_status.parentWidget(), self.window.statusBar())

    def test_picker_availability_follows_selected_preset(self):
        flashthemes = self.window.preset.findText("FlashThemes")
        wrapper = self.window.preset.findText("Wrapper Offline 2.1+")

        self.window.preset.setCurrentIndex(flashthemes)
        self.assertTrue(self.window.browse_video.isEnabled())
        self.assertTrue(self.window.browse_user.isEnabled())
        self.window.preset.setCurrentIndex(wrapper)
        self.assertTrue(self.window.browse_video.isEnabled())
        self.assertFalse(self.window.browse_user.isEnabled())

    def test_video_match_only_updates_video_field(self):
        self.window.movie_id.setText("old-video")
        self.window.user_id.setText("existing-user")

        self.window._apply_browser_match(BrowserMatch("video", "new-video"))

        self.assertEqual(self.window.movie_id.text(), "new-video")
        self.assertEqual(self.window.user_id.text(), "existing-user")

    def test_user_match_only_updates_user_field(self):
        self.window.movie_id.setText("existing-video")
        self.window.user_id.setText("old-user")

        self.window._apply_browser_match(BrowserMatch("user", "new-user"))

        self.assertEqual(self.window.movie_id.text(), "existing-video")
        self.assertEqual(self.window.user_id.text(), "new-user")

    def test_cancel_does_not_update_either_field(self):
        flashthemes = self.window.preset.findText("FlashThemes")
        self.window.preset.setCurrentIndex(flashthemes)
        self.window.movie_id.setText("video")
        self.window.user_id.setText("user")

        with patch("goexport_gui.window.BrowserDialog") as dialog_type:
            dialog_type.return_value.exec.return_value = QDialog.DialogCode.Rejected
            dialog_type.return_value.selected_match = BrowserMatch("video", "ignored")
            self.window._browse_for_id("video")

        self.assertEqual(self.window.movie_id.text(), "video")
        self.assertEqual(self.window.user_id.text(), "user")
        dialog_type.assert_called_once()
        self.assertEqual(dialog_type.call_args.args[1], "video")

    def test_export_cancel_button_tracks_active_service(self):
        self.assertFalse(self.window.cancel_export_button.isEnabled())
        service = MagicMock()
        service.cancel.return_value = True
        self.window._service = service

        self.window._export_started()
        self.assertTrue(self.window.cancel_export_button.isEnabled())
        self.window._cancel_export()

        service.cancel.assert_called_once_with()
        self.assertFalse(self.window.cancel_export_button.isEnabled())
        self.assertEqual(self.window.status.text(), "Cancelling export...")

        self.window._export_finished()
        self.assertFalse(self.window.cancel_export_button.isEnabled())

    def test_obs_controls_follow_capture_backend(self):
        self.assertEqual(self.window.capture_backend.currentData(), "pyscap")
        self.assertFalse(self.window.obs_host.isEnabled())

        self.window.capture_backend.setCurrentIndex(
            self.window.capture_backend.findData("obs")
        )

        self.assertTrue(self.window.obs_host.isEnabled())
        self.assertTrue(self.window.obs_password.isEnabled())
        self.assertTrue(self.window.obs_force_profile.isEnabled())

    def test_options_include_obs_settings(self):
        self.window.movie_id.setText("movie")
        self.window.capture_backend.setCurrentIndex(
            self.window.capture_backend.findData("obs")
        )
        self.window.obs_host.setText("obs.example")
        self.window.obs_port.setText("4456")
        self.window.obs_profile.setText("Export Profile")
        self.window.obs_scene_collection.setText("Export Scenes")
        self.window.obs_password.setText("secret")
        self.window.obs_force_profile.setChecked(True)

        options = self.window._options()

        self.assertIsNotNone(options)
        assert options is not None
        self.assertEqual(options["capture_backend"], "obs")
        self.assertEqual(options["obs_host"], "obs.example")
        self.assertEqual(options["obs_port"], 4456)
        self.assertEqual(options["obs_profile"], "Export Profile")
        self.assertEqual(options["obs_scene_collection"], "Export Scenes")
        self.assertEqual(options["obs_password"], "secret")
        self.assertTrue(options["obs_force_profile"])


if __name__ == "__main__":
    unittest.main()
