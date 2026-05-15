# 后端API接口文档

## 基础约定
- **统一前缀**: `/api`
- **响应格式**: `{ code:number, message:string, data:any }`
- **错误码**:
  - `0`: 成功
  - `40001`: 参数错误
  - `40002`: 文件解析失败
  - `40401`: 资源不存在
  - `50001`: 内部错误

## 接口状态说明
- active：当前前端正在使用，后端需实现并保证可用
- reserved：前端暂未使用（预留/可选），后端可按需实现
- deprecated：当前版本前端已移除或改为本地存储，不再调用

---

## 仪表盘与历史

GET /api/dashboard/recent  【active】
- 描述：获取最近处理的任务与统计
- 响应：{ data: { recent: Array<{id:string,time:string,table:string,status:string}>, stats:{ total:number, success:number, fail:number } } }

GET /api/history  【reserved】
- 描述：获取历史记录列表
- 查询参数：page, page_size
- 响应：{ data: { list: Array<{id:string,time:string,file:string,status:string,detail:string}>, total:number } }

---

## 文档提取流程

**POST /api/extract/start**  【active】
- 描述：创建文档提取任务
- 请求体：`multipart/form-data`
  - `file`: Word文档文件(.doc/.docx)
  - `field_ids`: 协议字段ID数组
- 响应：`{ data: { task_id:string } }`

**GET /api/extract/status/{task_id}**  【active】
- 描述：查询任务执行状态
- 响应：`{ data: { status:queued|running|success|failed, progress:number, message?:string } }`

**GET /api/extract/preview/{task_id}**  【新增】
- 描述：预览提取结果和字段映射建议
- 响应：`{ data: { extracted_fields:array, mapping_suggestions:array, unmatched_fields:array } }`

**POST /api/extract/apply-mapping**  【新增】
- 描述：应用用户定义的字段映射配置
- 请求体：`{ task_id:string, mappings:array }`
- 响应：`{ data: { success:boolean } }`

**GET /api/extract/download/{task_id}**  【active】
- 描述：下载处理结果文件
- 响应：Excel文件流(`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)

---

## 知识库管理

**GET /api/knowledge/list**  【active】
- 描述：分页获取知识库条目
- 查询参数：`q?, table_id?, page?, page_size?`
- 响应：`{ data: { list: Array<{ id:string, table_id:string, source:string, target:string, hits:number, confidence:number }>, total:number } }`

**POST /api/knowledge/query**  【active】
- 描述：查询字段匹配建议
- 请求体：`{ source:string, table_id?:string, context?:string }`
- 响应：`{ data: { candidates: Array<{ target:string, confidence:number, match_type:'exact'|'fuzzy'|'semantic' }> } }`

**POST /api/knowledge/upsert**  【reserved】
- 描述：新增或更新知识库映射
- 请求体：`{ id?:string, table_id:string, source:string, target:string, confidence?:number }`
- 响应：`{ data: { id:string } }`

**GET /api/knowledge/stats**  【reserved】
- 描述：知识库统计信息
- 响应：`{ data: { total:number, by_table: Array<{ table_id:string, count:number }>, top_hits: Array<{ source:string, target:string, hits:number }> } }`

---

## 人工匹配  【reserved】

POST /api/match/parse-protocol
- 描述：解析通信协议文本或文档，抽取协议字段（由后端完成）
- 请求：multipart/form-data 或 application/json
  - body: { text?:string, file?:File }
- 响应：{ data: { fields: string[] } }

POST /api/match/parse-target-headers
- 描述：解析目标表格（word/Excel/CSV）表头（由后端完成）
- 请求：multipart/form-data
  - file: File
- 响应：{ data: { headers: string[] } }

POST /api/match/save-mapping
- 描述：保存一次人工匹配的映射关系，并可写入知识库
- 请求：application/json
  - body: { table_id:string, mapping: Array<{ source:string, target:string, confidence?:number }>, operator?:string }
- 响应：{ data: { id:string } }

---

## 批量处理  【reserved】

POST /api/batch/upload
- 描述：上传待处理的 CSV/Excel 文件并创建任务（由后端解析并处理）
- 请求：multipart/form-data
  - file: File
  - options?: { table_id?:string, strategy?:'strict'|'fuzzy', overwrite?:boolean }
- 响应：{ data: { task_id:string } }

GET /api/batch/status/{task_id}
- 描述：查询批量任务状态（后端维护队列与进度）
- 响应：{ data: { task_id:string, status:'queued'|'running'|'success'|'failed', progress:number, message?:string } }

GET /api/batch/download/{task_id}
- 描述：下载批量处理结果（Excel 文件流）
- 响应：application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

---

## 字段配置  【deprecated】
说明：当前版本协议字段与目标字段均由前端使用 localStorage 管理（支持导入/导出备份），前端不会调用后端接口。本节作为后续后端实现的参考（预留形态）。

GET /api/config/protocol-fields  【reserved】
- 描述：获取协议字段列表
- 响应：{ data: { list: Array<{ id:string, name:string }> } }

POST /api/config/protocol-fields/upsert  【reserved】
- 描述：新增或更新协议字段
- 请求：{ id?:string, name:string }
- 响应：{ data: { id:string } }

POST /api/config/protocol-fields/delete  【reserved】
- 描述：删除协议字段
- 请求：{ id:string }
- 响应：{ code:0 }

GET /api/config/target-fields  【reserved】
- 描述：获取目标字段列表
- 响应：{ data: { list: Array<{ id:string, name:string }> } }

POST /api/config/target-fields/upsert  【reserved】
- 描述：新增或更新目标字段
- 请求：{ id?:string, name:string }
- 响应：{ data: { id:string } }

POST /api/config/target-fields/delete  【reserved】
- 描述：删除目标字段
- 请求：{ id:string }
- 响应：{ code:0 }

---

## 提取模板  【deprecated】
说明：当前版本提取模板由前端使用 localStorage 管理（支持导入/导出备份），前端不会调用后端接口。本节作为后续后端实现的参考（预留形态）。

GET /api/templates/list  【reserved】
- 描述：获取模板列表
- 响应：{ data: { list: Array<{ id:string, name:string, field_ids:string[] }> } }

POST /api/templates/upsert  【reserved】
- 描述：新增或更新模板
- 请求：{ id?:string, name:string, field_ids:string[] }
- 响应：{ data: { id:string } }

POST /api/templates/delete  【reserved】
- 描述：删除模板
- 请求：{ id:string }
- 响应：{ code:0 }

---



