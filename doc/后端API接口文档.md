# 后端 API 接口文档

---

## 基础约定

| 项目 | 说明 |
|------|------|
| **统一前缀** | `/api` |
| **Content-Type** | `application/json`（文件上传使用 `multipart/form-data`） |
| **响应格式** | `{ "code": number, "message": string, "data": any }` |

### 错误码定义

| 错误码 | 说明 |
|--------|------|
| `0` | 成功 |
| `40001` | 参数错误 |
| `40002` | 文件解析失败 |
| `40401` | 资源不存在 |
| `50001` | 内部错误 |

### 接口状态说明

| 状态 | 说明 |
|------|------|
| **active** | 前端正在使用，必须保证可用 |
| **reserved** | 前端暂未使用，后端已完整实现，可随时启用 |
| **deprecated** | 前端已改为本地存储，不再调用后端接口 |

---

## 一、仪表盘 (Dashboard)

### GET /api/dashboard/recent 【active】

获取最近处理的任务列表和统计信息。

**响应示例**：
```json
{
  "code": 0,
  "message": "操作成功",
  "data": {
    "recent": [
      {
        "id": "a1b2c3d4",
        "time": "2026-05-21T10:30:00",
        "table": "PD控制指令",
        "status": "success"
      }
    ],
    "stats": {
      "total": 42,
      "success": 38,
      "fail": 4
    }
  }
}
```

---

## 二、文档提取 (Extract)

### POST /api/extract/start 【active】

创建文档提取任务。

**请求格式**：`multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | Word (.doc/.docx) / Excel (.xlsx/.xls) / CSV 文件 |
| `field_ids` | string[] | 否 | 前端选中的协议字段 ID 数组 |

**响应示例**：
```json
{
  "code": 0,
  "message": "操作成功",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "expected_fields": ["协议名称", "数据类型", "单位"]
  }
}
```

**处理流程**（同步执行）：
1. 文件格式验证 → 保存到 `backend/uploads/`
2. DocumentParser 解析文档 → 识别表格类型
3. TableLinker 关联辅助表 → 注入元数据
4. DataProcessor 清洗数据 → 类型标准化/值域格式化/公式标准化
5. EnhancedFieldMatcher 字段匹配 → 映射质量评分
6. ExcelExporter 导出 → 基于模板生成 Excel
7. 任务完成 → 持久化到 `tasks_history.json`

**错误响应**：
```json
{ "code": 40001, "message": "不支持的文件格式，请上传 .doc, .docx, .xlsx, .xls, .csv 格式的文件", "data": null }
{ "code": 40002, "message": "文件解析失败: [详细错误]", "data": null }
```

---

### GET /api/extract/status/{task_id} 【active】

查询任务执行状态和进度。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务ID（由 `/start` 返回） |

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "status": "running",
    "progress": 65,
    "message": "",
    "mapping_quality": {
      "score": 0.85,
      "level": "good",
      "exact_count": 12,
      "fuzzy_count": 5,
      "unmatched_count": 2,
      "total": 19
    }
  }
}
```

**status 枚举值**：

| 值 | 说明 |
|------|------|
| `running` | 处理中 |
| `success` | 处理完成，可下载 |
| `failed` | 处理失败，查看 message 字段 |
| `queued` | 排队中（预留） |

**映射质量等级**：

| level | 条件 |
|-------|------|
| `excellent` | score > 0.9 |
| `good` | 0.7 < score ≤ 0.9 |
| `poor` | score ≤ 0.7 |
| `unknown` | 无法计算 |

---

### GET /api/extract/download/{task_id} 【active】

下载处理完成的 Excel 结果文件。

