#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 _classify_remark_content 函数"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.data_cleaner import DataProcessor

def test_classify(text):
    """测试分类函数"""
    p = DataProcessor()
    
    # 使用 name mangling 访问私有方法
    classify_method = getattr(p, '_DataProcessor__classify_remark_content')
    result = classify_method(text)
    
    print(f"\n输入：'{text}'")
    print("输出:")
    for k, v in result.items():
        print(f"  {k}: '{v}'")
    
    return result

if __name__ == "__main__":
    print("="*60)
    print("测试 _classify_remark_content 函数")
    print("="*60)
    
    test_cases = [
        '乘以 0.1',
        '量化单位 0.5 度',
        '分辨率 0.392157%',
        'LSB=0.1V',
        '0~65535，LSB=0.1V，单位:V',
    ]
    
    for txt in test_cases:
        test_classify(txt)
    
    print("\n" + "="*60)
