#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
硅基流动应用程序 - 修复与运行脚本
"""
import os
import sys
import shutil
from datetime import datetime

def main():
    print("=" * 50)
    print("  硅基流动应用程序 - 修复与运行脚本")
    print("=" * 50)
    print()
    
    # 显示选项
    print("请选择操作:")
    print("1. 运行修复版程序 (不修改原始文件)")
    print("2. 修复原始文件并运行")
    print("3. 退出")
    
    # 获取用户选择
    try:
        choice = input("\n请输入选项 (1-3): ")
        
        if choice == "1":
            # 运行修复版程序
            print("\n正在启动修复版程序...")
            os.system("python fixed_main.py")
            
        elif choice == "2":
            # 修复原始文件
            print("\n正在备份原始文件...")
            
            # 创建备份目录
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                
            # 备份原始文件
            backup_file = os.path.join(backup_dir, f"main_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
            shutil.copy("main.py", backup_file)
            print(f"原始文件已备份到: {backup_file}")
            
            # 修复原始文件
            print("正在修复原始文件...")
            
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
                
            # 在文件开头添加导入语句
            fixed_content = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from api_client import SilijiClient
from baidu_client import BaiduClient
from netease_client import NeteaseClient
from tencent_client import TencentClient
from aliyun_client import AliyunClient
import json
import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import pytesseract

"""
            
            # 删除原始文件前几行中的导入语句
            lines = content.split("\n")
            # 跳过前9行(包含导入语句)
            new_lines = []
            for i, line in enumerate(lines):
                if i < 9 and any(x in line for x in ["import", "from"]):
                    continue
                else:
                    new_lines.append(line)
                    
            # 合并修复内容
            fixed_content += "\n".join(new_lines)
            
            # 写入修复文件
            with open("main.py", "w", encoding="utf-8") as f:
                f.write(fixed_content)
                
            print("文件修复完成!")
            print("\n正在启动应用程序...")
            os.system("python main.py")
            
        elif choice == "3":
            print("\n感谢使用!")
            sys.exit(0)
            
        else:
            print("\n无效选项，请重新运行脚本选择!")
            
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        print("如有需要，请联系开发人员获取支持。")
        
if __name__ == "__main__":
    main() 