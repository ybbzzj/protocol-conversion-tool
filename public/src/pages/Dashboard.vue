<template>
  <div class="container">
    <div class="card">
      <h2>首页</h2>
      <p class="status">展示最近的匹配、任务统计。</p>
      
      <div class="grid grid-2">
        <div>
          <h3>最近处理</h3>
          <table class="table">
            <thead><tr><th>时间</th><th>表格来源</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="item in recent" :key="item.id">
                <td>{{ item.time }}</td>
                <td>{{ item.table }}</td>
                <td><span class="badge">{{ item.status }}</span></td>
              </tr>
              <tr v-if="recent.length === 0">
                <td colspan="3" style="text-align: center; color: var(--text-secondary); padding: 16px;">暂无记录</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div>
          <h3>统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="label">总任务</div>
              <div class="value">{{ stats.total }}</div>
            </div>
            <div class="stat-item success">
              <div class="label">成功</div>
              <div class="value">{{ stats.success }}</div>
            </div>
            <div class="stat-item fail">
              <div class="label">失败</div>
              <div class="value">{{ stats.fail }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, endpoints } from '../api'
import { useLoadingStore, useToastStore } from '../stores/ui'
const recent = ref<any[]>([])
const stats = ref({ total: 0, success: 0, fail: 0 })
const loading = useLoadingStore(); const toast = useToastStore()

onMounted(async ()=>{
  loading.start('加载首页...')
  try{ const { data } = await api.get(endpoints.dashboardRecent); recent.value = data?.data?.recent || []; stats.value = data?.data?.stats || stats.value }
  catch(err:any){ toast.show(err?.message || '加载失败') }
  finally{ loading.stop() }
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.stat-item {
  background: #f8fafc;
  padding: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  text-align: center;
}
.stat-item .label {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 4px;
}
.stat-item .value {
  color: var(--text-main);
  font-size: 24px;
  font-weight: 600;
}
.stat-item.success .value { color: #10b981; }
.stat-item.fail .value { color: #ef4444; }
</style>
