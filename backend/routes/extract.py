# -*- coding: utf-8 -*-
from flask import Blueprint, request, send_file
import os
import uuid
import json
import copy
import re
from datetime import datetime
from typing import Dict, List
from backend.utils import success_response, error_response
from backend.config import Config
from backend.services.table_detector import DocumentParser
from backend.services.table_linker import TableLinker
from backend.services.excel_exporter import ExcelExporter
from backend.services.data_cleaner import DataProcessor
from backend.services.field_matcher import EnhancedFieldMatcher as FieldMatcher

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
    
    # 加载用户选择的期望字段
    expected_fields = _load_expected_fields(field_ids, field_names)
    
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
        'expected_fields': expected_fields,  # 期望字段
        'mapping_quality': None  # 映射质量评分
    }
    
    try:
        # 保存文件
        file.save(upload_path)
        tasks_status[task_id]['progress'] = 10

        parse_path = upload_path
        if file_ext == '.doc':
            parse_path = _convert_doc_to_docx(upload_path)
        
        # 执行提取
        parser = DocumentParser()
        result = parser.parse(parse_path)
        tasks_status[task_id]['progress'] = 50
        
        # 表格关联：注入元数据、过滤辅助表、附加bit子行
        linker = TableLinker()
        linked_tables = linker.link_tables(result['tables'])
        
        processor = DataProcessor()
        matcher = FieldMatcher()
        
        # 使用原始表格数据而不是处理后的数据
        # 保存原始提取的表格数据用于预览
        tasks_status[task_id]['raw_tables'] = result['tables']
        
        # 保存处理后的表格数据用于导出
        processed_tables = []
        table_count = len(linked_tables)
        tasks_status[task_id]['table_count'] = table_count
        
        # 记录第一个表的名称作为主表名
        if linked_tables:
            tasks_status[task_id]['msg_name'] = linked_tables[0].get('msg_name', '')
            tasks_status[task_id]['table_count'] = table_count
        
        for idx, table in enumerate(linked_tables):
            # 只保留 field_def 类型的表格（辅助表已由 table_linker 过滤掉）
            table_type = table.get('table_type', '')
            if table_type not in ('field_def', '', None):
                # 辅助表（端口分配/消息ID/bit定义）不输出到 Excel
                table_count -= 1
                continue

            table_rows = []
            for row in table['data_rows']:
                # 过滤掉只有名称/内容但没有其他数据的无效行
                # （如"聚合式的信息流表征示意"、"发起时机"等元数据行）
                if not row.get('_is_bit_row') and not processor.is_valid_data_row(row):
                    continue
                
                # bit 子行直接透传，不做 field 匹配
                if row.get('_is_bit_row'):
                    table_rows.append(row)
                    continue

                proc_res = processor.process_row(row)
                matched_row = {}
                for field, value in proc_res['cleaned'].items():
                    match_res = matcher.match_field(field)
                    # 兼容字典和对象格式
                    target = match_res.get('target') if isinstance(match_res, dict) else (match_res.target if hasattr(match_res, 'target') else field)
                    target = target if target else field
                    matched_row[target] = value

                # 保留格式化结果（值域、转换公式）
                for fkey, fval in proc_res.get('formatted', {}).items():
                    matched_row[f'_fmt_{fkey}'] = fval

                # 位数对齐
                if '位数' in proc_res['converted']:
                    matched_row['类型（bit）'] = proc_res['converted']['位数']

                table_rows.append(matched_row)

            # 构建表格数据，包含元数据（meta）及元数据来源（meta_sources）
            table_data = {
                'msg_name': table['msg_name'],
                'data_rows': table_rows,
                'meta': table.get('meta', {}),
                'table_type': table_type,
                'meta_sources': table.get('meta_sources', {}),
            }
            processed_tables.append(table_data)
            
            # 更新进度
            progress = 50 + int((idx + 1) / table_count * 30) if table_count > 0 else 80
            tasks_status[task_id]['progress'] = progress
            
        # 导出
        output_dir = os.path.join('backend', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        exporter = ExcelExporter(output_dir)
        output_file = exporter.export_with_template(processed_tables, task_id)
        tasks_status[task_id]['progress'] = 90
        
        # 计算映射质量
        extracted_field_names = []
        for table in processed_tables:
            # 表级元数据（如消息ID）也参与映射质量统计
            for mk, mv in (table.get('meta') or {}).items():
                if mv and str(mv).strip() not in ('—', '-', ''):
                    extracted_field_names.append(mk)
            for row in table['data_rows']:
                extracted_field_names.extend(row.keys())
        
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
            'mapping_quality': mapping_quality,
            'processed_tables': processed_tables
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

        remove_crc = _parse_bool(request.args.get('remove_crc', 'false'))

        output_path = status.get('output_path')
        if not output_path or not os.path.exists(output_path):
            return error_response(40401, "文件已过期或被删除")

        generated_temp = None
        if remove_crc:
            processed_tables = status.get('processed_tables') or []
            if processed_tables:
                output_dir = os.path.join('backend', 'outputs')
                os.makedirs(output_dir, exist_ok=True)
                exporter = ExcelExporter(output_dir)
                controlled_tables = _apply_output_controls(processed_tables, remove_crc=True)
                generated_temp = exporter.export_with_template(controlled_tables, f"{task_id}_crc_filtered")
                if generated_temp and os.path.exists(generated_temp):
                    output_path = generated_temp
        
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
        
        # 文件传输完成后只删除临时文件；主结果保留，支持重复下载。
        try:
            if generated_temp and os.path.exists(generated_temp):
                os.remove(generated_temp)
                print(f"[下载完成] 已删除临时文件: {generated_temp}")
        except Exception as e:
            print(f"[警告] 删除文件失败: {e}")
        
        return response
    except Exception as e:
        return error_response(50001, f"下载失败: {str(e)}")


def _parse_bool(v: str) -> bool:
    return str(v).strip().lower() in ('1', 'true', 'yes', 'on')


def _convert_doc_to_docx(doc_path: str) -> str:
    """
    将旧版 .doc 转为 .docx 后再交给 python-docx 解析。
    依赖 Windows + Microsoft Word + pywin32；不满足时明确报错，避免导出空结果。
    """
    if not doc_path.lower().endswith('.doc'):
        return doc_path

    try:
        import win32com.client
    except Exception as e:
        raise RuntimeError("当前环境不支持 .doc 自动转换，请先将文件另存为 .docx 后再提取") from e

    abs_doc_path = os.path.abspath(doc_path)
    docx_path = abs_doc_path + 'x'
    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(abs_doc_path)
        doc.SaveAs(docx_path, FileFormat=12)
        return docx_path
    except Exception as e:
        raise RuntimeError(f".doc 转 .docx 失败，请先手动另存为 .docx 后再提取：{e}") from e
    finally:
        try:
            if doc is not None:
                doc.Close(False)
        except Exception:
            pass
        try:
            if word is not None:
                word.Quit()
        except Exception:
            pass


def _row_has_effective_data(row: Dict) -> bool:
    if not isinstance(row, dict):
        return False
    for k, v in row.items():
        if str(k).startswith('_'):
            continue
        txt = str(v).strip() if v is not None else ''
        if txt and txt not in ('—', '-', ''):
            return True
    return False


def _is_crc_row(row: Dict) -> bool:
    if not isinstance(row, dict):
        return False
    for k, v in row.items():
        if str(k).startswith('_') or v is None:
            continue
        txt = str(v)
        if re.search(r'CRC\s*校验', txt, re.IGNORECASE):
            return True
    return False


def _apply_output_controls(processed_tables: List[Dict], remove_crc: bool = False) -> List[Dict]:
    """
    对提取后的结果进行可选清洗（下载阶段执行，不影响提取主流程）
    目前支持：
    - 删除 CRC 校验字行：当行内容含“CRC校验”字样，且下一行无有效数据（或不存在）时删除
    """
    tables = copy.deepcopy(processed_tables or [])
    if not remove_crc:
        return tables

    for table in tables:
        rows = table.get('data_rows') or []
        if not rows:
            continue
        kept = []
        n = len(rows)
        for i, row in enumerate(rows):
            if _is_crc_row(row):
                next_row = rows[i + 1] if i + 1 < n else None
                if next_row is None or not _row_has_effective_data(next_row):
                    continue
            kept.append(row)
        table['data_rows'] = kept
    return tables


def _load_expected_fields(field_ids, field_names=None):
    """
    根据用户选择的字段ID加载期望字段名称
    """
    try:
        # 前端字段配置目前存储在浏览器本地，打包后这些 ID 不一定存在于后端配置文件。
        # 因此前端会同时提交字段名称，后端优先使用名称，避免期望字段为空。
        expected_names = []
        for name in (field_names or []):
            name = str(name).strip()
            if name and name not in expected_names:
                expected_names.append(name)
        if expected_names:
            return expected_names

        # 从配置文件加载协议字段
        config_path = Config.PROTOCOL_FIELDS_PATH
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                protocol_fields = json.load(f)
                
                # 根据ID查找字段名称
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
    expected_set = {_quality_field_key(f) for f in expected_fields if str(f).strip()}
    best_by_expected = {}
    
    # 对每个提取字段做匹配，并按用户期望字段统计覆盖情况。
    for ext_field in extracted_fields:
        match_result = matcher.match_field(ext_field)
        if not isinstance(match_result, dict):
            continue
        target = _quality_field_key(match_result.get('target'))
        if target not in expected_set:
            continue
        old = best_by_expected.get(target)
        if old is None or match_result.get('confidence', 0) > old.get('confidence', 0):
            best_by_expected[target] = match_result

    mapping_results = list(best_by_expected.values())
    
    # 统计匹配结果
    exact_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'exact')
    semantic_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'semantic')
    alias_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'alias')
    fuzzy_only_count = sum(1 for r in mapping_results if isinstance(r, dict) and r.get('match_type') == 'fuzzy')
    # 保持兼容：历史字段 fuzzy_count 仍返回“广义模糊”数量
    fuzzy_count = fuzzy_only_count + semantic_count + alias_count
    total = len(expected_set)
    unmatched_count = max(total - len(best_by_expected), 0)
    
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


def _quality_field_key(field) -> str:
    text = str(field or '').strip()
    if text.upper() == 'ID' or text in ('消息ID', '消息标识', '信息标识'):
        return '消息ID'
    return text
