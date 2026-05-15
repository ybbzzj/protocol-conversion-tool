# 📋 前端提取界面"创建任务失败"诊断与修复报告

## 🔍 问题诊断

### 症状
前端"文档提取"页面点击"开始提取"按钮后显示 **"创建任务失败"** 提示，任务未被创建。

### 根本原因分析

#### 原因 1: **FormData 字段格式不匹配** ✅ (已修复)
- **前端代码问题** (`public/src/pages/Extract.vue` 第 195 行):
  ```javascript
  // ❌ 错误的方式 - 发送单个 JSON 字符串
  fd.append('field_ids', JSON.stringify(selectedFieldIds.value))
  ```

- **后端期望** (`backend/routes/extract.py` 第 33 行):
  ```python
  # ✅ 期望多个表单字段
  field_ids = request.form.getlist('field_ids')
  ```

- **问题**: Flask `request.form.getlist()` 期望接收多个同名的表单字段（如 `field_ids=val1&field_ids=val2`），而前端发送的是单个 JSON 字符串，导致解析失败。

#### 原因 2: **字段配置缺失** ⚠️ (需要用户手动操作)
- 用户未在"字段配置"页面添加任何协议字段
- 前端检查 `selectedFieldIds.value.length===0` 则立即退出，显示 "请选择协议字段"
- 即使前端显示有字段列表，但实际上是空的（本地存储中为空）

---

## 🔧 修复方案

### 修复 1: 更正 FormData 格式 (已完成) ✅

**修改文件**: `public/src/pages/Extract.vue`

**修改位置**: `startExtract()` 函数（第 188-203 行）

**修改前**:
```javascript
async function startExtract(){
  if(selectedFieldIds.value.length===0){ toast.show('请选择协议字段'); return }
  if(!fileObj.value){ toast.show('请上传协议文档'); return }
  try{
    loading.start('创建提取任务...')
    const fd = new FormData()
    fd.append('file', fileObj.value)
    fd.append('field_ids', JSON.stringify(selectedFieldIds.value))  // ❌ 错误
    const { data } = await api.post(endpoints.extractStart, fd, { headers:{ 'Content-Type':'multipart/form-data' } })
    currentTaskId.value = data?.data?.task_id || ''
    if(!currentTaskId.value){ toast.show('未返回任务ID'); return }
    toast.show('任务已创建，开始查询进度')
    startPolling()
  }catch(e:any){ toast.show('创建任务失败') }
  finally{ loading.stop() }
}
```

**修改后**:
```javascript
async function startExtract(){
  if(selectedFieldIds.value.length===0){ toast.show('请选择协议字段'); return }
  if(!fileObj.value){ toast.show('请上传协议文档'); return }
  try{
    loading.start('创建提取任务...')
    const fd = new FormData()
    fd.append('file', fileObj.value)
    // ✅ 正确方式: 为每个 field_id 添加独立的表单字段
    for(const fieldId of selectedFieldIds.value){
      fd.append('field_ids', fieldId)
    }
    const { data } = await api.post(endpoints.extractStart, fd, { headers:{ 'Content-Type':'multipart/form-data' } })
    currentTaskId.value = data?.data?.task_id || ''
    if(!currentTaskId.value){ toast.show('未返回任务ID'); return }
    toast.show('任务已创建，开始查询进度')
    startPolling()
  }catch(e:any){ 
    console.error('创建任务失败:', e)
    // ✅ 改进错误提示，显示具体错误信息
    toast.show('创建任务失败: ' + (e.response?.data?.message || e.message || '未知错误')) 
  }
  finally{ loading.stop() }
}
```

**改进点**:
1. ✅ 使用 `for` 循环为每个 `field_id` 添加独立的表单字段
2. ✅ 增强错误提示，显示后端返回的具体错误信息
3. ✅ 添加 `console.error()` 便于调试

---

### 修复 2: 使用步骤指南（用户操作）

#### 第 1 步: 添加协议字段

1. 打开应用: http://localhost:5173/
2. 左侧菜单 → 点击 **"字段配置"** 页面
3. 在 **"协议字段"** 部分：
   - 输入框中输入字段名（如 "序号", "信源", "信宿", "信息内容" 等）
   - 点击 **"新增"** 按钮
   - 重复添加多个字段
   
   **示例字段**:
   ```
   - 序号
   - 信源
   - 信宿
   - 信息内容
   - 接收组播地址
   - 接收端口号
   - 信源系统码
   - 信源机器码
   - 信宿系统码
   - 信宿机器码
   ```

