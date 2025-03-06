"""
パッケージングテストスクリプト作成用のスクリプト

PyInstallerでパッケージングしてからテストを実行するためのシェルスクリプトを生成します。
"""

import os

def create_package_test_script():
    """
    PyInstallerでパッケージングしてからテストを実行するためのシェルスクリプトを作成
    
    このスクリプトは、以下の手順を実行します:
    1. PyInstallerを使用してアプリケーションをパッケージング
    2. パッケージングされたアプリケーションの基本テスト
    """
    script_content = """#!/bin/bash
# USB Boot Linux GUI ディスクユーティリティのパッケージングテストスクリプト

echo "=== USB Boot Linux GUI ディスクユーティリティのパッケージングテスト ==="

# 現在のディレクトリを確認
echo "作業ディレクトリ: $(pwd)"

# 1. PyInstallerでパッケージング
echo -e "\\n1. PyInstallerでアプリケーションをパッケージング中..."
if ! pip install pyinstaller; then
    echo "PyInstallerのインストールに失敗しました。"
    exit 1
fi

if ! pyinstaller --onefile --windowed src/main.py; then
    echo "パッケージングに失敗しました。"
    exit 1
fi

# 2. パッケージングされたアプリを検証
echo -e "\\n2. パッケージされたアプリケーションの検証..."

# 実行ファイルの存在を確認
if [[ "$OSTYPE" == "win32" || "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    APP_PATH="dist/main.exe"
else
    APP_PATH="dist/main"
fi

if [ ! -f "$APP_PATH" ]; then
    echo "エラー: パッケージされたアプリケーション $APP_PATH が見つかりません。"
    exit 1
fi

if [ ! -x "$APP_PATH" ]; then
    echo "エラー: パッケージされたアプリケーション $APP_PATH に実行権限がありません。"
    chmod +x "$APP_PATH"
    echo "実行権限を付与しました。"
fi

echo "パッケージされたアプリケーション $APP_PATH が正しく作成されました。"

# 3. 実行テスト
echo -e "\\n3. アプリケーションの起動テスト..."

# 一時ディレクトリを作成
TEST_DIR=$(mktemp -d)
echo "テスト用一時ディレクトリ: $TEST_DIR"

# 環境変数を設定
export LOG_DIR="$TEST_DIR/logs"

# アプリケーションを実行（バックグラウンドで）
"$APP_PATH" &
APP_PID=$!

# 少し待つ
echo "アプリケーションを起動中..."
sleep 3

# プロセスが実行中か確認
if ps -p $APP_PID > /dev/null; then
    echo "アプリケーションが正常に起動しました。"
    echo "プロセスID: $APP_PID"
    
    # ログディレクトリの確認
    if [ -d "$LOG_DIR" ]; then
        echo "ログディレクトリが正しく作成されました: $LOG_DIR"
        ls -la "$LOG_DIR"
    else
        echo "警告: ログディレクトリが作成されませんでした: $LOG_DIR"
    fi
    
    # プロセスを終了
    echo "アプリケーションを終了中..."
    kill $APP_PID
    sleep 1
    
    # 正常に終了したか確認
    if ps -p $APP_PID > /dev/null; then
        echo "警告: アプリケーションが応答しないため強制終了します。"
        kill -9 $APP_PID
    else
        echo "アプリケーションは正常に終了しました。"
    fi
else
    echo "エラー: アプリケーションの起動に失敗しました。"
    exit 1
fi

# 一時ディレクトリを削除
rm -rf "$TEST_DIR"

echo -e "\\n=== すべてのテストが成功しました! ==="
echo "パッケージされたアプリケーション: $APP_PATH"
echo "このアプリケーションを実機にコピーして実行できます。"
"""
    
    # スクリプトをファイルに書き込む
    script_path = os.path.join("tests", "packaging", "run_package_tests.sh")
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # 実行権限を付与
    os.chmod(script_path, 0o755)
    
    print(f"パッケージングテストスクリプトを作成しました: {script_path}")
    print("以下のコマンドでパッケージングとテストを実行できます:")
    print(f"bash {script_path}")

# スクリプト実行
if __name__ == "__main__":
    create_package_test_script() 