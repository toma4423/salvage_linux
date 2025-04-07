# Disk Utility

USB Boot Linux用のGUIディスクユーティリティです。ディスクのマウント、フォーマット、パーミッション設定などの操作を簡単に行えます。

## 主な機能

- ディスクのマウント/アンマウント
- ディスクのフォーマット（ext4, exfat, ReFS）
- パーミッション設定
- ディスクプロパティの表示
- S.M.A.R.T.情報の表示
- ディスクの健全性評価
- ファイルマネージャーでの開封

## インストール方法

### バイナリからのインストール

1. 最新のリリースから`disk_utility`をダウンロード
2. 実行権限を付与:
   ```bash
   chmod +x disk_utility
   ```
3. 任意のディレクトリに配置

### ソースからのインストール

1. リポジトリをクローン:
   ```bash
   git clone https://github.com/toma4423/salvage_linux.git
   cd salvage_linux
   ```

2. 依存関係をインストール:
   ```bash
   pip install -r requirements.txt
   ```

3. アプリケーションを実行:
   ```bash
   python src/main.py
   ```

## 使用方法

1. アプリケーションを起動
2. 左側のパネルから操作したいディスクを選択
3. 右クリックメニューから以下の操作を選択:
   - マウント/アンマウント
   - フォーマット
   - パーミッション設定
   - プロパティ表示
   - ファイルマネージャーで開く

## 注意事項

- ReFSフォーマット機能は現在仮実装の段階です
- システムディレクトリへの操作は制限されています
- 一部の機能は管理者権限が必要です

## 開発状況

### v0.1.5 (2024-07-26)
- ReFSフォーマット機能の仮実装を追加
- ディスクプロパティ表示機能を追加
- S.M.A.R.T.情報表示機能を追加
- ディスクの健全性評価機能を追加
- ファイルマネージャーでの開封機能を追加

### v0.1.4 (2024-07-25)
- S.M.A.R.T.情報取得の複数方式対応
- S.M.A.R.T.情報取得の信頼性向上
- ユーザーインターフェースの改善
- 重要な属性の色分け表示

### v0.1.3 (2024-07-24)
- ディスク操作の基本機能を実装
- マウント/アンマウント機能
- フォーマット機能（ext4, exfat）
- パーミッション設定機能
- エラーハンドリングの改善
- ログ機能の強化

## ライセンス

MIT License

## 作者

toma4423

## 更新履歴
詳細な更新履歴は[CHANGELOG.md](CHANGELOG.md)を参照してください。

### 最新バージョン (v0.1.5)
- ReFSファイルシステムのサポートを追加
- ディスク操作の安全性を向上
- エラーメッセージの改善
- テストカバレッジの向上

### バージョン (v0.1.4)
- S.M.A.R.T.情報取得機能の複数経路による取得方法を追加
- 異なるディスクメーカーのフォーマットに対応する柔軟な解析機能を追加
- プログラム構造と使用方法に関するドキュメントを大幅に拡充
- S.M.A.R.T.情報取得の信頼性と互換性を向上
- ディスク健康状態判定アルゴリズムの精度向上

### バージョン (v0.1.3)
- ディスクプロパティ表示機能を追加
- 未マウントディスクの右クリックメニューを追加
- S.M.A.R.T.情報表示機能を追加
- ファイルシステムの状態確認機能を追加
- ディスク健康状態評価機能を追加
- プロパティ情報のJSON形式での保存機能を追加

## ライセンス
MIT ライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 貢献
バグ報告や機能リクエストは[GitHubのIssue](https://github.com/toma4423/salvage_linux/issues)にて受け付けています。
プルリクエストも歓迎します。

## Features

- Mount/unmount disks
- Format disks with various filesystems (exFAT, FAT32, NTFS, ext4, ReFS)
- Set disk permissions
- View disk properties and SMART information
- Open mounted disks in file manager
- User-friendly GUI interface

## Configuration Options

### File Manager Settings
- Choose your preferred file manager (Nautilus, Nemo, or Thunar)
- Set default file manager options

### Advanced Settings
- Default format type (exFAT, FAT32, NTFS, ext4, ReFS)
- Log level settings
- ReFS support requires additional tools:
  ```bash
  # For Debian/Ubuntu-based systems
  sudo apt-get update
  sudo apt-get install refs-tools

  # For Fedora/RHEL-based systems
  sudo dnf install refs-tools
  ``` 
