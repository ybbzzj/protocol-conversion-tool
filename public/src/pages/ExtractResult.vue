<template>
  <div class="container">
    <h2>提取结果</h2>

    <section class="card" v-if="lastResult">
      <h3>最近一次提取</h3>
      <p class="hint">文件：{{ lastResult.filename || '未记录文件名' }}</p>
      <p class="hint">任务：{{ lastResult.taskId }}</p>
      <p class="hint">完成时间：{{ formatTime(lastResult.completedAt) }}</p>
      <p class="hint" v-if="qualityText">映射质量：{{ qualityText }}</p>

      <label class="hint option-row">
        <input type="checkbox" v-model="downloadRemoveCrc" />
        下载时删除 CRC 校验字行（仅当该行为末行或其下一行无有效数据）
      </label>

      <div class="actions">
        <button class="btn" @click="downloadResult">下载结果</button>
        <button class="btn secondary" @click="goMapping">人工处理</button>
        <button class="btn secondary" @click="reload">刷新</button>
      </div>
    </section>

    <section class="card" v-else>
      <h3>暂无提取结果</h3>
      <p class="hint">完成一次文档提取后，这里会展示最近一次提取任务。</p>
      <button class="btn" @click="router.push({ name: 'extract' })">去提取</button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { endpoints } from '../api'
import { useToastStore, useLoadingStore } from '../stores/ui'

type LastExtractResult = {
  taskId: string
  filename?: string
  completedAt?: string
  mapping_quality?: any
}

const LS_LAST_EXTRACT_RESULT = 'last_extract_result'

const router = useRouter()
const toast = useToastStore()
const loading = useLoadingStore()
const lastResult = ref<LastExtractResult | null>(null)
const downloadRemoveCrc = ref(false)

const qualityText = computed(() => {
  const q = lastResult.value?.mapping_quality
  if (!q || q.score === undefined) return ''
  return `${(q.score * 100).toFixed(1)}%（精确 ${q.exact_count || 0}，模糊 ${q.fuzzy_count || 0}，未匹配 ${q.unmatched_count || 0}）`
})

function reload() {
  try {
    const raw = localStorage.getItem(LS_LAST_EXTRACT_RESULT)
    lastResult.value = raw ? JSON.parse(raw) : null
  } catch {
    lastResult.value = null
  }
}

function formatTime(value?: string) {
  if (!value) return '未记录'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

function goMapping() {
  if (!lastResult.value?.taskId) {
    toast.show('任务ID缺失')
    return
  }
  router.push({ name: 'mapping', params: { taskId: lastResult.value.taskId } })
}

async function downloadResult() {
  const taskId = lastResult.value?.taskId
  if (!taskId) {
    toast.show('任务ID缺失')
    return
  }
  try {
    loading.start('下载中...')
    const params = new URLSearchParams()
    if (downloadRemoveCrc.value) {
      params.set('remove_crc', 'true')
    }
    const downloadUrl = `${endpoints.extractDownload(taskId)}${params.toString() ? `?${params.toString()}` : ''}`
    const response = await fetch(downloadUrl)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const filename = `${(lastResult.value?.filename || `result_${taskId.slice(0, 8)}`).replace(/\.[^\.]*$/, '')}.xlsx`
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
  } catch (e: any) {
    toast.show('下载失败: ' + (e.message || '未知错误'))
  } finally {
    loading.stop()
  }
}

onMounted(reload)
</script>

<style scoped>
.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
