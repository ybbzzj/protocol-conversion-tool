# -*- coding: utf-8 -*-
from flask import Blueprint, request
from backend.utils import success_response, error_response
from backend.routes.extract import tasks_status

history_bp = Blueprint('history', __name__)

@history_bp.route('/', methods=['GET'])
def get_history():
    """获取历史记录列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 验证分页参数
        if page < 1:
            return error_response(40001, "page 必须大于等于 1")
        if page_size < 1 or page_size > 100:
            return error_response(40001, "page_size 必须在 1-100 之间")
        
        # 从任务存储中获取所有任务
        all_tasks = []
        for task_id, task_info in tasks_status.items():
            all_tasks.append({
                'id': task_id[:8],  # 任务ID前8位
                'time': task_info.get('created_at', ''),
                'file': task_info.get('filename', ''),
                'status': task_info.get('status', 'unknown'),
                'detail': f"{task_info.get('msg_name', '—')} (表数: {task_info.get('table_count', 0)})",
                'message': task_info.get('message', '')
            })
        
        # 按时间倒序排列
        all_tasks = sorted(all_tasks, key=lambda x: x['time'], reverse=True)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        total = len(all_tasks)
        
        return success_response({
            'list': all_tasks[start:end],
            'total': total
        })
    except ValueError:
        return error_response(40001, "page 和 page_size 必须是整数")
    except Exception as e:
        import traceback
        print(f"[history] 错误: {traceback.format_exc()}")
        return error_response(50001, f"历史记录查询失败: {str(e)}")
