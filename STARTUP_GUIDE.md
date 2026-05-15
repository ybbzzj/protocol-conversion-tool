# 🚀 前后端项目启动指南

## 项目概述

这是一个**协议文档提取与自动化映射系统**，包含：
- **后端**: Python Flask API 服务
- **前端**: Vue 3 + Vite Web 应用

---

## 📋 系统要求

### 硬件要求
- CPU: 2+ 核心
- 内存: 4GB+
- 磁盘: 2GB+ 可用空间

### 软件要求
- Python 3.8+
- Node.js 16+ (前端)
- npm 或 yarn

---

## 🔧 一键启动（推荐）

### 第一步：安装依赖

```bash
# 进入项目目录
cd /Users/yuanyuqing/Documents/code/schoolProject

# 安装后端依赖
pip3 install -r backend/requirements.txt

# 安装前端依赖
cd public
npm install
# 或
yarn install
```

### 第二步：启动后端服务

```bash
# 从项目根目录启动后端
python3 -m flask run --host=0.0.0.0 --port=5000

# 或使用 Gunicorn (生产环境)
gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
```

**预期输出**:
```
 * Serving Flask app 'backend.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

### 第三步：启动前端开发服务器

**新开一个终端**:

```bash
cd /Users/yuanyuqing/Documents/code/schoolProject/public

npm run dev
# 或
yarn dev
```

**预期输出**:
```
  VITE v5.0.8  ready in 324 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

### 第四步：访问应用

在浏览器中打开:
```
http://localhost:5173/
```

---

## 📱 详细启动步骤

### 方式 1: 开发环境启动（推荐开发者使用）

#### 步骤 1: 检查 Python 版本

```bash
python3 --version
# 输出: Python 3.8+ 即可
```

#### 步骤 2: 检查 Node 版本

```bash
node --version
npm --version
# 输出: v16+ 和 npm 8+ 即可
```

#### 步骤 3: 安装后端依赖

```bash
cd /Users/yuanyuqing/Documents/code/schoolProject

# 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip3 install -r backend/requirements.txt
```

**依赖包说明**:
```
flask              # Web 框架
flask-cors         # 跨域支持
python-docx        # Word 文档处理
docx2python        # Word 文档解析
openpyxl           # Excel 处理
pandas             # 数据处理
numpy              # 数值计算
rapidfuzz          # 模糊匹配
```

#### 步骤 4: 启动后端服务

```bash
# 方式 A: 使用 Flask 内置服务器 (开发用)
python3 -m flask run --host=0.0.0.0 --port=5000

# 方式 B: 使用 Gunicorn (生产用)
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"

# 方式 C: 指定配置文件
FLASK_ENV=development python3 -m flask run
```

**验证后端启动**:
```bash
# 新开一个终端
curl http://localhost:5000/health
# 输出: {"status": "healthy", "version": "2.0.0"}
```

#### 步骤 5: 安装前端依赖

```bash
cd /Users/yuanyuqing/Documents/code/schoolProject/public

npm install
# 或使用 yarn
yarn install
```

**如果安装慢**，配置国内源：
```bash
# 使用阿里源
npm config set registry https://registry.npmmirror.com

# 然后重新安装
npm install
```

#### 步骤 6: 启动前端开发服务器

```bash
npm run dev
# 或
yarn dev
```

**预期看到**:
```
  VITE v5.0.8  ready in 324 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

#### 步骤 7: 打开浏览器

```
http://localhost:5173/
```

---

### 方式 2: 生产环境启动

#### 后端部署

```bash
# 1. 安装 Gunicorn
pip3 install gunicorn

# 2. 启动服务（4 个工作进程）
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 "backend.app:create_app()"

# 3. 或使用 supervisord 进程管理
# 编写 supervisor 配置文件
cat > /etc/supervisor/conf.d/protocol-backend.conf << EOF
[program:protocol-backend]
command=gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
directory=/Users/yuanyuqing/Documents/code/schoolProject
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/protocol-backend.log
EOF

# 重载配置
supervisorctl reread
supervisorctl update
supervisorctl start protocol-backend
```

#### 前端构建

```bash
cd /Users/yuanyuqing/Documents/code/schoolProject/public

# 生产构建
npm run build

# 输出到 dist 目录
# 将 dist 目录部署到 Nginx 或其他 Web 服务器
```

#### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /Users/yuanyuqing/Documents/code/schoolProject/public/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🧪 测试启动

### 测试后端接口

```bash
# 运行单元测试
python3 test_all_interfaces.py
```

**预期结果**:
```
================================================================================
后端 API 接口完整性验证
================================================================================

[1] 仪表盘与历史 API 测试
✓ GET /api/dashboard/recent - 成功
✓ GET /api/history - 成功

...

================================================================================
测试总结
总测试数: 13
通过: 13 ✅
失败: 0

✓ 所有接口测试通过！
================================================================================
```

### 手动测试 API

```bash
# 测试 GET 接口
curl http://localhost:5000/api/dashboard/recent

# 测试 POST 接口
curl -X POST http://localhost:5000/api/knowledge/upsert \
  -H "Content-Type: application/json" \
  -d '{"table_id":"test","source":"源字段","target":"目标字段"}'

# 上传文件测试
curl -X POST http://localhost:5000/api/extract/start \
  -F "file=@word/测试协议20251216.docx"
```

---

## ⚙️ 配置说明

### 后端配置文件

**`backend/config.py`**:
```python
# 开发环境配置
class DevelopmentConfig:
    DEBUG = True
    TESTING = False
    JSONIFY_PRETTYPRINT_REGULAR = True

# 测试环境配置
class TestingConfig:
    DEBUG = True
    TESTING = True

# 生产环境配置
class ProductionConfig:
    DEBUG = False
    TESTING = False
