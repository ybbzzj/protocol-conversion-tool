#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试增强的表格关联功能，包括端口分配表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.table_linker import TableLinker

def test_enhanced_linking():
    """测试增强的表格关联功能"""
    print("开始测试增强的表格关联功能...")
    
    # 创建示例表格数据，包括端口分配表
    sample_tables = [
        {
            'index': 4,
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
                },
                {
                    '序号': '2', 
                    '参数': '控制指令1',
                    '数据类型': 'USHORT',
                    '数据长度（字节）': '2',
                    '值域': '0x1701：供电\n0x1702：断电\n其他值无效',
                    '单位': '—',
                    '备注': ''
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
    
    # 测试增强的表格关联
    linker = TableLinker()
    linked_tables = linker.link_tables(sample_tables)
    
    print(f"原始表格数量: {len(sample_tables)}")
    print(f"关联后表格数量: {len(linked_tables)}")
    
    # 检查PD控制指令表是否获得了所有相关信息
    for table in linked_tables:
        if table['msg_name'] == 'PD控制指令':
            meta = table.get('meta', {})
            msg_id = meta.get('消息ID')
            multicast_addr = meta.get('接收组播地址')
            port_num = meta.get('接收端口号')
            
            print(f"PD控制指令的消息ID: {msg_id}")
            print(f"PD控制指令的接收组播地址: {multicast_addr}")
            print(f"PD控制指令的接收端口号: {port_num}")
            
            if msg_id and multicast_addr and port_num:
                print("✓ 增强的表格关联成功!")
                print(f"  完整元数据: {meta}")
                return True
    
    print("✗ 增强的表格关联失败!")
    return False

if __name__ == "__main__":
    success = test_enhanced_linking()
    if success:
        print("\n增强的表格关联功能测试通过!")
    else:
        print("\n增强的表格关联功能测试失败!")