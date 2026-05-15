# 协议转换工具 - 快速部署清单

## ✅ 检查清单

### 在开发机器上（可联网）

- [ ] **1. 安装 Python 3.8.x**
  ```bash
  python --version
  # 应该显示 Python 3.8.x
  ```

- [ ] **2. 安装项目依赖**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **3. 下载语义模型**
  ```bash
  python download_model.py
  # 检查 models/ernie-3.0-nano-zh 是否存在
  ```

- [ ] **4. 构建前端**
  ```bash
  cd public
  npm install
  npm run build
  # 检查 public/dist/index.html 是否存在
  ```

- [ ] **5. 打包 EXE**
  ```bash
  cd ..
  build_exe.bat
  # 检查 dist/协议转换工具/ 是否生成
  ```

### 在目标机器上（Windows 7，离线）

#### 方式 A: 使用 EXE（推荐）

- [ ] **复制整个 `dist/协议转换工具` 文件夹**
- [ ] **运行 `协议转换工具.exe`**
- [ ] **访问 http://localhost:5001**

#### 方式 B: 使用 Python 环境

- [ ] **确认 Python 3.8 已安装**
  ```bash
  python --version
  ```

- [ ] **复制源代码和模型文件**
- [ ] **安装离线依赖**
  ```bash
  install_offline.bat
  ```

- [ ] **运行程序**
  ```bash
  python main.py
  ```

---

## 🚨 常见问题速查

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError` | 运行 `install_offline.bat` |
| 模型加载失败 | 确认 `models/ernie-3.0-nano-zh` 存在 |
| 前端 404 | 运行 `npm run build` 重新构建 |
| 端口被占用 | 修改 `app.py` 中的端口号 |
| Windows 7 无法启动 | 安装 [VC++ 2019 Redistributable](https://aka.ms/vs/16/release/vc_redist.x64.exe) |

---

## 📦 文件结构

```
protocol-conversion-tool/
├── backend/                    # 后端代码
│   ├── routes/                # API 路由
│   ├── services/              # 业务逻辑
│   ├── data/                  # 数据文件
│   └── app.py                 # Flask 应用
├── public/                     # 前端代码
│   ├── src/                   # Vue 源码
│   └── dist/                  # 构建产物（重要！）
├── models/                     # 语义模型（重要！）
│   └── ernie-3.0-nano-zh/
├── download_offline_packages.py  # 离线包下载工具
├── download_model.py             # 模型下载工具
├── install_offline.bat           # 离线安装脚本
├── build_exe.bat                 # 打包脚本
├── build.spec                    # PyInstaller 配置
├── requirements.txt              # Python 依赖
└── DEPLOYMENT_GUIDE.md           # 详细部署文档
```

---

## 💡 关键命令

### 开发环境
```bash
# 安装依赖
pip install -r requirements.txt

# 下载模型
python download_model.py

# 构建前端
cd public && npm install && npm run build

# 打包
cd .. && build_exe.bat
```

### 离线环境
```bash
# 安装离线包
install_offline.bat

# 运行程序
python main.py
# 或
协议转换工具.exe
```

---

## 📞 需要帮助？

查看详细文档：`DEPLOYMENT_GUIDE.md`
