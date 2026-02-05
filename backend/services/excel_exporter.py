# -*- coding: utf-8 -*-
import os
import shutil
import re
from datetime import datetime
from typing import List, Dict, Any
from openpyxl import load_workbook
from backend.services.field_matcher import FieldMatcher
from backend.services.data_cleaner import DataProcessor

class ExcelExporter:
    # 元数据映射配置：定义元数据键别名和对应的Excel列名
    METADATA_MAPPING = {
        # 直接映射到Excel列的字段（别名 -> Excel列名）
        '信息标识映射': {
            '信息标识', '信息ID', '消息ID', '信息名称标识', '标识'
        },
        '信源系统码映射': {
            '信源系统码', '信源码'
        },
        '信源机器码映射': {
            '信源机器码'
        },
        '信宿系统码映射': {
            '信宿系统码'
        },
        '信宿机器码映射': {
            '信宿机器码'
        },
        '子地址映射': {
            '子地址', '消息地址', '子地址或消息地址'
        },
        'ID映射': {
            'ID', '消息ID', '信息标识'  # ID列的备用名
        },
        # 无法直接映射，需追加到备注的字段
        '备注追加字段': {
            '传输周期', '发起时机', '错误处理', '其他'
            # 注意：'信源、信宿' 已单独处理（会尝试分解），不在此列表中
        }
    }
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.matcher = FieldMatcher()
        self.processor = DataProcessor()
    
    def _find_excel_column_for_metadata(self, meta_key: str, available_columns: List[str]) -> str:
        """
        根据元数据键查找对应的Excel列名（智能匹配）
        
        Args:
            meta_key: 元数据键名
            available_columns: Excel中所有可用的列名列表
            
        Returns:
            匹配的Excel列名，如果没有匹配则返回None
        """
        # 精确匹配
        if meta_key in available_columns:
            return meta_key
        
        # 逐个检查映射配置
        for mapping_type, aliases in self.METADATA_MAPPING.items():
            if mapping_type == '备注追加字段':
                continue
            
            if meta_key in aliases:
                # 根据mapping_type确定Excel列名
                if '信息标识' in mapping_type:
                    return 'ID' if 'ID' in available_columns else None
                elif '信源系统码' in mapping_type:
                    return '信源系统码' if '信源系统码' in available_columns else None
                elif '信源机器码' in mapping_type:
                    return '信源机器码' if '信源机器码' in available_columns else None
                elif '信宿系统码' in mapping_type:
                    return '信宿系统码' if '信宿系统码' in available_columns else None
                elif '信宿机器码' in mapping_type:
                    return '信宿机器码' if '信宿机器码' in available_columns else None
                elif '子地址' in mapping_type:
                    return '子地址或消息地址' if '子地址或消息地址' in available_columns else None
        
        return None
    
    def _should_append_to_remarks(self, meta_key: str) -> bool:
        """判断是否应该将元数据追加到备注列"""
        return meta_key in self.METADATA_MAPPING.get('备注追加字段', set())
    
    def _parse_source_destination(self, combined_value: str, available_columns: List[str]) -> dict:
        """
        解析"信源、信宿"的复合字段，尝试分解为独立的信源和信宿信息
        
        示例：
        - 输入: "BCRT1-SA0-模式码0x04"
        - 输出: {'信源机器码': 'BC', '信宿机器码': 'RT1-SA0-模式码0x04'}
        
        Args:
            combined_value: 组合的信源、信宿字符串
            available_columns: Excel中所有可用列名
            
        Returns:
            字典，包含解析后的信源/信宿字段映射
        """
        result = {}
        
        if not combined_value or not isinstance(combined_value, str):
            return result
        
        # 尝试用"-"分隔符分解
        if '-' in combined_value:
            parts = combined_value.split('-', 1)  # 最多分解为2部分
            source = parts[0].strip()
            destination = '-'.join(parts[1:]).strip() if len(parts) > 1 else ""
            
            # 如果第一部分看起来像代码（如BC、SA0等），则作为信源
            if source and len(source) <= 5 and source.isalnum():
                if '信源机器码' in available_columns and source:
                    result['信源机器码'] = source
                if '信宿机器码' in available_columns and destination:
                    result['信宿机器码'] = destination
                return result
        
        # 如果没有"-"分隔符，尝试按固定位数分解（前2-3个字符作为信源）
        if len(combined_value) > 3:
            # 尝试识别信源部分（通常是2-3个字符的代码）
            for src_len in [3, 2]:  # 先尝试3字符，再尝试2字符
                source = combined_value[:src_len]
                destination = combined_value[src_len:].strip()
                
                # 检查分解是否合理（信源部分是字母/数字，信宿部分不为空）
                if source and destination and source.replace('-', '').replace('_', '').isalnum():
                    if '信源机器码' in available_columns:
                        result['信源机器码'] = source
                    if '信宿机器码' in available_columns:
                        result['信宿机器码'] = destination
                    return result
        
        # 如果无法分解，则不添加到结果
        return result

    def export_with_template(self, tables_data: List[Dict], task_id: str) -> str:
        # 1. 物理复制模板
        template_path = os.path.join(os.getcwd(), 'word', 'csvfile', '协议模板.xlsx')
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = os.path.join(self.output_dir, f"协议_{timestamp}.xlsx")
        shutil.copy(template_path, output_path)
        
        wb = load_workbook(output_path)
        ws = wb.active
        
        # 2. 读取表头
        template_headers = [cell.value if cell.value else "" for cell in ws[1]]
        current_row = 2
        
        for table in tables_data:
            msg_name = table.get('msg_name', '')
            for i, row in enumerate(table.get('data_rows', [])):
                # 深度清洗
                proc_res = self.processor.process_row(row)
                cleaned_data = proc_res['cleaned']
                conv_info = proc_res['converted']
                
                # 整合待填充数据
                fill_data = dict(cleaned_data)
                
                # --- 强制保护名称列 ---
                if i == 0:
                    fill_data['名称'] = msg_name
                    # 获取Excel中所有可用的列名
                    available_columns = template_headers
                    
                    # 注入元数据 - 包括所有从混合结构提取的元数据
                    meta = table.get('meta', {})
                    
                    # 智能映射元数据到对应的Excel列
                    remarks_parts = []  # 用于收集无法直接映射的元数据
                    
                    for meta_key, meta_value in meta.items():
                        if not meta_value:
                            continue
                        
                        # 特殊处理："信源、信宿"复合字段
                        if meta_key == '信源、信宿':
                            # 尝试分解为信源和信宿
                            parsed = self._parse_source_destination(meta_value, available_columns)
                            if parsed:
                                fill_data.update(parsed)
                            else:
                                # 分解失败，追加到备注
                                remarks_parts.append(f"{meta_key}:{meta_value}")
                            continue
                        
                        # 尝试找到对应的Excel列
                        excel_column = self._find_excel_column_for_metadata(meta_key, available_columns)
                        
                        if excel_column:
                            # 直接映射到Excel列
                            fill_data[excel_column] = meta_value
                        elif self._should_append_to_remarks(meta_key):
                            # 无法直接映射，追加到备注
                            remarks_parts.append(f"{meta_key}:{meta_value}")
                    
                    # 如果有无法直接映射的元数据，追加到备注列
                    if remarks_parts:
                        existing_remarks = fill_data.get('备注', '')
                        if existing_remarks:
                            fill_data['备注'] = existing_remarks + ' | ' + ' | '.join(remarks_parts)
                        else:
                            fill_data['备注'] = ' | '.join(remarks_parts)
                else:
                    fill_data['名称'] = ""
                
                # 标准化类型
                if '标准类型' in conv_info: fill_data['转换类型'] = conv_info['标准类型']
                if '位数' in conv_info: fill_data['类型（bit）'] = conv_info['位数']
                
                # 处理判读公式：映射值域到判读公式列
                range_val = cleaned_data.get('值域', cleaned_data.get('取值范围', ''))
                # 如果没有值域，尝试从"值"字段获取
                if not range_val:
                    range_val = cleaned_data.get('值', '')
                range_source = 'original' if range_val else None
                
                # 如果值域为空，尝试从备注/数据处理方法中提取范围
                if not range_val:
                    search_fields = [
                        cleaned_data.get('备注', ''),
                        cleaned_data.get('数据处理方法', ''),
                        cleaned_data.get('说明', '')
                    ]
                    search_text = ' '.join(f for f in search_fields if f)
                    
                    # 提取范围表达式：0~400、[0,255]、0~0xFFFF等
                    range_patterns = [
                        (r'取值范围[：:]*\s*([^\s，。、;；]+)', r'\1'),  # 取值范围: 0~400
                        (r'(\d+[~\-]0x[0-9A-Fa-f]+)', r'\1'),  # 0~0xFFFF
                        (r'(0x[0-9A-Fa-f]+[~\-]\d+)', r'\1'),  # 0xFFFF~0
                        (r'(0x[0-9A-Fa-f]+[~\-]0x[0-9A-Fa-f]+)', r'\1'),  # 0x00~0xFF
                        (r'(\d+[~\-]\d+)', r'\1'),  # 0~400 或 0-400
                        (r'(\[\d+[,，]\d+\])', r'\1'),  # [0,255]
                        (r'(\{\d+[,，\d]+\})', r'\1'),  # {0,1,2}
                    ]
                    
                    for pattern, replacement in range_patterns:
                        match = re.search(pattern, search_text)
                        if match:
                            range_val = match.group(1) if replacement == r'\1' else re.sub(pattern, replacement, match.group(0))
                            # 标准化为闭区间格式（如果是简单范围）
                            if '~' in range_val or '-' in range_val:
                                range_val = range_val.replace('-', '~')  # 统一用~
                            range_source = 'extracted'  # 标记为提取来源（需要标红）
                            break
                
                if range_val:
                    fill_data['判读公式'] = range_val
                    fill_data['判读公式来源'] = range_source
                
                # 处理单位列：优先原始单位 → 备注提取 → 值域备选
                unit_val = cleaned_data.get('单位', '')
                unit_source = 'original'  # 标记单位来源
                
                if not unit_val:  # 原始单位为空
                    # 从备注或数据处理方法字段中提取单位信息
                    search_fields = [
                        cleaned_data.get('备注', ''),
                        cleaned_data.get('数据处理方法', ''),
                        cleaned_data.get('说明', '')
                    ]
                    search_text = ' '.join(f for f in search_fields if f)
                    
                    if search_text:
                        # 改进的单位提取规则 - 按优先级匹配
                        unit_patterns = [
                            # 复合单位优先
                            (r'[°∠∠][/\\s]*(s|秒)', '°/s'),  # 角速度 °/s
                            (r'[°∠∠][/\\s]*(h|小时)', '°/h'),  # 角速度 °/h
                            (r'[°∠∠][/\\s]*(min|分钟)', '°/min'),  # 角速度 °/min
                            (r'(m/s2|m/s²|m/s\^2)', 'm/s²'),  # 加速度
                            (r'(km/h|千米/小时)', 'km/h'),     # 速度
                            (r'(r/min|rpm|转/分钟)', 'r/min'), # 转速
                                                    
                            # 基本单位
                            (r'\b(ms|毫秒)\b', 'ms'),
                            (r'\b(s|秒)\b', 's'),
                            (r'\b(Hz|赫兹)\b', 'Hz'),
                            (r'[°∠度]\b', '°'),  # 角度
                            (r'(℃|°C|摄氏度)\b', '℃'),
                            (r'\b(V|伏)\b', 'V'),
                            (r'\b(A|安)\b', 'A'),
                            (r'(Ω|欧姆)\b', 'Ω'),
                            (r'\b(bit|位)\b', 'bit'),
                            (r'\b(byte|字节)\b', 'byte'),
                            (r'\b(mV|毫伏)\b', 'mV'),
                            (r'\b(mA|毫安)\b', 'mA')
                        ]
                        
                        for pattern, unit_name in unit_patterns:
                            match = re.search(pattern, search_text, re.IGNORECASE)
                            if match:
                                unit_val = unit_name
                                unit_source = 'extracted'  # 标记为提取来源（需要标红）
                                break
                
                # 处理转换公式：提取并规范化小数点（只处理含小数点的数字）
                formula_val = cleaned_data.get('转换公式', cleaned_data.get('数据处理方法', ''))
                if formula_val:
                    # 只对含小数点的数字进行3位有效数字处理
                    def normalize_decimal(match):
                        num_str = match.group(0)
                        if '.' not in num_str:  # 跳过整数
                            return num_str
                        num = float(num_str)
                        if num == 0:
                            return '0'
                        # 保留3位有效数字
                        val_rounded = float(f"{num:.3g}")
                        return str(val_rounded)
                    
                    # 只匹配包含小数点的数字
                    formula_val = re.sub(r'\d+\.\d+', normalize_decimal, formula_val)
                    fill_data['转换公式'] = formula_val
                
                # 注：不再使用值域作为单位的备选，值域已映射到判读公式列
                
                if unit_val: 
                    fill_data['单位'] = unit_val
                    fill_data['单位来源'] = unit_source  # 记录来源用于标红

                # --- 精准填充 17 列 ---
                for col_idx, col_name in enumerate(template_headers, 1):
                    if not col_name: continue
                    val = self._find_value_for_column(col_name, fill_data)
                    if val is not None:
                        cell = ws.cell(row=current_row, column=col_idx, value=val)
                        # 标记从备注/其他地方提取的数据（标红）
                        should_mark_red = False
                        if '判读公式' in col_name and fill_data.get('判读公式来源') == 'extracted':
                            should_mark_red = True
                        elif col_name == '单位' and fill_data.get('单位来源') == 'extracted':
                            should_mark_red = True
                        
                        if should_mark_red:
                            cell.font = cell.font.copy(color="FF0000")  # 红色字体
                current_row += 1
        
        wb.save(output_path)
        return output_path

    def _find_value_for_column(self, col_name: str, fill_data: Dict) -> Any:
        if col_name in fill_data: return fill_data[col_name]
        
        # 别名查找
        for k, v in fill_data.items():
            res = self.matcher.match_field(k)
            if res.target == col_name: return v
            
        # 手动补丁
        if col_name == '内容': return fill_data.get('参数', fill_data.get('信号名称', None))
        if col_name == '转换类型': return fill_data.get('数据类型', fill_data.get('类型', None))
        if '判读公式' in col_name: return fill_data.get('判读公式', None)  # 处理"判读公式（暂不设计）"
        return None
