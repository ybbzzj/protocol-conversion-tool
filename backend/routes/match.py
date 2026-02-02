# -*- coding: utf-8 -*-
from flask import Blueprint, request
from backend.services.field_matcher import FieldMatcher
from backend.utils import success_response, error_response
import uuid

match_bp = Blueprint('match', __name__)

@match_bp.route('/match/parse-protocol', methods=['POST'])
def parse_protocol():
    # 模拟从文本或文件提取字段
    text = request.json.get('text') if request.is_json else None
    if not text and 'file' in request.files:
        # 这里实际应调用解析逻辑，暂模拟返回固定字段
        return success_response({'fields': ['序号', '参数', '数据类型', '备注']})
    
    import re
    fields = re.split(r'[,，;；\n\t|]', text) if text else []
    return success_response({'fields': [f.strip() for f in fields if f.strip()]})

@match_bp.route('/match/save-mapping', methods=['POST'])
def save_mapping():
    data = request.json
    table_id = data.get('table_id')
    mapping = data.get('mapping', [])
    
    if not table_id or not mapping:
        return error_response(40001, "缺少参数")
        
    matcher = FieldMatcher()
    for item in mapping:
        source = item.get('source')
        target = item.get('target')
        if source and target:
            matcher.save_mapping(source, target)
            
    return success_response({'id': str(uuid.uuid4())})
