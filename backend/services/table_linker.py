# -*- coding: utf-8 -*-
"""
表格关联服务 - 重构版

核心改进：
1. 新增 _build_port_dict：全局扫描端口分配表，建立 消息名→{信源系统码...} 字典
2. 新增 _build_msgid_dict：全局扫描消息ID表，建立 消息名→消息ID 字典
3. 新增 _build_bit_def_map：收集所有 bit 位定义表，供字段关联使用
4. 改进 link_tables：字段定义表直接查全局字典注入 meta，不再依赖邻近关系
5. 新增 bit 位关联：当字段备注含"见表B.X"或类型含"见表"时，自动附加 bit_def 行
"""

from typing import List, Dict, Any, Optional
import re


def _normalize_msg_name(name: str) -> str:
    """标准化消息名称，用于字典查找（去除首尾空格，统一全角/半角）"""
    if not name:
        return ''
    return name.strip()


def _find_col_value(row: Dict, candidates: List[str]) -> str:
    """在 row 中按候选列名列表查找第一个有值的字段"""
    for key in row:
        for candidate in candidates:
            if candidate in key or key in candidate:
                val = row[key]
                if val and val not in ('—', '-', ''):
                    return str(val).strip()
    return ''


def _parse_bit_range(bit_str: str) -> int:
    """
    解析 bit 范围字符串，计算位数。
    'D7' → 1, 'D6~D3' → 4, 'D2~D1' → 2, 'D0' → 1
    也支持 bit7, bit6:5 格式
    """
    if not bit_str:
        return 1
    s = bit_str.strip().upper()
    # 单个 bit：D7 / bit7 / D0
    m = re.match(r'^[DBIT]+(\d+)$', s)
    if m:
        return 1
    # 范围：D6~D3 / D6-D3 / D2:D1 / bit6:5
    m = re.match(r'^[DBIT]*(\d+)[~:\-][DBIT]*(\d+)$', s)
    if m:
        high = int(m.group(1))
        low = int(m.group(2))
        return abs(high - low) + 1
    return 1


