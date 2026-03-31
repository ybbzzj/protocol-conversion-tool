# 🚀 Python 3.8 + Windows 7 离线打包 - 快速开始

## ⚡ 一键部署（推荐）

在**可联网的开发机器**上执行以下命令：

```bash
deploy.bat
```

这个脚本会自动完成所有步骤！

---

## 📋 手动部署步骤

如果自动脚本有问题，可以手动执行以下步骤：

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 下载语义模型

```bash
python download_model.py
```

### 3️⃣ 构建前端

```bash
cd public
npm install
npm run build
cd ..
```

### 4️⃣ 打包成 EXE

```bash
build_exe.bat
```

---

## 🎯 部署到目标机器（Windows 7，离线）

### 方式 A: 使用 EXE（最简单）

复制整个 `dist\协议转换工具` 文件夹到目标机器，运行 `协议转换工具.exe`

### 方式 B: 离线安装包

1. 在开发机器下载离线包：
   ```bash
   python download_offline_packages.py
   ```

2. 复制 `offline_packages` 文件夹到目标机器

3. 在目标机器安装：
   ```bash
   install_offline.bat
   ```

4. 运行程序：
   ```bash
   python main.py
   ```

---

## 📚 详细文档

- **QUICK_START.md** - 快速参考清单
- **DEPLOYMENT_GUIDE.md** - 详细部署指南  
- **README_PYTHON38_WINDOWS7.md** - 完整技术说明

---

## 🔧 常用命令

### 检查兼容性
```bash
python check_python38_compat.py
```

### 重新打包
```bash
pyinstaller --clean build.spec
```

### 清理构建文件
```bash
rmdir /s /q build dist
```

---

## ⚠️ 重要提示

1. **Python 版本必须是 3.8** - Windows 7 不支持 Python 3.9+
2. **必须先构建前端** - 否则 exe 会缺少前端资源
3. **必须下载模型** - 否则语义匹配功能不可用
4. **保持文件结构完整** - 不要单独移动某些文件

---

## 🛠️ 故障排查

### 问题：打包后运行报错

**解决**:
```bash
# 确保所有依赖已正确安装
pip install -r requirements.txt

# 清理并重新打包
rmdir /s /q build dist
build_exe.bat
```

### 问题：模型加载失败

**解决**:
```bash
# 检查模型目录是否存在
dir models\ernie-3.0-nano-zh

# 如果不存在，重新下载
python download_model.py
```

### 问题：前端 404

**解决**:
```bash
# 重新构建前端
cd public
npm run build
cd ..
```

---

## 📞 需要帮助？

查看 `DEPLOYMENT_GUIDE.md` 的故障排查章节，或运行兼容性检查工具获取建议。

---

**适用环境**: Python 3.8.x + Windows 7 (64 位)  
**最后更新**: 2026-03-24
