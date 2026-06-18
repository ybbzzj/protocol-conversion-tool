# -*- coding: utf-8 -*-
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from docx import Document
from docx.oxml.ns import qn

logger = logging.getLogger(__name__)

# ─── 常量定义 ────────────────────────────────────────────────────────────────

# 信息名称行中不是消息名称的固定噪声词
INFO_NAME_ROW_NOISE = {
    '信息名称', '通信帧名称', '信息标识', '上级信息名称',
    '信息流向', '—', '－', '-', '', 'xx', 'XX',
    '信源、信宿', '信源、信目', '信源', '信宿',
    '传输周期', '发起时机', '错误处理', '其他',
}

# 数据类型关键字（用于识别字段定义表）
DATA_TYPE_KEYWORDS = {
    'UINTEGER', 'UINT', 'USHORT', 'UFLOAT', 'FLOAT',
    'DOUBLE', 'CHAR', 'BYTE', 'SHORT', 'BIT',
    'UINT8', 'UINT16', 'UINT32', 'INT8', 'INT16', 'INT32',
    '字节',
}

# 干扰表格前置段落关键词
NOISE_PARA_MARKERS = ['干扰表格', '测试用', '不需要提取']

# 干扰表格表头关键词
NOISE_HEADER_KEYWORDS = ['测试指令', '是否带数据', '周期']

# 示例/目标格式表标志（首行包含这些列名，说明是示例表，跳过）
EXAMPLE_TABLE_HEADERS = {'名称', '信源系统码', '内容', '转换类型', '判读公式'}

# 内容列候选名（按优先级排列）
COL_CONTENT_CANDIDATES = ['内容', '数据含义', '字段', '参数', '信号名称', '名称']
# 数据类型列候选名
COL_TYPE_CANDIDATES = ['数据类型', '类型', '数据格式']
# 字节数列候选名
COL_BYTES_CANDIDATES = ['字节数', '字节', '数据长度（字节）', '长度']
# 值域列候选名
COL_RANGE_CANDIDATES = ['值域', '取值范围', '区间']
# 转换公式列候选名
COL_FORMULA_CANDIDATES = ['数据处理', '数据转换方法', '转换公式', '数据处理方法']
# 备注列候选名
COL_REMARK_CANDIDATES = ['备注', '说明', '数据来源']
# 单位列候选名
COL_UNIT_CANDIDATES = ['单位']
# 固定值列候选名（计算结果表中的"值"列）
COL_VALUE_CANDIDATES = ['值']


# ─── 辅助函数 ─────────────────────────────────────────────────────────────────

def _get_para_text(para_elem) -> str:
    """从段落 XML 元素中提取纯文本"""
    text = ''
    for child in para_elem:
        ctag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if ctag == 'r':
            for t in child:
                ttag = t.tag.split('}')[-1] if '}' in t.tag else t.tag
                if ttag == 't' and t.text:
                    text += t.text
    return text.strip()


def _build_grid(table) -> Tuple[List[List[str]], List[List[bool]]]:
    """
    用 python-docx 构建表格文本网格，精确处理合并单元格。

    - 水平合并（gridSpan）：同行跨列的单元格，grid 中每列都填写相同内容
    - 垂直合并（vMerge）：跨行合并，续行单元格填写起始行的内容，并标记 is_vmerge_cont=True

    返回：
        grid[r][c]         : 字符串，单元格文本（合并区域均填充实际值）
        is_vmerge_cont[r][c]: bool，True 表示该格是垂直合并的续行（非起始行）
    """
    n_rows = len(table.rows)
    # 列数用第一行的列数估算（含合并）
    try:
        n_cols = len(table.columns)
    except Exception:
        n_cols = max(len(r.cells) for r in table.rows) if n_rows else 0

    grid = [[''] * n_cols for _ in range(n_rows)]
    is_vmerge_cont = [[False] * n_cols for _ in range(n_rows)]
    # 记录每列最近一次 vMerge restart 的值（用于续行填充）
    vmerge_values = [''] * n_cols

    for r_idx, row in enumerate(table.rows):
        col_cursor = 0
        # 直接遍历行的 XML w:tc 元素，避免 python-docx row.cells 自动扩展合并格导致重复
        tr = row._tr
        for tc in tr.findall(qn('w:tc')):
            # 跳过已被水平合并填充的列（前一个单元格的 gridSpan 填充过）
            while col_cursor < n_cols and grid[r_idx][col_cursor] != '':
                col_cursor += 1
            if col_cursor >= n_cols:
                break

            tcpr = tc.find(qn('w:tcPr'))

            # ── 水平合并（gridSpan） ──
            gridspan = 1
            if tcpr is not None:
                gs_elem = tcpr.find(qn('w:gridSpan'))
                if gs_elem is not None:
                    try:
                        gridspan = int(gs_elem.get(qn('w:val'), '1'))
                    except (ValueError, TypeError):
                        gridspan = 1

            # ── 垂直合并（vMerge） ──
            vmerge_elem = tcpr.find(qn('w:vMerge')) if tcpr is not None else None
            # 提取单元格文本（遍历 w:p/w:r/w:t）
            cell_text_parts = []
            for p_elem in tc.findall(qn('w:p')):
                para_text = ''
                for r_elem in p_elem.findall(qn('w:r')):
                    # ◄ 【优化】识别上标和下标
                    is_sup = False
                    is_sub = False
                    r_pr = r_elem.find(qn('w:rPr'))
                    if r_pr is not None:
                        vert_align = r_pr.find(qn('w:vertAlign'))
                        if vert_align is not None:
                            val = vert_align.get(qn('w:val'), '')
                            if val == 'superscript': is_sup = True
                            elif val == 'subscript': is_sub = True

                    for t_elem in r_elem.findall(qn('w:t')):
                        if t_elem.text:
                            t_text = t_elem.text
                            if is_sup:
                                # 如果是上标且不是以 ^ 开头，补上 ^
                                t_text = f"^{t_text}" if not t_text.startswith('^') else t_text
                            elif is_sub:
                                # 如果是下标且不是以 _ 开头，补上 _
                                t_text = f"_{t_text}" if not t_text.startswith('_') else t_text
                            para_text += t_text
                if para_text.strip():
                    cell_text_parts.append(para_text.strip())
            cell_text = ' '.join(cell_text_parts)

            if vmerge_elem is not None:
                val = vmerge_elem.get(qn('w:val'), '')
                if val == 'restart':
                    # 垂直合并起始行：记录文本
                    vmerge_values[col_cursor] = cell_text
                    actual_text = cell_text
                else:
                    # 垂直合并续行：使用起始行文本，标记为续行
                    actual_text = vmerge_values[col_cursor]
                    for c in range(col_cursor, min(col_cursor + gridspan, n_cols)):
                        is_vmerge_cont[r_idx][c] = True
            else:
                actual_text = cell_text
                vmerge_values[col_cursor] = cell_text  # 更新该列的最新值

            # 填充水平合并的所有列
            for c in range(col_cursor, min(col_cursor + gridspan, n_cols)):
                grid[r_idx][c] = actual_text

            col_cursor += gridspan

    return grid, is_vmerge_cont


