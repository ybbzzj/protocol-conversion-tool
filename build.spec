# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules
import os
import sys
from pathlib import Path

# --- 收集第三方库的依赖 ---
# 注意：不包含 paddlepaddle 和 paddlenlp，使用基础匹配算法
print("Collecting openpyxl dependencies...")
datas_openpyxl, binaries_openpyxl, hiddenimports_openpyxl = collect_all('openpyxl')

# 手动添加 numpy 的二进制文件
try:
    import numpy
    
    numpy_path = os.path.dirname(numpy.__file__)
    print(f"Found numpy at: {numpy_path}")
    
    # 收集 numpy 的二进制文件
    numpy_datas, numpy_binaries, _ = collect_all('numpy')
    datas_openpyxl.extend(numpy_datas)
    binaries_openpyxl.extend(numpy_binaries)
    
    print(f"Added numpy binaries via collect_all")
except Exception as e:
    print(f"Warning: Could not collect numpy binaries: {e}")
    import traceback
    traceback.print_exc()

# 合并所有依赖
datas = datas_openpyxl
binaries = binaries_openpyxl
hiddenimports = hiddenimports_openpyxl

# 添加更多的隐藏导入
hiddenimports += [
    'flask',
    'flask_cors',
    'docx2python',
    'python_docx',
    'rapidfuzz',
]

# --- 添加本项目自定义的资源文件 (格式：(源路径，目标目录)) ---
# SPEC 是当前 spec 文件所在目录
if hasattr(SPEC, 'parent'):
    base_dir = str(SPEC.parent)
else:
    base_dir = os.path.dirname(os.path.abspath(SPEC)) if isinstance(SPEC, str) else os.getcwd()
    
added_datas = [
    (os.path.join(base_dir, 'public', 'dist'), 'public/dist'),
    # 注意：models 目录不打包到 exe，需要单独提供
    # (os.path.join(base_dir, 'models'), 'models'),
    (os.path.join(base_dir, 'word', 'csvfile'), 'word/csvfile'),
    (os.path.join(base_dir, 'backend', 'data'), 'backend/data'),
    (os.path.join(base_dir, 'backend', 'config_protocol_fields.json'), 'backend'),
    (os.path.join(base_dir, 'backend', 'config_target_fields.json'), 'backend'),
    (os.path.join(base_dir, 'backend', 'config_templates.json'), 'backend'),
]

datas.extend(added_datas)

# --- 定义分析目标 ---
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['paddle', 'paddlenlp'],  # 排除 paddle，避免自动打包
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# --- 定义 EXE 配置 ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='协议转换工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 保留控制台以便调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=None, # 暂时不指定图标
)

# --- 定义 COLLECT 配置 (生成文件夹模式) ---
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],  # Python 3.8 可能需要排除某些库
    name='协议转换工具'
)
