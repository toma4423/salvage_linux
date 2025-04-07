"""
version.py - バージョン情報管理

このモジュールはDisk Utilityアプリケーションのバージョン情報を管理します。
リリース時に参照される単一の情報源として機能します。

author: toma4423
"""

# バージョン番号 (セマンティックバージョニング)
__version__ = "0.1.5"

# アプリケーション名
APP_NAME = "Disk Utility"

# 著作権表示
COPYRIGHT = "© 2023-2024 toma4423"

def get_version_info():
    """
    バージョン情報を含む文字列を返します。
    
    Returns:
        str: アプリケーション名とバージョン番号を含む文字列
    """
    return f"{APP_NAME} v{__version__}"

def get_about_info():
    """
    アプリケーションについての詳細情報を含む文字列を返します。
    
    Returns:
        str: アプリケーションの詳細情報
    """
    return f"{APP_NAME} v{__version__}\n{COPYRIGHT}\n\nUSB Boot Linux GUIディスクユーティリティ" 