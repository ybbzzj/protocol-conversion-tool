# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

# 自动定位项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, 'backend'))

# 模拟最小化 Flask 环境以满足服务依赖
class MockApp:
    config = {'KNOWLEDGE_BASE_FILE': 'backend/data/knowledge_base.json'}
    def app_context(self): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass

from services.table_detector import DocumentParser
from services.excel_exporter import ExcelExporter
from services.data_cleaner import DataProcessor

def test_full_extraction_flow():
    print("="*50)
    print("恢复测试：后端提取流程 (复用模板填充模式)")
    print("="*50)
    
    # 1. 准备文件
    docx_path = os.path.join(ROOT_DIR, '协议模板（公开）.docx')
    output_dir = os.path.join(ROOT_DIR, 'backend', 'outputs')
    
    # 2. 初始化服务
    parser = DocumentParser()
    processor = DataProcessor()
    exporter = ExcelExporter(output_dir)
    
    # 3. 解析
    print(f"\n[1/3] 解析文档: {os.path.basename(docx_path)}")
    result = parser.parse(docx_path)
    print(f"-> 识别到 {result['tables_count']} 个协议表格")
    
    # 4. 导出
    print("\n[2/3] 正在对齐模板并生成报告...")
    task_id = "restore_test_" + datetime.now().strftime('%H%M%S')
    output_file = exporter.export_with_template(result['tables'], task_id)
    
    print("\n[3/3] 流程完成！")
    print(f"-> 最终生成的 Excel: {os.path.abspath(output_file)}")
    print("="*50)

if __name__ == '__main__':
    test_full_extraction_flow()
