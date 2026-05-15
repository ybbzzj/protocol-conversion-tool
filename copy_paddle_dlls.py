"""
复制 PaddlePaddle DLL 文件到指定目录
"""
import os
import shutil
import sys

def copy_paddle_dlls(exe_dir):
    """复制 PaddlePaddle 的 DLL 文件到 exe 目录下的 paddle/libs"""
    
    # 获取 PaddlePaddle 安装位置
    import paddle
    paddle_dir = os.path.dirname(paddle.__file__)
    src_libs = os.path.join(paddle_dir, 'libs')
    
    # 目标 libs 目录
    dst_libs = os.path.join(exe_dir, 'paddle', 'libs')
    
    print(f"源目录：{src_libs}")
    print(f"目标目录：{dst_libs}")
    
    # 确保目标目录存在
    os.makedirs(dst_libs, exist_ok=True)
    
    # 复制所有 DLL 文件
    dll_files = [f for f in os.listdir(src_libs) if f.endswith('.dll')]
    
    if not dll_files:
        print("❌ 未找到 DLL 文件")
        return False
    
    print(f"准备复制 {len(dll_files)} 个 DLL 文件...")
    
    for dll in dll_files:
        src_file = os.path.join(src_libs, dll)
        dst_file = os.path.join(dst_libs, dll)
        shutil.copy2(src_file, dst_file)
        print(f"  ✅ {dll}")
    
    print(f"\n✅ 成功复制 {len(dll_files)} 个 DLL 文件")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python copy_paddle_dlls.py <exe 目录>")
        sys.exit(1)
    
    exe_dir = sys.argv[1]
    success = copy_paddle_dlls(exe_dir)
    sys.exit(0 if success else 1)
