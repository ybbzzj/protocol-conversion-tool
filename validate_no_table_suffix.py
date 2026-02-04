#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证最终结果中不再包含以"表"结尾的表格
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.table_detector import DocumentParser
from backend.services.table_linker import TableLinker

def test_final_filter():
    doc_path = r'word\测试协议20251216.docx'
    
    if not os.path.exists(doc_path):
        print(f"❌ 文件不存在: {doc_path}")
        return False
    
    print("=" * 50)
    print("验证最终过滤逻辑...")
    print("=" * 50)
    
    try:
        # 1. 解析所有表格
        parser = DocumentParser()
        result = parser.parse(doc_path)
        all_tables = result['tables']
        print(f"解析阶段识别到 {len(all_tables)} 个表格:")
        for t in all_tables:
            print(f"  - {t['msg_name']}")
        
        print()
        
        # 2. 链接并过滤
        linker = TableLinker()
        final_tables = linker.link_tables(all_tables)
        
        print(f"链接过滤后剩余 {len(final_tables)} 个表格:")
        for t in final_tables:
            print(f"  - {t['msg_name']}")
        
        print()
        
        # 3. 检查是否还有以"表"结尾的
        table_ending_names = [t['msg_name'] for t in final_tables if t['msg_name'].endswith('表')]
        
        if table_ending_names:
            print("❌ 仍有以'表'结尾的表格被保留:")
            for name in table_ending_names:
                print(f"  - {name}")
            return False
        else:
            print("✅ 成功过滤掉所有以'表'结尾的表格!")
            return True
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_final_filter()
    sys.exit(0 if success else 1)
