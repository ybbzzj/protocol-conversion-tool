# -*- coding: utf-8 -*-
from flask import Blueprint, request
from backend.services.field_matcher import EnhancedFieldMatcher as FieldMatcher
from backend.services.table_detector import DocumentParser
from backend.utils import success_response, error_response
import uuid
import os
import re

match_bp = Blueprint('match', __name__)

@match_bp.route('/parse-protocol', methods=['POST'])
def parse_protocol():
    """从通信协议文本或文档提取字段"""
    if request.is_json:
        text = request.json.get('text') if request.json else None
    else:
        text = None
    
    file = request.files.get('file') if 'file' in request.files else None
    
    if not text and not file:
        return error_response(40001, "缺少参数：需要提供 text 或 file")
    
    fields = []
    temp_path = None
    
    try:
        if file:
            # 解析Word/Excel文件提取表头
            temp_path = os.path.join('backend', 'uploads', f"parse_{uuid.uuid4()}_{file.filename}")
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            file.save(temp_path)
            
            parser = DocumentParser()
            result = parser.parse(temp_path)
            
            # 从第一个表获取表头
            if result['tables'] and result['tables'][0]['headers']:
                fields = result['tables'][0]['headers']
        
        elif text:
            # 从文本分割提取字段
            fields = re.split(r'[,，;；\n\t|]', text)
            fields = [f.strip() for f in fields if f.strip()]
        
        return success_response({'fields': fields})
    
    except Exception as e:
        import traceback
        print(f"[parse-protocol] 错误: {traceback.format_exc()}")
        return error_response(40002, f"协议解析失败: {str(e)}")
    finally:
        # 清理临时文件
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass

@match_bp.route('/parse-target-headers', methods=['POST'])
def parse_target_headers():
    """解析目标Excel/Word表格的表头"""
    if 'file' not in request.files:
        return error_response(40001, "缺少文件参数")
    
    file = request.files['file']
    if not file or file.filename == '':
        return error_response(40001, "文件为空")
    
    temp_path = None
    try:
        temp_path = os.path.join('backend', 'uploads', f"target_{uuid.uuid4()}_{file.filename}")
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        parser = DocumentParser()
        result = parser.parse(temp_path)
        
        headers = []
        # 获取第一个表的表头
        if result['tables'] and result['tables'][0]['headers']:
            headers = result['tables'][0]['headers']
        
        return success_response({'headers': headers})
    except Exception as e:
        import traceback
        print(f"[parse-target-headers] 错误: {traceback.format_exc()}")
        return error_response(40002, f"表头提取失败: {str(e)}")
    finally:
        # 清理临时文件
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass

@match_bp.route('/save-mapping', methods=['POST'])
def save_mapping():
    """保存人工匹配的映射关系"""
    data = request.json
    if not data:
        return error_response(40001, "缺少请求体")
    
    table_id = data.get('table_id')
    mapping = data.get('mapping', [])
    operator = data.get('operator', '未知操作者')
    
    if not table_id or not mapping:
        return error_response(40001, "缺少参数: table_id 和 mapping")
    
    if not isinstance(mapping, list) or len(mapping) == 0:
        return error_response(40001, "mapping 必须是非空数组")
    
    try:
        matcher = FieldMatcher()
        saved_count = 0
        for item in mapping:
            source = item.get('source')
            target = item.get('target')
            if source and target:
                matcher.save_mapping(source, target)
                saved_count += 1
        
        if saved_count == 0:
            return error_response(40001, "没有有效的映射项")
        
        mapping_id = str(uuid.uuid4())
        return success_response({'id': mapping_id})
    except Exception as e:
        import traceback
        print(f"[save-mapping] 错误: {traceback.format_exc()}")
        return error_response(50001, f"保存映射失败: {str(e)}")
