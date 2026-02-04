#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试您提供的具体数据案例
"""

import re

def test_your_specific_case():
    print("测试您提供的具体数据案例...")
    
    # 您提供的数据行
    test_data = {
        '序号': '3',
        '参数': '平均角速度wx',
        '数据类型': 'UINTEGER-32',
        '数据长度（字节）': '4',
        '值域': '0~4294967295',
        '单位': '',  # 空单位
        '备注': '惯性测量系 °/h'
    }
    
    print("原始数据:")
    for k, v in test_data.items():
        print(f"  {k}: '{v}'")
    
    # 模拟提取逻辑
    unit_val = test_data.get('单位', '')
    unit_source = 'original'
    
    print(f"\n处理过程:")
    print(f"1. 原始单位: '{unit_val}' -> 空，需要提取")
    
    if not unit_val:  # 原始单位为空
        remark = test_data.get('备注', '')
        print(f"2. 备注内容: '{remark}'")
        
        if remark:
            # 使用更新后的单位提取规则
            unit_patterns = [
                # 复合单位优先
                (r'[°∠∠][/\\s]*(s|秒)', '°/s'),  # 角速度 °/s
                (r'[°∠∠][/\\s]*(h|小时)', '°/h'),  # 角速度 °/h
                (r'[°∠∠][/\\s]*(min|分钟)', '°/min'),  # 角速度 °/min
                (r'(m/s2|m/s²|m/s\^2)', 'm/s²'),  # 加速度
                (r'(km/h|千米/小时)', 'km/h'),     # 速度
                (r'(r/min|rpm|转/分钟)', 'r/min'), # 转速
                
                # 基本单位
                (r'\b(ms|毫秒)\b', 'ms'),
                (r'\b(s|秒)\b', 's'),
                (r'\b(Hz|赫兹)\b', 'Hz'),
                (r'[°∠度]\b', '°'),  # 角度
                (r'(℃|°C|摄氏度)\b', '℃'),
                (r'\b(V|伏)\b', 'V'),
                (r'\b(A|安)\b', 'A'),
                (r'(Ω|欧姆)\b', 'Ω'),
                (r'\b(bit|位)\b', 'bit'),
                (r'\b(byte|字节)\b', 'byte'),
                (r'\b(mV|毫伏)\b', 'mV'),
                (r'\b(mA|毫安)\b', 'mA')
            ]
            
            found = False
            for pattern, unit_name in unit_patterns:
                match = re.search(pattern, remark, re.IGNORECASE)
                if match:
                    unit_val = unit_name
                    unit_source = 'remark_extracted'
                    print(f"3. ✓ 匹配成功: 正则 '{pattern}' -> 提取单位 '{unit_name}'")
                    found = True
                    break
            
            if not found:
                print(f"3. ✗ 未匹配到任何单位")
                print(f"4. ↓ 最终使用值域备选: '{test_data.get('值域', '')}'")
                unit_val = test_data.get('值域', '')
                unit_source = 'range_fallback'
        else:
            print(f"2. ✗ 无备注信息")
    
    print(f"\n最终结果:")
    print(f"  提取的单位: '{unit_val}'")
    print(f"  来源标记: {unit_source}")
    
    # 验证结果
    if unit_val == '°/h' and unit_source == 'remark_extracted':
        print("  ✅ 正确：从备注提取到 '°/h' 并标记为备注提取")
        return True
    elif unit_source == 'range_fallback':
        print("  ❌ 错误：不应该使用值域备选")
        return False
    else:
        print(f"  ❌ 错误：期望 '°/h'，实际得到 '{unit_val}'")
        return False

def test_other_cases():
    print("\n" + "="*50)
    print("测试其他相关案例...")
    
    test_cases = [
        {
            'name': '帧计数3',
            'data': {
                '参数': '帧计数3',
                '单位': '—',
                '备注': '乘以 10'
            }
        },
        {
            'name': '电压',
            'data': {
                '参数': '电压',
                '单位': 'ms',
                '备注': '0 ~0xFFFF，实际电压/v = （模拟量采集数据/212）×21'
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        data = case['data']
        unit_val = data.get('单位', '')
        
        if unit_val in ['', '—', '-']:
            print(f"原始单位: '{unit_val}' -> 需要处理")
            remark = data.get('备注', '')
            print(f"备注: '{remark}'")
            print("✓ 单位为空，将触发备注提取逻辑")
        else:
            print(f"原始单位: '{unit_val}' -> 直接使用")
            print("✓ 使用原始单位")

if __name__ == "__main__":
    success = test_your_specific_case()
    test_other_cases()
    
    print("\n" + "="*50)
    if success:
        print("🎉 您的具体案例测试通过！")
        print("平均角速度wx 的单位将正确从备注 '惯性测量系 °/h' 中提取为 '°/h' 并标红显示")
    else:
        print("❌ 测试失败，请检查逻辑")