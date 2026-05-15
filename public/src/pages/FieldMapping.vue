<template>
  <div class="field-mapping-container">
    <h2>字段映射配置</h2>
    
    <!-- 任务状态显示 -->
    <div class="task-info" v-if="taskId">
      <p>当前任务ID: {{ taskId }}</p>
      <button @click="loadPreview" :disabled="loading" class="btn">
        {{ loading ? '加载中...' : '加载字段预览' }}
      </button>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <p>正在分析文档字段...</p>
    </div>
    
    <!-- 字段预览区域 -->
    <div v-if="previewData" class="preview-section">
      <h3>字段预览与映射建议</h3>
      
      <div class="stats">
        <div class="stat-item">
          <span class="label">总字段数:</span>
          <span class="value">{{ previewData?.total_fields || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="label">已匹配:</span>
          <span class="value success">{{ previewData?.matched_fields?.length || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="label">待处理:</span>
          <span class="value warning">{{ previewData?.unmatched_fields?.length || 0 }}</span>
        </div>
      </div>
      
      <!-- 已匹配字段 -->
      <div class="matched-section" v-if="previewData?.matched_fields?.length > 0">
        <h4>已自动匹配的字段</h4>
        <div class="matched-fields-grid">
          <div 
            v-for="field in previewData?.matched_fields || []" 
            :key="field.original"
            class="matched-field-card"
            :class="field.type"
          >
            <div class="field-row">
              <span class="original-field">{{ field.original }}</span>
              <span class="arrow">→</span>
              <span class="mapped-field">{{ field.matched }}</span>
            </div>
            <div class="field-meta">
              <span class="confidence-badge" :class="getConfidenceClass(field.confidence)">
                {{ (field.confidence * 100).toFixed(0) }}%
              </span>
              <span class="match-type-badge" :class="field.type">
                {{ getMatchTypeText(field.type) }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 字段映射工作区 -->
      <div class="unmatched-section" v-if="previewData">
        <div class="workspace-header">
          <h4>字段映射工作区</h4>
          <div class="workspace-actions">
            <button @click="autoMap" class="btn primary small" :disabled="autoMapping">
              {{ autoMapping ? '自动映射中...' : '🤖 智能自动映射' }}
            </button>
            <button @click="clearAllMappings" class="btn secondary small" v-if="mappings.length > 0">
              清空所有映射
            </button>
          </div>
        </div>
        
        <div class="mapping-workspace">
          <!-- 左侧：待映射字段 -->
          <div class="source-fields-panel">
            <div class="panel-header">
              <h5>📄 待映射字段</h5>
              <span class="count-badge">{{ unmappedSourceFields.length }}</span>
            </div>
            <div class="field-list" v-if="unmappedSourceFields.length > 0">
              <div 
                v-for="field in unmappedSourceFields" 
                :key="field"
                class="draggable-field source-field"
                :class="{ 'dragging': draggedField === field, 'has-suggestion': getTopSuggestion(field) }"
                draggable="true"
                @dragstart="handleDragStart($event, field)"
                @dragend="handleDragEnd($event)"
                @mouseenter="showSuggestion(field)"
                @mouseleave="hideSuggestion"
              >
                <div class="field-content">
                  <span class="field-icon">📌</span>
                  <span class="field-name">{{ field }}</span>
                  <span class="field-actions">
                    <button 
                      v-if="getTopSuggestion(field)" 
                      @click="quickMap(field)"
                      class="quick-map-btn"
                      :title="`快速映射到: ${getTopSuggestion(field)?.target}`"
                    >
                      ⚡
                    </button>
                    <button @click="ignoreField(field)" class="ignore-btn" title="忽略此字段">
                      ✕
                    </button>
                  </span>
                </div>
                <!-- 推荐提示 -->
                <div v-if="hoveredField === field && getTopSuggestion(field)" class="suggestion-tooltip">
                  推荐: {{ getTopSuggestion(field)?.target }} 
                  ({{ getTopSuggestion(field)?.confidence ? (getTopSuggestion(field)!.confidence * 100).toFixed(0) : '0' }}%)
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <p>✅ 所有字段已映射</p>
            </div>
          </div>
          
          <!-- 中间：已建立的映射关系 -->
          <div class="mappings-panel">
            <div class="panel-header">
              <h5>🔗 已建立的映射</h5>
              <span class="count-badge success">{{ mappings.length }}</span>
            </div>
            <div class="mappings-list" v-if="mappings.length > 0">
              <div 
                v-for="mapping in mappings" 
                :key="mapping.id"
                class="mapping-item"
                :class="{ 'multi-source': mapping.source.length > 1 }"
              >
                <div class="mapping-content">
                  <div class="mapping-source">
                    <span v-for="(src, idx) in mapping.source" :key="src">
                      {{ src }}<span v-if="idx < mapping.source.length - 1">, </span>
                    </span>
                  </div>
                  <div class="mapping-arrow">
                    <svg width="40" height="20" viewBox="0 0 40 20">
                      <line x1="0" y1="10" x2="35" y2="10" stroke="#007bff" stroke-width="2"/>
                      <polygon points="35,6 40,10 35,14" fill="#007bff"/>
                    </svg>
                  </div>
                  <div class="mapping-target">
                    {{ mapping.target }}
                  </div>
                </div>
                <div class="mapping-meta">
                  <span class="confidence-badge" :class="getConfidenceClass(mapping.confidence)">
                    {{ (mapping.confidence * 100).toFixed(0) }}%
                  </span>
                  <button @click="removeMapping(mapping.id)" class="remove-btn" title="删除映射">
                    🗑️
                  </button>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <p>👈 从左侧拖拽字段到右侧目标字段建立映射</p>
            </div>
          </div>
          
          <!-- 右侧：目标字段池 -->
          <div class="target-fields-panel">
            <div class="panel-header">
              <h5>🎯 目标字段</h5>
              <span class="count-badge">{{ unmappedTargetFields.length }}</span>
            </div>
            <div class="field-list" v-if="unmappedTargetFields.length > 0">
              <div 
                v-for="field in unmappedTargetFields" 
                :key="field"
                class="droppable-field target-field"
                :class="{ 
                  'drop-target': dropTarget === field,
                  'suggested': isSuggestedTarget(field)
                }"
                @drop="handleDrop($event, field)"
                @dragover="handleDragOver($event)"
                @dragenter="handleDragEnter($event, field)"
                @dragleave="handleDragLeave($event, field)"
              >
                <div class="field-content">
                  <span class="field-icon">🎯</span>
                  <span class="field-name">{{ field }}</span>
                  <span class="mapped-count" v-if="getFieldMappingCount(field) > 0">
                    {{ getFieldMappingCount(field) }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <p>✅ 所有目标字段已映射</p>
            </div>
          </div>
        </div>
        
        <!-- 映射统计和操作 -->
        <div class="mapping-footer" v-if="mappings.length > 0 || ignoredFields.length > 0">
          <div class="stats-row">
            <div class="stat">
              <span class="stat-label">已映射:</span>
              <span class="stat-value success">{{ mappings.length }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">待映射:</span>
              <span class="stat-value warning">{{ unmappedSourceFields.length }}</span>
            </div>
            <div class="stat" v-if="ignoredFields.length > 0">
              <span class="stat-label">已忽略:</span>
              <span class="stat-value muted">{{ ignoredFields.length }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 应用映射按钮 -->
      <div class="action-section" v-if="mappings.length > 0">
        <button @click="applyMappings" class="btn primary" :disabled="applying">
          {{ applying ? '应用中...' : `应用 ${mappings.length} 个映射` }}
        </button>
        <button @click="clearAllMappings" class="btn secondary">
          清空映射
        </button>
      </div>
      
      <!-- 下一步：下载文件 -->
      <div class="action-section next-step" v-if="previewData">
        <button @click="downloadResult" class="btn success">
          下载生成文件
        </button>
      </div>
    </div>
    
    <!-- 映射历史 -->
    <div class="history-section" v-if="mappingHistory.length > 0">
      <h3>映射历史</h3>
      <div class="history-list">
        <div 
          v-for="history in mappingHistory" 
          :key="history.id"
          class="history-item"
        >
          <span>{{ history.message }}</span>
          <span class="timestamp">{{ history.timestamp }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useToastStore, useLoadingStore } from '../stores/ui'
import { api, endpoints } from '../api'

const props = defineProps<{
  taskId?: string
}>()

const toast = useToastStore()
const loadingStore = useLoadingStore()

// 数据类型定义
interface FieldMapping {
  id: string
  source: string[]
  target: string
  confidence: number
  type?: string
}

interface FieldSuggestion {
  target: string
  confidence: number
  reason?: string
}

// 状态管理
const loading = ref(false)
const applying = ref(false)
const autoMapping = ref(false)
const previewData = ref<any>(null)
const mappings = reactive<FieldMapping[]>([])
const mappingHistory = reactive<Array<{id: string, message: string, timestamp: string}>>([])
const ignoredFields = reactive<string[]>([])
const fieldSuggestions = reactive<Record<string, FieldSuggestion[]>>({})

// 标准目标字段
const standardTargetFields = [
  'ID', '参数', '内容', '信号名称', '数据类型', '类型', 
  '长度', '字节', '单位', '备注', '值域', '信源', '信宿', 
  '信息内容', '消息ID', '接口名称', '时间戳', '转换类型'
]

// 拖拽状态
const draggedField = ref<string>('')
const isDragging = ref(false)
const dropTarget = ref<string>('')
const hoveredField = ref<string>('')

// 计算属性：未映射的源字段
const unmappedSourceFields = computed(() => {
  if (!previewData.value?.extracted_fields) return []
  
  const mappedSources = new Set(mappings.flatMap(m => m.source))
  const ignored = new Set(ignoredFields)
  
  return previewData.value.extracted_fields.filter(
    (field: string) => !mappedSources.has(field) && !ignored.has(field)
  )
})

// 计算属性：未映射的目标字段
const unmappedTargetFields = computed(() => {
  const mappedTargets = new Set(mappings.map(m => m.target))
  return standardTargetFields.filter(field => !mappedTargets.has(field))
})

// 方法定义
async function loadPreview() {
  if (!props.taskId) {
    toast.show('请先创建任务')
    return
  }
  
  loading.value = true
  try {
    const response = await api.get(`/mapping/preview/${props.taskId}`)
    previewData.value = response.data?.data || null
    
    // 加载字段推荐
    if (previewData.value?.extracted_fields) {
      await loadSuggestions(previewData.value.extracted_fields)
    }
    
    // 自动应用高置信度映射
    if (previewData.value?.mapping_suggestions) {
      const highConfidenceMappings = previewData.value.mapping_suggestions.filter(
        (m: any) => m.matched && m.confidence >= 0.9
      )
      
      highConfidenceMappings.forEach((m: any) => {
        createMapping([m.original], m.matched, m.confidence, m.type)
      })
      
      if (highConfidenceMappings.length > 0) {
        toast.show(`已自动映射 ${highConfidenceMappings.length} 个高置信度字段`)
      }
    }
    
    toast.show('字段预览加载成功')
  } catch (error: any) {
    toast.show('加载失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function loadSuggestions(fields: string[]) {
  try {
    const response = await api.post('/mapping/batch-suggest', {
      source_fields: fields,
      available_targets: standardTargetFields
    })
    
    if (response.data?.data?.suggestions) {
      Object.assign(fieldSuggestions, response.data.data.suggestions)
    }
  } catch (error) {
    console.error('加载推荐失败:', error)
  }
}

// 智能自动映射
async function autoMap() {
  if (unmappedSourceFields.value.length === 0) {
    toast.show('没有待映射的字段')
    return
  }
  
  autoMapping.value = true
  try {
    const response = await api.post('/mapping/auto-map', {
      source_fields: unmappedSourceFields.value,
      target_fields: unmappedTargetFields.value,
      threshold: 0.75
    })
    
    const result = response.data?.data
    if (result?.auto_mappings) {
      result.auto_mappings.forEach((m: any) => {
        createMapping(m.source, m.target, m.confidence, m.type)
      })
      
      toast.show(`自动映射完成：${result.auto_mappings.length} 个字段`)
    }
  } catch (error: any) {
    toast.show('自动映射失败: ' + (error.message || '未知错误'))
  } finally {
    autoMapping.value = false
  }
}

// 创建映射
function createMapping(source: string[], target: string, confidence: number = 0.9, type: string = 'manual') {
  // 检查是否已存在
  const existingIndex = mappings.findIndex(m => 
    m.source.length === source.length && 
    m.source.every(s => source.includes(s))
  )
  
  const mapping: FieldMapping = {
    id: existingIndex >= 0 ? mappings[existingIndex].id : generateId(),
    source: source,
    target: target,
    confidence: confidence,
    type: type
  }
  
  if (existingIndex >= 0) {
    mappings[existingIndex] = mapping
  } else {
    mappings.push(mapping)
  }
}

// 生成唯一ID
function generateId(): string {
  return `mapping_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// 删除映射
function removeMapping(mappingId: string) {
  const index = mappings.findIndex(m => m.id === mappingId)
  if (index >= 0) {
    const mapping = mappings[index]
    mappings.splice(index, 1)
    toast.show(`已删除映射: ${mapping.source.join(', ')} → ${mapping.target}`)
  }
}

// 清空所有映射
function clearAllMappings() {
  if (mappings.length === 0) return
  
  if (confirm(`确定要清空所有 ${mappings.length} 个映射关系吗？`)) {
    mappings.length = 0
    toast.show('已清空所有映射关系')
  }
}

// 忽略字段
function ignoreField(field: string) {
  if (!ignoredFields.includes(field)) {
    ignoredFields.push(field)
    toast.show(`已忽略字段: ${field}`)
  }
}

// 获取字段的最佳推荐
function getTopSuggestion(field: string): FieldSuggestion | null {
  const suggestions = fieldSuggestions[field]
  if (!suggestions || suggestions.length === 0) return null
  return suggestions[0]
}

// 快速映射（使用推荐）
function quickMap(field: string) {
  const suggestion = getTopSuggestion(field)
  if (suggestion) {
    createMapping([field], suggestion.target, suggestion.confidence, 'suggested')
    toast.show(`已映射: ${field} → ${suggestion.target}`)
  }
}

// 显示推荐提示
function showSuggestion(field: string) {
  hoveredField.value = field
  
  // 高亮推荐的目标字段
  const suggestion = getTopSuggestion(field)
  if (suggestion) {
    dropTarget.value = suggestion.target
  }
}

// 隐藏推荐提示
function hideSuggestion() {
  hoveredField.value = ''
  if (!isDragging.value) {
    dropTarget.value = ''
  }
}

// 判断是否为推荐的目标字段
function isSuggestedTarget(targetField: string): boolean {
  if (!hoveredField.value) return false
  const suggestion = getTopSuggestion(hoveredField.value)
  return suggestion?.target === targetField
}

// 获取目标字段的映射数量
function getFieldMappingCount(targetField: string): number {
  return mappings.filter(m => m.target === targetField).length
}

// 拖拽处理函数
function handleDragStart(event: DragEvent, fieldName: string) {
  draggedField.value = fieldName
  isDragging.value = true
  event.dataTransfer!.effectAllowed = 'move'
  
  // 显示推荐
  showSuggestion(fieldName)
}

function handleDragEnd(event: DragEvent) {
  isDragging.value = false
  draggedField.value = ''
  dropTarget.value = ''
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
}

function handleDragEnter(event: DragEvent, targetField: string) {
  event.preventDefault()
  dropTarget.value = targetField
}

function handleDragLeave(event: DragEvent, targetField: string) {
  // 只在真正离开时清除
  const relatedTarget = event.relatedTarget as Node | null
  if (!relatedTarget || !(event.currentTarget as HTMLElement)?.contains?.(relatedTarget)) {
    if (dropTarget.value === targetField) {
      dropTarget.value = ''
    }
  }
}

function handleDrop(event: DragEvent, targetField: string) {
  event.preventDefault()
  
  if (draggedField.value && targetField) {
    createMapping([draggedField.value], targetField, 0.9, 'manual')
    toast.show(`已建立映射: ${draggedField.value} → ${targetField}`)
  }
  
  draggedField.value = ''
  dropTarget.value = ''
  isDragging.value = false
}

// 应用映射
async function applyMappings() {
  if (!props.taskId || mappings.length === 0) {
    toast.show('没有可应用的映射')
    return
  }
  
  applying.value = true
  try {
    const response = await api.post('/mapping/apply', {
      task_id: props.taskId,
      mappings: mappings.map(m => ({
        original: Array.isArray(m.source) ? m.source[0] : m.source,
        target: m.target,
        confidence: m.confidence
      }))
    })
    
    if (response.data?.code === 0 || response.data?.data?.success) {
      const historyItem = {
        id: Date.now().toString(),
        message: `成功应用 ${mappings.length} 个字段映射`,
        timestamp: new Date().toLocaleTimeString()
      }
      mappingHistory.push(historyItem)
      
      toast.show('字段映射应用成功')
    }
  } catch (error: any) {
    toast.show('应用失败: ' + (error.message || '未知错误'))
  } finally {
    applying.value = false
  }
}

// 下载结果
async function downloadResult() {
  if (!props.taskId) {
    toast.show('任务ID不存在')
    return
  }
  
  try {
    loadingStore.start('下载中...')
    const response = await fetch(endpoints.extractDownload(props.taskId))
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    let filename = `result_${props.taskId.slice(0, 8)}.xlsx`
    const contentDisposition = response.headers.get('content-disposition')
    if (contentDisposition) {
      const filenameStarMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
      if (filenameStarMatch && filenameStarMatch[1]) {
        filename = decodeURIComponent(filenameStarMatch[1])
      } else {
        const filenameMatch = contentDisposition.match(/filename=["']?([^"';]+)["']?/i)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1]
        }
      }
    }
    
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
    console.error('下载失败:', e)
    toast.show('下载失败: ' + (e.message || '未知错误'))
  } finally {
    loadingStore.stop()
  }
}

function getConfidenceClass(confidence: number) {
  if (confidence >= 0.9) return 'high'
  if (confidence >= 0.7) return 'medium'
  return 'low'
}

function getMatchTypeText(type: string) {
  const typeMap: Record<string, string> = {
    'exact': '精确匹配',
    'fuzzy': '模糊匹配',
    'alias': '别名映射',
    'semantic': '语义匹配',
    'manual': '手动映射',
    'suggested': '推荐映射'
  }
  return typeMap[type] || type
}

// 组件挂载时自动加载预览
onMounted(() => {
  if (props.taskId) {
    loadPreview()
  }
})

// 监听任务ID变化
watch(() => props.taskId, (newTaskId) => {
  if (newTaskId) {
    loadPreview()
  }
})
</script>

<style scoped>
.field-mapping-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.task-info {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.stats {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-item .label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.stat-item .value {
  font-size: 18px;
  font-weight: bold;
}

.stat-item .value.success { color: #4CAF50; }
.stat-item .value.warning { color: #FF9800; }

/* 工作区头部 */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.workspace-header h4 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.workspace-actions {
  display: flex;
  gap: 10px;
}

/* 字段映射工作区样式 */
.mapping-workspace {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr;
  gap: 20px;
  margin: 20px 0;
  min-height: 500px;
}

.source-fields-panel, .mappings-panel, .target-fields-panel {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  border: 2px solid #e9ecef;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #dee2e6;
}

.panel-header h5 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 8px;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  background: #6c757d;
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.count-badge.success {
  background: #28a745;
}

/* 字段列表 */
.field-list {
  flex: 1;
  overflow-y: auto;
  max-height: 600px;
}

/* 可拖拽字段样式 */
.draggable-field {
  padding: 12px;
  margin: 8px 0;
  background: white;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s ease;
  user-select: none;
  position: relative;
}

.draggable-field:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0,123,255,0.15);
  border-color: #007bff;
}

.draggable-field:active {
  cursor: grabbing;
  opacity: 0.7;
}

.draggable-field.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.draggable-field.has-suggestion {
  border-left: 4px solid #28a745;
}

/* 拖拽目标样式 */
.droppable-field {
  padding: 12px;
  margin: 8px 0;
  background: white;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.droppable-field:hover {
  transform: translateX(-4px);
  border-color: #28a745;
  background: #f1f8f4;
}

.droppable-field.drop-target {
  border-color: #28a745;
  border-style: solid;
  background: #d4edda;
  transform: scale(1.03);
  box-shadow: 0 0 0 3px rgba(40,167,69,0.2);
}

.droppable-field.suggested {
  border-color: #ffc107;
  background: #fff3cd;
}

/* 字段内容 */
.field-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.field-name {
  flex: 1;
  font-weight: 500;
  color: #212529;
  font-size: 14px;
}

.field-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.draggable-field:hover .field-actions {
  opacity: 1;
}

.quick-map-btn, .ignore-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.quick-map-btn:hover {
  background: #0056b3;
  transform: scale(1.1);
}

.ignore-btn {
  background: #dc3545;
}

.ignore-btn:hover {
  background: #c82333;
  transform: scale(1.1);
}

.mapped-count {
  background: #007bff;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: bold;
}

/* 推荐提示 */
.suggestion-tooltip {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  padding: 6px 10px;
  background: #28a745;
  color: white;
  border-radius: 4px;
  font-size: 12px;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.suggestion-tooltip::before {
  content: '';
  position: absolute;
  top: -4px;
  left: 20px;
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-bottom: 4px solid #28a745;
}

/* 映射列表 */
.mappings-list {
  flex: 1;
  overflow-y: auto;
  max-height: 600px;
}

.mapping-item {
  background: white;
  border: 2px solid #007bff;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  transition: all 0.2s ease;
}

.mapping-item:hover {
  box-shadow: 0 4px 12px rgba(0,123,255,0.2);
  transform: translateY(-2px);
}

.mapping-item.multi-source {
  border-color: #6f42c1;
  background: #f8f5ff;
}

.mapping-content {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.mapping-source {
  flex: 1;
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.mapping-arrow {
  flex-shrink: 0;
}

.mapping-target {
  flex: 1;
  font-weight: 600;
  color: #007bff;
  font-size: 14px;
}

.mapping-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.confidence-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: bold;
}

.confidence-badge.high {
  background: #d4edda;
  color: #155724;
}

.confidence-badge.medium {
  background: #fff3cd;
  color: #856404;
}

.confidence-badge.low {
  background: #f8d7da;
  color: #721c24;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  opacity: 0.6;
  transition: all 0.2s;
}

.remove-btn:hover {
  opacity: 1;
  transform: scale(1.2);
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #6c757d;
  text-align: center;
  font-size: 14px;
}

/* 映射底部统计 */
.mapping-footer {
  margin-top: 20px;
  padding: 16px;
  background: #e3f2fd;
  border-radius: 8px;
  border: 1px solid #bbdefb;
}

.stats-row {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.stat {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
}

.stat-value.success { color: #28a745; }
.stat-value.warning { color: #ffc107; }
.stat-value.muted { color: #6c757d; }

/* 已匹配字段网格 */
.matched-fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.matched-field-card {
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
}

.matched-field-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.matched-field-card.exact {
  border-color: #28a745;
  background: #f8fff9;
}

.matched-field-card.fuzzy {
  border-color: #ffc107;
  background: #fffbf0;
}

.matched-field-card.alias {
  border-color: #17a2b8;
  background: #f0f9ff;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 15px;
}

.field-row .original-field {
  font-weight: 500;
  color: #495057;
}

.field-row .arrow {
  color: #6c757d;
  font-weight: bold;
}

.field-row .mapped-field {
  font-weight: 600;
  color: #007bff;
}

.field-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.match-type-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.match-type-badge.exact {
  background: #d4edda;
  color: #155724;
}

.match-type-badge.fuzzy {
  background: #fff3cd;
  color: #856404;
}

.match-type-badge.alias {
  background: #d1ecf1;
  color: #0c5460;
}

/* 按钮样式 */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn.small {
  padding: 6px 12px;
  font-size: 12px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.primary {
  background: #007bff;
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,123,255,0.3);
}

.btn.secondary {
  background: #6c757d;
  color: white;
}

.btn.secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn.success {
  background: #28a745;
  color: white;
}

.btn.success:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(40,167,69,0.3);
}

.action-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 10px;
}

.next-step {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px dashed #28a745;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* 历史记录 */
.history-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid #eee;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  margin: 5px 0;
  background: #f9f9f9;
  border-radius: 4px;
  font-size: 14px;
}

.timestamp {
  color: #999;
  font-size: 12px;
}
</style>
