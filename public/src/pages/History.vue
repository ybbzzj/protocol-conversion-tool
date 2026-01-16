<template>
  <div class="container">
    <div class="card">
      <h2>历史记录</h2>
      <table class="table">
        <thead><tr><th>时间</th><th>文件</th><th>状态</th><th>详情</th></tr></thead>
        <tbody>
          <tr v-for="h in history" :key="h.id">
            <td>{{ h.time }}</td>
            <td>{{ h.file }}</td>
            <td><span class="badge">{{ h.status }}</span></td>
            <td>{{ h.detail }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, endpoints } from '../api'
import { useLoadingStore, useToastStore } from '../stores/ui'
const history = ref<any[]>([])
const loading = useLoadingStore(); const toast = useToastStore()

onMounted(async ()=>{
  loading.start('加载历史记录...')
  try{ const { data } = await api.get(endpoints.historyList); history.value = data?.data?.list || [] }
  catch(err:any){ toast.show(err?.message || '加载失败') }
  finally{ loading.stop() }
})
</script>