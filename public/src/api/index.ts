import axios from 'axios'
export const api = axios.create({ baseURL: '/api', timeout: 20000 })

export type MatchLine = { source:string, target:string, confidence?:number }

export const endpoints = {
  // 仪表板与历史
  dashboardRecent: '/dashboard/recent',
  historyList: '/history',

  // 人工匹配
  parseProtocol: '/match/parse-protocol',
  parseTargetHeaders: '/match/parse-target-headers',
  saveMapping: '/match/save-mapping',
  knowledgeQuery: '/knowledge/query',

  // 知识库
  knowledgeList: '/knowledge/list',
  knowledgeStats: '/knowledge/stats',
  knowledgeUpsert: '/knowledge/upsert',

  // 批量处理
  batchUpload: '/batch/upload',
  batchStatus: (taskId:string)=>`/batch/status/${taskId}`,
  batchDownload: (taskId:string)=>`/batch/download/${taskId}`,

  // 字段配置（协议字段、目标字段）
  protocolFieldsList: '/config/protocol-fields',
  protocolFieldUpsert: '/config/protocol-fields/upsert',
  protocolFieldDelete: '/config/protocol-fields/delete',
  targetFieldsList: '/config/target-fields',
  targetFieldUpsert: '/config/target-fields/upsert',
  targetFieldDelete: '/config/target-fields/delete',

  // 提取模板
  templatesList: '/templates/list',
  templatesUpsert: '/templates/upsert',
  templatesDelete: '/templates/delete',

  // 文档提取流程
  extractStart: '/extract/start',
  extractStatus: (taskId:string)=>`/extract/status/${taskId}`,
  extractDownload: (taskId:string)=>`/extract/download/${taskId}`,
}