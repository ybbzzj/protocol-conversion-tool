# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from backend.services.field_matcher import FieldMatcher

match_bp = Blueprint('match', __name__)

@match_bp.route('/match/save-mapping', methods=['POST'])
def save_mapping():
    data = request.json
    source = data.get('source')
    target = data.get('target')
    
    if not source or not target:
        return jsonify({'status': 'error', 'message': '缺少参数'}), 400
        
    matcher = FieldMatcher()
    matcher.save_mapping(source, target)
    return jsonify({'status': 'success', 'message': '映射已保存至本地知识库'})