**响应格式**：`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

**响应头**：
```
Content-Disposition: attachment; filename*=UTF-8''原始文件名.xlsx
```

**说明**：
- 文件名自动使用原始上传文件名（扩展名改为 .xlsx）
- 下载完成后服务端自动删除临时文件
- 仅 `status=success` 的任务可下载

---

## 三、知识库管理 (Knowledge)

### GET /api/knowledge/list 【active】

分页获取知识库条目列表。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 否 | - | 搜索关键字（匹配 source 或 target） |
| `table_id` | string | 否 | - | 按表标识筛选 |
| `page` | integer | 否 | 1 | 页码（≥1） |
| `page_size` | integer | 否 | 20 | 每页条数（1~100） |

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "source": "参数名称",
        "target": "参数",
        "table_id": "BC-RT1",
        "confidence": 0.95,
        "hits": 15,
        "created_at": "2026-01-15T10:30:00"
      }
    ],
    "total": 230
  }
}
```

---

### POST /api/knowledge/query 【active】

根据源字段查询知识库匹配建议（精确 + 模糊）。

**请求体**：
```json
{
  "source": "参数名称",
  "table_id": "BC-RT1",
  "context": "控制指令"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | 是 | 待匹配的源字段名 |
| `table_id` | string | 否 | 限定表范围 |
| `context` | string | 否 | 上下文信息（预留） |

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "candidates": [
      {
        "target": "参数",
        "confidence": 1.0,
        "match_type": "exact",
        "hits": 15
      },
      {
        "target": "信号名称",
        "confidence": 0.63,
        "match_type": "fuzzy",
        "hits": 3
      }
    ]
  }
}
```

---

### POST /api/knowledge/upsert 【reserved】

新增或更新知识库映射条目。

**请求体**：
```json
{
  "id": "optional-existing-id",
  "table_id": "BC-RT1",
  "source": "参数名称",
  "target": "参数",
  "confidence": 0.95
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | 是 | 源字段名 |
| `target` | string | 是 | 目标字段名 |
| `confidence` | number | 否 (默认0.8) | 置信度，范围 0~1 |
| `table_id` | string | 否 (默认default) | 表标识 |
| `id` | string | 否 | 条目ID（不传则自动生成UUID） |

---

### GET /api/knowledge/stats 【reserved】

获取知识库统计信息。

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "total": 230,
    "by_table": [
      { "table_id": "BC-RT1", "count": 85 },
      { "table_id": "default", "count": 120 }
    ],
    "top_hits": [
      { "source": "参数", "target": "参数", "hits": 45, "confidence": 1.0 }
    ]
  }
}
```

---

## 四、字段映射 (Mapping)

### GET /api/mapping/preview/{task_id} 【active】

预览文档提取结果和字段映射建议。

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "extracted_fields": ["序号", "参数名称", "数据类型", "字节数", "备注"],
    "table_data": [{ "表格名称": "PD控制指令", "序号": "1", ... }],
    "mapping_suggestions": [
      { "original": "参数名称", "matched": "参数", "confidence": 1.0, "type": "exact" },
      { "original": "数据类型", "matched": null, "confidence": 0.0, "type": "unmatched", "suggestions": [...] }
    ],
    "matched_fields": [...],
    "unmatched_fields": [...],
    "total_fields": 5
  }
}
```

---

### POST /api/mapping/batch-suggest 【active】

批量获取字段推荐建议。

**请求体**：
```json
{
  "source_fields": ["参数名称", "数据长度", "备注"],
  "available_targets": ["参数", "类型", "值域", "单位", "备注"]
}
```

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "suggestions": {
      "参数名称": [
        { "target": "参数", "confidence": 0.95, "reason": "知识库匹配" }
      ]
    }
  }
}
```

---

### POST /api/mapping/auto-map 【active】

智能自动映射——根据相似度计算最佳一对一映射。

