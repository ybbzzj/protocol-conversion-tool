import { createRouter, createWebHashHistory } from 'vue-router'

const Dashboard = () => import('../pages/Dashboard.vue')
const Knowledge = () => import('../pages/Knowledge.vue')
const Extract = () => import('../pages/Extract.vue')
const Config = () => import('../pages/Config.vue')
const Help = () => import('../pages/Help.vue')
const FieldMapping = () => import('../pages/FieldMapping.vue')
const ExtractResult = () => import('../pages/ExtractResult.vue')

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: Dashboard },
    { path: '/extract', name: 'extract', component: Extract },
    { path: '/extract-result', name: 'extract-result', component: ExtractResult },
    { path: '/config', name: 'config', component: Config },
    { path: '/knowledge', name: 'knowledge', component: Knowledge },
    { path: '/help', name: 'help', component: Help },
    { path: '/mapping/:taskId', name: 'mapping', component: FieldMapping, props: true },
  ],
})

export default router
