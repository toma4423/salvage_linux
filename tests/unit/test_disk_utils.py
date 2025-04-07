"""
DiskUtilsのユニットテスト
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import os
import subprocess
from src.disk_utils import DiskUtils, DiskInfo, UnmountedDisksResponse, validate_unmounted_disks_response, validate_disk_info
from typing import List, Dict, Any
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
class TestDiskUtils:
    """DiskUtilsのテストクラス"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テストの前準備"""
        self.logger = Logger()
        self.disk_utils = DiskUtils(self.logger)
        yield
        # クリーンアップ処理があればここに記述

    @patch('subprocess.check_output')
    @patch('json.loads')
    def test_get_unmounted_disks(self, mock_json_loads, mock_check_output, disk_utils, mock_logger):
        """未マウントディスクの取得テスト"""
        # lsblkコマンドの出力をシミュレート
        mock_output = {
            "blockdevices": [
                {
                    "name": "sda1",
                    "size": "8G",
                    "type": "part",
                    "mountpoint": None,
                    "fstype": "ext4"
                },
                {
                    "name": "sdb1",
                    "size": "16G",
                    "type": "part",
                    "mountpoint": None,
                    "fstype": "ntfs"
                }
            ]
        }
        mock_check_output.return_value = json.dumps(mock_output).encode('utf-8')
        mock_json_loads.return_value = mock_output
        
        # メソッドを実行
        result = disk_utils.get_unmounted_disks()
        
        # 結果を検証
        assert isinstance(result, dict)
        assert "blockdevices" in result
        assert len(result["blockdevices"]) == 2
        
        # UnmountedDisksResponse型に準拠していることを確認
        assert validate_unmounted_disks_response(result)
        
        # lsblkコマンドが実行されたことを確認
        mock_check_output.assert_called()
    
    @patch('subprocess.check_output')
    @patch('json.loads')
    def test_get_mounted_disks(self, mock_json_loads, mock_check_output, disk_utils, mock_logger):
        """マウント済みディスクの取得テスト"""
        # lsblkコマンドの出力をシミュレート
        mock_output = {
            "blockdevices": [
                {
                    "name": "sda1",
                    "size": "8G",
                    "type": "part",
                    "mountpoint": "/mnt/test",
                    "fstype": "ext4"
                },
                {
                    "name": "sdb1",
                    "size": "16G",
                    "type": "part",
                    "mountpoint": "/mnt/data",
                    "fstype": "ntfs"
                }
            ]
        }
        mock_check_output.return_value = json.dumps(mock_output).encode('utf-8')
        mock_json_loads.return_value = mock_output
        
        # メソッドを実行
        result = disk_utils.get_mounted_disks()
        
        # 結果を検証
        assert isinstance(result, list)
        assert len(result) == 2
        
        # List[DiskInfo]型に準拠していることを確認
        assert isinstance(result, List)
        
        # 最初のディスク情報を取得
        disk_info = result[0]
        
        # DiskInfo型に準拠していることを確認
        assert isinstance(disk_info, dict)
        assert validate_disk_info(disk_info)
        
        # 必須フィールドの存在を確認
        assert "name" in disk_info
        assert "path" in disk_info
        assert "device" in disk_info
        assert "size" in disk_info
        assert "type" in disk_info
        assert "mountpoint" in disk_info
        
        # lsblkコマンドが実行されたことを確認
        mock_check_output.assert_called()
    
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

    @patch('subprocess.Popen')
    def test_open_file_manager_success(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動の成功テスト"""
        # プロセス起動成功をシミュレート
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        # メソッドを実行
        success, message = disk_utils.open_file_manager("/mnt/test")
        
        # 結果を検証
        assert success
        assert "ファイルマネージャー" in message
        
        # プロセスが起動されたことを確認
        mock_popen.assert_called_once_with(["xdg-open", "/mnt/test"])
    
    @patch('subprocess.Popen')
    def test_open_file_manager_error(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動エラーのテスト"""
        # プロセス起動エラーをシミュレート
        mock_popen.side_effect = OSError("Command not found")
        
        # メソッドを実行
        success, message = disk_utils.open_file_manager("/mnt/test")
        
        # 結果を検証
        assert not success
        assert "ファイルマネージャー" in message
        assert "失敗" in message
        
        # プロセスが起動されたことを確認
        mock_popen.assert_called_once_with(["xdg-open", "/mnt/test"]) 