#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查表格关联后的电压字段数据
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.table_linker import TableLinker

# 加载识别结果
result_path = os.path.join(os.path.dirname(__file__), 'backend', 'table_recognition_results', 'latest_recognition.json')
with open(result_path, 'r', encoding='utf-8') as f:
    recognition_result = json.load(f)

tables = recognition_result['tables']

print("="*80)
print(f"加载到 {len(tables)} 个表格")
print("="*80)

# 显示所有表格名称
print("\n表格列表:")
for idx, table in enumerate(tables, 1):
    msg_name = table.get('msg_name', '')
    if msg_name:
        print(f"  {idx}. {msg_name}")

# 找到包含电压字段的表格
for idx, table in enumerate(tables, 1):
    if '某设备装置测量数据 3' in table.get('msg_name', ''):
        print(f"\n【原始表格 {idx}】{table.get('msg_name')}")
        print(f"  Meta: {table.get('meta', {})}")
        
        voltage_row = None
        for row in table.get('data_rows', []):
            if row.get('参数') == '电压':
                voltage_row = row
                break
        
        if voltage_row:
            print(f"  电压字段原始数据:")
            for k, v in voltage_row.items():
                if v and str(v).strip():
                    print(f"    {k}: {v}")

# 执行表格关联
print("\n" + "="*80)
print("执行表格关联...")
print("="*80)

linker = TableLinker()
linked_tables = linker.link_tables(tables)

# 显示所有关联后的表格
print(f"\n关联后有 {len(linked_tables)} 个表格:")
for idx, table in enumerate(linked_tables, 1):
    msg_name = table.get('msg_name', '')
    meta_keys = list(table.get('meta', {}).keys())
    print(f"  {idx}. {msg_name} - Meta 键：{meta_keys}")

# 找到关联后的电压字段
for idx, table in enumerate(linked_tables, 1):
    if '某设备装置测量数据 3' in table.get('msg_name', ''):
        print(f"\n【关联后表格 {idx}】{table.get('msg_name')}")
        print(f"  Meta: {table.get('meta', {})}")
        
        voltage_row = None
        for row in table.get('data_rows', []):
            if row.get('参数') == '电压':
                voltage_row = row
                break
        
        if voltage_row:
            print(f"  电压字段关联后数据:")
            for k, v in voltage_row.items():
                if v and str(v).strip():
                    print(f"    {k}: {v}")
            
            # 检查是否有额外的 meta 注入到行中
            table_meta = table.get('meta', {})
            if table_meta:
                print(f"  ⚠ 表格 Meta 中有额外信息（可能被注入到行数据）:")
                for k, v in table_meta.items():
                    print(f"    {k}: {v}")
