#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成最新的 Excel 转换结果

使用方法:
    python3 generate_latest_result.py
    
输出:
    backend/outputs/协议_YYYYMMDDHHMMSS.xlsx
"""

import sys
sys.path.insert(0, '/Users/yuanyuqing/Documents/code/schoolProject')

import json
from backend.services.excel_exporter import ExcelExporter

def main():
    print("=" * 100)
    print("【生成最新的 Excel 转换结果】")
    print("=" * 100)

    # 读取 JSON 数据
    try:
        with open('table_recognition_results/latest_recognition.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ 错误：找不到 table_recognition_results/latest_recognition.json")
        return False

    # 提取 tables 数据
    tables_data = data.get('tables', [])
    print(f"\n✓ 从 JSON 中提取了 {len(tables_data)} 个表格")

    # 导出为 Excel
    try:
        exporter = ExcelExporter('backend/outputs')
        output_path = exporter.export_with_template(tables_data, 'latest_result')
        print(f"\n✓ 已生成新的 Excel 文件:")
        print(f"  {output_path}")
        
        print("\n" + "=" * 100)
        print("✓ 完成！")
        print("=" * 100)
        return True
    except Exception as e:
        print(f"\n❌ 生成 Excel 文件失败: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
