<template>
  <div class="container">
    <div class="card">
      <h2>批量处理</h2>
      <div style="margin: 20px 0;">
        <input type="file" class="input" @change="onFile" accept=".csv,.xls,.xlsx" style="padding: 12px;" />
        <div class="status" v-if="fileName" style="margin-top: 8px;">已选择：{{ fileName }}</div>
      </div>
      
      <div class="flex">
        <button class="btn" @click="start" :disabled="!file || running">开始处理</button>
        <button class="btn secondary" @click="download" :disabled="!canDownload">导出结果</button>
      </div>
      
      <div class="card" v-if="running" style="margin-top: 24px; background: #f8fafc; border: none;">
        <div class="flex"><span class="loader"></span> <span>处理进度：{{ progress }}%</span></div>
      </div>
      
      <div class="card" v-if="error" style="margin-top: 24px; border-color: var(--danger); background: #fef2f2;">
        <strong style="color: var(--danger);">错误：</strong> {{ error }}
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { api, endpoints } from '../api'
import { useLoadingStore, useToastStore } from '../stores/ui'
const loading = useLoadingStore(); const toast = useToastStore()

const file = ref<File|null>(null)
const fileName = ref('')
const running = ref(false)
const progress = ref(0)
const error = ref('')
const taskId = ref('')
const canDownload = ref(false)

function onFile(e: Event){ const f = (e.target as HTMLInputElement).files?.[0]; if(!f) return; file.value = f; fileName.value = f.name }

async function start(){
  if(!file.value) return
  error.value = ''
  running.value = true
  progress.value = 0
  loading.start('上传并创建任务...')
  try{
    const fd = new FormData(); fd.append('file', file.value)
    const { data } = await api.post(endpoints.batchUpload, fd)
    taskId.value = data?.data?.task_id || ''
    toast.show(taskId.value ? `任务已创建：${taskId.value}` : '任务创建成功')
    loading.stop()
    pollStatus()
  }catch(err:any){
    loading.stop(); running.value=false; error.value = err?.message || String(err)
  }
}

let timer: any
async function pollStatus(){
  if(!taskId.value){ running.value=false; return }
  timer && clearInterval(timer)
  timer = setInterval(async ()=>{
    try{
      const { data } = await api.get(endpoints.batchStatus(taskId.value))
      const st = data?.data?.status; const p = data?.data?.progress ?? 0
      progress.value = Math.min(100, Number(p))
      if(st==='success'){ clearInterval(timer); running.value=false; progress.value=100; canDownload.value = true; toast.show('处理完成') }
      else if(st==='failed'){ clearInterval(timer); running.value=false; error.value = data?.data?.message || '处理失败' }
    }catch(err:any){ clearInterval(timer); running.value=false; error.value = err?.message || String(err) }
  }, 1000)
}

function download(){ if(!taskId.value) return; window.open(endpoints.batchDownload(taskId.value), '_blank') }
</script>
