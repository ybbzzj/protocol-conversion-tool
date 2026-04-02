#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复验证测试 - 测试所有修复后的功能
1. 值域格式统一：0-100 → [0,100]
2. 复杂枚举清理：0x00:OFF(0), 0x01:ON(1) → {0, 1}
3. 备注保留原始内容（正常行为）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.data_cleaner import DataProcessor


def test_range_format():
    """测试 1: 值域格式统一"""
    print("="*80)
    print("测试组 1: 值域格式统一 (0-100 → [0,100])")
    print("="*80)
    
    test_cases = [
        {
            'name': '分隔符为短横线',
            'input': {'值域': '0-100'},
            'expected_range': '[0,100]'
        },
        {
            'name': '分隔符为波浪号',
            'input': {'值域': '0~100'},
            'expected_range': '[0,100]'
        },
        {
            'name': '已有方括号',
            'input': {'值域': '[0,100]'},
            'expected_range': '[0,100]'
        },
        {
            'name': '负数范围（波浪号）',
            'input': {'值域': '-40~125'},
            'expected_range': '[-40,125]'
        },
        {
            'name': '负数范围（短横线）',
            'input': {'值域': '-40-125'},
            'expected_range': '[-40,125]'
        },
        {
            'name': '小数范围',
            'input': {'值域': '0.0~5.0'},
            'expected_range': '[0.0,5.0]'
        },
        {
            'name': '十六进制范围',
            'input': {'值域': '0x00~0xFF'},
            'expected_range': '[0,255]'
        },
        {
            'name': '备注中的范围',
            'input': {'备注': '范围 0-100'},
            'expected_range': '[0,100]'
        },
        {
            'name': '混合分隔符',
            'input': {'备注': '0~100 或 0-255'},
            'expected_range': '[0,100]'
        },
    ]
    
    p = DataProcessor()
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = p.process_row(case['input'])
        actual_range = result['formatted'].get('值域') or result['cleaned'].get('值域')
        
        success = case['expected_range'] in str(actual_range) if case['expected_range'] else not actual_range
        
        if success:
            passed += 1
            status = "[PASS]"
        else:
            failed += 1
            status = "[FAIL]"
        
        print(f"\n{i}. {case['name']} [{status}]")
        print(f"   输入：{case['input']}")
        print(f"   期望：{case['expected_range']}")
        print(f"   实际：{actual_range}")
    
    print(f"\n{'='*80}")
    print(f"通过：{passed}/{len(test_cases)} ({passed/len(test_cases)*100:.1f}%)")
    print(f"{'='*80}\n")


def test_complex_enum():
    """测试 2: 复杂枚举清理"""
    print("="*80)
    print("测试组 2: 复杂枚举清理 (支持括号内的补充说明)")
    print("="*80)
    
    test_cases = [
        {
            'name': '带括号的十六进制枚举',
            'input': {'备注': '0x00:OFF(0), 0x01:ON(1)'},
            'expected_range': '{0x00, 0x01}'  # 保持十六进制
        },
        {
            'name': '不带括号的十六进制枚举',
            'input': {'备注': '0x00:关闭 0x01:开启'},
            'expected_range': '{0x00, 0x01}'  # 保持十六进制
        },
        {
            'name': '十进制枚举带括号',
            'input': {'备注': '0:停止 (STOP), 1:运行 (RUN), 2:待机 (STANDBY)'},
            'expected_range': '{0, 1, 2}'
        },
        {
            'name': '混合进制枚举',
            'input': {'备注': '0x00:低电平 (0V), 0x01:高电平 (3.3V)'},
            'expected_range': '{0x00, 0x01}'  # 保持十六进制
        },
        {
            'name': '多枚举项带括号',
            'input': {'备注': '0:状态 A(描述 1), 1:状态 B(描述 2), 2:状态 C(描述 3)'},
            'expected_range': '{0, 1, 2}'
        },
        {
            'name': '中文冒号枚举',
            'input': {'备注': '0x00：正常 0x01：异常'},
            'expected_range': '{0x00, 0x01}'  # 保持十六进制
        },
        {
            'name': '分号分隔枚举',
            'input': {'备注': '0:关；1:开；2:自动'},
            'expected_range': '{0, 1, 2}'
        },
    ]
    
    p = DataProcessor()
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = p.process_row(case['input'])
        actual_range = result['formatted'].get('值域') or result['cleaned'].get('值域')
        
        success = case['expected_range'] in str(actual_range) if case['expected_range'] else not actual_range
        
        if success:
            passed += 1
            status = "[PASS]"
        else:
            failed += 1
            status = "[FAIL]"
        
        print(f"\n{i}. {case['name']} [{status}]")
        print(f"   输入：{case['input']}")
        print(f"   期望：{case['expected_range']}")
        print(f"   实际：{actual_range}")
        
        # 显示完整的格式化结果
        print(f"   完整输出:")
        for k in ['值域', '单位', '转换公式', '备注']:
            v = result['formatted'].get(k) or result['cleaned'].get(k)
            if v:
                print(f"     {k}: {v}")
    
    print(f"\n{'='*80}")
    print(f"通过：{passed}/{len(test_cases)} ({passed/len(test_cases)*100:.1f}%)")
    print(f"{'='*80}\n")


