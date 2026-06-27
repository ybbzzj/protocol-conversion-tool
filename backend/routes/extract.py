# -*- coding: utf-8 -*-
from flask import Blueprint, request, send_file
import os
import uuid
import json
import threading
from datetime import datetime
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
            meta = {k: v for k, v in task.items() if k not in ('raw_tables', 'processed_tables', 'linked_tables')}
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
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext == '.doc':
        return error_response(40001, "不支持 .doc 格式，请将文件另存为 .docx 后再上传")
    allowed_extensions = {'.docx', '.xlsx', '.xls', '.csv'}
    if file_ext not in allowed_extensions:
        return error_response(40001, f"不支持的文件格式，请上传 {', '.join(allowed_extensions)} 格式的文件")
    
    field_ids = request.form.getlist('field_ids')
    field_names = request.form.getlist('field_names')
    id_field_names = request.form.getlist('id_field_names')  # 用户标记的ID表头字段

    # 输出控制选项：是否删除末尾 CRC 校验字行（默认开启）
    remove_crc = request.form.get('remove_crc', 'true').lower() != 'false'

    # 获取目标消息名称（用于兜底提取）
    target_message_names = request.form.getlist('target_message_names')
    
    # 获取用户配置（用于配置匹配和兜底提取）
    table_configs = request.form.get('table_configs')
    if table_configs:
        try:
            table_configs = json.loads(table_configs)
        except json.JSONDecodeError:
            table_configs = None
    
    # 如果未传入结构化配置，则使用前端传来的字段名列表作为兜底配置
    # 同时附带用户标记的ID表头字段名
    if not table_configs and field_names:
        table_configs = {
            'fields': field_names,
            'id_field_names': id_field_names,  # 用户在配置页标记的ID表字段
        }

    # 加载用户选择的期望字段：优先使用前端直接传来的字段名
    # （前端字段 id 为本地随机生成，与后端配置 id 不一致，无法靠 id 反查名称）
    if field_names:
        expected_fields = field_names
    else:
        expected_fields = _load_expected_fields(field_ids)
    
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
        'remove_crc': remove_crc,  # 输出控制：是否删除末尾 CRC 校验字行
        'target_message_names': target_message_names,  # 目标消息名称（用于兜底提取）
        'table_configs': table_configs,  # 用户配置（用于配置匹配）
        'mapping_quality': None  # 映射质量评分
    }
    
    try:
        # 保存文件
        file.save(upload_path)
        tasks_status[task_id]['progress'] = 10
        
    except Exception as e:
        tasks_status[task_id]['status'] = 'failed'
        tasks_status[task_id]['message'] = f'文件保存失败: {e}'
        _save_tasks_to_disk()
        return error_response(40002, f"文件保存失败: {e}")

    # 提取过程放入后台线程执行，路由立即返回，使前端可通过轮询观察进度
    t = threading.Thread(target=_run_extraction, args=(task_id, upload_path, remove_crc, target_message_names, table_configs), daemon=True)
    t.start()

    return success_response({
        'task_id': task_id,
        'expected_fields': expected_fields
    })

def _dump_processed_tables(processed_tables, doc_path):
    """将字段映射后的 processed_tables 输出为 JSON（调试用）"""
    import json as _json
    import os as _os
    from datetime import datetime as _dt
    
    output_dir = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.dirname(doc_path))),
        'table_recognition_results'
    )
    if not _os.path.exists(output_dir):
        _os.makedirs(output_dir)
    
    out_file = _os.path.join(output_dir, '4_processed_tables.json')
    data = {
        'file': _os.path.basename(doc_path),
        'timestamp': _dt.now().isoformat(),
        'total_processed_tables': len(processed_tables),
        'tables': []
    }
    for table in processed_tables:
        table_info = {
            'msg_name': table.get('msg_name', ''),
            'table_type': table.get('table_type', ''),
            'meta': table.get('meta', {}),
            'data_rows_count': len(table.get('data_rows', [])),
            'data_rows': [
                {k: (str(v)[:120] if v else '') for k, v in row.items() if not str(k).startswith('_')}
                for row in table.get('data_rows', [])[:15]
            ]
        }
        data['tables'].append(table_info)
    
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 处理后表格已保存: {out_file}")
    except Exception as e:
        print(f"[ERROR] 保存处理后表格失败: {e}")


