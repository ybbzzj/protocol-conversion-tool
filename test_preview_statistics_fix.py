# -*- coding: utf-8 -*-
"""
测试预览统计修复功能
验证是否正确遍历所有有效字段表
"""
import sys
import os
import io
# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from backend.services.table_detector import DocumentParser
from backend.routes.mapping import _extract_fields_and_data_from_raw_tables

def test_preview_statistics_fix():
    """测试预览统计修复功能"""
    
    # 测试文档路径
    test_doc = "word/混合模式协议(公开).docx"
    
    if not os.path.exists(test_doc):
        print(f"[ERROR] 测试文档不存在: {test_doc}")
        return False
    
    # 目标消息名称
    target_names = ["XX装置仿真输入数据"]
    
    print(f"[TEST] 测试预览统计修复功能")
    print(f"[DOC] 测试文档: {test_doc}")
    print(f"[TARGET] 目标消息名称: {target_names}")
    print("-" * 60)
    
    # 使用目标名称提取
    print(f"\n[EXTRACT] 使用目标名称提取表格")
    parser = DocumentParser(target_message_names=target_names)
    result = parser.parse(test_doc)
    raw_tables = result['tables']
    
    print(f"[RESULT] 识别到 {len(raw_tables)} 个表格:")
    for idx, table in enumerate(raw_tables):
        table_type = table.get('table_type', 'unknown')
        msg_name = table.get('msg_name', '未知')
        data_rows_count = len(table.get('data_rows', []))
        print(f"   表 {idx + 1}: {msg_name} (类型: {table_type}, 数据行: {data_rows_count})")
    
    # 测试修复后的预览统计功能
    print(f"\n[PREVIEW] 测试修复后的预览统计功能")
    extracted_fields, table_data = _extract_fields_and_data_from_raw_tables(raw_tables)
    
    print(f"[RESULT] 提取到 {len(extracted_fields)} 个唯一字段:")
    if extracted_fields:
        for field in extracted_fields:
            print(f"   - {field}")
    else:
        print("   [WARNING] 未提取到任何字段")
    
    print(f"\n[DATA] 表格数据预览:")
    for idx, data in enumerate(table_data):
        table_name = data.get('表格名称', 'Unknown')
        print(f"   表 {idx + 1}: {table_name}")
        # 显示部分字段数据
        for key, value in list(data.items())[:5]:
            if key not in ['表格名称', '行号']:
                print(f"      {key}: {value}")
    
    # 验证关键字段是否被提取
    print(f"\n[VERIFY] 验证关键字段提取情况:")
    expected_fields = ["仿真状态标志位", "XX计时时间", "参数", "数据类型", "单位"]
    found_fields = []
    
    for field in expected_fields:
        if any(field in extracted_field for extracted_field in extracted_fields):
            found_fields.append(field)
            print(f"   [SUCCESS] 找到字段: {field}")
        else:
            print(f"   [WARNING] 未找到字段: {field}")
    
    # 统计有效字段表数量
    valid_field_tables = [t for t in raw_tables if t.get('table_type') in ('field_def', '', None)]
    print(f"\n[STATS] 统计信息:")
    print(f"   总表格数: {len(raw_tables)}")
    print(f"   有效字段表数: {len(valid_field_tables)}")
    print(f"   提取字段数: {len(extracted_fields)}")
    print(f"   预览表格数: {len(table_data)}")
    
    # 验证结果
    if len(extracted_fields) == 0:
        print(f"\n[ERROR] 预览统计修复失败：字段数为零")
        return False
    
    if len(found_fields) >= 3:
        print(f"\n[SUCCESS] 预览统计修复成功：找到 {len(found_fields)}/{len(expected_fields)} 个期望字段")
        return True
    else:
        print(f"\n[WARNING] 预览统计可能存在问题：只找到 {len(found_fields)}/{len(expected_fields)} 个期望字段")
        return False

if __name__ == "__main__":
    try:
        success = test_preview_statistics_fix()
        if success:
            print("\n[SUCCESS] 测试通过")
        else:
            print("\n[ERROR] 测试失败")
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 测试出错: {e}")
        print(traceback.format_exc())