**请求体**：
```json
{
  "source_fields": ["参数名称", "数据长度"],
  "target_fields": ["参数", "类型", "值域"],
  "threshold": 0.75
}
```

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "auto_mappings": [
      { "source": ["参数名称"], "target": "参数", "confidence": 0.95, "type": "auto" }
    ],
    "remaining_sources": ["数据长度"],
    "remaining_targets": ["类型", "值域"]
  }
}
```

---

### POST /api/mapping/apply 【reserved】

应用用户定义的字段映射配置，并写入知识库和用户映射持久化文件。

**请求体**：
```json
{
  "task_id": "550e8400-...",
  "mappings": [
    { "original": "参数名称", "target": "参数", "confidence": 0.9 },
    { "original": "数据类型", "target": "类型", "confidence": 0.85 }
  ]
}
```

---

### GET /api/mapping/suggest/{task_id} 【reserved】

获取提取字段的详细匹配建议（分类：exact_matches / fuzzy_matches / alias_matches / unmatched）。

### POST /api/mapping/custom 【reserved】

添加单条自定义字段映射。

**请求体**：
```json
{
  "source": "参数名称",
  "target": "参数",
  "table_id": "BC-RT1"
}
```

### GET /api/mapping/user-mappings 【reserved】

获取用户所有自定义映射列表。

### POST /api/mapping/user-mappings 【reserved】

添加用户自定义映射（同时写入知识库）。

### DELETE /api/mapping/user-mappings/{original_field} 【reserved】

删除指定的用户自定义映射。

---

## 五、协议匹配 (Match) 【reserved】

### POST /api/match/parse-protocol

从通信协议文本或文档中提取字段。

**请求格式**（二选一）：
- `multipart/form-data`：上传文档文件（`file` 字段）
- `application/json`：传入文本（`text` 字段）

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "fields": ["序号", "参数", "数据类型", "字节数", "单位", "备注"]
  }
}
```

---

### POST /api/match/parse-target-headers

解析目标表格（Word/Excel/CSV）的表头。

**请求格式**：`multipart/form-data`，`file` 字段上传文件。

---

### POST /api/match/save-mapping

保存一次人工匹配的映射关系，并写入知识库。

**请求体**：
```json
{
  "table_id": "BC-RT1",
  "mapping": [
    { "source": "参数名称", "target": "参数", "confidence": 0.9 },
    { "source": "数据类型", "target": "类型", "confidence": 0.85 }
  ],
  "operator": "user_001"
}
```

---

## 六、批量处理 (Batch) 【reserved】

### POST /api/batch/upload

上传 CSV/Excel 文件并创建批量处理任务。

**请求格式**：`multipart/form-data`

| 参数 | 类型 | 说明 |
|------|------|------|
| `file` | File | CSV 或 Excel 文件 |
| `options[table_id]` | string | 表标识（可选） |
| `options[strategy]` | string | 策略：`strict`（严格）/ `fuzzy`（模糊） |
| `options[overwrite]` | string | 是否覆盖：`true` / `false` |

---

### GET /api/batch/status/{task_id}

查询批量任务状态（`queued` / `running` / `success` / `failed`），含 `processed_count` / `total_count`。

### GET /api/batch/download/{task_id}

下载批量处理结果 Excel 文件。

---

## 七、字段配置 (Config) 【reserved】

> 当前版本字段配置由前端使用 localStorage 管理，后端接口已完整实现供后续使用。

### GET /api/config/protocol-fields

获取协议字段列表。

### POST /api/config/protocol-fields/upsert

新增或更新协议字段。请求体：`{ "id?": string, "name": string }`

### POST /api/config/protocol-fields/delete

删除协议字段。请求体：`{ "id": string }`

### GET /api/config/target-fields

获取目标字段列表。

### POST /api/config/target-fields/upsert

新增或更新目标字段。请求体：`{ "id?": string, "name": string }`

### POST /api/config/target-fields/delete

删除目标字段。请求体：`{ "id": string }`

---

## 八、模板管理 (Templates) 【reserved】

> 当前版本提取模板由前端使用 localStorage 管理，后端接口已完整实现供后续使用。

### GET /api/templates/list

获取提取模板列表。

