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
        关联表格，将所有辅助表的信息添加到核心协议表中
        
        Args:
            tables: 所有识别到的表格
            
        Returns:
            关联后的表格列表
        """
        # 分离核心协议表和辅助表
        protocol_tables = []
        auxiliary_tables = []
        
        for table in tables:
            headers = table.get('headers', [])
            msg_name = table.get('msg_name', '')
            
            # 判断是否为核心协议表（包含参数、数据类型等字段）
            has_content = any('参数' in h or '内容' in h or '信号名称' in h for h in headers)
            has_type = any('数据类型' in h or '类型' in h for h in headers)
            
            if has_content and has_type:
                # 核心协议表
                protocol_tables.append(table)
            else:
                # 所有其他表都视为辅助表
                # 注：包括ID编码表、端口分配表等所有辅助表
                if msg_name.endswith('表') or not has_content:
                    auxiliary_tables.append(table)
        
        # 为每个核心协议表尝试从所有辅助表关联信息
        linked_tables = []
        
        for proto_table in protocol_tables:
            msg_name = proto_table.get('msg_name', '')
            
            # 初始化元数据
            meta = proto_table.get('meta', {})
            
            # 遍历所有辅助表，尝试关联信息
            for aux_table in auxiliary_tables:
                aux_metadata = self.extract_all_metadata_from_table(aux_table, msg_name)
                
                if aux_metadata:
                    # 合并辅助表的元数据（如果元数据中没有这些字段才添加）
                    for key, value in aux_metadata.items():
                        if key not in meta:  # 避免覆盖已有的信息
                            meta[key] = value
            
            # 更新协议表的元数据
            proto_table['meta'] = meta
            linked_tables.append(proto_table)
        
        return linked_tables