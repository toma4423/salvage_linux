"""
Pytestの設定ファイル

このファイルはPytestの設定を行い、テストの実行環境を整えます。
特にsrcディレクトリをPythonのインポートパスに追加することで、
テストからソースコードをインポートできるようにします。
"""

import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root) 