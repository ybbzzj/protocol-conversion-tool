import os
import paddle

# 获取 PaddlePaddle 安装位置
paddle_dir = os.path.dirname(paddle.__file__)
print(f"PaddlePaddle 安装位置：{paddle_dir}")
print()

# 检查可能的 libs 目录
libs_dirs = [
    os.path.join(paddle_dir, 'libs'),
    os.path.join(paddle_dir, '..', 'libs'),
    os.path.join(paddle_dir, 'base', '..', 'libs'),
]

print("检查 libs 目录:")
for d in libs_dirs:
    exists = os.path.exists(d)
    print(f"  {'✅' if exists else '❌'} {d} -> {'存在' if exists else '不存在'}")
    
    # 如果存在，列出其中的 DLL 文件
    if exists:
        dll_files = [f for f in os.listdir(d) if f.endswith('.dll')]
        print(f"     找到 {len(dll_files)} 个 DLL 文件")
        if dll_files[:3]:  # 只显示前 3 个
            print(f"     示例：{', '.join(dll_files[:3])}")
