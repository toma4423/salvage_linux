"""
DiskUtilsのユニットテスト
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import os
import subprocess
from src.disk_utils import DiskUtils

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
        
        # ログ呼び出し回数は検証しない（実装によって変わる可能性がある）
        assert mock_logger.info.called
    
    @patch('subprocess.check_output')
    def test_get_unmounted_disks_subprocess_error(self, mock_check_output, disk_utils, mock_logger):
        """未マウントディスク取得時にsubprocessエラーが発生した場合のテスト"""
        # subprocessがエラーを発生させるようにモック
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "lsblk")
        
        # メソッドを実行
        result = disk_utils.get_unmounted_disks()
        
        # 結果を検証
        assert result == []
        
        # Loggerがエラーを記録したことを確認
        mock_logger.error.assert_called()
    
    @patch('subprocess.check_output')
    def test_get_unmounted_disks_json_error(self, mock_check_output, disk_utils, mock_logger):
        """未マウントディスク取得時にJSONエラーが発生した場合のテスト"""
        # 不正なJSONを返すようにモック
        mock_check_output.return_value = "invalid json"
        
        # メソッドを実行
        result = disk_utils.get_unmounted_disks()
        
        # 結果を検証
        assert result == []
        
        # Loggerがエラーを記録したことを確認
        mock_logger.error.assert_called()
    
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
        
        # ログ呼び出し回数は検証しない（実装によって変わる可能性がある）
        assert mock_logger.info.called
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type(self, mock_check_output, disk_utils):
        """ファイルシステムタイプ取得のテスト"""
        # blkidコマンドの出力をモック（universal_newlines=Trueを設定するため文字列で返す）
        mock_check_output.return_value = "ntfs"
        
        # メソッドを実行
        fs_type = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert fs_type == "ntfs"
        
        # blkidコマンドが正しく呼び出されたことを確認
        mock_check_output.assert_called()
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type_error(self, mock_check_output, disk_utils):
        """ファイルシステムタイプ取得エラーのテスト"""
        # blkidコマンドがエラーを発生させるようにモック
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "blkid")
        
        # メソッドを実行
        fs_type = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert fs_type == ""
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.check_call')
    def test_mount_disk_success(self, mock_check_call, mock_makedirs, mock_exists, disk_utils, mock_logger):
        """マウント成功のテスト"""
        # パスのバリデーションをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        
        # マウントポイントが既に存在すると仮定
        mock_exists.return_value = True
        
        # ファイルシステムタイプ取得メソッドをモック
        disk_utils.get_filesystem_type = MagicMock(return_value="ntfs")
        
        # メソッドを実行
        success, mount_point, error_msg = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert success is True
        assert mount_point == "/mnt/sda1"
        assert error_msg == ""
        
        # マウントコマンドが正しく呼び出されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        assert mock_logger.info.called
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.check_call')
    def test_mount_disk_makedirs_error(self, mock_check_call, mock_makedirs, mock_exists, disk_utils, mock_logger):
        """マウントポイント作成エラーのテスト"""
        # パスのバリデーションをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        
        # マウントポイントが存在しないと仮定
        mock_exists.return_value = False
        
        # マウントポイント作成エラーをシミュレート
        mock_makedirs.side_effect = OSError("Permission denied")
        
        # メソッドを実行
        success, error_msg, _ = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert success is False
        assert "マウントポイントの作成に失敗" in error_msg
        
        # マウントコマンドが呼び出されていないことを確認
        mock_check_call.assert_not_called()
        
        # エラーログが記録されたことを確認
        assert mock_logger.error.called
    
    @patch('os.path.exists')
    @patch('subprocess.check_call')
    def test_mount_disk_mount_error(self, mock_check_call, mock_exists, disk_utils, mock_logger):
        """マウントコマンドエラーのテスト"""
        # パスのバリデーションをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        
        # マウントポイントが既に存在すると仮定
        mock_exists.return_value = True
        
        # ファイルシステムタイプ取得メソッドをモック
        disk_utils.get_filesystem_type = MagicMock(return_value="ntfs")
        
        # マウントエラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mount")
        
        # メソッドを実行
        success, error_msg, _ = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert success is False
        assert "マウントに失敗" in error_msg
        
        # エラーログが記録されたことを確認
        assert mock_logger.error.called
    
    @patch('subprocess.check_call')
    def test_format_disk_ntfs_success(self, mock_check_call, disk_utils, mock_logger):
        """NTFSフォーマット成功のテスト"""
        # パスのバリデーションとシステムディレクトリチェックをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        disk_utils._is_system_directory = MagicMock(return_value=False)
        
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "ntfs")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # フォーマットコマンドが正しく呼び出されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        assert mock_logger.info.called
    
    @patch('subprocess.check_call')
    def test_format_disk_exfat_success(self, mock_check_call, disk_utils, mock_logger):
        """exFATフォーマット成功のテスト"""
        # パスのバリデーションとシステムディレクトリチェックをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        disk_utils._is_system_directory = MagicMock(return_value=False)
        
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "exfat")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # フォーマットコマンドが正しく呼び出されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        assert mock_logger.info.called
    
    @patch('subprocess.check_call')
    def test_format_disk_unsupported_fs(self, mock_check_call, disk_utils, mock_logger):
        """サポートされていないファイルシステムのテスト"""
        # パスのバリデーションとシステムディレクトリチェックをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        disk_utils._is_system_directory = MagicMock(return_value=False)
        
        # サポートされていないファイルシステムを設定
        disk_utils.allowed_fs_types = ["ntfs", "exfat"]
        
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "ext4")
        
        # 結果を検証
        assert success is False
        assert "サポートされていない" in error_msg
        
        # フォーマットコマンドが呼び出されていないことを確認
        mock_check_call.assert_not_called()
        
        # エラーログが記録されたことを確認
        assert mock_logger.error.called
    
    @patch('subprocess.check_call')
    def test_format_disk_error(self, mock_check_call, disk_utils, mock_logger):
        """フォーマットエラーのテスト"""
        # パスのバリデーションとシステムディレクトリチェックをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        disk_utils._is_system_directory = MagicMock(return_value=False)
        
        # フォーマットエラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mkfs.ntfs")
        
        # メソッドを実行
        success, error_msg = disk_utils.format_disk("/dev/sda1", "ntfs")
        
        # 結果を検証
        assert success is False
        assert "エラー" in error_msg or "失敗" in error_msg
        
        # エラーログが記録されたことを確認
        assert mock_logger.error.called
    
    @patch('subprocess.check_call')
    def test_set_permissions_success(self, mock_check_call, disk_utils, mock_logger):
        """権限付与成功のテスト"""
        # パスのバリデーションとシステムディレクトリチェックをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        disk_utils._is_system_directory = MagicMock(return_value=False)
        
        # メソッドを実行
        success, error_msg = disk_utils.set_permissions("/mnt/sda1")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # 権限付与コマンドが正しく呼び出されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        assert mock_logger.info.called
    
    @patch('subprocess.check_call')
    def test_set_permissions_error(self, mock_check_call, disk_utils, mock_logger):
        """権限付与エラーのテスト"""
        # パスのバリデーションとシステムディレクトリチェックをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        disk_utils._is_system_directory = MagicMock(return_value=False)
        
        # 権限付与エラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "chmod")
        
        # メソッドを実行
        success, error_msg = disk_utils.set_permissions("/mnt/sda1")
        
        # 結果を検証
        assert success is False
        assert "エラー" in error_msg or "失敗" in error_msg
        
        # エラーログが記録されたことを確認
        assert mock_logger.error.called
    
    @patch('subprocess.Popen')
    def test_open_file_manager_success(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動成功のテスト"""
        # パスのバリデーションをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        
        # メソッドを実行
        success, error_msg = disk_utils.open_file_manager("/mnt/sda1")
        
        # 結果を検証
        assert success is True
        assert error_msg == ""
        
        # Popenが正しく呼び出されたことを確認
        mock_popen.assert_called()
        
        # ログが記録されたことを確認
        assert mock_logger.info.called
    
    @patch('subprocess.Popen')
    def test_open_file_manager_error(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動エラーのテスト"""
        # パスのバリデーションをモック
        disk_utils._is_valid_path = MagicMock(return_value=True)
        
        # エラーをシミュレート
        mock_popen.side_effect = FileNotFoundError("No such file or directory")
        
        # メソッドを実行
        success, error_msg = disk_utils.open_file_manager("/mnt/sda1")
        
        # 結果を検証
        assert success is False
        assert "利用可能なファイルマネージャーが見つかりません" in error_msg
        
        # エラーログが記録されたことを確認
        assert mock_logger.error.called 