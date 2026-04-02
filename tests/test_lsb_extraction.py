#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 LSB 描述的提取
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.services.data_cleaner import DataProcessor

# 测试数据
test_row = {
    "序号": "",
    "内容": "计时时间",
    "类型": "UINTEGER-32",
    "值域": "0~4294967295",
    "单位": "ms",
    "数据处理方法": "32 位整型数，LSB=1ms，以上电为零点，软件开算时刻清零。"
}

processor = DataProcessor()
result = processor.process_row(test_row)

print("="*80)
print("LSB 描述提取测试")
print("="*80)

print(f"\n原始数据:")
for k, v in test_row.items():
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

print(f"\n【检查】备注内容:")
cleaned_remark = result.get('cleaned', {}).get('数据处理方法', '')
formatted_remark = result.get('formatted', {}).get('备注', '')
print(f"  cleaned 中的数据处理方法：{cleaned_remark}")
print(f"  formatted 中的备注：{formatted_remark}")
