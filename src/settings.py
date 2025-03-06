"""
settings.py - アプリケーション設定画面モジュール

このモジュールはアプリケーションの設定画面を提供します。
ユーザーはファイルマネージャーなど各種設定を変更できます。

author: toma4423
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import logging

class SettingsDialog:
    """
    設定ダイアログクラス
    アプリケーション設定を変更するためのダイアログを提供します
    """
    
    def __init__(self, parent, config_manager, logger):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            config_manager: 設定マネージャーインスタンス
            logger: ロガーインスタンス
        """
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        
        # 変更があったかどうかのフラグ
        self.changes_made = False
        
        # ダイアログの作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("設定")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)  # 親ウィンドウに対してモーダルに
        self.dialog.grab_set()  # 他のウィンドウからの入力を無効化
        
        # ウィンドウを画面中央に配置
        self.center_window()
        
        # 設定画面の作成
        self._create_widgets()
        
        # ダイアログが閉じられたときの処理
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def center_window(self):
        """ウィンドウを画面中央に配置する"""
        # ウィンドウサイズを取得
        window_width = self.dialog.winfo_reqwidth()
        window_height = self.dialog.winfo_reqheight()
        
        # 画面の中央座標を計算
        position_right = int(self.parent.winfo_rootx() + (self.parent.winfo_width() / 2) - (window_width / 2))
        position_down = int(self.parent.winfo_rooty() + (self.parent.winfo_height() / 2) - (window_height / 2))
        
        # ウィンドウ位置を設定
        self.dialog.geometry(f"+{position_right}+{position_down}")
    
    def _create_widgets(self):
        """設定画面のウィジェットを作成する"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ノートブック（タブ付きコンテナ）
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 一般設定タブ
        general_tab = ttk.Frame(notebook)
        notebook.add(general_tab, text="一般設定")
        
        # ファイルマネージャー設定タブ
        file_manager_tab = ttk.Frame(notebook)
        notebook.add(file_manager_tab, text="ファイルマネージャー")
        
        # その他の設定タブ
        advanced_tab = ttk.Frame(notebook)
        notebook.add(advanced_tab, text="詳細設定")
        
        # 一般設定タブの内容
        self._create_general_settings(general_tab)
        
        # ファイルマネージャー設定タブの内容
        self._create_file_manager_settings(file_manager_tab)
        
        # 詳細設定タブの内容
        self._create_advanced_settings(advanced_tab)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 保存ボタン
        save_button = ttk.Button(button_frame, text="保存", command=self.save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # キャンセルボタン
        cancel_button = ttk.Button(button_frame, text="キャンセル", command=self.on_close)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # デフォルトに戻すボタン
        reset_button = ttk.Button(button_frame, text="デフォルトに戻す", command=self.reset_to_defaults)
        reset_button.pack(side=tk.LEFT, padx=5)
    
    def _create_general_settings(self, parent):
        """一般設定タブの内容を作成する"""
        # ログレベル設定
        log_frame = ttk.LabelFrame(parent, text="ログレベル", padding=10)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.log_level_var = tk.StringVar(value=self.config_manager.get("log_level", "INFO"))
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        # ラジオボタンでログレベルを選択
        for i, level in enumerate(log_levels):
            ttk.Radiobutton(
                log_frame, 
                text=level, 
                variable=self.log_level_var, 
                value=level
            ).grid(row=0, column=i, padx=10)
        
        # 言語設定
        lang_frame = ttk.LabelFrame(parent, text="言語", padding=10)
        lang_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.language_var = tk.StringVar(value=self.config_manager.get("language", "ja"))
        languages = [("日本語", "ja"), ("English", "en")]
        
        # ラジオボタンで言語を選択
        for i, (text, value) in enumerate(languages):
            ttk.Radiobutton(
                lang_frame, 
                text=text, 
                variable=self.language_var, 
                value=value
            ).grid(row=0, column=i, padx=10)
    
    def _create_file_manager_settings(self, parent):
        """ファイルマネージャー設定タブの内容を作成する"""
        instruction_label = ttk.Label(
            parent, 
            text="ファイルマネージャーの選択\n異なる環境で使用する場合は「自動検出」をお勧めします",
            justify=tk.LEFT,
            wraplength=450
        )
        instruction_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 自動検出か特定のファイルマネージャーを選択
        mode_frame = ttk.Frame(parent)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 現在の設定を取得
        current_fm = self.config_manager.get("file_manager", "auto")
        self.fm_mode_var = tk.StringVar(value="auto" if current_fm == "auto" else "specific")
        
        ttk.Radiobutton(
            mode_frame, 
            text="自動検出（推奨）", 
            variable=self.fm_mode_var, 
            value="auto",
            command=self._update_file_manager_ui
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            mode_frame, 
            text="特定のファイルマネージャーを指定", 
            variable=self.fm_mode_var, 
            value="specific",
            command=self._update_file_manager_ui
        ).pack(anchor=tk.W)
        
        # 特定のファイルマネージャー選択フレーム
        self.specific_fm_frame = ttk.Frame(parent)
        self.specific_fm_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # デフォルトのファイルマネージャーリスト
        file_managers = self.config_manager.get("file_managers_list", [])
        available_fms = []
        
        # システムにインストールされているファイルマネージャーを確認
        for fm in file_managers:
            # dbus-launchなどの複合コマンドは除外
            if " " not in fm:
                try:
                    result = subprocess.run(
                        ["which", fm], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        text=True, 
                        check=False
                    )
                    if result.returncode == 0:
                        available_fms.append(fm)
                except Exception:
                    continue
        
        # 特定のファイルマネージャーを選択できないケースを考慮
        if not available_fms:
            available_fms = ["xdg-open", "pcmanfm", "nautilus", "thunar", "dolphin", "nemo", "caja"]
        
        # 現在指定されているファイルマネージャー
        self.selected_fm_var = tk.StringVar()
        if current_fm != "auto" and current_fm in available_fms:
            self.selected_fm_var.set(current_fm)
        else:
            self.selected_fm_var.set(available_fms[0] if available_fms else "xdg-open")
        
        # ファイルマネージャーのコンボボックス
        ttk.Label(self.specific_fm_frame, text="ファイルマネージャー:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.fm_combobox = ttk.Combobox(
            self.specific_fm_frame,
            textvariable=self.selected_fm_var,
            values=available_fms,
            state="readonly",
            width=20
        )
        self.fm_combobox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # カスタムファイルマネージャーの入力
        ttk.Label(self.specific_fm_frame, text="または、カスタムコマンド:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.custom_fm_var = tk.StringVar()
        if current_fm != "auto" and current_fm not in available_fms:
            self.custom_fm_var.set(current_fm)
            
        self.custom_fm_entry = ttk.Entry(
            self.specific_fm_frame,
            textvariable=self.custom_fm_var,
            width=30
        )
        self.custom_fm_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # ファイルマネージャーリストの表示
        fm_list_frame = ttk.LabelFrame(parent, text="自動検出時のファイルマネージャー優先順位", padding=10)
        fm_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # デフォルトのファイルマネージャーリスト
        self.fm_list_var = tk.StringVar(value=file_managers)
        self.fm_listbox = tk.Listbox(
            fm_list_frame,
            listvariable=self.fm_list_var,
            selectmode=tk.SINGLE,
            height=8
        )
        self.fm_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(fm_list_frame, orient="vertical", command=self.fm_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.fm_listbox.config(yscrollcommand=scrollbar.set)
        
        # 並べ替えボタン
        button_frame = ttk.Frame(fm_list_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        up_button = ttk.Button(button_frame, text="↑", width=2, command=self._move_fm_up)
        up_button.pack(pady=2)
        
        down_button = ttk.Button(button_frame, text="↓", width=2, command=self._move_fm_down)
        down_button.pack(pady=2)
        
        # UI状態を更新
        self._update_file_manager_ui()
    
    def _create_advanced_settings(self, parent):
        """詳細設定タブの内容を作成する"""
        # フォーマットのデフォルト設定
        format_frame = ttk.LabelFrame(parent, text="デフォルトフォーマット形式", padding=10)
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.format_var = tk.StringVar(value=self.config_manager.get("format_default", "exfat"))
        formats = [
            ("exFAT（推奨）", "exfat"),
            ("FAT32", "vfat"),
            ("NTFS", "ntfs"),
            ("ext4", "ext4")
        ]
        
        # ラジオボタンでフォーマット形式を選択
        for i, (text, value) in enumerate(formats):
            ttk.Radiobutton(
                format_frame, 
                text=text, 
                variable=self.format_var, 
                value=value
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=2)
    
    def _update_file_manager_ui(self):
        """ファイルマネージャー設定UIの状態を更新する"""
        if self.fm_mode_var.get() == "auto":
            for child in self.specific_fm_frame.winfo_children():
                child.configure(state="disabled")
        else:
            for child in self.specific_fm_frame.winfo_children():
                child.configure(state="normal")
    
    def _move_fm_up(self):
        """選択したファイルマネージャーを上に移動する"""
        selected_idx = self.fm_listbox.curselection()
        if not selected_idx or selected_idx[0] == 0:
            return
            
        idx = selected_idx[0]
        # 現在のリストを取得
        file_managers = list(self.fm_listbox.get(0, tk.END))
        # 選択された項目を上に移動
        file_managers[idx], file_managers[idx-1] = file_managers[idx-1], file_managers[idx]
        # リストを更新
        self.fm_listbox.delete(0, tk.END)
        for fm in file_managers:
            self.fm_listbox.insert(tk.END, fm)
        # 選択状態を維持
        self.fm_listbox.selection_set(idx-1)
        self.changes_made = True
    
    def _move_fm_down(self):
        """選択したファイルマネージャーを下に移動する"""
        selected_idx = self.fm_listbox.curselection()
        if not selected_idx or selected_idx[0] == self.fm_listbox.size() - 1:
            return
            
        idx = selected_idx[0]
        # 現在のリストを取得
        file_managers = list(self.fm_listbox.get(0, tk.END))
        # 選択された項目を下に移動
        file_managers[idx], file_managers[idx+1] = file_managers[idx+1], file_managers[idx]
        # リストを更新
        self.fm_listbox.delete(0, tk.END)
        for fm in file_managers:
            self.fm_listbox.insert(tk.END, fm)
        # 選択状態を維持
        self.fm_listbox.selection_set(idx+1)
        self.changes_made = True
    
    def save_settings(self):
        """設定を保存する"""
        try:
            # ログレベル設定
            self.config_manager.set("log_level", self.log_level_var.get())
            
            # 言語設定
            self.config_manager.set("language", self.language_var.get())
            
            # ファイルマネージャー設定
            if self.fm_mode_var.get() == "auto":
                self.config_manager.set("file_manager", "auto")
                # ファイルマネージャーリストを更新
                file_managers = list(self.fm_listbox.get(0, tk.END))
                self.config_manager.set("file_managers_list", file_managers)
            else:
                # 特定のファイルマネージャーを使用
                if self.custom_fm_var.get().strip():
                    # カスタムコマンドが入力されている場合
                    self.config_manager.set("file_manager", self.custom_fm_var.get().strip())
                else:
                    # コンボボックスで選択されたファイルマネージャー
                    self.config_manager.set("file_manager", self.selected_fm_var.get())
            
            # フォーマット形式
            self.config_manager.set("format_default", self.format_var.get())
            
            # 設定を保存
            self.config_manager.save_config()
            
            # ログレベルを適用
            log_level = getattr(logging, self.log_level_var.get(), logging.INFO)
            self.logger.setLevel(log_level)
            
            messagebox.showinfo("設定", "設定が保存されました")
            self.dialog.destroy()
        except Exception as e:
            self.logger.error(f"設定の保存中にエラーが発生しました: {e}")
            messagebox.showerror("エラー", f"設定の保存中にエラーが発生しました: {e}")
    
    def reset_to_defaults(self):
        """設定をデフォルトに戻す"""
        if messagebox.askyesno("確認", "すべての設定をデフォルトに戻しますか？"):
            self.config_manager.reset_to_defaults()
            messagebox.showinfo("設定", "設定をデフォルトに戻しました。\n変更を適用するには再起動してください。")
            self.dialog.destroy()
    
    def on_close(self):
        """ダイアログが閉じられたときの処理"""
        if self.changes_made:
            if messagebox.askyesno("確認", "変更が保存されていません。\n変更を破棄しますか？"):
                self.dialog.destroy()
        else:
            self.dialog.destroy() 