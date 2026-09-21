"""Loading of the small, user-editable GUI preset file."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from goexport_gui.browser_picker import BrowserPickerConfig, browser_picker_config


@dataclass(frozen=True)
class Preset:
    name: str
    values: dict[str, Any]
    browser_picker: BrowserPickerConfig | None = None


def preset_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "presets.toml"
    return Path(__file__).resolve().parent.parent / "presets.toml"


def load_presets(path: Path | None = None) -> list[Preset]:
    with (path or preset_file()).open("rb") as source:
        data = tomllib.load(source)
    entries = data.get("preset", {})
    if not isinstance(entries, dict) or not entries:
        raise ValueError("presets.toml must contain [preset.<name>] sections.")
    return sorted(
        [
            Preset(
                name,
                dict(values),
                browser_picker_config(values.get("browser_picker"), preset_name=name),
            )
            for name, values in entries.items()
            if isinstance(values, dict)
        ],
        key=lambda preset: preset.name.casefold(),
    )