def _dedup_row(row: List[str]) -> List[str]:
    """对行进行水平合并去重：相邻相同值只保留一个"""
    result = []
    prev = None
    for cell in row:
        if cell != prev:
            result.append(cell)
            prev = cell
    return result


def _dedup_headers(header_row: List[str]) -> Tuple[List[str], List[int]]:
    """
    对表头行去重，返回 (去重后的表头列表, 对应原始列索引列表)。
    相邻相同的表头（水平合并产生）只保留第一个。
    空表头替换为 column_N。
    """
    unique_headers = []
    kept_indices = []
    prev = None
    for idx, h in enumerate(header_row):
        h_clean = h.strip()
        if h_clean != prev:
            if not h_clean:
                h_clean = f'column_{idx}'
            unique_headers.append(h_clean)
            kept_indices.append(idx)
            prev = h_clean if h_clean else None
        # 相同的相邻值跳过（水平合并重复列）
    return unique_headers, kept_indices


def _extract_msg_name_from_info_row(row_unique: List[str]) -> str:
    """
    从"信息名称行"（行0）的去重单元格列表中提取消息名称。
    过滤掉 INFO_NAME_ROW_NOISE 中所有固定噪声词，取第一个有效值。
    """
    for cell in row_unique:
        cell_clean = cell.strip()
        if cell_clean and cell_clean not in INFO_NAME_ROW_NOISE:
            if len(cell_clean) >= 2 and not cell_clean.isdigit():
                return cell_clean
    return ''


def _extract_name_from_para(para_text: str) -> str:
    """
    从前置段落文本中提取消息/表格名称。
    支持：'表XX 某状态信息'、'表B.1某信道状态'、普通文本
    """
    if not para_text:
        return ''
    text = para_text.strip()

    # 格式1：'表XX 某状态信息'（数字/字母后有空格）
    m = re.match(r'^表[A-Za-z0-9.。\s]*\s+(.+)', text)
    if m:
        name = m.group(1).strip()
        if name and len(name) >= 2:
            return name

    # 格式2：'表B.1某信道状态'（无空格，字母+数字+点后紧跟中文）
    m = re.match(r'^表[A-Za-z0-9.。]+(.+)', text)
    if m:
        name = m.group(1).strip()
        if name and len(name) >= 2:
            return name

    # 格式3：普通文本（非纯序号）
    if len(text) >= 2 and len(text) <= 60:
        if not re.match(r'^[一二三四五六七八九十百千\d\s]+$', text):
            return text

    return ''


def _parse_aggregate_meta(text: str) -> Dict:
    """
    解析聚合式消息元数据字符串。
    如 'BCRT1-SA0-模式码0x03' → {信源机器码:'BC', 信宿机器码:'1', 子地址:'0', 数据段长度:'3'}
    """
    meta = {}
    # 信源机器码 BC，信宿机器码 RT后的数字
    m = re.search(r'(BC)\s*(?:→|->)?\s*RT\s*(\w+)', text, re.IGNORECASE)
    if m:
        meta['信源机器码'] = 'BC'
        meta['信宿机器码'] = m.group(2)
    # 子地址 SA0
    m = re.search(r'SA\s*(\d+)', text, re.IGNORECASE)
    if m:
        meta['子地址'] = m.group(1)
    # 数据段长度（模式码0x03）
    m = re.search(r'模式码\s*(0x[0-9A-Fa-f]+|\d+)', text)
    if m:
        val = m.group(1)
        if val.upper().startswith('0X'):
            meta['数据段长度'] = str(int(val, 16))
        else:
            meta['数据段长度'] = val
    return meta


