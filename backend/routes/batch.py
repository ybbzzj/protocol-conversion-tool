# -*- coding: utf-8 -*-
from flask import Blueprint, request, send_file
from backend.utils import success_response, error_response
from backend.services.table_detector import DocumentParser
from backend.services.excel_exporter import ExcelExporter
from backend.services.data_cleaner import DataProcessor
from backend.services.field_matcher import EnhancedFieldMatcher as FieldMatcher
import uuid
import os
from datetime import datetime

batch_bp = Blueprint('batch', __name__)

# 批量任务存储
batch_tasks_status = {}

@batch_bp.route('/upload', methods=['POST'])
def upload_batch():
    """上传待处理的 CSV/Excel 文件并创建任务"""
    if 'file' not in request.files:
        return error_response(40001, "缺少文件参数")
    
    file = request.files['file']
    if not file or file.filename == '':
        return error_response(40001, "文件为空")
    
    # 验证文件类型
    allowed_extensions = {'.xlsx', '.xls', '.csv'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return error_response(40001, f"不支持的文件格式，请上传 CSV 或 Excel 格式的文件")
    
    # 解析选项
    options = {
        'table_id': request.form.get('options[table_id]'),
        'strategy': request.form.get('options[strategy]', 'strict'),
        'overwrite': request.form.get('options[overwrite]', 'false').lower() == 'true'
    }
    
    task_id = str(uuid.uuid4())
    upload_path = os.path.join('backend', 'uploads', f"batch_{task_id}_{file.filename}")
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)
    
    # 初始化批量任务信息
    batch_tasks_status[task_id] = {
        'status': 'running',
        'progress': 10,
        'file_path': upload_path,
        'filename': file.filename,
        'created_at': datetime.now().isoformat(),
        'options': options,
        'output_path': None,
        'message': '',
        'processed_count': 0,
        'total_count': 0
    }
    
    try:
        # 执行批量处理
        parser = DocumentParser()
        result = parser.parse(upload_path)
        
        processor = DataProcessor()
        matcher = FieldMatcher()
        
        processed_tables = []
        total_tables = len(result['tables'])
        batch_tasks_status[task_id]['total_count'] = total_tables
        
        for idx, table in enumerate(result['tables']):
            table_rows = []
            for row in table['data_rows']:
                proc_res = processor.process_row(row)
                matched_row = {}
                for field, value in proc_res['cleaned'].items():
                    match_res = matcher.match_field(field)
                    # 兼容字典和对象格式
                    target = match_res.get('target') if isinstance(match_res, dict) else (match_res.target if hasattr(match_res, 'target') else field)
                    target = target if target else field
                    matched_row[target] = value
                
                # 位数对齐
                if '位数' in proc_res['converted']:
                    matched_row['类型（bit）'] = proc_res['converted']['位数']
                
                table_rows.append(matched_row)
            
            # 构建表格数据
            table_data = {
                'msg_name': table['msg_name'],
                'data_rows': table_rows,
                'meta': table.get('meta', {})
            }
            processed_tables.append(table_data)
            
            # 更新进度
            progress = 10 + int((idx + 1) / total_tables * 80)
            batch_tasks_status[task_id]['progress'] = progress
            batch_tasks_status[task_id]['processed_count'] = idx + 1
        
        # 导出
        output_dir = os.path.join('backend', 'outputs')
        exporter = ExcelExporter(output_dir)
        output_file = exporter.export_with_template(processed_tables, f"batch_{task_id}")
        
        batch_tasks_status[task_id].update({
            'status': 'success',
            'progress': 100,
            'output_path': output_file
        })
        
        return success_response({'task_id': task_id})
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        batch_tasks_status[task_id]['status'] = 'failed'
        batch_tasks_status[task_id]['message'] = str(e)
        print(f"[批量任务 {task_id}] 错误: {error_trace}")
        return error_response(40002, f"批量处理失败: {str(e)}")
    finally:
        # 清理上传的临时文件
        try:
            if os.path.exists(upload_path) and batch_tasks_status[task_id]['status'] == 'failed':
                os.remove(upload_path)
        except:
            pass

@batch_bp.route('/status/<task_id>', methods=['GET'])
def get_batch_status(task_id):
    """查询批量任务状态"""
    status = batch_tasks_status.get(task_id)
    if not status:
        return error_response(40401, "任务不存在")
    
    return success_response({
        'task_id': task_id,
        'status': status['status'],
        'progress': status.get('progress', 0),
        'message': status.get('message', ''),
        'processed_count': status.get('processed_count', 0),
        'total_count': status.get('total_count', 0)
    })

@batch_bp.route('/download/<task_id>', methods=['GET'])
def download_batch_result(task_id):
    """下载批量处理结果"""
    try:
        status = batch_tasks_status.get(task_id)
        if not status or status['status'] != 'success':
            return error_response(40401, "结果文件不存在或任务未完成")
        
        if not os.path.exists(status['output_path']):
            return error_response(40401, "文件已过期或被删除")
        
        return send_file(
            os.path.abspath(status['output_path']),
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return error_response(50001, f"下载失败: {str(e)}")
