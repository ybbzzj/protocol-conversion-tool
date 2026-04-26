# -*- coding: utf-8 -*-
"""
语义模型服务类 - 使用 BGE Small 中文模型 (bge-small-zh-v1.5)

BGE Small 优势：
- 语义理解能力稳定
- 模型文件约 100MB（分离部署，不打包进 exe）
- 支持中文语义匹配
"""
import os
import sys
import threading
import numpy as np


class EmbeddingService:
    """BGE Small 中文语义模型服务类"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EmbeddingService, cls).__new__(cls)
                cls._instance._initialized = False
                cls._instance._available = False
                cls._instance._model = None
                cls._instance._tokenizer = None
                cls._instance._embedding_cache = {}
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # BGE Small 中文模型路径
        self.model_name = "bge-small-zh-v1.5"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # 兼容 exe 环境和开发环境
        if getattr(sys, 'frozen', False):
            # exe 环境：exe 所在目录
            model_path = os.path.join(os.path.dirname(sys.executable), 'models', self.model_name)
        else:
            # 开发环境：项目根目录
            model_path = os.path.join(base_dir, 'models', self.model_name)

        self.model_path = model_path
        print(f"[EmbeddingService] 模型路径：{model_path}")

        try:
            print("[EmbeddingService] 正在加载 BGE Small 中文模型...")

            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                print(f"[EmbeddingService] ⚠️  未找到模型文件：{model_path}")
                print(f"[EmbeddingService] 📥 请运行以下命令下载模型：")
                print(f"[EmbeddingService]    python download_model.py")
                print(f"[EmbeddingService] 💡 或者手动下载模型并放到：{model_path}")
                self._model = None
                self._tokenizer = None
                self._initialized = True
                self._available = False
                return

            # 导入 Transformers + PyTorch
            import torch
            from transformers import AutoModel, AutoTokenizer

            print(f"[EmbeddingService] ✅ 检测到 PyTorch 版本：{torch.__version__}")

            # 加载 tokenizer
            print(f"[EmbeddingService] 正在加载 Tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)

            # 加载模型
            print(f"[EmbeddingService] 正在加载模型权重...")
            self._model = AutoModel.from_pretrained(model_path)
            self._model.eval()  # 设置为评估模式

            self._initialized = True
            self._available = True
            print("[EmbeddingService] ✅ BGE Small 中文模型加载成功！")

        except ImportError as e:
            print(f"[EmbeddingService] ❌ 错误：未安装 PyTorch 或 Transformers")
            print(f"[EmbeddingService] 💡 请运行以下命令安装依赖:")
            print(f"[EmbeddingService]    python -m pip install torch==1.13.1 transformers==4.30.2")
            print(f"[EmbeddingService] 详细错误：{e}")
            self._model = None
            self._tokenizer = None
            self._initialized = True
            self._available = False
        except Exception as e:
            print(f"[EmbeddingService] ❌ 模型加载失败：{e}")
            import traceback
            traceback.print_exc()
            self._model = None
            self._tokenizer = None
            self._initialized = True
            self._available = False

    def get_embedding(self, text: str):
        """将文本转换为向量"""
        if not self._available or not self._model or not self._tokenizer:
            return None
        if not text:
            return None

        text = str(text).strip()
        if not text:
            return None

        if text in self._embedding_cache:
            return self._embedding_cache[text]

        try:
            import torch

            # BGE 推荐句向量前缀
            encoded_text = f"query: {text}"
            inputs = self._tokenizer(
                encoded_text,
                return_tensors='pt',
                truncation=True,
                padding=True,
                max_length=64
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
                token_embeddings = outputs.last_hidden_state
                attention_mask = inputs['attention_mask'].unsqueeze(-1).expand(token_embeddings.size()).float()
                sum_embeddings = (token_embeddings * attention_mask).sum(dim=1)
                sum_mask = attention_mask.sum(dim=1).clamp(min=1e-9)
                sentence_vec = sum_embeddings / sum_mask
                sentence_vec = sentence_vec.squeeze(0).cpu().numpy().astype(np.float32)

            norm = np.linalg.norm(sentence_vec)
            if norm > 0:
                sentence_vec = sentence_vec / norm

            self._embedding_cache[text] = sentence_vec
            return sentence_vec
        except Exception as e:
            print(f"[EmbeddingService] 获取向量失败：{e}")
            return None

    def calculate_similarity(self, text1, text2):
        """计算两个文本的余弦相似度"""
        vec1 = self.get_embedding(text1)
        vec2 = self.get_embedding(text2)
        
        if vec1 is None or vec2 is None:
            return 0.0

        # 余弦相似度计算
        denominator = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        if denominator == 0:
            return 0.0
        similarity = float(np.dot(vec1, vec2) / denominator)
        # 数值稳定性处理
        return max(min(similarity, 1.0), -1.0)

    def is_available(self):
        """检查语义模型是否可用"""
        return self._available


# 全局单例
embedding_service = EmbeddingService()
