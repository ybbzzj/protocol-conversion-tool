# -*- coding: utf-8 -*-
"""
BGE Small 中文模型下载工具
用于下载 BAAI/bge-small-zh-v1.5 模型到本地
"""

import os
import sys
from typing import Dict, List, Optional


def _collect_proxies() -> Dict[str, str]:
    """从环境变量收集代理配置"""
    proxy_env_keys = [
        ('http', ['HF_HTTP_PROXY', 'HTTP_PROXY', 'http_proxy']),
        ('https', ['HF_HTTPS_PROXY', 'HTTPS_PROXY', 'https_proxy']),
    ]
    proxies: Dict[str, str] = {}

    for scheme, keys in proxy_env_keys:
        for key in keys:
            value = os.environ.get(key, '').strip()
            if value:
                # requests 需要带 scheme，若用户只填了 host:port，这里补上
                if '://' not in value:
                    value = f'http://{value}'
                proxies[scheme] = value
                break
    return proxies


def _attempt_snapshot_download(
    snapshot_download,
    repo_id: str,
    local_dir: str,
    allow_patterns: List[str],
    endpoint: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None,
) -> None:
    """执行一次下载尝试"""
    kwargs = {
        'repo_id': repo_id,
        'local_dir': local_dir,
        'local_dir_use_symlinks': False,
        'allow_patterns': allow_patterns,
        'resume_download': True,
    }
    if endpoint:
        kwargs['endpoint'] = endpoint
    if proxies:
        kwargs['proxies'] = proxies
    snapshot_download(**kwargs)

def download_model():
    """下载 BGE Small 中文模型"""
    hf_repo = "BAAI/bge-small-zh-v1.5"
    local_model_dir = "bge-small-zh-v1.5"

    print("=" * 60)
    print("BGE Small 中文模型下载工具")
    print("=" * 60)
    print()
    print(f"🎯 目标模型：{hf_repo}")
    print(f"📦 模型大小：约 100 MB")
    print()

    # 检查是否已安装 huggingface_hub
    try:
        import huggingface_hub
        from huggingface_hub import snapshot_download
        print(f"✅ huggingface_hub 版本：{huggingface_hub.__version__}")
    except ImportError as e:
        print("❌ 错误：未检测到 huggingface_hub")
        print("请先运行：pip install huggingface-hub==0.20.3")
        print(f"详细错误：{e}")
        return False

    # 检查是否已安装 transformers（下载后本地加载要用）
    try:
        import transformers
        print(f"✅ transformers 版本：{transformers.__version__}")
    except ImportError as e:
        print("❌ 错误：未检测到 transformers")
        print("请先运行：pip install transformers==4.30.2")
        print(f"详细错误：{e}")
        return False

    # 确定模型保存路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, 'models', local_model_dir)

    # 尝试的下载端点（按顺序）
    env_endpoint = os.environ.get('HF_ENDPOINT', '').strip()
    endpoints = []
    if env_endpoint:
        endpoints.append(env_endpoint)
    # 官方端点
    endpoints.append("https://huggingface.co")
    # 国内常用镜像端点
    endpoints.append("https://hf-mirror.com")
    # 去重但保留顺序
    dedup_endpoints = []
    for ep in endpoints:
        if ep and ep not in dedup_endpoints:
            dedup_endpoints.append(ep)
    endpoints = dedup_endpoints

    proxies = _collect_proxies()

    required_files = [
        "config.json",
        "model.safetensors",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
    ]

    if os.path.exists(save_dir):
        print(f"⚠️  模型目录已存在：{save_dir}")
        if all(os.path.exists(os.path.join(save_dir, f)) for f in required_files):
            print("✅ 模型文件完整，无需重新下载")
            return True
        print("⚠️  模型文件不完整，将重新下载")
    
    # 创建目录
    os.makedirs(save_dir, exist_ok=True)

    print(f"📥 开始下载模型...")
    print(f"📁 保存位置：{save_dir}")
    print()
    print("💡 说明：会从 Hugging Face 下载文件，请保持网络稳定...")
    print(f"🌐 下载端点顺序：{endpoints}")
    if proxies:
        print(f"🔌 检测到代理配置：{proxies}")
    else:
        print("🔌 未检测到代理配置")
    print()

    try:
        # 仅下载本地推理所需文件，减少体积
        allow_patterns = [
            "config.json",
            "model.safetensors",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.txt",
            "tokenizer.json",
        ]

        download_ok = False
        last_error = None
        for endpoint in endpoints:
            try:
                print(f"➡️  尝试端点：{endpoint}")
                _attempt_snapshot_download(
                    snapshot_download=snapshot_download,
                    repo_id=hf_repo,
                    local_dir=save_dir,
                    allow_patterns=allow_patterns,
                    endpoint=endpoint,
                    proxies=proxies if proxies else None,
                )
                download_ok = True
                print(f"✅ 端点下载成功：{endpoint}")
                break
            except Exception as e:
                last_error = e
                print(f"⚠️ 端点失败：{endpoint}")
                print(f"   错误：{e}")

                # 如果是代理错误，自动重试一次（不使用代理）
                if proxies and ('ProxyError' in str(e) or 'proxy' in str(e).lower()):
                    try:
                        print("↩️ 检测到代理错误，尝试同端点直连下载...")
                        _attempt_snapshot_download(
                            snapshot_download=snapshot_download,
                            repo_id=hf_repo,
                            local_dir=save_dir,
                            allow_patterns=allow_patterns,
                            endpoint=endpoint,
                            proxies=None,
                        )
                        download_ok = True
                        print(f"✅ 端点直连下载成功：{endpoint}")
                        break
                    except Exception as e2:
                        last_error = e2
                        print(f"⚠️ 直连重试失败：{e2}")

        if not download_ok:
            raise RuntimeError(f"所有端点均下载失败，最后错误：{last_error}")

        missing = [f for f in required_files if not os.path.exists(os.path.join(save_dir, f))]
        if missing:
            print(f"❌ 下载后仍缺少关键文件：{missing}")
            return False

        print()
        print("=" * 60)
        print("✅ 模型下载完成！")
        print(f"📦 模型位置：{save_dir}")
        print("=" * 60)
        print()
        print("💡 使用说明:")
        print("   1. 模型文件已保存到 models 目录")
        print("   2. 打包时，需要将整个 models 文件夹与 exe 一起提供")
        print("   3. 程序运行时会自动从该目录加载模型")
        print("   4. 客户部署时，确保 models 目录与 exe 在同一层级")
        print()
        print("📂 部署结构:")
        print("   协议转换工具/")
        print("   ├── 协议转换工具.exe")
        print("   └── models/")
        print("       └── bge-small-zh-v1.5/")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 模型下载失败：{e}")
        print("=" * 60)
        print()
        print("可能的原因:")
        print("  1. 网络连接问题")
        print("  2. 代理配置不可用（建议先清理 HTTP_PROXY/HTTPS_PROXY）")
        print("  3. 磁盘空间不足")
        print("  4. 当前网络无法访问 huggingface.co，可尝试 HF_ENDPOINT=https://hf-mirror.com")
        print()
        
        # 清理未完成的下载
        if os.path.exists(save_dir):
            import shutil
            shutil.rmtree(save_dir)
            print(f"已清理未完成的下载：{save_dir}")

        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
