# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
import os
from datetime import datetime
from backend.services.table_detector import DocumentParser
from backend.services.excel_exporter import ExcelExporter

extract_bp = Blueprint('extract', __name__)

@extract_bp.route('/extract/start', methods=['POST'])
def start_extraction():
    # 这里模拟提取接口逻辑
    return jsonify({
        'status': 'success',
        'task_id': f"task_{datetime.now().strftime('%H%M%S')}",
        'message': '提取任务已启动'
    })

@extract_bp.route('/extract/preview/<task_id>', methods=['GET'])
def get_preview(task_id):
    return jsonify({'status': 'success', 'data': []})
