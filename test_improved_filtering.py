#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试改进后的数据行过滤策略
"""

def test_improved_filtering_strategy():
    """测试改进后的过滤策略"""
    print("开始测试改进后的数据行过滤策略...")
    
    # 模拟表格数据
    table_data = {
        'data_rows': [
            # 正常的协议参数行
            {
                '序号': '1',
                '参数': '飞行计时时间',
                '数据类型': 'UINTEGER-32',
                '数据长度（字节）': '4',
                '值域': '0~0xFFFFFFFF',
                '单位': 'ms',
                '备注': '接收XX指令后，完成时标清零'
            },
            # 包含消息ID的重要元数据行
            {
                '序号': '',
                '参数': '',
                '消息ID': '0x6E84',
                '数据类型': '',
                '数据长度（字节）': '',
                '值域': '',
                '单位': '',
                '备注': 'PD控制指令的ID'
            },
            # 包含端口信息的重要元数据行
            {
                '序号': '',
                '参数': '',
                '接收组播地址': '225.0.0.112',
                '接收端口号': '12000',
                '信源系统码': '100',
                '信源机器码': '110',
                '信宿系统码': '100',
                '信宿机器码': '112'
            },
            # 真的应该被过滤掉的空行
            {
                '序号': '',
                '参数': '',
                '数据类型': '',
                '数据长度（字节）': '',
                '值域': '',
                '单位': '',
                '备注': ''
            },
            # 包含噪声的行
            {
                '序号': '1',
                '参数': '参见附录C',
                '数据类型': 'UINT16',
                '数据长度（字节）': '2',
                '值域': '',
                '单位': '',
                '备注': ''
            }
        ]
    }
    
    print("原始数据行数量:", len(table_data['data_rows']))
    
    # 模拟改进后的过滤逻辑
    retained_rows = []
    
    for i, row in enumerate(table_data['data_rows']):
        row_display = ' | '.join([f"{k}:{v}" for k, v in row.items()])
        content_val = row.get('参数', row.get('内容', row.get('信号名称', '')))
        
        # 改进的过滤策略
        noise_reasons = []
        row_text_all = "".join(str(v) for v in row.values() if v)
        
        # 检查是否包含重要元数据字段（即使内容字段为空）
        has_important_metadata = any(key in ['消息ID', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'] for key in row.keys())
        has_non_empty_metadata = any(key in ['消息ID', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'] and row.get(key) for key in row.keys())
        
        # 如果是包含重要元数据的行，即使是内容字段为空也要保留
        if not content_val and not has_non_empty_metadata:
            noise_reasons.append("内容字段为空且无重要元数据")
        if '参见' in row_text_all:
            noise_reasons.append("含噪声词'参见'")
        
        print(f"  行 {i+1}: {row_display}")
        print(f"    - content_val: '{content_val}'")
        print(f"    - has_non_empty_metadata: {bool(has_non_empty_metadata)}")
        print(f"    - noise_reasons: {noise_reasons}")
        
        if not noise_reasons:
            decision = "✓ 保留"
            retained_rows.append(row)
        else:
            decision = f"✗ 过滤 (原因: {'; '.join(noise_reasons)})"
        
        print(f"    - 决策: {decision}")
        print()
    
    print(f"过滤后保留的行数: {len(retained_rows)}")
    
    # 验证重要信息是否被正确保留
    important_info_found = False
    for row in retained_rows:
        if '消息ID' in row and row['消息ID']:
            print(f"✓ 消息ID信息被正确保留: {row['消息ID']}")
            important_info_found = True
        if '接收组播地址' in row and row['接收组播地址']:
            print(f"✓ 接收组播地址信息被正确保留: {row['接收组播地址']}")
            important_info_found = True
        if '接收端口号' in row and row['接收端口号']:
            print(f"✓ 接收端口号信息被正确保留: {row['接收端口号']}")
            important_info_found = True
    
    if important_info_found:
        print("\n✓ 改进的过滤策略成功保留了重要元数据!")
        return True
    else:
        print("\n✗ 改进的过滤策略可能存在问题!")
        return False

if __name__ == "__main__":
    success = test_improved_filtering_strategy()
    if success:
        print("\n改进的过滤策略测试通过!")
    else:
        print("\n改进的过滤策略测试失败!")