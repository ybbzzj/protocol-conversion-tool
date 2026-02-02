# -*- coding: utf-8 -*-
import os
import shutil
import re
from datetime import datetime
from typing import List, Dict
from openpyxl import load_workbook

class ExcelExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_with_template(self, tables_data: List[Dict], task_id: str) -> str:
        template_path = os.path.join(os.getcwd(), 'word', 'csvfile', '协议模板（公开）.docx.xlsx')
        output_path = os.path.join(self.output_dir, f"protocol_{task_id}.xlsx")
        
        # 复制模板
        shutil.copy(template_path, output_path)
        wb = load_workbook(output_path)
        ws = wb.active
        
        # 读取模板列头
        headers = [cell.value for cell in ws[1]]
        current_row = 2
        
        for table in tables_data:
            msg_name = table.get('msg_name', '')
            for i, row in enumerate(table.get('data_rows', [])):
                # 准备 17 列标准数据
                formatted = self._map_to_standard(row, msg_name if i == 0 else '')
                for col_idx, col_name in enumerate(headers, 1):
                    if col_name in formatted:
                        ws.cell(row=current_row, column=col_idx, value=formatted[col_name])
                current_row += 1
        
        wb.save(output_path)
        return output_path

    def _map_to_standard(self, row: Dict, msg_name: str) -> Dict:
        # 将 Word 字段映射到 Excel 模板字段
        res = {
            '名称': msg_name,
            '内容': row.get('参数', row.get('内容', row.get('字段', ''))),
            '转换类型': row.get('数据类型', row.get('类型', '')),
            '单位': row.get('单位', ''),
            '备注': row.get('备注', row.get('说明', ''))
        }
        
        # 提取 bit 位数 (如 UINT32 -> 32)
        full_type = str(res['转换类型'])
        bit_match = re.search(r'(\d+)', full_type)
        res['类型（bit）'] = bit_match.group(1) if bit_match else ""
        
        # 处理值域 (如果 word 有值域，附加到备注)
        range_val = row.get('值域', row.get('取值范围', ''))
        if range_val:
            res['备注'] = f"范围:{range_val}; {res['备注']}" if res['备注'] else f"范围:{range_val}"
            
        return res
