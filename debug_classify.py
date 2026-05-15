#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试 _classify_remark_content 逻辑"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import re
from backend.services.data_cleaner import FormulaStandardizer

def simulate_classify(txt):
    """模拟 _classify_remark_content 的逻辑"""
    print(f"\n输入文本：'{txt}'")
    print("="*60)
    
    result = {}
    remaining_txt = txt
    
    # 步骤 1：提取值域
    print("\n步骤 1：提取值域...")
    range_match = re.search(r'(?:取值范围 | 范围)?\s*-?\d+\s*~\s*-?\d+', txt)
    if range_match:
        range_str = range_match.group(0).strip()
        result['值域'] = f'[{range_str.split("~")[0].replace("取值范围","").replace("范围","").strip()}, {range_str.split("~")[1].strip()}]'
        remaining_txt = remaining_txt.replace(range_match.group(0), '', 1)
        print(f"  提取到值域：{result['值域']}")
        print(f"  剩余文本：'{remaining_txt}'")
    
    # 步骤 2：提取单位
    print("\n步骤 2：提取单位...")
    unit_patterns = [
        (r'单位\s*[=:：]\s*([A-Za-z/°℃\u00b0\u2103]+)', '单位='),
        (r'LSB\s*=\s*([\d.]+)([A-Za-z/°℃\u00b0\u2103]+)', 'LSB='),
    ]
    for pattern, ptype in unit_patterns:
        unit_match = re.search(pattern, txt)
        if unit_match:
            if ptype == '单位=':
                result['单位'] = unit_match.group(1).strip()
            elif ptype == 'LSB=':
                result['单位'] = unit_match.group(2).strip()
            remaining_txt = remaining_txt.replace(unit_match.group(0), '', 1)
            print(f"  提取到单位：{result.get('单位')}")
            print(f"  剩余文本：'{remaining_txt}'")
            break
    
    # 步骤 3：提取转换公式
    print("\n步骤 3：提取转换公式...")
    quantize_match = re.search(r'(?:量化单位 | 分辨率)\s*[\d.]+', txt, re.IGNORECASE)
    if quantize_match:
        formula_val = quantize_match.group(0).strip()
        result['转换公式'] = FormulaStandardizer().standardize(formula_val)
        remaining_txt = remaining_txt.replace(quantize_match.group(0), '', 1)
        print(f"  提取到公式：{result['转换公式']}")
        print(f"  剩余文本：'{remaining_txt}'")
    else:
        lsb_formula_match = re.search(r'LSB\s*=\s*[\d.]+', txt)
        if lsb_formula_match and '单位' not in result:
            formula_val = lsb_formula_match.group(0).strip()
            result['转换公式'] = FormulaStandardizer().standardize(formula_val)
            remaining_txt = remaining_txt.replace(lsb_formula_match.group(0), '', 1)
            print(f"  提取到 LSB 公式：{result['转换公式']}")
            print(f"  剩余文本：'{remaining_txt}'")
        else:
            chinese_formula_match = re.search(r'[乘除×÷]\s*[以]?\s*[\d.]+(?:\s*[+\-]\s*[\d.]+)?', txt)
            if chinese_formula_match:
                prefix = txt[:chinese_formula_match.start()]
                if not prefix or not re.search(r'[\u4e00-\u9fff]$', prefix):
                    formula_val = chinese_formula_match.group(0).strip()
                    result['转换公式'] = FormulaStandardizer().standardize(formula_val)
                    remaining_txt = remaining_txt.replace(chinese_formula_match.group(0), '', 1)
                    print(f"  提取到中文公式：{result['转换公式']}")
                    print(f"  剩余文本：'{remaining_txt}'")
    
    # 步骤 4：清理剩余文本
    print("\n步骤 4：清理剩余文本...")
    remaining_txt = re.sub(r'\s+', ' ', remaining_txt).strip()
    remaining_txt = re.sub(r'^[，,;；:.:\s]+', '', remaining_txt)
    remaining_txt = re.sub(r'[，,;；:.:\s]+$', '', remaining_txt)
    print(f"  清理后剩余：'{remaining_txt}'")
    
    if remaining_txt and len(remaining_txt) >= 2:
        result['备注'] = remaining_txt
        print(f"  保留备注：{result['备注']}")
    
    print("\n" + "="*60)
    print("最终结果:")
    for k, v in result.items():
        print(f"  {k}: '{v}'")
    print("="*60)
    
    return result

if __name__ == "__main__":
    test_cases = [
        '乘以 0.1',
        '量化单位 0.5 度',
        '分辨率 0.392157%',
        'LSB=0.1V',
    ]
    
    for txt in test_cases:
        simulate_classify(txt)
