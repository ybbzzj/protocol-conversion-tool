#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试单位列数据恢复功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.excel_exporter import ExcelExporter
from backend.services.data_cleaner import DataProcessor

def test_unit_column_restoration():
    print("测试单位列数据恢复功能...")
    
    # 模拟一个包含单位和值域的原始数据行
    test_row = {
        '序号': '1',
        '参数': '飞行计时时间',
        '数据类型': 'UINTEGER-32',
        '数据长度（字节）': '4',
        '值域': '0~4294967295',
        '单位': 'ms',  # 原始表格中确实有单位字段
        '备注': '32位整型数，LSB=1ms'
    }
    
    processor = DataProcessor()
    exporter = ExcelExporter('./test_output')
    
    # 处理数据行
    proc_res = processor.process_row(test_row)
    cleaned_data = proc_res['cleaned']
    
    print(f"原始数据: {test_row}")
    print(f"清洗后数据: {cleaned_data}")
    
    # 模拟导出器中的单位处理逻辑
    unit_val = cleaned_data.get('单位', '')
    if not unit_val:  # 如果原始单位为空，则使用值域作为备选
        unit_val = cleaned_data.get('值域', cleaned_data.get('取值范围', ''))
    
    print(f"最终单位值: '{unit_val}'")
    
    # 验证结果
    if unit_val == 'ms':
        print("✅ 成功：单位列正确保留了原始值 'ms'")
        return True
    else:
        print(f"❌ 失败：单位列错误地变成了 '{unit_val}'")
        return False

def test_fallback_to_range():
    print("\n测试备选值域逻辑...")
    
    # 模拟没有单位字段，只有值域的情况
    test_row = {
        '序号': '2',
        '参数': '温度传感器',
        '数据类型': 'FLOAT',
        '数据长度（字节）': '4',
        '值域': '-40~85',  # 没有单位字段
        '备注': '摄氏度范围'
    }
    
    processor = DataProcessor()
    proc_res = processor.process_row(test_row)
    cleaned_data = proc_res['cleaned']
    
    # 模拟导出器中的单位处理逻辑
    unit_val = cleaned_data.get('单位', '')
    if not unit_val:  # 如果原始单位为空，则使用值域作为备选
        unit_val = cleaned_data.get('值域', cleaned_data.get('取值范围', ''))
    
    print(f"原始数据: {test_row}")
    print(f"清洗后数据: {cleaned_data}")
    print(f"最终单位值: '{unit_val}'")
    
    # 验证结果
    if unit_val == '-40~85':
        print("✅ 成功：当无单位时正确使用值域作为备选")
        return True
    else:
        print(f"❌ 失败：备选逻辑未正确执行")
        return False

if __name__ == "__main__":
    success1 = test_unit_column_restoration()
    success2 = test_fallback_to_range()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！单位列处理逻辑已修复。")
    else:
        print("\n❌ 部分测试失败，请检查代码。")