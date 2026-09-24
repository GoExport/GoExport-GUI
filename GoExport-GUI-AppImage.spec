# -*- mode: python ; coding: utf-8 -*-
"""One-directory build used as the payload for the Linux AppImage."""

a = Analysis(
    ["gui_main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("version.txt", "."),
        ("presets.toml", "."),
        ("goexport_gui/resources/default.ico", "goexport_gui/resources"),
        ("goexport_gui/resources/goexport-logo.svg", "goexport_gui/resources"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GoExport-GUI",
    icon="goexport_gui/resources/default.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="GoExport-GUI",
)
