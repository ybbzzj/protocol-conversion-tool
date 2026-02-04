# -*- coding: utf-8 -*-
import re
import logging
from typing import List, Dict, Any
from docx2python import docx2python

logger = logging.getLogger(__name__)

# 使用相对导入处理模块间的依赖关系
try:
    from .table_linker import TableLinker
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from backend.services.table_linker import TableLinker
    except ImportError:
        # 如果仍在主进程中运行，添加路径后再导入
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from backend.services.table_linker import TableLinker


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
            # 捕获 docx2python 库的索引错误
            try:
                doc_temp = docx2python(file_path)
            except IndexError as e:
                if "list index out of range" in str(e):
                    logger.error(f"docx2python encountered index error processing {file_path}: {str(e)}")
                    logger.error("This usually happens when the document has complex formatting that docx2python can't handle")
                    return []
                else:
                    raise  # 重新抛出其他IndexError
            
            with doc_temp as doc:
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
                        # 确保行不为空
                        if row:
                            grid.append([" ".join(cell).strip() if cell else "" for cell in row])
                    
                    # 1. 定位表头
                    header_row_idx = -1
                    max_score = 0
                    # 确保grid不为空
                    if not grid:
                        continue
                    for r_idx, row in enumerate(grid[:min(15, len(grid))]):
                        # 确保行不为空
                        if not row:
                            continue
                        matches = sum(1 for cell in row if any(k in cell for k in self.keywords))
                        # 评分机制：至少匹配2个关键字
                        score = matches / 4.0 if matches <= 4 else 1.0
                        if matches >= 2 and score > max_score:
                            max_score, header_row_idx = score, r_idx
                    
                    if header_row_idx != -1 and 0 <= header_row_idx < len(grid):
                        headers = grid[header_row_idx] if 0 <= header_row_idx < len(grid) else []
                        msg_name = ""
                        meta = {}
                        
                        # 2. 提取元数据（表头之上的行）
                        # 利用 docx2python 自动填充特性提取 Key-Value 对
                        for r_idx in range(header_row_idx):
                            row = grid[r_idx]
                            unique_cells = []
                            if row and len(row) > 0:
                                unique_cells.append(row[0] if len(row) > 0 else "")
                                for i in range(1, len(row)):
                                    if i < len(row) and i-1 < len(row) and row[i] != row[i-1]:
                                        unique_cells.append(row[i])
                            
                            # A. 尝试在单元格之间寻找 Key-Value (例如: [名称][PD指令])
                            for i in range(len(unique_cells) - 1):
                                k = unique_cells[i] if i < len(unique_cells) else ""
                                v = unique_cells[i+1] if i+1 < len(unique_cells) else ""
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
                        
                        # 4. 新增：处理类似"表1 端口分配表"格式的表格标题
                        if not msg_name and grid:
                            # 检查表头上方的几行，看是否有"表X 表名"格式的标题
                            for r_idx in range(min(5, header_row_idx)):  # 检查表头上方最多5行
                                row = grid[r_idx]
                                if row:
                                    # 检查每行的第一个单元格，通常包含表格标题
                                    first_cell = row[0] if row and len(row) > 0 else ""
                                    if first_cell and '表' in first_cell and ' ' in first_cell:
                                        # 尝试匹配"表X 表名"或"表X 表名 表"格式
                                        # 更智能的分割：查找第一个空格后的所有内容，而不是只取第二部分
                                        space_pos = first_cell.find(' ')
                                        if space_pos != -1:
                                            table_name_part = first_cell[space_pos + 1:].strip()
                                            # 移除可能的"表"字
                                            if table_name_part.endswith('表'):
                                                table_name_part = table_name_part[:-1]
                                            if table_name_part:
                                                msg_name = table_name_part
                                                break
                        
                        # 5. 如果还是没有找到名称，尝试从表头中推断
                        if not msg_name:
                            # 如果表头包含特定关键词，可以根据表头内容推断表格类型
                            if any('消息ID' in h or '消息标识' in h for h in headers):
                                msg_name = '消息ID编码表'
                            elif any(keyword in str(headers) for keyword in ['接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']):
                                msg_name = '端口分配表'
                            elif content_found and type_found:
                                msg_name = '协议参数表'
                        
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
                        
                        # --- 添加：标记表格类型用于日志输出 ---
                        # 检查表头是否包含数据内容所需的核心类别
                        seq_found = any(any(kw in h for kw in self.header_categories['sequence']) for h in unique_headers)
                        content_found = any(any(kw in h for kw in self.header_categories['content']) for h in unique_headers)
                        type_found = any(any(kw in h for kw in self.header_categories['type']) for h in unique_headers)
                        
                        # 检查是否包含消息ID等相关信息（这些通常属于元数据表）
                        meta_found = any(any(kw in h for kw in self.header_categories['meta']) for h in unique_headers)
                        
                        # 检查是否为端口分配表等辅助表
                        is_port_table = any(keyword in str(unique_headers) for keyword in ['接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'])
                        
                        # 检查是否为消息ID编码表等辅助表
                        is_meta_table = any('消息ID' in h or '消息标识' in h for h in unique_headers)
                        
                        # 只有同时包含内容类和类型类字段的才是核心协议数据表
                        is_core_protocol_table = content_found and type_found
                        
                        # 标记是否为辅助性元数据表
                        is_auxiliary_table = is_port_table or is_meta_table
                        
                        # 提取数据行
                        for r_idx in range(header_row_idx + 1, len(grid)):
                            if r_idx >= len(grid):
                                continue
                            row = grid[r_idx]
                            if not row or len(row) == 0 or len(row) < len(headers) // 2: continue
                            
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
                        
                        # 临时保存所有表格，后续统一过滤
                        if data_rows:
                            # 创建表格数据副本，添加辅助表标记用于过滤
                            table_data = {
                                'index': table_idx,
                                'msg_name': msg_name,
                                'meta': meta,
                                'data_rows': data_rows,
                                'headers': unique_headers,  # 使用处理后的表头
                                'is_auxiliary': is_auxiliary_table  # 添加辅助表标记
                            }
                            extracted_tables.append(table_data)
        except Exception as e:
            logger.error(f"Error extracting tables from {file_path}: {str(e)}")
            
        # 过滤掉辅助性元数据表，只返回核心协议数据表，并移除内部标记字段
        filtered_tables = []
        for table in extracted_tables:
            if not table.get('is_auxiliary', False):
                # 移除内部使用的辅助表标记字段
                clean_table = {k: v for k, v in table.items() if k != 'is_auxiliary'}
                filtered_tables.append(clean_table)
        
        return filtered_tables

class DocumentParser:
    def __init__(self, config=None):
        self.detector = TableDetector()
        self.linker = TableLinker()
    def parse(self, path):
        raw_tables = self.detector.extract_tables_from_docx(path)
        # 关联表格信息
        linked_tables = self.linker.link_tables(raw_tables)
        return {'tables': linked_tables, 'tables_count': len(linked_tables)}
