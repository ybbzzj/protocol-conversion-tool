#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试改进后的表格命名功能
"""

def test_table_naming_logic():
    """测试表格命名逻辑"""
    print("测试改进后的表格命名逻辑...")
    
    # 模拟表格数据结构
    import re
    
    # 模拟表格内容
    grid = [
        ["表1 端口分配表"],  # 表格标题行
        ["序号", "信源", "信宿", "信息内容", "接收组播地址", "接收端口号", "信源系统码", "信源机器码", "信宿系统码", "信宿机器码"],  # 表头行
        ["1", "", "XX组合计算模块", "PD控制指令", "225.0.0.112", "12000", "100", "110", "100", "112"],
        ["2", "", "XX装置", "PD控制指令", "225.0.0.112", "12000", "100", "129", "100", "112"]
    ]
    
    # 模拟检测器的逻辑
    header_row_idx = 1  # 表头在第2行
    headers = grid[header_row_idx]
    
    # 初始消息名称为空
    msg_name = ""
    
    # 内容字段候选名
    content_fields = ['参数', '内容', '信号名称', '信息内容', '接口名称', '飞行计时']
    
    # 检查表头是否包含数据内容所需的核心类别
    content_found = any('参数' in h or '内容' in h or '信号名称' in h or '信息内容' in h for h in headers)
    type_found = any('数据类型' in h or '类型' in h for h in headers)
    
    print(f"表头: {headers}")
    print(f"content_found: {content_found}")
    print(f"type_found: {type_found}")
    
    # 4. 新增：处理类似"表1 端口分配表"格式的表格标题
    if not msg_name and grid:
        # 检查表头上方的几行，看是否有"表X 表名"格式的标题
        for r_idx in range(min(5, header_row_idx)):  # 检查表头上方最多5行
            row = grid[r_idx]
            if row:
                # 检查每行的第一个单元格，通常包含表格标题
                first_cell = row[0] if len(row) > 0 else ""
                print(f"检查上方行 {r_idx}: '{first_cell}'")
                if first_cell and '表' in first_cell and ' ' in first_cell:
                    # 尝试匹配"表X 表名"或"表X 表名 表"格式
                    parts = first_cell.split(' ', 1)
                    print(f"分割结果: {parts}")
                    if len(parts) > 1:
                        table_name_part = parts[1].strip()
                        # 移除可能的"表"字
                        if table_name_part.endswith('表'):
                            table_name_part = table_name_part[:-1]
                        if table_name_part:
                            msg_name = table_name_part
                            print(f"提取到表格名称: {msg_name}")
                            break
    
    # 5. 如果还是没有找到名称，尝试从表头中推断
    if not msg_name:
        # 如果表头包含特定关键词，可以根据表头内容推断表格类型
        if any('消息ID' in h or '消息标识' in h for h in headers):
            msg_name = '消息ID编码表'
        elif any(keyword in str(headers) for keyword in ['接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']):
            msg_name = '端口分配表'
        elif content_found and type_found:
            msg_name = '协议参数表'
    
    # 清洗标题标签
    msg_name = re.sub(r'^(信息|名称|标识|信号|消息|—)+', '', msg_name).strip()
    
    print(f"最终确定的表格名称: {msg_name}")
    
    # 验证结果
    if msg_name == "端口分配":
        print("✓ 成功提取表格名称 '端口分配'")
        return True
    else:
        print(f"✗ 表格名称提取失败，期望 '端口分配'，实际得到 '{msg_name}'")
        return False

def test_different_table_formats():
    """测试不同表格格式的命名"""
    print("\n测试不同表格格式的命名...")
    
    test_cases = [
        {
            'name': '端口分配表',
            'grid': [
                ["表1 端口分配表"],
                ["序号", "信源", "信宿", "信息内容", "接收组播地址", "接收端口号"]
            ],
            'expected': '端口分配'
        },
        {
            'name': '消息ID编码表',
            'grid': [
                ["表2 消息ID编码表"],
                ["序号", "信源", "信宿", "信息内容", "消息ID"]
            ],
            'expected': '消息ID编码'
        },
        {
            'name': '协议参数表',
            'grid': [
                ["表4 PD控制指令"],
                ["序号", "参数", "数据类型", "数据长度（字节）", "值域", "单位", "备注"]
            ],
            'expected': 'PD控制指令'
        }
    ]
    
    all_passed = True
    
    for i, case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {case['name']}")
        grid = case['grid']
        expected = case['expected']
        
        header_row_idx = 1
        headers = grid[header_row_idx]
        
        msg_name = ""
        
        # 检查表头内容
        content_found = any('参数' in h or '内容' in h or '信号名称' in h or '信息内容' in h for h in headers)
        type_found = any('数据类型' in h or '类型' in h for h in headers)
        
        # 4. 处理类似"表X 表名"格式的表格标题
        if not msg_name and grid:
            for r_idx in range(min(5, header_row_idx)):
                row = grid[r_idx]
                if row:
                    first_cell = row[0] if len(row) > 0 else ""
                    if first_cell and '表' in first_cell and ' ' in first_cell:
                        parts = first_cell.split(' ', 1)
                        if len(parts) > 1:
                            table_name_part = parts[1].strip()
                            if table_name_part.endswith('表'):
                                table_name_part = table_name_part[:-1]
                            if table_name_part:
                                msg_name = table_name_part
                                break
        
        # 5. 如果还是没有找到名称，尝试从表头中推断
        if not msg_name:
            if any('消息ID' in h or '消息标识' in h for h in headers):
                msg_name = '消息ID编码表'
            elif any(keyword in str(headers) for keyword in ['接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']):
                msg_name = '端口分配表'
            elif content_found and type_found:
                msg_name = '协议参数表'
        
        import re
        msg_name = re.sub(r'^(信息|名称|标识|信号|消息|—)+', '', msg_name).strip()
        
        print(f"  提取名称: '{msg_name}', 期望: '{expected}'")
        
        if msg_name == expected:
            print(f"  ✓ {case['name']} 名称提取正确")
        else:
            print(f"  ✗ {case['name']} 名称提取错误")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success1 = test_table_naming_logic()
    success2 = test_different_table_formats()
    
    print(f"\n{'='*50}")
    if success1 and success2:
        print("✓ 所有表格命名测试通过!")
    else:
        print("✗ 部分表格命名测试失败!")