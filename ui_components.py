"""
UI组件模块
提供增强的用户体验功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import pyperclip
import io
from PIL import Image, ImageTk

class PopupWindow:
    """弹出窗口类"""
    
    def __init__(self, parent, title="快速操作", width=500, height=400):
        """初始化弹出窗口"""
        self.parent = parent
        
        # 创建顶层窗口
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        self.window.resizable(True, True)
        
        # 设置模态窗口
        self.window.transient(parent)
        self.window.grab_set()
        
        # 居中显示
        self.center_window()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        
        # 获取屏幕宽度和高度
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.window.geometry(f"+{x}+{y}")
        
    def add_widget(self, widget):
        """添加组件到主框架"""
        widget.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def close(self):
        """关闭窗口"""
        self.window.destroy()


class ClipboardPopup(PopupWindow):
    """剪贴板弹出窗口"""
    
    def __init__(self, parent, callback, title="快速提问", width=600, height=500):
        """初始化剪贴板弹出窗口"""
        super().__init__(parent, title, width, height)
        self.callback = callback
        
        # 添加操作按钮
        self.create_actions()
        
        # 添加文本框
        self.create_text_area()
        
        # 添加按钮框架
        self.create_buttons()
        
        # 获取剪贴板内容
        self.get_clipboard_content()
        
    def create_actions(self):
        """创建操作按钮"""
        actions_frame = ttk.Frame(self.main_frame)
        actions_frame.pack(fill=tk.X, pady=5)
        
        # 添加操作按钮
        actions = [
            ("快速提问", self.ask_question),
            ("解释内容", self.explain_content),
            ("翻译内容", self.translate_content),
            ("总结内容", self.summarize_content)
        ]
        
        for text, command in actions:
            btn = ttk.Button(actions_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)
            
    def create_text_area(self):
        """创建文本区域"""
        # 添加标签
        ttk.Label(self.main_frame, text="剪贴板内容:").pack(anchor="w", pady=(10, 5))
        
        # 创建文本框
        self.text_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, height=15)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加提示文本框
        ttk.Label(self.main_frame, text="自定义提示 (可选):").pack(anchor="w", pady=(10, 5))
        self.prompt_entry = ttk.Entry(self.main_frame)
        self.prompt_entry.pack(fill=tk.X, pady=5)
        
    def create_buttons(self):
        """创建按钮"""
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # 取消按钮
        ttk.Button(
            buttons_frame, 
            text="取消", 
            command=self.close
        ).pack(side=tk.RIGHT, padx=5)
        
        # 提交按钮
        ttk.Button(
            buttons_frame, 
            text="提交", 
            command=self.submit
        ).pack(side=tk.RIGHT, padx=5)
        
        # 刷新按钮
        ttk.Button(
            buttons_frame, 
            text="刷新剪贴板", 
            command=self.get_clipboard_content
        ).pack(side=tk.LEFT, padx=5)
        
    def get_clipboard_content(self):
        """获取剪贴板内容"""
        try:
            content = pyperclip.paste()
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, content)
        except Exception as e:
            messagebox.showerror("错误", f"无法获取剪贴板内容: {str(e)}")
            
    def submit(self):
        """提交内容"""
        content = self.text_area.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "内容不能为空")
            return
            
        # 调用回调函数
        self.callback(content)
        self.close()
        
    def ask_question(self):
        """快速提问"""
        content = self.text_area.get(1.0, tk.END).strip()
        prompt = self.prompt_entry.get().strip()
        
        if not content:
            messagebox.showwarning("警告", "内容不能为空")
            return
            
        full_prompt = f"{prompt + ': ' if prompt else ''}请回答这个问题: {content}"
        self.callback(full_prompt)
        self.close()
        
    def explain_content(self):
        """解释内容"""
        content = self.text_area.get(1.0, tk.END).strip()
        prompt = self.prompt_entry.get().strip()
        
        if not content:
            messagebox.showwarning("警告", "内容不能为空")
            return
            
        full_prompt = f"{prompt + ': ' if prompt else ''}请解释以下内容: {content}"
        self.callback(full_prompt)
        self.close()
        
    def translate_content(self):
        """翻译内容"""
        content = self.text_area.get(1.0, tk.END).strip()
        prompt = self.prompt_entry.get().strip() or "中文"
        
        if not content:
            messagebox.showwarning("警告", "内容不能为空")
            return
            
        full_prompt = f"请将以下内容翻译为{prompt}: {content}"
        self.callback(full_prompt)
        self.close()
        
    def summarize_content(self):
        """总结内容"""
        content = self.text_area.get(1.0, tk.END).strip()
        prompt = self.prompt_entry.get().strip()
        
        if not content:
            messagebox.showwarning("警告", "内容不能为空")
            return
            
        full_prompt = f"{prompt + ': ' if prompt else ''}请总结以下内容: {content}"
        self.callback(full_prompt)
        self.close()


class ModelComparisonWindow(PopupWindow):
    """模型比较窗口"""
    
    def __init__(self, parent, models, submit_callback, title="模型比较", width=800, height=600):
        """初始化模型比较窗口"""
        super().__init__(parent, title, width, height)
        self.models = models
        self.submit_callback = submit_callback
        
        # 创建内容区域
        self.create_content_area()
        
    def create_content_area(self):
        """创建内容区域"""
        # 添加提示标签
        ttk.Label(self.main_frame, text="输入问题或提示:").pack(anchor="w", pady=(10, 5))
        
        # 创建输入框
        self.prompt_text = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, height=5)
        self.prompt_text.pack(fill=tk.X, pady=5)
        
        # 创建模型选择区域
        self.create_model_selection()
        
        # 添加按钮
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # 取消按钮
        ttk.Button(
            buttons_frame, 
            text="取消", 
            command=self.close
        ).pack(side=tk.RIGHT, padx=5)
        
        # 提交按钮
        ttk.Button(
            buttons_frame, 
            text="比较", 
            command=self.submit
        ).pack(side=tk.RIGHT, padx=5)
        
    def create_model_selection(self):
        """创建模型选择区域"""
        # 添加标签
        ttk.Label(self.main_frame, text="选择要比较的模型:").pack(anchor="w", pady=(10, 5))
        
        # 创建模型选择框架
        models_frame = ttk.Frame(self.main_frame)
        models_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建左右两列
        left_frame = ttk.Frame(models_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(models_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 添加复选框
        self.model_vars = {}
        
        for i, (model_id, model_name) in enumerate(self.models.items()):
            # 根据索引决定放在左边还是右边
            parent = left_frame if i % 2 == 0 else right_frame
            
            # 创建变量
            var = tk.BooleanVar(value=True if i < 3 else False)  # 默认选择前三个
            self.model_vars[model_id] = var
            
            # 创建复选框
            cb = ttk.Checkbutton(
                parent, 
                text=model_name,
                variable=var
            )
            cb.pack(anchor="w", pady=2)
            
    def submit(self):
        """提交比较请求"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showwarning("警告", "提示内容不能为空")
            return
            
        # 获取选择的模型
        selected_models = [
            model_id for model_id, var in self.model_vars.items() 
            if var.get()
        ]
        
        if not selected_models:
            messagebox.showwarning("警告", "请至少选择一个模型")
            return
            
        # 调用回调函数
        self.submit_callback(prompt, selected_models)
        self.close()


