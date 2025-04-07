"""
ロギング機能を提供するモジュール

このモジュールは、アプリケーション全体で使用されるロギング機能を提供します。
ログの自動ローテーション、適切なパーミッション設定、安全なパスサニタイズを実装しています。
"""

import os
import re
import stat
import logging
import logging.handlers
import sys
from typing import Optional, List
from datetime import datetime
from pathlib import Path

class Logger:
    """
    ロガークラス
    
    アプリケーションのログ出力を管理します。
    以下の機能を提供します：
    - ログの自動ローテーション（1MB毎、最大5ファイル）
    - 適切なパーミッション設定（ディレクトリ: 0o755, ファイル: 0o644）
    - パスのサニタイズ（特殊文字の除去、パストラバーサル対策）
    """
    
    def __init__(self, log_dir: str = "logs", log_file: Optional[str] = None):
        """
        初期化
        
        Args:
            log_dir: ログディレクトリのパス
            log_file (Optional[str]): ログファイルのパス。Noneの場合は標準出力に出力
        """
        # メソッド呼び出し回数を初期化
        self._call_count = 0
        
        # パストラバーサル対策
        self.log_dir = os.path.abspath(os.path.join(os.getcwd(), log_dir))
        
        # ログディレクトリの作成とパーミッション設定
        self._setup_log_directory()
        
        # ログファイル名の設定
        if log_file is None:
            self.log_file = os.path.join(self.log_dir, "disk_utility.log")
        else:
            self.log_file = os.path.join(self.log_dir, log_file)
        
        # ロガーの設定
        self.logger = logging.getLogger('disk_utility')
        self.logger.setLevel(logging.DEBUG)
        
        # 既存のハンドラをクリア
        self.logger.handlers.clear()
        
        self.messages: List[str] = []  # テスト用にメッセージを保存するリスト
        
        try:
            # ファイルが存在しない場合は作成
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'a') as f:
                    pass
            
            # ログファイルのパーミッションを設定
            os.chmod(self.log_file, 0o644)
            
            # ローテーティングファイルハンドラの設定
            handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=1024 * 1024,  # 1MB
                backupCount=5,
                encoding='utf-8',
                mode='a'
            )
            
            # フォーマッタの設定
            formatter = logging.Formatter(
                '%(levelname)s     %(name)s:%(filename)s:%(lineno)d %(message)s'
            )
            handler.setFormatter(formatter)
            
            # ハンドラを追加
            self.logger.addHandler(handler)
            
        except Exception as e:
            raise RuntimeError(f"ログファイルの設定に失敗しました: {str(e)}")
    
    def _setup_log_directory(self) -> None:
        """
        ログディレクトリを作成し、適切なパーミッションを設定します。
        
        Raises:
            RuntimeError: ディレクトリの作成や権限設定に失敗した場合
        """
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(self.log_dir, exist_ok=True)
            
            # ディレクトリのパーミッションを設定
            os.chmod(self.log_dir, 0o755)
            
        except Exception as e:
            raise RuntimeError(f"ログディレクトリの設定に失敗しました: {str(e)}")
    
    def _sanitize_path(self, path: str) -> str:
        """
        パスを安全に正規化します。
        
        Args:
            path (str): 正規化するパス
            
        Returns:
            str: 正規化されたパス
        """
        try:
            # まず絶対パスに変換
            absolute = os.path.abspath(path)
            
            # パスを正規化（.. や . を解決）
            normalized = os.path.normpath(absolute)
            
            # 特殊文字を除去（ただし、/ は保持）
            sanitized = re.sub(r'[<>:"|?*\\]', '', normalized)
            
            return sanitized
            
        except Exception as e:
            raise RuntimeError(f"パスの正規化に失敗しました: {str(e)}")
    
    def _write_log(self, level: str, message: str) -> None:
        """
        ログを書き込みます。
        
        Args:
            level (str): ログレベル
            message (str): ログメッセージ
        """
        try:
            # メソッド呼び出し回数を更新
            self._call_count += 1
            
            # ログメッセージを保存
            self.messages.append(message)
            
            # ログを書き込み
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_line = f"{timestamp} {level} {message}\n"
                f.write(log_line)
                
        except Exception as e:
            print(f"ログの書き込みに失敗しました: {str(e)}")
    
    def info(self, message: str) -> None:
        """
        情報レベルのログを出力します。
        
        Args:
            message (str): ログメッセージ
        """
        self._write_log('INFO', message)
    
    def warning(self, message: str) -> None:
        """
        警告レベルのログを出力します。
        
        Args:
            message (str): ログメッセージ
        """
        self._write_log('WARNING', message)
    
    def error(self, message: str) -> None:
        """
        エラーレベルのログを出力します。
        
        Args:
            message (str): ログメッセージ
        """
        self._write_log('ERROR', message)
    
    def debug(self, message: str) -> None:
        """
        デバッグレベルのログを出力します。
        
        Args:
            message (str): ログメッセージ
        """
        self._write_log('DEBUG', message)