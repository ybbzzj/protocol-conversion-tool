# -*- coding: utf-8 -*-
"""
语义模型下载工具（ONNX 版本）

默认下载:
    Xenova/bge-small-zh-v1.5
到本地目录:
    ./models/bge-small-zh-v1.5
"""
import argparse
import os
import sys


DEFAULT_REPO = "Xenova/bge-small-zh-v1.5"
DEFAULT_DIRNAME = "bge-small-zh-v1.5"


def _required_files(onnx_file: str):
    return [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
        onnx_file,
    ]


def _validate_download(target_dir: str, required_files):
    missing = []
    for rel_path in required_files:
        full_path = os.path.join(target_dir, rel_path)
        if not os.path.exists(full_path):
            missing.append(rel_path)
    return missing


def download_model(repo_id: str, target_dir: str, onnx_file: str):
    print("=" * 68)
    print("语义模型下载工具（ONNX）")
    print("=" * 68)
    print(f"模型仓库: {repo_id}")
    print(f"保存目录: {target_dir}")
    print(f"ONNX文件: {onnx_file}")
    print()

    try:
        from huggingface_hub import snapshot_download
    except ImportError as e:
        print("❌ 未安装 huggingface-hub")
        print("请先执行: pip install huggingface-hub==0.17.3")
        print("详细错误:", e)
        return False

    required_files = _required_files(onnx_file)

    print("将下载以下关键文件:")
    for rf in required_files:
        print(f"  - {rf}")
    print()

    os.makedirs(target_dir, exist_ok=True)

    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
            allow_patterns=required_files
        )
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print("提示: 如在中国大陆网络环境，可设置 HF_ENDPOINT 后重试。")
        print("例如: set HF_ENDPOINT=https://hf-mirror.com")
        return False

    missing = _validate_download(target_dir, required_files)
    if missing:
        print("❌ 下载不完整，缺少以下文件:")
        for item in missing:
            print(f"  - {item}")
        return False

    onnx_path = os.path.join(target_dir, onnx_file)
    size_mb = os.path.getsize(onnx_path) / (1024 * 1024)

    print()
    print("=" * 68)
    print("✅ 模型下载完成")
    print(f"目录: {target_dir}")
    print(f"ONNX大小: {size_mb:.1f} MB")
    print("=" * 68)
    print()
    print("部署结构示例:")
    print("  协议转换工具/")
    print("  ├── 协议转换工具.exe")
    print("  └── models/")
    print(f"      └── {os.path.basename(target_dir)}/")
    print(f"          └── {onnx_file}")
    return True


def main():
    parser = argparse.ArgumentParser(description="下载语义模型（ONNX）")
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"模型仓库（默认: {DEFAULT_REPO}）")
    parser.add_argument("--target", default=None, help="目标目录（默认: ./models/bge-small-zh-v1.5）")
    parser.add_argument("--onnx-file", default="onnx/model.onnx", help="ONNX模型相对路径（默认: onnx/model.onnx）")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = args.target or os.path.join(base_dir, "models", DEFAULT_DIRNAME)

    success = download_model(args.repo, target_dir, args.onnx_file)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
