#!/usr/bin/env python3
"""
アプリケーションの設定ダイアログを提供するモジュール
ファイルマネージャーの選択やその他の設定を変更できます
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QMessageBox,
    QCheckBox, QSpinBox, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SettingsDialog(QDialog):
    """
    アプリケーションの設定ダイアログ
    """
    def __init__(self, parent, config_manager, logger):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            config_manager: 設定を管理するConfigManagerインスタンス
            logger: ロガーインスタンス
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.changed = False
        
        # ダイアログの設定
        self.setWindowTitle("設定")
        self.setMinimumWidth(400)
        
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        
        # ファイルマネージャー設定
        fm_group = QGroupBox("ファイルマネージャー")
        fm_layout = QFormLayout(fm_group)
        
        # ファイルマネージャーの選択
        self.fm_combo = QComboBox()
        self.fm_combo.addItems(["nautilus", "dolphin", "nemo", "thunar", "pcmanfm"])
        current_fm = self.config_manager.get("file_manager", "nautilus")
        self.fm_combo.setCurrentText(current_fm)
        self.fm_combo.currentTextChanged.connect(self._on_setting_changed)
        fm_layout.addRow("デフォルトのファイルマネージャー:", self.fm_combo)
        
        # カスタムファイルマネージャーのパス
        custom_fm_layout = QHBoxLayout()
        self.custom_fm_path = QLineEdit()
        self.custom_fm_path.setText(self.config_manager.get("custom_file_manager_path", ""))
        self.custom_fm_path.textChanged.connect(self._on_setting_changed)
        custom_fm_layout.addWidget(self.custom_fm_path)
        
        browse_button = QPushButton("参照...")
        browse_button.clicked.connect(self._browse_custom_fm)
        custom_fm_layout.addWidget(browse_button)
        
        fm_layout.addRow("カスタムファイルマネージャーのパス:", custom_fm_layout)
        
        main_layout.addWidget(fm_group)
        
        # 表示設定
        display_group = QGroupBox("表示設定")
        display_layout = QFormLayout(display_group)
        
        # ダークモード
        self.dark_mode = QCheckBox("ダークモードを有効にする")
        self.dark_mode.setChecked(self.config_manager.get("dark_mode", False))
        self.dark_mode.stateChanged.connect(self._on_setting_changed)
        display_layout.addRow(self.dark_mode)
        
        # フォントサイズ
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(self.config_manager.get("font_size", 10))
        self.font_size.valueChanged.connect(self._on_setting_changed)
        display_layout.addRow("フォントサイズ:", self.font_size)
        
        main_layout.addWidget(display_group)
        
        # 動作設定
        behavior_group = QGroupBox("動作設定")
        behavior_layout = QFormLayout(behavior_group)
        
        # 自動マウント
        self.auto_mount = QCheckBox("ディスクを自動的にマウントする")
        self.auto_mount.setChecked(self.config_manager.get("auto_mount", True))
        self.auto_mount.stateChanged.connect(self._on_setting_changed)
        behavior_layout.addRow(self.auto_mount)
        
        # 確認ダイアログ
        self.confirm_dialog = QCheckBox("重要な操作前に確認ダイアログを表示する")
        self.confirm_dialog.setChecked(self.config_manager.get("confirm_dialog", True))
        self.confirm_dialog.stateChanged.connect(self._on_setting_changed)
        behavior_layout.addRow(self.confirm_dialog)
        
        main_layout.addWidget(behavior_group)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def _on_setting_changed(self):
        """
        設定が変更されたときの処理
        """
        self.changed = True
    
    def _browse_custom_fm(self):
        """
        カスタムファイルマネージャーのパスを選択
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "カスタムファイルマネージャーを選択",
            "/usr/bin",
            "実行ファイル (*)"
        )
        
        if file_path:
            self.custom_fm_path.setText(file_path)
            self._on_setting_changed()
    
    def _save_settings(self):
        """
        設定を保存
        """
        try:
            # 設定を更新
            self.config_manager.set("file_manager", self.fm_combo.currentText())
            self.config_manager.set("custom_file_manager_path", self.custom_fm_path.text())
            self.config_manager.set("dark_mode", self.dark_mode.isChecked())
            self.config_manager.set("font_size", self.font_size.value())
            self.config_manager.set("auto_mount", self.auto_mount.isChecked())
            self.config_manager.set("confirm_dialog", self.confirm_dialog.isChecked())
            
            # 設定を保存
            if self.config_manager.save_config():
                self.logger.info("設定を保存しました")
                QMessageBox.information(self, "保存完了", "設定を保存しました。")
                self.accept()
            else:
                self.logger.error("設定の保存に失敗しました")
                QMessageBox.critical(self, "エラー", "設定の保存に失敗しました。")
            
        except Exception as e:
            self.logger.error(f"設定の保存中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(
                self,
                "エラー",
                f"設定の保存中にエラーが発生しました: {str(e)}"
            ) 