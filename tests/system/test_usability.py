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

@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成するフィクスチャ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # テスト後にディレクトリを削除
    shutil.rmtree(temp_dir)

@pytest.fixture
def mocked_root():
    """モック化されたTkinterルートウィンドウを提供するフィクスチャ"""
    root = MagicMock(spec=tk.Tk)
    
    # Frameのモックを作成
    frame_mock = MagicMock(spec=tk.Frame)
    root.Frame.return_value = frame_mock
    
    # Listboxのモックを作成
    listbox_mock = MagicMock(spec=tk.Listbox)
    root.Listbox.return_value = listbox_mock
    
    # 他のウィジェットも同様にモック化
    button_mock = MagicMock(spec=tk.Button)
    root.Button.return_value = button_mock
    
    label_mock = MagicMock(spec=tk.Label)
    root.Label.return_value = label_mock
    
    combobox_mock = MagicMock()
    root.ttk.Combobox.return_value = combobox_mock
    
    # pack, gridなどのレイアウトメソッドも準備
    frame_mock.pack.return_value = None
    listbox_mock.pack.return_value = None
    button_mock.pack.return_value = None
    label_mock.pack.return_value = None
    
    return root

@pytest.fixture
def logger_and_disk_utils(temp_dir):
    """実際のロガーとディスクユーティリティを提供するフィクスチャ"""
    log_dir = os.path.join(temp_dir, "logs")
    logger = Logger(log_dir=log_dir)
    disk_utils = DiskUtils(logger)
    
    return logger, disk_utils

@pytest.fixture
def gui_app(mocked_root, logger_and_disk_utils):
    """モック化されたGUIインスタンスを提供するフィクスチャ"""
    logger, disk_utils = logger_and_disk_utils
    gui_instance = DiskUtilityApp(mocked_root)
    # DiskUtilsとLoggerを直接設定
    gui_instance.disk_utils = disk_utils
    gui_instance.logger = logger
    return gui_instance

