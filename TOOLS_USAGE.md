# 🛠️ Python 3.8 + Windows 7 打包工具集使用说明

本文档介绍为适配 Python 3.8 和 Windows 7 所创建的所有工具和脚本。

---

## 📦 工具列表

### 1. deploy.bat - 一键部署脚本 ⭐推荐

**功能**: 自动完成所有部署步骤

**使用场景**: 
- 首次部署开发环境
- 快速搭建完整工作环境

**使用方法**:
```bash
deploy.bat
```

**自动化步骤**:
1. ✅ 检查 Python 版本
2. 📦 安装项目依赖
3. 🧠 下载语义模型
4. 🎨 构建前端（需要 Node.js）
5. 🔍 运行兼容性检查（可选）
6. 📦 打包成 EXE（可选）

**优点**:
- 全自动流程
- 智能错误处理
- 友好的用户提示
- 适合不熟悉命令行的人员

---

### 2. build_exe.bat - EXE 打包工具

**功能**: 将项目打包成独立的可执行文件

**使用场景**:
- 单独打包（不重新安装依赖）
- 重新打包（修改代码后）

**使用方法**:
```bash
build_exe.bat
```

**自动化检查**:
- ✅ Python 环境
- ✅ PyInstaller 安装
- ✅ 前端构建状态
- ✅ 模型文件存在性

**输出位置**: `dist/协议转换工具/`

---

### 3. download_offline_packages.py - 离线包下载工具

**功能**: 下载所有 Python 依赖包到本地

**使用场景**:
- 准备离线安装包
- 为多台机器准备部署包

**使用方法**:
```bash
python download_offline_packages.py -r requirements.txt -d ./offline_packages
```

**参数说明**:
- `-r, --requirements`: requirements.txt 文件路径（默认：requirements.txt）
- `-d, --download-dir`: 下载目录（默认：./offline_packages）

**输出示例**:
```
offline_packages/
├── Flask-2.0.3-py3-none-any.whl
├── paddlepaddle-2.4.2-cp38-cp38-win_amd64.whl
├── paddlenlp-2.5.2-py3-none-any.whl
└── ... (约 50+ 个 whl 文件)
```

---

### 4. install_offline.bat - 离线包安装工具

**功能**: 从本地目录安装所有依赖

**使用场景**:
- 在离线的目标机器上安装依赖
- 避免重复下载

**使用方法**:
```bash
install_offline.bat
```

**前提条件**:
- Python 3.8 已安装
- offline_packages 目录存在

**安装过程**:
```bash
python -m pip install --no-index --find-links="./offline_packages" -r requirements.txt
```

---

### 5. download_model.py - 语义模型下载工具

**功能**: 下载 ERNIE 3.0 Nano 中文语义模型

**使用场景**:
- 首次部署时下载模型
- 模型损坏时重新下载

**使用方法**:
```bash
python download_model.py
```

**下载内容**:
- Tokenizer 配置文件
- 模型权重文件
- 词汇表文件

**保存位置**: `models/ernie-3.0-nano-zh/`

**模型大小**: ~100MB

---

### 6. check_python38_compat.py - Python 3.8 兼容性检查工具

**功能**: 全面检查项目是否兼容 Python 3.8

**使用场景**:
- 部署前验证
- 代码迁移前检查
- 排查兼容性问题

**使用方法**:
```bash
python check_python38_compat.py
```

**检查项目**:
1. ✅ Python 版本检测
2. ✅ 语法兼容性分析
3. ✅ 依赖包版本验证
4. ✅ 潜在问题扫描

**输出示例**:
```
============================================================
Python 3.8 兼容性检查工具
============================================================

当前 Python 版本：3.8.8
✅ Python 版本符合要求 (3.8.x)

检查目录：backend
检查了 15 个文件
✅ 所有文件语法正确

检查依赖包兼容性：requirements.txt
✅ 依赖包版本看起来兼容 Python 3.8

============================================================
检查总结
============================================================

✅ 未发现语法错误
✅ 未发现兼容性问题

🎉 项目代码看起来兼容 Python 3.8!
```

---

### 7. build.spec - PyInstaller 配置文件

**功能**: 定义 PyInstaller 打包的详细参数

**主要内容**:
- 依赖库收集规则
- 数据文件包含规则
- 隐藏导入声明
- EXE 生成选项

**关键配置**:
```python
# 收集 PaddlePaddle 和 PaddleNLP 的所有依赖
datas_nlp, binaries_nlp, hiddenimports_nlp = collect_all('paddlenlp')
datas_paddle, binaries_paddle, hiddenimports_paddle = collect_all('paddlepaddle')

# 添加项目资源文件
added_datas = [
    ('public/dist', 'public/dist'),
    ('models', 'models'),
    ('backend/data', 'backend/data'),
]
```

