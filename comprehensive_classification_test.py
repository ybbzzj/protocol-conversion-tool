#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试智能分类功能 - 修复前 vs 修复后对比
测试范围：枚举值、单位、值域、转换公式的识别与分割
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.data_cleaner import DataProcessor

def run_test(test_name, input_data, expected):
    """运行单个测试并返回是否通过"""
    print(f"\n{'='*80}")
    print(f"测试：{test_name}")
    print(f"{'='*80}")
    
    # 显示输入
    print("输入数据:")
    for k, v in input_data.items():
        if v:
            print(f"  {k}: {v}")
    
    # 执行处理
    processor = DataProcessor()
    result = processor.process_row(input_data)
    
    # 提取实际结果
    actual = {
        '值域': result['formatted'].get('值域'),
        '单位': result['formatted'].get('单位'),
        '转换公式': result['formatted'].get('转换公式'),
        '备注': result['cleaned'].get('备注')
    }
    
    # 显示结果
    print("\n输出结果:")
    if actual['值域']:
        print(f"  值域：{actual['值域']}")
    else:
        print(f"  值域：(无)")
    
    if actual['单位']:
        print(f"  单位：{actual['单位']}")
    else:
        print(f"  单位：(无)")
    
    if actual['转换公式']:
        print(f"  转换公式：{actual['转换公式']}")
    else:
        print(f"  转换公式：(无)")
    
    if actual['备注']:
        print(f"  备注：{actual['备注']}")
    else:
        print(f"  备注：(无)")
    
    # 验证结果
    print("\n期望结果:")
    passed = True
    for field in ['值域', '单位', '转换公式', '备注']:
        exp_val = expected.get(field)
        act_val = actual.get(field)
        
        # 特殊处理 None 和空字符串
        if exp_val is None and (act_val == '' or act_val is None):
            match = True
            exp_display = '(无)'
            act_display = '(无)'
        elif exp_val == '' and (act_val == '' or act_val is None):
            match = True
            exp_display = '(无)'
            act_display = act_val or '(无)'
        else:
            match = (exp_val == act_val)
            exp_display = exp_val or '(无)'
            act_display = act_val or '(无)'
        
        status = "✅" if match else "❌"
        print(f"  {status} {field}:")
        print(f"      期望：{exp_display}")
        print(f"      实际：{act_display}")
        
        if not match:
            passed = False
    
    return passed


