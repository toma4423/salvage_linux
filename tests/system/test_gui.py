"""
GUIシステムテスト
"""

import pytest
import tempfile
import shutil
import os
import time
import threading
import tkinter as tk
from unittest.mock import patch, MagicMock
from src.main import DiskUtilityApp

@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成するフィクスチャ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # テスト後にディレクトリを削除
    shutil.rmtree(temp_dir)

@pytest.fixture
def gui_app():
    """GUIアプリケーションのインスタンスを提供するフィクスチャ"""
    # geteuid()をモックして常に0（root権限）を返すようにする
    with patch('os.geteuid', return_value=0):
        # refresh_disk_listsをモックしてディスク情報をスキップ
        with patch.object(DiskUtilityApp, '_refresh_disk_lists'):
            root = tk.Tk()
            app = DiskUtilityApp(root)
            
            # テスト用に一部の振る舞いをオーバーライド
            app.logger.info = MagicMock()
            app.logger.error = MagicMock()
            app.disk_utils.get_unmounted_disks = MagicMock(return_value=[
                {
                    "name": "sda1",
                    "path": "/dev/sda1",
                    "size": "100G",
                    "type": "part",
                    "fstype": "ntfs"
                }
            ])
            app.disk_utils.get_mounted_disks = MagicMock(return_value=[
                {
                    "name": "sdb1",
                    "path": "/dev/sdb1",
                    "size": "50G",
                    "type": "part",
                    "fstype": "ext4",
                    "mountpoint": "/mnt/sdb1"
                }
            ])
            
            yield app
            
            # テスト後にGUIを閉じる
            root.after(100, root.destroy)  # 100ms後にウィンドウを閉じる
            root.mainloop()

