# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

# 自动定位项目根目录并加入路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app
from backend.services.table_detector import TableDetector, DocumentParser
from backend.services.data_cleaner import DataProcessor
from backend.services.excel_exporter import ExcelExporter
from backend.services.table_linker import TableLinker

def log_to_file(message, log_path):
    """将日志同时输出到终端和文件"""
    print(message)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def run_detailed_test():
    app = create_app('testing')
    
    # 创建日志目录和文件
    log_dir = os.path.join(ROOT_DIR, 'backend', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'extraction_trace.log')
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"[日志开始] {datetime.now().isoformat()}\n")
    
    with app.app_context():
        header = f"\n{'='*30} 后端全链路测试（高精度识别与全留痕日志） {'='*30}"
        log_to_file(header, log_file)
        
        docx_path = os.path.join(ROOT_DIR, 'word/测试协议20251216.docx')
        output_dir = os.path.join(ROOT_DIR, 'backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 解析阶段
        log_to_file(f"\n[1/3 正在解析对象]: Word文档 {os.path.basename(docx_path)}", log_file)
        log_to_file(f"  ├─ 具体内容: 扫描文档中的所有表格结构及上下文标题", log_file)
        log_to_file(f"  ├─ 处理逻辑: 虚拟网格对齐 -> 标题层级回溯 -> 业务含义权重评分", log_file)
        
        detector = TableDetector()
        raw_tables = detector.extract_tables_from_docx(docx_path)
        
        linker = TableLinker()
        linked_tables = linker.link_tables(raw_tables)
        
        log_to_file(f"  └─ 处理结果: 成功识别并提取 {len(linked_tables)} 个有效协议表格", log_file)

        # 2. 数据处理与筛选阶段（逐表显式留痕）
        processor = DataProcessor()
        processed_tables = []
        
        for table in linked_tables:
            msg_name = table.get('msg_name') or "未知消息"
            
            # 第一层：正在处理的对象
            log_to_file(f"\n[2/3 正在处理对象]: 协议表格 [{msg_name}]", log_file)
            
            # 展示表头
            headers = table.get('headers', [])
            log_to_file(f"  [表头] {' | '.join(headers)}", log_file)
            
            # 第二层：展示原始数据行及筛选过程
            log_to_file("  [原始数据行 + 筛选过程]", log_file)
            retained_rows = []
            for i, row in enumerate(table.get('data_rows', [])):
                row_display = ' | '.join([f"{k}:{v}" for k, v in row.items()])
                content_val = row.get('参数', row.get('内容', row.get('信号名称', '')))
                
                # 判定决策逻辑
                noise_reasons = []
                row_text_all = "".join(str(v) for v in row.values() if v)
                
                # 重要特征保留：含元数据或含实质内容
                has_important_metadata = any(key in ['消息ID', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'] and row[key] for key in row.keys())
                
                if not content_val and not has_important_metadata:
                    noise_reasons.append("内容字段为空且无重要元数据")
                if '参见' in row_text_all: 
                    noise_reasons.append("含噪声词'参见'")
                
                if noise_reasons:
                    decision = f"✗ 过滤 (原因: {'; '.join(noise_reasons)})"
                else:
                    decision = "✓ 保留"
                    retained_rows.append(row)
                
                # 输出原始行留痕
                log_to_file(f"    [{i+1:2d}] {row_display} => {decision}", log_file)
            
            # 第三层：具体清洗逻辑
            log_to_file(f"  ├─ 具体内容: 对上述 {len(retained_rows)} 行保留行进行字段标准化", log_file)
            log_to_file(f"  ├─ 处理逻辑: 标题标签剥离 -> 17列标准映射 -> 数据类型动态提取", log_file)
            
            table_rows = []
            for row in retained_rows:
                proc_res = processor.process_row(row)
                row_data = proc_res['cleaned']
                # 补全转换后的技术列
                if '位数' in proc_res['converted']: row_data['类型（bit）'] = proc_res['converted']['位数']
                if '标准类型' in proc_res['converted']: row_data['转换类型'] = proc_res['converted']['标准类型']
                table_rows.append(row_data)
            
            processed_tables.append({
                'msg_name': msg_name, 
                'data_rows': table_rows, 
                'meta': table.get('meta', {})
            })
            
            # 第四层：处理结果形态
            if table_rows:
                first_field = table_rows[0].get('参数', table_rows[0].get('内容', '数据字段'))
                log_to_file(f"  └─ 处理结果: 成功完成字段标准化，首字段形态为 [{first_field}]", log_file)
            else:
                log_to_file(f"  └─ 处理结果: 该表格无有效数据通过筛选，已跳过转换", log_file)

        # 3. 导出阶段
        log_to_file(f"\n[3/3 正在处理对象]: 生成标准化 Excel 报表", log_file)
        log_to_file(f"  ├─ 具体内容: 使用协议模板对 {len(processed_tables)} 个表格进行数据填充", log_file)
        log_to_file(f"  ├─ 处理逻辑: 模板克隆 -> Header精准定位 -> 消息列合并 -> 单元格格式化", log_file)
        
        exporter = ExcelExporter(output_dir)
        timestamp = datetime.now().strftime('%H%M%S')
        task_id = f"protocol_restore_test_{timestamp}_{timestamp}"
        
        output_file = exporter.export_with_template(processed_tables, task_id)
        log_to_file(f"  └─ 处理结果: 文件生成成功 -> {os.path.abspath(output_file)}", log_file)

        footer = f"\n{'='*30} 测试完成（详细全过程已存档至 {log_file}） {'='*30}\n"
        log_to_file(footer, log_file)

if __name__ == '__main__':
    run_detailed_test()
