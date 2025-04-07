"""
開発環境用のDiskUtils統合テスト
macOS環境で実行可能なテストのみを含みます。
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess
from src.disk_utils import DiskUtils
from src.logger import Logger

@pytest.fixture
def logger():
    """テスト用のLoggerインスタンスを返すフィクスチャ"""
    return Logger()

@pytest.fixture
def disk_utils(logger):
    """テスト用のDiskUtilsインスタンスを返すフィクスチャ"""
    return DiskUtils(logger)

@pytest.mark.integration
class TestDevDiskUtilsWithLogger:
    """開発環境用のDiskUtils統合テストクラス"""
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type_logging(self, mock_check_output, disk_utils, logger):
        """ファイルシステムタイプ取得のログ記録を確認"""
        # 成功ケース
        mock_check_output.return_value = b'TYPE=ntfs\n'
        disk_utils.get_filesystem_type("/dev/sda1")
        assert any("ファイルシステムタイプを取得しました" in msg for msg in logger.messages)
        
        # エラーケース
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "blkid")
        with pytest.raises(RuntimeError):
            disk_utils.get_filesystem_type("/dev/sda1")
        assert any("ファイルシステムタイプの取得に失敗しました" in msg for msg in logger.messages)

    @patch('subprocess.check_call')
    def test_format_disk_logging(self, mock_check_call, disk_utils, logger):
        """ディスクフォーマットのログ記録を確認"""
        # 成功ケース
        disk_utils.format_disk("/dev/sda1", "ntfs")
        assert any("ディスクをフォーマットしました" in msg for msg in logger.messages)
        
        # エラーケース
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mkfs.ntfs")
        disk_utils.format_disk("/dev/sda1", "ntfs")
        assert any("ディスクのフォーマットに失敗しました" in msg for msg in logger.messages)

    @patch('subprocess.check_call')
    def test_check_refs_tools_available_logging(self, mock_check_call, disk_utils, logger):
        """ReFSツール確認のログ記録を確認"""
        # 成功ケース
        disk_utils.check_refs_tools_available()
        assert any("ReFSツールが利用可能です" in msg for msg in logger.messages)
        
        # エラーケース
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "which")
        disk_utils.check_refs_tools_available()
        assert any("ReFSツールが利用できません" in msg for msg in logger.messages) 