# 将当前目录加入Python路径
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

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
import os
import sys
import math

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

class ChatStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("硅基流动 Studio")
        self.root.geometry("1200x800")
        
        # 设置主题状态
        self.is_dark_mode = tk.BooleanVar(value=True)  # 默认为深色模式
        
        # 设置主题颜色
        self.update_theme_colors()
        
        # 应用深色主题
        self.root.configure(bg=self.bg_color)
        
        # 设置配置文件路径
        self.config_dir = os.path.join(os.path.expanduser("~"), ".siliji_app")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.auto_save_file = os.path.join(self.config_dir, "chat_history.txt")
        
        # 创建配置目录
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 初始化语音引擎
        self.engine = pyttsx3.init()
        
        # 创建API客户端
        self.client = SilijiClient("sk-xxszzsdtwmodqelhtbexppaeoasjbtepwqbspprijocdhvdw")
        
        # 创建云API客户端
        self.baidu_client = None
        self.netease_client = None
        self.tencent_client = None
        self.aliyun_client = None
        self.current_image_client = "baidu"  # 默认使用百度云
        self.current_voice_client = "local"  # 默认使用本地语音识别
        
        # 创建消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 加载配置
        self.load_config()
        
        # 初始化扫描状态
        self.scan_active = False
        self.scan_thread = None
        
        # 创建自定义样式
        self.create_styles()
        
        # 创建主框架
        self.create_main_frame()
        
        # 创建侧边栏
        self.create_sidebar()
        
        # 创建聊天区域
        self.create_chat_area()
        
        # 聊天历史
        self.chat_history = []
        
        # 启动消息处理
        self.process_messages()
        
        # 绑定快捷键
        self.bind_shortcuts()
        
    def update_theme_colors(self):
        """更新主题颜色"""
        if self.is_dark_mode.get():
            # 深色主题
            self.bg_color = "#121212"  # 深色背景
            self.text_color = "#000000"  # 黑色文本
            self.accent_color = "#38A169"  # 绿色强调色
            self.highlight_color = "#2D3748"  # 高亮色
            self.secondary_color = "#4A5568"  # 次要颜色
        else:
            # 浅色主题
            self.bg_color = "#F7FAFC"  # 浅色背景
            self.text_color = "#000000"  # 黑色文本
            self.accent_color = "#38A169"  # 保持绿色强调色
            self.highlight_color = "#E2E8F0"  # 浅色高亮
            self.secondary_color = "#CBD5E0"  # 浅色次要颜色
            
    def toggle_theme(self):
        """切换主题模式"""
        # 切换主题状态
        self.is_dark_mode.set(not self.is_dark_mode.get())
        
        # 更新颜色设置
        self.update_theme_colors()
        
        # 更新UI元素样式
        self.update_ui_theme()
        
        # 保存主题设置
        self.save_config()
        
        # 更新状态
        mode_text = "深色" if self.is_dark_mode.get() else "浅色"
        self.message_queue.put(("status", f"已切换到{mode_text}模式"))
        
    def update_ui_theme(self):
        """更新UI元素样式适应新主题"""
        # 更新根窗口背景
        self.root.configure(bg=self.bg_color)
        
        # 重新创建样式
        self.create_styles()
        
        # 更新聊天显示区域样式
        self.chat_display.configure(
            bg=self.bg_color,
            fg="#000000",
            insertbackground="#000000",
            selectbackground=self.accent_color
        )
        
        # 更新输入框样式
        self.input_field.configure(
            bg=self.highlight_color,
            fg="#000000",
            insertbackground="#000000"
        )
        
        # 更新历史记录列表样式
        if hasattr(self, 'history_listbox'):
            self.history_listbox.configure(
                bg=self.highlight_color,
                fg="#000000",
                selectbackground=self.accent_color
            )
        
        # 应用样式到所有框架和组件
        self._update_widget_styles(self.root)
        
    def _update_widget_styles(self, widget):
        """递归更新所有控件的样式"""
        for child in widget.winfo_children():
            # 根据控件类型应用不同样式
            widget_class = child.__class__.__name__
            
            if widget_class == "Frame" or widget_class == "TFrame":
                try:
                    child.configure(background=self.bg_color)
                except:
                    pass
            elif widget_class == "Label" or widget_class == "TLabel":
                try:
                    child.configure(background=self.bg_color, foreground="#000000")
                except:
                    pass
            elif widget_class == "Text" or widget_class == "ScrolledText":
                try:
                    child.configure(
                        bg=self.bg_color,
                        fg="#000000",
                        insertbackground="#000000",
                        selectbackground=self.accent_color
                    )
                except:
                    pass
            elif widget_class == "Entry":
                try:
                    child.configure(
                        bg=self.highlight_color,
                        fg="#000000",
                        insertbackground="#000000"
                    )
                except:
                    pass
            elif widget_class == "Canvas":
                try:
                    child.configure(bg=self.bg_color)
                except:
                    pass
            elif widget_class == "Listbox":
                try:
                    child.configure(
                        bg=self.highlight_color,
                        fg="#000000",
                        selectbackground=self.accent_color
                    )
                except:
                    pass
            
            # 递归处理子控件
            self._update_widget_styles(child)
        
    def create_styles(self):
        """创建自定义样式"""
        # 创建样式对象
        self.style = ttk.Style()
        
        # 配置通用样式
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground="#000000")
        self.style.configure("TButton", background=self.highlight_color, foreground="#000000")
        self.style.configure("TEntry", fieldbackground=self.highlight_color, foreground="#000000")
        self.style.configure("TNotebook", background=self.bg_color)
        self.style.configure("TNotebook.Tab", background=self.highlight_color, foreground="#000000")
        
        # 自定义按钮样式
        self.style.configure("Accent.TButton", background=self.accent_color)
        self.style.map("Accent.TButton", background=[("active", self.accent_color)])
        
        # 侧边栏样式
        self.style.configure("Sidebar.TFrame", background=self.highlight_color)
        self.style.configure("Sidebar.TLabel", background=self.highlight_color, foreground="#000000")
        
        # 聊天区域样式
        self.style.configure("Chat.TFrame", background=self.bg_color)
        
        # 历史记录卡片样式
        self.style.configure("HistoryCard.TFrame",
                            background=self.highlight_color,
                            relief="solid",
                            borderwidth=1)
        
        # 卡片标题样式
        self.style.configure("CardTitle.TLabel",
                            background=self.highlight_color,
                            font=("宋体", 10, "bold"))
        
        # 卡片内容样式
        self.style.configure("CardContent.TLabel",
                            background=self.highlight_color,
                            wraplength=250)
        
    def create_main_frame(self):
        # 主分割框架
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL, style="TFrame")
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
    def create_sidebar(self):
        # 侧边栏框架（现在放在左边）
        self.sidebar = ttk.Frame(self.main_paned, width=300, style="Sidebar.TFrame")
        self.main_paned.add(self.sidebar, weight=1)
        
        # 创建左上角logo和标题
        header_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 用canvas创建绿色小圆点作为logo
        logo_canvas = tk.Canvas(header_frame, width=30, height=30, 
                               bg=self.highlight_color, highlightthickness=0)
        logo_canvas.pack(side=tk.LEFT, padx=5)
        logo_canvas.create_oval(5, 5, 25, 25, fill=self.accent_color, outline="")
        
        # 添加标题
        title_label = ttk.Label(header_frame, text="硅基流动", 
                               font=("宋体", 14, "bold"), style="Sidebar.TLabel")
        title_label.pack(side=tk.LEFT, padx=5)
        
        # 创建选项卡
        self.tab_control = ttk.Notebook(self.sidebar)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # 浏览记录选项卡
        self.history_tab = ttk.Frame(self.tab_control, style="Sidebar.TFrame")
        self.tab_control.add(self.history_tab, text="浏览记录")
        
        # 创建几个模型选项卡
        self.assistant_tab = ttk.Frame(self.tab_control, style="Sidebar.TFrame")
        self.tab_control.add(self.assistant_tab, text="助手")
        
        # 创建模型选项列表
        self.create_model_list(self.assistant_tab)
        
        # 创建浏览记录界面
        self.create_history_tab(self.history_tab)
        
        # 状态栏
        status_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        # 用户信息
        user_frame = ttk.Frame(status_frame, style="Sidebar.TFrame")
        user_frame.pack(fill=tk.X, pady=5)
        
        # 用canvas创建用户头像
        user_canvas = tk.Canvas(user_frame, width=30, height=30, 
                               bg=self.highlight_color, highlightthickness=0)
        user_canvas.pack(side=tk.LEFT, padx=5)
        user_canvas.create_oval(5, 5, 25, 25, fill="#6B46C1", outline="")
        
        # 用户名和时间
        user_info = ttk.Frame(user_frame, style="Sidebar.TFrame")
        user_info.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        user_name = ttk.Label(user_info, text="用户", style="Sidebar.TLabel")
        user_name.pack(anchor="w")
        
        user_time = ttk.Label(user_info, text=time.strftime("%d/%m %H:%M"), 
                             font=("宋体", 8), foreground="#000000", style="Sidebar.TLabel")
        user_time.pack(anchor="w")
        
        # 主题切换开关
        self.theme_canvas = tk.Canvas(user_frame, width=40, height=20, 
                               bg=self.highlight_color, highlightthickness=0)
        self.theme_canvas.pack(side=tk.RIGHT, padx=5)
        self.draw_theme_switch()
        self.theme_canvas.bind("<Button-1>", lambda e: self.toggle_theme_with_animation())
        
        # 状态标签
        self.status_label = ttk.Label(status_frame, text="准备就绪", style="Sidebar.TLabel")
        self.status_label.pack(pady=5, anchor="w")
        
    def create_model_list(self, parent):
        """创建模型列表"""
        # 添加一些示例模型卡片
        models = [
            ("默认助手", "deepseek-ai/DeepSeek-V3", "提供全面的问题解答和对话支持"),
            ("代码助手", "deepseek-ai/deepseek-coder-33b", "快速生成代码和解释代码"),
            ("网页生成", "Web page generation", "快速设计并生成网页"),
            ("图片生成", "Image generation", "根据描述创建图像"),
            ("Python解释器", "Python interpreter", "执行和解释Python代码"),
            ("HR人力资源管理", "Human Resources", "提供人力资源管理相关建议"),
            ("前端工程师", "Frontend Engineer", "Web前端开发专家"),
            ("运维工程师", "Operations Engineer", "系统运维与部署专家"),
            ("开发工程师", "Software Engineer", "软件开发全栈专家"),
            ("测试工程师", "Test Engineer", "软件测试与质量保证")
        ]
        
        # 创建画布和滚动条
        canvas_frame = ttk.Frame(parent, style="Sidebar.TFrame")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(canvas_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建画布
        canvas = tk.Canvas(canvas_frame, bg=self.highlight_color, 
                          yscrollcommand=scrollbar.set, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)
        
        # 创建内容框架
        models_frame = ttk.Frame(canvas, style="Sidebar.TFrame")
        canvas.create_window((0, 0), window=models_frame, anchor="nw")
        
        # 添加模型卡片
        for i, (name, model, desc) in enumerate(models):
            # 创建卡片框架
            card = ttk.Frame(models_frame, style="Sidebar.TFrame")
            card.pack(fill=tk.X, padx=10, pady=5)
            
            # 左侧图标
            icon_canvas = tk.Canvas(card, width=30, height=30, 
                                  bg=self.highlight_color, highlightthickness=0)
            icon_canvas.pack(side=tk.LEFT, padx=5)
            icon_canvas.create_oval(5, 5, 25, 25, fill="#4299E1", outline="")
            
            # 右侧内容
            content = ttk.Frame(card, style="Sidebar.TFrame")
            content.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # 添加模型名称和编号标签
            header = ttk.Frame(content, style="Sidebar.TFrame")
            header.pack(fill=tk.X, expand=True)
            
            name_label = ttk.Label(header, text=name, font=("宋体", 10, "bold"), 
                                 style="Sidebar.TLabel")
            name_label.pack(side=tk.LEFT)
            
            if i == 0:  # 第一个项目添加数字标识
                num_label = ttk.Label(header, text="9", foreground="#9CA3AF",
                                    style="Sidebar.TLabel")
                num_label.pack(side=tk.RIGHT)
            
            # 绑定点击事件
            for widget in [card, icon_canvas, content, name_label]:
                widget.bind("<Button-1>", lambda e, m=model: self.select_model(m))
                
        # 更新画布滚动区域
        models_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
    def select_model(self, model):
        """选择模型"""
        self.model_var.set(model)
        self.message_queue.put(("status", f"已选择模型: {model}"))
        
    def create_siliji_settings(self, parent):
        # 模型选择
        ttk.Label(parent, text="模型选择").pack(pady=5, padx=10, anchor="w")
        self.model_var = tk.StringVar(value="deepseek-ai/DeepSeek-V3")
        self.model_combo = ttk.Combobox(parent, textvariable=self.model_var)
        self.model_combo['values'] = (
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "deepseek-ai/deepseek-coder-33b",
            "deepseek-ai/deepseek-coder-7b",
            "deepseek-ai/deepseek-coder-1.3b",
            "deepseek-ai/deepseek-math-7b",
            "deepseek-ai/deepseek-moe-16b",
            "01-ai/Yi-34B",
            "01-ai/Yi-34B-Chat",
            "01-ai/Yi-6B",
            "01-ai/Yi-6B-Chat",
            "baichuan-inc/Baichuan2-13B-Chat",
            "baichuan-inc/Baichuan2-7B-Chat",
            "internlm/internlm-chat-7b",
            "internlm/internlm-chat-20b",
            "internlm/internlm2-chat-7b",
            "internlm/internlm2-chat-20b",
            "Qwen/Qwen-72B-Chat",
            "Qwen/Qwen-14B-Chat",
            "Qwen/Qwen-7B-Chat",
            "Qwen/Qwen-1.8B-Chat",
            "THUDM/chatglm3-6b",
            "THUDM/chatglm2-6b",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "openchat/openchat-3.5",
            "meta-llama/Llama-2-70b-chat",
            "meta-llama/Llama-2-13b-chat",
            "meta-llama/Llama-2-7b-chat"
        )
        self.model_combo.pack(pady=5, padx=10, fill=tk.X)
        
        # 参数设置
        ttk.Label(parent, text="参数设置").pack(pady=5, padx=10, anchor="w")
        
        # Temperature
        ttk.Label(parent, text="Temperature").pack(pady=2, padx=10, anchor="w")
        self.temperature_var = tk.DoubleVar(value=0.7)
        self.temperature_scale = ttk.Scale(
            parent, from_=0, to=1, 
            variable=self.temperature_var, orient=tk.HORIZONTAL
        )
        self.temperature_scale.pack(pady=2, padx=10, fill=tk.X)
        
        # Max Tokens
        ttk.Label(parent, text="Max Tokens").pack(pady=2, padx=10, anchor="w")
        self.max_tokens_var = tk.IntVar(value=512)
        self.max_tokens_entry = ttk.Entry(
            parent, textvariable=self.max_tokens_var
        )
        self.max_tokens_entry.pack(pady=2, padx=10, fill=tk.X)
        
        # Top P
        ttk.Label(parent, text="Top P").pack(pady=2, padx=10, anchor="w")
        self.top_p_var = tk.DoubleVar(value=0.7)
        self.top_p_scale = ttk.Scale(
            parent, from_=0, to=1, 
            variable=self.top_p_var, orient=tk.HORIZONTAL
        )
        self.top_p_scale.pack(pady=2, padx=10, fill=tk.X)
        
        # 屏幕扫描开关
        self.scan_button = ttk.Button(parent, text="开启屏幕扫描", command=self.toggle_screen_scan)
        self.scan_button.pack(pady=5, padx=10)
        
        # API密钥输入
        ttk.Label(parent, text="API密钥").pack(pady=2, padx=10, anchor="w")
        self.api_code_var = tk.StringVar(value="sk-xxszzsdtwmodqelhtbexppaeoasjbtepwqbspprijocdhvdw")
        self.api_code_entry = ttk.Entry(
            parent, textvariable=self.api_code_var
        )
        self.api_code_entry.pack(pady=2, padx=10, fill=tk.X)
        
        # 更新API密钥按钮
        update_button = ttk.Button(parent, text="更新API密钥", command=self.update_api_key)
        update_button.pack(pady=5, padx=10)

        # 云服务设置按钮
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=10)
        cloud_settings_button = ttk.Button(parent, text="云服务设置", command=self.show_cloud_settings)
        cloud_settings_button.pack(pady=5, padx=10, fill="x")

    def create_baidu_settings(self, parent):
        """创建百度云设置页面"""
        # 标题
        ttk.Label(parent, text="百度云API设置", font=("宋体", 12, "bold")).pack(pady=10, padx=10, anchor="w")
        
        # API密钥输入
        ttk.Label(parent, text="API Key").pack(pady=5, padx=10, anchor="w")
        self.baidu_api_key_var = tk.StringVar(value="")
        self.baidu_api_entry = ttk.Entry(parent, textvariable=self.baidu_api_key_var, width=40)
        self.baidu_api_entry.pack(pady=5, padx=10, fill="x")
        
        # Secret Key输入
        ttk.Label(parent, text="Secret Key").pack(pady=5, padx=10, anchor="w")
        self.baidu_secret_key_var = tk.StringVar(value="")
        self.baidu_secret_entry = ttk.Entry(parent, textvariable=self.baidu_secret_key_var, width=40)
        self.baidu_secret_entry.pack(pady=5, padx=10, fill="x")
        
        # 验证按钮
        verify_button = ttk.Button(parent, text="验证并连接", command=lambda: self.verify_api_keys("baidu"))
        verify_button.pack(pady=5, padx=10)
        
        # 功能区
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=10)
        ttk.Label(parent, text="百度云功能", font=("宋体", 10, "bold")).pack(pady=5, padx=10, anchor="w")
        
        # OCR 按钮
        ocr_button = ttk.Button(parent, text="文字识别 (OCR)", command=self.baidu_ocr)
        ocr_button.pack(pady=5, padx=10, fill="x")
        
        # 图像识别按钮
        image_recog_button = ttk.Button(parent, text="图像识别", command=self.baidu_image_recognition)
        image_recog_button.pack(pady=5, padx=10, fill="x")
        
        # 语音按钮
        voice_button = ttk.Button(parent, text="语音识别", command=lambda: self.cloud_voice_recognition("baidu"))
        voice_button.pack(pady=5, padx=10, fill="x")
        
        # 翻译与分词功能
        ttk.Button(parent, text="文本翻译", command=self.baidu_translate).pack(pady=5, padx=10, fill="x")
        ttk.Button(parent, text="中文分词", command=self.baidu_lexer).pack(pady=5, padx=10, fill="x")

    def create_netease_settings(self, parent):
        """创建网易云设置页面"""
        # 标题
        ttk.Label(parent, text="网易云API设置", font=("宋体", 12, "bold")).pack(pady=10, padx=10, anchor="w")
        
        # API密钥输入
        ttk.Label(parent, text="API Key").pack(pady=5, padx=10, anchor="w")
        self.netease_api_key_var = tk.StringVar(value="")
        self.netease_api_entry = ttk.Entry(parent, textvariable=self.netease_api_key_var, width=40)
        self.netease_api_entry.pack(pady=5, padx=10, fill="x")
        
        # Secret Key输入
        ttk.Label(parent, text="Secret Key").pack(pady=5, padx=10, anchor="w")
        self.netease_secret_key_var = tk.StringVar(value="")
        self.netease_secret_entry = ttk.Entry(parent, textvariable=self.netease_secret_key_var, width=40)
        self.netease_secret_entry.pack(pady=5, padx=10, fill="x")
        
        # 验证按钮
        verify_button = ttk.Button(parent, text="验证并连接", command=lambda: self.verify_api_keys("netease"))
        verify_button.pack(pady=5, padx=10)
        
        # 功能区
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=10)
        ttk.Label(parent, text="网易云功能", font=("宋体", 10, "bold")).pack(pady=5, padx=10, anchor="w")
        
        # OCR 按钮
        ocr_button = ttk.Button(parent, text="文字识别 (OCR)", command=lambda: self.cloud_ocr("netease"))
        ocr_button.pack(pady=5, padx=10, fill="x")
        
        # 图像识别按钮
        image_recog_button = ttk.Button(parent, text="图像识别", command=lambda: self.cloud_image_recognition("netease"))
        image_recog_button.pack(pady=5, padx=10, fill="x")
        
        # 语音按钮
        voice_button = ttk.Button(parent, text="语音识别", command=lambda: self.cloud_voice_recognition("netease"))
        voice_button.pack(pady=5, padx=10, fill="x")

    def create_tencent_settings(self, parent):
        """创建腾讯云设置页面"""
        # 标题
        ttk.Label(parent, text="腾讯云API设置", font=("宋体", 12, "bold")).pack(pady=10, padx=10, anchor="w")
        
        # API密钥输入
        ttk.Label(parent, text="SecretId").pack(pady=5, padx=10, anchor="w")
        self.tencent_api_key_var = tk.StringVar(value="")
        self.tencent_api_entry = ttk.Entry(parent, textvariable=self.tencent_api_key_var, width=40)
        self.tencent_api_entry.pack(pady=5, padx=10, fill="x")
        
        # Secret Key输入
        ttk.Label(parent, text="SecretKey").pack(pady=5, padx=10, anchor="w")
        self.tencent_secret_key_var = tk.StringVar(value="")
        self.tencent_secret_entry = ttk.Entry(parent, textvariable=self.tencent_secret_key_var, width=40)
        self.tencent_secret_entry.pack(pady=5, padx=10, fill="x")
        
        # 验证按钮
        verify_button = ttk.Button(parent, text="验证并连接", command=lambda: self.verify_api_keys("tencent"))
        verify_button.pack(pady=5, padx=10)
        
        # 功能区
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=10)
        ttk.Label(parent, text="腾讯云功能", font=("宋体", 10, "bold")).pack(pady=5, padx=10, anchor="w")
        
        # OCR 按钮
        ocr_button = ttk.Button(parent, text="文字识别 (OCR)", command=lambda: self.cloud_ocr("tencent"))
        ocr_button.pack(pady=5, padx=10, fill="x")
        
        # 图像识别按钮
        image_recog_button = ttk.Button(parent, text="图像识别", command=lambda: self.cloud_image_recognition("tencent"))
        image_recog_button.pack(pady=5, padx=10, fill="x")
        
        # 语音按钮
        voice_button = ttk.Button(parent, text="语音识别", command=lambda: self.cloud_voice_recognition("tencent"))
        voice_button.pack(pady=5, padx=10, fill="x")

    def create_aliyun_settings(self, parent):
        """创建阿里云设置页面"""
        # 标题
        ttk.Label(parent, text="阿里云API设置", font=("宋体", 12, "bold")).pack(pady=10, padx=10, anchor="w")
        
        # API密钥输入
        ttk.Label(parent, text="AccessKey ID").pack(pady=5, padx=10, anchor="w")
        self.aliyun_api_key_var = tk.StringVar(value="")
        self.aliyun_api_entry = ttk.Entry(parent, textvariable=self.aliyun_api_key_var, width=40)
        self.aliyun_api_entry.pack(pady=5, padx=10, fill="x")
        
        # Secret Key输入
        ttk.Label(parent, text="AccessKey Secret").pack(pady=5, padx=10, anchor="w")
        self.aliyun_secret_key_var = tk.StringVar(value="")
        self.aliyun_secret_entry = ttk.Entry(parent, textvariable=self.aliyun_secret_key_var, width=40)
        self.aliyun_secret_entry.pack(pady=5, padx=10, fill="x")
        
        # 验证按钮
        verify_button = ttk.Button(parent, text="验证并连接", command=lambda: self.verify_api_keys("aliyun"))
        verify_button.pack(pady=5, padx=10)
        
        # 功能区
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=10)
        ttk.Label(parent, text="阿里云功能", font=("宋体", 10, "bold")).pack(pady=5, padx=10, anchor="w")
        
        # OCR 按钮
        ocr_button = ttk.Button(parent, text="文字识别 (OCR)", command=lambda: self.cloud_ocr("aliyun"))
        ocr_button.pack(pady=5, padx=10, fill="x")
        
        # 图像识别按钮
        image_recog_button = ttk.Button(parent, text="图像识别", command=lambda: self.cloud_image_recognition("aliyun"))
        image_recog_button.pack(pady=5, padx=10, fill="x")
        
        # 语音按钮
        voice_button = ttk.Button(parent, text="语音识别", command=lambda: self.cloud_voice_recognition("aliyun"))
        voice_button.pack(pady=5, padx=10, fill="x")

    def verify_api_keys(self, provider):
        """验证API密钥
        
        Args:
            provider: 云服务提供商标识，如"baidu"、"netease"等
        """
        # 获取API密钥
        api_key = getattr(self, f"{provider}_api_key_var").get().strip()
        secret_key = getattr(self, f"{provider}_secret_key_var").get().strip()
        
        # 提供商显示名称映射
        provider_display = {
            "baidu": "百度云",
            "netease": "网易云",
            "tencent": "腾讯云",
            "aliyun": "阿里云"
        }
        
        if not api_key or not secret_key:
            self.message_queue.put(("error", f"请输入{provider_display[provider]} API 密钥"))
            return
            
        try:
            self.message_queue.put(("status", f"正在验证{provider_display[provider]}密钥..."))
            
            # 根据不同提供商创建对应的客户端
            if provider == "baidu":
                client = BaiduClient(api_key, secret_key)
            elif provider == "netease":
                client = NeteaseClient(api_key, secret_key)
            elif provider == "tencent":
                client = TencentClient(api_key, secret_key)
            elif provider == "aliyun":
                client = AliyunClient(api_key, secret_key)
            else:
                raise ValueError(f"不支持的云服务提供商: {provider}")
            
            # 保存客户端引用
            setattr(self, f"{provider}_client", client)
            
            # 保存API密钥到配置
            self.save_config()
            
            self.message_queue.put(("status", f"{provider_display[provider]}连接成功"))
            self.message_queue.put(("ai_stream", f"\n{provider_display[provider]} API连接成功，您现在可以使用{provider_display[provider]}功能了。\n"))
        except Exception as e:
            self.message_queue.put(("error", f"{provider_display[provider]}验证失败: {str(e)}"))

    def show_cloud_settings(self):
        """显示云服务设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("云服务设置")
        settings_window.geometry("700x550")
        settings_window.resizable(True, True)
        
        # 创建选项卡
        tab_control = ttk.Notebook(settings_window)
        tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建各个云服务的设置页
        baidu_tab = ttk.Frame(tab_control)
        netease_tab = ttk.Frame(tab_control)
        tencent_tab = ttk.Frame(tab_control)
        aliyun_tab = ttk.Frame(tab_control)
        general_tab = ttk.Frame(tab_control)
        
        tab_control.add(general_tab, text="通用设置")
        tab_control.add(baidu_tab, text="百度云")
        tab_control.add(netease_tab, text="网易云")
        tab_control.add(tencent_tab, text="腾讯云")
        tab_control.add(aliyun_tab, text="阿里云")
        
        # 通用设置页
        ttk.Label(general_tab, text="云服务通用设置", font=("宋体", 12, "bold")).pack(pady=10, padx=10, anchor="w")
        
        # 默认图像识别服务设置
        ttk.Separator(general_tab, orient="horizontal").pack(fill="x", padx=10, pady=5)
        ttk.Label(general_tab, text="默认图像识别服务", font=("宋体", 10, "bold")).pack(pady=5, padx=10, anchor="w")
        
        # 创建单选按钮组
        self.default_cloud_var = tk.StringVar(value=self.current_image_client)
        ttk.Radiobutton(general_tab, text="百度云", variable=self.default_cloud_var, value="baidu").pack(pady=5, padx=20, anchor="w")
        ttk.Radiobutton(general_tab, text="网易云", variable=self.default_cloud_var, value="netease").pack(pady=5, padx=20, anchor="w")
        ttk.Radiobutton(general_tab, text="腾讯云", variable=self.default_cloud_var, value="tencent").pack(pady=5, padx=20, anchor="w")
        ttk.Radiobutton(general_tab, text="阿里云", variable=self.default_cloud_var, value="aliyun").pack(pady=5, padx=20, anchor="w")

        # 默认语音识别服务设置
        ttk.Separator(general_tab, orient="horizontal").pack(fill="x", padx=10, pady=10)
        ttk.Label(general_tab, text="默认语音识别服务", font=("宋体", 10, "bold")).pack(pady=5, padx=10, anchor="w")
        
        # 创建单选按钮组
        self.default_voice_var = tk.StringVar(value=getattr(self, "current_voice_client", "local"))
        ttk.Radiobutton(general_tab, text="本地识别", variable=self.default_voice_var, value="local").pack(pady=5, padx=20, anchor="w")
        ttk.Radiobutton(general_tab, text="百度云", variable=self.default_voice_var, value="baidu").pack(pady=5, padx=20, anchor="w")
        ttk.Radiobutton(general_tab, text="网易云", variable=self.default_voice_var, value="netease").pack(pady=5, padx=20, anchor="w")
        ttk.Radiobutton(general_tab, text="腾讯云", variable=self.default_voice_var, value="tencent").pack(pady=5, padx=20, anchor="w")
        ttk.Radiobutton(general_tab, text="阿里云", variable=self.default_voice_var, value="aliyun").pack(pady=5, padx=20, anchor="w")

        # API服务状态显示
        ttk.Separator(general_tab, orient="horizontal").pack(fill="x", padx=10, pady=10)
        ttk.Label(general_tab, text="云服务连接状态", font=("宋体", 10, "bold")).pack(pady=5, padx=10, anchor="w")
        
        status_frame = ttk.Frame(general_tab)
        status_frame.pack(fill="x", padx=20, pady=5)
        
        # 显示各个云服务的连接状态
        services = [("百度云", "baidu"), ("网易云", "netease"), ("腾讯云", "tencent"), ("阿里云", "aliyun")]
        for i, (name, service) in enumerate(services):
            status_text = "已连接" if getattr(self, f"{service}_client", None) else "未连接"
            status_color = "green" if getattr(self, f"{service}_client", None) else "red"
            
            ttk.Label(status_frame, text=f"{name}:").grid(row=i, column=0, sticky="w", padx=5, pady=3)
            status_label = ttk.Label(status_frame, text=status_text)
            status_label.grid(row=i, column=1, sticky="w", padx=5, pady=3)
            
            # 添加样式
            if status_color == "green":
                status_label.configure(foreground="green")
            else:
                status_label.configure(foreground="red")
        
        # 应用按钮
        def apply_settings():
            self.current_image_client = self.default_cloud_var.get()
            self.current_voice_client = self.default_voice_var.get()
            self.message_queue.put(("status", f"已设置默认图像服务: {self.current_image_client}, 语音服务: {self.current_voice_client}"))
            settings_window.focus_set()  # 让窗口重新获得焦点
            
            # 保存设置到配置文件
            self.save_config()
            
        ttk.Button(general_tab, text="应用设置", command=apply_settings).pack(pady=20)
        
        # 云服务特定设置
        # 百度云设置
        self.create_baidu_settings(baidu_tab)
        # 网易云设置
        self.create_netease_settings(netease_tab)
        # 腾讯云设置
        self.create_tencent_settings(tencent_tab)
        # 阿里云设置
        self.create_aliyun_settings(aliyun_tab)
        
        # 添加底部按钮区域
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        # 关闭按钮
        ttk.Button(
            button_frame, 
            text="关闭", 
            command=settings_window.destroy
        ).pack(side="right", padx=5)
        
        # 确保窗口模态
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 窗口居中
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f'{width}x{height}+{x}+{y}')

    def baidu_ocr(self):
        """使用百度云 OCR 功能"""
        self.cloud_ocr("baidu")

    def cloud_ocr(self, provider):
        """使用指定云服务的 OCR 功能
        
        Args:
            provider: 云服务提供商名称，如 'baidu', 'netease', 'tencent', 'aliyun'
        """
        # 检查对应的客户端是否已初始化
        client = getattr(self, f"{provider}_client", None)
        if not client:
            self.message_queue.put(("error", f"请先验证{provider}云API密钥"))
            return
            
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.jpg *.jpeg *.png")])
        if not file_path:
            return
            
        threading.Thread(target=self._run_cloud_ocr, args=(provider, file_path), daemon=True).start()
    
    def _run_cloud_ocr(self, provider, file_path):
        try:
            client = getattr(self, f"{provider}_client")
            self.message_queue.put(("status", f"正在使用{provider}云OCR识别..."))
            
            # 调用不同提供商的OCR方法
            if provider == "baidu":
                result = client.ocr_general(file_path)
            elif provider == "netease":
                result = client.ocr_general(file_path)  # 假设实现了相同的接口
            elif provider == "tencent":
                result = client.ocr_general(file_path)  # 假设实现了相同的接口
            elif provider == "aliyun":
                result = client.ocr_general(file_path)  # 假设实现了相同的接口
            else:
                raise ValueError(f"不支持的云服务提供商: {provider}")
                
            self.message_queue.put(("ai_stream", f"\n{provider}云OCR识别结果:\n{result}\n"))
            self.message_queue.put(("status", "OCR识别完成"))
        except Exception as e:
            self.message_queue.put(("error", f"OCR识别错误: {str(e)}"))

    def baidu_image_recognition(self):
        """使用百度云图像识别功能"""
        self.cloud_image_recognition("baidu")
            
    def cloud_image_recognition(self, provider):
        """使用指定云服务的图像识别功能
        
        Args:
            provider: 云服务提供商名称，如 'baidu', 'netease', 'tencent', 'aliyun'
        """
        # 检查对应的客户端是否已初始化
        client = getattr(self, f"{provider}_client", None)
        if not client:
            self.message_queue.put(("error", f"请先验证{provider}云API密钥"))
            return
            
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.jpg *.jpeg *.png")])
        if not file_path:
            return
            
        threading.Thread(target=self._run_cloud_image_recog, args=(provider, file_path), daemon=True).start()
    
    def _run_cloud_image_recog(self, provider, file_path):
        try:
            client = getattr(self, f"{provider}_client")
            self.message_queue.put(("status", f"正在使用{provider}云图像识别..."))
            
            # 调用不同提供商的图像识别方法
            if provider == "baidu":
                result = client.image_recognition(file_path)
            elif provider == "netease":
                result = client.image_recognition(file_path)  # 假设实现了相同的接口
            elif provider == "tencent":
                result = client.image_recognition(file_path)  # 假设实现了相同的接口
            elif provider == "aliyun":
                result = client.image_recognition(file_path)  # 假设实现了相同的接口
            else:
                raise ValueError(f"不支持的云服务提供商: {provider}")
                
            # 处理结果
            if isinstance(result, list):
                text_result = "\n".join([f"{item.get('keyword', '未知')} ({item.get('score', 0):.2f})" for item in result[:5]])
                self.message_queue.put(("ai_stream", f"\n{provider}云图像识别结果:\n{text_result}\n"))
            else:
                self.message_queue.put(("ai_stream", f"\n{provider}云图像识别结果:\n{result}\n"))
                
            self.message_queue.put(("status", "图像识别完成"))
        except Exception as e:
            self.message_queue.put(("error", f"图像识别错误: {str(e)}"))

    def upload_image(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.jpg *.jpeg *.png")])
        if file_path:
            # 使用当前默认的图像识别服务
            provider = self.current_image_client
            client = getattr(self, f"{provider}_client", None)
            
            if client:
                threading.Thread(target=self._run_cloud_image_recog, args=(provider, file_path), daemon=True).start()
            else:
                # 如果默认云服务未配置，使用原有的本地处理方法
                threading.Thread(target=self.process_image, args=(file_path,), daemon=True).start()

    def process_image(self, file_path):
        try:
            from PIL import Image
            import torch
            from torchvision import transforms, models
            
            # 图像预处理
            transform = transforms.Compose([
                transforms.Resize(32),  # CIFAR-10 使用 32x32 的图像
                transforms.CenterCrop(32),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
            ])
            
            image = Image.open(file_path).convert('RGB')
            tensor = transform(image).unsqueeze(0)
            
            # 状态更新
            self.message_queue.put(("status", "正在处理图像..."))
            
            # 使用预训练模型
            # 注意：这里使用 ResNet 但映射到 CIFAR-10 的 10 个类别
            model = models.resnet18(pretrained=True)
            # 修改最后一层以适应 CIFAR-10 的 10 个类别
            model.fc = torch.nn.Linear(model.fc.in_features, 10)
            model.eval()
            
            # 进行预测
            with torch.no_grad():
                outputs = model(tensor)
            
            # 获取预测结果
            _, predicted = torch.max(outputs, 1)
            labels = ['飞机', '汽车', '鸟', '猫', '鹿', '狗', '青蛙', '马', '船', '卡车']
            
            # 显示图像和预测类别
            result = f"识别结果：{labels[predicted[0].item() % len(labels)]}"
            
            self.message_queue.put(("ai_stream", f"\n{result}\n"))
            self.text_to_speech(result)
            self.message_queue.put(("status", "图像处理完成"))
            
        except ImportError as e:
            error_msg = f"缺少必要依赖: {str(e)}\n请运行: pip install torch torchvision pillow"
            self.message_queue.put(("error", error_msg))
            self.text_to_speech(error_msg)
        except Exception as e:
            self.message_queue.put(("error", f"图片处理错误: {str(e)}"))
        
    def update_status(self, text):
        self.status_label.config(text=text)
        
    def clear_chat(self):
        self.chat_display.delete(1.0, tk.END)
        
    def text_to_speech(self, text):
        """文本转语音"""
        if not self.tts_enabled:
            return
            
        try:
            # 使用选择的语音引擎
            if self.current_voice_client == "local":
                # 使用本地TTS引擎
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # 使用云服务TTS引擎
                client = getattr(self, f"{self.current_voice_client}_client", None)
                if client:
                    client.text_to_speech(text)
                else:
                    # 如果没有可用的云服务客户端，回退到本地引擎
                    self.engine.say(text)
                    self.engine.runAndWait()
        except Exception as e:
            self.message_queue.put(("status", f"语音播放失败: {str(e)}"))
            
    def add_ai_message(self, message):
        """添加AI消息（用于手动添加AI回复）"""
        # 创建AI气泡
        self.add_message_bubble("ai", message)
        
        # 保存聊天记录
        self.save_chat_history()
        
    def start_voice_input(self):
        """启动语音输入功能"""
        # 弹出语音服务选择对话框
        if hasattr(self, 'is_listening') and self.is_listening:
            return
        
        # 如果语音识别已经在运行，直接返回
        self.is_listening = True
        
        # 定义云服务提供商名称映射
        providers = {
            "local": "本地语音识别",
            "baidu": "百度云语音识别",
            "netease": "网易云语音识别",
            "tencent": "腾讯云语音识别",
            "aliyun": "阿里云语音识别"
        }
        
        # 检查云服务是否已配置
        available_providers = ["local"]  # 本地语音识别总是可用的
        for provider in ["baidu", "netease", "tencent", "aliyun"]:
            if getattr(self, f"{provider}_client", None):
                available_providers.append(provider)
        
        # 如果只有一个可用提供商，直接使用
        if len(available_providers) == 1:
            self.update_status("正在使用本地语音识别...")
            threading.Thread(target=self.voice_input_local, daemon=True).start()
            return
        
        # 如果有多个提供商，弹出选择对话框
        select_dialog = tk.Toplevel(self.root)
        select_dialog.title("选择语音识别服务")
        select_dialog.geometry("300x250")
        select_dialog.resizable(False, False)
        
        # 标题标签
        ttk.Label(select_dialog, text="请选择语音识别服务:", font=("宋体", 12)).pack(pady=10, padx=20)
        
        # 语音服务选择框架
        services_frame = ttk.Frame(select_dialog)
        services_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 创建单选按钮
        voice_provider_var = tk.StringVar(value=available_providers[0])
        for i, provider in enumerate(available_providers):
            ttk.Radiobutton(
                services_frame, 
                text=providers[provider], 
                variable=voice_provider_var, 
                value=provider
            ).pack(anchor="w", pady=5)
        
        # 创建确认按钮
        def confirm_selection():
            provider = voice_provider_var.get()
            select_dialog.destroy()
            
            # 开始语音识别
            self.update_status(f"正在使用{providers[provider]}...")
            
            # 根据不同的提供商启动不同的语音识别线程
            if provider == "local":
                threading.Thread(target=self.voice_input_local, daemon=True).start()
            else:
                threading.Thread(target=self.cloud_voice_recognition, args=(provider,), daemon=True).start()
        
        # 创建按钮
        button_frame = ttk.Frame(select_dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(button_frame, text="确定", command=confirm_selection).pack(side="right", padx=5)
        ttk.Button(button_frame, text="取消", command=lambda: [select_dialog.destroy(), setattr(self, 'is_listening', False)]).pack(side="right", padx=5)
        
        # 确保对话框模态
        select_dialog.transient(self.root)
        select_dialog.grab_set()
        
        # 当对话框关闭但没有选择服务时，停止语音输入
        select_dialog.protocol("WM_DELETE_WINDOW", lambda: [select_dialog.destroy(), setattr(self, 'is_listening', False)])

    def stop_voice_input(self):
        """停止语音输入"""
        if hasattr(self, 'is_listening'):
            self.is_listening = False
        self.update_status("准备就绪")

    def voice_input_local(self):
        """使用本地语音识别引擎进行语音识别"""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                self.update_status("请说话...")
                audio = recognizer.listen(source, timeout=5)
                self.update_status("正在识别...")
                
                text = recognizer.recognize_google(audio, language='zh-CN')
                self.input_field.delete(0, tk.END)
                self.input_field.insert(0, text)
                self.send_message()
                
            except sr.WaitTimeoutError:
                self.update_status("没有检测到语音输入")
            except sr.UnknownValueError:
                self.update_status("无法识别语音")
            except sr.RequestError:
                self.update_status("语音识别服务出错")
            
        self.is_listening = False
        self.update_status("准备就绪")

    def cloud_voice_recognition(self, provider):
        """使用云服务的语音识别功能
        
        Args:
            provider: 云服务提供商名称，如 'baidu', 'netease', 'tencent', 'aliyun'
        """
        # 检查对应的客户端是否已初始化
        client = getattr(self, f"{provider}_client", None)
        if not client:
            self.message_queue.put(("error", f"请先验证{provider}云API密钥"))
            self.is_listening = False
            return
        
        try:
            # 使用麦克风录制音频
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.update_status("请说话...")
                recognizer.adjust_for_ambient_noise(source)
                
                # 录制音频
                try:
                    audio = recognizer.listen(source, timeout=5)
                except sr.WaitTimeoutError:
                    self.update_status("没有检测到语音输入")
                    self.is_listening = False
                    return
                
                self.update_status("正在识别...")
                
                # 保存音频到临时文件
                import tempfile
                import wave
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_filename = temp_file.name
                
                # 将音频数据保存为WAV文件
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(1)  # 单声道
                    wf.setsampwidth(2)  # 16位
                    wf.setframerate(16000)  # 16kHz
                    wf.writeframes(audio.get_wav_data())
                
                # 调用不同提供商的语音识别API
                result = ""
                if provider == "baidu":
                    result = client.speech_recognition(temp_filename)
                elif provider == "netease":
                    result = client.speech_recognition(temp_filename)
                elif provider == "tencent":
                    result = client.speech_recognition(temp_filename)
                elif provider == "aliyun":
                    result = client.speech_recognition(temp_filename)
                
                # 删除临时文件
                import os
                os.unlink(temp_filename)
                
                # 将识别结果填入输入框
                if result:
                    self.input_field.delete(0, tk.END)
                    self.input_field.insert(0, result)
                    self.send_message()
                else:
                    self.update_status("未能识别语音内容")
                
        except Exception as e:
            self.message_queue.put(("error", f"语音识别错误: {str(e)}"))
        finally:
            self.is_listening = False
            self.update_status("准备就绪")

    def send_message(self):
        user_message = self.input_field.get()
        if not user_message.strip():
            return
            
        # 显示用户消息（改为气泡形式）
        self.add_message_bubble("user", user_message)
        
        # 获取当前参数
        params = {
            "model": self.model_var.get(),
            "temperature": self.temperature_var.get(),
            "max_tokens": self.max_tokens_var.get(),
            "top_p": self.top_p_var.get(),
            "stream": True  # 启用流式响应
        }
        
        # 清空输入框并滚动到底部
        self.input_field.delete(0, tk.END)
        self.chat_display.see(tk.END)
        
        # 保存聊天记录
        self.save_chat_history()
        
        # 在新线程中调用API
        threading.Thread(
            target=self.process_chat_response,
            args=(user_message, params),
            daemon=True
        ).start()

    def add_message_bubble(self, sender, message):
        """添加消息气泡"""
        self.chat_display.config(state=tk.NORMAL)
        
        # 在消息前添加换行
        current_text = self.chat_display.get("1.0", tk.END)
        if current_text.strip():
            self.chat_display.insert(tk.END, "\n\n")
        
        # 创建标签位置
        bubble_tag = f"bubble_{int(time.time() * 1000)}"
        
        # 插入消息并标记
        if sender == "user":
            # 用户气泡在右侧
            self.chat_display.insert(tk.END, f"{message}", bubble_tag)
            self.chat_display.tag_configure(bubble_tag, 
                                          background="#E3F2FD", 
                                          foreground="#000000",
                                          borderwidth=1, 
                                          relief=tk.SOLID,
                                          lmargin1=100,  # 左边距
                                          lmargin2=100,  # 第二行左边距
                                          rmargin=20,    # 右边距
                                          justify=tk.RIGHT,
                                          spacing1=5,    # 段前空间
                                          spacing3=5)    # 段后空间
        else:
            # AI气泡在左侧
            self.chat_display.insert(tk.END, f"{message}", bubble_tag)
            self.chat_display.tag_configure(bubble_tag, 
                                          background="#F1F1F1", 
                                          foreground="#000000",
                                          borderwidth=1, 
                                          relief=tk.SOLID,
                                          lmargin1=20,   # 左边距
                                          lmargin2=20,   # 第二行左边距
                                          rmargin=100,   # 右边距
                                          justify=tk.LEFT,
                                          spacing1=5,    # 段前空间
                                          spacing3=5)    # 段后空间
        
        # 添加发送者标识
        if sender == "user":
            self.chat_display.insert(tk.END, "\n", f"{bubble_tag}_sender")
            self.chat_display.insert(tk.END, "你", f"{bubble_tag}_sender")
            self.chat_display.tag_configure(f"{bubble_tag}_sender", 
                                          foreground="#5c6bc0",
                                          justify=tk.RIGHT,
                                          rmargin=20)
        else:
            self.chat_display.insert(tk.END, "\n", f"{bubble_tag}_sender")
            self.chat_display.insert(tk.END, "AI", f"{bubble_tag}_sender")
            self.chat_display.tag_configure(f"{bubble_tag}_sender", 
                                          foreground="#66bb6a",
                                          justify=tk.LEFT,
                                          lmargin1=20)
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def process_chat_response(self, user_message, params):
        try:
            # 更新状态
            self.message_queue.put(("status", "正在请求 API..."))
            
            # 尝试获取响应
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": user_message}],
                **params
            )
            
            # 初始化AI气泡
            self.message_queue.put(("ai_bubble_start", ""))
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        json_str = line.decode('utf-8').replace('data: ', '')
                        if json_str == '[DONE]':
                            continue
                        
                        json_data = json.loads(json_str)
                        if 'choices' in json_data and len(json_data['choices']) > 0:
                            content = json_data['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                full_response += content
                                self.message_queue.put(("ai_stream", content))
                    except json.JSONDecodeError:
                        # 记录错误但继续处理
                        self.message_queue.put(("status", "解析响应数据时出现错误"))
                        continue
                    except Exception as e:
                        # 记录其他错误但继续处理
                        self.message_queue.put(("status", f"处理响应时出错: {str(e)}"))
                        continue
            
            if not full_response:
                self.message_queue.put(("error", "API 返回了空响应"))
            else:
                # 语音播放完整回复
                self.text_to_speech(full_response)
                # 更新状态
                self.message_queue.put(("status", "响应完成"))
                self.message_queue.put(("ai_bubble_end", ""))
                
        except Exception as e:
            error_msg = f"API 请求错误: {str(e)}"
            self.message_queue.put(("error", error_msg))
            self.text_to_speech("很抱歉，API 请求出现错误")
        
    def process_messages(self):
        try:
            while True:
                msg_type, content = self.message_queue.get_nowait()
                
                if msg_type == "ai_bubble_start":
                    # 创建新的AI气泡
                    self.chat_display.config(state=tk.NORMAL)
                    self.current_ai_bubble = f"bubble_{int(time.time() * 1000)}"
                    
                    # 在消息前添加换行
                    current_text = self.chat_display.get("1.0", tk.END)
                    if current_text.strip():
                        self.chat_display.insert(tk.END, "\n\n")
                        
                    # 创建空气泡用于流式填充 - 确保有足够的内容使标签可见
                    self.chat_display.insert(tk.END, "  ", self.current_ai_bubble)  # 添加两个空格
                    self.chat_display.tag_configure(self.current_ai_bubble, 
                                              background="#F1F1F1", 
                                              foreground="#000000",
                                              borderwidth=1, 
                                              relief=tk.SOLID,
                                              lmargin1=20,   # 左边距
                                              lmargin2=20,   # 第二行左边距
                                              rmargin=100,   # 右边距
                                              justify=tk.LEFT,
                                              spacing1=5,    # 段前空间
                                              spacing3=5)    # 段后空间
                    
                    # 添加AI标识
                    self.chat_display.insert(tk.END, "\n", f"{self.current_ai_bubble}_sender")
                    self.chat_display.insert(tk.END, "AI", f"{self.current_ai_bubble}_sender")
                    self.chat_display.tag_configure(f"{self.current_ai_bubble}_sender", 
                                              foreground="#66bb6a",
                                              justify=tk.LEFT,
                                              lmargin1=20)
                    
                    self.current_ai_content = " "  # 初始化为一个空格
                    self.chat_display.config(state=tk.DISABLED)
                
                elif msg_type == "ai_stream":
                    # 检查是否存在当前气泡
                    if not hasattr(self, 'current_ai_bubble') or self.current_ai_bubble is None:
                        # 如果没有当前气泡，先创建一个
                        self.chat_display.config(state=tk.NORMAL)
                        self.current_ai_bubble = f"bubble_{int(time.time() * 1000)}"
                        
                        # 在消息前添加换行
                        current_text = self.chat_display.get("1.0", tk.END)
                        if current_text.strip():
                            self.chat_display.insert(tk.END, "\n\n")
                            
                        # 创建空气泡用于流式填充 - 确保有足够的内容使标签可见
                        self.chat_display.insert(tk.END, "  ", self.current_ai_bubble)  # 添加两个空格
                        self.chat_display.tag_configure(self.current_ai_bubble, 
                                                  background="#F1F1F1", 
                                                  foreground="#000000",
                                                  borderwidth=1, 
                                                  relief=tk.SOLID,
                                                  lmargin1=20,   # 左边距
                                                  lmargin2=20,   # 第二行左边距
                                                  rmargin=100,   # 右边距
                                                  justify=tk.LEFT,
                                                  spacing1=5,    # 段前空间
                                                  spacing3=5)    # 段后空间
                        
                        # 添加AI标识
                        self.chat_display.insert(tk.END, "\n", f"{self.current_ai_bubble}_sender")
                        self.chat_display.insert(tk.END, "AI", f"{self.current_ai_bubble}_sender")
                        self.chat_display.tag_configure(f"{self.current_ai_bubble}_sender", 
                                                  foreground="#66bb6a",
                                                  justify=tk.LEFT,
                                                  lmargin1=20)
                        
                        self.current_ai_content = " "  # 初始化为一个空格
                        self.chat_display.config(state=tk.DISABLED)
                    
                    # 追加内容到气泡
                    self.chat_display.config(state=tk.NORMAL)
                    self.current_ai_content += content
                    
                    # 检查标签是否存在，然后更新气泡内容
                    try:
                        # 确保标签存在
                        if self.current_ai_bubble in self.chat_display.tag_names():
                            start_index = self.chat_display.index(f"{self.current_ai_bubble}.first")
                            end_index = self.chat_display.index(f"{self.current_ai_bubble}.last")
                            self.chat_display.delete(start_index, end_index)
                            self.chat_display.insert(start_index, self.current_ai_content, self.current_ai_bubble)
                        else:
                            # 如果标签不存在，重新创建一个气泡
                            self.chat_display.insert(tk.END, "\n\n", "spacer")
                            self.chat_display.insert(tk.END, self.current_ai_content, self.current_ai_bubble)
                            self.chat_display.tag_configure(self.current_ai_bubble, 
                                                      background="#F1F1F1", 
                                                      foreground="#000000",
                                                      borderwidth=1, 
                                                      relief=tk.SOLID,
                                                      lmargin1=20,   # 左边距
                                                      lmargin2=20,   # 第二行左边距
                                                      rmargin=100,   # 右边距
                                                      justify=tk.LEFT,
                                                      spacing1=5,    # 段前空间
                                                      spacing3=5)    # 段后空间
                            
                            # 添加AI标识
                            self.chat_display.insert(tk.END, "\n", f"{self.current_ai_bubble}_sender")
                            self.chat_display.insert(tk.END, "AI", f"{self.current_ai_bubble}_sender")
                            self.chat_display.tag_configure(f"{self.current_ai_bubble}_sender", 
                                                      foreground="#66bb6a",
                                                      justify=tk.LEFT,
                                                      lmargin1=20)
                    except Exception as e:
                        # 捕获任何可能的错误
                        print(f"更新气泡错误: {str(e)}")
                        # 回退到简单追加模式
                        self.chat_display.insert(tk.END, content)
                    
                    self.chat_display.config(state=tk.DISABLED)
                    self.chat_display.see(tk.END)
                    
                    # 保存聊天记录
                    self.save_chat_history()
                
                elif msg_type == "ai_bubble_end":
                    # 气泡完成，重置引用
                    self.current_ai_bubble = None
                    
                elif msg_type == "error":
                    # 错误消息显示为特殊气泡
                    self.chat_display.config(state=tk.NORMAL)
                    error_tag = f"error_{int(time.time() * 1000)}"
                    
                    # 在消息前添加换行
                    current_text = self.chat_display.get("1.0", tk.END)
                    if current_text.strip():
                        self.chat_display.insert(tk.END, "\n\n")
                    
                    # 插入错误消息
                    self.chat_display.insert(tk.END, content, error_tag)
                    self.chat_display.tag_configure(error_tag, 
                                                 background="#FFEBEE", 
                                                 foreground="#D32F2F",
                                                 borderwidth=1, 
                                                 relief=tk.SOLID,
                                                 lmargin1=20,
                                                 rmargin=20,
                                                 spacing1=5,    # 段前空间
                                                 spacing3=5)    # 段后空间
                            
                    self.chat_display.config(state=tk.DISABLED)
                    self.chat_display.see(tk.END)
                    
                    # 保存聊天记录
                    self.save_chat_history()
                    
                    # 重置当前AI气泡
                    self.current_ai_bubble = None
                    
                elif msg_type == "status":
                    self.update_status(content)
                
        except queue.Empty:
            pass
        finally:
            # 每10ms检查一次消息队列
            self.root.after(10, self.process_messages)

    def update_api_key(self):
        """更新API密钥"""
        api_key = self.api_code_var.get().strip()
        if api_key:
            self.client = SilijiClient(api_key)
            self.message_queue.put(("status", "API密钥已更新"))
            self.save_config()
        else:
            self.message_queue.put(("error", "请输入有效的API密钥"))

    def bind_shortcuts(self):
        self.root.bind('<Control-o>', self.open_file_dialog)
        self.root.bind('<Control-t>', lambda e: self.toggle_theme_with_animation())
        # 添加快捷键绑定
        self.root.bind_all('<Control-c>', self.copy_text)
        self.root.bind_all('<Control-v>', self.paste_text)
        self.root.bind_all('<Control-a>', self.select_all)

    def copy_text(self, event=None):
        """处理复制操作"""
        focused_widget = self.root.focus_get()
        if isinstance(focused_widget, tk.Text):
            try:
                content = focused_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
            except tk.TclError:
                pass
        elif isinstance(focused_widget, tk.Entry):
            focused_widget.event_generate("<<Copy>>")

    def paste_text(self, event=None):
        """处理粘贴操作"""
        focused_widget = self.root.focus_get()
        if isinstance(focused_widget, tk.Text) and focused_widget.cget('state') == 'normal':
            try:
                content = self.root.clipboard_get()
                focused_widget.insert(tk.INSERT, content)
            except tk.TclError:
                pass
        elif isinstance(focused_widget, tk.Entry):
            focused_widget.event_generate("<<Paste>>")

    def select_all(self, event=None):
        """处理全选操作"""
        focused_widget = self.root.focus_get()
        if isinstance(focused_widget, tk.Text):
            focused_widget.tag_add(tk.SEL, "1.0", tk.END)
            focused_widget.mark_set(tk.INSERT, "1.0")
            focused_widget.see(tk.INSERT)
            return "break"
        elif isinstance(focused_widget, tk.Entry):
            focused_widget.select_range(0, tk.END)
            return "break"

    def open_file_dialog(self, event=None):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                content = file.read()
            self.chat_display.see(tk.END)
                
    def select_screen_area(self):
        """使用图形界面让用户选择屏幕区域"""
        import pyautogui
        from tkinter import Toplevel, Canvas
        
        # 隐藏主窗口
        self.root.withdraw()
        
        # 截取全屏
        screenshot = pyautogui.screenshot()
        screen_width, screen_height = screenshot.size
        
        # 创建新窗口显示截图
        area_window = Toplevel()
        area_window.title("选择扫描区域")
        area_window.attributes('-fullscreen', True)
        area_window.resizable(False, False)
        
        # 创建画布
        canvas = Canvas(area_window, width=screen_width, height=screen_height)
        canvas.pack()
        
        # 将截图显示在画布上
        from PIL import ImageTk
        screenshot_tk = ImageTk.PhotoImage(screenshot)
        canvas.create_image(0, 0, anchor="nw", image=screenshot_tk)
        canvas.image = screenshot_tk  # 保持引用
        
        # 选择区域的变量
        start_x, start_y = 0, 0
        rect_id = None
        selected_area = None
        
        # 鼠标事件处理
        def on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x, event.y
            
            # 创建矩形
            rect_id = canvas.create_rectangle(
                start_x, start_y, start_x, start_y,
                outline="red", width=2
            )
        
        def on_drag(event):
            nonlocal rect_id
            if rect_id:
                # 更新矩形
                canvas.coords(rect_id, start_x, start_y, event.x, event.y)
        
        def on_release(event):
            nonlocal selected_area, rect_id
            if rect_id:
                # 获取最终矩形坐标
                x1, y1 = start_x, start_y
                x2, y2 = event.x, event.y
                
                # 确保坐标正确（左上角和右下角）
                left = min(x1, x2)
                top = min(y1, y2)
                width = abs(x1 - x2)
                height = abs(y1 - y2)
                
                if width > 10 and height > 10:  # 忽略太小的选择
                    selected_area = (left, top, width, height)
                    # 完成选择，关闭窗口
                    area_window.after(500, area_window.destroy)
        
        # 绑定鼠标事件
        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        
        # 添加提示文本
        canvas.create_text(
            screen_width // 2, 30,
            text="拖动鼠标选择要扫描的区域，然后释放鼠标按钮",
            fill="red", font=("宋体", 16, "bold")
        )
        
        # 添加取消按钮
        cancel_button = tk.Button(
            area_window, text="取消",
            command=area_window.destroy,
            bg="red", fg="white", font=("宋体", 12)
        )
        cancel_button.place(x=screen_width-100, y=10)
        
        # 等待窗口关闭
        area_window.wait_window()
        
        # 恢复主窗口
        self.root.deiconify()
        
        return selected_area

    def save_chat_history(self):
        """保存聊天记录"""
        # 获取当前聊天内容（纯文本）
        self.chat_display.config(state=tk.NORMAL)
        chat_content = self.chat_display.get("1.0", tk.END).strip()
        self.chat_display.config(state=tk.DISABLED)
        
        if not chat_content:
            return
            
        # 创建历史记录目录
        history_dir = os.path.join(self.config_dir, "history")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
            
        # 检查是否继续保存当前文件或创建新文件
        if hasattr(self, 'current_history_file'):
            # 保存到当前正在查看的文件
            history_file = os.path.join(history_dir, self.current_history_file)
        else:
            # 创建新文件名（日期时间_从内容提取的标题）
            date_str = time.strftime("%Y%m%d_%H%M%S")
            
            # 从内容中提取标题（尝试找第一条用户消息）
            lines = chat_content.splitlines()
            title = "未命名对话"
            for line in lines:
                if "你" in line and len(line) > 2:
                    # 尝试提取用户消息内容作为标题
                    title = line.replace("你", "").strip()
                    if len(title) > 20:
                        title = title[:20] + "..."  # 限制标题长度
                    break
                    
            # 创建文件名
            file_name = f"{date_str}_{title}.txt"
            history_file = os.path.join(history_dir, file_name)
            
            # 保存当前查看的历史记录文件名
            self.current_history_file = file_name
            
            # 刷新历史记录列表
            self.load_history_records()
            
        # 保存内容
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                f.write(chat_content)
        except Exception as e:
            self.message_queue.put(("error", f"保存聊天记录失败: {str(e)}"))

    def create_chat_area(self):
        # 聊天区域框架
        self.chat_frame = ttk.Frame(self.main_paned, style="Chat.TFrame")
        self.main_paned.add(self.chat_frame, weight=3)
        
        # 聊天头部
        chat_header = ttk.Frame(self.chat_frame, style="Chat.TFrame")
        chat_header.pack(fill=tk.X, padx=20, pady=10)
        
        # 模型标签
        model_label = ttk.Label(chat_header, 
                              text="deepseek-ai/DeepSeek-V3 | 硅基流动", 
                              font=("宋体", 12, "bold"),
                              style="TLabel")
        model_label.pack(side=tk.LEFT)
        
        # Token计数器
        token_label = ttk.Label(chat_header, 
                              text="Tokens: 0 / 12000", 
                              foreground="#000000",
                              style="TLabel")
        token_label.pack(side=tk.RIGHT)
        
        # 聊天显示区域
        chat_display_frame = ttk.Frame(self.chat_frame, style="Chat.TFrame")
        chat_display_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # 自定义聊天显示区域样式
        self.chat_display = scrolledtext.ScrolledText(
            chat_display_frame, 
            wrap=tk.WORD,
            bg=self.bg_color,
            fg="#000000",
            insertbackground="#000000",
            selectbackground=self.accent_color,
            font=("宋体", 10),
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # 设置聊天区域为只读
        self.chat_display.config(state=tk.DISABLED)
        
        # 在首次创建时添加欢迎消息
        self.chat_display.config(state=tk.NORMAL)
        welcome_tag = "welcome_message"
        self.chat_display.insert(tk.END, "欢迎使用硅基流动 Studio，请输入您的问题...", welcome_tag)
        self.chat_display.tag_configure(welcome_tag, 
                                     justify=tk.CENTER,
                                     foreground="#9E9E9E",
                                     font=("宋体", 12),
                                     spacing1=30,
                                     spacing3=20)
        self.chat_display.config(state=tk.DISABLED)
        
        # 启用TTS功能
        self.tts_enabled = tk.BooleanVar(value=True)
        
        # 输入区域框架
        input_frame = ttk.Frame(self.chat_frame, style="Chat.TFrame")
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # 输入区背景框架
        input_bg = ttk.Frame(input_frame, style="Chat.TFrame")
        input_bg.pack(fill=tk.X, pady=5)
        
        # 输入框
        self.input_field = tk.Entry(
            input_bg,
            bg=self.highlight_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief=tk.FLAT,
            font=("宋体", 10),
            borderwidth=10
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(input_bg, style="Chat.TFrame")
        button_frame.pack(side=tk.RIGHT, padx=5)
        
        # 图片上传按钮
        self.upload_button = ttk.Button(
            button_frame, text="📁", 
            command=self.upload_image,
            style="TButton",
            width=2
        )
        self.upload_button.pack(side=tk.LEFT, padx=2)
        
        # 语音按钮
        self.voice_button = ttk.Button(
            button_frame, text="🎤", 
            style="TButton",
            width=2
        )
        self.voice_button.pack(side=tk.LEFT, padx=2)
        
        # 发送按钮
        self.send_button = ttk.Button(
            button_frame, text="▶", 
            command=self.send_message,
            style="Accent.TButton",
            width=2
        )
        self.send_button.pack(side=tk.LEFT, padx=2)
        
        # 工具栏
        toolbar = ttk.Frame(input_bg, style="Chat.TFrame")
        toolbar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # 工具按钮
        tools = [
            ("📝", "文本编辑"),
            ("🔗", "添加链接"),
            ("🌐", "翻译"),
            ("📊", "表格"),
            ("🏭", "代码"),
            ("🔍", "搜索"),
            ("🤝", "@提及"),
            ("😊", "表情"),
            ("⚙️", "设置")
        ]
        
        for icon, tooltip in tools:
            btn = ttk.Button(toolbar, text=icon, width=2, style="TButton")
            btn.pack(side=tk.LEFT, padx=2)
            
        # 字数统计标签
        self.char_count_label = ttk.Label(
            toolbar, text="0 / 2347", 
            foreground="#000000",
            style="TLabel"
        )
        self.char_count_label.pack(side=tk.RIGHT, padx=5)
        
        # 绑定事件
        self.input_field.bind('<Return>', lambda e: self.send_message())
        self.voice_button.bind('<ButtonPress-1>', lambda e: self.start_voice_input())
        self.voice_button.bind('<ButtonRelease-1>', lambda e: self.stop_voice_input())
        self.input_field.bind('<KeyRelease>', self.update_char_count)
        
        # 添加硅基流动设置区域（现在放在右边）
        self.settings_frame = ttk.Frame(self.main_paned, width=300, style="Sidebar.TFrame")
        self.main_paned.add(self.settings_frame, weight=1)
        
        # 设置标题
        ttk.Label(self.settings_frame, text="硅基流动设置", 
                font=("宋体", 12, "bold"), style="Sidebar.TLabel").pack(pady=10, padx=10, anchor="w")
        
        # 添加硅基流动设置
        self.create_siliji_settings(self.settings_frame)
        
    def update_char_count(self, event=None):
        """更新字符计数"""
        count = len(self.input_field.get())
        self.char_count_label.config(text=f"{count} / 2347")

    def baidu_translate(self):
        """使用百度云翻译功能"""
        if not self.baidu_client:
            self.message_queue.put(("error", "请先验证百度云API密钥"))
            return
            
        # 创建翻译对话框
        translate_dialog = tk.Toplevel(self.root)
        translate_dialog.title("百度文本翻译")
        translate_dialog.geometry("500x400")
        translate_dialog.resizable(False, False)
        
        # 源语言
        ttk.Label(translate_dialog, text="源语言:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        from_lang_var = tk.StringVar(value="zh")
        from_lang_combo = ttk.Combobox(translate_dialog, textvariable=from_lang_var, width=5)
        from_lang_combo['values'] = ("zh", "en", "jp", "kor", "fra", "spa", "th", "ara", "ru", "pt", "de", "it", "nl")
        from_lang_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 目标语言
        ttk.Label(translate_dialog, text="目标语言:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        to_lang_var = tk.StringVar(value="en")
        to_lang_combo = ttk.Combobox(translate_dialog, textvariable=to_lang_var, width=5)
        to_lang_combo['values'] = ("zh", "en", "jp", "kor", "fra", "spa", "th", "ara", "ru", "pt", "de", "it", "nl")
        to_lang_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # 源文本
        ttk.Label(translate_dialog, text="源文本:").grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="w")
        source_text = tk.Text(translate_dialog, height=5)
        source_text.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        # 翻译按钮
        def do_translate():
            source = source_text.get(1.0, tk.END).strip()
            if not source:
                return
                
            try:
                result = self.baidu_client.translate(
                    source, 
                    from_lang=from_lang_var.get(), 
                    to_lang=to_lang_var.get()
                )
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, result)
                
                # 同时显示在主对话框中
                self.message_queue.put(("ai_stream", f"\n翻译结果: {result}\n"))
            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"翻译错误: {str(e)}")
        
        translate_btn = ttk.Button(translate_dialog, text="翻译", command=do_translate)
        translate_btn.grid(row=3, column=0, columnspan=4, padx=5, pady=5)
        
        # 结果文本
        ttk.Label(translate_dialog, text="翻译结果:").grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="w")
        result_text = tk.Text(translate_dialog, height=5)
        result_text.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        # 配置网格权重
        translate_dialog.grid_rowconfigure(2, weight=1)
        translate_dialog.grid_rowconfigure(5, weight=1)
        translate_dialog.grid_columnconfigure(0, weight=1)
        translate_dialog.grid_columnconfigure(1, weight=1)
        translate_dialog.grid_columnconfigure(2, weight=1)
        translate_dialog.grid_columnconfigure(3, weight=1)

    def baidu_lexer(self):
        """使用百度云中文分词功能"""
        if not self.baidu_client:
            self.message_queue.put(("error", "请先验证百度云API密钥"))
            return
            
        # 获取当前聊天窗口的文本
        text = self.chat_display.get(1.0, tk.END).strip()
        if not text:
            self.message_queue.put(("error", "没有文本可以分析"))
            return
            
        # 选择要分析的文本
        lexer_dialog = tk.Toplevel(self.root)
        lexer_dialog.title("中文分词")
        lexer_dialog.geometry("500x400")
        
        # 文本输入
        ttk.Label(lexer_dialog, text="请输入要分析的文本:").pack(pady=5, padx=10, anchor="w")
        text_input = tk.Text(lexer_dialog, height=8)
        text_input.pack(fill="both", expand=True, padx=10, pady=5)
        text_input.insert(tk.END, text)
        
        # 分析按钮
        def do_lexer():
            target_text = text_input.get(1.0, tk.END).strip()
            if not target_text:
                return
                
            threading.Thread(
                target=self._run_baidu_lexer, 
                args=(target_text, lexer_dialog),
                daemon=True
            ).start()
            
        analyze_btn = ttk.Button(lexer_dialog, text="开始分析", command=do_lexer)
        analyze_btn.pack(pady=10)
    
    def _run_baidu_lexer(self, text, dialog):
        try:
            self.message_queue.put(("status", "正在分词分析..."))
            result = self.baidu_client.nlp_lexer(text)
            
            # 处理结果
            if isinstance(result, dict) and "items" in result:
                items = result["items"]
                formatted_result = "\n".join([
                    f"{item.get('item', '')}\t{item.get('pos', '未知')}" 
                    for item in items[:50]
                ])
                self.message_queue.put(("ai_stream", f"\n分词结果:\n{formatted_result}\n"))
            else:
                self.message_queue.put(("ai_stream", f"\n分词结果:\n{str(result)}\n"))
                
            self.message_queue.put(("status", "分词分析完成"))
            
            # 关闭对话框
            if dialog and dialog.winfo_exists():
                dialog.destroy()
                
        except Exception as e:
            self.message_queue.put(("error", f"分词分析错误: {str(e)}"))

    def save_config(self):
        """保存配置信息到文件"""
        config = {
            "siliji_api_key": self.api_code_var.get(),
            "current_image_client": self.current_image_client,
            "current_voice_client": getattr(self, "current_voice_client", "local"),
            "is_dark_mode": self.is_dark_mode.get(),  # 保存主题设置
            "cloud_api_keys": {}
        }
        
        # 保存各个云服务的API密钥
        for provider in ["baidu", "netease", "tencent", "aliyun"]:
            api_key_var = getattr(self, f"{provider}_api_key_var", None)
            secret_key_var = getattr(self, f"{provider}_secret_key_var", None)
            
            if api_key_var and secret_key_var:
                config["cloud_api_keys"][provider] = {
                    "api_key": api_key_var.get(),
                    "secret_key": secret_key_var.get()
                }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.message_queue.put(("status", "配置已保存"))
        except Exception as e:
            self.message_queue.put(("error", f"保存配置失败: {str(e)}"))
    
    def load_config(self):
        """从文件加载配置信息"""
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 加载硅基流动API密钥
            if "siliji_api_key" in config:
                self.api_code_var = tk.StringVar(value=config["siliji_api_key"])
                self.client = SilijiClient(config["siliji_api_key"])
            
            # 加载默认图像识别服务
            if "current_image_client" in config:
                self.current_image_client = config["current_image_client"]
            
            # 加载默认语音识别服务
            if "current_voice_client" in config:
                self.current_voice_client = config["current_voice_client"]
            else:
                self.current_voice_client = "local"  # 默认使用本地语音识别
                
            # 加载主题设置
            if "is_dark_mode" in config:
                self.is_dark_mode.set(config["is_dark_mode"])
                self.update_theme_colors()
                # 在界面创建后应用主题
                self.root.after(100, self.update_ui_theme)
            
            # 加载各个云服务的API密钥
            if "cloud_api_keys" in config:
                cloud_keys = config["cloud_api_keys"]
                
                for provider, keys in cloud_keys.items():
                    api_key = keys.get("api_key", "")
                    secret_key = keys.get("secret_key", "")
                    
                    # 设置密钥变量，稍后在创建UI时会使用
                    setattr(self, f"{provider}_api_key_var", tk.StringVar(value=api_key))
                    setattr(self, f"{provider}_secret_key_var", tk.StringVar(value=secret_key))
                    
                    # 如果有密钥，尝试创建客户端
                    if api_key and secret_key:
                        try:
                            if provider == "baidu":
                                client = BaiduClient(api_key, secret_key)
                            elif provider == "netease":
                                client = NeteaseClient(api_key, secret_key)
                            elif provider == "tencent":
                                client = TencentClient(api_key, secret_key)
                            elif provider == "aliyun":
                                client = AliyunClient(api_key, secret_key)
                            
                            # 保存客户端引用
                            setattr(self, f"{provider}_client", client)
                        except Exception:
                            # 如果创建客户端失败，忽略错误
                            pass
            
            self.message_queue.put(("status", "配置已加载"))
        except Exception as e:
            self.message_queue.put(("error", f"加载配置失败: {str(e)}"))

    def on_closing(self):
        """窗口关闭时的处理"""
        # 保存配置
        self.save_config()
                    
        # 保存聊天记录
        # 保存聊天记录
        self.save_chat_history()
        # 关闭窗口
        self.root.destroy()

    def toggle_screen_scan(self):
        """实现屏幕扫描功能"""
        # 调用select_screen_area方法获取选中的区域
        selected_area = self.select_screen_area()
        if selected_area:
            # 处理选中的区域
            self.message_queue.put(("status", f"屏幕扫描完成，选中的区域: {selected_area}"))
        else:
            self.message_queue.put(("status", "未选择有效的屏幕区域"))

    def load_history_records(self):
        """加载历史对话记录"""
        # 清空现有内容
        for widget in self.history_content.winfo_children():
            widget.destroy()
        
        # 历史记录目录
        history_dir = os.path.join(self.config_dir, "history")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # 加载历史记录文件
        history_files = [f for f in os.listdir(history_dir) if f.endswith('.txt')]
        history_files.sort(reverse=True)  # 最新的排在前面
        
        for file in history_files:
            self._create_history_card(file)

    def _create_history_card(self, file):
        """创建历史记录卡片"""
        # 创建卡片框架
        card = ttk.Frame(self.history_content, style="Sidebar.TFrame")
        card.pack(fill=tk.X, pady=2)
        
        # 提取日期和标题
        try:
            date_str = file.split('_')[0]
            title = file.replace('.txt', '').split('_', 1)[1] if '_' in file else "未命名对话"
        except:
            date_str = "未知日期"
            title = file.replace('.txt', '')
        
        # 格式化日期显示
        try:
            date_obj = time.strptime(date_str, "%Y%m%d_%H%M%S")
            display_date = time.strftime("%Y-%m-%d %H:%M", date_obj)
        except:
            display_date = date_str
        
        # 创建内容框架
        content = ttk.Frame(card, style="Sidebar.TFrame")
        content.pack(fill=tk.X, padx=10, pady=5)
        
        # 日期标签
        date_label = ttk.Label(content, text=display_date, 
                              font=("宋体", 9),
                              foreground="#666666",
                              style="Sidebar.TLabel")
        date_label.pack(anchor="w")
        
        # 标题标签
        title_label = ttk.Label(content, text=title,
                               font=("宋体", 10, "bold"),
                               style="Sidebar.TLabel")
        title_label.pack(anchor="w")
        
        # 预览内容
        preview_text = self._get_chat_preview(file)
        if preview_text:
            preview_label = ttk.Label(content, text=preview_text,
                                    font=("宋体", 9),
                                    wraplength=250,
                                    style="Sidebar.TLabel")
            preview_label.pack(anchor="w", pady=(2,0))
        
        # 操作按钮框架
        btn_frame = ttk.Frame(content, style="Sidebar.TFrame")
        btn_frame.pack(fill=tk.X, pady=(5,0))
        
        # 打开按钮
        open_btn = ttk.Button(btn_frame, text="打开",
                             command=lambda f=file: self._load_history_file(f),
                             style="Accent.TButton", width=8)
        open_btn.pack(side=tk.LEFT)
        
        # 删除按钮
        delete_btn = ttk.Button(btn_frame, text="删除",
                               command=lambda f=file, c=card: self._delete_history_file(f, c),
                               style="TButton", width=8)
        delete_btn.pack(side=tk.RIGHT)
        
        # 绑定点击事件
        for widget in [card, content, title_label, preview_label]:
            widget.bind('<Button-1>', lambda e, f=file: self._load_history_file(f))

    def _get_chat_preview(self, file):
        """获取对话预览内容"""
        try:
            history_file = os.path.join(self.config_dir, "history", file)
            with open(history_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 获取前100个字符作为预览
                preview = content[:100].replace('\n', ' ')
                return preview + "..." if len(content) > 100 else preview
        except:
            return ""

    def _load_history_file(self, file):
        """加载历史对话文件"""
        history_file = os.path.join(self.config_dir, "history", file)
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清空当前对话并显示历史对话
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, content)
            self.chat_display.config(state=tk.DISABLED)
            
            # 保存当前正在查看的历史记录文件名
            self.current_history_file = file
            
            # 更新状态
            self.message_queue.put(("status", f"已加载历史对话: {file}"))
        except Exception as e:
            self.message_queue.put(("error", f"加载历史对话失败: {str(e)}"))

    def _delete_history_file(self, file, card_widget):
        """删除历史对话文件"""
        if messagebox.askyesno("确认删除", f"确定要删除此历史记录吗？此操作不可恢复。"):
            history_file = os.path.join(self.config_dir, "history", file)
            try:
                if os.path.exists(history_file):
                    os.remove(history_file)
                
                # 从UI中移除卡片
                card_widget.destroy()
                
                # 如果删除的是当前正在查看的记录，清空聊天窗口
                if hasattr(self, 'current_history_file') and self.current_history_file == file:
                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.delete(1.0, tk.END)
                    self.chat_display.config(state=tk.DISABLED)
                    delattr(self, 'current_history_file')
                
                self.message_queue.put(("status", f"已删除历史记录: {file}"))
            except Exception as e:
                self.message_queue.put(("error", f"删除历史记录失败: {str(e)}"))

    def on_history_select(self, event):
        """处理历史记录选择事件"""
        # 检查是否有选择项
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        # 获取选中的文件名
        index = selection[0]
        file_name = self.history_files_map.get(index, self.history_listbox.get(index))
            
        # 加载历史对话内容
        history_file = os.path.join(self.config_dir, "history", file_name)
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 清空当前对话并显示历史对话
                self.chat_display.delete(1.0, tk.END)
                self.chat_display.insert(tk.END, content)
                
                # 保存当前正在查看的历史记录文件名
                self.current_history_file = file_name
                
                # 更新状态
                self.message_queue.put(("status", f"已加载历史对话: {file_name}"))
            except Exception as e:
                self.message_queue.put(("error", f"加载历史对话失败: {str(e)}"))
                
    def delete_history_record(self):
        """删除选中的历史记录"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的历史记录")
            return
            
        index = selection[0]
        file_name = self.history_files_map.get(index, self.history_listbox.get(index))
            
        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除历史记录 '{file_name}' 吗？此操作不可恢复。"):
            # 删除文件
            history_file = os.path.join(self.config_dir, "history", file_name)
            try:
                if os.path.exists(history_file):
                    os.remove(history_file)
                    
                # 从列表中移除
                self.history_listbox.delete(index)
                if index in self.history_files_map:
                    del self.history_files_map[index]
                
                # 如果删除的是当前正在查看的记录，清空聊天窗口
                if hasattr(self, 'current_history_file') and self.current_history_file == file_name:
                    self.chat_display.delete(1.0, tk.END)
                    delattr(self, 'current_history_file')
                    
                self.message_queue.put(("status", f"已删除历史记录: {file_name}"))
            except Exception as e:
                self.message_queue.put(("error", f"删除历史记录失败: {str(e)}"))
                
    def new_conversation(self):
        """创建新对话"""
        # 清空聊天窗口
        self.chat_display.delete(1.0, tk.END)
        
        # 移除当前历史文件引用
        if hasattr(self, 'current_history_file'):
            delattr(self, 'current_history_file')
            
        self.message_queue.put(("status", "已创建新对话"))
        
    def create_history_tab(self, parent):
        """创建浏览记录选项卡"""
        # 创建主框架
        main_frame = ttk.Frame(parent, style="Sidebar.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部工具栏
        toolbar = ttk.Frame(main_frame, style="Sidebar.TFrame")
        toolbar.pack(fill=tk.X, padx=10, pady=(10,5))
        
        # 标题和搜索框
        title_frame = ttk.Frame(toolbar, style="Sidebar.TFrame")
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(title_frame, text="历史对话", 
                  font=("宋体", 12, "bold"), 
                  style="Sidebar.TLabel").pack(side=tk.LEFT)
        
        # 搜索框
        search_frame = ttk.Frame(title_frame, style="Sidebar.TFrame")
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 工具按钮
        btn_frame = ttk.Frame(toolbar, style="Sidebar.TFrame")
        btn_frame.pack(side=tk.RIGHT, padx=(5,0))
        
        ttk.Button(btn_frame, text="🔄", width=3, 
                   command=self.load_history_records).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➕", width=3,
                   command=self.new_conversation).pack(side=tk.LEFT, padx=2)
        
        # 历史记录列表框架
        list_frame = ttk.Frame(main_frame, style="Sidebar.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建Canvas和滚动条
        self.history_canvas = tk.Canvas(list_frame, 
                                      bg=self.highlight_color,
                                      highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                 command=self.history_canvas.yview)
        
        # 配置Canvas
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建内容框架
        self.history_content = ttk.Frame(self.history_canvas, style="Sidebar.TFrame")
        self.history_canvas_frame = self.history_canvas.create_window(
            (0, 0), window=self.history_content, anchor="nw"
        )
        
        # 布局
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self.history_content.bind('<Configure>', self._on_frame_configure)
        self.history_canvas.bind('<Configure>', self._on_canvas_configure)
        self.search_var.trace('w', self._on_search_change)
        
        # 加载历史记录
        self.load_history_records()

    def _on_frame_configure(self, event=None):
        """更新Canvas的滚动区域"""
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """当Canvas大小改变时，调整内容框架宽度"""
        self.history_canvas.itemconfig(self.history_canvas_frame, width=event.width)

    def _on_search_change(self, *args):
        """处理搜索框内容变化"""
        search_text = self.search_var.get().lower()
        for child in self.history_content.winfo_children():
            if isinstance(child, ttk.Frame):
                title_label = child.winfo_children()[1]
                text = title_label.cget("text").lower()
                child.pack_forget() if search_text and search_text not in text else child.pack(fill=tk.X, pady=2)

    def draw_theme_switch(self):
        """绘制主题切换开关"""
        self.theme_canvas.delete("all")
        
        # 设置开关背景色
        bg_color = self.accent_color if self.is_dark_mode.get() else "#CBD5E0"
        
        # 绘制圆角矩形作为背景
        self._create_rounded_rectangle(
            self.theme_canvas,
            0, 0, 40, 20, 
            radius=10, 
            fill=bg_color, 
            tags="switch_bg"
        )
        
        # 绘制开关按钮
        button_x = 30 if self.is_dark_mode.get() else 10
        # 绘制月亮图标（深色模式）或太阳图标（浅色模式）
        if self.is_dark_mode.get():
            # 月亮图标
            self.theme_canvas.create_oval(
                button_x-8, 2, button_x+8, 18, 
                fill="#FFFFFF", outline="", 
                tags="switch_button"
            )
            # 在月亮右侧添加小缺口效果
            self.theme_canvas.create_oval(
                button_x-2, 4, button_x+6, 16, 
                fill=bg_color, outline="", 
                tags="switch_button_detail"
            )
        else:
            # 太阳图标
            self.theme_canvas.create_oval(
                button_x-8, 2, button_x+8, 18, 
                fill="#FFEB3B", outline="", 
                tags="switch_button"
            )
            # 添加太阳光芒
            for i in range(8):
                angle = i * 45
                rad = angle * 3.14159 / 180
                x1 = button_x + 9 * 0.8 * math.cos(rad)
                y1 = 10 + 9 * 0.8 * math.sin(rad)
                x2 = button_x + 14 * 0.8 * math.cos(rad)
                y2 = 10 + 14 * 0.8 * math.sin(rad)
                self.theme_canvas.create_line(
                    x1, y1, x2, y2, 
                    fill="#FFEB3B", width=2, 
                    tags="switch_button_detail"
                )
    
    def _create_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        """创建圆角矩形"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def toggle_theme_with_animation(self):
        """带动画效果的主题切换"""
        self.is_dark_mode.set(not self.is_dark_mode.get())
        
        # 更新颜色设置
        self.update_theme_colors()
        
        # 获取当前按钮位置和目标位置
        current_x = 30 if not self.is_dark_mode.get() else 10
        target_x = 10 if not self.is_dark_mode.get() else 30
        
        # 设置动画步骤
        steps = 10
        dx = (target_x - current_x) / steps
        
        # 执行动画
        self._animate_switch(current_x, dx, steps, 0)
    
    def _animate_switch(self, current_x, dx, steps, step):
        """执行开关动画的一步"""
        if step <= steps:
            # 更新按钮位置
            self.theme_canvas.delete("switch_button", "switch_button_detail")
            button_x = current_x + dx * step
            
            # 设置开关背景色，根据动画进度渐变
            progress = step / steps
            if self.is_dark_mode.get():
                # 从浅色过渡到深色
                r = int(203 + (56 - 203) * progress)
                g = int(213 + (161 - 213) * progress)
                b = int(224 + (105 - 224) * progress)
            else:
                # 从深色过渡到浅色
                r = int(56 + (203 - 56) * progress)
                g = int(161 + (213 - 161) * progress)
                b = int(105 + (224 - 105) * progress)
            bg_color = f"#{r:02x}{g:02x}{b:02x}"
            
            # 更新开关背景颜色
            self.theme_canvas.delete("switch_bg")
            self._create_rounded_rectangle(
                self.theme_canvas,
                0, 0, 40, 20, 
                radius=10, 
                fill=bg_color, 
                tags="switch_bg"
            )
            
            # 绘制图标
            if self.is_dark_mode.get():
                # 逐渐变为月亮图标
                self.theme_canvas.create_oval(
                    button_x-8, 2, button_x+8, 18, 
                    fill="#FFFFFF", outline="", 
                    tags="switch_button"
                )
                # 月亮缺口越来越明显
                detail_progress = min(1, step / (steps * 0.7))
                if detail_progress > 0:
                    self.theme_canvas.create_oval(
                        button_x-2, 4, button_x+6, 16, 
                        fill=bg_color, outline="", 
                        tags="switch_button_detail"
                    )
            else:
                # 逐渐变为太阳图标
                self.theme_canvas.create_oval(
                    button_x-8, 2, button_x+8, 18, 
                    fill="#FFEB3B", outline="", 
                    tags="switch_button"
                )
                # 太阳光芒越来越明显
                ray_progress = min(1, step / (steps * 0.7))
                if ray_progress > 0:
                    for i in range(8):
                        angle = i * 45
                        rad = angle * 3.14159 / 180
                        x1 = button_x + 9 * 0.8 * math.cos(rad)
                        y1 = 10 + 9 * 0.8 * math.sin(rad)
                        x2 = button_x + (9 + 5 * ray_progress) * 0.8 * math.cos(rad)
                        y2 = 10 + (9 + 5 * ray_progress) * 0.8 * math.sin(rad)
                        self.theme_canvas.create_line(
                            x1, y1, x2, y2, 
                            fill="#FFEB3B", width=2 * ray_progress, 
                            tags="switch_button_detail"
                        )
            
            # 继续下一步动画
            self.root.after(20, lambda: self._animate_switch(current_x, dx, steps, step + 1))
        else:
            # 动画完成，更新UI
            self.draw_theme_switch()
            self.update_ui_theme()
            
            # 保存主题设置
            self.save_config()
            
            # 更新状态
            mode_text = "深色" if self.is_dark_mode.get() else "浅色"
            self.message_queue.put(("status", f"已切换到{mode_text}模式"))

def main():
    root = tk.Tk()
    app = ChatStudio(root)
    
    # 添加设置菜单
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # 文件菜单
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="文件", menu=file_menu)
    file_menu.add_command(label="保存设置", command=app.save_config)
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=app.on_closing)
    
    # 设置菜单
    settings_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="设置", menu=settings_menu)
    settings_menu.add_command(label="云服务设置", command=app.show_cloud_settings)
    
    # 主题菜单
    theme_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="主题", menu=theme_menu)
    theme_menu.add_command(label="切换深色/浅色模式", command=app.toggle_theme_with_animation)
    theme_mode = "浅色" if not app.is_dark_mode.get() else "深色"
    theme_menu.add_command(label=f"当前模式: {theme_mode}", state="disabled")
    
    # 帮助菜单
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="帮助", menu=help_menu)
    help_menu.add_command(label="关于", command=lambda: tk.messagebox.showinfo("关于", "硅基流动 Studio\n版本 1.0\n支持多家云服务的AI助手"))
    
    # 绑定窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()
                
