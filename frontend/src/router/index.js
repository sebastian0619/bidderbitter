import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/files',
    name: 'FileManager',
    component: () => import('../views/FileManager.vue')
  },
  {
    path: '/pdf-tools',
    name: 'PDFTools',
    component: () => import('../views/PDFTools.vue')
  },
  {
    path: '/tags',
    name: 'TagManager',
    component: () => import('../views/TagManager.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
