#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析测试协议文档，列出所有识别到的表格供用户确认筛选规则
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.table_detector import DocumentParser

def analyze_test_document():
    doc_path = r'word\测试协议20251216.docx'
    
    if not os.path.exists(doc_path):
        print(f"❌ 文件不存在: {doc_path}")
        return
    
    print("=" * 50)
    print("正在分析测试文档...")
    print("=" * 50)
    
    try:
        parser = DocumentParser()
        result = parser.parse(doc_path)
        tables = result['tables']
        
        print(f"✅ 共识别到 {len(tables)} 个表格:")
        print()
        
        for i, table in enumerate(tables, 1):
            msg_name = table.get('msg_name', '未知')
            headers = table.get('headers', [])
            data_rows = table.get('data_rows', [])
            meta = table.get('meta', {})
            
            print(f"{i:2d}. 表格名称: {msg_name}")
            print(f"    表头字段: {headers}")
            print(f"    数据行数: {len(data_rows)}")
            if meta:
                print(f"    元数据: {meta}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_test_document()
