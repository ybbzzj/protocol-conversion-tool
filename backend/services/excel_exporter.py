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
                    # 注入元数据
                    fill_data.update(table.get('meta', {}))
                    # 如果元数据中有消息ID，也添加到填充数据中
                    if '消息ID' in table.get('meta', {}):
                        fill_data['ID'] = table['meta']['消息ID']
                    # 映射其他元数据字段到适当的列
                    meta = table.get('meta', {})
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
                else:
                    fill_data['名称'] = ""
                
                # 标准化类型
                if '标准类型' in conv_info: fill_data['转换类型'] = conv_info['标准类型']
                if '位数' in conv_info: fill_data['类型（bit）'] = conv_info['位数']
                
                # 处理单位列：优先原始单位 → 备注提取 → 值域备选
                unit_val = cleaned_data.get('单位', '')
                unit_source = 'original'  # 标记单位来源
                
                if not unit_val:  # 原始单位为空
                    # 从备注中提取单位信息
                    remark = cleaned_data.get('备注', '')
                    if remark:
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
                            match = re.search(pattern, remark, re.IGNORECASE)
                            if match:
                                unit_val = unit_name
                                unit_source = 'remark_extracted'
                                break
                
                if not unit_val:  # 备注中也未提取到单位
                    # 最后备选：使用值域
                    unit_val = cleaned_data.get('值域', cleaned_data.get('取值范围', ''))
                    unit_source = 'range_fallback'
                
                if unit_val: 
                    fill_data['单位'] = unit_val
                    fill_data['单位来源'] = unit_source  # 记录来源用于标红

                # --- 精准填充 17 列 ---
                for col_idx, col_name in enumerate(template_headers, 1):
                    if not col_name: continue
                    val = self._find_value_for_column(col_name, fill_data)
                    if val is not None:
                        cell = ws.cell(row=current_row, column=col_idx, value=val)
                        # 如果是单位列且来源于备注提取，则标红
                        if col_name == '单位' and fill_data.get('单位来源') == 'remark_extracted':
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
        return None
