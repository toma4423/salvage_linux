"""
パフォーマンステスト
"""

import pytest
import time
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
@pytest.mark.slow
class TestPerformance:
    """パフォーマンステスト"""
    
    @patch('subprocess.check_output')
    def test_disk_listing_performance(self, mock_check_output, logger_and_disk_utils):
        """ディスク一覧取得のパフォーマンステスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # 大量のディスクとパーティションをシミュレート
        large_disk_list = {"blockdevices": []}
        for i in range(100):  # 100ディスク
            disk = {
                "name": f"sd{chr(97 + i)}",  # sda, sdb, ...
                "size": "100G",
                "type": "disk",
                "fstype": None,
                "mountpoint": None,
                "children": []
            }
            
            # 各ディスクに5パーティションを追加
            for j in range(1, 6):  # 5パーティション
                partition = {
                    "name": f"sd{chr(97 + i)}{j}",  # sda1, sda2, ...
                    "size": "20G",
                    "type": "part",
                    "fstype": "ntfs",
                    "mountpoint": None if i % 2 == 0 else f"/mnt/sd{chr(97 + i)}{j}"  # 半分はマウント済み
                }
                disk["children"].append(partition)
            
            large_disk_list["blockdevices"].append(disk)
        
        mock_check_output.return_value = str(large_disk_list).replace("'", "\"")
        
        # 未マウントディスクの取得時間を計測
        start_time = time.time()
        unmounted_disks = disk_utils.get_unmounted_disks()
        unmounted_time = time.time() - start_time
        
        # マウント済みディスクの取得時間を計測
        start_time = time.time()
        mounted_disks = disk_utils.get_mounted_disks()
        mounted_time = time.time() - start_time
        
        # 結果を検証
        print(f"\n未マウントディスク取得時間: {unmounted_time:.4f}秒")
        print(f"マウント済みディスク取得時間: {mounted_time:.4f}秒")
        
        # 許容時間内で処理が完了することを確認
        assert unmounted_time < 1.0  # 1秒以内
        assert mounted_time < 1.0  # 1秒以内
    
    @patch('subprocess.check_call')
    def test_format_disk_performance(self, mock_check_call, logger_and_disk_utils):
        """ディスクフォーマットのパフォーマンステスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # フォーマットコマンドの実行をシミュレート（実際には実行しない）
        mock_check_call.side_effect = lambda cmd: time.sleep(0.5)  # 0.5秒かかると仮定
        
        # NTFSフォーマットの時間を計測
        start_time = time.time()
        success, _ = disk_utils.format_disk("/dev/sda1", "ntfs")
        ntfs_format_time = time.time() - start_time
        
        # exFATフォーマットの時間を計測
        start_time = time.time()
        success, _ = disk_utils.format_disk("/dev/sda1", "exfat")
        exfat_format_time = time.time() - start_time
        
        # 結果を検証
        print(f"\nNTFSフォーマット時間: {ntfs_format_time:.4f}秒")
        print(f"exFATフォーマット時間: {exfat_format_time:.4f}秒")
        
        # 許容時間内で処理が完了することを確認
        assert ntfs_format_time < 1.0  # 1秒以内
        assert exfat_format_time < 1.0  # 1秒以内
    
    @patch('subprocess.check_call')
    def test_set_permissions_performance(self, mock_check_call, logger_and_disk_utils):
        """権限付与のパフォーマンステスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # 権限付与コマンドの実行をシミュレート（実際には実行しない）
        # 大きなディスクの場合は時間がかかると仮定
        mock_check_call.side_effect = lambda cmd: time.sleep(1.0)  # 1秒かかると仮定
        
        # 権限付与の時間を計測
        start_time = time.time()
        success, _ = disk_utils.set_permissions("/mnt/sda1")
        permission_time = time.time() - start_time
        
        # 結果を検証
        print(f"\n権限付与時間: {permission_time:.4f}秒")
        
        # 許容時間内で処理が完了することを確認
        assert permission_time < 2.0  # 2秒以内
    
    @patch('subprocess.Popen')
    def test_open_file_manager_performance(self, mock_popen, logger_and_disk_utils):
        """ファイルマネージャー起動のパフォーマンステスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # ファイルマネージャー起動をシミュレート
        mock_popen.return_value = MagicMock()
        
        # ファイルマネージャー起動の時間を計測
        start_time = time.time()
        success, _ = disk_utils.open_file_manager("/mnt/sda1")
        open_time = time.time() - start_time
        
        # 結果を検証
        print(f"\nファイルマネージャー起動時間: {open_time:.4f}秒")
        
        # 許容時間内で処理が完了することを確認
        assert open_time < 0.5  # 0.5秒以内 