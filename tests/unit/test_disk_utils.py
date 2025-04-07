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
    def test_get_unmounted_disks(self, mock_check_output, disk_utils, mock_logger):
        """未マウントディスクの取得テスト"""
        # lsblkコマンドの出力をシミュレート
        mock_check_output.return_value = b"/dev/sda1\n/dev/sdb1\n"
        
        # メソッドを実行
        disks = disk_utils.get_unmounted_disks()
        
        # 結果を検証
        assert len(disks) == 2
        assert "/dev/sda1" in disks
        assert "/dev/sdb1" in disks
        
        # lsblkコマンドが実行されたことを確認
        mock_check_output.assert_called()
    
    @patch('subprocess.check_output')
    def test_get_mounted_disks(self, mock_check_output, disk_utils, mock_logger):
        """マウント済みディスクの取得テスト"""
        # mountコマンドの出力をシミュレート
        mock_check_output.return_value = b"/dev/sda1 on /mnt/test type ext4\n/dev/sdb1 on /mnt/data type ntfs\n"
        
        # メソッドを実行
        disks = disk_utils.get_mounted_disks()
        
        # 結果を検証
        assert len(disks) == 2
        assert "/dev/sda1" in disks
        assert "/dev/sdb1" in disks
        
        # mountコマンドが実行されたことを確認
        mock_check_output.assert_called()
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type(self, mock_check_output, disk_utils, mock_logger):
        """ファイルシステムタイプの取得テスト"""
        # blkidコマンドの出力をシミュレート
        mock_check_output.return_value = b'LABEL="test" TYPE="ext4"'
        
        # メソッドを実行
        fs_type = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert fs_type == "ext4"
        
        # blkidコマンドが実行されたことを確認
        mock_check_output.assert_called()
    
    @patch('subprocess.check_output')
    def test_get_filesystem_type_error(self, mock_check_output, disk_utils, mock_logger):
        """ファイルシステムタイプ取得時にエラーが発生した場合のテスト"""
        # blkidコマンドがエラーを返すようにシミュレート
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "blkid")
        
        # メソッドを実行
        fs_type = disk_utils.get_filesystem_type("/dev/sda1")
        
        # 結果を検証
        assert fs_type == ""
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
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
        success, message = disk_utils.mount_disk("/dev/sda1", "/mnt/test")
        
        # 結果を検証
        assert success
        assert "マウント" in message
        
        # マウントコマンドが実行されたことを確認
        mock_check_call.assert_called()
        
        # ログが記録されたことを確認
        mock_logger.info.assert_called()
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.check_call')
    def test_mount_disk_makedirs_error(self, mock_check_call, mock_makedirs, mock_exists, disk_utils, mock_logger):
        """マウントポイント作成時にエラーが発生した場合のテスト"""
        # パスが存在しないと仮定
        mock_exists.return_value = False

        # マウントポイント作成エラーをシミュレート
        mock_makedirs.side_effect = OSError("Permission denied")

        # メソッドを実行
        success, message = disk_utils.mount_disk("/dev/sda1", "/mnt/test")

        # 結果を検証
        assert not success
        assert "マウントポイントの作成に失敗しました" in message

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
        
        # メソッドを実行
        success, message = disk_utils.mount_disk("/dev/sda1", "/mnt/test")
        
        # 結果を検証
        assert not success
        assert "マウントに失敗しました" in message
        
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
        assert "ディスクのフォーマットに成功しました" in message
        
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
        assert "ディスクのフォーマットに成功しました" in message
        
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
        assert "ディスクのフォーマットに成功しました" in message
        
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
        assert "フォーマットに失敗しました" in message
        
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
        assert "マウントポイント" in message
        assert "権限を設定しました" in message
        
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
        assert "権限設定エラー" in message
        
        # エラーログが記録されたことを確認
        mock_logger.error.assert_called()
    
    @patch('os.path.exists')
    @patch('subprocess.check_call')
    @patch('subprocess.Popen')
    def test_open_file_manager_success(self, mock_popen, mock_check_call, mock_exists, disk_utils, mock_logger):
        """ファイルマネージャー起動の成功テスト"""
        # パスが存在すると仮定
        mock_exists.return_value = True

        # whichコマンドの成功をシミュレート
        mock_check_call.return_value = 0

        # ファイルマネージャー起動成功をシミュレート
        mock_popen.return_value = MagicMock()

        # メソッドを実行
        success, message = disk_utils.open_file_manager("/dev/sda1")

        # 結果を検証
        assert success
        assert "ファイルマネージャーを起動しました" in message

        # ログが記録されたことを確認
        mock_logger.info.assert_called()

    @patch('os.path.exists')
    @patch('subprocess.check_call')
    @patch('subprocess.Popen')
    def test_open_file_manager_error(self, mock_popen, mock_check_call, mock_exists, disk_utils, mock_logger):
        """ファイルマネージャー起動時にエラーが発生した場合のテスト"""
        # パスが存在すると仮定
        mock_exists.return_value = True

        # whichコマンドの失敗をシミュレート
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "which")

        # メソッドを実行
        success, message = disk_utils.open_file_manager("/dev/sda1")

        # 結果を検証
        assert not success
        assert "利用可能なファイルマネージャーが見つかりません" in message

        # エラーログが記録されたことを確認
        mock_logger.error.assert_called() 