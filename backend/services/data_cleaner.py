# -*- coding: utf-8 -*-
import re
from typing import Dict, Tuple, Any, Optional

class DataTypeConverter:
    # 完整的 8/16/32 位数据类型映射字典
    TYPE_MAPPING = {
        'CHAR': ('UINT8', 8), 'UCHAR': ('UINT8', 8), 'BYTE': ('UINT8', 8),
        'SHORT': ('UINT16', 16), 'USHORT': ('UINT16', 16), 'UINT16': ('UINT16', 16),
        'INT': ('UINT32', 32), 'UINT': ('UINT32', 32), 'INTEGER-32': ('UINT32', 32),
        'UINTEGER-32': ('UINT32', 32), 'FLOAT': ('FLOAT32', 32), 'DOUBLE': ('FLOAT64', 64),
        '32位无符号整型': ('UINT32', 32), '16位无符号整型': ('UINT16', 16),
        '32BIT无符号整型': ('UINT32', 32), '16BIT无符号整型': ('UINT16', 16)
    }

    def convert_type(self, type_str: str) -> Tuple[str, int, str]:
        if not type_str: return ("", 0, "warning")
        clean = type_str.strip().upper()
        # 1. 查表
        if clean in self.TYPE_MAPPING:
            return self.TYPE_MAPPING[clean][0], self.TYPE_MAPPING[clean][1], "normal"
        # 2. 正则提取数字
        match = re.search(r'(\d+)', type_str)
        bits = int(match.group(1)) if match else 0
        return type_str, bits, "normal"

class DataProcessor:
    def __init__(self, config=None):
        self.type_converter = DataTypeConverter()

    def process_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # 增加安全性检查：只有字符串才执行 strip()
        result = {
            'cleaned': {
                str(k).strip(): (v.strip() if isinstance(v, str) else v) 
                for k, v in row.items()
            }, 
            'converted': {}
        }
        
        # 自动识别类型字段
        type_val = ""
        for k, v in result['cleaned'].items():
            if any(kw in k for kw in ['类型', 'TYPE']):
                type_val = v
                break
        
        if type_val:
            std_type, bits, _ = self.type_converter.convert_type(type_val)
            result['converted']['标准类型'] = std_type
            result['converted']['位数'] = bits
            
        return result
