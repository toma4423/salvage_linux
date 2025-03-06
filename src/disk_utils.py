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

class DiskUtils:
    """
    ディスク操作を行うクラス
    """
    def __init__(self, logger):
        """
        初期化
        
        Args:
            logger: ロガーオブジェクト
        """
        self.logger = logger
        
        # 保護されたシステムディレクトリのリスト
        self.protected_dirs = [
            "/", "/boot", "/etc", "/usr", "/var", "/bin", "/sbin", 
            "/lib", "/lib64", "/opt", "/root", "/proc", "/sys", "/dev", "/run"
        ]
        
        # 許可されたファイルシステムタイプのリスト
        self.allowed_fs_types = ["ntfs", "exfat", "ext4", "ext3", "ext2", "fat32", "vfat"]
    
    def get_unmounted_disks(self):
        """
        未マウントのディスクとパーティションのリストを取得
        
        Returns:
            list: 未マウントディスクの情報リスト
        """
        self.logger.info("未マウントディスクのリストを取得中...")
        
        try:
            # lsblkコマンドを実行して全ディスク情報をJSON形式で取得
            output = subprocess.check_output(
                ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT"],
                universal_newlines=True
            )
            
            disks_data = json.loads(output)
            
            # 未マウントのディスクとパーティションをフィルタリング
            unmounted_disks = []
            
            for device in disks_data.get("blockdevices", []):
                # ディスク自体の処理
                if device.get("mountpoint") is None and device.get("type") == "disk":
                    disk_info = {
                        "name": device.get("name"),
                        "path": f"/dev/{device.get('name')}",
                        "size": device.get("size"),
                        "type": device.get("type"),
                        "fstype": device.get("fstype", "")
                    }
                    unmounted_disks.append(disk_info)
                
                # パーティションの処理
                for partition in device.get("children", []):
                    if partition.get("mountpoint") is None and partition.get("type") == "part":
                        partition_info = {
                            "name": partition.get("name"),
                            "path": f"/dev/{partition.get('name')}",
                            "size": partition.get("size"),
                            "type": partition.get("type"),
                            "fstype": partition.get("fstype", "")
                        }
                        unmounted_disks.append(partition_info)
            
            self.logger.info(f"未マウントディスク {len(unmounted_disks)} 件を検出")
            return unmounted_disks
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ディスク情報の取得に失敗しました: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"ディスク情報のJSONデコードに失敗しました: {str(e)}")
            return []
    
    def get_mounted_disks(self):
        """
        マウント済みのディスクとパーティションのリストを取得
        
        Returns:
            list: マウント済みディスクの情報リスト
        """
        self.logger.info("マウント済みディスクのリストを取得中...")
        
        try:
            # lsblkコマンドを実行して全ディスク情報をJSON形式で取得
            output = subprocess.check_output(
                ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT"],
                universal_newlines=True
            )
            
            disks_data = json.loads(output)
            
            # マウント済みのディスクとパーティションをフィルタリング
            mounted_disks = []
            
            for device in disks_data.get("blockdevices", []):
                # ディスク自体の処理
                if device.get("mountpoint") is not None and device.get("type") == "disk":
                    disk_info = {
                        "name": device.get("name"),
                        "path": f"/dev/{device.get('name')}",
                        "size": device.get("size"),
                        "type": device.get("type"),
                        "fstype": device.get("fstype", ""),
                        "mountpoint": device.get("mountpoint")
                    }
                    mounted_disks.append(disk_info)
                
                # パーティションの処理
                for partition in device.get("children", []):
                    if partition.get("mountpoint") is not None and partition.get("type") == "part":
                        # ルートファイルシステムなど、システムディスクは除外
                        if partition.get("mountpoint") not in ["/", "/boot", "/home"]:
                            partition_info = {
                                "name": partition.get("name"),
                                "path": f"/dev/{partition.get('name')}",
                                "size": partition.get("size"),
                                "type": partition.get("type"),
                                "fstype": partition.get("fstype", ""),
                                "mountpoint": partition.get("mountpoint")
                            }
                            mounted_disks.append(partition_info)
            
            self.logger.info(f"マウント済みディスク {len(mounted_disks)} 件を検出")
            return mounted_disks
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ディスク情報の取得に失敗しました: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"ディスク情報のJSONデコードに失敗しました: {str(e)}")
            return []
    
    def get_filesystem_type(self, device_path):
        """
        デバイスのファイルシステムタイプを取得
        
        Args:
            device_path (str): デバイスパス（例: /dev/sda1）
            
        Returns:
            str: ファイルシステムタイプ（不明な場合は空文字列）
        """
        try:
            output = subprocess.check_output(
                ["blkid", "-o", "value", "-s", "TYPE", device_path],
                universal_newlines=True
            )
            return output.strip()
        except subprocess.CalledProcessError:
            return ""
    
    def _is_valid_path(self, path):
        """
        パスが有効であるかを検証する（セキュリティチェック）
        
        Args:
            path (str): 検証するパス
            
        Returns:
            bool: パスが有効な場合はTrue、そうでない場合はFalse
        """
        # パスが空でないことを確認
        if not path or not isinstance(path, str):
            return False
            
        # 相対パスやパストラバーサルを含むパスを拒否
        if '..' in path or not path.startswith('/'):
            return False
            
        # コマンドインジェクションを防止するための特殊文字チェック
        if re.search(r'[;&|`$]', path):
            return False
            
        return True
    
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
    
    def mount_disk(self, device_path, mount_point=None):
        """
        ディスクをマウント
        
        Args:
            device_path (str): デバイスパス（例: /dev/sda1）
            mount_point (str, optional): マウントポイント（指定しない場合は自動生成）
            
        Returns:
            tuple: (成功したかどうか, マウントポイント, エラーメッセージ)
        """
        # パスのバリデーション
        if not self._is_valid_path(device_path):
            self.logger.error(f"無効なデバイスパス: {device_path}")
            return False, "無効なデバイスパスが指定されました。", ""
        
        try:
            # マウントポイントが指定されていない場合は自動生成
            if mount_point is None:
                device_name = os.path.basename(device_path)
                mount_point = f"/mnt/{device_name}"
            
            # マウントポイントのバリデーション
            if not self._is_valid_path(mount_point):
                self.logger.error(f"無効なマウントポイント: {mount_point}")
                return False, "無効なマウントポイントが指定されました。", ""
            
            # マウントポイントディレクトリが存在しない場合は作成
            if not os.path.exists(mount_point):
                try:
                    os.makedirs(mount_point)
                except OSError as e:
                    error_msg = f"マウントポイントの作成に失敗しました: {str(e)}"
                    self.logger.error(error_msg)
                    return False, error_msg, ""
            
            # ファイルシステムタイプを取得
            fs_type = self.get_filesystem_type(device_path)
            
            # マウントコマンドを構築
            mount_cmd = ["mount"]
            
            if fs_type == "ntfs":
                mount_cmd.extend(["-t", "ntfs-3g"])
            elif fs_type == "exfat":
                mount_cmd.extend(["-t", "exfat"])
            
            mount_cmd.extend([device_path, mount_point])
            
            # マウントコマンドを実行
            self.logger.info(f"{device_path} を {mount_point} にマウント中...")
            subprocess.check_call(mount_cmd)
            
            self.logger.info(f"{device_path} を {mount_point} にマウント成功")
            return True, mount_point, ""
            
        except subprocess.CalledProcessError as e:
            error_msg = f"{device_path} のマウントに失敗しました: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, ""
    
    def format_disk(self, device_path, fs_type="exfat"):
        """
        ディスクをフォーマット
        
        Args:
            device_path (str): デバイスパス（例: /dev/sda1）
            fs_type (str): フォーマットするファイルシステムタイプ（"ntfs" または "exfat"）
            
        Returns:
            tuple: (成功したかどうか, エラーメッセージ)
        """
        # パスのバリデーション
        if not self._is_valid_path(device_path):
            error_msg = f"無効なデバイスパス: {device_path}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # ファイルシステムタイプのバリデーション
        if fs_type not in self.allowed_fs_types:
            error_msg = f"サポートされていないファイルシステムタイプ: {fs_type}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # システムディレクトリをフォーマットから保護
        if os.path.exists(device_path) and self._is_system_directory(device_path):
            error_msg = f"システムディレクトリはフォーマットできません: {device_path}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # コマンドを構築
        if fs_type.lower() == "ntfs":
            format_cmd = ["mkfs.ntfs", "-f", device_path]
        elif fs_type.lower() == "exfat":
            format_cmd = ["mkfs.exfat", device_path]
        else:
            error_msg = f"サポートされていないファイルシステムタイプ: {fs_type}"
            self.logger.error(error_msg)
            return False, error_msg
        
        try:
            self.logger.info(f"{device_path} を {fs_type} でフォーマット中...")
            subprocess.check_call(format_cmd)
            self.logger.info(f"{device_path} のフォーマット成功")
            return True, ""
        except subprocess.CalledProcessError as e:
            error_msg = f"{device_path} のフォーマットに失敗しました: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def set_permissions(self, mount_point):
        """
        マウントポイント以下のファイルとディレクトリに最大権限を付与
        
        Args:
            mount_point (str): マウントポイント
            
        Returns:
            tuple: (成功したかどうか, エラーメッセージ)
        """
        # パスのバリデーション
        if not self._is_valid_path(mount_point):
            error_msg = f"無効なマウントポイント: {mount_point}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # システムディレクトリへの権限付与から保護
        if self._is_system_directory(mount_point):
            error_msg = f"システムディレクトリへの権限付与はできません: {mount_point}"
            self.logger.error(error_msg)
            return False, error_msg
        
        try:
            self.logger.info(f"{mount_point} に権限を付与中...")
            subprocess.check_call(["chmod", "-R", "777", mount_point])
            self.logger.info(f"{mount_point} への権限付与成功")
            return True, ""
        except subprocess.CalledProcessError as e:
            error_msg = f"{mount_point} への権限付与に失敗しました: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def open_file_manager(self, mount_point):
        """
        指定したマウントポイントをファイルマネージャー (PCManFM) で開く
        
        Args:
            mount_point (str): マウントポイント
            
        Returns:
            tuple: (成功したかどうか, エラーメッセージ)
        """
        # パスのバリデーション
        if not self._is_valid_path(mount_point):
            error_msg = f"無効なマウントポイント: {mount_point}"
            self.logger.error(error_msg)
            return False, error_msg
        
        try:
            self.logger.info(f"{mount_point} をファイルマネージャーで開いています...")
            subprocess.Popen(["pcmanfm", mount_point])
            return True, ""
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_msg = f"ファイルマネージャーの起動に失敗しました: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg 