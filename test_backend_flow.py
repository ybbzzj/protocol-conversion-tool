# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime

# 自动定位项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, 'backend'))

from app import create_app
from services.table_detector import DocumentParser
from services.field_matcher import FieldMatcher
from services.data_cleaner import DataProcessor
from services.excel_exporter import ExcelExporter

def match_type_desc(mtype):
    desc = {'exact': '知识库精确匹配', 'alias': '内置别名映射', 'fuzzy': '模糊语义计算', 'none': '未匹配'}
    return desc.get(mtype, mtype)

def test_full_extraction_flow():
    app = create_app('testing')
    with app.app_context():
        print("\n" + "="*60)
        print("【后端全流程自动化测试】恢复版本：详细日志追踪模式")
        print("="*60)
        
        # 1. 初始化
        docx_path = os.path.join(ROOT_DIR, '协议模板（公开）.docx')
        output_dir = os.path.join(ROOT_DIR, 'backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        parser = DocumentParser()
        matcher = FieldMatcher() 
        processor = DataProcessor()
        exporter = ExcelExporter(output_dir)

        # 2. 解析文档
        print(f"\n[步骤1] 正在解析 Word 文档: {os.path.basename(docx_path)}...")
        result = parser.parse(docx_path)
        print(f"-> 成功识别出 {result['tables_count']} 个协议数据表")
        
        processed_tables = []
        for table in result['tables']:
            print(f"\n>>> 正在处理表格 #{table['index']} | 消息名: {table['msg_name'] or '未知'} <<<")
            print(f"  [识别表头]: {table['headers']}")
            
            table_rows = []
            for i, row in enumerate(table['data_rows']):
                # A. 清洗数据
                proc_res = processor.process_row(row)
                
                # B. 匹配字段并记录详细日志
                matched_row = {}
                for field, value in proc_res['cleaned'].items():
                    match_res = matcher.match_field(field)
                    target = match_res.target if match_res.target else field
                    matched_row[target] = value
                    
                    # 仅为第一行数据打印详细的“匹配心路历程”
                    if i == 0:
                        print(f"    - 字段追踪: '{field}' -> '{target}' | 置信度: {match_res.confidence:.2f} | 策略: {match_type_desc(match_res.match_type)}")
                
                # 注入额外信息（如位数、公式）
                for k, v in proc_res['converted'].items():
                    if k == '位数': matched_row['类型（bit）'] = v
                    elif k == '标准类型': matched_row['转换类型'] = v
                
                table_rows.append(matched_row)
            
            print(f"  [处理完毕]: 已完成 {len(table['data_rows'])} 行协议项的清洗与映射")
            processed_tables.append({'msg_name': table['msg_name'], 'data_rows': table_rows})

        # 3. 模板填充导出
        print(f"\n[步骤2] 正在调用 Excel 模板并填充数据...")
        task_id = "detail_run_" + datetime.now().strftime('%H%M%S')
        output_file = exporter.export_with_template(processed_tables, task_id)
        
        print("\n" + "="*60)
        print("【测试成功完成】")
        print(f"输出文件: {os.path.abspath(output_file)}")
        print("="*60 + "\n")

if __name__ == '__main__':
    test_full_extraction_flow()
