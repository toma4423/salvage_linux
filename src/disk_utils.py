"""
ディスクユーティリティモジュール
ディスクの操作（マウント、フォーマット、権限付与など）を行うための関数を提供します。
"""

import subprocess
import json
import os
import re
import shlex
from pathlib import Path
from src.config_manager import ConfigManager
from typing import Tuple, List, Optional
from .logger import Logger

class DiskUtils:
    """
    ディスク操作を行うクラス
    """
    def __init__(self, logger: Logger, config_manager=None, test_mode=False):
        """
        初期化
        
        Args:
            logger: ロガーインスタンス
            config_manager (ConfigManager, optional): 設定マネージャーインスタンス
            test_mode (bool): テストモードフラグ
        """
        self.logger = logger
        self.test_mode = test_mode
        # 設定マネージャーが指定されていない場合は新しいインスタンスを作成
        self.config_manager = config_manager if config_manager else ConfigManager()
        
        # 保護されたシステムディレクトリのリスト
        self.protected_dirs = [
            "/", "/boot", "/etc", "/usr", "/var", "/bin", "/sbin", 
            "/lib", "/lib64", "/opt", "/root", "/proc", "/sys", "/dev", "/run"
        ]
        
        # 許可されたファイルシステムタイプのリスト
        self.allowed_fs_types = ["ntfs", "exfat", "ext4", "ext3", "ext2", "fat32", "vfat", "refs"]
    
        self.supported_fs = ['ext4', 'ntfs', 'exfat', 'refs']
    
    def get_unmounted_disks(self) -> dict:
        """
        未マウントのディスクを取得します

        Returns:
            dict: 未マウントディスクの情報を含む辞書
        """
        try:
            # lsblkコマンドで未マウントディスクを取得（JSON形式）
            output = subprocess.check_output(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE"])
            disks_data = json.loads(output.decode())
            return disks_data
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.logger.error(f"未マウントディスクの取得に失敗しました: {str(e)}")
            return {"blockdevices": []}

    def get_mounted_disks(self) -> List[str]:
        """
        マウント済みのディスクの一覧を取得します

        Returns:
            List[str]: マウント済みディスクのパスのリスト
        """
        try:
            output = subprocess.check_output(["mount"], stderr=subprocess.DEVNULL)
            mounts = output.decode('utf-8').strip().split('\n')
            disks = []
            for mount in mounts:
                if mount.startswith('/dev/'):
                    disk = mount.split()[0]
                    disks.append(disk)
            return disks
        except (subprocess.CalledProcessError, UnicodeDecodeError):
            self.logger.error("マウント済みディスクの取得に失敗しました")
            return []
    
    def get_filesystem_type(self, device_path: str) -> str:
        """
        デバイスのファイルシステムタイプを取得します

        Args:
            device_path (str): デバイスパス

        Returns:
            str: ファイルシステムタイプ（取得できない場合は空文字列）
        """
        try:
            output = subprocess.check_output(["blkid", device_path], stderr=subprocess.DEVNULL)
            output_str = output.decode('utf-8')
            
            # TYPE="ext4"のような形式からファイルシステムタイプを抽出
            match = re.search(r'TYPE="([^"]+)"', output_str)
            if match:
                return match.group(1)
            
            return ""
        except (subprocess.CalledProcessError, UnicodeDecodeError):
            self.logger.error(f"ファイルシステムタイプの取得に失敗しました: {device_path}")
            return ""
    
    def _is_valid_path(self, path):
        """
        パスが有効かどうかをチェック
        
        Args:
            path (str): チェックするパス
            
        Returns:
            bool: パスが有効な場合はTrue、そうでない場合はFalse
        """
        # パスが空でないことを確認
        if not path:
            return False
        
        # パスに特殊文字が含まれていないことを確認
        if re.search(r'[;&|`$(){}[\]<>!?*]', path):
            return False
        
        # パスに相対パスが含まれていないことを確認
        if ".." in path or "~" in path:
            return False
        
        # デバイスパスの場合は/dev/で始まることを確認
        if path.startswith("/dev/"):
            # デバイスパスが単純な形式であることを確認
            if not re.match(r'^/dev/[a-zA-Z0-9]+$', path):
                return False
            return True
        
        # マウントポイントの場合は絶対パスであることを確認
        if path.startswith("/"):
            # マウントポイントが単純な形式であることを確認
            if not re.match(r'^/[a-zA-Z0-9/_-]+$', path):
                return False
            return True
        
        return False
    
    def _check_refs_tools_available(self):
        """
        ReFSツールが利用可能かどうかをチェック
        
        Returns:
            bool: ReFSツールが利用可能な場合はTrue、そうでない場合はFalse
        """
        try:
            # mkfs.refsコマンドが存在するかチェック
            subprocess.check_call(["which", "mkfs.refs"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # refsutilコマンドが存在するかチェック
            subprocess.check_call(["which", "refsutil"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _is_system_directory(self, path):
        """
        パスがシステムディレクトリかどうかを確認する
        
        Args:
            path (str): チェックするパス
            
        Returns:
            bool: システムディレクトリの場合はTrue、そうでない場合はFalse
        """
        # 保護されたシステムディレクトリかどうかをチェック
        for protected_dir in self.protected_dirs:
            if path == protected_dir or path.startswith(f"{protected_dir}/"):
                return True
                
        return False
    
    def mount_disk(self, device_path: str, mount_point: str) -> Tuple[bool, str]:
        """
        ディスクをマウントします

        Args:
            device_path (str): デバイスパス
            mount_point (str): マウントポイント

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
        """
        # デバイスパスの検証
        if not device_path.startswith("/dev/"):
            return False, "デバイスパスは/dev/で始まる必要があります"

        # マウントポイントの検証
        if not mount_point.startswith("/"):
            return False, "マウントポイントは/で始まる必要があります"

        try:
            # マウントポイントが存在しない場合は作成
            if not os.path.exists(mount_point):
                try:
                    os.makedirs(mount_point)
                except OSError as e:
                    self.logger.error("マウントポイントの作成に失敗しました")
                    return False, "マウントポイントの作成に失敗しました"

            # ファイルシステムタイプを取得
            fs_type = self.get_filesystem_type(device_path)
            if not fs_type:
                return False, "ファイルシステムタイプを取得できませんでした"

            # マウントコマンドを実行
            subprocess.check_call(["mount", "-t", fs_type, device_path, mount_point])
            self.logger.info(f"{device_path}を{mount_point}にマウントしました")
            return True, "ディスクのマウントに成功しました"
        except OSError as e:
            self.logger.error(f"マウントに失敗しました: {str(e)}")
            return False, f"マウントに失敗しました: {str(e)}"
        except subprocess.CalledProcessError as e:
            self.logger.error(f"マウントに失敗しました: {str(e)}")
            return False, f"マウントに失敗しました: {str(e)}"

    def _validate_path(self, path: str) -> Tuple[bool, str]:
        """
        パスが有効かどうかを検証します

        Args:
            path (str): 検証するパス

        Returns:
            Tuple[bool, str]: (有効かどうか, エラーメッセージ)
        """
        if not path:
            return False, "パスが空です"

        if ".." in path or "//" in path:
            return False, "不正なパスが含まれています"

        if not path.startswith("/dev/"):
            return False, "デバイスパスは/dev/で始まる必要があります"

        return True, ""

    def format_disk(self, device_path: str, filesystem_type: str) -> Tuple[bool, str]:
        """
        ディスクをフォーマットします

        Args:
            device_path (str): デバイスパス
            filesystem_type (str): ファイルシステムタイプ

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
        """
        # デバイスパスの検証
        if not device_path.startswith("/dev/"):
            return False, "デバイスパスは/dev/で始まる必要があります"

        # サポートされているファイルシステムかチェック
        if filesystem_type not in ["ntfs", "exfat", "refs"]:
            self.logger.error(f"サポートされていないファイルシステムです: {filesystem_type}")
            return False, f"サポートされていないファイルシステムです: {filesystem_type}"

        # ReFSの場合、ツールの存在をチェック
        if filesystem_type == "refs":
            if not self._check_refs_tools_available():
                self.logger.error("ReFSツールが見つかりません")
                return False, "ReFSツールが見つかりません"

        try:
            # フォーマットコマンドを実行
            if filesystem_type == "ntfs":
                subprocess.check_call(["mkfs.ntfs", device_path])
            elif filesystem_type == "exfat":
                subprocess.check_call(["mkfs.exfat", device_path])
            elif filesystem_type == "refs":
                subprocess.check_call(["mkfs.refs", device_path])

            self.logger.info(f"{device_path}を{filesystem_type}でフォーマットしました")
            return True, "ディスクのフォーマットに成功しました"
        except subprocess.CalledProcessError as e:
            self.logger.error(f"フォーマットに失敗しました: {str(e)}")
            return False, f"フォーマットに失敗しました: {str(e)}"

    def set_permissions(self, path: str) -> Tuple[bool, str]:
        """
        パスの権限を設定します

        Args:
            path (str): 権限を設定するパス

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
        """
        # パスの検証
        if not path.startswith("/"):
            return False, "パスは/で始まる必要があります"

        try:
            # 権限を設定
            subprocess.check_call(["chmod", "755", path])
            self.logger.info(f"{path}の権限を設定しました")
            return True, "マウントポイントの権限を設定しました"
        except subprocess.CalledProcessError as e:
            self.logger.error(f"権限設定エラー: {str(e)}")
            return False, f"権限設定エラー: {str(e)}"

    def open_file_manager(self, path: str) -> Tuple[bool, str]:
        """
        ファイルマネージャーでパスを開きます

        Args:
            path (str): 開くパス

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
        """
        # パスの検証
        if not path.startswith("/"):
            return False, "パスは/で始まる必要があります"

        # パスの存在確認
        if not os.path.exists(path):
            self.logger.error(f"パスが存在しません: {path}")
            return False, f"パスが存在しません: {path}"

        # 利用可能なファイルマネージャーのリスト
        file_managers = [
            ["xdg-open"],
            ["nautilus"],
            ["nemo"],
            ["dolphin"],
            ["thunar"],
            ["pcmanfm"],
            ["open"]  # macOS用
        ]

        # ファイルマネージャーの存在確認
        available_managers = []
        for manager in file_managers:
            try:
                subprocess.check_call(["which", manager[0]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                available_managers.append(manager)
            except (subprocess.CalledProcessError, OSError):
                continue

        if not available_managers:
            self.logger.error("利用可能なファイルマネージャーが見つかりません")
            return False, "利用可能なファイルマネージャーが見つかりません"

        # ファイルマネージャーで開く
        for manager in available_managers:
            try:
                subprocess.Popen(manager + [path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.logger.info(f"{path}をファイルマネージャーで開きました")
                return True, "ファイルマネージャーを起動しました"
            except (subprocess.CalledProcessError, OSError):
                continue

        self.logger.error("利用可能なファイルマネージャーが見つかりません")
        return False, "利用可能なファイルマネージャーが見つかりません"
    
    def find_disk_by_display_name(self, display_name, unmounted_only=False, mounted_only=False):
        """
        表示名からディスク情報を取得
        
        表示名はリストボックスに表示される形式（"sda1 (8GB, ディスク)"など）であり、
        この関数はその表示名を解析して実際のディスク情報を返します。
        
        Args:
            display_name (str): リストボックスに表示されるディスク名
            unmounted_only (bool): Trueの場合、未マウントディスクのみから検索
            mounted_only (bool): Trueの場合、マウント済みディスクのみから検索
            
        Returns:
            dict or None: 見つかったディスク情報、見つからない場合はNone
        """
        self.logger.debug(f"表示名からディスク検索: {display_name}")
        
        # デバイス名を抽出（"sda1 (8GB, ディスク)" -> "sda1"）
        device_name_match = re.match(r'(\S+)', display_name)
        if not device_name_match:
            self.logger.error(f"無効な表示名: {display_name}")
            return None
        
        device_name = device_name_match.group(1)
        self.logger.debug(f"抽出されたデバイス名: {device_name}")
        
        # 検索するディスクリスト
        disk_list = []
        
        if not mounted_only:
            unmounted_disks = self.get_unmounted_disks()
            disk_list.extend(unmounted_disks)
        
        if not unmounted_only:
            mounted_disks = self.get_mounted_disks()
            disk_list.extend(mounted_disks)
        
        # デバイス名でディスクを検索
        for disk in disk_list:
            # deviceフィールドまたはpathフィールドでデバイス名を比較
            if (os.path.basename(disk.get("device", "")) == device_name or
                os.path.basename(disk.get("path", "")) == device_name):
                self.logger.debug(f"ディスクが見つかりました: {disk}")
                
                # deviceフィールドが存在しない場合はpathフィールドからコピー
                if "device" not in disk and "path" in disk:
                    disk["device"] = disk["path"]
                
                return disk
        
        self.logger.warning(f"ディスクが見つかりません: {device_name}")
        return None 