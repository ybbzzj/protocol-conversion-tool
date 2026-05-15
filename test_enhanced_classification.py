#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版的智能分类功能
- 枚举值识别（十六进制和十进制）
- 文字描述转单位
- 多位置兼容（备注、值域、单位列）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.data_cleaner import DataProcessor

def test_enum_extraction():
    """测试枚举值提取"""
    print("="*80)
    print("测试 1: 枚举值提取")
    print("="*80)
    
    test_cases = [
        # (输入，期望输出)
        ("0x1701:供电 0x1702:断电", "{5889, 5890}"),
        ("0:停止 1:运行 2:待机", "{0, 1, 2}"),
        ("高电平：1，低电平：0", "{1, 0}"),
        ("0x00:OFF 0x01:ON", "{0, 1}"),
    ]
    
    p = DataProcessor()
    
    for input_txt, expected in test_cases:
        result = p._extract_enum_from_description(input_txt)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} Input: '{input_txt}'")
        print(f"   Expected: {expected}")
        print(f"   Actual: {result}")
        print()

def test_unit_extraction():
    """测试单位从文字中提取"""
    print("="*80)
    print("测试 2: 文字描述提取单位")
    print("="*80)
    
    test_cases = [
        ("温度 (摄氏度)", "℃"),
        ("电压 [伏特]", "V"),
        ("时间（毫秒）", "ms"),
        ("频率 (Hz)", "Hz"),
        ("电流（安培）", "A"),
    ]
    
    p = DataProcessor()
    
    for input_txt, expected in test_cases:
        result = p._extract_unit_from_text(input_txt)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} Input: '{input_txt}'")
        print(f"   Expected: {expected}")
        print(f"   Actual: {result}")
        print()

def test_full_classification():
    """测试完整的智能分类"""
    print("="*80)
    print("测试 3: 完整智能分类")
    print("="*80)
    
    test_cases = [
        {
            'name': '十六进制枚举在备注',
            'input': {'内容': '状态', '备注': '0x1701:供电 0x1702:断电'},
            'expected': {'值域': '{5889, 5890}', '备注': '0x1701:供电 0x1702:断电'}
        },
        {
            'name': '十进制枚举在备注',
            'input': {'内容': '状态', '备注': '0:停止 1:运行 2:待机'},
            'expected': {'值域': '{0, 1, 2}', '备注': '0:停止 1:运行 2:待机'}
        },
        {
            'name': '文字单位在括号',
            'input': {'内容': '温度', '备注': '环境温度 (摄氏度)'},
            'expected': {'单位': '℃', '备注': '环境温度'}
        },
        {
            'name': '混合内容',
            'input': {'内容': '电压', '备注': '0~4095，单位：V，分辨率 0.001'},
            'expected': {'值域': '[0, 4095]', '单位': 'V', '转换公式': '0.001x+0'}
        },
    ]
    
    p = DataProcessor()
    
    for case in test_cases:
        print(f"\n测试：{case['name']}")
        result = p.process_row(case['input'])
        
        print(f"  输入备注：{case['input']['备注']}")
        print(f"  期望结果:")
        for k, v in case['expected'].items():
            print(f"    {k}: {v}")
        
        print(f"  实际结果:")
        for k in ['值域', '单位', '转换公式', '备注']:
            actual = result['formatted'].get(k) or result['cleaned'].get(k)
            if actual:
                print(f"    {k}: {actual}")
        
        # 简单验证
        all_pass = True
        for k, exp_v in case['expected'].items():
            act_v = result['formatted'].get(k) or result['cleaned'].get(k)
            if exp_v not in str(act_v):
                all_pass = False
        
        if all_pass:
            print("  [PASS]")
        else:
            print("  [FAIL]")
        print()

if __name__ == "__main__":
    try:
        test_enum_extraction()
        test_unit_extraction()
        test_full_classification()
        
        print("\n" + "="*80)
        print("All tests completed!")
        print("="*80)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
