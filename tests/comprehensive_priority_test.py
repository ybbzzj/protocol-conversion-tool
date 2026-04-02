#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合优先级测试 - 测试单位、值域、转换公式、备注之间的优先级关系
覆盖场景：
1. 多个字段都有内容时的优先级
2. 混合文本的提取顺序
3. 冲突处理（同一信息在不同列）
4. 边界情况
"""
import sys
import os
# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.data_cleaner import DataProcessor


def test_priority_order():
    """测试优先级顺序：值域 > 单位 > 转换公式 > 备注"""
    print("="*80)
    print("测试组 1: 优先级顺序")
    print("="*80)
    
    test_cases = [
        {
            'name': '值域优先于备注',
            'input': {'值域': '0~100', '备注': '范围是 0 到 100'},
            'expected': {'值域': '[0, 100]', '备注': '范围是 0 到 100'}
        },
        {
            'name': '单位优先于备注',
            'input': {'单位': 'V', '备注': '单位是伏特'},
            'expected': {'单位': 'V', '备注': '单位是伏特'}
        },
        {
            'name': '转换公式优先于备注',
            'input': {'转换公式': '0.1x+0', '备注': '乘以 0.1'},
            'expected': {'转换公式': '0.1x+0', '备注': '乘以 0.1'}
        },
        {
            'name': '值域列优先于备注中的范围描述',
            'input': {'值域': '[0,255]', '备注': '0~255'},
            'expected': {'值域': '[0,255]'}  # 备注不应再包含范围
        },
        {
            'name': '单位列优先于备注中的单位描述',
            'input': {'单位': '℃', '备注': '温度 (摄氏度)'},
            'expected': {'单位': '℃'}  # 备注可能还保留原文
        },
    ]
    
    p = DataProcessor()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}.{case['name']}")
        result = p.process_row(case['input'])
        
        print(f"  输入:")
        for k, v in case['input'].items():
            print(f"    {k}: {v}")
        
        print(f"  期望:")
        for k, v in case['expected'].items():
            print(f"    {k}: {v}")
        
        print(f"  实际:")
        for k in ['值域', '单位', '转换公式', '备注']:
            v = result['formatted'].get(k) or result['cleaned'].get(k)
            if v:
                print(f"    {k}: {v}")
        
        # 验证关键字段
        all_pass = True
        for k, exp_v in case['expected'].items():
            act_v = result['formatted'].get(k) or result['cleaned'].get(k)
            if exp_v not in str(act_v):
                all_pass = False
        
        print(f"  [{'PASS' if all_pass else 'FAIL'}]")


def test_mixed_text_extraction():
    """测试混合文本提取"""
    print("\n" + "="*80)
    print("测试组 2: 混合文本提取")
    print("="*80)
    
    test_cases = [
        {
            'name': '备注中包含值域 + 单位',
            'input': {'备注': '0~4095，单位 V'},
            'expected': {'值域': '[0,4095]', '单位': 'V'}
        },
        {
            'name': '备注中包含值域 + 单位 + 公式',
            'input': {'备注': '0~65535，LSB=0.1V'},
            'expected': {'值域': '[0,65535]', '单位': 'V', '转换公式': '0.1x+0'}
        },
        {
            'name': '备注中包含枚举 + 单位',
            'input': {'备注': '0x00:低 0x01:高，单位 V'},
            'expected': {'值域': '{0,1}', '单位': 'V'}
        },
        {
            'name': '备注中包含范围 + 公式 + 文字',
            'input': {'备注': '范围 -40~125，乘以 0.1，工作温度'},
            'expected': {'值域': '[-40,125]', '转换公式': '0.1x+0', '备注': '工作温度'}
        },
        {
            'name': '值域列有范围，备注也有范围',
            'input': {'值域': '0-100', '备注': '范围 0~100，单位 V'},
            'expected': {'值域': '[0,100]', '单位': 'V'}
        },
        {
            'name': '多列都有单位',
            'input': {'单位': 'V', '备注': '电压 (伏特)'},
            'expected': {'单位': 'V'}  # 应该统一为 V
        },
        {
            'name': '转换公式在不同列',
            'input': {'转换公式': '0.1x+0', '备注': '乘以 0.1'},
            'expected': {'转换公式': '0.1x+0'}  # 保持原公式
        },
    ]
    
    p = DataProcessor()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}.{case['name']}")
        result = p.process_row(case['input'])
        
        print(f"  输入备注：{case['input'].get('备注', '')}")
        print(f"  期望结果:")
        for k, v in case['expected'].items():
            print(f"    {k}: {v}")
        
        print(f"  实际结果:")
        for k in ['值域', '单位', '转换公式', '备注']:
            v = result['formatted'].get(k) or result['cleaned'].get(k)
            if v:
                print(f"    {k}: {v}")
        
        # 验证
        all_pass = True
        for k, exp_v in case['expected'].items():
            act_v = result['formatted'].get(k) or result['cleaned'].get(k)
            if exp_v not in str(act_v):
                all_pass = False
        
        print(f"  [{'PASS' if all_pass else 'FAIL'}]")


def test_conflict_resolution():
    """测试冲突处理"""
    print("\n" + "="*80)
    print("测试组 3: 冲突处理")
    print("="*80)
    
    test_cases = [
        {
            'name': '值域列和备注列范围不一致',
            'input': {'值域': '0~100', '备注': '实际范围 0~255'},
            'expected': {'值域': '[0,100]'}  # 以值域列为准
        },
        {
            'name': '单位列和备注列单位不一致',
            'input': {'单位': 'V', '备注': '单位 mV'},
            'expected': {'单位': 'V'}  # 以单位列为准
        },
        {
            'name': '备注中有两个范围描述',
            'input': {'备注': '0~100 或 0~255'},
            'expected': {'值域': '[0,100]'}  # 提取第一个
        },
        {
            'name': '十六进制和十进制混用',
            'input': {'备注': '0x00:OFF(0), 0x01:ON(1)'},
            'expected': {'值域': '{0,1}'}  # 统一为十进制
        },
    ]
    
    p = DataProcessor()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}.{case['name']}")
        result = p.process_row(case['input'])
        
        print(f"  输入:")
        for k, v in case['input'].items():
            print(f"    {k}: {v}")
        
        print(f"  期望:")
        for k, v in case['expected'].items():
            print(f"    {k}: {v}")
        
        print(f"  实际:")
        for k in ['值域', '单位', '转换公式', '备注']:
            v = result['formatted'].get(k) or result['cleaned'].get(k)
            if v:
                print(f"    {k}: {v}")
        
        # 验证
        all_pass = True
        for k, exp_v in case['expected'].items():
            act_v = result['formatted'].get(k) or result['cleaned'].get(k)
            if exp_v not in str(act_v):
                all_pass = False
        
        print(f"  [{'PASS' if all_pass else 'FAIL'}]")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*80)
    print("测试组 4: 边界情况")
    print("="*80)
    
    test_cases = [
        {
            'name': '空值处理',
            'input': {'备注': ''},
            'expected': {}
        },
        {
            'name': 'None 值处理',
            'input': {'备注': None},
            'expected': {}
        },
        {
            'name': '特殊字符',
            'input': {'备注': '—'},
            'expected': {}
        },
        {
            'name': '单个字符',
            'input': {'备注': 'V'},
            'expected': {'单位': 'V'}
        },
        {
            'name': '负数范围',
            'input': {'备注': '-40~85'},
            'expected': {'值域': '[-40,85]'}
        },
        {
            'name': '小数范围',
            'input': {'备注': '0.0~5.0V'},
            'expected': {'值域': '[0.0,5.0]', '单位': 'V'}
        },
        {
            'name': '百分比单位',
            'input': {'备注': '分辨率 0.392157%'},
            'expected': {'转换公式': '0.392157x+0'}  # %不作为单位
        },
        {
            'name': '复合单位',
            'input': {'备注': '速度 (m/s)'},
            'expected': {'单位': 'm/s'}
        },
    ]
    
    p = DataProcessor()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}.{case['name']}")
        try:
            result = p.process_row(case['input'])
            
            print(f"  输入：{case['input']}")
            print(f"  期望：{case['expected']}")
            
            print(f"  实际:")
            for k in ['值域', '单位', '转换公式', '备注']:
                v = result['formatted'].get(k) or result['cleaned'].get(k)
                if v:
                    print(f"    {k}: {v}")
            
            # 简单验证
            if not case['expected']:
                has_content = any([
                    result['formatted'].get('值域'),
                    result['formatted'].get('单位'),
                    result['formatted'].get('转换公式'),
                    result['cleaned'].get('备注')
                ])
                all_pass = not has_content
            else:
                all_pass = True
                for k, exp_v in case['expected'].items():
                    act_v = result['formatted'].get(k) or result['cleaned'].get(k)
                    if exp_v not in str(act_v):
                        all_pass = False
            
            print(f"  [{'PASS' if all_pass else 'FAIL'}]")
        except Exception as e:
            print(f"  [ERROR] {e}")


def test_real_world_scenarios():
    """测试真实场景"""
    print("\n" + "="*80)
    print("测试组 5: 真实场景")
    print("="*80)
    
    test_cases = [
        {
            'name': 'CAN 总线信号',
            'input': {
                '名称': '车速信号',
                '内容': '车辆行驶速度',
                '数据类型': 'UINTEGER-16',
                '备注': '0~65535，LSB=0.01km/h，单位 km/h'
            },
            'expected': {
                '值域': '[0,65535]',
                '单位': 'km/h',
                '转换公式': '0.01x+0'
            }
        },
        {
            'name': '温度传感器',
            'input': {
                '名称': '环境温度',
                '内容': '工作温度范围',
                '数据类型': 'INTEGER-16',
                '备注': '-40~125 摄氏度，分辨率 0.1℃'
            },
            'expected': {
                '值域': '[-40,125]',
                '单位': '℃',
                '转换公式': '0.1x+0'
            }
        },
        {
            'name': '开关状态',
            'input': {
                '名称': '主继电器',
                '内容': '继电器控制',
                '数据类型': 'UINTEGER-8',
                '备注': '0x00:断开 0x01:闭合'
            },
            'expected': {
                '值域': '{0,1}'
            }
        },
        {
            'name': 'PWM 占空比',
            'input': {
                '名称': '风扇控制',
                '内容': 'PWM 占空比',
                '数据类型': 'UINTEGER-8',
                '备注': '0~255 对应 0%~100%，分辨率 0.392157%'
            },
            'expected': {
                '值域': '[0,255]',
                '转换公式': '0.392157x+0'
            }
        },
        {
            'name': 'ADC 采样',
            'input': {
                '名称': '电池电压',
                '内容': 'ADC 采样值',
                '数据类型': 'UINTEGER-12',
                '备注': '0~4095，乘以 0.00122，单位 V'
            },
            'expected': {
                '值域': '[0,4095]',
                '单位': 'V',
                '转换公式': '0.00122x+0'
            }
        },
    ]
    
    p = DataProcessor()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}.{case['name']}")
        result = p.process_row(case['input'])
        
        print(f"  输入备注：{case['input']['备注']}")
        print(f"  期望结果:")
        for k, v in case['expected'].items():
            print(f"    {k}: {v}")
        
        print(f"  实际结果:")
        for k in ['值域', '单位', '转换公式', '备注']:
            v = result['formatted'].get(k) or result['cleaned'].get(k)
            if v:
                print(f"    {k}: {v}")
        
        # 验证关键字段
        all_pass = True
        for k, exp_v in case['expected'].items():
            act_v = result['formatted'].get(k) or result['cleaned'].get(k)
            if exp_v and exp_v not in str(act_v):
                all_pass = False
        
        print(f"  [{'PASS' if all_pass else 'FAIL'}]")


if __name__ == "__main__":
    try:
        print("="*80)
        print("综合优先级测试开始")
        print("="*80)
        
        test_priority_order()
        test_mixed_text_extraction()
        test_conflict_resolution()
        test_edge_cases()
        test_real_world_scenarios()
        
        print("\n" + "="*80)
        print("所有测试完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败：{e}")
        import traceback
        traceback.print_exc()
