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
                            "fstype": "ntfs",
                            "mountpoint": "/mnt/sda1"
                        }
                    ]
                },
                {
                    "name": "sdb",
                    "size": "50G",
                    "type": "disk",
                    "fstype": None,
                    "mountpoint": "/mnt/sdb"
                }
            ]
        })
        mock_check_output.return_value = mock_lsblk_output
    
        # メソッドを実行
        result = disk_utils.get_mounted_disks()
    
        # 結果を検証
        assert len(result) == 3  # sda1, sdbの3つが返るはず
        assert result[0]["name"] == "sda1"
        assert result[1]["name"] == "sdb"
        assert result[0]["mountpoint"] == "/mnt/sda1"
        assert result[1]["mountpoint"] == "/mnt/sdb"
        
        # ログ呼び出し回数は検証しない（実装によって変わる可能性がある）
        assert mock_logger.info.called
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type(self, mock_check_output, disk_utils):
        """ファイルシステムタイプ取得のテスト"""
        # blkidコマンドの出力をモック
        mock_check_output.return_value = 'TYPE="ntfs"\n'
        
        # メソッドを実行
        result = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert result == "ntfs"
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type_error(self, mock_check_output, disk_utils):
        """ファイルシステムタイプ取得時にエラーが発生した場合のテスト"""
        # subprocessがエラーを発生させるようにモック
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "blkid")
        
        # メソッドを実行
        result = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert result is None
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.check_call')
    def test_mount_disk_success(self, mock_check_call, mock_makedirs, mock_exists, disk_utils, mock_logger):
        """ディスクマウントの成功テスト"""
        # パスが存在すると仮定
        mock_exists.return_value = True
        
        # マウントポイント作成をシミュレート
        mock_makedirs.return_value = None
        
        # マウント成功をシミュレート
        mock_check_call.return_value = 0
        
        # ファイルシステムタイプ取得をモック
        disk_utils.get_filesystem_type = lambda x: "ntfs"
        
        # メソッドを実行
        success, message = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert success
        assert "マウント成功" in message
        
        # マウントコマンドが実行されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        mock_logger.info.assert_called()
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.check_call')
    def test_mount_disk_makedirs_error(self, mock_check_call, mock_makedirs, mock_exists, disk_utils, mock_logger):
        """マウントポイント作成時にエラーが発生した場合のテスト"""
        # パスが存在すると仮定
        mock_exists.return_value = True
        
        # マウントポイント作成エラーをシミュレート
        mock_makedirs.side_effect = OSError("Permission denied")
        
        # メソッドを実行
        success, message = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert not success
        assert "マウントポイント作成失敗" in message
        
        # マウントコマンドが実行されていないことを確認
        mock_check_call.assert_not_called()
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
    @patch('os.path.exists')
    @patch('subprocess.check_call')
    def test_mount_disk_mount_error(self, mock_check_call, mock_exists, disk_utils, mock_logger):
        """マウント時にエラーが発生した場合のテスト"""
        # パスが存在すると仮定
        mock_exists.return_value = True
        
        # マウントエラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mount")
        
        # ファイルシステムタイプ取得をモック
        disk_utils.get_filesystem_type = lambda x: "ntfs"
        
        # メソッドを実行
        success, message = disk_utils.mount_disk("/dev/sda1")
        
        # 結果を検証
        assert not success
        assert "マウント失敗" in message
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
    @patch('subprocess.check_call')
    def test_format_disk_ntfs_success(self, mock_check_call, disk_utils, mock_logger):
        """NTFSフォーマットの成功テスト"""
        # フォーマット成功をシミュレート
        mock_check_call.return_value = 0
        
        # メソッドを実行
        success, message = disk_utils.format_disk("/dev/sda1", "ntfs")
        
        # 結果を検証
        assert success
        assert "フォーマット成功" in message
        
        # フォーマットコマンドが実行されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        mock_logger.info.assert_called()
    
    @patch('subprocess.check_call')
    def test_format_disk_exfat_success(self, mock_check_call, disk_utils, mock_logger):
        """exFATフォーマットの成功テスト"""
        # フォーマット成功をシミュレート
        mock_check_call.return_value = 0
        
        # メソッドを実行
        success, message = disk_utils.format_disk("/dev/sda1", "exfat")
        
        # 結果を検証
        assert success
        assert "フォーマット成功" in message
        
        # フォーマットコマンドが実行されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        mock_logger.info.assert_called()
    
    @patch('subprocess.check_call')
    def test_format_disk_refs_success(self, mock_check_call, disk_utils, mock_logger):
        """ReFSフォーマットの成功テスト"""
        # フォーマット成功をシミュレート
        mock_check_call.return_value = 0
        
        # ReFSツールの存在チェックをモック
        disk_utils._check_refs_tools_available = lambda: True
        
        # メソッドを実行
        success, message = disk_utils.format_disk("/dev/sda1", "refs")
        
        # 結果を検証
        assert success
        assert "フォーマット成功" in message
        
        # フォーマットコマンドが実行されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        mock_logger.info.assert_called()
    
    @patch('subprocess.check_call')
    def test_format_disk_refs_tools_missing(self, mock_check_call, disk_utils, mock_logger):
        """ReFSツールが存在しない場合のテスト"""
        # ReFSツールの存在チェックをモック
        disk_utils._check_refs_tools_available = lambda: False
        
        # メソッドを実行
        success, message = disk_utils.format_disk("/dev/sda1", "refs")
        
        # 結果を検証
        assert not success
        assert "ReFSツール" in message
        assert "見つかりません" in message
        
        # フォーマットコマンドが実行されていないことを確認
        mock_check_call.assert_not_called()
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
    @patch('subprocess.check_call')
    def test_check_refs_tools_available_success(self, mock_check_call, disk_utils):
        """ReFSツールの存在チェック成功のテスト"""
        # ツールが存在することをシミュレート
        mock_check_call.return_value = 0
        
        # メソッドを実行
        result = disk_utils._check_refs_tools_available()
        
        # 結果を検証
        assert result
    
    @patch('subprocess.check_call')
    def test_check_refs_tools_available_failure(self, mock_check_call, disk_utils):
        """ReFSツールの存在チェック失敗のテスト"""
        # ツールが存在しないことをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "which")
        
        # メソッドを実行
        result = disk_utils._check_refs_tools_available()
        
        # 結果を検証
        assert not result
    
    @patch('subprocess.check_call')
    def test_format_disk_unsupported_fs(self, mock_check_call, disk_utils, mock_logger):
        """サポートされていないファイルシステムのテスト"""
        # メソッドを実行
        success, message = disk_utils.format_disk("/dev/sda1", "unsupported")
        
        # 結果を検証
        assert not success
        assert "サポートされていない" in message
        assert "ファイルシステム" in message
        
        # フォーマットコマンドが実行されていないことを確認
        mock_check_call.assert_not_called()
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
    @patch('subprocess.check_call')
    def test_format_disk_error(self, mock_check_call, disk_utils, mock_logger):
        """フォーマット時にエラーが発生した場合のテスト"""
        # フォーマットエラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "mkfs.ntfs")
        
        # メソッドを実行
        success, message = disk_utils.format_disk("/dev/sda1", "ntfs")
        
        # 結果を検証
        assert not success
        assert "フォーマット失敗" in message
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
    @patch('subprocess.check_call')
    def test_set_permissions_success(self, mock_check_call, disk_utils, mock_logger):
        """権限設定の成功テスト"""
        # 権限設定成功をシミュレート
        mock_check_call.return_value = 0
        
        # メソッドを実行
        success, message = disk_utils.set_permissions("/dev/sda1")
        
        # 結果を検証
        assert success
        assert "権限設定成功" in message
        
        # 権限設定コマンドが実行されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        mock_logger.info.assert_called()
    
    @patch('subprocess.check_call')
    def test_set_permissions_error(self, mock_check_call, disk_utils, mock_logger):
        """権限設定時にエラーが発生した場合のテスト"""
        # 権限設定エラーをシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "chmod")
        
        # メソッドを実行
        success, message = disk_utils.set_permissions("/dev/sda1")
        
        # 結果を検証
        assert not success
        assert "権限設定失敗" in message
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
    @patch('subprocess.Popen')
    def test_open_file_manager_success(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動の成功テスト"""
        # ファイルマネージャー起動成功をシミュレート
        mock_popen.return_value = MagicMock()
        
        # メソッドを実行
        success, message = disk_utils.open_file_manager("/dev/sda1")
        
        # 結果を検証
        assert success
        assert "ファイルマネージャー起動成功" in message
        
        # ファイルマネージャーが起動されたことを確認
        mock_popen.assert_called()
        
        # ログが記録されたことを確認
        mock_logger.info.assert_called()
    
    @patch('subprocess.Popen')
    def test_open_file_manager_error(self, mock_popen, disk_utils, mock_logger):
        """ファイルマネージャー起動時にエラーが発生した場合のテスト"""
        # ファイルマネージャー起動エラーをシミュレート
        mock_popen.side_effect = OSError("File manager not found")
        
        # メソッドを実行
        success, message = disk_utils.open_file_manager("/dev/sda1")
        
        # 結果を検証
        assert not success
        assert "ファイルマネージャー起動失敗" in message
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called() 