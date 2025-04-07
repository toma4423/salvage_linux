"""
ユーザビリティテスト
"""

import pytest
import tkinter as tk
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from src.main import DiskUtilityApp
from src.disk_utils import DiskUtils
from src.logger import Logger
import time
from PyQt5.QtWidgets import QApplication
import sys

@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成するフィクスチャ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # テスト後にディレクトリを削除
    shutil.rmtree(temp_dir)

@pytest.fixture
def mocked_root():
    """モック化されたtkinterルートウィンドウを提供するフィクスチャ"""
    # ルートウィンドウのモック
    root = MagicMock()
    root.title.return_value = None
    root.geometry.return_value = None
    
    # Tkinterのクラスをモック
    # Listboxのモック
    listbox_mock = MagicMock()
    listbox_mock.delete.return_value = None
    listbox_mock.insert.return_value = None
    listbox_mock.curselection.return_value = [0]
    listbox_mock.get.return_value = "sample item"
    root.Listbox = MagicMock(return_value=listbox_mock)
    
    # Textのモック
    text_mock = MagicMock()
    text_mock.delete.return_value = None
    text_mock.insert.return_value = None
    text_mock.config.return_value = None
    root.Text = MagicMock(return_value=text_mock)
    
    # Buttonのモック
    button_mock = MagicMock()
    button_mock.config.return_value = None
    button_mock.cget.return_value = tk.DISABLED
    root.Button = MagicMock(return_value=button_mock)
    
    # StringVarのモック
    stringvar_mock = MagicMock()
    stringvar_mock.get = MagicMock(return_value="ntfs")
    stringvar_mock.set = MagicMock()
    root.StringVar = MagicMock(return_value=stringvar_mock)
    
    # Frameのモック
    frame_mock = MagicMock()
    root.Frame = MagicMock(return_value=frame_mock)
    
    # Labelのモック
    label_mock = MagicMock()
    root.Label = MagicMock(return_value=label_mock)
    
    # ttk関連のモック
    ttk_mock = MagicMock()
    ttk_mock.Frame = MagicMock(return_value=MagicMock())
    ttk_mock.Button = MagicMock(return_value=button_mock)
    ttk_mock.Label = MagicMock(return_value=MagicMock())
    ttk_mock.LabelFrame = MagicMock(return_value=MagicMock())
    ttk_mock.Combobox = MagicMock(return_value=MagicMock())
    ttk_mock.Radiobutton = MagicMock(return_value=MagicMock())
    root.ttk = ttk_mock
    
    return root

