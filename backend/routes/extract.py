# -*- coding: utf-8 -*-
from flask import Blueprint, request, send_file
import os
import uuid
import json
from datetime import datetime
from backend.utils import success_response, error_response
from backend.config import Config
from backend.services.table_detector import DocumentParser
from backend.services.table_linker import TableLinker
from backend.services.excel_exporter import ExcelExporter
from backend.services.data_cleaner import DataProcessor
from backend.services.field_matcher import EnhancedFieldMatcher as FieldMatcher
from backend.services.output_postprocessor import apply_output_controls, normalize_output_options

extract_bp = Blueprint('extract', __name__)

# 全局任务存储 - 所有任务共享此存储
tasks_status = {}

from backend.config import Config
TASKS_HISTORY_PATH = os.path.join(Config.DATA_DIR, 'tasks_history.json')

def _load_tasks_from_disk():
    """从磁盘加载任务历史记录"""
    global tasks_status
    try:
        if os.path.exists(TASKS_HISTORY_PATH):
            with open(TASKS_HISTORY_PATH, 'r', encoding='utf-8') as f:
                history = json.load(f)
                # 过滤掉过期的文件路径或大对象，只保留元数据
                tasks_status.update(history)
                print(f"[任务系统] 已从磁盘加载 {len(history)} 条历史记录")
    except Exception as e:
        print(f"[任务系统] 加载历史记录失败: {e}")

