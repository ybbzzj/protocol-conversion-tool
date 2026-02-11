<template>
  <div class="container">
    <h2>文档提取</h2>

    <section class="card">
      <h3>选择协议字段</h3>
      <div class="actions">
        <input class="input" v-model="fieldSearch" placeholder="搜索字段..." style="max-width: 300px;" />
        <button class="btn" @click="doSearch">搜索</button>
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
      <input type="file" accept=".doc,.docx" @change="onFileChange" class="input" style="padding: 8px;" />
      <p class="hint">支持 .doc/.docx</p>
    </section>

    <section class="card">
      <div class="flex">
        <button class="btn" @click="startExtract">开始提取</button>
        <span v-if="taskStatus" class="status">状态：{{ taskStatus.status }}（进度：{{ taskStatus.progress }}%）</span>
      </div>
      
      <div v-if="taskStatus?.status==='success'" class="result" style="margin-top: 16px;">
        <button class="btn" @click="downloadResult">下载结果</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api, endpoints } from '../api'
import { useToastStore, useLoadingStore } from '../stores/ui'

type FieldItem = { id:string, name:string }
type TemplateItem = { id:string, name:string, field_ids:string[] }

const toast = useToastStore()
const loading = useLoadingStore()

// 本地存储 Key
const LS_PROTOCOL_FIELDS = 'local_protocol_fields'
const LS_TEMPLATES = 'local_extract_templates'

const protocolFields = ref<FieldItem[]>([])
const templates = ref<TemplateItem[]>([])
const selectedFieldIds = ref<string[]>([])
const selectedTemplateId = ref<string>('')
const templateName = ref('')
const fieldSearch = ref('')

const fileObj = ref<File | null>(null)
const currentTaskId = ref<string>('')
const taskStatus = ref<{ status:string, progress:number, message?:string } | null>(null)
let pollTimer: any = null

const tplImportInputRef = ref<HTMLInputElement | null>(null)

const filteredFields = computed(()=>{
  const q = fieldSearch.value.trim().toLowerCase()
  return q ? protocolFields.value.filter(f=>f.name.toLowerCase().includes(q)) : protocolFields.value
})

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
  fileObj.value = input.files && input.files[0] ? input.files[0] : null
}

async function startExtract(){
  if(selectedFieldIds.value.length===0){ toast.show('请选择协议字段'); return }
  if(!fileObj.value){ toast.show('请上传协议文档'); return }
  try{
    loading.start('创建提取任务...')
    const fd = new FormData()
    fd.append('file', fileObj.value)
    // 正确方式: 为每个 field_id 添加独立的表单字段，后端用 request.form.getlist() 获取
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
        if(st.status==='success') toast.show('提取完成，可下载结果')
        else toast.show('提取失败：'+(st.message||''))
      }
    }catch(e:any){ /* 静默或展示错误 */ }
  }, 2000)
}

function stopPolling(){ if(pollTimer){ clearInterval(pollTimer); pollTimer=null } }

async function downloadResult(){
  if(!currentTaskId.value){ toast.show('任务ID缺失'); return }
  try{
    loading.start('下载中...')
    // ✅ 使用 fetch 下载文件（比 window.open 更可靠）
    const response = await fetch(endpoints.extractDownload(currentTaskId.value))
    if(!response.ok){ throw new Error(`HTTP ${response.status}`) }
    
    // 获取文件名（从 Content-Disposition 头）
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `result_${currentTaskId.value.slice(0, 8)}.xlsx`
    if(contentDisposition){
      const matches = contentDisposition.match(/filename[^;=\n]*=((["\']*).*?\2|[^;\n]*)/)
      if(matches && matches[1]) filename = matches[1].replace(/["\\']/g, '')
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
</style>
