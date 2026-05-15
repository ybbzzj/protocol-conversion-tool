#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确字段一致性对比测试
针对相同名称+内容的行，验证其他字段是否与预期结果一致
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from collections import defaultdict

def detailed_field_comparison():
    """详细字段对比分析"""
    print("=== 精确字段一致性对比分析 ===\n")
    
    try:
        # 读取两个Excel文件
        expected_path = 'word/csvfile/转换结果20260227.xlsx'
        actual_path = 'backend/outputs/协议_20260227233850.xlsx'  # 使用最新生成的文件
        
        expected_df = pd.read_excel(expected_path)
        actual_df = pd.read_excel(actual_path)
        
        print(f"📊 数据概览:")
        print(f"   预期结果行数: {len(expected_df)}")
        print(f"   实际结果行数: {len(actual_df)}")
        print()
        
        # 创建对比字典：{名称_内容: {字段: 值}}
        expected_dict = {}
        actual_dict = {}
        
        # 处理预期结果
        for _, row in expected_df.iterrows():
            name = str(row.get('名称', '')).strip()
            content = str(row.get('内容', '')).strip()
            if name and content:
                key = f"{name}_{content}"
                expected_dict[key] = dict(row)
        
        # 处理实际结果
        for _, row in actual_df.iterrows():
            name = str(row.get('名称', '')).strip()
            content = str(row.get('内容', '')).strip()
            if name and content:
                key = f"{name}_{content}"
                actual_dict[key] = dict(row)
        
        print(f"🔑 唯一标识符统计:")
        print(f"   预期结果唯一组合: {len(expected_dict)}")
        print(f"   实际结果唯一组合: {len(actual_dict)}")
        print()
        
        # 找到共同的名称+内容组合
        common_keys = set(expected_dict.keys()) & set(actual_dict.keys())
        print(f"🎯 共同的名称+内容组合: {len(common_keys)}个")
        print()
        
        # 详细对比每个共同组合的字段
        mismatch_count = 0
        total_compared = 0
        
        for key in sorted(common_keys):
            exp_row = expected_dict[key]
            act_row = actual_dict[key]
            
            name, content = key.split('_', 1)
            print(f"📋 组合: {name} - {content}")
            
            # 对比关键字段
            key_fields = ['数据类型', '单位', '备注', '值域', '转换公式']
            has_mismatch = False
            
            for field in key_fields:
                exp_val = str(exp_row.get(field, '')).strip()
                act_val = str(act_row.get(field, '')).strip()
                
                if exp_val != act_val:
                    if not has_mismatch:
                        print(f"   ❌ 字段不一致:")
                        has_mismatch = True
                        mismatch_count += 1
                    print(f"      {field}:")
                    print(f"         预期: {repr(exp_val)}")
                    print(f"         实际: {repr(act_val)}")
                    total_compared += 1
            
            if not has_mismatch:
                print(f"   ✅ 所有字段一致")
            
            print()
        
        print("=" * 60)
        print(f"📊 对比总结:")
        print(f"   共同组合数: {len(common_keys)}")
        print(f"   字段不一致组合数: {mismatch_count}")
        print(f"   总体一致率: {((len(common_keys) - mismatch_count) / len(common_keys) * 100):.1f}%")
        print(f"   总对比字段数: {total_compared}")
        
    except Exception as e:
        print(f"❌ 对比失败: {e}")
        import traceback
        traceback.print_exc()

def find_specific_examples():
    """查找具体的问题案例"""
    print("\n=== 具体问题案例分析 ===\n")
    
    try:
        expected_df = pd.read_excel('word/csvfile/转换结果20260227.xlsx')
        actual_df = pd.read_excel('backend/outputs/协议_20260227233850.xlsx')
        
        # 查找几个典型的匹配组合
        examples = [
            ('某设备装置测量数据3', '某设备计时时间'),
            ('状态信息', '某设备计时时间'), 
            ('某设备装置测量数据1', '某设备计时时间')
        ]
        
        for name, content in examples:
            print(f"🔍 案例: {name} - {content}")
            
            # 在预期结果中查找
            exp_matches = expected_df[
                (expected_df['名称'] == name) & 
                (expected_df['内容'] == content)
            ]
            
            # 在实际结果中查找
            act_matches = actual_df[
                (actual_df['名称'] == name) & 
                (actual_df['内容'] == content)
            ]
            
            if not exp_matches.empty and not act_matches.empty:
                exp_row = exp_matches.iloc[0]
                act_row = act_matches.iloc[0]
                
                fields_to_compare = ['数据类型', '单位', '备注', '值域']
                for field in fields_to_compare:
                    exp_val = str(exp_row.get(field, '')).strip()
                    act_val = str(act_row.get(field, '')).strip()
                    
                    status = "✅" if exp_val == act_val else "❌"
                    print(f"   {status} {field}:")
                    print(f"      预期: {repr(exp_val)}")
                    print(f"      实际: {repr(act_val)}")
            else:
                print("   ⚠️  未找到匹配行")
            
            print()
            
    except Exception as e:
        print(f"❌ 案例分析失败: {e}")

if __name__ == "__main__":
    detailed_field_comparison()
    find_specific_examples()