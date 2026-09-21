"""Configuration and URL matching for the GUI browser picker."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal, Pattern
from urllib.parse import urlsplit


@dataclass(frozen=True)
class BrowserMatch:
    """An ID extracted from a URL by a preset's browser rules."""

    field: str
    value: str


PickerField = Literal["video", "user"]


@dataclass(frozen=True)
class BrowserPickerConfig:
    """Validated browser-picker settings for one preset."""

    start_url: str
    video_url_regex: str | None = None
    user_url_regex: str | None = None
    _video_pattern: Pattern[str] | None = field(init=False, repr=False)
    _user_pattern: Pattern[str] | None = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_video_pattern",
            _compile_pattern(self.video_url_regex, "video_url_regex"),
        )
        object.__setattr__(
            self,
            "_user_pattern",
            _compile_pattern(self.user_url_regex, "user_url_regex"),
        )

    def supports(self, field_name: PickerField) -> bool:
        """Return whether this preset can select the requested field."""
        return (
            self._video_pattern if field_name == "video" else self._user_pattern
        ) is not None

    def matches(
        self, url: str, field_name: PickerField | None = None
    ) -> list[BrowserMatch]:
        """Return all configured rules that match *url*."""
        matches: list[BrowserMatch] = []
        for candidate_field, pattern in (
            ("video", self._video_pattern),
            ("user", self._user_pattern),
        ):
            if field_name is not None and candidate_field != field_name:
                continue
            if pattern is None:
                continue
            match = pattern.search(url)
            if match is not None:
                captured_id = match.group("id")
                if captured_id:
                    matches.append(BrowserMatch(candidate_field, captured_id))
        return matches


def normalize_browser_url(address: str) -> str | None:
    """Return an HTTP(S) address, defaulting schemeless input to HTTPS."""
    normalized = address.strip()
    if not normalized:
        return None
    parsed_url = urlsplit(normalized)
    if not parsed_url.scheme:
        normalized = f"https://{normalized}"
        parsed_url = urlsplit(normalized)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return None
    return normalized


def browser_picker_config(
    value: Any, *, preset_name: str
) -> BrowserPickerConfig | None:
    """Validate and construct a preset's optional browser-picker settings."""
    if value is None:
        return None
    setting = f"preset.{preset_name}.browser_picker"
    if not isinstance(value, dict):
        raise ValueError(f"[{setting}] must be a TOML table.")

    allowed = {"start_url", "video_url_regex", "user_url_regex"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{setting} has unsupported setting '{unknown[0]}'.")

    start_url = value.get("start_url")
    if not isinstance(start_url, str) or not start_url.strip():
        raise ValueError(f"{setting}.start_url must be a non-empty string.")
    normalized_start_url = normalize_browser_url(start_url)
    if normalized_start_url is None or urlsplit(start_url).scheme not in {
        "http",
        "https",
    }:
        raise ValueError(f"{setting}.start_url must be an HTTP or HTTPS URL.")

    patterns: dict[str, str | None] = {}
    for name in ("video_url_regex", "user_url_regex"):
        pattern = value.get(name)
        if pattern is not None and (not isinstance(pattern, str) or not pattern):
            raise ValueError(f"{setting}.{name} must be a non-empty string.")
        patterns[name] = pattern
    if not any(patterns.values()):
        raise ValueError(f"{setting} must define video_url_regex or user_url_regex.")

    try:
        return BrowserPickerConfig(start_url=normalized_start_url, **patterns)
    except ValueError as error:
        raise ValueError(f"{setting}: {error}") from error


def _compile_pattern(value: str | None, name: str) -> Pattern[str] | None:
    if value is None:
        return None
    try:
        pattern = re.compile(value)
    except re.error as error:
        raise ValueError(
            f"{name} is not a valid regular expression: {error}"
        ) from error
    if "id" not in pattern.groupindex:
        raise ValueError(f"{name} must contain a named '(?P<id>...)' capture group")
    return pattern
