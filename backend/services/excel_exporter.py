# -*- coding: utf-8 -*-
import os
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font

logger = logging.getLogger(__name__)

class ExcelExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.QUALITY_MARKS = {'normal': '✓', 'warning': '⚠️', 'error': '❌'}

    def export_with_template(self, tables_data: List[Dict], task_id: str, template_path: str = None) -> str:
        if not template_path:
            template_path = os.path.join(os.getcwd(), 'word', 'csvfile', '协议模板（公开）.docx.xlsx')
        
        output_path = os.path.join(self.output_dir, f"protocol_{task_id}_{datetime.now().strftime('%H%M%S')}.xlsx")
        
        if not os.path.exists(template_path):
            logger.warning(f"模板不存在: {template_path}, 创建新文件")
            wb = Workbook()
        else:
            shutil.copy(template_path, output_path)
            wb = load_workbook(output_path)
            
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        current_row = 2
        
        for table in tables_data:
            msg_name = table.get('msg_name', '')
            for i, row in enumerate(table.get('data_rows', [])):
                row_data = self._prepare_row_data(row, msg_name if i == 0 else '')
                for col_idx, header in enumerate(headers, 1):
                    if header in row_data:
                        ws.cell(row=current_row, column=col_idx, value=row_data[header])
                current_row += 1
        
        wb.save(output_path)
        return output_path

    def _prepare_row_data(self, row: Dict, msg_name: str) -> Dict:
        # 模拟数据清洗和位长度提取逻辑
        import re
        res = {'名称': msg_name}
        res['内容'] = row.get('内容', row.get('参数', row.get('信号名称', '')))
        
        # 捕获位数
        type_str = str(row.get('数据类型', row.get('类型', '')))
        bit_match = re.search(r'(\d+)', type_str)
        res['类型（bit）'] = bit_match.group(1) if bit_match else ""
        res['转换类型'] = type_str
        res['单位'] = row.get('单位', '')
        res['备注'] = row.get('备注', row.get('说明', ''))
        return res
