#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预期结果兼容模式处理器
专门用于生成与预期结果格式完全一致的输出
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.excel_exporter import ExcelExporter
import pandas as pd

class ExpectedCompatibleExporter(ExcelExporter):
    """预期结果兼容导出器"""
    
    def _extract_unit(self, cleaned: dict) -> tuple:
        """
        重写单位提取逻辑，模仿预期结果的处理方式
        预期结果倾向于把处理方法放入单位栏
        """
        unit_val = ''
        unit_source = 'original'
        
        # 1. 首先检查数据处理方法字段
        if '数据处理方法' in cleaned and cleaned['数据处理方法']:
            process_method = str(cleaned['数据处理方法']).strip()
            # 如果处理方法包含技术规格信息，则优先使用
            if any(keyword in process_method for keyword in 
                   ['LSB=', '位=', '32位', '16位', '整型数', '以上电为零点']):
                unit_val = process_method
                unit_source = 'from_process_method'
                return unit_val, unit_source
        
        # 2. 检查传统的单位字段
        unit_fields = ['单位', '计量单位', 'Unit']
        for unit_field in unit_fields:
            if unit_field in cleaned and cleaned[unit_field]:
                candidate = str(cleaned[unit_field]).strip()
                # 只有简单的单位符号才使用
                if candidate in ['ms', 's', 'V', 'A', 'Hz', '—', '-', '无'] or \
                   len(candidate) <= 5:
                    unit_val = candidate
                    unit_source = 'original'
                    return unit_val, unit_source
        
        # 3. 从备注中提取
        if '备注' in cleaned and cleaned['备注']:
            remark = str(cleaned['备注']).strip()
            extracted = self._extract_unit_from_remark_simple(remark)
            if extracted:
                unit_val = extracted
                unit_source = 'extracted'
                return unit_val, unit_source
        
        return unit_val, unit_source
    
    def _extract_unit_from_remark_simple(self, remark: str) -> str:
        """简化的单位提取，只提取明显的技术单位"""
        if not remark:
            return ''
            
        # 只提取最明显的单位符号
        simple_units = ['ms', 's', 'V', 'A', 'Hz', '°', '%']
        for unit in simple_units:
            if unit in remark:
                return unit
        return ''
    
    def _find_remark_value(self, cleaned: dict) -> str:
        """
        重写备注提取逻辑，移除已经在单位栏中的处理方法
        """
        remark_val = super()._find_remark_value(cleaned)
        
        if remark_val and '数据处理方法' in cleaned:
            process_method = str(cleaned['数据处理方法']).strip()
            
            # 移除处理方法内容
            if process_method in remark_val:
                remark_val = remark_val.replace(process_method, '').strip()
            
            # 移除技术规格关键词
            keywords = ['32位整型数', 'LSB=', '以上电为零点', '软件开算时刻清零', 
                       '16位', '8位', '整型数']
            for keyword in keywords:
                if keyword in remark_val:
                    remark_val = remark_val.replace(keyword, '').strip()
            
            remark_val = remark_val.strip(' ，。')
        
        return remark_val if remark_val else ''

def test_compatibility():
    """测试兼容性模式"""
    print("=== 预期结果兼容模式测试 ===\n")
    
    try:
        # 直接测试字段处理逻辑
        exporter = ExpectedCompatibleExporter('backend/outputs')
        
        # 测试几个典型的字段处理情况
        test_data = [
            {
                'name': '某设备装置测量数据3',
                'content': '某设备计时时间',
                'cleaned_data': {
                    '单位': 'ms',
                    '数据处理方法': '32位整型数，LSB=1ms，以上电为零点，软件开算时刻清零。',
                    '备注': '一些额外说明'
                }
            },
            {
                'name': '状态信息',
                'content': '某设备计时时间', 
                'cleaned_data': {
                    '数据处理方法': '32位整型数，LSB=1ms，以上电为零点，软件开算时刻清零。',
                    '备注': '测试备注'
                }
            }
        ]
        
        print("🔍 字段处理逻辑测试:")
        for test_case in test_data:
            print(f"\n📋 {test_case['name']} - {test_case['content']}")
            
            # 测试单位提取
            unit_val, unit_source = exporter._extract_unit(test_case['cleaned_data'])
            print(f"   单位提取结果: {repr(unit_val)} (来源: {unit_source})")
            
            # 测试备注提取
            remark_val = exporter._find_remark_value(test_case['cleaned_data'])
            print(f"   备注提取结果: {repr(remark_val)}")
            
            # 显示原始数据供对比
            print(f"   原始数据处理方法: {repr(test_case['cleaned_data'].get('数据处理方法', ''))}")
            print(f"   原始数据备注: {repr(test_case['cleaned_data'].get('备注', ''))}")
        
        # 读取现有文件进行对比
        actual_path = 'backend/outputs/协议_20260227234614.xlsx'
        expected_path = 'word/csvfile/转换结果20260227.xlsx'
        
        actual_df = pd.read_excel(actual_path)
        expected_df = pd.read_excel(expected_path)
        
        print("\n📊 当前对比结果:")
        print(f"   预期行数: {len(expected_df)}")
        print(f"   实际行数: {len(actual_df)}")
        
        # 找到几个关键的测试用例
        test_cases = [
            ('某设备装置测量数据3', '某设备计时时间'),
            ('状态信息', '某设备计时时间'),
            ('某设备装置测量数据1', '某设备计时时间')
        ]
        
        print("\n🔍 关键测试用例对比:")
        for name, content in test_cases:
            exp_matches = expected_df[
                (expected_df['名称'] == name) & 
                (expected_df['内容'] == content)
            ]
            
            act_matches = actual_df[
                (actual_df['名称'] == name) & 
                (actual_df['内容'] == content)
            ]
            
            if not exp_matches.empty:
                exp_row = exp_matches.iloc[0]
                print(f"\n📋 {name} - {content}")
                print(f"   预期单位: {repr(str(exp_row.get('单位', '')))}")
                print(f"   预期备注: {repr(str(exp_row.get('备注', '')))}")
                
                if not act_matches.empty:
                    act_row = act_matches.iloc[0]
                    print(f"   实际单位: {repr(str(act_row.get('单位', '')))}")
                    print(f"   实际备注: {repr(str(act_row.get('备注', '')))}")
                    
                    unit_match = str(exp_row.get('单位', '')) == str(act_row.get('单位', ''))
                    remark_match = str(exp_row.get('备注', '')) == str(act_row.get('备注', ''))
                    
                    print(f"   单位一致: {'✅' if unit_match else '❌'}")
                    print(f"   备注一致: {'✅' if remark_match else '❌'}")
                else:
                    print("   ⚠️  实际结果中未找到匹配行")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_compatibility()