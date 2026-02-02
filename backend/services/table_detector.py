# -*- coding: utf-8 -*-
import re
import logging
from typing import List, Dict, Any
from docx import Document

logger = logging.getLogger(__name__)

class TableDetector:
    def __init__(self, config=None):
        self.keywords = ['序号', '参数', '内容', '数据类型', '类型', '长度', '单位', '备注', '值域']
        self.noise_markers = ['参见', '信息名称', '信号名称', '信息标识', '上级', '参见附录']

    def extract_tables_from_docx(self, file_path: str) -> List[Dict]:
        doc = Document(file_path)
        tables = []
        
        # 记录全文段落，用于标题回溯
        all_paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        for idx, table in enumerate(doc.tables):
            n_rows, n_cols = len(table.rows), len(table.columns)
            grid = [["" for _ in range(n_cols)] for _ in range(n_rows)]
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    grid[r_idx][c_idx] = cell.text.strip()
            
            # 1. 定位表头
            best_row, max_score = -1, 0.0
            for i, row in enumerate(grid[:15]):
                matches = sum(1 for cell in row if any(k in cell for k in self.keywords))
                score = matches / 4.0 if matches <= 4 else 1.0
                if score > max_score:
                    max_score, best_row = score, i
            
            if max_score >= 0.4:
                headers = grid[best_row]
                msg_name = ""
                meta = {}
                
                # 2. 巅峰版标题提取逻辑：向上回溯表格内行及文档段落
                # A. 表格内回溯
                for i in range(best_row):
                    row_text = " ".join([c for c in grid[i] if c])
                    for key in ['信源机器码', '信宿机器码', '子地址', '消息地址', '数据段长度', '信息标识', '名称']:
                        if key in row_text:
                            parts = re.split(r'[：:\s]+', row_text)
                            val = parts[-1].strip() if len(parts) > 1 else ""
                            if '名称' in key: msg_name = val
                            else: meta[key] = val
                
                # B. 文档段落回溯 (如果表格内没找到)
                if not msg_name:
                    for p_text in reversed(all_paragraphs[:100]):
                        if any(k in p_text for k in ['信息名称', '名称', '协议名称']):
                            res = re.split(r'[：:\s]+', p_text)
                            if len(res) > 1:
                                msg_name = res[-1].strip()
                                break
                
                # 清洗标题标签
                msg_name = re.sub(r'^(信息|名称|标识|信号)+', '', msg_name).strip()

                # 3. 强力过滤噪声行
                data_rows = []
                for r_idx in range(best_row + 1, n_rows):
                    row_data = {headers[c]: grid[r_idx][c] for c in range(min(len(headers), n_cols))}
                    content = row_data.get('参数', row_data.get('内容', row_data.get('信号名称', '')))
                    
                    row_all_text = "".join(row_data.values())
                    is_noise = any(m in row_all_text for m in self.noise_markers)
                    
                    if content and not is_noise and len(content) > 1:
                        data_rows.append(row_data)
                
                if data_rows:
                    tables.append({
                        'index': idx, 'msg_name': msg_name, 'meta': meta,
                        'data_rows': data_rows, 'headers': headers
                    })
        return tables

class DocumentParser:
    def __init__(self, config=None):
        self.detector = TableDetector()
    def parse(self, path):
        res = self.detector.extract_tables_from_docx(path)
        return {'tables': res, 'tables_count': len(res)}
