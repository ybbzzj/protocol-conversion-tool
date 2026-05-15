"""
修复 paddlenlp datasets 中的 scipy 导入问题
将 scipy.linalg.block_diag 改为延迟导入
"""
import os
import sys

def patch_intokens_dataset():
    """修改 intokens_dataset.py，将 scipy 导入改为延迟导入"""
    
    # 找到 paddlenlp 安装目录
    try:
        import paddlenlp
        paddlenlp_dir = os.path.dirname(paddlenlp.__file__)
    except ImportError:
        print("PaddleNLP not installed, skipping patch")
        return False
    
    dataset_path = os.path.join(paddlenlp_dir, 'datasets', 'intokens_dataset.py')
    
    if not os.path.exists(dataset_path):
        print(f"File not found: {dataset_path}")
        return False
    
    # 读取文件
    with open(dataset_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除顶部的 from scipy.linalg import block_diag
    old_import = "from scipy.linalg import block_diag"
    if old_import not in content:
        print("Import not found, may already be patched")
        return False
    
    # 删除这个导入行
    content = content.replace(old_import + "\n", "")
    content = content.replace(old_import, "")
    
    # 2. 在使用 block_diag 的地方添加延迟导入（第 52 行附近）
    lines = content.split('\n')
    
    # 找到使用 block_diag 的行并添加局部导入
    for i, line in enumerate(lines):
        if 'block_diag(' in line and 'import' not in line:
            # 在这一行之前添加局部导入
            indent = len(line) - len(line.lstrip())
            spaces = ' ' * indent
            lines[i] = f"{spaces}# 延迟导入 scipy.linalg.block_diag\n{spaces}from scipy.linalg import block_diag\n{line}"
            break
    
    content = '\n'.join(lines)
    
    # 写回文件
    with open(dataset_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully patched {dataset_path}")
    return True

if __name__ == '__main__':
    success = patch_intokens_dataset()
    if success:
        print("✓ PaddleNLP intokens_dataset patched successfully!")
    else:
        print("✗ Failed to patch or not needed")
        sys.exit(0)  # 不视为错误
