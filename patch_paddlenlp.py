"""
修复 paddlenlp 中的 scipy 导入问题
将 scipy.linalg.block_diag 改为延迟导入
"""
import os
import sys

def patch_glm_tokenizer():
    """修改 glm/tokenizer.py，将 scipy 导入改为延迟导入"""
    
    # 找到 paddlenlp 安装目录
    import paddlenlp
    paddlenlp_dir = os.path.dirname(paddlenlp.__file__)
    tokenizer_path = os.path.join(paddlenlp_dir, 'transformers', 'glm', 'tokenizer.py')
    
    if not os.path.exists(tokenizer_path):
        print(f"File not found: {tokenizer_path}")
        return False
    
    # 读取文件
    with open(tokenizer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除顶部的 from scipy.linalg import block_diag
    old_import = "from scipy.linalg import block_diag"
    if old_import not in content:
        print("Already patched or import not found")
        return False
    
    # 删除这个导入行
    content = content.replace(old_import + "\n", "")
    content = content.replace(old_import, "")
    
    # 2. 在使用 block_diag 的地方添加延迟导入
    # 找到第 92 行的使用位置
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
    with open(tokenizer_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully patched {tokenizer_path}")
    return True

if __name__ == '__main__':
    success = patch_glm_tokenizer()
    if success:
        print("✓ PaddleNLP GLM tokenizer patched successfully!")
    else:
        print("✗ Failed to patch")
        sys.exit(1)
