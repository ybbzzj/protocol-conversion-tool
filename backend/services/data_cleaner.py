# -*- coding: utf-8 -*-
import re
from typing import Dict, Tuple, Any, Optional


class DataTypeConverter:
    """
    数据类型标准化转换器。

    支持：
    - UINTEGER-32 / UINT32 / 32BIT无符号整型 → UINT32 (32)
    - FLOAT / FLOAT32 / 单精度 → FLOAT32 (32)
    - DOUBLE / FLOAT64 / 双精度 → FLOAT64 (64)
    - 枚举型 → ENUM (0 bit, 特殊处理)
    - 空字符串/未知 → 原样返回

    新增：16进制字节数 → 十进制位数换算
    """

    TYPE_MAPPING: Dict[str, Tuple[str, int]] = {
        # 8 bit
        'CHAR':    ('UINT8', 8), 'UCHAR': ('UINT8', 8), 'BYTE': ('UINT8', 8),
        'UINT8':   ('UINT8', 8), 'INT8':  ('INT8',  8),
        # 16 bit
        'SHORT':   ('UINT16', 16), 'USHORT':  ('UINT16', 16), 'UINT16': ('UINT16', 16),
        'INT16':   ('INT16',  16),
        # 32 bit
        'INT':     ('UINT32', 32), 'UINT':    ('UINT32', 32),
        'LONG':    ('UINT32', 32), 'ULONG':   ('UINT32', 32),
        'INTEGER-32':  ('UINT32', 32), 'UINTEGER-32': ('UINT32', 32),
        'UINT32':  ('UINT32', 32), 'INT32':   ('INT32',  32),
        '32BIT无符号整型': ('UINT32', 32), '32位无符号整型': ('UINT32', 32),
        '32BIT有符号整型': ('INT32',  32), '32位有符号整型': ('INT32',  32),
        # 16 bit 中文别名
        '16BIT无符号整型': ('UINT16', 16), '16位无符号整型': ('UINT16', 16),
        '16BIT有符号整型': ('INT16',  16), '16位有符号整型': ('INT16',  16),
        # 8 bit 中文别名
        '8BIT无符号整型': ('UINT8', 8),  '8位无符号整型': ('UINT8', 8),
        # 浮点
        'FLOAT':   ('FLOAT32', 32), 'FLOAT32': ('FLOAT32', 32),
        '单精度浮点':  ('FLOAT32', 32), '单精度': ('FLOAT32', 32),
        'DOUBLE':  ('FLOAT64', 64), 'FLOAT64': ('FLOAT64', 64),
        '双精度浮点':  ('FLOAT64', 64), '双精度': ('FLOAT64', 64),
        # 枚举
        'ENUM': ('ENUM', 0), '枚举': ('ENUM', 0),
    }

    def convert_type(self, type_str: str) -> Tuple[str, int, str]:
        """
        将原始类型字符串标准化。

        Returns:
            (标准类型名称, 位数, 状态) 其中状态为 'normal' 或 'warning'
        """
        if not type_str:
            return ("", 0, "warning")

        type_str = str(type_str).strip()
        clean = type_str.upper().replace(' ', '').replace('-', '-')

        # 1. 直接查表（精确匹配）
        if clean in self.TYPE_MAPPING:
            t, bits = self.TYPE_MAPPING[clean]
            return t, bits, "normal"

        # 2. 不区分大小写查表
        for key, (t, bits) in self.TYPE_MAPPING.items():
            if clean == key.upper().replace(' ', '').replace('-', '-'):
                return t, bits, "normal"

        # 3. 从类型字符串提取位数
        # 3a. 先找字节数并转换为位数（如 "4字节" → 32位）
        byte_match = re.search(r'(\d+)\s*[字节Bb][Yy][Tt][Ee]?|(\d+)\s*B\b', type_str, re.IGNORECASE)
        if byte_match:
            nbytes = int(byte_match.group(1) or byte_match.group(2))
            bits = nbytes * 8
            if bits == 8:   return 'UINT8', bits, "normal"
            if bits == 16:  return 'UINT16', bits, "normal"
            if bits == 32:  return 'UINT32', bits, "normal"
            if bits == 64:  return 'UINT64', bits, "normal"

        # 3b. 直接找 bit 数
        bit_match = re.search(r'(\d+)\s*[bB][iI][tT]?\b', type_str)
        if bit_match:
            bits = int(bit_match.group(1))
            return type_str, bits, "normal"

        # 3c. 找普通数字（如 "UINT32" → 32）
        num_match = re.search(r'(\d+)', type_str)
        bits = int(num_match.group(1)) if num_match else 0

        return type_str, bits, "normal"


