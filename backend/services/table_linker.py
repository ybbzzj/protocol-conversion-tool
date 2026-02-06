# -*- coding: utf-8 -*-
"""
表格关联服务
用于将不同类型的相关表格进行关联，如将协议参数表与消息ID编码表进行关联
"""
from typing import List, Dict, Any, Optional
import re


class TableLinker:
    def __init__(self):
        # 消息名称映射词典，用于模糊匹配
        self.name_mappings = {
            'PD控制指令': ['PD控制指令', 'PD指令', 'PD控制器'],
            'PD器状态': ['PD器状态', 'PD状态', 'PD设备状态']
        }
        
        # 表格类型识别关键字
        self.table_type_keywords = {
            'port_allocation': ['端口分配表', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'],
            'message_id': ['消息ID编码表', '消息ID', '消息标识'],
            'protocol_param': ['参数', '数据类型', '数据长度', '值域', '单位', '备注']
        }

    def find_matching_table(self, tables: List[Dict], target_type: str) -> Optional[Dict]:
        """
        根据目标类型查找对应的表格
        
        Args:
            tables: 所有识别到的表格
            target_type: 目标表格类型，如 'message_id_table' 或 'port_allocation_table'
        
        Returns:
            匹配的表格或None
        """
        if target_type == 'message_id_table':
            for table in tables:
                # 检查是否为消息ID编码表
                headers = table.get('headers', [])
                data_rows = table.get('data_rows', [])
                
                # 包含消息ID字段且数据行较多的表格很可能是消息ID编码表
                has_msg_id = any('消息ID' in header or '消息标识' in header for header in headers)
                has_msg_content = any('信息内容' in header for header in headers)
                
                if has_msg_id and has_msg_content and len(data_rows) > 0:
                    return table
        elif target_type == 'port_allocation_table':
            for table in tables:
                # 检查是否为端口分配表
                headers = table.get('headers', [])
                data_rows = table.get('data_rows', [])
                
                # 包含端口分配相关字段的表格
                has_port_fields = any(keyword in str(headers) for keyword in self.table_type_keywords['port_allocation'])
                
                if has_port_fields and len(data_rows) > 0:
                    return table
        return None

    def match_message_name_and_get_metadata(self, param_msg_name: str, id_table: Dict) -> Optional[Dict]:
        """
        在消息ID编码表中查找匹配的消息名称，并返回相关元数据（信源、信宿、消息ID等）
        
        Args:
            param_msg_name: 参数表中的消息名称
            id_table: 消息ID编码表
        
        Returns:
            包含消息ID及其他元数据的字典，或None
        """
        data_rows = id_table.get('data_rows', [])
        headers = id_table.get('headers', [])
        
        # 查找相关字段的列索引
        msg_content_col = None
        msg_id_col = None
        src_col = None  # 信源
        dst_col = None  # 信宿
        
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
        
        # 在消息ID编码表中查找匹配的消息名称
        for row in data_rows:
            row_values = list(row.values())
            
            if len(row_values) > msg_content_col:
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                
                # 简单的文本匹配
                if param_msg_name.strip() in str(content_val) or str(content_val).strip() in param_msg_name:
                    # 构建元数据字典
                    metadata = {}
                    if msg_id_col is not None and msg_id_col < len(row_values):
                        metadata['消息ID'] = str(row_values[msg_id_col])
                    if src_col is not None and src_col < len(row_values):
                        metadata['信源'] = str(row_values[src_col])
                    if dst_col is not None and dst_col < len(row_values):
                        metadata['信宿'] = str(row_values[dst_col])
                    
                    return metadata
        
        # 尝试模糊匹配
        for row in data_rows:
            row_values = list(row.values())
            if len(row_values) > msg_content_col:
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                
                # 检查是否在预定义的名称映射中
                for canonical_name, aliases in self.name_mappings.items():
                    if param_msg_name in aliases and str(content_val) in aliases:
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
        """
        在消息ID编码表中查找匹配的消息名称
        
        Args:
            param_msg_name: 参数表中的消息名称
            id_table: 消息ID编码表
        
        Returns:
            匹配的消息ID或None
        """
        data_rows = id_table.get('data_rows', [])
        headers = id_table.get('headers', [])
        
        # 查找信息内容和消息ID的列索引
        msg_content_col = None
        msg_id_col = None
        
        for idx, header in enumerate(headers):
            if '信息内容' in header:
                msg_content_col = idx
            elif '消息ID' in header or '消息标识' in header:
                msg_id_col = idx
        
        if msg_content_col is None or msg_id_col is None:
            return None
        
        # 在消息ID编码表中查找匹配的消息名称
        for row in data_rows:
            # 获取行数据，兼容不同的键名格式
            row_values = list(row.values())
            
            if len(row_values) > max(msg_content_col, msg_id_col):
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                id_val = row_values[msg_id_col] if msg_id_col < len(row_values) else ""
                
                # 简单的文本匹配
                if param_msg_name.strip() in str(content_val):
                    return str(id_val)
                
                # 尝试反向匹配
                if str(content_val).strip() in param_msg_name:
                    return str(id_val)
        
        # 尝试模糊匹配
        for row in data_rows:
            row_values = list(row.values())
            if len(row_values) > max(msg_content_col, msg_id_col):
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                id_val = row_values[msg_id_col] if msg_id_col < len(row_values) else ""
                
                # 检查是否在预定义的名称映射中
                for canonical_name, aliases in self.name_mappings.items():
                    if param_msg_name in aliases and str(content_val) in aliases:
                        return str(id_val)
        
        return None

    def match_message_name_in_port_table(self, param_msg_name: str, port_table: Dict) -> Optional[Dict]:
        """
        在端口分配表中查找匹配的消息名称，并返回相关元数据
        
        Args:
            param_msg_name: 参数表中的消息名称
            port_table: 端口分配表
        
        Returns:
            匹配的元数据字典或None
        """
        data_rows = port_table.get('data_rows', [])
        headers = port_table.get('headers', [])
        
        # 查找信息内容及相关字段的列索引
        msg_content_col = None
        multicast_addr_col = None
        port_num_col = None
        src_sys_code_col = None
        src_machine_code_col = None
        dst_sys_code_col = None
        dst_machine_code_col = None
        
        for idx, header in enumerate(headers):
            if '信息内容' in header:
                msg_content_col = idx
            elif '接收组播地址' in header:
                multicast_addr_col = idx
            elif '接收端口号' in header:
                port_num_col = idx
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
        
        # 在端口分配表中查找匹配的消息名称
        for row in data_rows:
            row_values = list(row.values())
            
            if len(row_values) > msg_content_col:
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                
                # 简单的文本匹配
                if param_msg_name.strip() in str(content_val):
                    # 构建元数据字典
                    metadata = {}
                    if multicast_addr_col is not None and multicast_addr_col < len(row_values):
                        metadata['接收组播地址'] = str(row_values[multicast_addr_col])
                    if port_num_col is not None and port_num_col < len(row_values):
                        metadata['接收端口号'] = str(row_values[port_num_col])
                    if src_sys_code_col is not None and src_sys_code_col < len(row_values):
                        metadata['信源系统码'] = str(row_values[src_sys_code_col])
                    if src_machine_code_col is not None and src_machine_code_col < len(row_values):
                        metadata['信源机器码'] = str(row_values[src_machine_code_col])
                    if dst_sys_code_col is not None and dst_sys_code_col < len(row_values):
                        metadata['信宿系统码'] = str(row_values[dst_sys_code_col])
                    if dst_machine_code_col is not None and dst_machine_code_col < len(row_values):
                        metadata['信宿机器码'] = str(row_values[dst_machine_code_col])
                    
                    return metadata
                
                # 尝试反向匹配
                if str(content_val).strip() in param_msg_name:
                    # 构建元数据字典
                    metadata = {}
                    if multicast_addr_col is not None and multicast_addr_col < len(row_values):
                        metadata['接收组播地址'] = str(row_values[multicast_addr_col])
                    if port_num_col is not None and port_num_col < len(row_values):
                        metadata['接收端口号'] = str(row_values[port_num_col])
                    if src_sys_code_col is not None and src_sys_code_col < len(row_values):
                        metadata['信源系统码'] = str(row_values[src_sys_code_col])
                    if src_machine_code_col is not None and src_machine_code_col < len(row_values):
                        metadata['信源机器码'] = str(row_values[src_machine_code_col])
                    if dst_sys_code_col is not None and dst_sys_code_col < len(row_values):
                        metadata['信宿系统码'] = str(row_values[dst_sys_code_col])
                    if dst_machine_code_col is not None and dst_machine_code_col < len(row_values):
                        metadata['信宿机器码'] = str(row_values[dst_machine_code_col])
                    
                    return metadata
        
        # 尝试模糊匹配
        for row in data_rows:
            row_values = list(row.values())
            if len(row_values) > msg_content_col:
                content_val = row_values[msg_content_col] if msg_content_col < len(row_values) else ""
                
                # 检查是否在预定义的名称映射中
                for canonical_name, aliases in self.name_mappings.items():
                    if param_msg_name in aliases and str(content_val) in aliases:
                        # 构建元数据字典
                        metadata = {}
                        if multicast_addr_col is not None and multicast_addr_col < len(row_values):
                            metadata['接收组播地址'] = str(row_values[multicast_addr_col])
                        if port_num_col is not None and port_num_col < len(row_values):
                            metadata['接收端口号'] = str(row_values[port_num_col])
                        if src_sys_code_col is not None and src_sys_code_col < len(row_values):
                            metadata['信源系统码'] = str(row_values[src_sys_code_col])
                        if src_machine_code_col is not None and src_machine_code_col < len(row_values):
                            metadata['信源机器码'] = str(row_values[src_machine_code_col])
                        if dst_sys_code_col is not None and dst_sys_code_col < len(row_values):
                            metadata['信宿系统码'] = str(row_values[dst_sys_code_col])
                        if dst_machine_code_col is not None and dst_machine_code_col < len(row_values):
                            metadata['信宿机器码'] = str(row_values[dst_machine_code_col])
                        
                        return metadata
        
        return None

    def extract_all_metadata_from_table(self, auxiliary_table: Dict, target_msg_name: str) -> Optional[Dict]:
        """
        从任意辅助表中提取所有可用的元数据
        
        Args:
            auxiliary_table: 辅助表
            target_msg_name: 目标消息名称
            
        Returns:
            提取的元数据字典，或None
        """
        data_rows = auxiliary_table.get('data_rows', [])
        headers = auxiliary_table.get('headers', [])
        
        if not headers or not data_rows:
            return None
        
        # 在表中查找"信息内容"或相似的消息名称列
        msg_content_col = None
        for idx, header in enumerate(headers):
            if '信息内容' in header or '消息内容' in header or '消息' in header:
                msg_content_col = idx
                break
        
        if msg_content_col is None:
            return None
        
        # 在表中查找匹配的消息名称
        for row in data_rows:
            row_values = list(row.values())
            
            if len(row_values) > msg_content_col:
                content_val = str(row_values[msg_content_col]) if msg_content_col < len(row_values) else ""
                
                # 文本匹配或反向匹配
                if target_msg_name.strip() in content_val or content_val.strip() in target_msg_name:
                    # 提取这一行的所有数据作为元数据
                    metadata = {}
                    for col_idx, header in enumerate(headers):
                        if col_idx < len(row_values):
                            val = row_values[col_idx]
                            if val and val not in ['', '-', '—', 'xx']:
                                # 清理表头名（去掉"信息内容"等）
                                clean_header = header.strip()
                                if clean_header and clean_header not in ['信息内容', '消息内容', '消息']:
                                    metadata[clean_header] = str(val)
                    
                    if metadata:
                        return metadata
        
        return None

    def link_tables(self, tables: List[Dict]) -> List[Dict]:
        """
        关联表格，将邻近的辅助表的信息添加到核心协议表中
        
        新逻辑：
        1. 识别"核心表"（数据行最多的）
        2. 在前后寻找相似名称的辅助表（如"某设备装置测量数据1"、"某设备装置测量数据11"）
        3. 将辅助表的元数据关联到核心表
        
        Args:
            tables: 所有识别到的表格
            
        Returns:
            关联后的表格列表（仅包含核心表）
        """
        if not tables:
            return []
        
        # 分离核心协议表和辅助表
        protocol_tables = []
        auxiliary_tables = []
        
        for idx, table in enumerate(tables):
            headers = table.get('headers', [])
            msg_name = table.get('msg_name', '')
            data_rows = table.get('data_rows', [])
            meta = table.get('meta', {})
            
            # 判断是否为核心协议表（包含参数、数据类型等字段）
            has_content = any('参数' in h or '内容' in h or '信号名称' in h for h in headers)
            has_type = any('数据类型' in h or '类型' in h for h in headers)
            
            # 检查是否有有意义的协议名称
            # 从表内元数据或msg_name获取实际的协议名称
            has_real_protocol_name = False
            if meta:
                # 检查元数据中是否有实际的协议名称（不是默认的表名）
                for key in meta:
                    val = meta.get(key, '')
                    if any(k in key for k in ['信息名称', '数据项名称', '通信帧名称']) and val:
                        if val not in ['端口分配表', '协议参数表', '状态表', '指令定义表', 'ID编码表']:
                            has_real_protocol_name = True
                            break
            
            # 如果msg_name看起来是一个真实的协议名称（不是默认的表类型名）
            if not has_real_protocol_name and msg_name:
                default_names = ['端口分配表', '协议参数表', '状态表', '指令定义表', 'ID编码表', '消息ID编码表', '某状态信息']
                if msg_name not in default_names:
                    has_real_protocol_name = True
            
            if has_content and has_type and has_real_protocol_name:
                # 核心协议表：必须有数据列且有实际的协议名称
                table_with_index = table.copy()
                table_with_index['_original_index'] = idx  # 记录原始索引用于邻近查询
                protocol_tables.append(table_with_index)
            else:
                # 所有其他表都视为辅助表
                table_with_index = table.copy()
                table_with_index['_original_index'] = idx  # 记录原始索引
                auxiliary_tables.append(table_with_index)
        
        # 为每个核心协议表尝试从邻近的辅助表关联信息
        linked_tables = []
        
        for proto_table in protocol_tables:
            proto_idx = proto_table.get('_original_index', -1)
            msg_name = proto_table.get('msg_name', '')
            
            # 初始化元数据
            meta = proto_table.get('meta', {})
            
            # 策略：在前后寻找相似名称的辅助表
            # 优先查找名称高度相似的辅助表（如"某设备装置测量数据"、"某设备装置测量数据1"等）
            for aux_table in auxiliary_tables:
                aux_idx = aux_table.get('_original_index', -1)
                aux_msg_name = aux_table.get('msg_name', '')
                
                # 检查辅助表是否在邻近位置（前后不超过5个表）且名称相关
                if proto_idx >= 0 and aux_idx >= 0:
                    distance = abs(proto_idx - aux_idx)
                    if distance > 0 and distance <= 5:  # 邻近范围内，但不包括自己
                        # 检查名称是否相似（基础名称相同，可能有数字后缀差异）
                        # 例如："某设备装置测量数据" == "某设备装置测量数据1" 或 "某设备装置测量数据11"
                        if self._is_related_table_name(msg_name, aux_msg_name):
                            aux_metadata = self.extract_all_metadata_from_table(aux_table, msg_name)
                            
                            if aux_metadata:
                                # 合并辅助表的元数据（如果元数据中没有这些字段才添加）
                                for key, value in aux_metadata.items():
                                    if key not in meta:  # 避免覆盖已有的信息
                                        meta[key] = value
            
            # 更新协议表的元数据
            proto_table['meta'] = meta
            # 移除临时的索引字段
            if '_original_index' in proto_table:
                del proto_table['_original_index']
            linked_tables.append(proto_table)
        
        return linked_tables
    
    def _is_related_table_name(self, name1: str, name2: str) -> bool:
        """
        判断两个表名是否相关（同一系列的表）
        例如："某设备装置测量数据" 和 "某设备装置测量数据1" 应该被认为是相关的
        
        Args:
            name1: 表名1
            name2: 表名2
            
        Returns:
            True 如果相关，False 否则
        """
        if not name1 or not name2:
            return False
        
        # 移除末尾的数字，获取基础名称
        def get_base_name(name):
            # 移除末尾的所有数字和标点
            return re.sub(r'[0-9。.]*$', '', name).strip()
        
        base1 = get_base_name(name1)
        base2 = get_base_name(name2)
        
        # 如果基础名称相同且长度合理，则认为相关
        if base1 and base2:
            # 完全相同
            if base1 == base2:
                return True
            
            # 一个是另一个的子串（长度至少80%）
            len_min = min(len(base1), len(base2))
            len_max = max(len(base1), len(base2))
            if len_min > 0 and len_min / len_max >= 0.8:
                # 检查是否是包含关系
                if base1 in base2 or base2 in base1:
                    return True
        
        return False