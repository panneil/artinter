#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
硅基流动应用程序启动脚本
"""

import os
import sys

# 确保能找到当前目录中的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    # 直接导入所需模块
    import tkinter as tk
    from api_client import SilijiClient
    from baidu_client import BaiduClient
    from netease_client import NeteaseClient
    from tencent_client import TencentClient
    from aliyun_client import AliyunClient
    
    # 导入主程序中的主函数
    from main import main
    
    # 启动应用
    main() 