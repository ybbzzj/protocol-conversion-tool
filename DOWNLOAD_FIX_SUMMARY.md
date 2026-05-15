# 📥 下载功能修复总结

## 问题症状
提取成功但点击"下载结果"按钮后没有任何反应，或者文件在浏览器中打开预览而不是下载。

## 根本原因

### 前端问题
**文件**: `public/src/pages/Extract.vue` (第 229 行)

**原始代码**:
```typescript
// ❌ 使用 window.open() 打开 URL
function downloadResult(){ 
  if(!currentTaskId.value){ toast.show('任务ID缺失'); return } 
  window.open(endpoints.extractDownload(currentTaskId.value), '_blank') 
}
```

**问题**:
1. `window.open()` 会打开新标签页，而不是下载文件
2. 浏览器会尝试在标签页中打开 Excel 文件，而不是保存到本地
3. 没有错误处理，如果请求失败用户看不到错误信息
4. 文件名不可控，下载的文件使用系统默认名称

### 后端问题
**文件**: `backend/routes/extract.py` (第 152 行)

**原始代码**:
```python
return send_file(os.path.abspath(status['output_path']), as_attachment=True)
```

**问题**:
1. 没有指定文件名，浏览器使用随机名称
2. 内容类型可能不正确，影响浏览器的处理方式

---

## ✅ 修复方案

### 修复 1: 前端改用 fetch + blob 方式

**文件**: `public/src/pages/Extract.vue`

```typescript
// ✅ 使用 fetch 和 blob 实现可靠的下载
async function downloadResult(){
  if(!currentTaskId.value){ toast.show('任务ID缺失'); return }
  try{
    loading.start('下载中...')
    // 发送 fetch 请求获取文件
    const response = await fetch(endpoints.extractDownload(currentTaskId.value))
    if(!response.ok){ throw new Error(`HTTP ${response.status}`) }
    
    // 从响应头获取文件名
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `result_${currentTaskId.value.slice(0, 8)}.xlsx`
    if(contentDisposition){
      const matches = contentDisposition.match(/filename[^;=\n]*=((["\']*).*?\2|[^;\n]*)/)
      if(matches && matches[1]) filename = matches[1].replace(/["\\']/g, '')
    }
    
    // 创建 blob 并使用 <a> 标签下载
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()                  // 触发下载
    document.body.removeChild(link)
    URL.revokeObjectURL(url)     // 清理内存
    
    toast.show('下载完成')
  }catch(e:any){
    console.error('下载失败:', e)
    toast.show('下载失败: ' + (e.message || '未知错误'))
  }finally{
    loading.stop()
  }
}
```

**改进点**:
1. ✅ 使用 `fetch` 而不是 `window.open`
2. ✅ 正确处理 blob 数据
3. ✅ 动态创建 `<a>` 标签并触发点击
4. ✅ 保留了文件名信息
5. ✅ 完善的错误处理和加载状态
6. ✅ 清理资源 (revokeObjectURL)

### 修复 2: 后端返回正确的文件头

**文件**: `backend/routes/extract.py`

```python
@extract_bp.route('/download/<task_id>', methods=['GET'])
def download_result(task_id):
    try:
        status = tasks_status.get(task_id)
        if not status or status['status'] != 'success':
            return error_response(40401, "结果文件不存在或任务未完成")
        
        output_path = status['output_path']
        if not os.path.exists(output_path):
            return error_response(40401, "文件已过期或被删除")
        
        # ✅ 提取文件名作为下载名称
        filename = os.path.basename(output_path)
        
        return send_file(
            os.path.abspath(output_path),
            as_attachment=True,
            download_name=filename  # ✅ 设置正确的下载文件名
        )
    except Exception as e:
        return error_response(50001, f"下载失败: {str(e)}")
```

**改进点**:
1. ✅ 指定 `download_name` 参数确保文件名正确
2. ✅ 使用 `os.path.basename()` 获取实际文件名
3. ✅ 完善的错误处理

---

## 🔄 工作流程

```
用户点击"下载结果"按钮
        ↓
前端 fetch 请求: GET /api/extract/download/{taskId}
        ↓
后端验证任务状态和文件存在性
        ↓
后端返回:
  - HTTP 200
  - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - Content-Disposition: attachment; filename="协议_20260212_xxxxx.xlsx"
  - 文件二进制内容
        ↓
前端接收 blob 数据
        ↓
前端创建 <a href="blob:..."> 标签
        ↓
前端模拟点击 <a> 标签
        ↓
浏览器下载文件到本地
        ↓
前端显示 "下载完成" 提示
```

---

## ✅ 验证

### 前端测试

1. ✅ 刷新浏览器（Vite 自动热重载）
2. ✅ 上传文件，点击"开始提取"
3. ✅ 等待提取完成
4. ✅ 点击"下载结果"按钮
5. ✅ 文件应该直接下载到本地（通常在 Downloads 文件夹）
6. ✅ 文件名应该类似 `协议_20260212_xxxxx.xlsx`

### 后端测试

```bash
# 获取任务 ID
TASK_ID=$(curl -s -X POST http://localhost:5001/api/extract/start \
  -F "file=@word/测试协议20251216.docx" \
  -F "field_ids=field1" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['task_id'])")

# 下载文件
curl -s http://localhost:5001/api/extract/download/$TASK_ID -o /tmp/test_download.xlsx

# 检查文件
file /tmp/test_download.xlsx
# 输出: Microsoft Excel 2007+ Workbook, from 'python-openpyxl'
```

---

## 📊 修复前后对比

| 方面 | 修复前 | 修复后 |
|------|------|--------|
| 下载方式 | window.open() | fetch + blob |
| 用户体验 | 浏览器打开/预览文件 | 直接下载文件 |
| 文件名 | 随机/系统默认 | 正确的原始文件名 |
| 错误提示 | 无 | "下载失败: ..." |
| 加载状态 | 无提示 | 显示"下载中..." |
| 成功反馈 | 无 | 显示"下载完成" |

---

## 🎯 现在可以做什么

1. ✅ 刷新浏览器 (F5 或 Ctrl+Shift+R)
2. ✅ 上传文档并提取
3. ✅ 等待提取完成（进度条 100%）
4. ✅ 点击"下载结果"按钮
5. ✅ 文件直接下载到本地！

---

## 💡 技术细节

### 为什么用 fetch 而不是 window.open?

| 方式 | 优点 | 缺点 |
|------|------|------|
| `window.open()` | 简单 | 打开新标签，浏览器可能打开预览而不下载 |
| `<a download>` | 更可靠，直接下载 | 需要创建 blob URL |
| `fetch + blob` | 最可靠，完全控制 | 代码稍复杂，但更稳定 |

### 文件下载的三个步骤

1. **获取文件**: `fetch(url)` 获取 response
2. **转为 blob**: `response.blob()` 获取二进制数据
3. **触发下载**: 创建 `<a>` 标签设置 `href` 和 `download` 属性，然后点击

---

## 📝 修改清单

| 文件 | 修改内容 | 状态 |
|------|--------|------|
| public/src/pages/Extract.vue | downloadResult() 函数改用 fetch | ✅ 完成 |
| backend/routes/extract.py | send_file() 添加 download_name 参数 | ✅ 完成 |

---

**修复完成！现在应该能正常下载文件了。** 🎉
