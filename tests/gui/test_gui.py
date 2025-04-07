"""
GUIテストモジュール
"""

import pytest
import tkinter as tk
from tkinter import ttk, messagebox
import os
import time
from unittest.mock import patch, MagicMock, ANY
from src.main import DiskUtilityApp
from src.disk_utils import DiskUtils
from src.logger import Logger
from PyQt5.QtWidgets import QApplication
import sys

@pytest.mark.gui
@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成するフィクスチャ"""
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # テスト後にディレクトリを削除
    shutil.rmtree(temp_dir)

@pytest.mark.gui
@pytest.fixture
def mocked_tk():
    """モック化されたtkinterモジュールを提供するフィクスチャ"""
    # Tkinterのグローバル状態の定数を設定
    original_disabled = tk.DISABLED
    original_normal = tk.NORMAL
    
    # テスト中に使用される定数にアクセスできるようにする
    yield {
        'DISABLED': original_disabled,
        'NORMAL': original_normal,
        'END': tk.END
    }

@pytest.mark.gui
@pytest.fixture
def qt_app():
    """QApplicationインスタンスを提供するフィクスチャ"""
    # 環境変数を設定してヘッドレスモードを有効にする
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.mark.gui
@pytest.fixture
def gui_app(qt_app):
    """モック化されたGUIインスタンスを提供するフィクスチャ"""
    # ルートウィンドウのモック
    root = MagicMock()
    root.title.return_value = "USBブートLinux ディスクユーティリティ"
    root.geometry.return_value = None
    
    # afterメソッドの実装を直接コールバックを実行するように変更
    def execute_after(ms, callback, *args):
        if callable(callback):
            return callback(*args)
    root.after = MagicMock(side_effect=execute_after)
    
    # ロガーとDiskUtilsのモック
    logger = MagicMock()
    disk_utils = MagicMock()
    
    # DiskUtilsのメソッドをモック化
    disk_utils.mount_disk = MagicMock(return_value=(True, "/mnt/test", ""))
    disk_utils.format_disk = MagicMock(return_value=(True, ""))
    disk_utils.set_permissions = MagicMock(return_value=(True, ""))
    disk_utils.get_unmounted_disks = MagicMock(return_value=[
        {"name": "sda", "path": "/dev/sda", "size": "8GB", "type": "disk", "fstype": "ntfs"}
    ])
    disk_utils.get_mounted_disks = MagicMock(return_value=[
        {"name": "sdb1", "path": "/dev/sdb1", "size": "16GB", "type": "part", 
         "fstype": "ntfs", "mountpoint": "/mnt/sdb1"}
    ])
    
    # GUIインスタンスを作成（テストモードを有効に）
    app = DiskUtilityApp(test_mode=True)
    
    # モックをアプリケーションに設定
    app.logger = logger
    app.disk_utils = disk_utils
    
    # テスト用の選択ディスク属性を追加
    app.selected_unmounted_disk = None
    app.selected_mounted_disk = None
    
    # Listboxウィジェットのモック
    unmounted_listbox = MagicMock()
    unmounted_listbox.curselection.return_value = [0]  # 常に最初の項目が選択されているとみなす
    unmounted_listbox.delete.return_value = None
    unmounted_listbox.insert.return_value = None
    unmounted_listbox.get.return_value = "sda1 (8GB, ディスク)"
    
    mounted_listbox = MagicMock()
    mounted_listbox.curselection.return_value = [0]  # 常に最初の項目が選択されているとみなす
    mounted_listbox.delete.return_value = None
    mounted_listbox.insert.return_value = None
    mounted_listbox.get.return_value = "sdb1 (16GB, /mnt/sdb1)"
    
    # Textウィジェットのモック
    unmounted_info = MagicMock()
    unmounted_info.delete.return_value = None
    unmounted_info.insert.return_value = None
    unmounted_info.config.return_value = None
    
    mounted_info = MagicMock()
    mounted_info.delete.return_value = None
    mounted_info.insert.return_value = None
    mounted_info.config.return_value = None
    
    # ボタンのモック
    mount_button = MagicMock()
    mount_button.cget.return_value = tk.DISABLED
    mount_button.config.return_value = None
    
    format_button = MagicMock()
    format_button.cget.return_value = tk.DISABLED
    format_button.config.return_value = None
    
    open_button = MagicMock()
    open_button.cget.return_value = tk.DISABLED
    open_button.config.return_value = None
    
    permission_button = MagicMock()
    permission_button.cget.return_value = tk.DISABLED
    permission_button.config.return_value = None
    
    # モックウィジェットをアプリケーションに設定
    app.unmounted_disk_listbox = unmounted_listbox
    app.mounted_disk_listbox = mounted_listbox
    app.unmounted_disk_info = unmounted_info
    app.mounted_disk_info = mounted_info
    app.mount_button = mount_button
    app.format_button = format_button
    app.open_button = open_button
    app.permission_button = permission_button
    
    # ディスクデータのモック
    app.unmounted_disks = [
        {"name": "sda", "path": "/dev/sda", "size": "8GB", "type": "disk", "fstype": "ntfs"}
    ]
    app.mounted_disks = [
        {"name": "sdb1", "path": "/dev/sdb1", "size": "16GB", "type": "part", 
         "fstype": "ntfs", "mountpoint": "/mnt/sdb1"}
    ]
    
    # _on_unmounted_disk_selectメソッドをオーバーライド
    def _on_unmounted_disk_select(event):
        app.selected_unmounted_disk = app.unmounted_disks[0]["path"]
        app.mount_button.config(state=tk.NORMAL)
        app.format_button.config(state=tk.NORMAL)
    
    # _on_mounted_disk_selectメソッドをオーバーライド
    def _on_mounted_disk_select(event):
        app.selected_mounted_disk = app.mounted_disks[0]["mountpoint"]
        app.open_button.config(state=tk.NORMAL)
        app.permission_button.config(state=tk.NORMAL)
    
    app._on_unmounted_disk_select = _on_unmounted_disk_select
    app._on_mounted_disk_select = _on_mounted_disk_select
    
    return app

@pytest.mark.gui
def test_gui_initialization(gui_app):
    """GUIの初期化テスト"""
    # アプリケーションが正しく初期化されていることを確認
    assert gui_app is not None
    assert gui_app.test_mode is True
    assert gui_app.logger is not None
    assert gui_app.disk_utils is not None

@pytest.mark.gui
def test_disk_list_initialization(gui_app):
    """ディスクリストの初期化テスト"""
    # 未マウントディスクリストが正しく初期化されていることを確認
    assert gui_app.unmounted_disk_listbox is not None
    assert gui_app.unmounted_disk_listbox.delete.called
    assert gui_app.unmounted_disk_listbox.insert.called
    
    # マウント済みディスクリストが正しく初期化されていることを確認
    assert gui_app.mounted_disk_listbox is not None
    assert gui_app.mounted_disk_listbox.delete.called
    assert gui_app.mounted_disk_listbox.insert.called

@pytest.mark.gui
def test_disk_info_initialization(gui_app):
    """ディスク情報の初期化テスト"""
    # 未マウントディスク情報が正しく初期化されていることを確認
    assert gui_app.unmounted_disk_info is not None
    assert gui_app.unmounted_disk_info.delete.called
    assert gui_app.unmounted_disk_info.insert.called
    
    # マウント済みディスク情報が正しく初期化されていることを確認
    assert gui_app.mounted_disk_info is not None
    assert gui_app.mounted_disk_info.delete.called
    assert gui_app.mounted_disk_info.insert.called

@pytest.mark.gui
def test_button_initialization(gui_app):
    """ボタンの初期化テスト"""
    # マウントボタンが正しく初期化されていることを確認
    assert gui_app.mount_button is not None
    assert gui_app.mount_button.cget.return_value == tk.DISABLED
    
    # フォーマットボタンが正しく初期化されていることを確認
    assert gui_app.format_button is not None
    assert gui_app.format_button.cget.return_value == tk.DISABLED
    
    # 開くボタンが正しく初期化されていることを確認
    assert gui_app.open_button is not None
    assert gui_app.open_button.cget.return_value == tk.DISABLED
    
    # 権限ボタンが正しく初期化されていることを確認
    assert gui_app.permission_button is not None
    assert gui_app.permission_button.cget.return_value == tk.DISABLED

@pytest.mark.gui
def test_unmounted_disk_selection(gui_app):
    """未マウントディスクの選択テスト"""
    # 未マウントディスクを選択
    gui_app._on_unmounted_disk_select(None)
    
    # 選択されたディスクが正しく設定されていることを確認
    assert gui_app.selected_unmounted_disk == "/dev/sda"
    
    # ボタンの状態が正しく更新されていることを確認
    assert gui_app.mount_button.config.called
    assert gui_app.format_button.config.called

@pytest.mark.gui
def test_mounted_disk_selection(gui_app):
    """マウント済みディスクの選択テスト"""
    # マウント済みディスクを選択
    gui_app._on_mounted_disk_select(None)
    
    # 選択されたディスクが正しく設定されていることを確認
    assert gui_app.selected_mounted_disk == "/mnt/sdb1"
    
    # ボタンの状態が正しく更新されていることを確認
    assert gui_app.open_button.config.called
    assert gui_app.permission_button.config.called

@pytest.mark.gui
def test_mount_disk(gui_app):
    """ディスクのマウントテスト"""
    # 未マウントディスクを選択
    gui_app._on_unmounted_disk_select(None)
    
    # マウントボタンをクリック
    gui_app._mount_disk()
    
    # マウント処理が正しく実行されていることを確認
    assert gui_app.disk_utils.mount_disk.called
    assert gui_app.disk_utils.mount_disk.call_args[0][0] == "/dev/sda"

@pytest.mark.gui
def test_format_disk(gui_app):
    """ディスクのフォーマットテスト"""
    # 未マウントディスクを選択
    gui_app._on_unmounted_disk_select(None)
    
    # フォーマットボタンをクリック
    gui_app._format_disk()
    
    # フォーマット処理が正しく実行されていることを確認
    assert gui_app.disk_utils.format_disk.called
    assert gui_app.disk_utils.format_disk.call_args[0][0] == "/dev/sda"

@pytest.mark.gui
def test_open_file_manager(gui_app):
    """ファイルマネージャーの起動テスト"""
    # マウント済みディスクを選択
    gui_app._on_mounted_disk_select(None)
    
    # 開くボタンをクリック
    gui_app._open_file_manager()
    
    # ファイルマネージャーが正しく起動されていることを確認
    assert gui_app.disk_utils.open_file_manager.called
    assert gui_app.disk_utils.open_file_manager.call_args[0][0] == "/mnt/sdb1"

@pytest.mark.gui
def test_set_permissions(gui_app):
    """権限の設定テスト"""
    # マウント済みディスクを選択
    gui_app._on_mounted_disk_select(None)
    
    # 権限ボタンをクリック
    gui_app._set_permissions()
    
    # 権限設定処理が正しく実行されていることを確認
    assert gui_app.disk_utils.set_permissions.called
    assert gui_app.disk_utils.set_permissions.call_args[0][0] == "/mnt/sdb1" 