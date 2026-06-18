# -*- coding: utf-8 -*-
"""
综合测试：展示修复前后的对比效果
包含多个测试场景和前后对比
"""
import sys
import os
import io
# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from backend.services.table_detector import DocumentParser
from backend.routes.mapping import _extract_fields_and_data_from_raw_tables

def test_scenario_1_basic_extraction():
    """测试场景1：基础提取功能对比"""
    print("=" * 80)
    print("[场景1] 基础提取功能对比")
    print("=" * 80)
    
    test_doc = "word/混合模式协议(公开).docx"
    target_names = ["XX装置仿真输入数据"]
    
    # 修复前：不使用目标名称
    print("\n[修复前] 不使用目标名称提取:")
    parser_before = DocumentParser()
    result_before = parser_before.parse(test_doc)
    tables_before = result_before['tables']
    
    print(f"  识别表格数: {len(tables_before)}")
    for idx, table in enumerate(tables_before):
        print(f"    表{idx+1}: {table.get('msg_name', '未知')} ({table.get('table_type', 'unknown')})")
    
    # 修复后：使用目标名称
    print(f"\n[修复后] 使用目标名称 '{target_names}':")
    parser_after = DocumentParser(target_message_names=target_names)
    result_after = parser_after.parse(test_doc)
    tables_after = result_after['tables']
    
    print(f"  识别表格数: {len(tables_after)}")
    for idx, table in enumerate(tables_after):
        print(f"    表{idx+1}: {table.get('msg_name', '未知')} ({table.get('table_type', 'unknown')})")
    
    # 对比结果
    print(f"\n[对比结果]:")
    if len(tables_after) == len(tables_before):
        print(f"  ✅ 表格数量相同: {len(tables_after)}个")
    else:
        print(f"  ⚠️  表格数量变化: {len(tables_before)} → {len(tables_after)}")
    
    # 查找目标表
    target_table_before = None
    target_table_after = None
    
    for table in tables_before:
        if any(target in table.get('msg_name', '') for target in target_names):
            target_table_before = table
            break
    
    for table in tables_after:
        if any(target in table.get('msg_name', '') for target in target_names):
            target_table_after = table
            break
    
    if target_table_before and target_table_after:
        print(f"  ✅ 前后都找到目标表: {target_table_after.get('msg_name', '')}")
        rows_before = len(target_table_before.get('data_rows', []))
        rows_after = len(target_table_after.get('data_rows', []))
        print(f"  📊 数据行数: {rows_before} → {rows_after}")
    elif target_table_after:
        print(f"  ✅ 修复后找到目标表: {target_table_after.get('msg_name', '')}")
        print(f"  ❌ 修复前未找到目标表")
    else:
        print(f"  ❌ 前后都未找到目标表")
    
    return {
        'before': len(tables_before),
        'after': len(tables_after),
        'target_found_before': target_table_before is not None,
        'target_found_after': target_table_after is not None
    }

def test_scenario_2_preview_statistics():
    """测试场景2：预览统计修复对比"""
    print("\n" + "=" * 80)
    print("[场景2] 预览统计修复对比")
    print("=" * 80)
    
    test_doc = "word/混合模式协议(公开).docx"
    target_names = ["XX装置仿真输入数据"]
    
    parser = DocumentParser(target_message_names=target_names)
    result = parser.parse(test_doc)
    raw_tables = result['tables']
    
    print(f"\n[原始数据] 总表格数: {len(raw_tables)}")
    
    # 统计表格类型
    field_def_count = sum(1 for t in raw_tables if t.get('table_type') in ('field_def', '', None))
    other_count = len(raw_tables) - field_def_count
    
    print(f"  字段定义表: {field_def_count}个")
    print(f"  其他类型表: {other_count}个")
    
    # 修复后的预览统计
    print(f"\n[修复后] 遍历所有有效字段表:")
    extracted_fields, table_data = _extract_fields_and_data_from_raw_tables(raw_tables)
    
    print(f"  提取字段数: {len(extracted_fields)}")
    print(f"  预览表格数: {len(table_data)}")
    
    # 模拟修复前的行为（只看第一张表）
    print(f"\n[修复前] 只看第一张表:")
    if raw_tables:
        first_table = raw_tables[0]
        first_table_type = first_table.get('table_type', 'unknown')
        first_table_name = first_table.get('msg_name', 'Unknown')
        first_table_rows = first_table.get('data_rows', [])
        
        print(f"  第一张表: {first_table_name} (类型: {first_table_type})")
        print(f"  数据行数: {len(first_table_rows)}")
        
        if first_table_rows:
            first_row_fields = list(first_table_rows[0].keys())
            print(f"  提取字段数: {len(first_row_fields)}")
        else:
            print(f"  提取字段数: 0 (第一张表无数据)")
    
    # 对比结果
    print(f"\n[对比结果]:")
    if len(extracted_fields) > 0:
        print(f"  ✅ 修复后正确提取字段: {len(extracted_fields)}个")
        if len(table_data) == field_def_count:
            print(f"  ✅ 预览表格数等于有效字段表数: {len(table_data)}个")
        else:
            print(f"  ⚠️  预览表格数({len(table_data)}) ≠ 有效字段表数({field_def_count})")
    else:
        print(f"  ❌ 修复后字段数为零")
    
    return {
        'total_tables': len(raw_tables),
        'field_def_count': field_def_count,
        'extracted_fields': len(extracted_fields),
        'preview_tables': len(table_data)
    }

