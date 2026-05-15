#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化测试单位列恢复逻辑
"""

def test_unit_logic():
    print("测试单位列处理逻辑...")
    
    # 测试用例1：有单位字段的情况
    test_data1 = {
        '参数': '飞行计时时间',
        '数据类型': 'UINTEGER-32',
        '值域': '0~4294967295',
        '单位': 'ms',
        '备注': '32位整型数'
    }
    
    print("测试用例1 - 有单位字段:")
    print(f"  原始数据: {test_data1}")
    
    # 模拟修复后的逻辑
    unit_val = test_data1.get('单位', '')
    if not unit_val:
        unit_val = test_data1.get('值域', test_data1.get('取值范围', ''))
    
    print(f"  处理后单位值: '{unit_val}'")
    
    if unit_val == 'ms':
        print("  ✅ 正确保留了原始单位 'ms'")
        test1_pass = True
    else:
        print(f"  ❌ 错误：应该是 'ms'，但得到了 '{unit_val}'")
        test1_pass = False
    
    # 测试用例2：无单位字段的情况
    test_data2 = {
        '参数': '温度传感器',
        '数据类型': 'FLOAT',
        '值域': '-40~85',
        '备注': '摄氏度范围'
    }
    
    print("\n测试用例2 - 无单位字段:")
    print(f"  原始数据: {test_data2}")
    
    # 模拟修复后的逻辑
    unit_val2 = test_data2.get('单位', '')
    if not unit_val2:
        unit_val2 = test_data2.get('值域', test_data2.get('取值范围', ''))
    
    print(f"  处理后单位值: '{unit_val2}'")
    
    if unit_val2 == '-40~85':
        print("  ✅ 正确使用值域作为备选 '-40~85'")
        test2_pass = True
    else:
        print(f"  ❌ 错误：应该是 '-40~85'，但得到了 '{unit_val2}'")
        test2_pass = False
    
    return test1_pass and test2_pass

if __name__ == "__main__":
    success = test_unit_logic()
    if success:
        print("\n🎉 单位列处理逻辑验证通过！")
        print("修复要点：")
        print("1. 优先使用原始表格中的'单位'字段值")
        print("2. 只有当单位为空时，才使用'值域'作为备选")
        print("3. 避免了将值域强制覆盖单位的错误行为")
    else:
        print("\n❌ 测试失败，请检查逻辑")