def main():
    print("="*80)
    print("智能分类功能全面测试")
    print("="*80)
    
    test_cases = [
        # ==================== 场景 A：枚举值识别 ====================
        {
            'name': 'A1: 16 进制枚举（核心场景）',
            'input': {
                '名称': '供电状态',
                '内容': '供电状态',
                '数据类型': 'UINTEGER-16',
                '备注': '0x1701:供电 0x1702:断电'
            },
            'expected': {
                '值域': '{5889, 5890}',
                '单位': None,
                '转换公式': None,
                '备注': '0x1701:供电 0x1702:断电'
            }
        },
        {
            'name': 'A2: 十进制枚举',
            'input': {
                '名称': '设备状态',
                '内容': '运行状态',
                '数据类型': 'UINTEGER-8',
                '备注': '0:停止 1:运行 2:待机'
            },
            'expected': {
                '值域': '{0, 1, 2}',
                '单位': None,
                '转换公式': None,
                '备注': '0:停止 1:运行 2:待机'
            }
        },
        {
            'name': 'A3: CAN 总线状态枚举',
            'input': {
                '名称': 'CAN 状态',
                '内容': '通信状态',
                '数据类型': 'UINTEGER-8',
                '备注': '0:BusOff 1:ErrorActive 2:ErrorPassive 3:Init'
            },
            'expected': {
                '值域': '{0, 1, 2, 3}',
                '单位': None,
                '转换公式': None,
                '备注': '0:BusOff 1:ErrorActive 2:ErrorPassive 3:Init'
            }
        },
        
        # ==================== 场景 B：负数范围（已修复）====================
        {
            'name': 'B1: 负数温度范围（已修复 bug）',
            'input': {
                '名称': '温度监测',
                '内容': '温度值',
                '数据类型': 'INTEGER-16',
                '备注': '取值范围 -40~125，单位:℃'
            },
            'expected': {
                '值域': '[-40,125]',
                '单位': '℃',
                '转换公式': None,
                '备注': None
            }
        },
        {
            'name': 'B2: 双负数范围',
            'input': {
                '名称': '温差',
                '内容': '温度差值',
                '数据类型': 'INTEGER-16',
                '备注': '-50~-10'
            },
            'expected': {
                '值域': '[-50,-10]',
                '单位': None,
                '转换公式': None,
                '备注': None
            }
        },
        
        # ==================== 场景 C：混合内容分割 ====================
        {
            'name': 'C1: 范围 + 单位',
            'input': {
                '名称': '电压检测',
                '内容': '电压值',
                '数据类型': 'UINTEGER-16',
                '备注': '0~4095，单位:V'
            },
            'expected': {
                '值域': '[0,4095]',
                '单位': 'V',
                '转换公式': None,
                '备注': None
            }
        },
        {
            'name': 'C2: LSB 单位 + 范围',
            'input': {
                '名称': '时间戳',
                '内容': '时间计数',
                '数据类型': 'UINTEGER-32',
                '备注': 'LSB=1ms，0~4294967295'
            },
            'expected': {
                '值域': '[0,4294967295]',
                '单位': 'ms',
                '转换公式': '1x+0',
                '备注': None
            }
        },
        {
            'name': 'C3: 完整混合（单位 + 范围 + 公式）',
            'input': {
                '名称': '压力传感器',
                '内容': '压力值',
                '数据类型': 'UINTEGER-16',
                '备注': '单位:kPa，取值范围:0~1000，乘以 0.01'
            },
            'expected': {
                '值域': '[0,1000]',
                '单位': 'kPa',
                '转换公式': '0.01x+0',
                '备注': None
            }
        },
        
        # ==================== 场景 D：转换公式识别 ====================
        {
            'name': 'D1: 乘以 N 格式',
            'input': {
                '名称': 'AD 转换',
                '内容': '数字量',
                '数据类型': 'UINTEGER-12',
                '备注': '乘以 0.1'
            },
            'expected': {
                '值域': None,
                '单位': None,
                '转换公式': '0.1x+0',
                '备注': None
            }
        },
        {
            'name': 'D2: 量化单位格式',
            'input': {
                '名称': '角度传感器',
                '内容': '角度值',
                '数据类型': 'UINTEGER-16',
                '备注': '量化单位 0.5 度'
            },
            'expected': {
                '值域': None,
                '单位': None,
                '转换公式': '0.5x+0',
                '备注': None
            }
        },
        {
            'name': 'D3: 分辨率格式',
            'input': {
                '名称': 'DAC 输出',
                '内容': '模拟量',
                '数据类型': 'UINTEGER-12',
                '备注': '分辨率 0.001V'
            },
            'expected': {
                '值域': None,
                '单位': None,
                '转换公式': '0.001x+0',
                '备注': None
            }
        },
        
        # ==================== 场景 E：括号单位提取 ====================
        {
            'name': 'E1: 圆括号单位',
            'input': {
                '名称': '频率测量',
                '内容': '信号频率',
                '数据类型': 'UINTEGER-32',
                '备注': '信号频率 (Hz)'
            },
            'expected': {
                '值域': None,
                '单位': 'Hz',
                '转换公式': None,
                '备注': '信号频率'
            }
        },
        {
            'name': 'E2: 方括号单位',
            'input': {
                '名称': '环境温度',
                '内容': '温度',
                '数据类型': 'INTEGER-16',
                '备注': '环境温度 [℃]'
            },
            'expected': {
                '值域': None,
                '单位': '℃',
                '转换公式': None,
                '备注': '环境温度'
            }
        },
        
        # ==================== 场景 F：纯描述性备注 ====================
        {
            'name': 'F1: 纯描述不应提取结构化信息',
            'input': {
                '名称': '状态标志',
                '内容': '运行标志',
                '数据类型': 'UINTEGER-8',
                '备注': '32 位整型数，最高位为符号位，低 7 位表示数值'
            },
            'expected': {
                '值域': None,
                '单位': None,
                '转换公式': None,
                '备注': '32 位整型数，最高位为符号位，低 7 位表示数值'
            }
        },
        
        # ==================== 场景 G：实际协议案例 ====================
        {
            'name': 'G1: 实际案例 - 模拟量采集',
            'input': {
                '名称': '模拟量输入',
                '内容': '电压值',
                '数据类型': 'UINTEGER-16',
                '备注': '0~65535，LSB=0.1V，单位:V'
            },
            'expected': {
                '值域': '[0,65535]',
                '单位': 'V',
                '转换公式': '0.1x+0',
                '备注': None
            }
        },
        {
            'name': 'G2: 实际案例 - PWM 占空比',
            'input': {
                '名称': 'PWM 控制',
                '内容': '占空比',
                '数据类型': 'UINTEGER-8',
                '备注': '0~255 对应 0%~100%，分辨率 0.392157%'
            },
            'expected': {
                '值域': '[0,255]',
                '单位': None,
                '转换公式': '0.392157x+0',
                '备注': '对应 0%~100%'
            }
        },
    ]
    
    # 运行所有测试
    results = []
    for test_case in test_cases:
        passed = run_test(test_case['name'], test_case['input'], test_case['expected'])
        results.append({
            'name': test_case['name'],
            'passed': passed
        })
    
    # 统计结果
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    # 打印总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    print(f"总测试数：{total}")
    print(f"通过：{passed} ✅")
    print(f"失败：{failed} ❌")
    print(f"通过率：{pass_rate:.1f}%")
    print()
    
    # 列出失败的测试
    if failed > 0:
        print("失败测试列表:")
        for r in results:
            if not r['passed']:
                print(f"  ❌ {r['name']}")
        print()
    
    # 按类别统计
    categories = {}
    for r in results:
        category = r['name'].split(':')[0]
        if category not in categories:
            categories[category] = {'total': 0, 'passed': 0}
        categories[category]['total'] += 1
        if r['passed']:
            categories[category]['passed'] += 1
    
    print("各类别测试结果:")
    for cat, stats in sorted(categories.items()):
        cat_pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        bar = "█" * int(cat_pass_rate / 5) + "░" * (20 - int(cat_pass_rate / 5))
        print(f"  {cat:15s} [{bar}] {stats['passed']:2d}/{stats['total']:2d} ({cat_pass_rate:5.1f}%)")
    
    print(f"\n{'='*80}")
    print("测试结束")
    print(f"{'='*80}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ 测试运行失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
