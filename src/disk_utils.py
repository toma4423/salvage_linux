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
from typing import Tuple, List, Optional, Dict, Any, TypedDict, Union, cast
from .logger import Logger
import sys

class DiskInfo(TypedDict, total=False):
    """ディスク情報を表す型"""
    name: str  # デバイス名
    path: str  # デバイスパス
    device: str  # デバイスパス（pathと同じ値）
    size: str  # サイズ
    type: str  # デバイスタイプ
    fstype: str  # ファイルシステムタイプ
    mountpoint: Optional[str]  # マウントポイント（オプション）
    model: Optional[str]  # モデル名（オプション）
    serial: Optional[str]  # シリアル番号（オプション）
    uuid: Optional[str]  # UUID（オプション）
    label: Optional[str]  # ラベル（オプション）
    partuuid: Optional[str]  # パーティションUUID（オプション）
    partlabel: Optional[str]  # パーティションラベル（オプション）

class UnmountedDisksResponse(TypedDict, total=False):
    """未マウントディスクのレスポンスを表す型"""
    blockdevices: List[DiskInfo]  # 未マウントディスクのリスト

def validate_disk_info(data: Dict[str, Any]) -> bool:
    """
    DiskInfoの構造を検証します。

    Args:
        data: 検証するデータ

    Returns:
        bool: 検証結果
    """
    return is_disk_info(data)

def validate_unmounted_disks_response(data: Dict[str, Any]) -> bool:
    """
    UnmountedDisksResponseの構造を検証します。

    Args:
        data: 検証するデータ

    Returns:
        bool: 検証結果
    """
    return is_unmounted_disks_response(data)

def is_disk_info(data: Dict[str, Any]) -> bool:
    """
    データがDiskInfoの要件を満たしているかチェックします。

    Args:
        data (Dict[str, Any]): チェックするデータ

    Returns:
        bool: データがDiskInfoの要件を満たしている場合True
    """
    required_fields = {"name", "path", "device", "size", "type", "fstype"}
    return all(field in data for field in required_fields)

def is_unmounted_disks_response(data: Dict[str, Any]) -> bool:
    """
    データがUnmountedDisksResponseの要件を満たしているかチェックします。

    Args:
        data (Dict[str, Any]): チェックするデータ

    Returns:
        bool: データがUnmountedDisksResponseの要件を満たしている場合True
    """
    if not isinstance(data, dict) or "blockdevices" not in data:
        return False
    if not isinstance(data["blockdevices"], list):
        return False
    return all(is_disk_info(disk) for disk in data["blockdevices"])

def create_disk_info(data: Dict[str, Any]) -> DiskInfo:
    """
    DiskInfoオブジェクトを作成します。

    Args:
        data (Dict[str, Any]): ディスク情報のデータ

    Returns:
        DiskInfo: 作成されたDiskInfoオブジェクト
    """
    device_path = f"/dev/{data['name']}"
    return cast(DiskInfo, {
        "name": data["name"],
        "path": device_path,
        "device": device_path,
        "size": data["size"],
        "type": data["type"],
        "fstype": data.get("fstype", ""),
        "mountpoint": data.get("mountpoint"),
        "model": data.get("model"),
        "serial": data.get("serial"),
        "uuid": data.get("uuid"),
        "label": data.get("label"),
        "partuuid": data.get("partuuid"),
        "partlabel": data.get("partlabel")
    })

def create_unmounted_disks_response(disks: List[DiskInfo]) -> Dict[str, List[DiskInfo]]:
    """
    UnmountedDisksResponseオブジェクトを作成します。

    Args:
        disks (List[DiskInfo]): ディスク情報のリスト

    Returns:
        Dict[str, List[DiskInfo]]: 作成されたUnmountedDisksResponseオブジェクト
    """
    return {"blockdevices": disks}

