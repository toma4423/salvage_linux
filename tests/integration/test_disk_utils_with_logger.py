"""
DiskUtilsとLoggerの統合テスト
"""

import pytest
import os
import subprocess
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from src.disk_utils import DiskUtils
from src.logger import Logger

@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成するフィクスチャ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # テスト後にディレクトリを削除
    shutil.rmtree(temp_dir)

@pytest.fixture
def logger_and_disk_utils(temp_dir):
    """実際のロガーとディスクユーティリティを提供するフィクスチャ"""
    log_dir = os.path.join(temp_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)  # 確実にログディレクトリを作成
    
    logger = Logger(log_dir=log_dir)
    disk_utils = DiskUtils(logger)
    
    # ログディレクトリではなく、実際のログファイルのパスを返す
    return logger, disk_utils, os.path.dirname(logger.log_file)

@pytest.mark.integration
class TestDiskUtilsWithLogger:
    """DiskUtilsとLoggerの統合テスト"""
    
    @patch('subprocess.check_output')
    def test_unmounted_disks_logged(self, mock_check_output, logger_and_disk_utils):
        """未マウントディスク取得のログが正しく記録されるかテスト"""
        logger, disk_utils, log_dir = logger_and_disk_utils
        
        # lsblkコマンドの出力をモック
        mock_check_output.return_value = """
        {
            "blockdevices": [
                {
                    "name": "sda",
                    "size": "100G",
                    "type": "disk",
                    "fstype": null,
                    "mountpoint": null,
                    "children": []
                }
            ]
        }
        """
        
        # メソッドを実行
        disk_utils.get_unmounted_disks()
        
        # ログファイルを確認
        log_files = os.listdir(log_dir)
        assert len(log_files) > 0  # ログファイルが存在することを確認
        
        # ログの内容を確認
        log_file_path = os.path.join(log_dir, log_files[0])
        with open(log_file_path, 'r') as f:
            log_content = f.read()
            assert "未マウントディスク" in log_content
    
    @patch('subprocess.check_call')
    def test_mount_disk_error_logged(self, mock_check_call, logger_and_disk_utils):
        """マウントエラーが正しくログに記録されるかテスト"""
        logger, disk_utils, log_dir = logger_and_disk_utils
        
        # マウントエラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mount")
        
        # ファイルシステムタイプ取得をモック
        disk_utils.get_filesystem_type = lambda x: "ntfs"
        
        # メソッドを実行
        disk_utils.mount_disk("/dev/sda1")
        
        # ログファイルを確認
        log_files = os.listdir(log_dir)
        assert len(log_files) > 0  # ログファイルが存在することを確認
        
        # ログの内容を確認
        log_file_path = os.path.join(log_dir, log_files[0])
        with open(log_file_path, 'r') as f:
            log_content = f.read()
            assert "マウント" in log_content
            assert "失敗" in log_content
    
    @patch('subprocess.check_call')
    def test_format_disk_logged(self, mock_check_call, logger_and_disk_utils):
        """フォーマット操作のログが正しく記録されるかテスト"""
        logger, disk_utils, log_dir = logger_and_disk_utils
        
        # フォーマット成功をシミュレート
        mock_check_call.return_value = 0
        
        # メソッドを実行
        disk_utils.format_disk("/dev/sda1", "ntfs")
        
        # ログファイルを確認
        log_files = os.listdir(log_dir)
        assert len(log_files) > 0  # ログファイルが存在することを確認
        
        # ログの内容を確認
        log_file_path = os.path.join(log_dir, log_files[0])
        with open(log_file_path, 'r') as f:
            log_content = f.read()
            assert "フォーマット" in log_content
            assert "成功" in log_content
    
    @patch('subprocess.check_call')
    def test_format_disk_refs_logged(self, mock_check_call, logger_and_disk_utils):
        """ReFSフォーマット操作のログが正しく記録されるかテスト"""
        logger, disk_utils, log_dir = logger_and_disk_utils
        
        # ReFSフォーマット成功をシミュレート
        mock_check_call.return_value = 0
        
        # メソッドを実行
        disk_utils.format_disk("/dev/sda1", "refs")
        
        # ログファイルを確認
        log_files = os.listdir(log_dir)
        assert len(log_files) > 0  # ログファイルが存在することを確認
        
        # ログの内容を確認
        log_file_path = os.path.join(log_dir, log_files[0])
        with open(log_file_path, 'r') as f:
            log_content = f.read()
            assert "ReFS" in log_content
            assert "フォーマット" in log_content
            assert "成功" in log_content
    
    @patch('subprocess.check_call')
    def test_set_permissions_logged(self, mock_check_call, logger_and_disk_utils):
        """権限設定のログが正しく記録されるかテスト"""
        logger, disk_utils, log_dir = logger_and_disk_utils
        
        # 権限設定成功をシミュレート
        mock_check_call.return_value = 0
        
        # メソッドを実行
        disk_utils.set_permissions("/dev/sda1")
        
        # ログファイルを確認
        log_files = os.listdir(log_dir)
        assert len(log_files) > 0  # ログファイルが存在することを確認
        
        # ログの内容を確認
        log_file_path = os.path.join(log_dir, log_files[0])
        with open(log_file_path, 'r') as f:
            log_content = f.read()
            assert "権限" in log_content
            assert "設定" in log_content
            assert "成功" in log_content 