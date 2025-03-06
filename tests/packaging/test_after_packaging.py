"""
PyInstallerパッケージング後のテストスクリプト

このスクリプトは、PyInstallerでパッケージングされた後のアプリケーションが
正しく動作するかどうかを確認するためのテストを提供します。
"""

import os
import sys
import subprocess
import tempfile
import time
import json
import pytest
import shutil
from pathlib import Path

def is_packaged_app_available():
    """パッケージングされたアプリケーションが利用可能かどうかを確認する"""
    # dist/main または dist/main.exe を探す
    dist_dir = Path("dist")
    app_name = "main" if sys.platform != "win32" else "main.exe"
    app_path = dist_dir / app_name
    
    return app_path.exists() and os.access(app_path, os.X_OK)

def run_packaged_app(timeout=5):
    """パッケージングされたアプリケーションを実行し、プロセスオブジェクトを返す"""
    app_name = "main" if sys.platform != "win32" else "main.exe"
    app_path = os.path.join("dist", app_name)
    
    # アプリケーションを実行（バックグラウンドで）
    proc = subprocess.Popen([app_path], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE)
    
    # 少し待ってアプリケーションが起動するのを確認
    time.sleep(timeout)
    return proc

def kill_process(proc):
    """プロセスを強制終了する"""
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        # 終了しない場合は強制終了
        proc.kill()

@pytest.mark.skipif(not is_packaged_app_available(), 
                    reason="パッケージングされたアプリケーションが見つかりません")
class TestPackagedApplication:
    """パッケージング後のアプリケーションテスト"""
    
    def test_application_starts(self):
        """アプリケーションが正常に起動するかテスト"""
        proc = run_packaged_app()
        
        try:
            # プロセスが実行中であることを確認
            assert proc.poll() is None, "アプリケーションが起動に失敗しました"
        finally:
            kill_process(proc)
    
    def test_log_directory_creation(self):
        """アプリケーションがログディレクトリを正しく作成するかテスト"""
        # 一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp()
        try:
            # 環境変数でログディレクトリを設定
            env = os.environ.copy()
            env["LOG_DIR"] = os.path.join(temp_dir, "logs")
            
            # アプリケーションを実行
            app_name = "main" if sys.platform != "win32" else "main.exe"
            app_path = os.path.join("dist", app_name)
            
            proc = subprocess.Popen([app_path], 
                                   env=env,
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            
            # 少し待ってログディレクトリが作成されるのを確認
            time.sleep(5)
            
            # ログディレクトリが作成されたことを確認
            log_dir = os.path.join(temp_dir, "logs")
            assert os.path.exists(log_dir), "ログディレクトリが作成されませんでした"
            
            # ログファイルが作成されたことを確認
            log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
            assert len(log_files) > 0, "ログファイルが作成されませんでした"
        finally:
            kill_process(proc)
            # 一時ディレクトリを削除
            shutil.rmtree(temp_dir)
    
    def test_no_error_output(self):
        """アプリケーションが標準エラー出力にエラーを出力しないことをテスト"""
        proc = run_packaged_app()
        
        try:
            # 少し待ってから標準エラー出力を確認
            time.sleep(3)
            stderr_data = proc.stderr.read(1024)
            
            # 標準エラー出力が空であることを確認
            assert not stderr_data, f"標準エラー出力にエラーがあります: {stderr_data.decode('utf-8', errors='ignore')}"
        finally:
            kill_process(proc)
    
def create_package_test_script():
    """
    PyInstallerでパッケージングしてからテストを実行するためのスクリプト
    
    このスクリプトは、以下の手順を実行します:
    1. PyInstallerを使用してアプリケーションをパッケージング
    2. パッケージングされたアプリケーションをテスト
    """
    script_content = """#!/usr/bin/env python3
import os
import subprocess
import sys
import time

def run_command(cmd):
    \"\"\"コマンドを実行し、結果を表示する\"\"\"
    print(f"実行中: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"エラー (コード {result.returncode}):")
        print(result.stderr)
        return False
    print("成功:")
    print(result.stdout)
    return True

def main():
    \"\"\"メインの実行関数\"\"\"
    print("=== USB Boot Linux GUI ディスクユーティリティのパッケージングテスト ===")
    
    # 現在のディレクトリを確認
    print(f"作業ディレクトリ: {os.getcwd()}")
    
    # 1. PyInstallerでパッケージング
    print("\\n1. PyInstallerでアプリケーションをパッケージング中...")
    if not run_command([
        "pyinstaller", 
        "--onefile",
        "--windowed",
        "src/main.py"
    ]):
        print("パッケージングに失敗しました。")
        return 1
    
    # 2. パッケージングされたアプリを検証
    print("\\n2. パッケージされたアプリケーションの検証...")
    
    # 実行ファイルの存在を確認
    app_name = "main" if sys.platform != "win32" else "main.exe"
    app_path = os.path.join("dist", app_name)
    
    if not os.path.exists(app_path):
        print(f"エラー: パッケージされたアプリケーション {app_path} が見つかりません。")
        return 1
    
    if not os.access(app_path, os.X_OK):
        print(f"エラー: パッケージされたアプリケーション {app_path} に実行権限がありません。")
        return 1
    
    print(f"パッケージされたアプリケーション {app_path} が正しく作成されました。")
    
    # 3. パッケージング後のテストを実行
    print("\\n3. パッケージング後のテストを実行中...")
    if not run_command([
        "pytest", 
        "-xvs", 
        "tests/packaging/test_after_packaging.py"
    ]):
        print("パッケージング後のテストに失敗しました。")
        return 1
    
    print("\\n=== すべてのテストが成功しました! ===")
    print(f"パッケージされたアプリケーション: {app_path}")
    print("このアプリケーションを実機にコピーして実行できます。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
    
    # スクリプトをファイルに書き込む
    script_path = os.path.join("tests", "packaging", "run_package_tests.py")
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # 実行権限を付与
    os.chmod(script_path, 0o755)
    
    print(f"パッケージングテストスクリプトを作成しました: {script_path}")
    print("以下のコマンドでパッケージングとテストを実行できます:")
    print(f"python {script_path}")

# このファイルが直接実行された場合、パッケージテストスクリプトを作成
if __name__ == "__main__":
    create_package_test_script() 