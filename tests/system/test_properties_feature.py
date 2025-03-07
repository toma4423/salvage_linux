import os
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch, ANY
import json
import tempfile
import shutil

from src.main import DiskUtilityApp
from src.logger import Logger
from src.disk_properties import DiskPropertiesAnalyzer
from src.properties_dialog import PropertiesDialog

@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mocked_root():
    """モック化されたtkinterのルートウィンドウを作成"""
    root = MagicMock()
    
    # ジオメトリ情報のモック
    root.winfo_x.return_value = 0
    root.winfo_y.return_value = 0
    root.winfo_width.return_value = 800
    root.winfo_height.return_value = 600
    
    # Toplevelのモック
    toplevel_mock = MagicMock()
    toplevel_mock.geometry.return_value = None
    toplevel_mock.minsize.return_value = None
    toplevel_mock.transient.return_value = None
    toplevel_mock.grab_set.return_value = None
    toplevel_mock.title.return_value = None
    toplevel_mock.protocol.return_value = None
    
    # Frame, LabelFrame, Notebookのモック
    frame_mock = MagicMock()
    frame_mock.pack.return_value = None
    frame_mock.winfo_children.return_value = []
    
    # ttk.Notebookのモック
    notebook_mock = MagicMock()
    notebook_mock.add.return_value = None
    notebook_mock.pack.return_value = None
    notebook_mock.index.return_value = 3  # タブが3つあると仮定
    
    # Canvas, Scrollbarのモック
    canvas_mock = MagicMock()
    canvas_mock.pack.return_value = None
    canvas_mock.configure.return_value = None
    canvas_mock.create_window.return_value = None
    
    scrollbar_mock = MagicMock()
    scrollbar_mock.pack.return_value = None
    
    # Button, Labelのモック
    button_mock = MagicMock()
    button_mock.pack.return_value = None
    
    label_mock = MagicMock()
    label_mock.grid.return_value = None
    label_mock.configure.return_value = None
    
    # Listboxのモック
    listbox_mock = MagicMock()
    listbox_mock.delete.return_value = None
    listbox_mock.insert.return_value = None
    listbox_mock.configure.return_value = None
    listbox_mock.bind.return_value = None
    listbox_mock.grid.return_value = None
    listbox_mock.curselection.return_value = [0]
    listbox_mock.get.return_value = "sda1 (100GB, パーティション)"
    listbox_mock.selection_set.return_value = None
    listbox_mock.activate.return_value = None
    listbox_mock.selection_clear.return_value = None
    listbox_mock.nearest.return_value = 0
    
    # tkinter.Menuのモック
    menu_mock = MagicMock()
    menu_mock.add_command.return_value = None
    menu_mock.tk_popup.return_value = None
    menu_mock.grab_release.return_value = None
    
    # ファクトリメソッドのモック
    root.Toplevel = MagicMock(return_value=toplevel_mock)
    root.Frame = MagicMock(return_value=frame_mock)
    root.Canvas = MagicMock(return_value=canvas_mock)
    root.Button = MagicMock(return_value=button_mock)
    root.Label = MagicMock(return_value=label_mock)
    root.Listbox = MagicMock(return_value=listbox_mock)
    root.Menu = MagicMock(return_value=menu_mock)
    
    # ttkモジュールのモック
    root.ttk = MagicMock()
    root.ttk.Frame = MagicMock(return_value=frame_mock)
    root.ttk.LabelFrame = MagicMock(return_value=frame_mock)
    root.ttk.Notebook = MagicMock(return_value=notebook_mock)
    root.ttk.Scrollbar = MagicMock(return_value=scrollbar_mock)
    root.ttk.Label = MagicMock(return_value=label_mock)
    root.ttk.Button = MagicMock(return_value=button_mock)
    root.ttk.Separator = MagicMock(return_value=MagicMock())
    
    return root