class DraggableWidget(ttk.Frame):
    """可拖动的组件"""
    
    def __init__(self, parent, title, content, on_drag=None, on_drop=None):
        """初始化可拖动组件"""
        super().__init__(parent)
        self.title = title
        self.content = content
        self.on_drag = on_drag
        self.on_drop = on_drop
        
        # 创建内容
        self.create_widgets()
        
        # 绑定拖动事件
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_motion)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        # 为所有子组件也绑定拖动事件
        for child in self.winfo_children():
            child.bind("<ButtonPress-1>", self.on_press)
            child.bind("<B1-Motion>", self.on_motion)
            child.bind("<ButtonRelease-1>", self.on_release)
            
    def create_widgets(self):
        """创建组件内容"""
        # 标题栏
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 标题
        ttk.Label(title_frame, text=self.title).pack(side=tk.LEFT)
        
        # 内容
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 内容标签
        ttk.Label(content_frame, text=self.content, wraplength=300).pack(fill=tk.BOTH, expand=True)
        
    def on_press(self, event):
        """按下鼠标时记录位置"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 调用拖动回调
        if self.on_drag:
            self.on_drag(self)
            
    def on_motion(self, event):
        """移动鼠标时跟随移动"""
        # 计算偏移量
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        
        # 获取当前位置
        x, y = self.winfo_x(), self.winfo_y()
        
        # 移动组件
        self.place(x=x+dx, y=y+dy)
        
    def on_release(self, event):
        """释放鼠标时停止移动"""
        # 调用放下回调
        if self.on_drop:
            self.on_drop(self)


class TransparentWindow(tk.Toplevel):
    """透明窗口"""
    
    def __init__(self, parent, alpha=0.8):
        """初始化透明窗口"""
        super().__init__(parent)
        
        # 设置透明度
        self.attributes("-alpha", alpha)
        
        # 去掉标题栏
        self.overrideredirect(True)
        
        # 将窗口置顶
        self.attributes("-topmost", True)
        
        # 绑定事件
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.on_motion)
        
    def start_move(self, event):
        """开始移动窗口"""
        self.x = event.x
        self.y = event.y
        
    def stop_move(self, event):
        """停止移动窗口"""
        self.x = None
        self.y = None
        
    def on_motion(self, event):
        """移动窗口"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")


