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
    - "字节" → UINT8 (8)  // 非标准类型转换为标准类型

    新增：16进制字节数 → 十进制位数换算
    返回值新增状态标记：'normal' 或 'inferred'（推断/转换出来的）
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
        'UINTEGERR-32': ('UINT32', 32),   # 拼写错误容错：多一个R
        'UINT32':  ('UINT32', 32), 'INT32':   ('INT32',  32),
        'INT-32':  ('INT32',  32), 'UINT-32': ('UINT32', 32),
        '32BIT无符号整型': ('UINT32', 32), '32位无符号整型': ('UINT32', 32),
        '32BIT有符号整型': ('INT32',  32), '32位有符号整型': ('INT32',  32),
        '32位整型': ('UINT32', 32),
        # 64 bit
        'INT64':   ('INT64',  64), 'UINT64':  ('UINT64', 64),
        'INTEGER-64':  ('INT64',  64), 'UINTEGER-64': ('UINT64', 64),
        'INT-64':  ('INT64',  64), 'UINT-64': ('UINT64', 64),
        'LONGLONG': ('INT64', 64), 'ULONGLONG': ('UINT64', 64),
        # 16 bit 中文别名
        '16BIT无符号整型': ('UINT16', 16), '16位无符号整型': ('UINT16', 16),
        '16BIT有符号整型': ('INT16',  16), '16位有符号整型': ('INT16',  16),
        # 8 bit 中文别名
        '8BIT无符号整型': ('UINT8', 8),  '8位无符号整型': ('UINT8', 8),
        # 浮点
        'FLOAT':   ('FLOAT', 32), 'FLOAT32': ('FLOAT', 32),
        '单精度浮点':  ('FLOAT', 32), '单精度': ('FLOAT', 32),
        'DOUBLE':  ('DOUBLE', 64), 'FLOAT64': ('DOUBLE', 64),
        '双精度浮点':  ('DOUBLE', 64), '双精度': ('DOUBLE', 64),
        # 枚举
        'ENUM': ('ENUM', 0), '枚举': ('ENUM', 0),
    }

    def convert_type(self, type_str: str) -> Tuple[str, int, str]:
        """
        将原始类型字符串标准化。

        Returns:
            (标准类型名称, 位数, 状态)
            其中状态为：
            - 'normal': 直接来自标准类型映射表
            - 'inferred': 从非标准类型（如"字节"）推断转换出来的
            - 'warning': 无法识别的类型
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

        # 3. 处理单独的"字节"或"Bytes"这样的非标准类型
        # "字节" → UINT8 (8 bit)
        if clean in ('字节', 'BYTE', 'BYTES'):
            return 'UINT8', 8, 'inferred'

        # 4. 从类型字符串提取字节数并换算为 bit 数（如 "4字节" → 32位）
        byte_match = re.search(r'(\d+)\s*(?:字节|[Bb][Yy][Tt][Ee]s?|B\b)', type_str, re.IGNORECASE)
        if byte_match:
            nbytes = int(byte_match.group(1))
            bits = nbytes * 8
            # 根据 bit 数推断标准类型
            if bits == 8:   return 'UINT8',  bits, 'inferred'
            if bits == 16:  return 'UINT16', bits, 'inferred'
            if bits == 32:  return 'UINT32', bits, 'inferred'
            if bits == 64:  return 'UINT64', bits, 'inferred'

        # 5. 直接找 bit 数（如 "16bit"）
        bit_match = re.search(r'(\d+)\s*[bB][iI][tT]\b', type_str)
        if bit_match:
            bits = int(bit_match.group(1))
            return type_str_clean, bits, 'normal'

        # 6. 从类型名称里提取数字（如 "UINT32" → 32）
        # 只有当字符串看起来像类型定义（以字母打头且含数字）时才提取
        if re.match(r'^[A-Za-z]', type_str_clean) and re.search(r'\d', type_str_clean):
            num_match = re.search(r'(\d+)', type_str_clean)
            bits = int(num_match.group(1)) if num_match else 0
            return type_str_clean, bits, 'warning'
        
        # 7. 如果全是数字或其他非法形式，返回空（不是有效类型）
        return '', 0, 'warning'


class RangeValueFormatter:
    """
    值域/取值范围格式标准化。

    目标格式：[min,max]（16进制→十进制，用方括号和逗号表示范围）
    特殊格式保留原样：{0, 1, 2, 3}（枚举值）
    """

    def format_range(self, range_str: str) -> str:
        """
        标准化值域字符串，保持原始进制格式。
    
        示例：
          '0x00~0xFF'   → '[0x00, 0xFF]'    ← 保持十六进制
          '[0, 255]'    → '[0, 255]'         ← 保持十进制
          '0-400'       → '[0, 400]'         ← 保持十进制
          '{0x1701, 0x1702}' → '{0x1701, 0x1702}'  ← 保持十六进制
          '0x1701:供电 0x1702:断电' → '{0x1701, 0x1702}'  ← 保持十六进制
          '乘以 10'      → （由 FormulaStandardizer 处理）
        """
        if not range_str:
            return ''
    
        s = range_str.strip()
    
        # 跳过空格或特殊表示
        if s in ('—', '-', '', 'N/A', 'n/a'):
            return s
    
        # 检查是否是枚举值格式（{...}）
        if s.startswith('{') and s.endswith('}'):
            # 提取枚举值内容
            enum_content = s[1:-1].strip()
            # 统一分隔符和去除空格，保持原始进制
            enum_content = re.sub(r'\s*[,，]\s*', ', ', enum_content)
            # 保留枚举值格式
            return f'{{{enum_content}}}'
    
        # 检查是否是 0x1701:供电 0x1702:断电 格式的枚举值
        hex_pattern = r'0x[0-9A-Fa-f]+'
        if re.search(hex_pattern, s):
            # 先检查是否包含范围分隔符（~ 或 -），如果有则不是枚举
            if '~' in s or (re.search(r'\d\s*-\s*\d', s) and not re.search(r'-\d', s)):
                # 是范围格式，跳过枚举处理
                pass
            else:
                # 提取所有 16 进制值（保持原样，不转换）
                hex_values = re.findall(hex_pattern, s)
                if len(hex_values) >= 2:
                    # 构建枚举值格式（保持十六进制）
                    return '{' + ', '.join(hex_values) + '}'
            
        # 1. 移除包围括号
        s = re.sub(r'^[\[\(]', '', s)
        s = re.sub(r'[\]\)]$', '', s)
        s = s.strip()
            
        # 1b. 保护负数：将所有负数标记为特殊符号，避免被误判为范围分隔符
        # 例如：-40~125 → __NEG__40~125，-10~-5 → __NEG__10~__NEG__5
        s = re.sub(r'-(\d+(?:\.\d+)?)', r'__NEG__\1', s)
            
        # Deleted:# 2. 16 进制转十进制（只转换纯十六进制值，如 0xFF）
        # Deleted:def hex_to_dec(m):
        # Deleted:    return str(int(m.group(0), 16))
        # Deleted:
        # Deleted:s = re.sub(r'0[xX][0-9A-Fa-f]+', hex_to_dec, s)
        # Deleted:
        # 2. 保持原始进制，不进行转换
            
        # 3. 统一分隔符：~ - → ,（用逗号作为范围分隔符）
        # 注意：此时负数已经被保护为 __NEG__，不会被替换
        # 关键修复：确保 - 作为分隔符时被替换，但不影响负数
        s = re.sub(r'\s*~\s*', ',', s)  # 先替换 ~
        s = re.sub(r'(?<!__NEG__)\s*-\s*(?!\d*__NEG__)', ',', s)  # 再替换 -（但不是负数部分）
        s = re.sub(r'\s*[,，]\s*', ',', s)  # 统一中文逗号
            
        # 4. 恢复负数标记：__NEG__ → -
        s = re.sub(r'__NEG__', '-', s)
            
        # 5. 清理多余逗号和空格
        s = re.sub(r',+', ',', s)  # 多个逗号变成一个
        s = re.sub(r'^,', '', s)   # 移除开头逗号
        s = re.sub(r',$', '', s)   # 移除结尾逗号
        s = re.sub(r'\s+', ' ', s)  # 移除多余空格，保留一个空格
                
        # 6. 用方括号包裹（输出格式：[min,max]）
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
        """生成 ax+b 格式字符串，自动规范化系数（注意：使用小写 x）"""
        a_str = self._fmt_num(a)
        b_float = float(b)
        b_str = self._fmt_num(b)
        # 如果 b 是负数，使用 x-|b| 的形式（而不是 x+-|b|）
        if b_float < 0:
            return f'{a_str}x{b_str}'  # b_str 已经包含负号，如 "-3"
        else:
            return f'{a_str}x+{b_str}'

    def standardize(self, formula_str: str) -> str:
        if not formula_str:
            return ''

        s = formula_str.strip()

        # 跳过空或无效
        if s in ('—', '-', '', '无', 'N/A'):
            return s

        # 0a. 16进制数格式 (0x开头的数字)：尝试转换为十进制
        # 如果只是简单的16进制数字，转换为十进制；如果是复杂表达式，保留原样
        hex_match = re.search(r'0[xX]([0-9A-Fa-f]+)', s)
        if hex_match:
            try:
                hex_val = int(hex_match.group(1), 16)
                # 替换16进制为十进制
                s_converted = s[:hex_match.start()] + str(hex_val) + s[hex_match.end():]
                # 如果转换后仍是有效公式格式，继续处理；否则保留原样
                if re.search(r'[\d.]+\s*\*?\s*[xX]', s_converted):
                    s = s_converted
                else:
                    return s  # 不是有效公式格式，保留原样
            except (ValueError, OverflowError):
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

        # 3. 复杂表达式：(X/A)×B 或 (数字/数字)×数字 → (B/A)X+0
        # 例如：(模拟量/2^12)×21 → (21/4096)X+0 ≈ 0.00512695X+0
        # 匹配模式：(任意变量名/常数或2^N)×常数，如 (data/100)*50 或 (模拟量采集数据/2^12)×21
        m = re.search(r'[\(（]\s*[xX\u4e00-\u9fff\w]*\s*[/÷]\s*([2-9][\^^][\d]+|[\d.]+)\s*[\)）]\s*[×*]\s*([\d.]+)', s)
        if m:
            divisor_str = m.group(1)
            multiplier = float(m.group(2))
            # 处理 2^12 这样的幂次表达式
            if '^' in divisor_str or '^' in divisor_str:
                power_match = re.match(r'([2-9])\s*[\^]\s*(\d+)', divisor_str)
                if power_match:
                    base = int(power_match.group(1))
                    exp = int(power_match.group(2))
                    divisor = base ** exp
                else:
                    divisor = float(divisor_str)
            else:
                divisor = float(divisor_str)
            
            if divisor != 0:
                a_val = multiplier / divisor
                a_str = f'{a_val:.6g}'
                return self._make_formula(a_str, '0')
        
        # 3b. 更灵活的复杂表达式：(任意/常数或幂次表达式)×常数
        m = re.search(r'[\(（]([^）)]*)[/÷]([2-9][\^^][\d]+|[\d.]+)[\)）]\s*[×*]\s*([\d.]+)', s)
        if m:
            divisor_str = m.group(2)
            multiplier = float(m.group(3))
            # 处理 2^12 这样的幂次表达式
            if '^' in divisor_str or '^' in divisor_str:
                power_match = re.match(r'([2-9])\s*[\^]\s*(\d+)', divisor_str)
                if power_match:
                    base = int(power_match.group(1))
                    exp = int(power_match.group(2))
                    divisor = base ** exp
                else:
                    divisor = float(divisor_str)
            else:
                divisor = float(divisor_str)
            
            if divisor != 0:
                a_val = multiplier / divisor
                a_str = f'{a_val:.6g}'
                return self._make_formula(a_str, '0')

        # 4. x/N 格式 → (1/N)X+0
        m = re.match(r'^[xX]/([\d.]+)$', s)
        if m:
            divisor = float(m.group(1))
            if divisor != 0:
                a_val = 1.0 / divisor
                # 保留有意义的精度
                a_str = f'{a_val:.6g}'
                return self._make_formula(a_str, '0')

        # 5. '乘以N' / '×N' / '乘N'，支持带偏移量 'N+M' 或 'N-M'
        m = re.search(r'[乘×]\s*[以]?\s*([\d.]+)\s*([+\-])\s*([\d.]+)', s)
        if m:
            a = m.group(1)
            sign = m.group(2)
            b_abs = float(m.group(3))
            b = b_abs if sign == '+' else -b_abs
            return self._make_formula(a, str(b))
        # 无偏移量的乘以 N
        m = re.search(r'[乘×]\s*[以]?\s*([\d.]+)', s)
        if m:
            return self._make_formula(m.group(1), '0')

        # 6. '除以N' / '÷N'，支持带偏移量 'N+M' 或 'N-M'
        m = re.search(r'[除÷]\s*[以]?\s*([\d.]+)\s*([+\-])\s*([\d.]+)', s)
        if m:
            divisor = float(m.group(1))
            sign = m.group(2)
            b_abs = float(m.group(3))
            if divisor != 0:
                a_val = 1.0 / divisor
                b = b_abs if sign == '+' else -b_abs
                return self._make_formula(f'{a_val:.6g}', str(b))
        # 无偏移量的除以 N
        m = re.search(r'[除÷]\s*[以]?\s*([\d.]+)', s)
        if m:
            divisor = float(m.group(1))
            if divisor != 0:
                a_val = 1.0 / divisor
                return self._make_formula(f'{a_val:.6g}', '0')

        # 7. '量化单位N' / '分辨率N'，支持带偏移量
        m = re.search(r'(?:量化单位|分辨率)\s*([\d.]+)\s*([+\-])\s*([\d.]+)', s)
        if m:
            a = m.group(1)
            sign = m.group(2)
            b_abs = float(m.group(3))
            b = b_abs if sign == '+' else -b_abs
            return self._make_formula(a, str(b))
        # 无偏移量的量化单位/分辨率
        m = re.search(r'(?:量化单位|分辨率)\s*([\d.]+)', s)
        if m:
            return self._make_formula(m.group(1), '0')

        # 8. 含小数点数字直接提取（如 '0.125°'）
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


class UnitExtractor:
    """
    单位提取器。
    从备注或描述文本中识别物理单位。
    """
    
    # 常见单位列表（支持大小写感知的正则匹配）
    # 注意：复合单位（m/s, km/h 等）必须放在前面，优先于单字母 m/s/km 匹配
    UNIT_PATTERNS = [
        r'm/s²', r'm/s2', r'm/s',                  # 复合速度/加速度单位（长 → 短，防止m/s被m误匹配）
        r'km/h',                                   # 速度
        r'rad/s²', r'rad/s2', r'rad/s',            # 复合角速度（必须在 rad 和 s 之前）
        r'°/s',                                    # 角速度（度/秒）
        r'ms', r'us', r'ns', r's', r'min', r'h',   # 时间
        r'mV', r'kV', r'V', r'mA', r'uA', r'A',   # 电压电流
        r'℃', r'°C',                               # 温度（K 单独后置，避免被 kg/kPa 的 k 抢先匹配）
        r'Hz', r'kHz', r'MHz', r'GHz',             # 频率
        r'rad', r'°', r'度',                       # 角度（单独，在复合角速度之后）
        r'%', r'dB', r'dBm',                       # 比例/增益
        r'km', r'cm', r'mm', r'um', r'nm', r'm',   # 长度
        r'kg', r'mg', r'ug',                       # 质量（必须在 K 之前，否则 K 的(?i)会误匹配 kg 的 k）
        r'kPa', r'MPa', r'Pa',                     # 压力（kPa 先于 Pa，Pa 先于 P/A 单字母）
        r'K',                                      # 开尔文温度（单字母，放在 kg/kPa 之后）
        r'byte', r'bits', r'bit',                  # 数据量
    ]

    def extract_unit(self, text: str) -> Optional[str]:
        if not text or len(text) > 200: # 备注太长可能包含干扰，限制长度
            return None

        # 如果备注中含有表格/章节/附录等引用，说明是引用说明，
        # 其中的孤立字母（如"见表A.2"中的A、"B.5"中的B）不应被提取为单位
        # 覆盖格式：见表A.2 / B.5 / 附表2 / 图3.1 / 附录C / 见第X章 等
        if (re.search(r'见[表附图][A-Za-z0-9.、.\-\u4e00-\u9fff]+', text)
            or re.search(r'[表附图][A-Za-z0-9.、.\-]+\d', text)
            or re.search(r'附录[A-Za-z]', text)
            or re.search(r'第[一二三四五六七八九十\d]+[章节]', text)):
            # 过滤掉单个大写字母单位（如 A/V/K），避免把表号中的字母误识别为单位
            # 但保留复合单位（如 mA/kHz 等）
            patterns_to_try = [p for p in self.UNIT_PATTERNS
                               if not re.match(r'^[A-Za-z]$', p)]
        # 先检查是否包含"分辨率"、"量化单位"等关键字，如果包含则不提取 % 作为单位
        # 因为这些场景下 % 是转换公式的一部分，不是物理单位
        elif re.search(r'(?:分辨率|量化单位|LSB)', text, re.IGNORECASE):
            # 过滤掉 % 单位，只尝试其他单位
            patterns_to_try = [p for p in self.UNIT_PATTERNS if p != r'%']
        else:
            patterns_to_try = self.UNIT_PATTERNS
        
        # 匹配模式：搜索单位出现的位置，然后通过上下文判断是否有效
        # 注意：Python 的 \b 只对 ASCII \w 字符有效，中文不算 \w，
        #       所以"最大电流3A"中 A 前面的 3 使得 \bA 不成立。
        #       单字母单位全部用"是否独立出现"的上下文逻辑来判断，不靠 \b。
        for pattern in patterns_to_try:
            if pattern in (r'°', r'℃', r'度', r'%'):
                full_pattern = pattern  # 特殊符号直接匹配
            elif len(pattern) == 1 and pattern.isalpha():
                # 单字母：不用 \b，直接搜索字母本身；上下文校验在后面做
                full_pattern = r'(?i)' + re.escape(pattern)
            else:
                # 多字母单位（ms/mA/kHz 等）：用 \b 防止把 "msl" 中的 "ms" 误匹配
                # 但去掉 (?<!中文) 的 lookbehind，允许"单位为ms"、"32位整型ms"等中文前缀
                full_pattern = r'(?i)' + pattern + r'(?![A-Za-z\d])'

            match = re.search(full_pattern, text)
            if match:
                matched_unit = match.group(0)
                # ── 单字母单位上下文校验 ─────────────────────────────────────────
                if len(matched_unit) == 1 and matched_unit.isalpha():
                    before = text[:match.start()]
                    after  = text[match.end():]

                    # ① 明确声明"单位为X / 单位是X / 单位：X / (X)"：直接通过
                    #    例："单位为A" → A 前面是"为"，通过; "(A)" → 通过
                    is_explicit_unit_decl = bool(
                        re.search(r'单位\s*[为是：:]\s*$', before.rstrip())
                    )
                    # (X) 格式：仅当括号内是单位且后面紧跟标点或结束时才算明确声明
                    # 例："(A)"后面如果还有"表示选项"则不算明确声明
                    if re.search(r'[（\(]\s*$', before):
                        paren_after = text[match.end():]
                        # 括号内容后面紧跟 ) 且 ) 后面是标点/结束/数字，才算明确声明
                        if re.match(r'^\s*[）\)]', paren_after):
                            close_paren_pos = paren_after.find(')') if ')' in paren_after else paren_after.find('）')
                            after_close = paren_after[close_paren_pos+1:].strip() if close_paren_pos >= 0 else ''
                            # ) 后面如果是逗号、句号、分号或空白/结束，算明确声明
                            if not after_close or re.match(r'^[,，。；;\s]', after_close):
                                is_explicit_unit_decl = True
                    

                    # ② 数值上下文：数字紧邻前面，或前面是"/"（复合单位如 °/s）
                    #    例："3A"、"5 A"、"12V"、"°/s"
                    has_numeric_context = bool(
                        re.search(r'[\d.]\s*$', before) or
                        re.search(r'[/]\s*$', before)
                    )

                    # ③ 排除：后面紧跟中文（字母是中文句子的一部分）
                    #    例："见表A中的"（A后面接中文"中"）、"图B所示"
                    followed_by_chinese = bool(re.match(r'^\s*[\u4e00-\u9fff]', after))

                    # ④ 排除：前面紧跟中文且无数字上下文且不是明确声明
                    #    例："见表A"（A前面是中文"表"，后面是字符串结束）
                    only_chinese_before = bool(
                        re.search(r'[\u4e00-\u9fff]\s*$', before) and not has_numeric_context
                    )

                    if is_explicit_unit_decl:
                        pass  # 明确声明，通过
                    elif has_numeric_context and not followed_by_chinese:
                        pass  # 数值上下文且后面不接中文，通过
                    else:
                        continue  # 其他（包括只有中文前缀无数字、后面接中文等）跳过
                return matched_unit
        
        return None


class DataProcessor:
    """数据行处理器"""

    def __init__(self, config=None):
        self.type_converter = DataTypeConverter()
        self.range_formatter = RangeValueFormatter()
        self.formula_std = FormulaStandardizer()
        self.unit_extractor = UnitExtractor()
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
            std_type, bits, type_status = self.type_converter.convert_type(type_val)
            result['converted']['标准类型'] = std_type
            result['converted']['位数'] = bits
            result['converted']['类型状态'] = type_status  # 'normal', 'inferred', 'warning'
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
        # 1. 尝试从原有的"值域"列提取
        for k, v in cleaned.items():
            if any(kw in k for kw in ['值域', '取值范围']):
                range_val = str(v).strip() if v else ''
                if range_val and range_val not in ('—', '-', ''):
                    break
                range_val = ''
        
        # 2. 如果值域列为空，尝试从备注列提取
        if not range_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['备注', '说明']):
                    txt = str(v).strip() if v else ''
                    if txt and txt not in ('—', '-', ''):
                        # 提取枚举值格式
                        enum_match = re.search(r'\{([^\}]+)\}', txt)
                        if enum_match:
                            range_val = enum_match.group(0)
                            break
                        # 提取范围格式（要求明确标注"取值范围"或"值域"关键词）
                        range_match = re.search(r'(?:取值范围 | 值域)[：:\s]*((?:\d+|0[xX][0-9A-Fa-f]+)\s*[~\-]\s*(?:\d+|0[xX][0-9A-Fa-f]+))', txt, re.IGNORECASE)
                        if range_match:
                            range_val = range_match.group(1)
                            break
                        # 提取 0x1701:供电 格式的枚举值（要求至少 2 个这样的格式）
                        enum_matches = re.findall(r'(0x[0-9A-Fa-f]+\s*:\s*[^\s,;,.]+)', txt, re.IGNORECASE)
                        if len(enum_matches) >= 2:
                            range_val = ' '.join(enum_matches)
                            break

        if range_val:
            result['formatted']['值域'] = self.range_formatter.format_range(range_val)

        # ── 单位提取 (优先从单位列提取，兜底从备注提取) ─────────────────────────
        unit_val = ''
        # 1. 尝试从原有的"单位"列提取
        for k, v in cleaned.items():
            if k == '单位' or k == 'UNIT':
                val = str(v).strip() if v else ''
                if val and val not in ('—', '-', ''):
                    unit_val = val
                    break
        
        # 2. 如果单位列为空，尝试从备注列提取
        if not unit_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['备注', '说明']):
                    txt = str(v).strip() if v else ''
                    if txt and txt not in ('—', '-', ''):
                        extracted = self.unit_extractor.extract_unit(txt)
                        if extracted:
                            unit_val = extracted
                            break
        
        if unit_val:
            result['formatted']['单位'] = unit_val

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
            - "乘以N" / "乘以N+M" / "×N" 等（但排除 "A×B" 这种两个数字间的乘法，如 "212×21"）
            - "除以N" / "除以N+M" / "÷N" 等
            - 复杂表达式：(A/B)×C 或 (X/A)×B 等
            - "量化单位N" / "分辨率N" 及其带偏移量的变体
            - 以数字开头的 "aX" 或 "a*X" 格式（整段只有公式）
            - 典型 aX+b 模式
            
            注意：纯整数/纯小数（如"1"、"0.5"）不是转换公式，应该被排除
            """
            # 排除纯整数或纯小数（不含任何运算符或特殊符号）
            if re.match(r'^[\d.]+$', txt.strip()):
                return False
            
            # 复杂表达式：(变量/常数或2^N)×常数，如 (模拟量/2^12)×21
            # 检测模式：括号内有除法，后面跟乘法
            if re.search(r'[\(（][^）)]*[/÷][^）)]*[\)）]\s*[×*]\s*[\d.]', txt):
                return True
            
            # 中文 "乘以N" 及 "乘以N±M" 形式（允许 "乘以10" 或 "乘以10+3" 但排除描述性表达）
            if re.search(r'(?<![0-9a-zA-Z])乘以\s*[\d.]+\s*[+\-]?\s*[\d.]*', txt):
                return True
            # "×N" 及 "×N±M" 形式：×号前不能是数字、字母、中文字、全角括号/标点
            # 但要允许 (数字)×数字 这样的表达式
            if re.search(r'(?<![0-9a-zA-Z\u4e00-\u9fff\uff01-\uff5e\uff00-\uffef])[×]\s*[\d.]+\s*[+\-]?\s*[\d.]*', txt):
                return True
            # 中文 "除以N" 及 "除以N±M" 形式
            if re.search(r'(?<![0-9a-zA-Z])除以\s*[\d.]+\s*[+\-]?\s*[\d.]*', txt):
                return True
            # "÷N" 及 "÷N±M" 形式
            if re.search(r'[÷]\s*[\d.]+\s*[+\-]?\s*[\d.]*', txt):
                return True
            # "量化单位N" / "分辨率N" 及其带偏移量的形式
            if re.search(r'(?:量化单位|分辨率)\s*[\d.]+\s*[+\-]?\s*[\d.]*', txt):
                return True
            # 以数字开头的 aX 或 a*X 格式（整行是公式，不是描述文本）
            if re.match(r'^[\d.]+\s*\*?\s*[xX]', txt):
                return True
            # 典型 aX+b 模式（数字+X+符号+数字）
            if re.search(r'(?<![a-zA-Z\u4e00-\u9fff])[\d.]+\s*\*?\s*[xX]\s*[+\-]\s*[\d.]', txt):
                return True
            # 等式格式：物理值=aX, Y=0.01×X, 分数系数=100/65535*X（物理量标定公式）
            if re.search(
                r'(?:[\u4e00-\u9fffA-Za-z][\w\u4e00-\u9fff]*\s*=\s*)'
                r'[\d.]+(?:/[\d.]+)?\s*[×*]\s*[XxA-Z]',
                txt
            ):
                return True
            # 变量×系数格式：ADC值×0.1+20（无等号，变量名在左×数字在右）
            if re.search(
                r'[\u4e00-\u9fffA-Za-z][\w\u4e00-\u9fff]*\s*[×*]\s*[\d.]+(?:\s*[+\-]\s*[\d.]+)?',
                txt
            ):
                return True
            return False

        # 先收集所有备注/说明列的文本（用于后续判断"数据处理"是否是干扰项）
        remark_texts = []
        for k, v in cleaned.items():
            if any(kw in k for kw in ['备注', '说明']):
                t = str(v).strip() if v else ''
                if t and t not in ('—', '-', ''):
                    remark_texts.append(t)
        combined_remark = ' '.join(remark_texts)

        def _classify_remark_content(txt: str) -> Dict[str, str]:
            """
            智能分类备注内容，返回 {目标字段：内容}
            支持的分类：值域、单位、转换公式、保留备注
            
            提取顺序和优先级：
            1. 值域（范围、枚举）- 最高优先级
            2. 单位 - 次优先级
            3. 转换公式 - 第三优先级
            4. 剩余内容作为备注
            """
            if not txt or len(txt) < 2:
                return {'备注': txt}
            
            result = {}
            remaining_txt = txt
            
            # ========== 步骤 1：提取值域（优先级最高）==========
            # 1.1 明确标注“值域”、“取值范围” + 范围格式（使用分组只捕获数值部分）
            range_match = re.search(r'(?:值域 | 取值范围)[：:\s]*([\[\(]?\s*-?(?:\d+|0[xX][0-9A-Fa-f]+)(?:\.\d+)?\s*[~\-]\s*-?(?:\d+|0[xX][0-9A-Fa-f]+)(?:\.\d+)?\s*[\]\)]?)', txt, re.IGNORECASE)
            if not range_match:
                # 1.2 花括号枚举：{0x1701, 0x1702} 或 {5889, 5890}
                range_match = re.search(r'(\{[^}]*(?:0x[0-9A-Fa-f]+|\d+)[^}]*\})', txt)
            if not range_match:
                # 1.3 纯数字范围（支持负数和十六进制）：-40~125, 0~100, 0~0xFFFF
                # 关键改进：第二个数字使用 [1-9]\d* 避免匹配到单个 0，从而正确匹配 0~0xFFFF 而不是 0~0
                range_match = re.search(r'(-?(?:\d+|0[xX][0-9A-Fa-f]+)\s*[~\-]\s*-?(?:[1-9]\d*|0[xX][0-9A-Fa-f]+))', txt)
                # 验证不是单个数字（必须包含分隔符）
                if range_match and '~' not in txt and '-' not in txt:
                    range_match = None
            
            if range_match:
                # 如果有分组 1（纯数值），使用分组 1；否则使用整个匹配
                range_val = range_match.group(1).strip() if range_match.lastindex and range_match.lastindex >= 1 else range_match.group(0).strip()
                # 排除明显不是范围的（如比例描述 "0%~100%" 中的单独部分）
                if any(c in range_val for c in ['~', '-', '{', '}', '[', ']', '(', ')']):
                    result['值域'] = RangeValueFormatter().format_range(range_val)
                    # 从剩余文本中移除（只移除范围部分，保留其他描述）
                    remaining_txt = remaining_txt.replace(range_match.group(0), '', 1)
            
            # ========== 步骤 2：提取单位 ==========
            # 2.1 LSB=N 单位（要求带物理单位）
            lsb_unit_match = re.search(r'LSB\s*=\s*([\d.]+\s*(?:ms|s|μs|us|min|h|Hz|kHz|MHz|GHz|V|mV|A|mA|mW|W|dB|dBm|℃|°|°C|bit|byte|KB|MB|°/[hmin]|km/h|m/s[²2]?))', txt, re.IGNORECASE)
            if lsb_unit_match:
                result['单位'] = lsb_unit_match.group(1).strip()
                remaining_txt = remaining_txt.replace(lsb_unit_match.group(0), '', 1)
            else:
                # 2.2 "单位为 N"、"单位:N"（要求冒号/等号紧邻单位）
                unit_keyword_match = re.search(r'单位 [为是：:]\s*([A-Za-z/°℃\u00b0\u2103]+)', txt, re.IGNORECASE)
                if unit_keyword_match:
                    unit_val = unit_keyword_match.group(1).strip()
                    if len(unit_val) <= 10 and unit_val not in ['为', '是', '的', '']:
                        result['单位'] = unit_val
                        remaining_txt = remaining_txt.replace(unit_keyword_match.group(0), '', 1)
                else:
                    # 2.3 括号中的单位 (ms)、[Hz]（要求在行尾或逗号前）
                    bracket_unit_match = re.search(r'[（\(\[]([A-Za-z/°℃\u00b0\u2103]+)[）\)\]](?:\s*$|\s*[,，])', txt)
                    if bracket_unit_match:
                        result['单位'] = bracket_unit_match.group(1).strip()
                        remaining_txt = remaining_txt.replace(bracket_unit_match.group(0), '', 1)
            
            # ========== 步骤 3：提取转换公式 ==========
            # 支持格式：
            # 1. 复杂表达式：(变量/常数或 2^N)×常数，如 (模拟量采集数据/2^12)×21
            # 2. 等式格式：物理值=aX, Y=0.01×X, Y=aX+b（物理量标定公式）
            # 3. 中文描述：乘以/除以 A±B（支持中文"加""减"和符号"+""-"）
            
            # 其他类型（LSB、量化单位、分辨率等）都不提取为转换公式
            
            # 3.0 优先匹配复杂表达式：(变量/常数或 2^N)×常数，如 (模拟量采集数据/2^12)×21
            complex_formula_match = re.search(r'[\(（][^）)]*[/÷][^）)]*[\)）]\s*[×*]\s*[\d.]+', txt)
            if complex_formula_match:
                formula_val = complex_formula_match.group(0).strip()
                result['转换公式'] = FormulaStandardizer().standardize(formula_val)
                remaining_txt = remaining_txt.replace(complex_formula_match.group(0), '', 1)
            else:
                # 3.05 等式格式："物理值=0.01×X" / "Y=aX" / "Y=aX+b"
                # 也支持分数系数 "物理值=100/65535*X"、汉字+英文变量名
                eq_formula_match = re.search(
                    r'(?:[\u4e00-\u9fffA-Za-z][\w\u4e00-\u9fff]*\s*=\s*)'
                    r'(([\d.]+(?:/[\d.]+)?)\s*[×*]\s*[XxA-Z](?:\s*[+\-]\s*[\d.]+)?)',
                    txt
                )
                if eq_formula_match:
                    formula_expr = eq_formula_match.group(1).strip()
                    result['转换公式'] = FormulaStandardizer().standardize(formula_expr)
                    remaining_txt = remaining_txt.replace(eq_formula_match.group(0), '', 1)
                else:
                    # 3.06 变量×系数格式："ADC值×0.1+20"（无等号，变量名×数字）
                    var_coef_match = re.search(
                        r'([\u4e00-\u9fffA-Za-z][\w\u4e00-\u9fff]*)\s*[×*]\s*([\d.]+)(?:\s*([+\-])\s*([\d.]+))?',
                        txt
                    )
                    if var_coef_match and var_coef_match.group(1) not in {'LSB', 'bit', 'byte', 'Byte'}:
                        coef   = var_coef_match.group(2)
                        b_sign = var_coef_match.group(3) or ''
                        b_val  = var_coef_match.group(4) or ''
                        formula_expr = f'{coef}×X{b_sign}{b_val}'
                        result['转换公式'] = FormulaStandardizer().standardize(formula_expr)
                        remaining_txt = remaining_txt.replace(var_coef_match.group(0), '', 1)
                    else:
                        pass  # 继续下一步
                if '转换公式' not in result:
                    # 3.1 中文描述：乘以/除以 N±M（支持中文"加""减"和符号"+""-"）
                    chinese_formula_with_offset = re.search(r'[乘除×÷]\s*[以]?\s*([\d.]+)\s*(?:[+\-]|加减 | 减去 | 减 | 加上 | 加)\s*([\d.]+)', txt)
                    if chinese_formula_with_offset:
                        a = chinese_formula_with_offset.group(1)
                        op = '×' if '乘' in txt or '×' in txt else '÷'
                        # 判断是加还是减
                        sign_str = chinese_formula_with_offset.group(0)
                        if any(c in sign_str for c in ['-', '减', '减去']):
                            sign = '-'
                        else:
                            sign = '+'
                        b = chinese_formula_with_offset.group(2)
                        if op == '÷':
                            result['转换公式'] = f'{1/float(a):.6g}x{sign}{b}'
                        else:
                            result['转换公式'] = f'{a}x{sign}{b}'
                        remaining_txt = remaining_txt.replace(chinese_formula_with_offset.group(0), '', 1)
                    else:
                        # 3.2 简单中文描述：乘以/除以 N
                        chinese_formula_simple = re.search(r'[乘除×÷]\s*[以]?\s*([\d.]+)', txt)
                        if chinese_formula_simple:
                            a = chinese_formula_simple.group(1)
                            op = '×' if '乘' in txt or '×' in txt else '÷'
                            if op == '÷':
                                result['转换公式'] = f'{1/float(a):.6g}x+0'
                            else:
                                result['转换公式'] = f'{a}x+0'
                            remaining_txt = remaining_txt.replace(chinese_formula_simple.group(0), '', 1)
            
            # ========== 步骤 4：从剩余文本中智能识别 ==========
            # 4.1 识别枚举值描述（支持备注中的"0x1701:供电 0x1702:断电"格式）
            if '值域' not in result:
                enum_desc = self._extract_enum_from_description(remaining_txt)
                if enum_desc:
                    result['值域'] = enum_desc
                    # 注意：不删除原文本，保持备注内容完整
            
            # 4.2 识别文字描述中的单位（如"温度 (摄氏度)" → "℃"）
            if '单位' not in result:
                text_unit = self._extract_unit_from_text(remaining_txt)
                if text_unit:
                    result['单位'] = text_unit
            
            # ========== 步骤 5：清理剩余文本 ==========
            remaining_txt = re.sub(r'\s+', ' ', remaining_txt).strip()
            # 移除开头和结尾的标点
            remaining_txt = re.sub(r'^[，,;；:.:\s]+', '', remaining_txt)
            remaining_txt = re.sub(r'[，,;；:.:\s]+$', '', remaining_txt)
            
            if remaining_txt and len(remaining_txt) >= 2:
                result['备注'] = remaining_txt
            
            return result
        
        def _is_enum_value_description(txt: str) -> bool:
            """判断是否是枚举值描述（如 '0x1701:供电 0x1702:断电'）"""
            if not txt or len(txt) < 5:
                return False
            
            # 特征 1：多个 16 进制数/数字 + 冒号 + 描述的格式
            hex_enum_pattern = r'(?:0x[0-9A-Fa-f]+|\d+)\s*:\s*[^\s:]+'
            hex_matches = re.findall(hex_enum_pattern, txt)
            
            # 特征 2：包含花括号的枚举格式 {...}
            brace_enum_pattern = r'\{[^}]*[0-9A-Fa-fxX][^}]*\}'
            brace_matches = re.findall(brace_enum_pattern, txt)
            
            # 特征 3：明确的"枚举"、"值域"等关键词 + 多个数值
            keyword_pattern = r'(?:枚举 | 值域|取值).*?((?:0x[0-9A-Fa-f]+|\d+)[^\n]{0,50})'
            keyword_matches = re.findall(keyword_pattern, txt, re.IGNORECASE)
            
            # 满足以下任一条件即可判定为枚举值：
            # 1. 有 2 个以上的冒号分隔枚举项
            # 2. 有花括号枚举格式
            # 3. 有枚举关键词且包含多个数值
            return len(hex_matches) >= 2 or len(brace_matches) >= 1 or (len(keyword_matches) >= 1 and len(re.findall(r'0x[0-9A-Fa-f]+|\d+', keyword_matches[0])) >= 2)
        
        def _is_math_formula(txt: str) -> bool:
            """判断是否是数学转换公式（如 '乘以 10'、'0.1x+5'）"""
            if not txt or len(txt) < 2:
                return False
            
            # 数学公式特征模式
            formula_patterns = [
                # 中文描述：乘以 N、除以 N、乘 N、除 N
                r'[乘除×÷]\s*[以]?\s*[\d.]+',
                # 代数表达式：aX+b, a*x+b, ax+b
                r'[\d.]+\s*\*?\s*[xX]\s*[+\-]\s*[\d.]+',
                # 纯乘法：aX, a*x
                r'[\d.]+\s*\*?\s*[xX]$',
                # 分数形式：x/N, X/n
                r'^[xX]/[\d.]+$',
                # 复杂表达式：(X/A)×B, (模拟量/100)*50
                r'[\(（].*?[xX\u4e00-\u9fff].*?[/÷].*?[\)）]\s*[×*]',
                # 量化单位描述：量化单位 N、分辨率 N
                r'(?:量化单位 | 分辨率)\s*[\d.]+',
                # LSB 描述：LSB=N, LSB=1ms
                r'LSB\s*=\s*[\d.]+',
            ]
            
            for pattern in formula_patterns:
                if re.search(pattern, txt, re.IGNORECASE):
                    return True
            
            return False
                
        def _is_simple_multiply_description(txt: str) -> bool:
            """
            判断是否是"乘以 N / 除以 N"这样的简短处理描述（而非真正的量化公式）。
            当同行备注/说明有更详细内容时，这类描述应该被忽略。
            """
            return bool(combined_remark and len(txt) <= 5
                        and re.fullmatch(r'[乘除×÷]\s*[以]?\s*[\d.]+', txt))

        # 优先级 2：数据转换相关列（数据转换、数据转换方法、转换公式）
        # 注意：'数据转换' 会匹配到 '数据转换方法' 这类列
        if not formula_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['转换公式', '数据转换']):
                    txt = str(v).strip() if v else ''
                    if not txt or txt in ('—', '-', ''):
                        continue
                    if not _has_formula_content(txt):
                        continue
                    # 过滤枚举值描述
                    if _is_enum_value_description(txt):
                        continue
                    # 同样需要过滤：当该列只是简短的"乘以 N"且同行有详细备注说明时，忽略
                    if _is_simple_multiply_description(txt):
                        continue
                    formula_val = txt
                    formula_source = k
                    break
        
        # 优先级 3：数据处理/数据处理方法/数据来源列（含转换公式或值域描述）
        # 同时提取公式和值域（如"物理值=0.01×X；值域：-100~100m/s"可同时提取两者）
        if not formula_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['数据处理方法', '数据处理', '数据转换方法', '数据来源']):
                    txt = str(v).strip() if v else ''
                    if not txt or txt in ('—', '-', ''):
                        continue
                    # 无论是否有公式，都尝试从数据来源列提取值域（避免丢失值域信息）
                    if '值域' not in result['formatted']:
                        classified_src = _classify_remark_content(txt)
                        if '值域' in classified_src:
                            result['formatted']['值域'] = classified_src['值域']
                    if not _has_formula_content(txt):
                        continue
                    # 过滤枚举值描述
                    if _is_enum_value_description(txt):
                        continue
                    if _is_simple_multiply_description(txt):
                        continue
                    # 对数据来源列：尝试提取等式中的公式部分（如"物理值=0.01×X"→"0.01×X"）
                    # 支持分数系数 "物理值=100/65535*X" 和汉字变量名
                    if '数据来源' in k:
                        eq_m = re.search(
                            r'(?:[\u4e00-\u9fffA-Za-z][\w\u4e00-\u9fff]*\s*=\s*)'
                            r'(([\d.]+(?:/[\d.]+)?)\s*[×*]\s*[XxA-Z](?:\s*[+\-]\s*[\d.]+)?)',
                            txt
                        )
                        if eq_m:
                            formula_val = eq_m.group(1).strip()
                            formula_source = k
                            break
                        # 变量×系数格式："ADC值×0.1+20"（无等号）
                        var_m = re.search(
                            r'([\u4e00-\u9fffA-Za-z][\w\u4e00-\u9fff]*)\s*[×*]\s*([\d.]+)(?:\s*([+\-])\s*([\d.]+))?',
                            txt
                        )
                        if var_m and var_m.group(1) not in {'LSB', 'bit', 'byte', 'Byte'}:
                            coef   = var_m.group(2)
                            b_sign = var_m.group(3) or ''
                            b_val  = var_m.group(4) or ''
                            formula_val = f'{coef}×X{b_sign}{b_val}'
                            formula_source = k
                            break
                    formula_val = txt
                    formula_source = k
                    break
        
        # 优先级 4：备注/说明列（智能分割和归类）
        if not formula_val:
            for k, v in cleaned.items():
                if any(kw in k for kw in ['备注', '说明']):
                    txt = str(v).strip() if v else ''
                    if txt and txt not in ('—', '-', ''):
                        # 先检查是否是纯枚举值描述，如果是则只提取值域
                        if _is_enum_value_description(txt):
                            # 使用智能分类提取值域
                            classified = _classify_remark_content(txt)
                            if '值域' in classified:
                                result['formatted']['值域'] = classified['值域']
                            # 保留原始备注
                            result['cleaned']['备注'] = txt
                            break
                        
                        # 对混合内容进行智能分割和归类
                        classified = _classify_remark_content(txt)
                        
                        # 应用分类结果
                        if '值域' in classified and '值域' not in result['formatted']:
                            result['formatted']['值域'] = classified['值域']
                        
                        if '单位' in classified and '单位' not in result['formatted']:
                            result['formatted']['单位'] = classified['单位']
                        
                        if '转换公式' in classified:
                            # 直接设置到结果中，而不是只设置 formula_val
                            result['formatted']['转换公式'] = classified['转换公式']
                            formula_val = classified['转换公式']
                        
                        # 保留原始备注内容（用户要求原模原样保留）
                        # 不覆盖 cleaned 中的备注，保持原始文本完整
                        # result['cleaned']['备注'] = txt  # 保持原始备注不变
                        
                        break

        if formula_val:
            result['formatted']['转换公式'] = self.formula_std.standardize(formula_val)

        return result
    
    def _extract_enum_from_description(self, txt: str) -> Optional[str]:
        """
        从文字描述中提取枚举值。
        
        支持的格式：
        - "0x1701:供电 0x1702:断电" → {0x1701, 0x1702}（保持十六进制）
        - "0:停止 1:运行 2:待机" → {0, 1, 2}（保持十进制）
        - "高电平：1，低电平：0" → {1, 0}
        
        保持原样原则：
        - 原文十六进制 → 保持十六进制
        - 原文十进制 → 保持十进制
        
        Args:
            txt: 描述文本
            
        Returns:
            枚举值字符串（花括号包裹），如果没有则返回 None
        """
        if not txt:
            return None
        
        # 模式 1: 十六进制枚举 0xNNNN:描述（支持括号内的补充说明）
        # 改进：匹配到逗号、分号或句号为单位，而不是简单的非空白字符
        hex_pattern = r'0[xX][0-9A-Fa-f]+\s*[:：]\s*[^\s,，;；.。]+'
        hex_matches = re.findall(hex_pattern, txt, re.IGNORECASE)
        if len(hex_matches) >= 2:
            # 提取十六进制值（保持原样，不转换）
            values = []
            for m in hex_matches:
                hex_val = re.search(r'0[xX]([0-9A-Fa-f]+)', m, re.IGNORECASE)
                if hex_val:
                    # 保持十六进制格式
                    values.append('0x' + hex_val.group(1))
            
            if values:
                return '{' + ', '.join(values) + '}'
        
        # 模式 2: 十进制枚举 数字：描述（同样支持括号）
        dec_pattern = r'\d+\s*[:：]\s*[^\s,，;；.。]+'
        dec_matches = re.findall(dec_pattern, txt)
        if len(dec_matches) >= 2:
            values = []
            for m in dec_matches:
                num_match = re.match(r'(\d+)', m)
                if num_match:
                    values.append(num_match.group(1))
            
            if values:
                return '{' + ', '.join(values) + '}'
        
        return None
    
    def _extract_unit_from_text(self, txt: str) -> Optional[str]:
        """
        从纯文字描述中提取单位。
        
        支持的格式：
        - "温度 (摄氏度)" → "℃"
        - "电压 [伏特]" → "V"
        - "时间（毫秒）" → "ms"
        
        Args:
            txt: 描述文本
            
        Returns:
            单位字符串，如果没有则返回 None
        """
        if not txt:
            return None
        
        # 常见中文单位映射
        unit_mapping = {
            '摄氏度': '℃',
            '华氏度': '℉',
            '伏特': 'V',
            '安培': 'A',
            '瓦特': 'W',
            '欧姆': 'Ω',
            '赫兹': 'Hz',
            '秒': 's',
            '毫秒': 'ms',
            '微秒': 'us',
            '分钟': 'min',
            '小时': 'h',
            '米': 'm',
            '千米': 'km',
            '厘米': 'cm',
            '毫米': 'mm',
        }
        
        # 尝试从括号中提取
        bracket_match = re.search(r'[（\(]([^）)]+)[）\)]', txt)
        if bracket_match:
            content = bracket_match.group(1).strip()
            # 检查是否是单位
            if content in unit_mapping:
                return unit_mapping[content]
            # 如果是英文单位直接返回
            if re.match(r'^[A-Za-z/°℃\u00b0\u2103]+$', content):
                return content
        
        return None
