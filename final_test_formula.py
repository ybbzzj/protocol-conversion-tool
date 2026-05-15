#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终测试 - 只提取复杂表达式和乘以/除以 A±B"""
import sys
sys.path.insert(0, 'backend')
from backend.services.data_cleaner import DataProcessor

tests = [
    # LSB 相关 - 不提取
    ('LSB=1', ''),
    ('LSB=0.5', ''),
    ('LSB=1ms', ''),
    
    # 量化单位/分辨率 - 不提取
    ('量化单位 0.5', ''),
    ('分辨率 0.01', ''),
    
    # 乘以/除以 - 要提取
    ('乘以 10', '10x+0'),
    ('除以 100', '0.01x+0'),
    ('乘以 0.1 加 5', '0.1x+5'),
    ('除以 100 减 10', '0.01x-10'),
    
    # 复杂表达式 - 要提取
    ('(模拟量采集数据/2^12)×21', '0.00512695x+0'),
    ('(X/4096)×21', '0.00512695x+0'),
]

p = DataProcessor()
print("="*80)
print("最终测试 - 转换公式提取逻辑")
print("="*80)
print("\n只提取两种格式:")
print("  1. 复杂表达式：(X/A)×B")
print("  2. 乘以/除以 A±B\n")

all_pass = True
for text, expected in tests:
    result = p.process_row({'备注': text})
    formula = result.get('formatted', {}).get('转换公式', '')
    
    if expected == '':
        status = "✅" if formula == '' else "❌"
    else:
        status = "✅" if formula == expected else "❌"
    
    if status == "❌":
        all_pass = False
    
    print(f"{status} {text:30s} -> {formula if formula else '(空)':20s} (期望：{expected if expected else '(空)'})")

print("\n" + "="*80)
if all_pass:
    print("✅ 所有测试通过！")
else:
    print("❌ 部分测试失败")
print("="*80)
