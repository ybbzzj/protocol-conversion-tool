# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs
import os
import sys
from pathlib import Path

# Python 3.8 的 dataclasses 是标准库模块，部分 PyInstaller/依赖收集逻辑会误读 __version__。
# 构建期补齐该属性，避免打包时因 AttributeError 中断。
try:
    import dataclasses as _dataclasses
    if not hasattr(_dataclasses, '__version__'):
        _dataclasses.__version__ = '0.8'
except Exception:
    pass

# --- 收集第三方库的依赖 ---
# 语义模型采用 ONNX，本体模型文件保持与 exe 分离部署
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

# 收集语义模型运行时依赖。运行时直接用 tokenizers 读取 tokenizer.json。
try:
    print("Collecting onnxruntime dependencies...")
    d, b, h = collect_all('onnxruntime')
    datas.extend(d)
    binaries.extend(b)
    hiddenimports.extend(h)
    binaries.extend(collect_dynamic_libs('onnxruntime'))
except Exception as e:
    print(f"Warning: Could not collect onnxruntime: {e}")

try:
    print("Collecting tokenizers binaries...")
    binaries.extend(collect_dynamic_libs('tokenizers'))
except Exception as e:
    print(f"Warning: Could not collect tokenizers binaries: {e}")

# .doc 转 .docx 依赖 Windows COM，仅在 Windows 打包环境收集。
if sys.platform.startswith('win'):
    print("Collecting pywin32 dependencies...")
    hiddenimports += [
        'win32com',
        'win32com.client',
        'win32com.client.gencache',
        'pythoncom',
        'pywintypes',
    ]
    for pkg in ['win32com', 'pythoncom', 'pywintypes']:
        try:
            d, b, h = collect_all(pkg)
            datas.extend(d)
            binaries.extend(b)
            hiddenimports.extend(h)
        except Exception as e:
            print(f"Warning: Could not collect {pkg}: {e}")
    try:
        binaries.extend(collect_dynamic_libs('pywin32_system32'))
    except Exception as e:
        print(f"Warning: Could not collect pywin32_system32 binaries: {e}")

# 添加更多的隐藏导入
hiddenimports += [
    'flask',
    'flask_cors',
    'docx2python',
    'python_docx',
    'rapidfuzz',
    'onnxruntime',
    'onnxruntime.capi',
    'onnxruntime.capi.onnxruntime_pybind11_state',
    'tokenizers',
    'tokenizers.models',
    'tokenizers.normalizers',
    'tokenizers.pre_tokenizers',
    'tokenizers.processors',
    'tokenizers.decoders',
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
    excludes=['transformers', 'huggingface_hub'],
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
