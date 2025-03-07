import os
import pytest
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
import logging

from src.logger import Logger
from src.disk_properties import DiskPropertiesAnalyzer

@pytest.fixture
def temp_dir():
    """一時ディレクトリを作成するフィクスチャ"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        # ログディレクトリを作成
        log_dir = os.path.join(tmpdirname, "logs")
        os.makedirs(log_dir, exist_ok=True)
        yield tmpdirname

@pytest.fixture
def logger_and_disk_properties(temp_dir):
    """LoggerとDiskPropertiesAnalyzerのインスタンスを作成するフィクスチャ"""
    config = {
        "log_dir": os.path.join(temp_dir, "logs"),
        "log_level": "INFO"
    }
    
    logger = Logger(config)
    disk_properties = DiskPropertiesAnalyzer(logger)
    
    return logger, disk_properties

@pytest.mark.integration
class TestDiskPropertiesWithLogger:
    """DiskPropertiesAnalyzerとLoggerの統合テスト"""
    
    @patch('subprocess.check_output')
    def test_get_disk_properties_logged(self, mock_check_output, logger_and_disk_properties, temp_dir, caplog):
        """ディスクプロパティ取得がログに記録されることをテスト"""
        logger, properties_analyzer = logger_and_disk_properties
        
        # ログレベルを設定
        caplog.set_level(logging.INFO)
        
        # 基本情報のモック
        mock_check_output.return_value = '{"blockdevices":[{"name":"sda","size":"1GB","model":"Test","serial":"123","type":"disk","fstype":"ext4"}]}'
        
        # プロパティを取得
        device_path = "/dev/sda"
        properties = properties_analyzer.get_disk_properties(device_path)
        
        # プロパティが正しく取得されていることを確認
        assert properties["device_path"] == device_path
        
        # ログが記録されていることを確認
        assert "プロパティ情報を取得しています" in caplog.text
    
    @patch('builtins.open')
    def test_save_properties_error_logged(self, mock_open, logger_and_disk_properties, temp_dir, caplog):
        """プロパティ保存エラーがログに記録されることをテスト"""
        logger, properties_analyzer = logger_and_disk_properties
        
        # ログレベルを設定
        caplog.set_level(logging.ERROR)
        
        # ファイルオープンエラーをモック
        mock_open.side_effect = Exception("Failed to open file")
        
        # サンプルプロパティ
        properties = {
            "device_path": "/dev/sda",
            "basic_info": {"name": "sda", "size": "1GB"}
        }
        
        # ファイルに保存
        result = properties_analyzer.save_properties_to_file(properties, "/dev/sda")
        
        # 保存に失敗していることを確認
        assert result is False
        
        # エラーがログに記録されていることを確認
        assert "プロパティ情報の保存中にエラーが発生しました" in caplog.text
    
    @patch('subprocess.run')
    def test_get_smart_info_logs(self, mock_run, logger_and_disk_properties, temp_dir, caplog):
        """S.M.A.R.T.情報取得がログに記録されることをテスト"""
        logger, properties_analyzer = logger_and_disk_properties
        
        # ログレベルを設定
        caplog.set_level(logging.ERROR)  # ERRORレベルに設定
        
        # S.M.A.R.T.情報取得エラーをモック
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_process.returncode = 1
        mock_run.side_effect = Exception("Command failed")
        
        # S.M.A.R.T.情報を取得
        device_path = "/dev/sda"
        smart_info = properties_analyzer._get_smart_info(device_path)
        
        # S.M.A.R.T.情報にエラーが含まれていることを確認
        assert smart_info["overall_health"] == "エラー"
        
        # エラーがログに記録されていることを確認
        assert "S.M.A.R.T.情報の取得中にエラーが発生しました" in caplog.text
    
    @patch('subprocess.run')
    def test_get_basic_disk_info_error_logged(self, mock_run, logger_and_disk_properties, temp_dir, caplog):
        """基本ディスク情報取得エラーがログに記録されることをテスト"""
        logger, properties_analyzer = logger_and_disk_properties
        
        # ログレベルを設定
        caplog.set_level(logging.ERROR)
        
        # コマンド実行エラーをモック
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_process.stderr = "Command failed"
        mock_process.returncode = 1
        mock_run.return_value = mock_process
        mock_run.side_effect = Exception("Command failed")
        
        # 基本情報を取得
        device_path = "/dev/sda1"
        with patch('subprocess.check_output', side_effect=Exception("Command failed")):
            basic_info = properties_analyzer._get_basic_disk_info(device_path)
        
        # 基本情報が辞書として返されることを確認
        assert isinstance(basic_info, dict)
        
        # エラーがログに記録されていることを確認
        assert "基本情報の取得中にエラーが発生しました" in caplog.text 