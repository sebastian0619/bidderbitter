import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Settings from '@/views/Settings.vue'
import FileConverter from '@/views/FileConverter.vue'
import NotFound from '@/views/NotFound.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '数据管理'
    }
  },
  {
    path: '/converter',
    name: 'FileConverter',
    component: FileConverter,
    meta: {
      title: '文件转Word'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 法律投标系统`
  }
  next()
})

export default router 