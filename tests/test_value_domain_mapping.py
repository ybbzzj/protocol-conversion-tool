#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试值域到判读公式的映射
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.table_detector import TableDetector
from backend.services.excel_exporter import ExcelExporter

def test_value_domain_mapping():
    print("\n[测试] 值域到判读公式映射\n")
    
    # 使用您的测试协议文档
    docx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'word/测试协议20260331.docx')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend/outputs')
    
    if not os.path.exists(docx_path):
        print(f"❌ 文档不存在: {docx_path}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"1️⃣  提取表格...")
    detector = TableDetector()
    tables_data = detector.extract_tables_from_docx(docx_path)
    print(f"   ✓ 提取到 {len(tables_data)} 个表格\n")
    
    # 检查第一个表格是否有值域
    if tables_data:
        first_table = tables_data[0]
        print(f"2️⃣  检查表格结构...")
        print(f"   表格名: {first_table.get('msg_name')}")
        print(f"   表头: {first_table.get('headers')}")
        
        if first_table.get('data_rows'):
            first_row = first_table['data_rows'][0]
            print(f"\n   第一行数据:")
            for k, v in first_row.items():
                print(f"     {k:15} : {v}")
            
            # 检查值域
            has_range = '值域' in first_row or '取值范围' in first_row
            print(f"\n   ✓ 是否包含值域: {has_range}")
            if has_range:
                range_val = first_row.get('值域') or first_row.get('取值范围')
                print(f"   ✓ 值域内容: {range_val}")
    
    print(f"\n3️⃣  导出 Excel...")
    try:
        exporter = ExcelExporter(output_dir)
        output_file = exporter.export_with_template(tables_data, 'test_task')
        print(f"   ✓ 导出成功: {output_file}")
    except Exception as e:
        print(f"   ❌ 导出失败: {e}")

if __name__ == "__main__":
    test_value_domain_mapping()
