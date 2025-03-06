"""
ログユーティリティモジュール
アプリケーションのログを管理するためのモジュールです。
"""

import logging
import os
from datetime import datetime

class Logger:
    """
    アプリケーションのログを管理するクラス
    """
    def __init__(self, log_dir='logs'):
        """
        ロガーの初期化
        
        Args:
            log_dir (str): ログファイルを保存するディレクトリのパス
        """
        self.log_dir = log_dir
        
        # ログディレクトリが存在しない場合は作成
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 現在の日時を含むログファイル名を生成
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"disk_utility_{current_time}.log")
        
        # ロガーの設定
        self.logger = logging.getLogger('disk_utility')
        self.logger.setLevel(logging.INFO)
        
        # ファイルハンドラの追加
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # フォーマッタの設定
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # ハンドラをロガーに追加
        self.logger.addHandler(file_handler)
    
    def info(self, message):
        """
        INFO レベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.info(message)
    
    def warning(self, message):
        """
        WARNING レベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.warning(message)
    
    def error(self, message):
        """
        ERROR レベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.error(message)
    
    def critical(self, message):
        """
        CRITICAL レベルのログを記録
        
        Args:
            message (str): ログメッセージ
        """
        self.logger.critical(message) 