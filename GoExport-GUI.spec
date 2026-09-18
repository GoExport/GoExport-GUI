# GoExport-GUI.spec

a = Analysis(
    ["gui_main.py"],
    pathex=[],
    binaries=[],
    datas=[("goexport_gui/resources/goexport-logo.svg", "goexport_gui/resources")],
    hiddenimports=[],
    hookspath=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="GoExport-GUI",
    icon='goexport_gui/resources/default.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
