# -*- coding: utf-8 -*-
"""
增强版字段匹配器
支持精确匹配、模糊匹配、语义匹配和人工修正
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from backend.config import Config
from backend.services.embedding_service import embedding_service

class EnhancedFieldMatcher:
    """增强字段匹配器"""
    
    def __init__(self):
        self.knowledge_base_file = Config.KNOWLEDGE_BASE_PATH
        self.knowledge_base = self._load_knowledge_base()
        self.similarity_threshold = 0.7
        self.semantic_threshold = 0.8  # 语义匹配阈值
        self.standard_fields = self._get_standard_fields()
        
        # 预计算标准字段向量以加速匹配
        self._preload_standard_embeddings()
        
        # 匹配结果缓存，避免同一字段在多行中重复计算
        self._match_cache = {}

    def _preload_standard_embeddings(self):
        """预先计算所有标准字段的向量"""
        if not self.standard_fields:
            return
        
        # 只需要触发一次，后续会从 EmbeddingService 的缓存中读取
        print(f"[FieldMatcher] 预计算 {len(self.standard_fields)} 个标准字段向量...")
        for field in self.standard_fields:
            embedding_service.get_embedding(field)
        
    def _load_knowledge_base(self) -> List[Dict]:
        """加载知识库"""
        try:
            if os.path.exists(self.knowledge_base_file):
                with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('mappings', [])
            return []
        except Exception as e:
            print(f"[知识库加载] 错误: {e}")
            return []
    
    def _save_knowledge_base(self):
        """保存知识库"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.knowledge_base_file), exist_ok=True)
            
            data = {
                'mappings': self.knowledge_base,
                'updated_at': __import__('datetime').datetime.now().isoformat()
            }
            
            with open(self.knowledge_base_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[知识库保存] 错误: {e}")
    
    def _get_standard_fields(self) -> List[str]:
        """获取标准字段列表"""
        # 从配置文件加载标准字段
        try:
            protocol_config = Config.PROTOCOL_FIELDS_PATH
            target_config = Config.TARGET_FIELDS_PATH
            
            standard_fields = set()
            
            # 加载协议字段
            if os.path.exists(protocol_config):
                with open(protocol_config, 'r', encoding='utf-8') as f:
                    protocol_data = json.load(f)
                    # 检查数据格式
                    if isinstance(protocol_data, list):
                        # 数组格式
                        for field in protocol_data:
                            if isinstance(field, dict) and 'name' in field:
                                standard_fields.add(field['name'])
                    elif isinstance(protocol_data, dict) and 'protocolFields' in protocol_data:
                        # 对象格式
                        for field in protocol_data['protocolFields']:
                            standard_fields.add(field['name'])
            
            # 加载目标字段
            if os.path.exists(target_config):
                with open(target_config, 'r', encoding='utf-8') as f:
                    target_data = json.load(f)
                    # 检查数据格式
                    if isinstance(target_data, list):
                        # 数组格式
                        for field in target_data:
                            if isinstance(field, dict) and 'name' in field:
                                standard_fields.add(field['name'])
                    elif isinstance(target_data, dict) and 'targetFields' in target_data:
                        # 对象格式
                        for field in target_data['targetFields']:
                            standard_fields.add(field['name'])
            
            return list(standard_fields)
        except Exception as e:
            print(f"[标准字段加载] 错误: {e}")
            # 返回默认标准字段
            return [
                '序号', '参数', '内容', '信号名称', '数据类型', '类型', 
                '长度', '字节', '单位', '备注', '值域', '信源', '信宿', 
                '信息内容', '消息ID', '接口名称', '时间戳', '转换类型'
            ]
    
    def match_with_context(self, extracted_fields: List[str], context: str = None) -> List[Dict]:
        """
        带上下文的字段匹配
        
        Args:
            extracted_fields: 提取的原始字段列表
            context: 文档上下文信息
            
        Returns:
            匹配结果列表
        """
        results = []
        
        for field in extracted_fields:
            # 0. 检查缓存
            if field in self._match_cache:
                results.append(self._match_cache[field])
                continue

            # 1. 精确匹配
            exact = self._exact_match(field)
            if exact:
                res = {
                    'original': field,
                    'matched': exact['target'],
                    'confidence': exact['confidence'],
                    'type': 'exact',
                    'source': exact.get('source', 'knowledge_base')
                }
                self._match_cache[field] = res
                results.append(res)
                continue
            
            # 2. 语义匹配 (新增)
            semantic = self._semantic_match(field)
            if semantic:
                res = {
                    'original': field,
                    'matched': semantic['target'],
                    'confidence': semantic['confidence'],
                    'type': 'semantic',
                    'source': 'ernie_3.0_nano'
                }
                self._match_cache[field] = res
                results.append(res)
                continue
            
            # 3. 模糊匹配
            fuzzy = self._fuzzy_match(field)
            if fuzzy:
                # 如果模糊匹配返回的是 exact_match，则使用 exact 类型
                match_type = 'exact' if fuzzy.get('source') == 'exact_match' else 'fuzzy'
                res = {
                    'original': field,
                    'matched': fuzzy['target'],
                    'confidence': fuzzy['confidence'],
                    'type': match_type,
                    'similarity': fuzzy['similarity'],
                    'source': fuzzy.get('source', 'fuzzy_match')
                }
                self._match_cache[field] = res
                results.append(res)
                continue
            
            # 4. 别名匹配
            alias = self._alias_match(field)
            if alias:
                res = {
                    'original': field,
                    'matched': alias['target'],
                    'confidence': alias['confidence'],
                    'type': 'alias',
                    'source': 'alias_mapping'
                }
                self._match_cache[field] = res
                results.append(res)
                continue
            
            # 5. 未匹配字段
            res = {
                'original': field,
                'matched': None,
                'confidence': 0.0,
                'type': 'unmatched',
                'suggestions': self._get_suggestions_for_field(field)
            }
            self._match_cache[field] = res
            results.append(res)
        
        return results
    
    def _exact_match(self, field: str) -> Optional[Dict]:
        """精确匹配"""
        # 在知识库中查找
        for item in self.knowledge_base:
            if item.get('source') == field and item.get('confidence', 0) >= 0.9:
                return {
                    'target': item['target'],
                    'confidence': item['confidence'],
                    'source': 'knowledge_base'
                }
        return None
    
    def _semantic_match(self, field: str) -> Optional[Dict]:
        """语义匹配"""
        best_match = None
        best_score = 0
        
        for std_field in self.standard_fields:
            # 调用语义服务计算相似度
            score = embedding_service.calculate_similarity(field, std_field)
            
            if score > best_score and score >= self.semantic_threshold:
                best_score = score
                best_match = {
                    'target': std_field,
                    'confidence': score,
                    'source': 'ernie_3.0_nano'
                }
        
        return best_match

    def _fuzzy_match(self, field: str) -> Optional[Dict]:
        """模糊匹配"""
        best_match = None
        best_similarity = 0
        
        for std_field in self.standard_fields:
            similarity = SequenceMatcher(None, field, std_field).ratio()
            # 如果字段完全相同，视为精确匹配
            if field == std_field:
                return {
                    'target': std_field,
                    'confidence': 1.0,
                    'similarity': 1.0,
                    'source': 'exact_match'
                }
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = {
                    'target': std_field,
                    'confidence': similarity,
                    'similarity': similarity,
                    'source': 'fuzzy_match'
                }
        
        return best_match
    
    def _alias_match(self, field: str) -> Optional[Dict]:
        """别名匹配"""
        # 常见字段别名映射
        aliases = {
            '参数名称': '参数',
            '字段名': '参数',
            '变量名': '参数',
            '时间': '时间戳',
            '时标': '时间戳',
            'timestamp': '时间戳',
            '类型说明': '数据类型',
            '格式': '数据类型',
            '数据格式': '数据类型',
            '单位说明': '单位',
            '备注说明': '备注',
            '取值范围': '值域',
            '范围': '值域'
        }
        
        # 直接别名匹配
        if field in aliases:
            return {
                'target': aliases[field],
                'confidence': 0.95,
                'source': 'alias_mapping'
            }
        
        # 模糊别名匹配
        for alias, target in aliases.items():
            if SequenceMatcher(None, field, alias).ratio() > 0.8:
                return {
                    'target': target,
                    'confidence': 0.85,
                    'source': 'fuzzy_alias'
                }
        
        return None
    
    def _get_suggestions_for_field(self, field: str) -> List[Dict]:
        """为未匹配字段获取建议"""
        suggestions = []
        
        # 基于相似度的建议
        for std_field in self.standard_fields:
            similarity = SequenceMatcher(None, field, std_field).ratio()
            if similarity > 0.6:
                suggestions.append({
                    'field': std_field,
                    'similarity': similarity,
                    'confidence': similarity
                })
        
        # 基于知识库的建议
        for item in self.knowledge_base:
            similarity = SequenceMatcher(None, field, item['source']).ratio()
            if similarity > 0.7:
                suggestions.append({
                    'field': item['target'],
                    'similarity': similarity,
                    'confidence': item['confidence'],
                    'source': 'knowledge_base'
                })
        
        # 按相似度排序并限制数量
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        return suggestions[:5]
    
    def get_detailed_suggestions(self, fields: List[str]) -> Dict[str, Any]:
        """获取详细的匹配建议"""
        results = {
            'exact_matches': [],
            'fuzzy_matches': [],
            'alias_matches': [],
            'unmatched': []
        }
        
        for field in fields:
            exact = self._exact_match(field)
            if exact:
                results['exact_matches'].append({
                    'original': field,
                    'matched': exact,
                    'type': 'exact'
                })
                continue
            
            fuzzy = self._fuzzy_match(field)
            if fuzzy:
                results['fuzzy_matches'].append({
                    'original': field,
                    'matched': fuzzy,
                    'type': 'fuzzy'
                })
                continue
            
            alias = self._alias_match(field)
            if alias:
                results['alias_matches'].append({
                    'original': field,
                    'matched': alias,
                    'type': 'alias'
                })
                continue
            
            results['unmatched'].append({
                'original': field,
                'suggestions': self._get_suggestions_for_field(field)
            })
        
        return results
    
    def save_mapping(self, source: str, target: str, table_id: str = 'default', confidence: float = 0.8):
        """
        保存字段映射到知识库
        
        Args:
            source: 源字段名
            target: 目标字段名
            table_id: 表标识
            confidence: 置信度
        """
        # 检查是否已存在
        existing_idx = None
        for i, item in enumerate(self.knowledge_base):
            if item.get('source') == source and item.get('table_id') == table_id:
                existing_idx = i
                break
        
        mapping_item = {
            'source': source,
            'target': target,
            'table_id': table_id,
            'confidence': confidence,
            'hits': 1,
            'created_at': __import__('datetime').datetime.now().isoformat()
        }
        
        if existing_idx is not None:
            # 更新现有记录
            self.knowledge_base[existing_idx]['hits'] += 1
            self.knowledge_base[existing_idx]['confidence'] = max(
                self.knowledge_base[existing_idx]['confidence'], 
                confidence
            )
        else:
            # 添加新记录
            self.knowledge_base.append(mapping_item)
        
        # 保存到文件
        self._save_knowledge_base()
    
    def match_field(self, source_field: str, table_id: str = None, context: str = None) -> Dict[str, Any]:
        """
        兼容旧版FieldMatcher的match_field方法
        用于单个字段匹配，返回匹配结果
        
        Args:
            source_field: 源字段名
            table_id: 可选的表ID
            context: 可选的上下文信息
            
        Returns:
            匹配结果字典
        """
        # 使用新的匹配方法
        results = self.match_with_context([source_field], context)
        if results:
            result = results[0]
            return {
                'target': result['matched'],
                'confidence': result['confidence'],
                'match_type': result['type'],
                'source_field': result['original']
            }
        else:
            return {
                'target': None,
                'confidence': 0.0,
                'match_type': 'unmatched',
                'source_field': source_field
            }
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """获取映射统计信息"""
        total_mappings = len(self.knowledge_base)
        exact_count = len([m for m in self.knowledge_base if m.get('confidence', 0) >= 0.9])
        fuzzy_count = len([m for m in self.knowledge_base if 0.7 <= m.get('confidence', 0) < 0.9])
        low_confidence_count = len([m for m in self.knowledge_base if m.get('confidence', 0) < 0.7])
        
        # 按表ID统计
        table_stats = {}
        for item in self.knowledge_base:
            table_id = item.get('table_id', 'default')
            table_stats[table_id] = table_stats.get(table_id, 0) + 1
        
        return {
            'total_mappings': total_mappings,
            'exact_matches': exact_count,
            'fuzzy_matches': fuzzy_count,
            'low_confidence': low_confidence_count,
            'by_table': table_stats,
            'standard_fields_count': len(self.standard_fields)
        }
    
    def suggest_with_context(self, source_field: str, context: Dict = None) -> List[Dict]:
        """
        为字段获取匹配建议
        
        Args:
            source_field: 源字段名
            context: 上下文信息，包含 available_targets 等
            
        Returns:
            建议列表
        """
        suggestions = []
        available_targets = context.get('available_targets', []) if context else []
        
        # 如果没有指定目标字段，使用所有标准字段
        targets = available_targets if available_targets else self.standard_fields
        
        # 计算与每个目标字段的相似度
        for target in targets:
            similarity = self._calculate_similarity(source_field, target)
            if similarity > 0.5:  # 只返回相似度大于0.5的建议
                suggestions.append({
                    'field': target,
                    'similarity': similarity,
                    'reason': '相似度匹配'
                })
        
        # 按相似度排序
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        return suggestions[:5]  # 最多返回5个建议
    
    def _calculate_similarity(self, source: str, target: str) -> float:
        """
        计算两个字段的相似度
        
        Args:
            source: 源字段
            target: 目标字段
            
        Returns:
            相似度 (0.0 - 1.0)
        """
        from difflib import SequenceMatcher
        
        # 完全匹配
        if source == target:
            return 1.0
        
        # 忽略大小写的匹配
        if source.lower() == target.lower():
            return 0.95
        
        # 计算序列相似度
        similarity = SequenceMatcher(None, source, target).ratio()
        
        # 检查知识库
        kb_match = self._exact_match(source)
        if kb_match and kb_match.get('target') == target:
            return max(similarity, kb_match.get('confidence', 0.9))
        
        return similarity