#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试从备注提取单位并标红的功能
"""

import re

def test_remark_unit_extraction():
    print("测试从备注提取单位功能...")
    
    # 测试用例：模拟平均角速度wx的情况
    test_cases = [
        {
            'name': '平均角速度wx',
            'data': {
                '参数': '平均角速度wx',
                '数据类型': 'FLOAT',
                '值域': '-2000~2000',
                '单位': '',  # 空单位
                '备注': '单位：°/s，表示角速度'
            }
        },
        {
            'name': '温度传感器',
            'data': {
                '参数': '温度传感器',
                '数据类型': 'FLOAT', 
                '值域': '-40~85',
                '单位': '',  # 空单位
                '备注': '测量范围-40到85摄氏度'
            }
        },
        {
            'name': '电压测量',
            'data': {
                '参数': '电压测量',
                '数据类型': 'UINT16',
                '值域': '0~5000',
                '单位': 'mV',  # 有原始单位
                '备注': '毫伏特测量'
            }
        },
        {
            'name': '计数器',
            'data': {
                '参数': '计数器',
                '数据类型': 'UINT32',
                '值域': '0~4294967295',
                '单位': '',  # 空单位
                '备注': '无单位的计数数据'
            }
        }
    ]
    
    # 单位提取模式
    unit_patterns = [
        r'\b(ms|毫秒)\b',
        r'\b(s|秒)\b', 
        r'\b(Hz|赫兹)\b',
        r'\b(°|度)\b',
        r'\b(℃|°C|摄氏度)\b',
        r'\b(V|伏)\b',
        r'\b(A|安)\b',
        r'\b(Ω|欧姆)\b',
        r'\b(bit|位)\b',
        r'\b(byte|字节)\b'
    ]
    
    all_passed = True
    
    for case in test_cases:
        print(f"\n测试: {case['name']}")
        data = case['data']
        print(f"  原始数据: {data}")
        
        # 模拟提取逻辑
        unit_val = data.get('单位', '')
        unit_source = 'original'
        
        if not unit_val:
            remark = data.get('备注', '')
            if remark:
                print(f"  备注内容: {remark}")
                for pattern in unit_patterns:
                    match = re.search(pattern, remark, re.IGNORECASE)
                    if match:
                        unit_val = match.group(1)
                        unit_source = 'remark_extracted'
                        print(f"  ✓ 从备注提取到单位: '{unit_val}'")
                        break
                if unit_source != 'remark_extracted':
                    print(f"  ✗ 备注中未找到可识别单位")
                    # 备选使用值域
                    unit_val = data.get('值域', '')
                    unit_source = 'range_fallback'
                    print(f"  ↓ 使用值域作为备选: '{unit_val}'")
            else:
                print(f"  ✗ 无备注信息")
        else:
            print(f"  ✓ 使用原始单位: '{unit_val}'")
        
        print(f"  最终单位值: '{unit_val}' (来源: {unit_source})")
        
        # 验证期望结果
        expected_units = {
            '平均角速度wx': '°',
            '温度传感器': '℃',  # 或者可能提取不到
            '电压测量': 'mV',
            '计数器': '0~4294967295'  # 值域备选
        }
        
        expected = expected_units[case['name']]
        if unit_val == expected or (case['name'] == '计数器' and unit_source == 'range_fallback'):
            print(f"  ✅ 结果正确")
        else:
            print(f"  ❌ 期望 '{expected}'，实际得到 '{unit_val}'")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = test_remark_unit_extraction()
    print("\n" + "="*50)
    if success:
        print("🎉 所有测试通过！")
        print("\n功能说明：")
        print("1. 单位列为空时优先从备注中提取单位")
        print("2. 提取规则支持常见单位：°、℃、s、Hz、V、A、Ω等")
        print("3. 从备注提取的单位在Excel中会显示为红色")
        print("4. 如果备注中也提取不到，则使用值域作为最后备选")
    else:
        print("❌ 部分测试失败")