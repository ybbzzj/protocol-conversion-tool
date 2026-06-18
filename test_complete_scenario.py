# -*- coding: utf-8 -*-
"""
测试验证三个修改点的完整场景，包括新格式ID表
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from backend.services.table_detector import DocumentParser, TableDetector
from backend.services.table_linker import TableLinker

def test_new_format_id_table():
    """测试新格式ID表（ID序号+ID定义+是否有数据）"""
    print("=" * 80)
    print("[测试] 新格式ID表识别")
    print("=" * 80)
    
    # 创建一个包含新格式ID表的模拟数据
    mock_tables = [
        {
            'table_type': 'unknown',
            'headers': ['ID序号', 'ID定义', '是否有数据'],
            'data_rows': [
                {'ID序号': '0x0301', 'ID定义': 'XX装置仿真输入数据', '是否有数据': '是'},
                {'ID序号': '0x8000', 'ID定义': 'XX装置数据1', '是否有数据': '是'},
                {'ID序号': '0x8001', 'ID定义': '测试数据2', '是否有数据': '否'},
            ],
            'preceding_para': '消息ID定义表',
            'msg_name': '消息ID定义表',
            'meta': {}
        },
        {
            'table_type': 'field_def',
            'headers': ['序号', '参数', '数据类型', '数据长度（字节）', '值域', '单位', '备注'],
            'data_rows': [
                {'序号': '', '参数': '仿真状态标志位', '数据类型': 'UCHAR', '数据长度（字节）': '1', '值域': '—', '单位': '—', '备注': '见注1'},
                {'序号': '', '参数': 'XX计时时间', '数据类型': 'UINTEGER-32', '数据长度（字节）': '4', '值域': '0~4294967295', '单位': 'ms', '备注': '—'},
            ],
            'preceding_para': 'XX装置仿真输入数据',
            'msg_name': 'XX装置仿真输入数据',
            'meta': {}
        }
    ]
    
    # 测试旧格式ID表
    old_format_id_table = {
        'table_type': 'unknown',
        'headers': ['消息ID', '信息内容'],
        'data_rows': [
            {'消息ID': '0x8000', '信息内容': 'XX装置数据1'},
            {'消息ID': '0x0301', '信息内容': 'XX装置仿真输入数据'},  # 添加这个匹配
        ],
        'preceding_para': '消息ID映射表',
        'msg_name': '消息ID映射表',
        'meta': {}
    }
    
    # 使用TableLinker测试ID表关联
    print("\n[测试2.2] ID表关联（新旧格式）")
    linker = TableLinker()
    
    # 测试新格式ID表
    new_id_tables = [mock_tables[0], mock_tables[1]]
    linked_new = linker.link_tables(new_id_tables)
    
    print(f"新格式ID表关联结果:")
    for table in linked_new:
        msg_name = table.get('msg_name', '')
        meta = table.get('meta', {})
        if meta.get('消息ID'):
            print(f"  ✅ {msg_name} → {meta['消息ID']}")
    
    # 测试旧格式ID表
    old_id_tables = [old_format_id_table, mock_tables[1]]
    linked_old = linker.link_tables(old_id_tables)
    
    print(f"\n旧格式ID表关联结果:")
    for table in linked_old:
        msg_name = table.get('msg_name', '')
        meta = table.get('meta', {})
        if meta.get('消息ID'):
            print(f"  ✅ {msg_name} → {meta['消息ID']}")

def test_config_fallback():
    """测试配置兜底功能"""
    print("\n" + "=" * 80)
    print("[测试] 配置兜底功能")
    print("=" * 80)
    
    doc_path = "word/混合模式协议(公开).docx"
    
    if not os.path.exists(doc_path):
        print(f"[ERROR] 文档不存在: {doc_path}")
        return
    
    # 配置1：字段表配置（包含"参数"和"数据类型"）
    config1 = {
        'groups': [
            {
                'table_type': 'field_def',
                'required_fields': ['参数', '数据类型'],
                'column_roles': {
                    'content': ['参数', '内容'],
                    'type': ['数据类型', '类型']
                }
            }
        ]
    }
    
    # 配置2：ID表配置（包含"ID序号"和"ID定义"）
    config2 = {
        'groups': [
            {
                'table_type': 'message_id',
                'required_fields': ['ID序号', 'ID定义'],
                'column_roles': {
                    'id_value': ['ID序号', '消息ID'],
                    'message_name': ['ID定义', '信息内容']
                }
            }
        ]
    }
    
    # 配置3：完整配置（字段表+ID表）
    config3 = {
        'groups': [
            {
                'table_type': 'field_def',
                'required_fields': ['参数', '数据类型'],
                'column_roles': {
                    'content': ['参数', '内容'],
                    'type': ['数据类型', '类型']
                }
            },
            {
                'table_type': 'message_id',
                'required_fields': ['ID序号', 'ID定义'],
                'column_roles': {
                    'id_value': ['ID序号', '消息ID'],
                    'message_name': ['ID定义', '信息内容']
                }
            }
        ]
    }
    
    print("\n[测试3.1] 字段表配置")
    parser1 = DocumentParser(config=config1)
    result1 = parser1.parse(doc_path)
    
    field_def_count = 0
    for table in result1['tables']:
        if table.get('table_type') == 'field_def':
            field_def_count += 1
    
    print(f"字段表识别数: {field_def_count}")
    
    print("\n[测试3.2] ID表配置")
    parser2 = DocumentParser(config=config2)
    result2 = parser2.parse(doc_path)
    
    message_id_count = 0
    for table in result2['tables']:
        if table.get('table_type') == 'message_id':
            message_id_count += 1
    
    print(f"ID表识别数: {message_id_count}")
    
    print("\n[测试3.3] 完整配置")
    parser3 = DocumentParser(config=config3)
    result3 = parser3.parse(doc_path)
    
    field_def_count3 = 0
    message_id_count3 = 0
    for table in result3['tables']:
        table_type = table.get('table_type')
        if table_type == 'field_def':
            field_def_count3 += 1
        elif table_type == 'message_id':
            message_id_count3 += 1
    
    print(f"字段表识别数: {field_def_count3}, ID表识别数: {message_id_count3}")
    
    # 验证日志记录
    print("\n[测试3.4] 日志记录")
    if parser3.detector.log_records:
        print(f"日志记录数: {len(parser3.detector.log_records)}")
        for record in parser3.detector.log_records:
            if record['status'] == '配置匹配':
                print(f"  ✅ 表{record['table_index']}: {record['status']} - {record['reason']}")
    
    # 验证关键字段提取
    print("\n[测试3.5] 关键字段提取")
    target_table = None
    for table in result3['tables']:
        if 'XX装置仿真输入数据' in table.get('msg_name', ''):
            target_table = table
            break
    
    if target_table:
        expected_fields = ["仿真状态标志位", "XX计时时间"]
        found_fields = []
        
        for row in target_table.get('data_rows', []):
            for key, value in row.items():
                for field in expected_fields:
                    if field in str(value) and field not in found_fields:
                        found_fields.append(field)
                        data_type = row.get('数据类型') or row.get('类型') or 'N/A'
                        print(f"  ✅ 找到字段: {field} / {data_type}")
        
        if len(found_fields) >= 2:
            print(f"  ✅ 关键字段提取完整: {len(found_fields)}/2")
        else:
            print(f"  ⚠️  关键字段提取不完整: {len(found_fields)}/2")

def test_interference_table_filtering():
    """测试干扰表过滤"""
    print("\n" + "=" * 80)
    print("[测试] 干扰表过滤")
    print("=" * 80)
    
    doc_path = "word/混合模式协议(公开).docx"
    
    if not os.path.exists(doc_path):
        print(f"[ERROR] 文档不存在: {doc_path}")
        return
    
    # 无配置
    parser1 = DocumentParser()
    result1 = parser1.parse(doc_path)
    count1 = sum(1 for t in result1['tables'] if t.get('table_type') == 'field_def')
    
    # 有配置
    config = {
        'groups': [
            {
                'table_type': 'field_def',
                'required_fields': ['参数', '数据类型'],
                'column_roles': {
                    'content': ['参数', '内容'],
                    'type': ['数据类型', '类型']
                }
            }
        ]
    }
    
    parser2 = DocumentParser(config=config)
    result2 = parser2.parse(doc_path)
    count2 = sum(1 for t in result2['tables'] if t.get('table_type') == 'field_def')
    
    print(f"无配置字段表数: {count1}")
    print(f"有配置字段表数: {count2}")
    
    if count1 == count2:
        print("  ✅ 配置不影响已有识别结果，干扰表被正确过滤")
    else:
        print("  ⚠️  配置影响了识别结果，需要进一步分析")

if __name__ == "__main__":
    try:
        test_new_format_id_table()
        test_config_fallback()
        test_interference_table_filtering()
        
        print("\n" + "=" * 80)
        print("[测试完成]")
        print("=" * 80)
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 测试失败: {e}")
        print(traceback.format_exc())
        sys.exit(1)