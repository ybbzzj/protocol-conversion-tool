import { createRouter, createWebHashHistory } from 'vue-router'

const Dashboard = () => import('../pages/Dashboard.vue')
const Knowledge = () => import('../pages/Knowledge.vue')
const Extract = () => import('../pages/Extract.vue')
const Config = () => import('../pages/Config.vue')
const Help = () => import('../pages/Help.vue')

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: Dashboard },
    { path: '/extract', name: 'extract', component: Extract },
    { path: '/config', name: 'config', component: Config },
    { path: '/knowledge', name: 'knowledge', component: Knowledge },
    { path: '/help', name: 'help', component: Help },
  ],
})

export default router