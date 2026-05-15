# -*- coding: utf-8 -*-
"""
语义模型服务类（ONNX 轻量方案）

默认模型目录:
    models/bge-small-zh-v1.5-onnx/
        tokenizer.json
        vocab.txt
        config.json
        onnx/model.onnx
"""
import os
import sys
import threading
from collections import OrderedDict
from typing import Iterable, Optional

import numpy as np


class EmbeddingService:
    """
    ONNX 语义模型服务类（离线可部署，适合 PyInstaller）
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EmbeddingService, cls).__new__(cls)
                cls._instance._initialized = False
                cls._instance._available = False
                cls._instance._tokenizer = None
                cls._instance._session = None
                cls._instance._input_names = []
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.model_name = "bge-small-zh-v1.5-onnx"
        self.model_repo = "Xenova/bge-small-zh-v1.5"
        self.max_length = 64
        self._cache_max_size = 3000
        self._embedding_cache = OrderedDict()
        self._cache_lock = threading.Lock()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if getattr(sys, 'frozen', False):
            default_model_path = os.path.join(os.path.dirname(sys.executable), 'models', self.model_name)
        else:
            default_model_path = os.path.join(base_dir, 'models', self.model_name)

        self.model_path = os.environ.get("SEMANTIC_MODEL_DIR", default_model_path)
        self.onnx_model_path = self._resolve_onnx_model_path(self.model_path)

        print(f"[EmbeddingService] 模型目录：{self.model_path}")

        try:
            if not os.path.isdir(self.model_path):
                print(f"[EmbeddingService] ⚠️ 未找到模型目录：{self.model_path}")
                self._set_unavailable()
                return

            if not self.onnx_model_path:
                print(f"[EmbeddingService] ⚠️ 未找到 ONNX 模型文件（model.onnx）")
                self._set_unavailable()
                return

            from transformers import AutoTokenizer
            import onnxruntime as ort

            print("[EmbeddingService] 正在加载 Tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                local_files_only=True,
                use_fast=True
            )

            print("[EmbeddingService] 正在加载 ONNX 模型...")
            sess_options = ort.SessionOptions()
            self._session = ort.InferenceSession(
                self.onnx_model_path,
                sess_options=sess_options,
                providers=["CPUExecutionProvider"]
            )
            self._input_names = [i.name for i in self._session.get_inputs()]

            self._available = True
            self._initialized = True
            print("[EmbeddingService] ✅ ONNX 语义模型加载成功")
        except ImportError as e:
            print("[EmbeddingService] ❌ 缺少依赖，请安装 onnxruntime 和 transformers")
            print("[EmbeddingService] 详细错误:", e)
            self._set_unavailable()
        except Exception as e:
            print(f"[EmbeddingService] ❌ 模型加载失败：{e}")
            import traceback
            traceback.print_exc()
            self._set_unavailable()

    @staticmethod
    def _resolve_onnx_model_path(model_dir: str) -> Optional[str]:
        """解析 ONNX 模型路径（支持多个常见文件名）"""
        candidates = [
            os.path.join(model_dir, "onnx", "model.onnx"),
            os.path.join(model_dir, "onnx", "model_int8.onnx"),
            os.path.join(model_dir, "onnx", "model_quantized.onnx"),
            os.path.join(model_dir, "model.onnx"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _set_unavailable(self):
        self._tokenizer = None
        self._session = None
        self._input_names = []
        self._available = False
        self._initialized = True

    @staticmethod
    def _norm_text(text: str) -> str:
        if text is None:
            return ""
        return str(text).strip()

    def _build_onnx_inputs(self, text: str):
        encoded = self._tokenizer(
            text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=self.max_length
        )
        onnx_inputs = {}
        for name in self._input_names:
            if name in encoded:
                onnx_inputs[name] = encoded[name].astype(np.int64)
            elif name == "token_type_ids":
                onnx_inputs[name] = np.zeros_like(encoded["input_ids"], dtype=np.int64)
            elif name == "attention_mask":
                onnx_inputs[name] = np.ones_like(encoded["input_ids"], dtype=np.int64)
        return onnx_inputs

    @staticmethod
    def _normalize_vector(vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec) + 1e-12
        return vec / norm

    def _pool_output(self, outputs, onnx_inputs) -> Optional[np.ndarray]:
        if not outputs:
            return None

        token_embeddings = outputs[0]
        if isinstance(token_embeddings, list):
            token_embeddings = np.array(token_embeddings)

        if token_embeddings.ndim == 2:
            vec = token_embeddings[0]
            return self._normalize_vector(vec.astype(np.float32))

        if token_embeddings.ndim != 3:
            return None

        attn_mask = onnx_inputs.get("attention_mask")
        if attn_mask is None:
            vec = token_embeddings.mean(axis=1)[0]
            return self._normalize_vector(vec.astype(np.float32))

        mask = attn_mask.astype(np.float32)[:, :, None]
        masked_sum = (token_embeddings * mask).sum(axis=1)
        token_count = np.clip(mask.sum(axis=1), 1e-9, None)
        vec = (masked_sum / token_count)[0]
        return self._normalize_vector(vec.astype(np.float32))

    def _get_from_cache(self, key: str) -> Optional[np.ndarray]:
        with self._cache_lock:
            cached = self._embedding_cache.get(key)
            if cached is None:
                return None
            self._embedding_cache.move_to_end(key)
            return cached

    def _save_to_cache(self, key: str, vec: np.ndarray):
        with self._cache_lock:
            self._embedding_cache[key] = vec
            self._embedding_cache.move_to_end(key)
            if len(self._embedding_cache) > self._cache_max_size:
                self._embedding_cache.popitem(last=False)

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """将文本转换为单位向量"""
        if not self._available or self._session is None or self._tokenizer is None:
            return None

        key = self._norm_text(text)
        if not key:
            return None

        cached = self._get_from_cache(key)
        if cached is not None:
            return cached

        try:
            onnx_inputs = self._build_onnx_inputs(key)
            outputs = self._session.run(None, onnx_inputs)
            vec = self._pool_output(outputs, onnx_inputs)
            if vec is None:
                return None
            self._save_to_cache(key, vec)
            return vec
        except Exception as e:
            print(f"[EmbeddingService] 获取向量失败：{e}")
            return None

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的余弦相似度"""
        vec1 = self.get_embedding(text1)
        vec2 = self.get_embedding(text2)
        if vec1 is None or vec2 is None:
            return 0.0
        similarity = float(np.dot(vec1, vec2))
        return max(min(similarity, 1.0), -1.0)

    def warmup(self, texts: Iterable[str], max_items: int = 200):
        """预热常用字段向量，减少首次匹配时延"""
        if not self.is_available():
            return
        count = 0
        for t in texts:
            if count >= max_items:
                break
            if t:
                self.get_embedding(t)
                count += 1

    def is_available(self) -> bool:
        return self._available


# 全局单例
embedding_service = EmbeddingService()