def _is_noise_table(grid: List[List[str]], preceding_para: str) -> bool:
    """
    判断是否为干扰/无效表格：
    1. 前置段落含干扰词
    2. 表头含干扰词（如测试指令、周期等）
    3. 是帧格式说明表（帧头/帧尾）
    4. 整表无任何数据类型关键字（特殊情况除外）
    5. 是示例/目标格式表（首行就是输出Excel的列名）
    
    【特殊情况】：以下表格即使无数据类型关键字也不应被过滤：
    - 端口分配表（含信源系统码+信宿系统码+信息内容）
    - 消息ID表（含消息ID+信息内容）
    """
    if any(marker in preceding_para for marker in NOISE_PARA_MARKERS):
        return True
    if not grid:
        return True

    row0_unique = _dedup_row(grid[0])
    row0_text = ' '.join(row0_unique)

    # 检查是否是示例/目标格式表
    row0_set = set(row0_unique)
    if EXAMPLE_TABLE_HEADERS.issubset(row0_set):
        return True

    # 检查表头含干扰词
    if any(kw in row0_text for kw in NOISE_HEADER_KEYWORDS):
        return True

    # 帧格式表
    all_text = ' '.join(cell for row in grid for cell in row)
    if '帧头' in all_text and '帧尾' in all_text:
        return True
    if '帧格式' in preceding_para:
        return True

    # ◄ 【新增】不过滤端口分配表和消息ID表（即使无数据类型关键字）
    has_port_allocation_features = ('信源系统码' in row0_text and '信宿系统码' in row0_text and '信息内容' in row0_text)
    has_message_id_features = ('消息ID' in row0_text and '信息内容' in row0_text)
    if has_port_allocation_features or has_message_id_features:
        return False

    # 检查整表是否含数据类型关键字
    all_upper = all_text.upper()
    has_data_type = any(kw.upper() in all_upper for kw in DATA_TYPE_KEYWORDS)
    return not has_data_type


def _match_target_message_name(grid: List[List[str]], preceding_para: str, target_names: set) -> bool:
    """
    检查表格是否匹配目标消息名称。
    匹配规则：
    1. 表标题（前置段落）是否包含目标名称
    2. 表格第一行（信息名称行）是否包含目标名称
    3. 表格内容中是否包含"信息名称"列，且该列值匹配目标名称
    """
    if not target_names:
        return False
    
    # 规则1：检查前置段落（表标题）
    para_name = _extract_name_from_para(preceding_para)
    if para_name and any(target in para_name for target in target_names):
        return True
    
    # 规则2：检查表格第一行（信息名称行）
    if grid and len(grid) > 0:
        row0_unique = _dedup_row(grid[0])
        msg_name = _extract_msg_name_from_info_row(row0_unique)
        if msg_name and any(target in msg_name for target in target_names):
            return True
    
    # 规则3：检查表格内容中的"信息名称"列
    if grid and len(grid) > 1:
        # 查找包含"信息名称"的列
        headers, kept_indices = _dedup_headers(grid[0])
        info_name_col_idx = None
        for idx, header in enumerate(headers):
            if '信息名称' in header or '通信帧名称' in header:
                info_name_col_idx = kept_indices[idx] if idx < len(kept_indices) else None
                break
        
        # 如果找到"信息名称"列，检查其值
        if info_name_col_idx is not None:
            for row in grid[1:]:  # 跳过表头行
                if info_name_col_idx < len(row):
                    cell_value = row[info_name_col_idx].strip()
                    if cell_value and any(target in cell_value for target in target_names):
                        return True
    
    return False


# ─── 主类 ─────────────────────────────────────────────────────────────────────

