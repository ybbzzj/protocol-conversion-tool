# -*- coding: utf-8 -*-
import re
import logging
from typing import List, Dict, Any
from docx2python import docx2python

logger = logging.getLogger(__name__)


class TableDetector:
    def __init__(self, config=None):
        # 表头识别关键字（扩展）
        self.keywords = ['序号', '参数', '内容', '数据类型', '类型', '长度', '单位', '备注', '值域',
                        '信源', '信宿', '信息内容', '消息ID', '接口名称', '周期', '数据处理方法']
        # 噪声行标记（精简，避免误过滤）
        self.noise_markers = ['参见附录']
        # 内容字段候选名（用于判断数据行有效性）
        self.content_fields = ['参数', '内容', '信号名称', '信息内容', '接口名称', '飞行计时']
        # 新的更精确的字段分类
        self.header_categories = {
            'sequence': ['序号'],  # 序号类
            'content': ['参数', '内容', '信号名称', '信息内容'],  # 内容类
            'type': ['数据类型', '类型', '类型（bit）', '转换类型'],  # 类型类
            'unit': ['单位'],  # 单位类
            'remark': ['备注', '值域'],  # 备注类
            'meta': ['信源', '信宿', '信息内容', '消息ID', '接口名称']  # 消息元数据类（应被排除）
        }

    def extract_tables_from_docx(self, file_path: str) -> List[Dict]:
        extracted_tables = []
        try:
            with docx2python(file_path) as doc:
                # doc.body 包含所有表格，结构为：Tables -> Rows -> Cells -> Paragraphs
                
                # 获取全文本用于备选标题回溯
                full_text_paragraphs = [p.strip() for p in doc.text.split('\n') if p.strip()]

                for table_idx, table in enumerate(doc.body):
                    if not table or len(table) < 2:
                        continue
                    
                    # 预处理表格：合并单元格内的段落并去除空白
                    # docx2python 会自动填充合并单元格的内容
                    grid = []
                    for row in table:
                        grid.append([" ".join(cell).strip() for cell in row])
                    
                    # 1. 定位表头
                    header_row_idx = -1
                    max_score = 0
                    for r_idx, row in enumerate(grid[:15]):
                        matches = sum(1 for cell in row if any(k in cell for k in self.keywords))
                        # 评分机制：至少匹配2个关键字
                        score = matches / 4.0 if matches <= 4 else 1.0
                        if matches >= 2 and score > max_score:
                            max_score, header_row_idx = score, r_idx
                    
                    if header_row_idx != -1:
                        headers = grid[header_row_idx]
                        msg_name = ""
                        meta = {}
                        
                        # 2. 提取元数据（表头之上的行）
                        # 利用 docx2python 自动填充特性提取 Key-Value 对
                        for r_idx in range(header_row_idx):
                            row = grid[r_idx]
                            unique_cells = []
                            if row:
                                unique_cells.append(row[0])
                                for i in range(1, len(row)):
                                    if row[i] != row[i-1]:
                                        unique_cells.append(row[i])
                            
                            # A. 尝试在单元格之间寻找 Key-Value (例如: [名称][PD指令])
                            for i in range(len(unique_cells) - 1):
                                k, v = unique_cells[i], unique_cells[i+1]
                                if any(kw in k for kw in ['信息名称', '名称', '协议名称']):
                                    if not msg_name and v and v not in ['—', '-']: msg_name = v
                                elif any(kw in k for kw in ['信息标识', '标识', '消息ID']):
                                    if v and v not in ['—', '-']: meta['信息标识'] = v
                                elif any(kw in k for kw in ['上级']):
                                    if v and v not in ['—', '-']: meta['上级'] = v
                            
                            # B. 尝试在单个单元格内寻找 (例如: [名称：PD指令])
                            if not msg_name:
                                for cell in unique_cells:
                                    if any(kw in cell for kw in ['信息名称', '名称', '协议名称']):
                                        parts = re.split(r'[：:\s]+', cell)
                                        if len(parts) > 1 and parts[-1] not in ['—', '-']:
                                            msg_name = parts[-1].strip()
                                            break
                        
                        # 3. 备选方案：如果表格内没找到标题，向文档段落回溯
                        if not msg_name:
                            for p_text in reversed(full_text_paragraphs[:200]):
                                if any(k in p_text for k in ['信息名称', '名称', '协议名称']):
                                    res = re.split(r'[：:\s]+', p_text)
                                    if len(res) > 1:
                                        msg_name = res[-1].strip()
                                        break
                        
                        # 清洗标题标签
                        msg_name = re.sub(r'^(信息|名称|标识|信号|消息|—)+', '', msg_name).strip()
                        
                        # 4. 提取数据行
                        data_rows = []
                        # 处理表头重复（合并单元格）：保留每个原始位置的表头，但为重复项添加索引
                        unique_headers = []
                        header_counts = {}  # 记录每个表头出现次数
                        for h in headers:
                            clean_h = re.sub(r'<[^>]+>', '', h).strip()  # 移除HTML标签
                            if not clean_h:
                                clean_h = f"column_{len(unique_headers)}"
                            
                            # 如果表头已存在且不是空列，添加索引后缀
                            if clean_h in header_counts and clean_h != f"column_{len(unique_headers)}":
                                header_counts[clean_h] += 1
                                clean_h = f"{clean_h}_{header_counts[clean_h]}"
                            else:
                                header_counts[clean_h] = 1
                            
                            unique_headers.append(clean_h)
                        
                        # --- 新增：更精确的表格有效性验证 ---
                        # 检查表头是否包含数据内容所需的核心类别
                        seq_found = any(any(kw in h for kw in self.header_categories['sequence']) for h in unique_headers)
                        content_found = any(any(kw in h for kw in self.header_categories['content']) for h in unique_headers)
                        type_found = any(any(kw in h for kw in self.header_categories['type']) for h in unique_headers)
                        
                        # 必须同时包含 内容类 和 类型类 字段，序号是可选的但更好
                        is_valid_data_table = content_found and type_found
                        
                        # 如果不是有效的数据表，则跳过
                        if not is_valid_data_table:
                            continue
                        
                        for r_idx in range(header_row_idx + 1, len(grid)):
                            row = grid[r_idx]
                            if len(row) < len(headers) // 2: continue
                            
                            row_data = {}
                            # 使用处理过的表头来创建行数据
                            for c_idx, clean_h in enumerate(unique_headers):
                                cell_val = row[c_idx] if c_idx < len(row) else ""
                                # 清理HTML标签
                                cell_val = re.sub(r'<[^>]+>', '', cell_val).strip()
                                row_data[clean_h] = cell_val
                            
                            # 过滤空行和噪声
                            row_all_text = "".join(row_data.values())
                            if not row_all_text.strip(): continue
                            
                            is_noise = any(m in row_all_text for m in self.noise_markers)
                            if is_noise: continue
                            
                            # 改进的有效性判断：检查是否有任何内容字段有值，或者至少有3个非空字段
                            content = None
                            for field in self.content_fields:
                                if field in row_data and row_data[field]:
                                    content = row_data[field]
                                    break
                            
                            # 检查是否有任何非空内容字段或至少3个非特殊字符字段
                            non_special_count = sum(1 for v in row_data.values() if v and v not in ['—', '-', ''])
                            
                            if content or non_special_count >= 3:
                                data_rows.append(row_data)
                        
                        if data_rows:
                            extracted_tables.append({
                                'index': table_idx,
                                'msg_name': msg_name,
                                'meta': meta,
                                'data_rows': data_rows,
                                'headers': unique_headers  # 使用处理后的表头
                            })
        except Exception as e:
            logger.error(f"Error extracting tables from {file_path}: {str(e)}")
            
        return extracted_tables

class DocumentParser:
    def __init__(self, config=None):
        self.detector = TableDetector()
    def parse(self, path):
        res = self.detector.extract_tables_from_docx(path)
        return {'tables': res, 'tables_count': len(res)}
