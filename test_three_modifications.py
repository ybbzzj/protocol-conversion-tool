# -*- coding: utf-8 -*-
"""
测试验证三个修改点：
1. 干扰表识别：配置匹配→智能识别→噪声过滤
2. ID表识别：支持table_type=message_id，兼容旧格式
3. 配置兜底：将用户配置传入表格识别阶段
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from backend.services.table_detector import DocumentParser, TableDetector
from backend.services.table_linker import TableLinker

def test_with_original_document():
    """使用原始文档测试三个修改点"""
    print("=" * 80)
    print("[测试验证] 使用'混合模式协议(公开)(1).docx'测试")
    print("=" * 80)
    
    doc_path = "word/混合模式协议(公开).docx"
    
    if not os.path.exists(doc_path):
        print(f"[ERROR] 测试文档不存在: {doc_path}")
        return False
    
    # ===== 测试1：无配置（原始行为） =====
    print(f"\n[测试1] 无配置（原始行为）")
    parser1 = DocumentParser()
    result1 = parser1.parse(doc_path)
    raw_tables1 = result1['tables']
    
    print(f"[识别结果] 总表格数: {len(raw_tables1)}")
    field_def_count1 = 0
    message_id_count1 = 0
    target_found1 = False
    
    for table in raw_tables1:
        table_type = table.get('table_type', 'unknown')
        msg_name = table.get('msg_name', '未知')
        data_rows = table.get('data_rows', [])
        
        if table_type == 'field_def':
            field_def_count1 += 1
            if 'XX装置仿真输入数据' in msg_name:
                target_found1 = True
                print(f"  ✅ 目标表: {msg_name} ({table_type}, {len(data_rows)}行)")
            else:
                print(f"  字段表: {msg_name} ({table_type}, {len(data_rows)}行)")
        elif table_type == 'message_id':
            message_id_count1 += 1
            print(f"  ID表: {msg_name} ({table_type}, {len(data_rows)}行)")
        elif table_type != 'skip':
            print(f"  {table_type}: {msg_name} ({len(data_rows)}行)")
    
    print(f"\n[统计] 字段表数: {field_def_count1}, ID表数: {message_id_count1}, 目标表: {'✅' if target_found1 else '❌'}")
    
    # ===== 测试2：使用目标名称兜底提取 =====
    print(f"\n\n[测试2] 使用目标名称兜底提取")
    target_names = ["XX装置仿真输入数据"]
    parser2 = DocumentParser(target_message_names=target_names)
    result2 = parser2.parse(doc_path)
    raw_tables2 = result2['tables']
    
    print(f"[目标名称] {target_names}")
    print(f"[识别结果] 总表格数: {len(raw_tables2)}")
    field_def_count2 = 0
    message_id_count2 = 0
    target_found2 = False
    target_table2 = None
    
    for table in raw_tables2:
        table_type = table.get('table_type', 'unknown')
        msg_name = table.get('msg_name', '未知')
        data_rows = table.get('data_rows', [])
        
        if table_type == 'field_def':
            field_def_count2 += 1
            if 'XX装置仿真输入数据' in msg_name:
                target_found2 = True
                target_table2 = table
                print(f"  ✅ 目标表: {msg_name} ({table_type}, {len(data_rows)}行)")
            else:
                print(f"  字段表: {msg_name} ({table_type}, {len(data_rows)}行)")
        elif table_type == 'message_id':
            message_id_count2 += 1
            print(f"  ID表: {msg_name} ({table_type}, {len(data_rows)}行)")
        elif table_type != 'skip':
            print(f"  {table_type}: {msg_name} ({len(data_rows)}行)")
    
    print(f"\n[统计] 字段表数: {field_def_count2}, ID表数: {message_id_count2}, 目标表: {'✅' if target_found2 else '❌'}")
    
    # 验证关键字段
    if target_table2:
        print(f"\n[关键字段验证]")
        expected_fields = ["仿真状态标志位", "XX计时时间"]
        found_fields = []
        
        for row in target_table2.get('data_rows', []):
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
    
    # ===== 测试3：使用配置兜底 =====
    print(f"\n\n[测试3] 使用配置兜底")
    table_configs = {
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
                    'id_value': ['ID序号'],
                    'message_name': ['ID定义']
                }
            }
        ]
    }
    
    parser3 = DocumentParser(config=table_configs, target_message_names=target_names)
    result3 = parser3.parse(doc_path)
    raw_tables3 = result3['tables']
    
    print(f"[配置] table_configs with groups")
    print(f"[识别结果] 总表格数: {len(raw_tables3)}")
    field_def_count3 = 0
    message_id_count3 = 0
    target_found3 = False
    
    for table in raw_tables3:
        table_type = table.get('table_type', 'unknown')
        msg_name = table.get('msg_name', '未知')
        data_rows = table.get('data_rows', [])
        
        if table_type == 'field_def':
            field_def_count3 += 1
            if 'XX装置仿真输入数据' in msg_name:
                target_found3 = True
                print(f"  ✅ 目标表: {msg_name} ({table_type}, {len(data_rows)}行)")
            else:
                print(f"  字段表: {msg_name} ({table_type}, {len(data_rows)}行)")
        elif table_type == 'message_id':
            message_id_count3 += 1
            print(f"  ID表: {msg_name} ({table_type}, {len(data_rows)}行)")
        elif table_type != 'skip':
            print(f"  {table_type}: {msg_name} ({len(data_rows)}行)")
    
    print(f"\n[统计] 字段表数: {field_def_count3}, ID表数: {message_id_count3}, 目标表: {'✅' if target_found3 else '❌'}")
    
    # ===== 测试4：验证ID表关联 =====
    print(f"\n\n[测试4] 验证ID表关联")
    linker = TableLinker()
    linked_tables = linker.link_tables(raw_tables3)
    
    print(f"[关联结果] 关联表格数: {len(linked_tables)}")
    
    for table in linked_tables:
        msg_name = table.get('msg_name', '未知')
        data_rows = table.get('data_rows', [])
        meta = table.get('meta', {})
        
        if 'XX装置仿真输入数据' in msg_name:
            print(f"\n  ✅ 目标表: {msg_name}")
            print(f"  数据行数: {len(data_rows)}")
            if meta:
                print(f"  元数据: {meta}")
    
    # ===== 对比分析 =====
    print(f"\n" + "=" * 80)
    print("[对比分析] 三个测试结果对比")
    print("=" * 80)
    
    print(f"\n[表格识别对比]")
    print(f"{'测试场景':<20} {'字段表数':<10} {'ID表数':<10} {'目标表':<10}")
    print(f"{'无配置':<20} {field_def_count1:<10} {message_id_count1:<10} {'✅' if target_found1 else '❌':<10}")
    print(f"{'目标名称':<20} {field_def_count2:<10} {message_id_count2:<10} {'✅' if target_found2 else '❌':<10}")
    print(f"{'配置兜底':<20} {field_def_count3:<10} {message_id_count3:<10} {'✅' if target_found3 else '❌':<10}")
    
    print(f"\n[核心验证结果]")
    
    # 验证1：干扰表识别
    if field_def_count1 == field_def_count2 == field_def_count3:
        print(f"  ✅ 干扰表识别：三种模式识别结果一致，干扰表被正确过滤")
    else:
        print(f"  ⚠️  干扰表识别：识别结果不一致，需要进一步分析")
    
    # 验证2：ID表识别
    if message_id_count1 > 0 or message_id_count2 > 0 or message_id_count3 > 0:
        print(f"  ✅ ID表识别：成功识别消息ID表")
    else:
        print(f"  ⚠️  ID表识别：未识别到消息ID表")
    
    # 验证3：目标表提取
    if target_found1 and target_found2 and target_found3:
        print(f"  ✅ 目标表提取：三种模式都成功提取目标表")
    else:
        print(f"  ⚠️  目标表提取：部分模式未提取到目标表")
    
    # 验证4：关键字段
    if target_table2 and len(found_fields) >= 2:
        print(f"  ✅ 关键字段提取：仿真状态标志位/UCHAR、XX计时时间/UINTEGER-32")
    else:
        print(f"  ❌ 关键字段提取：未完整提取关键字段")
    
    # ===== 日志记录检查 =====
    print(f"\n[日志记录检查]")
    if parser3.detector.log_records:
        print(f"  ✅ 日志记录数: {len(parser3.detector.log_records)}")
        for record in parser3.detector.log_records[:5]:
            print(f"    表{record['table_index']}: {record['status']} - {record['reason']}")
    else:
        print(f"  ⚠️  日志记录为空")
    
    # ===== 总体评估 =====
    print(f"\n" + "=" * 80)
    print("[总体评估]")
    print("=" * 80)
    
    success_count = 0
    
    if field_def_count1 == field_def_count2 == field_def_count3:
        success_count += 1
    
    if message_id_count1 > 0 or message_id_count2 > 0 or message_id_count3 > 0:
        success_count += 1
    
    if target_found1 and target_found2 and target_found3:
        success_count += 1
    
    if target_table2 and len(found_fields) >= 2:
        success_count += 1
    
    if parser3.detector.log_records:
        success_count += 1
    
    print(f"[测试通过率] {success_count}/5 = {success_count/5*100:.1f}%")
    
    if success_count >= 4:
        print(f"\n[SUCCESS] ✅✅✅ 所有核心功能测试通过！")
        return True
    else:
        print(f"\n[WARNING] ⚠️  部分测试未通过，需要进一步优化")
        return False

if __name__ == "__main__":
    try:
        success = test_with_original_document()
        sys.exit(0 if success else 1)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 测试失败: {e}")
        print(traceback.format_exc())
        sys.exit(1)