# GoExport GUI

Small PyQt6 launcher for a separately packaged GoExport V2 release.

## Run from source

Install the minimal GUI dependencies into `.venv` and start the application:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe gui_main.py
```

For exports, place `GoExport.exe` beside the GUI application. The GUI invokes
GoExport's documented `--json record` CLI mode, so GoExport remains responsible
for recording, bundled browser/Flash/FFmpeg dependencies, and output behavior.
The Advanced section exposes every setting supported by GoExport's `record`
command: output format and resolution, server/player URLs, outro behavior,
widescreen mode, Electron integration, Flash timeout behavior, verbose logging,
alternate Chromium, ChromeDriver, Flash, and FFmpeg settings, and the PyScap or
OBS recording backend. OBS settings include its WebSocket host, port, password,
GoExport profile, and scene collection. The password field is masked and passed
only to the child GoExport process; leaving it blank preserves an existing
`GOEXPORT_OBS_PASSWORD` environment variable. Enable **Reuse and reconfigure an
existing OBS profile** only when you explicitly want GoExport to take over the
selected profile and scene collection. Leaving a runtime path blank uses
GoExport's default. Additional Flashvars can add new player values or override
standard ones. Replacements are entered one per line as `name=value` and can
reference runtime fields such as `{user_id}`.

The **Browse** button beside each ID field opens an embedded browser for presets
that define the corresponding browser-picker rule. The Video ID button accepts
only matching video pages, while the User ID button accepts only matching user
pages. Navigate to a supported page, check the ID shown at the bottom, and
select **OK**. The browser accepts HTTP and HTTPS URLs; cookies last for the
current application session.

## Presets

Edit `presets.toml` to add or modify Wrapper-compatible server endpoints. A
preset selection loads the Advanced controls; your manual changes stay in effect
until you select another preset.

Presets may define the new fields directly:

```toml
[preset.Example]
additional_flashvars = "customMode=true"

[preset.Example.replacements]
owner_id = "{user_id}"
```

To enable the browser picker for a preset, add a nested table with a start URL
and at least one URL regex. Every regex must contain a named `id` capture group:

```toml
[preset.FlashThemes.browser_picker]
start_url = "https://flashthemes.net/"
video_url_regex = '^https://(?:www\.)?flashthemes\.net/movie/(?P<id>[A-Za-z0-9_-]+)/?(?:[?#].*)?$'
user_url_regex = '^https://(?:www\.)?flashthemes\.net/user/(?P<id>[0-9]+)/?(?:[?#].*)?$'
```

`video_url_regex` and `user_url_regex` are independently optional, but at least
one must be present. Invalid expressions or missing `id` groups are reported
when the GUI starts. A field's Browse button is disabled when the selected
preset does not define that field's URL regex.

## Build

Run:

```powershell
.\build_gui.ps1
```

It creates `dist\GoExport-GUI\GoExport-GUI.exe`. Publish that file beside the
matching `GoExport.exe` and its existing runtime files.

## Tagged releases

Pushing a tag matching `v*` runs the GitHub Actions release workflow. It builds
Windows x64, Linux x64, and Intel macOS GUI executables, then attaches one ZIP
per platform to the corresponding GitHub Release. Each ZIP contains only the
GUI executable and its required editable `presets.toml` file.
