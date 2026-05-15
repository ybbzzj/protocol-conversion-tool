# -*- coding: utf-8 -*-
"""输出结果后处理工具。"""

from copy import deepcopy
from typing import Any, Dict, List, Optional


EMPTY_MARKERS = ('', '-', '—', 'N/A', 'n/a', '无')


def normalize_output_options(options: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """规范化输出控制选项，保证缺省值稳定。"""
    options = options or {}
    return {
        'remove_crc_checksum': bool(options.get('remove_crc_checksum'))
    }


def has_effective_data(row: Dict[str, Any]) -> bool:
    """判断一行是否包含有效业务数据。"""
    for key, value in row.items():
        if str(key).startswith('_'):
            continue
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in EMPTY_MARKERS:
            return True
    return False


def row_contains_text(row: Dict[str, Any], keyword: str) -> bool:
    for key, value in row.items():
        if str(key).startswith('_') or value is None:
            continue
        if keyword in str(value):
            return True
    return False


def remove_trailing_crc_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    删除末尾 CRC 校验字段。

    规则按客户描述实现：若某字段内容含“CRC校验”，且该内容下一行再无有效数据，
    则删除该行。判断基于原始行序，避免把倒数第二行的有效 CRC 描述误删。
    """
    if not rows:
        return rows

    last_effective_idx = None
    for idx, row in enumerate(rows):
        if has_effective_data(row):
            last_effective_idx = idx

    if last_effective_idx is None:
        return rows

    last_row = rows[last_effective_idx]
    if not row_contains_text(last_row, 'CRC校验'):
        return rows

    return [
        row for idx, row in enumerate(rows)
        if idx != last_effective_idx
    ]


def apply_output_controls(tables_data: List[Dict[str, Any]],
                          options: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按输出控制选项处理待导出的表格数据。"""
    normalized = normalize_output_options(options)
    processed = deepcopy(tables_data)

    if normalized.get('remove_crc_checksum'):
        for table in processed:
            table['data_rows'] = remove_trailing_crc_rows(table.get('data_rows', []))

    return processed
