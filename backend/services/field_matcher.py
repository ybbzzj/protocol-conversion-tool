# -*- coding: utf-8 -*-
import json
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from rapidfuzz import process, fuzz
from flask import current_app

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    source: str
    target: str
    confidence: float
    match_type: str # exact, alias, fuzzy, none

class FieldMatcher:
    def __init__(self, config=None):
        self.config = config or {}
        self.knowledge_base = self._load_knowledge_base()
        self.alias_map = {
            '序号': 'ID',
            '参数': '内容',
            '信号名称': '内容',
            '数据类型': '转换类型',
            '类型': '转换类型',
            '数据长度': '类型（bit）',
            '字节': '类型（bit）'
        }

    def _load_knowledge_base(self) -> List[Dict]:
        file_path = current_app.config.get('KNOWLEDGE_BASE_FILE')
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_knowledge_base(self):
        file_path = current_app.config.get('KNOWLEDGE_BASE_FILE')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)

    def match_field(self, field_name: str) -> MatchResult:
        field_clean = field_name.strip()
        
        # 1. 精确匹配知识库
        for item in self.knowledge_base:
            if item['source'] == field_clean:
                return MatchResult(field_clean, item['target'], 1.0, 'exact')
        
        # 2. 别名映射
        if field_clean in self.alias_map:
            return MatchResult(field_clean, self.alias_map[field_clean], 0.9, 'alias')
            
        # 3. 模糊匹配
        targets = list(set([item['target'] for item in self.knowledge_base] + list(self.alias_map.values())))
        if targets:
            best_match = process.extractOne(field_clean, targets, scorer=fuzz.WRatio)
            if best_match and best_match[1] > 70:
                return MatchResult(field_clean, best_match[0], best_match[1]/100.0, 'fuzzy')
                
        return MatchResult(field_clean, "", 0.0, 'none')

    def save_mapping(self, source: str, target: str):
        # 更新或新增映射
        found = False
        for item in self.knowledge_base:
            if item['source'] == source:
                item['target'] = target
                item['hits'] = item.get('hits', 0) + 1
                found = True
                break
        if not found:
            self.knowledge_base.append({'source': source, 'target': target, 'hits': 1})
        self._save_knowledge_base()
