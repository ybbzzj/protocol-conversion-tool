#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置选项管理器
允许用户选择不同的处理策略
"""

class ProcessingConfig:
    """处理配置选项"""
    
    def __init__(self):
        # 命名策略
        self.naming_strategy = 'keep_original'  # 'keep_original' 或 'add_sequence'
        
        # 字段分配策略
        self.field_mapping_strategy = 'strict_separation'  # 'strict_separation' 或 'expected_compatible'
        
        # 去重策略
        self.deduplication_strategy = 'keep_all'  # 'keep_all' 或 'smart_deduplicate'
        
        # 单位提取策略
        self.unit_extraction_strategy = 'conservative'  # 'conservative' 或 'aggressive'
    
    def set_naming_strategy(self, strategy):
        """设置命名策略"""
        if strategy in ['keep_original', 'add_sequence']:
            self.naming_strategy = strategy
        else:
            raise ValueError("Invalid naming strategy")
    
    def set_field_mapping_strategy(self, strategy):
        """设置字段映射策略"""
        if strategy in ['strict_separation', 'expected_compatible']:
            self.field_mapping_strategy = strategy
        else:
            raise ValueError("Invalid field mapping strategy")
    
    def apply_config_to_exporter(self, exporter):
        """应用配置到导出器"""
        # 这里可以根据配置调整导出器的行为
        pass

# 默认配置实例
default_config = ProcessingConfig()

# 预设配置模板
CONFIG_TEMPLATES = {
    'strict_accuracy': {  # 严格准确性 - 保持数据原始性
        'naming_strategy': 'keep_original',
        'field_mapping_strategy': 'strict_separation', 
        'deduplication_strategy': 'keep_all',
        'unit_extraction_strategy': 'conservative'
    },
    
    'expected_compatible': {  # 与预期结果兼容 - 模仿人工整理结果
        'naming_strategy': 'keep_original',
        'field_mapping_strategy': 'expected_compatible',
        'deduplication_strategy': 'smart_deduplicate', 
        'unit_extraction_strategy': 'aggressive'
    }
}