"""
ロガーのユニットテスト
"""

import os
import pytest
from unittest.mock import patch, mock_open
from src.logger import Logger

class TestLogger:
    """Loggerクラスのテスト"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """一時ディレクトリを作成"""
        return str(tmp_path)

    @pytest.fixture
    def logger(self, temp_dir):
        """Loggerインスタンスを作成"""
        return Logger(temp_dir)

    def test_logger_init(self, temp_dir, logger):
        """ロガーの初期化テスト"""
        # ログディレクトリが作成されていることを確認
        assert os.path.exists(logger.log_dir)
        assert os.path.isdir(logger.log_dir)
        
        # ログファイルが作成されていることを確認
        assert os.path.exists(logger.log_file)
        assert os.path.isfile(logger.log_file)

    def test_logger_methods(self, logger):
        """ロガーのメソッドテスト"""
        with patch('builtins.open', mock_open()) as mock_file:
            # 各ログメソッドを呼び出し
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            logger.debug("Test debug message")
            
            # メソッド呼び出し回数を確認
            assert logger._call_count == 4
            
            # ファイル操作の回数を確認
            assert mock_file.call_count == 4
            assert mock_file.return_value.write.call_count == 4

    def test_logger_automatic_directory_creation(self, temp_dir):
        """ログディレクトリの自動作成テスト"""
        # 存在しないディレクトリを指定
        log_dir = os.path.join(temp_dir, "logs", "test")
        logger = Logger(log_dir)
        
        # ディレクトリが自動的に作成されていることを確認
        assert os.path.exists(logger.log_dir)
        assert os.path.isdir(logger.log_dir)

    def test_logger_file_error(self, logger):
        """ファイル操作エラーのテスト"""
        with patch('builtins.open', side_effect=IOError("Test error")):
            # エラーが発生しても例外が伝播しないことを確認
            logger.info("Test message")
            logger.warning("Test message")
            logger.error("Test message")
            logger.debug("Test message")

    def test_logger_rotation(self, logger):
        """ログローテーションのテスト"""
        with patch('builtins.open', mock_open()) as mock_file:
            # 大量のログを書き込み
            for i in range(1000):
                logger.info(f"Test message {i}")
            
            # 書き込み回数を確認
            assert mock_file.return_value.write.call_count == 1000 