# -*- coding: utf-8 -*-
from flask import Blueprint, request
from backend.services.field_matcher import FieldMatcher
from backend.utils import success_response, error_response

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/knowledge/list', methods=['GET'])
def list_knowledge():
    q = request.args.get('q', '').lower()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    
    matcher = FieldMatcher()
    kb_data = matcher.knowledge_base
    
    if q:
        kb_data = [item for item in kb_data if q in item['source'].lower() or q in item['target'].lower()]
        
    start = (page - 1) * page_size
    end = start + page_size
    
    return success_response({
        'list': kb_data[start:end],
        'total': len(kb_data)
    })

@knowledge_bp.route('/knowledge/stats', methods=['GET'])
def get_stats():
    matcher = FieldMatcher()
    return success_response({
        'total': len(matcher.knowledge_base),
        'by_table': [],
        'top_hits': sorted(matcher.knowledge_base, key=lambda x: x.get('hits', 0), reverse=True)[:5]
    })

@knowledge_bp.route('/knowledge/upsert', methods=['POST'])
def upsert():
    data = request.json
    source = data.get('source')
    target = data.get('target')
    if not source or not target:
        return error_response(40001, "缺少参数")
    
    matcher = FieldMatcher()
    matcher.save_mapping(source, target)
    return success_response({'id': 'ok'})
