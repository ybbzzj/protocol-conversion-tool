# -*- coding: utf-8 -*-
"""
测试目标消息名称兜底提取功能
"""
import sys
import os
import io
# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from backend.services.table_detector import DocumentParser

def test_target_message_name_extraction():
    """测试目标消息名称兜底提取功能"""
    
    # 测试文档路径
    test_doc = "word/混合模式协议(公开).docx"
    
    if not os.path.exists(test_doc):
        print(f"[ERROR] 测试文档不存在: {test_doc}")
        return False
    
    # 目标消息名称
    target_names = ["XX装置仿真输入数据"]
    
    print(f"[TEST] 测试目标消息名称兜底提取功能")
    print(f"[DOC] 测试文档: {test_doc}")
    print(f"[TARGET] 目标消息名称: {target_names}")
    print("-" * 60)
    
    # 不使用目标名称提取（对照组）
    print("\n[CONTROL] 对照组：不使用目标名称提取")
    parser_normal = DocumentParser()
    result_normal = parser_normal.parse(test_doc)
    tables_normal = result_normal['tables']
    
    print(f"[RESULT] 识别到 {len(tables_normal)} 个表格:")
    for idx, table in enumerate(tables_normal):
        print(f"   表 {idx + 1}: {table.get('msg_name', '未知')} (类型: {table.get('table_type', 'unknown')})")
    
    # 使用目标名称提取（实验组）
    print(f"\n[EXPERIMENT] 实验组：使用目标名称提取 {target_names}")
    parser_target = DocumentParser(target_message_names=target_names)
    result_target = parser_target.parse(test_doc)
    tables_target = result_target['tables']
    
    print(f"[RESULT] 识别到 {len(tables_target)} 个表格:")
    for idx, table in enumerate(tables_target):
        print(f"   表 {idx + 1}: {table.get('msg_name', '未知')} (类型: {table.get('table_type', 'unknown')})")
    
    # 检查是否提取到目标表格
    print("\n[VERIFY] 验证目标表格提取情况:")
    target_found = False
    for table in tables_target:
        msg_name = table.get('msg_name', '')
        if any(target in msg_name for target in target_names):
            print(f"[SUCCESS] 找到目标表格: {msg_name}")
            target_found = True
            
            # 检查关键字段
            data_rows = table.get('data_rows', [])
            print(f"   [DATA] 表格包含 {len(data_rows)} 行数据")
            
            # 查找期望的字段
            expected_fields = ["仿真状态标志位", "XX计时时间"]
            found_fields = []
            
            for row in data_rows:
                for field in expected_fields:
                    # 检查字段名是否在行数据中
                    for key, value in row.items():
                        if field in str(value):
                            if field not in found_fields:
                                found_fields.append(field)
                                print(f"   [SUCCESS] 找到字段: {field}")
                                # 显示该行的数据类型信息
                                if '数据类型' in row:
                                    print(f"      数据类型: {row.get('数据类型', 'N/A')}")
                                if '类型' in row:
                                    print(f"      类型: {row.get('类型', 'N/A')}")
            
            if len(found_fields) >= 2:
                print(f"[SUCCESS] 成功提取到至少 2 个期望字段: {found_fields}")
            else:
                print(f"[WARNING] 只提取到 {len(found_fields)} 个期望字段: {found_fields}")
            
            break
    
    if not target_found:
        print(f"[ERROR] 未找到目标表格: {target_names}")
        return False
    
    # 对比结果
    print("\n[COMPARE] 对比结果:")
    if len(tables_target) > len(tables_normal):
        print(f"[SUCCESS] 使用目标名称后，多提取了 {len(tables_target) - len(tables_normal)} 个表格")
    elif len(tables_target) == len(tables_normal):
        print(f"[INFO] 两种方式提取的表格数量相同")
    else:
        print(f"[WARNING] 使用目标名称后，少提取了 {len(tables_normal) - len(tables_target)} 个表格")
    
    return True

if __name__ == "__main__":
    try:
        success = test_target_message_name_extraction()
        if success:
            print("\n[SUCCESS] 测试通过")
        else:
            print("\n[ERROR] 测试失败")
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 测试出错: {e}")
        print(traceback.format_exc())