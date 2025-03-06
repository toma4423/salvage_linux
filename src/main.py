#!/usr/bin/env python3
"""
USBブートLinux GUIディスクユーティリティ
ディスクのマウント、フォーマット、および権限付与をGUIで簡便に行うためのツール
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# インポート文を相対パスに修正
from src.logger import Logger
from src.disk_utils import DiskUtils
from src.version import get_version_info, APP_NAME, __version__

class DiskUtilityApp:
    """
    ディスクユーティリティのメインアプリケーションクラス
    """
    def __init__(self, root, test_mode=False):
        """
        初期化
        
        Args:
            root: Tkinterのルートウィンドウ
            test_mode: テストモードフラグ。Trueの場合は権限チェックをスキップ
        """
        self.root = root
        self.test_mode = test_mode
        
        # タイトルにバージョン情報を追加
        self.root.title(get_version_info())
        
        # 最小ウィンドウサイズを設定（レイアウト崩れを防止）
        self.root.minsize(800, 600)
        self.root.geometry("900x600")
        
        # スーパーユーザー権限の確認（テストモードでない場合）
        if not test_mode and os.geteuid() != 0:
            messagebox.showerror(
                "権限エラー", 
                "このアプリケーションはスーパーユーザー権限で実行する必要があります。\n"
                "`sudo`コマンドを使って再実行してください。"
            )
            sys.exit(1)
        
        # ロガーとディスクユーティリティのインスタンス作成
        self.logger = Logger()
        self.disk_utils = DiskUtils(self.logger)
        
        # 選択されたディスクの保存用変数
        self.selected_unmounted_disk = None
        self.selected_mounted_disk = None
        
        # GUIの構築
        self._build_gui()
        
        # 起動時にディスクリストを更新
        self._refresh_disk_lists()
    
    def _build_gui(self):
        """
        GUIの構築 - ウィンドウサイズ変更に対応したレスポンシブなレイアウト
        """
        # ルートウィンドウの行・列の設定
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)  # ステータスバー用
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # メインフレームの行・列の設定
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)  # 下部ボタン用
        
        # 左右のパネル分割
        left_panel = ttk.LabelFrame(main_frame, text="未マウントディスク", padding="10")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(0, weight=1)  # リストボックス
        left_panel.grid_rowconfigure(1, weight=0)  # 情報フレーム
        left_panel.grid_rowconfigure(2, weight=0)  # ボタンフレーム
        left_panel.grid_rowconfigure(3, weight=0)  # フォーマット選択フレーム
        
        right_panel = ttk.LabelFrame(main_frame, text="マウント済みディスク", padding="10")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=1)  # リストボックス
        right_panel.grid_rowconfigure(1, weight=0)  # 情報フレーム
        right_panel.grid_rowconfigure(2, weight=0)  # ボタンフレーム
        
        # 未マウントディスクリスト（左パネル）
        self.unmounted_disk_listbox = tk.Listbox(left_panel, selectmode=tk.SINGLE, height=15)
        self.unmounted_disk_listbox.grid(row=0, column=0, sticky="nsew")
        self.unmounted_disk_listbox.bind('<<ListboxSelect>>', self._on_unmounted_disk_select)
        
        # スクロールバーの追加
        unmounted_scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=self.unmounted_disk_listbox.yview)
        unmounted_scrollbar.grid(row=0, column=1, sticky="ns")
        self.unmounted_disk_listbox.configure(yscrollcommand=unmounted_scrollbar.set)
        
        # 未マウントディスク情報表示エリア
        unmounted_info_frame = ttk.LabelFrame(left_panel, text="ディスク情報", padding="5")
        unmounted_info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        unmounted_info_frame.grid_columnconfigure(0, weight=1)
        
        self.unmounted_disk_info = tk.Text(unmounted_info_frame, height=5, wrap=tk.WORD)
        self.unmounted_disk_info.grid(row=0, column=0, sticky="nsew")
        self.unmounted_disk_info.config(state=tk.DISABLED)
        
        # 未マウントディスク操作ボタン
        unmounted_button_frame = ttk.Frame(left_panel, padding="5")
        unmounted_button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        unmounted_button_frame.grid_columnconfigure(0, weight=1)
        unmounted_button_frame.grid_columnconfigure(1, weight=1)
        
        self.mount_button = ttk.Button(
            unmounted_button_frame, 
            text="マウント", 
            command=self._mount_selected_disk,
            state=tk.DISABLED
        )
        self.mount_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.format_button = ttk.Button(
            unmounted_button_frame, 
            text="フォーマット", 
            command=self._format_selected_disk,
            state=tk.DISABLED
        )
        self.format_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        # フォーマット形式選択
        format_select_frame = ttk.Frame(left_panel, padding="5")
        format_select_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        ttk.Label(format_select_frame, text="フォーマット形式:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # テストモードの場合はStringVarではなく通常の文字列を使用
        if self.test_mode:
            self.fs_type_var = "exfat"  # デフォルト値
        else:
            self.fs_type_var = tk.StringVar()
            self.fs_type_var.set("exfat")  # デフォルト値
        
        ntfs_radio = ttk.Radiobutton(
            format_select_frame, 
            text="NTFS", 
            variable=self.fs_type_var if not self.test_mode else None, 
            value="ntfs"
        )
        ntfs_radio.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        exfat_radio = ttk.Radiobutton(
            format_select_frame, 
            text="exFAT", 
            variable=self.fs_type_var if not self.test_mode else None, 
            value="exfat"
        )
        exfat_radio.grid(row=0, column=2, sticky="w")
        
        # マウント済みディスクリスト（右パネル）
        self.mounted_disk_listbox = tk.Listbox(right_panel, selectmode=tk.SINGLE, height=15)
        self.mounted_disk_listbox.grid(row=0, column=0, sticky="nsew")
        self.mounted_disk_listbox.bind('<<ListboxSelect>>', self._on_mounted_disk_select)
        
        # スクロールバーの追加
        mounted_scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=self.mounted_disk_listbox.yview)
        mounted_scrollbar.grid(row=0, column=1, sticky="ns")
        self.mounted_disk_listbox.configure(yscrollcommand=mounted_scrollbar.set)
        
        # マウント済みディスク情報表示エリア
        mounted_info_frame = ttk.LabelFrame(right_panel, text="ディスク情報", padding="5")
        mounted_info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        mounted_info_frame.grid_columnconfigure(0, weight=1)
        
        self.mounted_disk_info = tk.Text(mounted_info_frame, height=5, wrap=tk.WORD)
        self.mounted_disk_info.grid(row=0, column=0, sticky="nsew")
        self.mounted_disk_info.config(state=tk.DISABLED)
        
        # マウント済みディスク操作ボタン
        mounted_button_frame = ttk.Frame(right_panel, padding="5")
        mounted_button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        mounted_button_frame.grid_columnconfigure(0, weight=1)
        mounted_button_frame.grid_columnconfigure(1, weight=1)
        
        self.open_button = ttk.Button(
            mounted_button_frame, 
            text="ファイルマネージャーで開く", 
            command=self._open_selected_disk,
            state=tk.DISABLED
        )
        self.open_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.permission_button = ttk.Button(
            mounted_button_frame, 
            text="権限付与", 
            command=self._set_permissions_to_selected_disk,
            state=tk.DISABLED
        )
        self.permission_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        # 共通操作ボタン（下部）
        bottom_frame = ttk.Frame(main_frame, padding="10")
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        bottom_frame.grid_columnconfigure(1, weight=1)  # 右寄せにするため
        
        refresh_button = ttk.Button(
            bottom_frame, 
            text="更新", 
            command=self._refresh_disk_lists
        )
        refresh_button.grid(row=0, column=1, sticky="e")
        
        # ステータスバー
        if self.test_mode:
            self.status_var = "準備完了"
        else:
            self.status_var = tk.StringVar()
            self.status_var.set("準備完了")
        
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var if not self.test_mode else None, 
            text="準備完了" if self.test_mode else None,
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2)
        )
        status_bar.grid(row=1, column=0, sticky="ew")
    
    def _refresh_disk_lists(self):
        """
        ディスクリストを更新
        """
        if self.test_mode:
            self.status_var = "ディスク情報を更新中..."
        else:
            self.status_var.set("ディスク情報を更新中...")
        
        # 未マウントディスクリストのクリア
        self.unmounted_disk_listbox.delete(0, tk.END)
        
        # 未マウントディスクの取得と表示
        unmounted_disks = self.disk_utils.get_unmounted_disks()
        self.unmounted_disks = unmounted_disks  # 参照用に保存
        
        for disk in unmounted_disks:
            disk_name = disk["name"]
            disk_size = disk["size"]
            disk_type = "ディスク" if disk["type"] == "disk" else "パーティション"
            
            self.unmounted_disk_listbox.insert(
                tk.END, 
                f"{disk_name} ({disk_size}, {disk_type})"
            )
        
        # マウント済みディスクリストのクリア
        self.mounted_disk_listbox.delete(0, tk.END)
        
        # マウント済みディスクの取得と表示
        mounted_disks = self.disk_utils.get_mounted_disks()
        self.mounted_disks = mounted_disks  # 参照用に保存
        
        for disk in mounted_disks:
            disk_name = disk["name"]
            disk_size = disk["size"]
            mount_point = disk["mountpoint"]
            
            self.mounted_disk_listbox.insert(
                tk.END, 
                f"{disk_name} ({disk_size}, {mount_point})"
            )
        
        # 情報表示エリアをクリア
        self._clear_disk_info()
        
        # ボタンの無効化
        self._disable_buttons()
        
        if self.test_mode:
            self.status_var = "ディスク情報の更新が完了しました"
        else:
            self.status_var.set("ディスク情報の更新が完了しました")
    
    def _on_unmounted_disk_select(self, event):
        """
        未マウントディスクが選択された時の処理
        """
        try:
            # 選択されたインデックスを取得
            selection = self.unmounted_disk_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            
            # 選択されたディスク情報を表示
            disk = self.unmounted_disks[index]
            
            # テキスト領域を有効化して内容をクリア
            self.unmounted_disk_info.config(state=tk.NORMAL)
            self.unmounted_disk_info.delete(1.0, tk.END)
            
            # 情報を表示
            self.unmounted_disk_info.insert(tk.END, f"名前: {disk['name']}\n")
            self.unmounted_disk_info.insert(tk.END, f"パス: {disk['path']}\n")
            self.unmounted_disk_info.insert(tk.END, f"サイズ: {disk['size']}\n")
            self.unmounted_disk_info.insert(tk.END, f"タイプ: {disk['type']}\n")
            
            fs_type = disk['fstype'] if disk['fstype'] else "未フォーマット"
            self.unmounted_disk_info.insert(tk.END, f"ファイルシステム: {fs_type}\n")
            
            # テキスト領域を読み取り専用に戻す
            self.unmounted_disk_info.config(state=tk.DISABLED)
            
            # マウントとフォーマットボタンを有効化
            self.mount_button.config(state=tk.NORMAL)
            self.format_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.logger.error(f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
    
    def _on_mounted_disk_select(self, event):
        """
        マウント済みディスクが選択された時の処理
        """
        try:
            # 選択されたインデックスを取得
            selection = self.mounted_disk_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            
            # 選択されたディスク情報を表示
            disk = self.mounted_disks[index]
            
            # テキスト領域を有効化して内容をクリア
            self.mounted_disk_info.config(state=tk.NORMAL)
            self.mounted_disk_info.delete(1.0, tk.END)
            
            # 情報を表示
            self.mounted_disk_info.insert(tk.END, f"名前: {disk['name']}\n")
            self.mounted_disk_info.insert(tk.END, f"パス: {disk['path']}\n")
            self.mounted_disk_info.insert(tk.END, f"サイズ: {disk['size']}\n")
            self.mounted_disk_info.insert(tk.END, f"タイプ: {disk['type']}\n")
            self.mounted_disk_info.insert(tk.END, f"ファイルシステム: {disk['fstype']}\n")
            self.mounted_disk_info.insert(tk.END, f"マウントポイント: {disk['mountpoint']}\n")
            
            # テキスト領域を読み取り専用に戻す
            self.mounted_disk_info.config(state=tk.DISABLED)
            
            # 開くと権限付与ボタンを有効化
            self.open_button.config(state=tk.NORMAL)
            self.permission_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.logger.error(f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"ディスク情報の表示中にエラーが発生しました: {str(e)}")
    
    def _clear_disk_info(self):
        """
        ディスク情報表示エリアをクリア
        """
        self.unmounted_disk_info.config(state=tk.NORMAL)
        self.unmounted_disk_info.delete(1.0, tk.END)
        self.unmounted_disk_info.config(state=tk.DISABLED)
        
        self.mounted_disk_info.config(state=tk.NORMAL)
        self.mounted_disk_info.delete(1.0, tk.END)
        self.mounted_disk_info.config(state=tk.DISABLED)
    
    def _disable_buttons(self):
        """
        全てのボタンを無効化
        """
        self.mount_button.config(state=tk.DISABLED)
        self.format_button.config(state=tk.DISABLED)
        self.open_button.config(state=tk.DISABLED)
        self.permission_button.config(state=tk.DISABLED)
    
    def _mount_selected_disk(self):
        """
        選択された未マウントディスクをマウント
        """
        try:
            # 選択されたインデックスを取得
            selection = self.unmounted_disk_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            disk = self.unmounted_disks[index]
            
            # マウントの処理を別スレッドで実行
            if self.test_mode:
                self.status_var = f"{disk['name']} をマウント中..."
            else:
                self.status_var.set(f"{disk['name']} をマウント中...")
            
            def mount_thread():
                try:
                    success, mount_point, error_msg = self.disk_utils.mount_disk(disk['path'])
                    
                    if success:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "マウント成功",
                            f"{disk['name']} を {mount_point} にマウントしました。"
                        ))
                        self.root.after(0, self._refresh_disk_lists)
                    else:
                        self.root.after(0, lambda: messagebox.showerror(
                            "マウントエラー",
                            f"{disk['name']} のマウントに失敗しました。\n"
                            f"エラー: {error_msg}"
                        ))
                    
                    # ステータスをリセット
                    if self.test_mode:
                        self.root.after(0, lambda: setattr(self, 'status_var', "準備完了"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("準備完了"))
                    
                except Exception as e:
                    self.logger.error(f"マウント処理中にエラーが発生しました: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "エラー",
                        f"マウント処理中にエラーが発生しました: {str(e)}"
                    ))
                    # ステータスをリセット
                    if self.test_mode:
                        self.root.after(0, lambda: setattr(self, 'status_var', "準備完了"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("準備完了"))
            
            thread = threading.Thread(target=mount_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"マウント処理の準備中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"マウント処理の準備中にエラーが発生しました: {str(e)}")
            if self.test_mode:
                self.status_var = "準備完了"
            else:
                self.status_var.set("準備完了")
    
    def _format_selected_disk(self):
        """
        選択された未マウントディスクをフォーマット
        """
        try:
            # 選択されたインデックスを取得
            selection = self.unmounted_disk_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            disk = self.unmounted_disks[index]
            
            # フォーマット形式取得
            fs_type = self.fs_type_var if self.test_mode else self.fs_type_var.get()
            
            # 確認ダイアログを表示
            if not messagebox.askyesno(
                "確認",
                f"{disk['name']} ({disk['path']}) を {fs_type} でフォーマットします。\n"
                f"すべてのデータが消去されます。\n\n"
                f"続行しますか？"
            ):
                return
            
            # フォーマットの処理を別スレッドで実行
            if self.test_mode:
                self.status_var = f"{disk['name']} をフォーマット中..."
            else:
                self.status_var.set(f"{disk['name']} をフォーマット中...")
            
            def format_thread():
                try:
                    success, error_msg = self.disk_utils.format_disk(disk['path'], fs_type)
                    
                    if success:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "フォーマット成功",
                            f"{disk['name']} を {fs_type} 形式でフォーマットしました。"
                        ))
                    else:
                        self.root.after(0, lambda: messagebox.showerror(
                            "フォーマットエラー",
                            f"{disk['name']} のフォーマットに失敗しました。\n"
                            f"エラー: {error_msg}"
                        ))
                    
                    # ステータスをリセット
                    if self.test_mode:
                        self.root.after(0, lambda: setattr(self, 'status_var', "準備完了"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("準備完了"))
                    
                except Exception as e:
                    self.logger.error(f"フォーマット処理中にエラーが発生しました: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "エラー",
                        f"フォーマット処理中にエラーが発生しました: {str(e)}"
                    ))
                    # ステータスをリセット
                    if self.test_mode:
                        self.root.after(0, lambda: setattr(self, 'status_var', "準備完了"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("準備完了"))
            
            thread = threading.Thread(target=format_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"フォーマット処理の準備中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"フォーマット処理の準備中にエラーが発生しました: {str(e)}")
            if self.test_mode:
                self.status_var = "準備完了"
            else:
                self.status_var.set("準備完了")
    
    def _open_selected_disk(self):
        """
        選択されたマウント済みディスクをファイルマネージャーで開く
        """
        try:
            # 選択されたインデックスを取得
            selection = self.mounted_disk_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            disk = self.mounted_disks[index]
            
            if self.test_mode:
                self.status_var = f"{disk['mountpoint']} をファイルマネージャーで開いています..."
            else:
                self.status_var.set(f"{disk['mountpoint']} をファイルマネージャーで開いています...")
            
            success, error_msg = self.disk_utils.open_file_manager(disk['mountpoint'])
            
            if not success:
                messagebox.showerror(
                    "エラー",
                    f"ファイルマネージャーの起動に失敗しました。\n"
                    f"エラー: {error_msg}"
                )
            
            if self.test_mode:
                self.status_var = "準備完了"
            else:
                self.status_var.set("準備完了")
            
        except Exception as e:
            self.logger.error(f"ファイルマネージャー起動中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"ファイルマネージャー起動中にエラーが発生しました: {str(e)}")
            if self.test_mode:
                self.status_var = "準備完了"
            else:
                self.status_var.set("準備完了")
    
    def _set_permissions_to_selected_disk(self):
        """
        選択されたマウント済みディスクに権限を付与
        """
        try:
            # 選択されたインデックスを取得
            selection = self.mounted_disk_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            disk = self.mounted_disks[index]
            
            # 確認ダイアログを表示
            if not messagebox.askyesno(
                "確認",
                f"{disk['mountpoint']} に読み書き権限を付与します。\n\n"
                f"続行しますか？"
            ):
                return
            
            # 権限付与の処理を別スレッドで実行
            if self.test_mode:
                self.status_var = f"{disk['mountpoint']} に権限を付与中..."
            else:
                self.status_var.set(f"{disk['mountpoint']} に権限を付与中...")
            
            def permission_thread():
                try:
                    success, error_msg = self.disk_utils.set_permissions(disk['mountpoint'])
                    
                    if success:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "権限付与成功",
                            f"{disk['mountpoint']} に読み書き権限を付与しました。"
                        ))
                    else:
                        self.root.after(0, lambda: messagebox.showerror(
                            "権限付与エラー",
                            f"{disk['mountpoint']} への権限付与に失敗しました。\n"
                            f"エラー: {error_msg}"
                        ))
                    
                    # ステータスをリセット
                    if self.test_mode:
                        self.root.after(0, lambda: setattr(self, 'status_var', "準備完了"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("準備完了"))
                    
                except Exception as e:
                    self.logger.error(f"権限付与処理中にエラーが発生しました: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "エラー",
                        f"権限付与処理中にエラーが発生しました: {str(e)}"
                    ))
                    # ステータスをリセット
                    if self.test_mode:
                        self.root.after(0, lambda: setattr(self, 'status_var', "準備完了"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("準備完了"))
            
            thread = threading.Thread(target=permission_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"権限付与処理の準備中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"権限付与処理の準備中にエラーが発生しました: {str(e)}")
            if self.test_mode:
                self.status_var = "準備完了"
            else:
                self.status_var.set("準備完了")


def main():
    """
    メイン関数
    """
    root = tk.Tk()
    app = DiskUtilityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main() 