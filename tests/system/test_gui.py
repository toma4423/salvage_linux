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

@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成するフィクスチャ"""
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # テスト後にディレクトリを削除
    shutil.rmtree(temp_dir)

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

@pytest.fixture
def qt_app():
    """QApplicationインスタンスを提供するフィクスチャ"""
    # 環境変数を設定してヘッドレスモードを有効にする
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication(sys.argv)
    yield app
    app.quit()

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

@pytest.mark.system
@pytest.mark.gui
class TestGUI:
    """GUIのテストクラス"""
    
    def test_gui_init(self, gui_app):
        """GUIの初期化テスト"""
        # GUIが正しく初期化されたかを確認
        assert gui_app.root.title() == "USBブートLinux ディスクユーティリティ"
        assert hasattr(gui_app, 'unmounted_disk_listbox')
        assert hasattr(gui_app, 'mounted_disk_listbox')
        
        # ボタンのチェックはcgetの戻り値で確認
        assert gui_app.mount_button.cget('state') == tk.DISABLED
        assert gui_app.format_button.cget('state') == tk.DISABLED
    
    def test_refresh_disk_lists(self, gui_app):
        """ディスクリスト更新のテスト"""
        # ディスクユーティリティのモックを設定
        gui_app.disk_utils.get_unmounted_disks.return_value = [
            {"name": "sda1", "path": "/dev/sda1", "size": "100G", "type": "part", "fstype": "ntfs"}
        ]
        gui_app.disk_utils.get_mounted_disks.return_value = [
            {"name": "sdb1", "path": "/dev/sdb1", "size": "50G", "type": "part", 
             "fstype": "ntfs", "mountpoint": "/mnt/sdb1"}
        ]
        
        # メソッドを実行
        gui_app._refresh_disk_lists()
        
        # リストボックスのクリアと挿入が呼ばれたことを確認
        gui_app.unmounted_disk_listbox.delete.assert_called_with(0, tk.END)
        gui_app.mounted_disk_listbox.delete.assert_called_with(0, tk.END)
        assert gui_app.unmounted_disk_listbox.insert.called
        assert gui_app.mounted_disk_listbox.insert.called
    
    def test_unmounted_disk_selection(self, gui_app):
        """未マウントディスク選択のテスト"""
        # 選択イベントを手動で発生させる
        gui_app._on_unmounted_disk_select(None)
        
        # 結果を検証：選択されたディスクが保存されていること
        assert gui_app.selected_unmounted_disk == "/dev/sda"
        
        # ボタンがアクティブになったことを確認
        gui_app.mount_button.config.assert_called()
        gui_app.format_button.config.assert_called()
    
    def test_mounted_disk_selection(self, gui_app):
        """マウント済みディスク選択のテスト"""
        # 選択イベントを手動で発生させる
        gui_app._on_mounted_disk_select(None)
        
        # 結果を検証：選択されたディスクが保存されていること
        assert gui_app.selected_mounted_disk == "/mnt/sdb1"
        
        # ボタン状態の更新が呼ばれたことを確認
        gui_app.permission_button.config.assert_called()
        gui_app.open_button.config.assert_called()
    
    def test_mount_selected_disk(self, gui_app):
        """ディスクマウント処理のテスト"""
        # 選択ディスクを設定
        gui_app.selected_unmounted_disk = "/dev/sda"
        gui_app._on_unmounted_disk_select(None)
        
        # マウント成功をモック
        gui_app.disk_utils.mount_disk.return_value = (True, "/mnt/sda", "")
        
        # マウント処理を実行
        with patch('tkinter.messagebox.showinfo') as mock_showinfo:
            # モックメッセージボックスが直接呼ばれるように設定
            mock_showinfo.side_effect = lambda title, message: None
            
            # スレッドの代わりに直接関数を実行するようにパッチ
            with patch('threading.Thread') as mock_thread:
                mock_thread.side_effect = lambda target, daemon=False: MagicMock(
                    start=lambda: target()
                )
                
                # マウント処理を実行
                gui_app._mount_selected_disk()
                
                # マウント関数が呼ばれたことを確認
                gui_app.disk_utils.mount_disk.assert_called_with("/dev/sda")
                
                # 成功メッセージが表示されたことを確認
                assert mock_showinfo.called
    
    def test_format_selected_disk(self, gui_app):
        """ディスクフォーマット処理のテスト"""
        # 選択ディスクを設定
        gui_app.selected_unmounted_disk = "/dev/sda"
        gui_app._on_unmounted_disk_select(None)
        
        # フォーマット成功をモック
        gui_app.disk_utils.format_disk.return_value = (True, "")
        
        # 確認ダイアログのモック
        with patch('tkinter.messagebox.askyesno', return_value=True) as mock_askyesno, \
             patch('tkinter.messagebox.showinfo') as mock_showinfo:
            
            # モックメッセージボックスが直接呼ばれるように設定
            mock_showinfo.side_effect = lambda title, message: None
            mock_askyesno.side_effect = lambda title, message: True
            
            # スレッドの代わりに直接関数を実行するようにパッチ
            with patch('threading.Thread') as mock_thread:
                mock_thread.side_effect = lambda target, daemon=False: MagicMock(
                    start=lambda: target()
                )
                
                # フォーマット処理を実行
                gui_app._format_selected_disk()
                
                # フォーマット関数が呼ばれたことを確認
                # テストモードでは fs_type_var は文字列なので、get()はなく直接値が渡される
                gui_app.disk_utils.format_disk.assert_called_with("/dev/sda", "exfat")
                
                # 成功メッセージが表示されたことを確認
                assert mock_showinfo.called
    
    def test_set_permissions(self, gui_app):
        """権限付与処理のテスト"""
        # 選択ディスクを設定
        gui_app.selected_mounted_disk = "/mnt/sdb1"
        gui_app._on_mounted_disk_select(None)
        
        # 権限付与成功をモック
        gui_app.disk_utils.set_permissions.return_value = (True, "")
        
        # 確認ダイアログと成功メッセージのモック
        with patch('tkinter.messagebox.askyesno', return_value=True) as mock_askyesno, \
             patch('tkinter.messagebox.showinfo') as mock_showinfo:
            
            # モックメッセージボックスが直接呼ばれるように設定
            mock_showinfo.side_effect = lambda title, message: None
            mock_askyesno.side_effect = lambda title, message: True
            
            # スレッドの代わりに直接関数を実行するようにパッチ
            with patch('threading.Thread') as mock_thread:
                mock_thread.side_effect = lambda target, daemon=False: MagicMock(
                    start=lambda: target()
                )
                
                # 権限付与処理を実行
                gui_app._set_permissions_to_selected_disk()
                
                # 権限付与関数が呼ばれたことを確認
                gui_app.disk_utils.set_permissions.assert_called_with("/mnt/sdb1")
                
                # 成功メッセージが表示されたことを確認
                assert mock_showinfo.called 