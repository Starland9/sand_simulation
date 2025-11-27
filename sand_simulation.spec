# -*- mode: python -*-
"""PyInstaller build specification for Sand Simulation."""

from pathlib import Path

block_cipher = None

PROJECT_DIR = Path.cwd()
MAIN_SCRIPT = PROJECT_DIR / "main.py"

hidden_imports = [
    "OpenGL.platform",
    "OpenGL.platform.glx",
    "OpenGL.platform.freeglut",
    "OpenGL.arrays.vbo",
    "PyQt6.QtOpenGLWidgets",
]

a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="sand_simulation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Sand Simulation",
)
