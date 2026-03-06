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
        'UINTERGER-32': ('UINT32', 32),   # 常见拼写错误容错
        'UINT32':  ('UINT32', 32), 'INT32':   ('INT32',  32),
        'INT-32':  ('INT32',  32), 'UINT-32': ('UINT32', 32),
        '32BIT无符号整型': ('UINT32', 32), '32位无符号整型': ('UINT32', 32),
        '32BIT有符号整型': ('INT32',  32), '32位有符号整型': ('INT32',  32),
        '32位整型': ('UINT32', 32),
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
        # 去掉括号内的补充说明（如 "UINTEGER-32（4字节）" → "UINTEGER-32"）
        type_str_clean = re.sub(r'[（(][^)）]*[)）]', '', type_str).strip()
        clean = type_str_clean.upper().replace(' ', '')

        # 1. 直接查表（精确匹配，忽略大小写和空格）
        if clean in self.TYPE_MAPPING:
            t, bits = self.TYPE_MAPPING[clean]
            return t, bits, "normal"

        # 2. 不区分大小写查表（补偿连字符差异）
        for key, (t, bits) in self.TYPE_MAPPING.items():
            if clean == key.upper().replace(' ', ''):
                return t, bits, "normal"

        # 3. 从类型字符串提取字节数并换算为 bit 数（如 "4字节" → 32位）
        byte_match = re.search(r'(\d+)\s*(?:字节|[Bb][Yy][Tt][Ee]s?|B\b)', type_str, re.IGNORECASE)
        if byte_match:
            nbytes = int(byte_match.group(1))
            bits = nbytes * 8
            # 根据 bit 数推断标准类型
            if bits == 8:   return 'UINT8',  bits, 'normal'
            if bits == 16:  return 'UINT16', bits, 'normal'
            if bits == 32:  return 'UINT32', bits, 'normal'
            if bits == 64:  return 'UINT64', bits, 'normal'

        # 4. 直接找 bit 数（如 "16bit"）
        bit_match = re.search(r'(\d+)\s*[bB][iI][tT]\b', type_str)
        if bit_match:
            bits = int(bit_match.group(1))
            return type_str_clean, bits, 'normal'

        # 5. 从类型名称里提取数字（如 "UINT32" → 32）
        # 只有当字符串看起来像类型定义（以字母打头且含数字）时才提取
        if re.match(r'^[A-Za-z]', type_str_clean) and re.search(r'\d', type_str_clean):
            num_match = re.search(r'(\d+)', type_str_clean)
            bits = int(num_match.group(1)) if num_match else 0
        else:
            bits = 0

        return type_str_clean, bits, 'normal'


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

    目标格式：aX+b（标准线性变换形式）
    将中文描述的转换方法规范化为代数表达式：
      '乘以10'         → '10X+0'
      '除以100'        → '0.01X+0'
      '乘以0.1'        → '0.1X+0'
      '×0.125'        → '0.125X+0'
      '量化单位0.5°'   → '0.5X+0'
      '10X+5'          → '10X+5'（已标准格式直接规范化）
    """

    @staticmethod
    def _fmt_num(val_str: str) -> str:
        """将数字字符串格式化：去掉不必要的 .0 末尾（如 10.0→10, 0.5→0.5）"""
        try:
            f = float(val_str)
            # 如果是整数值，输出整数形式
            if f == int(f):
                return str(int(f))
            # 否则保留小数，但去掉末尾多余的 0
            return f'{f:g}'
        except (ValueError, TypeError):
            return str(val_str)

    def _make_formula(self, a: str, b: str = '0') -> str:
        """生成 aX+b 格式字符串，自动规范化系数"""
        a_str = self._fmt_num(a)
        b_str = self._fmt_num(b)
        return f'{a_str}X+{b_str}'

    def standardize(self, formula_str: str) -> str:
        if not formula_str:
            return ''

        s = formula_str.strip()

        # 跳过空或无效
        if s in ('—', '-', '', '无', 'N/A'):
            return s

        # 0. 含16进制数的公式（如 0x000000477*x+0），无法转为标准十进制 aX+b，保留原样
        if re.search(r'0[xX][0-9A-Fa-f]+', s):
            return s

        # 1. 已经是 aX+b 或 a*X+b 格式（大小写均可），直接规范化
        m = re.match(r'^([\d.eE+\-]+)\s*\*?\s*[xX]\s*([+\-])\s*([\d.eE+\-]+)$', s)
        if m:
            a, sign, b = m.group(1), m.group(2), m.group(3)
            try:
                b_val = float(b) if sign == '+' else -float(b)
                return self._make_formula(a, str(b_val))
            except ValueError:
                pass

        # 2. 纯 aX 或 a*X 格式（没有 +b 部分）
        m = re.match(r'^([\d.eE+\-]+)\s*\*?\s*[xX]$', s)
        if m:
            return self._make_formula(m.group(1), '0')

        # 3. x/N 格式 → (1/N)X+0
        m = re.match(r'^[xX]/([\d.]+)$', s)
        if m:
            divisor = float(m.group(1))
            if divisor != 0:
                a_val = 1.0 / divisor
                # 保留有意义的精度
                a_str = f'{a_val:.6g}'
                return self._make_formula(a_str, '0')

        # 4. '乘以N' / '×N' / '乘N'
        m = re.search(r'[乘×]\s*[以]?\s*([\d.]+)', s)
        if m:
            return self._make_formula(m.group(1), '0')

        # 5. '除以N' / '÷N'
        m = re.search(r'[除÷]\s*[以]?\s*([\d.]+)', s)
        if m:
            divisor = float(m.group(1))
            if divisor != 0:
                a_val = 1.0 / divisor
                return self._make_formula(f'{a_val:.6g}', '0')

        # 6. '量化单位N' / '分辨率N'
        m = re.search(r'(?:量化单位|分辨率)\s*([\d.]+)', s)
        if m:
            return self._make_formula(m.group(1), '0')

        # 7. 含小数点数字直接提取（如 '0.125°'）
        m = re.search(r'([\d.]+)\s*[°度]?\s*$', s)
        if m:
            factor = m.group(1)
            try:
                val = float(factor)
                # 避免把大整数（如年份）误判为系数
                if 0 < val < 10000 and '.' in factor:
                    return self._make_formula(factor, '0')
            except ValueError:
                pass

        return s


class DataProcessor:
    """数据行处理器"""

    def __init__(self, config=None):
        self.type_converter = DataTypeConverter()
        self.range_formatter = RangeValueFormatter()
        self.formula_std = FormulaStandardizer()
        # 定义内容字段名称集合（这些字段用于存放数据名称或描述）
        self.content_field_names = {'名称', '内容', '参数', '信号名称', '字段', '数据含义', '参数名称', '数据项名称', '代号', '描述'}

    def is_valid_data_row(self, row: Dict[str, Any]) -> bool:
        """
        验证行是否为有效数据行。
        
        过滤掉只有"名称"和"内容"但没有其他实际数据的无效行。
        这些通常是错误包含的元数据行，如：
        - 只有 '名称'='聚合式的信息流表征示意', '内容'='' 的行
        - 只有 '名称'='发起时机', '内容'='' 的行
        - 只有 '名称'='错误处理', '内容'='' 的行
        - 只有 '名称'='序号', '内容'='' 的行
        
        Args:
            row: 数据行字典
        
        Returns:
            bool: 如果行有效返回 True，否则返回 False
        """
        if not row:
            return False
        
        # 聚合式表格元数据行关键词（这些作为"内容"出现时，表示是元数据行而非数据行）
        # 注意：只匹配精确的元数据行标记，避免误匹配包含这些词的字段名（如"消息序号"不应被当作"序号"元数据）
        metadata_row_keywords = {
            '聚合式的信息流表征示意', '信息名称行', '信息标识行', '信源、信宿', '信源、信目',
            '传输周期', '发起时机', '错误处理', '检查结果', '非周期', '按实际操作流程'
        }
        
        # 检测元数据行（聚合式表格中的元数据区）
        for key, value in row.items():
            # 跳过内部字段
            if str(key).startswith('_'):
                continue
            # 只检查内容字段
            if key in self.content_field_names and value:
                value_str = str(value).strip()
                # 检查该内容字段是否完全等于元数据关键词（精确匹配）
                if value_str in metadata_row_keywords:
                    return False  # 是元数据行，不是有效数据行
                # 检查是否以元数据关键词开头（对于"聚合式的信息流表征示意"等）
                for keyword in metadata_row_keywords:
                    if keyword in value_str and len(value_str) - len(value_str.replace(keyword, '')) >= len(keyword):
                        # 只有当元数据关键词占比超过50%或是标题类关键词时才过滤
                        if '的' in keyword or len(keyword) >= 8:
                            return False
        
        # 检查是否有任何非内容字段的实际数据
        has_non_content_data = False
        for key, value in row.items():
            # 跳过内部字段
            if str(key).startswith('_'):
                continue
            # 跳过内容字段（名称、内容等描述字段）
            if key in self.content_field_names:
                continue
            # 检查是否有实际值
            if value and str(value).strip() and str(value).strip() not in ('—', '-', ''):
                has_non_content_data = True
                break
        
        # 如果没有任何非内容字段的数据，说明这是无效行
        return has_non_content_data

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
        # 搜索顺序：专用类型列（'类型'/'数据类型'/'数据格式'/'转换类型'）> 其他含 TYPE 的列
        # 注意：'数据长度' / '字节数' / '长度' 列不是类型列，排除
        type_val = ''
        type_search_keys = ['数据类型', '数据格式', '转换类型', '类型']
        # 先按精确优先顺序查找
        for target_kw in type_search_keys:
            for k, v in cleaned.items():
                # 排除字节/长度相关列
                if any(ex in k for ex in ['字节', '长度', '长', '数据段长度']):
                    continue
                if target_kw in k:
                    val = str(v).strip() if v else ''
                    if val and val not in ('—', '-', ''):
                        type_val = val
                        break
            if type_val:
                break
        # 如果未找到，回退到 TYPE 英文关键词
        if not type_val:
            for k, v in cleaned.items():
                if any(ex in k for ex in ['字节', '长度']):
                    continue
                if 'TYPE' in k.upper():
                    val = str(v).strip() if v else ''
                    if val and val not in ('—', '-', ''):
                        type_val = val
                        break

        if type_val:
            std_type, bits, _ = self.type_converter.convert_type(type_val)
            result['converted']['标准类型'] = std_type
            result['converted']['位数'] = bits
        else:
            # 尝试从字节数列推算 bit 数（无类型列时的兜底）
            for k, v in cleaned.items():
                if any(kw in k for kw in ['字节数', '字节', '数据长度', '数据段长度', '长度']):
                    if any(ex in k for ex in ['类型', '数据类型', '数据格式']):
                        continue  # 跳过"数据类型"等列
                    val = str(v).strip() if v else ''
                    if val and re.match(r'^\d+$', val):
                        nbytes = int(val)
                        bits = nbytes * 8
                        if bits in (8, 16, 32, 64):
                            type_map = {8: 'UINT8', 16: 'UINT16', 32: 'UINT32', 64: 'UINT64'}
                            result['converted']['位数'] = bits
                            # 不推断标准类型，只推断位数（避免误判）
                        break

        # ── 值域格式化 ─────────────────────────────────────────────────────────
        range_val = ''
        for k, v in cleaned.items():
            if any(kw in k for kw in ['值域', '取值范围']):
                range_val = str(v).strip() if v else ''
                if range_val and range_val not in ('—', '-', ''):
                    break
                range_val = ''

        if range_val:
            result['formatted']['值域'] = self.range_formatter.format_range(range_val)

        # ── 转换公式标准化 ─────────────────────────────────────────────────────
        # 搜索顺序：专用转换公式列 > 数据处理/数据转换列 > 数据处理方法列 > 备注列
        # 备注列中的公式识别优先级最低，且只有真正像公式的内容才会提取
        formula_val = ''
        formula_source = ''   # 记录来源列名，供后续判断
        # 优先级1：专用转换公式列
        for k, v in cleaned.items():
            if any(kw == k or k == kw for kw in ['转换公式']):
                if v and str(v).strip() not in ('—', '-', ''):
                    formula_val = str(v).strip()
                    formula_source = k
                    break
        def _has_formula_content(txt: str) -> bool:
            """
            检测文本是否含有明确的转换公式描述。
            规则：
            - "乘以N" / "×N"（但排除 "A×B" 这种两个数字间的乘法，如 "212×21"）
            - "除以N" / "÷N"
            - "量化单位N" / "分辨率N"
            - 以数字开头的 "aX" 或 "a*X" 格式（整段只有公式）
            """
            # 中文 "乘以N"（允许 "乘以10" 但不允许 "A乘以B" 的多操作数表达式）
            if re.search(r'(?<![0-9a-zA-Z])乘以\s*[\d.]', txt):
                return True
            # "×N"：×号前不能是数字、字母、中文字、全角括号/标点（避免误识别 "212×21"、"数据）×21"）
            # 允许：行首或半角空格/标点后的 "×N"，如 "×10"
            if re.search(r'(?<![0-9a-zA-Z\u4e00-\u9fff\uff01-\uff5e\uff00-\uffef])[×]\s*[\d.]', txt):
                return True
            # 中文 "除以N"
            if re.search(r'(?<![0-9a-zA-Z])除以\s*[\d.]', txt):
                return True
            # "÷N"
            if re.search(r'[÷]\s*[\d.]', txt):
                return True
            # "量化单位N" / "分辨率N"
            if re.search(r'(?:量化单位|分辨率)\s*[\d.]', txt):
                return True
            # 以数字开头的 aX 或 a*X 格式（整行是公式，不是描述文本）
            if re.match(r'^[\d.]+\s*\*?\s*[xX]', txt):
                return True
            # 典型 aX+b 模式（数字+X+符号+数字）
            if re.search(r'(?<![a-zA-Z\u4e00-\u9fff])[\d.]+\s*\*?\s*[xX]\s*[+\-]\s*[\d.]', txt):
                return True
            return False

        # 优先级2：数据转换/数据转换方法列
        if not formula_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['数据转换', '转换公式', '数据转换方法']):
                    txt = str(v).strip() if v else ''
                    if txt and txt not in ('—', '-', '') and _has_formula_content(txt):
                        formula_val = txt
                        formula_source = k
                        break
        # 优先级3：数据处理/数据处理方法列（中文描述，如"乘以10"）
        # 只提取明确含有转换公式的内容，避免把描述性文本（如"32位整型数..."）误识别
        if not formula_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['数据处理方法', '数据处理']):
                    txt = str(v).strip() if v else ''
                    if txt and txt not in ('—', '-', '') and _has_formula_content(txt):
                        formula_val = txt
                        formula_source = k
                        break
        # 优先级4：备注/说明列（只提取明显像公式/转换描述的内容）
        if not formula_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['备注', '说明']):
                    txt = str(v).strip() if v else ''
                    if txt and txt not in ('—', '-', '') and _has_formula_content(txt):
                        formula_val = txt
                        formula_source = k
                        break

        if formula_val:
            result['formatted']['转换公式'] = self.formula_std.standardize(formula_val)

        return result
