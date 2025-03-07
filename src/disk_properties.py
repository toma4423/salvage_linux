"""
disk_properties.py - ディスクプロパティ情報取得モジュール

このモジュールはディスク/パーティションの詳細なプロパティ情報を取得します。
S.M.A.R.T.情報の取得、ファイルシステムの状態チェック、健康状態の判定などの機能を提供します。

author: toma4423
"""

import subprocess
import json
import os
import re
import datetime
import shlex
from pathlib import Path


class DiskPropertiesAnalyzer:
    """
    ディスクプロパティ情報を解析するクラス
    
    ディスクのS.M.A.R.T.情報や健康状態、ファイルシステムの状態を分析して取得します。
    """
    
    def __init__(self, logger):
        """
        初期化
        
        Args:
            logger: ログを記録するLoggerインスタンス
        """
        self.logger = logger
        
        # S.M.A.R.T.属性閾値定義
        self.smart_thresholds = {
            "Reallocated_Sector_Ct": {"normal": 0, "warning": 10, "critical": 10},
            "Current_Pending_Sector": {"normal": 0, "warning": 5, "critical": 5},
            "Offline_Uncorrectable": {"normal": 0, "warning": 1, "critical": 1},
            "UDMA_CRC_Error_Count": {"normal": 0, "warning": 5, "critical": 5}
        }

    def get_disk_properties(self, device_path):
        """
        指定されたディスクのプロパティ情報を取得します
        
        Args:
            device_path (str): ディスクデバイスのパス（例: /dev/sda）
            
        Returns:
            dict: ディスクのプロパティ情報を含む辞書
        """
        self.logger.info(f"{device_path} のプロパティ情報を取得しています")
        
        try:
            # ディスクの基本情報を取得
            basic_info = self._get_basic_disk_info(device_path)
            
            # パーティションかディスク全体かを判断
            is_partition = self._is_partition(device_path)
            
            properties = {
                "device_path": device_path,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "basic_info": basic_info,
                "is_partition": is_partition
            }
            
            # ディスク全体の場合は、S.M.A.R.T.情報を取得
            if not is_partition:
                smart_info = self._get_smart_info(device_path)
                health_status = self._determine_health_status(smart_info)
                properties["smart_info"] = smart_info
                properties["health_status"] = health_status
            
            # パーティションの場合は、ファイルシステム情報とディスク健康状態を取得
            else:
                # ディスク本体のパスを取得（例: /dev/sda1 → /dev/sda）
                parent_disk = self._get_parent_disk(device_path)
                fs_info = self._get_filesystem_info(device_path)
                
                # 親ディスクのS.M.A.R.T.情報を取得
                if parent_disk:
                    smart_info = self._get_smart_info(parent_disk)
                    health_status = self._determine_health_status(smart_info)
                    properties["parent_disk"] = parent_disk
                    properties["parent_smart_info"] = smart_info
                    properties["health_status"] = health_status
                
                properties["filesystem_info"] = fs_info
            
            return properties
            
        except Exception as e:
            self.logger.error(f"プロパティ情報の取得中にエラーが発生しました: {str(e)}")
            return {"error": str(e)}
    
    def _get_basic_disk_info(self, device_path):
        """
        ディスクの基本情報を取得します
        
        Args:
            device_path (str): ディスクデバイスのパス
            
        Returns:
            dict: ディスクの基本情報
        """
        try:
            result = {}
            
            # lsblkコマンドで基本情報を取得
            cmd = ["lsblk", "-o", "NAME,SIZE,MODEL,SERIAL,TYPE,FSTYPE", "-J", device_path]
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if process.returncode == 0:
                lsblk_data = json.loads(process.stdout)
                if "blockdevices" in lsblk_data and len(lsblk_data["blockdevices"]) > 0:
                    device_info = lsblk_data["blockdevices"][0]
                    result = {
                        "name": device_info.get("name", ""),
                        "size": device_info.get("size", ""),
                        "model": device_info.get("model", ""),
                        "serial": device_info.get("serial", ""),
                        "type": device_info.get("type", ""),
                        "fstype": device_info.get("fstype", "")
                    }
            
            return result
            
        except Exception as e:
            self.logger.error(f"基本情報の取得中にエラーが発生しました: {str(e)}")
            return {}
    
    def _is_partition(self, device_path):
        """
        デバイスがパーティションかディスク全体かを判断します
        
        Args:
            device_path (str): ディスクデバイスのパス
            
        Returns:
            bool: パーティションであればTrue、ディスク全体であればFalse
        """
        # パス名からパーティションかを判断（数字が含まれていればパーティション）
        device_name = os.path.basename(device_path)
        return any(char.isdigit() for char in device_name)
    
    def _get_parent_disk(self, partition_path):
        """
        パーティションの親ディスクのパスを取得します
        
        Args:
            partition_path (str): パーティションのパス（例: /dev/sda1）
            
        Returns:
            str: 親ディスクのパス（例: /dev/sda）
        """
        try:
            # パーティション名から数字を取り除いて親ディスク名を推測
            device_name = os.path.basename(partition_path)
            # 最後の連続する数字を削除
            parent_name = re.sub(r'\d+$', '', device_name)
            return os.path.join(os.path.dirname(partition_path), parent_name)
        except Exception as e:
            self.logger.error(f"親ディスクの取得中にエラーが発生しました: {str(e)}")
            return None
    
    def _get_smart_info(self, device_path):
        """
        S.M.A.R.T.情報を取得します
        
        Args:
            device_path (str): ディスクデバイスのパス
            
        Returns:
            dict: S.M.A.R.T.情報
        """
        try:
            result = {
                "overall_health": "不明",
                "attributes": {},
                "temperature": "N/A",
                "power_on_hours": "N/A",
                "error_log_summary": "利用できません",
                "smart_supported": False
            }
            
            # smartctl -a コマンドで詳細情報を取得
            cmd = ["smartctl", "-a", device_path]
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = process.stdout
            
            # 全体的な健康状態を取得
            if "SMART overall-health self-assessment test result" in output:
                match = re.search(r"SMART overall-health self-assessment test result: (\w+)", output)
                if match:
                    result["overall_health"] = match.group(1)
                    result["smart_supported"] = True
            
            # サポート状況を確認
            if not result["smart_supported"] and "Device does not support SMART" in output:
                result["overall_health"] = "サポートされていません"
                return result
            
            # 重要な属性を取得
            for attr_name in self.smart_thresholds:
                pattern = r"{}.*?(\d+)".format(attr_name.replace("_", " "))
                match = re.search(pattern, output)
                if match:
                    result["attributes"][attr_name] = int(match.group(1))
            
            # 温度情報を取得
            temp_match = re.search(r"Temperature.*?(\d+)", output)
            if temp_match:
                result["temperature"] = f"{temp_match.group(1)}°C"
            
            # 稼働時間を取得
            hours_match = re.search(r"Power_On_Hours.*?(\d+)", output)
            if hours_match:
                hours = int(hours_match.group(1))
                days = hours // 24
                result["power_on_hours"] = f"{hours}時間 ({days}日)"
            
            # エラーログの要約を取得
            cmd = ["smartctl", "-l", "error", device_path]
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            error_output = process.stdout
            
            if "No Errors Logged" in error_output:
                result["error_log_summary"] = "エラーなし"
            elif "SMART Error Log" in error_output:
                error_count = error_output.count("Error ")
                recent_error = re.search(r"Error \d+ occurred at.*?(\d{4}-\d{2}-\d{2})", error_output)
                recent_date = recent_error.group(1) if recent_error else "不明"
                result["error_log_summary"] = f"{error_count}個のエラー, 最新: {recent_date}"
            
            # 詳細なS.M.A.R.T.属性を取得（smartctl -x）
            cmd = ["smartctl", "-x", device_path]
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            detailed_output = process.stdout
            
            # SATA PHYイベントカウンタなど
            sata_errors = {}
            phy_event_patterns = [
                (r"CRC Error Count.*?(\d+)", "CRC_Error_Count"),
                (r"Illegal State.*?(\d+)", "Illegal_State"),
                (r"R_ERR response.*?(\d+)", "R_ERR_Response")
            ]
            
            for pattern, key in phy_event_patterns:
                match = re.search(pattern, detailed_output)
                if match:
                    sata_errors[key] = int(match.group(1))
            
            if sata_errors:
                result["sata_errors"] = sata_errors
            
            return result
            
        except Exception as e:
            self.logger.error(f"S.M.A.R.T.情報の取得中にエラーが発生しました: {str(e)}")
            return {
                "overall_health": "エラー",
                "error": str(e),
                "smart_supported": False
            }
    
    def _get_filesystem_info(self, device_path):
        """
        ファイルシステムの情報を取得します
        
        Args:
            device_path (str): パーティションのパス
            
        Returns:
            dict: ファイルシステム情報
        """
        try:
            result = {
                "fstype": "不明",
                "fsck_result": "未実行",
                "fsck_status": "不明",
                "fsck_details": ""
            }
            
            # ファイルシステムタイプを取得
            cmd = ["lsblk", "-o", "FSTYPE", "-n", device_path]
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            fstype = process.stdout.strip()
            result["fstype"] = fstype if fstype else "未フォーマット"
            
            # ファイルシステムタイプがある場合のみfsckを実行
            if result["fstype"] and result["fstype"] != "未フォーマット":
                # fsck -n コマンドで状態チェック（読み取り専用モード）
                cmd = ["fsck", "-n", device_path]
                
                # ファイルシステムに応じてコマンドをカスタマイズ
                if result["fstype"] == "ntfs":
                    cmd = ["ntfsfix", "--no-action", device_path]
                elif result["fstype"] == "exfat":
                    # exFATにはfatresize -iなどを使用
                    cmd = ["fatresize", "-i", device_path]
                
                # コマンド実行（標準エラー出力も取得）
                process = subprocess.run(cmd, capture_output=True, text=True, check=False)
                output = process.stdout + process.stderr
                
                # 出力結果から状態を判断
                if process.returncode == 0:
                    if "clean" in output.lower() or "no errors" in output.lower():
                        result["fsck_status"] = "正常"
                        result["fsck_result"] = "エラーなし"
                    else:
                        result["fsck_status"] = "警告"
                        result["fsck_result"] = "軽微なエラーあり"
                else:
                    if "could not" in output.lower() or "failed" in output.lower():
                        result["fsck_status"] = "エラー"
                        result["fsck_result"] = "実行失敗"
                    else:
                        result["fsck_status"] = "故障"
                        result["fsck_result"] = "重大なエラーあり"
                
                # 詳細情報は最大1000文字まで
                result["fsck_details"] = output[:1000] if len(output) > 1000 else output
            
            return result
            
        except Exception as e:
            self.logger.error(f"ファイルシステム情報の取得中にエラーが発生しました: {str(e)}")
            return {
                "fstype": "不明",
                "fsck_result": "エラー",
                "fsck_status": "エラー",
                "fsck_details": str(e)
            }
    
    def _determine_health_status(self, smart_info):
        """
        S.M.A.R.T.情報から健康状態を判定します
        
        Args:
            smart_info (dict): S.M.A.R.T.情報
            
        Returns:
            dict: 健康状態の情報
        """
        result = {
            "status": "不明",
            "score": 0,
            "issues": []
        }
        
        # S.M.A.R.T.がサポートされていない場合
        if not smart_info.get("smart_supported", False):
            result["status"] = "不明"
            result["issues"].append("S.M.A.R.T.がサポートされていません")
            return result
        
        # 全体的な健康状態
        overall_health = smart_info.get("overall_health", "")
        
        # スコア計算の初期値（100点満点）
        score = 100
        issues = []
        
        # 全体的な健康状態による評価
        if overall_health == "PASSED":
            # 基本的にはPASSED
            pass
        elif overall_health == "FAILED":
            score -= 50
            issues.append("S.M.A.R.T.全体テスト: 失敗")
        else:
            score -= 10
            issues.append(f"S.M.A.R.T.全体テスト: {overall_health}")
        
        # 各重要属性の評価
        attributes = smart_info.get("attributes", {})
        for attr_name, attr_value in attributes.items():
            thresholds = self.smart_thresholds.get(attr_name, {})
            normal = thresholds.get("normal", 0)
            warning = thresholds.get("warning", 0)
            critical = thresholds.get("critical", 0)
            
            # 属性値に基づく減点とメッセージ
            if attr_value > critical:
                score -= 30
                issues.append(f"{attr_name}: {attr_value} (致命的)")
            elif attr_value > normal:
                score -= 10
                issues.append(f"{attr_name}: {attr_value} (警告)")
        
        # エラーログの評価
        error_log = smart_info.get("error_log_summary", "")
        if error_log != "エラーなし" and error_log != "利用できません":
            score -= 15
            issues.append(f"エラーログ: {error_log}")
        
        # SATA エラーの評価
        sata_errors = smart_info.get("sata_errors", {})
        for error_name, error_count in sata_errors.items():
            if error_count > 0:
                score -= 5
                issues.append(f"SATAエラー {error_name}: {error_count}")
        
        # スコアに基づいてステータスを決定
        if score >= 90:
            result["status"] = "正常"
        elif score >= 70:
            result["status"] = "異常"
        else:
            result["status"] = "故障"
        
        result["score"] = score
        result["issues"] = issues
        
        return result
    
    def save_properties_to_file(self, properties, device_path):
        """
        プロパティ情報をJSONファイルに保存します（ダミー実装 - 実際の実装はGUIから行う）
        
        Args:
            properties (dict): プロパティ情報
            device_path (str): デバイスパス
            
        Returns:
            bool: 保存に成功したかどうか
        """
        try:
            device_name = os.path.basename(device_path).replace('/', '_')
            now = datetime.datetime.now()
            filename = f"disk_properties_{device_name}_{now.strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8-sig') as f:
                json.dump(properties, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"プロパティ情報を {filename} に保存しました")
            return True
            
        except Exception as e:
            self.logger.error(f"プロパティ情報の保存中にエラーが発生しました: {str(e)}")
            return False 