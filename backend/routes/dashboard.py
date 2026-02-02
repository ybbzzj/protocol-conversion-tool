# -*- coding: utf-8 -*-
from flask import Blueprint
from backend.utils import success_response

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/recent', methods=['GET'])
def get_recent():
    # 模拟仪表盘数据
    return success_response({
        'recent': [
            {'id': '1', 'time': '2024-05-25 10:00:00', 'table': '控制指令', 'status': 'success'},
            {'id': '2', 'time': '2024-05-25 11:30:00', 'table': '器状态', 'status': 'success'}
        ],
        'stats': {
            'total': 10,
            'success': 8,
            'fail': 2
        }
    })
