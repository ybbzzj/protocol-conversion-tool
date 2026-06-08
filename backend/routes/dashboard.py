# -*- coding: utf-8 -*-
import os
from flask import Blueprint
from backend.utils import success_response
from backend.routes.extract import tasks_status

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/recent', methods=['GET'])
def get_recent():
    """获取最近任务列表和统计信息"""
    # 从任务存储中获取真实数据
    recent_tasks = []
    total = len(tasks_status)
    success_count = 0
    fail_count = 0
    
    # 按创建时间倒序排列，获取最近10个任务
    sorted_tasks = sorted(
        tasks_status.items(),
        key=lambda x: x[1].get('created_at', ''),
        reverse=True
    )[:10]
    
    for task_id, task_info in sorted_tasks:
        status = task_info.get('status', 'unknown')
        if status == 'success':
            success_count += 1
        elif status == 'failed':
            fail_count += 1
        
        file_path = task_info.get('file_path', '')
        abs_path = os.path.abspath(file_path) if file_path else ''

        recent_tasks.append({
            'id': task_id[:8],  # 任务ID前8位作为显示
            'task_id': task_id,  # 完整任务ID，供前端跳转人工映射页
            'time': task_info.get('created_at', ''),
            'table': task_info.get('msg_name', '—'),  # 表名称
            'source_path': abs_path,  # 导入文档在服务器的绝对路径
            'status': status
        })
    
    return success_response({
        'recent': recent_tasks,
        'stats': {
            'total': total,
            'success': success_count,
            'fail': fail_count
        }
    })
