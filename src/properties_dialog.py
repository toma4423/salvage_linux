"""
properties_dialog.py - ディスクプロパティダイアログモジュール

このモジュールはディスク/パーティションのプロパティ情報を表示するダイアログを提供します。
基本情報、S.M.A.R.T.情報、ファイルシステム情報などを表示し、テキストファイルへの保存機能も備えています。

author: toma4423
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import datetime
import re
from typing import Dict, Any, Optional


class PropertiesDialog:
    """
    ディスクプロパティ情報を表示するダイアログクラス
    
    未マウントディスクのプロパティ情報を表示し、テキストファイルへの保存機能を提供します。
    """
    
    def __init__(self, parent, properties: Dict[str, Any], device_path: str, logger):
        """
        初期化
        
        Args:
            parent: 親ウィンドウ
            properties: ディスクプロパティ情報
            device_path: ディスクデバイスのパス
            logger: ログを記録するLoggerインスタンス
        """
        self.parent = parent
        self.properties = properties
        self.device_path = device_path
        self.logger = logger
        
        # ダイアログの作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"プロパティ - {device_path}")
        self.dialog.geometry("700x500")
        self.dialog.minsize(600, 400)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # ウィンドウを中央に配置
        self._center_window()
        
        # ウィジェットの作成
        self._create_widgets()
        
        # ダイアログが閉じられたときの処理
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_window(self):
        """ウィンドウを画面中央に配置する"""
        # 親ウィンドウの位置とサイズを取得
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # ダイアログのサイズを取得
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # 画面の中央座標を計算
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # ウィンドウ位置を設定
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """ウィジェットを作成する"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ノートブック（タブ）の作成
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本情報タブ
        basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(basic_tab, text="基本情報")
        self._create_basic_info_tab(basic_tab)
        
        # パーティションの場合はS.M.A.R.T.情報とファイルシステム情報を表示
        if self.properties.get("is_partition", False):
            # ファイルシステム情報タブ
            fs_tab = ttk.Frame(self.notebook)
            self.notebook.add(fs_tab, text="ファイルシステム情報")
            self._create_filesystem_info_tab(fs_tab)
            
            # S.M.A.R.T.情報タブ（パーティションの場合は親ディスクのS.M.A.R.T.情報）
            if "parent_smart_info" in self.properties:
                smart_tab = ttk.Frame(self.notebook)
                self.notebook.add(smart_tab, text="S.M.A.R.T.情報")
                self._create_smart_info_tab(smart_tab, use_parent=True)
        
        # ディスク全体の場合はS.M.A.R.T.情報のみ
        else:
            if "smart_info" in self.properties:
                smart_tab = ttk.Frame(self.notebook)
                self.notebook.add(smart_tab, text="S.M.A.R.T.情報")
                self._create_smart_info_tab(smart_tab)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 保存ボタン
        save_button = ttk.Button(button_frame, text="テキストファイルに保存", command=self._save_to_file)
        save_button.pack(side=tk.RIGHT)
        
        # 閉じるボタン
        close_button = ttk.Button(button_frame, text="閉じる", command=self._on_close)
        close_button.pack(side=tk.RIGHT, padx=10)
    
    def _create_basic_info_tab(self, parent):
        """基本情報タブを作成"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # デバイス情報
        device_frame = ttk.LabelFrame(scrollable_frame, text="デバイス情報", padding=10)
        device_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        
        basic_info = self.properties.get("basic_info", {})
        is_partition = self.properties.get("is_partition", False)
        
        # デバイスタイプ
        device_type = "パーティション" if is_partition else "ディスク"
        self._add_label_pair(device_frame, "デバイスタイプ:", device_type)
        
        # 基本情報
        self._add_label_pair(device_frame, "デバイスパス:", self.device_path)
        
        if basic_info.get("name"):
            self._add_label_pair(device_frame, "名前:", basic_info.get("name", ""))
        
        if basic_info.get("size"):
            self._add_label_pair(device_frame, "サイズ:", basic_info.get("size", ""))
        
        if basic_info.get("model"):
            self._add_label_pair(device_frame, "モデル:", basic_info.get("model", ""))
        
        if basic_info.get("serial"):
            self._add_label_pair(device_frame, "シリアル番号:", basic_info.get("serial", ""))
        
        if basic_info.get("type"):
            self._add_label_pair(device_frame, "種類:", basic_info.get("type", ""))
        
        if basic_info.get("fstype"):
            self._add_label_pair(device_frame, "ファイルシステム:", basic_info.get("fstype", ""))
        
        # 取得日時
        timestamp = self.properties.get("timestamp", "不明")
        self._add_label_pair(device_frame, "情報取得日時:", timestamp)
        
        # 健康状態
        health_frame = ttk.LabelFrame(scrollable_frame, text="健康状態", padding=10)
        health_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        
        health_info = None
        if is_partition:
            # パーティションの場合は親ディスクの健康状態
            health_info = self.properties.get("health_status", {})
        else:
            health_info = self.properties.get("health_status", {})
        
        if health_info:
            status = health_info.get("status", "不明")
            score = health_info.get("score", 0)
            
            # 健康状態ステータス
            label_text = "健康状態:"
            value_text = status
            
            label = ttk.Label(health_frame, text=label_text)
            label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            
            # 状態に応じた色で表示
            value = ttk.Label(health_frame, text=value_text)
            if status == "正常":
                value.configure(foreground="green")
            elif status == "異常":
                value.configure(foreground="orange")
            elif status == "故障":
                value.configure(foreground="red")
            value.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
            
            # 健康スコア
            if score > 0:
                self._add_label_pair(health_frame, "健康スコア:", f"{score}/100")
            
            # 検出された問題
            issues = health_info.get("issues", [])
            if issues:
                issues_label = ttk.Label(health_frame, text="検出された問題:")
                issues_label.grid(row=2, column=0, sticky=tk.NW, padx=5, pady=2)
                
                issues_text = tk.Text(health_frame, wrap=tk.WORD, height=5, width=40)
                issues_text.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
                
                for issue in issues:
                    issues_text.insert(tk.END, f"• {issue}\n")
                
                issues_text.configure(state=tk.DISABLED)
    
    def _create_filesystem_info_tab(self, parent):
        """ファイルシステム情報タブを作成"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ファイルシステム情報
        fs_info = self.properties.get("filesystem_info", {})
        if not fs_info:
            ttk.Label(scrollable_frame, text="ファイルシステム情報は利用できません").pack(padx=10, pady=10)
            return
        
        fs_frame = ttk.LabelFrame(scrollable_frame, text="ファイルシステム情報", padding=10)
        fs_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        
        # ファイルシステムタイプ
        fstype = fs_info.get("fstype", "不明")
        self._add_label_pair(fs_frame, "ファイルシステム:", fstype)
        
        # fsckの結果
        fsck_result = fs_info.get("fsck_result", "未実行")
        fsck_status = fs_info.get("fsck_status", "不明")
        
        label = ttk.Label(fs_frame, text="ファイルシステム状態:")
        label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        # 状態に応じた色で表示
        value = ttk.Label(fs_frame, text=f"{fsck_result} ({fsck_status})")
        if fsck_status == "正常":
            value.configure(foreground="green")
        elif fsck_status == "警告":
            value.configure(foreground="orange")
        elif fsck_status in ["エラー", "故障"]:
            value.configure(foreground="red")
        value.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # fsckの詳細
        fsck_details = fs_info.get("fsck_details", "")
        if fsck_details:
            details_label = ttk.Label(fs_frame, text="詳細:")
            details_label.grid(row=2, column=0, sticky=tk.NW, padx=5, pady=2)
            
            details_text = tk.Text(fs_frame, wrap=tk.WORD, height=10, width=50)
            details_text.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
            details_text.insert(tk.END, fsck_details)
            details_text.configure(state=tk.DISABLED)
    
    def _create_smart_info_tab(self, parent, use_parent=False):
        """S.M.A.R.T.情報タブを作成"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # S.M.A.R.T.情報
        if use_parent:
            smart_info = self.properties.get("parent_smart_info", {})
            parent_disk = self.properties.get("parent_disk", "")
            title_text = f"S.M.A.R.T.情報 ({parent_disk})"
        else:
            smart_info = self.properties.get("smart_info", {})
            title_text = "S.M.A.R.T.情報"
        
        if not smart_info:
            ttk.Label(scrollable_frame, text="S.M.A.R.T.情報は利用できません").pack(padx=10, pady=10)
            return
        
        # S.M.A.R.T.のサポート状況
        if not smart_info.get("smart_supported", False):
            message = "このデバイスはS.M.A.R.T.をサポートしていません。"
            ttk.Label(scrollable_frame, text=message).pack(padx=10, pady=10)
            return
        
        # 基本情報フレーム
        basic_frame = ttk.LabelFrame(scrollable_frame, text=title_text, padding=10)
        basic_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        
        # 全体的な健康状態
        overall_health = smart_info.get("overall_health", "不明")
        
        label = ttk.Label(basic_frame, text="全体的な健康状態:")
        label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        # 状態に応じた色で表示
        value = ttk.Label(basic_frame, text=overall_health)
        if overall_health == "PASSED":
            value.configure(foreground="green")
        elif overall_health == "FAILED":
            value.configure(foreground="red")
        value.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 温度
        temperature = smart_info.get("temperature", "N/A")
        self._add_label_pair(basic_frame, "温度:", temperature)
        
        # 稼働時間
        power_on_hours = smart_info.get("power_on_hours", "N/A")
        self._add_label_pair(basic_frame, "稼働時間:", power_on_hours)
        
        # エラーログ
        error_log = smart_info.get("error_log_summary", "N/A")
        self._add_label_pair(basic_frame, "エラーログ:", error_log)
        
        # 重要な属性フレーム
        attr_frame = ttk.LabelFrame(scrollable_frame, text="重要なS.M.A.R.T.属性", padding=10)
        attr_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        
        # テーブルヘッダー
        ttk.Label(attr_frame, text="属性名", font=("", 10, "bold")).grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(attr_frame, text="値", font=("", 10, "bold")).grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        ttk.Label(attr_frame, text="状態", font=("", 10, "bold")).grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        ttk.Separator(attr_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        # 属性値
        attributes = smart_info.get("attributes", {})
        row_idx = 2
        
        # 属性名の日本語表示用マッピング
        attr_names = {
            "Reallocated_Sector_Ct": "代替処理済セクタ数",
            "Current_Pending_Sector": "代替処理保留中のセクタ数",
            "Offline_Uncorrectable": "オフライン訂正不可能セクタ数",
            "UDMA_CRC_Error_Count": "UDMA CRCエラー数"
        }
        
        if not attributes:
            ttk.Label(attr_frame, text="重要な属性情報は利用できません").grid(row=row_idx, column=0, columnspan=3, padx=5, pady=2)
        else:
            for attr_name, attr_value in attributes.items():
                # 属性名（英語表記 + 日本語表記）
                display_name = attr_names.get(attr_name, attr_name)
                if attr_name != display_name:
                    display_name = f"{display_name} ({attr_name})"
                ttk.Label(attr_frame, text=display_name).grid(row=row_idx, column=0, padx=5, pady=2, sticky=tk.W)
                
                # 属性値
                ttk.Label(attr_frame, text=str(attr_value)).grid(row=row_idx, column=1, padx=5, pady=2, sticky=tk.W)
                
                # 状態判定
                if attr_value == 0:
                    status_text = "正常"
                    status_color = "green"
                elif attr_name == "Reallocated_Sector_Ct" and attr_value > 10:
                    status_text = "危険"
                    status_color = "red"
                elif attr_name == "Current_Pending_Sector" and attr_value > 5:
                    status_text = "危険"
                    status_color = "red"
                elif attr_name == "Offline_Uncorrectable" and attr_value > 1:
                    status_text = "危険"
                    status_color = "red"
                elif attr_name == "UDMA_CRC_Error_Count" and attr_value > 5:
                    status_text = "危険"
                    status_color = "red"
                else:
                    status_text = "警告"
                    status_color = "orange"
                
                status_label = ttk.Label(attr_frame, text=status_text)
                status_label.grid(row=row_idx, column=2, padx=5, pady=2, sticky=tk.W)
                status_label.configure(foreground=status_color)
                
                row_idx += 1
        
        # SATA エラー情報
        sata_errors = smart_info.get("sata_errors", {})
        if sata_errors:
            sata_frame = ttk.LabelFrame(scrollable_frame, text="SATAエラー情報", padding=10)
            sata_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
            
            row_idx = 0
            for error_name, error_count in sata_errors.items():
                error_display = error_name.replace("_", " ")
                self._add_label_pair(sata_frame, f"{error_display}:", str(error_count), row=row_idx)
                row_idx += 1
    
    def _add_label_pair(self, parent, label_text, value_text, row=None):
        """ラベルとその値のペアを追加"""
        if row is None:
            # row未指定の場合は、現在の子ウィジェット数から計算
            row = len(parent.winfo_children()) // 2
        
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        
        value = ttk.Label(parent, text=value_text)
        value.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
    
    def _save_to_file(self):
        """プロパティ情報をJSONファイルに保存"""
        try:
            # ファイル名を生成
            device_name = os.path.basename(self.device_path).replace('/', '_')
            now = datetime.datetime.now()
            default_filename = f"disk_properties_{device_name}_{now.strftime('%Y%m%d_%H%M%S')}.json"
            
            # ファイル保存ダイアログを表示
            file_path = filedialog.asksaveasfilename(
                parent=self.dialog,
                title="プロパティ情報の保存",
                initialdir=os.path.expanduser("~"),
                initialfile=default_filename,
                filetypes=[("JSONファイル", "*.json"), ("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
                defaultextension=".json"
            )
            
            if not file_path:
                return
            
            # プロパティ情報をJSONに変換
            json_string = json.dumps(self.properties, ensure_ascii=False, indent=4)
            
            # BOM付きUTF-8でファイルに保存
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(json_string)
            
            self.logger.info(f"プロパティ情報を {file_path} に保存しました")
            messagebox.showinfo("保存完了", f"プロパティ情報を保存しました。\n{file_path}")
            
        except Exception as e:
            self.logger.error(f"プロパティ情報の保存中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"保存中にエラーが発生しました。\n{str(e)}")
    
    def _on_close(self):
        """ダイアログを閉じる"""
        self.dialog.destroy() 