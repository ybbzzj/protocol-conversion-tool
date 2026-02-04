#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证复杂混合结构表格的识别逻辑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from backend.services.table_detector import TableDetector

def test_mixed_structure_detection():
    print("测试复杂混合结构表格识别...")
    
    # 模拟用户提供的表格结构 (Grid 形式)
    # 第一行: 信息名称 检查结果 信息标识 xx
    # 第二行: 信源、信宿 BC...
    # 第三行: 传输周期 非周期 其他 -
    # 第四行: 发起时机 按实际操作流程 错误处理 -
    # 第五行: 序号 内容 类型 值域 单位 数据处理方法
    # 第六行: 1 计时时间 UINTEGER-32 0~4294967295 ms 32位整型数...
    
    grid = [
        ["信息名称", "检查结果", "信息标识", "xx"],
        ["信源、信宿", "BC=>RT1-SA0-模式码0x03", "BC=>RT1-SA0-模式码0x03", "BC=>RT1-SA0-模式码0x03"], # 模拟合并单元格
        ["传输周期", "非周期", "其他", "-"],
        ["发起时机", "按实际操作流程", "错误处理", "-"],
        ["序号", "内容", "类型", "值域", "单位", "数据处理方法"],
        ["1", "计时时间", "UINTEGER-32", "0~4294967295", "ms", "32位整型数..."]
    ]
    
    detector = TableDetector()
    
    # 模拟定位表头逻辑
    header_row_idx = -1
    for r_idx, row in enumerate(grid):
        matches = sum(1 for cell in row if any(k in cell for k in detector.keywords))
        if matches >= 3: # 序号, 内容, 类型 匹配
            header_row_idx = r_idx
            break
    
    print(f"识别到表头行索引: {header_row_idx}")
    
    # 模拟提取元数据逻辑
    msg_name = ""
    meta = {}
    all_unique_cells = []
    for r_idx in range(header_row_idx):
        row = grid[r_idx]
        row_unique = [row[0]]
        for i in range(1, len(row)):
            if row[i] != row[i-1]: row_unique.append(row[i])
        all_unique_cells.extend(row_unique)
    
    print(f"提取的元数据单元格: {all_unique_cells}")
    
    # K-V 匹配
    for i in range(len(all_unique_cells) - 1):
        k, v = all_unique_cells[i], all_unique_cells[i+1]
        if any(kw in k for kw in ['信息名称', '名称', '协议名称']):
            if not msg_name and v and v not in ['—', '-'] and v != k: msg_name = v
        elif any(kw in k for kw in ['信息标识', '标识', '消息ID']):
            if v and v not in ['—', '-'] and v != k: meta['信息标识'] = v
            
    print(f"识别到的消息名称: {msg_name}")
    print(f"识别到的元数据: {meta}")
    
    # 模拟过滤逻辑
    msg_name_lower = msg_name.lower()
    is_important_business = any(keyword in msg_name_lower for keyword in ['指令', '控制', '命令', '状态', '检查', '结果', '协议', '消息'])
    
    # 表头列检查
    unique_headers = grid[header_row_idx]
    content_found = any(any(kw in h for kw in detector.header_categories['content']) for h in unique_headers)
    type_found = any(any(kw in h for kw in detector.header_categories['type']) for h in unique_headers)
    
    is_param_table = content_found and type_found
    is_core_protocol_table = is_param_table and is_important_business and '参数表' not in msg_name_lower
    
    print(f"重要业务表判定: {is_important_business}")
    print(f"核心协议表判定: {is_core_protocol_table}")
    
    if msg_name == "检查结果" and is_core_protocol_table:
        print("✓ 成功识别并保留了复杂混合结构表格！")
        return True
    else:
        print("✗ 识别失败")
        return False

if __name__ == "__main__":
    test_mixed_structure_detection()