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
                    for t_elem in r_elem.findall(qn('w:t')):
                        if t_elem.text:
                            para_text += t_elem.text
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
    4. 整表无任何数据类型关键字
    5. 是示例/目标格式表（首行就是输出Excel的列名）
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

    # 检查整表是否含数据类型关键字
    all_upper = all_text.upper()
    has_data_type = any(kw.upper() in all_upper for kw in DATA_TYPE_KEYWORDS)
    return not has_data_type


# ─── 主类 ─────────────────────────────────────────────────────────────────────

class TableDetector:
    """
    协议文档表格检测器（python-docx 版本）。
    完整替换 docx2python，精确处理水平/垂直合并单元格。
    """

    def __init__(self, config=None):
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
        """解析单个表格"""
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

        # 强制跳过
        if force_skip:
            return base

        # ── 判断是否为干扰/无效表格 ──────────────────────────────────────────
        if _is_noise_table(grid, preceding_para):
            return base

        # ── 获取行0去重内容 ─────────────────────────────────────────────────
        row0_unique = _dedup_row(grid[0])
        row0_text = ' '.join(row0_unique)

        # ── 端口分配表识别（含信源系统码+信宿系统码） ────────────────────────
        if '信源系统码' in row0_text and '信宿系统码' in row0_text:
            return self._parse_port_allocation(grid, t_idx, preceding_para)

        # ── 消息ID表识别（含消息ID+信息内容，≤6列） ──────────────────────────
        if '消息ID' in row0_text and '信息内容' in row0_text:
            unique_cols, _ = _dedup_headers(grid[0])
            if len(unique_cols) <= 7:
                return self._parse_message_id_table(grid, t_idx, preceding_para)

        # ── bit位定义表识别（含位号+状态参数） ────────────────────────────────
        if ('位号' in row0_text or '位号' in ' '.join(_dedup_row(grid[1])) if len(grid) > 1 else False) \
                and '状态参数' in row0_text:
            return self._parse_bit_def_table(grid, t_idx, preceding_para)
        # 也匹配只有"位号"列的情况
        if '位号' in row0_text and any(kw in row0_text for kw in ['状态参数', '取值说明']):
            return self._parse_bit_def_table(grid, t_idx, preceding_para)

        # ── 字段定义表（A/B/C三种类型） ────────────────────────────────────────
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
        headers, kept_indices = _dedup_headers(grid[0])
        data_rows = self._extract_data_rows(grid, headers, kept_indices, start_row=1)
        return {
            'index': t_idx,
            'msg_name': '消息ID表',
            'headers': headers,
            'data_rows': data_rows,
            'meta': {},
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
        has_info_name_row = any(kw in row0_text for kw in ['信息名称', '通信帧名称'])

        header_row_idx = -1
        msg_name = ''
        meta = {}

        if has_info_name_row:
            # 类型A / 聚合式：行0 是信息名称行
            msg_name = _extract_msg_name_from_info_row(row0_unique)

            # 从行1开始找真正的列名行（含数据类型/内容等关键字）
            for r_idx in range(1, min(8, n_rows)):
                ru = _dedup_row(grid[r_idx])
                rt = ' '.join(ru)
                has_type = any(kw in rt for kw in ['数据类型', '类型', '数据格式', '字节', '字节数', '长度'])
                has_content = any(kw in rt for kw in ['内容', '参数', '信号名称', '字段', '数据含义', '名称'])
                has_seq = '序号' in rt
                if has_type or (has_content and has_seq) or (has_content and len(ru) >= 3):
                    header_row_idx = r_idx
                    break

            # 聚合式：收集元数据区（行1到表头行之间）
            if header_row_idx >= 2:
                for r_idx in range(1, header_row_idx):
                    row_text = ' '.join(_dedup_row(grid[r_idx]))
                    if any(kw in row_text for kw in ['BCRT', 'SA', '模式码', '→', 'BC']):
                        meta.update(_parse_aggregate_meta(row_text))
                    # 提取信源信宿（IP地址格式）
                    if '信源、信宿' in row_text or '信源、信目' in row_text:
                        for cell in _dedup_row(grid[r_idx]):
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
        过滤空行、注释行。
        """
        data_rows = []
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

            data_rows.append(row_dict)

        return data_rows


# ─── DocumentParser ──────────────────────────────────────────────────────────

class DocumentParser:
    def __init__(self, config=None):
        self.detector = TableDetector(config)
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

    def parse(self, path: str) -> Dict:
        raw_tables = self.detector.extract_tables_from_docx(path)
        linked_tables = self.linker.link_tables(raw_tables)
        return {'tables': linked_tables, 'tables_count': len(linked_tables)}
