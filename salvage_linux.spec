# -*- mode: python ; coding: utf-8 -*-
"""
salvage_linux.spec - PyInstallerのビルド設定ファイル

このファイルはPyInstallerがsalvage_linux（USB Boot Linux GUIディスクユーティリティ）を
単一の実行ファイルにパッケージングするための設定を定義します。

バージョン: 0.1.0
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='salvage_linux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # コンソールウィンドウを表示する（バージョン0.x.xのため）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='path/to/icon.ico',  # アイコンはまだ作成されていないため、コメントアウト
) 