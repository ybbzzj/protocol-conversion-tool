#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本 2：查看 link_tables 后的数据结构变化
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.table_detector import TableDetector
from services.table_linker import TableLinker
from backend.services.data_cleaner import DataProcessor

doc_path = os.path.join(os.path.dirname(__file__), '..', 'word', '测试协议20260331.docx')
doc_path = os.path.abspath(doc_path)

print("="*80)
print("调试 2：查看 link_tables 前后的变化")
print("="*80)

detector = TableDetector()
tables = detector.extract_tables_from_docx(doc_path)

print(f"\n提取到 {len(tables)} 个表格\n")

# 统计原始表格的有效行数
processor = DataProcessor()
total_valid_before = 0
for t_idx, table in enumerate(tables, 1):
    data_rows = table.get('data_rows', [])
    valid_count = sum(1 for row in data_rows if processor.is_valid_data_row(row))
    total_valid_before += valid_count

print(f"link_tables 前：总计 {total_valid_before} 个有效数据行\n")

# 执行 link_tables
linker = TableLinker()
linked_tables = linker.link_tables(tables)

print(f"link_tables 后：{len(linked_tables)} 个表格\n")

# 检查每个链接后的表格
total_valid_after = 0
for t_idx, table in enumerate(linked_tables, 1):
    print(f"{'='*80}")
    print(f"链接表 {t_idx}: {table.get('table_name', '未命名')}")
    print(f"{'='*80}")
    
    rows = table.get('rows', [])
    print(f"行数：{len(rows)}")
    
    valid_count = sum(1 for row in rows if processor.is_valid_data_row(row))
    print(f"有效行数：{valid_count}")
    total_valid_after += valid_count
    
    if rows:
        print(f"\n前 2 行示例:")
        for i, row in enumerate(rows[:2], 1):
            print(f"\n  行 {i}:")
            non_empty_fields = [(k, v) for k, v in row.items() if v and str(v).strip()]
            if non_empty_fields:
                for k, v in non_empty_fields[:5]:  # 只显示前 5 个非空字段
                    print(f"    {k}: '{v}'")
                if len(non_empty_fields) > 5:
                    print(f"    ... (还有 {len(non_empty_fields)-5} 个字段)")
            
            is_valid = processor.is_valid_data_row(row)
            print(f"    [验证] {'有效' if is_valid else '无效'}")
            
            if not is_valid:
                content_fields = processor.content_field_names
                has_non_content = False
                for k, v in row.items():
                    if not str(k).startswith('_') and k not in content_fields:
                        if v and str(v).strip() and str(v).strip() not in ('—', '-', ''):
                            has_non_content = True
                            break
                
                if not has_non_content:
                    print(f"      -> 原因：只有内容字段有值")
    
    print()

print(f"\n总计：{total_valid_after} 个有效数据行")
