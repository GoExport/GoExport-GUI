from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

GUI_ROOT = Path(__file__).resolve().parent.parent
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

from goexport_gui.browser_picker import (  # noqa: E402
    BrowserMatch,
    BrowserPickerConfig,
    browser_picker_config,
    normalize_browser_url,
)
from goexport_gui.presets import load_presets  # noqa: E402

VIDEO_PATTERN = (
    r"^https://(?:www\.)?example\.com/movie/"
    r"(?P<id>[A-Za-z0-9_-]+)/?(?:[?#].*)?$"
)
USER_PATTERN = r"^https://(?:www\.)?example\.com/user/(?P<id>[0-9]+)/?(?:[?#].*)?$"


class BrowserPickerConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = BrowserPickerConfig(
            "https://example.com/",
            video_url_regex=VIDEO_PATTERN,
            user_url_regex=USER_PATTERN,
        )

    def test_extracts_video_id_with_supported_characters(self):
        self.assertEqual(
            self.config.matches("https://example.com/movie/Ab_12-c"),
            [BrowserMatch("video", "Ab_12-c")],
        )

    def test_extracts_user_id_with_trailing_slash_query_and_fragment(self):
        self.assertEqual(
            self.config.matches("https://www.example.com/user/193690/?tab=movies#top"),
            [BrowserMatch("user", "193690")],
        )

    def test_nonmatching_url_returns_no_match(self):
        self.assertEqual(self.config.matches("https://example.com/account/193690"), [])

    def test_ambiguous_url_returns_both_matches(self):
        config = BrowserPickerConfig(
            "https://example.com/",
            video_url_regex=r"example\.com/(?P<id>movie)",
            user_url_regex=r"example\.com/(?P<id>movie)",
        )
        self.assertEqual(
            config.matches("https://example.com/movie"),
            [BrowserMatch("video", "movie"), BrowserMatch("user", "movie")],
        )

    def test_single_rule_is_valid(self):
        config = browser_picker_config(
            {"start_url": "https://example.com", "video_url_regex": VIDEO_PATTERN},
            preset_name="Example",
        )
        self.assertIsNotNone(config)
        assert config is not None
        self.assertIsNone(config.user_url_regex)
        self.assertTrue(config.supports("video"))
        self.assertFalse(config.supports("user"))

    def test_field_specific_matching_ignores_the_other_rule(self):
        self.assertEqual(
            self.config.matches("https://example.com/movie/video-one", "video"),
            [BrowserMatch("video", "video-one")],
        )
        self.assertEqual(
            self.config.matches("https://example.com/movie/video-one", "user"), []
        )

    def test_invalid_regex_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a valid regular expression"):
            browser_picker_config(
                {"start_url": "https://example.com", "video_url_regex": "["},
                preset_name="Example",
            )

    def test_missing_named_group_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "named.*id"):
            browser_picker_config(
                {
                    "start_url": "https://example.com",
                    "video_url_regex": r"/movie/([A-Za-z0-9]+)",
                },
                preset_name="Example",
            )

    def test_missing_start_url_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "start_url"):
            browser_picker_config(
                {"video_url_regex": VIDEO_PATTERN}, preset_name="Example"
            )

    def test_empty_rule_table_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must define"):
            browser_picker_config(
                {"start_url": "https://example.com"}, preset_name="Example"
            )

    def test_schemeless_navigation_defaults_to_https(self):
        self.assertEqual(
            normalize_browser_url("example.com/movie/one"),
            "https://example.com/movie/one",
        )

    def test_non_web_navigation_is_rejected(self):
        self.assertIsNone(normalize_browser_url("javascript:alert(1)"))


class PresetLoadingTests(unittest.TestCase):
    def test_presets_with_and_without_picker_rules_load(self):
        contents = f"""
[preset.Browsable]
url = "https://example.com"

[preset.Browsable.browser_picker]
start_url = "https://example.com"
video_url_regex = '{VIDEO_PATTERN}'

[preset.Plain]
url = "http://localhost/"
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "presets.toml"
            path.write_text(contents, encoding="utf-8")
            presets = load_presets(path)

        by_name = {preset.name: preset for preset in presets}
        self.assertIsNotNone(by_name["Browsable"].browser_picker)
        self.assertIsNone(by_name["Plain"].browser_picker)


if __name__ == "__main__":
    unittest.main()