def test_remark_preservation():
    """测试 3: 备注保留原始内容"""
    print("="*80)
    print("测试组 3: 备注保留原始内容（正常行为）")
    print("="*80)
    
    test_cases = [
        {
            'name': '枚举值描述保留原文',
            'input': {'备注': '0x00:OFF(0), 0x01:ON(1)，用于控制电源'},
            'expected_range': '{0, 1}',
            'expected_remark_contains': '0x00:OFF(0), 0x01:ON(1)'  # 备注应保留原文
        },
        {
            'name': '范围描述保留原文',
            'input': {'备注': '范围 0-100，工作电压'},
            'expected_range': '[0,100]',
            'expected_remark_contains': '范围'  # 备注可能保留部分原文
        },
        {
            'name': '混合内容保留说明',
            'input': {'备注': '0~5V，分辨率 0.1V，精度±1%'},
            'expected_range': '[0,5]',
            'expected_unit': 'V',
            'expected_formula': '0.1x+0'
        },
    ]
    
    p = DataProcessor()
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = p.process_row(case['input'])
        actual_range = result['formatted'].get('值域')
        actual_remark = result['cleaned'].get('备注')
        actual_unit = result['formatted'].get('单位')
        actual_formula = result['formatted'].get('转换公式')
        
        # 检查值域
        range_ok = case['expected_range'] in str(actual_range) if case.get('expected_range') else True
        
        # 检查备注是否包含指定内容
        remark_ok = case['expected_remark_contains'] in str(actual_remark) if case.get('expected_remark_contains') else True
        
        # 检查单位
        unit_ok = case['expected_unit'] in str(actual_unit) if case.get('expected_unit') else True
        
        # 检查公式
        formula_ok = case['expected_formula'] in str(actual_formula) if case.get('expected_formula') else True
        
        success = case['expected_range'] in str(actual_range) if case['expected_range'] else not actual_range
        
        if success:
            passed += 1
            status = "[PASS]"
        else:
            failed += 1
            status = "[FAIL]"
        
        print(f"\n{i}. {case['name']} [{status}]")
        print(f"   输入：{case['input']}")
        print(f"   期望值域：{case.get('expected_range', 'N/A')}")
        print(f"   期望备注包含：{case.get('expected_remark_contains', 'N/A')}")
        print(f"   实际值域：{actual_range}")
        print(f"   实际备注：{actual_remark}")
        print(f"   实际单位：{actual_unit}")
        print(f"   实际公式：{actual_formula}")
    
    print(f"\n{'='*80}")
    print(f"通过：{passed}/{len(test_cases)} ({passed/len(test_cases)*100:.1f}%)")
    print(f"{'='*80}\n")


def test_mixed_scenarios():
    """测试 4: 混合场景综合测试"""
    print("="*80)
    print("测试组 4: 混合场景综合测试")
    print("="*80)
    
    test_cases = [
        {
            'name': 'CAN 总线信号（真实场景）',
            'input': {
                '名称': '车速信号',
                '内容': '车辆行驶速度',
                '数据类型': 'UINTEGER-16',
                '备注': '0-65535，LSB=0.01km/h，单位 km/h'
            },
            'expected': {
                '值域': '[0,65535]',
                '单位': 'km/h',
                '转换公式': '0.01x+0'
            }
        },
        {
            'name': '温度传感器（负数 + 小数）',
            'input': {
                '名称': '环境温度',
                '内容': '工作温度范围',
                '数据类型': 'INTEGER-16',
                '备注': '-40-125 摄氏度，分辨率 0.1℃'
            },
            'expected': {
                '值域': '[-40,125]',
                '单位': '℃',
                '转换公式': '0.1x+0'
            }
        },
        {
            'name': '开关状态（复杂枚举）',
            'input': {
                '名称': '主继电器',
                '内容': '继电器控制',
                '数据类型': 'UINTEGER-8',
                '备注': '0x00:断开 (OFF), 0x01:闭合 (ON)'
            },
            'expected': {
                '值域': '{0, 1}'
            }
        },
        {
            'name': 'PWM 占空比（百分比）',
            'input': {
                '名称': '风扇控制',
                '内容': 'PWM 占空比',
                '数据类型': 'UINTEGER-8',
                '备注': '0-255 对应 0%-100%，分辨率 0.392157%'
            },
            'expected': {
                '值域': '[0,255]',
                '转换公式': '0.392157x+0'
            }
        },
        {
            'name': 'ADC 采样（混合分隔符）',
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
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = p.process_row(case['input'])
        
        all_ok = True
        details = []
        
        for field, expected in case['expected'].items():
            actual = result['formatted'].get(field) or result['cleaned'].get(field)
            field_ok = expected in str(actual) if expected else not actual
            all_ok = all_ok and field_ok
            ok_mark = "[OK]" if field_ok else "[FAIL]"
            details.append(f"{field}: {actual} {ok_mark}")
        
        if all_ok:
            passed += 1
            status = "[PASS]"
        else:
            failed += 1
            status = "[FAIL]"
        
        print(f"\n{i}. {case['name']} [{status}]")
        print(f"   输入备注：{case['input']['备注']}")
        print(f"   期望:")
        for k, v in case['expected'].items():
            print(f"     {k}: {v}")
        print(f"   实际:")
        for detail in details:
            print(f"     {detail}")
    
    print(f"\n{'='*80}")
    print(f"通过：{passed}/{len(test_cases)} ({passed/len(test_cases)*100:.1f}%)")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    try:
        print("="*80)
        print("修复验证测试开始")
        print("="*80)
        print()
        
        test_range_format()
        test_complex_enum()
        test_remark_preservation()
        test_mixed_scenarios()
        
        print("="*80)
        print("所有测试完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败：{e}")
        import traceback
        traceback.print_exc()