@pytest.mark.system
@pytest.mark.usability
class TestUsability:
    """ユーザビリティテスト"""
    
    def test_gui_components_existence(self, gui_app, mocked_root):
        """GUIの必要なコンポーネントが存在することを確認するテスト"""
        # 必要なコンポーネントが作成されていることを確認
        assert hasattr(gui_app, 'unmounted_disk_listbox')
        assert hasattr(gui_app, 'mounted_disk_listbox')
        assert hasattr(gui_app, 'format_button')
        assert hasattr(gui_app, 'mount_button')
        assert hasattr(gui_app, 'permissions_button')
        assert hasattr(gui_app, 'open_button')
        assert hasattr(gui_app, 'fs_type_combobox')
    
    def test_button_state_change(self, gui_app):
        """ディスク選択時にボタンの状態が適切に変化することを確認するテスト"""
        # 初期状態ではボタンは無効化されているはず
        gui_app.mount_button.config.assert_called_with(state=tk.DISABLED)
        gui_app.format_button.config.assert_called_with(state=tk.DISABLED)
        gui_app.permissions_button.config.assert_called_with(state=tk.DISABLED)
        gui_app.open_button.config.assert_called_with(state=tk.DISABLED)
        
        # 未マウントディスクを選択した状態をシミュレート
        gui_app.unmounted_disk_listbox.curselection.return_value = (0,)
        gui_app.unmounted_disk_listbox.get.return_value = "/dev/sda1"
        gui_app.mounted_disk_listbox.curselection.return_value = ()
        
        # 未マウントディスク選択時のイベントハンドラを呼び出し
        gui_app._on_unmounted_disk_select(None)
        
        # マウントとフォーマットボタンが有効化され、権限とオープンボタンが無効化されていることを確認
        gui_app.mount_button.config.assert_called_with(state=tk.NORMAL)
        gui_app.format_button.config.assert_called_with(state=tk.NORMAL)
        gui_app.permissions_button.config.assert_called_with(state=tk.DISABLED)
        gui_app.open_button.config.assert_called_with(state=tk.DISABLED)
        
        # マウント済みディスクを選択した状態をシミュレート
        gui_app.unmounted_disk_listbox.curselection.return_value = ()
        gui_app.mounted_disk_listbox.curselection.return_value = (0,)
        gui_app.mounted_disk_listbox.get.return_value = "/mnt/sda1"
        
        # マウント済みディスク選択時のイベントハンドラを呼び出し
        gui_app._on_mounted_disk_select(None)
        
        # 権限とオープンボタンが有効化され、マウントとフォーマットボタンが無効化されていることを確認
        gui_app.mount_button.config.assert_called_with(state=tk.DISABLED)
        gui_app.format_button.config.assert_called_with(state=tk.DISABLED)
        gui_app.permissions_button.config.assert_called_with(state=tk.NORMAL)
        gui_app.open_button.config.assert_called_with(state=tk.NORMAL)
    
    def test_file_system_types_available(self, gui_app):
        """利用可能なファイルシステムタイプがコンボボックスに表示されることを確認するテスト"""
        # コンボボックスの値を確認
        gui_app.fs_type_combobox.config.assert_called()
        
        # 少なくとも必須のファイルシステムタイプがあることを確認
        required_fs_types = ["ntfs", "exfat", "ext4", "fat32"]
        fs_type_values = gui_app.fs_type_values
        
        for fs_type in required_fs_types:
            assert fs_type in fs_type_values
    
    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.messagebox.showerror')
    def test_feedback_messages(self, mock_showerror, mock_showinfo, gui_app):
        """操作時のフィードバックメッセージが適切に表示されることを確認するテスト"""
        # 成功メッセージの表示テスト
        gui_app.show_success_message("テスト成功")
        mock_showinfo.assert_called_with("成功", "テスト成功")
        
        # エラーメッセージの表示テスト
        gui_app.show_error_message("テストエラー")
        mock_showerror.assert_called_with("エラー", "テストエラー")
    
    def test_disk_list_update(self, gui_app):
        """ディスクリストが適切に更新されることを確認するテスト"""
        # モックディスクリストを設定
        unmounted_disks = ["/dev/sda1", "/dev/sdb1"]
        mounted_disks = ["/mnt/sdc1", "/mnt/sdd1"]
        
        # ディスクユーティリティのモックメソッドに戻り値を設定
        gui_app.disk_utils.get_unmounted_disks = MagicMock(return_value=unmounted_disks)
        gui_app.disk_utils.get_mounted_disks = MagicMock(return_value=mounted_disks)
        
        # リスト更新メソッドを呼び出し
        gui_app._refresh_disk_lists()
        
        # リストボックスが正しく更新されたことを確認
        gui_app.unmounted_disk_listbox.delete.assert_called_with(0, tk.END)
        gui_app.mounted_disk_listbox.delete.assert_called_with(0, tk.END)
        
        # 未マウントディスクがリストに追加されたことを確認
        for disk in unmounted_disks:
            gui_app.unmounted_disk_listbox.insert.assert_any_call(tk.END, disk)
        
        # マウント済みディスクがリストに追加されたことを確認
        for disk in mounted_disks:
            gui_app.mounted_disk_listbox.insert.assert_any_call(tk.END, disk)
    
    @patch('time.sleep')
    def test_responsive_ui_during_operations(self, mock_sleep, gui_app):
        """操作中にUIが応答し続けることを確認するテスト"""
        # ディスクフォーマット操作をシミュレート
        gui_app.disk_utils.format_disk = MagicMock(side_effect=lambda disk, fs_type: (mock_sleep(1), (True, "成功"))[1])
        
        # 未マウントディスクを選択した状態をシミュレート
        gui_app.selected_unmounted_disk = "/dev/sda1"
        gui_app.fs_type_combobox.get = MagicMock(return_value="ntfs")
        
        # フォーマット操作を実行
        gui_app._format_selected_disk()
        
        # UI更新メソッドが呼び出されたことを確認
        assert gui_app.root.update_idletasks.called
    
    def test_error_recovery(self, gui_app):
        """エラー発生時に適切に回復することを確認するテスト"""
        # エラーを発生させるモックメソッドを設定
        gui_app.disk_utils.mount_disk = MagicMock(return_value=(False, "テストエラー"))
        
        # 未マウントディスクを選択した状態をシミュレート
        gui_app.selected_unmounted_disk = "/dev/sda1"
        
        # マウント操作を実行
        gui_app._mount_selected_disk()
        
        # エラーが発生してもUIが応答し続けることを確認
        assert gui_app.root.update_idletasks.called
        
        # ディスクリストが再更新されることを確認
        gui_app._refresh_disk_lists.assert_called()
    
    @patch('tkinter.messagebox.askquestion')
    def test_confirmation_dialogs(self, mock_askquestion, gui_app):
        """確認ダイアログが適切に表示されることを確認するテスト"""
        # askquestionの戻り値を設定
        mock_askquestion.return_value = "yes"
        
        # 未マウントディスクを選択した状態をシミュレート
        gui_app.selected_unmounted_disk = "/dev/sda1"
        gui_app.fs_type_combobox.get = MagicMock(return_value="ntfs")
        gui_app.disk_utils.format_disk = MagicMock(return_value=(True, "成功"))
        
        # フォーマット操作を実行
        gui_app._format_selected_disk()
        
        # 確認ダイアログが表示されたことを確認
        mock_askquestion.assert_called()
        assert "確認" in mock_askquestion.call_args[0][0]
        assert "フォーマット" in mock_askquestion.call_args[0][1] 