class CodeSyntaxHighlighter:
    """代码语法高亮"""
    
    def __init__(self, text_widget):
        """初始化语法高亮器"""
        self.text_widget = text_widget
        
        # 定义标签
        self.text_widget.tag_configure("keyword", foreground="#569CD6")
        self.text_widget.tag_configure("string", foreground="#CE9178")
        self.text_widget.tag_configure("comment", foreground="#6A9955")
        self.text_widget.tag_configure("function", foreground="#DCDCAA")
        self.text_widget.tag_configure("class", foreground="#4EC9B0")
        self.text_widget.tag_configure("number", foreground="#B5CEA8")
        
        # 定义关键字
        self.python_keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del", "elif",
            "else", "except", "False", "finally", "for", "from", "global", "if", "import",
            "in", "is", "lambda", "None", "nonlocal", "not", "or", "pass", "raise",
            "return", "True", "try", "while", "with", "yield"
        ]
        
        # 绑定事件
        self.text_widget.bind("<<Modified>>", self.highlight)
        
    def highlight(self, event=None):
        """高亮显示文本"""
        # 防止递归调用
        if self.text_widget.tag_ranges("keyword"):
            return
            
        # 获取文本内容
        content = self.text_widget.get("1.0", "end-1c")
        
        # 移除所有标签
        for tag in ["keyword", "string", "comment", "function", "class", "number"]:
            self.text_widget.tag_remove(tag, "1.0", "end")
            
        # 高亮关键字
        for keyword in self.python_keywords:
            start_index = "1.0"
            while True:
                start_index = self.text_widget.search(r'\y' + keyword + r'\y', start_index, "end", regexp=True)
                if not start_index:
                    break
                    
                end_index = f"{start_index}+{len(keyword)}c"
                self.text_widget.tag_add("keyword", start_index, end_index)
                start_index = end_index
                
        # 高亮字符串（单引号和双引号）
        for quote in ['"', "'"]:
            start_index = "1.0"
            while True:
                start_index = self.text_widget.search(quote, start_index, "end")
                if not start_index:
                    break
                    
                # 查找下一个引号
                end_index = self.text_widget.search(quote, f"{start_index}+1c", "end")
                if not end_index:
                    break
                    
                # 高亮
                end_index = f"{end_index}+1c"
                self.text_widget.tag_add("string", start_index, end_index)
                start_index = end_index
                
        # 高亮注释
        start_index = "1.0"
        while True:
            start_index = self.text_widget.search('#', start_index, "end")
            if not start_index:
                break
                
            # 查找行尾
            line = self.text_widget.index(start_index).split('.')[0]
            end_index = f"{line}.end"
            
            # 高亮
            self.text_widget.tag_add("comment", start_index, end_index)
            start_index = f"{line}.end+1c"
            
        # 高亮函数调用
        function_pattern = r'\w+\('
        start_index = "1.0"
        while True:
            start_index = self.text_widget.search(function_pattern, start_index, "end", regexp=True)
            if not start_index:
                break
                
            # 获取函数名
            func_end = self.text_widget.search('(', start_index, f"{start_index}+20c")
            if not func_end:
                break
                
            # 高亮
            self.text_widget.tag_add("function", start_index, func_end)
            start_index = func_end
            
        # 高亮类定义
        class_pattern = r'class\s+\w+'
        start_index = "1.0"
        while True:
            start_index = self.text_widget.search(class_pattern, start_index, "end", regexp=True)
            if not start_index:
                break
                
            # 找到"class"后的第一个空格
            space_index = self.text_widget.search(r'\s', start_index, f"{start_index}+10c", regexp=True)
            if not space_index:
                break
                
            # 找到类名结束
            end_index = self.text_widget.search(r'[\s:({]', f"{space_index}+1c", f"{space_index}+30c", regexp=True)
            if not end_index:
                end_index = f"{start_index}+20c"
                
            # 高亮类名
            self.text_widget.tag_add("class", f"{space_index}+1c", end_index)
            start_index = end_index
            
        # 高亮数字
        number_pattern = r'\d+'
        start_index = "1.0"
        while True:
            start_index = self.text_widget.search(number_pattern, start_index, "end", regexp=True)
            if not start_index:
                break
                
            # 获取数字结束位置
            end_index = f"{start_index}+{len(self.text_widget.get(start_index, f'{start_index} lineend'))}c"
            
            # 高亮
            self.text_widget.tag_add("number", start_index, end_index)
            start_index = end_index


