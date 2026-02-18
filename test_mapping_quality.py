#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试映射质量计算功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.routes.extract import _calculate_mapping_quality, _load_expected_fields
from backend.services.field_matcher import EnhancedFieldMatcher

def test_mapping_quality():
    """测试映射质量计算"""
    print("=== 测试映射质量计算 ===\n")
    
    # 测试数据
    extracted_fields = [
        '名称', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码',
        '子地址或消息地址', '数据段长度（总线为字，其他为字节）', 'ID',
        '内容', '子内容', '转换类型', '类型（bit）', '判读公式', 
        '转换公式', '单位', '备注'
    ]
    
    expected_fields = ['参数', '数据类型', '单位', '备注', '值域']
    
    print("提取的字段:")
    for field in extracted_fields:
        print(f"  - {field}")
    
    print(f"\n期望的字段:")
    for field in expected_fields:
        print(f"  - {field}")
    
    # 计算映射质量
    quality = _calculate_mapping_quality(extracted_fields, expected_fields)
    
    print(f"\n映射质量结果:")
    print(f"  - 评分: {quality['score']:.2f}")
    print(f"  - 等级: {quality['level']}")
    print(f"  - 精确匹配: {quality['exact_count']}")
    print(f"  - 模糊匹配: {quality['fuzzy_count']}")
    print(f"  - 未匹配: {quality['unmatched_count']}")
    print(f"  - 总数: {quality['total']}")
    
    # 详细匹配结果
    print(f"\n详细匹配结果:")
    matcher = EnhancedFieldMatcher()
    for field in extracted_fields[:10]:  # 只显示前10个
        result = matcher.match_field(field)
        if isinstance(result, dict):
            target = result.get('target', 'N/A')
            confidence = result.get('confidence', 0)
            match_type = result.get('match_type', 'N/A')
            print(f"  {field} → {target} (置信度: {confidence:.2f}, 类型: {match_type})")
        else:
            print(f"  {field} → N/A (结果类型: {type(result)})")

def test_load_expected_fields():
    """测试加载期望字段"""
    print("\n=== 测试加载期望字段 ===\n")
    
    # 模拟字段ID
    field_ids = ['1', '2', '3', '4', '5']
    
    expected_fields = _load_expected_fields(field_ids)
    
    print(f"字段ID: {field_ids}")
    print(f"加载的期望字段: {expected_fields}")

if __name__ == '__main__':
    test_load_expected_fields()
    test_mapping_quality()