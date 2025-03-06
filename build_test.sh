#!/bin/bash
# PyInstallerを使用してローカルでビルドをテストするスクリプト

# 色の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PyInstallerを使用したビルドテストを開始します...${NC}"

# 依存関係の確認
echo -e "${YELLOW}依存関係をチェックしています...${NC}"
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}PyInstallerがインストールされていません。インストールしてください:${NC}"
    echo "pip install pyinstaller"
    exit 1
fi

# テストの実行
echo -e "${YELLOW}テストを実行しています...${NC}"
python -m pytest || { echo -e "${RED}テストに失敗しました。ビルドを中止します。${NC}"; exit 1; }

# PyInstallerでビルド
echo -e "${YELLOW}PyInstallerでビルドしています...${NC}"
pyinstaller salvage_linux.spec || { echo -e "${RED}ビルドに失敗しました。${NC}"; exit 1; }

# 実行権限の付与
echo -e "${YELLOW}実行権限を付与しています...${NC}"
chmod +x dist/salvage_linux

echo -e "${GREEN}ビルドが完了しました。${NC}"
echo -e "${YELLOW}実行ファイル: ${NC}dist/salvage_linux"
echo -e "${YELLOW}実行方法: ${NC}sudo ./dist/salvage_linux"

# サイズ情報を表示
echo -e "${YELLOW}実行ファイルのサイズ: ${NC}"
ls -lh dist/salvage_linux 