# -*- coding: utf-8 -*-
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from docx2python import docx2python

logger = logging.getLogger(__name__)

@dataclass
class TableInfo:
    """提取的表格信息"""
    index: int
    headers: List[str]
    header_row: int
    data_rows: List[Dict[str, str]]
    raw_rows: List[List[str]]
    msg_name: str = ""
    parent_msg_name: str = ""
    table_type: str = "unknown"
    confidence: float = 1.0
    meta: Dict = field(default_factory=dict)

class TableDetector:
    """智能表格识别引擎 (docx2python版)"""
    HEADER_KEYWORDS = {
        'data_fields': ['序号', '参数', '内容', '数据类型', '类型', '单位', '值域', '备注', '说明', '字段', '字节', '长度', '数据长度'],
        'msg_info': ['信息名称', '消息名称', '上级信息名称', '信息标识', '0x'],
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}

    def extract_tables_from_docx(self, file_path: str) -> List[TableInfo]:
        try:
            with docx2python(file_path) as docx_content:
                all_tables = []
                table_idx = 0
                for sheet in docx_content.body:
                    for table in sheet:
                        raw_rows = []
                        for row in table:
                            clean_row = [self._clean_text(" ".join(cell)) for cell in row]
                            raw_rows.append(clean_row)
                        
                        if not raw_rows: continue
                        table_info = self._analyze_raw_table(raw_rows, table_idx)
                        if table_info and table_info.table_type != 'invalid':
                            all_tables.append(table_info)
                        table_idx += 1
                return all_tables
        except Exception as e:
            logger.error(f"提取失败: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def _analyze_raw_table(self, raw_rows: List[List[str]], index: int) -> Optional[TableInfo]:
        header_row, headers, confidence = self._detect_header(raw_rows)
        if header_row < 0: return None
        msg_name, parent_name = self._extract_message_info(raw_rows, header_row)
        data_rows = self._extract_data_rows(raw_rows, header_row, headers)
        return TableInfo(index=index, headers=headers, header_row=header_row, data_rows=data_rows, 
                         raw_rows=raw_rows, msg_name=msg_name, parent_msg_name=parent_name, 
                         table_type='data_table', confidence=confidence)

    def _detect_header(self, raw_rows: List[List[str]]) -> Tuple[int, List[str], float]:
        best_row, best_headers, max_score = -1, [], 0.0
        legacy_baseline = ["序号", "参数", "数据类型", "数据长度", "值域", "单位", "备注"]
        for i, row in enumerate(raw_rows[:10]): # 仅在前10行找表头
            matches = set()
            for cell in row:
                for kw in legacy_baseline + self.HEADER_KEYWORDS['data_fields']:
                    if kw in cell: matches.add(kw)
            score = len(matches) / 4.0 if len(matches) <= 4 else 1.0
            if score > max_score:
                max_score, best_row, best_headers = score, i, row
        return best_row, best_headers, max_score

    def _extract_message_info(self, raw_rows: List[List[str]], header_row: int) -> Tuple[str, str]:
        msg_name = ""
        for i in range(header_row):
            row_text = "".join(raw_rows[i])
            id_match = re.search(r'0x[0-9A-Fa-f]+', row_text)
            if id_match: msg_name = id_match.group(0)
            if any(k in row_text for k in ['信息名称', '消息名称']):
                msg_name = raw_rows[i][-1] # 简单假设在末尾
        return msg_name, ""

    def _extract_data_rows(self, raw_rows: List[List[str]], header_row: int, headers: List[str]) -> List[Dict]:
        data = []
        for i in range(header_row + 1, len(raw_rows)):
            row = raw_rows[i]
            if len(row) < len(headers): continue
            data.append({headers[j]: row[j] for j in range(len(headers))})
        return data

class DocumentParser:
    def __init__(self, config: Dict = None):
        self.table_detector = TableDetector(config)
    def parse(self, file_path: str) -> Dict:
        tables = self.table_detector.extract_tables_from_docx(file_path)
        return {'file_path': file_path, 'tables_count': len(tables), 'tables': [vars(t) for t in tables]}
