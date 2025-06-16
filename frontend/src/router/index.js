import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/awards',
    redirect: '/awards/list'
  },
  {
    path: '/awards/list',
    name: 'AwardsList',
    component: () => import('@/views/Awards/AwardsList.vue'),
    meta: { title: '获奖列表' }
  },
  {
    path: '/awards/upload',
    name: 'AwardsUpload',
    component: () => import('@/views/Awards/AwardsUpload.vue'),
    meta: { title: '上传获奖文档' }
  },
  {
    path: '/awards/manual',
    name: 'AwardsManual',
    component: () => import('@/views/Awards/AwardsManual.vue'),
    meta: { title: '手动录入获奖' }
  },
  {
    path: '/performances',
    redirect: '/performances/list'
  },
  {
    path: '/performances/list',
    name: 'PerformancesList',
    component: () => import('@/views/Performances/PerformancesList.vue'),
    meta: { title: '业绩列表' }
  },
  {
    path: '/performances/upload',
    name: 'PerformancesUpload',
    component: () => import('@/views/Performances/PerformancesUpload.vue'),
    meta: { title: '上传业绩文档' }
  },
  {
    path: '/performances/manual',
    name: 'PerformancesManual',
    component: () => import('@/views/Performances/PerformancesManual.vue'),
    meta: { title: '手动录入业绩' }
  },
  {
    path: '/generate',
    redirect: '/generate/combined'
  },
  {
    path: '/generate/awards',
    name: 'GenerateAwards',
    component: () => import('@/views/Generate/GenerateAwards.vue'),
    meta: { title: '生成获奖文档' }
  },
  {
    path: '/generate/performances',
    name: 'GeneratePerformances',
    component: () => import('@/views/Generate/GeneratePerformances.vue'),
    meta: { title: '生成业绩文档' }
  },
  {
    path: '/generate/combined',
    name: 'GenerateCombined',
    component: () => import('@/views/Generate/GenerateCombined.vue'),
    meta: { title: '生成综合文档' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 