def test_scenario_3_multiple_targets():
    """测试场景3：多个目标名称测试"""
    print("\n" + "=" * 80)
    print("[场景3] 多个目标名称测试")
    print("=" * 80)
    
    test_doc = "word/混合模式协议(公开).docx"
    target_names_list = [
        ["XX装置仿真输入数据"],
        ["测试结果"],
        ["XX装置数据1", "测试数据2"],
        []  # 空目标列表
    ]
    
    results = []
    
    for idx, target_names in enumerate(target_names_list):
        print(f"\n[测试{idx+1}] 目标名称: {target_names if target_names else '无'}")
        
        parser = DocumentParser(target_message_names=target_names)
        result = parser.parse(test_doc)
        tables = result['tables']
        
        # 查找匹配的表格
        matched_tables = []
        for table in tables:
            msg_name = table.get('msg_name', '')
            if not target_names:
                # 无目标名称时，统计所有字段定义表
                if table.get('table_type') in ('field_def', '', None):
                    matched_tables.append(msg_name)
            else:
                # 有目标名称时，查找匹配的表
                if any(target in msg_name for target in target_names):
                    matched_tables.append(msg_name)
        
        print(f"  识别表格数: {len(tables)}")
        print(f"  匹配表格数: {len(matched_tables)}")
        if matched_tables:
            print(f"  匹配表格: {', '.join(matched_tables)}")
        else:
            print(f"  匹配表格: 无")
        
        results.append({
            'targets': target_names,
            'total_tables': len(tables),
            'matched_count': len(matched_tables),
            'matched_tables': matched_tables
        })
    
    # 对比结果
    print(f"\n[对比结果]:")
    for idx, result in enumerate(results):
        targets = result['targets']
        matched_count = result['matched_count']
        if targets:
            print(f"  测试{idx+1}: 目标{len(targets)}个 → 匹配{matched_count}个表")
        else:
            print(f"  测试{idx+1}: 无目标 → 全部{result['total_tables']}个字段定义表")
    
    return results

