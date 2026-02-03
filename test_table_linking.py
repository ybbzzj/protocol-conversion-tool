#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试表格关联功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.table_detector import DocumentParser
from backend.services.table_linker import TableLinker

def test_table_linking():
    """测试表格关联功能"""
    print("开始测试表格关联功能...")
    
    # 创建示例表格数据
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
        }
    ]
    
    # 测试表格关联
    linker = TableLinker()
    linked_tables = linker.link_tables(sample_tables)
    
    print(f"原始表格数量: {len(sample_tables)}")
    print(f"关联后表格数量: {len(linked_tables)}")
    
    # 检查PD控制指令表是否获得了消息ID
    for table in linked_tables:
        if table['msg_name'] == 'PD控制指令':
            msg_id = table.get('meta', {}).get('消息ID')
            print(f"PD控制指令的消息ID: {msg_id}")
            if msg_id:
                print("✓ 表格关联成功!")
                return True
    
    print("✗ 表格关联失败!")
    return False

if __name__ == "__main__":
    success = test_table_linking()
    if success:
        print("\n表格关联功能测试通过!")
    else:
        print("\n表格关联功能测试失败!")