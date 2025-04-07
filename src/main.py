#!/usr/bin/env python3
"""
USBブートLinux GUIディスクユーティリティ
ディスクのマウント、フォーマット、および権限付与をGUIで簡便に行うためのツール
"""

import os
import sys
import threading
import argparse
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QMenu, QAction, QMessageBox,
    QTextEdit, QRadioButton, QButtonGroup,
    QDialog
)
from PyQt5.QtCore import Qt
from typing import List

# インポート文をパッケージ相対インポートに修正
from src.logger import Logger
from src.disk_utils import DiskUtils, DiskInfo
from src.version import get_version_info, APP_NAME, __version__
from src.config_manager import ConfigManager
from src.settings import SettingsDialog
from src.disk_properties import DiskPropertiesAnalyzer
from src.properties_dialog import PropertiesDialog

class DiskUtilityApp(QMainWindow):
    """
    ディスクユーティリティのメインアプリケーションクラス
    """
    def __init__(self, test_mode=False):
        """
        初期化
        
        Args:
            test_mode: テストモードフラグ。Trueの場合は権限チェックをスキップ
        """
        super().__init__()
        self.test_mode = test_mode
        
        # 設定マネージャーの初期化
        self.config_manager = ConfigManager()
        
        # タイトルにバージョン情報を追加
        self.setWindowTitle(f"{APP_NAME} {get_version_info()}")
        
        # 最小ウィンドウサイズを設定（レイアウト崩れを防止）
        self.setMinimumSize(800, 600)
        self.resize(900, 600)
        
        # スーパーユーザー権限の確認（テストモードでない場合）
        if not test_mode and os.geteuid() != 0:
            QMessageBox.critical(
                self,
                "権限エラー", 
                "このアプリケーションはスーパーユーザー権限で実行する必要があります。\n"
                "`sudo`コマンドを使って再実行してください。"
            )
            sys.exit(1)
        
        # ロガーの初期化
        self.logger = Logger()
        
        # ディスクユーティリティの初期化
        self.disk_utils = DiskUtils(self.logger, test_mode=test_mode)
        
        # プロパティアナライザーの初期化
        self.properties_analyzer = DiskPropertiesAnalyzer(self.logger)
        
        # 選択されたディスクの保存用変数
        self.selected_unmounted_disk = None
        self.selected_mounted_disk = None
        
        # ディスクリストの初期化
        self.unmounted_disks: List[DiskInfo] = []
        self.mounted_disks: List[DiskInfo] = []
        
        # メニューバーの作成
        self._create_menu()
        
        # GUIの構築
        self._build_gui()
        
        # ステータスバーの作成
        self.statusBar().showMessage("準備完了")
        
        # 起動時にディスクリストを更新
        self._refresh_disk_lists()
    
    def _create_menu(self):
        """
        メニューバーの作成
        """
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        refresh_action = QAction("更新", self)
        refresh_action.triggered.connect(self._refresh_disk_lists)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("設定", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ")
        announcements_action = QAction("お知らせ", self)
        announcements_action.triggered.connect(self.show_announcements)
        help_menu.addAction(announcements_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _build_gui(self):
        """
        GUIの構築 - ウィンドウサイズ変更に対応したレスポンシブなレイアウト
        """
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # スプリッターで左右のパネルを分割
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左右のパネル分割
        left_panel = QGroupBox("未マウントディスク")
        left_layout = QVBoxLayout(left_panel)
        
        right_panel = QGroupBox("マウント済みディスク")
        right_layout = QVBoxLayout(right_panel)
        
        # スプリッターにパネルを追加
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 未マウントディスクリスト（左パネル）
        self.unmounted_disk_listbox = QListWidget()
        self.unmounted_disk_listbox.setSelectionMode(QListWidget.SingleSelection)
        self.unmounted_disk_listbox.currentItemChanged.connect(self._on_unmounted_disk_select)
        left_layout.addWidget(self.unmounted_disk_listbox)
        
        # 未マウントディスク情報表示エリア
        unmounted_info_group = QGroupBox("ディスク情報")
        unmounted_info_layout = QVBoxLayout(unmounted_info_group)
        self.unmounted_disk_info = QTextEdit()
        self.unmounted_disk_info.setReadOnly(True)
        unmounted_info_layout.addWidget(self.unmounted_disk_info)
        left_layout.addWidget(unmounted_info_group)
        
        # 未マウントディスク操作ボタン
        unmounted_button_layout = QHBoxLayout()
        self.mount_button = QPushButton("マウント")
        self.mount_button.clicked.connect(self._mount_selected_disk)
        self.mount_button.setEnabled(False)
        unmounted_button_layout.addWidget(self.mount_button)
        
        self.format_button = QPushButton("フォーマット")
        self.format_button.clicked.connect(self._format_selected_disk)
        self.format_button.setEnabled(False)
        unmounted_button_layout.addWidget(self.format_button)
        
        left_layout.addLayout(unmounted_button_layout)
        
        # フォーマット形式選択
        format_group = QGroupBox("フォーマット形式")
        format_layout = QHBoxLayout(format_group)
        
        self.fs_type_group = QButtonGroup(self)
        
        ntfs_radio = QRadioButton("NTFS")
        ntfs_radio.setChecked(False)
        self.fs_type_group.addButton(ntfs_radio)
        format_layout.addWidget(ntfs_radio)
        
        exfat_radio = QRadioButton("exFAT")
        exfat_radio.setChecked(True)
        self.fs_type_group.addButton(exfat_radio)
        format_layout.addWidget(exfat_radio)
        
        left_layout.addWidget(format_group)
        
        # マウント済みディスクリスト（右パネル）
        self.mounted_disk_listbox = QListWidget()
        self.mounted_disk_listbox.setSelectionMode(QListWidget.SingleSelection)
        self.mounted_disk_listbox.currentItemChanged.connect(self._on_mounted_disk_select)
        right_layout.addWidget(self.mounted_disk_listbox)
        
        # マウント済みディスク情報表示エリア
        mounted_info_group = QGroupBox("ディスク情報")
        mounted_info_layout = QVBoxLayout(mounted_info_group)
        self.mounted_disk_info = QTextEdit()
        self.mounted_disk_info.setReadOnly(True)
        mounted_info_layout.addWidget(self.mounted_disk_info)
        right_layout.addWidget(mounted_info_group)
        
        # マウント済みディスク操作ボタン
        mounted_button_layout = QHBoxLayout()
        self.open_button = QPushButton("ファイルマネージャーで開く")
        self.open_button.clicked.connect(self._open_selected_disk)
        self.open_button.setEnabled(False)
        mounted_button_layout.addWidget(self.open_button)
        
        self.permission_button = QPushButton("権限付与")
        self.permission_button.clicked.connect(self._set_permissions_to_selected_disk)
        self.permission_button.setEnabled(False)
        mounted_button_layout.addWidget(self.permission_button)
        
        right_layout.addLayout(mounted_button_layout)
        
        # 共通操作ボタン（下部）
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self._refresh_disk_lists)
        bottom_layout.addWidget(refresh_button)
        
        main_layout.addLayout(bottom_layout)
        
        # 右クリックメニューを追加
        self._add_unmounted_disk_context_menu()
    
    def _add_unmounted_disk_context_menu(self):
        """
        未マウントディスクリストボックスに右クリックメニューを追加
        """
        self.unmounted_disk_listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.unmounted_disk_listbox.customContextMenuRequested.connect(self._show_unmounted_context_menu)
    
    def _show_unmounted_context_menu(self, position):
        """
        未マウントディスクの右クリックメニューを表示
        
        Args:
            position: クリックされた位置
        """
        if self.unmounted_disk_listbox.currentItem():
            context_menu = QMenu()
            properties_action = context_menu.addAction("プロパティ")
            properties_action.triggered.connect(self._show_unmounted_properties)
            context_menu.exec_(self.unmounted_disk_listbox.mapToGlobal(position))
    
    def _on_unmounted_disk_select(self, current, previous):
        """
        未マウントディスクが選択された時の処理
        """
        if not current:
            self.mount_button.setEnabled(False)
            self.format_button.setEnabled(False)
            return
        
        try:
            # 選択されたインデックスを取得
            index = self.unmounted_disk_listbox.row(current)
            
            # 選択されたディスク情報を表示
            disk = self.unmounted_disks[index]
            
            # 情報を表示
            info_text = f"名前: {disk['name']}\n"
            info_text += f"パス: {disk['path']}\n"
            info_text += f"サイズ: {disk['size']}\n"
            info_text += f"タイプ: {disk['type']}\n"
            
            fs_type = disk['fstype'] if disk['fstype'] else "未フォーマット"
            info_text += f"ファイルシステム: {fs_type}\n"
            
            self.unmounted_disk_info.setText(info_text)
            
            # マウントとフォーマットボタンを有効化
            self.mount_button.setEnabled(True)
            self.format_button.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
    
    def _on_mounted_disk_select(self, current, previous):
        """
        マウント済みディスクが選択された時の処理
        """
        if not current:
            self.open_button.setEnabled(False)
            self.permission_button.setEnabled(False)
            return
        
        try:
            # 選択されたインデックスを取得
            index = self.mounted_disk_listbox.row(current)
            
            # 選択されたディスク情報を表示
            disk = self.mounted_disks[index]
            
            # 情報を表示
            info_text = f"名前: {disk['name']}\n"
            info_text += f"パス: {disk['path']}\n"
            info_text += f"サイズ: {disk['size']}\n"
            info_text += f"タイプ: {disk['type']}\n"
            info_text += f"ファイルシステム: {disk['fstype']}\n"
            info_text += f"マウントポイント: {disk['mountpoint']}\n"
            
            self.mounted_disk_info.setText(info_text)
            
            # 開くと権限付与ボタンを有効化
            self.open_button.setEnabled(True)
            self.permission_button.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
    
    def _refresh_disk_lists(self):
        """
        ディスクリストを更新
        """
        try:
            # 未マウントディスクのリストを取得
            disks_data = self.disk_utils.get_unmounted_disks()
            
            # リストをクリア
            self.unmounted_disk_listbox.clear()
            self.unmounted_disks = []
            
            # 未マウントディスクを追加
            for device in disks_data.get("blockdevices", []):
                # ディスク自体の処理
                if device.get("mountpoint") is None and device.get("type") == "disk":
                    disk_info: DiskInfo = {
                        "name": device.get("name"),
                        "path": f"/dev/{device.get('name')}",
                        "device": f"/dev/{device.get('name')}",  # deviceフィールドを追加
                        "size": device.get("size"),
                        "type": device.get("type"),
                        "fstype": device.get("fstype", ""),
                        "mountpoint": None
                    }
                    self.unmounted_disks.append(disk_info)
                    self._add_disk_to_list(disk_info, self.unmounted_disk_listbox)
                
                # パーティションの処理
                for partition in device.get("children", []):
                    if partition.get("mountpoint") is None and partition.get("type") == "part":
                        partition_info: DiskInfo = {
                            "name": partition.get("name"),
                            "path": f"/dev/{partition.get('name')}",
                            "device": f"/dev/{partition.get('name')}",  # deviceフィールドを追加
                            "size": partition.get("size"),
                            "type": partition.get("type"),
                            "fstype": partition.get("fstype", ""),
                            "mountpoint": None
                        }
                        self.unmounted_disks.append(partition_info)
                        self._add_disk_to_list(partition_info, self.unmounted_disk_listbox)
            
            # マウント済みディスクのリストを取得（テストモードでは空のリストを返す）
            if not self.test_mode:
                mounted_disks = self.disk_utils.get_mounted_disks()
                self.mounted_disk_listbox.clear()
                self.mounted_disks = []
                for disk in mounted_disks:
                    # マウント済みディスクの情報を統一された形式に変換
                    disk_info: DiskInfo = {
                        "name": disk.get("name", os.path.basename(disk.get("path", ""))),
                        "path": disk.get("path", ""),
                        "device": disk.get("path", ""),  # deviceフィールドを追加
                        "size": disk.get("size", "Unknown"),
                        "type": disk.get("type", "disk"),
                        "mountpoint": disk.get("mountpoint", ""),
                        "fstype": disk.get("fstype", "")
                    }
                    self.mounted_disks.append(disk_info)
                    self._add_disk_to_list(disk_info, self.mounted_disk_listbox)
            
            self.logger.info("ディスクリストを更新しました")
            
        except Exception as e:
            self.logger.error(f"ディスクリストの更新に失敗しました: {e}")
            QMessageBox.warning(
                self,
                "エラー",
                f"ディスクリストの更新に失敗しました:\n{str(e)}"
            )
    
    def _add_disk_to_list(self, disk_info, list_widget):
        """
        ディスク情報をリストに追加
        
        Args:
            disk_info (dict): ディスク情報
            list_widget (QListWidget): 追加先のリストウィジェット
        """
        name = disk_info.get("name", "Unknown")
        size = disk_info.get("size", "Unknown")
        fs_type = disk_info.get("fstype", "")
        fs_type_str = f" ({fs_type})" if fs_type else ""
        
        item = QListWidgetItem(f"{name} - {size}{fs_type_str}")
        item.setData(Qt.UserRole, disk_info)
        list_widget.addItem(item)
    
    def _mount_selected_disk(self):
        """
        選択された未マウントディスクをマウント
        """
        try:
            # 選択されたインデックスを取得
            current_item = self.unmounted_disk_listbox.currentItem()
            if not current_item:
                return
            
            index = self.unmounted_disk_listbox.row(current_item)
            disk = self.unmounted_disks[index]
            
            # マウントの処理を別スレッドで実行
            self.statusBar().showMessage(f"{disk['name']} をマウント中...")
            
            def mount_thread():
                try:
                    success, mount_point, error_msg = self.disk_utils.mount_disk(disk['path'])
                    
                    if success:
                        QMessageBox.information(
                            self,
                            "マウント成功",
                            f"{disk['name']} を {mount_point} にマウントしました。"
                        )
                        self._refresh_disk_lists()
                    else:
                        QMessageBox.critical(
                            self,
                            "マウントエラー",
                            f"{disk['name']} のマウントに失敗しました。\n"
                            f"エラー: {error_msg}"
                        )
                    
                    # ステータスをリセット
                    self.statusBar().showMessage("準備完了")
                    
                except Exception as e:
                    self.logger.error(f"マウント処理中にエラーが発生しました: {str(e)}")
                    QMessageBox.critical(
                        self,
                        "エラー",
                        f"マウント処理中にエラーが発生しました: {str(e)}"
                    )
                    # ステータスをリセット
                    self.statusBar().showMessage("準備完了")
            
            thread = threading.Thread(target=mount_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"マウント処理の準備中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"マウント処理の準備中にエラーが発生しました: {str(e)}")
            self.statusBar().showMessage("準備完了")
    
    def _format_selected_disk(self):
        """
        選択された未マウントディスクをフォーマット
        """
        try:
            # 選択されたインデックスを取得
            current_item = self.unmounted_disk_listbox.currentItem()
            if not current_item:
                return
            
            index = self.unmounted_disk_listbox.row(current_item)
            disk = self.unmounted_disks[index]
            
            # フォーマット形式取得
            fs_type = "ntfs" if self.fs_type_group.checkedButton().text() == "NTFS" else "exfat"
            
            # 確認ダイアログを表示
            reply = QMessageBox.question(
                self,
                "確認",
                f"{disk['name']} ({disk['path']}) を {fs_type} でフォーマットします。\n"
                f"すべてのデータが消去されます。\n\n"
                f"続行しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # フォーマットの処理を別スレッドで実行
            self.statusBar().showMessage(f"{disk['name']} をフォーマット中...")
            
            def format_thread():
                try:
                    success, error_msg = self.disk_utils.format_disk(disk['path'], fs_type)
                    
                    if success:
                        QMessageBox.information(
                            self,
                            "フォーマット成功",
                            f"{disk['name']} を {fs_type} 形式でフォーマットしました。"
                        )
                    else:
                        QMessageBox.critical(
                            self,
                            "フォーマットエラー",
                            f"{disk['name']} のフォーマットに失敗しました。\n"
                            f"エラー: {error_msg}"
                        )
                    
                    # ステータスをリセット
                    self.statusBar().showMessage("準備完了")
                    
                except Exception as e:
                    self.logger.error(f"フォーマット処理中にエラーが発生しました: {str(e)}")
                    QMessageBox.critical(
                        self,
                        "エラー",
                        f"フォーマット処理中にエラーが発生しました: {str(e)}"
                    )
                    # ステータスをリセット
                    self.statusBar().showMessage("準備完了")
            
            thread = threading.Thread(target=format_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"フォーマット処理の準備中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"フォーマット処理の準備中にエラーが発生しました: {str(e)}")
            self.statusBar().showMessage("準備完了")
    
    def _open_selected_disk(self):
        """
        選択されたマウント済みディスクをファイルマネージャーで開く
        """
        try:
            # 選択されたインデックスを取得
            current_item = self.mounted_disk_listbox.currentItem()
            if not current_item:
                return
            
            index = self.mounted_disk_listbox.row(current_item)
            disk = self.mounted_disks[index]
            
            self.statusBar().showMessage(f"{disk['mountpoint']} をファイルマネージャーで開いています...")
            
            success, error_msg = self.disk_utils.open_file_manager(disk['mountpoint'])
            
            if not success:
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"ファイルマネージャーの起動に失敗しました。\n"
                    f"エラー: {error_msg}"
                )
            
            self.statusBar().showMessage("準備完了")
            
        except Exception as e:
            self.logger.error(f"ファイルマネージャー起動中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"ファイルマネージャー起動中にエラーが発生しました: {str(e)}")
            self.statusBar().showMessage("準備完了")
    
    def _set_permissions_to_selected_disk(self):
        """
        選択されたマウント済みディスクに権限を付与
        """
        try:
            # 選択されたインデックスを取得
            current_item = self.mounted_disk_listbox.currentItem()
            if not current_item:
                return
            
            index = self.mounted_disk_listbox.row(current_item)
            disk = self.mounted_disks[index]
            
            # 確認ダイアログを表示
            reply = QMessageBox.question(
                self,
                "確認",
                f"{disk['mountpoint']} に読み書き権限を付与します。\n\n"
                f"続行しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # 権限付与の処理を別スレッドで実行
            self.statusBar().showMessage(f"{disk['mountpoint']} に権限を付与中...")
            
            def permission_thread():
                try:
                    success, error_msg = self.disk_utils.set_permissions(disk['mountpoint'])
                    
                    if success:
                        QMessageBox.information(
                            self,
                            "権限付与成功",
                            f"{disk['mountpoint']} に読み書き権限を付与しました。"
                        )
                    else:
                        QMessageBox.critical(
                            self,
                            "権限付与エラー",
                            f"{disk['mountpoint']} への権限付与に失敗しました。\n"
                            f"エラー: {error_msg}"
                        )
                    
                    # ステータスをリセット
                    self.statusBar().showMessage("準備完了")
                    
                except Exception as e:
                    self.logger.error(f"権限付与処理中にエラーが発生しました: {str(e)}")
                    QMessageBox.critical(
                        self,
                        "エラー",
                        f"権限付与処理中にエラーが発生しました: {str(e)}"
                    )
                    # ステータスをリセット
                    self.statusBar().showMessage("準備完了")
            
            thread = threading.Thread(target=permission_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"権限付与処理の準備中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"権限付与処理の準備中にエラーが発生しました: {str(e)}")
            self.statusBar().showMessage("準備完了")
    
    def _show_unmounted_properties(self):
        """
        選択された未マウントディスクのプロパティを表示
        """
        try:
            current_item = self.unmounted_disk_listbox.currentItem()
            if not current_item:
                self.logger.warning("ディスクが選択されていません")
                QMessageBox.warning(self, "警告", "ディスクが選択されていません。")
                return
            
            # 選択されたインデックスを取得
            index = self.unmounted_disk_listbox.row(current_item)
            disk = self.unmounted_disks[index]
            
            self.logger.info(f"プロパティ表示: {disk['name']}")
            
            # デバイスパスを取得
            device_path = disk.get("device") or disk.get("path")
            if not device_path:
                self.logger.error("デバイスパスが見つかりません")
                QMessageBox.critical(self, "エラー", "デバイスパスが見つかりません。")
                return
            
            # プロパティアナライザーを作成
            properties_analyzer = DiskPropertiesAnalyzer(self.logger)
            
            # プロパティ情報を取得
            properties = properties_analyzer.get_disk_properties(device_path)
            
            # プロパティダイアログを表示
            dialog = PropertiesDialog(self, properties, device_path, self.logger)
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"プロパティ表示中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"プロパティ表示中にエラーが発生しました。\n{str(e)}")
    
    def _show_about(self):
        """
        バージョン情報を表示
        """
        QMessageBox.information(
            self,
            "バージョン情報",
            f"{APP_NAME}\n"
            f"バージョン: {__version__}\n\n"
            "開発者: toma4423\n"
            "ライセンス: MIT\n\n"
            "USBディスクのマウント、フォーマット、権限付与を\n"
            "GUI操作で簡単に行うためのツールです。"
        )
    
    def open_settings_dialog(self):
        """
        設定ダイアログを開く
        """
        dialog = SettingsDialog(self, self.config_manager, self.logger)
        dialog.exec_()
        # 設定変更後にディスクリストを更新
        self._refresh_disk_lists()
    
    def show_announcements(self):
        """お知らせを新しいウィンドウで表示"""
        announcements = """
【重要なお知らせ】

■ ReFSフォーマット機能について
現在、ReFSフォーマット機能は仮実装の段階です。
以下の制限事項があります：
・ReFSツールのインストールが必要です
・フォーマット操作の信頼性が限定的です
・データの整合性チェックが不完全です

■ 今後の予定
・ReFSフォーマット機能の完全実装
・フォーマット前のデータバックアップ機能
・フォーマット操作のロールバック機能
・より詳細なエラー報告機能

■ ご注意
・重要なデータの操作は必ずバックアップを取ってください
・システムディスクへの操作は制限されています
・一部の機能は管理者権限が必要です

■ フィードバック
機能の改善のため、ご意見・ご要望をお待ちしています。
GitHubのIssueでご報告ください。
"""
        # お知らせダイアログを作成
        dialog = QDialog(self)
        dialog.setWindowTitle("お知らせ")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        # レイアウトを作成
        layout = QVBoxLayout()
        
        # テキストエディタを作成
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(announcements)
        layout.addWidget(text_edit)
        
        # OKボタンを追加
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        # レイアウトをダイアログに設定
        dialog.setLayout(layout)
        
        # ダイアログを表示
        dialog.exec_()


def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description="ディスクユーティリティ")
    parser.add_argument("--test", action="store_true", help="テストモードで実行（権限チェックをスキップ）")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = DiskUtilityApp(test_mode=args.test)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 