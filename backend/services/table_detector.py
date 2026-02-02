# -*- coding: utf-8 -*-
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from docx import Document

logger = logging.getLogger(__name__)

class TableDetector:
    def __init__(self, config=None):
        self.keywords = ['序号', '参数', '内容', '数据类型', '类型', '长度', '单位', '备注', '值域']

    def extract_tables_from_docx(self, file_path: str) -> List[Dict]:
        doc = Document(file_path)
        tables = []
        for idx, table in enumerate(doc.tables):
            # --- 核心：虚拟网格逻辑 (解决合并单元格) ---
            n_rows = len(table.rows)
            n_cols = len(table.columns)
            grid = [["" for _ in range(n_cols)] for _ in range(n_rows)]
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    grid[r_idx][c_idx] = cell.text.strip()
            
            # --- 表头识别 (评分制) ---
            best_row, max_score = -1, 0.0
            for i, row in enumerate(grid[:10]):
                matches = sum(1 for cell in row if any(k in cell for k in self.keywords))
                score = matches / 4.0 if matches <= 4 else 1.0
                if score > max_score:
                    max_score, best_row = score, i
            
            if max_score >= 0.4:
                headers = grid[best_row]
                # 提取标题 (向上查找包含 0x 或名称的行)
                msg_name = ""
                for i in range(best_row):
                    row_text = "".join(grid[i])
                    if '0x' in row_text or '名称' in row_text:
                        msg_name = row_text.split('：')[-1].split(':')[-1].strip()
                
                # 提取数据
                data_rows = []
                for r_idx in range(best_row + 1, n_rows):
                    row_data = {headers[c]: grid[r_idx][c] for c in range(min(len(headers), n_cols))}
                    if any(row_data.values()): # 过滤全空行
                        data_rows.append(row_data)
                
                tables.append({
                    'index': idx, 'msg_name': msg_name, 'headers': headers,
                    'data_rows': data_rows, 'table_type': 'data_table'
                })
        return tables

class DocumentParser:
    def __init__(self, config=None):
        self.detector = TableDetector()
    def parse(self, path):
        res = self.detector.extract_tables_from_docx(path)
        return {'tables': res, 'tables_count': len(res)}
