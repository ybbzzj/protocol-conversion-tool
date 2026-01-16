<template>
  <div class="container">
    <div class="card">
      <h2>人工匹配</h2>
      <div class="grid grid-2 list-container">
        <div>
          <h3>协议字段列表</h3>
          <p class="hint">拖拽字段到右侧进行匹配</p>
          <ul>
            <li v-for="s in sourceFields" :key="s" draggable="true" @dragstart="onDragStart($event, s)">
              {{ s }}
            </li>
          </ul>
        </div>
        <div>
          <h3>目标表头列表</h3>
          <p class="hint">将左侧字段拖入此处</p>
          <ul>
            <li v-for="t in targetHeaders" :key="t" @dragover.prevent @drop="onDrop($event, t)" :class="{ matched: mapping[t] }">
              <div class="flex" style="justify-content: space-between;">
                <span>{{ t }}</span>
                <span class="badge" v-if="mapping[t]">{{ mapping[t] }}</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
      
      <div class="flex" style="margin-top:24px; padding-top: 24px; border-top: 1px solid var(--border-color);">
        <input class="input" v-model="tableId" placeholder="来源 table_id（如：BC-RT1）" style="max-width: 300px;" />
        <button class="btn" @click="save" :disabled="!tableId">保存映射</button>
        <button class="btn secondary" @click="queryKnowledge" :disabled="!tableId">查询知识库建议</button>
      </div>
      
      <div class="card" style="margin-top: 24px; background: #f8fafc; border: none;">
        <h3>已建立的连线</h3>
        <table class="table" style="background: white; border-radius: var(--radius-sm); overflow: hidden;">
          <thead><tr><th>来源字段</th><th>目标表头</th></tr></thead>
          <tbody>
            <tr v-for="(src, tgt) in entries" :key="tgt"><td>{{ src }}</td><td>{{ tgt }}</td></tr>
            <tr v-if="entries.length === 0"><td colspan="2" style="text-align: center; color: var(--text-secondary);">暂无匹配</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, ref } from 'vue'
import { useToastStore, useLoadingStore } from '../stores/ui'
import { api, endpoints, MatchLine } from '../api'
const toast = useToastStore(); const loading = useLoadingStore()

// 由后端解析获得（此处仍放置默认占位，启动后可通过接口替换）
const sourceFields = ref<string[]>(['BC','I','O','0x03','模式'])
const targetHeaders = ref<string[]>(['BC','Input','Output','Code','Mode'])
const tableId = ref('')

const mapping: Record<string,string> = reactive({})

function onDragStart(e: DragEvent, field: string){ e.dataTransfer?.setData('text/plain', field) }
function onDrop(e: DragEvent, header: string){ const field = e.dataTransfer?.getData('text/plain'); if(field){ mapping[header] = field; toast.show(`匹配: ${field} -> ${header}`) } }

const entries = computed(()=>Object.entries(mapping))

async function save(){
  loading.start('保存映射...')
  try{
    const payload: { table_id:string, mapping: MatchLine[], operator?:string } = {
      table_id: tableId.value,
      mapping: Object.entries(mapping).map(([t,s])=>({ source:s, target:t }))
    }
    await api.post(endpoints.saveMapping, payload)
    toast.show('映射已保存')
  }catch(err:any){ toast.show(err?.message || '保存失败') }
  finally{ loading.stop() }
}

async function queryKnowledge(){
  loading.start('查询知识库建议...')
  try{
    const s = Object.values(mapping)[0] || 'BC'
    const { data } = await api.post(endpoints.knowledgeQuery, { table_id: tableId.value, source: s })
    const candidates = data?.data?.candidates || []
    if(candidates.length){ toast.show(`建议：${candidates[0].target} (${Math.round(candidates[0].confidence*100)}%)`) }
    else{ toast.show('暂无建议') }
  }catch(err:any){ toast.show(err?.message || '查询失败') }
  finally{ loading.stop() }
}
</script>

<style scoped>
.list-container ul { list-style: none; padding: 0; margin: 0; }
.list-container li { 
  background: white; 
  border: 1px solid var(--border-color); 
  padding: 12px 16px; 
  margin-bottom: 8px; 
  border-radius: var(--radius-sm); 
  cursor: grab; 
  transition: all 0.2s;
  box-shadow: var(--shadow-sm);
}
.list-container li:hover { border-color: var(--primary); transform: translateY(-1px); box-shadow: var(--shadow-md); }
.list-container li:active { cursor: grabbing; }

.list-container li.matched {
  background: #f0f9ff;
  border-color: #bae6fd;
}
</style>
