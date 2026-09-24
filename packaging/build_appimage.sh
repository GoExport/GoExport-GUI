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

qxcb_plugin=$(find "$payload" -type f -path '*/platforms/libqxcb.so' -print -quit)
if [[ -z "$qxcb_plugin" ]]; then
  echo "PyInstaller payload is missing the Qt xcb platform plugin." >&2
  exit 1
fi

if [[ -z $(find "$payload" -name 'libxcb-cursor.so.0' -print -quit) ]]; then
  echo "PyInstaller payload is missing libxcb-cursor.so.0." >&2
  exit 1
fi

qxcb_dependencies=$(ldd "$qxcb_plugin")
if grep -q 'not found' <<<"$qxcb_dependencies"; then
  echo "Qt xcb platform plugin has unresolved shared-library dependencies:" >&2
  echo "$qxcb_dependencies" >&2
  exit 1
fi

rm -rf "$app_dir"
mkdir -p "$app_dir/usr/lib/goexport-gui" "$app_dir/usr/bin" "$gui_root/dist"
cp -a "$payload/." "$app_dir/usr/lib/goexport-gui/"
ln -s ../lib/goexport-gui/GoExport-GUI "$app_dir/usr/bin/GoExport-GUI"
ln -s usr/bin/GoExport-GUI "$app_dir/AppRun"
cp "$gui_root/packaging/linux/goexport-gui.desktop" "$app_dir/"
cp "$gui_root/goexport_gui/resources/goexport-logo.svg" "$app_dir/goexport-gui.svg"

ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$appimagetool" "$app_dir" "$output"
chmod 755 "$output"
