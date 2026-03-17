# -*- coding: utf-8 -*-
import os
import threading
import paddle
import paddle.nn.functional as F
from paddlenlp.transformers import AutoModel, AutoTokenizer

class EmbeddingService:
    '''
    语义模型服务类，负责加载和提供文本嵌入向量。
    '''
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EmbeddingService, cls).__new__(cls)
                cls._instance._initialized = False
                cls._instance._embedding_cache = {} # 增加缓存
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # baidu ernie-3.0-nano-zh 模型
        self.model_name = "ernie-3.0-nano-zh"
        
        # ✅ 增加离线路径检测
        # 默认模型存放位置：项目根目录/models/ernie-3.0-nano-zh
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        offline_path = os.path.join(base_dir, 'models', self.model_name)
        
        if os.path.exists(offline_path):
            print(f"[EmbeddingService] 检测到离线模型，正在加载: {offline_path}")
            load_target = offline_path
        else:
            print(f"[EmbeddingService] 正在从云端初始化语义模型: {self.model_name}...")
            load_target = self.model_name
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(load_target)
            self.model = AutoModel.from_pretrained(load_target)
            self.model.eval() # 设置为评估模式
            self._initialized = True
            print("[EmbeddingService] 模型初始化成功")
        except Exception as e:
            print(f"[EmbeddingService] 模型加载失败: {e}")
            self._initialized = False

    def get_embedding(self, text):
        """将文本转换为向量"""
        if not self._initialized or not text:
            return None
            
        # 检查缓存
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        with paddle.no_grad():
            inputs = self.tokenizer(text, return_tensors="pd")
            outputs = self.model(**inputs)
            # 取 [CLS] 向量作为句向量
            embedding = outputs[0][:, 0, :]
            
            # 存入缓存
            self._embedding_cache[text] = embedding
            return embedding

    def calculate_similarity(self, text1, text2):
        """计算两个文本的余弦相似度"""
        vec1 = self.get_embedding(text1)
        vec2 = self.get_embedding(text2)
        
        if vec1 is None or vec2 is None:
            return 0.0
            
        similarity = F.cosine_similarity(vec1, vec2).item()
        return similarity

# 全局单例
embedding_service = EmbeddingService()
