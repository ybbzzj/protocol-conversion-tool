<template>
  <div class="container">
    <h2>文档提取</h2>

    <section class="card">
      <h3>选择协议字段</h3>
      <div class="actions">
        <input class="input" v-model="fieldSearch" placeholder="搜索字段..." style="max-width: 300px;" />
        <button class="btn" @click="doSearch">搜索</button>
        <button class="btn secondary" @click="toggleSelectAll">{{ isAllSelected ? '取消全选' : '全选' }}</button>
        <button class="btn secondary" @click="reloadProtocolFields">刷新</button>
      </div>
      <div class="field-list">
        <label v-for="f in filteredFields" :key="f.id" class="field-item">
          <input type="checkbox" :value="f.id" v-model="selectedFieldIds" /> {{ f.name }}
        </label>
      </div>
      <p class="hint">可多选。可在“字段配置”页面维护。</p>
    </section>

    <section class="card">
      <h3>提取模板</h3>
      <div class="template-row">
        <select class="input" v-model="selectedTemplateId" style="max-width: 300px;">
          <option value="">选择已有模板...</option>
          <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
        <button class="btn" @click="applyTemplate">应用模板</button>
        <button class="btn secondary" @click="reloadTemplates">刷新</button>
      </div>
      <div class="template-save">
        <input class="input" v-model="templateName" placeholder="输入模板名称" style="max-width: 300px;" />
        <button class="btn" @click="saveTemplate">保存当前选择为模板</button>
        <button class="btn danger" @click="deleteTemplate">删除选中模板</button>
      </div>
      <div class="template-backup">
        <button class="btn secondary" @click="exportTemplates">导出模板（JSON）</button>
        <button class="btn secondary" @click="triggerImportTemplates">导入模板（JSON）</button>
        <input ref="tplImportInputRef" type="file" accept="application/json,.json" style="display:none" @change="onImportTemplatesChange" />
        <p class="hint" style="margin:0">导入时按模板名称合并去重，仅添加不存在名称的模板。</p>
      </div>
    </section>

    <section class="card">
      <h3>上传协议文档</h3>
      <input type="file" accept=".docx" @change="onFileChange" class="input" style="padding: 8px;" />
      <p class="hint">支持 .docx</p>
    </section>

    <section class="card">
      <h3>输出控制</h3>
      <div class="output-options">
        <label class="option-item">
          <input type="checkbox" v-model="removeCrc" />
          <span>删除末尾 CRC 校验字行</span>
        </label>
        <p class="hint">勾选后，若表格数据最后一项为 CRC 校验字/校验码，将从结果中剔除。</p>
      </div>
    </section>

    <section class="card">
      <div class="flex">
        <button class="btn" @click="startExtract">开始提取</button>
        <span v-if="taskStatus" class="status">状态：{{ taskStatus.status }}（进度：{{ taskStatus.progress }}%）</span>
      </div>

      <div v-if="taskStatus && taskStatus.status!=='success' && taskStatus.status!=='failed'" class="progress-wrap">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (taskStatus.progress || 0) + '%' }"></div>
        </div>
      </div>

      <div v-if="taskStatus?.status==='success'" class="result" style="margin-top: 16px;">
        <button class="btn" @click="downloadResult">下载结果</button>
      </div>
    </section>

    <!-- 提取完成结果弹窗：无论匹配质量如何，由用户选择下一步 -->
    <div v-if="modalVisible" class="modal-mask" @click.self="modalVisible=false">
      <div class="modal-box">
        <h3 class="modal-title">提取完成</h3>
        <p class="modal-sub">字段匹配率 <b>{{ coveragePercent }}%</b></p>

        <!-- 维度一：期望覆盖（按用户选取的协议字段数计算匹配率） -->
        <div class="modal-group">
          <div class="modal-group-title">期望覆盖</div>
          <div class="modal-stats">
            <div class="stat-row">
              <span class="stat-label">已选协议字段</span>
              <span class="stat-val">{{ resultModal.expected }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label"><i class="dot dot-ok"></i>本次覆盖</span>
              <span class="stat-val">{{ resultModal.covered }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">覆盖率</span>
              <span class="stat-val">{{ coveragePercent }}%</span>
            </div>
          </div>
        </div>

        <!-- 维度二：映射质量（程序提取到的全部字段去向） -->
        <div class="modal-group">
          <div class="modal-group-title">映射质量</div>
          <div class="modal-stats">
            <div class="stat-row">
              <span class="stat-label">提取字段</span>
              <span class="stat-val">{{ resultModal.total }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label"><i class="dot dot-ok"></i>已映射</span>
              <span class="stat-val">{{ resultModal.auto }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label"><i class="dot dot-warn"></i>待人工匹配</span>
              <span class="stat-val">{{ resultModal.manual }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label"><i class="dot dot-err"></i>其中未匹配</span>
              <span class="stat-val">{{ resultModal.unmatched }}</span>
            </div>
          </div>
        </div>

        <p class="modal-hint">匹配率按已选协议字段计算；提取字段中难匹配的会进入人工匹配左侧待处理。建议核对后再下载。</p>
        <div class="modal-actions">
          <button class="btn secondary" @click="downloadFromModal">直接下载</button>
          <button class="btn" @click="gotoMapping">进入人工匹配</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api, endpoints } from '../api'
import { useToastStore, useLoadingStore } from '../stores/ui'

type FieldItem = { id:string, name:string, isIdField?:boolean }
type TemplateItem = { id:string, name:string, field_ids:string[] }

const toast = useToastStore()
const loading = useLoadingStore()
const router = useRouter()

// 本地存储 Key
const LS_PROTOCOL_FIELDS = 'local_protocol_fields'
const LS_TEMPLATES = 'local_extract_templates'

const protocolFields = ref<FieldItem[]>([])
const templates = ref<TemplateItem[]>([])
const selectedFieldIds = ref<string[]>([])
const selectedTemplateId = ref<string>('')
const templateName = ref('')
const fieldSearch = ref('')

// 输出控制选项：默认删除末尾 CRC 校验字行
const removeCrc = ref(true)

const fileObj = ref<File | null>(null)
const currentTaskId = ref<string>('')
const originalFilename = ref<string>('')
const taskStatus = ref<{ status:string, progress:number, message?:string } | null>(null)
let pollTimer: any = null

// 提取完成后的结果选择弹窗
const modalVisible = ref(false)
const resultModal = ref<{ score:number, total:number, auto:number, manual:number, unmatched:number, expected:number, covered:number, coverage:number }>({
  score: 0, total: 0, auto: 0, manual: 0, unmatched: 0, expected: 0, covered: 0, coverage: 0
})
const coveragePercent = computed(()=> (resultModal.value.coverage * 100).toFixed(1))

const tplImportInputRef = ref<HTMLInputElement | null>(null)

const filteredFields = computed(()=>{
  const q = fieldSearch.value.trim().toLowerCase()
  return q ? protocolFields.value.filter(f=>f.name.toLowerCase().includes(q)) : protocolFields.value
})

const isAllSelected = computed(() => {
  return filteredFields.value.length > 0 && filteredFields.value.every(f => selectedFieldIds.value.includes(f.id))
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    // 如果已经全选，则在当前筛选结果中取消选中
    const filteredIds = filteredFields.value.map(f => f.id)
    selectedFieldIds.value = selectedFieldIds.value.filter(id => !filteredIds.includes(id))
  } else {
    // 如果未全选，则将当前筛选结果全部加入选中列表（去重）
    const filteredIds = filteredFields.value.map(f => f.id)
    const newIds = [...new Set([...selectedFieldIds.value, ...filteredIds])]
    selectedFieldIds.value = newIds
  }
}

function saveFieldsToLocal(items: FieldItem[]){ localStorage.setItem(LS_PROTOCOL_FIELDS, JSON.stringify(items)) }
function loadFieldsFromLocal(): FieldItem[]{ try{ const raw = localStorage.getItem(LS_PROTOCOL_FIELDS); return raw ? JSON.parse(raw) : [] } catch{ return [] } }

function saveTemplatesToLocal(items: TemplateItem[]){ localStorage.setItem(LS_TEMPLATES, JSON.stringify(items)) }
function loadTemplatesFromLocal(): TemplateItem[]{ try{ const raw = localStorage.getItem(LS_TEMPLATES); return raw ? JSON.parse(raw) : [] } catch{ return [] } }

function doSearch(){ /* 已通过 filteredFields 实时过滤，这里仅作为交互入口，无额外逻辑 */ }

function reloadProtocolFields(){
  protocolFields.value = loadFieldsFromLocal()
  if(protocolFields.value.length === 0){ toast.show('本地暂无协议字段，请先到“字段配置”页面添加') }
}

function reloadTemplates(){ templates.value = loadTemplatesFromLocal() }

function applyTemplate(){
  const t = templates.value.find(x=>x.id===selectedTemplateId.value)
  if(!t){ toast.show('请选择模板'); return }
  selectedFieldIds.value = [...(t.field_ids || [])]
}

function saveTemplate(){
  if(!templateName.value.trim()){ toast.show('请输入模板名称'); return }
  if(selectedFieldIds.value.length===0){ toast.show('请选择至少一个协议字段'); return }
  const id = `${Date.now()}`
  const list = loadTemplatesFromLocal()
  list.push({ id, name: templateName.value.trim(), field_ids: [...selectedFieldIds.value] })
  saveTemplatesToLocal(list)
  templates.value = list
  selectedTemplateId.value = id
  templateName.value = ''
  toast.show('模板已保存在前端本地')
}

function deleteTemplate(){
  if(!selectedTemplateId.value){ toast.show('请先选择模板'); return }
  const list = loadTemplatesFromLocal().filter(t=>t.id !== selectedTemplateId.value)
  saveTemplatesToLocal(list)
  templates.value = list
  selectedTemplateId.value = ''
  toast.show('模板已删除')
}

function exportTemplates(){
  const data = { templates: loadTemplatesFromLocal() }
  downloadJSON(data, `templates_backup_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.json`)
  toast.show('已导出模板 JSON')
}
function triggerImportTemplates(){ tplImportInputRef.value?.click() }
async function onImportTemplatesChange(ev: Event){
  const input = ev.target as HTMLInputElement
  const file = input.files && input.files[0] ? input.files[0] : null
  if(!file){ return }
  try{
    const text = await file.text()
    const json = JSON.parse(text)
    const incoming: TemplateItem[] = Array.isArray(json?.templates) ? json.templates : []
    const merged = mergeTemplatesByName(loadTemplatesFromLocal(), incoming)
    saveTemplatesToLocal(merged)
    templates.value = merged
    toast.show('模板导入成功，已按名称合并去重')
  }catch{ toast.show('导入失败：JSON 格式不正确') }
  finally{ input.value = '' }
}

function mergeTemplatesByName(existing: TemplateItem[], incoming: TemplateItem[]): TemplateItem[]{
  const map = new Map<string, TemplateItem>()
  for(const e of existing){ const name = (e?.name||'').trim(); if(!name) continue; map.set(name.toLowerCase(), e) }
  for(const i of incoming){
    const name = (i?.name||'').trim(); if(!name) continue
    const key = name.toLowerCase()
    if(!map.has(key)){
      const cleanIds = Array.isArray(i.field_ids) ? i.field_ids.filter(x=> typeof x==='string') : []
      map.set(key, { id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, name, field_ids: cleanIds })
    }
  }
  return Array.from(map.values())
}

function downloadJSON(data: any, filename: string){
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

function onFileChange(ev: Event){
  const input = ev.target as HTMLInputElement
  const f = input.files && input.files[0] ? input.files[0] : null
  if(f && f.name.toLowerCase().endsWith('.doc')){
    toast.show('不支持 .doc 格式，请用 Word 将文件另存为 .docx 后再上传')
    input.value = ''
    fileObj.value = null
    return
  }
  fileObj.value = f
  // 保存原始文件名
  if(fileObj.value){
    originalFilename.value = fileObj.value.name
  }
}

async function startExtract(){
  if(selectedFieldIds.value.length===0){ toast.show('请选择协议字段'); return }
  if(!fileObj.value){ toast.show('请上传协议文档'); return }
  try{
    loading.start('创建提取任务...')
    const fd = new FormData()
    fd.append('file', fileObj.value)
    // 输出控制：是否删除末尾 CRC 校验字行
    fd.append('remove_crc', removeCrc.value ? 'true' : 'false')
    // 正确方式: 为每个 field_id 添加独立的表单字段，后端用 request.form.getlist() 获取
    for(const fieldId of selectedFieldIds.value){
      fd.append('field_ids', fieldId)
    }
    // 同时传字段名：前端字段 id 是本地随机生成的，与后端配置 id 不一致，
    // 期望字段以名称为准，后端优先使用 field_names
    const idToField = new Map(protocolFields.value.map(f => [f.id, f]))
    for(const fieldId of selectedFieldIds.value){
      const field = idToField.get(fieldId)
      if(field){
        fd.append('field_names', field.name)
        // 如果该字段标记为ID表头，单独发送
        if(field.isIdField){ fd.append('id_field_names', field.name) }
      }
    }
    const { data } = await api.post(endpoints.extractStart, fd, { headers:{ 'Content-Type':'multipart/form-data' } })
    currentTaskId.value = data?.data?.task_id || ''
    if(!currentTaskId.value){ toast.show('未返回任务ID'); return }
    toast.show('任务已创建，开始查询进度')
    startPolling()
  }catch(e:any){ 
    console.error('创建任务失败:', e)
    toast.show('创建任务失败: ' + (e.response?.data?.message || e.message || '未知错误')) 
  }
  finally{ loading.stop() }
}

function startPolling(){
  stopPolling()
  pollTimer = setInterval(async()=>{
    try{
      const { data } = await api.get(endpoints.extractStatus(currentTaskId.value))
      const st = data?.data || { status:'queued', progress:0 }
      taskStatus.value = st
      if(st.status==='success' || st.status==='failed'){
        stopPolling()
        if(st.status==='success') {
          // 智能流程分流
          handleSmartWorkflow(st)
        } else {
          toast.show('提取失败：'+(st.message||''))
        }
      }
    }catch(e:any){ /* 静默或展示错误 */ }
  }, 2000)
}

function handleSmartWorkflow(statusData) {
  // 无论匹配质量如何，统一弹出选择弹窗，由用户决定进入人工匹配还是直接下载
  const quality = statusData.mapping_quality
  if (quality && quality.score !== undefined) {
    resultModal.value = {
      score: quality.score,
      total: quality.total ?? 0,
      auto: quality.auto_count ?? 0,
      manual: quality.manual_count ?? 0,
      unmatched: quality.unmatched_count ?? 0,
      expected: quality.expected_count ?? 0,
      covered: quality.covered_count ?? 0,
      coverage: quality.coverage ?? 0
    }
  } else {
    // 无质量评分时也给出弹窗，数字置零
    resultModal.value = { score: 0, total: 0, auto: 0, manual: 0, unmatched: 0, expected: 0, covered: 0, coverage: 0 }
  }
  modalVisible.value = true
}

function gotoMapping(){
  modalVisible.value = false
  router.push({ name: 'mapping', params: { taskId: currentTaskId.value } })
}

function downloadFromModal(){
  modalVisible.value = false
  downloadResult()
}

function stopPolling(){ if(pollTimer){ clearInterval(pollTimer); pollTimer=null } }

async function downloadResult(){
  if(!currentTaskId.value){ toast.show('任务ID缺失'); return }
  try{
    loading.start('下载中...')
    // ✅ 使用 fetch 下载文件（比 window.open 更可靠）
    const response = await fetch(endpoints.extractDownload(currentTaskId.value))
    if(!response.ok){ throw new Error(`HTTP ${response.status}`) }
    
    // 使用原始文件名作为下载文件名
    let filename = originalFilename.value
    // 如果原始文件名存在，移除扩展名并添加.xlsx
    if(filename){
      const nameWithoutExt = filename.replace(/\.[^\.]*$/, '')
      filename = `${nameWithoutExt}.xlsx`
    } else {
      // 回退到默认命名
      filename = `result_${currentTaskId.value.slice(0, 8)}.xlsx`
    }
    
    // 创建 blob 并下载
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    toast.show('下载完成')
  }catch(e:any){
    console.error('下载失败:', e)
    toast.show('下载失败: ' + (e.message || '未知错误'))
  }finally{
    loading.stop()
  }
}

onMounted(()=>{ reloadProtocolFields(); reloadTemplates() })
</script>

<style scoped>
.actions{ display:flex; gap:8px; margin-bottom:12px; align-items: center; }
.field-list{ display:flex; flex-wrap:wrap; gap:8px; max-height: 240px; overflow:auto; padding: 4px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); }
.field-item{ background:#f1f5f9; padding:6px 12px; border-radius:20px; font-size: 13px; display: flex; align-items: center; gap: 6px; cursor: pointer; transition: background 0.2s; }
.field-item:hover { background: #e2e8f0; }
.template-row{ display:flex; gap:8px; align-items:center; margin-bottom: 12px; }
.template-save{ display:flex; gap:8px; align-items:center; margin-bottom: 12px; }
.template-backup{ display:flex; gap:8px; align-items:center; }
.output-options{ display:flex; flex-direction:column; gap:4px; }
.option-item{ display:flex; align-items:center; gap:8px; cursor:pointer; font-size:14px; }
.progress-wrap{ margin-top:12px; }
.progress-bar{ width:100%; height:10px; background:#e2e8f0; border-radius:6px; overflow:hidden; }
.progress-fill{ height:100%; background:#007bff; border-radius:6px; transition:width 0.3s ease; }

/* 提取完成结果弹窗 */
.modal-mask{ position:fixed; inset:0; background:rgba(15,23,42,0.4); backdrop-filter:blur(2px); display:flex; align-items:center; justify-content:center; z-index:9999; }
.modal-box{ background:var(--bg-card); width:380px; max-width:calc(100vw - 32px); padding:24px; border-radius:var(--radius-md); box-shadow:var(--shadow-lg); }
.modal-title{ margin:0 0 4px; font-size:18px; color:var(--text-main); }
.modal-sub{ margin:0 0 16px; font-size:14px; color:var(--text-secondary); }
.modal-sub b{ color:var(--primary); font-size:16px; }
.modal-group{ margin-bottom:12px; }
.modal-group-title{ font-size:13px; font-weight:600; color:var(--text-main); margin-bottom:6px; }
.modal-stats{ display:flex; flex-direction:column; gap:8px; padding:10px 12px; background:#f8fafc; border:1px solid var(--border-color); border-radius:var(--radius-sm); }
.stat-row{ display:flex; justify-content:space-between; align-items:center; font-size:14px; }
.stat-label{ color:var(--text-secondary); display:flex; align-items:center; gap:6px; }
.stat-val{ color:var(--text-main); font-weight:600; }
.dot{ width:8px; height:8px; border-radius:50%; display:inline-block; }
.dot-ok{ background:#22c55e; }
.dot-warn{ background:#f59e0b; }
.dot-err{ background:#ef4444; }
.modal-hint{ margin:12px 0 16px; font-size:12px; color:var(--text-secondary); line-height:1.5; }
.modal-actions{ display:flex; gap:8px; justify-content:flex-end; }
</style>
