# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for D-IPCam."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

a = Analysis(
    ['d_ipcam/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtMultimedia',
        'cv2',
        'numpy',
        'av',
        'sqlite3',
    ],
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
    name='D-IPCam',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name='D-IPCam',
)

app = BUNDLE(
    coll,
    name='D-IPCam.app',
    icon=None,
    bundle_identifier='com.d-ipcam.app',
    info_plist={
        'CFBundleName': 'D-IPCam',
        'CFBundleDisplayName': 'D-IPCam',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHighResolutionCapable': True,
        'NSMicrophoneUsageDescription': 'D-IPCam needs microphone access for two-way audio with cameras.',
        'NSCameraUsageDescription': 'D-IPCam may need camera access for local camera testing.',
        'LSMinimumSystemVersion': '10.15',
    },
)
