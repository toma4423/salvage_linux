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
    logger = Logger(log_dir=log_dir)
    disk_utils = DiskUtils(logger)
    
    return logger, disk_utils

@pytest.mark.system
@pytest.mark.security
class TestSecurity:
    """セキュリティテスト"""
    
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    def test_format_disk_permission_validation(self, mock_exists, mock_check_call, logger_and_disk_utils):
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
            
            # モックをリセット
            mock_check_call.reset_mock()
            
            # フォーマット試行
            success, message = disk_utils.format_disk(path, "ntfs")
            
            # システムディレクトリのフォーマットが拒否されることを確認
            assert not success, f"{path}のフォーマットが許可されました"
            assert "システムディレクトリ" in message, f"{path}のエラーメッセージが不適切です: {message}"
            
            # フォーマットコマンドが実行されていないことを確認
            mock_check_call.assert_not_called()
        
        # 非システムディレクトリのテスト
        for path in non_system_paths:
            # パスが存在すると仮定
            mock_exists.return_value = True
            
            # モックをリセット
            mock_check_call.reset_mock()
            
            # フォーマット試行
            success, message = disk_utils.format_disk(path, "ntfs")
            
            # 非システムディレクトリのフォーマットが許可されることを確認
            assert success, f"{path}のフォーマットが拒否されました"
            
            # フォーマットコマンドが実行されたことを確認
            mock_check_call.assert_called()
    
    @patch('subprocess.check_call')
    def test_mount_disk_path_validation(self, mock_check_call, logger_and_disk_utils):
        """ディスクマウント時のパス検証テスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # 不正なパスでのマウント試行
        invalid_paths = [
            "../etc/shadow",
            "../../etc/passwd",
            "/dev/../../etc",
            "; rm -rf /",
            "& echo malicious",
            "/dev/sda1; sudo rm -rf /"
        ]
        
        for path in invalid_paths:
            # マウント試行（3つの戻り値を受け取る）
            success, message, _ = disk_utils.mount_disk(path)
            
            # 不正なパスのマウントが拒否されることを確認
            assert not success, f"{path}のマウントが許可されました"
            assert "無効" in message, f"{path}のエラーメッセージが不適切です: {message}"
            
            # マウントコマンドが実行されていないことを確認
            mock_check_call.assert_not_called()
    
    @patch('subprocess.check_call')
    def test_format_disk_command_injection(self, mock_check_call, logger_and_disk_utils):
        """フォーマット時のコマンドインジェクション対策テスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # コマンドインジェクションを試みるパス
        injection_paths = [
            "/dev/sda1; rm -rf /",
            "/dev/sda1 && echo 'hacked'",
            "/dev/sda1 || true",
            "/dev/sda1 | cat /etc/passwd"
        ]
        
        # 不正なファイルシステムタイプ
        injection_fs_types = [
            "ntfs; rm -rf /",
            "ntfs && echo 'hacked'",
            "ntfs || true",
            "ntfs | cat /etc/passwd",
            "invalid_fs_type"
        ]
        
        # パスのテスト
        for path in injection_paths:
            # フォーマット試行
            success, message = disk_utils.format_disk(path, "ntfs")
            
            # 不正なパスのフォーマットが拒否されることを確認
            assert not success, f"{path}のフォーマットが許可されました"
            assert "無効" in message, f"{path}のエラーメッセージが不適切です: {message}"
            
        # ファイルシステムタイプのテスト
        for fs_type in injection_fs_types:
            # フォーマット試行
            success, message = disk_utils.format_disk("/dev/sda1", fs_type)
            
            # 不正なファイルシステムタイプのフォーマットが拒否されることを確認
            assert not success, f"{fs_type}のフォーマットが許可されました"
            assert "無効" in message or "サポートされていない" in message, f"{fs_type}のエラーメッセージが不適切です: {message}"
    
    @patch('subprocess.check_call')
    def test_set_permissions_security(self, mock_check_call, logger_and_disk_utils):
        """権限付与時のセキュリティテスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # 不正なマウントポイントでの権限付与試行
        invalid_mount_points = [
            "/",
            "/etc",
            "/boot",
            "/usr",
            "/var",
            "../etc",
            "/mnt; rm -rf /"
        ]
        
        for mount_point in invalid_mount_points:
            # 権限付与試行
            success, message = disk_utils.set_permissions(mount_point)
            
            # 重要なシステムディレクトリへの権限付与が拒否されることを確認
            assert not success, f"{mount_point}への権限付与が許可されました"
            
            # エラーメッセージの検証（パスによって異なるメッセージが返される）
            if mount_point.startswith("/") and not ";" in mount_point:
                if mount_point in disk_utils.protected_dirs:
                    assert "システムディレクトリ" in message, f"{mount_point}のエラーメッセージが不適切です: {message}"
                else:
                    assert "無効" in message or "不正" in message, f"{mount_point}のエラーメッセージが不適切です: {message}"
            else:
                assert "無効" in message, f"{mount_point}のエラーメッセージが不適切です: {message}"
            
            # 権限付与コマンドが実行されていないことを確認
            mock_check_call.assert_not_called()
    
    def test_logger_path_traversal(self, temp_dir):
        """ロガーのパストラバーサル対策テスト"""
        # 不正なログディレクトリパスでのロガー初期化試行
        invalid_log_dirs = [
            "../../../etc", 
            "../../tmp",
            "/var/log; rm -rf /",
            "/tmp/../../../../etc"
        ]
        
        for log_dir in invalid_log_dirs:
            # ロガー初期化
            logger = Logger(log_dir=log_dir)
            
            # ログファイルのパスが適切に処理されていることを確認
            assert ".." not in logger.log_file
            assert ";" not in logger.log_file
            assert "|" not in logger.log_file
            assert "&" not in logger.log_file
            
            # 実際のログファイルパスがシステムディレクトリにならないことを確認
            for system_dir in ["/etc", "/usr", "/var", "/boot"]:
                assert not logger.log_file.startswith(system_dir) 