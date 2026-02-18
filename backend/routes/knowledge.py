# -*- coding: utf-8 -*-
from flask import Blueprint, request
from backend.services.field_matcher import EnhancedFieldMatcher as FieldMatcher
from backend.utils import success_response, error_response
import uuid
from difflib import SequenceMatcher

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/list', methods=['GET'])
def list_knowledge():
    """分页获取知识库条目"""
    try:
        q = request.args.get('q', '').lower().strip()
        table_id = request.args.get('table_id', '').strip()
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 验证分页参数
        if page < 1:
            return error_response(40001, "page 必须大于等于 1")
        if page_size < 1 or page_size > 100:
            return error_response(40001, "page_size 必须在 1-100 之间")
        
        matcher = FieldMatcher()
        kb_data = matcher.knowledge_base
        
        # 按关键词过滤
        if q:
            kb_data = [item for item in kb_data if q in item.get('source', '').lower() or q in item.get('target', '').lower()]
        
        # 按table_id过滤
        if table_id:
            kb_data = [item for item in kb_data if item.get('table_id') == table_id]
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        total = len(kb_data)
        
        return success_response({
            'list': kb_data[start:end],
            'total': total
        })
    except ValueError:
        return error_response(40001, "page 和 page_size 必须是整数")
    except Exception as e:
        import traceback
        print(f"[knowledge/list] 错误: {traceback.format_exc()}")
        return error_response(50001, f"知识库列表查询失败: {str(e)}")

@knowledge_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取知识库匹配统计"""
    matcher = FieldMatcher()
    kb_data = matcher.knowledge_base
    
    # 按table_id统计
    by_table = {}
    for item in kb_data:
        table_id = item.get('table_id', 'default')
        by_table[table_id] = by_table.get(table_id, 0) + 1
    
    by_table_list = [{'table_id': k, 'count': v} for k, v in by_table.items()]
    
    # 获取热门映射（按命中数排序）
    top_hits = sorted(kb_data, key=lambda x: x.get('hits', 0), reverse=True)[:10]
    
    return success_response({
        'total': len(kb_data),
        'by_table': by_table_list,
        'top_hits': top_hits
    })

@knowledge_bp.route('/upsert', methods=['POST'])
def upsert():
    """新增或更新知识库映射"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    item_id = data.get('id', str(uuid.uuid4()))
    table_id = data.get('table_id', 'default')
    source = data.get('source', '').strip()
    target = data.get('target', '').strip()
    confidence = data.get('confidence', 0.8)
    
    if not source or not target:
        return error_response(40001, "缺少参数: source 和 target")
    
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        return error_response(40001, "confidence 必须是 0-1 之间的数值")
    
    try:
        matcher = FieldMatcher()
        matcher.save_mapping(source, target)
        return success_response({'id': item_id})
    except Exception as e:
        import traceback
        print(f"[knowledge/upsert] 错误: {traceback.format_exc()}")
        return error_response(50001, f"知识库保存失败: {str(e)}")

@knowledge_bp.route('/query', methods=['POST'])
def query_knowledge():
    """根据源字段查询知识库建议"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    source = data.get('source', '').strip()
    table_id = data.get('table_id')
    context = data.get('context', '')
    
    if not source:
        return error_response(40001, "缺少参数: source")
    
    try:
        matcher = FieldMatcher()
        kb_data = matcher.knowledge_base
        
        # 按table_id过滤（如果提供）
        if table_id:
            kb_data = [item for item in kb_data if item.get('table_id') == table_id]
        
        candidates = []
        
        for item in kb_data:
            item_source = item.get('source', '')
            item_target = item.get('target', '')
            
            # 精确匹配
            if item_source.lower() == source.lower():
                candidates.append({
                    'target': item_target,
                    'confidence': 1.0,
                    'match_type': 'exact',
                    'hits': item.get('hits', 0)
                })
            else:
                # 模糊匹配（相似度计算）
                similarity = SequenceMatcher(None, source.lower(), item_source.lower()).ratio()
                if similarity > 0.6:
                    candidates.append({
                        'target': item_target,
                        'confidence': round(similarity * 0.9, 3),  # 模糊匹配置信度降低，四舍五入到小数点后3位
                        'match_type': 'fuzzy',
                        'hits': item.get('hits', 0)
                    })
        
        # 按置信度和命中数排序
        candidates = sorted(candidates, key=lambda x: (x['confidence'], x['hits']), reverse=True)[:10]
        
        return success_response({'candidates': candidates})
    except Exception as e:
        import traceback
        print(f"[knowledge/query] 错误: {traceback.format_exc()}")
        return error_response(50001, f"知识库查询失败: {str(e)}")
