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
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.matcher = FieldMatcher()
        self.processor = DataProcessor()

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
                    # 注入元数据 - 包括所有从混合结构提取的元数据
                    meta = table.get('meta', {})
                    fill_data.update(meta)
                    
                    # 特别处理常见的元数据字段，确保它们被映射到正确的Excel列
                    if '接收组播地址' in meta:
                        fill_data['接收组播地址'] = meta['接收组播地址']
                    if '接收端口号' in meta:
                        fill_data['接收端口号'] = meta['接收端口号']
                    if '信源系统码' in meta:
                        fill_data['信源系统码'] = meta['信源系统码']
                    if '信源机器码' in meta:
                        fill_data['信源机器码'] = meta['信源机器码']
                    if '信宿系统码' in meta:
                        fill_data['信宿系统码'] = meta['信宿系统码']
                    if '信宿机器码' in meta:
                        fill_data['信宿机器码'] = meta['信宿机器码']
                    # 处理从横向部分提取的元数据
                    if '信源、信宿' in meta:
                        fill_data['信源、信宿'] = meta['信源、信宿']
                    if '传输周期' in meta:
                        fill_data['传输周期'] = meta['传输周期']
                    if '发起时机' in meta:
                        fill_data['发起时机'] = meta['发起时机']
                    if '错误处理' in meta:
                        fill_data['错误处理'] = meta['错误处理']
                    if '其他' in meta:
                        fill_data['其他'] = meta['其他']
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
