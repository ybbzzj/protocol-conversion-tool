# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime

# 自动定位项目根目录并加入路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入后端核心服务
from backend.app import create_app
from backend.services.table_detector import DocumentParser
from backend.services.data_cleaner import DataProcessor
from backend.services.field_matcher import FieldMatcher
from backend.services.excel_exporter import ExcelExporter

class ProcessingTracer:
    """处理全链路追踪日志工具"""
    @staticmethod
    def section(title):
        print(f"\n{'='*20} {title} {'='*20}")

    @staticmethod
    def step(name, input_data=None, logic=None, output_data=None):
        print(f"\n[处理步骤]: {name}")
        if input_data:
            print(f"  └─ 原始形态 (Input): {input_data}")
        if logic:
            print(f"  └─ 处理逻辑 (Logic): {logic}")
        if output_data:
            print(f"  └─ 输出结果 (Output): {output_data}")

def run_backend_test():
    # 创建 minimal 运行环境以加载配置
    app = create_app('testing')
    
    with app.app_context():
        tracer = ProcessingTracer()
        tracer.section("后端核心逻辑全流程追踪")

        # 准备工作
        docx_path = os.path.join(ROOT_DIR, '协议模板（公开）.docx')
        output_dir = os.path.join(ROOT_DIR, 'backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 文档解析
        tracer.section("1. 文档解析阶段 (Table Detection)")
        parser = DocumentParser()
        
        tracer.step(
            "读取并识别表格",
            input_data=f"文件: {os.path.basename(docx_path)}",
            logic="使用 python-docx 建立虚拟网格(Virtual Grid)对齐合并单元格，基于关键词评分识别表头",
            output_data="解析成功"
        )
        
        result = parser.parse(docx_path)
        print(f"  -> 识别详情: 共发现 {result['tables_count']} 个协议数据表")
        
        # 2. 字段级深度处理
        tracer.section("2. 数据清洗与智能匹配 (Cleaning & Matching)")
        processor = DataProcessor()
        matcher = FieldMatcher()
        
        processed_tables = []
        for table in result['tables']:
            print(f"\n--- 正在处理表格: {table['msg_name'] or '未命名协议'} ---")
            
            table_rows = []
            # 仅详细追踪前 2 行作为示例，避免日志过长
            for i, row in enumerate(table['data_rows']):
                is_sample = (i < 2)
                
                # A. 清洗
                proc_res = processor.process_row(row)
                
                # B. 匹配
                matched_row = {}
                detail_logs = []
                for field, value in proc_res['cleaned'].items():
                    match_res = matcher.match_field(field)
                    target = match_res.target if match_res.target else field
                    matched_row[target] = value
                    
                    if is_sample:
                        detail_logs.append(f"'{field}'->'{target}'({match_res.match_type})")
                
                # C. 转换
                if '位数' in proc_res['converted']:
                    matched_row['类型（bit）'] = proc_res['converted']['位数']
                
                if is_sample:
                    tracer.step(
                        f"处理第 {i+1} 行数据",
                        input_data=row,
                        logic=f"清洗首尾空格 -> 模糊语义匹配目标列 -> 提取数据类型位数({proc_res['converted'].get('位数', '无')})",
                        output_data=matched_row
                    )
                    print(f"  └─ 字段映射链路: {' | '.join(detail_logs)}")
                
                table_rows.append(matched_row)
            
            processed_tables.append({'msg_name': table['msg_name'], 'data_rows': table_rows})
            print(f"  -> 表格处理完成: 共处理 {len(table_rows)} 行数据")

        # 3. 模板导出
        tracer.section("3. 结果导出阶段 (Excel Export)")
        exporter = ExcelExporter(output_dir)
        task_id = "trace_run_" + datetime.now().strftime('%H%M%S')
        
        tracer.step(
            "生成 Excel 文件",
            input_data="17列标准协议模板",
            logic="复制模板文件 -> 按照表头名称精准填充单元格 -> 自动处理消息名称合并",
        )
        
        output_file = exporter.export_with_template(processed_tables, task_id)
        tracer.step(
            "导出完成",
            output_data=f"文件已保存至: {os.path.abspath(output_file)}"
        )

        tracer.section("后端流程追踪结束")

if __name__ == '__main__':
    run_backend_test()
