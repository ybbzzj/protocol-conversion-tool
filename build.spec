# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
import os

# --- 收集第三方库的依赖 ---
datas, binaries, hiddenimports = collect_all('paddlenlp')
datas_paddle, binaries_paddle, hiddenimports_paddle = collect_all('paddle')
datas_openpyxl, binaries_openpyxl, hiddenimports_openpyxl = collect_all('openpyxl')

datas.extend(datas_paddle)
binaries.extend(binaries_paddle)
hiddenimports.extend(hiddenimports_paddle)

datas.extend(datas_openpyxl)
binaries.extend(binaries_openpyxl)
hiddenimports.extend(hiddenimports_openpyxl)

# --- 添加本项目自定义的资源文件 (格式: (源路径, 目标目录)) ---
added_datas = [
    ('public/dist', 'public/dist'),
    ('models', 'models'),
    ('word/csvfile', 'word/csvfile'),
    ('backend/data', 'backend/data'),
    ('backend/config_protocol_fields.json', 'backend'),
    ('backend/config_target_fields.json', 'backend'),
    ('backend/config_templates.json', 'backend'),
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
    excludes=[],
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
    console=True,
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
    upx_exclude=[],
    name='协议转换工具'
)
