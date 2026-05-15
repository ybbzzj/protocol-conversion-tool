#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整调试 _classify_remark_content"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.data_cleaner import DataProcessor, FormulaStandardizer
import re

def debug_classify(txt):
    """完全模拟 _classify_remark_content 的逻辑"""
    print(f"\n{'='*80}")
    print(f"输入文本：'{txt}'")
    print('='*80)
    
    result = {}
    remaining_txt = txt
    
    # ========== 步骤 1：提取值域 ==========
    print("\n【步骤 1】提取值域...")
    range_match = re.search(r'(?:取值范围 | 范围)?\s*-?\d+\s*~\s*-?\d+', txt)
    if range_match:
        range_str = range_match.group(0).strip()
        result['值域'] = f'[{range_str.split("~")[0].replace("取值范围","").replace("范围","").strip()}, {range_str.split("~")[1].strip()}]'
        remaining_txt = remaining_txt.replace(range_match.group(0), '', 1)
        print(f"  ✅ 提取到值域：{result['值域']}")
        print(f"  剩余文本：'{remaining_txt}'")
    else:
        print("  ❌ 未匹配到值域")
    
    # ========== 步骤 2：提取单位 ==========
    print("\n【步骤 2】提取单位...")
    lsb_unit_match = re.search(r'LSB\s*=\s*([\d.]+\s*(?:ms|s|μs|us|min|h|Hz|kHz|MHz|GHz|V|mV|A|mA|mW|W|dB|dBm|℃|°|°C|bit|byte|KB|MB|°/[hmin]|km/h|m/s[²2]?))', txt, re.IGNORECASE)
    if lsb_unit_match:
        result['单位'] = lsb_unit_match.group(1).strip()
        remaining_txt = remaining_txt.replace(lsb_unit_match.group(0), '', 1)
        print(f"  ✅ LSB 单位：{result['单位']}")
    else:
        unit_keyword_match = re.search(r'单位 [为是：:]\s*([A-Za-z/°℃\u00b0\u2103]+)', txt, re.IGNORECASE)
        if unit_keyword_match:
            result['单位'] = unit_keyword_match.group(1).strip()
            remaining_txt = remaining_txt.replace(unit_keyword_match.group(0), '', 1)
            print(f"  ✅ 关键字单位：{result['单位']}")
        else:
            bracket_unit_match = re.search(r'[（\(\[]([A-Za-z/°℃\u00b0\u2103]+)[）\)\]](?:\s*$|\s*[,，])', txt)
            if bracket_unit_match:
                result['单位'] = bracket_unit_match.group(1).strip()
                remaining_txt = remaining_txt.replace(bracket_unit_match.group(0), '', 1)
                print(f"  ✅ 括号单位：{result['单位']}")
            else:
                print("  ❌ 未匹配到单位")
    
    # ========== 步骤 3：提取转换公式 ==========
    print("\n【步骤 3】提取转换公式...")
    quantize_match = re.search(r'量化单位\s*[\d.]+', txt, re.IGNORECASE)
    if not quantize_match:
        quantize_match = re.search(r'分辨率\s*[\d.]+', txt, re.IGNORECASE)
    if quantize_match:
        formula_val = quantize_match.group(0).strip()
        result['转换公式'] = FormulaStandardizer().standardize(formula_val)
        remaining_txt = remaining_txt.replace(quantize_match.group(0), '', 1)
        print(f"  ✅ 量化单位/分辨率公式：{result['转换公式']}")
    else:
        lsb_formula_match = re.search(r'LSB\s*=\s*[\d.]+', txt)
        if lsb_formula_match:
            formula_val = lsb_formula_match.group(0).strip()
            result['转换公式'] = FormulaStandardizer().standardize(formula_val)
            remaining_txt = remaining_txt.replace(lsb_formula_match.group(0), '', 1)
            print(f"  ✅ LSB 公式：{result['转换公式']}")
        else:
            chinese_formula_match = re.search(r'[乘除×÷]\s*[以]?\s*[\d.]+(?:\s*[+\-]\s*[\d.]+)?', txt)
            if chinese_formula_match:
                prefix = txt[:chinese_formula_match.start()]
                if not prefix or not re.search(r'[\u4e00-\u9fff]$', prefix):
                    formula_val = chinese_formula_match.group(0).strip()
                    result['转换公式'] = FormulaStandardizer().standardize(formula_val)
                    remaining_txt = remaining_txt.replace(chinese_formula_match.group(0), '', 1)
                    print(f"  ✅ 中文公式：{result['转换公式']}")
                else:
                    print(f"  ❌ 前缀有汉字，跳过")
            else:
                print("  ❌ 未匹配到公式")
    
    # ========== 步骤 4：清理剩余文本 ==========
    print("\n【步骤 4】清理剩余文本...")
    remaining_txt = re.sub(r'\s+', ' ', remaining_txt).strip()
    remaining_txt = re.sub(r'^[，,;；:.:\s]+', '', remaining_txt)
    remaining_txt = re.sub(r'[，,;；:.:\s]+$', '', remaining_txt)
    print(f"  清理后：'{remaining_txt}'")
    
    if remaining_txt and len(remaining_txt) >= 2:
        result['备注'] = remaining_txt
        print(f"  → 保留备注：{result['备注']}")
    
    print("\n" + "="*80)
    print("最终结果:")
    for k, v in result.items():
        print(f"  {k}: '{v}'")
    print("="*80)
    
    return result

if __name__ == "__main__":
    test_cases = [
        '分辨率 0.392157%',
        '0~255 对应 0%~100%，分辨率 0.392157%',
    ]
    
    for txt in test_cases:
        debug_classify(txt)
