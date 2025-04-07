#!/usr/bin/env python3
"""
ディスク/パーティションのプロパティ情報を表示するダイアログを提供するモジュール
基本情報、S.M.A.R.T.情報、ファイルシステム情報を表示し、テキストファイルに保存する機能を提供
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QTextEdit, QPushButton, QFileDialog, QMessageBox,
    QScrollArea, QFrame, QGridLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

class PropertiesDialog(QDialog):
    """
    ディスク/パーティションのプロパティ情報を表示するダイアログ
    """
    def __init__(self, parent, properties, device_path, logger):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            properties: プロパティ情報の辞書
            device_path: デバイスパス
            logger: ロガーインスタンス
        """
        super().__init__(parent)
        self.properties = properties
        self.device_path = device_path
        self.logger = logger
        
        # ダイアログの設定
        self.setWindowTitle(f"プロパティ - {os.path.basename(device_path)}")
        self.setMinimumSize(600, 400)
        
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        
        # タブウィジェットの作成
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 基本情報タブ
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        self._create_basic_info_tab(basic_layout)
        tab_widget.addTab(basic_tab, "基本情報")
        
        # S.M.A.R.T.情報タブ
        smart_tab = QWidget()
        smart_layout = QVBoxLayout(smart_tab)
        self._create_smart_info_tab(smart_layout)
        tab_widget.addTab(smart_tab, "S.M.A.R.T.情報")
        
        # ファイルシステム情報タブ
        fs_tab = QWidget()
        fs_layout = QVBoxLayout(fs_tab)
        self._create_filesystem_info_tab(fs_layout)
        tab_widget.addTab(fs_tab, "ファイルシステム情報")
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save_to_file)
        button_layout.addWidget(save_button)
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
    
    def _create_basic_info_tab(self, layout):
        """
        基本情報タブを作成
        
        Args:
            layout: レイアウト
        """
        # スクロールエリアの作成
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # スクロールエリアの中身
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # 基本情報グループ
        basic_group = QGroupBox("基本情報")
        basic_group_layout = QGridLayout(basic_group)
        
        # 基本情報の表示
        row = 0
        for key, value in self.properties.get("basic_info", {}).items():
            label = QLabel(f"{key}:")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            basic_group_layout.addWidget(label, row, 0)
            
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            basic_group_layout.addWidget(value_label, row, 1)
            
            row += 1
        
        content_layout.addWidget(basic_group)
        content_layout.addStretch()
        
        scroll.setWidget(content)
    
    def _create_smart_info_tab(self, layout):
        """
        S.M.A.R.T.情報タブを作成
        
        Args:
            layout: レイアウト
        """
        # スクロールエリアの作成
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # スクロールエリアの中身
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # S.M.A.R.T.情報グループ
        smart_group = QGroupBox("S.M.A.R.T.情報")
        smart_group_layout = QGridLayout(smart_group)
        
        # S.M.A.R.T.情報の表示
        row = 0
        for key, value in self.properties.get("smart_info", {}).items():
            label = QLabel(f"{key}:")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            smart_group_layout.addWidget(label, row, 0)
            
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            
            # 重要な属性の場合は色を変更
            if key in ["Health Status", "Temperature", "Power Cycles"]:
                palette = value_label.palette()
                palette.setColor(QPalette.WindowText, QColor("red"))
                value_label.setPalette(palette)
            
            smart_group_layout.addWidget(value_label, row, 1)
            
            row += 1
        
        content_layout.addWidget(smart_group)
        content_layout.addStretch()
        
        scroll.setWidget(content)
    
    def _create_filesystem_info_tab(self, layout):
        """
        ファイルシステム情報タブを作成
        
        Args:
            layout: レイアウト
        """
        # スクロールエリアの作成
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # スクロールエリアの中身
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # ファイルシステム情報グループ
        fs_group = QGroupBox("ファイルシステム情報")
        fs_group_layout = QGridLayout(fs_group)
        
        # ファイルシステム情報の表示
        row = 0
        for key, value in self.properties.get("filesystem_info", {}).items():
            label = QLabel(f"{key}:")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            fs_group_layout.addWidget(label, row, 0)
            
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            fs_group_layout.addWidget(value_label, row, 1)
            
            row += 1
        
        content_layout.addWidget(fs_group)
        content_layout.addStretch()
        
        scroll.setWidget(content)
    
    def _save_to_file(self):
        """
        プロパティ情報をテキストファイルに保存
        """
        try:
            # 保存先の選択
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "プロパティ情報の保存",
                os.path.expanduser("~"),
                "テキストファイル (*.txt)"
            )
            
            if not file_path:
                return
            
            # ファイルに書き込み
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"デバイス: {self.device_path}\n\n")
                
                # 基本情報
                f.write("=== 基本情報 ===\n")
                for key, value in self.properties.get("basic_info", {}).items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                
                # S.M.A.R.T.情報
                f.write("=== S.M.A.R.T.情報 ===\n")
                for key, value in self.properties.get("smart_info", {}).items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                
                # ファイルシステム情報
                f.write("=== ファイルシステム情報 ===\n")
                for key, value in self.properties.get("filesystem_info", {}).items():
                    f.write(f"{key}: {value}\n")
            
            QMessageBox.information(
                self,
                "保存完了",
                f"プロパティ情報を {file_path} に保存しました。"
            )
            
        except Exception as e:
            self.logger.error(f"プロパティ情報の保存中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(
                self,
                "エラー",
                f"プロパティ情報の保存中にエラーが発生しました: {str(e)}"
            ) 