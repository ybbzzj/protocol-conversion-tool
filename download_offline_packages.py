# -*- coding: utf-8 -*-
"""
离线依赖下载工具
用于在可联网的机器上下载所有需要的 Python 包及其依赖
适用于 Python 3.8 + Windows 7 环境
"""

import os
import sys
import subprocess
import argparse

def download_packages(requirements_file, download_dir):
    """
    下载所有依赖包到指定目录
    
    Args:
        requirements_file: requirements.txt 文件路径
        download_dir: 下载目录
    """
    if not os.path.exists(requirements_file):
        print(f"错误：找不到 requirements 文件：{requirements_file}")
        return False
    
    # 创建下载目录
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    print(f"开始下载依赖包到：{download_dir}")
    print("=" * 60)
    
    # 使用 pip download 命令
    cmd = [
        sys.executable, "-m", "pip", "download",
        "-r", requirements_file,
        "-d", download_dir,
        "--no-cache-dir",  # 不使用缓存
        "-v"  # 详细输出
    ]
    
    # 添加 Python 3.8 和 Windows 限制
    cmd.extend([
        "--python-version", "38",
        "--only-binary", ":all:",
        "--platform", "win_amd64"  # 如果是 64 位系统
    ])
    
    print(f"执行命令：{' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ 所有依赖包下载完成！")
        print(f"📦 下载位置：{download_dir}")
        print("=" * 60)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 下载失败：{e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="离线依赖包下载工具")
    parser.add_argument(
        "-r", "--requirements",
        default="requirements.txt",
        help="requirements.txt 文件路径 (默认：requirements.txt)"
    )
    parser.add_argument(
        "-d", "--download-dir",
        default="./offline_packages",
        help="下载目录 (默认：./offline_packages)"
    )
    
    args = parser.parse_args()
    
    # 确定 requirements 文件路径
    if os.path.isabs(args.requirements):
        req_file = args.requirements
    else:
        # 尝试在当前目录和 backend 目录查找
        if os.path.exists(args.requirements):
            req_file = args.requirements
        elif os.path.exists(os.path.join("backend", args.requirements)):
            req_file = os.path.join("backend", args.requirements)
        else:
            print(f"❌ 找不到 requirements 文件：{args.requirements}")
            print("请使用 -r 参数指定正确的路径")
            return 1
    
    print(f"📋 使用 requirements 文件：{req_file}")
    print(f"📥 下载到目录：{args.download_dir}")
    print()
    
    success = download_packages(req_file, args.download_dir)
    
    if success:
        print("\n💡 使用说明:")
        print(f"   1. 将整个 '{args.download_dir}' 文件夹复制到目标机器")
        print(f"   2. 在目标机器执行：pip install --no-index --find-links={args.download_dir} -r requirements.txt")
        print("   3. 或者使用提供的 install_offline.bat 脚本自动安装")
        return 0
    else:
        print("\n❌ 下载过程中出现错误，请检查网络连接或 requirements 文件")
        return 1

if __name__ == "__main__":
    sys.exit(main())
