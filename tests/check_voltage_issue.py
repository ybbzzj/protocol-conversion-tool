#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查电压字段的完整处理结果
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.services.data_cleaner import DataProcessor

# 电压字段的原始数据
voltage_row = {
    "序号": "",
    "参数": "电压",
    "数据类型": "USHORT",
    "数据长度（字节）": "2",
    "值域": "",
    "单位": "ms",
    "备注": "0~0xFFFF，实际电压/v = （模拟量采集数据/2^12）×21"
}

processor = DataProcessor()
result = processor.process_row(voltage_row)

print("="*80)
print("电压字段完整处理结果")
print("="*80)

print(f"\n原始数据:")
for k, v in voltage_row.items():
    if v and str(v).strip():
        print(f"  {k}: {v}")

print(f"\n【cleaned】清洗后:")
for k, v in result.get('cleaned', {}).items():
    if v and str(v).strip():
        print(f"  {k}: {v}")

print(f"\n【converted】标准化:")
for k, v in result.get('converted', {}).items():
    print(f"  {k}: {v}")

print(f"\n【formatted】格式化:")
for k, v in result.get('formatted', {}).items():
    if v and str(v).strip():
        print(f"  {k}: {v}")

# 检查是否有额外的元数据
print(f"\n【检查】是否有多余内容:")
all_keys = set()
for section in ['cleaned', 'converted', 'formatted']:
    all_keys.update(result.get(section, {}).keys())

suspicious_keywords = ['发起时机', '错误处理', '传输周期', '聚合式']
for key in all_keys:
    for keyword in suspicious_keywords:
        if keyword in str(key) or (isinstance(result.get('cleaned', {}).get(key), str) and keyword in result['cleaned'][key]):
            print(f"  ⚠ 发现可疑内容：{key} = {result.get('cleaned', {}).get(key)}")
