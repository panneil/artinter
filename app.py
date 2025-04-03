"""
硅基流动应用主入口
集成多种LLM提供商、文档处理和多功能界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import json
import threading
import queue
import time
import sys
import pyperclip
from PIL import Image, ImageTk

# 导入自定义模块
from siliji_app.llm_providers import LLMProviderFactory
from siliji_app.assistant_manager import AssistantManager
from siliji_app.conversation_manager import ConversationManager
from siliji_app.document_processor import DocumentProcessor
from siliji_app.network_providers import NetworkManager
from siliji_app.ui_components import (
    PopupWindow, ClipboardPopup, ModelComparisonWindow,
    DraggableWidget, TransparentWindow, CodeSyntaxHighlighter,
    MermaidRenderer
)

class SilijiStudio:
    """硅基流动主应用类"""
    
    def __init__(self, root):
        """初始化应用"""
        self.root = root
        self.root.title("硅基流动 Studio")
        self.root.geometry("1280x800")
        
        # 设置主题颜色
        self.bg_color = "#121212"  # 深色背景
        self.text_color = "#FFFFFF"  # 白色文本
        self.accent_color = "#38A169"  # 绿色强调色
        self.highlight_color = "#2D3748"  # 高亮色
        self.secondary_color = "#4A5568"  # 次要颜色
        
        # 应用深色主题
        self.root.configure(bg=self.bg_color)
        
        # 设置配置目录
        self.config_dir = os.path.join(os.path.expanduser("~"), ".siliji_app")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # 配置文件路径
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # 初始化各管理器
        self.init_managers()
        
        # 创建UI样式
        self.create_styles()
        
        # 创建消息队列
        self.message_queue = queue.Queue()
        
        # 创建主界面
        self.create_main_ui()
        
        # 处理消息
        self.process_messages()
        
        # 加载配置
        self.load_config()
        
        # 绑定事件
        self.bind_events()
        
        # 启动定时保存
        self.auto_save_thread = threading.Thread(target=self.auto_save_loop)
        self.auto_save_thread.daemon = True
        self.auto_save_thread.start()
        
    def init_managers(self):
        """初始化各功能管理器"""
        # 助手管理器
        self.assistant_manager = AssistantManager(self.config_dir)
        
        # 对话管理器
        self.conversation_manager = ConversationManager(self.config_dir)
        
        # 文档处理器
        tesseract_path = os.environ.get("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        self.document_processor = DocumentProcessor(tesseract_path)
        
        # 网络管理器
        self.network_manager = NetworkManager()
        
        # LLM提供商
        self.llm_providers = {}
        self.current_provider = None
        self.current_assistant = None 