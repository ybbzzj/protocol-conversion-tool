#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试 data_cleaner 的枚举值处理逻辑
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.data_cleaner import DataProcessor

def test_enum_handling():
    """测试枚举值是否会被错误地放到转换公式列"""
    print("=" * 60)
    print("测试枚举值处理")
    print("=" * 60)
    
    processor = DataProcessor()
    
    # 测试用例 1：备注中包含枚举值描述
    test_row_1 = {
        '名称': '状态信息',
        '内容': '供电状态',
        '数据类型': 'UINTEGER-16',
        '字节': '2',
        '备注': '0x1701:供电 0x1702:断电'
    }
    
    print("\n[测试用例 1]")
    print(f"输入：{test_row_1}")
    result_1 = processor.process_row(test_row_1)
    
    print(f"\n清理后数据:")
    for k, v in result_1['cleaned'].items():
        if v:
            print(f"  {k}: {v}")
    
    print(f"\n格式化后数据:")
    for k, v in result_1['formatted'].items():
        if v:
            print(f"  {k}: {v}")
    
    print(f"\n转换后数据:")
    for k, v in result_1['converted'].items():
        if v:
            print(f"  {k}: {v}")
    
    # 验证结果
    print("\n[验证结果]")
    has_error = False
    
    # 检查值域是否正确提取
    if '值域' in result_1['formatted']:
        range_val = result_1['formatted']['值域']
        print(f"✓ 值域已提取：{range_val}")
        # 验证是否是枚举格式 {...}
        if range_val.startswith('{') and range_val.endswith('}'):
            print(f"✓ 值域格式正确（枚举格式）")
        else:
            print(f"✗ 值域格式错误（应该是枚举格式）")
            has_error = True
    else:
        print(f"✗ 值域未提取")
        has_error = True
    
    # 检查转换公式是否为空（枚举值不应该放在转换公式）
    if '转换公式' in result_1['formatted']:
        formula_val = result_1['formatted']['转换公式']
        print(f"✗ 转换公式有值：{formula_val}")
        print(f"  → 错误！枚举值描述不应该被当作转换公式")
        has_error = True
    else:
        print(f"✓ 转换公式为空（正确）")
    
    # 检查备注是否保留
    if '备注' in result_1['cleaned']:
        remark_val = result_1['cleaned']['备注']
        print(f"✓ 备注已保留：{remark_val}")
    else:
        print(f"✗ 备注丢失")
        has_error = True
    
    print("\n" + "=" * 60)
    if has_error:
        print("❌ 测试失败：存在错误")
    else:
        print("✅ 测试通过：所有检查项正确")
    print("=" * 60)
    
    return not has_error


def test_more_enum_cases():
    """测试更多枚举值场景"""
    print("\n\n")
    print("=" * 60)
    print("测试更多枚举值场景")
    print("=" * 60)
    
    processor = DataProcessor()
    
    test_cases = [
        {
            'name': '十进制枚举',
            'row': {
                '内容': '设备状态',
                '备注': '5889:供电 5890:断电'
            }
        },
        {
            'name': '混合进制枚举',
            'row': {
                '内容': '运行模式',
                '备注': '0x1000:自动 0x1001:手动 2:停止'
            }
        },
        {
            'name': '带花括号的枚举',
            'row': {
                '内容': '开关状态',
                '备注': '值域:{0x1701, 0x1702}'
            }
        },
        {
            'name': '真正的转换公式',
            'row': {
                '内容': '温度值',
                '备注': '乘以 0.1'
            }
        },
        {
            'name': '范围和枚举混合',
            'row': {
                '内容': '电压状态',
                '备注': '取值范围:0~4095, 0:正常 1:异常'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试用例 {i}: {test_case['name']}]")
        row = test_case['row']
        result = processor.process_row(row)
        
        print(f"  输入备注：{row.get('备注', '')}")
        
        if '值域' in result['formatted']:
            print(f"  值域：{result['formatted']['值域']}")
        else:
            print(f"  值域：(无)")
        
        if '转换公式' in result['formatted']:
            formula = result['formatted']['转换公式']
            print(f"  转换公式：{formula}")
            # 判断是否应该放在转换公式
            if ':' in str(row.get('备注', '')):
                print(f"  ⚠️  警告：包含冒号的内容不应该在转换公式")
        else:
            print(f"  转换公式：(无)")
        
        if '单位' in result['formatted']:
            print(f"  单位：{result['formatted']['单位']}")


if __name__ == "__main__":
    success = test_enum_handling()
    test_more_enum_cases()
    
    sys.exit(0 if success else 1)
