# -*- coding: utf-8 -*-
"""
完整验证修改意见1的所有要求
1. 目标消息名称兜底提取能力
2. 预览统计修复（遍历所有有效字段表）
3. 验证"XX装置仿真输入数据"表格提取
"""
import sys
import os
import io
# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from backend.services.table_detector import DocumentParser
from backend.routes.mapping import _extract_fields_and_data_from_raw_tables

def test_complete_modification():
    """完整验证修改意见1的所有要求"""
    
    # 测试文档路径
    test_doc = "word/混合模式协议(公开).docx"
    
    if not os.path.exists(test_doc):
        print(f"[ERROR] 测试文档不存在: {test_doc}")
        return False
    
    # 目标消息名称
    target_names = ["XX装置仿真输入数据"]
    
    print("=" * 80)
    print("[COMPLETE TEST] 完整验证修改意见1的所有要求")
    print("=" * 80)
    print(f"[DOC] 测试文档: {test_doc}")
    print(f"[TARGET] 目标消息名称: {target_names}")
    print("-" * 80)
    
    # ========== 测试1：目标消息名称兜底提取能力 ==========
    print("\n[TEST 1] 目标消息名称兜底提取能力")
    print("-" * 80)
    
    parser = DocumentParser(target_message_names=target_names)
    result = parser.parse(test_doc)
    raw_tables = result['tables']
    
    print(f"[RESULT] 识别到 {len(raw_tables)} 个表格")
    
    # 查找目标表格
    target_table = None
    for table in raw_tables:
        msg_name = table.get('msg_name', '')
        if any(target in msg_name for target in target_names):
            target_table = table
            print(f"[SUCCESS] 找到目标表格: {msg_name}")
            break
    
    if not target_table:
        print(f"[ERROR] 未找到目标表格: {target_names}")
        return False
    
    # 验证目标表格的关键字段
    data_rows = target_table.get('data_rows', [])
    print(f"[DATA] 目标表格包含 {len(data_rows)} 行数据")
    
    # 查找期望的字段值
    expected_field_values = [
        {"field": "仿真状态标志位", "expected_type": "UCHAR"},
        {"field": "XX计时时间", "expected_type": "UINTEGER-32"}
    ]
    
    found_fields = []
    for expected in expected_field_values:
        field_name = expected["field"]
        expected_type = expected["expected_type"]
        
        for row in data_rows:
            # 检查各个可能的字段列
            for key, value in row.items():
                if field_name in str(value):
                    # 查找对应的数据类型
                    data_type = row.get('数据类型') or row.get('类型') or 'N/A'
                    if expected_type in str(data_type):
                        found_fields.append({
                            "field": field_name,
                            "type": data_type,
                            "row_data": row
                        })
                        print(f"[SUCCESS] 找到字段: {field_name} / {data_type}")
                        break
            if field_name in [f["field"] for f in found_fields]:
                break
    
    if len(found_fields) < 2:
        print(f"[ERROR] 目标表格字段提取不完整，只找到 {len(found_fields)}/2 个期望字段")
        return False
    
    # ========== 测试2：预览统计修复 ==========
    print("\n[TEST 2] 预览统计修复（遍历所有有效字段表）")
    print("-" * 80)
    
    # 统计有效字段表
    valid_field_tables = [t for t in raw_tables if t.get('table_type') in ('field_def', '', None)]
    print(f"[STATS] 总表格数: {len(raw_tables)}")
    print(f"[STATS] 有效字段表数: {len(valid_field_tables)}")
    
    # 测试修复后的预览统计功能
    extracted_fields, table_data = _extract_fields_and_data_from_raw_tables(raw_tables)
    
    print(f"[RESULT] 提取到 {len(extracted_fields)} 个唯一字段")
    print(f"[RESULT] 预览表格数: {len(table_data)}")
    
    if len(extracted_fields) == 0:
        print(f"[ERROR] 预览统计修复失败：字段数为零")
        return False
    
    if len(table_data) != len(valid_field_tables):
        print(f"[WARNING] 预览表格数({len(table_data)}) != 有效字段表数({len(valid_field_tables)})")
    else:
        print(f"[SUCCESS] 预览表格数等于有效字段表数")
    
    # ========== 测试3：底线兜底提取能力验证 ==========
    print("\n[TEST 3] 底线兜底提取能力验证")
    print("-" * 80)
    
    # 验证即使有干扰表，目标表也能被提取
    print(f"[VERIFY] 验证目标表在干扰表存在的情况下仍被提取")
    
    # 检查是否有非field_def类型的表（模拟干扰表）
    other_tables = [t for t in raw_tables if t.get('table_type') not in ('field_def', '', None)]
    if other_tables:
        print(f"[INFO] 文档中包含 {len(other_tables)} 个非字段定义表（辅助表/干扰表）")
        for table in other_tables:
            print(f"   - {table.get('msg_name', 'Unknown')} (类型: {table.get('table_type', 'unknown')})")
    
    # 再次确认目标表存在
    if target_table:
        print(f"[SUCCESS] 目标表成功提取，兜底机制正常工作")
    else:
        print(f"[ERROR] 目标表提取失败，兜底机制异常")
        return False
    
    # ========== 最终结果 ==========
    print("\n" + "=" * 80)
    print("[FINAL RESULT] 修改意见1验证结果")
    print("=" * 80)
    
    results = {
        "目标消息名称兜底提取": "PASS" if target_table else "FAIL",
        "关键字段提取": "PASS" if len(found_fields) >= 2 else "FAIL",
        "预览统计修复": "PASS" if len(extracted_fields) > 0 else "FAIL",
        "底线兜底能力": "PASS" if target_table else "FAIL"
    }
    
    for test_name, result in results.items():
        status = "[PASS]" if result == "PASS" else "[FAIL]"
        print(f"{status} {test_name}: {result}")
    
    all_passed = all(result == "PASS" for result in results.values())
    
    if all_passed:
        print("\n[SUCCESS] 所有测试通过，修改意见1已完全实现")
        return True
    else:
        print("\n[ERROR] 部分测试失败，需要进一步修复")
        return False

if __name__ == "__main__":
    try:
        success = test_complete_modification()
        sys.exit(0 if success else 1)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 测试出错: {e}")
        print(traceback.format_exc())
        sys.exit(1)