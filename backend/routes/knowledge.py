# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from backend.services.field_matcher import FieldMatcher

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/knowledge/list', methods=['GET'])
def list_knowledge():
    matcher = FieldMatcher()
    return jsonify({
        'status': 'success', 
        'data': matcher.knowledge_base,
        'total': len(matcher.knowledge_base)
    })
