#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试元数据注入功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.table_detector import TableDetector

def test_metadata_injection():
    """测试元数据注入功能"""
    
    test_file = "/Users/yuanyuqing/Documents/code/schoolProject/word/测试协议20251216.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    print(f"📄 测试元数据注入功能\n")
    
    detector = TableDetector()
    tables = detector.extract_tables_from_docx(test_file)
    
    # 查找有元数据的表格
    tables_with_meta = [t for t in tables if t.get('meta')]
    
    print(f"✅ 找到 {len(tables_with_meta)} 个带元数据的表格\n")
    
    for i, table in enumerate(tables_with_meta[:5]):  # 显示前5个
        print(f"{'='*80}")
        print(f"[表格 {table['index']}] 消息名称: {table.get('msg_name', '未命名')}")
        print(f"{'='*80}")
        
        meta = table.get('meta', {})
        print(f"\n【原始元数据】({len(meta)} 项):")
        for key, value in meta.items():
            print(f"  • {key}: {value}")
        
        headers = table.get('headers', [])
        data_rows = table.get('data_rows', [])
        
        print(f"\n【表头】({len(headers)} 列):")
        print(f"  {' | '.join(headers)}")
        
        if data_rows:
            first_row = data_rows[0]
            print(f"\n【第一行数据（检查元数据注入）】:")
            for key, value in first_row.items():
                # 标记元数据字段
                is_meta = key in meta
                marker = "✓ [META]" if is_meta else "  [DATA]"
                val_display = value[:40] + '...' if len(str(value)) > 40 else value
                print(f"  {marker} {key}: {val_display}")
        
        print()

if __name__ == '__main__':
    test_metadata_injection()
