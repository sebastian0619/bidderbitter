import { createRouter, createWebHistory } from 'vue-router'
import FileConverter from '@/views/FileConverter.vue'
import NotFound from '@/views/NotFound.vue'

const isProduction = (import.meta.env.VITE_PRODUCTION + '').toLowerCase() === 'true';

const routes = isProduction ? [
  {
    path: '/',
    redirect: '/converter'
  },
  {
    path: '/converter',
    name: 'FileConverter',
    component: FileConverter,
    meta: { title: '文件转Word' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound
  }
] : [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '数据管理' }
  },
  {
    path: '/converter',
    name: 'FileConverter',
    component: FileConverter,
    meta: { title: '文件转Word' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  },
  {
    path: '/section-manager',
    name: 'SectionManager',
    component: () => import('@/views/SectionManager.vue'),
    meta: { title: '智能章节管理' }
  },
  {
    path: '/award-search',
    name: 'AwardSearch',
    component: () => import('@/views/AwardSearch.vue'),
    meta: { title: 'AI自动检索奖项' }
  },
  
  {
    path: '/ai-assistant',
    name: 'AIAssistant',
    component: () => import('@/views/AIAssistant.vue'),
    meta: { title: 'AI智能助手' }
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('@/views/projects/ProjectList.vue'),
    meta: { title: '投标项目管理' }
  },
  {
    path: '/projects/new',
    name: 'CreateProject',
    component: () => import('@/views/projects/ProjectForm.vue'),
    meta: { title: '创建投标项目', mode: 'create' }
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: () => import('@/views/projects/ProjectDetail.vue'),
    meta: { title: '项目详情' },
    props: true
  },
  {
    path: '/projects/:id/edit',
    name: 'EditProject',
    component: () => import('@/views/projects/ProjectForm.vue'),
    meta: { title: '编辑项目', mode: 'edit' },
    props: true
  },
  {
    path: '/awards/new',
    name: 'CreateAward',
    component: () => import('@/views/awards/AwardForm.vue'),
    meta: { title: '创建新奖项' }
  },
  {
    path: '/templates',
    name: 'Templates',
    component: () => import('@/views/templates/TemplateList.vue'),
    meta: { title: '文档模板管理' }
  },
  {
    path: '/templates/:id',
    name: 'TemplateDetail',
    component: () => import('@/views/templates/TemplateDetail.vue'),
    meta: { title: '模板详情' },
    props: true
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 投标文件制作系统`
  }
  next()
})

export default router 