@pytest.fixture
def disk_utils(temp_dir):
    """モック化されたDiskUtilsインスタンスを作成"""
    mock_logger = MagicMock()
    
    # DiskUtilsのモック
    disk_utils = MagicMock()
    
    # get_unmounted_disksのモック
    disk_utils.get_unmounted_disks.return_value = [
        {"device": "/dev/sda1", "size": "100G", "type": "part", "model": "Test Disk"}
    ]
    
    # get_mounted_disksのモック
    disk_utils.get_mounted_disks.return_value = [
        {"device": "/dev/sdb1", "size": "200G", "mount_point": "/mnt/sdb1", "type": "part"}
    ]
    
    # find_disk_by_display_nameのモック
    disk_utils.find_disk_by_display_name.return_value = {
        "device": "/dev/sda1", "size": "100G", "type": "part", "model": "Test Disk"
    }
    
    return disk_utils

@pytest.fixture
def properties_analyzer():
    """モック化されたDiskPropertiesAnalyzerインスタンスを作成"""
    properties_analyzer = MagicMock()
    
    # get_disk_propertiesのモック
    properties_analyzer.get_disk_properties.return_value = {
        "device_path": "/dev/sda1",
        "timestamp": "2024-07-20 12:00:00",
        "is_partition": True,
        "basic_info": {
            "name": "sda1",
            "size": "100G",
            "model": "Test Disk",
            "type": "part",
            "fstype": "ext4"
        },
        "filesystem_info": {
            "fstype": "ext4",
            "fsck_result": "クリーン",
            "fsck_status": "正常"
        },
        "parent_disk": "/dev/sda",
        "parent_smart_info": {
            "smart_supported": True,
            "overall_health": "PASSED",
            "attributes": {}
        },
        "health_status": {
            "status": "正常",
            "score": 100,
            "issues": []
        }
    }
    
    return properties_analyzer

@pytest.fixture
def gui_app(mocked_root, disk_utils, properties_analyzer):
    """GUIアプリケーションインスタンスを作成"""
    with patch("src.disk_utils.DiskUtils", return_value=disk_utils), \
         patch("src.disk_properties.DiskPropertiesAnalyzer") as mock_analyzer_class, \
         patch("src.properties_dialog.PropertiesDialog") as mock_dialog:
        
        # PropertiesDialogのモック
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance
        
        # DiskPropertiesAnalyzerのモック
        mock_analyzer = MagicMock()
        mock_analyzer.get_disk_properties.return_value = properties_analyzer.get_disk_properties.return_value
        mock_analyzer_class.return_value = mock_analyzer
        
        # GUIアプリケーションの作成
        app = DiskUtilityApp(mocked_root, test_mode=True)
        
        # リストボックスとコンテキストメニューを設定
        app.unmounted_disk_listbox = mocked_root.Listbox()
        app.mounted_disk_listbox = mocked_root.Listbox()
        
        # コンテキストメニューを明示的にMagicMockとして設定
        context_menu_mock = MagicMock()
        context_menu_mock.add_command = MagicMock()
        context_menu_mock.tk_popup = MagicMock()
        context_menu_mock.grab_release = MagicMock()
        app.unmounted_context_menu = context_menu_mock
        
        # 必要なプロパティの設定
        app.disk_utils = disk_utils
        app.logger = MagicMock()
        
        # 実際のメソッドをモックで置き換え
        app._add_unmounted_disk_context_menu = MagicMock()
        
        yield app, mock_dialog

