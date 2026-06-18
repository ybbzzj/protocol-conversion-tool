# -*- coding: utf-8 -*-
"""
检查测试文档中的表格结构，确认是否存在ID表
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backend.services.table_detector import DocumentParser

def analyze_document():
    """分析文档结构"""
    doc_path = "word/混合模式协议(公开).docx"
    
    if not os.path.exists(doc_path):
        print(f"[ERROR] 文档不存在: {doc_path}")
        return
    
    print(f"[分析] 文档: {doc_path}")
    print("=" * 80)
    
    parser = DocumentParser()
    result = parser.parse(doc_path)
    tables = result['tables']
    
    print(f"[统计] 总表格数: {len(tables)}")
    print("\n[表格详情]")
    
    for i, table in enumerate(tables):
        table_type = table.get('table_type', 'unknown')
        headers = table.get('headers', [])
        data_rows = table.get('data_rows', [])
        msg_name = table.get('msg_name', '')
        preceding_para = table.get('preceding_para', '')
        meta = table.get('meta', {})
        
        print(f"\n--- 表格{i} ---")
        print(f"类型: {table_type}")
        print(f"消息名: {msg_name}")
        print(f"表头: {headers}")
        print(f"数据行数: {len(data_rows)}")
        print(f"前置段落: {preceding_para[:100]}...")
        print(f"元数据: {meta}")
        
        # 显示前3行数据
        if data_rows:
            print(f"前3行数据:")
            for j, row in enumerate(data_rows[:3]):
                print(f"  行{j}: {row}")

if __name__ == "__main__":
    analyze_document()