def _run_extraction(task_id, upload_path, remove_crc, target_message_names=None, table_configs=None):
    """后台线程：执行解析、关联、导出与映射质量计算，并实时更新进度。"""
    try:
        # 执行提取（传入目标消息名称和配置用于兜底提取）
        parser = DocumentParser(config=table_configs, target_message_names=target_message_names)
        result = parser.parse(upload_path, options={'remove_crc_tail': remove_crc})
        tasks_status[task_id]['progress'] = 50

        # 表格关联：注入元数据、过滤辅助表、附加bit子行
        linker = TableLinker()
        linked_tables = linker.link_tables(result['tables'])

        # 使用原始表格数据而不是处理后的数据
        # 保存原始提取的表格数据用于预览
        tasks_status[task_id]['raw_tables'] = result['tables']
        # 保存关联后的表格数据，供人工修正后重新导出使用（仅内存，不持久化）
        tasks_status[task_id]['linked_tables'] = linked_tables

        # 记录第一个表的名称作为主表名
        if linked_tables:
            tasks_status[task_id]['msg_name'] = linked_tables[0].get('msg_name', '')

        # 处理表格并导出
        processed_tables = _build_processed_tables(linked_tables)
        _dump_processed_tables(processed_tables, upload_path)
        tasks_status[task_id]['table_count'] = len(processed_tables)
        tasks_status[task_id]['progress'] = 80
        output_file = _export_processed_tables(processed_tables, task_id)
        tasks_status[task_id]['progress'] = 90

        # 计算映射质量（口径与人工映射页左侧统一）：
        # 使用与 preview 完全相同的字段源（清洗后的真实源字段）与匹配逻辑，
        # 保证“弹窗待人工处理数”与“人工页左侧待映射数”一致。
        from backend.routes.mapping import _extract_fields_and_data_from_raw_tables
        source_fields, _ = _extract_fields_and_data_from_raw_tables(result['tables'])
        expected_fields = tasks_status[task_id].get('expected_fields', [])

        print(f'[映射质量调试] 待映射源字段数: {len(source_fields)}')
        print(f'[映射质量调试] 待映射源字段: {source_fields[:10]}...')
        print(f'[映射质量调试] 期望字段数: {len(expected_fields)}')

        mapping_quality = _calculate_mapping_quality(source_fields, expected_fields)
        print(f'[映射质量调试] 计算结果: {mapping_quality}')

        tasks_status[task_id].update({
            'status': 'success',
            'progress': 100,
            'output_path': output_file,
            'mapping_quality': mapping_quality
        })

        # ✅ 保存到磁盘
        _save_tasks_to_disk()

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        tasks_status[task_id]['status'] = 'failed'
        tasks_status[task_id]['message'] = str(e)
        print(f"[提取任务 {task_id}] 错误: {error_trace}")

        # ✅ 保存到磁盘
        _save_tasks_to_disk()
    finally:
        # 清理上传的临时文件（仅失败时）
        try:
            if os.path.exists(upload_path) and tasks_status[task_id]['status'] == 'failed':
                os.remove(upload_path)
        except Exception:
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

        # 保留结果文件，允许用户多次下载（避免再次下载报 404）
        return response
    except Exception as e:
        return error_response(50001, f"下载失败: {str(e)}")


def _build_processed_tables(linked_tables, user_overrides=None):
    """
    将关联后的表格处理为可导出的结构。

    Args:
        linked_tables: TableLinker 关联后的表格列表
        user_overrides: 可选，用户手动修正映射 {原始字段: 目标字段}，优先级高于自动匹配

    Returns:
        processed_tables 列表
    """
    user_overrides = user_overrides or {}
    processor = DataProcessor()
    matcher = FieldMatcher()
    processed_tables = []

    for table in linked_tables:
        # 只保留 field_def 类型的表格（辅助表已由 table_linker 过滤掉）
        table_type = table.get('table_type', '')
        if table_type not in ('field_def', '', None):
            # 辅助表（端口分配/消息ID/bit定义）不输出到 Excel
            continue

        table_rows = []
        for row in table['data_rows']:
            # 过滤掉只有名称/内容但没有其他数据的无效行
            if not row.get('_is_bit_row') and not processor.is_valid_data_row(row):
                continue

            # bit 子行直接透传，不做 field 匹配
            if row.get('_is_bit_row'):
                table_rows.append(row)
                continue

            proc_res = processor.process_row(row)
            matched_row = {}
            override_cols = []  # 本行中由用户手动映射决定的目标列（导出时优先于启发式）
            for field, value in proc_res['cleaned'].items():
                # 用户手动修正优先
                if field in user_overrides:
                    target = user_overrides[field]
                    if target:
                        override_cols.append(target)
                else:
                    match_res = matcher.match_field(field)
                    target = match_res.get('target') if isinstance(match_res, dict) else (match_res.target if hasattr(match_res, 'target') else field)
                    target = target if target else field
                matched_row[target] = value

            # 保留格式化结果（值域、转换公式）
            for fkey, fval in proc_res.get('formatted', {}).items():
                matched_row[f'_fmt_{fkey}'] = fval

            # 位数对齐
            if '位数' in proc_res['converted']:
                matched_row['类型（bit）'] = proc_res['converted']['位数']

            # 记录用户手动映射的目标列，供导出器优先填充
            if override_cols:
                matched_row['_override_cols'] = override_cols

            table_rows.append(matched_row)

        processed_tables.append({
            'msg_name': table['msg_name'],
            'data_rows': table_rows,
            'meta': table.get('meta', {}),
            'table_type': table_type,
            'meta_sources': table.get('meta_sources', {}),
        })

    return processed_tables


