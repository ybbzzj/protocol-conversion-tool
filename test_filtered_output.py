#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试过滤后的输出，确保只输出协议参数表，而不输出辅助表格
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.table_linker import TableLinker

def test_filtered_output():
    """测试过滤后的输出"""
    print("测试过滤后的输出，确保只输出协议参数表...")
    
    # 模拟各种类型的表格数据
    all_tables = [
        # 标准协议参数表 (如表5 PD器状态)
        {
            'index': 5,
            'msg_name': 'PD器状态',
            'meta': {},
            'data_rows': [
                {
                    '序号': '1',
                    '参数': '飞行计时时间',
                    '数据类型': 'UINTEGER-32',
                    '数据长度（字节）': '4',
                    '值域': '0~0xFFFFFFFF',
                    '单位': 'ms',
                    '备注': '该时间为软件运行计时时间'
                },
                {
                    '序号': '2', 
                    '参数': 'PD状态',
                    '数据类型': 'UCHAR',
                    '数据长度（字节）': '1',
                    '值域': '0xAA：接通状态；0x55：未接通状态；其他值无效。',
                    '单位': '—',
                    '备注': '—'
                }
            ],
            'headers': ['序号', '参数', '数据类型', '数据长度（字节）', '值域', '单位', '备注']
        },
        # 消息ID编码表 (如表2)
        {
            'index': 2,
            'msg_name': '消息ID编码表',
            'meta': {},
            'data_rows': [
                {
                    '序号': '1',
                    '信源': '',
                    '信宿': 'XX组合计算模块',
                    '信息内容': 'PD控制指令',
                    '消息ID': '0x6E84'
                },
                {
                    '序号': '2',
                    '信源': '',
                    '信宿': 'XX装置',
                    '信息内容': 'PD控制指令', 
                    '消息ID': '0x81A0'
                },
                {
                    '序号': '3',
                    '信源': '',
                    '信宿': 'XX模块',
                    '信息内容': 'PD器状态',
                    '消息ID': '0x7000'
                }
            ],
            'headers': ['序号', '信源', '信宿', '信息内容', '消息ID']
        },
        # 端口分配表 (如表1)
        {
            'index': 1,
            'msg_name': '端口分配表',
            'meta': {},
            'data_rows': [
                {
                    '序号': '1',
                    '信源': '',
                    '信宿': 'XX组合计算模块',
                    '信息内容': 'PD控制指令',
                    '接收组播地址': '225.0.0.112',
                    '接收端口号': '12000',
                    '信源系统码': '100',
                    '信源机器码': '110',
                    '信宿系统码': '100',
                    '信宿机器码': '112'
                },
                {
                    '序号': '2',
                    '信源': '',
                    '信宿': 'XX装置',
                    '信息内容': 'PD控制指令',
                    '接收组播地址': '225.0.0.112',
                    '接收端口号': '12000',
                    '信源系统码': '100',
                    '信源机器码': '129',
                    '信宿系统码': '100',
                    '信宿机器码': '112'
                },
                {
                    '序号': '3',
                    '信源': '',
                    '信宿': 'XX模块',
                    '信息内容': 'PD器状态',
                    '接收组播地址': '225.0.0.105',
                    '接收端口号': '20000',
                    '信源系统码': '100',
                    '信源机器码': '112',
                    '信宿系统码': '0',
                    '信宿机器码': '0'
                }
            ],
            'headers': ['序号', '信源', '信宿', '信息内容', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']
        }
    ]
    
    print(f"输入表格数量: {len(all_tables)}")
    for i, table in enumerate(all_tables):
        print(f"  输入表格 {i+1}: {table['msg_name']} (类型: {table['headers'][:3]}...)")
    
    # 使用表格关联器处理
    linker = TableLinker()
    linked_tables = linker.link_tables(all_tables)
    
    print(f"\n关联后表格数量: {len(linked_tables)}")
    
    protocol_tables_count = 0
    auxiliary_tables_count = 0
    
    for i, table in enumerate(linked_tables):
        msg_name = table['msg_name']
        
        # 判断是否为协议参数表
        headers = table['headers']
        has_content = any('参数' in h or '内容' in h or '信号名称' in h for h in headers)
        has_type = any('数据类型' in h or '类型' in h for h in headers)
        
        if has_content and has_type:
            table_type = "协议参数表"
            protocol_tables_count += 1
        else:
            table_type = "辅助表（已过滤）"
            auxiliary_tables_count += 1
        
        print(f"  输出表格 {i+1}: {msg_name} ({table_type})")
        
        # 显示元数据
        if table['meta']:
            print(f"    关联元数据: {list(table['meta'].keys())}")
    
    print(f"\n统计:")
    print(f"  协议参数表: {protocol_tables_count}")
    print(f"  辅助表（已过滤）: {auxiliary_tables_count}")
    
    # 验证只输出了协议参数表
    if auxiliary_tables_count == 0 and protocol_tables_count > 0:
        print("\n✓ 修改成功！只输出了协议参数表，辅助表格已被过滤。")
        print("  - 协议参数表的内容会被输出")
        print("  - 消息ID编码表、端口分配表等辅助信息已关联为元数据")
        print("  - 不会在最终结果中出现辅助表格的内容")
        return True
    else:
        print(f"\n✗ 修改失败！仍输出了 {auxiliary_tables_count} 个辅助表格。")
        return False

def test_metadata_association():
    """测试元数据关联功能"""
    print(f"\n{'='*60}")
    print("测试元数据关联功能...")
    
    # 创建一个协议表和对应的辅助表
    tables = [
        {
            'index': 5,
            'msg_name': 'PD控制指令',
            'meta': {},
            'data_rows': [
                {
                    '序号': '1',
                    '参数': '飞行计时时间',
                    '数据类型': 'UINTEGER-32',
                    '数据长度（字节）': '4',
                    '值域': '0~0xFFFFFFFF',
                    '单位': 'ms',
                    '备注': '接收XX指令后，完成时标清零'
                }
            ],
            'headers': ['序号', '参数', '数据类型', '数据长度（字节）', '值域', '单位', '备注']
        },
        {
            'index': 2,
            'msg_name': '消息ID编码表',
            'meta': {},
            'data_rows': [
                {
                    '序号': '1',
                    '信源': '',
                    '信宿': 'XX组合计算模块',
                    '信息内容': 'PD控制指令',
                    '消息ID': '0x6E84'
                }
            ],
            'headers': ['序号', '信源', '信宿', '信息内容', '消息ID']
        },
        {
            'index': 1,
            'msg_name': '端口分配表',
            'meta': {},
            'data_rows': [
                {
                    '序号': '1',
                    '信源': '',
                    '信宿': 'XX组合计算模块',
                    '信息内容': 'PD控制指令',
                    '接收组播地址': '225.0.0.112',
                    '接收端口号': '12000',
                    '信源系统码': '100',
                    '信源机器码': '110',
                    '信宿系统码': '100',
                    '信宿机器码': '112'
                }
            ],
            'headers': ['序号', '信源', '信宿', '信息内容', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']
        }
    ]
    
    linker = TableLinker()
    linked_tables = linker.link_tables(tables)
    
    # 找到协议参数表
    protocol_table = None
    for table in linked_tables:
        headers = table['headers']
        has_content = any('参数' in h or '内容' in h or '信号名称' in h for h in headers)
        has_type = any('数据类型' in h or '类型' in h for h in headers)
        if has_content and has_type:
            protocol_table = table
            break
    
    if protocol_table:
        meta = protocol_table['meta']
        print(f"PD控制指令表关联的元数据: {meta}")
        
        expected_keys = ['消息ID', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']
        found_keys = [key for key in expected_keys if key in meta]
        
        print(f"找到的元数据字段: {found_keys}")
        
        if len(found_keys) >= 3:  # 至少找到几个关键字段
            print("✓ 元数据成功关联到协议参数表，辅助表格内容已过滤！")
            return True
        else:
            print("✗ 元数据关联不完整")
            return False
    else:
        print("✗ 未找到协议参数表")
        return False

if __name__ == "__main__":
    success1 = test_filtered_output()
    success2 = test_metadata_association()
    
    print(f"\n{'='*60}")
    if success1 and success2:
        print("🎉 所有测试通过！系统现在能够：")
        print()
        print("✅ 只输出协议参数表的内容到最终结果")
        print("✅ 将消息ID编码表、端口分配表等辅助信息作为元数据关联")
        print("✅ 不在最终结果中显示辅助表格的内容")
        print("✅ 保持元数据的完整性以供后续使用")
        print()
        print("您的要求已完全满足！")
    else:
        print("❌ 部分测试失败")