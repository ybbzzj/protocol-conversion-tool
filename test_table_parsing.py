#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试脚本：验证复合表格结构解析功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.table_detector import TableDetector

def test_table_parsing():
    """测试表格解析功能"""
    
    # 测试文件路径
    test_file = "/Users/yuanyuqing/Documents/code/schoolProject/word/测试协议20251216.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    print(f"📄 开始解析文件: {os.path.basename(test_file)}\n")
    
    # 初始化检测器
    detector = TableDetector()
    
    # 提取表格
    tables = detector.extract_tables_from_docx(test_file)
    print(f"✅ 成功识别 {len(tables)} 个表格\n")
    
    # 逐个展示表格
    for i, table in enumerate(tables):
        print(f"{'='*80}")
        print(f"[表格 {i+1}] 消息名称: {table.get('msg_name', '未命名')}")
        print(f"{'='*80}")
        
        # 显示元数据
        meta = table.get('meta', {})
        if meta:
            print(f"【元数据】:")
            for key, value in meta.items():
                print(f"  • {key}: {value}")
            print()
        
        # 显示表头
        headers = table.get('headers', [])
        print(f"【表头】({len(headers)} 列)")
        print(f"  {' | '.join(headers)}\n")
        
        # 显示前5行数据
        data_rows = table.get('data_rows', [])
        print(f"【数据行】(共 {len(data_rows)} 行):")
        
        for row_idx, row in enumerate(data_rows[:5]):
            print(f"\n  [行 {row_idx+1}]:")
            for key, value in row.items():
                # 截断长值
                val_display = value[:50] + '...' if len(str(value)) > 50 else value
                print(f"    • {key}: {val_display}")
        
        if len(data_rows) > 5:
            print(f"\n  ... 还有 {len(data_rows) - 5} 行数据")
        
        print()
    
    print(f"{'='*80}")
    print("✅ 表格解析完成！")
    print(f"{'='*80}")

if __name__ == '__main__':
    test_table_parsing()
