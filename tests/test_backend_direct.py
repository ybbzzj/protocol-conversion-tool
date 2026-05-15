#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端直接测试脚本 - 绕过前端直接处理协议文档并生成 Excel

使用方法:
    python test_backend_direct.py <协议文档路径> [输出目录]
    
示例:
    python test_backend_direct.py "word/测试协议 20260331.docx"
    python test_backend_direct.py "word/测试协议 20260331.docx" "./test_output"
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.table_detector import TableDetector
from services.table_linker import TableLinker
from services.data_cleaner import DataProcessor
from services.excel_exporter import ExcelExporter


def process_protocol_doc(doc_path: str, output_dir: str = None):
    """
    直接处理协议文档并生成 Excel
    
    Args:
        doc_path: 协议文档路径（.docx 或 .xlsx）
        output_dir: 输出目录（默认为 backend/outputs）
    
    Returns:
        dict: 处理结果信息
    """
    print("="*80)
    print("协议文档处理工具（直接后端调用）")
    print("="*80)
    print(f"输入文件：{doc_path}")
    print(f"输出目录：{output_dir or 'backend/outputs'}")
    print("="*80)
    
    # 验证文件存在
    if not os.path.exists(doc_path):
        print(f"[ERROR] 文件不存在：{doc_path}")
        return None
    
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'backend', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    start_time = datetime.now()
    
    try:
        # ========== 步骤 1：表格检测和识别 ==========
        print("\n【步骤 1】表格检测和识别...")
        detector = TableDetector()
        
        # 检测文件类型并处理
        file_ext = os.path.splitext(doc_path)[1].lower()
        if file_ext == '.docx':
            print("  检测到 Word 文档，开始提取表格...")
            tables = detector.extract_tables_from_docx(doc_path)
            print(f"  [OK] 提取到 {len(tables)} 个表格")
            
            # 保存识别结果（包装成 dict 格式）
            recognition_result = {'tables': tables}
            result_path = os.path.join(os.path.dirname(__file__), 'backend', 'table_recognition_results', 'latest_recognition.json')
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(recognition_result, f, ensure_ascii=False, indent=2)
            print(f"  [INFO] 识别结果已保存到：{result_path}")
            
        elif file_ext in ['.xlsx', '.xls']:
            print("  检测到 Excel 文档，直接读取...")
            # TODO: 实现 Excel 直接读取逻辑
            tables = []
            print("  [WARN] Excel 直接处理功能待实现")
        else:
            print(f"[ERROR] 不支持的文件格式：{file_ext}")
            return None
                        
        if not tables:
            print("[WARNING] 未提取到任何表格，终止处理")
            return None
                
        # ========== 步骤 2：表格关联和整理 ==========
        print("\n【步骤 2】表格关联和整理...")
        linker = TableLinker()
        linked_tables = linker.link_tables(tables)
        print(f"  [OK] 关联后表格数：{len(linked_tables)}")
                
        # ========== 步骤 3：数据清洗和格式化 ==========
        print("\n【步骤 3】数据清洗和格式化...")
        processor = DataProcessor()
        formatted_rows = []
                
        for table_idx, table in enumerate(linked_tables, 1):
            table_name = table.get('msg_name', f'表{table_idx}')
            print(f"\n  处理 {table_name}...")
                            
            rows = table.get('data_rows', [])  # 修复：使用 data_rows 而不是 rows
            for row_idx, row in enumerate(rows, 1):
                # 跳过空行和无效行
                if not processor.is_valid_data_row(row):
                    continue
                                
                # 处理数据行
                formatted = processor.process_row(row)
                if formatted and any(formatted.values()):
                    formatted['所属表格'] = table_name
                    formatted_rows.append(formatted)
                    
            print(f"    -> 有效数据行：{len([r for r in rows if processor.is_valid_data_row(r)])}")
                
        print(f"\n  [OK] 总计格式化数据行：{len(formatted_rows)}")
                
        if not formatted_rows:
            print("[WARNING] 没有有效数据，终止处理")
            return None
                
        # ========== 步骤 4：导出 Excel ==========
        print("\n【步骤 4】导出 Excel...")
        exporter = ExcelExporter(output_dir=output_dir)
                
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        input_filename = os.path.splitext(os.path.basename(doc_path))[0]
        output_filename = f"协议_{timestamp}.xlsx"
        output_path = os.path.join(output_dir, output_filename)
                
        # 导出 Excel（使用 export_with_template 或 export_to_excel）
        # 注意：需要先准备 tables_data 格式
        tables_data = []
        for table in linked_tables:
            tables_data.append(table)
        
        exporter.export_with_template(tables_data, task_id="test")
        print(f"  [OK] Excel 已生成：{output_path}")
                
        # ========== 完成 ==========
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
                
        print("\n" + "="*80)
        print("[OK] 处理完成！")
        print("="*80)
        print(f"输入文件：{os.path.basename(doc_path)}")
        print(f"输出文件：{output_filename}")
        print(f"数据行数：{len(formatted_rows)}")
        print(f"处理时间：{duration:.2f}秒")
        print("="*80)
        
        return {
            'success': True,
            'input_file': doc_path,
            'output_file': output_path,
            'row_count': len(formatted_rows),
            'duration': duration,
            'tables_processed': len(linked_tables)
        }
        
    except Exception as e:
        print("\n" + "="*80)
        print("[ERROR] 处理失败！")
        print("="*80)
        print(f"错误信息：{e}")
        import traceback
        traceback.print_exc()
        print("="*80)
        
        return {
            'success': False,
            'input_file': doc_path,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def main():
    """主函数"""
    # ========== 配置区域（直接修改这里） ==========
    # 协议文档路径 - 修改为你要测试的文件（从下面列表中选择）
    doc_path = "word\\测试协议20260331.docx"
    
    # 输出目录 - None 表示使用默认目录 (backend/outputs)
    output_dir = None  # 或指定目录如 r"./test_output"
    # ===========================================
    
    # 如果需要通过命令行参数覆盖，取消下面注释
    # if len(sys.argv) > 1:
    #     doc_path = sys.argv[1]
    # if len(sys.argv) > 2:
    #     output_dir = sys.argv[2]
    
    # 自动转换相对路径为绝对路径
    if not os.path.isabs(doc_path):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 支持 / 和 \ 两种分隔符
        doc_path = os.path.join(root_dir, *doc_path.replace('\\', '/').split('/'))
        
        # 如果文件不存在，尝试在 word 目录下查找
        if not os.path.exists(doc_path):
            word_dir = os.path.join(root_dir, 'word')
            alt_path = os.path.join(word_dir, os.path.basename(doc_path))
            if os.path.exists(alt_path):
                doc_path = alt_path
    
    # 检查文件是否存在
    if not os.path.exists(doc_path):
        print(f"[ERROR] 文件不存在：{doc_path}")
        print("\n请检查 test_backend_direct.py 中的 doc_path 配置")
        print("\n当前 word 目录下的测试文件:")
        word_dir = os.path.join(root_dir, 'word')
        if os.path.exists(word_dir):
            test_files = [f for f in os.listdir(word_dir) if f.endswith('.docx') and not f.startswith('~$')]
            for i, f in enumerate(sorted(test_files), 1):
                print(f"  {i}. word\\{f}")
        else:
            print(f"[ERROR] word 目录不存在：{word_dir}")
        sys.exit(1)
    
    # 执行处理
    result = process_protocol_doc(doc_path, output_dir)
    
    # 返回状态码
    sys.exit(0 if result and result.get('success') else 1)


if __name__ == "__main__":
    main()
