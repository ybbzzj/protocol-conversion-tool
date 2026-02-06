# -*- coding: utf-8 -*-
from flask import Blueprint, request, send_file
import os
import uuid
from datetime import datetime
from backend.utils import success_response, error_response
from backend.services.table_detector import DocumentParser
from backend.services.excel_exporter import ExcelExporter
from backend.services.data_cleaner import DataProcessor
from backend.services.field_matcher import FieldMatcher

extract_bp = Blueprint('extract', __name__)

# 模拟任务存储
tasks_status = {}

@extract_bp.route('/extract/start', methods=['POST'])
def start_extraction():
    if 'file' not in request.files:
        return error_response(40001, "缺少文件")
    
    file = request.files['file']
    field_ids = request.form.getlist('field_ids')
    
    task_id = str(uuid.uuid4())
    upload_path = os.path.join('backend', 'uploads', f"{task_id}_{file.filename}")
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)
    
    # 模拟任务运行 (实际应异步)
    tasks_status[task_id] = {
        'status': 'running',
        'progress': 10,
        'file_path': upload_path,
        'filename': file.filename
    }
    
    try:
        # 执行提取
        parser = DocumentParser()
        result = parser.parse(upload_path)
        
        processor = DataProcessor()
        matcher = FieldMatcher()
        
        processed_tables = []
        print(f"识别到 {len(result['tables'])} 个表格")
        for table in result['tables']:
            table_rows = []
            for row in table['data_rows']:
                proc_res = processor.process_row(row)
                matched_row = {}
                for field, value in proc_res['cleaned'].items():
                    match_res = matcher.match_field(field)
                    target = match_res.target if match_res.target else field
                    matched_row[target] = value
                
                # 位数对齐
                if '位数' in proc_res['converted']:
                    matched_row['类型（bit）'] = proc_res['converted']['位数']
                
                table_rows.append(matched_row)
            # 构建表格数据，包含元数据（meta）
            table_data = {
                'msg_name': table['msg_name'],
                'data_rows': table_rows,
                'meta': table.get('meta', {})  # 传递元数据，包括信源、信宿、消息ID等
            }
            processed_tables.append(table_data)
            
        # 导出
        output_dir = os.path.join('backend', 'outputs')
        exporter = ExcelExporter(output_dir)
        output_file = exporter.export_with_template(processed_tables, task_id)
        
        tasks_status[task_id].update({
            'status': 'success',
            'progress': 100,
            'output_path': output_file
        })
        
        return success_response({'task_id': task_id})
        
    except Exception as e:
        tasks_status[task_id]['status'] = 'failed'
        tasks_status[task_id]['message'] = str(e)
        return error_response(40002, f"解析失败: {str(e)}")

@extract_bp.route('/extract/status/<task_id>', methods=['GET'])
def get_status(task_id):
    status = tasks_status.get(task_id)
    if not status:
        return error_response(40401, "任务不存在")
    return success_response({
        'status': status['status'],
        'progress': status.get('progress', 0),
        'message': status.get('message', '')
    })

@extract_bp.route('/extract/download/<task_id>', methods=['GET'])
def download_result(task_id):
    status = tasks_status.get(task_id)
    if not status or status['status'] != 'success':
        return error_response(40401, "结果文件不存在或任务未完成")
    
    return send_file(os.path.abspath(status['output_path']), as_attachment=True)
