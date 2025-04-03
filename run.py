#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动硅基流动应用程序的入口脚本
"""

import os
import sys

# 将当前目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 导入并启动主应用
from main import main

if __name__ == "__main__":
    # 启动应用程序
    main() 