class MermaidRenderer:
    """Mermaid图表渲染器"""
    
    def __init__(self, text_widget):
        """初始化渲染器"""
        self.text_widget = text_widget
        
        # 定义标签
        self.text_widget.tag_configure("mermaid", background="#f0f0f0")
        
        # 查找Mermaid代码块
        self.scan_for_mermaid_blocks()
        
    def scan_for_mermaid_blocks(self):
        """扫描Mermaid代码块"""
        content = self.text_widget.get("1.0", "end-1c")
        
        # 查找Mermaid代码块
        import re
        pattern = r'```mermaid\n([\s\S]*?)```'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            start_index = f"1.0+{match.start()}c"
            end_index = f"1.0+{match.end()}c"
            
            # 高亮Mermaid代码块
            self.text_widget.tag_add("mermaid", start_index, end_index)
            
            # 在代码块旁边添加"渲染"按钮
            self.add_render_button(match.group(1), start_index)
            
    def add_render_button(self, mermaid_code, position):
        """添加渲染按钮"""
        # 创建按钮
        button = ttk.Button(
            self.text_widget, 
            text="渲染", 
            command=lambda: self.render_mermaid(mermaid_code)
        )
        
        # 将按钮嵌入到文本中
        self.text_widget.window_create(position, window=button)
        
    def render_mermaid(self, mermaid_code):
        """渲染Mermaid代码"""
        # 创建弹出窗口用于显示图表
        # 注意：这里只是模拟，实际渲染需要使用JavaScript或其他工具
        popup = PopupWindow(self.text_widget, "Mermaid图表预览")
        
        # 显示代码
        code_text = scrolledtext.ScrolledText(popup.main_frame, height=10)
        code_text.insert("1.0", mermaid_code)
        code_text.pack(fill=tk.X, pady=10)
        
        # 显示提示
        ttk.Label(
            popup.main_frame, 
            text="实际应用中，这里会显示渲染后的图表。\n需要结合JavaScript或其他工具实现。"
        ).pack(pady=10) 