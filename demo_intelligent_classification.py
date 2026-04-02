#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类功能演示 - 修复前 vs 修复后对比
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.data_cleaner import DataProcessor

def demo_case(name, input_data, expected):
    """演示单个案例"""
    print(f"\n{'='*70}")
    print(f"案例：{name}")
    print(f"{'='*70}")
    print(f"输入数据:")
    for k, v in input_data.items():
        if v:
            print(f"  {k}: {v}")
    
    processor = DataProcessor()
    result = processor.process_row(input_data)
    
    print(f"\n输出结果:")
    if '值域' in result['formatted']:
        print(f"  ✅ 值域：{result['formatted']['值域']}")
    else:
        print(f"     值域：(无)")
    
    if '单位' in result['formatted']:
        print(f"  ✅ 单位：{result['formatted']['单位']}")
    else:
        print(f"     单位：(无)")
    
    if '转换公式' in result['formatted']:
        print(f"  ✅ 转换公式：{result['formatted']['转换公式']}")
    else:
        print(f"     转换公式：(无)")
    
    if '备注' in result['cleaned']:
        print(f"  ✅ 备注：{result['cleaned']['备注']}")
    else:
        print(f"     备注：(无)")
    
    print(f"\n期望结果:")
    for k, v in expected.items():
        status = "✅" if v else "  "
        print(f"  {status} {k}: {v if v else '(无)'}")


def main():
    print("="*70)
    print("智能分类功能演示 - 修复前 vs 修复后对比")
    print("="*70)
    
    # 案例 1：枚举值识别（场景 A）
    demo_case(
        name="场景 A：枚举值与转换公式的智能区分",
        input_data={
            '名称': '某设备装置测量数据 test',
            '内容': '供电状态',
            '数据类型': 'UINTEGER-16',
            '字节': '2',
            '备注': '0x1701:供电 0x1702:断电'
        },
        expected={
            '值域': '{5889, 5890}',
            '单位': None,
            '转换公式': None,
            '备注': '0x1701:供电 0x1702:断电'
        }
    )
    
    # 案例 2：混合内容分割（场景 B）
    demo_case(
        name="场景 B：备注内容的智能分割与归类",
        input_data={
            '名称': '温度监测',
            '内容': '温度值',
            '数据类型': 'INTEGER-16',
            '备注': '取值范围 -40~125，单位:℃，精度 0.1℃'
        },
        expected={
            '值域': '[-40,125]',
            '单位': '℃',
            '转换公式': '0.1x+0',
            '备注': None
        }
    )
    
    # 案例 3：LSB 单位 + 范围
    demo_case(
        name="复杂场景：LSB 单位 + 范围混合",
        input_data={
            '名称': '模拟量输入',
            '内容': '电压值',
            '数据类型': 'UINTEGER-16',
            '备注': '0~65535，LSB=0.1V，单位:V'
        },
        expected={
            '值域': '[0,65535]',
            '单位': 'V',
            '转换公式': '0.1x+0',
            '备注': None
        }
    )
    
    # 案例 4：纯描述性备注
    demo_case(
        name="边界场景：纯描述性备注（不应提取任何结构化信息）",
        input_data={
            '名称': '状态标志',
            '内容': '运行状态',
            '数据类型': 'UINTEGER-8',
            '备注': '32 位整型数，最高位为符号位，低 7 位表示数值'
        },
        expected={
            '值域': None,
            '单位': None,
            '转换公式': None,
            '备注': '32 位整型数，最高位为符号位，低 7 位表示数值'
        }
    )
    
    # 案例 5：CAN 总线状态枚举
    demo_case(
        name="实际案例：CAN 总线状态枚举",
        input_data={
            '名称': 'CAN 状态',
            '内容': '通信状态',
            '数据类型': 'UINTEGER-8',
            '备注': '0:BusOff 1:ErrorActive 2:ErrorPassive 3:Init'
        },
        expected={
            '值域': '{0, 1, 2, 3}',
            '单位': None,
            '转换公式': None,
            '备注': '0:BusOff 1:ErrorActive 2:ErrorPassive 3:Init'
        }
    )
    
    print("\n" + "="*70)
    print("演示结束")
    print("="*70)
    print("\n📊 功能亮点总结:")
    print("  1. ✅ 枚举值自动识别并转换为标准格式 {...}")
    print("  2. ✅ 混合内容智能分割（值域、单位、公式、备注）")
    print("  3. ✅ LSB 等单位自动提取和标准化")
    print("  4. ✅ 转换公式自动识别和规范化 (aX+b 格式)")
    print("  5. ✅ 保留原始备注信息，避免信息丢失")
    print("\n💡 提示：完整测试报告请查看 INTELLIGENT_CLASSIFICATION_REPORT.md")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 演示失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
