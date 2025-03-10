# 変更履歴

このプロジェクトに対するすべての注目すべき変更はこのファイルに文書化されます。

フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づいています。
またこのプロジェクトは[セマンティックバージョニング](https://semver.org/lang/ja/)を適用しています。

## [0.1.4] - 2024-07-25

### 追加
- S.M.A.R.T.情報取得機能の複数経路による取得方法を追加
- 異なるディスクメーカーのフォーマットに対応する柔軟な解析機能を追加
- プログラム構造と使用方法に関するドキュメントを大幅に拡充

### 改善
- S.M.A.R.T.情報取得の信頼性と互換性を向上
- JSON形式とテキスト解析の両方による情報取得をサポート
- S.M.A.R.T.情報取得失敗時のエラー説明と対処法表示を改善
- ディスク健康状態判定アルゴリズムの精度向上
- 重要属性値の色分け表示によるユーザーインターフェースの改良

### 技術的詳細
- `_get_smart_info_json()`と`_get_smart_info_text()`の複数取得経路実装
- 取得失敗時のフォールバック機構による高い信頼性の実現
- smartctlのタイムアウト設定と例外処理の強化
- 多様なディスクフォーマットに対応する正規表現パターンの実装
- 重要S.M.A.R.T.属性の色分け表示によるユーザーエクスペリエンス向上

## [0.1.3] - 2024-07-20

### 追加
- ディスクプロパティ表示機能を追加
- 未マウントディスクの右クリックメニューを追加
- S.M.A.R.T.情報表示機能を追加
- ファイルシステムの状態確認機能を追加
- ディスク健康状態評価機能を追加
- プロパティ情報のJSON形式での保存機能を追加

### 改善
- ディスクの詳細情報へのアクセスを容易に
- 対話型のプロパティダイアログを実装
- 情報をタブ形式で整理し閲覧性を向上
- S.M.A.R.T.属性による健康状態の評価アルゴリズムを実装
- テスト環境におけるタイムアウト機能の追加
- プロパティファイルの保存形式をデフォルトでJSONに変更
- ディスク検索ロジックを改善し、互換性を向上

### 技術的詳細
- DiskPropertiesAnalyzerクラスによるディスク情報の詳細分析
- PropertiesDialogクラスによる情報表示とファイル保存機能
- S.M.A.R.T.情報の解析と重要属性に基づく健康状態評価
- ファイルシステムチェックの統合
- スレッドセーフなインターフェースの実装
- ディスク検索ロジックの修正（device/pathフィールドの互換性対応）
- プロパティファイルの拡張子をJSONに統一

## [0.1.2] - 2024-07-01

### 追加
- ユーザー設定機能を追加
- 環境に応じたファイルマネージャー自動検出機能を追加
- 設定ダイアログによる各種設定の変更機能を追加
- メニューバーから設定画面を開く機能を追加

### 改善
- 異なるLinux環境でのファイルマネージャー互換性を向上
- ユーザーがログレベルを選択できる機能を追加
- フォーマット形式のデフォルト設定機能を追加
- 設定の永続化（~/.config/salvage_linux/config.json）

### 技術的詳細
- ConfigManagerクラスを実装して設定の管理を担当
- 設定ファイルはJSON形式で保存
- 自動ファイルマネージャー検出アルゴリズムの実装
- ログレベルの動的変更機能を実装

## [0.1.1] - 2024-06-30

### 改善
- GUIレイアウトをレスポンシブに改良
- ウィンドウサイズ変更時のレイアウト崩れを防止
- スクロールバーを追加してリストの閲覧性を向上
- ウィンドウに最小サイズを設定して表示の一貫性を確保
- エラーメッセージをより分かりやすく改善

### 技術的詳細
- ジオメトリマネージャをpackからgridに変更
- 各ウィジェットにgrid_columnconfigureとgrid_rowconfigureを設定
- ウィンドウの最小サイズを設定（800x600）
- ユーザビリティ向上のためのUI調整

## [0.1.0] - 2024-06-23

### 追加
- 初期バージョンリリース
- ディスクのマウント機能
- ディスクのフォーマット機能（ext4, vfat, ntfsに対応）
- ディスクへの権限付与機能
- マウント済みディスクの表示
- マウントされていないディスクの表示
- ディスク情報の表示（パス、タイプなど）
- 操作ログの記録機能
- セキュリティ機能（システムディレクトリの保護、パス検証）

### 技術的詳細
- モジュール化された設計（DiskUtils, Logger）
- 非同期処理によるUI応答性の確保
- 包括的なテストスイート（単体テスト、統合テスト、システムテスト）
- GitHub Actionsによる自動リリース 