class DiskUtils:
    """
    ディスク操作を行うクラス
    """
    def __init__(self, logger: Logger, test_mode: bool = False):
        """
        初期化

        Args:
            logger (Logger): ロガー
            test_mode (bool): テストモードかどうか
        """
        self.logger = logger
        self.test_mode = test_mode
        self.allowed_fs_types = ["ntfs", "exfat", "refs"]

    def get_unmounted_disks(self) -> Dict[str, List[DiskInfo]]:
        """
        未マウントのディスク情報を取得します。

        Returns:
            Dict[str, List[DiskInfo]]: 未マウントディスクの情報

        Raises:
            RuntimeError: ディスク情報の取得に失敗した場合
        """
        try:
            self.logger.info("未マウントディスクの取得を開始します")
            result = subprocess.check_output(["lsblk", "-J", "-o", "NAME,PATH,SIZE,TYPE,MOUNTPOINT,MODEL,FSTYPE,SERIAL,UUID,LABEL,PARTUUID,PARTLABEL"]).decode()
            data = json.loads(result)
            disks: List[DiskInfo] = []
            for blockdev in data.get("blockdevices", []):
                if not blockdev.get("mountpoint"):
                    disk_info = create_disk_info(blockdev)
                    if is_disk_info(disk_info):
                        disks.append(disk_info)
                        self.logger.info(f"未マウントディスクを検出: {disk_info['name']}")
            response = {"blockdevices": disks}
            if is_unmounted_disks_response(response):
                self.logger.info(f"未マウントディスクの取得が完了しました: {len(disks)}個のディスクが見つかりました")
                return response
            raise RuntimeError("Invalid response format")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"未マウントディスクの取得に失敗しました: {str(e)}")
            raise RuntimeError(f"未マウントディスクの取得に失敗しました: {str(e)}")
        except Exception as e:
            self.logger.error(f"未マウントディスクの取得に失敗しました: {str(e)}")
            raise RuntimeError(f"未マウントディスクの取得に失敗しました: {str(e)}")
    
    def get_mounted_disks(self) -> List[DiskInfo]:
        """
        マウント済みのディスク情報を取得します。

        Returns:
            List[DiskInfo]: マウント済みディスクの情報リスト

        Raises:
            RuntimeError: ディスク情報の取得に失敗した場合
        """
        try:
            self.logger.info("マウント済みディスクの取得を開始します")
            result = subprocess.check_output(["lsblk", "-J", "-o", "NAME,PATH,SIZE,TYPE,MOUNTPOINT,MODEL,FSTYPE,SERIAL,UUID,LABEL,PARTUUID,PARTLABEL"]).decode()
            data = json.loads(result)
            disks: List[DiskInfo] = []
            for blockdev in data.get("blockdevices", []):
                if blockdev.get("mountpoint"):
                    disk_info = create_disk_info(blockdev)
                    if is_disk_info(disk_info):
                        disks.append(disk_info)
                        self.logger.info(f"マウント済みディスクを検出: {disk_info['name']}")
                # 子デバイスもチェック
                for child in blockdev.get("children", []):
                    if child.get("mountpoint"):
                        child_info = create_disk_info(child)
                        if is_disk_info(child_info):
                            disks.append(child_info)
                            self.logger.info(f"マウント済みディスクを検出: {child_info['name']}")
            self.logger.info(f"マウント済みディスクの取得が完了しました: {len(disks)}個のディスクが見つかりました")
            return disks
        except subprocess.CalledProcessError as e:
            self.logger.error(f"マウント済みディスクの取得に失敗しました: {str(e)}")
            raise RuntimeError(f"マウント済みディスクの取得に失敗しました: {str(e)}")
        except Exception as e:
            self.logger.error(f"マウント済みディスクの取得に失敗しました: {str(e)}")
            raise RuntimeError(f"マウント済みディスクの取得に失敗しました: {str(e)}")
    
    def get_filesystem_type(self, device_path: str) -> str:
        """指定されたデバイスのファイルシステムタイプを取得する
        
        Args:
            device_path (str): デバイスパス
            
        Returns:
            str: ファイルシステムタイプ
            
        Raises:
            RuntimeError: ファイルシステムタイプの取得に失敗した場合
        """
        try:
            # デバイスパスの検証
            if not self._validate_device_path(device_path):
                error_msg = f"ファイルシステムタイプの取得に失敗しました: 不正なデバイスパスです"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # blkidコマンドでファイルシステムタイプを取得
            result = subprocess.check_output(
                ["blkid", "-o", "export", device_path],
                stderr=subprocess.STDOUT
            ).decode('utf-8')
            
            # 結果からTYPE=の行を抽出
            for line in result.splitlines():
                if line.startswith("TYPE="):
                    fs_type = line.split("=")[1]
                    self.logger.info(f"ファイルシステムタイプを取得しました: {fs_type}")
                    return fs_type
            
            # TYPE=が見つからない場合
            error_msg = f"ファイルシステムタイプの取得に失敗しました: ファイルシステムタイプが見つかりません"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"ファイルシステムタイプの取得に失敗しました: blkidコマンドの実行に失敗しました"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"ファイルシステムタイプの取得に失敗しました: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def check_refs_tools_available(self) -> bool:
        """
        ReFSフォーマットツールが利用可能かチェックします。

        Returns:
            bool: ツールが利用可能な場合はTrue
        """
        try:
            subprocess.check_call(["which", "mkfs.refs"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logger.info("ReFSツールが利用可能です")
            return True
        except subprocess.CalledProcessError:
            self.logger.error("ReFSツールが利用できません")
            return False

    def _validate_device_path(self, path: str) -> bool:
        """
        デバイスパスが安全か検証します。

        Args:
            path (str): 検証するデバイスパス

        Returns:
            bool: 検証結果
        """
        if not path:
            return False

        # コマンドインジェクションの可能性をチェック
        if ";" in path or "&&" in path or "|" in path or "`" in path or "$(" in path:
            return False

        # パストラバーサルの可能性をチェック
        if ".." in path or "//" in path:
            return False

        # テストモードの場合は全てのパスを許可
        if self.test_mode:
            return True

        # 通常モードでは/dev/で始まるパスのみ許可
        if not path.startswith("/dev/"):
            return False

        # デバイスパスの形式をチェック
        if not re.match(r'^/dev/[a-zA-Z0-9]+$', path):
            return False

        return True

    def format_disk(self, device_path: str, fs_type: str) -> Tuple[bool, str]:
        """
        ディスクをフォーマットします。

        Args:
            device_path (str): デバイスパス
            fs_type (str): ファイルシステムタイプ

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
                - bool: 成功した場合はTrue
                - str: 処理結果のメッセージ

        Raises:
            RuntimeError: フォーマットに失敗した場合
        """
        if not self._validate_device_path(device_path):
            error_msg = f"不正なデバイスパスです: {device_path}"
            self.logger.error(error_msg)
            return False, error_msg

        if fs_type not in self.allowed_fs_types:
            error_msg = f"サポートされていないファイルシステムタイプです: {fs_type}"
            self.logger.error(error_msg)
            return False, error_msg

        try:
            if fs_type == "ntfs":
                subprocess.check_call(["mkfs.ntfs", device_path])
            elif fs_type == "exfat":
                subprocess.check_call(["mkfs.exfat", device_path])
            elif fs_type == "refs":
                if not self.check_refs_tools_available():
                    error_msg = "ReFSフォーマットツールが見つかりません"
                    self.logger.error(error_msg)
                    return False, error_msg
                subprocess.check_call(["mkfs.refs", device_path])
            success_msg = f"ディスクをフォーマットしました: {device_path}を{fs_type}でフォーマットしました"
            self.logger.info(success_msg)
            return True, success_msg
        except subprocess.CalledProcessError as e:
            error_msg = f"ディスクのフォーマットに失敗しました: {device_path} - {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"ディスクのフォーマットに失敗しました: {device_path} - {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def set_permissions(self, device_path: str) -> Tuple[bool, str]:
        """
        デバイスの権限を設定します。

        Args:
            device_path: デバイスパス

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)

        Raises:
            RuntimeError: 権限設定に失敗した場合
        """
        if not self._validate_device_path(device_path):
            error_msg = f"不正なパスです: {device_path}"
            self.logger.error(error_msg)
            return False, error_msg

        try:
            subprocess.check_call(["chmod", "666", device_path])
            success_msg = f"権限の設定: {device_path}の権限を設定しました"
            self.logger.info(success_msg)
            return True, success_msg
        except subprocess.CalledProcessError as e:
            error_msg = f"権限の設定に失敗しました: {device_path} - {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"権限の設定に失敗しました: {device_path} - {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def open_file_manager(self, path: str) -> Tuple[bool, str]:
        """
        ファイルマネージャーを開きます。

        Args:
            path (str): 開くパス

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
                - bool: 成功した場合はTrue
                - str: 処理結果のメッセージ

        Raises:
            RuntimeError: ファイルマネージャーの起動に失敗した場合
        """
        if not os.path.exists(path):
            error_msg = f"ファイルマネージャーの起動に失敗しました: パスが存在しません: {path}"
            self.logger.error(error_msg)
            return False, error_msg

        try:
            self.logger.info(f"ファイルマネージャーを開きます: {path}")

            # テストモードの場合は実際のコマンドを実行しない
            if self.test_mode:
                success_msg = f"ファイルマネージャーで{path}を開きました"
                self.logger.info(success_msg)
                return True, success_msg

            # macOSの場合はopenコマンド、それ以外はxdg-openを使用
            command = ["open" if sys.platform == "darwin" else "xdg-open", path]
            process = subprocess.Popen(command)
            
            # プロセスの終了を待つ
            process.wait(timeout=5)
            
            if process.returncode != 0:
                error_msg = f"ファイルマネージャーの起動に失敗しました: {path}"
                self.logger.error(error_msg)
                return False, error_msg
                
            success_msg = f"ファイルマネージャーで{path}を開きました"
            self.logger.info(success_msg)
            return True, success_msg
            
        except subprocess.TimeoutExpired:
            process.kill()
            error_msg = f"ファイルマネージャーの起動がタイムアウトしました: {path}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"ファイルマネージャーの起動に失敗しました: {path} - {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def find_disk_by_display_name(self, display_name: str, unmounted_only: bool = False, mounted_only: bool = False) -> Optional[DiskInfo]:
        """
        表示名からディスク情報を取得
        
        表示名はリストボックスに表示される形式（"sda1 (8GB, ディスク)"など）であり、
        この関数はその表示名を解析して実際のディスク情報を返します。
        
        Args:
            display_name (str): リストボックスに表示されるディスク名
            unmounted_only (bool): Trueの場合、未マウントディスクのみから検索
            mounted_only (bool): Trueの場合、マウント済みディスクのみから検索
            
        Returns:
            Optional[DiskInfo]: 見つかったディスク情報、見つからない場合はNone
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
        disk_list: List[DiskInfo] = []
        
        if not mounted_only:
            unmounted_disks_data = self.get_unmounted_disks()
            # 辞書形式のデータからディスク情報を抽出
            for device in unmounted_disks_data.get("blockdevices", []):
                # ディスク自体の処理
                if device.get("mountpoint") is None and device.get("type") == "disk":
                    disk_info: DiskInfo = {
                        "name": device.get("name"),
                        "path": f"/dev/{device.get('name')}",
                        "size": device.get("size"),
                        "type": device.get("type"),
                        "mountpoint": None,
                        "model": device.get("model"),
                    }
                    disk_list.append(disk_info)
                
                # パーティションの処理
                for partition in device.get("children", []):
                    if partition.get("mountpoint") is None and partition.get("type") == "part":
                        partition_info: DiskInfo = {
                            "name": partition.get("name"),
                            "path": f"/dev/{partition.get('name')}",
                            "size": partition.get("size"),
                            "type": partition.get("type"),
                            "mountpoint": None,
                            "model": partition.get("model"),
                        }
                        disk_list.append(partition_info)
        
        if not unmounted_only:
            mounted_disks = self.get_mounted_disks()
            disk_list.extend(mounted_disks)
        
        # デバイス名でディスクを検索
        for disk in disk_list:
            # deviceフィールドまたはpathフィールドでデバイス名を比較
            if (os.path.basename(disk.get("path", "")) == device_name):
                self.logger.debug(f"ディスクが見つかりました: {disk}")
                return disk
        
        self.logger.debug(f"ディスクが見つかりませんでした: {display_name}")
        return None 