def _export_processed_tables(processed_tables, task_id):
    """导出处理后的表格为 Excel 文件，返回文件路径"""
    output_dir = os.path.join('backend', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    exporter = ExcelExporter(output_dir)
    return exporter.export_with_template(processed_tables, task_id)


def regenerate_output(task_id, user_overrides):
    """
    根据用户手动修正的映射，重新生成 Excel 输出文件。

    Args:
        task_id: 任务ID
        user_overrides: {原始字段: 目标字段}

    Returns:
        (success: bool, message: str)
    """
    status = tasks_status.get(task_id)
    if not status:
        return False, "任务不存在"

    linked_tables = status.get('linked_tables')
    if not linked_tables:
        return False, "原始表格数据已过期，无法重新生成（请重新上传文档）"

    try:
        processed_tables = _build_processed_tables(linked_tables, user_overrides=user_overrides)
        output_file = _export_processed_tables(processed_tables, task_id)
        status['output_path'] = output_file
        status['table_count'] = len(processed_tables)
        status['message'] = '已根据人工修正重新生成结果'
        _save_tasks_to_disk()
        return True, output_file
    except Exception as e:
        import traceback
        print(f"[重新生成 {task_id}] 错误: {traceback.format_exc()}")
        return False, str(e)


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


def _calculate_mapping_quality(source_fields, expected_fields=None):
    """
    计算字段映射质量（口径与人工映射页左侧统一）。

    入参 source_fields 为清洗后的真实源表头（与 preview 同一来源）。
    按 match_with_context 的置信度分两档，与前端自动映射条件
    （matched 且 confidence >= 0.9）保持一致：
      - auto_count   : 置信度 >= 0.9，会被自动映射进中间栏；
      - manual_count : 其余字段（含低置信与无匹配），需在人工页左侧处理。
    保证“弹窗待人工处理数”恒等于“人工页左侧待映射数”。

    expected_fields 为用户在提取页勾选的协议字段（期望字段）。
    用于计算“期望覆盖”这一独立维度（与上面的映射质量口径分开，互不混算）：
      - expected_count : 用户勾选的协议字段数（分母）；
      - covered_count  : 这些字段中、能在提取到的源字段里找到 >=0.9 相似项的数量（分子）；
      - coverage       : covered_count / expected_count，反映“想要的字段文档提供了多少”。
    """
    matcher = FieldMatcher()
    expected_fields = expected_fields or []

    # —— 维度一：映射质量（基于提取到的源字段）——
    auto_count = 0       # 置信度 >= 0.9，自动映射
    manual_count = 0     # 需人工处理（进左侧）
    unmatched_count = 0  # 完全无匹配（manual 的子集，仅用于提示）

    for field in source_fields:
        r = matcher.match_field(field)
        target = r.get('target') if isinstance(r, dict) else None
        confidence = r.get('confidence', 0) if isinstance(r, dict) else 0

        if target and confidence >= 0.9:
            auto_count += 1
        else:
            manual_count += 1
            if not target:
                unmatched_count += 1

    total = len(source_fields)
    score = auto_count / total if total > 0 else 0
    level = 'excellent' if score > 0.9 else 'good' if score > 0.7 else 'poor'

    # —— 维度二：期望覆盖（基于用户勾选的协议字段）——
    # 对每个期望字段，若提取到的源字段中存在相似度 >=0.9 的项，则视为被覆盖。
    covered_count = 0
    for exp in expected_fields:
        if any(matcher._calculate_similarity(exp, src) >= 0.9 for src in source_fields):
            covered_count += 1
    expected_count = len(expected_fields)
    coverage = covered_count / expected_count if expected_count > 0 else 0

    return {
        'score': score,
        'level': level,
        'auto_count': auto_count,
        'manual_count': manual_count,
        'unmatched_count': unmatched_count,
        'total': total,
        'expected_count': expected_count,
        'covered_count': covered_count,
        'coverage': coverage,
    }