class RangeValueFormatter:
    """
    值域/取值范围格式标准化。

    目标格式：[min,max]（16进制→十进制，用方括号和逗号表示范围）
    特殊格式保留原样：{0, 1, 2, 3}（枚举值）
    """

    def format_range(self, range_str: str) -> str:
        """
        标准化值域字符串。

        示例：
          '0x00~0xFF'   → '[0,255]'
          '[0, 255]'    → '[0,255]'
          '0-400'       → '[0,400]'
          '乘以10'      → （由 FormulaStandardizer 处理）
        """
        if not range_str:
            return ''

        s = range_str.strip()

        # 跳过空格或特殊表示
        if s in ('—', '-', '', 'N/A', 'n/a'):
            return s

        # 1. 移除包围括号
        s = re.sub(r'^[\[\(\{]', '', s)
        s = re.sub(r'[\]\)\}]$', '', s)
        s = s.strip()

        # 2. 16进制转十进制（只转换纯十六进制值，如 0xFF）
        def hex_to_dec(m):
            return str(int(m.group(0), 16))

        s = re.sub(r'0[xX][0-9A-Fa-f]+', hex_to_dec, s)

        # 3. 统一分隔符：~ - → ,（用逗号作为范围分隔符）
        s = re.sub(r'\s*[~\-]\s*', ',', s)
        s = re.sub(r'\s*[,，]\s*', ',', s)

        # 4. 移除多余空格
        s = re.sub(r'\s+', '', s)

        # 5. 用方括号包裹（输出格式：[min,max]）
        return f'[{s}]'


class FormulaStandardizer:
    """
    数据处理公式标准化器。

    将中文描述的转换方法规范化为代数表达式：
      '乘以10'       → '10x'
      '除以100'      → 'x/100'
      '乘以0.1'      → '0.1x'
      '×0.125'      → '0.125x'
      '量化单位0.5°' → '0.5x'
    """

    def standardize(self, formula_str: str) -> str:
        if not formula_str:
            return ''

        s = formula_str.strip()

        # 跳过空或无效
        if s in ('—', '-', '', '无', 'N/A'):
            return s

        # 1. '乘以N' / '×N'
        m = re.search(r'[乘×]\s*[以]?\s*([\d.]+)', s)
        if m:
            factor = m.group(1)
            return f'{factor}x'

        # 2. '除以N' / '÷N' / '/N'
        m = re.search(r'[除÷/]\s*[以]?\s*([\d.]+)', s)
        if m:
            divisor = m.group(1)
            return f'x/{divisor}'

        # 3. '量化单位N' / '分辨率N'
        m = re.search(r'(?:量化单位|分辨率)\s*([\d.]+)', s)
        if m:
            factor = m.group(1)
            return f'{factor}x'

        # 4. 含小数点数字直接提取（如 '0.125°'）
        m = re.search(r'([\d.]+)\s*°?\s*$', s)
        if m:
            factor = m.group(1)
            # 避免把大整数（如年份）误判为系数
            val = float(factor)
            if 0 < val < 1000 and '.' in factor:
                return f'{factor}x'

        # 5. 保留含数学表达式原样（如已经是 'x/10' 格式）
        if re.match(r'^[xX]?[*/+\-]?[\d.xX()]+$', s):
            return s

        # 6. 对含小数点的数字保留3位有效数字
        def normalize_decimal(m):
            num_str = m.group(0)
            if '.' not in num_str:
                return num_str
            num = float(num_str)
            if num == 0:
                return '0'
            val_rounded = float(f'{num:.3g}')
            return str(val_rounded)

        s = re.sub(r'\d+\.\d+', normalize_decimal, s)

        return s


class DataProcessor:
    """数据行处理器"""

    def __init__(self, config=None):
        self.type_converter = DataTypeConverter()
        self.range_formatter = RangeValueFormatter()
        self.formula_std = FormulaStandardizer()

    def process_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单行数据：
        - cleaned: 原始字段清洗（strip、HTML标签去除）
        - converted: 标准化结果（标准类型、位数）
        - formatted: 值域/公式格式化结果
        """
        result = {
            'cleaned': {
                str(k).strip(): (v.strip() if isinstance(v, str) else v)
                for k, v in row.items()
            },
            'converted': {},
            'formatted': {},
        }

        cleaned = result['cleaned']

        # ── 类型标准化 ────────────────────────────────────────────────────────
        type_val = ''
        for k, v in cleaned.items():
            if any(kw in k for kw in ['类型', 'TYPE', '数据格式']):
                type_val = str(v) if v else ''
                break

        if type_val:
            std_type, bits, _ = self.type_converter.convert_type(type_val)
            result['converted']['标准类型'] = std_type
            result['converted']['位数'] = bits

        # ── 值域格式化 ─────────────────────────────────────────────────────────
        range_val = ''
        for k, v in cleaned.items():
            if any(kw in k for kw in ['值域', '取值范围']):
                range_val = str(v) if v else ''
                break

        if range_val:
            result['formatted']['值域'] = self.range_formatter.format_range(range_val)

        # ── 转换公式标准化 ─────────────────────────────────────────────────────
        formula_val = ''
        for k, v in cleaned.items():
            if any(kw in k for kw in ['转换公式', '数据处理方法', '数据处理', '数据转换']):
                formula_val = str(v) if v else ''
                break

        if formula_val:
            result['formatted']['转换公式'] = self.formula_std.standardize(formula_val)

        return result
