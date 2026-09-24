#!/usr/bin/env bash
set -euo pipefail

gui_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
appimagetool=${APPIMAGETOOL:-appimagetool-x86_64.AppImage}
app_dir="$gui_root/build/GoExport-GUI.AppDir"
payload="$gui_root/package-appimage/GoExport-GUI"
output="$gui_root/dist/GoExport-GUI-x86_64.AppImage"

python -m PyInstaller "$gui_root/GoExport-GUI-AppImage.spec" \
  --noconfirm --clean \
  --distpath "$gui_root/package-appimage" \
  --workpath "$gui_root/build/appimage-pyinstaller"

rm -rf "$app_dir"
mkdir -p "$app_dir/usr/lib/goexport-gui" "$app_dir/usr/bin" "$gui_root/dist"
cp -a "$payload/." "$app_dir/usr/lib/goexport-gui/"
ln -s ../lib/goexport-gui/GoExport-GUI "$app_dir/usr/bin/GoExport-GUI"
ln -s usr/bin/GoExport-GUI "$app_dir/AppRun"
cp "$gui_root/packaging/linux/goexport-gui.desktop" "$app_dir/"
cp "$gui_root/goexport_gui/resources/goexport-logo.svg" "$app_dir/goexport-gui.svg"

ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$appimagetool" "$app_dir" "$output"
chmod 755 "$output"
