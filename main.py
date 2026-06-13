#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OsEasy-ToolKit
作者: NyxFox (Python重写版)
功能: 解锁噢易学生端的各类限制
主入口文件 (支持 GUI 和 CLI 双模式)
"""

import sys


def main():
    """主入口：默认启动 GUI，传 --cli 参数则启动控制台版"""
    if "--cli" in sys.argv:
        from core.toolkit import main as cli_main
        cli_main()
    else:
        try:
            from gui import OsEasyGUI
            app = OsEasyGUI()
            app.run()
        except ImportError as e:
            print(f"[!] GUI 模块导入失败: {e}")
            print("[*] 尝试启动控制台版本（添加 --cli 参数可强制使用控制台）...")
            print()
            from core.toolkit import main as cli_main
            cli_main()


if __name__ == "__main__":
    main()
