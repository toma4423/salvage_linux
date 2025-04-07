"""
セキュリティテスト
"""

import pytest
import os
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
    
    return logger, disk_utils

@pytest.mark.system
@pytest.mark.security
class TestSecurity:
    """セキュリティテスト"""
    
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    @patch('os.access')
    def test_format_disk_permission_validation(self, mock_access, mock_exists, mock_check_call, logger_and_disk_utils):
        """ディスクフォーマット時の権限検証テスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # システムディレクトリへのフォーマット試行をシミュレート
        system_paths = [
            "/boot",
            "/etc",
            "/usr",
            "/var",
            "/",
            "/opt"
        ]
        
        # /homeは別途テスト
        non_system_paths = [
            "/home"
        ]
        
        # システムディレクトリのテスト
        for path in system_paths:
            # パスが存在すると仮定
            mock_exists.return_value = True
            mock_access.return_value = True
            
            # モックをリセット
            mock_check_call.reset_mock()
            
            # フォーマット試行
            message = disk_utils.format_disk(path, "ntfs")
            
            # システムディレクトリのフォーマットが拒否されることを確認
            assert "システムディレクトリ" in message, f"{path}のエラーメッセージが不適切です: {message}"
            
            # フォーマットコマンドが実行されていないことを確認
            mock_check_call.assert_not_called()
        
        # 非システムディレクトリのテスト
        for path in non_system_paths:
            # パスが存在すると仮定
            mock_exists.return_value = True
            mock_access.return_value = True
            
            # モックをリセット
            mock_check_call.reset_mock()
            
            # フォーマット試行
            message = disk_utils.format_disk(path, "ntfs")
            
            # 非システムディレクトリのフォーマットが許可されることを確認
            assert "完了" in message, f"{path}のフォーマットが拒否されました: {message}"
            
            # フォーマットコマンドが実行されたことを確認
            mock_check_call.assert_called()
    
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    @patch('os.access')
    def test_mount_disk_path_validation(self, mock_access, mock_exists, mock_check_call, logger_and_disk_utils):
        """ディスクマウント時のパス検証テスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # 不正なパスでのマウント試行
        invalid_paths = [
            "../etc/shadow",
            "../../etc/passwd",
            "/dev/../../etc",
            "/dev/null; rm -rf /",
            "/dev/sda1 && echo 'hacked'",
            "/dev/sda1 | cat /etc/passwd"
        ]
        
        for path in invalid_paths:
            # パスが存在すると仮定
            mock_exists.return_value = True
            mock_access.return_value = True
            
            # モックをリセット
            mock_check_call.reset_mock()
            
            # マウント試行
            success, message = disk_utils.mount_disk(path)
            
            # 不正なパスのマウントが拒否されることを確認
            assert not success, f"{path}のマウントが許可されました"
            assert "不正なパス" in message, f"{path}のエラーメッセージが不適切です: {message}"
            
            # マウントコマンドが実行されていないことを確認
            mock_check_call.assert_not_called()
    
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    @patch('os.access')
    def test_format_disk_command_injection(self, mock_access, mock_exists, mock_check_call, logger_and_disk_utils):
        """ディスクフォーマット時のコマンドインジェクション対策テスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # コマンドインジェクションを試みるパス
        injection_paths = [
            "/dev/sda1; rm -rf /",
            "/dev/sda1 && echo 'hacked'",
            "/dev/sda1 | cat /etc/passwd",
            "/dev/sda1 `cat /etc/passwd`",
            "/dev/sda1 $(cat /etc/passwd)"
        ]
        
        for path in injection_paths:
            # パスが存在すると仮定
            mock_exists.return_value = True
            mock_access.return_value = True
            
            # モックをリセット
            mock_check_call.reset_mock()
            
            # フォーマット試行
            success, message = disk_utils.format_disk(path, "ntfs")
            
            # コマンドインジェクションが拒否されることを確認
            assert not success, f"{path}のフォーマットが許可されました"
            assert "不正なパス" in message, f"{path}のエラーメッセージが不適切です: {message}"
            
            # フォーマットコマンドが実行されていないことを確認
            mock_check_call.assert_not_called()
    
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    @patch('os.access')
    def test_set_permissions_security(self, mock_access, mock_exists, mock_check_call, logger_and_disk_utils):
        """権限設定時のセキュリティテスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # 不正なパスでの権限設定試行
        invalid_paths = [
            "/etc/shadow",
            "/etc/passwd",
            "/root",
            "/",
            "../etc/shadow",
            "../../etc/passwd"
        ]
        
        for path in invalid_paths:
            # パスが存在すると仮定
            mock_exists.return_value = True
            mock_access.return_value = True
            
            # モックをリセット
            mock_check_call.reset_mock()
            
            # 権限設定試行
            success, message = disk_utils.set_permissions(path)
            
            # 不正なパスの権限設定が拒否されることを確認
            assert not success, f"{path}の権限設定が許可されました"
            assert "不正なパス" in message, f"{path}のエラーメッセージが不適切です: {message}"
            
            # 権限設定コマンドが実行されていないことを確認
            mock_check_call.assert_not_called()
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_logger_path_traversal(self, mock_makedirs, mock_exists, temp_dir):
        """ロガーのパストラバーサル対策テスト"""
        # パストラバーサルを試みるパス
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\etc\\passwd",
            "/var/log/../../../etc/shadow",
            "logs/../../../../etc/passwd"
        ]
        
        for path in traversal_paths:
            # パスが存在しないと仮定
            mock_exists.return_value = False
            mock_makedirs.reset_mock()
            
            # ロガーの初期化
            logger = Logger(log_dir=path)
            
            # パスがサニタイズされていることを確認
            assert logger.log_dir.endswith("logs"), f"{path}のパスが正しくサニタイズされていません: {logger.log_dir}"
            
            # ログディレクトリが作成されたことを確認
            mock_makedirs.assert_called_once_with(logger.log_dir, exist_ok=True) 