class TableDetector:
    """
    协议文档表格检测器（python-docx 版本）。
    完整替换 docx2python，精确处理水平/垂直合并单元格。
    
    修改点：
    1. 支持配置匹配：按"表格类型+字段组合+列角色"传入配置
    2. 处理顺序改为：配置匹配 → 智能识别 → 噪声过滤
    3. 支持 table_type=message_id，兼容旧格式和新格式
    4. 配置兜底：字段表命中配置后必须提取，ID表命中后用于补ID
    """

    def __init__(self, config=None, target_message_names=None):
        # 输出控制：是否丢弃 data_rows 末尾的 CRC 校验字行（默认开启，保持既有行为）
        self.remove_crc_tail = True
        # 保留 keywords 等属性以兼容外部调用
        self.keywords = ['序号', '参数', '内容', '信号名称', '信息内容', '数据类型', '类型',
                         '长度', '单位', '备注', '值域', '信源', '信宿', '消息ID']
        self.noise_markers = ['参见附录']
        self.content_fields = ['参数', '内容', '信号名称', '信息内容', '数据含义', '字段']
        self.header_categories = {
            'sequence': ['序号'],
            'content': ['参数', '内容', '信号名称', '信息内容', '数据含义', '字段'],
            'type': ['数据类型', '类型', '数据格式'],
            'unit': ['单位'],
            'remark': ['备注', '说明', '值域', '数据处理方法'],
            'meta': ['信源', '信宿', '信息内容', '消息ID', '接口名称', '周期', '发起时机', '错误处理']
        }
        # 目标消息名称列表（用于兜底提取）
        self.target_message_names = set(target_message_names) if target_message_names else set()
        
        # 配置兜底：用户传入的表格配置
        self.table_configs = self._parse_config(config)
        
        # 日志记录器
        self.log_records = []
    
    def _parse_config(self, config):
        """解析用户配置，提取表格类型和字段组合配置"""
        if not config:
            return []
        
        configs = []
        
        if isinstance(config, list):
            for item in config:
                if isinstance(item, dict):
                    configs.append(item)
        elif isinstance(config, dict):
            # 支持配置分组，不能只传平铺字段名
            groups = config.get('groups', [])
            if groups:
                for group in groups:
                    if isinstance(group, dict):
                        configs.append(group)
            else:
                configs.append(config)
        
        return configs
    
    def _match_config(self, grid, headers_text):
        """
        根据配置匹配表格类型。
        匹配规则：
        1. 检查表格类型配置（table_type）
        2. 检查字段组合（必须包含的字段）
        3. 检查列角色（id_value, message_name等）
        
        特殊规则：
        - 字段表配置（field_def）至少要求"内容/参数"和"数据类型"命中
        - 允许多出"序号"等列
        
        返回：(匹配的配置, 表格类型) 或 (None, None)
        """
        if not self.table_configs:
            return None, None
        
        for config in self.table_configs:
            table_type = config.get('table_type')
            required_fields = config.get('required_fields', [])
            column_roles = config.get('column_roles', {})
            
            if not table_type:
                continue
            
            # 字段表配置特殊规则：至少要求"内容/参数"和"数据类型"命中
            if table_type == 'field_def':
                has_content_field = False
                has_type_field = False
                
                # 检查是否有内容字段（内容/参数/信号名称等）
                content_candidates = ['内容', '参数', '信号名称', '信息内容', '数据含义', '字段']
                for candidate in content_candidates:
                    if candidate in headers_text:
                        has_content_field = True
                        break
                
                # 检查是否有数据类型字段
                type_candidates = ['数据类型', '类型', '数据格式']
                for candidate in type_candidates:
                    if candidate in headers_text:
                        has_type_field = True
                        break
                
                # 字段表必须同时包含内容字段和数据类型字段
                if not (has_content_field and has_type_field):
                    continue
            
            # 检查字段组合：必须包含所有required_fields
            has_all_required = True
            for field in required_fields:
                if field not in headers_text:
                    has_all_required = False
                    break
            
            if not has_all_required:
                continue
            
            # 检查列角色匹配
            if column_roles:
                role_matched = True
                for role, candidates in column_roles.items():
                    if isinstance(candidates, list):
                        found = any(candidate in headers_text for candidate in candidates)
                    else:
                        found = candidates in headers_text
                    if not found:
                        role_matched = False
                        break
                if not role_matched:
                    continue
            
            # 配置匹配成功
            logger.info(f"配置匹配成功: table_type={table_type}, headers_text={headers_text[:50]}...")
            return config, table_type
        
        return None, None
    
    def _log_table_status(self, t_idx, status, reason, table_type=None, msg_name=None):
        """记录表格识别状态日志"""
        self.log_records.append({
            'table_index': t_idx,
            'status': status,
            'reason': reason,
            'table_type': table_type,
            'msg_name': msg_name
        })
        logger.info(f"Table #{t_idx}: {status} - {reason} (type={table_type}, name={msg_name})")

    def extract_tables_from_docx(self, file_path: str) -> List[Dict]:
        """
        主入口：解析 docx 文件，返回结构化表格列表。
        每个表格字典包含：
            index, msg_name, headers, data_rows, meta,
            table_type ('field_def'|'port_allocation'|'message_id'|'bit_def'|'skip'),
            is_auxiliary (bool, 兼容旧接口)
        """
        extracted_tables = []
        try:
            doc = Document(file_path)
        except Exception as e:
            logger.error(f"Failed to open {file_path}: {e}")
            return []

        # 遍历 body 元素，建立段落-表格位置关系
        table_idx = 0
        last_para = ''
        noise_next = False  # 前置段落含干扰词时，标记后续表格为干扰

        for elem in doc.element.body:
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

            if tag == 'p':
                para_text = _get_para_text(elem)
                if para_text:
                    last_para = para_text
                    if any(marker in para_text for marker in NOISE_PARA_MARKERS):
                        noise_next = True
                    # 注意：不重置 noise_next，因为后续连续表格也要跳过
                    # 只有下一个非干扰段落后才重置（见下方逻辑）

            elif tag == 'tbl':
                if table_idx >= len(doc.tables):
                    table_idx += 1
                    continue

                table = doc.tables[table_idx]
                parsed = self._parse_single_table(table, table_idx, last_para, noise_next)
                extracted_tables.append(parsed)

                # 如果当前表格是干扰表，且前置段落也是干扰，保持 noise_next
                # 否则重置（只有明确标记才跳过）
                if not any(marker in last_para for marker in NOISE_PARA_MARKERS):
                    noise_next = False

                table_idx += 1

        return extracted_tables

    def _parse_single_table(self, table, t_idx: int, preceding_para: str, force_skip: bool) -> Dict:
        """
        解析单个表格
        
        修改点：处理顺序改为配置匹配 → 智能识别 → 噪声过滤
        1. 配置匹配：按"表格类型+字段组合+列角色"匹配
        2. 智能识别：端口分配表、消息ID表（兼容新旧格式）、bit位定义表
        3. 噪声过滤：最后判断是否为干扰表
        """
        base = {
            'index': t_idx,
            'msg_name': '',
            'headers': [],
            'data_rows': [],
            'meta': {},
            'table_type': 'skip',
            'is_auxiliary': False,
            'preceding_para': preceding_para,
        }

        try:
            grid, is_vmerge_cont = _build_grid(table)
        except Exception as e:
            logger.warning(f"Table #{t_idx}: grid error: {e}")
            return base

        if not grid or len(grid) < 1:
            return base

        # 获取行0去重内容
        row0_unique = _dedup_row(grid[0])
        row0_text = ' '.join(row0_unique)
        
        # ── 修改点1：配置匹配（最高优先级） ─────────────────────────────────────
        config, matched_table_type = self._match_config(grid, row0_text)
        if config and matched_table_type:
            # 配置匹配成功，强制提取
            self._log_table_status(t_idx, '配置匹配', f'命中配置: {matched_table_type}', matched_table_type)
            
            if matched_table_type == 'field_def':
                return self._parse_field_def_table(grid, is_vmerge_cont, t_idx, preceding_para)
            elif matched_table_type == 'message_id':
                return self._parse_message_id_table(grid, t_idx, preceding_para)
            elif matched_table_type == 'port_allocation':
                return self._parse_port_allocation(grid, t_idx, preceding_para)
            elif matched_table_type == 'bit_def':
                return self._parse_bit_def_table(grid, t_idx, preceding_para)
        
        # ── 修改点2：智能识别（中等优先级） ─────────────────────────────────────
        
        # 端口分配表识别（含信源系统码+信宿系统码）
        if '信源系统码' in row0_text and '信宿系统码' in row0_text:
            self._log_table_status(t_idx, '智能识别', '端口分配表', 'port_allocation')
            return self._parse_port_allocation(grid, t_idx, preceding_para)

        # 消息ID表识别（兼容新旧格式）
        # 旧格式：消息ID + 信息内容
        # 新格式：ID序号 + ID定义 + 是否有数据（ID序号为id_value，ID定义为message_name）
        has_message_id = '消息ID' in row0_text
        has_info_content = '信息内容' in row0_text
        has_id_seq = 'ID序号' in row0_text or '序号' in row0_text and 'ID' in row0_text
        has_id_def = 'ID定义' in row0_text
        
        if (has_message_id and has_info_content) or (has_id_seq and has_id_def):
            unique_cols, _ = _dedup_headers(grid[0])
            if len(unique_cols) <= 7:
                self._log_table_status(t_idx, '智能识别', '消息ID表', 'message_id')
                return self._parse_message_id_table(grid, t_idx, preceding_para)

        # bit位定义表识别（含位号+状态参数）
        if ('位号' in row0_text or '位号' in ' '.join(_dedup_row(grid[1])) if len(grid) > 1 else False) \
                and '状态参数' in row0_text:
            self._log_table_status(t_idx, '智能识别', 'bit位定义表', 'bit_def')
            return self._parse_bit_def_table(grid, t_idx, preceding_para)
        # 也匹配只有"位号"列的情况
        if '位号' in row0_text and any(kw in row0_text for kw in ['状态参数', '取值说明']):
            self._log_table_status(t_idx, '智能识别', 'bit位定义表', 'bit_def')
            return self._parse_bit_def_table(grid, t_idx, preceding_para)
        
        # ── 修改点3：噪声过滤（最低优先级） ─────────────────────────────────────
        
        # 强制跳过（除非匹配目标名称）
        if force_skip:
            if not _match_target_message_name(grid, preceding_para, self.target_message_names):
                self._log_table_status(t_idx, '过滤', '前置段落干扰词', 'skip')
                return base

        # 判断是否为干扰/无效表格
        if _is_noise_table(grid, preceding_para):
            # 检查是否匹配目标名称，如果匹配则强制提取
            if not _match_target_message_name(grid, preceding_para, self.target_message_names):
                self._log_table_status(t_idx, '过滤', '噪声表', 'skip')
                return base
            else:
                self._log_table_status(t_idx, '强制提取', '匹配目标名称，跳过噪声过滤', 'field_def')
                logger.info(f"Table #{t_idx}: 匹配目标名称，强制跳过干扰表判断")
        
        # ── 字段定义表（最后处理） ──────────────────────────────────────────────
        self._log_table_status(t_idx, '智能识别', '字段定义表', 'field_def')
        return self._parse_field_def_table(grid, is_vmerge_cont, t_idx, preceding_para)

    # ── 端口分配表 ────────────────────────────────────────────────────────────

    def _parse_port_allocation(self, grid: List[List[str]], t_idx: int, preceding_para: str) -> Dict:
        headers, kept_indices = _dedup_headers(grid[0])
        data_rows = self._extract_data_rows(grid, headers, kept_indices, start_row=1)
        return {
            'index': t_idx,
            'msg_name': '端口分配表',
            'headers': headers,
            'data_rows': data_rows,
            'meta': {},
            'table_type': 'port_allocation',
            'is_auxiliary': True,
            'preceding_para': preceding_para,
        }

    # ── 消息ID映射表 ──────────────────────────────────────────────────────────

    def _parse_message_id_table(self, grid: List[List[str]], t_idx: int, preceding_para: str) -> Dict:
        """
        解析消息ID表，兼容新旧格式：
        - 旧格式：消息ID + 信息内容
        - 新格式：ID序号 + ID定义 + 是否有数据
        
        新格式中：ID序号为 id_value，ID定义为 message_name
        """
        headers, kept_indices = _dedup_headers(grid[0])
        data_rows = self._extract_data_rows(grid, headers, kept_indices, start_row=1)
        
        # 标记列角色，便于 TableLinker 建立映射
        meta = {}
        
        # 识别列角色
        for header in headers:
            if '消息ID' in header or 'ID序号' in header:
                meta['id_column'] = header
            elif '信息内容' in header or 'ID定义' in header:
                meta['name_column'] = header
        
        return {
            'index': t_idx,
            'msg_name': '消息ID表',
            'headers': headers,
            'data_rows': data_rows,
            'meta': meta,
            'table_type': 'message_id',
            'is_auxiliary': True,
            'preceding_para': preceding_para,
        }

    # ── bit位定义表 ───────────────────────────────────────────────────────────

    def _parse_bit_def_table(self, grid: List[List[str]], t_idx: int, preceding_para: str) -> Dict:
        headers, kept_indices = _dedup_headers(grid[0])
        data_rows = self._extract_data_rows(grid, headers, kept_indices, start_row=1)
        msg_name = _extract_name_from_para(preceding_para)
        return {
            'index': t_idx,
            'msg_name': msg_name,
            'headers': headers,
            'data_rows': data_rows,
            'meta': {},
            'table_type': 'bit_def',
            'is_auxiliary': True,
            'preceding_para': preceding_para,
        }

    # ── 字段定义表（A/B/C 三种类型 + 聚合式） ─────────────────────────────────

    def _parse_field_def_table(self, grid: List[List[str]], is_vmerge_cont: List[List[bool]],
                                t_idx: int, preceding_para: str) -> Dict:
        n_rows = len(grid)
        skip_result = {
            'index': t_idx, 'msg_name': '', 'headers': [], 'data_rows': [],
            'meta': {}, 'table_type': 'skip', 'is_auxiliary': False,
            'preceding_para': preceding_para,
        }

        # ── 判断是否有"信息名称行"（行0 含 信息名称/通信帧名称） ──────────────
        row0_unique = _dedup_row(grid[0])
        row0_text = ' '.join(row0_unique)
        # 聚合式表格识别：行0含特定关键词 或 前置段落含"聚合式"
        has_info_name_row = any(kw in row0_text for kw in ['信息名称', '通信帧名称'])
        is_aggregate_table = '聚合式' in preceding_para

        header_row_idx = -1
        msg_name = ''
        meta = {}

        if has_info_name_row or is_aggregate_table:
            # 类型A / 聚合式：行0 是信息名称行 或 前置段落标记为聚合式
            if has_info_name_row:
                msg_name = _extract_msg_name_from_info_row(row0_unique)
            else:
                # 来自聚合式前置段落，消息名称从前置段落提取
                msg_name = _extract_name_from_para(preceding_para)

            # ◄ 【新增】名称优先级：优先从横向元数据结构中提取
            # 聚合式表格的元数据是横向排列的，且由于合并单元格，实际列排列为：
            # 列0=键1（如"数据项名称"），列1=键1_重复（合并），列2=值1（如"计算结果"），列3=值1_重复（合并）...
            # 或更简单地说：找第一个非空的非重复值（不是"数据项名称"等元数据键）
            if is_aggregate_table and n_rows > 0:
                row0 = grid[0]
                if row0 and len(row0) >= 2:
                    # 在行0中查找表名（通常是第一个不是元数据键的值）
                    metadata_keys = {'数据项名称', '消息名称', '表名', '通信名称', '数据流名称'}
                    for col_idx, cell_val in enumerate(row0):
                        cell_clean = cell_val.strip()
                        # 跳过元数据键和空值
                        if cell_clean and cell_clean not in metadata_keys and cell_clean not in INFO_NAME_ROW_NOISE:
                            # 检查这是否看起来像表名（不含数据类型关键字）
                            if not any(kw in cell_clean for kw in ['字节', 'UINT', 'INT', 'FLOAT', '序号', '内容']):
                                msg_name = cell_clean  # 【最高优先级】从横向元数据取表名
                                break
            
            # 备选：从表内第一列纵向元数据提取（如果上面的逻辑不适用）
            if not msg_name and is_aggregate_table and n_rows > 1:
                for check_row in range(1, min(4, n_rows)):  # 检查行1-3
                    first_col_val = grid[check_row][0].strip()  # 第一列
                    if first_col_val and first_col_val not in INFO_NAME_ROW_NOISE:
                        # 检查这是否是有效的表名（不是元数据关键词）
                        if not any(kw in first_col_val for kw in ['发起时机', '错误处理', '传输周期', '按实际操作流程', '序号', '检查结果']):
                            # 再检查这一行是否看起来像表名而不是数据行
                            row_content = ' '.join(_dedup_row(grid[check_row]))
                            if not any(kw in row_content for kw in ['字节', '字节数', 'UINT', 'INT', 'FLOAT']):
                                msg_name = first_col_val  # 【次优先级】
                                break

            # 从行1开始找真正的列名行（含数据类型/内容等关键字）
            # 对于聚合式表格，表头可能在行1-7之间的任何位置
            start_search = 1 if has_info_name_row else 0
            for r_idx in range(start_search, min(8, n_rows)):
                ru = _dedup_row(grid[r_idx])
                rt = ' '.join(ru)
                has_type = any(kw in rt for kw in ['数据类型', '类型', '数据格式', '字节', '字节数', '长度'])
                # 对于聚合式表格，需要更精确地识别内容列（排除元数据行）
                has_content = any(kw in rt for kw in ['内容', '参数', '信号名称', '字段', '数据含义', '名称'])
                # 添加聚合式特有的表头标记
                has_aggregate_marker = any(kw in rt for kw in ['计算结果', '消息类型', '消息序号']) and has_type
                has_seq = '序号' in rt
                
                # 排除元数据行（聚合式表格的元数据区特征：只有特定的关键词，没有"内容"列）
                # 元数据行特征：包含元数据关键词且行只有2-3个唯一的非空值
                is_metadata_row_pattern = False
                if has_info_name_row or is_aggregate_table:
                    non_empty_cells = [c for c in ru if c and c not in ('—', '-')]
                    metadata_keywords = {'信息名称', '信息标识', '信源、信宿', '信源、信目', '传输周期', '发起时机', '错误处理'}
                    # 如果行包含元数据关键词且无"内容"和"序号"，则是元数据行
                    has_metadata_kw = any(kw in rt for kw in metadata_keywords)
                    is_metadata_row_pattern = has_metadata_kw and not has_content and not has_seq
                    
                    # 对于聚合式表格：如果只有"计算结果"/"消息类型"等特殊列但没有"序号"或真正的"内容"列
                    # 说明这不是字段定义表的表头，而是元数据行的变体
                    if not is_metadata_row_pattern and r_idx < 3 and is_aggregate_table:
                        # 行0-2：检查是否缺少"序号"且只有特殊关键词
                        has_special_marker = any(kw in rt for kw in ['计算结果', '消息类型', '消息序号', '信源、信宿', '信源、信目'])
                        if has_special_marker and not has_seq and not (has_content and has_type):
                            # 这是元数据行，跳过
                            is_metadata_row_pattern = True
                
                if is_metadata_row_pattern:
                    continue
                
                # 判断是否是表头行
                if has_type or (has_content and has_seq) or (has_content and len(ru) >= 3) or has_aggregate_marker:
                    header_row_idx = r_idx
                    break

            # 聚合式：收集元数据区（行1到表头行之间）
            # 支持两种格式：
            # 1. 纵向：行1列0=键，后续行处理
            # 2. 横向：行0-N中，列0=键1，列1=值1，列2=键2，列3=值2...
            if has_info_name_row and header_row_idx >= 2:
                for r_idx in range(1, header_row_idx):
                    row = _dedup_row(grid[r_idx])
                    row_text = ' '.join(row)
                    
                    # ◄ 新增：横向元数据提取（键值对横向排列）
                    # 特别处理这一行，假设列0=键1，列1=值1，列2=键2，列3=值2...
                    for col_idx in range(0, len(row) - 1, 2):
                        key_cell = row[col_idx].strip()
                        val_cell = row[col_idx + 1].strip() if col_idx + 1 < len(row) else ''
                        
                        if key_cell and val_cell and key_cell not in ('—', '-', ''):
                            # 标准化元数据键
                            if key_cell in ['信源、信宿', '信源、信目']:
                                meta['信源、信宿'] = val_cell
                            elif '发起时机' in key_cell:
                                meta['发起时机'] = val_cell
                            elif '发送周期' in key_cell:
                                meta['发送周期'] = val_cell
                            elif '错误处理' in key_cell:
                                meta['错误处理'] = val_cell
                            elif '备注' in key_cell:
                                meta['备注'] = val_cell
                    
                    # ◄ 原有逻辑：处理特殊格式（BCRT、SA等）
                    if any(kw in row_text for kw in ['BCRT', 'SA', '模式码', '→', 'BC']):
                        meta.update(_parse_aggregate_meta(row_text))
                    
                    # ◄ 原有逻辑：提取信源信宿（IP地址格式）
                    if '信源、信宿' in row_text or '信源、信目' in row_text:
                        for cell in row:
                            if '→' in cell or ':' in cell:
                                meta['信源、信宿'] = cell
        else:
            # 类型B / C：行0 就是列名行
            row0_text = ' '.join(_dedup_row(grid[0]))
            has_type = any(kw in row0_text for kw in ['数据类型', '类型', '数据格式'])
            has_content = any(kw in row0_text for kw in ['内容', '参数', '信号名称', '字段', '数据含义', '名称'])
            if has_type or has_content:
                header_row_idx = 0
                # 消息名称来自前置段落标题
                msg_name = _extract_name_from_para(preceding_para)
            else:
                return skip_result

        if header_row_idx == -1:
            return skip_result

        # ── 提取列名（去重） ──────────────────────────────────────────────────
        headers, kept_indices = _dedup_headers(grid[header_row_idx])

        # ── 提取数据行 ─────────────────────────────────────────────────────────
        data_rows = self._extract_data_rows(grid, headers, kept_indices,
                                             start_row=header_row_idx + 1,
                                             is_vmerge_cont=is_vmerge_cont)

        if not data_rows:
            return skip_result

        # ── 判断是否是辅助表（端口/ID 已经提前识别，这里只标记字段定义表） ──
        is_auxiliary = False

        return {
            'index': t_idx,
            'msg_name': msg_name,
            'headers': headers,
            'data_rows': data_rows,
            'meta': meta,
            'table_type': 'field_def',
            'is_auxiliary': is_auxiliary,
            'preceding_para': preceding_para,
        }

    # ── 通用数据行提取 ─────────────────────────────────────────────────────────

    def _extract_data_rows(self, grid: List[List[str]], headers: List[str],
                           kept_indices: List[int], start_row: int,
                           is_vmerge_cont: Optional[List[List[bool]]] = None) -> List[Dict]:
        """
        从 grid 的 start_row 开始提取数据行，按 headers/kept_indices 映射列。
        过滤空行、注释行、无效元数据行（只有名称和内容但无其他数据的行）。
        """
        data_rows = []
        # 定义内容字段名称集合（这些字段用于存放数据名称或描述）
        content_field_names = {'名称', '内容', '参数', '信号名称', '字段', '数据含义', '参数名称', '数据项名称', '代号', '描述'}
        # 聚合式表格元数据行关键词（这些作为"内容"出现时，表示是元数据行而非数据行）
        # 注意：只匹配精确的元数据行标记，避免误匹配包含这些词的字段名（如"消息序号"不应被当作"序号"元数据）
        metadata_row_keywords = {
            '聚合式的信息流表征示意', '信息名称行', '信息标识行', '信源、信宿', '信源、信目',
            '传输周期', '发起时机', '错误处理', '^序号$',  # 用正则表达式匹配单独的"序号"
            '检查结果', '非周期', '按实际操作流程'
        }

        # 内容字段（数据含义/名称等）所在的 grid 列，用于判断垂直合并续行
        content_col_idx = None
        for h, col_idx in zip(headers, kept_indices):
            if h in content_field_names:
                content_col_idx = col_idx
                break

        for r_idx in range(start_row, len(grid)):
            row = grid[r_idx]

            row_dict = {}
            for h_idx, (h, col_idx) in enumerate(zip(headers, kept_indices)):
                val = row[col_idx] if col_idx < len(row) else ''
                row_dict[h] = val.strip()

            # 过滤纯空行
            row_all = ''.join(row_dict.values())
            if not row_all.strip():
                continue

            # ◄ 垂直合并续行合并：
            # 若内容字段（如“数据含义”）所在单元格是 docx 垂直合并的续行，说明本行与上一
            # 数据项属于同一个合并单元格（例如“设备状态”跨多行，而“备注”列 D1~D8 各自独立）。
            # 此时把本行中“与上一行不同的非空值”追加到上一行（换行连接），而非新增数据行。
            is_continuation = (
                is_vmerge_cont is not None
                and content_col_idx is not None
                and r_idx < len(is_vmerge_cont)
                and content_col_idx < len(is_vmerge_cont[r_idx])
                and is_vmerge_cont[r_idx][content_col_idx]
            )
            if is_continuation and data_rows:
                prev = data_rows[-1]
                for header, value in row_dict.items():
                    v = (value or '').strip()
                    if not v or v in ('—', '-'):
                        continue
                    prev_v = (prev.get(header) or '').strip()
                    if v == prev_v:
                        continue
                    prev[header] = (prev_v + '\n' + v) if prev_v else v
                continue

            # 过滤注释行
            if any(row_all.startswith(p) for p in ['注：', '注:', '说明：', '说明:']):
                continue

            # 过滤噪声（参见附录等）
            if any(m in row_all for m in self.noise_markers):
                continue

            # 至少要有1个有实际意义的字段
            non_empty = [v for v in row_dict.values() if v and v not in ('—', '-', '序号', '')]
            if not non_empty:
                continue

            # ◄ 元数据行检测（聚合式表格中的元数据区）
            # 如果行的内容字段（名称、内容等）包含元数据关键词，则过滤掉
            is_metadata_row = False
            for header, value in row_dict.items():
                if header in content_field_names and value:
                    value_str = str(value).strip()
                    # 检查该内容字段是否包含元数据关键词
                    for keyword in metadata_row_keywords:
                        if keyword.startswith('^') and keyword.endswith('$'):
                            # 正则表达式：精确匹配
                            pattern = keyword[1:-1]
                            if re.fullmatch(pattern, value_str):
                                is_metadata_row = True
                                break
                        elif keyword in value_str:
                            # 子串匹配
                            is_metadata_row = True
                            break
                if is_metadata_row:
                    break
            
            if is_metadata_row:
                continue

            # ◄ 核心过滤：如果只有名称/内容字段有值，但其他数据字段全空，则过滤掉
            # 这些通常是错误包含的元数据行，如"聚合式的信息流表征示意"
            has_non_content_data = False
            for header, value in row_dict.items():
                # 跳过内容字段（名称、内容等描述字段）
                if header in content_field_names:
                    continue
                # 检查其他字段是否有实际数据
                if value and str(value).strip() and str(value).strip() not in ('—', '-', ''):
                    has_non_content_data = True
                    break
            
            # 如果没有任何非内容字段的数据，说明这是无效行，过滤掉
            if not has_non_content_data:
                continue

            data_rows.append(row_dict)

        # ◄ 末尾 CRC 校验字过滤（可由输出控制开关关闭）：
        # 若最后一个有效数据行的内容字段包含 CRC校验字/检验字/校验码/检验码（CRC 大小写不敏感），
        # 则丢弃该行（这类校验字段通常不是协议有效数据项）。
        # 仅作用于最后一项：若 CRC 行后面仍有有效数据行，则保留（见 content 居中的情况）。
        if self.remove_crc_tail:
            crc_keywords = ('crc校验字', 'crc检验字', 'crc校验码', 'crc检验码')
            if data_rows:
                last_row = data_rows[-1]
                for header, value in last_row.items():
                    if header in content_field_names and value:
                        v = str(value).strip().lower()
                        if any(kw in v for kw in crc_keywords):
                            data_rows.pop()
                            break

        return data_rows


