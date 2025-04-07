#!/usr/bin/env python3
"""
Disk Utilityのバージョン情報を管理するモジュール
"""

# バージョン情報
VERSION = "0.1.5"
__version__ = VERSION
APP_NAME = "Disk Utility"
COPYRIGHT = "© 2024 Disk Utility Team"

def get_version_info():
    """
    アプリケーション名とバージョンを返す
    
    Returns:
        str: アプリケーション名とバージョン
    """
    return f"{APP_NAME} v{VERSION}"

def get_about_info():
    """
    アプリケーションの詳細情報を返す
    
    Returns:
        str: アプリケーションの詳細情報
    """
    return f"""
{APP_NAME} v{VERSION}

{COPYRIGHT}

このアプリケーションは、ディスクの管理と操作を簡単に行うためのツールです。
マウント/アンマウント、フォーマット、パーティション作成などの機能を提供します。
""" 