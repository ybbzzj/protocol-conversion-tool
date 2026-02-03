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
        output_path = os.path.join(self.output_dir, f"protocol_{task_id}.xlsx")
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
                else:
                    fill_data['名称'] = ""
                
                # 标准化类型
                if '标准类型' in conv_info: fill_data['转换类型'] = conv_info['标准类型']
                if '位数' in conv_info: fill_data['类型（bit）'] = conv_info['位数']
                
                # 注入公式
                range_val = cleaned_data.get('值域', cleaned_data.get('取值范围', ''))
                if range_val: fill_data['判读公式（暂不设计）'] = range_val

                # --- 精准填充 17 列 ---
                for col_idx, col_name in enumerate(template_headers, 1):
                    if not col_name: continue
                    val = self._find_value_for_column(col_name, fill_data)
                    if val is not None:
                        ws.cell(row=current_row, column=col_idx, value=val)
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
