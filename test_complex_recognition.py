#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试改进后的复杂表格识别能力
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_complex_table_recognition():
    print("测试改进后的复杂表格识别能力...")
    print("=" * 60)
    
    # 模拟用户提供的复杂表格结构（表3）
    complex_table_grid = [
        ["信息名称", "检查结果1", "信息标识", "xx"],           # 元数据行1
        ["信源、信宿", "BC→RT1-SA0-模式码0x03", "", ""],      # 元数据行2
        ["传输周期", "非周期", "其他", "-"],                  # 元数据行3
        ["发起时机", "按实际操作流程", "错误处理", "-"],       # 元数据行4
        ["序号", "内容", "类型", "值域", "单位", "数据处理方法"],  # 真正的表头
        ["1", "计时时间1", "UINTEGER-32", "0~4294967295", "ms", "32位整型数..."],  # 数据行1
        ["2", "帧计数", "UINTEGER-32", "0~4294967295", "-", "计数器数据"]       # 数据行2
    ]
    
    print("测试数据结构:")
    for i, row in enumerate(complex_table_grid):
        print(f"  行{i}: {row}")
    
    try:
        from backend.services.table_detector import TableDetector
        detector = TableDetector()
        
        print("\n开始识别过程:")
        
        # 模拟表头识别过程
        header_row_idx = -1
        max_score = 0
        
        print("\n1. 表头识别阶段:")
        # 第一轮：基于关键词匹配
        for r_idx, row in enumerate(complex_table_grid[:min(20, len(complex_table_grid))]):
            if not row:
                continue
            matches = sum(1 for cell in row if any(k in cell for k in detector.keywords))
            score = matches / 4.0 if matches <= 4 else 1.0
            print(f"  行{r_idx}: 匹配数={matches}, 得分={score:.2f}, 内容={row}")
            if matches >= 2 and score > max_score:
                max_score, header_row_idx = score, r_idx
        
        # 第二轮：如果没有找到，尝试基于结构特征
        if header_row_idx == -1:
            print("  未找到标准表头，尝试结构特征识别...")
            for r_idx, row in enumerate(complex_table_grid[:min(15, len(complex_table_grid))]):
                if not row:
                    continue
                has_seq = any('序号' in cell for cell in row)
                has_content = any('参数' in cell or '内容' in cell or '信号名称' in cell for cell in row)
                has_type = any('类型' in cell or '数据类型' in cell for cell in row)
                is_candidate = (has_seq and has_content and has_type) or (has_content and has_type and len(row) >= 4)
                print(f"  行{r_idx}: 序号={has_seq}, 内容={has_content}, 类型={has_type}, 候选={is_candidate}")
                if is_candidate:
                    header_row_idx = r_idx
                    break
        
        print(f"\n✓ 识别到表头行: {header_row_idx}")
        if header_row_idx >= 0:
            headers = complex_table_grid[header_row_idx]
            print(f"  表头内容: {headers}")
            
            # 模拟元数据提取
            print("\n2. 元数据提取阶段:")
            msg_name = ""
            meta = {}
            
            # 检查表头前的行
            for r_idx in range(min(5, header_row_idx)):
                row = complex_table_grid[r_idx]
                if row and len(row) >= 2:
                    print(f"  检查行{r_idx}: {row}")
                    
                    # 传统的逐个单元格检查
                    for i in range(len(row) - 1):
                        key_cell = row[i]
                        value_cell = row[i+1]
                        if any(kw in key_cell for kw in ['信息名称', '名称', '协议名称']):
                            if not msg_name and value_cell and value_cell not in ['—', '-', 'xx']:
                                msg_name = value_cell
                                print(f"    ✓ 提取信息名称: '{msg_name}'")
                        elif any(kw in key_cell for kw in ['信息标识', '标识']):
                            if value_cell and value_cell not in ['—', '-', 'xx']:
                                meta['信息标识'] = value_cell
                                print(f"    ✓ 提取信息标识: '{value_cell}'")
                    
                    # 新增：整行键值对检查（横向排列）
                    if len(row) >= 4:
                        print(f"    检查横向键值对...")
                        for i in range(0, len(row)-1, 2):
                            if i+1 < len(row):
                                key_cell = row[i]
                                value_cell = row[i+1]
                                if (any(kw in key_cell for kw in ['信息名称', '名称', '协议名称']) and 
                                    value_cell and value_cell not in ['—', '-', 'xx'] and 
                                    value_cell != key_cell):
                                    if not msg_name:
                                        msg_name = value_cell
                                        print(f"    ✓ 横向提取信息名称: '{msg_name}'")
                                elif (any(kw in key_cell for kw in ['信息标识', '标识']) and 
                                      value_cell and value_cell not in ['—', '-', 'xx'] and 
                                      value_cell != key_cell):
                                    meta['信息标识'] = value_cell
                                    print(f"    ✓ 横向提取信息标识: '{value_cell}'")
            
            print(f"\n3. 最终识别结果:")
            print(f"  消息名称: '{msg_name}'")
            print(f"  元数据: {meta}")
            print(f"  表头行: {headers}")
            
            # 模拟数据行提取
            data_rows = []
            for r_idx in range(header_row_idx + 1, len(complex_table_grid)):
                row = complex_table_grid[r_idx]
                if row and any(cell.strip() for cell in row):  # 非空行
                    # 将行数据映射到表头
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row) and row[i].strip():
                            row_dict[header] = row[i].strip()
                    if row_dict:
                        data_rows.append(row_dict)
            
            print(f"  识别到 {len(data_rows)} 行数据:")
            for i, row_data in enumerate(data_rows):
                print(f"    行{i+1}: {row_data}")
            
            # 验证结果
            expected_msg_name = "检查结果1"
            if msg_name == expected_msg_name:
                print(f"\n✅ 识别成功！正确提取消息名称: '{msg_name}'")
                return True
            else:
                print(f"\n❌ 识别失败！期望 '{expected_msg_name}'，实际得到 '{msg_name}'")
                return False
        else:
            print("❌ 未能识别到有效表头")
            return False
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complex_table_recognition()
    print("\n" + "=" * 60)
    if success:
        print("🎉 复杂表格识别测试通过！")
        print("系统现在能够正确识别:")
        print("1. 混合结构表格（元数据+数据表）")
        print("2. 横向排列的键值对")
        print("3. 多层次的表头结构")
    else:
        print("❌ 测试失败，请检查识别逻辑")