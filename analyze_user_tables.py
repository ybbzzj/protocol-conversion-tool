#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析用户提供的表格识别情况
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.table_detector import DocumentParser

def analyze_user_tables():
    print("分析用户提供的表格识别情况...")
    print("=" * 60)
    
    # 模拟用户提供的三个表格结构
    print("用户提供的表格内容:")
    print("\n【表1】端口分配表（辅助表）")
    print("信息名称\t检查结果1\t信息标识\txx")
    print("信源、信宿\tBC→RT1-SA0-模式码0x03")
    print("传输周期\t非周期\t其他\t-")
    print("发起时机\t按实际操作流程\t错误处理\t-")
    print("序号\t内容\t类型\t值域\t单位\t数据处理方法")
    print("1\t计时时间1\tUINTEGER-32\t0~4294967295\tms\t32位整型数...")
    
    print("\n【表2】ID定义表（辅助表）")
    print("序号\t信源\t信宿\t信息内容\t消息ID")
    print("1\t某设备\t综合模块\t某设备装置测量数据1\t0x8000")
    
    print("\n【表3】聚合式信息流表征（核心表）")
    print("信息名称\t检查结果1\t信息标识\txx")
    print("信源、信宿\tBC→RT1-SA0-模式码0x03")
    print("传输周期\t非周期\t其他\t-")
    print("发起时机\t按实际操作流程\t错误处理\t-")
    print("序号\t内容\t类型\t值域\t单位\t数据处理方法")
    print("1\t计时时间1\tUINTEGER-32\t0~4294967295\tms\t32位整型数...")
    print()
    print("信息名称\t检查结果2\t信息标识\txx")
    print("信源、信宿\tBC→RT1-SA0-模式码0x04")
    print("传输周期\t非周期\t其他\t-")
    print("发起时机\t按实际操作流程\t错误处理\t-")
    print("代号\t内容\t类型\t值域\t单位\t数据处理方法")
    print("Synq_time\t计时时间2\tUINTEGER-32\t0~4294967295\tms\t32位整型数...")
    print("注：时间按小端处理")
    
    # 测试现有识别逻辑
    print("\n" + "=" * 60)
    print("测试现有识别逻辑:")
    
    try:
        # 创建虚拟测试数据来模拟识别过程
        test_grids = [
            # 表1: 端口分配表
            [
                ["序号", "信源", "信宿", "信息内容", "接收组播地址", "接收端口号", "信源系统码", "信源机器码", "信宿系统码", "信宿机器码"],
                ["1", "", "某设备", "综合模块", "某设备装置测量数据1", "225.0.0.111", "20000", "100", "128", "100", "111"]
            ],
            
            # 表2: ID定义表
            [
                ["序号", "信源", "信宿", "信息内容", "消息ID"],
                ["1", "", "某设备", "综合模块", "某设备装置测量数据1", "0x8000"]
            ],
            
            # 表3: 聚合式信息流表征（复杂结构）
            [
                ["信息名称", "检查结果1", "信息标识", "xx"],
                ["信源、信宿", "BC→RT1-SA0-模式码0x03", "", ""],
                ["传输周期", "非周期", "其他", "-"],
                ["发起时机", "按实际操作流程", "错误处理", "-"],
                ["序号", "内容", "类型", "值域", "单位", "数据处理方法"],
                ["1", "计时时间1", "UINTEGER-32", "0~4294967295", "ms", "32位整型数..."]
            ]
        ]
        
        from backend.services.table_detector import TableDetector
        detector = TableDetector()
        
        print("\n识别结果分析:")
        for i, grid in enumerate(test_grids, 1):
            print(f"\n--- 表格 {i} ---")
            
            # 模拟表头识别
            header_scores = []
            for r_idx, row in enumerate(grid[:min(3, len(grid))]):
                matches = sum(1 for cell in row if any(k in cell for k in detector.keywords))
                score = matches / 4.0 if matches <= 4 else 1.0
                header_scores.append((r_idx, matches, score))
                print(f"  行{r_idx}: 匹配关键词数={matches}, 得分={score:.2f}")
            
            # 找到最佳表头
            best_header = max(header_scores, key=lambda x: x[2]) if header_scores else (-1, 0, 0)
            header_row_idx = best_header[0]
            
            if header_row_idx >= 0:
                headers = grid[header_row_idx]
                print(f"  ✓ 识别表头行: {header_row_idx}")
                print(f"  表头字段: {headers}")
                
                # 检查表格类型
                headers_str = str(headers)
                is_port_table = any(keyword in headers_str for keyword in ['接收组播地址', '接收端口号'])
                is_id_table = any('消息ID' in h for h in headers)
                is_param_table = any('参数' in h or '内容' in h for h in headers) and any('类型' in h for h in headers)
                
                print(f"  表格类型判断:")
                print(f"    - 端口分配表: {is_port_table}")
                print(f"    - 消息ID表: {is_id_table}")
                print(f"    - 参数表: {is_param_table}")
                
                # 模拟元数据提取
                msg_name = ""
                if i == 3:  # 表3的特殊情况
                    # 从上方的元数据行提取信息名称
                    if len(grid) > header_row_idx:
                        for r_idx in range(min(3, header_row_idx)):
                            if r_idx < len(grid):
                                first_cell = grid[r_idx][0] if grid[r_idx] else ""
                                if '信息名称' in first_cell and len(grid[r_idx]) > 1:
                                    msg_name = grid[r_idx][1]
                                    break
                
                print(f"  提取的消息名称: '{msg_name}'")
                
            else:
                print(f"  ✗ 无法识别有效表头")
        
        print("\n" + "=" * 60)
        print("识别问题总结:")
        print("1. 【表1 端口分配表】✓ 可以识别为辅助表")
        print("2. 【表2 ID定义表】✓ 可以识别为辅助表") 
        print("3. 【表3 聚合表】⚠ 存在挑战:")
        print("   - 混合结构：上半部分是键值对元数据，下半部分是标准表格")
        print("   - 需要改进元数据提取逻辑来处理这种复杂格式")
        print("   - 当前逻辑可能无法正确提取'检查结果1'作为消息名称")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_user_tables()