#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：查看表格数据结构，诊断为什么所有行都被过滤
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.table_detector import TableDetector
from services.table_linker import TableLinker

doc_path = os.path.join(os.path.dirname(__file__), '..', 'word', '测试协议20260331.docx')
doc_path = os.path.abspath(doc_path)

if not os.path.exists(doc_path):
    print(f"[ERROR] 文件不存在：{doc_path}")
    sys.exit(1)

print("="*80)
print("调试：查看表格数据结构")
print("="*80)

detector = TableDetector()
tables = detector.extract_tables_from_docx(doc_path)

print(f"\n提取到 {len(tables)} 个表格\n")

for t_idx, table in enumerate(tables[:3], 1):  # 只看前 3 个表
    print(f"{'='*80}")
    print(f"表格 {t_idx}: {table.get('msg_name', '未命名')}")
    print(f"{'='*80}")
    
    headers = table.get('headers', [])
    print(f"表头：{headers}")
    
    data_rows = table.get('data_rows', [])
    print(f"数据行数：{len(data_rows)}")
    
    if data_rows:
        print(f"\n前 3 行数据示例:")
        for i, row in enumerate(data_rows[:3], 1):
            print(f"\n  行 {i}:")
            for k, v in row.items():
                if v and str(v).strip():  # 只显示非空值
                    print(f"    {k}: '{v}'")
            
            # 检查是否满足 is_valid_data_row
            from backend.services.data_cleaner import DataProcessor
            processor = DataProcessor()
            is_valid = processor.is_valid_data_row(row)
            print(f"    [验证] {'有效' if is_valid else '无效'}")
            
            if not is_valid:
                # 分析为什么无效
                content_fields = processor.content_field_names
                has_non_content = False
                for k, v in row.items():
                    if not str(k).startswith('_') and k not in content_fields:
                        if v and str(v).strip() and str(v).strip() not in ('—', '-', ''):
                            has_non_content = True
                            print(f"      -> 发现非内容字段：{k} = '{v}'")
                
                if not has_non_content:
                    print(f"      -> 原因：只有内容字段（名称/内容）有值，其他字段全空")
    
    print()
