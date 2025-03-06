"""
config_manager.py - 設定管理モジュール

このモジュールはアプリケーション設定を管理します。
ユーザー設定の読み込み、保存、デフォルト設定の提供を行います。

author: toma4423
"""

import os
import json
import platform
from pathlib import Path

class ConfigManager:
    """
    設定管理クラス
    アプリケーション設定の読み込み、保存、アクセスを提供します
    """
    
    def __init__(self, config_dir=None):
        """
        初期化
        
        Args:
            config_dir (str, optional): 設定ディレクトリのパス。指定しない場合はホームディレクトリの.config/salvage_linuxを使用
        """
        if config_dir is None:
            # デフォルトの設定ディレクトリ（~/.config/salvage_linux）
            home_dir = str(Path.home())
            self.config_dir = os.path.join(home_dir, '.config', 'salvage_linux')
        else:
            self.config_dir = config_dir
            
        # 設定ファイルのパス
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # デフォルト設定
        self.default_config = {
            "file_manager": "auto",  # 'auto'は自動検出
            "file_managers_list": [
                "xdg-open",    # デスクトップ環境のデフォルトファイルマネージャー
                "pcmanfm",     # LXDEやLXQT環境
                "nautilus",    # GNOME環境
                "thunar",      # XFCE環境
                "dolphin",     # KDE環境
                "nemo",        # Cinnamon環境
                "caja",        # MATE環境
                "dbus-launch pcmanfm",
                "dbus-launch nautilus"
            ],
            "format_default": "exfat",  # デフォルトのフォーマット形式
            "log_level": "INFO",       # ログレベル
            "language": "ja"           # 言語設定
        }
        
        # 現在の設定（最初はデフォルト値からロード）
        self.config = self.default_config.copy()
        
        # 設定ディレクトリが存在しない場合は作成
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
        
        # 設定ファイルからロード（存在する場合）
        self.load_config()
    
    def load_config(self):
        """
        設定ファイルから設定をロードします。
        設定ファイルが存在しない場合はデフォルト設定を使用します。
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # デフォルト設定をロードした設定で更新
                    self.config.update(loaded_config)
        except Exception as e:
            print(f"設定ファイルのロードに失敗しました: {e}")
            # 問題がある場合はデフォルト設定を使用
            self.config = self.default_config.copy()
    
    def save_config(self):
        """
        現在の設定を設定ファイルに保存します。
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"設定ファイルの保存に失敗しました: {e}")
            return False
    
    def get(self, key, default=None):
        """
        設定値を取得します。
        
        Args:
            key (str): 設定キー
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            設定値またはデフォルト値
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """
        設定値を設定します。
        
        Args:
            key (str): 設定キー
            value: 設定値
            
        Returns:
            bool: 成功した場合はTrue
        """
        self.config[key] = value
        return self.save_config()
    
    def get_file_manager(self):
        """
        設定されているファイルマネージャーを取得します。
        'auto'の場合は利用可能なファイルマネージャーのリストを返します。
        
        Returns:
            str または list: ファイルマネージャー名または利用可能なファイルマネージャーのリスト
        """
        file_manager = self.get('file_manager')
        if file_manager == 'auto':
            return self.get('file_managers_list')
        return file_manager
    
    def set_file_manager(self, file_manager):
        """
        使用するファイルマネージャーを設定します。
        
        Args:
            file_manager (str): ファイルマネージャー名または'auto'
            
        Returns:
            bool: 成功した場合はTrue
        """
        return self.set('file_manager', file_manager)
    
    def reset_to_defaults(self):
        """
        すべての設定をデフォルト値にリセットします。
        
        Returns:
            bool: 成功した場合はTrue
        """
        self.config = self.default_config.copy()
        return self.save_config() 