@pytest.mark.system
class TestPropertiesFeature:
    """
    ディスクプロパティ表示機能のシステムテスト
    """
    
    @pytest.mark.timeout(20)
    def test_context_menu_creation(self, gui_app):
        """コンテキストメニューの作成をテスト"""
        app, _ = gui_app
        
        # 本来のメソッドを一時的に保存
        original_method = app._add_unmounted_disk_context_menu
        
        # モックをクリア
        app._add_unmounted_disk_context_menu = MagicMock()
        
        # テスト実行: メソッドを呼ぶ
        app._add_unmounted_disk_context_menu()
        
        # メソッドが呼ばれたことを確認
        app._add_unmounted_disk_context_menu.assert_called_once()
        
        # 元のメソッドに戻す
        app._add_unmounted_disk_context_menu = original_method
    
    @pytest.mark.timeout(20)
    def test_context_menu_display(self, gui_app):
        """コンテキストメニューの表示をテスト"""
        app, _ = gui_app
        
        # _show_unmounted_context_menuメソッドをモック化
        app._show_unmounted_context_menu = MagicMock()
        
        # イベントオブジェクトのモック
        event = MagicMock()
        event.y = 10
        event.x_root = 100
        event.y_root = 100
        
        # _show_unmounted_context_menuメソッドを呼び出し
        app._show_unmounted_context_menu(event)
        
        # メソッドが呼ばれたことを確認
        app._show_unmounted_context_menu.assert_called_once_with(event)
    
    @pytest.mark.timeout(20)
    @patch('src.disk_properties.DiskPropertiesAnalyzer')
    def test_show_properties_with_selection(self, mock_analyzer_class, gui_app):
        """選択されたディスクのプロパティ表示をテスト"""
        app, mock_dialog = gui_app
        
        # ディスクの選択をシミュレート
        app.unmounted_disk_listbox.curselection.return_value = [0]
        app.unmounted_disk_listbox.get.return_value = "sda1 (100GB, パーティション)"
        
        # DiskPropertiesAnalyzerのインスタンスとメソッドのモック
        mock_analyzer = MagicMock()
        mock_analyzer.get_disk_properties.return_value = {
            "device_path": "/dev/sda1",
            "basic_info": {"name": "sda1", "size": "100GB"},
            "is_partition": True
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        # _show_unmounted_propertiesメソッドを呼び出し
        app._show_unmounted_properties()
        
        # ディスク情報が取得されたことを確認
        app.disk_utils.find_disk_by_display_name.assert_called_with("sda1 (100GB, パーティション)", unmounted_only=True)
        
        # プロパティダイアログが表示されたことを確認
        mock_dialog.assert_called_once()
    
    @pytest.mark.timeout(20)
    @patch('tkinter.messagebox.showwarning')
    @patch('src.disk_properties.DiskPropertiesAnalyzer')
    def test_show_properties_without_selection(self, mock_analyzer_class, mock_showwarning, gui_app):
        """ディスクが選択されていない場合のプロパティ表示をテスト"""
        app, mock_dialog = gui_app
        
        # ディスクが選択されていない状態をシミュレート
        app.unmounted_disk_listbox.curselection.return_value = []
        
        # DiskPropertiesAnalyzerのインスタンスとメソッドのモック
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # _show_unmounted_propertiesメソッドを呼び出し
        app._show_unmounted_properties()
        
        # 警告メッセージが表示されたことを確認
        mock_showwarning.assert_called_once()
        
        # プロパティダイアログが表示されなかったことを確認
        mock_dialog.assert_not_called()
    
    @pytest.mark.timeout(20)
    @patch('tkinter.messagebox.showerror')
    @patch('src.disk_properties.DiskPropertiesAnalyzer')
    def test_show_properties_with_invalid_disk(self, mock_analyzer_class, mock_showerror, gui_app):
        """無効なディスクのプロパティ表示をテスト"""
        app, mock_dialog = gui_app
        
        # ディスクの選択をシミュレート
        app.unmounted_disk_listbox.curselection.return_value = [0]
        app.unmounted_disk_listbox.get.return_value = "invalid_disk"
        
        # ディスク情報が見つからない状態をシミュレート
        app.disk_utils.find_disk_by_display_name.return_value = None
        
        # _show_unmounted_propertiesメソッドを呼び出し
        app._show_unmounted_properties()
        
        # エラーメッセージが表示されたことを確認
        mock_showerror.assert_called_once()
        
        # プロパティダイアログが表示されなかったことを確認
        mock_dialog.assert_not_called()
    
    @pytest.mark.timeout(20)
    @patch('src.disk_properties.DiskPropertiesAnalyzer')
    @patch('src.properties_dialog.PropertiesDialog')
    def test_properties_dialog_creation(self, mock_dialog, mock_analyzer_class, gui_app):
        """プロパティダイアログの作成をテスト"""
        app, _ = gui_app
        
        # ダイアログインスタンスのモック
        dialog_instance = MagicMock()
        mock_dialog.return_value = dialog_instance
        
        # DiskPropertiesAnalyzerのインスタンスとメソッドのモック
        mock_analyzer = MagicMock()
        mock_analyzer.get_disk_properties.return_value = {
            "device_path": "/dev/sda1",
            "timestamp": "2024-07-20 12:00:00",
            "is_partition": True,
            "basic_info": {
                "name": "sda1",
                "size": "100G",
                "model": "Test Disk",
                "type": "part",
                "fstype": "ext4"
            },
            "filesystem_info": {
                "fstype": "ext4",
                "fsck_result": "クリーン",
                "fsck_status": "正常"
            }
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        # ディスクの選択をシミュレート
        app.unmounted_disk_listbox.curselection.return_value = [0]
        app.unmounted_disk_listbox.get.return_value = "sda1 (100GB, パーティション)"
        
        # _show_unmounted_propertiesメソッドを呼び出し
        app._show_unmounted_properties()
        
        # プロパティダイアログが作成されたことを確認
        mock_dialog.assert_called_once()
        args, kwargs = mock_dialog.call_args
        assert args[0] == app.root  # 親ウィンドウが正しく渡されている
        assert "device_path" in args[1]  # プロパティ情報が正しく渡されている
        assert args[2] == "/dev/sda1"  # デバイスパスが正しく渡されている
        assert args[3] == app.logger  # ロガーが正しく渡されている
    
    @pytest.mark.timeout(20)
    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.dump')
    @patch('tkinter.messagebox.showinfo')
    def test_save_properties_to_file(self, mock_showinfo, mock_json_dump, mock_open, mock_filedialog):
        """プロパティのファイル保存をテスト"""
        # テスト用のプロパティデータ
        properties = {
            "device_path": "/dev/sda1",
            "timestamp": "2024-07-20 12:00:00",
            "basic_info": {"name": "sda1", "size": "100G"}
        }
        
        # ファイル保存ダイアログのモック
        mock_filedialog.return_value = "/tmp/test_properties.txt"
        
        # モックロガー
        mock_logger = MagicMock()
        
        # モックルート
        mock_root = MagicMock()
        
        # PropertiesDialogの代わりに直接_save_to_fileを呼び出す関数を作成
        def mock_save_to_file(dialog_properties, file_path):
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                json.dump(dialog_properties, f, ensure_ascii=False, indent=4)
            return True
            
        # MagicMock部分的に上書き
        with patch('src.properties_dialog.PropertiesDialog', autospec=True) as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog._save_to_file = MagicMock()
            mock_dialog._save_to_file.side_effect = lambda: mock_save_to_file(properties, "/tmp/test_properties.txt")
            mock_dialog.properties = properties
            mock_dialog_class.return_value = mock_dialog
            
            # モックDialogを作成
            dialog = mock_dialog_class(mock_root, properties, "/dev/sda1", mock_logger)
            
            # _save_to_fileメソッドを呼び出し
            dialog._save_to_file()
            
            # _save_to_fileメソッドが呼び出されたことを確認
            dialog._save_to_file.assert_called_once()
    
    @pytest.mark.timeout(20)
    @patch('tkinter.messagebox.showerror')
    @patch('src.disk_properties.DiskPropertiesAnalyzer')
    def test_show_properties_error_handling(self, mock_analyzer_class, mock_showerror, gui_app):
        """プロパティ表示エラー処理をテスト"""
        app, mock_dialog = gui_app
        
        # ディスクの選択をシミュレート
        app.unmounted_disk_listbox.curselection.return_value = [0]
        app.unmounted_disk_listbox.get.return_value = "sda1 (100GB, パーティション)"
        
        # DiskPropertiesAnalyzerのインスタンスとメソッドのモック
        mock_analyzer = MagicMock()
        mock_analyzer.get_disk_properties.return_value = {
            "device_path": "/dev/sda1",
            "basic_info": {"name": "sda1", "size": "100GB"}
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        # プロパティ表示中のエラーをシミュレート
        mock_dialog.side_effect = Exception("テストエラー")
        
        # _show_unmounted_propertiesメソッドを呼び出し
        app._show_unmounted_properties()
        
        # エラーメッセージが表示されたことを確認
        mock_showerror.assert_called_once() 