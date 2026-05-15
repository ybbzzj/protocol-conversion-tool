<template>
  <div class="container">
    <h2>字段配置</h2>

    <section class="card">
      <h3>备份与恢复</h3>
      <div class="row">
        <button class="btn" @click="exportAllFields">导出字段（JSON）</button>
        <button class="btn" @click="triggerImport">导入字段（JSON）</button>
        <input ref="importInputRef" type="file" accept="application/json,.json" style="display:none" @change="onImportFileChange" />
      </div>
      <p class="hint">导出文件包含协议字段与目标字段。导入时会按字段名称合并去重。</p>
    </section>

    <div class="grid">
      <section class="card">
        <h3>协议字段</h3>
        <div class="row">
          <input class="input" v-model="pfName" placeholder="字段名" />
          <button class="btn" @click="addProtocolField">新增</button>
          <button class="btn secondary" @click="refreshProtocolFields">刷新</button>
        </div>
        <table class="table">
          <thead><tr><th>名称</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in protocolFields" :key="item.id">
              <td>
                <input class="input" v-model="item.name" />
              </td>
              <td>
                <button class="btn" @click="saveProtocolField(item)">保存</button>
                <button class="btn danger" @click="deleteProtocolField(item)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card">
        <h3>目标字段</h3>
        <div class="row">
          <input class="input" v-model="tfName" placeholder="字段名" />
          <button class="btn" @click="addTargetField">新增</button>
          <button class="btn secondary" @click="refreshTargetFields">刷新</button>
        </div>
        <table class="table">
          <thead><tr><th>名称</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in targetFields" :key="item.id">
              <td>
                <input class="input" v-model="item.name" />
              </td>
              <td>
                <button class="btn" @click="saveTargetField(item)">保存</button>
                <button class="btn danger" @click="deleteTargetField(item)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToastStore } from '../stores/ui'

type FieldItem = { id:string, name:string }
const toast = useToastStore()

// 本地存储 Key
const LS_PROTOCOL_FIELDS = 'local_protocol_fields'
const LS_TARGET_FIELDS = 'local_target_fields'

const protocolFields = ref<FieldItem[]>([])
const targetFields = ref<FieldItem[]>([])
const pfName = ref('')
const tfName = ref('')

const importInputRef = ref<HTMLInputElement | null>(null)

function loadFromLS(key:string): FieldItem[]{ try{ const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : [] } catch{ return [] } }
function saveToLS(key:string, items: FieldItem[]){ localStorage.setItem(key, JSON.stringify(items)) }

function refreshProtocolFields(){ protocolFields.value = loadFromLS(LS_PROTOCOL_FIELDS) }
function refreshTargetFields(){ targetFields.value = loadFromLS(LS_TARGET_FIELDS) }

function addProtocolField(){
  const name = pfName.value.trim()
  if(!name){
    toast.show('请输入字段名')
    return
  }
  const items = loadFromLS(LS_PROTOCOL_FIELDS)
  const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  items.push({ id, name })
  saveToLS(LS_PROTOCOL_FIELDS, items)
  pfName.value=''
  refreshProtocolFields()
  toast.show('已新增协议字段')
}
function saveProtocolField(item: FieldItem){
  const items = loadFromLS(LS_PROTOCOL_FIELDS).map(x=> x.id===item.id ? { ...x, name:item.name.trim() } : x)
  saveToLS(LS_PROTOCOL_FIELDS, items)
  refreshProtocolFields()
  toast.show('协议字段已保存')
}
function deleteProtocolField(item: FieldItem){
  const items = loadFromLS(LS_PROTOCOL_FIELDS).filter(x=> x.id!==item.id)
  saveToLS(LS_PROTOCOL_FIELDS, items)
  refreshProtocolFields()
  toast.show('协议字段已删除')
}

function addTargetField(){
  const name = tfName.value.trim()
  if(!name){
    toast.show('请输入字段名')
    return
  }
  const items = loadFromLS(LS_TARGET_FIELDS)
  const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  items.push({ id, name })
  saveToLS(LS_TARGET_FIELDS, items)
  tfName.value=''
  refreshTargetFields()
  toast.show('已新增目标字段')
}
function saveTargetField(item: FieldItem){
  const items = loadFromLS(LS_TARGET_FIELDS).map(x=> x.id===item.id ? { ...x, name:item.name.trim() } : x)
  saveToLS(LS_TARGET_FIELDS, items)
  refreshTargetFields()
  toast.show('目标字段已保存')
}
function deleteTargetField(item: FieldItem){
  const items = loadFromLS(LS_TARGET_FIELDS).filter(x=> x.id!==item.id)
  saveToLS(LS_TARGET_FIELDS, items)
  refreshTargetFields()
  toast.show('目标字段已删除')
}

function exportAllFields(){
  const data = {
    protocolFields: loadFromLS(LS_PROTOCOL_FIELDS),
    targetFields: loadFromLS(LS_TARGET_FIELDS),
  }
  downloadJSON(data, `fields_backup_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.json`)
  toast.show('已导出字段 JSON')
}
function triggerImport(){ importInputRef.value?.click() }
async function onImportFileChange(ev: Event){
  const input = ev.target as HTMLInputElement
  const file = input.files && input.files[0] ? input.files[0] : null
  if(!file){ return }
  try{
    const text = await file.text()
    const json = JSON.parse(text)
    const incomingProtocol: FieldItem[] = Array.isArray(json?.protocolFields) ? json.protocolFields : []
    const incomingTarget: FieldItem[] = Array.isArray(json?.targetFields) ? json.targetFields : []
    // 以名称去重合并，保留现有字段code
    const mergedProtocol = mergeByName(loadFromLS(LS_PROTOCOL_FIELDS), incomingProtocol)
    const mergedTarget = mergeByName(loadFromLS(LS_TARGET_FIELDS), incomingTarget)
    saveToLS(LS_PROTOCOL_FIELDS, mergedProtocol)
    saveToLS(LS_TARGET_FIELDS, mergedTarget)
    refreshProtocolFields(); refreshTargetFields()
    toast.show('导入成功，已合并字段')
  }catch{ toast.show('导入失败：JSON 格式不正确') }
  finally{ input.value = '' }
}

function mergeByName(existing: FieldItem[], incoming: FieldItem[]): FieldItem[]{
  const map = new Map<string, FieldItem>()
  for(const e of existing){ const name = e.name.trim(); if(!name) continue; map.set(name.toLowerCase(), e) }
  for(const i of incoming){
    const name = (i?.name||'').trim(); if(!name) continue
    const key = name.toLowerCase()
    if(!map.has(key)){
      map.set(key, { id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, name })
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

onMounted(()=>{ refreshProtocolFields(); refreshTargetFields() })
</script>

<style scoped>
.row{ display:flex; gap:8px; margin-bottom:10px; }
</style>
