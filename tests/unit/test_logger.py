"""
Loggerのユニットテスト
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import tempfile
from src.logger import Logger

@pytest.fixture
def temp_dir():
    """一時ディレクトリを作成するフィクスチャ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def logger(temp_dir):
    """テスト用のLoggerインスタンスを返すフィクスチャ"""
    log_dir = os.path.join(temp_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)  # 確実にログディレクトリを作成
    return Logger(log_dir)

@pytest.mark.unit
class TestLogger:
    """Loggerのテストクラス"""
    
    def test_logger_init(self, temp_dir, logger):
        """Loggerの初期化テスト"""
        # ログディレクトリが作成されていることを確認
        log_dir = os.path.join(temp_dir, "logs")
        assert os.path.exists(log_dir)
        assert os.path.isdir(log_dir)
        
        # ログファイルが作成されていることを確認
        log_file = os.path.join(log_dir, "app.log")
        assert os.path.exists(log_file)
        assert os.path.isfile(log_file)
    
    @patch('builtins.open', new_callable=MagicMock)
    def test_logger_methods(self, mock_open, logger):
        """ロガーメソッドのテスト"""
        # ファイルオブジェクトをモック
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 各メソッドを実行
        logger.info("情報メッセージ")
        logger.warning("警告メッセージ")
        logger.error("エラーメッセージ")
        logger.debug("デバッグメッセージ")
        
        # ファイルが正しく開かれたことを確認
        assert mock_open.call_count == 4
        
        # 各メソッドでファイルに書き込みが行われたことを確認
        assert mock_file.write.call_count == 4
    
    def test_logger_automatic_directory_creation(self, temp_dir):
        """ログディレクトリの自動作成テスト"""
        # 存在しないディレクトリを指定
        log_dir = os.path.join(temp_dir, "new_logs")
        
        # Loggerを初期化
        logger = Logger(log_dir)
        
        # ディレクトリが作成されていることを確認
        assert os.path.exists(log_dir)
        assert os.path.isdir(log_dir)
        
        # ログファイルが作成されていることを確認
        log_file = os.path.join(log_dir, "app.log")
        assert os.path.exists(log_file)
        assert os.path.isfile(log_file)
    
    def test_path_sanitization(self, temp_dir):
        """パスのサニタイズテスト"""
        # 不正なパスを含むディレクトリを指定
        log_dir = os.path.join(temp_dir, "logs", "..", "..", "outside")
        
        # Loggerを初期化
        logger = Logger(log_dir)
        
        # パスが正規化されていることを確認
        expected_dir = os.path.join(temp_dir, "outside")
        assert logger.log_dir == expected_dir
        
        # ログファイルが正しい場所に作成されていることを確認
        log_file = os.path.join(expected_dir, "app.log")
        assert os.path.exists(log_file)
        assert os.path.isfile(log_file)
    
    @patch('builtins.open', new_callable=MagicMock)
    def test_logger_file_error(self, mock_open, logger):
        """ファイル操作エラーのテスト"""
        # ファイル操作でエラーを発生させる
        mock_open.side_effect = IOError("ファイル操作エラー")
        
        # エラーが発生しても例外が伝播しないことを確認
        logger.info("テストメッセージ")
        logger.warning("テストメッセージ")
        logger.error("テストメッセージ")
        logger.debug("テストメッセージ")
    
    def test_logger_permissions(self, temp_dir):
        """ログファイルのパーミッションテスト"""
        log_dir = os.path.join(temp_dir, "logs")
        log_file = os.path.join(log_dir, "app.log")
        
        # ログファイルのパーミッションを確認
        assert os.access(log_file, os.R_OK)
        assert os.access(log_file, os.W_OK)
    
    @patch('builtins.open', new_callable=MagicMock)
    def test_logger_rotation(self, mock_open, logger):
        """ログローテーションのテスト"""
        # ファイルオブジェクトをモック
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 大量のログを書き込む
        for i in range(1000):
            logger.info(f"テストメッセージ {i}")
        
        # ファイルが正しく開かれたことを確認
        assert mock_open.call_count == 1000
        
        # 各メソッドでファイルに書き込みが行われたことを確認
        assert mock_file.write.call_count == 1000 