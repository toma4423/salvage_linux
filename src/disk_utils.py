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
from .config_manager import ConfigManager

class DiskUtils:
    """
    ディスク操作を行うクラス
    """
    def __init__(self, logger, config_manager=None):
        """
        初期化
        
        Args:
            logger: ロガーインスタンス
            config_manager (ConfigManager, optional): 設定マネージャーインスタンス
        """
        self.logger = logger
        # 設定マネージャーが指定されていない場合は新しいインスタンスを作成
        self.config_manager = config_manager if config_manager else ConfigManager()
        
        # 保護されたシステムディレクトリのリスト
        self.protected_dirs = [
            "/", "/boot", "/etc", "/usr", "/var", "/bin", "/sbin", 
            "/lib", "/lib64", "/opt", "/root", "/proc", "/sys", "/dev", "/run"
        ]
        
        # 許可されたファイルシステムタイプのリスト
        self.allowed_fs_types = ["ntfs", "exfat", "ext4", "ext3", "ext2", "fat32", "vfat", "refs"]
    
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
        パスが有効かどうかをチェック
        
        Args:
            path (str): チェックするパス
            
        Returns:
            bool: パスが有効な場合はTrue、そうでない場合はFalse
        """
        # パスが空でないことを確認
        if not path:
            return False
        
        # デバイスパスの場合は/dev/で始まることを確認
        if path.startswith("/dev/"):
            # パスに特殊文字が含まれていないことを確認
            if re.search(r'[;&|`$]', path):
                return False
            return True
        
        # マウントポイントの場合は絶対パスであることを確認
        if path.startswith("/"):
            # パスに特殊文字が含まれていないことを確認
            if re.search(r'[;&|`$]', path):
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
            
            # システムディレクトリへのマウントを防止
            if self._is_system_directory(mount_point):
                error_msg = f"システムディレクトリへのマウントはできません: {mount_point}"
                self.logger.error(error_msg)
                return False, error_msg, ""
            
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
            fs_type (str): フォーマットするファイルシステムタイプ（"ntfs"、"exfat"、"refs"など）
            
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
        if self._is_system_directory(device_path):
            error_msg = f"システムディレクトリはフォーマットできません: {device_path}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # ReFSツールのチェック
        if fs_type.lower() == "refs" and not self._check_refs_tools_available():
            error_msg = "ReFSツールが見つかりません。必要なツールをインストールしてください。"
            self.logger.error(error_msg)
            return False, error_msg
        
        # コマンドを構築
        if fs_type.lower() == "ntfs":
            format_cmd = ["mkfs.ntfs", "-f", device_path]
        elif fs_type.lower() == "exfat":
            format_cmd = ["mkfs.exfat", device_path]
        elif fs_type.lower() == "refs":
            format_cmd = ["mkfs.refs", device_path]
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
        except FileNotFoundError as e:
            error_msg = f"ReFSツールが見つかりません: {str(e)}"
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
        指定したマウントポイントをファイルマネージャーで開く
        環境に応じて適切なファイルマネージャーを検出して使用します
        
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
        
        # 設定から指定されたファイルマネージャーを取得
        file_manager_setting = self.config_manager.get_file_manager()
        
        # ファイルマネージャーリストの設定
        if isinstance(file_manager_setting, list):
            # 'auto'の場合は設定に保存されているリストを使用
            file_managers = file_manager_setting
        else:
            # 特定のファイルマネージャーが指定されている場合
            file_managers = [file_manager_setting]
        
        self.logger.info(f"{mount_point} をファイルマネージャーで開いています...")
        
        # 有効なファイルマネージャーを順番に試す
        for manager in file_managers:
            try:
                # スペースが含まれる場合はシェルコマンドとして実行
                if " " in manager:
                    subprocess.Popen(f"{manager} {mount_point}", shell=True)
                    self.logger.info(f"ファイルマネージャー {manager} でマウントポイントを開きました")
                    return True, ""
                else:
                    # 事前にファイルマネージャーが利用可能かチェック
                    try:
                        subprocess.check_call(["which", manager], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        # ファイルマネージャーが見つかったら実行
                        subprocess.Popen([manager, mount_point])
                        self.logger.info(f"ファイルマネージャー {manager} でマウントポイントを開きました")
                        return True, ""
                    except subprocess.CalledProcessError:
                        # このファイルマネージャーは利用できないので次を試す
                        continue
            except Exception as e:
                # このファイルマネージャーでは失敗したので次を試す
                self.logger.warning(f"ファイルマネージャー {manager} での起動に失敗しました: {str(e)}")
                continue
        
        # すべてのファイルマネージャーが失敗した場合
        error_msg = "利用可能なファイルマネージャーが見つかりません"
        self.logger.error(error_msg)
        return False, error_msg

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