# ─── DocumentParser ──────────────────────────────────────────────────────────

class DocumentParser:
    def __init__(self, config=None, target_message_names=None):
        self.detector = TableDetector(config, target_message_names)
        try:
            from .table_linker import TableLinker
        except ImportError:
            try:
                from backend.services.table_linker import TableLinker
            except ImportError:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from backend.services.table_linker import TableLinker
        self.linker = TableLinker()

    def parse(self, path: str, options: Dict = None) -> Dict:
        import json
        import os

        # 应用输出控制选项
        options = options or {}
        if 'remove_crc_tail' in options:
            self.detector.remove_crc_tail = bool(options['remove_crc_tail'])

        raw_tables = self.detector.extract_tables_from_docx(path)
        linked_tables = self.linker.link_tables(raw_tables)
        
        # ◄ 【新增】输出识别结果为JSON
        self._output_recognition_results(raw_tables, linked_tables, path)
        
        return {'tables': linked_tables, 'tables_count': len(linked_tables)}
    
    def _output_recognition_results(self, raw_tables: List[Dict], linked_tables: List[Dict], doc_path: str):
        """输出表格识别结果为JSON文件（用于调试和验证）"""
        import json
        import os
        from datetime import datetime
        
        # 仅保留一份结果
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(doc_path))), 'table_recognition_results')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'latest_recognition.json')
        
        # 构建简化的输出结构
        result_data = {
            'file': os.path.basename(doc_path),
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(linked_tables),
            'tables': []
        }
        
        for idx, table in enumerate(linked_tables):
            table_info = {
                'index': table.get('index'),
                'msg_name': table.get('msg_name', ''),
                'table_type': table.get('table_type', ''),
                'is_auxiliary': table.get('is_auxiliary', False),
                'headers': table.get('headers', []),
                'data_rows_count': len(table.get('data_rows', [])),
                'meta': table.get('meta', {}),
                'data_rows': [
                    {k: (str(v)[:100] if v else '') for k, v in row.items() if not str(k).startswith('_')}
                    for row in table.get('data_rows', [])[:10]  # 仅保留前10行
                ]
            }
            result_data['tables'].append(table_info)
        
        # 写入JSON文件（覆盖旧文件）
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            print("[INFO] 表格识别结果已保存: {}".format(output_file))
        except Exception as e:
            print("[ERROR] 保存识别结果失败: {}".format(e))
