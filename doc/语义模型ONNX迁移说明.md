# 语义模型 ONNX 迁移说明

## 1. 迁移目标
- 从 `PaddlePaddle + ERNIE` 迁移为 `ONNX Runtime + 本地Tokenizer`。
- 保留离线部署能力，模型与 EXE 分离，避免运行端联网。

## 2. 推荐模型
- 默认仓库：`Xenova/bge-small-zh-v1.5`
- 默认目录：`models/bge-small-zh-v1.5-onnx`
- 关键文件：
  - `config.json`
  - `tokenizer.json`
  - `vocab.txt`
  - `onnx/model.onnx`（或 `onnx/model_int8.onnx`）

## 3. 下载模型
```bash
python download_model.py
```

可选参数：
```bash
python download_model.py --repo Xenova/bge-small-zh-v1.5 --onnx-file onnx/model_int8.onnx
```

## 4. 打包 EXE
```bat
build_exe.bat
```

打包后部署结构：
```text
协议转换工具/
├── 协议转换工具.exe
└── models/
    └── bge-small-zh-v1.5-onnx/
```

## 5. 匹配策略优先级
1. 精确匹配
2. 别名匹配
3. 语义匹配（ONNX）
4. 模糊匹配

语义模型不可用时会自动降级为规则匹配，不影响主流程。
