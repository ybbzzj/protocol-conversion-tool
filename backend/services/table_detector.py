# -*- coding: utf-8 -*-
import re
import logging
import html
from typing import List, Dict, Any, Optional
from docx2python import docx2python
from docx import Document

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
        self.keywords = ['序号', '参数', '内容', '信号名称', '信息内容', '数据类型', '类型', '长度', '单位', '备注', '值域',
                        '信源', '信宿', '信息内容', '消息ID', '接口名称', '周期', '数据处理方法', '发起时机', '错误处理']
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
            'remark': ['备注', '值域', '数据处理方法'],  # 备注类
            'meta': ['信源', '信宿', '信息内容', '消息ID', '接口名称', '周期', '发起时机', '错误处理']  # 消息元数据类
        }
        # 用于存储从python-docx获取的表格标题映射 (table_index -> title)
        self.table_titles_from_docx = {}
    
    def _extract_table_titles_from_docx(self, file_path: str) -> Dict[int, str]:
        """
        从Word文档中提取表格前面的标题文本
        返回一个映射：{table_index -> title}
        
        策略：
        1. 优先查找"表X 标题"或"表X. 标题"格式的明确标题
        2. 只提取真实存在的标题，不生成默认名称
        3. 没有标题的表格将被忽略（留作空值，由表检测器的后续逻辑处理）
        """
        titles = {}
        try:
            doc = Document(file_path)
            table_count = 0
            
            # 获取所有body元素（段落和表格）
            for block_idx, block in enumerate(list(doc.element.body)):
                if block.tag.endswith('tbl'):  # 表格
                    # 回溯查找前面的标题
                    parent = block.getparent()
                    block_position = parent.index(block)
                    
                    # 从这个表格往前查找最近的标题性文本
                    title = ""
                    # 限制回溯范围，避免查找到太远的不相关文本（最多往前2个段落）
                    for i in range(max(0, block_position - 2), -1, -1):
                        elem = parent[i]
                        if elem.tag.endswith('p'):
                            text = elem.text if hasattr(elem, 'text') else ''
                            if text.strip() and len(text) < 100:
                                # 只接受"表X"格式的标题
                                if '表' in text:
                                    # 匹配"表X 标题"、"表X. 标题"或"表 标题"等格式
                                    match = re.search(r'表[0-9A-Za-z.。]*\s*(.+?)(?:\s*$|[\s。，；])', text)
                                    if match:
                                        title = match.group(1).strip()
                                        # 移除末尾可能的标点
                                        title = re.sub(r'[\s。，；]+$', '', title).strip()
                                        # 移除末尾可能的"表"字
                                        if title.endswith('表'):
                                            title = title[:-1].strip()
                                        
                                        if title and len(title) > 0 and len(title) < 80:
                                            break
                        
                        # 如果找到有效标题，立即跳出
                        if title:
                            break
                    
                    # 只有找到真实的标题才记录
                    if title:
                        titles[table_count] = title
                    
                    table_count += 1
        except Exception as e:
            logger.warning(f"Failed to extract table titles from docx: {str(e)}")
        
        return titles

    def _clean_html_entities(self, text):
        """清理HTML实体编码（如&#x00E8;等），但保留分隔符"""
        if not text:
            return text
        # 解码HTML实体
        text = html.unescape(text)
        # 移除剩余的HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 只删除【无用的特殊字符】，但【保留分隔符】
        # 保留的字符：ASCII(32-126)、中文(\u4e00-\u9fff)、箭头(→等)、中文符号(、。等)
        # 删除的字符：除上述外的其他特殊字符（如è等无用编码字符）
        kept_chars = set()
        for c in text:
            ord_val = ord(c)
            # 保留：ASCII字符、中文、箭头、常见标点
            if (32 <= ord_val <= 126 or  # ASCII
                '\u4e00' <= c <= '\u9fff' or  # 中文
                c in '→→→·—–-_()（）【】《》「」『』、，。；：！？=+-*/'):  # 分隔符和标点
                kept_chars.add(c)
        
        text = ''.join(c for c in text if c in kept_chars or ord(c) >= 128)
        return text.strip()

    def extract_tables_from_docx(self, file_path: str) -> List[Dict]:
        extracted_tables = []
        try:
            # 首先从python-docx获取表格标题映射
            self.table_titles_from_docx = self._extract_table_titles_from_docx(file_path)
            
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
                    
                    # 1. 定位表头 - 改进逻辑以适应混合结构表格
                    header_row_idx = -1
                    max_score = 0
                    # 确保grid不为空
                    if not grid:
                        continue
                    
                    # 扩大搜索范围，检查更多行以适应复杂结构
                    # 首先尝试找到真正的数据表头行（包含序号、内容、类型等标准字段）
                    for r_idx, row in enumerate(grid[:min(20, len(grid))]):
                        if not row:
                            continue
                        
                        # 检查是否包含标准的数据表头关键词
                        has_seq = any('序号' in cell for cell in row)
                        has_content = any('参数' in cell or '内容' in cell or '信号名称' in cell for cell in row)
                        has_type = any('类型' in cell or '数据类型' in cell for cell in row)
                        has_value = any('值域' in cell or '取值范围' in cell for cell in row)
                        has_unit = any('单位' in cell for cell in row)
                        
                        # 检查是否包含这些标准字段的组合
                        standard_field_count = sum([has_seq, has_content, has_type, has_value, has_unit])
                        
                        if standard_field_count >= 3:  # 至少包含3个标准字段
                            header_row_idx = r_idx
                            break
                    
                    # 如果没找到标准字段表头，使用关键词匹配方法
                    if header_row_idx == -1:
                        for r_idx, row in enumerate(grid[:min(20, len(grid))]):
                            # 确保行不为空
                            if not row:
                                continue
                            matches = sum(1 for cell in row if any(k in cell for k in self.keywords))
                            # 评分机制：至少匹配2个关键字
                            score = matches / 4.0 if matches <= 4 else 1.0
                            if matches >= 2 and score > max_score:
                                max_score, header_row_idx = score, r_idx
                    
                    # 如果还是找不到，尝试基于结构特征
                    if header_row_idx == -1:
                        for r_idx, row in enumerate(grid[:min(15, len(grid))]):
                            if not row:
                                continue
                            # 检查是否包含典型的参数表头关键词组合
                            has_seq = any('序号' in cell for cell in row)
                            has_content = any('参数' in cell or '内容' in cell or '信号名称' in cell for cell in row)
                            has_type = any('类型' in cell or '数据类型' in cell for cell in row)
                            if (has_seq and has_content and has_type) or (has_content and has_type and len(row) >= 4):
                                header_row_idx = r_idx
                                break

                    # 特殊处理：识别混合结构表格
                    is_mixed_structure = False
                    metadata_end_row = -1
                    if header_row_idx >= 0:
                        # 检查表头前是否存在元数据区域
                        for r_idx in range(min(5, header_row_idx)):
                            row = grid[r_idx] if r_idx < len(grid) else []
                            if row:
                                # 检查是否为键值对结构（相邻单元格成对出现）
                                kv_pairs = 0
                                for i in range(0, len(row)-1, 2):
                                    if i+1 < len(row):
                                        key_cell = row[i]
                                        value_cell = row[i+1]
                                        # 检查是否为有效的键值对
                                        if (key_cell and value_cell and 
                                            key_cell != value_cell and
                                            value_cell not in ['-', '—', 'xx', ''] and
                                            any(keyword in key_cell for keyword in ['信息名称', '名称', '信息标识', '信源', '信宿', '传输周期', '发起时机'])):
                                            kv_pairs += 1
                                
                                # 如果找到足够的键值对，标记为混合结构
                                if kv_pairs >= 2:
                                    is_mixed_structure = True
                                    metadata_end_row = r_idx
                                    break

                    if header_row_idx != -1 and 0 <= header_row_idx < len(grid):
                        headers = grid[header_row_idx] if 0 <= header_row_idx < len(grid) else []
                        # 【优先使用】从表格外部（python-docx）获取的标题
                        msg_name = self.table_titles_from_docx.get(table_idx, "")
                        meta = {}
                        
                        # 2. 提取元数据（表头之上的行）
                        # 初始化unique_cells
                        unique_cells = []
                        
                        # 【改进】总是尝试从表头之前的所有行提取元数据（支持多种配对方式）
                        # 遍历表头之前的所有行，提取所有的键值对
                        for meta_row_idx in range(header_row_idx):  # 遍历表头之前的所有行
                            meta_row = grid[meta_row_idx] if meta_row_idx < len(grid) else []
                            if len(meta_row) >= 2:  # 确保有足够的单元格形成键值对
                                col_count = len(meta_row)
                                
                                # 策略：在元数据行中寻找所有有效的键值对
                                # 处理方式：逐列扫描，找到"键"和"值"的组合
                                processed_keys = set()  # 记录已处理的键，避免重复
                                
                                for col_idx in range(0, col_count - 1):
                                    # 尝试将当前列作为"键"
                                    potential_key = meta_row[col_idx].strip() if col_idx < len(meta_row) else ""
                                    
                                    # 检查是否是有效的元数据键
                                    is_metadata_key = any(kw in potential_key for kw in [
                                        '信息名称', '名称', '数据项名称', '协议名称',
                                        '信息标识', '标识', '消息ID',
                                        '信源', '信宿', '信源、信宿',
                                        '传输周期', '发起时机', '错误处理', '其他',
                                        '代号', '上级'
                                    ])
                                    
                                    if not is_metadata_key or not potential_key:
                                        continue
                                    
                                    if potential_key in processed_keys:
                                        continue
                                    
                                    # 找到一个有效的键，现在寻找对应的值
                                    # 策略1：检查紧邻的下一列
                                    value_col = col_idx + 1
                                    if value_col < col_count:
                                        potential_value = meta_row[value_col].strip() if value_col < len(meta_row) else ""
                                        
                                        # 如果下一列是键值相同的情况（重复列），则跳过，继续找下一个非重复值
                                        if potential_value == potential_key:
                                            # 尝试跳过相同值，找下一个不同的值
                                            for next_col in range(value_col + 1, col_count):
                                                next_value = meta_row[next_col].strip() if next_col < len(meta_row) else ""
                                                if next_value and next_value != potential_key and next_value not in ['-', '—', 'xx', '']:
                                                    potential_value = next_value
                                                    break
                                        
                                        # 验证找到了一个有效的值
                                        if potential_value and potential_value != potential_key and potential_value not in ['']:
                                            # 检查 potential_value 是否看起来是一个表名（作为 msg_name 候选）
                                            if any(kw in potential_key for kw in ['信息名称', '名称', '协议名称']) and not msg_name:
                                                msg_name = potential_value
                                            
                                            # 将键值对存储到meta中
                                            meta[potential_key] = potential_value
                                            processed_keys.add(potential_key)
                        
                        # 清理meta中的HTML实体编码
                        for key in meta:
                            if isinstance(meta[key], str):
                                meta[key] = self._clean_html_entities(meta[key])

                        # 特殊处理：对于多行元数据结构（如Table 21），检查是否有更丰富的元数据
                        # 检查前几行是否有键值对结构
                        for r_idx in range(min(5, header_row_idx)):  # 扩大检查范围
                            row = grid[r_idx]
                            if row and len(row) >= 2:
                                # 检查是否为键值对结构
                                for i in range(len(row) - 1):
                                    key_cell = row[i]
                                    value_cell = row[i+1]
                                    if any(kw in key_cell for kw in ['信息名称', '名称', '协议名称', '信息标识', '标识', '消息ID', '上级']):
                                        if not msg_name and value_cell and value_cell not in ['—', '-'] and value_cell != key_cell:
                                            msg_name = value_cell
                                        elif value_cell and value_cell not in ['—', '-'] and value_cell != key_cell:
                                            # 尝试将值存储到meta中
                                            if any(kw in key_cell for kw in ['信息标识', '标识', '消息ID']):
                                                meta['信息标识'] = value_cell
                                            elif any(kw in key_cell for kw in ['上级']):
                                                meta['上级'] = value_cell
                                
                                # 特别处理：检查整行是否都是键值对（横向排列）
                                if len(row) >= 4:  # 至少需要4个单元格才能形成有意义的键值对
                                    for i in range(0, len(row)-1, 2):  # 步长为2，成对处理
                                        if i+1 < len(row):
                                            key_cell = row[i]
                                            value_cell = row[i+1]
                                            # 检查是否为有效的键值对
                                            if (any(kw in key_cell for kw in ['信息名称', '名称', '协议名称']) and 
                                                value_cell and value_cell not in ['—', '-', 'xx'] and 
                                                value_cell != key_cell):
                                                if not msg_name:
                                                    msg_name = value_cell
                                            elif (any(kw in key_cell for kw in ['信息标识', '标识']) and 
                                                  value_cell and value_cell not in ['—', '-', 'xx'] and 
                                                  value_cell != key_cell):
                                                meta['信息标识'] = value_cell
                        
                        # 继续原来的逻辑，处理表头之上的行，提取所有唯一的单元格内容用于 K-V 匹配
                        all_unique_cells = []
                        for r_idx in range(header_row_idx):
                            row = grid[r_idx]
                            if row and len(row) > 0:
                                row_unique = []
                                row_unique.append(row[0])
                                for i in range(1, len(row)):
                                    if row[i] != row[i-1]:
                                        row_unique.append(row[i])
                                all_unique_cells.extend(row_unique)
                        
                        # A. 尝试在单元格之间寻找 Key-Value (例如: [名称][PD指令])
                        for i in range(len(all_unique_cells) - 1):
                            k = all_unique_cells[i]
                            v = all_unique_cells[i+1]
                            if any(kw in k for kw in ['信息名称', '名称', '协议名称']):
                                if not msg_name and v and v not in ['—', '-'] and v != k: msg_name = v
                            elif any(kw in k for kw in ['信息标识', '标识', '消息ID']):
                                if v and v not in ['—', '-'] and v != k: meta['信息标识'] = v
                            elif any(kw in k for kw in ['上级']):
                                if v and v not in ['—', '-'] and v != k: meta['上级'] = v
                        
                        # B. 尝试在单个单元格内寻找 (例如: [名称：PD指令])
                        if not msg_name:
                            for cell in all_unique_cells:
                                if any(kw in cell for kw in ['信息名称', '名称', '协议名称']):
                                    parts = re.split(r'[：:\s]+', cell)
                                    if len(parts) > 1 and parts[-1] not in ['—', '-']:
                                        msg_name = parts[-1].strip()
                                        break
                        
                        # 【备选方案】如果表格外部没有标题，再尝试从表格内部提取
                        # 3. 备选方案：如果表格内没找到标题，向文档段落回溯
                        if not msg_name:
                            for p_text in reversed(full_text_paragraphs[:200]):
                                if any(k in p_text for k in ['信息名称', '名称', '协议名称']):
                                    res = re.split(r'[：:\s]+', p_text)
                                    if len(res) > 1:
                                        msg_name = res[-1].strip()
                                        break
                        
                        # 4. 新增：处理类似"表1 端口分配表"或"表2. ID的定义"格式的表格标题
                        if not msg_name and grid:
                            # 检查表头上方的几行，看是否有表格标题格式
                            for r_idx in range(min(5, header_row_idx)):  # 检查表头上方最多5行
                                row = grid[r_idx]
                                if row:
                                    # 检查每行的第一个单元格，通常包含表格标题
                                    first_cell = row[0] if row and len(row) > 0 else ""
                                    if first_cell and '表' in first_cell:
                                        # 优先处理"表X. 表名"格式（带句号或圆点）
                                        match = re.match(r'^表\d+[.。]\s*(.+?)(?:\s|$)', first_cell)
                                        if match:
                                            msg_name = match.group(1).strip()
                                            if msg_name:
                                                break
                                        
                                        # 退而求其次处理"表X 表名"格式（带空格）
                                        if ' ' in first_cell:
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
                            headers_str = ' '.join(headers) if headers else ''
                            
                            # 第一优先级：检查是否为特殊表格类型
                            if any('消息ID' in h or '消息标识' in h for h in headers):
                                msg_name = '消息ID编码表'
                            elif any(keyword in headers_str for keyword in ['接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码']):
                                msg_name = '端口分配表'
                            else:
                                # 第二优先级：基于表头内容推断
                                temp_seq_found = any(any(kw in h for kw in self.header_categories['sequence']) for h in headers) if headers else False
                                temp_content_found = any(any(kw in h for kw in self.header_categories['content']) for h in headers) if headers else False
                                temp_type_found = any(any(kw in h for kw in self.header_categories['type']) for h in headers) if headers else False
                                
                                # 检查特殊业务关键词
                                if '接口' in headers_str and temp_content_found:
                                    msg_name = '接口参数表'
                                elif '指令' in headers_str or '命令' in headers_str:
                                    msg_name = '指令定义表'
                                elif '状态' in headers_str:
                                    msg_name = '状态表'
                                elif temp_content_found and temp_type_found:
                                    msg_name = '协议参数表'
                        
                        # 清洗标题标签
                        msg_name = re.sub(r'^(信息|名称|标识|信号|消息|—)+', '', msg_name).strip()
                        
                        # 4. 提取数据行
                        data_rows = []
                        # 处理表头重复（合并单元格）：去除完全重复的列，只保留第一个
                        unique_headers = []
                        seen_headers = set()  # 用于跟踪已见过的表头
                        header_indices_to_keep = []  # 记录要保留的原始列索引
                        
                        for col_idx, h in enumerate(headers):
                            clean_h = re.sub(r'<[^>]+>', '', h).strip()  # 移除HTML标签
                            if not clean_h:
                                clean_h = f"column_{col_idx}"
                            
                            # 如果这个表头之前没见过，就保留它
                            if clean_h not in seen_headers:
                                seen_headers.add(clean_h)
                                unique_headers.append(clean_h)
                                header_indices_to_keep.append(col_idx)
                        
                        # 更新headers为去重后的版本
                        headers = unique_headers
                        
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
                        
                        # 检查是否为协议参数表（主要包含参数和数据类型）
                        is_param_table = content_found and type_found
                        
                        # 检查是否为指令相关的协议表（包含指令、命令、控制等关键词）
                        msg_name_lower = msg_name.lower()
                        is_instruction_related = any(keyword in msg_name_lower for keyword in ['指令', '控制', '命令'])
                        
                        # 检查是否为状态相关的协议表（也属于协议的一部分）
                        is_status_related = '状态' in msg_name_lower
                        
                        # 检查是否为协议相关的表格（但排除通用的参数表）
                        is_protocol_related = '协议' in msg_name_lower and '参数' not in msg_name_lower
                        
                        # 检查是否为消息相关的表格
                        is_message_related = '消息' in msg_name_lower
                        
                        # 检查业务含义相关的关键词
                        msg_name_lower = msg_name.lower()
                        # 扩展重要业务关键词，涵盖用户提到的“检查”、“结果”、“数据”、“测量”
                        is_important_business = any(keyword in msg_name_lower for keyword in ['指令', '控制', '命令', '状态', '检查', '结果', '数据', '测量', '协议', '消息'])
                        
                        # 只要包含核心列（内容/类型）或具有业务含义的标题，就认定为核心协议数据表
                        is_core_protocol_table = is_param_table or is_important_business
                        
                        # 标记是否为辅助性元数据表（仅当既没有业务关键词也不是参数表时才标记为辅助）
                        # 根据用户要求，我们要尽量保留这些表格，因此这里缩小辅助表的定义
                        is_auxiliary_table = (is_port_table or is_meta_table) and not is_important_business
                        
                        # 强制保留所有包含数据行的表格，除非明确是端口/ID等纯元数据辅助表且用户未要求展示
                        # 这里我们根据用户反馈，将核心判断改为：只要有数据行且不是纯噪声，就保留
                        is_core_protocol_table = True if data_rows else is_core_protocol_table
                        
                        # 提取数据行（只保留去重后的列）
                        for r_idx in range(header_row_idx + 1, len(grid)):
                            if r_idx >= len(grid):
                                continue
                            row = grid[r_idx]
                            if not row or len(row) == 0 or len(row) < len(headers) // 2: continue
                            
                            row_data = {}
                            # 使用处理过的表头来创建行数据，只提取要保留的列
                            for kept_idx, col_idx in enumerate(header_indices_to_keep):
                                if kept_idx < len(headers):
                                    clean_h = headers[kept_idx]
                                    cell_val = row[col_idx] if col_idx < len(row) else ""
                                    # 清理HTML标签
                                    cell_val = re.sub(r'<[^>]+>', '', cell_val).strip()
                                    row_data[clean_h] = cell_val
                            
                            # 过滤空行和噪声
                            row_all_text = "".join(row_data.values())
                            if not row_all_text.strip(): continue
                            
                            # 过滤注释行（如'注：时间按小端处理'）
                            if any(comment_prefix in row_all_text for comment_prefix in ['注：', '注:', '说明：', '说明:', '备注：', '备注:']):
                                continue
                            
                            # 检查行的列数是否与表头匹配（至少要有一定比例的列）
                            non_empty_cols = sum(1 for cell in row if cell and cell.strip())
                            expected_cols = len(unique_headers)
                            min_required_cols = max(2, expected_cols // 3)  # 至少需要2列或1/3的列
                            
                            if non_empty_cols < min_required_cols:
                                continue
                            
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
                            # 【元数据注入】将所有meta字段注入到data_rows[0]
                            # 按照需求：如果目标字段已存在且非空，则不覆盖；否则注入meta中的值
                            if data_rows and meta:
                                for meta_key, meta_value in meta.items():
                                    # 检查是否已存在对应的表头（允许模糊匹配，如"名称"可能对应"消息名称"）
                                    existing_key = None
                                    for header in unique_headers:
                                        if meta_key in header or header in meta_key:
                                            existing_key = header
                                            break
                                    
                                    # 如果没有对应的表头，直接注入到第一行
                                    if not existing_key:
                                        # 检查第一行是否已有该键值且非空
                                        if meta_key not in data_rows[0] or not data_rows[0][meta_key]:
                                            data_rows[0][meta_key] = meta_value
                            
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
            
        # 返回所有识别到的表格，不再进行硬过滤
        # 内部逻辑标记 is_auxiliary 仅用于后续日志分级，不作为删除依据
        return extracted_tables

class DocumentParser:
    def __init__(self, config=None):
        self.detector = TableDetector()
        self.linker = TableLinker()
    def parse(self, path):
        raw_tables = self.detector.extract_tables_from_docx(path)
        # 关联表格信息
        linked_tables = self.linker.link_tables(raw_tables)
        return {'tables': linked_tables, 'tables_count': len(linked_tables)}
