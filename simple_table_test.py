#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试表格检测器对不同表格类型的识别能力
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.table_detector import TableDetector
import tempfile
import zipfile
import os

def create_simple_test_doc():
    """创建一个简单的测试文档，包含各种类型的表格"""
    
    # 使用docx2python可以识别的简单结构
    # 实际上我们不需要创建复杂的docx，只需要测试表格检测器的逻辑
    
    # 模拟表格数据，测试检测器能否识别不同类型的表头
    mock_tables = [
        # PD控制指令表 (核心协议表)
        {
            'headers': ['序号', '参数', '数据类型', '数据长度（字节）', '值域', '单位', '备注'],
            'data_rows': [
                {'序号': '1', '参数': '飞行计时时间', '数据类型': 'UINTEGER-32', '数据长度（字节）': '4', '值域': '0~0xFFFFFFFF', '单位': 'ms', '备注': '接收XX指令后，完成时标清零'},
                {'序号': '2', '参数': '控制指令1', '数据类型': 'USHORT', '数据长度（字节）': '2', '值域': '0x1701：供电\n0x1702：断电\n其他值无效', '单位': '—', '备注': ''}
            ],
            'msg_name': 'PD控制指令',
            'index': 4
        },
        # 消息ID编码表
        {
            'headers': ['序号', '信源', '信宿', '信息内容', '消息ID'],
            'data_rows': [
                {'序号': '1', '信源': '', '信宿': 'XX组合计算模块', '信息内容': 'PD控制指令', '消息ID': '0x6E84'},
                {'序号': '2', '信源': '', '信宿': 'XX装置', '信息内容': 'PD控制指令', '消息ID': '0x81A0'},
                {'序号': '3', '信源': '', '信宿': 'XX模块', '信息内容': 'PD器状态', '消息ID': '0x7000'}
            ],
            'msg_name': '消息ID编码表',
            'index': 2
        },
        # 端口分配表
        {
            'headers': ['序号', '信源', '信宿', '信息内容', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'],
            'data_rows': [
                {'序号': '1', '信源': '', '信宿': 'XX组合计算模块', '信息内容': 'PD控制指令', '接收组播地址': '225.0.0.112', '接收端口号': '12000', '信源系统码': '100', '信源机器码': '110', '信宿系统码': '100', '信宿机器码': '112'},
                {'序号': '2', '信源': '', '信宿': 'XX装置', '信息内容': 'PD控制指令', '接收组播地址': '225.0.0.112', '接收端口号': '12000', '信源系统码': '100', '信源机器码': '129', '信宿系统码': '100', '信宿机器码': '112'},
                {'序号': '3', '信源': '', '信宿': 'XX模块', '信息内容': 'PD器状态', '接收组播地址': '225.0.0.105', '接收端口号': '20000', '信源系统码': '100', '信源机器码': '112', '信宿系统码': '0', '信宿机器码': '0'}
            ],
            'msg_name': '端口分配表',
            'index': 1
        }
    ]
    
    return mock_tables

def test_table_detection_logic():
    """测试表格检测器的逻辑"""
    print("测试表格检测器对不同类型表格的识别逻辑...")
    
    # 直接测试检测器的识别逻辑
    detector = TableDetector()
    
    # 模拟表格检测器的判断逻辑
    test_cases = [
        {
            'name': 'PD控制指令表',
            'headers': ['序号', '参数', '数据类型', '数据长度（字节）', '值域', '单位', '备注'],
            'expected': '核心协议表'
        },
        {
            'name': '消息ID编码表',
            'headers': ['序号', '信源', '信宿', '信息内容', '消息ID'],
            'expected': '消息ID编码表'
        },
        {
            'name': '端口分配表',
            'headers': ['序号', '信源', '信宿', '信息内容', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'],
            'expected': '端口分配表'
        },
        {
            'name': '普通表',
            'headers': ['列1', '列2', '列3'],
            'expected': '不满足条件（应被过滤）'
        }
    ]
    
    for case in test_cases:
        headers = case['headers']
        
        # 模拟检测器的判断逻辑
        seq_found = any(any(kw in h for kw in detector.header_categories['sequence']) for h in headers)
        content_found = any(any(kw in h for kw in detector.header_categories['content']) for h in headers)
        type_found = any(any(kw in h for kw in detector.header_categories['type']) for h in headers)
        
        is_core_protocol_table = content_found and type_found
        is_meta_table = any('消息ID' in h or '消息标识' in h for h in headers)
        is_port_table = any(keyword in str(headers) for keyword in ['接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'])
        
        is_valid_data_table = is_core_protocol_table or is_meta_table or is_port_table
        
        result = "保留" if is_valid_data_table else "过滤"
        
        print(f"\n表格: {case['name']}")
        print(f"  表头: {headers}")
        print(f"  识别结果: {result}")
        print(f"  预期: {case['expected']}")
        print(f"  核心协议表: {is_core_protocol_table}, 消息ID表: {is_meta_table}, 端口表: {is_port_table}")
        
        if case['expected'] == '核心协议表' and is_core_protocol_table:
            print("  ✓ 正确识别为核心协议表")
        elif case['expected'] == '消息ID编码表' and is_meta_table:
            print("  ✓ 正确识别为消息ID编码表")
        elif case['expected'] == '端口分配表' and is_port_table:
            print("  ✓ 正确识别为端口分配表")
        elif case['expected'] == '不满足条件（应被过滤）' and not is_valid_data_table:
            print("  ✓ 正确过滤掉无关表格")
        elif case['expected'] == '不满足条件（应被过滤）' and is_valid_data_table:
            print("  ⚠ 意外保留了无关表格")
        else:
            print("  ✗ 识别错误")
    
    print("\n表格检测逻辑测试完成!")

def test_with_mock_tables():
    """使用模拟表格测试关联功能"""
    print("\n" + "="*50)
    print("测试表格关联功能...")
    
    from backend.services.table_linker import TableLinker
    
    # 创建模拟的表格数据
    mock_tables = [
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
    linked_tables = linker.link_tables(mock_tables)
    
    print(f"输入表格数量: {len(mock_tables)}")
    print(f"输出表格数量: {len(linked_tables)}")
    
    # 查找PD控制指令表
    for table in linked_tables:
        if table['msg_name'] == 'PD控制指令':
            print(f"\nPD控制指令表的元数据: {table['meta']}")
            
            # 验证是否成功关联了ID和端口信息
            meta = table['meta']
            success = True
            
            if '消息ID' in meta:
                print(f"✓ 成功关联消息ID: {meta['消息ID']}")
            else:
                print("✗ 未能关联消息ID")
                success = False
                
            if '接收组播地址' in meta:
                print(f"✓ 成功关联接收组播地址: {meta['接收组播地址']}")
            else:
                print("✗ 未能关联接收组播地址")
                success = False
                
            if '接收端口号' in meta:
                print(f"✓ 成功关联接收端口号: {meta['接收端口号']}")
            else:
                print("✗ 未能关联接收端口号")
                success = False
                
            if '信源系统码' in meta:
                print(f"✓ 成功关联信源系统码: {meta['信源系统码']}")
            else:
                print("✗ 未能关联信源系统码")
                success = False
                
            if success:
                print("\n✓ 表格关联功能工作正常，成功识别并关联了端口分配表和消息ID编码表!")
            else:
                print("\n✗ 表格关联功能存在问题")
            
            break

if __name__ == "__main__":
    test_table_detection_logic()
    test_with_mock_tables()