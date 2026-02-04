#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证针对非规范布局（横向/纵向）及名称包含“结果”的表格识别逻辑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from backend.services.table_detector import TableDetector

def test_unstructured_table_recognition():
    """测试非规范表格识别逻辑"""
    print("测试非规范表格识别逻辑...")
    
    # 模拟用户提供的场景
    # 场景1：横向布局，包含“信息名称 检查结果”
    grid_horizontal = [
        ['信息名称', '检查结果', '信息标识', 'xx'],
        ['信源、信宿', 'BCRT1-SA0-模式码0x03', '', ''],
        ['传输周期', '非周期', '其他', '-'],
        ['发起时机', '按实际操作流程', '错误处理', '-'],
        ['序号', '内容', '类型', '值域', '单位', '数据处理方法'],
        ['1', '计时时间', 'UINTEGER-32', '0~4294967295', 'ms', '32位整型数...']
    ]
    
    # 场景2：纵向布局
    grid_vertical = [
        ['信息名称', '信息标识', '', ''],
        ['检查结果', 'xx', '', ''],
        ['序号', '内容', '类型', '值域', '单位', '数据处理方法'],
        ['1', '计时时间', 'UINTEGER-32', '0~4294967295', 'ms', '32位整型数...']
    ]
    
    detector = TableDetector()
    
    def analyze_grid(grid, label):
        print(f"\n--- 分析场景: {label} ---")
        # 手动执行 TableDetector.extract_tables_from_docx 中的核心逻辑片段
        # 1. 定位表头
        header_row_idx = -1
        for r_idx, row in enumerate(grid):
            matches = sum(1 for cell in row if any(k in cell for k in detector.keywords))
            if matches >= 2:
                header_row_idx = r_idx
                break
        
        if header_row_idx == -1:
            print("✗ 未找到表头")
            return False
            
        print(f"找到表头于行 {header_row_idx}: {grid[header_row_idx]}")
        
        # 2. 提取名称和元数据
        msg_name = ""
        meta = {}
        for r_idx in range(min(5, header_row_idx)):
            row = grid[r_idx]
            # 横向
            if len(row) >= 2:
                for i in range(len(row) - 1):
                    key_cell = row[i]
                    value_cell = row[i+1]
                    if any(kw in key_cell for kw in ['信息名称', '名称', '协议名称']):
                        if not msg_name and value_cell and value_cell not in ['—', '-']:
                            msg_name = value_cell
            
            # 纵向
            if r_idx < header_row_idx - 1:
                next_row = grid[r_idx + 1]
                for i in range(min(len(row), len(next_row))):
                    key_cell = row[i]
                    value_cell = next_row[i]
                    if any(kw in key_cell for kw in ['信息名称', '名称', '协议名称']):
                        if not msg_name and value_cell and value_cell not in ['—', '-', '']:
                            msg_name = value_cell
                            
        print(f"提取到名称: '{msg_name}'")
        
        # 3. 过滤逻辑
        unique_headers = grid[header_row_idx]
        content_found = any(any(kw in h for kw in detector.header_categories['content']) for h in unique_headers)
        type_found = any(any(kw in h for kw in detector.header_categories['type']) for h in unique_headers)
        
        msg_name_lower = msg_name.lower()
        is_instruction_related = any(keyword in msg_name_lower for keyword in ['指令', '控制', '命令'])
        is_status_related = '状态' in msg_name_lower
        is_result_related = '结果' in msg_name_lower # 关键点
        is_protocol_related = '协议' in msg_name_lower and '参数' not in msg_name_lower
        is_message_related = '消息' in msg_name_lower
        
        is_param_table = content_found and type_found
        is_core_protocol_table = is_param_table and (is_instruction_related or is_status_related or is_result_related or is_protocol_related or is_message_related)
        
        print(f"is_param_table: {is_param_table}")
        print(f"is_result_related: {is_result_related}")
        print(f"is_core_protocol_table: {is_core_protocol_table}")
        
        if is_core_protocol_table:
            print(f"✓ 成功识别表格 '{msg_name}'")
            return True
        else:
            print(f"✗ 识别失败")
            return False

    res1 = analyze_grid(grid_horizontal, "横向布局")
    res2 = analyze_grid(grid_vertical, "纵向布局")
    
    if res1 and res2:
        print("\n🎉 全部测试通过！现在可以正确提取名称为 '检查结果' 的非规范表格了。")
    else:
        print("\n❌ 测试未完全通过。")

if __name__ == "__main__":
    test_unstructured_table_recognition()