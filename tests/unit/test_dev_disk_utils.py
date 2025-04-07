"""
開発環境用のDiskUtilsテスト
macOS環境で実行可能なテストのみを含みます。
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess
from src.disk_utils import DiskUtils
from src.logger import Logger

@pytest.fixture
def mock_logger():
    """モック化されたLoggerオブジェクトを返すフィクスチャ"""
    return MagicMock()

@pytest.fixture
def disk_utils(mock_logger):
    """テスト用のDiskUtilsインスタンスを返すフィクスチャ"""
    return DiskUtils(mock_logger)

@pytest.mark.unit
class TestDevDiskUtils:
    """開発環境用のDiskUtilsテストクラス"""
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type_success(self, mock_check_output, disk_utils, mock_logger):
        """ファイルシステムタイプの取得が成功することを確認"""
        mock_check_output.return_value = b'TYPE=ntfs\n'
        result = disk_utils.get_filesystem_type("/dev/sda1")
        assert result == "ntfs"

    @patch('subprocess.check_output')
    def test_get_filesystem_type_error(self, mock_check_output, disk_utils, mock_logger):
        """ファイルシステムタイプの取得に失敗した場合のエラー処理を確認"""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "blkid")
        with pytest.raises(RuntimeError):
            disk_utils.get_filesystem_type("/dev/sda1")
    
    @patch('subprocess.check_call')
    def test_format_disk_success(self, mock_check_call, disk_utils, mock_logger):
        """ディスクのフォーマットが成功することを確認"""
        success, message = disk_utils.format_disk("/dev/sda1", "ntfs")
        assert success
        assert "フォーマットしました" in message
        mock_check_call.assert_called_once_with(["mkfs.ntfs", "/dev/sda1"])

    @patch('subprocess.check_call')
    def test_format_disk_invalid_path(self, mock_check_call, disk_utils, mock_logger):
        """不正なパスでのフォーマットが拒否されることを確認"""
        success, message = disk_utils.format_disk("/etc/passwd", "ntfs")
        assert not success
        assert "不正なデバイスパスです" in message

    @patch('subprocess.check_call')
    def test_format_disk_invalid_fs_type(self, mock_check_call, disk_utils, mock_logger):
        """不正なファイルシステムタイプでのフォーマットが拒否されることを確認"""
        success, message = disk_utils.format_disk("/dev/sda1", "invalid")
        assert not success
        assert "サポートされていないファイルシステムタイプです" in message

    @patch('subprocess.check_call')
    def test_format_disk_error(self, mock_check_call, disk_utils, mock_logger):
        """フォーマットに失敗した場合のエラー処理を確認"""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mkfs.ntfs")
        success, message = disk_utils.format_disk("/dev/sda1", "ntfs")
        assert not success
        assert "フォーマットに失敗しました" in message

    @patch('subprocess.check_call')
    def test_check_refs_tools_available_success(self, mock_check_call, disk_utils, mock_logger):
        """ReFSツールの存在確認が成功することを確認"""
        result = disk_utils.check_refs_tools_available()
        assert result
        mock_check_call.assert_called_once_with(["which", "mkfs.refs"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @patch('subprocess.check_call')
    def test_check_refs_tools_available_error(self, mock_check_call, disk_utils, mock_logger):
        """ReFSツールが存在しない場合のエラー処理を確認"""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "which")
        result = disk_utils.check_refs_tools_available()
        assert not result 