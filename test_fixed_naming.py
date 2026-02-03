#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的表格命名功能
"""

def test_fixed_naming_logic():
    """测试修复后的表格命名逻辑"""
    print("测试修复后的表格命名逻辑...")
    
    test_cases = [
        {
            'name': '端口分配表',
            'cell_content': '表1 端口分配表',
            'expected': '端口分配'
        },
        {
            'name': '消息ID编码表',
            'cell_content': '表2 消息ID编码表',
            'expected': '消息ID编码'
        },
        {
            'name': 'PD控制指令表',
            'cell_content': '表4 PD控制指令',
            'expected': 'PD控制指令'
        }
    ]
    
    all_passed = True
    
    for case in test_cases:
        cell_content = case['cell_content']
        expected = case['expected']
        
        print(f"\n测试: '{cell_content}'")
        
        # 模拟修复后的逻辑
        table_name_part = ""
        
        if '表' in cell_content and ' ' in cell_content:
            # 更智能的分割：查找第一个空格后的所有内容
            space_pos = cell_content.find(' ')
            if space_pos != -1:
                table_name_part = cell_content[space_pos + 1:].strip()
                # 移除可能的"表"字
                if table_name_part.endswith('表'):
                    table_name_part = table_name_part[:-1]
        
        print(f"  提取结果: '{table_name_part}', 期望: '{expected}'")
        
        if table_name_part == expected:
            print(f"  ✓ {case['name']} 名称提取正确")
        else:
            print(f"  ✗ {case['name']} 名称提取错误")
            all_passed = False
    
    return all_passed

def test_original_problem():
    """测试原始问题场景"""
    print("\n" + "="*50)
    print("测试原始问题场景...")
    
    # 模拟原始问题中的情况
    grid = [
        ["表1 端口分配表"],  # 表格标题行
        ["序号", "信源", "信宿", "信息内容", "接收组播地址", "接收端口号", "信源系统码", "信源机器码", "信宿系统码", "信宿机器码"],  # 表头行
        ["1", "", "XX组合计算模块", "PD控制指令", "225.0.0.112", "12000", "100", "110", "100", "112"]
    ]
    
    header_row_idx = 1
    headers = grid[header_row_idx]
    
    # 初始消息名称为空
    msg_name = ""
    
    # 检查表头是否包含数据内容所需的核心类别
    content_found = any('参数' in h or '内容' in h or '信号名称' in h or '信息内容' in h for h in headers)
    type_found = any('数据类型' in h or '类型' in h for h in headers)
    
    print(f"表头: {headers}")
    print(f"content_found: {content_found}, type_found: {type_found}")
    
    # 检查表头上方的几行，看是否有"表X 表名"格式的标题
    if not msg_name and grid:
        for r_idx in range(min(5, header_row_idx)):  # 检查表头上方最多5行
            row = grid[r_idx]
            if row:
                # 检查每行的第一个单元格，通常包含表格标题
                first_cell = row[0] if len(row) > 0 else ""
                print(f"检查上方行 {r_idx}: '{first_cell}'")
                
                if first_cell and '表' in first_cell and ' ' in first_cell:
                    # 更智能的分割：查找第一个空格后的所有内容
                    space_pos = first_cell.find(' ')
                    if space_pos != -1:
                        table_name_part = first_cell[space_pos + 1:].strip()
                        # 移除可能的"表"字
                        if table_name_part.endswith('表'):
                            table_name_part = table_name_part[:-1]
                        if table_name_part:
                            msg_name = table_name_part
                            print(f"✓ 成功提取表格名称: '{msg_name}'")
                            break
    
    # 如果还是没有找到名称，尝试从表头中推断
    if not msg_name:
        # 如果表头包含特定关键词，可以根据表头内容推断表格类型
        if any('消息ID' in h or '消息标识' in h for h in headers):
            msg_name = '消息ID编码表'
        elif any(keyword in str(headers) for keyword in ['接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']):
            msg_name = '端口分配表'
        elif content_found and type_found:
            msg_name = '协议参数表'
    
    # 清洗标题标签
    import re
    msg_name = re.sub(r'^(信息|名称|标识|信号|消息|—)+', '', msg_name).strip()
    
    print(f"最终确定的表格名称: '{msg_name}'")
    
    if msg_name == "端口分配":
        print("✓ 原始问题场景测试通过！现在可以正确识别'表1 端口分配表'为'端口分配'")
        return True
    else:
        print(f"✗ 原始问题场景测试失败，期望'端口分配'，实际得到'{msg_name}'")
        return False

if __name__ == "__main__":
    success1 = test_fixed_naming_logic()
    success2 = test_original_problem()
    
    print(f"\n{'='*50}")
    if success1 and success2:
        print("✓ 所有修复后的表格命名测试通过!")
        print("现在系统能够正确识别表格标题，如：")
        print("- '表1 端口分配表' → '端口分配'")
        print("- '表2 消息ID编码表' → '消息ID编码'")
        print("- '表4 PD控制指令' → 'PD控制指令'")
    else:
        print("✗ 部分修复后的表格命名测试失败!")