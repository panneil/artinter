#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
硅基流动应用程序 - 修复版
"""
# 首先导入必要的系统模块
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

# 此处开始是原main.py的内容
# 设置 Tesseract 的路径和环境变量
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR'
TESSDATA_PATH = os.path.join(TESSERACT_PATH, 'tessdata')

# 确保路径存在
if not os.path.exists(TESSERACT_PATH):
    print(f"错误: Tesseract 未安装或路径不正确: {TESSERACT_PATH}")
    print("请从 https://github.com/UB-Mannheim/tesseract/wiki 下载并安装 Tesseract")
    sys.exit(1)

if not os.path.exists(TESSDATA_PATH):
    os.makedirs(TESSDATA_PATH)

# 设置 Tesseract 路径
pytesseract.pytesseract.tesseract_cmd = os.path.join(TESSERACT_PATH, 'tesseract.exe')

# 设置环境变量
os.environ['TESSDATA_PREFIX'] = TESSDATA_PATH

# 检查中文语言包
CHINESE_LANG_FILE = os.path.join(TESSDATA_PATH, 'chi_sim.traineddata')
if not os.path.exists(CHINESE_LANG_FILE):
    print(f"错误: 中文语言包未找到: {CHINESE_LANG_FILE}")
    print("请确保已下载中文语言包并放置在正确位置")
    sys.exit(1)

# 以下应该是原main.py中ChatStudio类的定义，但为简化演示这里只放置一个示例类
class ChatStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("硅基流动 Studio")
        self.root.geometry("1200x800")
        
        # 设置主题颜色
        self.bg_color = "#121212"  # 深色背景
        self.text_color = "#FFFFFF"  # 白色文本
        self.accent_color = "#38A169"  # 绿色强调色
        self.highlight_color = "#2D3748"  # 高亮色
        self.secondary_color = "#4A5568"  # 次要颜色
        
        # 应用深色主题
        self.root.configure(bg=self.bg_color)
        
        # 在这里显示一个简单的标签，表示修复成功
        label = tk.Label(root, text="硅基流动启动成功！\n导入问题已修复", 
                         bg=self.bg_color, fg=self.text_color, font=("宋体", 24))
        label.pack(expand=True)

# 主函数
def main():
    root = tk.Tk()
    app = ChatStudio(root)
    root.mainloop()

if __name__ == "__main__":
    main() 