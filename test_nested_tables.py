#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试嵌套表格识别和转换的修复效果。
"""
import json
import sys
sys.path.insert(0, '/Users/yuanyuqing/Documents/code/schoolProject')

from backend.services.table_detector import DocumentTableExtractor
from backend.services.table_linker import TableLinker

# 1. 使用table_detector提取表格
doc_path = '/Users/yuanyuqing/Documents/code/schoolProject/backend/uploads/37cc34c3-5606-43ea-9ea4-ae4be95c6e7b_测试协议20260227.docx'
extractor = DocumentTableExtractor()
tables = extractor.extract_all_tables_from_document(doc_path)

print(f"Extracted {len(tables)} tables")

# 2. 使用table_linker进行表格关联
linker = TableLinker()
linked_tables = linker.link_tables(tables)

print(f"Linked {len(linked_tables)} tables")

# 3. 查找包含嵌套子行的表
for table_idx, table in enumerate(linked_tables):
    msg_name = table.get('msg_name', '')
    data_rows = table.get('data_rows', [])
    headers = table.get('headers', [])
    
    has_bit_rows = any(row.get('_is_bit_row') for row in data_rows)
    
    if has_bit_rows:
        print(f"\n{'='*80}")
        print(f"Table {table_idx}: {msg_name}")
        print(f"Headers: {headers}")
        print(f"Total rows: {len(data_rows)} (including bit sub-rows)")
        print(f"\nData rows:")
        
        for r_idx, row in enumerate(data_rows):
            if row.get('_is_bit_row'):
                print(f"\n  [BIT SUB-ROW {r_idx}]:")
            else:
                print(f"\n  [NORMAL ROW {r_idx}]:")
            
            for key, value in row.items():
                if not key.startswith('_'):
                    print(f"    {key}: {value}")