### POST /api/templates/upsert

新增或更新模板。请求体：`{ "id?": string, "name": string, "field_ids": string[] }`

### POST /api/templates/delete

删除模板。请求体：`{ "id": string }`

---

## 九、历史记录 (History) 【reserved】

### GET /api/history

获取历史任务记录列表（分页）。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | integer | 否 | 1 | 页码 |
| `page_size` | integer | 否 | 20 | 每页条数 |

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": "a1b2c3d4",
        "time": "2026-05-21T10:30:00",
        "file": "测试协议20251216.docx",
        "status": "success",
        "detail": "PD控制指令 (表数: 3)",
        "message": ""
      }
    ],
    "total": 42
  }
}
```

---

## 十、接口汇总表

| 序号 | 方法 | 路径 | 模块 | 状态 |
|------|------|------|------|------|
| 1 | GET | `/api/dashboard/recent` | 仪表盘 | active |
| 2 | POST | `/api/extract/start` | 文档提取 | active |
| 3 | GET | `/api/extract/status/{task_id}` | 文档提取 | active |
| 4 | GET | `/api/extract/download/{task_id}` | 文档提取 | active |
| 5 | GET | `/api/knowledge/list` | 知识库 | active |
| 6 | POST | `/api/knowledge/query` | 知识库 | active |
| 7 | POST | `/api/knowledge/upsert` | 知识库 | reserved |
| 8 | GET | `/api/knowledge/stats` | 知识库 | reserved |
| 9 | GET | `/api/mapping/preview/{task_id}` | 字段映射 | active |
| 10 | POST | `/api/mapping/batch-suggest` | 字段映射 | active |
| 11 | POST | `/api/mapping/auto-map` | 字段映射 | active |
| 12 | POST | `/api/mapping/apply` | 字段映射 | reserved |
| 13 | GET | `/api/mapping/suggest/{task_id}` | 字段映射 | reserved |
| 14 | POST | `/api/mapping/custom` | 字段映射 | reserved |
| 15 | GET | `/api/mapping/user-mappings` | 字段映射 | reserved |
| 16 | POST | `/api/mapping/user-mappings` | 字段映射 | reserved |
| 17 | DELETE | `/api/mapping/user-mappings/{field}` | 字段映射 | reserved |
| 18 | POST | `/api/match/parse-protocol` | 协议匹配 | reserved |
| 19 | POST | `/api/match/parse-target-headers` | 协议匹配 | reserved |
| 20 | POST | `/api/match/save-mapping` | 协议匹配 | reserved |
| 21 | POST | `/api/batch/upload` | 批量处理 | reserved |
| 22 | GET | `/api/batch/status/{task_id}` | 批量处理 | reserved |
| 23 | GET | `/api/batch/download/{task_id}` | 批量处理 | reserved |
| 24 | GET | `/api/config/protocol-fields` | 字段配置 | reserved |
| 25 | POST | `/api/config/protocol-fields/upsert` | 字段配置 | reserved |
| 26 | POST | `/api/config/protocol-fields/delete` | 字段配置 | reserved |
| 27 | GET | `/api/config/target-fields` | 字段配置 | reserved |
| 28 | POST | `/api/config/target-fields/upsert` | 字段配置 | reserved |
| 29 | POST | `/api/config/target-fields/delete` | 字段配置 | reserved |
| 30 | GET | `/api/templates/list` | 模板管理 | reserved |
| 31 | POST | `/api/templates/upsert` | 模板管理 | reserved |
| 32 | POST | `/api/templates/delete` | 模板管理 | reserved |
| 33 | GET | `/api/history` | 历史记录 | reserved |
| 34 | GET | `/health` | 系统健康 | active |

---

> **文档版本**：v2.0  
> **实现状态**：34 个接口全部实现，5 个 active + 28 个 reserved + 1 个 health  
> **基于代码**：`backend/routes/` 下 9 个路由模块的实际代码