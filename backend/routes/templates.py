# -*- coding: utf-8 -*-
from flask import Blueprint, request
from backend.utils import success_response, error_response
import uuid
import json
import os

templates_bp = Blueprint('templates', __name__)

# 本地存储模板数据
CONFIG_FILE_TEMPLATES = 'backend/config_templates.json'

def load_json_file(filepath):
    """加载JSON文件"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_json_file(filepath, data):
    """保存JSON文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@templates_bp.route('/list', methods=['GET'])
def list_templates():
    """获取模板列表"""
    templates = load_json_file(CONFIG_FILE_TEMPLATES)
    return success_response({'list': templates})

@templates_bp.route('/upsert', methods=['POST'])
def upsert_template():
    """新增或更新模板"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    template_id = data.get('id', str(uuid.uuid4()))
    name = data.get('name', '').strip()
    field_ids = data.get('field_ids', [])
    
    if not name:
        return error_response(40001, "缺少参数: name")
    
    if len(name) > 100:
        return error_response(40001, "name 长度不能超过 100 个字符")
    
    if not isinstance(field_ids, list):
        return error_response(40001, "field_ids 必须是数组")
    
    try:
        templates = load_json_file(CONFIG_FILE_TEMPLATES)
        
        # 查找是否存在
        existing = next((t for t in templates if t['id'] == template_id), None)
        if existing:
            # 更新
            existing['name'] = name
            existing['field_ids'] = field_ids
        else:
            # 新增
            templates.append({
                'id': template_id,
                'name': name,
                'field_ids': field_ids
            })
        
        save_json_file(CONFIG_FILE_TEMPLATES, templates)
        return success_response({'id': template_id})
    except Exception as e:
        import traceback
        print(f"[templates/upsert] 错误: {traceback.format_exc()}")
        return error_response(50001, f"模板保存失败: {str(e)}")

@templates_bp.route('/delete', methods=['POST'])
def delete_template():
    """删除模板"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    template_id = data.get('id')
    if not template_id:
        return error_response(40001, "缺少参数: id")
    
    try:
        templates = load_json_file(CONFIG_FILE_TEMPLATES)
        original_count = len(templates)
        templates = [t for t in templates if t['id'] != template_id]
        
        if len(templates) == original_count:
            return error_response(40401, f"模板不存在: {template_id}")
        
        save_json_file(CONFIG_FILE_TEMPLATES, templates)
        return success_response({})
    except Exception as e:
        import traceback
        print(f"[templates/delete] 错误: {traceback.format_exc()}")
        return error_response(50001, f"模板删除失败: {str(e)}")
