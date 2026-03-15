from paddlenlp.transformers import AutoModel, AutoTokenizer
import paddle.nn.functional as F
import paddle

# 1. 加载本地模型（第一次运行会自动下载到本地缓存）
model_name = "ernie-3.0-nano-zh" # 极其轻量的版本
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
def get_embedding(text):
    # 将文本转换为向量
    inputs = tokenizer(text, return_tensors="pd")
    outputs = model(**inputs)
    # 取 [CLS] 向量作为句向量
    return outputs[0][:, 0, :]

# 2. 计算两个字段的语义相似度
vec1 = get_embedding("时间戳")
vec2 = get_embedding("时标")

# 计算余弦相似度
similarity = F.cosine_similarity(vec1, vec2).item()
print(f"“时间戳” 与 “时标” 的语义相似度为: {similarity:.4f}")
# 测试结果：“时间戳” 与 “时标” 的语义相似度为: 0.8875