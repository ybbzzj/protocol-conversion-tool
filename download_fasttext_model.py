""
下载 FastText 中文预训练模型
模型文件：cc.zh.300.bin (约 67MB)
"""
import os
import sys
import urllib.request
import hashlib

def download_fasttext_model():
    """下载 FastText 中文模型"""
    
    # 模型存放目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'cc.zh.300.bin')
    
    # 检查是否已存在
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✅ 模型已存在：{model_path}")
        print(f"   文件大小：{file_size:.1f} MB")
        return True
    
    # Facebook FastText 中文模型下载地址
    model_url = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.zh.300.bin.gz"
    
    print("="*60)
    print("FastText 中文模型下载工具")
    print("="*60)
    print()
    print(f"模型文件：cc.zh.300.bin")
    print(f"预计大小：约 67 MB")
    print(f"下载地址：{model_url}")
    print()
    
    # 询问用户是否下载
    choice = input("是否立即下载模型？(y/n): ").strip().lower()
    if choice != 'y':
        print()
        print("手动下载说明：")
        print(f"1. 访问：{model_url}")
        print(f"2. 下载后解压，将 cc.zh.300.bin 放到：{models_dir}")
        return False
    
    try:
        print("\n开始下载...")
        
        # 使用 urllib 下载
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            sys.stdout.write(f"\r进度：{percent:.1f}% ({downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB)")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(model_url, model_path + '.gz', report_progress)
        
        print("\n下载完成！")
        
        # 解压 .gz 文件
        print("正在解压...")
        import gzip
        with gzip.open(model_path + '.gz', 'rb') as f_in:
            with open(model_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        # 删除 .gz 文件
        os.remove(model_path + '.gz')
        
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✅ 模型已保存到：{model_path}")
        print(f"   文件大小：{file_size:.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 下载失败：{e}")
        print("\n请尝试手动下载：")
        print(f"1. 访问：{model_url}")
        print(f"2. 下载后解压，将 cc.zh.300.bin 放到：{models_dir}")
        return False


if __name__ == '__main__':
    success = download_fasttext_model()
    sys.exit(0 if success else 1)