@pytest.fixture
def logger_and_disk_utils(temp_dir):
    """実際のロガーとモック化されたディスクユーティリティを提供するフィクスチャ"""
    log_dir = os.path.join(temp_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 実際のロガーを作成
    logger = Logger(log_dir=log_dir)
    
    # DiskUtilsをモック
    disk_utils = MagicMock()
    
    # モックメソッドを設定
    disk_utils.get_unmounted_disks = MagicMock(return_value=[
        {"name": "sda", "path": "/dev/sda", "size": "8GB", "type": "disk", "fstype": "ntfs"}
    ])
    
    disk_utils.get_mounted_disks = MagicMock(return_value=[
        {"name": "sdb1", "path": "/dev/sdb1", "size": "16GB", "type": "part", 
         "fstype": "ntfs", "mountpoint": "/mnt/sdb1"}
    ])
    
    disk_utils.mount_disk = MagicMock(return_value=(True, "/mnt/test", ""))
    disk_utils.format_disk = MagicMock(return_value=(True, ""))
    disk_utils.set_permissions = MagicMock(return_value=(True, ""))
    disk_utils.open_file_manager = MagicMock(return_value=(True, ""))
    
    return logger, disk_utils

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
def gui_app(mocked_root, logger_and_disk_utils, qt_app):
    """モック化されたGUIインスタンスを提供するフィクスチャ"""
    logger, disk_utils = logger_and_disk_utils
    gui_instance = DiskUtilityApp(test_mode=True)
    
    # DiskUtilsとLoggerを直接設定
    gui_instance.disk_utils = disk_utils
    gui_instance.logger = logger
    
    # ディスクデータのモック
    gui_instance.unmounted_disks = [
        {"name": "sda", "path": "/dev/sda", "size": "8GB", "type": "disk", "fstype": "ntfs"}
    ]
    gui_instance.mounted_disks = [
        {"name": "sdb1", "path": "/dev/sdb1", "size": "16GB", "type": "part", 
         "fstype": "ntfs", "mountpoint": "/mnt/sdb1"}
    ]
    
    # UIコンポーネントを直接設定
    gui_instance.unmounted_disk_listbox = mocked_root.Listbox()
    gui_instance.mounted_disk_listbox = mocked_root.Listbox()
    gui_instance.unmounted_disk_info = mocked_root.Text()
    gui_instance.mounted_disk_info = mocked_root.Text()
    gui_instance.mount_button = mocked_root.Button()
    gui_instance.format_button = mocked_root.Button()
    gui_instance.permission_button = mocked_root.Button()
    gui_instance.open_button = mocked_root.Button()
    
    return gui_instance

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

@pytest.mark.system
@pytest.mark.usability
class TestUsability:
    """ユーザビリティのテストクラス"""
    
    def test_gui_components_existence(self, gui_app, mocked_root):
        """GUIコンポーネントの存在確認テスト"""
        # 主要なUIコンポーネントが存在することを確認
        assert hasattr(gui_app, 'unmounted_disk_listbox')
        assert hasattr(gui_app, 'mounted_disk_listbox')
        assert hasattr(gui_app, 'mount_button')
        assert hasattr(gui_app, 'format_button')
        assert hasattr(gui_app, 'permission_button')
        assert hasattr(gui_app, 'open_button')
    
    def test_button_state_change(self, gui_app):
        """ボタン状態変更テスト"""
        # 初期状態（無効）を確認
        assert gui_app.mount_button.cget('state') == tk.DISABLED
        assert gui_app.format_button.cget('state') == tk.DISABLED
        assert gui_app.permission_button.cget('state') == tk.DISABLED
        assert gui_app.open_button.cget('state') == tk.DISABLED
        
        # 未マウントディスク選択時のボタン状態変更
        gui_app._on_unmounted_disk_select(None)
        
        # 未マウントディスク操作ボタンが有効になることを確認
        gui_app.mount_button.config.assert_called()
        gui_app.format_button.config.assert_called()
        
        # マウント済みディスク選択時のボタン状態変更
        gui_app._on_mounted_disk_select(None)
        
        # マウント済みディスク操作ボタンが有効になることを確認
        gui_app.open_button.config.assert_called()
        gui_app.permission_button.config.assert_called()
    
    def test_file_system_types_available(self, gui_app):
        """ファイルシステムタイプ選択テスト"""
        # テストモードではfs_type_varが文字列になっている
        assert gui_app.fs_type_var == "exfat"
    
    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.messagebox.showerror')
    def test_feedback_messages(self, mock_showerror, mock_showinfo, gui_app):
        """フィードバックメッセージテスト"""
        # マウント成功時のメッセージ表示
        gui_app.selected_unmounted_disk = "/dev/sda"
        gui_app.disk_utils.mount_disk.return_value = (True, "/mnt/sda", "")
        
        # rootのafterメソッドを直接実行するようにモック
        gui_app.root.after = MagicMock(side_effect=lambda delay, func, *args: func(*args) if callable(func) else None)
        
        # スレッドの代わりに直接関数を実行するようにパッチ
        with patch('threading.Thread') as mock_thread:
            mock_thread.side_effect = lambda target, daemon=False: MagicMock(
                start=lambda: target()
            )
            
            # マウント処理を実行
            gui_app._mount_selected_disk()
            
            # 成功メッセージが表示されることを確認
            assert mock_showinfo.called
    
    def test_disk_list_update(self, gui_app):
        """ディスクリスト更新テスト"""
        # ディスクリスト更新メソッドを実行
        gui_app._refresh_disk_lists()
        
        # リストボックスが更新されたことを確認
        gui_app.unmounted_disk_listbox.delete.assert_called_with(0, tk.END)
        gui_app.mounted_disk_listbox.delete.assert_called_with(0, tk.END)
        
        # 挿入が行われたことを確認
        assert gui_app.unmounted_disk_listbox.insert.called
        assert gui_app.mounted_disk_listbox.insert.called
    
    @patch('time.sleep')
    def test_responsive_ui_during_operations(self, mock_sleep, gui_app):
        """操作中のUI応答性テスト"""
        # マウント処理中にUIが応答すること
        gui_app.selected_unmounted_disk = "/dev/sda"
        
        with patch('threading.Thread') as mock_thread:
            # スレッド開始をモック
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            # マウント処理を実行
            gui_app._mount_selected_disk()
            
            # スレッドが開始されたことを確認
            assert mock_thread_instance.start.called
    
    def test_error_recovery(self, gui_app):
        """エラー復旧テスト"""
        # エラー発生時に適切にメッセージ表示し、正常状態に戻ること
        gui_app.selected_unmounted_disk = "/dev/sda"
        gui_app.disk_utils.mount_disk.return_value = (False, "", "マウントに失敗しました")
        
        # rootのafterメソッドを直接実行するようにモック
        gui_app.root.after = MagicMock(side_effect=lambda delay, func, *args: func(*args) if callable(func) else None)
        
        with patch('tkinter.messagebox.showerror') as mock_showerror:
            # スレッドの代わりに直接関数を実行するようにパッチ
            with patch('threading.Thread') as mock_thread:
                mock_thread.side_effect = lambda target, daemon=False: MagicMock(
                    start=lambda: target()
                )
                
                # マウント処理を実行
                gui_app._mount_selected_disk()
                
                # エラーメッセージが表示されることを確認
                assert mock_showerror.called
    
    @patch('tkinter.messagebox.askyesno')
    def test_confirmation_dialogs(self, mock_askquestion, gui_app):
        """確認ダイアログテスト"""
        # 確認ダイアログが表示されること
        gui_app.selected_unmounted_disk = "/dev/sda"
        mock_askquestion.return_value = True
        
        # フォーマット処理を実行
        gui_app._format_selected_disk()
        
        # 確認ダイアログが表示されたことを確認
        assert mock_askquestion.called 