def _save_tasks_to_disk():
    """将任务元数据持久化到磁盘"""
    try:
        # 只持久化必要的元数据，排除 raw_tables 等大对象
        persist_data = {}
        # 只保留最近的 50 条记录
        sorted_ids = sorted(
            tasks_status.keys(),
            key=lambda x: tasks_status[x].get('created_at', ''),
            reverse=True
        )[:50]
        
        for tid in sorted_ids:
            task = tasks_status[tid]
            # 创建副本并删除大字段
            meta = {k: v for k, v in task.items() if k not in ('raw_tables', 'processed_tables')}
            persist_data[tid] = meta
            
        os.makedirs(os.path.dirname(TASKS_HISTORY_PATH), exist_ok=True)
        with open(TASKS_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(persist_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[任务系统] 持久化历史记录失败: {e}")

# 模块加载时自动读取
_load_tasks_from_disk()

@extract_bp.route('/start', methods=['POST'])
def start_extraction():
    """创建文档提取任务"""
    if 'file' not in request.files:
        return error_response(40001, "缺少文件参数")
    
    file = request.files['file']
    if not file or file.filename == '':
        return error_response(40001, "文件为空")
    
    # 验证文件类型
    allowed_extensions = {'.doc', '.docx', '.xlsx', '.xls', '.csv'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return error_response(40001, f"不支持的文件格式，请上传 {', '.join(allowed_extensions)} 格式的文件")
    
    field_ids = request.form.getlist('field_ids')
    field_names = request.form.getlist('field_names')
    output_options = _load_output_options(request.form)
    
    # 加载用户选择的期望字段
    expected_fields = field_names or _load_expected_fields(field_ids)
    
    task_id = str(uuid.uuid4())
    upload_path = os.path.join('backend', 'uploads', f"{task_id}_{file.filename}")
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    
    # 初始化任务信息（包含仪表盘所需数据和期望字段）
    tasks_status[task_id] = {
        'status': 'running',
        'progress': 0,
        'file_path': upload_path,
        'filename': file.filename,
        'created_at': datetime.now().isoformat(),
        'msg_name': '',  # 表名称（第一个表的名称）
        'table_count': 0,
        'output_path': None,
        'message': '',
        'field_ids': field_ids,
        'field_names': field_names,
        'output_options': output_options,
        'expected_fields': expected_fields,  # 期望字段
        'mapping_quality': None  # 映射质量评分
    }
    
    try:
        # 保存文件
        file.save(upload_path)
        tasks_status[task_id]['progress'] = 10
        
        # 执行提取
        parser = DocumentParser()
        result = parser.parse(upload_path)
        tasks_status[task_id]['progress'] = 50
        
        # 表格关联：注入元数据、过滤辅助表、附加bit子行
        linker = TableLinker()
        linked_tables = linker.link_tables(result['tables'])
        
        # 使用原始表格数据而不是处理后的数据
        # 保存原始提取的表格数据用于预览
        tasks_status[task_id]['raw_tables'] = result['tables']
        tasks_status[task_id]['linked_tables'] = linked_tables
        
        table_count = len(linked_tables)
        tasks_status[task_id]['table_count'] = table_count
        
        # 记录第一个表的名称作为主表名
        if linked_tables:
            tasks_status[task_id]['msg_name'] = linked_tables[0].get('msg_name', '')
            tasks_status[task_id]['table_count'] = table_count
        
        processed_tables = build_processed_tables(linked_tables, output_options=output_options)
        tasks_status[task_id]['processed_tables'] = processed_tables
        tasks_status[task_id]['progress'] = 80
            
        # 导出
        output_dir = os.path.join('backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        exporter = ExcelExporter(output_dir)
        output_file = exporter.export_with_template(processed_tables, task_id)
        tasks_status[task_id]['progress'] = 90
        
        # 计算映射质量
        extracted_field_names = _collect_exported_field_names(processed_tables)
        
        # 去重
        extracted_field_names = list(set(extracted_field_names))
        expected_fields = tasks_status[task_id].get('expected_fields', [])
        
        print(f'[映射质量调试] 提取字段数: {len(extracted_field_names)}')
        print(f'[映射质量调试] 期望字段数: {len(expected_fields)}')
        print(f'[映射质量调试] 提取字段: {extracted_field_names[:10]}...')
        print(f'[映射质量调试] 期望字段: {expected_fields}')
        
        mapping_quality = _calculate_mapping_quality(extracted_field_names, expected_fields)
        print(f'[映射质量调试] 计算结果: {mapping_quality}')
        
        tasks_status[task_id].update({
            'status': 'success',
            'progress': 100,
            'output_path': output_file,
            'mapping_quality': mapping_quality
        })
        
        # ✅ 保存到磁盘
        _save_tasks_to_disk()
        
        return success_response({
            'task_id': task_id,
            'expected_fields': expected_fields
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        tasks_status[task_id]['status'] = 'failed'
        tasks_status[task_id]['message'] = str(e)
        print(f"[提取任务 {task_id}] 错误: {error_trace}")
        
        # ✅ 保存到磁盘
        _save_tasks_to_disk()
        
        return error_response(40002, f"文件解析失败: {str(e)}")
    finally:
        # 清理上传的临时文件
        try:
            if os.path.exists(upload_path) and tasks_status[task_id]['status'] == 'failed':
                os.remove(upload_path)
        except:
            pass

@extract_bp.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    status = tasks_status.get(task_id)
    if not status:
        return error_response(40401, "任务不存在")
    return success_response({
        'status': status['status'],
        'progress': status.get('progress', 0),
        'message': status.get('message', ''),
        'mapping_quality': status.get('mapping_quality')
    })

@extract_bp.route('/download/<task_id>', methods=['GET'])
def download_result(task_id):
    try:
        status = tasks_status.get(task_id)
        if not status or status['status'] != 'success':
            return error_response(40401, "结果文件不存在或任务未完成")
        
        output_path = status['output_path']
        if not output_path or not os.path.exists(output_path):
            return error_response(40401, "文件已过期或被删除")
        
        # ✅ 使用原始上传文件名作为下载文件名
        original_filename = status.get('filename', f"result_{task_id[:8]}")
        # 移除文件扩展名并添加.xlsx
        name_without_ext = os.path.splitext(original_filename)[0]
        filename = f"{name_without_ext}.xlsx"
        
        # 直接返回文件内容，避免send_file的潜在问题
        from flask import Response
        
        with open(os.path.abspath(output_path), 'rb') as f:
            file_content = f.read()
        
        # 对文件名进行URL编码以避免中文编码问题
        import urllib.parse
        encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
        
        response = Response(
            file_content,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                'Content-Length': str(len(file_content))
            }
        )
        
        # 文件传输完成后删除源文件，确保结果只保留一份
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
                print(f"[下载完成] 已删除文件: {output_path}")
                # 更新任务状态，标记文件已被下载
                status['output_path'] = None
                status['message'] = '文件已下载并删除'
                _save_tasks_to_disk()
        except Exception as e:
            print(f"[警告] 删除文件失败: {e}")
        
        return response
    except Exception as e:
        return error_response(50001, f"下载失败: {str(e)}")


def _load_output_options(form):
    """读取前端输出控制选项。"""
    raw = {
        'remove_crc_checksum': form.get('remove_crc_checksum') in ('1', 'true', 'True', 'yes', 'on')
    }
    return normalize_output_options(raw)


def _normalize_field_mappings(mappings):
    """将前端映射列表转为 source -> target 字典。"""
    result = {}
    for item in mappings or []:
        if not isinstance(item, dict):
            continue
        source = item.get('original') or item.get('source')
        target = item.get('target')
        if isinstance(source, list):
            sources = source
        else:
            sources = [source]
        for src in sources:
            if src and target:
                result[str(src)] = str(target)
    return result


def _resolve_target_field(field, matcher, explicit_mapping):
    """优先使用人工映射，其次使用自动字段匹配。"""
    if field in explicit_mapping:
        return explicit_mapping[field]

    match_res = matcher.match_field(field)
    target = match_res.get('target') if isinstance(match_res, dict) else (
        match_res.target if hasattr(match_res, 'target') else field
    )
    return target if target else field


def _is_formula_source_mapped_to_remark(cleaned, explicit_mapping):
    """用户把数据处理类字段映射到备注时，不再额外生成转换公式列。"""
    for field in cleaned:
        target = explicit_mapping.get(field)
        if target != '备注':
            continue
        if any(kw in field for kw in ['数据处理', '数据转换', '转换公式']):
            return True
    return False


def _put_mapped_value(row, target, value):
    """写入映射值；多源映射到备注时合并保留。"""
    if value is None:
        return
    text = str(value).strip() if isinstance(value, str) else value
    if text in ('', '-', '—', None):
        return

    if target == '备注' and row.get(target):
        current = str(row[target]).strip()
        incoming = str(text).strip()
        parts = [p.strip() for p in current.split('；') if p.strip()]
        if incoming not in parts:
            row[target] = current + '；' + incoming
        return

    row[target] = value


def build_processed_tables(linked_tables, field_mappings=None, output_options=None):
    """
    将关联后的表格转为 ExcelExporter 可消费的数据。
    field_mappings 用于人工指定 source -> target，output_options 用于导出前后处理。
    """
    processor = DataProcessor()
    matcher = FieldMatcher()
    explicit_mapping = _normalize_field_mappings(field_mappings)

    processed_tables = []

    for table in linked_tables:
        table_type = table.get('table_type', '')
        if table_type not in ('field_def', '', None):
            continue

        table_rows = []
        for row in table.get('data_rows', []):
            # 过滤掉只有名称/内容但没有其他数据的无效行
            if not row.get('_is_bit_row') and not processor.is_valid_data_row(row):
                continue

            # bit 子行直接透传，不做 field 匹配
            if row.get('_is_bit_row'):
                table_rows.append(row)
                continue

            proc_res = processor.process_row(row)
            matched_row = {}
            formula_source_mapped_to_remark = False
            for field, value in proc_res['cleaned'].items():
                target = _resolve_target_field(field, matcher, explicit_mapping)
                if target == '备注' and any(kw in field for kw in ['数据处理', '数据转换', '转换公式']):
                    formula_source_mapped_to_remark = True
                _put_mapped_value(matched_row, target, value)

            formatted = dict(proc_res.get('formatted', {}))
            if formula_source_mapped_to_remark or _is_formula_source_mapped_to_remark(proc_res['cleaned'], explicit_mapping):
                formatted.pop('转换公式', None)

            # 保留格式化结果（值域、转换公式）
            for fkey, fval in formatted.items():
                matched_row[f'_fmt_{fkey}'] = fval

            # 位数对齐
            if '位数' in proc_res['converted']:
                matched_row['类型（bit）'] = proc_res['converted']['位数']

            table_rows.append(matched_row)

        table_data = {
            'msg_name': table.get('msg_name', ''),
            'data_rows': table_rows,
            'meta': table.get('meta', {}),
            'table_type': table_type,
            'meta_sources': table.get('meta_sources', {}),
        }
        processed_tables.append(table_data)

    return apply_output_controls(processed_tables, output_options)


def _collect_exported_field_names(processed_tables):
    """收集导出结果中可能出现的字段名，包含表级元数据列。"""
    extracted = []
    for table in processed_tables:
        for key in table.get('meta', {}).keys():
            extracted.append(ExcelExporter.META_TO_EXCEL.get(key, key))
        for row in table.get('data_rows', []):
            for key in row.keys():
                if str(key).startswith('_fmt_'):
                    extracted.append(str(key)[5:])
                elif not str(key).startswith('_'):
                    extracted.append(key)
    return list(set(extracted))


def _load_expected_fields(field_ids):
    """
    根据用户选择的字段ID加载期望字段名称
    """
    try:
        # 从配置文件加载协议字段
        config_path = Config.PROTOCOL_FIELDS_PATH
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                protocol_fields = json.load(f)
                
                # 根据ID查找字段名称
                expected_names = []
                for field_id in field_ids:
                    # 处理数组格式的配置文件
                    if isinstance(protocol_fields, list):
                        for field in protocol_fields:
                            if isinstance(field, dict) and str(field.get('id', '')) == str(field_id):
                                expected_names.append(field['name'])
                                break
                
                return expected_names
        
        return []
    except Exception as e:
        print(f"[加载期望字段] 错误: {e}")
        return []


def _calculate_mapping_quality(extracted_fields, expected_fields):
    """
    计算字段映射质量评分
    """
    if not extracted_fields or not expected_fields:
        return {
            'score': 0,
            'level': 'unknown',
            'exact_count': 0,
            'semantic_count': 0,
            'alias_count': 0,
            'fuzzy_count': 0,
            'unmatched_count': 0,
            'total': 0
        }
    
    matcher = FieldMatcher()
    mapping_results = []
    
    # 对每个提取的字段进行匹配
    for ext_field in extracted_fields:
        match_result = matcher.match_field(ext_field)
        mapping_results.append(match_result)
    
    # 统计匹配结果
    exact_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'exact')
    semantic_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'semantic')
    alias_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'alias')
    fuzzy_only_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'fuzzy')
    # 保持兼容：历史字段 fuzzy_count 仍返回“广义模糊”数量
    fuzzy_count = fuzzy_only_count + semantic_count + alias_count
    unmatched_count = sum(1 for r in mapping_results if isinstance(r, dict) and not r.get('target'))
    total = len(mapping_results)
    
    # 计算加权评分
    if total > 0:
        score = (
            exact_count * 1.0
            + semantic_count * 0.85
            + alias_count * 0.8
            + fuzzy_only_count * 0.7
        ) / total
        level = 'excellent' if score > 0.9 else 'good' if score > 0.7 else 'poor'
    else:
        score = 0
        level = 'unknown'
    
    return {
        'score': score,
        'level': level,
        'exact_count': exact_count,
        'semantic_count': semantic_count,
        'alias_count': alias_count,
        'fuzzy_count': fuzzy_count,
        'unmatched_count': unmatched_count,
        'total': total
    }
