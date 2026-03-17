from paddlenlp.transformers import AutoModel, AutoTokenizer
model_name = "ernie-3.0-nano-zh"
save_path = "./models/ernie-3.0-nano-zh"

# 下载并保存
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)
print(f"模型已保存至: {save_path}")