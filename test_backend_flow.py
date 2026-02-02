# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

# 自动定位项目根目录并加入路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app
from backend.services.table_detector import DocumentParser
from backend.services.data_cleaner import DataProcessor
from backend.services.excel_exporter import ExcelExporter

def run_structured_test():
    app = create_app('testing')
    
    with app.app_context():
        print(f"\n{'='*30} 后端全链路测试 {'='*30}")
        
        docx_path = os.path.join(ROOT_DIR, '协议模板（公开）.docx')
        output_dir = os.path.join(ROOT_DIR, 'backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 解析阶段
        parser = DocumentParser()
        print(f"\n[1/3 正在解析对象]: Word文档 {os.path.basename(docx_path)}")
        print(f"  ├─ 具体内容: 读取文档中的所有表格及上下文")
        print(f"  ├─ 处理逻辑: 虚拟网格对齐 -> 表头评分定位 -> 元数据行过滤(排除参见、机器码等行)")
        
        result = parser.parse(docx_path)
        print(f"  └─ 处理结果: 成功识别 {result['tables_count']} 个核心协议表")

        # 2. 清洗与转换
        processor = DataProcessor()
        processed_tables = []
        
        for table in result['tables']:
            msg_id = table['msg_name'] or "未知消息"
            print(f"\n[2/3 正在处理对象]: 协议消息 [{msg_id}]")
            print(f"  ├─ 具体内容: 清洗标题及处理 {len(table['data_rows'])} 行原始字段")
            print(f"  ├─ 处理逻辑: 正则剥离标题标签 -> 自动匹配 17 列标准列名 -> 动态提取类型位数")
            
            table_rows = []
            for i, row in enumerate(table['data_rows']):
                proc_res = processor.process_row(row)
                row_data = proc_res['cleaned']
                # 记录位数
                if '位数' in proc_res['converted']:
                    row_data['类型（bit）'] = proc_res['converted']['位数']
                table_rows.append(row_data)
            
            processed_tables.append({'msg_name': table['msg_name'], 'data_rows': table_rows})
            print(f"  └─ 处理结果: 字段 '{table_rows[0].get('参数','内容')}' 等已完成标准化转换")

        # 3. 导出阶段
        exporter = ExcelExporter(output_dir)
        task_id = "final_fix_" + datetime.now().strftime('%H%M%S')
        
        print(f"\n[3/3 正在处理对象]: 生成 Excel 报表")
        print(f"  ├─ 具体内容: 使用协议模板（公开）.docx.xlsx 进行填充")
        print(f"  ├─ 处理逻辑: 复制模板 -> 定位 17 列 Header -> 精准填入数据 -> 合并消息名称列")
        
        output_file = exporter.export_with_template(processed_tables, task_id)
        print(f"  └─ 处理结果: 文件生成成功 -> {os.path.abspath(output_file)}")

        print(f"\n{'='*30} 测试完成 {'='*30}\n")

if __name__ == '__main__':
    run_structured_test()