**手动使用**:
```bash
pyinstaller build.spec
```

---

## 🎯 典型使用场景

### 场景 1: 首次部署（开发机器，可联网）

**推荐工具**: `deploy.bat`

**或者手动执行**:
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载模型
python download_model.py

# 3. 构建前端
cd public && npm install && npm run build

# 4. 打包
cd .. && build_exe.bat
```

---

### 场景 2: 部署到多台离线机器

**步骤**:

#### 在开发机器上准备:
```bash
# 1. 下载离线包
python download_offline_packages.py

# 2. 打包 EXE
build_exe.bat
```

#### 在每台目标机器上:
**方式 A（推荐）**:
```bash
# 直接运行打包好的 EXE
dist\协议转换工具\协议转换工具.exe
```

**方式 B（需要 Python 环境）**:
```bash
# 1. 复制源代码和离线包
# 2. 安装依赖
install_offline.bat

# 3. 运行程序
python main.py
```

---

### 场景 3: 代码修改后重新打包

**推荐工具**: `build_exe.bat`

**或者手动执行**:
```bash
# 清理旧文件
rmdir /s /q build dist

# 重新打包
pyinstaller --clean build.spec
```

---

### 场景 4: 排查兼容性问题

**推荐工具**: `check_python38_compat.py`

**配合使用**:
```bash
# 1. 运行兼容性检查
python check_python38_compat.py

# 2. 查看详细依赖
pip list

# 3. 如有问题，重新安装
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

---

## 📊 工具对比表

| 工具 | 主要用途 | 使用阶段 | 是否需要联网 |
|------|---------|---------|-------------|
| deploy.bat | 一键完整部署 | 初次部署 | ✅ 需要 |
| build_exe.bat | 打包成 EXE | 任何阶段 | ❌ 不需要 |
| download_offline_packages.py | 下载离线包 | 准备离线部署 | ✅ 需要 |
| install_offline.bat | 安装离线包 | 目标机器部署 | ❌ 不需要 |
| download_model.py | 下载语义模型 | 初次部署 | ✅ 需要 |
| check_python38_compat.py | 兼容性检查 | 排查问题 | ❌ 不需要 |
| build.spec | PyInstaller 配置 | 打包时使用 | ❌ 不需要 |

---

## 🔍 常见问题

### Q1: 应该使用哪个工具？

**A**: 
- 如果是第一次部署 → 使用 `deploy.bat`
- 如果只需要打包 → 使用 `build_exe.bat`
- 如果要部署到离线机器 → 使用 `download_offline_packages.py` + `install_offline.bat`
- 如果遇到兼容性问题 → 使用 `check_python38_compat.py`

### Q2: 这些工具的优先级是什么？

**A**:
1. **必用**: `deploy.bat` 或手动执行所有步骤
2. **推荐**: `check_python38_compat.py`（部署前检查）
3. **按需**: `download_offline_packages.py`（离线部署时使用）

### Q3: 可以跳过某些工具吗？

**A**:
- ❌ 不能跳过：依赖安装、模型下载、前端构建
- ✅ 可以跳过：兼容性检查（但强烈推荐）
- ⚠️ 视情况：离线包下载（如果目标机器可以联网则不需要）

### Q4: 工具执行失败怎么办？

**A**:
1. 查看错误信息
2. 检查 Python 版本是否为 3.8
3. 检查网络连接（如果需要下载）
4. 查看对应的详细文档
5. 尝试手动执行相应步骤

---

## 💡 最佳实践

### 1. 开发阶段
```bash
# 使用 deploy.bat 一次性完成所有部署
deploy.bat
```

### 2. 修改代码后
```bash
# 只需重新打包
build_exe.bat
```

### 3. 部署到客户机器
```bash
# 准备离线包
python download_offline_packages.py

# 打包 EXE
build_exe.bat

# 交付给客户整个 dist 文件夹和 offline_packages 文件夹
```

### 4. 故障排查
```bash
# 首先运行兼容性检查
python check_python38_compat.py

# 根据提示修复问题
```

---

## 📝 工具维护

### 更新依赖版本
编辑 `requirements.txt`，然后重新运行：
```bash
python download_offline_packages.py
```

### 修改打包配置
编辑 `build.spec`，然后重新运行：
```bash
build_exe.bat
```

### 添加新的检查项
编辑 `check_python38_compat.py`，添加相应的检查逻辑。

---

## 🆘 获取帮助

每个工具都有详细的注释和错误提示：
- 查看工具的 docstring
- 阅读错误输出信息
- 参考 `DEPLOYMENT_GUIDE.md`
- 运行对应的 `--help` 参数（如果支持）

---

**最后更新**: 2026-03-24  
**适用版本**: Python 3.8 + Windows 7