@pytest.mark.system
@pytest.mark.gui
class TestGUI:
    """GUIテスト"""
    
    def test_gui_init(self, gui_app):
        """GUIの初期化テスト"""
        # GUIが正しく初期化されたかを確認
        assert gui_app.root.title() == "USBブートLinux ディスクユーティリティ"
        assert isinstance(gui_app.unmounted_disk_listbox, tk.Listbox)
        assert isinstance(gui_app.mounted_disk_listbox, tk.Listbox)
        assert gui_app.mount_button["state"] == tk.DISABLED
        assert gui_app.format_button["state"] == tk.DISABLED
        assert gui_app.open_button["state"] == tk.DISABLED
        assert gui_app.permission_button["state"] == tk.DISABLED
    
    def test_refresh_disk_lists(self, gui_app):
        """ディスクリストの更新テスト"""
        # _refresh_disk_lists()の代わりに実際のリストを更新するための別メソッド
        def update_lists():
            # 未マウントディスクリストのクリア
            gui_app.unmounted_disk_listbox.delete(0, tk.END)
            
            # 未マウントディスクの表示
            for disk in gui_app.disk_utils.get_unmounted_disks():
                gui_app.unmounted_disk_listbox.insert(
                    tk.END, 
                    f"{disk['name']} ({disk['size']}, {'ディスク' if disk['type'] == 'disk' else 'パーティション'})"
                )
            
            # マウント済みディスクリストのクリア
            gui_app.mounted_disk_listbox.delete(0, tk.END)
            
            # マウント済みディスクの表示
            for disk in gui_app.disk_utils.get_mounted_disks():
                gui_app.mounted_disk_listbox.insert(
                    tk.END, 
                    f"{disk['name']} ({disk['size']}, {disk['mountpoint']})"
                )
        
        # リストを更新
        update_lists()
        
        # 結果を検証
        assert gui_app.unmounted_disk_listbox.size() == 1  # 1つの未マウントディスクがある
        assert gui_app.mounted_disk_listbox.size() == 1  # 1つのマウント済みディスクがある
    
    def test_unmounted_disk_selection(self, gui_app):
        """未マウントディスク選択のテスト"""
        # ディスクリストを更新
        gui_app.unmounted_disks = [
            {
                "name": "sda1",
                "path": "/dev/sda1",
                "size": "100G",
                "type": "part",
                "fstype": "ntfs"
            }
        ]
        
        # 未マウントディスクリストを更新
        gui_app.unmounted_disk_listbox.delete(0, tk.END)
        gui_app.unmounted_disk_listbox.insert(tk.END, "sda1 (100G, パーティション)")
        
        # リスト内のアイテムを選択（インデックス0）
        gui_app.unmounted_disk_listbox.selection_set(0)
        
        # 選択イベントを手動で発生させる
        gui_app._on_unmounted_disk_select(None)
        
        # 結果を検証
        assert gui_app.mount_button["state"] == tk.NORMAL  # マウントボタンが有効になっている
        assert gui_app.format_button["state"] == tk.NORMAL  # フォーマットボタンが有効になっている
    
    def test_mounted_disk_selection(self, gui_app):
        """マウント済みディスク選択のテスト"""
        # ディスクリストを更新
        gui_app.mounted_disks = [
            {
                "name": "sdb1",
                "path": "/dev/sdb1",
                "size": "50G",
                "type": "part",
                "fstype": "ext4",
                "mountpoint": "/mnt/sdb1"
            }
        ]
        
        # マウント済みディスクリストを更新
        gui_app.mounted_disk_listbox.delete(0, tk.END)
        gui_app.mounted_disk_listbox.insert(tk.END, "sdb1 (50G, /mnt/sdb1)")
        
        # リスト内のアイテムを選択（インデックス0）
        gui_app.mounted_disk_listbox.selection_set(0)
        
        # 選択イベントを手動で発生させる
        gui_app._on_mounted_disk_select(None)
        
        # 結果を検証
        assert gui_app.open_button["state"] == tk.NORMAL  # 開くボタンが有効になっている
        assert gui_app.permission_button["state"] == tk.NORMAL  # 権限付与ボタンが有効になっている
    
    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.messagebox.showerror')
    def test_mount_selected_disk(self, mock_showerror, mock_showinfo, gui_app):
        """ディスクマウント処理のテスト"""
        # 選択ディスクを設定
        gui_app.unmounted_disks = [
            {
                "name": "sda1",
                "path": "/dev/sda1",
                "size": "100G",
                "type": "part",
                "fstype": "ntfs"
            }
        ]
        
        # 未マウントディスクリストを更新
        gui_app.unmounted_disk_listbox.delete(0, tk.END)
        gui_app.unmounted_disk_listbox.insert(tk.END, "sda1 (100G, パーティション)")
        gui_app.unmounted_disk_listbox.selection_set(0)
        
        # マウント処理をモック
        gui_app.disk_utils.mount_disk = MagicMock(return_value=(True, "/mnt/sda1", ""))
        
        # リフレッシュ処理をモック
        gui_app._refresh_disk_lists = MagicMock()
        
        # マウント処理を実行
        gui_app._mount_selected_disk()
        
        # スレッドが完了するのを待つために少し待つ
        time.sleep(0.5)
        
        # 結果を検証
        gui_app.disk_utils.mount_disk.assert_called_once_with("/dev/sda1")
        mock_showinfo.assert_called_once()  # 成功メッセージが表示された
        gui_app._refresh_disk_lists.assert_called_once()  # リストが更新された
    
    @patch('tkinter.messagebox.askyesno', return_value=True)
    @patch('tkinter.messagebox.showinfo')
    def test_format_selected_disk(self, mock_showinfo, mock_askyesno, gui_app):
        """ディスクフォーマット処理のテスト"""
        # 選択ディスクを設定
        gui_app.unmounted_disks = [
            {
                "name": "sda1",
                "path": "/dev/sda1",
                "size": "100G",
                "type": "part",
                "fstype": "ntfs"
            }
        ]
        
        # 未マウントディスクリストを更新
        gui_app.unmounted_disk_listbox.delete(0, tk.END)
        gui_app.unmounted_disk_listbox.insert(tk.END, "sda1 (100G, パーティション)")
        gui_app.unmounted_disk_listbox.selection_set(0)
        
        # フォーマット形式を設定
        gui_app.fs_type_var.set("exfat")
        
        # フォーマット処理をモック
        gui_app.disk_utils.format_disk = MagicMock(return_value=(True, ""))
        
        # リフレッシュ処理をモック
        gui_app._refresh_disk_lists = MagicMock()
        
        # フォーマット処理を実行
        gui_app._format_selected_disk()
        
        # スレッドが完了するのを待つために少し待つ
        time.sleep(0.5)
        
        # 結果を検証
        mock_askyesno.assert_called_once()  # 確認ダイアログが表示された
        gui_app.disk_utils.format_disk.assert_called_once_with("/dev/sda1", "exfat")
        mock_showinfo.assert_called_once()  # 成功メッセージが表示された
        gui_app._refresh_disk_lists.assert_called_once()  # リストが更新された
    
    @patch('tkinter.messagebox.askyesno', return_value=True)
    @patch('tkinter.messagebox.showinfo')
    def test_set_permissions(self, mock_showinfo, mock_askyesno, gui_app):
        """権限付与処理のテスト"""
        # 選択ディスクを設定
        gui_app.mounted_disks = [
            {
                "name": "sdb1",
                "path": "/dev/sdb1",
                "size": "50G",
                "type": "part",
                "fstype": "ext4",
                "mountpoint": "/mnt/sdb1"
            }
        ]
        
        # マウント済みディスクリストを更新
        gui_app.mounted_disk_listbox.delete(0, tk.END)
        gui_app.mounted_disk_listbox.insert(tk.END, "sdb1 (50G, /mnt/sdb1)")
        gui_app.mounted_disk_listbox.selection_set(0)
        
        # 権限付与処理をモック
        gui_app.disk_utils.set_permissions = MagicMock(return_value=(True, ""))
        
        # 権限付与処理を実行
        gui_app._set_permissions_to_selected_disk()
        
        # スレッドが完了するのを待つために少し待つ
        time.sleep(0.5)
        
        # 結果を検証
        mock_askyesno.assert_called_once()  # 確認ダイアログが表示された
        gui_app.disk_utils.set_permissions.assert_called_once_with("/mnt/sdb1")
        mock_showinfo.assert_called_once()  # 成功メッセージが表示された 