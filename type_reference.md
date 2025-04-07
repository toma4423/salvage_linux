# 型情報と変数の関係性リファレンス

このドキュメントは、プロジェクト内の変数や関数の型情報、および変数間の関係性を詳細に記録したものです。
修正時にこのドキュメントを参照することで、型の不一致や変数の関係性の問題を防ぐことができます。

## 目次

1. [クラス構造](#クラス構造)
2. [主要な変数と型](#主要な変数と型)
3. [関数の引数と戻り値](#関数の引数と戻り値)
4. [変数間の関係性](#変数間の関係性)
5. [既知の問題点](#既知の問題点)
6. [修正時の注意点](#修正時の注意点)

## クラス構造

### DiskUtilityApp (src/main.py)

メインアプリケーションクラス。GUIの構築と操作を担当します。

**主要な属性:**
- `test_mode` (bool): テストモードフラグ
- `config_manager` (ConfigManager): 設定マネージャーインスタンス
- `logger` (Logger): ロガーインスタンス
- `disk_utils` (DiskUtils): ディスク操作ユーティリティインスタンス
- `properties_analyzer` (DiskPropertiesAnalyzer): ディスクプロパティ分析インスタンス
- `selected_unmounted_disk` (dict or None): 選択された未マウントディスク情報
- `selected_mounted_disk` (dict or None): 選択されたマウント済みディスク情報
- `unmounted_disks` (List[dict]): 未マウントディスクのリスト
- `mounted_disks` (List[dict]): マウント済みディスクのリスト
- `unmounted_disk_listbox` (QListWidget): 未マウントディスクリストウィジェット
- `mounted_disk_listbox` (QListWidget): マウント済みディスクリストウィジェット
- `unmounted_disk_info` (QTextEdit): 未マウントディスク情報表示エリア
- `mounted_disk_info` (QTextEdit): マウント済みディスク情報表示エリア
- `mount_button` (QPushButton): マウントボタン
- `format_button` (QPushButton): フォーマットボタン
- `open_button` (QPushButton): ファイルマネージャーで開くボタン
- `permission_button` (QPushButton): 権限付与ボタン
- `fs_type_group` (QButtonGroup): フォーマット形式選択ボタングループ
- `refresh_button` (QPushButton): ディスクリスト更新ボタン
- `settings_button` (QPushButton): 設定ダイアログを開くボタン
- `status_bar` (QStatusBar): ステータスバー

### DiskUtils (src/disk_utils.py)

ディスク操作を行うクラス。マウント、フォーマット、権限付与などの操作を提供します。

**主要な属性:**
- `logger` (Logger): ロガーインスタンス
- `test_mode` (bool): テストモードフラグ
- `config_manager` (ConfigManager): 設定マネージャーインスタンス
- `protected_dirs` (List[str]): 保護されたシステムディレクトリのリスト
- `allowed_fs_types` (List[str]): 許可されたファイルシステムタイプのリスト
- `supported_fs` (List[str]): サポートされているファイルシステムのリスト
- `default_mount_point` (str): デフォルトのマウントポイント

### Logger (src/logger.py)

ロギング機能を提供するクラス。ログの出力と管理を行います。

**主要な属性:**
- `_call_count` (int): メソッド呼び出し回数
- `log_dir` (str): ログディレクトリのパス
- `log_file` (str): ログファイルのパス
- `logger` (logging.Logger): ロガーインスタンス
- `handler` (RotatingFileHandler): ログファイルハンドラ
- `log_level` (int): ログレベル
- `log_rotation` (int): ログローテーションサイズ
- `log_backup_count` (int): ログバックアップ数

### ConfigManager (src/config_manager.py)

設定の管理を行うクラス。設定の読み込み、保存、取得を提供します。

**主要な属性:**
- `config_file` (str): 設定ファイルのパス
- `config` (dict): 設定データ
- `default_config` (dict): デフォルト設定

### DiskPropertiesAnalyzer (src/disk_properties.py)

ディスクのプロパティを分析するクラス。ディスク情報の取得と解析を行います。

**主要な属性:**
- `logger` (Logger): ロガーインスタンス
- `disk_utils` (DiskUtils): ディスク操作ユーティリティインスタンス

### PropertiesDialog (src/properties_dialog.py)

ディスクプロパティを表示するダイアログクラス。

**主要な属性:**
- `properties` (dict): ディスクプロパティ情報
- `device_path` (str): デバイスパス
- `logger` (Logger): ロガーインスタンス
- `properties_text` (QTextEdit): プロパティ表示エリア
- `close_button` (QPushButton): 閉じるボタン

### SettingsDialog (src/settings.py)

設定ダイアログクラス。アプリケーションの設定を変更するためのUIを提供します。

**主要な属性:**
- `config_manager` (ConfigManager): 設定マネージャーインスタンス
- `logger` (Logger): ロガーインスタンス
- `dark_mode_checkbox` (QCheckBox): ダークモード設定チェックボックス
- `auto_mount_checkbox` (QCheckBox): 自動マウント設定チェックボックス
- `default_mount_point_edit` (QLineEdit): デフォルトマウントポイント入力欄
- `log_level_combo` (QComboBox): ログレベル選択コンボボックス
- `log_rotation_spin` (QSpinBox): ログローテーションサイズ設定スピンボックス
- `log_backup_count_spin` (QSpinBox): ログバックアップ数設定スピンボックス
- `save_button` (QPushButton): 設定保存ボタン
- `cancel_button` (QPushButton): キャンセルボタン

## 主要な変数と型

### ディスク情報 (dict)

ディスク情報は以下のキーを持つ辞書として表現されます：

```python
disk_info = {
    "name": str,          # ディスク名 (例: "sda1")
    "path": str,          # デバイスパス (例: "/dev/sda1")
    "device": str,        # デバイスパス (例: "/dev/sda1") - pathと同じ値
    "size": str,          # サイズ (例: "8G")
    "type": str,          # タイプ (例: "disk", "part")
    "fstype": str,        # ファイルシステムタイプ (例: "ext4", "ntfs")
    "mountpoint": str,    # マウントポイント (マウント済みの場合)
    "model": str,         # モデル名 (例: "Samsung SSD 860 EVO")
    "serial": str,        # シリアル番号
    "uuid": str,          # UUID
    "label": str,         # ラベル
    "partuuid": str,      # パーティションUUID
    "partlabel": str,     # パーティションラベル
    "children": List[dict] # 子デバイス (パーティションなど)
}
```

### ログメッセージ (str)

ログメッセージは文字列として表現されます。ログレベルに応じて以下のメソッドが使用されます：

- `logger.info(message: str)`
- `logger.warning(message: str)`
- `logger.error(message: str)`
- `logger.debug(message: str)`

### 設定データ (dict)

設定データは以下のキーを持つ辞書として表現されます：

```python
config = {
    "dark_mode": bool,           # ダークモード設定
    "auto_mount": bool,          # 自動マウント設定
    "default_mount_point": str,  # デフォルトマウントポイント
    "log_level": str,            # ログレベル
    "log_rotation": int,         # ログローテーションサイズ
    "log_backup_count": int,     # ログバックアップ数
    "protected_dirs": List[str], # 保護されたシステムディレクトリのリスト
    "allowed_fs_types": List[str] # 許可されたファイルシステムタイプのリスト
}
```

### エラー情報 (Tuple[bool, str])

操作の結果を表すタプルとして表現されます：

```python
result = (success: bool, message: str)
```

- `success`: 操作が成功したかどうか
- `message`: 結果のメッセージまたはエラーメッセージ

## 関数の引数と戻り値

### DiskUtils クラスの主要なメソッド

#### get_unmounted_disks() -> dict

未マウントのディスクを取得します。

**戻り値:**
```python
{
    "blockdevices": [
        {
            "name": str,          # デバイス名 (例: "sda")
            "size": str,          # サイズ (例: "500G")
            "type": str,          # タイプ (例: "disk")
            "mountpoint": str,    # マウントポイント (未マウントの場合はNone)
            "fstype": str,        # ファイルシステムタイプ
            "model": str,         # モデル名
            "serial": str,        # シリアル番号
            "uuid": str,          # UUID
            "label": str,         # ラベル
            "children": [         # 子デバイス (パーティションなど)
                {
                    "name": str,      # パーティション名 (例: "sda1")
                    "size": str,      # サイズ (例: "100G")
                    "type": str,      # タイプ (例: "part")
                    "mountpoint": str, # マウントポイント (未マウントの場合はNone)
                    "fstype": str,    # ファイルシステムタイプ
                    "partuuid": str,  # パーティションUUID
                    "partlabel": str, # パーティションラベル
                },
                # 他のパーティション...
            ]
        },
        # 他のデバイス...
    ]
}
```

#### get_mounted_disks() -> List[dict]

マウント済みのディスクの一覧を取得します。

**戻り値:**
```python
[
    {
        "name": str,          # デバイス名 (例: "sda1")
        "path": str,          # デバイスパス (例: "/dev/sda1")
        "device": str,        # デバイスパス (例: "/dev/sda1")
        "size": str,          # サイズ (例: "100G")
        "type": str,          # タイプ (例: "disk", "part")
        "mountpoint": str,    # マウントポイント
        "fstype": str,        # ファイルシステムタイプ
        "model": str,         # モデル名
        "serial": str,        # シリアル番号
        "uuid": str,          # UUID
        "label": str,         # ラベル
        "partuuid": str,      # パーティションUUID
        "partlabel": str,     # パーティションラベル
    },
    # 他のマウント済みディスク...
]
```

#### get_filesystem_type(device_path: str) -> str

デバイスのファイルシステムタイプを取得します。

**引数:**
- `device_path` (str): デバイスパス (例: "/dev/sda1")

**戻り値:**
- `str`: ファイルシステムタイプ (例: "ext4", "ntfs") または空文字列

#### mount_disk(device_path: str, mount_point: str) -> Tuple[bool, str]

ディスクをマウントします。

**引数:**
- `device_path` (str): デバイスパス (例: "/dev/sda1")
- `mount_point` (str): マウントポイント (例: "/mnt/usb")

**戻り値:**
- `Tuple[bool, str]`: (成功したかどうか, メッセージ)

#### format_disk(device_path: str, filesystem_type: str) -> Tuple[bool, str]

ディスクをフォーマットします。

**引数:**
- `device_path` (str): デバイスパス (例: "/dev/sda1")
- `filesystem_type` (str): ファイルシステムタイプ (例: "ntfs", "exfat")

**戻り値:**
- `Tuple[bool, str]`: (成功したかどうか, メッセージ)

#### set_permissions(path: str) -> Tuple[bool, str]

パスの権限を設定します。

**引数:**
- `path` (str): 権限を設定するパス (例: "/mnt/usb")

**戻り値:**
- `Tuple[bool, str]`: (成功したかどうか, メッセージ)

#### open_file_manager(path: str) -> Tuple[bool, str]

ファイルマネージャーでパスを開きます。

**引数:**
- `path` (str): 開くパス (例: "/mnt/usb")

**戻り値:**
- `Tuple[bool, str]`: (成功したかどうか, メッセージ)

#### find_disk_by_display_name(display_name: str, unmounted_only: bool = False, mounted_only: bool = False) -> dict or None

表示名からディスク情報を取得します。

**引数:**
- `display_name` (str): リストボックスに表示されるディスク名 (例: "sda1 (8GB, ディスク)")
- `unmounted_only` (bool): Trueの場合、未マウントディスクのみから検索
- `mounted_only` (bool): Trueの場合、マウント済みディスクのみから検索

**戻り値:**
- `dict or None`: 見つかったディスク情報、見つからない場合はNone

#### is_protected_path(path: str) -> bool

パスが保護されたシステムディレクトリかどうかを判定します。

**引数:**
- `path` (str): 判定するパス

**戻り値:**
- `bool`: 保護されたパスの場合はTrue、そうでない場合はFalse

#### is_allowed_filesystem(filesystem_type: str) -> bool

ファイルシステムタイプが許可されているかどうかを判定します。

**引数:**
- `filesystem_type` (str): 判定するファイルシステムタイプ

**戻り値:**
- `bool`: 許可されている場合はTrue、そうでない場合はFalse

### DiskUtilityApp クラスの主要なメソッド

#### _refresh_disk_lists() -> None

ディスクリストを更新します。

#### _add_disk_to_list(disk_info: dict, list_widget: QListWidget) -> None

ディスク情報をリストに追加します。

**引数:**
- `disk_info` (dict): ディスク情報
- `list_widget` (QListWidget): 追加先のリストウィジェット

#### _mount_selected_disk() -> None

選択された未マウントディスクをマウントします。

#### _format_selected_disk() -> None

選択された未マウントディスクをフォーマットします。

#### _open_selected_disk() -> None

選択されたマウント済みディスクをファイルマネージャーで開きます。

#### _set_permissions_to_selected_disk() -> None

選択されたマウント済みディスクに権限を付与します。

#### _show_unmounted_properties() -> None

選択された未マウントディスクのプロパティを表示します。

#### _on_unmounted_disk_select() -> None

未マウントディスクが選択されたときの処理を行います。

#### _on_mounted_disk_select() -> None

マウント済みディスクが選択されたときの処理を行います。

#### _show_announcements() -> None

お知らせを表示します。

#### _show_error_message(message: str) -> None

エラーメッセージを表示します。

**引数:**
- `message` (str): 表示するエラーメッセージ

#### _show_info_message(message: str) -> None

情報メッセージを表示します。

**引数:**
- `message` (str): 表示する情報メッセージ

#### _show_warning_message(message: str) -> None

警告メッセージを表示します。

**引数:**
- `message` (str): 表示する警告メッセージ

#### _show_critical_message(message: str) -> None

重大なエラーメッセージを表示します。

**引数:**
- `message` (str): 表示する重大なエラーメッセージ

#### _update_status_bar(message: str) -> None

ステータスバーを更新します。

**引数:**
- `message` (str): 表示するメッセージ

### Logger クラスの主要なメソッド

#### info(message: str) -> None

情報レベルのログを出力します。

**引数:**
- `message` (str): ログメッセージ

#### warning(message: str) -> None

警告レベルのログを出力します。

**引数:**
- `message` (str): ログメッセージ

#### error(message: str) -> None

エラーレベルのログを出力します。

**引数:**
- `message` (str): ログメッセージ

#### debug(message: str) -> None

デバッグレベルのログを出力します。

**引数:**
- `message` (str): ログメッセージ

#### _sanitize_path(path: str) -> str

パスを正規化します。

**引数:**
- `path` (str): 正規化するパス

**戻り値:**
- `str`: 正規化されたパス

#### _setup_log_directory() -> None

ログディレクトリを設定します。

#### _setup_logger() -> None

ロガーを設定します。

### ConfigManager クラスの主要なメソッド

#### get_config() -> dict

設定を取得します。

**戻り値:**
- `dict`: 設定データ

#### set_config(key: str, value: Any) -> None

設定を設定します。

**引数:**
- `key` (str): 設定キー
- `value` (Any): 設定値

#### save_config() -> bool

設定を保存します。

**戻り値:**
- `bool`: 成功したかどうか

#### load_config() -> None

設定を読み込みます。

#### _create_default_config() -> None

デフォルト設定を作成します。

### DiskPropertiesAnalyzer クラスの主要なメソッド

#### analyze_disk(device_path: str) -> dict

ディスクのプロパティを分析します。

**引数:**
- `device_path` (str): デバイスパス

**戻り値:**
- `dict`: ディスクのプロパティ情報

#### get_disk_model(device_path: str) -> str

ディスクのモデル名を取得します。

**引数:**
- `device_path` (str): デバイスパス

**戻り値:**
- `str`: モデル名

#### get_disk_serial(device_path: str) -> str

ディスクのシリアル番号を取得します。

**引数:**
- `device_path` (str): デバイスパス

**戻り値:**
- `str`: シリアル番号

#### get_disk_uuid(device_path: str) -> str

ディスクのUUIDを取得します。

**引数:**
- `device_path` (str): デバイスパス

**戻り値:**
- `str`: UUID

#### get_disk_label(device_path: str) -> str

ディスクのラベルを取得します。

**引数:**
- `device_path` (str): デバイスパス

**戻り値:**
- `str`: ラベル

## 変数間の関係性

### ディスク情報の流れ

1. `DiskUtils.get_unmounted_disks()` と `DiskUtils.get_mounted_disks()` がディスク情報を取得
2. `DiskUtilityApp._refresh_disk_lists()` がこれらの情報を受け取り、`unmounted_disks` と `mounted_disks` に格納
3. `DiskUtilityApp._add_disk_to_list()` がディスク情報をリストウィジェットに表示
4. ユーザーがディスクを選択すると、`DiskUtilityApp._on_unmounted_disk_select()` と `DiskUtilityApp._on_mounted_disk_select()` が呼び出される
5. 選択されたディスク情報は `selected_unmounted_disk` と `selected_mounted_disk` に格納される
6. 各種操作（マウント、フォーマット、権限付与など）は選択されたディスク情報を使用して実行される

### ログ情報の流れ

1. 各クラスのインスタンスが `Logger` インスタンスを持つ
2. 各メソッドが `logger.info()`, `logger.warning()`, `logger.error()`, `logger.debug()` を呼び出してログを出力
3. `Logger` クラスがログをファイルに書き込む
4. ログの設定（レベル、ローテーションサイズ、バックアップ数）は `ConfigManager` を通じて管理される

### 設定情報の流れ

1. `ConfigManager` インスタンスが設定を管理
2. `DiskUtilityApp` と `DiskUtils` が `ConfigManager` インスタンスを持つ
3. 設定の変更は `SettingsDialog` を通じて行われる
4. 設定の変更は `ConfigManager.set_config()` を通じて保存される
5. 設定の保存は `ConfigManager.save_config()` を通じて行われる
6. 設定の読み込みは `ConfigManager.load_config()` を通じて行われる
7. デフォルト設定は `ConfigManager._create_default_config()` を通じて作成される

### エラー処理の流れ

1. 各メソッドでエラーが発生すると、`Logger` インスタンスを通じてエラーログが記録される
2. エラーメッセージは `DiskUtilityApp` の各種メッセージ表示メソッドを通じてユーザーに表示される
3. エラーの種類に応じて、適切なメッセージ表示メソッドが選択される
   - 重大なエラー: `_show_critical_message()`
   - エラー: `_show_error_message()`
   - 警告: `_show_warning_message()`
   - 情報: `_show_info_message()`
4. エラーメッセージはステータスバーにも表示される

## 既知の問題点

1. `get_unmounted_disks()` と `get_mounted_disks()` の戻り値の型が異なる
   - `get_unmounted_disks()` は `dict` を返す
   - `get_mounted_disks()` は `List[dict]` を返す
   - これにより、`find_disk_by_display_name()` メソッドで型の不一致が発生する可能性がある

2. ディスク情報の形式が一貫していない
   - 一部のメソッドでは `device` キーを使用
   - 一部のメソッドでは `path` キーを使用
   - これにより、キーの存在チェックが必要になる

3. `_show_unmounted_properties()` メソッドが `find_disk_by_display_name()` を使用しているが、リストボックスから直接ディスク情報を取得する方が効率的

4. エラーハンドリングが不十分
   - 一部のメソッドではエラーハンドリングが不十分
   - エラーメッセージが詳細でない場合がある

5. 型ヒントが不足している
   - 一部のメソッドに型ヒントがない
   - これにより、型の不一致を早期に発見できない

6. テストカバレッジが不十分
   - 一部のメソッドがテストされていない
   - エッジケースのテストが不足している

## 修正時の注意点

1. ディスク情報の形式を統一する
   - すべてのディスク情報に `device` キーと `path` キーを含める
   - `device` キーは常に `/dev/` で始まるパスを含める
   - `path` キーは `device` キーと同じ値を持つ

2. メソッドの戻り値の型を統一する
   - `get_unmounted_disks()` と `get_mounted_disks()` の戻り値の型を統一する
   - どちらも `List[dict]` を返すようにするか、どちらも `dict` を返すようにする

3. リストボックスからのディスク情報取得を最適化する
   - `find_disk_by_display_name()` の代わりに、リストボックスのインデックスから直接ディスク情報を取得する
   - これにより、不要な検索処理を避けることができる

4. エラーハンドリングを強化する
   - すべてのメソッドで適切なエラーハンドリングを行う
   - エラーメッセージを詳細に記録する
   - ユーザーにわかりやすいエラーメッセージを表示する

5. 型ヒントを追加する
   - すべてのメソッドに型ヒントを追加する
   - これにより、型の不一致を早期に発見できる

6. テストを更新する
   - 修正に合わせてテストを更新する
   - 新しいテストケースを追加する
   - 既存のテストケースが正しく動作することを確認する

7. ドキュメントを更新する
   - 修正に合わせてドキュメントを更新する
   - 新しい機能や変更点を記録する
   - 既知の問題点を更新する 