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
        header = f"\n{'='*30} 后端全链路测试（带表格展示与筛选留痕） {'='*30}"
        log_to_file(header, log_file)
        
        docx_path = os.path.join(ROOT_DIR, '协议模板（公开）.docx')
        output_dir = os.path.join(ROOT_DIR, 'backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 解析阶段（展示原始表格内容）
        parser = DocumentParser()
        log_to_file(f"\n[1/3 正在解析对象]: Word文档 {os.path.basename(docx_path)}", log_file)
        log_to_file(f"  ├─ 具体内容: 读取文档中的所有表格及上下文", log_file)
        log_to_file(f"  ├─ 处理逻辑: 虚拟网格对齐 -> 表头评分定位 -> 元数据行过滤", log_file)
        
        # 获取原始识别的表格（包括辅助表格）
        from backend.services.table_detector import TableDetector
        detector = TableDetector()
        raw_tables = detector.extract_tables_from_docx(docx_path)
        
        # 显示经过表格链接器处理后的表格（即与最终结果强相关的表格）
        from backend.services.table_linker import TableLinker
        linker = TableLinker()
        linked_tables = linker.link_tables(raw_tables)  # 使用原始表格进行链接
        
        core_tables_count = len([t for t in linked_tables if any(h in str(t.get('headers', [])) for h in ['参数', '内容', '信号名称'])])
        log_to_file(f"  └─ 处理结果: 共 {core_tables_count} 个核心协议表可用于最终输出", log_file)
        
        # 分类原始表格：辅助表（不会输出到结果）和核心表（会输出到结果）
        auxiliary_tables = []
        core_tables = []
        
        for table in raw_tables:
            headers_str = str(table.get('headers', []))
            has_main_content = any(h in headers_str for h in ['参数', '信号名称'])
            has_secondary_content = '内容' in headers_str
            is_auxiliary = any(keyword in headers_str for keyword in ['消息ID', '消息标识', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'])
            
            if has_main_content or (has_secondary_content and not is_auxiliary):
                core_tables.append(table)
            else:
                auxiliary_tables.append(table)
        
        # 先展示不会输出到结果的表格（辅助表）
        # log_to_file(f"\n>>> 不会输出到结果的表格 <<<", log_file)
        for idx, table in enumerate(auxiliary_tables):
            msg_id = table.get('msg_name', '未知消息')
            log_to_file(f"\n>>> [辅助表] 展示原始表格内容 [消息: {msg_id}] <<<", log_file)
            
            # 打印表头
            headers = table.get('headers', [])
            if headers:
                headers_str = ' | '.join(headers)
                log_to_file(f"  [表头] {headers_str}", log_file)
            
            # 打印原始数据行
            log_to_file("  [原始数据行]", log_file)
            data_rows = table.get('data_rows', [])
            for i, row in enumerate(data_rows):
                row_display = ' | '.join([f"{k}:{v}" for k, v in row.items()])
                log_to_file(f"    [{i+1:2d}] {row_display} => ✓ 保留", log_file)
            
            log_to_file("", log_file)  # 空行分隔
        

        
        # 更新result变量为包含原始表格和处理后表格的信息
        result = {'tables': linked_tables, 'tables_count': len(linked_tables)}

        # 2. 表格展示与筛选过程
        processor = DataProcessor()
        processed_tables = []
        
        for table in result['tables']:
            msg_id = table['msg_name'] or "未知消息"
            log_to_file(f"\n>>> [核心表] 展示原始表格内容 [消息: {msg_id}] <<<", log_file)
            
            # 打印表头
            headers = table['headers']
            log_to_file(f"  [表头] {' | '.join(headers)}", log_file)
            
            # 打印原始数据行 + 筛选决策
            log_to_file("  [原始数据行 + 筛选过程]", log_file)
            retained_rows = []
            for i, row in enumerate(table['data_rows']):
                row_display = ' | '.join([f"{k}:{v}" for k, v in row.items()])
                content_val = row.get('参数', row.get('内容', row.get('信号名称', '')))
                
                # 判定是否保留 - 改进策略
                noise_reasons = []
                row_text_all = "".join(str(v) for v in row.values() if v)
                
                # 检查是否包含重要元数据字段（即使内容字段为空）
                has_important_metadata = any(key in ['消息ID', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'] for key in row.keys())
                has_non_empty_metadata = any(key in ['消息ID', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'] and row[key] for key in row.keys())
                
                # 如果是包含重要元数据的行，即使是内容字段为空也要保留
                if not content_val and not has_non_empty_metadata:
                    noise_reasons.append("内容字段为空且无重要元数据")
                if '参见' in row_text_all: noise_reasons.append("含噪声词'参见'")
                # 移除对'机器码'的过滤，因为这是重要信息
                # if '机器码' in row_text_all: noise_reasons.append("含元数据'机器码'")
                
                if noise_reasons:
                    decision = f"✗ 过滤 (原因: {'; '.join(noise_reasons)})"
                else:
                    decision = "✓ 保留"
                    retained_rows.append(row)
                
                log_to_file(f"    [{i+1:2d}] {row_display} => {decision}", log_file)
            
            # 清洗与转换（仅对保留行）
            log_to_file(f"\n[2/3 正在处理对象]: 协议消息 [{msg_id}]", log_file)
            log_to_file(f"  ├─ 具体内容: 清洗 {len(retained_rows)} 行保留字段", log_file)
            log_to_file(f"  ├─ 处理逻辑: 正则剥离标题标签 -> 自动匹配 17 列标准列名 -> 动态提取类型位数", log_file)
            
            table_rows = []
            for i, row in enumerate(retained_rows):
                proc_res = processor.process_row(row)
                row_data = proc_res['cleaned']
                if '位数' in proc_res['converted']: row_data['类型（bit）'] = proc_res['converted']['位数']
                if '标准类型' in proc_res['converted']: row_data['转换类型'] = proc_res['converted']['标准类型']
                table_rows.append(row_data)
            
            processed_tables.append({'msg_name': table['msg_name'], 'data_rows': table_rows, 'meta': table.get('meta', {})})
            if table_rows:
                log_to_file(f"  └─ 处理结果: 字段 '{table_rows[0].get('参数','内容')}' 等已完成标准化转换", log_file)
            else:
                log_to_file(f"  └─ 处理结果: 该表格无有效数据行，已跳过处理", log_file)

        # 3. 导出阶段
        exporter = ExcelExporter(output_dir)
        timestamp = datetime.now().strftime('%H%M%S')
        task_id = f"restore_test_{timestamp}_{timestamp}"
        
        log_to_file(f"\n[3/3 正在处理对象]: 生成 Excel 报表", log_file)
        log_to_file(f"  ├─ 具体内容: 使用协议模板（公开）.docx.xlsx 进行填充", log_file)
        log_to_file(f"  ├─ 处理逻辑: 复制模板 -> 定位 17 列 Header -> 精准填入数据 -> 合并消息名称列", log_file)
        
        output_file = exporter.export_with_template(processed_tables, task_id)
        log_to_file(f"  └─ 处理结果: 文件生成成功 -> {os.path.abspath(output_file)}", log_file)

        footer = f"\n{'='*30} 测试完成（完整过程已存档至 {log_file}） {'='*30}\n"
        log_to_file(footer, log_file)

if __name__ == '__main__':
    run_detailed_test()
