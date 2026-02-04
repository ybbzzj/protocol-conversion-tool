#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改进版备注单位提取测试
"""

import re

def improved_unit_extraction():
    print("改进版备注单位提取测试...")
    
    # 改进的测试用例
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
        }
    ]
    
    # 改进的单位提取规则 - 更智能的匹配顺序
    unit_patterns = [
        # 优先匹配复合单位
        (r'[°∠][/\s]*(s|秒)', '°/s'),  # 角速度单位 °/s
        (r'(m/s2|m/s²|m/s\^2)', 'm/s²'),  # 加速度单位
        (r'(km/h|千米/小时)', 'km/h'),   # 速度单位
        
        # 基本单位匹配
        (r'\b(ms|毫秒)\b', 'ms'),
        (r'\b(s|秒)\b', 's'),
        (r'\b(Hz|赫兹)\b', 'Hz'),
        (r'[°∠度]\b', '°'),  # 角度单位
        (r'(℃|°C|摄氏度)\b', '℃'),
        (r'\b(V|伏)\b', 'V'),
        (r'\b(A|安)\b', 'A'),
        (r'(Ω|欧姆)\b', 'Ω'),
        (r'\b(bit|位)\b', 'bit'),
        (r'\b(byte|字节)\b', 'byte'),
        (r'\b(mV|毫伏)\b', 'mV'),
        (r'\b(mA|毫安)\b', 'mA')
    ]
    
    print("测试改进的提取规则:")
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        data = case['data']
        remark = data.get('备注', '')
        print(f"备注: {remark}")
        
        extracted_unit = None
        
        # 按优先级顺序匹配
        for pattern, unit_name in unit_patterns:
            match = re.search(pattern, remark, re.IGNORECASE)
            if match:
                extracted_unit = unit_name
                print(f"✓ 匹配到: {pattern} -> {unit_name}")
                break
        
        if extracted_unit:
            print(f"提取结果: {extracted_unit} (红色标示)")
        else:
            print("✗ 未匹配到任何单位")
            
            # 尝试更宽松的匹配
            loose_patterns = [
                (r'度/秒|度每秒', '°/s'),
                (r'摄氏度|华氏度', '℃'),
                (r'毫米|厘米|米', 'm'),
                (r'毫秒|微秒', 's')
            ]
            
            for pattern, unit_name in loose_patterns:
                if re.search(pattern, remark):
                    extracted_unit = unit_name
                    print(f"✓ 宽松匹配: {pattern} -> {unit_name}")
                    break
            
            if not extracted_unit:
                print("↓ 使用值域备选")
                extracted_unit = data.get('值域', '')
        
        print(f"最终单位: '{extracted_unit}'")

if __name__ == "__main__":
    improved_unit_extraction()