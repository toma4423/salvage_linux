"""
ロガーモジュール

このモジュールは、アプリケーションのログ記録機能を提供します。
"""

import os
import logging
import datetime
import re
from pathlib import Path

class Logger:
    """
    ロギングクラス
    
    アプリケーションのログを記録する機能を提供します。
    ログレベルの設定、ログの出力先の指定、パスのサニタイズなどの機能を持ちます。
    """
    
    def __init__(self, log_dir='logs', level=logging.INFO):
        """
        初期化メソッド
        
        Args:
            log_dir (str): ログファイルを保存するディレクトリ
            level (int): ログレベル（logging.DEBUG, logging.INFO など）
        """
        # ログディレクトリのパスをサニタイズ
        log_dir = self._sanitize_path(log_dir)
        
        # ログファイル名を生成
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"disk_utility_{timestamp}.log"
        
        # ログディレクトリを作成
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # ログファイルパスを設定
        self.log_file = os.path.join(log_dir, log_filename)
        
        # ロガーを設定
        self.logger = logging.getLogger('disk_utility')
        self.logger.setLevel(level)
        
        # ファイルハンドラを設定
        self.file_handler = logging.FileHandler(self.log_file)
        self.file_handler.setLevel(level)
        
        # フォーマッタを設定
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_handler.setFormatter(formatter)
        
        # ハンドラをロガーに追加
        self.logger.addHandler(self.file_handler)
        
        # 初期ログ
        self.info(f"ロガーを初期化しました。レベル: {self._level_to_name(level)}")
    
    def _level_to_name(self, level):
        """
        ログレベルの数値を名前に変換
        
        Args:
            level (int): ログレベル
            
        Returns:
            str: ログレベルの名前
        """
        level_names = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL"
        }
        return level_names.get(level, f"UNKNOWN({level})")
    
    def setLevel(self, level):
        """
        ログレベルを設定
        
        Args:
            level (int): 設定するログレベル
        """
        self.logger.setLevel(level)
        self.file_handler.setLevel(level)
        self.info(f"ログレベルを変更しました: {self._level_to_name(level)}")
    
    def _sanitize_path(self, path):
        """
        パスを安全にサニタイズする
        
        Args:
            path (str): サニタイズするパス
            
        Returns:
            str: サニタイズされたパス
        """
        # パスが文字列でない場合はデフォルト値を使用
        if not isinstance(path, str):
            return 'logs'
        
        # パストラバーサルや特殊文字を含むパスをサニタイズ
        # '../' などの表現を削除
        path = re.sub(r'\.\./', '', path)
        path = re.sub(r'\.\.\\', '', path)
        
        # 特殊文字をサニタイズ
        path = re.sub(r'[;|&`$]', '', path)
        
        # 空のパスになった場合はデフォルト値を使用
        if not path or path.strip() == '':
            return 'logs'
        
        # 絶対パスを相対パスに変換
        if os.path.isabs(path):
            path = os.path.relpath(path, '/')
        
        return path
    
    def debug(self, message):
        """
        デバッグレベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.debug(message)
    
    def info(self, message):
        """
        情報レベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.info(message)
    
    def warning(self, message):
        """
        警告レベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.warning(message)
    
    def error(self, message):
        """
        エラーレベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.error(message)
    
    def critical(self, message):
        """
        致命的エラーレベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.critical(message) 