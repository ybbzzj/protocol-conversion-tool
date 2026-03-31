# -*- coding: utf-8 -*-
"""
语义模型服务类 - 使用 PaddlePaddle ERNIE 3.0 Nano

ERNIE 3.0 Nano 优势：
- 语义理解能力强
- 模型文件约 500MB（分离部署，不打包进 exe）
- 支持中文语义匹配
"""
import os
import sys
import threading
import numpy as np


class EmbeddingService:
    '''
    PaddlePaddle ERNIE 3.0 Nano 语义模型服务类
    支持离线模型加载（模型文件与 exe 分离）
    '''
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
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # ERNIE 3.0 Nano 中文模型路径
        self.model_name = "ernie-3.0-nano-zh"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 兼容 exe 环境和开发环境
        if getattr(sys, 'frozen', False):
            # exe 环境：exe 所在目录
            model_path = os.path.join(os.path.dirname(sys.executable), 'models', self.model_name)
        else:
            # 开发环境：项目根目录
            model_path = os.path.join(base_dir, 'models', self.model_name)
        
        print(f"[EmbeddingService] 模型路径：{model_path}")
        
        try:
            print(f"[EmbeddingService] 正在加载 ERNIE 3.0 Nano 模型...")
            
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
            
            # 导入 PaddlePaddle
            import paddle
            from paddlenlp.transformers import AutoModel, AutoTokenizer
            
            print(f"[EmbeddingService] ✅ 检测到 PaddlePaddle 版本：{paddle.__version__}")
            
            # 在 exe 环境中，需要确保 libs 目录存在
            if getattr(sys, 'frozen', False):
                # exe 环境：创建空的 libs 目录（欺骗 Paddle）
                libs_dir = os.path.join(os.path.dirname(sys.executable), 'paddle', 'libs')
                if not os.path.exists(libs_dir):
                    os.makedirs(libs_dir, exist_ok=True)
                    print(f"[EmbeddingService] 💡 已创建 libs 目录：{libs_dir}")
            
            # 加载 tokenizer
            print(f"[EmbeddingService] 正在加载 Tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # 加载模型
            print(f"[EmbeddingService] 正在加载模型权重...")
            self._model = AutoModel.from_pretrained(model_path)
            self._model.eval()  # 设置为评估模式
            
            self._initialized = True
            self._available = True
            print("[EmbeddingService] ✅ ERNIE 3.0 Nano 模型加载成功！")
            
        except ImportError as e:
            print(f"[EmbeddingService] ❌ 错误：未安装 PaddlePaddle 或 PaddleNLP")
            print(f"[EmbeddingService] 💡 请运行以下命令安装依赖:")
            print(f"[EmbeddingService]    python -m pip install paddlepaddle==2.6.2 paddlenlp==2.6.1")
            print(f"[EmbeddingService] 📦 或者运行：install_paddle.bat (Windows)")
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

    def get_embedding(self, text):
        """将文本转换为向量"""
        if not self._available or not self._model or not self._tokenizer or not text:
            return None
        
        try:
            # 使用 ERNIE 获取句向量
            inputs = self._tokenizer(text, return_tensors='np', padding=True, truncation=True, max_length=128)
            outputs = self._model(**inputs)
            
            # 取 [CLS] token 的输出作为句向量
            sentence_vec = outputs.last_hidden_state[:, 0, :]
            return sentence_vec.flatten()
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
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)
    
    def is_available(self):
        """检查语义模型是否可用"""
        return self._available


# 全局单例
embedding_service = EmbeddingService()
