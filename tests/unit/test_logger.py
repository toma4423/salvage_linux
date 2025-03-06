"""
Loggerモジュールのユニットテスト
"""

import os
import pytest
from src.logger import Logger
import tempfile
import shutil
import logging

@pytest.fixture
def temp_log_dir():
    """テスト用の一時ログディレクトリを作成するフィクスチャ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # テスト後にディレクトリを削除
    shutil.rmtree(temp_dir)

@pytest.mark.unit
class TestLogger:
    """Loggerクラスのテスト"""
    
    def test_logger_init(self, temp_log_dir):
        """ロガーの初期化のテスト"""
        logger = Logger(log_dir=temp_log_dir)
        
        # ロガーインスタンスが正しく作成されることを確認
        assert logger.log_dir == temp_log_dir
        assert logger.logger.name == 'disk_utility'
        assert logger.logger.level == logging.INFO
        
        # ログディレクトリが作成されていることを確認
        assert os.path.exists(temp_log_dir)
    
    def test_logger_methods(self, temp_log_dir):
        """ロガーのメソッドのテスト"""
        logger = Logger(log_dir=temp_log_dir)
        
        # 各種ログメソッドが例外を発生させずに実行できることを確認
        logger.info("テスト情報ログ")
        logger.warning("テスト警告ログ")
        logger.error("テストエラーログ")
        logger.critical("テスト重大エラーログ")
        
        # ログファイルが作成されていることを確認
        log_files = os.listdir(temp_log_dir)
        assert len(log_files) == 1  # ログファイルが1つ作成されていること
        
        # ログファイルの内容を確認
        log_file_path = os.path.join(temp_log_dir, log_files[0])
        with open(log_file_path, 'r') as f:
            log_content = f.read()
            assert "テスト情報ログ" in log_content
            assert "テスト警告ログ" in log_content
            assert "テストエラーログ" in log_content
            assert "テスト重大エラーログ" in log_content
    
    def test_logger_automatic_directory_creation(self):
        """ログディレクトリが存在しない場合に自動作成されるかのテスト"""
        # 一時的なパスを作成（実際には存在しない）
        non_existent_dir = os.path.join(tempfile.gettempdir(), "nonexistent_logs_dir")
        
        # もし既に存在する場合は削除
        if os.path.exists(non_existent_dir):
            shutil.rmtree(non_existent_dir)
            
        # 存在しないディレクトリを指定してロガーを初期化
        logger = Logger(log_dir=non_existent_dir)
        
        # ディレクトリが作成されたことを確認
        assert os.path.exists(non_existent_dir)
        
        # 後片付け
        shutil.rmtree(non_existent_dir) 