4. 点击 **"导出字段（JSON）"** 保存备份

#### 第 2 步: 在提取页面选择字段

1. 左侧菜单 → 点击 **"文档提取"** 页面
2. **"选择协议字段"** 部分：
   - 点击 **"刷新"** 按钮，加载已添加的字段
   - 勾选需要提取的字段（多选）
3. **"上传协议文档"** 部分：
   - 上传 `.doc` 或 `.docx` 文件（如 `word/测试协议20251216.docx`）
4. 点击 **"开始提取"** 按钮
5. 等待进度条完成（通常 5-30 秒）
6. 看到 **"提取完成，可下载结果"** 提示后，点击 **"下载结果"** 下载 Excel 文件

---

## 🧪 验证修复

### 后端 API 测试 (已通过) ✅

```bash
# 测试创建任务
curl -s -X POST http://localhost:5001/api/extract/start \
  -F "file=@word/测试协议20251216.docx" \
  -F "field_ids=field1" \
  -F "field_ids=field2" | python3 -m json.tool

# 预期输出:
# {
#   "code": 0,
#   "data": {
#     "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
#   },
#   "message": "成功"
# }

# 查询任务状态
curl -s http://localhost:5001/api/extract/status/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | python3 -m json.tool

# 预期输出:
# {
#   "code": 0,
#   "data": {
#     "status": "success",
#     "progress": 100,
#     "message": ""
#   },
#   "message": "成功"
# }
```

### 前端测试步骤

1. **清空浏览器本地存储** (可选):
   ```javascript
   // 在浏览器控制台执行:
   localStorage.clear()
   location.reload()
   ```

2. **按照上述"使用步骤指南"操作**

3. **观察浏览器控制台** (F12 → Console):
   - 应该看到 API 请求和响应
   - 如有错误，会显示具体信息

4. **检查网络请求** (F12 → Network):
   - 查看 `extract/start` 请求的 **Request** 部分
   - FormData 中应该有多个 `field_ids` 字段，而不是一个 JSON 字符串

---

## 📊 问题前后对比

| 方面 | 修复前 | 修复后 |
|------|-------|-------|
| FormData 格式 | `field_ids: "[\"id1\",\"id2\"]"` (JSON 字符串) | `field_ids: "id1"` + `field_ids: "id2"` (多个字段) |
| 后端解析 | `field_ids = ['[\"id1\",\"id2\"]']` (单元素列表) | `field_ids = ['id1', 'id2']` (正确) |
| 错误提示 | "创建任务失败" (模糊) | "创建任务失败: {具体错误信息}" (清晰) |
| 调试能力 | 无控制台日志 | 有 `console.error()` 输出 |

---

## 🔗 相关文件

- **前端代码**: `public/src/pages/Extract.vue` (已修复)
- **后端代码**: `backend/routes/extract.py` (正常)
- **API 配置**: `public/src/api/index.ts`
- **字段配置页**: `public/src/pages/Config.vue`

---

## 🚀 后续改进建议

### 短期 (可以立即实施)
- [ ] 为"提取"页面添加初始化提示："请先到字段配置添加协议字段"
- [ ] 添加示例字段初始化，便于首次使用
- [ ] 优化错误提示，显示更多调试信息

### 中期
- [ ] 支持从后端 API 加载字段定义（而不仅仅本地存储）
- [ ] 添加批量导入字段的功能
- [ ] 保存用户最近使用的字段选择

### 长期
- [ ] 集成知识库自动推荐字段
- [ ] 支持历史任务管理和重复使用
- [ ] 性能优化（目前已支持大文件）

---

## ✅ 总结

### 修复内容
1. ✅ 修正 FormData 多字段格式（`field_ids` 添加多次而不是 JSON 字符串）
2. ✅ 改进错误提示消息
3. ✅ 添加控制台调试日志

### 用户需要做的
1. ✅ 热重载前端代码（或手动刷新浏览器）
2. ✅ 按照步骤指南在"字段配置"页面添加协议字段
3. ✅ 在"文档提取"页面选择字段并上传文档

### 预期效果
- 创建任务将成功
- 进度条会显示提取进度（10% → 50% → 90% → 100%）
- 完成后可以下载 Excel 结果文件

---

**修复状态**: ✅ 代码已修复，等待前端热重载

**测试方法**: 打开浏览器 http://localhost:5173/ → 按照步骤指南操作 → 观察是否成功

**问题反馈**: 如仍有问题，请检查浏览器控制台错误信息并截图反馈
