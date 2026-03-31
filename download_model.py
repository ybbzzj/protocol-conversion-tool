
# -*- coding: utf-8 -*-
"""
PaddleNLP 模型下载工具
用于下载 ernie-3.0-nano-zh 模型到本地
"""

import os
import sys

def download_model():
    """下载 ERNIE 3.0 Nano 中文模型"""
    model_name = "ernie-3.0-nano-zh"
    
    print("=" * 60)
    print("PaddleNLP 模型下载工具")
    print("=" * 60)
    print()
    print(f"🎯 目标模型：{model_name}")
    print(f"📦 模型大小：约 500 MB")
    print()
    
    # 检查是否已安装 paddlenlp
    try:
        import paddlenlp
        from paddlenlp.transformers import AutoModel, AutoTokenizer
        print(f"✅ PaddleNLP 版本：{paddlenlp.__version__}")
    except ImportError as e:
        print("❌ 错误：未检测到 PaddleNLP")
        print("请先运行：pip install paddlenlp==2.6.1")
        print(f"详细错误：{e}")
        return False
    
    # 检查是否已安装 paddlepaddle
    try:
        import paddle
        print(f"✅ PaddlePaddle 版本：{paddle.__version__}")
    except ImportError as e:
        print("❌ 错误：未检测到 PaddlePaddle")
        print("请先运行：pip install paddlepaddle==2.6.2")
        print(f"详细错误：{e}")
        return False
    
    # 确定模型保存路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, 'models', model_name)
    
    if os.path.exists(save_dir):
        print(f"⚠️  模型目录已存在：{save_dir}")
        # 检查是否完整
        config_file = os.path.join(save_dir, 'config.json')
        model_file = os.path.join(save_dir, 'model_state.pdparams')
        vocab_file = os.path.join(save_dir, 'vocab.txt')
        
        if all(os.path.exists(f) for f in [config_file, model_file, vocab_file]):
            print("✅ 模型文件完整，无需重新下载")
            return True
        else:
            print("⚠️  模型文件不完整，将重新下载")
    
    # 创建目录
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"📥 开始下载模型...")
    print(f"📁 保存位置：{save_dir}")
    print()
    print("💡 说明：模型文件较大（约 500MB），请耐心等待...")
    print()
    
    try:
        # 下载 tokenizer
        print("1. 下载 Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(save_dir)
        print("   ✅ Tokenizer 下载完成")
        
        # 下载模型
        print("2. 下载模型权重...")
        model = AutoModel.from_pretrained(model_name)
        model.save_pretrained(save_dir)
        print("   ✅ 模型权重下载完成")
        
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
        print("       └── ernie-3.0-nano-zh/")
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
        print("  2. 账号未登录或权限不足")
        print("  3. 磁盘空间不足")
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
