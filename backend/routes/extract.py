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

# 全局任务存储 - 所有任务共享此存储
tasks_status = {}

@extract_bp.route('/start', methods=['POST'])
def start_extraction():
    """创建文档提取任务"""
    if 'file' not in request.files:
        return error_response(40001, "缺少文件参数")
    
    file = request.files['file']
    if not file or file.filename == '':
        return error_response(40001, "文件为空")
    
    # 验证文件类型
    allowed_extensions = {'.doc', '.docx', '.xlsx', '.xls', '.csv'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return error_response(40001, f"不支持的文件格式，请上传 {', '.join(allowed_extensions)} 格式的文件")
    
    field_ids = request.form.getlist('field_ids')
    
    task_id = str(uuid.uuid4())
    upload_path = os.path.join('backend', 'uploads', f"{task_id}_{file.filename}")
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    
    # 初始化任务信息（包含仪表盘所需数据）
    tasks_status[task_id] = {
        'status': 'running',
        'progress': 0,
        'file_path': upload_path,
        'filename': file.filename,
        'created_at': datetime.now().isoformat(),
        'msg_name': '',  # 表名称（第一个表的名称）
        'table_count': 0,
        'output_path': None,
        'message': ''
    }
    
    try:
        # 保存文件
        file.save(upload_path)
        tasks_status[task_id]['progress'] = 10
        
        # 执行提取
        parser = DocumentParser()
        result = parser.parse(upload_path)
        tasks_status[task_id]['progress'] = 50
        
        processor = DataProcessor()
        matcher = FieldMatcher()
        
        processed_tables = []
        table_count = len(result['tables'])
        
        # 记录第一个表的名称作为主表名
        if result['tables']:
            tasks_status[task_id]['msg_name'] = result['tables'][0].get('msg_name', '')
            tasks_status[task_id]['table_count'] = table_count
        
        for idx, table in enumerate(result['tables']):
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
            
            # 更新进度
            progress = 50 + int((idx + 1) / table_count * 30) if table_count > 0 else 80
            tasks_status[task_id]['progress'] = progress
            
        # 导出
        output_dir = os.path.join('backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        exporter = ExcelExporter(output_dir)
        output_file = exporter.export_with_template(processed_tables, task_id)
        tasks_status[task_id]['progress'] = 90
        
        tasks_status[task_id].update({
            'status': 'success',
            'progress': 100,
            'output_path': output_file
        })
        
        return success_response({'task_id': task_id})
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        tasks_status[task_id]['status'] = 'failed'
        tasks_status[task_id]['message'] = str(e)
        print(f"[提取任务 {task_id}] 错误: {error_trace}")
        return error_response(40002, f"文件解析失败: {str(e)}")
    finally:
        # 清理上传的临时文件
        try:
            if os.path.exists(upload_path) and tasks_status[task_id]['status'] == 'failed':
                os.remove(upload_path)
        except:
            pass

@extract_bp.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    status = tasks_status.get(task_id)
    if not status:
        return error_response(40401, "任务不存在")
    return success_response({
        'status': status['status'],
        'progress': status.get('progress', 0),
        'message': status.get('message', '')
    })

@extract_bp.route('/download/<task_id>', methods=['GET'])
def download_result(task_id):
    try:
        status = tasks_status.get(task_id)
        if not status or status['status'] != 'success':
            return error_response(40401, "结果文件不存在或任务未完成")
        
        output_path = status['output_path']
        if not output_path or not os.path.exists(output_path):
            return error_response(40401, "文件已过期或被删除")
        
        # ✅ 提取文件名作为下载名称，使用英文文件名避免编码问题
        filename = f"result_{task_id[:8]}.xlsx"
        
        # 直接返回文件内容，避免send_file的潜在问题
        from flask import Response
        
        with open(os.path.abspath(output_path), 'rb') as f:
            file_content = f.read()
        
        response = Response(
            file_content,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Length': str(len(file_content))
            }
        )
        
        # 暂时注释掉自动删除功能，确保可以验证文件一致性
        # try:
        #     if os.path.exists(output_path):
        #         os.remove(output_path)
        #         print(f"[下载完成] 已删除文件: {output_path}")
        #         # 更新任务状态，标记文件已被下载
        #         status['output_path'] = None
        #         status['message'] = '文件已下载并删除'
        # except Exception as e:
        #     print(f"[警告] 删除文件失败: {e}")
        
        return response
    except Exception as e:
        return error_response(50001, f"下载失败: {str(e)}")
