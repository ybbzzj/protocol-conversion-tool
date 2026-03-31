# 协议转换工具 - Python 3.8 + Windows 7 离线部署指南

## 📋 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [打包说明](#打包说明)
- [故障排查](#故障排查)

---

## 🖥️ 环境要求

### 开发/打包环境（可联网）
- **操作系统**: Windows 7/10/11 (64 位)
- **Python 版本**: Python 3.8.x (推荐 3.8.8)
- **Node.js**: v14+ (用于构建前端)
- **网络**: 需要联网下载依赖包和模型

### 运行环境（离线）
- **操作系统**: Windows 7 (64 位)
- **Python 版本**: Python 3.8.x
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 5GB 可用空间

---

## 🚀 快速开始

### 方式一：使用已打包的 EXE（推荐）

如果已经打包好，直接执行以下步骤：

1. **复制整个 `dist\协议转换工具` 文件夹**到目标机器
2. 确保文件夹结构完整：
   ```
   协议转换工具/
   ├── 协议转换工具.exe
   ├── models/
   │   └── ernie-3.0-nano-zh/
   ├── public/
   │   └── dist/
   ├── backend/
   │   └── data/
   └── ...其他文件
   ```
3. 双击运行 `协议转换工具.exe`
4. 浏览器访问：http://localhost:5001

---

## 📦 详细部署步骤

### 步骤 1: 准备开发环境（可联网的机器）

#### 1.1 安装 Python 3.8

```bash
# 下载 Python 3.8.8
# 访问 https://www.python.org/downloads/release/python-388/
# 选择 "Windows x86-64 executable installer"

# 安装时务必勾选：
# ✓ Add Python 3.8 to PATH
# ✓ pip
```

#### 1.2 安装 Node.js（用于构建前端）

```bash
# 下载 Node.js v14 LTS
# 访问 https://nodejs.org/en/download/releases/
# 选择 Windows Installer (.msi)
```

### 步骤 2: 安装项目依赖

```bash
# 进入项目目录
cd protocol-conversion-tool

# 安装所有依赖（包括 PyInstaller）
pip install -r requirements.txt
```

### 步骤 3: 下载语义模型

```bash
# 下载 ERNIE 3.0 Nano 中文模型
python download_model.py
```

**说明**: 
- 模型会下载到 `models/ernie-3.0-nano-zh/` 目录
- 模型大小约 100MB，下载时间取决于网络速度
- 下载完成后，模型会被自动包含到 exe 中

### 步骤 4: 构建前端

```bash
# 进入前端目录
cd public

# 安装前端依赖
npm install

# 构建生产版本
npm run build
```

构建完成后，会在 `public/dist/` 目录生成静态文件。

### 步骤 5: 打包成 EXE

```bash
# 返回项目根目录
cd ..

# 执行打包脚本
build_exe.bat
```

或者手动执行：

```bash
pyinstaller --clean build.spec
```

打包完成后，会在 `dist/协议转换工具/` 目录生成可执行文件。

---

## 💾 离线部署到目标机器（Windows 7）

### 方式 A: 使用 EXE（无需安装 Python）

1. **复制整个 `dist\协议转换工具` 文件夹**到目标机器
2. 直接运行 `协议转换工具.exe`

### 方式 B: 使用 Python 环境（需要安装 Python 3.8）

如果目标机器已有 Python 3.8，可以只复制源代码：

1. **复制以下文件到目标机器**:
   - 整个 `backend/` 目录
   - 整个 `public/` 目录
   - 整个 `models/` 目录
   - `requirements.txt`
   - `main.py`
   - `app.py`

2. **在目标机器安装依赖**:
   
   如果有离线包：
   ```bash
   # 将离线包目录复制到目标机器
   # 然后执行
   install_offline.bat
   ```
   
   如果目标机器可以临时联网：
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**:
   ```bash
   python main.py
   ```

---

## 🔧 打包说明

### PyInstaller 配置

打包使用 `build.spec` 配置文件，主要包含：

- **所有 Python 依赖**: Flask, PaddlePaddle, PaddleNLP 等
- **前端资源**: Vue 构建后的静态文件
- **模型文件**: ERNIE 3.0 Nano 模型
- **配置文件**: 字段映射、知识库等 JSON 文件

### 打包选项

```bash
# 清理模式（推荐）
pyinstaller --clean build.spec

# 调试模式（生成更大的 exe，但便于调试）
pyinstaller --debug build.spec

# 单文件模式（不推荐，启动慢）
pyinstaller --onefile build.spec
```

### 生成的文件结构

```
dist/协议转换工具/
├── 协议转换工具.exe          # 主程序
├── models/                    # 语义模型
│   └── ernie-3.0-nano-zh/
├── public/dist/              # 前端资源
│   ├── index.html
│   └── assets/
├── backend/
│   ├── data/                # 数据文件
│   └── *.json              # 配置文件
└── ...其他依赖库
```

---

## 🛠️ 故障排查

### 问题 1: 打包时报错 "ModuleNotFoundError"

**解决方案**:
```bash
# 确保所有依赖已安装
pip install -r requirements.txt

# 重新打包
pyinstaller --clean build.spec
```

### 问题 2: 运行时提示缺少 DLL 文件

**解决方案**:
```bash
# 编辑 build.spec，添加缺失的模块到 hiddenimports
hiddenimports += [
    '缺失的模块名',
]

# 重新打包
pyinstaller --clean build.spec
```

### 问题 3: 模型加载失败

**检查项**:
1. 确认 `models/ernie-3.0-nano-zh/` 目录存在
2. 确认目录下有 `config.json` 和模型权重文件
3. 检查磁盘空间是否充足

**重新下载模型**:
```bash
# 删除旧模型
rmdir /s /q models\ernie-3.0-nano-zh

# 重新下载
python download_model.py
```

### 问题 4: 前端页面无法访问

**检查项**:
1. 确认前端已构建：`public/dist/index.html` 存在
2. 检查端口 5001 是否被占用
3. 查看控制台日志

**重新构建前端**:
```bash
cd public
npm run build
```

### 问题 5: Windows 7 无法运行

**可能原因**:
- Python 版本高于 3.8（Windows 7 最高支持 Python 3.8）
- 缺少 Visual C++ Redistributable

**解决方案**:
```bash
# 下载并安装 Visual C++ Redistributable for Visual Studio 2015-2019
# 访问 https://aka.ms/vs/16/release/vc_redist.x64.exe
```

---

## 📝 注意事项

1. **Python 版本必须一致**: 打包和使用都必须是 Python 3.8
2. **首次启动较慢**: 需要加载语义模型，属正常现象
3. **不要移动 models 目录**: 程序通过相对路径查找模型
4. **建议整体复制**: 保持文件结构完整，避免单独移动文件
5. **定期更新依赖**: 关注安全更新和 bug 修复

---

## 📞 技术支持

如遇到其他问题，请查看：

- 项目文档：`doc/` 目录
- 后端日志：控制台输出
- 前端调试：浏览器开发者工具

---

## 📄 许可证

遵循项目原有许可证。
