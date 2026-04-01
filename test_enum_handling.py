#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试枚举值处理和备注信息提取
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_cleaner import RangeValueFormatter, DataProcessor

def test_enum_value_formatting():
    """测试枚举值格式化"""
    print("\n[测试] 枚举值格式化")
    formatter = RangeValueFormatter()
    
    test_cases = [
        '{0x1701, 0x1702}',
        '{0x1701,0x1702}',
        '0x1701:供电 0x1702:断电',
        '{5889, 5890}',
    ]
    
    for test_input in test_cases:
        result = formatter.format_range(test_input)
        print(f"  输入: {test_input}")
        print(f"  输出: {result}")
        print()

def test_remark_extraction():
    """测试从备注中提取信息"""
    print("\n[测试] 从备注中提取信息")
    processor = DataProcessor()
    
    test_rows = [
        {
            '内容': '供电状态',
            '备注': '0x1701:供电 0x1702:断电'
        },
        {
            '内容': '设备状态',
            '备注': '值域: {0x1701, 0x1702}, 单位: ms'
        },
        {
            '内容': '温度',
            '备注': '取值范围: 0~100, 单位: ℃'
        }
    ]
    
    for i, row in enumerate(test_rows):
        print(f"\n  测试用例 {i+1}:")
        print(f"  输入: {row}")
        result = processor.process_row(row)
        print(f"  处理结果: {result}")
        print()

if __name__ == "__main__":
    test_enum_value_formatting()
    test_remark_extraction()
