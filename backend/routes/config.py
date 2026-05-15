# -*- coding: utf-8 -*-
from flask import Blueprint, request
from backend.utils import success_response, error_response
import uuid
import json
import os

config_bp = Blueprint('config', __name__)

# 本地存储配置数据
CONFIG_FILE_PROTOCOL = 'backend/config_protocol_fields.json'
CONFIG_FILE_TARGET = 'backend/config_target_fields.json'

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

# ============ 协议字段接口 ============

@config_bp.route('/protocol-fields', methods=['GET'])
def get_protocol_fields():
    """获取协议字段列表"""
    fields = load_json_file(CONFIG_FILE_PROTOCOL)
    return success_response({'list': fields})

@config_bp.route('/protocol-fields/upsert', methods=['POST'])
def upsert_protocol_field():
    """新增或更新协议字段"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    field_id = data.get('id', str(uuid.uuid4()))
    name = data.get('name', '').strip()
    
    if not name:
        return error_response(40001, "缺少参数: name")
    
    if len(name) > 100:
        return error_response(40001, "name 长度不能超过 100 个字符")
    
    try:
        fields = load_json_file(CONFIG_FILE_PROTOCOL)
        
        # 查找是否存在
        existing = next((f for f in fields if f['id'] == field_id), None)
        if existing:
            # 更新
            existing['name'] = name
        else:
            # 新增
            fields.append({'id': field_id, 'name': name})
        
        save_json_file(CONFIG_FILE_PROTOCOL, fields)
        return success_response({'id': field_id})
    except Exception as e:
        import traceback
        print(f"[config/protocol-fields/upsert] 错误: {traceback.format_exc()}")
        return error_response(50001, f"协议字段保存失败: {str(e)}")

@config_bp.route('/protocol-fields/delete', methods=['POST'])
def delete_protocol_field():
    """删除协议字段"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    field_id = data.get('id')
    if not field_id:
        return error_response(40001, "缺少参数: id")
    
    try:
        fields = load_json_file(CONFIG_FILE_PROTOCOL)
        original_count = len(fields)
        fields = [f for f in fields if f['id'] != field_id]
        
        if len(fields) == original_count:
            return error_response(40401, f"协议字段不存在: {field_id}")
        
        save_json_file(CONFIG_FILE_PROTOCOL, fields)
        return success_response({})
    except Exception as e:
        import traceback
        print(f"[config/protocol-fields/delete] 错误: {traceback.format_exc()}")
        return error_response(50001, f"协议字段删除失败: {str(e)}")

# ============ 目标字段接口 ============

@config_bp.route('/target-fields', methods=['GET'])
def get_target_fields():
    """获取目标字段列表"""
    fields = load_json_file(CONFIG_FILE_TARGET)
    return success_response({'list': fields})

@config_bp.route('/target-fields/upsert', methods=['POST'])
def upsert_target_field():
    """新增或更新目标字段"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    field_id = data.get('id', str(uuid.uuid4()))
    name = data.get('name', '').strip()
    
    if not name:
        return error_response(40001, "缺少参数: name")
    
    if len(name) > 100:
        return error_response(40001, "name 长度不能超过 100 个字符")
    
    try:
        fields = load_json_file(CONFIG_FILE_TARGET)
        
        # 查找是否存在
        existing = next((f for f in fields if f['id'] == field_id), None)
        if existing:
            # 更新
            existing['name'] = name
        else:
            # 新增
            fields.append({'id': field_id, 'name': name})
        
        save_json_file(CONFIG_FILE_TARGET, fields)
        return success_response({'id': field_id})
    except Exception as e:
        import traceback
        print(f"[config/target-fields/upsert] 错误: {traceback.format_exc()}")
        return error_response(50001, f"目标字段保存失败: {str(e)}")

@config_bp.route('/target-fields/delete', methods=['POST'])
def delete_target_field():
    """删除目标字段"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    field_id = data.get('id')
    if not field_id:
        return error_response(40001, "缺少参数: id")
    
    try:
        fields = load_json_file(CONFIG_FILE_TARGET)
        original_count = len(fields)
        fields = [f for f in fields if f['id'] != field_id]
        
        if len(fields) == original_count:
            return error_response(40401, f"目标字段不存在: {field_id}")
        
        save_json_file(CONFIG_FILE_TARGET, fields)
        return success_response({})
    except Exception as e:
        import traceback
        print(f"[config/target-fields/delete] 错误: {traceback.format_exc()}")
        return error_response(50001, f"目标字段删除失败: {str(e)}")
