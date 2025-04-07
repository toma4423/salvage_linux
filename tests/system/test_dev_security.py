"""
開発環境用のセキュリティテスト
macOS環境で実行可能なテストのみを含みます。
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from src.disk_utils import DiskUtils, DiskInfo, UnmountedDisksResponse, validate_unmounted_disks_response, validate_disk_info, is_unmounted_disks_response
from src.logger import Logger
from typing import List, Dict, Any
import unittest
import subprocess

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
class TestDevSecurity:
    """開発環境用のセキュリティテストクラス"""

    def test_format_disk_invalid_path(self, logger_and_disk_utils):
        """不正なパスでのフォーマットが拒否されることを確認"""
        logger, disk_utils = logger_and_disk_utils
        
        # コマンドインジェクション試行
        success, message = disk_utils.format_disk("/dev/sda1; rm -rf /", "ntfs")
        assert not success
        assert "不正なデバイスパスです" in message

        # パストラバーサル試行
        success, message = disk_utils.format_disk("/dev/../etc/passwd", "ntfs")
        assert not success
        assert "不正なデバイスパスです" in message

        # システムディレクトリへのアクセス試行
        success, message = disk_utils.format_disk("/etc/passwd", "ntfs")
        assert not success
        assert "不正なデバイスパスです" in message

    def test_format_disk_invalid_fs_type(self, logger_and_disk_utils):
        """不正なファイルシステムタイプでのフォーマットが拒否されることを確認"""
        logger, disk_utils = logger_and_disk_utils
        
        # サポートされていないファイルシステムタイプ
        success, message = disk_utils.format_disk("/dev/sda1", "ext4")
        assert not success
        assert "サポートされていないファイルシステムタイプです" in message

        # 空のファイルシステムタイプ
        success, message = disk_utils.format_disk("/dev/sda1", "")
        assert not success
        assert "サポートされていないファイルシステムタイプです" in message

        # 不正な文字を含むファイルシステムタイプ
        success, message = disk_utils.format_disk("/dev/sda1", "ntfs; rm -rf /")
        assert not success
        assert "サポートされていないファイルシステムタイプです" in message

    def test_get_filesystem_type_invalid_path(self, logger_and_disk_utils):
        """不正なパスでのファイルシステムタイプ取得が拒否されることを確認"""
        logger, disk_utils = logger_and_disk_utils
        
        # コマンドインジェクション試行
        with pytest.raises(RuntimeError) as e:
            disk_utils.get_filesystem_type("/dev/sda1; rm -rf /")
        assert "不正なデバイスパスです" in str(e.value)

        # パストラバーサル試行
        with pytest.raises(RuntimeError) as e:
            disk_utils.get_filesystem_type("/dev/../etc/passwd")
        assert "不正なデバイスパスです" in str(e.value)

        # システムディレクトリへのアクセス試行
        with pytest.raises(RuntimeError) as e:
            disk_utils.get_filesystem_type("/etc/passwd")
        assert "不正なデバイスパスです" in str(e.value)

@pytest.mark.system
class TestDevTypeHints:
    """開発環境用の型ヒントのテスト"""
    
    @patch('subprocess.check_output')
    @patch('json.loads')
    def test_get_unmounted_disks_return_type(self, mock_json_loads, mock_check_output, logger_and_disk_utils):
        """get_unmounted_disksの戻り値の型テスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # モックの設定
        mock_check_output.return_value = b'{"blockdevices": []}'
        mock_json_loads.return_value = {"blockdevices": []}
        
        # メソッド呼び出し
        result = disk_utils.get_unmounted_disks()
        
        # 戻り値の型チェック
        assert isinstance(result, dict), "戻り値が辞書型ではありません"
        assert "blockdevices" in result, "戻り値に'blockdevices'キーがありません"
        assert isinstance(result["blockdevices"], list), "'blockdevices'の値がリスト型ではありません"
        
        # UnmountedDisksResponse型に準拠していることを確認
        assert is_unmounted_disks_response(result), "戻り値がUnmountedDisksResponse型に準拠していません"
    
    @patch('subprocess.check_output')
    @patch('json.loads')
    def test_get_mounted_disks_return_type(self, mock_json_loads, mock_check_output, logger_and_disk_utils):
        """get_mounted_disksの戻り値の型テスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # モックの設定
        mock_check_output.return_value = b'{"blockdevices": []}'
        mock_json_loads.return_value = {"blockdevices": []}
        
        # メソッド呼び出し
        result = disk_utils.get_mounted_disks()
        
        # 戻り値の型チェック
        assert isinstance(result, list), "戻り値がリスト型ではありません"
        
        # List[DiskInfo]型に準拠していることを確認
        assert isinstance(result, List), "戻り値がList型に準拠していません"
    
    @patch('subprocess.check_output')
    @patch('json.loads')
    def test_disk_info_structure(self, mock_json_loads, mock_check_output, logger_and_disk_utils):
        """DiskInfo構造のテスト"""
        logger, disk_utils = logger_and_disk_utils
        
        # モックの設定
        mock_disk_data = {
            "name": "sda1",
            "size": "8G",
            "type": "part",
            "mountpoint": "/mnt/usb",
            "fstype": "ext4",
            "model": "Samsung SSD",
            "serial": "123456789",
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "label": "USB",
            "partuuid": "123e4567-e89b-12d3-a456-426614174001",
            "partlabel": "USB-PART"
        }
        
        mock_check_output.return_value = b'{"blockdevices": [{"children": [{"name": "sda1", "size": "8G", "type": "part", "mountpoint": "/mnt/usb", "fstype": "ext4", "model": "Samsung SSD", "serial": "123456789", "uuid": "123e4567-e89b-12d3-a456-426614174000", "label": "USB", "partuuid": "123e4567-e89b-12d3-a456-426614174001", "partlabel": "USB-PART"}]}]}'
        mock_json_loads.return_value = {"blockdevices": [{"children": [mock_disk_data]}]}
        
        # メソッド呼び出し
        result = disk_utils.get_mounted_disks()
        
        # 結果が空でないことを確認
        assert len(result) > 0, "マウント済みディスクが返されませんでした"
        
        # 最初のディスク情報を取得
        disk_info = result[0]
        
        # DiskInfo型に準拠していることを確認
        assert isinstance(disk_info, dict), "ディスク情報が辞書型ではありません"
        
        # 必須フィールドの存在を確認
        assert "name" in disk_info, "nameフィールドがありません"
        assert "path" in disk_info, "pathフィールドがありません"
        assert "device" in disk_info, "deviceフィールドがありません"
        assert "size" in disk_info, "sizeフィールドがありません"
        assert "type" in disk_info, "typeフィールドがありません"
        assert "mountpoint" in disk_info, "mountpointフィールドがありません"
        
        # フィールドの型を確認
        assert isinstance(disk_info["name"], str), "nameフィールドが文字列型ではありません"
        assert isinstance(disk_info["path"], str), "pathフィールドが文字列型ではありません"
        assert isinstance(disk_info["device"], str), "deviceフィールドが文字列型ではありません"
        assert isinstance(disk_info["size"], str), "sizeフィールドが文字列型ではありません"
        assert isinstance(disk_info["type"], str), "typeフィールドが文字列型ではありません"
        assert isinstance(disk_info["mountpoint"], str), "mountpointフィールドが文字列型ではありません"
        
        # オプショナルフィールドの型を確認（存在する場合）
        if "fstype" in disk_info:
            assert isinstance(disk_info["fstype"], str), "fstypeフィールドが文字列型ではありません"
        if "model" in disk_info:
            assert isinstance(disk_info["model"], str) or disk_info["model"] is None, "modelフィールドが文字列型またはNoneではありません"
        if "serial" in disk_info:
            assert isinstance(disk_info["serial"], str) or disk_info["serial"] is None, "serialフィールドが文字列型またはNoneではありません"
        if "uuid" in disk_info:
            assert isinstance(disk_info["uuid"], str) or disk_info["uuid"] is None, "uuidフィールドが文字列型またはNoneではありません"
        if "label" in disk_info:
            assert isinstance(disk_info["label"], str) or disk_info["label"] is None, "labelフィールドが文字列型またはNoneではありません"
        if "partuuid" in disk_info:
            assert isinstance(disk_info["partuuid"], str) or disk_info["partuuid"] is None, "partuuidフィールドが文字列型またはNoneではありません"
        if "partlabel" in disk_info:
            assert isinstance(disk_info["partlabel"], str) or disk_info["partlabel"] is None, "partlabelフィールドが文字列型またはNoneではありません" 