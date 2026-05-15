"""
下载 PaddlePaddle 和 PaddleNLP 离线安装包
用于纯离线环境部署
"""
import os
import sys
import subprocess

def download_packages():
    """下载所有需要的 Python 包到本地目录"""
    
    print("=" * 60)
    print("离线依赖包下载工具")
    print("=" * 60)
    print()
    
    # 创建输出目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'offline_packages')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📦 保存位置：{output_dir}")
    print()
    
    # 需要下载的包列表
    packages = [
        'paddlepaddle==2.6.2',
        'paddlenlp==2.6.1',
    ]
    
    print("开始下载...")
    print()
    
    for package in packages:
        print(f"正在下载：{package}")
        
        # 使用 pip download 命令
        cmd = [
            sys.executable, '-m', 'pip', 'download',
            package,
            '-d', output_dir,
            '--no-deps',  # 不下载依赖，避免下载过多
            '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"   ✅ {package} 下载完成")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ {package} 下载失败：{e}")
            print()
            print("请检查网络连接或手动下载")
            return False
        
        print()
    
    print("=" * 60)
    print("✅ 所有依赖包下载完成！")
    print("=" * 60)
    print()
    print("💡 使用说明:")
    print("   1. 将 offline_packages 文件夹复制到目标机器")
    print("   2. 在目标机器运行：install_offline.bat")
    print()
    
    return True

if __name__ == '__main__':
    success = download_packages()
    sys.exit(0 if success else 1)
