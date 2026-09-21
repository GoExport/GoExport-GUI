from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_picker_availability_follows_selected_preset(self):
        flashthemes = self.window.preset.findText("FlashThemes")
        wrapper = self.window.preset.findText("Wrapper Offline 2.1+")

        self.window.preset.setCurrentIndex(flashthemes)
        self.assertTrue(self.window.browse_ids.isEnabled())
        self.window.preset.setCurrentIndex(wrapper)
        self.assertFalse(self.window.browse_ids.isEnabled())

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
            self.window._browse_for_id()

        self.assertEqual(self.window.movie_id.text(), "video")
        self.assertEqual(self.window.user_id.text(), "user")


if __name__ == "__main__":
    unittest.main()
