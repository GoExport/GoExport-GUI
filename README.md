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
The Advanced section can optionally pass alternate Chromium, ChromeDriver, Flash,
and FFmpeg paths to GoExport; leaving them blank uses GoExport's defaults.

## Presets

Edit `presets.toml` to add or modify Wrapper-compatible server endpoints. A
preset selection loads the Advanced controls; your manual changes stay in effect
until you select another preset.

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
