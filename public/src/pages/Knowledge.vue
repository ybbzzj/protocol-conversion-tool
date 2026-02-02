<template>
  <div class="container">
    <div class="card">
      <h2>知识库管理</h2>
      <div class="grid grid-2" style="margin-bottom: 24px;">
        <input class="input" v-model="q" placeholder="搜索关键字..." />
        <input class="input" v-model="tableId" placeholder="按来源 table_id 筛选..." />
      </div>
      
      <table class="table">
        <thead>
          <tr><th>来源(table_id)</th><th>源字段</th><th>目标字段</th><th>命中次数</th><th>置信度</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td>{{ item.table_id }}</td>
            <td>{{ item.source }}</td>
            <td>{{ item.target }}</td>
            <td>{{ item.hits }}</td>
            <td>{{ (item.confidence*100).toFixed(0) }}%</td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 32px;">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, endpoints } from '../api'
import { useLoadingStore, useToastStore } from '../stores/ui'
const q = ref(''); const tableId = ref('')
const items = ref<any[]>([])
const loading = useLoadingStore(); const toast = useToastStore()

onMounted(async ()=>{
  loading.start('加载知识库...')
  try{ const { data } = await api.get(endpoints.knowledgeList); items.value = data?.data?.list || [] }
  catch(err:any){ toast.show(err?.message || '加载失败') }
  finally{ loading.stop() }
})

const filtered = computed(()=> items.value.filter(i=> (!q.value || [i.source,i.target].some((v:string)=>String(v).includes(q.value))) && (!tableId.value || String(i.table_id).includes(tableId.value)) ))
</script>