class TableLinker:
    def __init__(self):
        # 保留旧接口的名称映射（兼容）
        self.name_mappings = {
            'PD控制指令': ['PD控制指令', 'PD指令', 'PD控制器'],
            'PD器状态': ['PD器状态', 'PD状态', 'PD设备状态']
        }
        self.table_type_keywords = {
            'port_allocation': ['端口分配表', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'],
            'message_id': ['消息ID编码表', '消息ID', '消息标识'],
            'protocol_param': ['参数', '数据类型', '数据长度', '值域', '单位', '备注']
        }

    # ── 全局字典构建 ──────────────────────────────────────────────────────────

    def _build_port_dict(self, tables: List[Dict]) -> Dict[str, Dict]:
        """
        扫描所有端口分配表，建立：
        消息名 → {信源系统码, 信源机器码, 信宿系统码, 信宿机器码}
        """
        port_dict = {}
        for table in tables:
            if table.get('table_type') != 'port_allocation':
                # 兼容旧格式：通过表头特征识别
                headers = table.get('headers', [])
                headers_text = ' '.join(headers)
                if not ('信源系统码' in headers_text and '信宿系统码' in headers_text):
                    continue

            headers = table.get('headers', [])
            data_rows = table.get('data_rows', [])

            # 找列索引
            col_content = col_src_sys = col_src_mc = col_dst_sys = col_dst_mc = None
            for idx, h in enumerate(headers):
                if '信息内容' in h:
                    col_content = idx
                elif '信源系统码' in h:
                    col_src_sys = idx
                elif '信源机器码' in h:
                    col_src_mc = idx
                elif '信宿系统码' in h:
                    col_dst_sys = idx
                elif '信宿机器码' in h:
                    col_dst_mc = idx

            if col_content is None:
                continue

            for row in data_rows:
                vals = list(row.values())
                if col_content >= len(vals):
                    continue
                name = str(vals[col_content]).strip()
                if not name or name in ('—', '-'):
                    continue

                entry = {}
                if col_src_sys is not None and col_src_sys < len(vals):
                    v = str(vals[col_src_sys]).strip()
                    if v and v not in ('—', '-'):
                        entry['信源系统码'] = v
                if col_src_mc is not None and col_src_mc < len(vals):
                    v = str(vals[col_src_mc]).strip()
                    if v and v not in ('—', '-'):
                        entry['信源机器码'] = v
                if col_dst_sys is not None and col_dst_sys < len(vals):
                    v = str(vals[col_dst_sys]).strip()
                    if v and v not in ('—', '-'):
                        entry['信宿系统码'] = v
                if col_dst_mc is not None and col_dst_mc < len(vals):
                    v = str(vals[col_dst_mc]).strip()
                    if v and v not in ('—', '-'):
                        entry['信宿机器码'] = v

                if entry:
                    port_dict[_normalize_msg_name(name)] = entry

        return port_dict

    def _build_msgid_dict(self, tables: List[Dict]) -> Dict[str, str]:
        """
        扫描所有消息ID表，建立：消息名 → 消息ID（如 '0x8000'）
        """
        msgid_dict = {}
        for table in tables:
            headers = table.get('headers', [])
            data_rows = table.get('data_rows', [])
            headers_text = ' '.join(headers)

            # 识别消息ID表：含"消息ID"且含"信息内容"
            if '消息ID' not in headers_text and '消息标识' not in headers_text:
                continue
            if '信息内容' not in headers_text:
                continue

            col_content = col_id = None
            for idx, h in enumerate(headers):
                if '信息内容' in h:
                    col_content = idx
                elif '消息ID' in h or '消息标识' in h:
                    col_id = idx

            if col_content is None or col_id is None:
                continue

            for row in data_rows:
                vals = list(row.values())
                if max(col_content, col_id) >= len(vals):
                    continue
                name = str(vals[col_content]).strip()
                msg_id = str(vals[col_id]).strip()
                if name and name not in ('—', '-') and msg_id and msg_id not in ('—', '-'):
                    msgid_dict[_normalize_msg_name(name)] = msg_id

        return msgid_dict

    def _build_bit_def_map(self, tables: List[Dict]) -> List[Dict]:
        """
        收集所有 bit 位定义表，返回列表供后续关联使用。
        每个元素：{preceding_para, index, headers, data_rows}
        """
        bit_tables = []
        for table in tables:
            if table.get('table_type') == 'bit_def':
                bit_tables.append(table)
            else:
                # 兼容旧格式：通过表头特征识别
                headers = table.get('headers', [])
                headers_text = ' '.join(headers)
                if '位号' in headers_text and '状态参数' in headers_text:
                    bit_tables.append(table)
        return bit_tables

    # ── 消息名称模糊匹配 ──────────────────────────────────────────────────────

    def _lookup_in_dict(self, msg_name: str, d: Dict) -> Optional[Any]:
        """
        在字典 d 中查找消息名：先精确匹配，再部分匹配（子串关系）。
        """
        name = _normalize_msg_name(msg_name)
        if name in d:
            return d[name]
        # 部分匹配：字典 key 包含 name，或 name 包含 key
        for key, val in d.items():
            if key and name and (key in name or name in key):
                return val
        # 模糊名称映射
        for canonical, aliases in self.name_mappings.items():
            if name in aliases:
                for alias in aliases:
                    if alias in d:
                        return d[alias]
        return None

    # ── bit位附加 ─────────────────────────────────────────────────────────────

    def _attach_bit_rows(self, field_row: Dict, bit_tables: List[Dict],
                         field_table_idx: int) -> List[Dict]:
        """
        检查某字段行是否有对应的 bit 位定义，如果有则返回 bit 子行列表。

        触发条件（满足任一）：
        1. 字段的"数据类型"列含"见表"字样（如"见表B.1某信道状态"）
        2. 字段的备注/说明列含"见表"字样
        3. 后续表格是 bit_def 类型且前置段落与字段名相关

        返回的每个 bit 子行结构：
        {'_is_bit_row': True, '子内容': 状态名, '类型（bit）': 位数, '转换类型继承': True}
        """
        bit_rows = []

        # 获取字段的数据类型和备注文本
        type_text = ''
        remark_text = ''
        for k, v in field_row.items():
            k_lower = k
            if any(kw in k_lower for kw in ['类型', '数据格式', 'TYPE']):
                type_text = str(v)
            if any(kw in k_lower for kw in ['备注', '说明', '数据来源']):
                remark_text = str(v)

        has_bit_ref = '见表' in type_text or '见表' in remark_text

        if not has_bit_ref:
            return []

        # 查找对应的 bit 定义表（优先使用紧跟在后面的 bit_def 表格）
        matched_bit_table = None
        for bt in bit_tables:
            bt_idx = bt.get('index', -1)
            bt_para = bt.get('preceding_para', '')
            # 取紧跟在字段定义表后面的 bit_def 表（索引接近且更大）
            if bt_idx > field_table_idx:
                matched_bit_table = bt
                break

        if not matched_bit_table:
            return []

        headers = matched_bit_table.get('headers', [])
        data_rows = matched_bit_table.get('data_rows', [])

        # 找位号列和状态参数列
        col_bit = col_state = None
        for idx, h in enumerate(headers):
            if '位号' in h or 'bit' in h.lower():
                col_bit = idx
            elif '状态参数' in h or '参数' in h:
                col_state = idx

        if col_bit is None or col_state is None:
            # 尝试用列名候选
            for idx, h in enumerate(headers):
                if '位' in h and col_bit is None:
                    col_bit = idx
                elif '状态' in h and col_state is None:
                    col_state = idx

        if col_bit is None:
            return []

        for row in data_rows:
            vals = list(row.values())
            bit_str = str(vals[col_bit]).strip() if col_bit < len(vals) else ''
            state_name = str(vals[col_state]).strip() if col_state is not None and col_state < len(vals) else ''

            if not bit_str or bit_str in ('—', '-'):
                continue

            bit_count = _parse_bit_range(bit_str)
            bit_rows.append({
                '_is_bit_row': True,
                '子内容': state_name,
                '类型（bit）': bit_count,
                '_bit_str': bit_str,
            })

        return bit_rows

    # ── 主入口 ────────────────────────────────────────────────────────────────

    def link_tables(self, tables: List[Dict]) -> List[Dict]:
        """
        关联表格：
        1. 构建全局端口字典、消息ID字典
        2. 收集 bit 位定义表
        3. 对每个字段定义表，注入端口/ID信息到 meta
        4. 对含"见表"字样的字段行，附加 bit 子行到 data_rows
        5. 只返回 field_def 类型的表格（辅助表不输出）
        """
        if not tables:
            return []

        # ── 构建全局字典 ──────────────────────────────────────────────────────
        port_dict = self._build_port_dict(tables)
        msgid_dict = self._build_msgid_dict(tables)
        bit_tables = self._build_bit_def_map(tables)

        # ── 处理字段定义表 ────────────────────────────────────────────────────
        linked_tables = []

        for table in tables:
            table_type = table.get('table_type', '')

            # 只处理字段定义表（field_def）
            # 兼容旧格式：通过 is_auxiliary=False 且有数据行判断
            is_field_def = (table_type == 'field_def')
            if not is_field_def and table_type not in ('', None):
                # 新格式，非字段定义表，跳过
                continue
            if not is_field_def:
                # 旧格式兼容：判断是否是协议参数表
                headers = table.get('headers', [])
                headers_text = ' '.join(headers)
                is_auxiliary = table.get('is_auxiliary', False)
                has_content = any(kw in headers_text for kw in ['参数', '内容', '信号名称', '数据含义', '字段'])
                has_type = any(kw in headers_text for kw in ['数据类型', '类型'])
                if is_auxiliary or not (has_content and has_type):
                    continue

            msg_name = table.get('msg_name', '')
            meta = dict(table.get('meta', {}))
            t_idx = table.get('index', -1)

            # ── 注入端口分配信息 ──────────────────────────────────────────────
            port_info = self._lookup_in_dict(msg_name, port_dict)
            if port_info:
                for k, v in port_info.items():
                    if k not in meta:
                        meta[k] = v

            # ── 注入消息ID ────────────────────────────────────────────────────
            msg_id = self._lookup_in_dict(msg_name, msgid_dict)
            if msg_id and 'ID' not in meta and '消息ID' not in meta and '信息标识' not in meta:
                meta['消息ID'] = msg_id

            # ── 兼容旧的精确匹配（保留原有逻辑以处理更多文档格式） ────────────
            if not port_info and not msg_id:
                for aux_table in tables:
                    aux_type = aux_table.get('table_type', '')
                    if aux_type in ('field_def', '') and not aux_table.get('is_auxiliary', False):
                        continue
                    aux_meta = self.extract_all_metadata_from_table(aux_table, msg_name)
                    if aux_meta:
                        for k, v in aux_meta.items():
                            if k not in meta:
                                meta[k] = v

            # ── 处理 bit 位子行 ────────────────────────────────────────────────
            data_rows = list(table.get('data_rows', []))
            new_data_rows = []
            for field_row in data_rows:
                new_data_rows.append(field_row)
                # 检查是否有 bit 位定义
                bit_sub_rows = self._attach_bit_rows(field_row, bit_tables, t_idx)
                if bit_sub_rows:
                    # 在字段行的子内容列标记为 False（表示"有子行但本行无子内容名"）
                    field_row['_has_bit_children'] = True
                    new_data_rows.extend(bit_sub_rows)

            result = dict(table)
            result['meta'] = meta
            result['data_rows'] = new_data_rows
            linked_tables.append(result)

        return linked_tables

    # ── 保留旧接口（兼容其他调用方） ─────────────────────────────────────────

    def find_matching_table(self, tables: List[Dict], target_type: str) -> Optional[Dict]:
        if target_type == 'message_id_table':
            for table in tables:
                headers = table.get('headers', [])
                data_rows = table.get('data_rows', [])
                has_msg_id = any('消息ID' in h or '消息标识' in h for h in headers)
                has_msg_content = any('信息内容' in h for h in headers)
                if has_msg_id and has_msg_content and len(data_rows) > 0:
                    return table
        elif target_type == 'port_allocation_table':
            for table in tables:
                headers = table.get('headers', [])
                data_rows = table.get('data_rows', [])
                has_port_fields = any(
                    keyword in str(headers)
                    for keyword in self.table_type_keywords['port_allocation']
                )
                if has_port_fields and len(data_rows) > 0:
                    return table
        return None

    def match_message_name_and_get_metadata(self, param_msg_name: str, id_table: Dict) -> Optional[Dict]:
        data_rows = id_table.get('data_rows', [])
        headers = id_table.get('headers', [])
        msg_content_col = msg_id_col = src_col = dst_col = None
        for idx, header in enumerate(headers):
            if '信息内容' in header or '消息内容' in header:
                msg_content_col = idx
            elif '消息ID' in header or '消息标识' in header:
                msg_id_col = idx
            elif '信源' in header and '信宿' not in header:
                src_col = idx
            elif '信宿' in header or '信目' in header:
                dst_col = idx
        if msg_content_col is None:
            return None
        for row in data_rows:
            row_values = list(row.values())
            if len(row_values) > msg_content_col:
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                if param_msg_name.strip() in str(content_val) or str(content_val).strip() in param_msg_name:
                    metadata = {}
                    if msg_id_col is not None and msg_id_col < len(row_values):
                        metadata['消息ID'] = str(row_values[msg_id_col])
                    if src_col is not None and src_col < len(row_values):
                        metadata['信源'] = str(row_values[src_col])
                    if dst_col is not None and dst_col < len(row_values):
                        metadata['信宿'] = str(row_values[dst_col])
                    return metadata
        return None

    def match_message_name(self, param_msg_name: str, id_table: Dict) -> Optional[str]:
        data_rows = id_table.get('data_rows', [])
        headers = id_table.get('headers', [])
        msg_content_col = msg_id_col = None
        for idx, header in enumerate(headers):
            if '信息内容' in header:
                msg_content_col = idx
            elif '消息ID' in header or '消息标识' in header:
                msg_id_col = idx
        if msg_content_col is None or msg_id_col is None:
            return None
        for row in data_rows:
            row_values = list(row.values())
            if len(row_values) > max(msg_content_col, msg_id_col):
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                id_val = row_values[msg_id_col] if msg_id_col < len(row_values) else ""
                if param_msg_name.strip() in str(content_val):
                    return str(id_val)
                if str(content_val).strip() in param_msg_name:
                    return str(id_val)
        return None

    def match_message_name_in_port_table(self, param_msg_name: str, port_table: Dict) -> Optional[Dict]:
        data_rows = port_table.get('data_rows', [])
        headers = port_table.get('headers', [])
        msg_content_col = src_sys_code_col = src_machine_code_col = None
        dst_sys_code_col = dst_machine_code_col = None
        for idx, header in enumerate(headers):
            if '信息内容' in header:
                msg_content_col = idx
            elif '信源系统码' in header:
                src_sys_code_col = idx
            elif '信源机器码' in header:
                src_machine_code_col = idx
            elif '信宿系统码' in header:
                dst_sys_code_col = idx
            elif '信宿机器码' in header:
                dst_machine_code_col = idx
        if msg_content_col is None:
            return None
        for row in data_rows:
            row_values = list(row.values())
            if len(row_values) > msg_content_col:
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                if param_msg_name.strip() in str(content_val) or str(content_val).strip() in param_msg_name:
                    metadata = {}
                    for col, key in [(src_sys_code_col, '信源系统码'), (src_machine_code_col, '信源机器码'),
                                     (dst_sys_code_col, '信宿系统码'), (dst_machine_code_col, '信宿机器码')]:
                        if col is not None and col < len(row_values):
                            metadata[key] = str(row_values[col])
                    return metadata
        return None

    def extract_all_metadata_from_table(self, auxiliary_table: Dict, target_msg_name: str) -> Optional[Dict]:
        data_rows = auxiliary_table.get('data_rows', [])
        headers = auxiliary_table.get('headers', [])
        if not headers or not data_rows:
            return None
        msg_content_col = None
        for idx, header in enumerate(headers):
            if '信息内容' in header or '消息内容' in header or '消息' in header:
                msg_content_col = idx
                break
        if msg_content_col is None:
            return None
        for row in data_rows:
            row_values = list(row.values())
            if len(row_values) > msg_content_col:
                content_val = str(row_values[msg_content_col]) if msg_content_col < len(row_values) else ""
                if target_msg_name.strip() == content_val.strip():
                    metadata = {}
                    for col_idx, header in enumerate(headers):
                        if col_idx < len(row_values):
                            val = row_values[col_idx]
                            if val and val not in ['', '-', '—', 'xx']:
                                clean_header = header.strip()
                                if clean_header and clean_header not in ['信息内容', '消息内容', '消息']:
                                    metadata[clean_header] = str(val)
                    if metadata:
                        return metadata
        return None

    def _is_related_table_name(self, name1: str, name2: str) -> bool:
        if not name1 or not name2:
            return False
        def get_base_name(name):
            return re.sub(r'[0-9。.]*$', '', name).strip()
        base1 = get_base_name(name1)
        base2 = get_base_name(name2)
        if base1 and base2:
            if base1 == base2:
                return True
            len_min = min(len(base1), len(base2))
            len_max = max(len(base1), len(base2))
            if len_min > 0 and len_min / len_max >= 0.8:
                if base1 in base2 or base2 in base1:
                    return True
        return False