def test_scenario_4_field_extraction():
    """测试场景4：关键字段提取验证"""
    print("\n" + "=" * 80)
    print("[场景4] 关键字段提取验证")
    print("=" * 80)
    
    test_doc = "word/混合模式协议(公开).docx"
    target_names = ["XX装置仿真输入数据"]
    
    expected_fields = [
        {"name": "仿真状态标志位", "type": "UCHAR"},
        {"name": "XX计时时间", "type": "UINTEGER-32"}
    ]
    
    print(f"\n[目标表格] {target_names[0]}")
    print(f"[期望字段]")
    for field in expected_fields:
        print(f"  - {field['name']} / {field['type']}")
    
    parser = DocumentParser(target_message_names=target_names)
    result = parser.parse(test_doc)
    tables = result['tables']
    
    # 查找目标表
    target_table = None
    for table in tables:
        if any(target in table.get('msg_name', '') for target in target_names):
            target_table = table
            break
    
    if not target_table:
        print(f"\n[ERROR] 未找到目标表格")
        return False
    
    data_rows = target_table.get('data_rows', [])
    print(f"\n[实际提取] 数据行数: {len(data_rows)}")
    
    # 验证字段提取
    found_fields = []
    for expected in expected_fields:
        field_name = expected["name"]
        expected_type = expected["type"]
        
        for row in data_rows:
            for key, value in row.items():
                if field_name in str(value):
                    data_type = row.get('数据类型') or row.get('类型') or 'N/A'
                    if expected_type in str(data_type):
                        found_fields.append({
                            "name": field_name,
                            "type": data_type,
                            "found": True
                        })
                        break
            if field_name in [f["name"] for f in found_fields]:
                break
    
    print(f"\n[提取结果]")
    for field in found_fields:
        status = "✅" if field["found"] else "❌"
        print(f"  {status} {field['name']} / {field['type']}")
    
    # 对比结果
    print(f"\n[对比结果]:")
    success_count = sum(1 for f in found_fields if f["found"])
    if success_count == len(expected_fields):
        print(f"  ✅ 成功提取所有期望字段: {success_count}/{len(expected_fields)}")
    else:
        print(f"  ⚠️  部分字段提取失败: {success_count}/{len(expected_fields)}")
    
    return {
        'expected_count': len(expected_fields),
        'found_count': success_count,
        'success_rate': success_count / len(expected_fields) if expected_fields else 0
    }

def generate_summary_report():
    """生成汇总报告"""
    print("\n" + "=" * 80)
    print("[汇总报告] 修复效果总结")
    print("=" * 80)
    
    # 执行所有测试场景
    scenario1_result = test_scenario_1_basic_extraction()
    scenario2_result = test_scenario_2_preview_statistics()
    scenario3_result = test_scenario_3_multiple_targets()
    scenario4_result = test_scenario_4_field_extraction()
    
    # 生成汇总
    print("\n" + "=" * 80)
    print("[最终汇总] 所有测试场景结果")
    print("=" * 80)
    
    print(f"\n[场景1] 基础提取功能:")
    print(f"  修复前表格数: {scenario1_result['before']}")
    print(f"  修复后表格数: {scenario1_result['after']}")
    print(f"  目标表查找(前): {'✅ 成功' if scenario1_result['target_found_before'] else '❌ 失败'}")
    print(f"  目标表查找(后): {'✅ 成功' if scenario1_result['target_found_after'] else '❌ 失败'}")
    
    print(f"\n[场景2] 预览统计修复:")
    print(f"  总表格数: {scenario2_result['total_tables']}")
    print(f"  有效字段表数: {scenario2_result['field_def_count']}")
    print(f"  提取字段数: {scenario2_result['extracted_fields']}")
    print(f"  预览表格数: {scenario2_result['preview_tables']}")
    print(f"  统计修复: {'✅ 成功' if scenario2_result['extracted_fields'] > 0 else '❌ 失败'}")
    
    print(f"\n[场景3] 多目标名称测试:")
    for idx, result in enumerate(scenario3_result):
        targets_str = ', '.join(result['targets']) if result['targets'] else '无'
        print(f"  测试{idx+1} ({targets_str}): 匹配{result['matched_count']}个表")
    
    print(f"\n[场景4] 关键字段提取:")
    print(f"  期望字段数: {scenario4_result['expected_count']}")
    print(f"  实际提取数: {scenario4_result['found_count']}")
    print(f"  成功率: {scenario4_result['success_rate']*100:.1f}%")
    print(f"  字段提取: {'✅ 成功' if scenario4_result['found_count'] >= 2 else '❌ 失败'}")
    
    # 总体评估
    print(f"\n[总体评估]")
    all_passed = (
        scenario1_result['target_found_after'] and
        scenario2_result['extracted_fields'] > 0 and
        scenario4_result['found_count'] >= 2
    )
    
    if all_passed:
        print(f"  ✅ 所有核心功能测试通过")
        print(f"  ✅ 修复效果显著，功能完全符合要求")
    else:
        print(f"  ⚠️  部分功能需要进一步优化")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = generate_summary_report()
        sys.exit(0 if success else 1)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 测试出错: {e}")
        print(traceback.format_exc())
        sys.exit(1)