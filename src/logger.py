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
    """ロギングクラス"""
    
    def __init__(self, log_dir='logs'):
        """
        初期化メソッド
        
        Args:
            log_dir (str): ログファイルを保存するディレクトリ
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
        self.logger.setLevel(logging.DEBUG)
        
        # ファイルハンドラを設定
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # フォーマッタを設定
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # ハンドラをロガーに追加
        self.logger.addHandler(file_handler)
        
        # 初期ログ
        self.info("ロガーを初期化しました。")
    
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