```

### 环境变量

```bash
# 创建 .env 文件
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=backend/app.py
CORS_ORIGINS=http://localhost:5173
```

### 前端配置文件

**`public/vite.config.ts`**:
```typescript
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
```

---

## 🐛 常见问题

### 问题 1: 后端无法启动

**错误**: `ModuleNotFoundError: No module named 'flask'`

**解决**:
```bash
# 确保安装了所有依赖
pip3 install -r backend/requirements.txt

# 或使用 requirements.txt 的完整路径
pip3 install -r /Users/yuanyuqing/Documents/code/schoolProject/backend/requirements.txt
```

### 问题 2: 前端无法安装依赖

**错误**: `npm ERR! code ENETUNREACH`

**解决**:
```bash
# 切换 npm 源
npm config set registry https://registry.npmmirror.com

# 清空缓存
npm cache clean --force

# 重新安装
npm install
```

### 问题 3: 端口已被占用

**错误**: `Address already in use`

**解决**:
```bash
# 后端默认使用 5000，改用其他端口
python3 -m flask run --port=5001

# 前端默认使用 5173，改用其他端口
npm run dev -- --port 5174
```

### 问题 4: CORS 错误

**错误**: `Access to XMLHttpRequest blocked by CORS policy`

**解决**:
- 后端已配置 CORS，自动允许前端跨域请求
- 确保 `public/vite.config.ts` 正确配置了代理

### 问题 5: 导入文档失败

**错误**: `文件解析失败`

**原因**: 支持的格式为 `.doc`, `.docx`, `.xlsx`, `.xls`, `.csv`

**解决**:
- 确保上传文件格式正确
- 检查文件是否损坏
- 查看 `backend/logs/extraction_trace.log` 了解详细错误

---

## 📝 日志位置

```
项目根目录/
├── backend/
│   ├── logs/
│   │   └── extraction_trace.log    # 提取过程详细日志
│   └── outputs/                    # 生成的 Excel 文件
```

**查看日志**:
```bash
tail -f backend/logs/extraction_trace.log
```

---

## 🔗 项目结构

```
schoolProject/
├── backend/                        # Python Flask 后端
│   ├── app.py                      # Flask 应用主文件
│   ├── config.py                   # 配置文件
│   ├── requirements.txt            # 依赖列表
│   ├── routes/                     # 路由定义
│   │   ├── extract.py              # 提取接口
│   │   ├── dashboard.py            # 仪表盘接口
│   │   ├── knowledge.py            # 知识库接口
│   │   ├── match.py                # 匹配接口
│   │   ├── batch.py                # 批量接口
│   │   ├── config.py               # 配置接口
│   │   ├── templates.py            # 模板接口
│   │   └── history.py              # 历史接口
│   ├── services/                   # 业务逻辑
│   │   ├── table_detector.py       # 表格检测
│   │   ├── table_linker.py         # 表格关联
│   │   ├── data_cleaner.py         # 数据清洗
│   │   ├── excel_exporter.py       # Excel 导出
│   │   └── field_matcher.py        # 字段匹配
│   ├── utils.py                    # 工具函数
│   ├── logs/                       # 日志目录
│   ├── uploads/                    # 上传文件临时存储
│   ├── outputs/                    # 处理结果输出
│   └── data/                       # 数据存储
├── public/                         # Vue 3 前端
│   ├── src/
│   │   ├── main.ts                 # 应用入口
│   │   ├── App.vue                 # 根组件
│   │   ├── pages/                  # 页面组件
│   │   ├── components/             # 通用组件
│   │   ├── stores/                 # Pinia 状态管理
│   │   └── router/                 # Vue Router 路由
│   ├── package.json                # 依赖配置
│   ├── vite.config.ts              # Vite 配置
│   └── index.html                  # 入口 HTML
├── doc/                            # 文档
│   ├── api.md                      # API 文档
│   └── ...
├── word/                           # 测试文档
│   ├── 测试协议20251216.docx
│   └── ...
├── requirements.txt                # 项目级依赖
└── README.md                       # 项目说明
```

---

## ✅ 启动检查清单

启动前，请确认以下项目：

- [ ] Python 版本 >= 3.8
- [ ] Node.js 版本 >= 16
- [ ] 后端依赖已安装 (`pip3 install -r backend/requirements.txt`)
- [ ] 前端依赖已安装 (`cd public && npm install`)
- [ ] 5000 端口未被占用
- [ ] 5173 端口未被占用
- [ ] 有测试文档 (`word/测试协议20251216.docx`)

---

## 🚀 快速启动命令汇总

### 开发环境（3 个终端窗口）

**终端 1 - 安装依赖**:
```bash
cd /Users/yuanyuqing/Documents/code/schoolProject
pip3 install -r backend/requirements.txt
cd public && npm install
```

**终端 2 - 启动后端**:
```bash
cd /Users/yuanyuqing/Documents/code/schoolProject
python3 -m flask run --host=0.0.0.0 --port=5000
```

**终端 3 - 启动前端**:
```bash
cd /Users/yuanyuqing/Documents/code/schoolProject/public
npm run dev
```

### 生产环境

**后端**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
```

**前端**:
```bash
npm run build
# 将 dist 目录部署到 Web 服务器
```

---

## 📞 获得帮助

### 查看日志

```bash
# 后端日志
tail -f backend/logs/extraction_trace.log

# 前端浏览器控制台
F12 打开开发者工具 -> Console 标签页
```

### 运行测试

```bash
python3 test_all_interfaces.py
```

### 检查服务状态

```bash
# 后端健康检查
curl http://localhost:5000/health

# 前端访问
http://localhost:5173/
```

---

**祝您使用愉快！🎉**
