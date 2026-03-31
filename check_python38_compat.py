# -*- coding: utf-8 -*-
"""
Python 3.8 兼容性检查工具
用于验证项目代码是否兼容 Python 3.8
"""

import sys
import os
import ast
import re

class Python38CompatibilityChecker:
    """Python 3.8 兼容性检查器"""
    
    def __init__(self):
        self.python_version = sys.version_info
        self.is_python38 = (self.python_version.major == 3 and 
                           self.python_version.minor == 8)
        self.errors = []
        self.warnings = []
        
    def check_python_version(self):
        """检查 Python 版本"""
        print("=" * 60)
        print("Python 3.8 兼容性检查工具")
        print("=" * 60)
        print()
        
        version_str = f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}"
        print(f"当前 Python 版本：{version_str}")
        
        if self.is_python38:
            print("✅ Python 版本符合要求 (3.8.x)")
        else:
            print(f"⚠️  警告：当前版本不是 Python 3.8")
            print(f"   Windows 7 最高支持 Python 3.8")
            if self.python_version.major == 3 and self.python_version.minor > 8:
                print(f"   Python 3.{self.python_version.minor} 不支持 Windows 7")
            self.warnings.append("Python 版本不是 3.8")
        
        print()
    
    def check_syntax_compatibility(self, file_path):
        """检查单个文件的语法兼容性"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析 AST
            ast.parse(content)
            
            # 检查 Python 3.9+ 的语法特性
            issues = []
            
            # 检查海象运算符 := (Python 3.8 支持，但列出作为参考)
            if ':=' in content:
                issues.append("使用了海象运算符 (:=) - Python 3.8 支持")
            
            # 检查 match-case 语句 (Python 3.10+)
            if re.search(r'\bmatch\s+\w+\s*:', content):
                issues.append("使用了 match-case 语句 - 需要 Python 3.10+")
            
            if issues:
                for issue in issues:
                    if "3.10" in issue or "3.9" in issue:
                        self.errors.append(f"{file_path}: {issue}")
                    else:
                        self.warnings.append(f"{file_path}: {issue}")
            
            return True
            
        except SyntaxError as e:
            self.errors.append(f"{file_path}: 语法错误 - {e}")
            return False
        except Exception as e:
            self.warnings.append(f"{file_path}: 读取失败 - {e}")
            return False
    
    def check_directory(self, directory, extensions=None):
        """检查目录下所有 Python 文件"""
        if extensions is None:
            extensions = ['.py']
        
        print(f"检查目录：{directory}")
        print("-" * 60)
        
        checked_files = 0
        error_files = 0
        
        for root, dirs, files in os.walk(directory):
            # 跳过隐藏目录和虚拟环境
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != 'venv' and d != 'env']
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    checked_files += 1
                    
                    if not self.check_syntax_compatibility(file_path):
                        error_files += 1
        
        print(f"检查了 {checked_files} 个文件")
        if error_files > 0:
            print(f"❌ {error_files} 个文件存在语法错误")
        else:
            print("✅ 所有文件语法正确")
        print()
    
    def check_dependencies(self, requirements_file):
        """检查依赖包的 Python 3.8 兼容性"""
        print(f"检查依赖包兼容性：{requirements_file}")
        print("-" * 60)
        
        if not os.path.exists(requirements_file):
            print(f"⚠️  警告：找不到 {requirements_file}")
            return
        
        # Python 3.8 兼容的包版本
        compatible_versions = {
            'flask': '<=2.0.3',
            'sqlalchemy': '<=1.4.46',
            'pandas': '<=1.3.5',
            'numpy': '<=1.21.6',
            'paddlepaddle': '<=2.4.2',
            'paddlenlp': '<=2.5.2',
            'rapidfuzz': '<=2.13.7',
        }
        
        incompatible = []
        
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析包名
                match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                if match:
                    package = match.group(1).lower()
                    
                    # 检查是否有版本限制
                    if '>=' in line or '==' in line:
                        version_match = re.search(r'[>=<]{1,2}\s*([0-9.]+)', line)
                        if version_match:
                            version = version_match.group(1)
                            
                            # 简单检查版本是否过高
                            if package in compatible_versions:
                                if version > compatible_versions[package].replace('<=', ''):
                                    incompatible.append(
                                        f"{package}: 当前版本 {version}, 建议 {compatible_versions[package]}"
                                    )
        
        if incompatible:
            print("⚠️  以下包可能不兼容 Python 3.8:")
            for item in incompatible:
                print(f"   - {item}")
            self.warnings.extend(incompatible)
        else:
            print("✅ 依赖包版本看起来兼容 Python 3.8")
        
        print()
    
    def run_full_check(self, project_dir='.'):
        """运行完整检查"""
        self.check_python_version()
        
        # 检查主要 Python 文件
        directories_to_check = [
            os.path.join(project_dir, 'backend'),
            os.path.join(project_dir, 'backend', 'routes'),
            os.path.join(project_dir, 'backend', 'services'),
        ]
        
        for directory in directories_to_check:
            if os.path.exists(directory):
                self.check_directory(directory)
        
        # 检查根目录的 Python 文件
        self.check_directory(project_dir)
        
        # 检查依赖
        req_files = [
            os.path.join(project_dir, 'requirements.txt'),
            os.path.join(project_dir, 'backend', 'requirements.txt'),
        ]
        
        for req_file in req_files:
            if os.path.exists(req_file):
                self.check_dependencies(req_file)
        
        # 输出总结
        print("=" * 60)
        print("检查总结")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for error in self.errors[:5]:  # 只显示前 5 个
                print(f"   - {error}")
            if len(self.errors) > 5:
                print(f"   ... 还有 {len(self.errors) - 5} 个错误")
        else:
            print("\n✅ 未发现语法错误")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings[:5]:  # 只显示前 5 个
                print(f"   - {warning}")
            if len(self.warnings) > 5:
                print(f"   ... 还有 {len(self.warnings) - 5} 个警告")
        
        print()
        
        return len(self.errors) == 0

def main():
    """主函数"""
    checker = Python38CompatibilityChecker()
    
    # 获取项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    success = checker.run_full_check(project_dir)
    
    if success:
        print("🎉 项目代码看起来兼容 Python 3.8!")
        print()
        print("下一步:")
        print("  1. 运行：pip install -r requirements.txt")
        print("  2. 下载模型：python download_model.py")
        print("  3. 构建前端：cd public && npm run build")
        print("  4. 打包：build_exe.bat")
    else:
        print("⚠️  发现兼容性问题，请先修复上述错误")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
