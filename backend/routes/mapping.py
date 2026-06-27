# -*- coding: utf-8 -*-
"""
字段映射路由模块
处理字段预览、映射配置、人工修正等功能
"""
from flask import Blueprint, request, jsonify
import os
import json
from typing import Dict, List, Any, Tuple
from backend.utils import success_response, error_response
from backend.services.field_matcher import EnhancedFieldMatcher as FieldMatcher
from backend.services.table_detector import TableDetector

# 创建蓝图
mapping_bp = Blueprint('mapping', __name__, url_prefix='/api/mapping')

# 全局变量存储任务映射配置
task_mappings = {}
# 全局变量存储用户自定义映射（持久化）
user_mappings = {}

# 人工映射的置信度：用户在映射页点击“应用”即视为人工确认，代表明确意图，
# 须 ≥ 知识库精确匹配门槛(0.9，见 field_matcher._exact_match)，
# 以确保该映射对后续新文档永久自动生效（而非沿用系统推荐的相似度）。
MANUAL_MAPPING_CONFIDENCE = 1.0

# 加载用户映射配置
def load_user_mappings():
    """加载用户自定义映射配置"""
    config_path = os.path.join('backend', 'data', 'user_mappings.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[加载用户映射] 错误: {e}")
    return {}

# 保存用户映射配置
def save_user_mappings():
    """保存用户自定义映射配置"""
    config_path = os.path.join('backend', 'data', 'user_mappings.json')
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(user_mappings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[保存用户映射] 错误: {e}")

# 初始化加载用户映射
user_mappings = load_user_mappings()

@mapping_bp.route('/preview/<task_id>', methods=['GET'])
def preview_extraction(task_id: str):
    """
    预览文档提取结果和字段映射建议
    """
    try:
        # 获取任务状态和原始表格数据
        from backend.routes.extract import tasks_status
        status = tasks_status.get(task_id)
        if not status or status['status'] != 'success':
            return error_response(40401, "任务未完成或不存在")
        
        # 使用原始提取的表格数据而不是最终导出的文件
        raw_tables = status.get('raw_tables', [])
        if not raw_tables:
            return error_response(40401, "原始表格数据不存在")
        
        # 从原始表格中提取字段和数据
        extracted_fields, table_data = _extract_fields_and_data_from_raw_tables(raw_tables)
        
        # 获取字段匹配建议
        matcher = FieldMatcher()
        mapping_suggestions = matcher.match_with_context(extracted_fields)
        
        # 分离已匹配和未匹配字段
        matched_fields = [f for f in mapping_suggestions if f['matched']]
        unmatched_fields = [f for f in mapping_suggestions if not f['matched']]
        
        return success_response({
            'extracted_fields': extracted_fields,
            'table_data': table_data,
            'mapping_suggestions': mapping_suggestions,
            'matched_fields': matched_fields,
            'unmatched_fields': unmatched_fields,
            'total_fields': len(extracted_fields),
            'expected_fields': status.get('expected_fields', [])
        })
        
    except Exception as e:
        return error_response(50001, f"预览失败: {str(e)}")

@mapping_bp.route('/batch-suggest', methods=['POST'])
def batch_suggest():
    """批量获取字段推荐"""
    try:
        data = request.json
        source_fields = data.get('source_fields', [])
        available_targets = data.get('available_targets', [])
        
        matcher = FieldMatcher()
        suggestions = {}
        
        for source_field in source_fields:
            field_suggestions = matcher.suggest_with_context(
                source_field,
                {'available_targets': available_targets}
            )
            
            # 只返回可用的目标字段
            filtered = [
                s for s in field_suggestions 
                if s['field'] in available_targets
            ][:3]  # 最多3个推荐
            
            if filtered:
                suggestions[source_field] = [
                    {
                        'target': s['field'],
                        'confidence': s['similarity'],
                        'reason': s.get('reason', '相似度匹配')
                    }
                    for s in filtered
                ]
        
        return success_response({'suggestions': suggestions})
        
    except Exception as e:
        import traceback
        print(f"[mapping/batch-suggest] 错误: {traceback.format_exc()}")
        return error_response(50001, f"批量推荐失败: {str(e)}")

@mapping_bp.route('/auto-map', methods=['POST'])
def auto_map():
    """智能自动映射"""
    try:
        data = request.json
        source_fields = data.get('source_fields', [])
        target_fields = data.get('target_fields', [])
        threshold = data.get('threshold', 0.75)
        
        matcher = FieldMatcher()
        auto_mappings = []
        used_targets = set()
        
        for source in source_fields:
            # 查找最佳匹配
            best_match = None
            best_score = 0
            
            for target in target_fields:
                if target in used_targets:
                    continue
                
                # 计算相似度
                similarity = matcher._calculate_similarity(source, target)
                
                # 检查知识库
                kb_match = matcher._exact_match(source)
                if kb_match and kb_match.get('target') == target:
                    similarity = max(similarity, 0.95)
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = target
            
            if best_match:
                auto_mappings.append({
                    'source': [source],
                    'target': best_match,
                    'confidence': best_score,
                    'type': 'auto'
                })
                used_targets.add(best_match)
        
        return success_response({
            'auto_mappings': auto_mappings,
            'remaining_sources': [s for s in source_fields if not any(m['source'][0] == s for m in auto_mappings)],
            'remaining_targets': [t for t in target_fields if t not in used_targets]
        })
        
    except Exception as e:
        import traceback
        print(f"[mapping/auto-map] 错误: {traceback.format_exc()}")
        return error_response(50001, f"自动映射失败: {str(e)}")

@mapping_bp.route('/apply', methods=['POST'])
def apply_mapping():
    """
    应用用户定义的字段映射配置
    """
    try:
        data = request.json
        if not data:
            return error_response(40001, "缺少请求体")
        
        task_id = data.get('task_id')
        mappings = data.get('mappings', [])
        
        if not task_id or not mappings:
            return error_response(40001, "缺少必要参数: task_id 和 mappings")
        
        # 验证映射数据格式
        for mapping in mappings:
            if not isinstance(mapping, dict):
                return error_response(40001, "映射项必须是对象格式")
            if 'original' not in mapping or 'target' not in mapping:
                return error_response(40001, "映射项缺少 original 或 target 字段")
        
        # 保存到任务映射（临时）
        task_mappings[task_id] = {
            'mappings': mappings,
            'applied_at': __import__('datetime').datetime.now().isoformat()
        }
        
        # 保存到用户映射（持久化）
        applied_count = 0
        for mapping in mappings:
            if mapping.get('target'):  # 只保存有效的映射
                original = mapping['original']
                target = mapping['target']

                # 保存用户映射（人工确认，置信度固定为高，保证永久生效）
                user_mappings[original] = {
                    'target': target,
                    'confidence': MANUAL_MAPPING_CONFIDENCE,
                    'created_at': __import__('datetime').datetime.now().isoformat()
                }
                applied_count += 1
        
        # 持久化保存
        save_user_mappings()
        
        # 更新知识库
        matcher = FieldMatcher()
        for mapping in mappings:
            if mapping.get('target'):  # 只保存有效的映射
                matcher.save_mapping(
                    mapping['original'], 
                    mapping['target'],
                    confidence=MANUAL_MAPPING_CONFIDENCE
                )

        # 根据本次映射重新生成当前任务的 Excel，使修正对当前文档立即生效
        from backend.routes.extract import regenerate_output
        user_overrides = {
            m['original']: m['target']
            for m in mappings
            if m.get('original') and m.get('target')
        }
        regenerated, regen_msg = regenerate_output(task_id, user_overrides)

        return success_response({
            'success': True,
            'applied_count': applied_count,
            'task_id': task_id,
            'regenerated': regenerated,
            'message': '已应用并重新生成结果' if regenerated else f'映射已保存，但重新生成失败：{regen_msg}'
        })
        
    except Exception as e:
        return error_response(50001, f"应用映射失败: {str(e)}")

@mapping_bp.route('/suggest/<task_id>', methods=['GET'])
def get_mapping_suggestions(task_id: str):
    """
    获取字段匹配建议
    """
    try:
        # 获取提取的字段
        from backend.routes.extract import tasks_status
        status = tasks_status.get(task_id)
        if not status:
            return error_response(40401, "任务不存在")
        
        output_path = status.get('output_path')
        if not output_path or not os.path.exists(output_path):
            return error_response(40401, "提取结果文件不存在")
        
        extracted_fields = _extract_fields_from_output(output_path)
        
        # 获取建议
        matcher = FieldMatcher()
        suggestions = matcher.get_detailed_suggestions(extracted_fields)
        
        return success_response({
            'suggestions': suggestions,
            'field_count': len(extracted_fields)
        })
        
    except Exception as e:
        return error_response(50001, f"获取建议失败: {str(e)}")

@mapping_bp.route('/custom', methods=['POST'])
def add_custom_mapping():
    """
    添加自定义字段映射
    """
    try:
        data = request.json
        if not data:
            return error_response(40001, "缺少请求体")
        
        source = data.get('source')
        target = data.get('target')
        table_id = data.get('table_id', 'default')
        
        if not source or not target:
            return error_response(40001, "缺少 source 或 target 参数")
        
        # 保存到知识库
        matcher = FieldMatcher()
        matcher.save_mapping(source, target, table_id=table_id, confidence=0.9)
        
        return success_response({
            'success': True,
            'message': f"已添加映射: {source} → {target}"
        })
        
    except Exception as e:
        return error_response(50001, f"添加自定义映射失败: {str(e)}")

@mapping_bp.route('/user-mappings', methods=['GET'])
def get_user_mappings():
    """
    获取用户自定义映射列表
    """
    try:
        return success_response({
            'mappings': user_mappings,
            'count': len(user_mappings)
        })
    except Exception as e:
        return error_response(50001, f"获取用户映射失败: {str(e)}")

@mapping_bp.route('/user-mappings', methods=['POST'])
def add_user_mapping():
    """
    添加用户自定义映射
    """
    try:
        data = request.json
        if not data:
            return error_response(40001, "缺少请求体")
        
        original = data.get('original')
        target = data.get('target')
        confidence = data.get('confidence', 0.8)
        
        if not original or not target:
            return error_response(40001, "缺少 original 或 target 参数")
        
        # 保存用户映射
        user_mappings[original] = {
            'target': target,
            'confidence': confidence,
            'created_at': __import__('datetime').datetime.now().isoformat()
        }
        
        # 持久化保存
        save_user_mappings()
        
        # 更新知识库
        matcher = FieldMatcher()
        matcher.save_mapping(original, target, confidence=confidence)
        
        return success_response({
            'success': True,
            'message': f"已添加映射: {original} → {target}"
        })
        
    except Exception as e:
        return error_response(50001, f"添加用户映射失败: {str(e)}")

@mapping_bp.route('/user-mappings/<original_field>', methods=['DELETE'])
def delete_user_mapping(original_field: str):
    """
    删除用户自定义映射
    """
    try:
        if original_field in user_mappings:
            del user_mappings[original_field]
            save_user_mappings()
            return success_response({
                'success': True,
                'message': f"已删除映射: {original_field}"
            })
        else:
            return error_response(40401, "映射不存在")
    except Exception as e:
        return error_response(50001, f"删除用户映射失败: {str(e)}")

def _extract_fields_and_data_from_raw_tables(raw_tables: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """
    从原始表格数据中提取字段名和完整表格数据
    返回: (字段列表, 表格数据列表)
    
    修复：遍历所有有效的字段表（field_def类型），避免前面有空表或干扰表时误报字段为零
    """
    try:
        if not raw_tables:
            return [], []
        
        # 收集所有字段表的字段名（去重）
        all_fields = set()
        all_table_data = []
        
        # 遍历所有表格，只处理有效的字段定义表
        for table in raw_tables:
            table_type = table.get('table_type', '')
            table_name = table.get('msg_name', 'Unknown')
            data_rows = table.get('data_rows', [])
            
            # 只处理字段定义表，跳过辅助表和干扰表
            if table_type not in ('field_def', '', None):
                continue
            
            # 如果表格有数据行，提取字段
            if data_rows:
                # 从第一行提取字段名
                first_row = data_rows[0]
                fields = list(first_row.keys())
                all_fields.update(fields)
                
                # 添加表格数据（只取第一行用于预览）
                row_with_table = {'表格名称': table_name, '行号': 1}
                row_with_table.update(first_row)
                all_table_data.append(row_with_table)
        
        # 转换为有序列表
        fields_list = list(all_fields)
        
        # 如果没有找到任何有效字段表，返回空列表
        if not fields_list:
            print("[原始表格数据提取] 未找到有效的字段定义表")
            return [], []
        
        return fields_list, all_table_data
    except Exception as e:
        # 如果处理失败，返回空列表
        print(f"[原始表格数据提取] 处理失败: {e}")
        import traceback
        print(traceback.format_exc())
        return [], []

# 注册蓝图到应用
def register_mapping_routes(app):
    """注册字段映射路由"""
    app.register_blueprint(mapping_bp)
