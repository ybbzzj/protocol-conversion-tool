#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行数据一致性测试
验证同一行数据在不同处理阶段是否保持一致
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.table_detector import DocumentParser
from backend.services.data_cleaner import DataProcessor
import json

def test_row_consistency():
    """测试行数据一致性"""
    print("=== 行数据一致性测试 ===\n")
    
    # 使用测试文档
    doc_path = r'word\测试协议20251216.docx'
    
    if not os.path.exists(doc_path):
        print(f"❌ 文档不存在: {doc_path}")
        return
    
    # 1. 解析文档
    print("1️⃣ 解析文档表格...")
    parser = DocumentParser()
    result = parser.parse(doc_path)
    tables = result['tables']
    print(f"   ✓ 识别到 {len(tables)} 个表格\n")
    
    # 2. 选择一个典型表格进行详细分析
    processor = DataProcessor()
    
    for table_idx, table in enumerate(tables[:3]):  # 分析前3个表格
        msg_name = table.get('msg_name', '未知')
        data_rows = table.get('data_rows', [])
        
        if not data_rows:
            continue
            
        print(f"📋 表格 {table_idx + 1}: {msg_name}")
        print(f"   数据行数: {len(data_rows)}")
        
        # 分析第一行数据的一致性
        if data_rows:
            first_row = data_rows[0]
            print(f"\n   🔍 第一行原始数据:")
            for key, value in first_row.items():
                print(f"      {key}: {repr(value)}")
            
            # 处理行数据
            processed = processor.process_row(first_row)
            cleaned = processed['cleaned']
            converted = processed['converted']
            formatted = processed['formatted']
            
            print(f"\n   🔄 处理后数据:")
            print(f"      清洗后字段数: {len(cleaned)}")
            print(f"      转换后字段数: {len(converted)}")
            print(f"      格式化后字段数: {len(formatted)}")
            
            # 检查关键字段是否保持一致
            content_fields = ['内容', '参数', '信号名称', '名称', '字段', '数据含义']
            found_content = None
            
            for field in content_fields:
                if field in first_row and first_row[field]:
                    found_content = first_row[field]
                    print(f"\n   ✅ 找到内容字段 '{field}': {repr(found_content)}")
                    break
            
            if found_content:
                # 检查在清洗后是否还存在
                cleaned_content = None
                for field in content_fields:
                    if field in cleaned and cleaned[field]:
                        cleaned_content = cleaned[field]
                        print(f"   ✅ 清洗后内容字段 '{field}': {repr(cleaned_content)}")
                        break
                
                # 验证一致性
                if found_content == cleaned_content:
                    print("   🟢 内容字段值完全一致!")
                elif cleaned_content and found_content.strip() == cleaned_content.strip():
                    print("   🟡 内容字段值基本一致 (仅空白符差异)")
                else:
                    print("   🔴 内容字段值不一致!")
                    print(f"      原始: {repr(found_content)}")
                    print(f"      清洗: {repr(cleaned_content)}")
            
            print("-" * 50)

def compare_with_expected():
    """与预期结果对比"""
    print("\n=== 与预期结果对比 ===\n")
    
    # 读取预期结果
    try:
        import pandas as pd
        expected_df = pd.read_excel('word/csvfile/转换结果20260227.xlsx')
        actual_df = pd.read_excel('backend/outputs/协议_20260227233337.xlsx')
        
        print(f"预期结果行数: {len(expected_df)}")
        print(f"实际结果行数: {len(actual_df)}")
        
        # 对比相同名称的数据行
        common_names = set(expected_df['名称'].dropna()) & set(actual_df['名称'].dropna())
        print(f"\n共同的表格名称 ({len(common_names)}个):")
        for name in list(common_names)[:5]:  # 显示前5个
            print(f"  - {name}")
            
            # 找到对应的行
            exp_rows = expected_df[expected_df['名称'] == name]
            act_rows = actual_df[actual_df['名称'] == name]
            
            if not exp_rows.empty and not act_rows.empty:
                exp_first = exp_rows.iloc[0]
                act_first = act_rows.iloc[0]
                
                print(f"    预期内容: {exp_first.get('内容', 'N/A')}")
                print(f"    实际内容: {act_first.get('内容', 'N/A')}")
                
                # 比较关键字段
                key_fields = ['内容', '数据类型', '单位', '备注']
                for field in key_fields:
                    exp_val = exp_first.get(field, '')
                    act_val = act_first.get(field, '')
                    if str(exp_val) != str(act_val):
                        print(f"    ❌ {field} 不一致:")
                        print(f"       预期: {repr(exp_val)}")
                        print(f"       实际: {repr(act_val)}")
                print()
                
    except Exception as e:
        print(f"❌ 对比失败: {e}")

if __name__ == "__main__":
    test_row_consistency()
    compare_with_expected()