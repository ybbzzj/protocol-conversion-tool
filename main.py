# -*- coding: utf-8 -*-
"""
PyInstaller 打包入口文件
"""
import sys
import os
import webbrowser

# 兼容 PyInstaller 打包后的路径问题
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，则将根目录设为 exe 所在目录
    os.chdir(sys._MEIPASS)

from backend.app import create_app

# 生产模式
app = create_app('production')

if __name__ == '__main__':
    # 自动在浏览器中打开
    webbrowser.open('http://127.0.0.1:5001')
    
    # 启动服务
    app.run(host='127.0.0.1', port=5001, debug=False)
