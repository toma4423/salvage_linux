"""
DiskUtilsモジュールのユニットテスト
"""

import pytest
import subprocess
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from src.disk_utils import DiskUtils
from src.logger import Logger

@pytest.fixture
def mock_logger():
    """モック化されたロガーを提供するフィクスチャ"""
    return MagicMock(spec=Logger)

@pytest.fixture
def disk_utils(mock_logger):
    """DiskUtilsのインスタンスを提供するフィクスチャ"""
    return DiskUtils(mock_logger)

@pytest.mark.unit
class TestDiskUtils:
    """DiskUtilsクラスのテスト"""
    
    @patch('subprocess.check_output')
    def test_get_unmounted_disks_success(self, mock_check_output, disk_utils, mock_logger):
        """未マウントディスクの取得成功のテスト"""
        # サンプルのlsblkコマンド出力をモック
        mock_lsblk_output = json.dumps({
            "blockdevices": [
                {
                    "name": "sda",
                    "size": "100G",
                    "type": "disk",
                    "fstype": None,
                    "mountpoint": None,
                    "children": [
                        {
                            "name": "sda1",
                            "size": "100G",
                            "type": "part",
                            "fstype": "ntfs",
                            "mountpoint": None
                        }
                    ]
                },
                {
                    "name": "sdb",
                    "size": "50G",
                    "type": "disk",
                    "fstype": None,
                    "mountpoint": None
                }
            ]
        })
        mock_check_output.return_value = mock_lsblk_output
        
        # メソッドを実行
        result = disk_utils.get_unmounted_disks()
        
        # 結果を検証
        assert len(result) == 3  # sda, sdb, sda1の3つが返るはず
        assert result[0]["name"] == "sda"
        assert result[1]["name"] == "sda1"
        assert result[2]["name"] == "sdb"
        assert result[0]["size"] == "100G"
        assert result[1]["size"] == "100G"
        assert result[2]["size"] == "50G"
        assert mock_logger.info.call_count == 1
    
    @patch('subprocess.check_output')
    def test_get_unmounted_disks_subprocess_error(self, mock_check_output, disk_utils, mock_logger):
        """lsblkコマンドが失敗した場合のテスト"""
        # SubprocessErrorをシミュレート
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "lsblk")
        
        # メソッドを実行
        result = disk_utils.get_unmounted_disks()
        
        # 結果を検証
        assert result == []
        assert mock_logger.error.call_count == 1  # エラーログが記録されるはず
    
    @patch('subprocess.check_output')
    def test_get_unmounted_disks_json_error(self, mock_check_output, disk_utils, mock_logger):
        """不正なJSONが返された場合のテスト"""
        # 不正なJSONをシミュレート
        mock_check_output.return_value = "不正なJSON"
        
        # メソッドを実行
        result = disk_utils.get_unmounted_disks()
        
        # 結果を検証
        assert result == []
        assert mock_logger.error.call_count == 1  # エラーログが記録されるはず
    
    @patch('subprocess.check_output')
    def test_get_mounted_disks_success(self, mock_check_output, disk_utils, mock_logger):
        """マウント済みディスクの取得成功のテスト"""
        # サンプルのlsblkコマンド出力をモック
        mock_lsblk_output = json.dumps({
            "blockdevices": [
                {
                    "name": "sda",
                    "size": "100G",
                    "type": "disk",
                    "fstype": None,
                    "mountpoint": None,
                    "children": [
                        {
                            "name": "sda1",
                            "size": "100G",
                            "type": "part",
                            "fstype": "ext4",
                            "mountpoint": "/mnt/sda1"
                        }
                    ]
                },
                {
                    "name": "sdb",
                    "size": "50G",
                    "type": "disk",
                    "fstype": "ntfs",
                    "mountpoint": "/mnt/sdb"
                }
            ]
        })
        mock_check_output.return_value = mock_lsblk_output
        
        # メソッドを実行
        result = disk_utils.get_mounted_disks()
        
        # 結果を検証
        assert len(result) == 2  # sda1とsdbの2つが返るはず
        assert result[0]["name"] == "sda1"
        assert result[1]["name"] == "sdb"
        assert result[0]["mountpoint"] == "/mnt/sda1"
        assert result[1]["mountpoint"] == "/mnt/sdb"
        assert mock_logger.info.call_count == 1
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type(self, mock_check_output, disk_utils):
        """ファイルシステムタイプの取得テスト"""
        # blkidコマンドの出力をモック
        mock_check_output.return_value = "ntfs\n"
        
        # メソッドを実行
        result = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert result == "ntfs"
        mock_check_output.assert_called_once_with(
            ["blkid", "-o", "value", "-s", "TYPE", "/dev/sda1"],
            universal_newlines=True
        )
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type_error(self, mock_check_output, disk_utils):
        """ファイルシステムタイプの取得失敗のテスト"""
        # コマンドエラーをシミュレート
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "blkid")
        
        # メソッドを実行
        result = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert result == ""
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.check_call')
    def test_mount_disk_success(self, mock_check_call, mock_makedirs, mock_exists, disk_utils, mock_logger):
        """ディスクのマウント成功のテスト"""
        # マウントポイントが存在しないと仮定
        mock_exists.return_value = False
        
        # ファイルシステムタイプ取得メソッドをモック
        disk_utils.get_filesystem_type = MagicMock(return_value="ntfs")
        
        # メソッドを実行
        success, mount_point, error_msg = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert success is True
        assert mount_point == "/mnt/sda1"
        assert error_msg == ""
        
        # マウントポイントの作成が行われたことを確認
        mock_makedirs.assert_called_once_with("/mnt/sda1")
        
        # マウントコマンドが正しく実行されたことを確認
        mock_check_call.assert_called_once_with(["mount", "-t", "ntfs-3g", "/dev/sda1", "/mnt/sda1"])
        
        # ログが記録されたことを確認
        assert mock_logger.info.call_count == 2
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.check_call')
    def test_mount_disk_makedirs_error(self, mock_check_call, mock_makedirs, mock_exists, disk_utils, mock_logger):
        """マウントポイント作成エラーのテスト"""
        # マウントポイントが存在しないと仮定
        mock_exists.return_value = False
        
        # マウントポイント作成エラーをシミュレート
        mock_makedirs.side_effect = OSError("Permission denied")
        
        # メソッドを実行
        success, mount_point, error_msg = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert success is False
        assert mount_point == ""
        assert "マウントポイントの作成に失敗しました" in error_msg
        
        # マウントコマンドが実行されなかったことを確認
        mock_check_call.assert_not_called()
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called_once()
    
    @patch('os.path.exists')
    @patch('subprocess.check_call')
    def test_mount_disk_mount_error(self, mock_check_call, mock_exists, disk_utils, mock_logger):
        """マウントコマンドエラーのテスト"""
        # マウントポイントが既に存在すると仮定
        mock_exists.return_value = True
        
        # ファイルシステムタイプ取得メソッドをモック
        disk_utils.get_filesystem_type = MagicMock(return_value="ntfs")
        
        # マウントエラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mount")
        
        # メソッドを実行
        success, mount_point, error_msg = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert success is False
        assert mount_point == ""
        assert "マウントに失敗しました" in error_msg
        
        # マウントコマンドが実行されたことを確認
        mock_check_call.assert_called_once()
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called_once()
    
    @patch('subprocess.check_call')
    def test_format_disk_ntfs_success(self, mock_check_call, disk_utils, mock_logger):
        """NTFSフォーマット成功のテスト"""
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "ntfs")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # フォーマットコマンドが正しく実行されたことを確認
        mock_check_call.assert_called_once_with(["mkfs.ntfs", "-f", "/dev/sda1"])
        
        # ログが記録されたことを確認
        assert mock_logger.info.call_count == 2
    
    @patch('subprocess.check_call')
    def test_format_disk_exfat_success(self, mock_check_call, disk_utils, mock_logger):
        """exFATフォーマット成功のテスト"""
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "exfat")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # フォーマットコマンドが正しく実行されたことを確認
        mock_check_call.assert_called_once_with(["mkfs.exfat", "/dev/sda1"])
        
        # ログが記録されたことを確認
        assert mock_logger.info.call_count == 2
    
    @patch('subprocess.check_call')
    def test_format_disk_unsupported_fs(self, mock_check_call, disk_utils, mock_logger):
        """サポートされていないファイルシステムのテスト"""
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "ext4")  # ext4はサポート外と仮定
        
        # 結果を検証
        assert success is False
        assert "サポートされていないファイルシステムタイプ" in error_msg
        
        # フォーマットコマンドが実行されなかったことを確認
        mock_check_call.assert_not_called()
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called_once()
    
    @patch('subprocess.check_call')
    def test_format_disk_error(self, mock_check_call, disk_utils, mock_logger):
        """フォーマットエラーのテスト"""
        # フォーマットエラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mkfs.ntfs")
        
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "ntfs")
        
        # 結果を検証
        assert success is False
        assert "フォーマットに失敗しました" in error_msg
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called_once()
    
    @patch('subprocess.check_call')
    def test_set_permissions_success(self, mock_check_call, disk_utils, mock_logger):
        """権限付与成功のテスト"""
        # メソッドを実行
        success, error_msg = disk_utils.set_permissions("/mnt/sda1")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # 権限付与コマンドが正しく実行されたことを確認
        mock_check_call.assert_called_once_with(["chmod", "-R", "777", "/mnt/sda1"])
        
        # ログが記録されたことを確認
        assert mock_logger.info.call_count == 2
    
    @patch('subprocess.check_call')
    def test_set_permissions_error(self, mock_check_call, disk_utils, mock_logger):
        """権限付与エラーのテスト"""
        # 権限付与エラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "chmod")
        
        # メソッドを実行
        success, error_msg = disk_utils.set_permissions("/mnt/sda1")
        
        # 結果を検証
        assert success is False
        assert "権限付与に失敗しました" in error_msg
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called_once()
    
    @patch('subprocess.Popen')
    def test_open_file_manager_success(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動成功のテスト"""
        # メソッドを実行
        success, error_msg = disk_utils.open_file_manager("/mnt/sda1")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # ファイルマネージャー起動コマンドが正しく実行されたことを確認
        mock_popen.assert_called_once_with(["pcmanfm", "/mnt/sda1"])
        
        # ログが記録されたことを確認
        assert mock_logger.info.call_count == 1
    
    @patch('subprocess.Popen')
    def test_open_file_manager_error(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動エラーのテスト"""
        # ファイルマネージャー起動エラーをシミュレート
        mock_popen.side_effect = FileNotFoundError("No such file or directory: 'pcmanfm'")
        
        # メソッドを実行
        success, error_msg = disk_utils.open_file_manager("/mnt/sda1")
        
        # 結果を検証
        assert success is False
        assert "ファイルマネージャーの起動に失敗しました" in error_msg
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called_once() 